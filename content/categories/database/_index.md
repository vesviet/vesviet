---
title: "Database"
description: "Database scalability, PostgreSQL internals, MySQL sharding, TiDB distributed SQL, and Redis caching by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/database/"
cover:
  image: "/images/posts/database.jpg"
---

> **Answer-first:** The Database category covers distributed data architectures, application-level MySQL sharding vs Vitess, NewSQL migration to TiDB Multi-Raft, PostgreSQL JSONB document modeling, Redis Lua atomic operations, and HNSW vector search engines, analyzing horizontal partitioning strategies, transactional consistency anomalies, distributed lock managers, and performance tuning for high-throughput transactional and analytical database systems.

## Core Focus Areas

- **Distributed SQL & Sharding:** Horizontal partitioning keys, cross-shard queries, and distributed ACID transactions.
- **NewSQL Multi-Raft Consensus:** Replacing legacy sharding clusters with transparently scalable TiDB or CockroachDB engines.
- **In-Memory & Vector Storage:** Atomic concurrency control with Redis Lua scripts and high-dimensional vector search indexing.

## Featured Series & Masterclasses

- [Architectural Tradeoffs Showdowns](/series/architectural-tradeoffs-showdowns/) — MariaDB vs MySQL storage engines, thread pools, and sharded MySQL vs TiDB NewSQL.
- [Distributed System Design Masterclass](/series/system-design/) — Database scaling, horizontal sharding strategies, and multi-region replication.

## Core Technical Essays

- [Replace MySQL Sharding with TiDB: Distributed SQL Migration Guide](/posts/mysql-scaling-sharding-tidb-architecture/) — Step-by-step zero-downtime migration from sharded MySQL to TiDB.
- [Vitess vs GORM Sharding: MySQL Write Scaling in Go](/posts/mysql-horizontal-scaling/) — Evaluating database proxy sharding vs client-side routing libraries.
- [MySQL Scalability: Read Replicas, Sharding & TiDB](/posts/mysql-scalability-guide/) — Architectural progression from single-node replication to distributed NewSQL.
- [Database Impact on Programming Languages](/posts/database-impact-on-programming-languages/) — How storage engine design dictates concurrency models and type systems.
- [Building Custom Golang Vector Database Engine with HNSW](/posts/building-custom-golang-vector-database-engine-hnsw/) — Vector index construction, cosine similarity, and graph navigation in Go.
- [AWS MySQL 8 EOL & Enterprise Commerce Upgrade](/posts/aws-mysql-8-eol-magento-2-4-8-upgrade-architecture/) — Navigating engine deprecation, utf8mb4 collation changes, and query optimization.