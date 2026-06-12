---
title: "Goroutine Leak Detection and Fix in Production Go Services"
slug: "goroutine-leak-detection-production-golang"
date: "2026-05-26T20:30:00+07:00"
lastmod: "2026-05-26T20:30:00+07:00"
draft: false
mermaid: true
categories:
  - "Engineering"
  - "Golang"
  - "Observability"
tags:
  - "Golang"
  - "Goroutine"
  - "pprof"
  - "Production"
  - "Debugging"
  - "Memory Leak"
  - "Observability"
description: "Learn how to detect, diagnose, and fix goroutine leaks in production Go microservices using pprof, goleak, and the new Go 1.26 goroutineleak profile."
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/goroutine-leak-cover.png"
  alt: "Goroutine Leak Detection and Fix in Production Go Services — pprof, goleak, synctest"
  relative: false
---


**Answer-first:** Learn how to detect, diagnose, and fix goroutine leaks in production Go microservices using pprof, goleak, and the new Go 1.26 goroutineleak profile.

A Kubernetes pod abruptly restarts with exit code 137. The memory metrics dashboard shows a slow, perfectly linear staircase pattern stretching over three days. There are no panic logs in stdout, no database errors, and no abnormal CPU spikes. Just a slow, silent OOM (Out Of Memory) death.

When Kubernetes terminates a pod due to memory exhaustion (OOM exit code 137), GitOps deployment tools like ArgoCD can trigger rollbacks or infinite restart loops, causing cascading cluster instability. Read our guide on [GitOps at scale with Kubernetes and ArgoCD](/posts/gitops-at-scale-kubernetes-argocd-microservices/) to see how infrastructure triggers these events. More often than not, the culprit behind this behavior in Go services is a **goroutine leak**.

Unlike memory leaks in languages like C/C++ or JVM heap leaks, Go goroutine leaks are particularly insidious because goroutines are extremely cheap to spawn. A goroutine starts with a tiny 2KB initial stack size (stable since Go 1.4). However, if a goroutine blocks indefinitely, it holds active references to any variables on its stack and any heap-allocated structures it pointers to. These act as garbage collection roots (GC roots), preventing the Go concurrent garbage collector from reclaiming the associated memory. Under traffic, a slow leak of 100 goroutines per hour can easily hold hostage gigabytes of heap memory within days.

In this deep dive, we will explore the root causes of goroutine leaks in production, how to diagnose them using pprof profiling and metrics diffing, how to write deterministic concurrent tests with Go 1.24’s new `synctest` package, and how to configure alerts to catch them before they trigger OOM alerts.

---

## The Root Causes: Real-world Leak Patterns

A goroutine leaks when it is spawned but has no logical path to exit. This typically happens because the goroutine is waiting on a channel operation, a network socket, a synchronization primitive, or is stuck in an unyielding loop.

### 1. The Unbuffered Channel Trap
In Go, sending to an unbuffered channel blocks the sender until a receiver is ready to read from it. If the receiving goroutine exits early—due to a timeout, a request context cancellation, or an error return—the sender is left blocked forever.

```go
// ❌ LEAKS: The sender blocks indefinitely if the consumer exits early
func fetchUserData(ctx context.Context) <-chan string {
    ch := make(chan string) // unbuffered channel
    go func() {
        // If the parent context cancels or times out, the consumer stops
        // reading from 'ch'. This write blocks the goroutine forever.
        ch <- queryDatabase() 
    }()
    return ch
}
```

**The Fix:** Use a buffered channel with a capacity of 1, or select on the context cancellation signal to ensure the sender exits if the receiver drops.

```go
// ✅ SAFE: Buffered channel allows the sender to write and exit
func fetchUserDataSafe(ctx context.Context) <-chan string {
    ch := make(chan string, 1) // buffered channel
    go func() {
        ch <- queryDatabase()
    }()
    return ch
}
```

### 2. Swallowing Context Cancellation
When spawning background goroutines within a request-scoped handler, those goroutines must respect context cancellation. If they block on channels or APIs without selecting on `ctx.Done()`, they remain active after the HTTP client cancels the connection.

```go
// ❌ LEAKS: Ignored context done signal keeps worker running
func processQueue(ctx context.Context, queue <-chan Job) {
    go func() {
        for job := range queue {
            // If ctx is canceled, this loop continues until queue is closed
            process(job)
        }
    }()
}
```

