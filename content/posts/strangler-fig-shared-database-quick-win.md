---
title: "Magento Migration: Shared DB, CDC, or Event Bus?"
description: "Magento database migration decision: compare Shared DB, CDC + Debezium, and Event Bus separation with a 16-dimension risk matrix and 4-question decision framework for architects."
date: "2026-07-18T18:00:00+07:00"
lastmod: "2026-07-18T18:00:00+07:00"
slug: "strangler-fig-shared-database-quick-win"
author: "Lê Tuấn Anh"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Magento", "Strangler Fig", "Shared Database", "CDC", "Debezium", "Event Bus", "Kafka", "Outbox Pattern", "Migration", "Architecture", "Golang", "Database Per Service"]
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/strangler-fig-shared-database-quick-win-cover.png"
  alt: "Magento database migration decision: Shared DB vs CDC vs Event Bus — Architecture Comparison"
  relative: false
canonicalURL: "https://tanhdev.com/posts/strangler-fig-shared-database-quick-win/"
---

**Answer-first:** Three database strategies exist for Magento→Golang migration: (A) Shared DB — immediate compute win, dangerous as a final state; (B) CDC + Debezium — gradual DB separation without changing PHP code; (C) Full Event Bus — complete autonomy but requires Magento to publish every state change as an event. **Option B is the recommended path for most teams.**

### What You'll Learn That AI Won't Tell You
- Why Go running against Magento's MySQL is faster at the compute layer but still bottlenecked at the EAV query layer — and what actually fixes it.
- The single deciding factor between CDC (Option B) and Event Bus (Option C): who owns the PHP Magento codebase.

---

> This post is part of the **[Composable Commerce Migration series](/series/composable-commerce-migration/)** — a step-by-step playbook for migrating Magento 2 to Go microservices. For the full migration execution guide, see [Part 6: Phase 1 Strangler Fig](/series/composable-commerce-migration/part-6-phase1-strangler-fig/).

## The Strangler Fig Dilemma: Compute vs. Data

When migrating away from a Magento monolith to a Golang backend, architects face a non-obvious decision: do we migrate the *API layer* and the *database* at the same time?

Migrating both simultaneously requires setting up Eventual Consistency, Dual-Writes, and Saga patterns from Day 1. This delays time-to-market and prevents the business from seeing performance improvements for 9–18 months.

The alternative is the **Shared Database Quick Win** — migrate the API compute layer first, keep the data layer intact, and buy time to architect a proper DB separation strategy.

But "buy time" only works if you have a clear plan for Phase 2. This post defines all three options and gives you a decision framework to pick the right path.

---

## Three Options on the Table

```
┌──────────────────┬──────────────────────────┬──────────────────────────┐
│  OPTION A        │  OPTION B                │  OPTION C                │
│  Shared DB       │  Evolutionary CDC        │  Full Separation +       │
│  (Quick Win)     │  (Debezium + Outbox)     │  Event Bus (Kafka)       │
├──────────────────┼──────────────────────────┼──────────────────────────┤
│  Go reads the    │  Go owns write DB.       │  Fully separate DBs.     │
│  same Magento    │  CDC syncs reads from    │  All comms via Kafka.    │
│  MySQL directly  │  Magento. No PHP changes │  Magento emits events    │
└──────────────────┴──────────────────────────┴──────────────────────────┘
```

---

## Option A — Shared Database (The Quick Win)

```
┌──────────────┐         ┌──────────────────────────────┐
│  Go (magento-go) │──READ──▶│                              │
│              │──WRITE─▶│   MySQL Magento (shared)     │
│  PHP Magento │──READ──▶│                              │
│              │──WRITE─▶└──────────────────────────────┘
└──────────────┘
```

In Phase 1 of a Strangler Fig, you introduce a smart router (e.g., `routemode` shadow proxy) in front of Magento, then rewrite high-throughput APIs in Go — but connect Go directly to the existing Magento MySQL.

### Why It Works (Immediate Gains)

**Magento PHP can take 100–200ms just to bootstrap before executing a single SQL query.** Go eliminates this overhead entirely. Measured in a real Magento→Go migration (`mag-go`), the same authentication endpoint dropped from 180ms to 8ms — a **22× reduction** — without changing the database query at all.

1. **Compute decoupling is instant.** The PHP framework overhead (DI container, ORM hydration, module observers) is gone.
2. **Zero data sync issues.** Both systems read the same committed MySQL rows — no eventual consistency lag.
3. **Rollback is trivial.** One config change in `routemode` flips traffic back to PHP.

