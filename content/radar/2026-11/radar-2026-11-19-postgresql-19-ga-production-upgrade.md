---
title: "Tech Radar: PostgreSQL 19 GA — The Production Upgrade Guide for 17/18 Fleets"
date: "2026-11-19T09:00:00+07:00"
lastmod: "2026-11-19T09:00:00+07:00"
author: "Lê Tuấn Anh"
slug: "radar-2026-11-19-postgresql-19-ga-production-upgrade"
description: "PostgreSQL 19 GA is scheduled for Nov 19 with in-core REPACK (CONCURRENTLY), parallel autovacuum, AIO worker auto-scaling and the WAIT command — plus a 52-CVE November security drop and a PG14 EOL cliff that every fleet must plan around."
categories: ["Tech Radar", "Data Platforms", "Distributed Systems"]
ring: "TRIAL"
tags: ["PostgreSQL 19", "REPACK", "pg_upgrade", "Async I/O", "Autovacuum", "Logical Replication", "Database Upgrade", "OIDC", "Performance", "Data Platforms"]
cover:
  image: "/images/posts/default-post-1.jpg"
  alt: "Tech Radar: PostgreSQL 19 GA Production Upgrade Guide — REPACK, Parallel Autovacuum and pg_upgrade Paths"
  relative: false
mermaid: true
ShowToc: true
TocOpen: true
draft: false
noTranslation: true
canonicalURL: "https://tanhdev.com/radar/2026-11/radar-2026-11-19-postgresql-19-ga-production-upgrade/"
keywords: ["postgresql 19 ga upgrade", "postgresql 19 repack concurrently", "postgresql 19 parallel autovacuum", "postgresql 19 async io workers", "pg_upgrade 18 to 19 checklist", "postgresql 19 wait command standby", "postgresql november 2026 security update 52 cves", "postgresql 14 end of life upgrade path", "postgresql 19 logical replication wal_level", "postgresql 19 jit disabled default"]
---

# Tech Radar: PostgreSQL 19 GA — The Production Upgrade Guide for 17/18 Fleets

> **Answer-first:** PostgreSQL 19 general availability is scheduled for **November 19, 2026** — the RC2 announcement names that date explicitly, "barring issues requiring delay." The release ships **212 features**, and four of them change production operations directly: in-core **`REPACK (CONCURRENTLY)`** (bloat removal without an exclusive lock, replacing the external `pg_repack` dependency), **parallel autovacuum** with per-table worker tuning and a scoring-based prioritization system, **auto-scaling async I/O workers** (`io_min_workers`/`io_max_workers`) building on the PostgreSQL 18 AIO subsystem, and the **`WAIT` command** for read-your-writes on standbys. Before planning the upgrade, note what landed on **November 12**: point releases for every supported branch fixing **52 security vulnerabilities** (including `pg_restore` and `pg_dump` code-execution CVEs rated 8.8), **PostgreSQL 14 reaching end-of-life** with 14.25 as its final release, and a set of post-update reindex and re-backup requirements. This edition is the day-one playbook: what actually ships, what breaks, and the exact `pg_upgrade` sequence for 17/18 fleets.

