---
title: "Go Engineers in Vietnam: Vetting for Magento Migration"
slug: "go-engineers-vietnam-migration-vetting"
author: "Lê Tuấn Anh"
date: "2026-07-08T19:30:00+07:00"
lastmod: "2026-07-08T19:30:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Golang", "Vietnam", "Hiring", "Microservices", "Migration", "Interview", "Magento"]
categories: ["Engineering Management", "Hiring"]
description: "Five interview scenarios to vet Go engineers in Vietnam for Magento migration — not greenfield skills. Covers Saga, CDC, dual-write, UUID mapping."
ShowToc: true
TocOpen: true
cover:
  image: "images/series/go-engineers-vietnam-vetting-cover.png"
  alt: "Vetting Go engineers in Vietnam for Magento migration projects"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/go-engineers-vietnam-migration-vetting/"
---

**Answer-first:** Vetting Go engineers for Magento migration requires a different interview framework than greenfield hiring. The critical signal is not Go syntax fluency — it's distributed systems experience under legacy coupling constraints. Five production scenarios reveal whether a candidate can actually own migration work versus only build clean APIs from scratch.

> **Series context:** This post is part of the [E-Commerce Re-Architecture in Vietnam](/series/magento-migration-vietnam/) series. For background on the migration architecture this team will execute, read [Zero-Downtime: Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/) first.

---

## Why Generic Go Interviews Fail for Migration Work

Most Go interview guides test the wrong skills for migration projects.

They evaluate goroutine syntax, channel patterns, and clean API design — all relevant for greenfield services. But a Magento→Go migration engineer's job in months 1–6 is not building clean services. It's running two systems simultaneously without losing orders.

The failure profile looks like this: a candidate passes every standard Go interview. They join the migration team. In week 3, they try to replace Magento's `quote` table logic with a direct service cutover — not understanding that `quote` is coupled to 6 extensions, 2 payment gateways, and 15 Magento observers. The team loses 3 weeks recovering from a bad dual-write setup.

The skills that prevent this failure are not taught in Go courses. They come from experience with: Saga patterns, CDC (Change Data Capture), dual-write consistency, and legacy data mapping.

Here are the five interview scenarios that surface these skills — or their absence.

---

## The Vetting Framework: What Migration Engineers Actually Do

Before the scenarios, understand the three phases of a Strangler Fig migration and which engineer skills each phase requires:

| Phase | Duration | Critical Skills |
|-------|----------|----------------|
| **Phase 1:** Dual-read setup | Weeks 1–6 | Debezium CDC, event schemas, read routing |
| **Phase 2:** Dual-write + validation | Weeks 7–16 | Saga orchestration, idempotency, reconciliation workers |
| **Phase 3:** Cutover + hot standby | Weeks 17–24 | Feature flags, traffic splitting, rollback readiness |

An engineer who can only do Phase 3 is a deployment engineer, not a migration architect. The value is in Phases 1 and 2.

---

## Scenario 1: Decomposing the `sales_order` EAV Table

**The question:**

> "Our Magento `sales_order` table has 90+ columns. In addition, order attributes are spread across `sales_order_varchar`, `sales_order_int`, `sales_order_decimal`, and `sales_order_text`. How do you decompose this into bounded contexts in your Go service design? What are the first 3 data modeling decisions you make?"

**What a strong answer looks like:**

- Identifies that `sales_order` is NOT one bounded context — it contains Order (business contract), Fulfillment (logistics state), Payment (financial record), and Customer Reference (identity link) as separate domains
- Immediately surfaces the EAV-to-flat-model problem: EAV joins require 10–15 JOINs per product query; the first migration step is building a projection (materialized view) in a flat Postgres table
- Asks: "Which attributes are core order data versus which are extension-injected?" — because Magento extensions inject attributes into the EAV tables, and these must be audited separately
- Proposes an `order_id` bridge: keeps Magento's integer `entity_id` mapped to new UUID via an `order_id_map` table during dual-write phase

**Red flags:**
- "We'd just SELECT * from sales_order and map to a Go struct" — shows no understanding of EAV structure
- No mention of extension-injected attributes — will discover them in production
- Proposes creating the UUID schema immediately without addressing the `magento_id_map` bridge

**The EAV problem in numbers:** Magento's EAV model joins 10–15 tables per product query. One category page load triggers 200–500 SQL queries on an unoptimized store. The first migration deliverable is eliminating this overhead via a flat Postgres projection.

---

## Scenario 2: The Integer-to-UUID Translation Problem

**The question:**

> "Magento uses sequential integer `entity_id` values across all core tables. Your new Go microservices use UUID v4. You're in a dual-write phase where both systems process orders simultaneously. How do you design the ID translation layer, and where does it live?"

**What a strong answer looks like:**