### The Dark Sides — Why This Cannot Be the Final State

#### Dark Side 1: Magento DB is a "Hidden API" You Don't Control

Magento's schema is not your API — but Go is now coupled to it as if it were.

```
Magento upgrade 2.4.6 → 2.4.7
  → Column renamed in customer_entity
  → Go struct binding silently fails or panics
  → Incident at 2am
```

Adobe has deprecated the "split database" feature in Magento 2.4.6+. Every upgrade consolidates the schema further. Each Go struct pointing at a Magento table is an undeclared dependency with no SLA.

#### Dark Side 2: Write Conflict — Race Conditions on Shared Tables

| Table | PHP writes | Go writes | Risk |
|---|---|---|---|
| `customer_entity` | ✅ | ✅ (address, token updates) | **HIGH** |
| `oauth_token` | ✅ | ✅ (magento-go auth module) | **CRITICAL** |
| `customer_address_entity` | ✅ | ✅ | **HIGH** |
| `quote` / `sales_order` | ✅ | Proxy only | Medium |

MySQL row-level locks prevent dirty reads but **do not prevent business logic conflicts**. If Go updates a customer session token at the same moment Magento invalidates it, the result is corrupted auth state — not a database error.

#### Dark Side 3: Distributed Monolith Trap

```
Go service ───────▶ Shared MySQL ◀─────── PHP Magento
    ↑                                           ↑
"microservice"                       monolithic coupling in practice
```

You now have two separate runtimes but **one failure domain**. A Go query that performs a full-scan on `catalog_product_entity_varchar` degrades Magento's checkout performance. This is architecturally identical to a monolith — it is just harder to debug because two codebases are involved.

#### Dark Side 4: EAV Is the Real Bottleneck — Go Doesn't Fix It

```sql
-- Just to load one customer with all EAV attributes:
SELECT ce.*, 
       cevs.value AS first_name,   -- customer_entity_varchar (JOIN 1)
       cevi.value AS store_id,     -- customer_entity_int (JOIN 2)
       ...
FROM customer_entity ce
JOIN customer_entity_varchar cevs ON ce.entity_id = cevs.entity_id
JOIN customer_entity_int cevi ON ce.entity_id = cevi.entity_id
...  -- 5–10 JOINs total
```

Go executes this query faster than PHP, but the **query plan is identical**. The bottleneck is the EAV schema design, not the language. The only fix is to flatten EAV into a proper Go-owned schema — which requires DB separation.

### How to Execute Option A Safely (Non-Negotiable Constraints)

If you commit to Option A as a transitional state:

1. **Read-only constraint**: Go must only `SELECT` on Magento-owned tables. All writes must be proxied back to Magento's PHP API.
2. **Table ownership policy**: Document which tables Go may read. No undocumented reads allowed.
3. **Schema pinning CI check**: Run a schema diff on every Magento upgrade PR. If a column changes that Go references, block the build.
4. **Set a hard deadline for Phase 2**: Option A without a Phase 2 date on the calendar will become permanent by inertia.

---

## Option B — Evolutionary CDC + Outbox (Recommended Path)

```
┌──────────────┐              ┌──────────────────┐
│  PHP Magento │──WRITE──────▶│  MySQL Magento   │
└──────────────┘              │  (master)        │
                              └────────┬─────────┘
                                       │ binlog (no PHP changes needed)
                                       ▼
                               ┌──────────────┐
                               │  Debezium    │  ← reads binlog directly
                               │  CDC Engine  │
                               └──────┬───────┘
                                      │ stream events
                                      ▼
┌──────────────┐  WRITE-OWNED  ┌────────────────────────┐
│  Go (magento-go) │──────────────▶│  Go DB (separate)      │
│              │  READ-SYNCED  │  Flat schema            │
│              │◀──────────────│  token, session,        │
└──────────────┘               │  customer_flat...       │
        │                      └────────────────────────┘
        │ Outbox events (Go → Magento if needed)
        ▼
   ┌──────────┐
   │  Kafka   │──▶ Magento consumer
   └──────────┘
```

**The critical insight:** Debezium reads MySQL's binary log (`binlog`) directly. This means **you never need to modify a single line of PHP Magento code** to stream every data change into the Go database.

### How CDC + Outbox Works

**Step 1 — Go creates its own DB for data it owns:**
```sql
-- Go-owned tables (Go writes here, Magento never touches)
CREATE TABLE magento_customer_token (
  id UUID PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMP NOT NULL
);

CREATE TABLE magento_outbox (
  id UUID PRIMARY KEY,
  event_type VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  published_at TIMESTAMP
);
```

