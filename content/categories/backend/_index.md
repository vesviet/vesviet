---
title: "Backend"
description: "Comprehensive backend architecture patterns, API gateways, REST, gRPC, and high-concurrency Go services by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/backend/"
cover:
  image: "/images/posts/backend.jpg"
---

> **Answer-first:** The Backend category delivers actionable engineering guides for building resilient Go microservices, low-latency gRPC APIs, distributed caching layers, and high-performance transactional engines. Applying these concurrent execution patterns optimizes worker thread pooling with errgroup, reduces memory allocations by up to 60%, and safeguards database connections against cascading connection pool exhaustion under heavy peak workloads.

## Core Technical Focus Areas

- **High-Performance Concurrency:** Bounded worker pools, graceful context propagation, goroutine leak detection, and backpressure handling.
- **gRPC & API Protocols:** Protocol Buffers v3, streaming RPCs, unary interceptors, metadata propagation, and low-latency API gateways.
- **Distributed Transactions:** Saga orchestrations with Dapr and Temporal, idempotent messaging, and distributed locking algorithms.

## Featured Series & Masterclasses

- [System Design Masterclass](/series/system-design/) — Resilient distributed architectures and high-load transactional patterns.
- [Alipay Double 11 Masterclass](/series/alipay-double-11/) — Extreme concurrency backend patterns from the world's highest-volume shopping events.

## Core Technical Essays

- [Go Microservices Production Guide](/posts/go-microservices/) — Architectural patterns, project structuring, and resilience in production.
- [Golang gRPC Microservices Production Guide](/posts/golang-grpc-microservices-production-guide/) — Zero-allocation Protobuf handling and interceptor pipelines.
- [Goroutine Pool Patterns in Go: errgroup & Backpressure](/posts/golang-goroutine-pool-errgroup-worker/) — Preventing uncontrolled goroutine spawns and managing concurrent workloads.
- [Temporal Saga Pattern in Go: Distributed Transactions Guide](/posts/temporal-saga-pattern-golang-distributed-transactions-guide/) — Deterministic workflow execution and stateful compensation handling.
- [Go Microservices Distributed Tracing with OpenTelemetry](/posts/go-microservices-distributed-tracing-architecture/) — W3C tracecontext propagation and latency diagnostics.
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/) — Diagnosing hung channels, leaked select loops, and zombie goroutines.