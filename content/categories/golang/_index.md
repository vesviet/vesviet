---
title: "Golang"
description: "Production Go (Golang) engineering: zero-allocation memory tuning, goroutine concurrency, gRPC, and Kratos microservices by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/golang/"
cover:
  image: "/images/posts/golang.jpg"
---

> **Answer-first:** The Golang category delivers production Go engineering masterclasses focusing on low-latency microservices, zero-allocation memory optimization, goroutine pool coordination, and Green Tea GC tuning. Implementing these high-performance patterns minimizes garbage collection pause times to sub-millisecond ranges, eliminates memory leaks, and unlocks ultra-high throughput across cloud-native backend services handling millions of concurrent connections.

## Core Technical Focus Areas

- **High-Performance Concurrency:** Goroutine life-cycle management, context propagation, worker pools with errgroup, and channel synchronization.
- **Memory Optimization & GC Tuning:** Escape analysis, buffer pooling with `sync.Pool`, zero-allocation serialization, and Go 1.26 Green Tea GC tuning.
- **Production Microservices:** Protobuf serialization, gRPC streaming, Kratos framework architecture, and distributed tracing.

## Featured Series & Masterclasses

- [System Design Masterclass](/series/system-design/) — Building fault-tolerant distributed backends with Go microservices.
- [Alipay Double 11 Masterclass](/series/alipay-double-11/) — Engineering lessons from peak-traffic Go services handling hundreds of thousands of TPS.

## Core Technical Essays

- [Go Microservices Production Guide](/posts/go-microservices/) — Clean architecture, dependency injection, and production project layout.
- [Golang gRPC Microservices Production Guide](/posts/golang-grpc-microservices-production-guide/) — Low-latency RPC communication, interceptor pipelines, and error handling.
- [Goroutine Pool Patterns in Go: errgroup & Backpressure](/posts/golang-goroutine-pool-errgroup-worker/) — Bounded worker concurrency and graceful backpressure mechanisms.
- [Go 1.26: Green Tea GC, Faster CGO & Goroutine Leak Detection](/posts/go-126-green-tea-gc-cgo-performance-guide/) — Benchmark analysis of Go runtime allocator improvements and GC pacing.
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/) — Live diagnostics, heap profiling, and leak prevention patterns.
- [Go pprof in Kubernetes: Remote Profiling & Flame Graphs](/posts/go-pprof-kubernetes-remote-profiling/) — Low-overhead production profiling across live container nodes.