> **Prerequisite:** Readers should be comfortable with major-version upgrade mechanics and replication topology (see [Go Microservices Production Playbook](/posts/go-microservices/) for the service layer that sits on top), with ledger-style Postgres workloads and hot-row concurrency (see [Composable Banking & Double-Entry Ledger Architecture](/radar/2026-11/radar-2026-11-10-composable-banking-double-entry-ledger-concurrency/)), and with workflow outbox/saga patterns that depend on transactional Postgres semantics (see [Temporal Workflow Go Architecture Series](https://tanhdev.com/series/cornerstone-technologies/temporal-workflow-go-architecture/) and [Temporal Saga Pattern for Distributed Transactions](https://tanhdev.com/posts/temporal-saga-pattern-golang-distributed-transactions-guide/)).

---

```yaml
name: "PostgreSQL 19: In-Core REPACK, Parallel Autovacuum & AIO Auto-Scaling (GA Nov 19)"
ring: "Trial"
quadrant: "Data Platforms"
rationale: "PostgreSQL 19 moves three operational burdens into the core — online bloat removal (REPACK CONCURRENTLY), parallel/prioritized autovacuum, and auto-scaling async I/O workers — while the November 12 security drop (52 CVEs, PostgreSQL 14 EOL) makes 'patch what you run' the same-day action regardless of upgrade plans. Trial in staging at GA; move to production after 19.1."
adr_link: "/radar/2026-11/radar-2026-11-19-postgresql-19-ga-production-upgrade/"
justification: "The RC2 announcement confirms GA for November 19, 2026 and documents the exact feature set (REPACK, parallel autovacuum, AIO worker scaling, WAIT) plus the migration steps that pg_upgrade cannot automate (locale-provider reindexes, max_locks_per_transaction doubling, JIT now off by default) — all verifiable before production exposure."
```

---

## 1. The Week at a Glance: Radar Ring Matrix

| Ring | Technology / Pattern | Domain | Why This Week |
| :--- | :--- | :--- | :--- |
| **ADOPT** | **November 12 point releases (18.7 / 17.12 / 16.16 / 15.20)** | Data Platforms | 52 security vulnerabilities fixed, several rated 8.8 (arbitrary code execution via `pg_restore`, `pg_dump`, type confusion); cumulative minor release, no `pg_upgrade` needed. |
| **ADOPT** | **Post-update reindex/re-backup sweep** | Data Platforms | The same announcement mandates reindexes for affected GIN/pg_trgm/TOAST/bpchar indexes and a fresh full backup for incremental-backup users — not optional. |
| **HOLD** | **Any PostgreSQL 14 deployment** | Data Platforms | 14.25 is the final release; the branch is end-of-life as of November 12, 2026 and will never receive another security fix. |
| **TRIAL** | **PostgreSQL 19 in staging (GA scheduled Nov 19)** | Data Platforms | `REPACK (CONCURRENTLY)`, parallel autovacuum, AIO auto-scaling and `WAIT` are production-changing; exercise real vacuum/REPACK workloads in staging first. |
| **TRIAL** | **`pg_upgrade` 18→19 rehearsal with locale-provider reindex plan** | Data Platforms | FTS/pg_trgm/fuzzystrmatch indexes need reindexing after upgrade and `max_locks_per_transaction` defaults doubled — rehearse before the real window. |
| **ASSESS** | **`pg_plan_advice` / planner advisor framework** | Data Platforms | Per-query planner control with an auto-apply mechanism is powerful for plan-regression fires, but long-term plan pinning needs its own governance. |
| **ASSESS** | **Sequence replication & logical replication without restart** | Data Platforms | `ALL SEQUENCES` replication and `wal_level` flip without restart simplify HA topologies; assess for fleets with many subscribers. |
| **HOLD** | **JSON_ARRAY()/JSON_OBJECT() in expression indexes, generated columns or partition keys** | Data Platforms | Reverted in RC2 for this release; drop and redefine any such objects created during beta/RC testing. |

---

## 2. What Actually Ships in PostgreSQL 19: The Verified Feature Set

> **BLUF:** The release notes enumerate 212 features. Four change production operations materially: `REPACK (CONCURRENTLY)`, parallel + prioritized autovacuum, auto-scaling AIO workers, and `WAIT` for standby read-your-writes. A second tier — logical replication without restart, sequence replication, the planner advisor framework, and a batch of SQL ergonomics (`IGNORE NULLS`, `ON CONFLICT DO SELECT ... RETURNING`, JSON `COPY TO`) — shapes how applications are written against Postgres going forward. Everything below is taken directly from the [official PostgreSQL 19 release notes](https://www.postgresql.org/docs/19/release-19.html).

### 2.1 `REPACK (CONCURRENTLY)`: Bloat Removal Becomes a SQL Command

For two decades, the answer to table bloat in Postgres was an awkward choice: `VACUUM FULL` (reclaims space, but takes an exclusive lock and blocks all traffic) or the external `pg_repack` extension (online, but another operational dependency to build, version-match and trust). PostgreSQL 19 promotes the operation into the core as the **`REPACK`** command:

- **`REPACK (CONCURRENTLY)`** reclaims disk space and reorganizes table contents without blocking reads or writes — the same behavior pg_repack users know, now supported in-tree.
- A new **`max_repack_replication_slots`** setting governs the slots REPACK uses to keep concurrent changes during the rebuild.
- A new **`pg_stat_progress_repack`** view makes the operation observable — you can finally answer "how far along is the repack of that 4 TB partitioned ledger table?" from SQL instead of log archaeology.

```sql
-- Before PostgreSQL 19: bloat removal required either
--   VACUUM FULL ledger_entries;              -- exclusive lock, outage-grade
--   or an external pg_repack extension.       -- operational dependency

-- PostgreSQL 19: in-core, online, observable
REPACK (CONCURRENTLY) ledger_entries;

-- Watch it run
SELECT phase, heap_tuples_scanned, heap_tuples_written
FROM pg_stat_progress_repack
WHERE relid = 'ledger_entries'::regclass;
```

*(Opinion, clearly separated from the facts above.)* For append-heavy ledger and event tables — the workload class we documented in the [composable banking ledger radar](/radar/2026-11/radar-2026-11-10-composable-banking-double-entry-ledger-concurrency/) — in-core REPACK removes an entire external dependency from the change-management chain. The right posture is still: run it in staging against a production-shaped table first, because online does not mean free; REPACK still doubles the table's storage temporarily and competes for I/O.

### 2.2 Parallel Autovacuum and Prioritization: The Vacuum Backlog Finally Has Levers

PostgreSQL 19 attacks the "vacuum can't keep up" problem from two directions:

1. **Parallelism.** Autovacuum can now vacuum indexes in parallel, controlled by **`autovacuum_max_parallel_workers`** globally and **`autovacuum_parallel_workers`** per table. For wide tables with dozens of indexes, this directly shortens the longest phase of the vacuum cycle.
2. **Prioritization.** A scoring system (configurable via **`autovacuum_*_score_weight`** GUCs) decides which tables get vacuumed first, with a new **`pg_stat_autovacuum_scores`** view exposing the current scores. You can finally tell autovacuum that the hot ledger table outranks the archive tables nobody reads.

```sql
-- Per-table parallel vacuum workers for the hottest table
ALTER TABLE ledger_entries
  SET (autovacuum_parallel_workers = 4);

-- Inspect what autovacuum thinks of your tables
SELECT relid::regclass AS table_name, score
FROM pg_stat_autovacuum_scores
ORDER BY score DESC
LIMIT 20;
```

One documented caveat from the release notes: **parallel vacuum workers share the vacuum cost limit**, so adding workers does not linearly speed vacuum in I/O-throttled deployments — measure before assuming the win.

### 2.3 Async I/O Grows Up: Worker Auto-Scaling

PostgreSQL 18 introduced the asynchronous I/O subsystem; PostgreSQL 19 makes it operationally sane:

- **Worker-based AIO now auto-scales** with new GUCs **`io_min_workers`**, **`io_max_workers`**, **`io_worker_idle_timeout`**, and **`io_worker_launch_interval`** — the pool breathes with the workload instead of running a fixed worker count.
- The old fixed **`io_workers`** setting is **removed** — if your PostgreSQL 18 configuration sets it, the upgrade configuration check will flag it.
- AIO integration extends to more operations than in 18, and **`EXPLAIN (ANALYZE, IO)`** now reports async I/O statistics, making read-ahead behavior visible per query.

*(Opinion.)* This is the quiet prerequisite for everything else in the release: REPACK, parallel vacuum and big analytic scans all push large sequential reads, and a fixed worker pool was the hidden bottleneck in 18 deployments. Auto-scaling removes a tuning surface most teams never knew they had.

### 2.4 The `WAIT` Command: Read-Your-Writes on Standbys Without Application Hacks

Every Postgres shop with read replicas has a version of this bug: the user writes, the read hits a lagging standby, the data "disappears." PostgreSQL 19 ships the **`WAIT`** command:

- **`WAIT`** pauses the server session until a given LSN has been **written, flushed, or replayed** on the standby — turning "please wait for my write" into a first-class SQL operation instead of a polling loop or a proxy-side heuristic.
- Combined with the long-standing `pg_current_wal_lsn()` / replay-lag machinery, this makes standby routing correctness enforceable at the database layer.

```sql
-- Application flow on a standby after a write on the primary
SELECT pg_last_wal_replay_lsn();
WAIT LSN '7/D10A2F58' REPLAY;   -- returns once the standby has replayed that position
-- ...now serve the read
```

*(Opinion.)* We called out lag-aware routing as an architectural liability in the [Temporal saga patterns](https://tanhdev.com/posts/temporal-saga-pattern-golang-distributed-transactions-guide/) work — compensations that read stale replicas produce wrong business decisions, not just stale UI. A database-level `WAIT` lets service code do the right thing without embedding lag heuristics in the proxy tier. Note the operational cost is real: an application that waits on a badly lagging standby is now an application that blocks in SQL, so pair `WAIT` with statement timeouts.

### 2.5 Replication, Planner, and SQL Ergonomics: The Second Tier

The remaining items that will shape application code and HA design:

| Feature | What It Does | Production Implication |
| :--- | :--- | :--- |
| **Logical replication without restart** | Setting `wal_level = replica` now enables logical replication automatically (new `effective_wal_level`), no restart required | Adding a logical subscriber no longer demands a restart window on the primary |
| **Sequence replication** | `CREATE SUBSCRIPTION ... ALL SEQUENCES`, `REFRESH SEQUENCES`, `pg_get_sequence_data()` | Sequence values finally propagate — closes a classic failover/subscriber gap |
| **Planner advisor framework** | `pg_plan_advice` extension controls planner decisions; `pg_stash_advice` auto-applies advice per query | Escape hatch for plan regressions — but plan pinning needs governance (see §6) |
| **`IGNORE NULLS` / `RESPECT NULLS`** | Window functions (lead, lag, first_value, last_value, nth_value) | Kills the hand-rolled "last non-null" CTE patterns |
| **`INSERT ... ON CONFLICT DO SELECT ... RETURNING`** | Returns and locks conflicting rows (`FOR UPDATE`/`FOR SHARE`) | Upsert flows can now read *what* conflicted without a second round-trip |
| **COPY improvements** | `ON_ERROR SET_NULL`, multi-header support, `COPY TO` JSON (`FORCE_ARRAY`), `COPY TO` partitioned tables, SIMD-accelerated `COPY FROM` | JSON export pipelines and bulk-load paths get faster and simpler |
| **Default TOAST compression → lz4** | New tables default to lz4 instead of pglz | Faster access to large TOASTed values; mostly invisible upgrade win |
| **Monitoring** | New views `pg_stat_lock`, `pg_stat_recovery`; per-process-type `log_min_messages`; `log_lock_waits` on by default | Lock diagnosis and recovery observability improve out of the box |

Authentication changes worth noting for security baselines: OAuth infrastructure is extended (custom `pg_hba.conf` options for OAuth validators, `oauth_ca_file`/`PGOAUTHCAFILE` in libpq, server-side SNI support via `pg_hosts.conf`), **MD5 authentication now issues warnings** after successful login (`md5_password_warnings`), and a new `password_expiration_warning_threshold` (default 7 days) warns before password expiry. There is no turn-key OIDC server authentication in 19 — the release notes describe OAuth plumbing extensions, not a headline OIDC feature — so treat "OIDC auth" claims in third-party roundups with care and plan SCRAM/OAuth migration on the strength of the deprecation warnings instead.

### 2.6 RC2 Corrections: The "If You Tested on Beta/RC, Re-Verify" List

Per the [November 12 RC2 announcement](https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442), RC2 fixed since RC1:

- **`JSON_ARRAY()`/`JSON_OBJECT()` reverted from expression indexes, generated columns, and partition keys** — if you created such objects during beta/RC testing, drop and redefine them before/at upgrade.
- **`GROUPING SETS` wrong-results** and **`first_value()`/`nth_value()` `IGNORE NULLS` infinite loop** fixed — re-run any result-diff tests written against RC1 output.
- **Standby promotion hang** and **`LISTEN`/`NOTIFY` queue stall** fixed — re-test failover and notification paths in staging, not from memory.
- Eager-aggregation fixes around volatile functions, and hash-execution performance regressions corrected.

---

## 3. November 12: The Security Drop Every Fleet Must Act On First

> **BLUF:** Before any 19 upgrade plan, the November 12 update is the urgent item: 18.7, 17.12, 16.16, 15.20 and 14.25 fixed **52 security vulnerabilities** — many rated 8.8, including arbitrary code execution through `pg_restore`, `pg_dump`, type-confusion vectors and extension scripting — plus over 140 bugs. **PostgreSQL 14 is end-of-life** as of the same day. Minor releases are cumulative and need no `pg_upgrade`, but several require post-update reindexes or re-backups.

The vulnerabilities worth knowing by name (full list in the [official announcement](https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442)):

- **CVE-2026-6460** (CVSS 8.8) — type confusion after `ALTER ... SET DATA TYPE` can execute arbitrary code.
- **CVE-2026-116314** (CVSS 8.8) — `pg_restore` arbitrary code execution via missing non-plain archive validation.
- **CVE-2026-116318** (CVSS 8.8) — `pg_dump` not-null constraint name SQL injection; **CVE-2026-116330** (8.8) — psql command injection in tar restore scripts. Backup/restore tooling itself is now an attack surface — treat restore scripts as untrusted artifacts.
- **CVE-2026-120145** (CVSS 8.8) — logical replication can write to subscriber system catalogs.
- **CVE-2026-14661** (CVSS 8.1) — dblink and subscriptions can append to arbitrary files.
- **CVE-2026-116325** (CVSS 8) — `reindexdb` index-name quoting SQL injection; **CVE-2026-116313** (7.2) — `vacuumdb --missing-stats-only` lets a database owner execute code as the vacuumdb user.

The post-update checklist from the same announcement — this is what "we patched" actually means:

```bash
# 1) Minor releases are cumulative: stop PostgreSQL, update binaries, start.
#    No pg_upgrade / dump-reload for the point release.

# 2) Post-update actions required by the announcement:
#    a. GIN index corruption fixes  -> reindex affected GIN indexes
psql -c "REINDEX INDEX your_gin_index;"

#    b. pg_trgm GiST corruption     -> reindex GiST indexes using gist_trgm_ops
psql -c "REINDEX INDEX your_trgm_gist_index;"

#    c. TOAST 'missing chunk number' errors -> reindex the table
psql -c "REINDEX TABLE your_table_name;"

#    d. Incremental backup users    -> take a NEW FULL BACKUP after updating

#    e. Find invalid partitioned-table NOT NULL NO INHERIT constraints:
psql -c "SELECT conrelid::regclass, conname FROM pg_constraint
         WHERE contype = 'n' AND connoinherit
           AND conrelid IN (SELECT oid FROM pg_class WHERE relkind = 'p');"
#       then ALTER TABLE ... DROP CONSTRAINT or ALTER CONSTRAINT ... INHERIT

#    f. Lengthless bpchar B-tree deduplication disabled -> reindex those indexes
#       (char(n) columns are unaffected)
```

And the deadline that cannot be negotiated: **PostgreSQL 14 reached end-of-life on November 12, 2026** — 14.25 is its final release. Per the [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/), an EOL branch will never receive another security fix, so every remaining PG14 deployment is now a standing vulnerability. If a major upgrade cannot happen this quarter, at minimum get off 14 via `pg_upgrade` to 16/17 now and schedule 19 later.

---

## 4. Upgrade Paths From 17/18: The Three Options and What They Cost

PostgreSQL supports three major-version upgrade routes, and the RC2 announcement points to the [official upgrading guide](https://www.postgresql.org/docs/19/upgrading.html). The choice is a business decision dressed as a technical one — each route buys a different trade between downtime, disk, and dual-write complexity:

| Route | Downtime | Cost Profile | When It Is Right |
| :--- | :--- | :--- | :--- |
| **`pg_upgrade`** (with `--link`) | Minutes-to-hours (catalog copy + count-down check); `--link` avoids a second data copy | Requires both clusters on disk simultaneously; fast, standard, well-trodden | Default choice for fleets that can tolerate a maintenance window |
| **`pg_dump` / `pg_restore`** | Hours-to-days for large clusters (full logical dump/restore) | Simple, version-safe, but I/O-bound and slow | Small clusters, or when migrating to new hardware/OS at the same time |
| **Logical replication** | Near-zero cutover downtime, but weeks of dual-running | Two live systems, schema kept in sync, cutover is a routing flip | Large HA fleets, or when moving through 14/15 first (supported majors) |

```mermaid
sequenceDiagram
    autonumber
    participant Ops as Operator (runbook)
    participant Old as PostgreSQL 18 primary + standbys
    participant New as PostgreSQL 19 initdb cluster
    participant App as Applications

    Note over Ops: T-7 days: rehearse on production-shaped data<br/>(locale-provider reindexes, bpchar, btree_gist checks)
    Ops->>Old: 1. Verify post-Nov-12 point release applied (18.7)
    Ops->>Old: 2. DROP any JSON_ARRAY()/JSON_OBJECT()<br/>expression indexes / generated cols / partition keys
    Ops->>New: 3. initdb with matching locale + encoding<br/>check max_locks_per_transaction (64 -> 128)
    Ops->>Ops: 4. Maintenance window begins (app read-only)
    Ops->>Old: 5. Final checkpoint
    Ops->>New: 6. pg_upgrade --link (catalog migration)
    Ops->>New: 7. Reindex FTS / pg_trgm / fuzzystrmatch indexes<br/>(locale provider change)
    Ops->>New: 8. ANALYZE all databases
    Ops->>App: 9. Reopen writes; verify WAIT-based<br/>standby read-your-writes paths
    Note over Ops: Rollback = keep old PGDATA untouched until<br/>soak period passes (pg_upgrade --link mutates old cluster)
```

### 4.1 The Incompatibility Checklist (What `pg_upgrade` Cannot Fix For You)

The release notes' migration section is the diff that will bite. Items our production checklist flags, in rough order of blast radius:

1. **`max_locks_per_transaction` default doubled 64 → 128.** If you rely on the default, doubling it to "keep the same effective behavior" is not needed — but if you *set* a custom value tuned against 64, re-validate lock-heavy transactions (big `ALTER TABLE` batches, partition maintenance).
2. **`standard_conforming_strings` is forced on**; `escape_string_warning` is removed. Old dumps produced with it off will not load — check ancient restore scripts before your next disaster-recovery drill.
3. **JIT is disabled by default.** Workloads that benefited from JIT (long, analytic queries) will lose that unless you re-enable `jit = on`. OLTP fleets mostly gain from this; BI fleets must consciously re-enable.
4. **FTS, pg_trgm, fuzzystrmatch now use the locale provider — reindex after upgrade.** This pairs with the November 12 fixes: text-search indexes are doubly flagged this cycle.
5. **Default inet/cidr index opclasses changed** (btree_gist → GiST); `pg_upgrade` blocks upgrades with broken btree_gist indexes on those types — resolve before the window, not during it.
6. **RADIUS authentication removed.** If any fleet node still authenticates via RADIUS, migrate to SCRAM or an OAuth validator first.
7. **MULE_INTERNAL encoding removed;** CR/LF banned in database/role/tablespace names; system columns banned in `COPY FROM ... WHERE`; `json_array()` no-row case now returns `[]` instead of NULL.
8. **Parallel vacuum workers share the cost limit** — I/O-throttled deployments may see slower-than-expected parallel vacuum; tune `vacuum_cost_limit` consciously.
9. **Wait events renamed** (BUFFERPIN→BUFFER, BufferContent removed, new BufferShared/ShareExclusive/Exclusive) — update dashboards and runbooks that key on wait-event names.
10. **tzdata updated to 2026f** — re-check timezone-dependent partitioning after upgrade.

*(Opinion.)* Items 2, 4 and 5 are the ones that surprise fleets in the window itself, because they surface only on the new cluster — rehearse the upgrade against a production-shaped copy and let `pg_upgrade`'s checks fail in staging, where failing is free.

### 4.2 The Day-One Production Playbook

```bash
# ---- Pre-upgrade (T-7 days) ----
# Confirm current cluster is on the Nov 12 point release first
psql -Atc "SHOW server_version;"           # expect 18.7 / 17.12 etc.

# Remove RC-era JSON function objects if you tested on beta/RC
psql -c "SELECT indexdef FROM pg_indexes
         WHERE indexdef ~ 'json_array\\(|json_object\\(';"

# Check for btree_gist indexes on inet/cidr (blocked by pg_upgrade if broken)
psql -c "SELECT n.nspname, c.relname FROM pg_class c
         JOIN pg_namespace n ON n.oid = c.relnamespace
         JOIN pg_am am ON am.oid = c.relam
         WHERE am.amname = 'gist';"

# ---- Upgrade window ----
pg_ctl stop -D /var/lib/postgresql/18/main
/usr/lib/postgresql/19/bin/initdb -D /var/lib/postgresql/19/main \
  --locale=C.UTF-8 --encoding=UTF8
/usr/lib/postgresql/19/bin/pg_upgrade \
  --old-datadir /var/lib/postgresql/18/main \
  --new-datadir /var/lib/postgresql/19/main \
  --old-bindir /usr/lib/postgresql/18/bin \
  --new-bindir /usr/lib/postgresql/19/bin \
  --link

# ---- Post-upgrade (mandatory, per release notes) ----
/usr/lib/postgresql/19/bin/vacuumdb --all --analyze-in-stages
# Reindex text-search-family indexes (locale provider change):
psql -c "REINDEX DATABASE appdb;"   # scoped: FTS/pg_trgm/fuzzystrmatch indexes
/usr/lib/postgresql/19/bin/pg_ctl start -D /var/lib/postgresql/19/main

# ---- Verification ----
psql -Atc "SHOW server_version;"                     # 19.x
psql -c "SELECT * FROM pg_stat_progress_repack;"     # REPACK observability live
psql -c "SELECT count(*) FROM pg_stat_autovacuum_scores;"  # prioritization live
```

Config migration notes: remove the PostgreSQL 18-era `io_workers` setting (replaced by `io_min_workers`/`io_max_workers`); decide explicitly on `jit = on` if your workload used it; review `md5_password_warnings` output to drive the MD5 → SCRAM retirement plan; and expect `log_lock_waits` to be on by default — adjust log volume/alerting accordingly.

---

## 5. What Production Engineers Should Do on Day One (GA Day, Nov 19)

> **BLUF:** Day one is not upgrade day. Day one is: (1) confirm every fleet node is on the November 12 point release of its current major version; (2) audit for PG14 EOL exposure; (3) stand up a 19 staging environment from RC2/GA bits with production-shaped data; (4) run the REPACK/parallel-vacuum/AIO experiments that justify the upgrade business case; (5) book the `pg_upgrade` window only after a clean rehearsal.

1. **Patch before you plan.** The 52-CVE drop is live risk on versions you run today; the 19 upgrade is future value. Do them in that order.
2. **Retire PG14 now, in two steps if needed.** EOL means the clock has stopped; move to a supported major even if 19 is not yet in your production channel.
3. **Stage 19 with production-shaped data.** The features that justify the upgrade — REPACK, parallel autovacuum, AIO — are only evaluable against real bloat, real index counts and real I/O patterns. RC2 is documented as "mostly identical to the final release," so RC2 results transfer.
4. **Write the two test suites before the window:** a result-diff suite for planner-visible behavior (`ON CONFLICT DO SELECT`, `GROUPING SETS`, window functions) and a reindex/backup-restore drill covering the November 12 post-update items.
5. **Plan the REPACK rollout like you planned autovacuum tuning:** per-table storage headroom, I/O windows, and `pg_stat_progress_repack`-based alerting from day one.
6. **Gate the production upgrade on 19.1.** The project's own cadence says the first point release is where early-release bugs get collected; our standing guidance for data platforms is GA-plus-one for anything the application cannot tolerate losing.

---

## 6. Radar Take: The Upgrade Is the Easy Part — Governance Is the New Surface

*(Opinion — our synthesis, not the sources'.)* PostgreSQL 19's headline features are all "operational burdens moving into the core": bloat removal, vacuum scheduling, I/O scaling, standby consistency. That is a genuine maturity step — fewer external extensions, fewer proxy heuristics, fewer 3 a.m. scripts. But it moves the hard part up a layer. When `REPACK` is a SQL command, when planner advice can be stashed and auto-applied per query, and when `WAIT` lets application sessions block on replication progress, the review questions change:

- Who is allowed to run `REPACK (CONCURRENTLY)` against which tables, and who owns the storage headroom it temporarily consumes?
- Who approves `pg_stash_advice` entries — and what is the expiry policy for a pinned plan, before the pinned plan itself becomes the regression?
- Which call paths are permitted to use `WAIT`, and what statement timeout bounds them when a standby degrades?

Fleets that treat 19 as "18 with new knobs" will capture the vacuum and REPACK wins but miss the governance questions. Fleets that write those policies in the same sprint as the `pg_upgrade` rehearsal will get both. For the service-side patterns that consume these database behaviors safely — outbox, saga compensation, idempotent retries — see the [Temporal workflow architecture series](https://tanhdev.com/series/cornerstone-technologies/temporal-workflow-go-architecture/) and our [Go microservices playbook](/posts/go-microservices/).

---

## 7. Frequently Asked Questions

{{< faq question="Is PostgreSQL 19 GA confirmed for November 19, 2026?" >}}
It is **scheduled**, not yet released as of this edition: the official RC2 announcement (November 12) states GA is planned for November 19, 2026 "unless a blocking issue is discovered," and RC2 is documented as mostly identical to the final release. Every feature claim in this article comes from the official PostgreSQL 19 release notes; the GA date should be re-confirmed against the postgresql.org announcements page on the day.
{{< /faq >}}

{{< faq question="Should we upgrade straight from 17 to 19, or go through 18 first?" >}}
Direct 17→19 with `pg_upgrade` is supported and fine for most fleets — the tool upgrades across majors in one pass. The two-step path (17→18→19) only earns its cost when you specifically want PostgreSQL 18's AIO foundation running in production for a while first, since 19's auto-scaling AIO workers (`io_min_workers`/`io_max_workers`) build directly on it. Fleets already on 18 should rehearse only one migration. What matters more than the path: apply the November 12 point release to your current major first, and budget for the mandatory post-upgrade reindexes (FTS/pg_trgm/fuzzystrmatch locale-provider change) and the `max_locks_per_transaction` default doubling.
{{< /faq >}}

{{< faq question="Does REPACK (CONCURRENTLY) make pg_repack and VACUUM FULL obsolete?" >}}
For most workloads, yes: in-core `REPACK (CONCURRENTLY)` provides the online bloat-removal behavior that previously required the external pg_repack extension, with new observability (`pg_stat_progress_repack`) and slot control (`max_repack_replication_slots`) built in. `VACUUM FULL` remains for cases where you want the strictest, simplest exclusive-lock semantics. What online does *not* mean is free: REPACK still needs temporary storage roughly equal to the table size and competes for I/O, so rollout should be scheduled and monitored like any heavy maintenance — and existing pg_repack deployments should be retired deliberately after 19 stabilizes, not mid-upgrade-window.
{{< /faq >}}

{{< faq question="The November 12 release fixed 52 CVEs — do we need pg_upgrade or downtime to apply it?" >}}
No `pg_upgrade`, no dump/reload: minor releases are cumulative, so applying 18.7/17.12/16.16/15.20 is a restart on updated binaries. But "no pg_upgrade" is not "no work": the announcement requires reindexes where GIN, pg_trgm GiST, or TOAST corruption is suspected, reindexing lengthless-bpchar B-tree indexes, a fresh full backup for incremental-backup users, and cleanup of invalid `NOT NULL NO INHERIT` constraints on partitioned tables. Also note PostgreSQL 14's final release (14.25) shipped the same day — that branch is now end-of-life and must be migrated off.
{{< /faq >}}

---

## 8. Primary Sources

- PostgreSQL 19 official release notes (feature set, migration/incompatibility list): [postgresql.org/docs/19/release-19.html](https://www.postgresql.org/docs/19/release-19.html)
- November 12, 2026 update announcement — 18.7/17.12/16.16/15.20/14.25 + 19 RC 2, 52 CVEs, post-update steps, PostgreSQL 14 EOL: [postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442](https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442)
- PostgreSQL 19 RC 1 announcement (RC schedule, GA planned Nov 19, RC2 fix list): [postgresql.org/about/news/postgresql-19-rc-1-released-3409/](https://www.postgresql.org/about/news/postgresql-19-rc-1-released-3409/)
- Major-version upgrade guide (`pg_upgrade` / dump-restore / logical replication): [postgresql.org/docs/19/upgrading.html](https://www.postgresql.org/docs/19/upgrading.html)
- PostgreSQL versioning policy (EOL semantics): [postgresql.org/support/versioning/](https://www.postgresql.org/support/versioning/)

### Internal References

- Ledger-style Postgres workloads and hot-row concurrency: [Composable Banking & Double-Entry Ledger Architecture](/radar/2026-11/radar-2026-11-10-composable-banking-double-entry-ledger-concurrency/)
- Service-side transactional patterns that sit on these database behaviors: [Temporal Workflow Go Architecture Series](https://tanhdev.com/series/cornerstone-technologies/temporal-workflow-go-architecture/) · [Temporal Saga Pattern for Distributed Transactions](https://tanhdev.com/posts/temporal-saga-pattern-golang-distributed-transactions-guide/)
- Platform build conventions: [Go Microservices Production Playbook](/posts/go-microservices/)
- Sharding-first scaling alternative when vertical scaling is exhausted: [MySQL Sharding & TiDB Architecture](/posts/mysql-scaling-sharding-tidb-architecture/)
