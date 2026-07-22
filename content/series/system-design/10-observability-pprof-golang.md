---
title: "Go Observability & pprof — Memory Leaks, CPU Profiling & GODEBUG"
slug: "10-observability-pprof-golang"
date: "2026-06-18T13:30:00+07:00"
lastmod: "2026-07-03T15:41:55+07:00"
draft: false
author: "Lê Tuấn Anh"
description: "Go pprof: heap diff memory leak diagnosis, goroutine leak detection, CPU flame graphs, GODEBUG gctrace parsing, and Four Golden Signals."
tags: ["observability", "golang", "pprof", "memory leak", "cpu profiling", "godebug", "system design"]
categories: ["System Design", "Backend Engineering"]
ShowToc: true
TocOpen: true
series: ["system-design"]
cover:
  image: "images/posts/ecommerce-microservices-blueprint-cover.png"
  alt: "System Design Masterclass in Golang: architecture patterns for high-traffic distributed systems"
  relative: false
canonicalURL: "https://tanhdev.com/series/system-design/10-observability-pprof-golang/"
---
**Answer-first:** Go's built-in `pprof` profiler provides CPU sampling, heap allocation analysis, goroutine stack inspection, and blocking profiler — all available as HTTP endpoints in running production services with minimal overhead. Heap diff between two snapshots is the fastest way to identify memory leaks.

> **Prerequisite:** This is Part 10 of the [System Design Masterclass](/series/system-design/). Previous parts built the architecture — this part teaches you how to *see inside* a running system and diagnose production performance issues.

### What You'll Learn That AI Won't Tell You
- **Heap Snapshots Diff Math:** The exact mechanics of how `go tool pprof` diffs memory allocations to pinpoint memory leaks after load tests.
- **Goroutine Stack Memory Leak:** The memory footprint calculation showing why leaked goroutines consume up to 2KB of RAM each, scaling to gigabytes under load.
- **gctrace Telemetry Signals:** How to parse `GODEBUG=gctrace=1` outputs to compute exact garbage collection CPU steal percentages.

---

## Four Golden Signals — The Observability Foundation

**Key Concept:** Google SRE Book's Four Golden Signals are the minimum metrics needed to describe the health of any service. Before investing in detailed profiling, ensure these four are instrumented and alerting correctly.

| Signal | Metric | Go Source | Alert Condition |
|---|---|---|---|
| **Latency** | p50/p95/p99 request duration | `promhttp` histogram | p99 > SLO budget |
| **Traffic** | Requests per second | `promhttp` counter | Sudden drop (outage signal) |
| **Errors** | HTTP 5xx error rate | `promhttp` counter with status label | Rate > 0.1% of traffic |
| **Saturation** | CPU%, memory%, goroutine count | `runtime.MemStats` | Memory > 80% of container limit |

---

## The pprof Profiling Grid

**Endpoint Guide:** `net/http/pprof` exposes six profiling endpoints. Each diagnoses a different class of problem. Import via side-effect (`_ "net/http/pprof"`) to automatically register all handlers on `http.DefaultServeMux`.

| Endpoint | Profile Type | Overhead | Diagnoses |
|---|---|---|---|
| `/debug/pprof/heap` | Heap — inuse & allocs | **< 1%** | Memory leaks (inuse_space), GC pressure (alloc_space) |
| `/debug/pprof/goroutine` | All goroutine stack traces | **< 0.1%** | Goroutine leaks — goroutines blocked indefinitely |
| `/debug/pprof/profile?seconds=30` | CPU sampling (100Hz) | **~5–10%** | CPU bottlenecks — hot code paths |
| `/debug/pprof/block` | Goroutine block events | **~2–5%** | Channel/mutex stalls causing latency |
| `/debug/pprof/mutex` | Contended mutex events | **~2–5%** | Lock contention between goroutines |
| `/debug/pprof/trace?seconds=5` | Full execution trace | **~10–15%** | GC events, scheduler decisions, syscall latency |

### pprof Server Setup

