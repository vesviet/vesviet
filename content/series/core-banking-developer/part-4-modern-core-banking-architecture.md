---
title: "Part 4 — Modern Core Banking Architecture (Microservices & Event-Driven)"
date: 2026-05-06T18:00:00+07:00
draft: false
description: "How next-generation digital banks escape monolithic legacy architectures and build Core Banking using Microservices, Event Sourcing, CQRS, and the Saga Pattern."
weight: 5
---

## From Monolith to Modern Core Banking

Traditional Core Banking systems (like T24 or Flexcube) are built with a **Monolithic** architecture — the entire business logic (CIF, CASA, Lending, GL, Payments...) runs in one massive application. This leads to:

- **High-risk deployments:** Modifying a small module requires redeploying the entire system.
- **Inefficient scaling:** You cannot scale just the Payments module during peak loads without scaling everything else.
- **Technology lock-in:** Bound to a single programming language and database.

The current trend is transitioning to **Headless Core Banking** — decoupling the domain logic from the delivery channels (Mobile App, Internet Banking, ATM).

---

## Overall Architecture

```
                    ┌─────────────────────────────────────┐
  CHANNELS          │  Mobile App  │  Internet Banking  │  ATM/POS  │
                    └──────────────────────┬──────────────────────────┘
                                           │ REST/gRPC
                    ┌──────────────────────▼──────────────────────────┐
  API GATEWAY       │         API Gateway (Auth, Rate Limit, Routing)  │
                    └──────────────────────┬──────────────────────────┘
                                           │
         ┌─────────────────────────────────┼──────────────────────────┐
         │                                 │                          │
  ┌──────▼──────┐               ┌──────────▼─────────┐    ┌──────────▼──────────┐
  │ CIF Service │               │  Account Service   │    │ Payment Service     │
  │ (Customer)  │               │  (CASA, GL)        │    │ (Transfers, Fees)   │
  └─────────────┘               └────────────────────┘    └─────────────────────┘
         │                                 │                          │
         └─────────────────────────────────┼──────────────────────────┘
                                           │ Events (Kafka/Dapr)
                    ┌──────────────────────▼──────────────────────────┐
  EVENT BUS         │              Message Broker (Kafka / Redis)      │
                    └──────────────────────┬──────────────────────────┘
                                           │
         ┌─────────────────────────────────┼──────────────────────────┐
         │                                 │                          │
  ┌──────▼──────┐               ┌──────────▼─────────┐    ┌──────────▼──────────┐
  │ Loan Service│               │ Notification Svc   │    │ Reporting Service   │
  │ (Lending)   │               │ (SMS, Push, Email) │    │ (CQRS Read Side)    │
  └─────────────┘               └────────────────────┘    └─────────────────────┘
```

---

## Pattern 1: Event Sourcing for the Ledger

In traditional architectures, we store the **current state**. In Event Sourcing, we store a **sequence of immutable events** that produce that state.

### Why does Event Sourcing fit Core Banking?

The ledger is already essentially Event Sourcing — every entry is an immutable event. The current balance is simply the result of **replaying** all entries from the beginning.

```go
// Events in the Account domain
type AccountOpened struct {
    AccountID    string
    CIFNumber    string
    Currency     string
    OpenedAt     time.Time
}

type MoneyDeposited struct {
    AccountID     string
    Amount        int64
    TransactionID string
    OccurredAt    time.Time
}

type MoneyWithdrawn struct {
    AccountID     string
    Amount        int64
    TransactionID string
    OccurredAt    time.Time
}

// Calculate balance by replaying events
func calculateBalance(events []Event) int64 {
    var balance int64
    for _, event := range events {
        switch e := event.(type) {
        case MoneyDeposited:
            balance += e.Amount
        case MoneyWithdrawn:
            balance -= e.Amount
        }
    }
    return balance
}
```

---

## Pattern 2: CQRS — Command Query Responsibility Segregation

