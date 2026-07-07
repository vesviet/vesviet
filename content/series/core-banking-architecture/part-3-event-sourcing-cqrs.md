---
title: "Event Sourcing & CQRS: Immutable Ledger for Microservices"
date: 2026-06-18T11:20:00+07:00
lastmod: 2026-07-03T15:41:55+07:00
draft: false
description: "Event Sourcing in Core Banking: PostgreSQL event store schema, CQRS balance <1ms vs O(N) SUM, Transactional Outbox with Debezium CDC — Monzo architecture."
weight: 3
series: ["core-banking-architecture"]
keywords: ["event sourcing saga pattern fintech", "transactional outbox pattern postgres", "CQRS balance calculation latency", "Monzo microservices architecture"]
author: "Tuan Anh"
schema: ["Article", "TechArticle", "FAQPage"]
cover:
  image: "/images/posts/banking-microservices-cover.png"
  alt: "Modern Core Banking Architecture series: Go, event sourcing, Saga pattern, and distributed ledger"
  relative: false
---

> **Series (Part 3 of 8):** This article builds upon the ACID transactions foundation from [Part 2](/series/core-banking-architecture/part-2-distributed-sql-acid-latency/). We will design a ledger using Event Sourcing — the exact solution that Monzo, Starling Bank, and many large neo-banks use to scale.

## What are Event Sourcing & CQRS in Fintech?

Fintech microservice systems utilize Event Sourcing and CQRS patterns to maintain distributed data consistency without distributed locks. To avoid dual-write failures, the Transactional Outbox pattern is applied in combination with CDC tools like Debezium. Pre-calculated CQRS balance lookups achieve **<1ms** latency, whereas on-the-fly `SUM()` aggregates degrade from **2ms to 200ms** at $O(N)$ with account history length.

---

## Why Was the Ledger Always Event Sourcing?

Double-entry bookkeeping — invented in the 15th century — is essentially Event Sourcing in its purest form:

- **Traditional approach**: Store **current state** (current balance) → history is lost
- **Event Sourcing**: Store an **immutable sequence of events** → current state is the result of a replay

```
Traditional:  accounts.balance = 500,000 VND   (no idea how it got there)

Event Sourcing:
  Event 1: AccountOpened        → balance = 0
  Event 2: MoneyDeposited(1M)   → balance = 1,000,000
  Event 3: MoneyWithdrawn(200K) → balance = 800,000
  Event 4: InterestAccrued(50K) → balance = 850,000
  Event 5: FeeCharged(350K)     → balance = 500,000
```

This is exactly how an accounting ledger works — every entry is an undeletable event. **Balance = replaying all events from the beginning** (or from the latest snapshot).

---

## Event Store Schema: PostgreSQL Production Design

### Core Event Store Table

```sql
-- Event Store: Central table storing all system events
CREATE TABLE event_store (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id       UUID NOT NULL,         -- Account/Entity ID (aggregate boundary)
    sequence_number BIGINT NOT NULL,       -- Monotonic counter PER stream
    event_type      VARCHAR(100) NOT NULL, -- 'MoneyDeposited', 'MoneyWithdrawn', etc.
    event_data      JSONB NOT NULL,        -- Event payload
    metadata        JSONB,                 -- correlation_id, causation_id, user_id, etc.
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Crucial: Prevent concurrent race conditions — each stream has its own sequence
    CONSTRAINT uq_stream_sequence UNIQUE (stream_id, sequence_number)
);

-- Index for event replay per account
CREATE INDEX idx_event_store_stream ON event_store (stream_id, sequence_number ASC);
-- Index for CDC/Outbox polling
CREATE INDEX idx_event_store_created ON event_store (created_at ASC);
```

**`sequence_number`** is the key to Optimistic Concurrency Control (OCC):

```go
// Append event with OCC — prevents concurrent writes to the same stream
func appendEvent(db *sql.DB, streamID uuid.UUID, expectedSeq int64, event Event) error {
    query := `
        INSERT INTO event_store (stream_id, sequence_number, event_type, event_data, metadata)
        VALUES ($1, $2, $3, $4, $5)
    `
    // sequence_number = expectedSeq + 1
    // If sequence already exists → UNIQUE constraint violation → conflict detected
    _, err := db.Exec(query,
        streamID,
        expectedSeq+1,
        event.Type,
        event.Data,
        event.Metadata,
    )
    if isUniqueViolation(err) {
        return ErrConcurrentModification // Retry or return conflict
    }
    return err
}
```

### Event Snapshots: Avoiding O(N) Replays

For accounts with a history of **millions of transactions**, replaying the entire event store becomes extremely slow. The solution: periodic snapshots.

```sql
-- Snapshot Table: Stores pre-computed state at a specific sequence point
CREATE TABLE event_snapshots (
    stream_id            UUID PRIMARY KEY,
    last_sequence_number BIGINT NOT NULL,
    state                JSONB NOT NULL,  -- Pre-computed balance at this point
    updated_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Pattern for reading balance with a snapshot:**

```go
// 1. Load the latest snapshot
snapshot, err := loadSnapshot(db, accountID)

