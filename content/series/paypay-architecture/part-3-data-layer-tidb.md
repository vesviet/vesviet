---
title: "Part 3 — The Data Layer: From Aurora to TiDB"
date: 2026-05-05T21:00:00+07:00
draft: false
description: "Why PayPay migrated from AWS Aurora to TiDB to achieve horizontal scalability."
weight: 4
---

## The Relational Database Bottleneck

Initially, PayPay relied on **AWS Aurora (MySQL)** for its core transactional data (ledgers, user balances). Aurora is fantastic, but it is fundamentally a traditional RDBMS. You can scale reads easily (by adding Read Replicas), but **all Writes must go through a single Primary Node**.

As PayPay grew to tens of millions of users, the Write TPS during campaigns began hitting the physical limits of the largest available Aurora instance (Vertical Scaling limits). 

### Traditional Solutions (And Why They Failed)
- **Manual Sharding:** Splitting the database by User ID (e.g., Users 1-1M on DB A, 1M-2M on DB B). This creates massive operational overhead, complex routing logic in the application, and makes cross-shard transactions (like User A transferring money to User B) a nightmare.
- **NoSQL (DynamoDB/Cassandra):** While horizontally scalable, NoSQL databases often lack strong ACID transactions and complex JOIN capabilities, which are absolute requirements for a financial ledger.

## The Move to TiDB (NewSQL)

PayPay's solution was to adopt **TiDB**, an open-source, distributed SQL database built by PingCAP.

### What is TiDB?
TiDB offers the best of both worlds:
1. **Horizontal Scalability of NoSQL:** You can add more nodes to scale Writes and Storage infinitely.
2. **ACID Guarantees of RDBMS:** It supports distributed transactions and speaks the MySQL protocol.

### How PayPay uses it:
By migrating the heaviest write-intensive domains (like the Payment Ledger) to TiDB, PayPay eliminated the single-node write bottleneck. 
- The application still writes standard SQL queries (as if talking to MySQL).
- TiDB seamlessly distributes the data and the queries across a cluster of state nodes (TiKV).

When a massive campaign is planned, the Platform team simply provisions more TiDB nodes to handle the write load, and scales them down afterward. This transition was a critical milestone in making the PayPay architecture truly planet-scale.
