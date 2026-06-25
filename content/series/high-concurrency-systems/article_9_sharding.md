---
title: "Chapter 9: Database Sharding & Read/Write Splitting"
date: 2026-06-09T10:40:00+07:00
lastmod: 2026-06-09T10:40:00+07:00
draft: false
series: ["Mastering High-Concurrency Systems in Production"]
series_order: 9
tags: ["golang", "database", "sharding", "architecture"]
mermaid: true
slug: "database-sharding-read-write-splitting"
description: "Scale your relational database infinitely using GORM dbresolver for Read/Write splitting and Consistent Hashing for massive Sharding."
ShowToc: true
TocOpen: true
---
[← Previous](/series/high-concurrency-systems/distributed-locking-redlock-zookeeper/) | [Series hub](/series/high-concurrency-systems/)

# Chapter 9: Scaling the Final Database Bottleneck

When your application reaches tens of millions of users, the Database becomes the ultimate bottleneck. CPU maxes out at 100%, RAM depletes, and queries take seconds instead of milliseconds. This is the stage where you must deploy distributed database strategies.

## 1. Read/Write Splitting

**Answer-first:** Because 80% of traffic is Read-only, separate your DB into a Write Master and Read Slaves. Use GORM's `dbresolver` plugin to route queries automatically without altering business logic.

In typical applications, Read operations (Select) account for 80-90% of traffic, while Writes (Insert/Update) are merely 10-20%. Cramming all of this into a single DB causes heavy Select queries to lock tables, paralyzing the Write pipeline.

**The Architecture:**
Deploy a **Master** node (strictly for WRITING) alongside multiple **Slave/Replica** nodes (strictly for READING). The Master continuously replicates its data asynchronously to the Slaves.

**Implementing in Golang:**
Do not write messy `if-else` blocks to manually switch DB connections. Utilize the `dbresolver` plugin from GORM:
```go
import "gorm.io/plugin/dbresolver"

db.Use(dbresolver.Register(dbresolver.Config{
    Sources:  []gorm.Dialector{mysql.Open("master_dsn")},
    Replicas: []gorm.Dialector{mysql.Open("slave1_dsn"), mysql.Open("slave2_dsn")},
    Policy:   dbresolver.RandomPolicy{},
}))
```
GORM intelligently parses your code: `db.Create()` is routed to the Master, while `db.Find()` is load-balanced across Slaves. Read scalability is now virtually infinite.

**Replication Lag Warning:**
Because Master-to-Slave replication takes a few milliseconds, if a user updates their profile (Write to Master) and immediately refreshes the page (Read from Slave), they might see old data. *Solution:* Flag the user session upon mutation, forcing all their read requests to target the Master for the next 3 seconds.

## 2. Database Sharding

**Answer-first:** When a single table hits billions of rows, splitting reads isn't enough. Sharding horizontally slices the table across multiple physical servers. Consistent Hashing is the preferred strategy to avoid massive data migrations during cluster resizing.

When data swells to billions of records (e.g., Transaction History), the Master's hard drive fills up, and indexing overhead crushes Write performance. Read/Write splitting becomes useless. You must "slice" the database into smaller fragments.

This is **Sharding**. There are two classic Shard Key strategies:

### A. Range-based Sharding
- Shards by ID or Date: Node 1 stores IDs 1 to 10M; Node 2 stores 10M to 20M.
- **Pros:** Trivial to scale out. Just buy Node 3 when Node 2 is full.
- **Cons:** Hotspotting. New data is always accessed the most, meaning the newest Node is perpetually overloaded while older Nodes sit idle.

### B. Hash-based Sharding
- Utilizes modulo arithmetic: `Hash(User_ID) % Node_Count`.
- **Pros:** Data is distributed flawlessly across all servers. No hotspots.
- **Fatal Flaw:** If you have 3 Nodes, you modulo by 3. If you add a 4th Node, the entire mathematical denominator changes! 99% of your data will now hash to the wrong server, requiring a catastrophic full-system data migration.

### C. Consistent Hashing
To solve the modulo flaw, engineers map the hash output onto a circular ring from $0$ to $2^{32}-1$. Database Nodes are placed at random points on this ring. When a piece of data hashes to a location, it walks clockwise around the ring until it finds the nearest Node.
When a new Server is added, only the tiny fraction of data immediately adjacent to it needs to be migrated. The rest of the cluster is undisturbed!

## 3. Don't Reinvent the Wheel

Do not write raw sharding logic in Golang. Adopt system-level middleware designed for distributed databases like **TiDB**, **ShardingSphere**, or **Vitess** (used by Slack and YouTube). Your Go application connects to Vitess exactly as if it were a standard MySQL database, but behind the scenes, Vitess intelligently routes the query across dozens of backend shards.

*(This concludes our Mastering High-Concurrency Series. May your Go systems stand unbreakable against the fiercest traffic storms!)*
