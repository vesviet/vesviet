---
title: "Go pprof Tutorial: CPU & Memory Profiling in Production"
slug: "golang-pprof-profiling-memory-cpu-tutorial"
date: "2026-06-02T08:00:00+07:00"
draft: false
description: "Ultimate Go pprof tutorial for production. Learn to safely profile CPU, memory, block contention, and detect leaks with Go 1.26 experimental features."
ShowToc: true
TocOpen: true
categories:
  - "Engineering"
  - "Golang"
  - "Observability"
tags:
  - "Golang"
  - "pprof"
  - "Production"
  - "Profiling"
  - "Performance"
  - "Memory Leak"
---

> **Prerequisite:** This guide covers how to profile and diagnose complex performance issues in production. If you are specifically dealing with unbounded goroutine growth, ensure you first understand the foundational concepts in [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/).

Performance degradation in production is inevitable. When a Go microservice suddenly spikes to 90% CPU utilization or triggers an Out-Of-Memory (OOM) kill in Kubernetes, guessing the root cause by staring at the code is rarely effective. You need data.

Enter **`pprof`**.

Built directly into the Go standard library, `pprof` is an incredibly powerful diagnostic tool that samples your application’s execution to identify exactly where CPU time is being spent and where memory is being allocated. While many developers use `pprof` locally, doing it safely in a high-throughput production environment requires understanding sampling rates, overhead, and secure exposure.

This tutorial is a deep-dive into production-ready Go profiling. We will explore how to safely expose endpoints, compare CPU profiling against the Execution Tracer, dissect memory metrics (`alloc_space` vs `inuse_space`), and leverage advanced features like custom profiling labels and the experimental Go 1.26 goroutine leak profiler.

---

## Safely Exposing pprof Endpoints in Production

The most common way to enable profiling is to import the `net/http/pprof` package. As a side effect of the import, this package automatically registers its HTTP handlers to the default `http.DefaultServeMux`.

```go
// Exposing pprof safely on an internal port
// Purpose: Starts an isolated HTTP server dedicated to pprof endpoints
// ensuring that diagnostic data is not exposed to the public internet.
package main

import (
	"log"
	"net/http"
	_ "net/http/pprof" // Automatically registers /debug/pprof/
)

func main() {
	// ... your main application logic ...

	// Run pprof in a background goroutine on a completely separate,
	// internal-only port (e.g., blocked by your VPC or Ingress rules).
	go func() {
		log.Println("Starting pprof server on localhost:6060")
		if err := http.ListenAndServe("localhost:6060", nil); err != nil {
			log.Fatalf("pprof server failed: %v", err)
		}
	}()
	
	// block forever or wait for graceful shutdown
	select {}
}
```

### Production Security and Overhead
Never expose `/debug/pprof/` to the public internet. Exposing it can lead to information disclosure (revealing your source code structure) and Denial of Service (DoS) if an attacker repeatedly triggers expensive CPU profiles.

**Is it safe to run in production?**
- **Heap (Memory) Profiling:** Extremely safe. It runs continuously by default with negligible overhead (statistically sampling 1 in every 512 KB allocated).
- **CPU Profiling:** Safe for short bursts. Running a 30-second CPU profile samples the stack at 100Hz and generally adds less than 2% overhead.
- **Block & Mutex Profiling:** Disabled by default. Setting their rates to `1` (capturing every event) can add 5–20% overhead. Use them surgically.

Once exposed, you can capture a profile using the `go tool pprof` command from your local machine (via port-forwarding):

```bash
# Capture a 30-second CPU profile and open the interactive web UI
go tool pprof -http=:8080 http://localhost:6060/debug/pprof/profile?seconds=30
```

---

## CPU Profiling vs. Execution Tracer (trace)

When a service is slow, the first instinct is to pull a CPU profile. But CPU profiles only tell you what the CPU is *actively doing*. If your service is slow because it is *waiting* (e.g., waiting for a database lock, blocked on channel I/O, or paused by the Garbage Collector), the CPU profile will look surprisingly empty.

### When to use `pprof` (CPU Profile)
Use `pprof` when you have **High CPU Utilization**. It identifies "hot paths"—the loops, expensive algorithms, or massive JSON decoding blocks that are burning through clock cycles.

### When to use `go tool trace` (Execution Tracer)
Use the tracer when you have **High Latency but Low CPU Utilization**. 
The tracer hooks directly into the Go runtime and records an event log of every goroutine scheduling decision, syscall, and garbage collection pause.

```bash
# Capture a 5-second trace
curl -o trace.out http://localhost:6060/debug/pprof/trace?seconds=5

# View the trace in the browser
go tool trace trace.out
```

**Overhead Warning:** The Execution Tracer is heavy. It generates massive files and can introduce 10–20% performance overhead. Do not run it continuously; use it for brief 1–5 second windows when actively debugging a latency spike.

---

## Memory Profiling: alloc_space vs inuse_space

Understanding the difference between allocation and retention is the biggest hurdle for engineers learning `pprof`. The `heap` profile tracks two fundamentally different metrics:

1. **`inuse_space` (Retention):** The amount of memory currently held by your application and not yet garbage collected. If this number climbs infinitely, you have a **Memory Leak**.
2. **`alloc_space` (Allocation Churn):** The total amount of memory ever allocated over the lifetime of the program, even if it was immediately garbage collected. If this number is astronomically high, you have **High GC Pressure**, which consumes CPU cycles to constantly clean up short-lived objects.

