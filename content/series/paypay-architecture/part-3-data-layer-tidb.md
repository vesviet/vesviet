---
title: "Part 3 — The Data Layer: From Aurora to TiDB"
date: "2026-05-05T21:00:00+07:00"
lastmod: "2026-05-05T21:00:00+07:00"
draft: false
description: "Why PayPay migrated from AWS Aurora to self-hosted TiDB: the Aurora bottleneck, TiDB's distributed architecture, the phased migration strategy, and the results."
weight: 4
cover:
  image: "images/posts/paypay-scaling-cover.png"
  alt: "PayPay Architecture series: scaling for planet-scale mobile payment campaigns in Japan"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/paypay-architecture/part-3-data-layer-tidb/"
---

## The Relational Database Bottleneck

When PayPay launched, **AWS Aurora (MySQL compatible)** was the obvious choice for the payment ledger. Aurora is managed, reliable, and well-understood. It scales read capacity easily through Read Replicas. For a startup under urgency to ship, it was the right decision.

As PayPay grew to tens of millions of users and transaction volumes climbed through each successive campaign, two problems became unavoidable.

**Problem 1: The Write Bottleneck.** Aurora's replication model is fundamentally single-primary. All write operations — every payment, every balance update, every ledger entry — must go through a single primary node. You can add as many Read Replicas as you want; the write throughput ceiling is determined entirely by the largest available Aurora instance class. PayPay hit that ceiling. Specifically, **binlog processing became the binding constraint**: Aurora's binary log, which powers replication to Read Replicas, could not keep up with the write volume during major campaigns.

**Problem 2: Vertical Scaling Limits.** When you've already deployed the largest available database instance and transaction volume keeps growing, your only options are architectural — not operational.

### Why Traditional Solutions Failed

**Manual Sharding** was evaluated and rejected. Splitting the user table by User ID (e.g., Users 1–1M on Shard A, 1M–2M on Shard B) sounds straightforward until you consider P2P money transfers: User A (Shard A) sends money to User B (Shard B). Now you have a **cross-shard distributed transaction** — a notoriously complex problem that requires either two-phase commit (slow and fragile) or eventual consistency (unacceptable for financial ledgers). The application code complexity would have been enormous and ongoing.

**NoSQL (DynamoDB or Cassandra)** was rejected for a simpler reason: financial ledgers require **ACID transactions**. You cannot accept a scenario where a payment is recorded in one DynamoDB partition but the balance update fails in another. NoSQL's eventual consistency model and limited transaction support make it fundamentally unsuitable for payment ledger workloads.

## The Move to TiDB (NewSQL)

PayPay's solution was **TiDB**, an open-source distributed SQL database built by PingCAP that combines the horizontal scalability of NoSQL with the ACID guarantees of a traditional RDBMS.

### TiDB's Architecture: Three Layers Working Together

TiDB's power comes from separating concerns into three independent layers:

**1. TiDB (SQL Compute Layer):** Stateless nodes that handle SQL parsing, query planning, and execution. These are the nodes your application connects to — they speak the MySQL protocol, so existing Java/Spring Boot code works without modification. TiDB nodes can be scaled horizontally without any data migration.

**2. TiKV (Distributed Storage Layer):** The actual data storage, distributed across nodes in 96MB chunks called **Regions**. Each Region is replicated three times using the **Raft consensus protocol**, which provides strong consistency guarantees. When TiKV needs to accept a write, a majority of replicas must confirm receipt before the write is acknowledged — exactly the ACID semantics that payment ledgers require.

**3. Placement Driver (PD):** The cluster brain — manages Region placement across TiKV nodes, handles global timestamp allocation (critical for MVCC-based transactions), and balances load. A minimum of 3 PD nodes are deployed to maintain Raft quorum.

### PayPay's Self-Hosted Deployment: Why Not TiDB Cloud?

PayPay chose to deploy TiDB as a **self-hosted cluster on AWS EC2** rather than using the managed TiDB Cloud service. The reasons were control and compliance:

- Full control over **multi-AZ placement** — the cluster spans 3 AWS Availability Zones with TiKV nodes distributed across them. If an entire AZ fails, the remaining two AZs maintain a Raft majority and service continues uninterrupted.
- Precise control over **EC2 instance types** — compute-optimized instances for TiDB nodes, storage-optimized instances for TiKV nodes.
- **Follower Read** enabled (`tidb_replica_read = 'closest-replicas'`): read queries are served from the closest TiKV replica, reducing cross-AZ network latency and data transfer costs.
- A **TiProxy or NLB (Network Load Balancer)** sits in front of the stateless TiDB nodes, distributing connection load.

## The Migration Strategy: Five Phases, Zero Downtime

Migrating a live payment ledger with zero downtime is a significant engineering challenge. PayPay executed a structured five-phase migration over approximately **three months**:

### Phase 1 — Preparation
- Export Aurora schema and validate MySQL protocol compatibility with TiDB (high — TiDB speaks MySQL dialect)
- Identify any Aurora-specific features not supported by TiDB and build workarounds
- Set up TiDB cluster in parallel (EC2 instances, 3-AZ topology, PD + TiKV + TiDB nodes)
- Performance baseline testing on the new cluster

### Phase 2 — Bulk Data Load (TiDB Lightning)
- Take a snapshot of Aurora at a known point in time
- Use **TiDB Lightning** in Physical Import Mode for high-speed initial data ingestion
- TiDB Lightning bypasses the SQL layer and writes directly to TiKV storage files — orders of magnitude faster than INSERT statements for large datasets (tens of terabytes)
- Aurora remains the live production database during this phase

### Phase 3 — Incremental Sync (TiCDC)
- Start **TiCDC** (TiDB Change Data Capture) to stream every write operation from Aurora to TiDB in real time
- TiCDC tails Aurora's binlog and replays changes into TiDB, keeping the two databases in sync with minimal lag
- This phase runs continuously until the cutover decision is made

### Phase 4 — Validation
- Run data accuracy comparisons: row counts, checksum comparisons, sample record verification
- Run performance tests against the TiDB cluster: target throughput, p99 latency, failover behavior (deliberately killing TiKV nodes to validate Raft recovery)
- Run availability tests: simulate AZ failure, confirm automatic failover with zero data loss

### Phase 5 — Traffic Cutover
- Use a **feature flag or load balancer weight shift** to gradually move production traffic from Aurora to TiDB
- Start with non-critical reads (transaction history queries), then move to writes
- Monitor consumer lag, TiDB write throughput, error rates in real time
- Full cutover once all metrics are healthy across multiple campaigns

**Result:** The migration completed in approximately 3 months. Zero incidents after go-live. Aurora's binlog bottleneck was eliminated. Application code required **zero changes** — TiDB's MySQL protocol compatibility meant existing Spring Boot services connected and queried identically.

## Outcomes: What TiDB Actually Delivers

After the migration, PayPay's data layer supports:

| Metric | Before (Aurora) | After (TiDB) |
|---|---|---|
| Write scaling | Single-primary ceiling | Horizontal — add TiKV nodes |
| Sharding complexity | Manual sharding planned | Eliminated entirely |
| Failover | AZ-limited primary failover | 3-AZ Raft-based, automatic |
| Application changes | — | Zero (MySQL compatible) |
| Peak TPS handled | Approaching ceiling | 1,250 TPS with headroom |

**Campaign elasticity:** Before a major campaign, the Platform team provisions additional TiDB compute nodes 30 minutes in advance — without touching TiKV storage nodes. Post-campaign, those compute nodes are deprovisioned within hours. The elastic cost model means PayPay pays for compute only when it needs it.

**Cross-shard problem: solved.** A P2P transfer between two users — regardless of how TiDB distributes their data internally — is a single distributed transaction managed by TiDB's transaction coordinator. The application writes a standard SQL `BEGIN / UPDATE / COMMIT` statement. TiDB handles the distributed coordination transparently, with full ACID guarantees. The nightmare that manual sharding would have created simply does not exist.

For context on how MySQL scaling challenges appear at different points in a system's growth, see [MySQL Scaling, Sharding, and TiDB](/posts/mysql-scaling-sharding-tidb-architecture/) — which covers the progression from vertical scaling to sharding to NewSQL in detail.