// 2. Load ONLY events AFTER the snapshot
events, err := loadEventsAfter(db, accountID, snapshot.LastSequenceNumber)

// 3. Apply events to the snapshot state
balance := snapshot.State.Balance
for _, event := range events {
    balance = applyEvent(balance, event)
}

// Instead of replaying 5 million events → only replay N events since the snapshot
```

**Snapshot Rule**: Create a snapshot every 100-1000 events (depending on throughput). A background job can automatically generate snapshots for "hot accounts".

---

## Monzo's Event Sourcing Architecture

[Monzo Engineering](https://monzo.com/blog/2018/03/09/shipping-kafka-at-monzo/) published the details of their architecture:

- **Write Path**: Go microservices write ledger postings to PostgreSQL (the primary source of truth).
- **Distribution**: Kafka pub/sub distributes events to various read models.
- **Read Models**:
  - **Cassandra**: Primary read database, optimized for time-series lookups.
  - **Elasticsearch**: Full-text search, transaction search.
  - **BigQuery**: Analytics and reporting.
- **Consistency**: Offline reconciliation systems check data periodically.

**Monzo Transaction Flow (simplified):**

```
Mobile App Request
       │
       ▼
Account Service (Go)
       │
  ┌────┴─────────────────────────────┐
  │  PostgreSQL Transaction          │
  │  1. INSERT into event_store      │
  │  2. INSERT into outbox_events    │
  └────┬─────────────────────────────┘
       │ commit
       ▼
Debezium CDC Connector
       │ reads WAL
       ▼
Apache Kafka
       │
  ┌────┼─────────────────────────────┐
  │    │                             │
  ▼    ▼                             ▼
Cassandra  Elasticsearch          BigQuery
(balance)  (search)               (analytics)
```

---

## CQRS Latency: <1ms vs O(N) SUM()

**CQRS (Command Query Responsibility Segregation)** separates the write path (commands) from the read path (queries):

### On-the-fly Aggregation: An O(N) Disaster

```sql
-- BAD: Calculating balance using SUM() directly from the ledger
SELECT SUM(CASE WHEN direction = 'CREDIT' THEN amount ELSE -amount END) AS balance
FROM entries
WHERE account_id = 'acc-001';

-- Latency: 2ms for 1K entries → 50ms for 100K → 200ms for 1M entries
```

### CQRS Pre-computed Read Model: <1ms

```sql
-- GOOD: Reading pre-computed balance from a materialized view / Redis
SELECT balance, available_balance, last_updated_at
FROM account_balances  -- CQRS read model
WHERE account_id = 'acc-001';

-- Latency: <1ms (point lookup, indexed)
-- Redis: <0.5ms (in-memory)
```

**CQRS Write/Read Flow:**

```
WRITE SIDE (Command)                READ SIDE (Query)
────────────────────────            ──────────────────────────
POST /transfers            →        account_balances table
POST /accounts             →        Elasticsearch index
PUT /loans/repay           →        Redis balance cache

↓ Event Published ↓                ↑ Subscribe & Update ↑
         └──────────────────────────┘
               (Kafka event stream)
```

---

## Transactional Outbox Pattern: Solving Dual-Writes

### The Dual-Write Problem

```
❌ WRONG — Not atomic:
1. db.Update(account)     ← SUCCESS
2. kafka.Publish(event)   ← FAIL (network error)
→ Database is updated but downstream services never receive the event
→ Balances are incorrect, notifications not sent, read models are stale
```

### Outbox Pattern Solution

Write the event into the same database transaction as the business logic, and use a background worker to publish it to Kafka:

```sql
-- PostgreSQL Transactional Outbox Table
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(100) NOT NULL,  -- 'Account', 'Transfer', 'Loan'
    aggregate_id    VARCHAR(100) NOT NULL,  -- Entity ID
    event_type      VARCHAR(100) NOT NULL,  -- 'MoneyTransferred', 'AccountOpened'
    payload         JSONB NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, PUBLISHED
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at    TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_outbox_status_created ON outbox_events (status, created_at ASC);
```

**Application code — inside the same DB transaction:**

```go
func (s *AccountService) Transfer(ctx context.Context, req TransferRequest) error {
    return s.db.WithTransaction(ctx, func(tx *sql.Tx) error {
        // 1. Business logic: Write ledger entries
        if err := insertLedgerEntries(tx, req); err != nil {
            return err
        }

        // 2. SAME transaction: Write outbox event
        outboxPayload, _ := json.Marshal(map[string]interface{}{
            "from_account": req.FromAccount,
            "to_account":   req.ToAccount,
            "amount":       req.Amount,
            "currency":     req.Currency,
        })
        _, err := tx.Exec(`
            INSERT INTO outbox_events (aggregate_type, aggregate_id, event_type, payload)
            VALUES ($1, $2, $3, $4)
        `, "Account", req.FromAccount, "MoneyTransferred", outboxPayload)
        return err
        // If commit is successful: BOTH ledger AND outbox event are written
        // If rollback occurs: NEITHER is written → perfect atomicity
    })
}
```

**Debezium CDC Connector** reads the PostgreSQL WAL and forwards events to Kafka:

```json
// Debezium connector config (connector.json)
{
  "name": "outbox-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres.internal",
    "database.port": "5432",
    "database.user": "debezium",
    "database.dbname": "core_banking",
    "table.include.list": "public.outbox_events",
    "transforms": "outbox",
    "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
    "transforms.outbox.table.field.event.id": "id",
    "transforms.outbox.table.field.event.key": "aggregate_id",
    "transforms.outbox.table.field.event.payload": "payload",
    "transforms.outbox.table.field.event.type": "event_type"
  }
}
```

---

## Event Versioning: Handling Schema Evolution

An Event Store is immutable — you cannot modify the schema of old events. The solution is versioning:

```go
// Upcaster: Convert event v1 → v2 when reading
type MoneyDepositedV1 struct {
    AccountID string  `json:"account_id"`
    Amount    float64 `json:"amount"`  // v1 uses float (WRONG)
}