### Debugging Workflow

**Scenario A: The OOM Killer (Finding Leaks)**
If Kubernetes is killing your pod for exceeding memory limits, you want to look at `inuse_space`. 

```bash
# Focus explicitly on retained memory
go tool pprof -inuse_space http://localhost:6060/debug/pprof/heap
```
Inside the interactive UI, type `top` to see the functions holding onto the most memory. Often, memory leaks in Go are actually **goroutine leaks**—a goroutine is blocked forever on a channel, keeping all of its local variables alive.

**Scenario B: Optimizing CPU through Memory (Fixing Churn)**
If your CPU usage is high, but the CPU profile shows `runtime.mallocgc` at the top, your program is spending all its time allocating and collecting memory.

```bash
# Focus explicitly on historical allocation volume
go tool pprof -alloc_space http://localhost:6060/debug/pprof/allocs
```
To fix this, you optimize by reducing allocations:
- **Pre-allocate slices:** `make([]int, 0, expectedCapacity)` prevents multiple underlying array re-allocations as the slice grows.
- **Use `sync.Pool`:** Cache and reuse temporary objects (like `bytes.Buffer` or JSON encoders) to completely bypass the GC.

---

## Finding Goroutine Leaks (and Go 1.26 Features)

A standard way to check for goroutine leaks is to compare the baseline number of goroutines against the current number. If it steadily grows from 100 to 10,000 without traffic increasing, you have a leak.

```bash
curl -s http://localhost:6060/debug/pprof/goroutine?debug=1 | grep "goroutine profile: total"
```

### The Go 1.26 `goroutineleak` Profile (Experimental)
Historically, finding *which* of the 10,000 goroutines was leaked required manual inspection of stack traces. Go 1.26 introduces a revolutionary experimental profile: `/debug/pprof/goroutineleak`.

This profile leverages the Garbage Collector's reachability analysis. It mathematically proves whether a goroutine blocked on a channel or mutex can *ever* be unblocked. If the synchronization primitive it is waiting on is unreachable by any active, runnable code, the runtime flags the goroutine as permanently leaked.

To use it in Go 1.26, you must compile your service with the experiment flag:
```bash
GOEXPERIMENT=goroutineleakprofile go build -o myapp main.go
```
Then, simply curl the endpoint to get a precise list of deadlocked, leaked goroutines:
```bash
go tool pprof http://localhost:6060/debug/pprof/goroutineleak
```

---

## Advanced: Custom Profiling Labels with pprof.Do

In a massive multi-tenant microservice, looking at a generic CPU profile is often unhelpful. You might see `json.Unmarshal` taking 40% of the CPU, but you don't know *which* API route or *which* tenant is triggering it.

Go supports **Custom Profiling Labels**, allowing you to attach arbitrary key-value pairs to the execution context. 

```go
// Tagging goroutines with custom pprof labels
// Purpose: Allows filtering CPU and allocation profiles by tenant or HTTP route
package handlers

import (
	"context"
	"runtime/pprof"
)

func ProcessOrder(ctx context.Context, tenantID string, route string) {
	// 1. Create a LabelSet (must be key-value pairs)
	labels := pprof.Labels("tenant", tenantID, "route", route)
	
	// 2. Wrap the execution block with pprof.Do
	// Any CPU samples or allocations collected inside this closure 
	// will be permanently tagged with these labels.
	pprof.Do(ctx, labels, func(ctx context.Context) {
		// Expensive processing goes here...
		decodeHeavyPayload()
	})
}
```

When you download the profile, you can open the Web UI (`go tool pprof -http=:8080 profile.out`) and use the **Focus** menu to filter by `tenant=xyz`. The Flame Graph will instantly redraw to show only the CPU cycles consumed by that specific tenant!

---

## Frequently Asked Questions (FAQ)

{{< faq q="What is the performance overhead of Go pprof?" >}}
Heap profiling uses probabilistic sampling (default `runtime.MemProfileRate` is 512 KB) and is practically free (< 1% overhead). CPU profiling (100Hz sampling) is also very lightweight (< 2%). However, setting Block or Mutex profile rates to capture 100% of events can add 5-20% overhead. Execution tracing (`go tool trace`) is the heaviest, adding 10-20% overhead while actively running.
{{< /faq >}}

{{< faq q="When should I use go tool trace instead of pprof?" >}}
Use `pprof` to find functions actively burning CPU or allocating memory. Use `go tool trace` when you need to diagnose latency spikes, scheduler delays, or lock contention where the CPU is mostly idle but requests are taking too long to complete.
{{< /faq >}}

{{< faq q="How do I profile mutex contention in Go?" >}}
First, enable it in your application code via `runtime.SetMutexProfileFraction(100)` (which samples 1% of contention events). Then, access the data via `go tool pprof http://localhost:6060/debug/pprof/mutex`. Look for functions waiting the longest for a `sync.Mutex` to unlock.
{{< /faq >}}

---

🔗 **Next Step:** Profiling tells you *why* a function is slow, but how do you track a slow request across 20 different microservices? Continue reading to learn how to implement [Distributed Tracing in Go Microservices with OpenTelemetry](/posts/opentelemetry-golang-distributed-tracing-microservices/) (Future Cluster B1). Alternatively, learn how to prevent cascading failures using [Circuit Breakers and Retries in Go](/posts/circuit-breaker-retry-golang-resilience/).

{{< author-cta >}}