**The Fix:** Explicitly monitor the context done state within the worker loop.

```go
// ✅ SAFE: Worker respects context cancellation
func processQueueSafe(ctx context.Context, queue <-chan Job) {
    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            case job, ok := <-queue:
                if !ok {
                    return
                }
                process(job)
            }
        }
    }()
}
```

### 3. gRPC Client and Stream Leaks
In complex microservice systems (such as our [21-service ecommerce platform](/posts/architecting-21-service-ecommerce-golang-ddd/)), a single goroutine leak in an API gateway or aggregator service can propagate thread and connection exhaustion downstream. 

A common anti-pattern in gRPC clients is instantiating a new `grpc.ClientConn` via `grpc.NewClient` (or `grpc.Dial` in older versions) per request instead of sharing a global client connection pool. Each client connection spawns multiple background helper goroutines (such as `loopyWriter`, `resetTransport`, and resolver watch loops). If the connection is not explicitly closed via `conn.Close()`, these goroutines leak.

Furthermore, client-side streams must be fully drained or cancelled. Calling `CloseSend()` only closes the send direction; the receive direction remains active, leaving the transport reader goroutine hanging.

```go
// ❌ LEAKS: Unclosed gRPC connection and stream
func callgRPCService(addr string) error {
    conn, _ := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
    client := pb.NewUserServiceClient(conn)
    
    stream, err := client.StreamLogs(context.Background(), &pb.LogRequest{})
    if err != nil {
        return err
    }
    
    // We exit early, but conn is never closed, and the stream's context is not canceled!
    _, err = stream.Recv()
    return err
}
```

**The Fix:** Reuse client connections as global singletons, and always call context cancel handlers or close stream handles properly.

```go
// ✅ SAFE: Reuses connections and cleans up stream lifecycles
type ServiceClient struct {
    conn *grpc.ClientConn
}

func (s *ServiceClient) CallSafe(ctx context.Context) error {
    // Shared conn is not re-created.
    client := pb.NewUserServiceClient(s.conn)
    
    streamCtx, cancel := context.WithCancel(ctx)
    defer cancel() // Canceling context terminates the client-side stream reader loop
    
    stream, err := client.StreamLogs(streamCtx, &pb.LogRequest{})
    if err != nil {
        return err
    }
    
    _, err = stream.Recv()
    return err
}
```

### 4. Database Rows and Transaction Leaks
Failing to release database connections to the driver pool (`database/sql` or `pgx`) will leak goroutines. When you execute `db.Query(...)`, you get back a `sql.Rows` object. If `rows.Close()` is not called, the connection is never returned.

A major pitfall is executing a query and calling a function that can panic *before* `defer rows.Close()` is registered. If the function panics, the rows remain open. Similarly, if `rows.Next()` returns true but `rows.Scan()` panics, some drivers fail to release resources unless `rows.Close()` is executed.

```go
// ❌ LEAKS: Panic before defer blocks resource release
func fetchStats(db *sql.DB) error {
    rows, err := db.Query("SELECT name, value FROM stats")
    if err != nil {
        return err
    }
    
    parseHeaders() // If this panics, rows.Close() is never registered!
    defer rows.Close()
    
    for rows.Next() {
        // ...
    }
    return nil
}
```

**The Fix:** Always register `defer rows.Close()` immediately after checking for the query error. For transactions, always call `defer tx.Rollback()`. If `tx.Commit()` succeeds, the deferred rollback is a safe no-op.

```go
// ✅ SAFE: Guaranteed cleanup for rows and transactions
func updateBalanceSafe(ctx context.Context, db *sql.DB, userID int, amount int64) (err error) {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        return err
    }
    defer tx.Rollback() // Rollback is a safe no-op if Commit succeeds

    rows, err := tx.QueryContext(ctx, "SELECT balance FROM users WHERE id = $1 FOR UPDATE", userID)
    if err != nil {
        return err
    }
    defer rows.Close() // Immediately registered

    var balance int64
    if rows.Next() {
        if err = rows.Scan(&balance); err != nil {
            return err
        }
    }
    rows.Close() // Explicitly close to bubble up errors before commit

    if _, err = tx.ExecContext(ctx, "UPDATE users SET balance = balance + $1 WHERE id = $2", amount, userID); err != nil {
        return err
    }

    return tx.Commit()
}
```