**Step 2 — Debezium streams Magento changes → Go DB:**
```yaml
# debezium-connector.yaml
connector.class: io.debezium.connector.mysql.MySqlConnector
database.hostname: magento-mysql-master
database.include.list: magento
table.include.list: magento.customer_entity, magento.catalog_product_entity
# Debezium reads binlog — zero Magento PHP changes required
```

**Step 3 — Go writes use Outbox Pattern (atomic):**
```go
// In a single DB transaction — no dual-write risk
tx.Exec(`INSERT INTO magento_customer_token (...) VALUES (...)`)
tx.Exec(`INSERT INTO magento_outbox (event_type, payload)
         VALUES ('TOKEN_CREATED', $1)`, tokenPayload)
// OutboxProcessor publishes to Kafka at 500ms intervals
// Debezium picks up the outbox row → routes to Magento if needed
```

### Why Option B Wins for Most Teams

| What you get | What you avoid |
|---|---|
| Go owns its schema — flatten EAV → 5× read speed | Never touch PHP Magento code |
| ACID writes on Go's own DB | No Saga complexity on Day 1 |
| Debezium streams Magento changes to Go | No dual-write race conditions |
| Per-domain rollout (Auth first, Checkout last) | No Big Bang cutover |

---

## Option C — Full DB Separation + Event Bus

```
┌─────────────────────────────────────────────────────────────┐
│                     EVENT BUS (Kafka)                        │
│  topic: customer.updated │ order.created │ inventory.changed │
└──────────┬───────────────────────────────┬──────────────────┘
           │ PUBLISH                       │ CONSUME
           ▼                               ▼
┌──────────────────┐          ┌───────────────────────────────┐
│  PHP Magento     │          │  Go Service (magento-go)           │
│                  │          │                                │
│  MySQL Magento   │          │  Go DB (owned, flat schema)   │
│  (fully owned)   │          │  CQRS read projections        │
│                  │          │  customer_flat, order_summary  │
│  ← Magento must  │          │                                │
│    publish ALL   │          └───────────────────────────────┘
│    state changes │                         │ PUBLISH
│    as events →   │◀────────────────────────┘
└──────────────────┘  (compensating events)
```

In Option C, both systems are completely isolated. Communication happens **exclusively through the event bus**. Each service owns its database entirely.

### What Option C Requires That Option B Does Not

The fundamental difference is **who publishes events**:

| | Option B (CDC) | Option C (Event Bus) |
|---|---|---|
| **Who publishes changes?** | Debezium reads binlog automatically | PHP Magento must write to outbox table |
| **PHP Magento code changes?** | ❌ None required | ✅ **Mandatory** — every state change needs an event |
| **Risk if PHP team is slow** | Zero (CDC is infrastructure) | High (Go DB will be missing data) |
| **Latency of sync** | 50–200ms (binlog lag) | 10–100ms (if Kafka is healthy) |
| **Event replay** | Yes (binlog history) | Yes (Kafka retention) |

**Option C is the right long-term target architecture.** But it requires the PHP Magento team to reliably emit domain events for *every* state change — customer updates, order status changes, inventory adjustments, promotion applications. Missing even one event category means Go's database silently diverges from Magento's.

---

## Full 3-Way Comparison Matrix

| Dimension | Option A: Shared DB | Option B: CDC + Outbox | Option C: Full Event Bus |
|---|---|---|---|
| **Consistency model** | Strong ACID ✅ | ACID writes, eventual reads ⚠️ | Eventual consistency ❌ |
| **Schema coupling** | Tight — Magento owns ❌ | Reduces per domain ⚠️ | Loose — event schema ✅ |
| **Write conflict risk** | High — race conditions ❌ | Low — owned writes ✅ | None — isolated ✅ |
| **EAV performance** | Unchanged ❌ | Flatten per domain ⚠️ | Full flatten ✅ |
| **Independent scaling** | No ❌ | Partial ⚠️ | Full ✅ |
| **Rollback Go service** | Trivial — flip routemode ✅ | Easy per domain ✅ | Hard — event schema backward compat ❌ |
| **Time to production** | Running now ✅ | 3–6 months ⚠️ | 9–18 months ❌ |
| **Magento code changes** | None ✅ | **None** (CDC reads binlog) ✅ | **Required** — event publisher ❌ |
| **New infrastructure** | None ✅ | Debezium + Kafka ⚠️ | Kafka + Schema Registry + CQRS ❌ |
| **Debug complexity** | Low ✅ | Medium ⚠️ | High — trace across hops ❌ |
| **Team skill required** | Low ✅ | Medium ⚠️ | High — distributed systems ❌ |
| **Fault isolation** | None — 1 DB = all fails ❌ | Partial ⚠️ | Full ✅ |
| **Checkout transaction safety** | ACID ✅ | Saga required ⚠️ | Saga + compensating tx ❌ |
| **Inventory oversell risk** | None (ACID) ✅ | Low if CDC lag < 100ms ⚠️ | High if consumer lags ❌ |
| **Data replay / audit** | None ❌ | Partial (Outbox) ⚠️ | Full (Kafka retention) ✅ |

