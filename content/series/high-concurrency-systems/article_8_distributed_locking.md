---
title: "Chapter 8: Distributed Locking for Race Conditions: Redlock vs ZooKeeper"
date: 2026-06-09T10:35:00+07:00
lastmod: 2026-06-09T10:35:00+07:00
draft: false
series: ["Mastering High-Concurrency Systems in Production"]
series_order: 8
tags: ["golang", "distributed lock", "redis", "redlock", "zookeeper"]
mermaid: true
slug: "distributed-locking-redlock-zookeeper"
description: "Master distributed synchronization by comparing Redis Redlock algorithms against strongly consistent Apache ZooKeeper locks."
ShowToc: true
TocOpen: true
aliases:
  - "/series/high-concurrency-systems/part-1-pessimistic-locks/"
  - "/series/high-concurrency-systems/part-2-optimistic-locks/"
---
[← Previous](/series/high-concurrency-systems/idempotency-api-design-payments/) | [Series hub](/series/high-concurrency-systems/) | [Next →](/series/high-concurrency-systems/database-sharding-read-write-splitting/)

# Chapter 8: Synchronizing Clusters with Distributed Locks

In a standalone Go application, preventing two Goroutines from overwriting the same data (Race Condition) is achieved via `sync.Mutex`. However, when your system scales out to 10 servers behind a Load Balancer, `sync.Mutex` is useless because it only locks local RAM. You need a **Distributed Lock**.

## 1. Basic Redis Locks

**Answer-first:** A basic Redis lock utilizes `SET resource id NX PX ttl`. It works for simple caching but suffers from Single Point of Failure vulnerabilities if the Redis Master crashes before syncing.

The simplest distributed lock uses a single Redis node with an atomic command:
`SET resource_name my_unique_id NX PX 30000`

- `NX`: Ensures only the first requester succeeds (acquires the lock).
- `PX 30000`: The lock auto-expires after 30 seconds (Lease Expiration) preventing Deadlocks if the lock-holding server crashes.

**The Flaw:** What if this Redis node crashes right after granting the lock to Server A, but before replicating to the Slave? The Slave promotes itself to Master without knowing Server A holds the lock. Server B requests a lock, and the new Master grants it. Two servers now hold the lock simultaneously $\to$ Data corruption.

## 2. The Redlock Algorithm

**Answer-first:** Redlock eliminates Redis Single Point of Failure by querying multiple independent Redis Masters. A lock is only acquired if a quorum (majority) of nodes grant it successfully.

To resolve Redis replication flaws, Salvatore Sanfilippo (creator of Redis) introduced the **Redlock** algorithm.

Redlock utilizes a cluster of $N$ (usually 5) independent Redis Masters. 
To acquire a lock, your Go Server must:
1. Sequentially request the lock on all 5 nodes.
2. If it successfully acquires the lock on a majority (**Quorum**: $\ge 3/5$ nodes) within a specified time limit, the lock is officially granted.
3. If it fails the quorum, it must rapidly delete the lock from all nodes.

In Golang, you can easily implement this using the `github.com/go-redsync/redsync` library. It is exceptionally fast and highly suitable for Microservices and Caching.

## 3. ZooKeeper / etcd Locks: The Performance Trade-off

**Answer-first:** While Redlock is fast, it is vulnerable to Clock Drift. Financial systems requiring absolute Strong Consistency use Apache ZooKeeper or etcd for reliable, event-driven locking.

Despite Redlock's popularity, distributed systems experts (like Martin Kleppmann) note its heavy reliance on synchronized physical clocks. If a server experiences Clock Drift, locks can expire unpredictably.

For Core Banking systems demanding absolute Strong Consistency, engineers deploy **Apache ZooKeeper** or **etcd**.

- **Mechanism:** ZK utilizes a directory structure. A Go server creates an Ephemeral Sequential Node. If its sequence number is the lowest, it holds the lock. If not, it registers a `Watch` event on the preceding node. When the preceding node finishes and deletes itself, ZK fires an event notifying the Go server.
- **Pros:** Extremely robust locking based on the ZAB/Raft consensus protocol. It eliminates CPU-wasting Polling loops because it is event-driven.
- **Cons:** Significantly slower than Redis, and maintaining a ZK cluster is operationally complex.

## 4. The Hidden Threat: Garbage Collection (GC) Lock Loss

**Answer-first:** Long Garbage Collection pauses can cause a lock to expire while a thread is still processing. Use a background Watchdog Goroutine to continually renew the lock's TTL while work is ongoing.

A rarely discussed vulnerability: Suppose your Redis lock has a 10-second TTL. Your Goroutine acquires it and processes data for 2 seconds. Suddenly, Golang triggers a massive Garbage Collection sweep (or OS CPU starvation) lasting 9 seconds.

By the time the pause ends, the Redis lock has expired, and Redis grants it to a new Goroutine. The original Goroutine awakens, completely unaware it lost the lock, and overwrites the DB, causing a catastrophe!

**The Defense:** Implement a **Watchdog** mechanism. A background Goroutine continuously monitors the processing thread. If the work is incomplete and the lock is nearing expiration, the Watchdog sends a command to renew (extend) the TTL in Redis automatically.