```go
package main

import (
    "log"
    "net/http"
    _ "net/http/pprof" // Side-effect import: registers /debug/pprof/* handlers
)

func main() {
    // pprof server on a separate port — NEVER expose this publicly
    go func() {
        log.Println("pprof listening on localhost:6060")
        // localhost binding ensures it's only accessible from within the host or via port-forward
        if err := http.ListenAndServe("localhost:6060", nil); err != nil {
            log.Printf("pprof server error: %v", err)
        }
    }()

    // Main application server
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

> [!CAUTION]
> **Never expose pprof publicly.** pprof leaks sensitive information: full stack traces (function names, file paths, memory addresses), allocation patterns, and internal concurrency structure. Access only via:
> - `kubectl port-forward pod/my-pod 6060:6060` (Kubernetes)
> - Internal VPN or bastion host
> - Service mesh with mTLS authorization policy

---

## Memory Leak Diagnosis — 5-Step Heap Diff

**Symptom Analysis:** Memory leaks in Go typically manifest as: (1) goroutines blocked indefinitely holding references, (2) growing slices/maps that accumulate without bound, (3) caches without eviction policies. The fastest diagnosis is a heap diff between two snapshots taken before and after a load period.

### Step-by-Step Process

```bash
# Step 1: Capture baseline heap
curl -sK -v -o baseline.pprof http://localhost:6060/debug/pprof/heap
echo "Baseline captured: $(date)"

# Step 2: Run load or wait 5–15 minutes under production traffic

# Step 3: Capture peak heap snapshot
curl -sK -v -o peak.pprof http://localhost:6060/debug/pprof/heap
echo "Peak captured: $(date)"

# Step 4: Diff profiles — shows ONLY the increase (the leak signal)
go tool pprof -base baseline.pprof peak.pprof

# Step 5: In interactive shell
(pprof) top 20          # Top 20 functions by allocation increase
(pprof) list SuspectFunc # Show per-line allocation detail for a specific function
(pprof) web             # Open flame graph in browser (requires graphviz)
```

### Common pprof Commands Reference

```bash
# CPU profile: 30 seconds of sampling (5–10% CPU overhead during capture)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Heap profile — focus on live objects (memory leak detection)
go tool pprof -inuse_space http://localhost:6060/debug/pprof/heap

# Heap profile — focus on total allocations (GC pressure detection)
go tool pprof -alloc_space http://localhost:6060/debug/pprof/heap

# Goroutine dump with full stack traces — pipe through grep
curl http://localhost:6060/debug/pprof/goroutine?debug=2 -o goroutines.txt
grep -A 20 "goroutine [0-9]* \[chan receive" goroutines.txt  # Find blocked goroutines

# Interactive web UI with flame graph (open browser at :8090)
go tool pprof -http=:8090 http://localhost:6060/debug/pprof/heap
```

---

## inuse_space vs alloc_space — Which to Use?

**Comparison Rule:** `inuse_space` shows memory **currently held** (live objects) — use this to find memory leaks. `alloc_space` shows total memory allocated since startup (including already GC'd) — use this to find hot allocation paths causing GC pressure.

### Decision Guide

| Symptom | Profile Mode | Why |
|---|---|---|
| Memory grows continuously, never drops | `inuse_space` heap diff | Live object accumulation |
| CPU high but unclear why | CPU profile (30s) | Find hot code paths |
| GC pauses > 100ms | `alloc_space` | Identify high-frequency allocation paths |
| Goroutine count grows without bound | goroutine dump (`?debug=2`) | Goroutine leaks — blocked channels |
| High latency despite low CPU | Block profile | Channel/mutex contention stalls |

---

## GODEBUG GC Trace — Reading the Output

**gctrace Utility:** `GODEBUG=gctrace=1` prints detailed GC cycle information to stderr — heap sizes, pause durations, and CPU percentage. This is the fastest way to detect GC pressure without pprof setup.

```bash
export GODEBUG=gctrace=1
./my-service 2>&1 | grep "^gc"

# Sample output:
# gc 1 @0.005s 3%: 0.012+1.5+0.045 ms clock, 0.096+1.5/1.2/0+0.36 ms cpu, 4->4->2 MB, 5 MB goal, 8 P
```

### Parsing the Output

```
gc 1          = GC cycle number 1
@0.005s       = 5ms after process start
3%            = 3% of CPU time spent in GC (alert if > 5%)

0.012+1.5+0.045 ms clock:
  0.012 ms    = stop-the-world sweep termination pause
  1.5 ms      = concurrent mark and sweep phase
  0.045 ms    = stop-the-world mark termination pause

4->4->2 MB:
  4 MB        = heap size at start of GC cycle
  4 MB        = heap size at end of marking
  2 MB        = live heap remaining after sweep

5 MB goal     = target heap size before next GC (GOGC based)
8 P           = number of goroutine processors (GOMAXPROCS)
```

> [!WARNING]
> **GC CPU percentage > 5%** is a signal to optimize. Common remediations: reduce allocations (reuse buffers with `sync.Pool`), increase `GOGC` (default 100 — GC runs when heap doubles; increase to 200 to GC less frequently), or set `GOMEMLIMIT` (Go 1.19+) as a hard limit to trigger earlier GC before OOM.

---

## Goroutine Leak Detection

**Leak Diagnosis:** A goroutine leak occurs when goroutines block indefinitely — waiting on a channel that never receives, waiting for a lock never released, or waiting on a context that's never cancelled. The goroutine count grows monotonically and memory grows proportionally to the stack size of leaked goroutines.

```go
package observability