---

## Risk Table Per Option

### Option A — Shared DB Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Magento upgrade breaks Go struct | **High** (every upgrade) | Service crash | Schema pinning + CI diff check |
| Write race condition on auth tables | **Medium** | Data corruption | Table ownership policy, Go read-only |
| DB bottleneck at scale | **High** | Both systems slow | Read replica for Go |
| Permanent distributed monolith | **Certain** without deadline | Architectural debt | Hard Phase 2 deadline |

### Option B — CDC Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| CDC pipeline failure | **Low** (Debezium HA) | Go DB out of sync | Lag monitoring + alerting |
| Duplicate event delivery | **Medium** | Duplicate records | Idempotency key on all consumers |
| MySQL binlog disk pressure | **Low** | Storage cost | binlog retention policy |
| Temporary dual-write window | **Medium** | Data drift | Outbox pattern from day one |

### Option C — Full Event Bus Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Magento emits incomplete events** | **Very High** | Go DB missing data | Integration test suite, mandatory |
| Event schema break | **High** (per business change) | Consumer crash | Schema Registry + backward compat |
| Saga failure → inconsistent order | **Medium** | Revenue impact | Dead-letter queue + manual review |
| Event storm during flash sale | **Medium** | Kafka backpressure | Topic partitioning + consumer lag SLA |
| Read-your-own-write lag | **High** | Poor UX after user action | Optimistic UI updates |

> **⚠️ Critical for Option C:** PHP Magento must write to an outbox table *within the same database transaction* as the business state change. This is often implemented incorrectly — publishing directly to Kafka after the DB commit creates a dual-write gap. If the Kafka publish fails, the event is lost silently and Go's database diverges permanently.

---

## Decision Framework — Which Option Is Right for You?

```
Q1: Does your team have 2+ engineers with distributed systems experience?
  └─ NO  → Stay on Option A, add guardrails (schema pinning, read-only policy)
  └─ YES → Q2

Q2: Is your inventory oversell tolerance exactly zero?
  └─ YES → Option B (CDC maintains ACID writes, no eventual consistency risk at write time)
  └─ NO  → Option B or C are both viable

Q3: Do you need Go to scale completely independently of Magento's DB?
  └─ NO  → Option B is sufficient and recommended
  └─ YES → Q4

Q4: Can the PHP Magento team commit to building and maintaining event publishers?
  └─ NO  → Option B is required (CDC needs no PHP changes)
  └─ YES → Option C is viable (timeline: 12–18 months)
```

{{< faq q="How long does a Magento database migration to Go take?" >}}
Option A (Shared DB) is running now — zero additional time. Option B (CDC + Debezium separation, domain by domain) takes **3–12 months** depending on team size and domain complexity: Auth/OIDC in 1–2 months, Customer read in 2–3 months, Cart/Checkout after Saga patterns are proven. Option C (Full Event Bus) requires **12–18 months** plus PHP Magento event publisher development before Go's database can be fully independent.
{{< /faq >}}

{{< faq q="What is the Outbox Pattern in microservices?" >}}
The **Transactional Outbox Pattern** solves the dual-write problem in event-driven systems. Instead of writing to the database AND publishing to Kafka in two separate operations (which can fail independently), you write the event to an `outbox` table **inside the same database transaction** as the business state change. A background processor (OutboxProcessor) then reads the outbox table and publishes events to Kafka at regular intervals — typically every 500ms. This guarantees that if the DB commit succeeds, the event will eventually be published, eliminating silent data loss.
{{< /faq >}}

{{< faq q="Can I use Debezium with Magento MySQL without changing PHP code?" >}}
Yes. Debezium is a Change Data Capture (CDC) tool that reads MySQL's binary log (`binlog`) directly — it does not require any application code changes. For Magento, you configure the [Debezium MySQL connector](https://debezium.io/documentation/reference/stable/connectors/mysql.html) to monitor specific tables (`customer_entity`, `catalog_product_entity`, etc.) and stream every INSERT/UPDATE/DELETE to Kafka or Redis Streams. The prerequisite is that MySQL `binlog` is enabled on your Magento database server (`log_bin = ON`), which is typically already the case on production MySQL instances configured for replication.
{{< /faq >}}

