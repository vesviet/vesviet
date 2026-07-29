---
title: "Shopee Architecture Masterclass: Flash Sale Scaling in Go"
slug: "shopee-architecture"
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

> **Answer-first:** The Shopee Architecture series details how Go microservices, Redis Lua inventory reservation, Apache Kafka peak shaving, TiDB distributed SQL, and OpenTelemetry/ClickHouse observability handle 10M+ QPS and millions of concurrent buyers during 11.11 flash sales without overselling or database connection starvation.

This series explores the core architectural patterns and technologies Shopee uses to handle millions of concurrent users, specifically focusing on extreme traffic spikes during Flash Sales and mega-campaigns like 11.11.

## Series Contents

The following five chapters break down Shopee's high-concurrency production stack step-by-step, tracing requests from gateway routing down to storage engine persistence and observability:

- [Chapter 1: Microservices Foundation](/series/shopee-architecture/01-microservices-foundation/)
- [Chapter 2: Flash Sale Engine](/series/shopee-architecture/02-flash-sale-engine/)
- [Chapter 3: Traffic Shield](/series/shopee-architecture/03-traffic-shield/)
- [Chapter 4: Database Scale](/series/shopee-architecture/04-database-scale/)
- [Chapter 5: Observability](/series/shopee-architecture/05-observability/)

---

*Looking for an architectural guide to migrating a legacy e-commerce platform to a microservices architecture similar to Shopee's? See our **[Composable Commerce Migration Series](/series/composable-commerce-migration/)** for a step-by-step production case study.*

## Architectural Scope & Technical Pillars

The matrix below maps each architectural module to its core engineering focus, primary technology stack, and target production Service Level Agreement (SLA):

| Module | Focus Area | Core Technologies | Target SLA / Metric |
|---|---|---|---|
| **Chapter 1: Microservices Foundation** | Domain decomposition & RPC dispatch | Go, gRPC, Protobuf, Kratos | Sub-5ms RPC latency |
| **Chapter 2: Flash Sale Engine** | Hot key prevention & inventory isolation | Redis, Lua Scripts, Atomic Decr | 100k+ QPS write throughput |
| **Chapter 3: Traffic Shield** | Peak shaving & graceful degradation | Apache Kafka, Token Bucket Rate Limiting | 99.99% availability under traffic spikes |
| **Chapter 4: Database Scale** | Distributed SQL & Sharding migration | MySQL Sharding, TiDB, Debezium CDC | Zero-downtime schema migrations |
| **Chapter 5: Observability** | Tracing & telemetry instrumentation | OpenTelemetry, Prometheus, Grafana | Unified trace context across microservices |

## Target Audience & Technical Prerequisites

This masterclass is engineered for **Senior Backend Architects, Systems Engineers, and Go Developers** building ultra-high-throughput systems. The guidelines assume practical experience with distributed systems design principles:

- Strong familiarity with Go concurrency patterns (goroutines, channels, worker pools).
- Understanding of distributed caching (Redis) and event messaging (Kafka).
- Fundamental knowledge of relational database indexing and sharding principles.

## Key System Invariants

Every architectural pattern in this series adheres to five core system invariants that guarantee system stability during 10M+ QPS traffic surges:

1. **Zero Overselling Guarantee**: Redis atomic decrements (`DECR`) coupled with Lua scripts prevent inventory balance from going negative under extreme peak loads.
2. **Asynchronous Write Offloading**: Order creation events flow into Apache Kafka topics before relational database persistence, absorbing 100k+ QPS traffic surges.
3. **Graceful Degradation Shields**: Token bucket rate limiters reject invalid request bursts at the API gateway before hitting backend microservices.
4. **Distributed Telemetry Correlation**: Unified OpenTelemetry trace context propagates through gRPC headers, providing distributed observability across all microservice layers.
5. **Storage Decoupling**: LSM-Tree storage models and distributed SQL (TiDB) decouple write transactions from physical disk latency bottlenecks.

## Frequently Asked Questions (FAQ)

{{< faq "How does Shopee's architecture prevent inventory overselling during 11.11 flash sales?" >}}
Shopee isolates inventory in Redis memory shards and executes atomic Lua scripts to evaluate user eligibility and decrement stock in a single thread-safe step. By decoupling stock pre-allocation from SQL database writes, inventory deductions execute in sub-milliseconds without acquiring relational database locks.
{{< /faq >}}

{{< faq "Why is Apache Kafka used for asynchronous peak shaving instead of synchronous gRPC processing?" >}}
Synchronous gRPC calls to relational databases during 10M+ QPS flash sale spikes exhaust database connection pools and cause severe row-lock deadlocks. Pushing order events into Kafka queues absorbs traffic bursts immediately, allowing write-behind consumer workers to persist orders into storage at a steady, controlled rate.
{{< /faq >}}

{{< faq "What architectural advantages does TiDB NewSQL provide over traditional MySQL sharding?" >}}
TiDB separates stateless SQL compute nodes from distributed TiKV storage nodes, eliminating manual database sharding maintenance and complex application routing proxies. It uses Multi-Raft consensus to automatically split and rebalance data regions across storage nodes while preserving strict ACID transactions.
{{< /faq >}}