- Proposes a dedicated `magento_id_map` table (or service) that maps every Magento integer ID to its corresponding UUID — not embedded logic in individual services
- Understands the write-order problem: when a new order is created, which system generates the canonical ID? (Answer: during migration, Magento generates the integer ID first; the new service assigns UUID and registers the mapping atomically)
- Handles the "gap" problem: Magento's auto-increment IDs can have gaps (failed transactions, deleted records). The migration worker must account for these without treating them as missing records
- Discusses what happens at cutover: once Magento is decommissioned, the `magento_id_map` becomes read-only historical reference for order history lookups

**Red flags:**
- "We'd use the Magento integer ID as the UUID" — not a UUID, breaks distributed ID generation assumptions
- No mention of atomicity during mapping registration — creates race conditions under dual-write
- No plan for historical order lookups post-cutover

**Why this matters:** A system without a clean ID translation layer creates silent data corruption during dual-write. Orders appear in one system but not the other. Support tickets spike. The rollback happens in production.

---

## Scenario 3: Debezium CDC vs. Polling — When and Why

**The question:**

> "We're evaluating how to sync Magento MySQL updates to our Go inventory service during dual-write. Should we use Debezium CDC (MySQL binlog streaming) or a polling worker that queries `updated_at > last_checked`? Make the call and justify it."

**What a strong answer looks like:**

- Chooses Debezium CDC for the inventory sync specifically — because inventory changes happen at high frequency during flash sales (stock reservations, releases, adjustments), and polling on `updated_at` misses rapid successive updates that overwrite each other within one polling interval
- Articulates the binlog advantage: Debezium captures every row-level change, not just the last state — critical for inventory where a stock reservation followed immediately by a release looks like "no change" to a polling worker
- Identifies where polling is acceptable: low-frequency, low-risk data like product descriptions, category assignments, customer profile updates
- Discusses the operational cost: Debezium requires MySQL binlog enabled, Kafka as the event backbone, schema registry for CDC event schemas — not free to operate, justified only for high-frequency or high-criticality data

**Red flags:**
- "Polling is simpler, let's start there for everything" — will lose inventory events under load
- No awareness of Debezium's binlog prerequisites
- Treats CDC as always the right answer without knowing the operational cost

**Tiki Vietnam uses this stack:** Tiki's engineering team runs Kafka for event-driven async workflows between services — the same architectural pattern Debezium feeds. This is not theoretical; it's the production standard for Vietnam's top e-commerce platform.

---

## Scenario 4: Saga Compensation vs. Database Rollback

**The question:**

> "A customer places an order. Your Order service creates the order (Go). The Inventory service reserves stock (Go). The Payment service charges the card (Go). The Payment charge fails. How do you roll back the inventory reservation? Walk me through exactly how you implement this."

**What a strong answer looks like:**

- Correctly identifies this as a Saga pattern scenario — specifically the **Choreography Saga** for simpler flows or **Orchestration Saga** for complex ones
- For inventory rollback: the Payment service publishes a `payment.failed` event to Kafka; the Inventory service subscribes and executes a compensating transaction (`ReleaseStockReservation`) with the original `reservation_id`
- Emphasizes idempotency: the compensating transaction must be safe to execute multiple times (at-least-once delivery from Kafka means duplicates happen). The `reservation_id` is the idempotency key
- Discusses what happens if the compensating transaction itself fails: dead-letter queue, manual intervention runbook, and Slack alert to the on-call engineer
- Does NOT suggest database-level 2PC (two-phase commit) — correctly identifies that distributed 2PC across Go microservices is impractical and breaks service isolation

**Red flags:**
- "We'd use a database transaction that spans both services" — 2PC in distributed systems, shows monolith thinking
- No mention of idempotency — will create double-compensations under message redelivery
- No plan for compensation failure — assumes compensating transactions always succeed

**The consultant's take:** In practice, most teams underestimate Saga complexity by 40–60% during scoping. The rollback logic alone for a 4-service checkout requires 8 compensating transactions, each with its own idempotency mechanism. Budget for this explicitly.

---

## Scenario 5: Strangler Fig Feature Flag Architecture

**The question:**

> "You're running Magento and Go checkout in parallel. You need to route 5% of checkout traffic to the new Go service for validation, then ramp to 50%, then 100% over 6 weeks. How do you implement this without modifying the frontend? Where does the routing logic live?"

**What a strong answer looks like:**

- Routes at the **API gateway layer** (Kong, Nginx, or AWS ALB) — not in the frontend, not in either backend service. This keeps both services unaware of the split
- Uses a **session-stable hash** (e.g., hash of `customer_id mod 100 < 5`) rather than random routing — ensures a customer who starts checkout on the Go service completes it there, not mid-flow on Magento
- Builds a **shadow mode** capability: Go service receives all requests but only writes to its own database when the customer is in the target percentage; otherwise processes but discards the result. This allows validation without write risk
- Defines **graduation criteria** before starting traffic ramp: error budget < 0.1%, P99 latency < 200ms, at least 7 days at each traffic level before advancing
- Plans the **kill switch**: a single feature flag toggle that routes 100% back to Magento within 30 seconds if error budget burns

**Red flags:**
- Routing logic in the frontend ("we'd add a JavaScript A/B flag") — creates visible flicker and can't easily be killed
- No session stability — customers mid-checkout get randomly routed between systems
- No graduation criteria — "we'll just watch it and increase traffic when it seems okay"

