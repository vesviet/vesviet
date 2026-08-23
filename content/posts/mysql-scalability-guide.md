---
title: "MySQL Scalability & Sharding: Vitess vs TiDB (10k+ TPS)"
slug: "mysql-scalability-guide"
author: "Lê Tuấn Anh"
date: "2026-06-10T14:30:00+07:00"
lastmod: "2026-08-23T08:30:00+07:00"
draft: false
description: "Comprehensive guide to scaling MySQL: InnoDB buffer pool tuning, ProxySQL pooling, Vitess middleware sharding, and zero-downtime TiDB NewSQL migration."
ShowToc: true
TocOpen: true
categories:
  - "Database"
  - "Architecture"
  - "Engineering"
tags:
  - "MySQL"
  - "Database Scaling"
  - "TiDB"
  - "Vitess"
  - "ProxySQL"
  - "GORM"
  - "Golang"
cover:
  image: "/images/posts/mysql-scalability-cover.jpg"
  alt: "MySQL Scalability & Sharding Alternatives: read replicas, Vitess, and TiDB NewSQL"
  relative: false
canonicalURL: "https://tanhdev.com/posts/mysql-scalability-guide/"
---

# MySQL Scalability & Sharding: Vitess vs TiDB (10k+ TPS)

> **Answer-first:** Scaling MySQL for high-traffic applications involves a phased progression: tuning InnoDB buffer pools and slow queries (0–500 TPS), offloading reads via ProxySQL and read replicas (500–3,000 TPS), and adopting horizontal write scaling (3,000+ TPS) via Vitess sharding or TiDB Distributed SQL to maintain sub-50ms P99 query latencies.

MySQL scalability is the ability to increase database throughput — reads per second, writes per second, or data volume — without rewriting your application. The critical distinction: **read scaling** (adding replicas) and **write scaling** (sharding or distributed SQL) require completely different architectural approaches. Choosing the wrong path creates technical debt that takes months to unwind.

This guide walks through every stage of the MySQL scaling ladder — InnoDB buffer pool tuning, ProxySQL pooling, async read replicas, Vitess/GORM sharding for write-heavy data, and TiDB migration — with Go-specific implementation patterns at each step.

---

## MySQL Scalability Patterns: Read Replicas vs. Sharding

Read replicas handle high-volume SELECT workloads, but expanding write capacity requires partitioning data or adopting distributed NewSQL engines to eliminate single-node bottlenecks.

**MySQL scalability is the ability to handle increased data volume and transaction throughput without performance degradation. For a production e-commerce platform, this means keeping p95 database query latency under 50ms as traffic scales from 1,000 to 10,000 requests per second.**


The four-phase performance envelope for a dedicated MySQL server:

| Phase | TPS Range | Primary Lever |
|-------|-----------|---------------|
| 1 — Baseline | 100–500 TPS | InnoDB buffer pool (70–80% RAM) |
| 2 — Query tuning | 500–1,500 TPS | Index optimization, schema design |
| 3 — Connection pooling | 1,500–3,000 TPS | ProxySQL, MySQL Router |
| 4 — Horizontal | 6,000–10,000+ TPS | Read replicas, sharding |

Buffer pool can be resized at runtime without a restart in MySQL 8.0+:

```sql
-- Resize buffer pool without restarting (MySQL 8.0+)
SET GLOBAL innodb_buffer_pool_size = 8 * 1024 * 1024 * 1024; -- 8 GB
```

Check buffer pool hit rate by comparing read requests to disk reads:

```sql
-- Buffer pool hit rate diagnostic
SELECT
  (1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)) * 100
  AS hit_rate_pct
FROM information_schema.GLOBAL_STATUS
WHERE Variable_name IN ('Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests');
```

If hit rate is below 95%, add RAM before reaching for replicas.

---

## When Does MySQL Need to Scale?

**Scale MySQL when CPU utilization consistently exceeds 70%, connection pools max out, or InnoDB buffer pool cache hit rates drop below 95%. In e-commerce, this typically happens during flash sales when cart and inventory writes cause severe table lock contention.**


### Signal 1: Buffer Pool Exhaustion

The first sign is usually a drop in buffer pool hit rate combined with rising disk I/O. At this stage, upgrading RAM is cheaper than adding replicas.

**Before doing anything else**, audit your slowest queries:

```bash
# Run pt-query-digest on a SECONDARY machine, never on production
pt-query-digest /var/log/mysql/slow.log > analysis_report.txt
```

Key output columns to prioritize:
- **Exec Time** (total) — largest value = biggest optimization opportunity
- **Rows Examine / Rows Sent ratio** — 1,000,000 examined / 1 sent = missing index
- **Lock Time** — high values signal transaction contention, not missing indexes

To identify high-latency statements on live servers, query performance schema:

```sql
-- Find queries in the P95 execution time range
SELECT digest_text, count_star, avg_timer_wait/1000000000 AS avg_ms
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_timer_wait DESC
LIMIT 20;
```

### Signal 2: Replication Lag

Legacy Seconds_Behind_Source metrics are inaccurate for multi-threaded replication setups. Performance schema tables track precise replication lag across individual worker threads:

```sql
-- Accurate lag per worker thread
SELECT
  WORKER_ID,
  LAST_APPLIED_TRANSACTION,
  TIMESTAMPDIFF(
    SECOND,
    LAST_APPLIED_TRANSACTION_ORIGINAL_COMMIT_TIMESTAMP,
    NOW()
  ) AS lag_seconds
FROM performance_schema.replication_applier_status_by_worker
WHERE SERVICE_STATE = 'ON'
ORDER BY lag_seconds DESC;
```

> ⚠️ **Check `SERVICE_STATE = 'ON'`** — if a worker thread is stopped, its lag metric is frozen. You will see zero lag while replication has actually halted.

### Signal 3: EXPLAIN Shows Full Table Scans

Before adding replicas, inspect query execution plans for unindexed full table scans:

```sql
-- Check before any scaling decision
EXPLAIN SELECT * FROM orders WHERE customer_id = 12345;
```

EXPLAIN `type` hierarchy: `const` > `eq_ref` > `ref` > `range` > **`ALL`** (full scan — address immediately). Adding sharding on top of a full-table-scan workload multiplies the problem across every shard.

Also check if `ALGORITHM=INSTANT` can handle your schema change before scheduling a maintenance window:

```sql
-- Many 8.0+ column additions require zero rebuild
ALTER TABLE orders ADD COLUMN coupon_code VARCHAR(64), ALGORITHM=INSTANT;
```

---

## Stage 1 — Read Scaling with MySQL Replicas

**Stage 1 scales read operations by deploying asynchronous MySQL read replicas. A Go microservice routes SELECT queries to replicas via connection pooling, while INSERT and UPDATE operations target the primary master node to ensure transactional consistency.**


### WRITESET vs. LOGICAL_CLOCK — The Parallel Replication Setting No One Explains

MySQL 8.4 LTS (released April 30, 2024) defaults to **WRITESET** parallel replication. Here is what that actually means:

- **LOGICAL_CLOCK** schedules transactions based on when they committed on the primary (group-commit timestamps). Parallelism is limited by how many transactions committed simultaneously.
- **WRITESET** hashes the primary key of every modified row using XXHASH64 and compares the hashes. If two transactions touch different rows, they run in parallel on the replica — regardless of commit order.

**The critical gotcha:** WRITESET silently falls back to serial replication for any table without a `PRIMARY KEY` or `UNIQUE KEY`. Tables that look fine on the primary become replication bottlenecks. Audit before enabling:

```sql
-- Find tables without a primary key (silent WRITESET killers)
SELECT TABLE_SCHEMA, TABLE_NAME
FROM information_schema.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_SCHEMA NOT IN ('information_schema','mysql','performance_schema','sys')
  AND TABLE_NAME NOT IN (
    SELECT TABLE_NAME FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_TYPE IN ('PRIMARY KEY','UNIQUE')
  );
```

Configure WRITESET dependency tracking on the primary and parallel workers on replicas:

```sql
-- On the primary
SET GLOBAL binlog_format = 'ROW';
SET GLOBAL binlog_transaction_dependency_tracking = 'WRITESET';
SET GLOBAL transaction_write_set_extraction = 'XXHASH64';
-- On replicas
SET GLOBAL replica_parallel_workers = 8; -- match vCPU count
SET GLOBAL replica_preserve_commit_order = ON;
```

### Go Connection Pool Sizing

For a Go service connecting to a ProxySQL front-end (recommended), size the pool using the HikariCP formula applied to your **database server's** core count — not the app server:

```
pool_size = (DB_core_count × 2) + effective_spindle_count
```

For an 8-core DB server with NVMe (1 effective spindle): `(8 × 2) + 1 = 17` connections.

For traffic-based sizing, apply Little's Law:

```
Required Connections = RPS × Average Query Latency (seconds)
```

Example: 500 RPS × 0.05s (50ms avg) = **25 connections** + 25% buffer = 32.

```go
// Production Go connection pool — database/sql
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(25)           // Equal to MaxOpenConns to avoid reconnect overhead
db.SetConnMaxLifetime(5 * time.Minute) // Recycle before DB-side timeout fires
```

Monitor `db.Stats().WaitCount` — if non-zero, increase the pool.

### ProxySQL Read/Write Split — The One Setting Teams Get Wrong

ProxySQL routes reads to replicas and writes to the primary. The critical setting most teams miss:

```sql
-- In ProxySQL admin console
-- Prevents reads in a transaction from hitting a replica
UPDATE mysql_users SET transaction_persistent = 1 WHERE username = 'app_user';
LOAD MYSQL USERS TO RUNTIME;
SAVE MYSQL USERS TO DISK;
```

Without `transaction_persistent = 1`, a `SELECT` inside an open transaction can route to a replica, reading stale data written moments earlier by the same transaction. This causes subtle race conditions in checkout flows and payment processing.

> 💡 **Read-after-write pattern without ProxySQL:** Use two separate `*sql.DB` pools (primary and replica). After a write, set a short TTL flag in Redis — for that duration, route reads for that user session to the primary pool.

---

## Stage 2 — Write Scaling with MySQL Sharding

**Stage 2 scales write operations by sharding the MySQL database horizontally across multiple servers. Data is partitioned using a sharding key (like user_id), meaning no single database instance holds the entire dataset, removing write bottlenecks.**


### The 4 Shard Key Selection Failures

| Failure | Example | Result |
|---------|---------|--------|
| Low cardinality | `country_code`, `status` | Few shards, imbalanced load |
| Monotonic sequence | `AUTO_INCREMENT`, timestamp | All new writes → same shard (hotspot) |
| Celebrity skew | `user_id` for a high-traffic account | One shard overwhelmed |
| Missing in WHERE | Shard on `tenant_id`, query on `email` | Scatter-gather across all shards |

### Partitioning vs. Sharding — The Most Confused Distinction

| | InnoDB Partitioning | Sharding |
|--|--------------------|---------  |
| Scope | **Same server** | Multiple servers |
| App changes | None (transparent) | Routing logic required |
| Solves | Maintenance, query pruning | Write throughput, storage ceiling |
| DROP old data | Instant (`ALTER TABLE ... DROP PARTITION`) | Complex shard-by-shard migration |

**InnoDB partitioning does NOT scale hardware limits.** It is a maintenance tool. Use it for time-series tables where you need instant data archival:

```sql
-- Orders partitioned by month — DROP PARTITION is instant
CREATE TABLE orders (
  id BIGINT NOT NULL,
  created_at DATE NOT NULL,
  PRIMARY KEY (id, created_at)  -- partition column MUST be in every unique key
) PARTITION BY RANGE COLUMNS(created_at) (
  PARTITION p_2026_01 VALUES LESS THAN ('2026-02-01'),
  PARTITION p_2026_02 VALUES LESS THAN ('2026-03-01'),
  PARTITION p_future  VALUES LESS THAN MAXVALUE
);
```

> ⚠️ **InnoDB partitioned tables do NOT support FOREIGN KEY constraints.** If your schema uses FKs, you must drop them before adding partitioning, or manage referential integrity at the application layer.

### GORM Sharding (Application-Level, Zero Infrastructure)

GORM Sharding intercepts SQL inside the application process, replaces the table name based on the shard key, and routes to the correct physical table. Zero network hops, zero extra infrastructure.

For full implementation details and the common `ErrMissingShardingKey` pitfall, see the companion post: [Vitess vs GORM Sharding: MySQL Write Scaling with Go](/posts/mysql-horizontal-scaling/).

### Vitess — Middleware Sharding for Large Scale

Vitess routes queries through `VTGate` → `VTablet` → physical MySQL shard. The VSchema defines the Primary Vindex (sharding key). Resharding is managed via `VReplication` — a production-safe streaming migration that keeps both old and new shards in sync during the cutover.

