---
title: "Chapter 4: Database Scale - From MySQL Sharding to the TiDB Dragon"
date: 2026-05-05T08:40:00+07:00
draft: false
mermaid: true
description: "How Shopee scales its data layer using TiDB and NewSQL to replace complex MySQL sharding."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/shopee-architecture/)
[← Prev](/series/shopee-architecture/03-traffic-shield/) • [Next →](/series/shopee-architecture/05-observability/)

# Chapter 4: Database Scale - The Rise of TiDB and NewSQL

No matter how many layers of Cache or Message Queues you have, the final destination of all transactional data is the Database (the Source of Truth). With tens of millions of daily orders and billions of records, traditional RDBMS like standalone MySQL quickly hit dangerous bottlenecks. The B+Tree index grows too deep, and Disk IOPS reach their physical ceiling.

## 1. The Nightmare of MySQL Sharding
Historically, to scale out MySQL, Shopee (and other tech giants) utilized **Database Sharding**.
- An enormous `Orders` table would be chopped into hundreds of physical databases. For example, using a hashing algorithm on `user_id` (`user_id % 100`) to route orders into Shard 0 through 99.
- **The Core Issues:**
  - While routing by `user_id` is great for buyers, what happens when a Seller wants to view all their store's orders? The system has to perform massive Scatter-Gather queries across hundreds of shards, which is incredibly slow.
  - **Distributed Transactions (2PC):** Updating related data that happens to reside on two different physical shards becomes an engineering nightmare.
  - Resharding and data migration when capacity is full takes months of coding and reconciliation.

## 2. The NewSQL Solution: TiDB
To eliminate the massive engineering overhead of manual sharding, Shopee heavily migrated its core systems to **TiDB**—an open-source NewSQL database. It offers the infinite horizontal scalability of NoSQL while maintaining the strict ACID guarantees and SQL compatibility of Relational databases.

TiDB's unique architecture completely decouples the Compute layer from the Storage layer:
- **TiDB Server (Compute Layer):** These act as stateless SQL engines. They receive standard MySQL protocol requests, parse the SQL, generate Execution Plans, and forward the requests. You can scale out this layer infinitely by spinning up more Docker containers.
- **TiKV (Storage Layer):** The actual data is stored in a distributed Key-Value store (based on RocksDB). Data is chunked into **Regions** (roughly 96MB each).
- **Auto-Sharding & Replication:** TiKV uses the **Raft consensus algorithm** to ensure every Region has 3 replicas spread across different physical disks. As data grows, TiKV automatically splits regions and seamlessly rebalances them onto newly added server nodes—requiring absolutely zero manual code intervention.

```mermaid
graph TD
    App[Shopee Backend] -->|Standard MySQL Protocol| TiDB[TiDB Server<br/>(Stateless SQL Engine)]
    App -->|MySQL Protocol| TiDB2[TiDB Server 2]
    
    subgraph "TiDB Cluster (NewSQL)"
        TiDB --> PD[Placement Driver<br/>Routing & Metadata]
        TiDB2 --> PD
        
        PD -.-> TiKV1[(TiKV Node 1<br/>Raft Leader)]
        PD -.-> TiKV2[(TiKV Node 2<br/>Raft Follower)]
        PD -.-> TiKV3[(TiKV Node 3<br/>Raft Follower)]
        
        TiDB --> TiKV1
        TiDB2 --> TiKV2
        
        TiFlash[(TiFlash<br/>Columnar Storage for OLAP)] -.->|Raft Learner| TiKV1
    end
```

## 3. HTAP (Hybrid Transactional and Analytical Processing)
A massive advantage of the TiDB ecosystem is **TiFlash**.
Normally, you would need complex overnight ETL pipelines to extract data from an OLTP database (MySQL) into a Data Warehouse (like Hadoop or Snowflake) for business reporting. Instead, TiFlash automatically replicates data from TiKV (Row-based format) into a Column-based format in real-time.

This allows Shopee's operation teams to run massive `SELECT ... GROUP BY` analytics queries across billions of Flash Sale records instantly, without causing any lag to the live transactional checkout flow of users.

**Developer Takeaway:** Do not try to "reinvent the wheel" by writing manual database sharding code at the application level unless you have an army of DBAs. NewSQL solutions like TiDB or CockroachDB are the future for transparently handling Big Data at an extreme scale.

{{< author-cta >}}