type MoneyDepositedV2 struct {
    AccountID string `json:"account_id"`
    AmountCents int64  `json:"amount_cents"` // v2 uses integer (CORRECT)
    Currency    string `json:"currency"`
}

func upcaster(eventType string, version int, data json.RawMessage) (interface{}, error) {
    switch {
    case eventType == "MoneyDeposited" && version == 1:
        var v1 MoneyDepositedV1
        json.Unmarshal(data, &v1)
        return MoneyDepositedV2{
            AccountID:   v1.AccountID,
            AmountCents: int64(v1.Amount * 100), // Convert
            Currency:    "VND",                   // Default
        }, nil
    // ...
    }
}
```

---

## QA & SDET Testing Strategy

### Test 1: Event Replay Consistency

```go
// Scenario: Drop read model → replay from event store → verify balance match
func TestEventReplayConsistency(t *testing.T) {
    ctx := context.Background()
    
    // 1. Get "live" balance from read model BEFORE
    liveBalance := getReadModelBalance(ctx, "account-001")
    
    // 2. Drop and rebuild read model from event store
    dropAccountBalancesTable(ctx)
    replayAllEventsFromEventStore(ctx)
    
    // 3. Get balance after replay
    replayedBalance := getReadModelBalance(ctx, "account-001")
    
    // 4. Must match exactly
    assert.Equal(t, liveBalance, replayedBalance,
        "Replayed balance must match live balance exactly")
}
```

### Test 2: Outbox Atomicity Under Failure

```go
// Inject failure BETWEEN database commit and Kafka publish
func TestOutboxAtomicityUnderFailure(t *testing.T) {
    // Mock Kafka publisher to fail
    mockKafka := &FailingKafkaPublisher{}
    
    // Execute transfer
    err := transferService.Transfer(ctx, TransferRequest{
        From: "acc-A", To: "acc-B", Amount: 1000000,
    })
    
    // Transfer still succeeds (DB is committed)
    assert.NoError(t, err)
    
    // Outbox event is still in PENDING state (Kafka failed)
    pendingEvents := countOutboxPending()
    assert.Greater(t, pendingEvents, 0)
    
    // After Kafka recovers, the outbox worker retries and publishes successfully
    fixKafka()
    waitForOutboxProcessing()
    
    // Balance of both accounts must be accurate
    assert.Equal(t, expectedBalanceA, getBalance("acc-A"))
    assert.Equal(t, expectedBalanceB, getBalance("acc-B"))
}
```

---

> 💡 **Read more:** [Saga Pattern](/series/core-banking-architecture/part-4-saga-pattern/) — Saga Pattern to handle distributed failures.

## FAQ


{{< faq q="Does Event Sourcing make queries more complex?" >}}
Yes — Event Sourcing optimizes for writes and auditing, but complicates reads. This is exactly why CQRS exists. The write side stores events; the read side builds materialized views optimized for queries. You should not use pure Event Sourcing without CQRS read models.
{{< /faq >}}

{{< faq q="Can Debezium handle large PostgreSQL WAL volumes?" >}}
Yes, but you need to monitor LAG (Debezium lag behind the WAL position). For volumes >10,000 TPS, it's recommended to dedicate a PostgreSQL replica purely for Debezium to avoid impacting the primary.
{{< /faq >}}

{{< faq q="How often should a snapshot be taken?" >}}
It depends on average event size and acceptable replay time. Rule of thumb: snapshot every **500 events**. With an average event size of 1KB → snapshot file ~500KB. Replaying from a snapshot (0 events) up to the max (500 events) will never exceed a few dozen milliseconds.

---

*Up Next: [Part 4 — Saga Pattern](/series/core-banking-architecture/part-4-saga-pattern/) — Choreography vs Orchestration Saga, failure transition matrices, and implementation with Temporal workflow engine.*
{{< /faq >}}
