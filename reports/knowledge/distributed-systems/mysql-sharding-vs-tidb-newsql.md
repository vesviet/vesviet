# Database Scaling Showdown: Sharded MySQL (Vitess) vs. Distributed TiDB NewSQL

> **Domain:** Distributed Systems | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Manual Sharding Keys`, `Multi-Raft Range Partitions`, `Distributed ACID`, `Vitess Proxy`

---

## 1. Problem Statement & Operational Context
When relational database tables exceed 100 million rows or write throughput exceeds 20,000 QPS, single-primary MySQL architectures collapse. Engineering teams face the fork between manual sharding and distributed NewSQL.

## 2. Technology Trade-off Matrix

| Dimension | Application Sharding / Vitess | TiDB Distributed NewSQL |
| :--- | :--- | :--- |
| **Cross-Shard Transactions** | Complex, slow (Two-Phase Commit) | **Transparent Distributed 2PC (Percolator)**|
| **Schema Resharding** | High-risk manual resharding operations | **Automatic background region splits** |
| **Cross-Table Joins** | Severely restricted or forbidden | **Supported natively via TiDB SQL Engine** |
| **Read/Write Latency** | Ultra-fast single shard (< 2ms) | Slightly higher network overhead (3–6ms) |

## 3. Agent Retrieval Guidance
- **Apply When:** Scaling e-commerce transaction tables, order databases, or multi-tenant SaaS beyond single RDS limits.
- **Related Articles:** `/posts/mysql-horizontal-scaling/`, `/series/architectural-tradeoffs-showdowns/05-sharded-mysql-vs-tidb-newsql/`.