### 5. WebSocket and SSE Client Disconnection Leaks
Long-lived server connections like WebSockets or Server-Sent Events (SSE) must actively monitor client disconnections. If the client disconnects and the server continues to write to the response without checking `r.Context().Done()` or setting deadlines, the handler goroutine blocks forever.

```go
// ❌ LEAKS: SSE loop continues writing even after client disconnects
func handleEvents(w http.ResponseWriter, r *http.Request) {
    flusher, _ := w.(http.Flusher)
    w.Header().Set("Content-Type", "text/event-stream")

    for {
        // The write will absorb bytes until TCP buffers fill up.
        // Once full, this loop blocks indefinitely on writes.
        fmt.Fprintf(w, "data: event at %s\n\n", time.Now().String())
        flusher.Flush()
        time.Sleep(1 * time.Second)
    }
}
```

**The Fix:** Explicitly select on the request context's cancellation signal.

```go
// ✅ SAFE: SSE loop exits immediately when client disconnects
func handleEventsSafe(w http.ResponseWriter, r *http.Request) {
    flusher, ok := w.(http.Flusher)
    if !ok {
        http.Error(w, "Streaming unsupported", http.StatusNotImplemented)
        return
    }
    
    w.Header().Set("Content-Type", "text/event-stream")
    ctx := r.Context()

    for {
        select {
        case <-ctx.Done():
            return // Client disconnected
        case <-time.After(1 * time.Second):
            fmt.Fprintf(w, "data: event at %s\n\n", time.Now().String())
            flusher.Flush()
        }
    }
}
```

### 6. WaitGroup and Mutex Misuses
Mismatched synchronization states can freeze goroutines. Spawning workers and calling `wg.Add(1)` inside the worker goroutine rather than in the parent thread creates a race condition. The parent may execute `wg.Wait()` before any workers start, letting the main execution exit while leaving the background workers orphaned.

Additionally, passing a `sync.Mutex` or `sync.WaitGroup` by value copies its internal lock state. Modifying the copy will not affect the original, causing deadlocks.

```go
// ❌ LEAKS & CRASHES: Race conditions and deadlock
func processConcurrent(items []string) {
    var wg sync.WaitGroup
    for _, item := range items {
        go func(val string) {
            // Race: wg.Add is called after parent executes wg.Wait()
            wg.Add(1) 
            defer wg.Done()
            process(val)
        }(item)
    }
    wg.Wait() // Returns immediately if no worker started yet
}
```

**The Fix:** Always call `wg.Add(1)` in the spawning thread before starting the goroutine, and always pass sync primitives by pointer.

```go
// ✅ SAFE: Proper WaitGroup orchestration
func processConcurrentSafe(items []string) {
    var wg sync.WaitGroup
    for _, item := range items {
        wg.Add(1) // Called in parent thread
        go func(val string) {
            defer wg.Done()
            process(val)
        }(item)
    }
    wg.Wait()
}
```

### 7. time.After inside Hot Loops
In Go, calling `time.After(duration)` inside a select statement within a loop creates a new `time.Timer` on every iteration.

```go
// ❌ LEAKS: Accumulates timer structures on every iteration
for {
    select {
    case msg := <-ch:
        process(msg)
    case <-time.After(5 * time.Second): // Created anew on every loop iteration
        return
    }
}
```

Before Go 1.23, these timers remained registered in the runtime scheduler until their duration expired, even if the channel case was chosen. Under high traffic, this leaked memory rapidly. While Go 1.23 introduced GC reclamation for orphaned timers, explicitly creating a single timer and resetting it remains the best practice for performance and garbage collection hygiene.

---

## Diagnosing in Production: pprof & Metrics

When a goroutine leak occurs in production, you need structured diagnostics to pinpoint the leaky stack trace.

### Metrics Monitoring
Expose Go runtime metrics using the standard `prometheus/client_golang` collector. Track `go_goroutines` (a gauge metric).
*   **Linear Drift:** A steady, linear increase in goroutines during idle periods confirms a leak.
*   **Step Spikes:** Sudden spikes that do not decrease indicate connection bottlenecks or downstream service outages.

```yaml
# PromQL Alert: Detects a >20% growth in goroutine count over 1 hour
- alert: GoroutineLeakSuspected
  expr: go_goroutines > (go_goroutines offset 1h * 1.2) AND go_goroutines > 100
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Sustained goroutine count growth on {{ $labels.instance }}"
    description: "Goroutines have increased by 20% in the last hour. Run pprof diff."
```

