---
title: "MySQL Scalability: Read Replicas, Sharding & TiDB"
cover:
  image: "/images/posts/mysql-scalability-cover.png"
  alt: "Mysql Scalability Guide"
slug: "mysql-scalability-guide"
author: "Lê Tuấn Anh"
date: "2026-06-10T14:30:00+07:00"
lastmod: "2026-07-03T15:22:00+07:00"
draft: false
description: "MySQL scalability: read replicas, GORM/Vitess sharding, or TiDB NewSQL? Includes buffer pool tuning, ProxySQL pooling, and a 6-step decision framework."
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
  image: "/images/posts/mysql-scalability-cover.png"
  alt: "MySQL Scalability: read replicas, sharding, and TiDB NewSQL — performance architecture guide"
  relative: false
---

**Answer-first:** MySQL scalability is the practical throughput ceiling of your database at each resource level. A single tuned InnoDB instance delivers 100–500 TPS at baseline, scaling to 6,000–10,000+ TPS with connection pooling, read replicas, and optimal hardware. Beyond that, write-scaling requires sharding or a distributed SQL layer.

### What You'll Learn That AI Won't Tell You
- Tuning InnoDB buffer pool size for high read/write ratio workloads.
- Why standard read replication fails to solve write bottlenecks and when toshard.


MySQL scalability is the ability to increase database throughput — reads per second, writes per second, or data volume — without rewriting your application. The critical distinction: **read scaling** (adding replicas) and **write scaling** (sharding or distributed SQL) require completely different architectural approaches. Choosing the wrong path creates technical debt that takes months to unwind.

This guide walks through every stage of the MySQL scaling ladder, from buffer pool tuning through TiDB migration, with Go-specific implementation patterns at each step.

---

## What Is MySQL Scalability?

**MySQL scalability is the ability to handle increased data volume and transaction throughput without performance degradation. For a production e-commerce platform, this means keeping p95 database query latency under 50ms as traffic scales from 1,000 to 10,000 requests per second.**



The four-phase performance envelope for a dedicated MySQL server:

| Phase | TPS Range | Primary Lever |
|-------|-----------|---------------|
| 1 — Baseline | 100–500 TPS | InnoDB buffer pool (70–80% RAM) |
| 2 — Query tuning | 500–1,500 TPS | Index optimization, schema design |
| 3 — Connection pooling | 1,500–3,000 TPS | ProxySQL, MySQL Router |
| 4 — Horizontal | 6,000–10,000+ TPS | Read replicas, sharding |

One verified starting point that most teams skip: `innodb_buffer_pool_size` is **dynamically resizable in MySQL 8.0+** — no restart required.

```sql
-- Resize buffer pool without restarting (MySQL 8.0+)
SET GLOBAL innodb_buffer_pool_size = 8 * 1024 * 1024 * 1024; -- 8 GB
```

A healthy buffer pool maintains a **≥99% hit rate**. Check yours:

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

Or use the sys schema directly against production:

```sql
-- Find queries in the P95 execution time range
SELECT digest_text, count_star, avg_timer_wait/1000000000 AS avg_ms
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_timer_wait DESC
LIMIT 20;
```

### Signal 2: Replication Lag

`Seconds_Behind_Source` is unreliable in multi-threaded replication. Use Performance Schema for accurate per-worker lag:

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

Requirements for WRITESET:

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

**The maintenance event horizon occurs when schema migrations on a multi-terabyte MySQL table take longer than the allowable downtime window. Teams often migrate away from single-node MySQL when tools like pt-online-schema-change begin failing under high production load.**



The operational cost compounds with each shard:

- Schema change on 8 shards × 4-hour `ALTER TABLE` = 32 engineering-hours per release
- Cross-shard join queries require application-level fan-out
- Rebalancing a hot shard requires a custom VReplication workflow or downtime
- A `DELETE ... WHERE date < X` on 1B rows runs for hours; `ALTER TABLE ... DROP PARTITION p_old` is instant

When this overhead starts delaying feature shipping, the economics of a distributed SQL migration begin to make sense.

---

## Stage 3 — MySQL Sharding Alternative: TiDB

**TiDB is a distributed, NewSQL database that provides MySQL compatibility with transparent horizontal scaling. It eliminates the need for manual application-level sharding by separating the stateless SQL compute layer from the distributed TiKV storage engine.**



For TiDB architecture (TiKV, Raft consensus, Percolator ACID, TiFlash HTAP), see the deep-dive: [Replace MySQL Sharding with TiDB: Distributed SQL Migration Guide](/posts/mysql-scaling-sharding-tidb-architecture/).

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