---

## Domain Priority — What to Separate First

Not all domains carry equal risk. Migrate in this order regardless of whether you choose Option B or C:

| Domain | Priority | Why | Risk |
|---|---|---|---|
| **Auth / Token** (`auth/`) | **First** | Go already owns token logic, zero Magento dependency | Low |
| **OIDC** (`oidc/`) | **First** | Fully Go-owned, no Magento data needed | Low |
| **Wishlist** (`wishlist/`) | Second | Simple domain, small data footprint | Low |
| **Customer read** (`customer/`) | Second | Flatten EAV → 5× read speed, write still proxied | Medium |
| **Customer write** | Third | Requires Saga with Magento for address/profile sync | Medium |
| **Cart / Checkout** (`cartcheckout/`) | **Last** | Highest business risk, requires mature Saga pattern | High |

**Never migrate Cart/Checkout to a separate DB until Saga patterns are proven in production on lower-risk domains.**

---

## Infrastructure Checklist Before DB Separation

Before committing to Option B or C, validate these prerequisites:

```yaml
required_before_option_b:
  - mysql_binlog_enabled: true          # Check with: SHOW VARIABLES LIKE 'log_bin'
  - debezium_or_dms: deployed           # Debezium embedded or standalone
  - kafka_or_redis_streams: deployed    # Message transport for CDC events
  - outbox_table: created_in_go_db      # magento_outbox table schema defined
  - idempotent_consumers: implemented   # Every consumer has idempotency key check
  - cdc_lag_monitoring: configured      # Alert if lag > 500ms

additional_for_option_c:
  - php_event_publisher: implemented    # Magento module writing to outbox table
  - schema_registry: deployed           # Avro or Protobuf schema management
  - saga_orchestrator: stable           # Proven in production on non-critical domain
  - dead_letter_queue: configured       # For failed saga compensation
```

---

## Recommended Roadmap

```
0–6 months (NOW)             6–12 months                12–24 months
────────────────             ───────────                ────────────
Option A + Guardrails   →    Option B: CDC              Option B → C (gradual)
                              Auth/OIDC DB first
Table ownership policy        Debezium streaming         Only when PHP team
Schema pinning CI check       Flatten EAV reads          can publish events
routemode shadow mode         Wishlist + Customer        Saga pattern proven
Hard Phase 2 deadline set     read separation            Cart/Checkout LAST
```

---

## See Also

### Series Deep-Dives

- **[Part 5: EAV Schema Migration — Magento's Biggest Trap](/series/composable-commerce-migration/part-5-eav-schema-migration/)** — The exact SQL queries to flatten `catalog_product_entity_varchar` and other EAV tables into performant Go-owned schemas
- **[Part 6: Phase 1 — Strangler Fig: Read-Only Migration + CDC](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)** — Implementation detail: Debezium config, feature flags, Go service code
- **[Part 7: Phase 2 — Dual-Write with Dapr PubSub](/series/composable-commerce-migration/part-7-phase2-dual-write/)** — Bidirectional sync, conflict resolution, feature flag rollout
- **[Part 9: Transactional Outbox + Saga Pattern](/series/composable-commerce-migration/part-9-outbox-saga/)** — PostgreSQL outbox implementation, choreography saga, idempotency keys
- **[Part 10: ADR Walkthrough — 24 Architecture Decisions](/series/composable-commerce-migration/part-10-adr-walkthrough/)** — Every major decision (Dapr vs Kafka, DB-per-service, gRPC vs REST) with trade-offs

### Related Posts

- **[Zero-Downtime: Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/)** — End-to-end 3-phase migration execution playbook with Debezium and Dapr bidirectional sync
- **[Migrating Magento to Microservices: When & Why](/posts/why-migrate-magento-to-microservices/)** — Decision triggers, EAV performance limits, and the migrate/don't-migrate checklist

### External References

- **[Debezium MySQL Connector Documentation](https://debezium.io/documentation/reference/stable/connectors/mysql.html)** — Official setup guide for CDC from MySQL binlog
- **[Adobe: Magento 2.4.6 Split Database Deprecation](https://experienceleague.adobe.com/docs/commerce-operations/configuration-guide/storage/split-db/split-db.html)** — Adobe's official notice deprecating the split database feature in Magento 2.4.6+