Core Banking has a unique characteristic: **writes must be exceptionally robust (ACID)** but **reads need to be lightning fast** (dashboards, reports). CQRS completely separates these two flows:

```
WRITE SIDE (Command)                READ SIDE (Query)
────────────────────────            ──────────────────────────
POST /transfers            →        Materialized Views
POST /accounts             →        Elasticsearch Index
PUT /loans/repay           →        Redis Cache

↓ Event Published ↓                ↑ Subscribe & Update ↑
         └──────────────────────────┘
              (Event Bus / Kafka)
```

**Real-world Example:**
- **Write Side:** Processes transfers using PostgreSQL with full ACID compliance, guaranteeing money isn't lost.
- **Read Side:** Dashboards display transaction history from Elasticsearch — ultra-fast queries, full-text search, and multi-condition filtering.

---

## Pattern 3: Saga — Distributed Transactions Across Services

When a cross-bank transfer requires coordinating 3 services: **Account Service** (deduct money), **Payment Service** (send to clearing house), and **Notification Service** (send SMS), how do you ensure integrity?

### Choreography Saga (Event-Driven)

```
Account Service                Payment Service           Notification Service
      │                               │                          │
      │── TransferInitiated ──────────▶│                          │
      │                               │── PaymentSubmitted ──────▶│
      │                               │                          │── SMS Sent
      │◀── PaymentCompleted ──────────│                          │
      │                               │                          │
   (release hold)                                            (done)

If Payment fails:
      │◀── PaymentFailed ─────────────│
      │                               │
   (cancel hold, refund)
```

### Outbox Pattern — Guaranteeing Events are Never Lost

Problem: What if a service successfully commits to the database but fails to publish the event to Kafka?

Solution: **Write the event to the database within the same transaction, then have a separate worker read and publish it to Kafka.**

```sql
-- Outbox table: written in the same transaction as business data
CREATE TABLE outbox_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic       VARCHAR(100) NOT NULL,  -- 'account.transfer.completed'
    payload     JSONB        NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- Inside the same Database Transaction:
-- 1. Update account balance
-- 2. Write ledger entries  
-- 3. INSERT into outbox_events

-- Separate worker running periodically:
-- SELECT * FROM outbox_events WHERE status = 'PENDING'
-- → Publish to Kafka
-- → UPDATE status = 'PUBLISHED'
```

---

## API Design for Financial Transactions

### Design Principles

1. **Stateless APIs:** Every request must contain all necessary information.
2. **Mandatory Idempotency headers** for all state-changing APIs.
3. **Strict separation between Request (commands) and Status (polling).**

```
POST /v1/transfers                    → Initiate transfer command
  Header: Idempotency-Key: <uuid>
  Body: { from, to, amount, currency }
  Response: { transfer_id, status: "PROCESSING" }

GET  /v1/transfers/{transfer_id}      → Check result
  Response: { status: "COMPLETED" | "FAILED", ... }
```

Never design a transfer API as a **synchronous block** because processing through a central clearing network (like SWIFT) can take anywhere from seconds to minutes.

---

## Technical Stack Selection

| Layer | Popular Choices | Reason |
|---|---|---|
| **Service Framework** | Go (Kratos, Fiber), Java (Spring Boot) | High performance, type-safe |
| **Primary Database** | PostgreSQL | Strong ACID, flexible JSONB |
| **Cache** | Redis | Balances, sessions, rate limiting |
| **Event Bus** | Apache Kafka, Dapr PubSub | Durable, ordered, replayable |
| **Service Mesh** | Istio, Dapr | mTLS, circuit breaking |
| **Orchestration** | Kubernetes | Auto-scaling, self-healing |

> *Next, we will understand how Core Banking communicates with the outside world — the international standards that all financial systems must speak. Continue reading [Part 5 — International Integration Standards: ISO 8583 & ISO 20022](/series/core-banking-developer/part-5-iso-standards-integration/).*