import (
    "fmt"
    "runtime"
    "time"
)

// GoroutineLeakDetector alerts when goroutine count grows beyond a threshold
type GoroutineLeakDetector struct {
    baseline  int
    threshold int
}

func NewGoroutineLeakDetector(threshold int) *GoroutineLeakDetector {
    return &GoroutineLeakDetector{
        baseline:  runtime.NumGoroutine(),
        threshold: threshold,
    }
}

func (g *GoroutineLeakDetector) Check() bool {
    current := runtime.NumGoroutine()
    if current > g.baseline+g.threshold {
        fmt.Printf("ALERT: goroutines=%d (baseline=%d, threshold=+%d) — potential leak!\n",
            current, g.baseline, g.threshold)
        return true
    }
    return false
}

// RuntimeMetricsExporter periodically logs Go runtime metrics
type RuntimeMetricsExporter struct {
    interval time.Duration
}

func (e *RuntimeMetricsExporter) Start() {
    go func() {
        ticker := time.NewTicker(e.interval)
        defer ticker.Stop()
        for range ticker.C {
            var ms runtime.MemStats
            runtime.ReadMemStats(&ms)
            fmt.Printf("[runtime] goroutines=%d heap_inuse=%dMiB heap_alloc=%dMiB gc_total_pause=%dms gc_cycles=%d\n",
                runtime.NumGoroutine(),
                ms.HeapInuse/1024/1024,
                ms.HeapAlloc/1024/1024,
                ms.PauseTotalNs/1_000_000,
                ms.NumGC,
            )
        }
    }()
}
```

**Common goroutine leak patterns in Go:**

```go
// ❌ LEAK: goroutine blocked on channel that nobody reads
func leakyHandler(w http.ResponseWriter, r *http.Request) {
    ch := make(chan Result) // Unbuffered channel
    go func() {
        result := expensiveWork()
        ch <- result // Blocks forever if caller returns early!
    }()
    
    select {
    case res := <-ch:
        w.Write(res.data)
    case <-time.After(1 * time.Second):
        http.Error(w, "timeout", 504) // Returns! goroutine still blocked on ch<-
    }
}

// ✅ FIXED: use context cancellation to unblock the goroutine
func fixedHandler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), time.Second)
    defer cancel() // Always cancel — even on success
    
    ch := make(chan Result, 1) // Buffered — goroutine can always send
    go func() {
        select {
        case ch <- expensiveWork():
        case <-ctx.Done(): // Exit if context cancelled
        }
    }()
    
    select {
    case res := <-ch:
        w.Write(res.data)
    case <-ctx.Done():
        http.Error(w, "timeout", 504)
    }
}
```

---

## Production Observability Stack

```go
package observability

import (
    "fmt"
    "net/http"
    _ "net/http/pprof" // Registers /debug/pprof/* handlers
    "time"
)

