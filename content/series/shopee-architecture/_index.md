---
title: "Shopee Architecture Masterclass: Flash Sale Scaling in Go"
date: "2026-05-05T08:00:00+07:00"
lastmod: "2026-05-05T08:00:00+07:00"
draft: false
weight: 140
description: "Structured architectural series on how Shopee evolved its backend systems to handle extreme high concurrency during 11.11 Flash Sales in production."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/shopee-flash-sale-cover.png"
  alt: "Shopee Architecture series: scaling for flash sales — rate limiting, Redis, and distributed systems"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/shopee-architecture/"
image: "images/posts/shopee-flash-sale-cover.png"
---

This series explores the core architectural patterns and technologies Shopee uses to handle millions of concurrent users, specifically focusing on extreme traffic spikes during Flash Sales and mega-campaigns like 11.11.

## Series Contents

- [Chapter 1: Microservices Foundation](/series/shopee-architecture/01-microservices-foundation/)
- [Chapter 2: Flash Sale Engine](/series/shopee-architecture/02-flash-sale-engine/)
- [Chapter 3: Traffic Shield](/series/shopee-architecture/03-traffic-shield/)
- [Chapter 4: Database Scale](/series/shopee-architecture/04-database-scale/)
- [Chapter 5: Observability](/series/shopee-architecture/05-observability/)

---

*Looking for a practical guide to migrating a legacy e-commerce platform to a microservices architecture similar to Shopee's? See our **[Composable Commerce Migration Series](/series/composable-commerce-migration/)** for a step-by-step production case study.*


## Architectural Scope & Technical Pillars

| Module | Focus Area | Core Technologies | Target SLA / Metric |
|---|---|---|---|
| **Chapter 1: Microservices Foundation** | Domain decomposition & RPC dispatch | Go, gRPC, Protobuf, Kratos | Sub-5ms RPC latency |
| **Chapter 2: Flash Sale Engine** | Hot key prevention & inventory isolation | Redis, Lua Scripts, Atomic Decr | 100k+ QPS write throughput |
| **Chapter 3: Traffic Shield** | Peak shaving & graceful degradation | Apache Kafka, Token Bucket Rate Limiting | 99.99% availability under traffic spikes |
| **Chapter 4: Database Scale** | Distributed SQL & Sharding migration | MySQL Sharding, TiDB, Debezium CDC | Zero-downtime schema migrations |
| **Chapter 5: Observability** | Tracing & telemetry instrumentation | OpenTelemetry, Prometheus, Grafana | Unified trace context across microservices |

## Target Audience & Technical Prerequisites

This masterclass is engineered for **Senior Backend Architects, Systems Engineers, and Go Developers** building ultra-high-throughput systems. 

**Prerequisites:**
- Strong familiarity with Go concurrency patterns (goroutines, channels, worker pools).
- Understanding of distributed caching (Redis) and event messaging (Kafka).
- Fundamental knowledge of relational database indexing and sharding principles.

## Key System Invariants

1. **Zero Overselling Guarantee**: Redis atomic decrements (`DECR`) coupled with Lua scripts prevent inventory balance from going negative under extreme peak loads.
2. **Asynchronous Write Offloading**: Order creation events flow into Apache Kafka topics before relational database persistence, absorbing 100k+ QPS traffic surges.
3. **Graceful Degradation Shields**: Token bucket rate limiters reject invalid request bursts at the API gateway before hitting backend microservices.
4. **Distributed Telemetry Correlation**: Unified OpenTelemetry trace context propagates through gRPC headers, providing distributed observability across all microservice layers.
5. **Storage Decoupling**: LSM-Tree storage models and distributed SQL (TiDB) decouple write transactions from physical disk latency bottlenecks.
