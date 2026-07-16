---
title: "Part 5: Observability in Memory – When Everything Shares a Single Call Stack"
lastmod: "2026-07-03T14:59:00+07:00"
description: "Comparing Distributed Tracing in Microservices with In-process Profiling in a Modular Monolith. Why is OpenTelemetry on a Monolith faster and cheaper?"
slug: "observability-in-process-modular-monolith-opentelemetry"
tags: ["Observability", "OpenTelemetry", "Distributed Tracing", "Modular Monolith", "Profiling"]
aliases: ["/series/modular-monolith-architecture/part-5-observability/", "/series/modular-monolith-architecture/cicd-simplified-atomic-deployments-monolith/part-5-observability.md"]
cover: {'image': 'images/posts/golang-microservices-cover.png', 'alt': 'Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal', 'relative': False}
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/modular-monolith-architecture/observability-in-process-modular-monolith-opentelemetry/"
ShowToc: true
TocOpen: true
---

> **Prerequisite:** Before reading this part, please ensure you have read the previous article in this series: [Part 5: Part 4: CI/CD Simplified & Atomic Deployments]({{< ref "part-4-cicd-simplified.md" >}}).

# Part 5: Observability in Memory – When Everything Shares a Single Call Stack

When it comes to operating a production system, Observability is the line between fixing an issue in 10 minutes and staying up all night searching for the root cause. Microservices architecture has made Observability extremely expensive and complex with the advent of **Distributed Tracing**.

Conversely, the **Modular Monolith** brings debugging back to its most fundamental roots: Monitoring the entire system through a **single Call Stack** in memory. This simplicity brings overwhelming technical advantages.

## 1. The Pain of Distributed Tracing

In a Microservices architecture, a single user request might trigger a chain of actions across 5 different services. To know where the request is bottlenecked, you have to use tools like Jaeger, Zipkin, or Datadog APM to stitch the logs together.

This process relies on Trace Propagation:
1. Service A generates a `trace_id`.
2. Service A packs the `trace_id` into an HTTP Header (or gRPC metadata).
3. The data is serialized, encoded, and pushed across the TCP/IP network.
4. Service B receives the network stream, deserializes it, reads the `trace_id`, generates a child span, and logs it.

**The Consequences:**
- **Performance Overhead:** Creating spans, processing HTTP Headers, and network transmission slows down the response time of every service.
- **Skyrocketing Storage Costs:** Millions of services constantly emitting logs and traces overload storage systems. The cost of collecting and indexing logs is often higher than the server compute cost itself (as mentioned in Part 2).
- **Dropped Spans:** Because it travels over the network, if a service drops offline or a log agent crashes, you receive a broken Trace, completely losing track of the actual point of failure.

## 2. The In-Process Advantage of the Modular Monolith

In a Modular Monolith, all communication between modules happens in RAM (In-process memory). Observability achieves maximum efficiency at near-zero cost.

### A. OpenTelemetry In-Process Tracing
Although **OpenTelemetry** is known as the gold standard for Distributed Tracing, it also perfectly supports the Modular Monolith. The difference is:
- Context propagation (passing IDs) does not happen over HTTP, but via **Thread-local variables** or the programming language's Context object.
- Creating a new Child Span directly in RAM takes **about a few nanoseconds**, completely unaffecting system latency (compared to the milliseconds of network parsing).
- You can configure OpenTelemetry to create a Span every time one Module calls a function of another Module via the Internal API, helping map out clear module boundaries without suffering network overhead.

### B. Single Call Stack and the Absolute Stack Trace
The biggest advantage of running in a single process is **Stack Trace Integrity**.
When an Exception occurs in the Database layer of the *Inventory* module (deep within a processing flow originating from the *Checkout* module), the Monolith system will print a single Stack Trace displaying the exact path from the outermost Controller, through the Internal APIs, down to the exact line of code that threw the error.
Everything is perfectly linked, synchronous, and 100% reliable – something Distributed Tracing can never guarantee.

### C. Deep In-process Profiling
A "secret weapon" of the Monolith is the ability to run **Continuous Profiling** (e.g., using `pprof` in Go, JFR in Java, or Datadog Profiler).
Instead of just knowing "Service B responded slowly," a Profiler can tell you exactly *which function, loop, or thread* is consuming the most CPU or RAM throughout the entire lifecycle of the request. This line-of-code level of detail is impossible to achieve if you try to analyze distributed log files.

## 3. Observability Recommendations for Modular Monoliths

To set up an optimal Observability system for a Modular Monolith:
1. **Instrument at Module Boundaries:** Attach OpenTelemetry spans at the public methods (Internal APIs) of each module. This helps you generate beautiful Dependency Graphs exactly like Microservices, but without the network latency cost.
2. **Monitor the Global Connection Pool:** Closely monitor the Database Connection Pool. In a Monolith, a slow-running module can hold a database connection for a long time and exhaust the pool for the entire application (A weakness to note).
3. **Apply Structured Logging (JSON Logs):** Ensure logs are appended with a static `module_name` to easily filter errors by the responsible team on systems like ELK or Datadog.


## 4. Custom Correlation Tracing In-Memory

Because a Modular Monolith runs in a single process, we do not need expensive tracing agents like Jaeger or OpenTelemetry collectors to trace execution flow. Instead, we can pass correlation IDs through Go's `context.Context` to link call stacks.