// StartObservabilityStack initializes all observability components
func StartObservabilityStack(pprofPort int, leakThreshold int) {
    // 1. pprof server (internal only)
    go func() {
        addr := fmt.Sprintf("localhost:%d", pprofPort)
        fmt.Printf("[observability] pprof server at http://%s/debug/pprof/\n", addr)
        http.ListenAndServe(addr, nil)
    }()

    // 2. Runtime metrics exporter (every 15s)
    exporter := &RuntimeMetricsExporter{interval: 15 * time.Second}
    exporter.Start()

    // 3. Goroutine leak detector (check every 30s)
    detector := NewGoroutineLeakDetector(leakThreshold)
    go func() {
        for range time.Tick(30 * time.Second) {
            detector.Check()
        }
    }()
}
```

---

## Case Study: Memory Leak via Shared Buffer — Production Incident

> 🔥 **[Production Failure]: Go Service OOM — 2 GB/hour Growth**
> **Symptom:** Service memory grew 2 GB/hour. OOM kill after 8 hours. CPU normal. No obvious hot path.
> **Investigation:**
> ```bash
> go tool pprof -base baseline.pprof peak.pprof
> (pprof) top 5
> # → strings.(*Builder).WriteString: +1.8 GB increase
> ```
> **Root Cause:** An HTTP middleware accumulated request URL paths into a `strings.Builder` variable captured in a closure — the variable was scoped to the server lifetime, not the request lifetime.
> ```go
> // ❌ Bug: var buf captured at server init, never reset
> var buf strings.Builder
> mux.Handle("/api/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
>     buf.WriteString(r.URL.Path) // Grows forever!
>     // ...
> }))
>
> // ✅ Fix: local variable scoped to each request
> mux.Handle("/api/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
>     var buf strings.Builder // Allocated per-request, GC'd after handler returns
>     buf.WriteString(r.URL.Path)
>     // ...
> }))
> ```
> **Resolution:** Heap diff identified the exact function in < 10 minutes. Fix was a single-line scope change. Memory leak eliminated.

---

## Series Summary — System Design Masterclass (Golang)

You've completed 10 parts of the masterclass. Here's the knowledge map you've built:

| Part | Topic | Core Concept |
|---|---|---|
| [1](/series/system-design/01-introduction-system-design-golang/) | System Design Thinking | CAP/PACELC, trade-off framework, Clean Architecture |
| [2](/series/system-design/02-load-balancing-api-gateway-go/) | Load Balancing | L4 vs L7, DSR routing, Token Bucket rate limiting |
| [3](/series/system-design/03-caching-strategies-redis-golang/) | Caching | Singleflight + XFetch + Tiered Cache |
| [4](/series/system-design/04-database-scaling-sharding/) | Database Scaling | B-Tree vs LSM, sharding, `database/sql` pool |
| [5](/series/system-design/05-async-message-queues-kafka-go/) | Event-Driven | Kafka zero-copy, Worker Pool, Exactly-Once |
| [6](/series/system-design/06-distributed-locks-concurrency/) | Distributed Locks | Redlock math, etcd Raft, split-brain |
| [7](/series/system-design/07-idempotency-api-design-go/) | Idempotent APIs | SetNX middleware, Stripe pattern |
| [8](/series/system-design/08-saga-pattern-distributed-transactions-go/) | Distributed Transactions | Temporal Saga, Outbox, Debezium |
| [9](/series/system-design/09-consistent-hashing-sharding/) | Consistent Hashing | Virtual nodes, CRC32 ring, GetN |
| **10** | **Observability** | **pprof, heap diff, GODEBUG, goroutine leaks** |
| [11](/series/system-design/11-security-api-rate-limiting/) | API Security | Layered defense, XFF spoofing, Redis Lua sliding window |
| [12](/series/system-design/12-communication-protocols-microservices/) | Communication | Protobuf wire format, HTTP/3 QUIC, GraphQL complexity, ConnectRPC |

🔗 **Next:** [Part 11: Security & API Rate Limiting — Token Bucket, Leaky Bucket & Redis Lua](/series/system-design/11-security-api-rate-limiting/)

---

## FAQ


{{< faq q="How do you detect memory leaks in Go?" >}}
Five steps: (1) capture baseline heap with `curl .../heap -o baseline.pprof`, (2) run load test for 10–30 minutes, (3) capture peak heap, (4) `go tool pprof -base baseline.pprof peak.pprof`, (5) `top 20` to identify functions with the largest allocation increase. Goroutine leak: `curl .../goroutine?debug=2` and grep for `chan receive` in the output.
{{< /faq >}}

{{< faq q="How do you use go tool pprof?" >}}
```bash
# CPU (5–10% overhead during capture):
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Heap (< 1% overhead):
go tool pprof -inuse_space http://localhost:6060/debug/pprof/heap

# Flame graph web UI:
go tool pprof -http=:8090 http://localhost:6060/debug/pprof/heap

# Interactive commands: top / list <func> / web / svg
```
{{< /faq >}}

{{< faq q="What is the difference between inuse_space and alloc_space?" >}}
`inuse_space` = memory **currently held** (live objects). Use to find memory leaks — if it grows continuously over time, something is accumulating. `alloc_space` = total memory allocated from process start, including already GC'd objects. Use to find hot allocation paths causing frequent GC cycles. Debugging a memory leak → `inuse_space`. Reducing GC pressure → `alloc_space`.
{{< /faq >}}

---

## Navigation & Next Steps

[← Previous Part]({{< ref "09-consistent-hashing-sharding.md" >}})
[Next Part →]({{< ref "11-security-api-rate-limiting.md" >}})

🔗 **Next Step:** Continue to [Part 11: Security & API Rate Limiting]({{< ref "11-security-api-rate-limiting.md" >}})

Need help implementing this architecture in your organization? [Contact us](/contact/) or [hire our technical consulting team](/hire/) to review your system design and codebase.
