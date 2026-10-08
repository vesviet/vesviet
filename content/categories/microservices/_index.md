---
title: "Microservices"
description: "Microservices design patterns, Domain-Driven Design, Dapr event mesh, Saga orchestration, and gRPC by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/microservices/"
cover:
  image: "/images/posts/microservices.jpg"
---

> **Answer-first:** The Microservices category focuses on breaking monolithic debt through Domain-Driven Design (DDD), building resilient distributed transaction workflows via Saga patterns with Dapr and Temporal, high-throughput gRPC inter-service communication, and transactional outbox event streaming, providing concrete architectural blueprints for service boundary decomposition, idempotent message handling, distributed deadlock avoidance, and end-to-end tracing across heterogeneous distributed clusters.

## Core Focus Areas

- **Service Decomposition & Bounded Contexts:** Identifying high-cohesion domain boundaries and eliminating cross-domain database coupling.
- **Distributed Transactions & Sagas:** Implementing orchestration and choreography patterns to guarantee eventual consistency across microservices.
- **Inter-Service Networking:** Low-latency binary gRPC Protobuf APIs, Dapr sidecar integration, and distributed tracing propagation.

## Featured Series & Masterclasses

- [High-Concurrency Systems](/series/high-concurrency-systems/) — Microservice communication topologies, API Gateways, and high-throughput connection pools.
- [Modular Monolith Architecture](/series/modular-monolith-architecture/) — Designing well-bounded in-process modules as a foundation before microservices extraction.
- [Composable Commerce Migration](/series/composable-commerce-migration/) — Strangler Fig migration patterns from monoliths to decoupled services.
- [Architectural Tradeoffs Showdowns](/series/architectural-tradeoffs-showdowns/) — Critical comparisons of messaging protocols, serialization formats, and architecture patterns.

## Core Technical Essays

- [Go Microservices Production Guide](/posts/go-microservices/) — Comprehensive guide to structuring, securing, and deploying Go microservices.
- [Architecting 21-Service E-commerce with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) — Production 21-service decomposition, Kratos framework, and distributed Sagas.
- [Blueprint of a 21-Service E-commerce Edge](/posts/blueprint-ecommerce-microservices-architecture-diagram/) — High-level traffic topology, Ingress routing, and internal communication mesh.
- [Banking Microservices Architecture: Go, Saga & Event Sourcing](/posts/banking-microservices-architecture/) — Mission-critical financial transaction processing and immutable ledgers.
- [Dapr Workflow Go Tutorial: Orchestrated Saga Pattern](/posts/dapr-workflow-saga-orchestration-guide/) — State-machine driven distributed transaction coordination in Go.
- [Building High-Throughput Event-Driven Microservices: Go, NATS JetStream & CQRS](/posts/building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs/) — Sub-millisecond messaging and CQRS architecture.