Vitess 24 (April 2026) added a `--shards` flag for `MoveTables` and `Reshard`, allowing you to migrate specific shard subsets rather than the entire keyspace.

**PlanetScale** is managed Vitess — it removed its free tier in early 2024.

### Zero-Downtime Schema Migration on Large Tables

Before reaching for sharding, many teams discover the schema migration problem. `ALTER TABLE` on a 1B-row table can take days. Two tools solve this:

| | gh-ost | pt-osc |
|--|--------|--------|
| Mechanism | Binlog-based (no triggers) | DML triggers |
| FK support | **No** | Yes |
| Pause/resume | Yes (Unix socket) | No |
| Overhead | Low (decoupled from writes) | Higher (trigger per-write overhead) |

gh-ost is preferred for high-write tables. But check `ALGORITHM=INSTANT` first — many MySQL 8.0+ column additions are instant and require neither tool.

> 🔥 **[Production Failure]: The Maintenance Event Horizon**
> **Symptom:** Adding a nullable column to the `events` table caused a 6-hour replication lag spike across all 12 replicas.
> **Root Cause:** The `ALTER TABLE` on a 400M-row table triggered a full table rebuild. Because it used `ALGORITHM=COPY` (not `ALGORITHM=INSTANT`), every replica had to re-apply every row write during the rebuild window.
> **Impact:** Read traffic degraded to primary-only for 6 hours; primary CPU reached 95%.
> **Resolution:** Roll back, wait for replicas to catch up, then re-apply with `ALGORITHM=INPLACE, LOCK=NONE` after verifying the column type supported online DDL.
> **Lesson:** Run `EXPLAIN ALTER TABLE` (MySQL 8.0.27+) to verify the algorithm before executing on production.

---

## The Maintenance Event Horizon — Why Teams Actually Migrate

Crossing the maintenance event horizon marks the operational threshold where traditional single-node MySQL administration becomes unviable for enterprise engineering teams. When online DDL schema changes take days to complete, cross-shard query fan-out impairs application latency, and manual re-sharding overhead delays feature releases, migrating toward distributed SQL becomes necessary.

**The maintenance event horizon occurs when schema migrations on a multi-terabyte MySQL table take longer than the allowable downtime window. Teams often migrate away from single-node MySQL when tools like pt-online-schema-change begin failing under high production load.**


The operational cost compounds with each shard:

- Schema change on 8 shards × 4-hour `ALTER TABLE` = 32 engineering-hours per release
- Cross-shard join queries require application-level fan-out
- Rebalancing a hot shard requires a custom VReplication workflow or downtime
- A `DELETE ... WHERE date < X` on 1B rows runs for hours; `ALTER TABLE ... DROP PARTITION p_old` is instant

When this overhead starts delaying feature shipping, the economics of a distributed SQL migration begin to make sense.

---

## Stage 3 — MySQL Sharding Alternative: TiDB

Adopting TiDB as a distributed NewSQL alternative eliminates the operational complexity of manual application-level MySQL sharding. By decoupling stateless SQL compute nodes from distributed TiKV storage engines, TiDB delivers transparent horizontal scaling, automatic region rebalancing, and millisecond DDL execution while maintaining complete wire-protocol compatibility with existing MySQL applications.

**TiDB is a distributed, NewSQL database that provides MySQL compatibility with transparent horizontal scaling. It eliminates the need for manual application-level sharding by separating the stateless SQL compute layer from the distributed TiKV storage engine.**


For TiDB architecture (TiKV, Raft consensus, Percolator ACID, TiFlash HTAP), see the detailed architectural guide: [Replace MySQL Sharding with TiDB: Distributed SQL Migration Guide](/posts/mysql-scaling-sharding-tidb-architecture/).

### What Changed in TiDB 8.5 (December 2024)

TiDB 8.5 LTS (released December 19, 2024, latest patch v8.5.6 in April 2026) introduced a DDL optimization that changes the migration calculus:

**Lossy DDL speedup (v8.5.5+):** When a schema change like `BIGINT → INT` or `CHAR(255) → VARCHAR(128)` results in no data truncation, TiDB executes it in **milliseconds instead of hours** — a 460,000x improvement on tables with hundreds of millions of rows.

This means schema migrations that blocked MySQL shard migrations for months are now effectively free on TiDB.

