---
title: "Golang"
description: "Production Go (Golang) engineering: zero-allocation memory tuning, goroutine concurrency, gRPC, and Kratos microservices by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/golang/"
cover:
  image: "/images/posts/golang.jpg"
---

> **Answer-first:** The Golang category delivers production-tested Go engineering patterns, focusing on zero-allocation memory optimization, Go 1.25/1.26 runtime internals, goroutine leak detection, remote pprof profiling in Kubernetes, and binary gRPC microservice frameworks, equipping engineers with concrete techniques for race condition prevention, memory escape analysis, garbage collector tuning, and building high-performance concurrency pipelines.

## Core Focus Areas

- **Runtime Internals & Memory Optimization:** Green Tea GC tuning, GOGC settings, GOMEMLIMIT behavior, and zero-allocation string/slice operations.
- **Concurrency & Goroutine Hygiene:** Designing bounded worker pools with `errgroup`, monotonic rate limiters, and eliminating goroutine leaks.
- **Microservices Frameworks & gRPC:** Production architecture with Go-Kratos v2, Protobuf serialization, interceptors, and binary IPC.

## Featured Series & Masterclasses

- [High-Concurrency Systems](/series/high-concurrency-systems/) — Deep-dive benchmarks comparing Go frameworks, networking runtimes, and connection pools.
- [Modular Monolith Architecture](/series/modular-monolith-architecture/) — Idiomatic Go package layouts, internal boundaries, and clean module composition.

## Core Technical Essays

- [Go Microservices Production Guide](/posts/go-microservices/) — Foundation patterns for high-throughput Go services and resilience sidecars.
- [Golang gRPC Microservices: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/) — Enterprise gRPC pipelines, interceptors, and security certificates.
- [Goroutine Pool Patterns in Go: errgroup & Backpressure](/posts/golang-goroutine-pool-errgroup-worker/) — Controlling task concurrency and worker lifecycle without resource starvation.
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/) — Catching blocked goroutines, unclosed channels, and timer leaks using pprof.
- [Go pprof in Kubernetes: Remote Profiling & Flame Graphs](/posts/go-pprof-kubernetes-remote-profiling/) — Safe live profiling of production container workloads without service degradation.
- [Go 1.26: Green Tea GC, Faster CGO & Goroutine Leak Detection](/posts/go-126-green-tea-gc-cgo-performance-guide/) — Analyzing upcoming compiler optimizations, garbage collection speedups, and runtime profiling features.
- [Modern Golang 1.23 & 1.24: High-Performance Zero-Alloc GC Tuning](/posts/modern-golang-123-124-high-performance-zero-alloc-gc-tuning/) — Memory arena profiling, Swiss Tables maps, and CPU cache optimization.