### Go Context Correlation Tracer
```go
package main

import (
	"context"
	"fmt"
	"time"
)

type correlationKey string
const traceKey correlationKey = "correlation_id"

func StartModuleSpan(ctx context.Context, moduleName string) (context.Context, func()) {
	traceID, ok := ctx.Value(traceKey).(string)
	if !ok {
		traceID = fmt.Sprintf("tr-%d", time.Now().UnixNano())
		ctx = context.WithValue(ctx, traceKey, traceID)
	}
	start := time.Now()
	fmt.Printf("[TRACE STARTED] ID: %s | Module: %s\n", traceID, moduleName)
	
	return ctx, func() {
		fmt.Printf("[TRACE FINISHED] ID: %s | Module: %s | Duration: %v\n", traceID, moduleName, time.Since(start))
	}
}

func main() {
	ctx := context.Background()
	ctx, end1 := StartModuleSpan(ctx, "Billing")
	time.Sleep(10 * time.Millisecond)
	
	_, end2 := StartModuleSpan(ctx, "Notification")
	time.Sleep(5 * time.Millisecond)
	
	end2()
	end1()
}
```

### Structured Logs and Local Context Benefits
Using correlation IDs inside `context.Context` gives us high-fidelity logs:
- **Low CPU/RAM Overhead:** Creating an in-memory span is a simple struct allocation, compared to sending JSON spans over network sockets.
- **Deterministic Tracking:** The correlation ID is guaranteed to propagate through synchronous goroutines.
- **Unified Log Aggregation:** Any logger (Logrus, Zap) can extract the ID from the context and append it as a field to stdout.
- **Simplified Production Audits:** In production, checking a single file containing trace IDs shows the complete lifecycle of a request from gateway to final storage.

### Technical Appendix: Log Shipping and OpenTelemetry Semantic Conventions
To make logs queryable on platforms like Elasticsearch, Datadog, or Grafana Loki:
- **Use JSON Formatting:** Emit all stdout logs in JSON format rather than raw text.
- **Structure Log Fields:** Map logs to the OpenTelemetry semantic conventions. Ensure each log block contains `trace.id`, `span.id`, `service.name`, `log.level`, and `message`.
- **Configure Fluentbit Shipping:** Deploy a local Fluentbit daemon on each cluster node. Fluentbit reads local container logs, parses the JSON payload, and routes them asynchronously to the aggregation backend.
- **Local Context Enrichment:** Automatically append active database metrics (like open connections and CPU load) to the span logging context during trace closures to simplify troubleshooting.




## Operational Context: Part 5 Observability Appendix

### Performance Profiling and CPU Optimization
To optimize the execution speed of modules within a monolithic binary, engineers must perform regular profiling using tools like Go's `pprof`. Profiling runs expose CPU bottlenecks caused by excessive pointer dereferencing and memory allocations. By replacing heap allocations with stack-allocated values and utilizing `sync.Pool` for reusable structures, garbage collection overhead is reduced, allowing the application to achieve sub-nanosecond processing efficiency.




## Operational Context: Part 5 Observability Appendix

### Memory Footprint and GC Optimization
Go's runtime manages memory allocation using a target percentage threshold. When memory usage climbs past this threshold, the garbage collector runs a sweep cycle, pausing execution threads. In a monolithic setup hosting multiple concurrent domains, you must tune this using the `GOGC` environment variable. Setting `GOGC` to 80 or 50 reduces the maximum memory footprint, ensuring the application stays within container memory quotas without triggering out-of-memory crashes.




## Operational Context: Part 5 Observability Appendix

### Network Egress Controls and Local Subnet Routing
When integrating the monolith with external services, configure client-side round-robin load balancing. By resolving downstream service IPs using internal DNS records, the application bypasses external NAT Gateways, routing all traffic within the local private subnet. This co-location eliminates network hops, securing communications and avoiding data transfer egress fees across availability zones.




## Operational Context: Part 5 Observability Appendix

### Transactional Isolation and Database Lock Mitigations
Operating multiple schemas under a single database instance requires setting strict transactional isolation levels. Run transactions using the `Read Committed` isolation level to prevent dirty reads while avoiding lock contention. Ensure that updates to the database occur in alphabetical order of the tables to mitigate deadlock situations during peak request concurrency.




## Operational Context: Part 5 Observability Appendix

### Monorepo Dependency Isolation and Compilation Tuning
Managing third-party dependencies in a single repository requires isolating package definitions. Avoid declaring globally scoped dependencies. Instead, configure discrete dependency lists for each module. Utilize build caching tools in the CI runner to skip unchanged packages during build steps, compressing compilation times and accelerating validation loops.


Observability in a Monolith is clear, cheap, and effective. But if your system is *currently* Microservices (or a terrible Spaghetti Monolith) and you want to consolidate them into a Modular Monolith, where should you start? **[Part 6: Migration Playbook]({{< ref "part-6-migration-playbook.md" >}})** provides a detailed roadmap.

---

## Navigation & Next Steps

[← Previous Part]({{< ref "part-4-cicd-simplified.md" >}})
[Next Part →]({{< ref "part-6-migration-playbook.md" >}})

🔗 **Next Step:** Continue to [Part 6: Part 6: Migration Playbook – Consolidating Microservices]({{< ref "part-6-migration-playbook.md" >}})

Need help implementing this architecture in your organization? [Contact us](/contact/) or [hire our technical consulting team](/hire/) to review your system design and codebase.