Other 8.5 improvements:
- P999 tail latency: reduced from tens of seconds → sub-100ms (GC pause optimization)
- TiKV average CPU usage: 10–25% reduction
- Slow-query burst frequency: 30–90% reduction

### TiDB Migration — The PK Conflict Problem

The #1 blocker when merging `AUTO_INCREMENT` shards into TiDB: each shard generates its own ID sequence independently, so IDs collide.

Three resolution strategies:

**Option 1 (preferred): Migrate to UUID**
```sql
-- TiDB: store UUID efficiently as BINARY(16)
CREATE TABLE orders (
  id BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID())),
  PRIMARY KEY (id)
);
```

**Option 2: Remove PK, add composite unique key**
```yaml
# TiDB DM task.yaml
ignore-checking-items:
  - "auto_increment_ID"
```
Then reconstruct uniqueness via `(shard_id, original_id)` composite key.

**Option 3: Composite primary key**
```sql
-- Downstream TiDB table
PRIMARY KEY (shard_id TINYINT, original_id BIGINT)
```

After migration, validate consistency:
```bash
# TiDB sync-diff-inspector — compares source shards to TiDB downstream
sync-diff-inspector --config=diff-config.toml
```

> ⚠️ **DM Safe Mode risk:** If you remove the PRIMARY KEY to bypass the conflict check, DM's Safe Mode (which uses `REPLACE INTO`) may silently overwrite rows without a uniqueness guarantee. Always reconstruct a unique constraint after removing the original PK.

---

## MySQL Scalability Decision Framework

| Dimension | Read Replicas | ProxySQL R/W Split | GORM Sharding | Vitess | TiDB |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Solves | Read throughput | Read throughput | Write (table-level) | Write (cluster) | Write + Storage |
| App changes | Medium | **None** | Medium | **None** | **None** |
| Infra cost | Low | Low | **Zero** | Medium | High |
| ACID across nodes | N/A | N/A | No | No | **Yes** |
| HTAP/Analytics | No | No | No | No | **Yes** (TiFlash) |
| Online resharding | N/A | N/A | Manual | VReplication | **Automatic** |
| Best for | Read-heavy apps | General MySQL | Go services, moderate scale | Large-scale MySQL | Beyond sharding |

### Cloud Hosting Considerations

If self-managing MySQL at scale, Aurora MySQL is worth evaluating:
- Up to 5x MySQL throughput via specialized storage layer
- Up to 15 read replicas with <10ms replica lag
- Sub-10-second automatic failover (Multi-AZ)

**Aurora I/O cost warning:** In high-traffic environments, Aurora per-I/O charges can spike significantly. Switch to the I/O-Optimized tier (fixed rate, no per-I/O billing) if your read/write ratio is high.

---

## Advanced MySQL Concurrency Patterns for Go Services

Building high-concurrency Go microservices against MySQL databases requires implementing resilient connection pooling, transaction retry logic, and row-level locking patterns. Utilizing SKIP LOCKED for distributed task queues and intercepting MySQL deadlock error codes with exponential backoff retries ensures high throughput without exhausting database server process resources.

**Go microservices optimize MySQL concurrency by strictly configuring `SetMaxOpenConns` to prevent connection exhaustion and using `SELECT ... FOR UPDATE` row-level locks combined with transaction timeouts to safely handle high-frequency e-commerce inventory deductions.**

### SKIP LOCKED for Distributed Job Queues

Instead of introducing separate queue middleware, high-concurrency systems use native MySQL row locking for worker allocation. High-throughput job queues utilize FOR UPDATE SKIP LOCKED to allow concurrent workers to reserve unassigned tasks without lock contention:

```sql
-- Worker picks the next available job without blocking other workers
START TRANSACTION;

SELECT id, payload FROM job_queue
WHERE status = 'pending'
ORDER BY created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;  -- skips rows locked by other workers

-- Process job, then update
UPDATE job_queue SET status = 'processing' WHERE id = ?;
COMMIT;
```

`SKIP LOCKED` is non-deterministic — each worker gets a different available row. Requires an index on `(status, created_at)`. *(For a broader discussion on handling database locks under high load without deadlocks, explore our [High Concurrency Systems](/series/high-concurrency-systems/) masterclass).*

### Go Deadlock Retry Pattern

InnoDB automatically resolves deadlock cycles (MySQL error `1213`) by rolling back the transaction with smaller write volume. Transaction wrappers in Go intercept deadlock error codes and execute retries with exponential backoff and randomized jitter:

