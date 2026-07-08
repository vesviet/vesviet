---
title: "Part 5: Observability in Memory â€“ When Everything Shares a Single Call Stack"
lastmod: "2026-07-03T14:59:00+07:00"
description: "Comparing Distributed Tracing in Microservices with In-process Profiling in a Modular Monolith. Why is OpenTelemetry on a Monolith faster and cheaper?"
slug: "observability-in-process-modular-monolith-opentelemetry"
tags: ["Observability", "OpenTelemetry", "Distributed Tracing", "Modular Monolith", "Profiling"]
aliases:
  - "/series/modular-monolith-architecture/part-5-observability/"
  - "/series/modular-monolith-architecture/cicd-simplified-atomic-deployments-monolith/part-5-observability.md"
cover:
  image: "images/posts/golang-microservices-cover.png"
  alt: "Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/modular-monolith-architecture/observability-in-process-modular-monolith-opentelemetry/"
---

# Part 5: Observability in Memory â€“ When Everything Shares a Single Call Stack

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
Everything is perfectly linked, synchronous, and 100% reliable â€“ something Distributed Tracing can never guarantee.

### C. Deep In-process Profiling
A "secret weapon" of the Monolith is the ability to run **Continuous Profiling** (e.g., using `pprof` in Go, JFR in Java, or Datadog Profiler).
Instead of just knowing "Service B responded slowly," a Profiler can tell you exactly *which function, loop, or thread* is consuming the most CPU or RAM throughout the entire lifecycle of the request. This line-of-code level of detail is impossible to achieve if you try to analyze distributed log files.

## 3. Observability Recommendations for Modular Monoliths

To set up an optimal Observability system for a Modular Monolith:
1. **Instrument at Module Boundaries:** Attach OpenTelemetry spans at the public methods (Internal APIs) of each module. This helps you generate beautiful Dependency Graphs exactly like Microservices, but without the network latency cost.
2. **Monitor the Global Connection Pool:** Closely monitor the Database Connection Pool. In a Monolith, a slow-running module can hold a database connection for a long time and exhaust the pool for the entire application (A weakness to note).
3. **Apply Structured Logging (JSON Logs):** Ensure logs are appended with a static `module_name` to easily filter errors by the responsible team on systems like ELK or Datadog.

Observability in a Monolith is clear, cheap, and effective. But if your system is *currently* Microservices (or a terrible Spaghetti Monolith) and you want to consolidate them into a Modular Monolith, where should you start? **[Part 6: Migration Playbook]({{< ref "part-6-migration-playbook.md" >}})** provides a detailed roadmap.