---

## The Vietnamese Go Ecosystem: Why This Pool Exists

There is a common assumption that Vietnam engineers are primarily strong in Java/PHP and weak in Go. The data contradicts this for senior-level talent.

**Evidence of Vietnam Go production maturity:**
- **ZaloPay** — Vietnam's leading digital payment app — maintains a public Go OSS library covering distributed transactions, circuit breakers, and fault tolerance patterns (confirmed via github.com)
- **Tiki** — Vietnam's #2 e-commerce platform — runs Go microservices on GKE, confirmed via multiple sources including tiki.vn engineering job postings
- **200lab.io** — Vietnam-based Go + microservices training platform actively training the pipeline
- **ITviec Go job postings** — Companies actively hiring senior Go engineers include Tiki, Sendo, ZaloPay, MoMo, One Mount Group, Kyanon Digital, and Dwarves Foundation

The engineer who has built production Go services at Tiki or ZaloPay has solved the exact same distributed transaction problems you need for a Magento migration. The salary difference is not a quality difference — it's a market difference.

---

## Green Signals and Red Flags Summary

**Green signals — hire for migration:**

| Signal | Why it matters |
|--------|---------------|
| Can describe a Saga they implemented, with compensation failure handling | Production Saga experience, not textbook |
| Has worked on a "strangler fig" or incremental service extraction (any language) | Understands the dual-system operational overhead |
| Understands idempotency and can give a concrete implementation | Critical for dual-write correctness |
| Can explain why 2PC doesn't work across microservices | Distributed systems thinking, not monolith thinking |
| Has production Kafka/Debezium experience | Will not underestimate CDC operational cost |
| Can describe a production incident they diagnosed with distributed tracing | Real production debugging experience |

**Red flags — do not hire for migration:**

| Red Flag | Risk |
|----------|------|
| "We'd just SELECT * from the Magento table" | Will miss EAV complexity entirely |
| Only Gin CRUD API experience | No distributed systems exposure |
| "Yes" to every requirement in the first call | Saving-face response — needs probing |
| Cannot explain goroutine scheduler basics | Greenfield-only; won't debug concurrency in production |
| Never used `go race` or pprof | No production debugging tools experience |
| No experience with message queues | Cannot implement event-driven migration sync |

---

## Practical Hiring Process

**Step 1 — Technical screen (1 hour):**
Use Scenarios 2 and 4 above. These are the quickest signal: ID translation reveals data modeling maturity; Saga compensation reveals distributed systems depth.

**Step 2 — Architecture review (2 hours):**
Ask the candidate to design a dual-write sync architecture for inventory, starting from a whiteboard. Evaluate their identification of failure modes, not just the happy path.

**Step 3 — Code review (take-home, 48 hours):**
Provide a simplified Magento `sales_order` table schema. Ask them to write a Go CDC event handler that processes `order.updated` events idempotently and updates a flat Postgres projection. Evaluate: idempotency key design, error handling, context propagation.

**Step 4 — Reference check:**
Ask specifically: "Did this engineer work on a migration or refactoring project, or only on greenfield services?" Past migration experience is the single best predictor of success on your project.

---

## FAQ

### How many senior Go engineers with migration experience exist in Vietnam?

The pool is smaller than greenfield Go engineers but real and growing. Estimate 200–400 senior engineers in Ho Chi Minh City and Hanoi with both Go production experience and distributed systems depth appropriate for migration work. Companies like Tiki, ZaloPay, and One Mount Group have trained a generation of this talent.

### What's the difference in vetting time vs. greenfield hiring?

Expect 30–40% more interview time per candidate. Migration vetting requires 2 substantive technical rounds (not just 1 coding screen) because the failure modes are more expensive. A bad greenfield hire adds tech debt. A bad migration hire causes production incidents.

### Should I prioritize Go experience or migration experience?

Migration experience in any strongly-typed language (Java, Kotlin, Rust) plus Go proficiency is better than deep Go greenfield plus no migration context. The distributed systems concepts transfer; the Go syntax is learnable in weeks.

### What's the right team composition for a Magento migration?

For a 12-month B2B migration:
- 1 Go architect / tech lead (migration experience mandatory)
- 2–3 senior Go engineers (distributed systems background)
- 1 Go mid-level engineer (under direct tech lead mentorship)
- 1 DevOps/platform engineer (Kubernetes, Kafka, Debezium ops)
- 0.5 QA engineer (integration testing focus)

Total: 5.5–6 engineers. At Vietnam rates ($2,800–$4,500/month senior, $1,800–$2,800/month mid), this team costs $180,000–$270,000/year in direct labor.

---

*Next in series: [Magento Migration Cost: Vietnam vs US/EU Team (2026 Model) →](/series/magento-migration-vietnam/magento-migration-cost-vietnam-vs-us-eu/)*

*Previous: [Vetting Magento Developers in Vietnam: Interview Playbook →](/posts/magento-developers-in-vietnam/)*