```go
// Retry transaction on deadlock (MySQL error 1213)
func runWithRetry(db *sql.DB, fn func(*sql.Tx) error) error {
    for attempt := 0; attempt < 3; attempt++ {
        tx, _ := db.Begin()
        if err := fn(tx); err != nil {
            tx.Rollback()
            var mysqlErr *mysql.MySQLError
            if errors.As(err, &mysqlErr) && mysqlErr.Number == 1213 {
                // Exponential backoff with jitter
                time.Sleep(time.Duration(attempt*100+rand.Intn(50)) * time.Millisecond)
                continue
            }
            return err
        }
        return tx.Commit()
    }
    return errors.New("deadlock: max retries exceeded")
}
```

Enable deadlock logging when debugging:
```sql
SET GLOBAL innodb_print_all_deadlocks = ON;
-- Run SHOW ENGINE INNODB STATUS\G to see LATEST DETECTED DEADLOCK
-- Disable after debugging to prevent error log bloat
SET GLOBAL innodb_print_all_deadlocks = OFF;
```

---

## Frequently Asked Questions

{{< faq q="Is MySQL fundamentally scalable for enterprise workloads?" >}}
MySQL scales effectively to billions of rows and tens of thousands of transactions per second when properly architected. The primary limit is not row count but operational friction during schema migrations on massive tables, which can be mitigated through sharding or distributed NewSQL databases like TiDB.
{{< /faq >}}

{{< faq q="What are the operational TPS thresholds across MySQL scaling phases?" >}}
A single tuned MySQL primary handles 100–500 transactions per second at baseline. Performance expands through query optimization (500–1,500 TPS), connection pooling via ProxySQL (1,500–3,000 TPS), and horizontal read replication or sharding for workloads exceeding 6,000 TPS.
{{< /faq >}}

{{< faq q="What is the most effective MySQL sharding alternative for high-write platforms?" >}}
TiDB is the leading MySQL-compatible distributed SQL alternative for high-throughput write workloads. It maintains full MySQL protocol compatibility while automatically partitioning data across distributed storage nodes, eliminating manual application-level sharding logic.
{{< /faq >}}

{{< faq q="When should an architecture team choose Vitess over TiDB?" >}}
Vitess is preferred when teams wish to retain standard MySQL storage nodes and already have dedicated SRE resources to manage VSchema and VReplication workflows. TiDB is recommended when applications require transparent ACID transactions across nodes, automatic region rebalancing, or hybrid operational/analytical processing (HTAP).
{{< /faq >}}

{{< faq q="How do engineering teams migrate from MySQL sharding to TiDB without ID collisions?" >}}
Primary key collisions during shard consolidation are resolved by migrating auto-incrementing integers to 128-bit UUIDs stored as `BINARY(16)`. Alternatively, teams can configure composite primary keys incorporating the source shard identifier before running TiDB Data Migration (DM) tools.
{{< /faq >}}

{{< faq q="What performance improvements does MySQL 8.4 LTS introduce for scalability?" >}}
MySQL 8.4 LTS makes WRITESET parallel replication the default setting, significantly accelerating replica synchronization for write-heavy workloads. It also enhances InnoDB buffer pool management and updates security defaults to support long-term enterprise deployments through 2032.
{{< /faq >}}

---

## Related Database & Scalability Resources

- **Distributed SQL Migration:** Learn how to replace manual sharding with Distributed SQL in [MySQL Sharding Alternatives: Replace Sharding with TiDB](/posts/mysql-scaling-sharding-tidb-architecture/).
- **Vitess Implementation:** Explore query routing and Go AST parsing in [Vitess vs GORM Sharding: MySQL Write Scaling in Go](/posts/mysql-horizontal-scaling/).
- **Inventory Synchronization:** Combine CDC, Kafka, and Redis in [Real-Time Inventory Synchronization: Kafka, CDC & Redis](/posts/real-time-inventory-ecommerce-architecture/).
- **High-Concurrency Case Study:** Review 10M+ user database architectures in [Shopee Architecture: Database Scaling](/series/shopee-architecture/04-database-scale/).
- **Microservices Guide:** Connect distributed database topologies across services in [Go Microservices Architecture: Production Guide](/posts/go-microservices/).

{{< author-cta >}}