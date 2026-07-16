---
title: "Shopee DB: MySQL Sharding to TiDB NewSQL Migration"
slug: "04-database-scale"
date: "2026-05-05T08:40:00+07:00"
lastmod: "2026-06-11T20:00:00+07:00"
draft: false
mermaid: true
description: "How Shopee scaled from MySQL sharding to TiDB NewSQL: ProxySQL connection pooling, read replica architecture, and TiDB migration for 100M+ users."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/shopee-flash-sale-cover.png"
  alt: "Shopee Architecture series: scaling for flash sales — rate limiting, Redis, and distributed systems"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/shopee-architecture/04-database-scale/"
---
# Chapter 4: Database Scale - The Rise of TiDB and NewSQL

**To scale beyond MySQL sharding limitations, Shopee migrated to TiDB—a NewSQL database that provides infinite horizontal scalability by decoupling compute from storage, eliminating the need for manual sharding and distributed transaction logic.**

[← Series hub]({{< ref "/series/shopee-architecture/_index.md" >}}) | [← Prev]({{< ref "/series/shopee-architecture/03-traffic-shield.md" >}}) | [Next →]({{< ref "/series/shopee-architecture/05-observability.md" >}})

> **Prerequisite:** Before reading this chapter, please ensure you have read the previous article in this series: [Chapter 3: Traffic Shield - Peak Shaving with Kafka and Graceful Degradation]({{< ref "03-traffic-shield.md" >}}).

No matter how many layers of Cache or Message Queues you have, the final destination of all transactional data is the Database (the Source of Truth). With tens of millions of daily orders and billions of records, traditional RDBMS like standalone MySQL quickly hit dangerous bottlenecks. The B+Tree index grows too deep, and Disk IOPS reach their physical ceiling.

---

## 1. How to Scale MySQL? The Nightmare of Sharding

**Manual database sharding solves write scaling but creates severe engineering nightmares: scatter-gather query latency for non-shard keys (e.g., Seller views) and highly complex distributed transactions (2PC) across physical databases.**

Historically, to scale out MySQL, Shopee (and other tech giants) utilized **Database Sharding**.
An enormous `Orders` table would be chopped into hundreds of physical databases. For example, using a hashing algorithm on `user_id` (`user_id % 100`) to route orders into Shard 0 through 99.

### Sharding Proxies: ProxySQL vs. Vitess

To manage connection pooling and routing to these shards, systems rely on database proxies. However, the architecture of these proxies differs significantly:
1. **ProxySQL:** A high-performance, SQL-aware proxy. It is excellent for **Read/Write splitting** (routing writes to master, reads to replicas), query caching, and connection pooling. However, ProxySQL does not native abstract a sharded database: the application code must still be aware of which query belongs to which shard key, or complex regex rules must be written to route queries.
2. **Vitess:** A database clustering system for horizontal scaling of MySQL. Originally built by YouTube, Vitess uses a proxy layer (`VTGate`) to intercept queries, analyze the schema, and automatically route queries to the correct MySQL shard (`VTTablet`). It abstracts the sharding completely, presenting the application with what looks like a single giant database instance, while managing the underlying physical MySQL instances.

---

## 2. The NewSQL Solution: TiDB

**TiDB acts as a drop-in MySQL replacement that scales infinitely. It separates stateless SQL compute nodes from distributed TiKV storage nodes, utilizing the Raft consensus algorithm to auto-shard and rebalance data without manual intervention.**

To eliminate the massive engineering overhead of manual sharding, Shopee heavily migrated its core systems to **TiDB**—an open-source NewSQL database. It offers the infinite horizontal scalability of NoSQL while maintaining the strict ACID guarantees and SQL compatibility of Relational databases.

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

### Percolator Distributed Transactions (2PC)

TiDB implements distributed ACID transactions using a decentralized commit protocol based on Google's **Percolator** model. It eliminates the single bottleneck of a central lock manager by storing transaction lock details directly inside the Key-Value records.

The Percolator 2-Phase Commit (2PC) works as follows:
1. **Prewrite Phase:** The transaction client chooses a "Primary Key". It then sends write commands to all relevant TiKV nodes. Each TiKV node writes the data along with a lock. The locks on secondary keys contain a pointer back to the Primary key's lock.
2. **Commit Phase:** If all prewrites succeed, the client requests a commit timestamp from the Placement Driver (PD) and commits the Primary Key by clearing its lock and writing a commit record. Once the Primary key is committed, the transaction is officially successful.
3. **Asynchronous Commit Rollout:** The secondary keys are committed asynchronously by removing their locks and writing commit records. If a concurrent reader encounters a lock on a secondary key, it follows the pointer to the Primary key to check if the transaction committed.

Here is a Go simulation of the Percolator 2PC commit protocol:

```go
package percolator

import (
	"errors"
	"sync"
)

var (
	ErrLockConflict = errors.New("lock conflict detected")
	ErrTxnAborted   = errors.New("transaction aborted due to write conflict")
)

type Row struct {
	Key      string
	Val      string
	StartTS  uint64
	CommitTS uint64
	Lock     *Lock
}

type Lock struct {
	PrimaryRow *Row
	StartTS    uint64
}

type Storage struct {
	mu   sync.Mutex
	data map[string]*Row
}

func NewStorage() *Storage {
	return &Storage{data: make(map[string]*Row)}
}

type Txn struct {
	storage  *Storage
	startTS  uint64
	writes   map[string]string
	primary  string
}

func NewTxn(s *Storage, startTS uint64) *Txn {
	return &Txn{
		storage: s,
		startTS: startTS,
		writes:  make(map[string]string),
	}
}

func (t *Txn) Write(key, val string) {
	t.writes[key] = val
	if t.primary == "" {
		t.primary = key
	}
}

// Commit attempts to commit the transaction using Percolator 2PC protocol.
func (t *Txn) Commit(commitTS uint64) error {
	t.storage.mu.Lock()
	defer t.storage.mu.Unlock()

	// 1. Prewrite Phase: Write locks and data buffers
	primaryRow := &Row{Key: t.primary, Val: t.writes[t.primary], StartTS: t.startTS}
	for key, val := range t.writes {
		curr, exists := t.storage.data[key]
		if exists && curr.Lock != nil {
			return ErrLockConflict
		}
		if exists && curr.CommitTS > t.startTS {
			return ErrTxnAborted
		}

		// Place lock pointing back to primary
		t.storage.data[key] = &Row{
			Key:     key,
			Val:     val,
			StartTS: t.startTS,
			Lock: &Lock{
				PrimaryRow: primaryRow,
				StartTS:    t.startTS,
			},
		}
	}

	// 2. Commit Phase: Commit the Primary lock key first
	primaryState := t.storage.data[t.primary]
	if primaryState == nil || primaryState.Lock == nil {
		return ErrTxnAborted
	}
	primaryState.CommitTS = commitTS
	primaryState.Lock = nil // Lock released on primary

	// 3. Secondary Keys Commit: Done asynchronously
	for key := range t.writes {
		if key != t.primary {
			row := t.storage.data[key]
			if row != nil {
				row.CommitTS = commitTS
				row.Lock = nil // Release secondary locks
			}
		}
	}

	return nil
}
```

### Placement Driver (PD) Region Balance Algorithms

The **Placement Driver (PD)** is the coordinator of the TiDB cluster. It allocates global timestamps, stores region metadata, and balances the workload across nodes. 

PD dynamically rebalances data using **Raft Region Balance Algorithms**:
- **Leader Balancing:** PD monitors heartbeats from all TiKV nodes. If it detects a node is running too many Raft leaders (which handle read/write traffic), it issues a scheduling command to transfer leader status (`TransferLeader`) to a replica on a less loaded TiKV node.
- **Peer/Capacity Balancing:** If a TiKV node is low on disk space, PD schedules a region migration. It creates a new follower replica on an idle TiKV node, adds it to the region's Raft peer list, allows it to sync, and then drops the replica on the overloaded node.

---

## 3. HTAP (Hybrid Transactional and Analytical Processing)

**TiFlash enables real-time analytics on live transactional data. It automatically replicates row-based TiKV data into columnar storage using Raft, allowing Shopee to run heavy analytical queries during a flash sale without degrading checkout performance.**

A massive advantage of the TiDB ecosystem is **TiFlash**.
Normally, you would need complex overnight ETL pipelines to extract data from an OLTP database (MySQL) into a Data Warehouse (like Hadoop or Snowflake) for business reporting. Instead, TiFlash automatically replicates data from TiKV (Row-based format) into a Column-based format in real-time. This is highly beneficial for use cases like [real-time inventory synchronization]({{< ref "/series/ecommerce-order-allocation/part-2-inventory-realtime.md" >}}) across distributed systems.

This allows Shopee's operation teams to run massive `SELECT ... GROUP BY` analytics queries across billions of Flash Sale records instantly, without causing any lag to the live transactional checkout flow of users.

---

## Summary and Developer Takeaways

Do not try to "reinvent the wheel" by writing manual database sharding code at the application level unless you have an army of DBAs. NewSQL solutions like TiDB or CockroachDB are the future for transparently handling Big Data at an extreme scale.

*Struggling to scale your database layer or migrate to NewSQL? [Hire me](/hire/) to architect your distributed database and sharding strategy.*

🔗 **Next Step:** Running a massive database and microservice architecture is impossible without eyes on the system. Learn how Shopee monitors its distributed platform in [Chapter 5: Observability - Finding Bugs in the Microservices Jungle]({{< ref "05-observability.md" >}}).

---

## References & Further Reading

- [PingCAP Case Study: How Shopee scales its Database with TiDB](https://www.pingcap.com/case-studies/shopee-scales-its-database-with-tidb/)
- [TiDB HTAP Architecture and TiFlash](https://www.pingcap.com/blog/htap-database-what-is-it-and-why-you-need-it/)

🔗 **Deep Dive:** For a comprehensive engineering analysis of the complete spectrum from MySQL replication to sharding to TiDB, including distributed ACID transactions and MVCC internals, read our standalone guide: [Scalable Database Architecture: How to Scale MySQL from Replication to Sharding and TiDB](/posts/mysql-scaling-sharding-tidb-architecture/).

🔗 **Scalability Decision Framework:** If you are evaluating whether replicas, GORM Sharding, Vitess, or TiDB is the right choice for your current stage, the [MySQL Scalability Guide](/posts/mysql-scalability-guide/) covers the complete decision ladder with Go-specific implementation patterns.

{{< author-cta >}}
