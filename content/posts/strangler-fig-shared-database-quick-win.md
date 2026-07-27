---
title: "Magento Migration: Shared DB, CDC, or Event Bus?"
description: "Magento database migration decision guide: compare Shared DB, CDC + Debezium, and Event Bus separation with a 16-dimension risk evaluation matrix."
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

# Magento Migration: Shared DB, CDC, or Event Bus?

> **Answer-First:** Migrating a Magento monolith using the Strangler Fig pattern requires choosing between three data migration strategies: Shared Database (quickest compute win, temporary EAV query bottleneck), Change Data Capture / Debezium (automated async sync to Go microservice DBs), and Event Bus separation (cleanest microservice decoupling, requiring PHP codebase modification).

- Why Go running against Magento's MySQL is faster at the compute layer but still bottlenecked at the EAV query layer — and what actually fixes it.
- The single deciding factor between CDC (Option B) and Event Bus (Option C): who owns the PHP Magento codebase.

---

> This post is part of the **[Composable Commerce Migration series](/series/composable-commerce-migration/)** — a step-by-step playbook for migrating Magento 2 to Go microservices. For the full migration execution guide, see [Part 6: Phase 1 Strangler Fig](/series/composable-commerce-migration/part-6-phase1-strangler-fig/).

## The Strangler Fig Dilemma: Compute vs. Data

Migrating monolithic e-commerce platforms like Magento to Go microservices presents software architects with a crucial decision regarding compute and data separation timelines. Decoupling application API compute layers before refactoring underlying relational databases allows engineering teams to achieve immediate execution latency gains while systematically designing long-term data isolation strategies across modern 2026 systems.

Migrating both simultaneously requires setting up Eventual Consistency, Dual-Writes, and Saga patterns from Day 1. This delays time-to-market and prevents the business from seeing performance improvements for 9–18 months.

The alternative is the **Shared Database Quick Win** — migrate the API compute layer first, keep the data layer intact, and buy time to architect a proper DB separation strategy.

But "buy time" only works if you have a clear plan for Phase 2. This post defines all three options and gives you a decision framework to pick the right path.

---

## Three Options on the Table

Decomposing monolithic e-commerce databases into modular microservices requires evaluating three core architectural migration paths. Engineering leaders must balance immediate compute performance gains against operational complexity, transaction consistency boundaries, legacy codebase modification requirements, and long-term service autonomy when choosing between shared database access, Change Data Capture pipelines, and event bus architectures in 2026.

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

Option A allows new microservices to read and write directly to tables within the existing legacy monolith database. While this approach minimizes initial migration effort and avoids immediate data sync pipelines, it retains database coupling, increases schema mutation risk, and delays true microservice isolation.

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

Connecting separate runtime services directly to a shared database schema creates a distributed monolith architecture. The diagram below illustrates how shared database coupling compromises microservice autonomy:

```
Go service ───────▶ Shared MySQL ◀─────── PHP Magento
    ↑                                           ↑
"microservice"                       monolithic coupling in practice
```

You now have two separate runtimes but **one failure domain**. A Go query that performs a full-scan on `catalog_product_entity_varchar` degrades Magento's checkout performance. This is architecturally identical to a monolith — it is just harder to debug because two codebases are involved.

#### Dark Side 4: EAV Is the Real Bottleneck — Go Doesn't Fix It

Go executes database queries with minimal runtime overhead, but the execution plan remains bound by EAV schema complexity. The SQL query below illustrates the expensive multi-table join structure required to hydrate a single customer entity from Magento's EAV schema:

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

Adopting Change Data Capture alongside transactional outbox patterns allows microservices to stream database state updates asynchronously without modifying legacy monolith source code. By capturing MySQL binary log events with Debezium and processing outbox tables in Go, backend teams achieve eventual consistency, eliminate dual-write hazards, and flatten EAV data schemas across 2026 cloud deployments.

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

**Step 1 — Go creates its own DB for data it owns:** To decouple write paths, the Go microservice provisions standalone tables for session tokens and transactional outbox events. The SQL DDL below creates dedicated tables uncoupled from Magento's schema:

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

**Step 2 — Debezium streams Magento changes → Go DB:** Debezium monitors database binlogs to replicate committed changes without application intervention. The YAML configuration below specifies table inclusion filters for CDC streaming:

```yaml
# debezium-connector.yaml
connector.class: io.debezium.connector.mysql.MySqlConnector
database.hostname: magento-mysql-master
database.include.list: magento
table.include.list: magento.customer_entity, magento.catalog_product_entity
# Debezium reads binlog — zero Magento PHP changes required
```

**Step 3 — Go writes use Outbox Pattern (atomic):** To guarantee that local database updates and outgoing events commit atomically, the Go service executes outbox writes inside the primary database transaction. The Go snippet below illustrates atomic outbox event insertion:

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

Option C enforces immediate database isolation by provisioning independent, dedicated datastores for each microservice from day one. Communication across domain boundaries occurs strictly via asynchronous domain events and strongly-typed gRPC interfaces, ensuring strict domain boundary enforcement, zero schema sharing, and maximum operational team autonomy.

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

Selecting the appropriate database migration pattern requires evaluating technical, operational, and organizational tradeoffs across multiple system dimensions. The comparative breakdown below evaluates Shared Database, Change Data Capture, and Full Event Bus architectures across transactional consistency models, schema coupling risks, implementation timelines, and operational maintenance overhead for 2026 microservice migrations.

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

Every database migration strategy carries specific architectural risks and operational trade-offs that impact production reliability. Engineering teams must evaluate potential schema breakage, race conditions, streaming pipeline failures, and event divergence scenarios, implementing targeted engineering mitigations and automated validation checks to safeguard system stability across 2026 production environments.

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

Evaluating which data migration pattern fits your organization requires balancing team experience, transaction safety limits, and target timelines. Engineering leaders should assess distributed systems expertise, database transaction guarantees, and migration speed before choosing between shared database, change data capture, or event-driven patterns. The decision tree below provides a structured evaluation path.

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

## Frequently Asked Questions

Below are answers to fundamental technical questions regarding Magento database migration strategies, Change Data Capture (CDC) setups with Debezium, and Transactional Outbox pattern implementations. These concise responses summarize practical architectural guidance for decoupling legacy monoliths, eliminating EAV bottlenecks, and ensuring data consistency across modern 2026 microservices.

### How long does a Magento database migration to Go take?

Option A (Shared DB) executes immediately as a compute-only proxy phase. Option B (CDC + Debezium domain separation) takes 3 to 12 months depending on domain complexity, migrating Auth in 1 to 2 months and Checkout after Saga patterns mature. Option C (Full Event Bus) requires 12 to 18 months along with dedicated PHP event publisher development.

### What is the Outbox Pattern in microservices?

The Transactional Outbox Pattern eliminates dual-write race conditions in distributed microservices. Instead of attempting independent writes to a database and message queue, outbox records are committed inside the primary database transaction. An asynchronous worker process then publishes committed events to Kafka at regular intervals.

### Can I use Debezium with Magento MySQL without changing PHP code?

Yes, Debezium operates directly against MySQL binary logs (`binlog`) at the infrastructure layer without requiring PHP codebase modifications. By capturing row-level changes asynchronously, Debezium streams catalog and customer events into Kafka topics with sub-100ms latency.

---

## Domain Priority — What to Separate First

Sequencing microservice database separation requires categorizing domain services by business risk, data complexity, and transactional dependencies. Engineering teams should prioritize low-risk domains like authentication tokens and wishlists before refactoring complex customer schemas or high-stakes cart and checkout transaction ledgers across multi-phase 2026 migration roadmaps.

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

Before committing to Option B or C, validate these prerequisites. The checklist below details the mandatory observability, deployment, and data migration prerequisites. Before executing a database split, ensure your infrastructure platform satisfies essential observability, security, and transaction safety requirements. The checklist below details the mandatory prerequisites and deployment safeguards for a safe production migration.

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

Transitioning from a shared database to full microservice independence should occur incrementally across distinct development phases. Engineering teams must establish operational guardrails during early read-only phases before decoupling high-risk transactional domains. Maintaining strict phase boundaries prevents premature architecture complexity while ensuring continuous feature delivery. The timeline below outlines the recommended multi-stage migration strategy.

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

To deepen your understanding of microservice migrations and database decoupling patterns, review our complementary technical guides and reference documentation. These resources provide step-by-step implementation details covering EAV schema flattening, Change Data Capture configurations with Debezium, transactional outbox implementations, and architecture decision records for enterprise 2026 systems.

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
