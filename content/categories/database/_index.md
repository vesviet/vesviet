---
title: "Database"
description: "Database scalability, PostgreSQL internals, MySQL sharding, TiDB distributed SQL, and Redis caching by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/database/"
cover:
  image: "/images/posts/database.jpg"
---

> **Answer-first:** The Database category examines advanced data architecture, horizontal MySQL sharding, distributed TiDB NewSQL clustering, and high-performance Redis caching topologies. Engineering teams following these storage strategies resolve distributed locking bottlenecks, maintain zero data loss under failovers, and sustain over 100,000 queries per second with deterministic sub-5ms read latencies across production database clusters.

## Core Technical Focus Areas

- **Relational Scaling & Sharding:** Horizontal partitioning keys, Vitess proxy routing, GORM sharding middleware, and cross-shard query optimization.
- **Distributed SQL (NewSQL):** TiDB Multi-Raft consensus, TiKV key-value storage engine, and zero-downtime MySQL replacement patterns.
- **High-Performance Caching & In-Memory Stores:** Redis clustering, cache-aside invalidation, Lua script transactional atomicity, and CDC cache synchronization.

## Featured Series & Masterclasses

- [PayPay Architecture Series](/series/paypay-architecture/) — Massive NewSQL scaling with TiDB, handling 7.8 billion annual transactions with zero distributed deadlocks.
- [Core Banking Architecture](/series/core-banking-architecture/) — High-assurance immutable ledger databases, transactional isolation, and financial audit durability.

## Core Technical Essays

- [MySQL Scalability Guide: Read Replicas, Sharding & TiDB](/posts/mysql-scalability-guide/) — Architectural progression from single-master instances to distributed SQL clusters.
- [Vitess vs GORM Sharding: MySQL Write Scaling in Go](/posts/mysql-horizontal-scaling/) — Comparative evaluation of application-level sharding vs middleware proxies.
- [Replace MySQL Sharding with TiDB: Distributed SQL Migration](/posts/mysql-scaling-sharding-tidb-architecture/) — Live migration strategies, dual-write verifications, and online schema changes.
- [Real-Time Inventory Synchronization: Kafka, CDC & Redis](/posts/real-time-inventory-ecommerce-architecture/) — High-throughput cache hydration with Debezium change data capture.