---
title: "Backend"
description: "Comprehensive backend architecture patterns, API gateways, REST, gRPC, and high-concurrency Go services by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/backend/"
cover:
  image: "/images/posts/backend.jpg"
---

> **Answer-first:** The Backend category delivers actionable implementation blueprints for high-throughput Go services, gRPC/Protobuf binary transport, concurrency control with errgroup worker pools, and asynchronous event processing with NATS JetStream and Kafka, emphasizing zero-allocation memory optimization, resilient circuit breakers, database connection pool tuning, and production profiling to sustain mission-critical backend workloads under extreme traffic.

## Core Focus Areas

- **High-Throughput IPC:** Binary gRPC communication, Protobuf v3 schemas, and Envoy gateway transcoding.
- **Concurrency & Goroutine Management:** Zero-allocation worker pools, backpressure, and runtime leak prevention.
- **Asynchronous Event-Driven Architectures:** Message broker integration, CQRS event sourcing, and transactional outbox patterns.

## Featured Series & Masterclasses

- [High-Concurrency Systems](/series/high-concurrency-systems/) — Deep benchmarks on Go framework runtimes, connection multiplexing, and traffic management.
- [Modular Monolith Architecture](/series/modular-monolith-architecture/) — Designing high-cohesion backend modules with clean internal interfaces in Go.
- [Architectural Tradeoffs Showdowns](/series/architectural-tradeoffs-showdowns/) — Protocol showdowns: gRPC binary streaming vs HTTP REST, NATS JetStream vs Apache Kafka.

## Core Technical Essays

- [Golang gRPC Microservices: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/) — Production-grade gRPC patterns and interceptor pipelines.
- [Goroutine Pool Patterns in Go: errgroup & Backpressure](/posts/golang-goroutine-pool-errgroup-worker/) — Controlling concurrency and preventing memory exhaustion.
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/) — Diagnosing unbuffered channels and context leaks using pprof.
- [Building High-Throughput Event-Driven Microservices: Go, NATS JetStream & CQRS](/posts/building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs/) — Sub-millisecond messaging and event sourcing.
- [Dapr Workflow Go Tutorial: Orchestrated Saga Pattern](/posts/dapr-workflow-saga-orchestration-guide/) — Durable execution and compensation workflows.
- [High-Throughput Go Framework Benchmarks: Gin vs Fiber vs Kratos](/posts/high-throughput-go-framework-benchmarks-gin-fiber-kratos/) — Quantitative latency and memory allocations under peak load.