### Active Diagnosis with pprof
Enable pprof in your service by importing the package:

```go
import _ "net/http/pprof"
```

Start the HTTP server on an internal admin port (e.g. `localhost:6060`).

#### pprof debug=1 vs debug=2
When querying the `/debug/pprof/goroutine` endpoint:
1.  **`debug=1` (Summary View):** Aggregates identical call stacks and shows the count of goroutines on each stack. This is the best way to spot a pattern (e.g. 5,000 goroutines blocked on a channel read).
2.  **`debug=2` (Detailed Dump):** Prints the raw stack trace of every single goroutine. This dump includes:
    *   The unique Go ID (`goid`).
    *   The execution status (e.g. `[chan receive]`, `[IO wait]`, `[syscall]`).
    *   The blocked duration: If blocked for over a minute, the header displays `[blocked for X minutes]`.

*Caution:* Requesting `debug=2` on services running hundreds of thousands of goroutines triggers a Stop-The-World (STW) pause, causing response latency spikes. Use `debug=1` first.

### pprof Diff Workflow
To find the exact line causing a leak, compare a stable baseline profile with a leaked state profile.

```bash
# 1. Capture baseline profile during stable behavior
curl -s -o baseline.pb.gz http://localhost:6060/debug/pprof/goroutine

# 2. Capture profile when goroutines have accumulated
curl -s -o leak.pb.gz http://localhost:6060/debug/pprof/goroutine

# 3. Diff the two profiles
go tool pprof -base baseline.pb.gz leak.pb.gz
```

Inside the interactive pprof shell, run `top` or `list` to isolate the functions responsible for the positive delta.

```bash
(pprof) top
Showing nodes accounting for 4200, 100% of 4200 total
      flat  flat%   sum%        cum   cum%
      4200   100%   100%       4200   100%  runtime.gopark
         0     0%   100%       4200   100%  net/http.(*persistConn).readLoop
```

### Go 1.26 Experimental goroutineleak Profile
Go 1.26 introduces the experimental `goroutineleak` profile. It uses garbage collection reachability traversal on synchronization primitives (channels, mutexes, waitgroups) to identify goroutines that are blocked on primitives that have no live references.

To enable this, compile your service with the build flag:

```bash
GOEXPERIMENT=goroutineleakprofile go build ./...
```

Access the endpoint via:

```bash
curl http://localhost:6060/debug/pprof/goroutineleak
```

This endpoint filters out healthy, running, or reachable background workers, showing only the stack traces of deadlocked or orphaned goroutines.

---

## CI Prevention: goleak & synctest

Catching leaks in tests during CI/CD prevents them from ever reaching production.

### Using go.uber.org/goleak
`goleak` monitors active goroutines at the start of a test and compares them with the active list at the end.

```go
func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m)
}
```

#### Silencing False Positives
Background tasks (such as pgx connection writers or gRPC balancers) can trigger false failures. Use `goleak.IgnoreTopFunction` to filter them out:

```go
func TestMyService(t *testing.T) {
    defer goleak.VerifyNone(t,
        goleak.IgnoreTopFunction("google.golang.org/grpc/internal/transport.(*controlBuffer).get"),
        goleak.IgnoreTopFunction("github.com/jackc/pgx/v5/pgxpool.(*Pool).backgroundWriter"),
        goleak.IgnoreTopFunction("net/http.(*persistConn).readLoop"),
    )
    // Test logic here
}
```

### Go 1.24 Virtual Time Testing with `testing/synctest`
Testing timeout-handling concurrent code using `time.Sleep` makes tests slow and flaky. Go 1.24 introduces the experimental `testing/synctest` package.

It executes concurrent code inside an isolated **bubble** with a **virtual clock**. The runtime scheduler fast-forwards virtual time instantly when all goroutines in the bubble are "durably blocked" (waiting on timers, channels, or select blocks).

To run these tests, execute:

```bash
GOEXPERIMENT=synctest go test ./...
```

```go
func TestConcurrentTimeoutSafe(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        ch := make(chan string)
        go func() {
            // This time.Sleep does not consume real-world time.
            // It fast-forwards instantly inside the bubble.
            time.Sleep(1 * time.Hour) 
            ch <- "done"
        }()

        synctest.Wait() // Block until the spawned goroutine is durably blocked on sleep

        select {
        case msg := <-ch:
            if msg != "done" {
                t.Errorf("expected done, got %s", msg)
            }
        case <-time.After(2 * time.Hour):
            t.Fatal("virtual timeout exceeded")
        }
    })
}
```

