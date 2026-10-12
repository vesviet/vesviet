---
title: "Architecture"
description: "In-depth system design masterclasses, microservices patterns, and high-throughput distributed systems architecture by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/architecture/"
cover:
  image: "/images/posts/architecture.jpg"
---

> **Answer-first:** The Architecture category provides production-grade system design blueprints for high-throughput distributed systems, Domain-Driven Design (DDD) bounded contexts, and fault-tolerant service meshes. Adopting these event-driven paradigms eliminates distributed deadlocks, guarantees idempotent transactional processing across microservices, and maintains sub-50ms P99 latency bounds under extreme seasonal traffic surges of 100,000+ requests per second.

## Core Technical Focus Areas

- **Domain-Driven Design (DDD):** Clean architecture layers, bounded context isolation, ubiquitous language, and domain aggregate invariants.
- **Event-Driven Architectures & Sagas:** Event sourcing, Transactional Outbox pattern, Change Data Capture (CDC), and compensating Saga workflows.
- **Geospatial & High-Concurrency Routing:** High-speed distance matrix calculation, Contraction Hierarchies, and vehicle routing fleet optimization.

## Featured Series & Masterclasses

- [System Design Masterclass](/series/system-design/) — End-to-end distributed system blueprints for high-throughput enterprise platforms.
- [Routing & Geospatial Architecture](/series/routing-geospatial-architecture/) — High-performance spatial indexing, distance matrices, and routing engines.
- [Alipay Double 11 Masterclass](/series/alipay-double-11/) — Unitized cell-based architectures and traffic shielding at 583,000 peak TPS.

## Core Technical Essays

- [Architecting a 21-Service E-Commerce Platform with Go & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) — Domain boundaries, aggregate roots, and gRPC service topologies.
- [OSRM vs GraphHopper: Architecture, Performance & RAM Comparison](/posts/osrm-vs-graphhopper-architecture-comparison/) — Contraction Hierarchies vs Multi-Level Dijkstra routing engine benchmarks.
- [GraphHopper Distance Matrix: Production Self-Hosting Guide](/posts/graphhopper-distance-matrix-production-guide/) — Self-hosting OSM matrix engines, Redis H3 caching, and 99% cost reduction.
- [CVRP & VRPTW Fleet Optimization: High-Throughput Routing in Go](/posts/cvrp-vrptw-alns-fleet-optimization-golang-architecture/) — Solving NP-hard fleet routing with Adaptive Large Neighborhood Search.
- [OSRM Shared Memory on Kubernetes for Live Traffic Updates](/posts/osrm-shared-memory-kubernetes-live-traffic/) — IPC shared memory segment swapping for zero-downtime routing updates.
- [Blueprint of a 21-Service Go E-Commerce Architecture Diagram](/posts/blueprint-ecommerce-microservices-architecture-diagram/) — Comprehensive multi-service system topology and gRPC interceptors.