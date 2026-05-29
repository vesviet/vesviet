---
title: "Part 2 — Handling the Surge: Event-Driven & Kafka"
date: 2026-05-05T21:00:00+07:00
draft: false
description: "How PayPay uses Apache Kafka as a shock absorber for payment spikes, implements Outbox Pattern, and guarantees exactly-once processing for financial ledgers."
weight: 3
---

## The Danger of Synchronous Processing

During a massive campaign launch — a sudden 50% cashback flash event, or a billion-yen giveaway — the TPS (Transactions Per Second) can jump **100x in a matter of seconds**. Millions of users open the app simultaneously, see the promotion banner, and tap "Pay" within the same 30-second window.

If the architecture is purely synchronous:

```
User App → API Gateway → Payment Service → Ledger Service → Database
```

That spike instantly exhausts database connection pools. The Ledger Service times out waiting for connections. Those timeouts cascade back to the Payment Service, which cascades back to the API Gateway, which returns errors to every user. The app effectively crashes — just when it has the most users and the most revenue potential. This is the scenario that broke PayPay in December 2018.

## The Event-Driven Buffer: Kafka as the Shock Absorber

To protect the core financial ledger from direct traffic pressure, PayPay routes all user-initiated events through **Apache Kafka** before they ever touch the database. This transforms the architecture from synchronous (request-response) to asynchronous (publish-subscribe):

```
User App → API Gateway → Edge Service
              → Validates lightweight pre-conditions
              → Publishes event to Kafka topic
              → Returns 202 Accepted (milliseconds)
                         ↓
              Kafka Topic (durable, ordered queue)
                         ↓
              Consumer Service
              → Pulls events at controlled rate
              → Writes to TiDB payment ledger
              → Processes cashback grants, fraud checks
```

The key insight: the **user receives a response immediately** (within milliseconds), while the actual ledger write happens asynchronously at the rate the database can safely handle. The user might see a brief "Processing" state in the app, but their transaction is safely queued and guaranteed to complete. Kafka acts as a massive **shock absorber** between the chaotic traffic layer and the sensitive financial data layer.

## Kafka Topic Design for Payments

Not all events are equal. PayPay organizes Kafka topics around business domains, with careful attention to partitioning:

**Core payment topics:**
- `transaction-events` — P2P transfers, merchant payments, balance debits
- `account-updates` — balance changes, KYC status transitions
- `campaign-events` — cashback grants, coupon claims, point distributions
- `fraud-signals` — anomaly events for real-time risk scoring

**Partitioning strategy:** Events are produced with a key of `user_id` or `account_id`. Kafka routes all events with the same key to the same partition, guaranteeing that events for a single user are processed in order. Without this, a user could have two concurrent cashback claims processed out of order — crediting the same coupon twice.

**Schema management:** PayPay uses a **Schema Registry** to manage message format evolution. As the Payment Service adds new fields to its event schema, the Schema Registry ensures backward compatibility — old consumers can still process messages produced by newer producers without breaking.

**Retention policy:** Financial audit logs require longer Kafka retention than transient operational events. Payment-related topics maintain extended retention periods for compliance; notification and analytics topics use shorter windows for cost efficiency.

## The Transactional Outbox Pattern

Kafka solves the throughput problem, but introduces a subtle consistency risk: the **dual-write problem**.

Naive implementation: a service writes the payment state to the database, *then* publishes an event to Kafka. What happens if the service crashes between those two operations? The database has the payment recorded, but the downstream Kafka consumers never receive the event — so the fraud detection service, the notifications service, and the campaign processor never know the payment happened. The database and the event stream are now **inconsistent**.

PayPay solves this with the **Transactional Outbox Pattern**:

```
Payment Service receives event:
  ┌─────────────────────────────────────────────┐
  │  BEGIN TRANSACTION (same DB transaction)    │
  │  1. Write payment state to payments table   │
  │  2. Write event record to outbox table      │
  │  COMMIT TRANSACTION                         │
  └─────────────────────────────────────────────┘
                    ↓
  CDC Process (TiCDC or Debezium):
  - Tails outbox table for new rows
  - Publishes event to Kafka
  - Marks outbox record as published
```

Because both the payment state and the outbox record are written in the **same atomic database transaction**, they either both succeed or both fail. There is no window where the database has the payment but Kafka does not have the event. The CDC process handles Kafka publishing asynchronously, but it guarantees eventual publication as long as the database transaction committed.

This pattern is critical for financial systems: it makes the database the authoritative source of truth for both state *and* event publication intent.

## The Full Idempotency Stack

Even with Kafka and the Outbox Pattern, distributed systems face network retries, consumer restarts, and at-least-once delivery semantics. PayPay implements a **four-layer idempotency stack** to ensure that no transaction is processed more than once, regardless of retries:

### Layer 1 — Idempotency Key (Client-Generated UUID)

Every payment request from the mobile client carries a unique UUID — the **Idempotency Key** — generated by the app before the request is sent. If the app retries a timed-out request (which it does automatically), it reuses the same UUID. The server recognizes the duplicate and returns the previously computed result without re-processing.

### Layer 2 — Idempotency Store (Redis)

Before the Payment Service processes any event, it checks **Redis** for the idempotency key:

```
Check Redis:
  - Key exists → return cached result (skip processing)
  - Key missing → process event, store result in Redis, return result
```

Redis provides O(1) lookup with microsecond latency — far cheaper than a database query for every incoming event.

### Layer 3 — Kafka Idempotent Producer

On the Kafka producer side, PayPay sets `enable.idempotence=true`. The Kafka broker assigns each producer a Producer ID (PID) and tracks sequence numbers per partition. If a producer retries a send (due to network timeout), the broker detects the duplicate sequence number and discards the duplicate — no duplicate message reaches consumers.

### Layer 4 — Idempotent Consumer (DB-Level Check)

As a final defense, the consumer service performs a database-level check on the event ID before committing the ledger write. If the record already exists, the consumer acknowledges the Kafka offset and moves on — no double-write. This catches edge cases where the Redis cache was cold or the consumer restarted mid-processing.

## Exactly-Once Semantics (EOS) in Practice

Beyond the application-level idempotency stack, PayPay leverages Kafka's **Exactly-Once Semantics** for the highest-criticality payment flows:

- **Manual offset commits only:** `enable.auto.commit=false` — the consumer commits its Kafka offset only *after* the database write succeeds. If the consumer crashes between consuming the message and writing to the database, Kafka redelivers the message on restart.
- **Kafka Transactions:** For complex flows involving multiple downstream topics, Kafka's transactional API allows the consumer to commit the offset and produce new events as a single atomic operation. Either all succeed or all are rolled back.

**Consumer lag as the primary health signal:** In PayPay's monitoring setup, consumer lag on payment topics is the first metric that alerts on-call engineers. A lag spike on `transaction-events` means payment processing is falling behind — before any user reports a delay. This leading indicator allows the Platform SRE team to scale consumers or throttle upstream traffic before user impact occurs.

For a broader perspective on event-driven patterns in Golang-based systems, see the [event-driven architecture with Dapr](/posts/mastering-event-driven-architecture-dapr/) post — many of the Kafka idempotency principles apply equally to Dapr's pub/sub model.