`synctest.Wait()` blocks the test runner until all goroutines in the bubble are either finished or durably blocked. If a worker leaks, the bubble will remain active or panic, catching leaks without relying on flaky timeout checks.

---

## Production-Ready Concurrency Patterns

Below are clean, production-ready implementation patterns for managing goroutine lifecycles.

### 1. The Priority/Biased Select
In select loops, Go selects ready cases randomly. If a job channel is flooded with data, the runtime might skip context cancellation. Use a biased select check:

```go
func worker(ctx context.Context, jobs <-chan Job) error {
    for {
        // 1. Biased select: Check cancellation first
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }

        // 2. Main select: Read data
        select {
        case <-ctx.Done():
            return ctx.Err()
        case job, ok := <-jobs:
            if !ok {
                return nil
            }
            if err := process(ctx, job); err != nil {
                return err
            }
        }
    }
}
```

### 2. Graceful Shutdown with SIGTERM
Ensure HTTP servers and worker pools drain during deployments:

```go
func main() {
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()

    var wg sync.WaitGroup
    jobs := make(chan Job, 100)

    // Start worker pool
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            _ = worker(ctx, jobs)
        }()
    }

    srv := &http.Server{Addr: ":8080"}
    go func() {
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("HTTP listen error: %v", err)
        }
    }()

    <-ctx.Done() // Block until SIGTERM/Interrupt
    log.Println("Shutdown signal received. Cleaning up...")

    // 1. Terminate the HTTP server (stops receiving new connections)
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    _ = srv.Shutdown(shutdownCtx)

    // 2. Close job queue (signals workers to drain and exit)
    close(jobs)

    // 3. Wait for workers to complete remaining tasks
    wg.Wait()
    log.Println("Clean exit completed.")
}
```

---

## Concurrency and Telemetry Checklist

Ensure these safeguards are met before deploying your Go service to production:

- [ ] **Context Propagation:** All long-running API and database calls use context-aware variants (`QueryContext`, `ExecContext`).
- [ ] **Biased Selects:** Select statements inside consumer loops prioritize context cancellation checking.
- [ ] **Transport Singletons:** `http.Client`, `http.Transport`, and `grpc.ClientConn` are shared globally, never created dynamically inside request scopes.
- [ ] **Response Body Close:** HTTP response bodies are closed and drained to `io.Discard` in defer blocks.
- [ ] **Prometheus Alerting:** A `go_goroutines` PromQL alert is configured to monitor linear growth over 1-hour windows.
- [ ] **CI goleak verification:** `goleak` is configured in `TestMain` or integration wrappers with custom `IgnoreTopFunction` settings for driver libraries.

When building modern [agentic architectures](/series/agentic-system-architecture) where background tasks fetch live data or run autonomous LLM tool execution loops, managing goroutine lifecycles is critical to prevent background worker threads from leaking across agent runs. By monitoring runtime statistics and catching concurrency issues early in testing, you can keep your production services stable and free of exit code 137 OOM crashes. For a comprehensive look at the entire Go production architecture that relies on these patterns, see the [Go Microservices Architecture: Production Guide](/posts/go-microservices/).

---

## Frequently Asked Questions

### Does GOMEMLIMIT prevent goroutine leaks?
No. `GOMEMLIMIT` manages Go runtime Garbage Collection soft memory targets. While it can trigger aggressive GC cycles to reclaim heap objects, it has no control over active goroutine stack memory allocations. Blocked goroutine stacks remain in memory, and the heap objects they reference cannot be garbage collected.

### What is the difference between a data race and a goroutine leak?
A data race occurs when multiple goroutines read/write to the same memory location concurrently without synchronization. A leak occurs when a goroutine is orphaned and runs forever. You can use the `-race` detector to catch data races during testing, and `goleak` or `pprof` to diagnose leaks.

### How much memory does a leaked goroutine consume?
A leaked goroutine consumes a baseline of 2KB for its stack, but it can grow larger (doubling dynamically up to 1GB on 64-bit systems). Additionally, any heap objects referenced by the leaked goroutine's stack variables will remain pinned in memory, often resulting in megabytes of leaked memory per goroutine.

{{< author-cta >}}