**Go microservices optimize MySQL concurrency by strictly configuring `SetMaxOpenConns` to prevent connection exhaustion and using `SELECT ... FOR UPDATE` row-level locks combined with transaction timeouts to safely handle high-frequency e-commerce inventory deductions.**

### SKIP LOCKED for Distributed Job Queues

Instead of building a separate queue service, MySQL InnoDB supports a native distributed queue pattern:

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

InnoDB auto-detects deadlocks (error code `1213`) and rolls back the transaction with fewer row modifications. Handle this in Go:

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

## FAQ

{{< faq q="Is MySQL scalable?" >}}
Yes. MySQL scales to billions of rows and thousands of TPS with proper architecture. There is no hard row-count limit in InnoDB. The practical ceiling is the "Maintenance Event Horizon" — schema changes on tables with hundreds of millions of rows become multi-hour operations that block deployment pipelines. At that point, the operational overhead of MySQL sharding typically triggers evaluation of distributed SQL alternatives like TiDB.
{{< /faq >}}

{{< faq q="What is the scalability of MySQL?" >}}
A tuned single MySQL primary instance delivers 100–500 TPS at baseline, scaling through four phases: Phase 1 (100–500 TPS): buffer pool and schema tuning. Phase 2 (500–1,500 TPS): composite indexes and query optimization. Phase 3 (1,500–3,000 TPS): connection pooling via ProxySQL. Phase 4+ (6,000–10,000+ TPS): read replicas and sharding. Hardware context matters significantly — these figures assume a dedicated database server with NVMe storage.
{{< /faq >}}

{{< faq q="What is the best MySQL sharding alternative in 2026?" >}}
TiDB is the leading MySQL sharding alternative for production workloads. It is MySQL wire-protocol compatible (no application rewrites for basic queries), auto-partitions data internally via Raft Regions, and provides native ACID distributed transactions. TiDB 8.5.5 (2025) reduced schema changes on 100M+ row tables from hours to milliseconds for non-truncating DDL. PlanetScale (managed Vitess) is the alternative for teams that want to stay on standard MySQL without managing a distributed system.
{{< /faq >}}

{{< faq q="When should I use Vitess vs TiDB?" >}}
Use Vitess (or PlanetScale) when you want to stay on standard MySQL and are comfortable managing shard keys, VSchema, and VReplication workflows at the application layer. Use TiDB when you need the write scalability of sharding without any application-level routing logic, need ACID distributed transactions, or require HTAP (running analytics on fresh operational data without ETL). TiDB's operational complexity is higher upfront but eliminates the per-shard maintenance overhead permanently.
{{< /faq >}}

{{< faq q="How do I replace MySQL sharding with TiDB?" >}}
Use TiDB Data Migration (DM) for shard merge. The primary blocker is AUTO_INCREMENT primary key conflicts — each shard generates its own sequence, so IDs collide when merged. Resolution options: migrate to UUID (BINARY(16) + UUID_TO_BIN()), use a composite primary key (shard_id, original_id), or configure DM with ignore-checking-items: ["auto_increment_ID"] and reconstruct a unique constraint downstream. Validate consistency post-migration with sync-diff-inspector. For datasets over 1 TiB, use Dumpling + TiDB Lightning (Physical Mode) for the initial load before enabling DM for incremental sync.
{{< /faq >}}

{{< faq q="Does MySQL 8.4 change anything for scalability?" >}}
MySQL 8.4 LTS (April 2024) makes WRITESET parallel replication the default, which improves replica throughput for high-write workloads without any configuration change. It also removes mysql_native_password authentication by default (breaking change for older drivers) and retires MASTER/SLAVE terminology. MySQL 8.0 reached end-of-life in April 2026 — 8.4 LTS is the upgrade target with support through April 2032. Pre-migration: run mysqlsh -- util checkForServerUpgrade --target-version=8.4.0 and upgrade replicas before the primary.
{{< /faq >}}

Once your database layer scales, the next bottleneck is inventory synchronization across services. For how e-commerce teams combine Debezium CDC, Kafka partition keying, and idempotent Redis Lua scripts to prevent overselling at scale, see [Real-Time Inventory Synchronization: Kafka, CDC & Redis](/posts/real-time-inventory-ecommerce-architecture). For a production case study of MySQL sharding at 10M+ users — including Shopee's ProxySQL connection pooling, read replica architecture, and TiDB migration — see [Shopee Architecture: Database Scaling](/series/shopee-architecture/04-database-scale/). For a complete view of how multiple scaled databases interact in a distributed ecosystem, see the [Go Microservices Architecture: Production Guide](/posts/go-microservices/).
