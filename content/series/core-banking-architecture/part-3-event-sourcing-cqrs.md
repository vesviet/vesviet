---
title: "Event Sourcing & CQRS: Immutable Ledger for Microservices"
slug: "part-3-event-sourcing-cqrs"
date: "2026-06-18T11:20:00+07:00"
lastmod: "2026-09-09T21:25:00+07:00"
draft: false
description: "Event Sourcing and CQRS architecture in core banking: append-only event store schemas, transactional outbox with Debezium CDC, Protobuf schema evolution, and sub-10ms projection hydration."
weight: 3
series: ["core-banking-architecture"]
categories: ["FinTech", "Event-Driven", "Architecture"]
tags: ["Event Sourcing", "CQRS", "Kafka", "PostgreSQL", "Golang", "Microservices"]
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/banking-microservices-cover.jpg"
  alt: "Modern Core Banking Architecture: Event Sourcing and CQRS for Distributed Financial Microservices"
  relative: false
canonicalURL: "https://tanhdev.com/series/core-banking-architecture/part-3-event-sourcing-cqrs/"
ShowToc: true
TocOpen: true
mermaid: true
---

[📖 Bản tiếng Việt (Vietnamese Edition)](https://learn.tanhdev.com/series/core-banking-architecture/part-3-event-sourcing-cqrs/)

---

> **Series Navigation:** This is Part 3 of the **Core Banking Systems Architecture Masterclass**. For the complete architectural curriculum, start at the [Master Overview Guide](/series/core-banking-architecture/).

# Event Sourcing & CQRS: Immutable Ledger for Microservices

**Answer-first:** Event Sourcing and CQRS (Command Query Responsibility Segregation) solve the fundamental tension in core banking between write-side audit immutability and read-side low-latency queries. By treating an append-only event log as the authoritative System of Record (SoR) and deriving balance read models asynchronously via transactional outbox Change Data Capture (CDC), financial platforms eliminate dual-write hazards, maintain mathematical auditability, and deliver sub-millisecond account balance lookups under massive concurrent workloads.

---

## 1. Why Banking Ledgers Are Naturally Event-Sourced

In standard enterprise applications, databases store current state, discarding the intermediate transitions that led to that state. In financial accounting, however, current state has zero legal authority without the complete chronological chain of mutations that generated it. 

Double-entry bookkeeping is the historical progenitor of Event Sourcing:

$$\text{Current Account Balance}(t) = \text{Initial Balance} + \sum_{i=1}^{n} \text{JournalEvent}_i$$

```mermaid
flowchart TD
    subgraph Command_Side ["Write Side (Command Path - Invariant Enforcement)"]
        Cmd["Transfer Command<br/>(Debit Alice, Credit Bob)"]
        Agg["Account Aggregate Root"]
        Validation{"Assert Invariants:<br/>Balance >= Amount & Active"}
        EventStore["PostgreSQL 17 Event Store<br/>(Append-Only Events Table)"]
        OutboxTable["Transactional Outbox Table<br/>(Atomic ACID Commit)"]

        Cmd --> Agg
        Agg --> Validation
        Validation -->|Approved| EventStore & OutboxTable
        Validation -->|Rejected| Err["Reject Command (EX02)"]
    end

    subgraph CDC_Streaming ["Debezium CDC & Message Backbone"]
        Debezium["Debezium WAL Streamer"]
        KafkaTopic(("Kafka Topic: banking.account.events<br/>(Partition Key: AccountID)"))
        OutboxTable -.->|pgoutput Logical Decoding| Debezium
        Debezium --> KafkaTopic
    end

    subgraph Query_Side ["Read Side (Query Path - Sub-1ms Projections)"]
        Consumer["Go Projection Consumer<br/>(Idempotent Dedup)"]
        RedisCache["Redis 7 In-Memory Cache<br/>(Real-Time Available Balance)"]
        ElasticStore["Elasticsearch 8<br/>(Customer Transaction History UI)"]

        KafkaTopic --> Consumer
        Consumer --> RedisCache & ElasticStore
    end
```

---

## 2. Eliminating Dual-Write Hazards: The Transactional Outbox Pattern

A common anti-pattern in distributed fintech microservices is attempting to write to the primary database and publish to Apache Kafka within the same application handler:

```go
// FATAL ANTI-PATTERN: Dual-Write Risk
func (s *PaymentService) HandleDeposit(ctx context.Context, cmd DepositCommand) error {
    // 1. Commit to PostgreSQL
    if err := s.repo.SaveEvent(ctx, event); err != nil {
        return err
    }
    // 2. Publish to Kafka -> If app crashes here, Kafka NEVER receives the event!
    return s.kafkaProducer.Send("account-events", event)
}
```

If the application container terminates or suffers a network timeout after writing to PostgreSQL but before publishing to Kafka, downstream read models (and fraud detection engines) drift out of sync forever.

The **Transactional Outbox Pattern** solves this by inserting the event into an `outbox` table within the same local database transaction. An independent log reader (Debezium via PostgreSQL `pgoutput` plugin) tails the Write-Ahead Log (WAL), guaranteeing at-least-once delivery to Kafka with zero dual-write vulnerabilities.

```mermaid
sequenceDiagram
    autonumber
    participant App as "Core Banking Command Handler"
    participant DB as "PostgreSQL 17 (Event Store + Outbox)"
    participant CDC as "Debezium CDC Engine"
    participant Kafka as "Apache Kafka Cluster"
    participant Projector as "Read Projection Service"

    App->>DB: BEGIN TRANSACTION
    App->>DB: INSERT INTO domain_events (event_id, aggregate_id, payload, version)
    App->>DB: INSERT INTO outbox_messages (id, topic, payload, created_at)
    App->>DB: COMMIT TRANSACTION (WAL Flushed Atomically)
    DB-->>App: Command Acknowledged (Latency < 2.5ms)

    Note over DB,CDC: Zero Dual-Write Latency Overhead
    CDC->>DB: Read WAL Changes via pgoutput Plugin
    CDC->>Kafka: Produce Event to Partition (Key = AggregateID)
    Kafka-->>CDC: Partition Offset Committed

    Kafka->>Projector: Consume Event Batch
    Projector->>Projector: Idempotent Dedup Check (event_id)
    Projector->>Projector: Update Read Cache & Projections
```

---

## 3. Snapshotting & High-Performance Event Replay

When reconstructing an account aggregate with 500,000 historical transactions, replaying every historical event from inception creates unacceptable latency:
- $O(N)$ event replay over 500,000 events: **~1,200ms** (unacceptable for an online payment API).
- Replay with **EOD Snapshotting** (snapshot every 1,000 events or daily at midnight): **< 1.8ms**.

```sql
-- Production DDL for Snapshot Store
CREATE TABLE account_snapshots (
    account_id UUID NOT NULL,
    version BIGINT NOT NULL,
    balance BIGINT NOT NULL, -- Minor units (e.g. cents)
    reserved_holds BIGINT NOT NULL,
    status VARCHAR(16) NOT NULL,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (account_id, version)
);

-- Query to rehydrate aggregate: Fetch latest snapshot + subsequent events only
SELECT * FROM account_snapshots 
WHERE account_id = 'c4b8b4b2-2975-4c07-9b2f-7c152a5c5a01' 
ORDER BY version DESC LIMIT 1;

-- Then replay delta events:
SELECT * FROM domain_events 
WHERE aggregate_id = 'c4b8b4b2-2975-4c07-9b2f-7c152a5c5a01' 
  AND version > 45000 
ORDER BY version ASC;
```

---

## 4. Optimistic Concurrency Control (OCC) in Event Stores

To protect against race-condition double-spending in event stores, event streams enforce strict monotonic versioning:

```sql
-- Appending event with Optimistic Concurrency Control
INSERT INTO domain_events (aggregate_id, event_type, payload, version)
VALUES ('c4b8b4b2-2975-4c07-9b2f-7c152a5c5a01', 'MoneyDebited', '{"amount": 50000}', 45001);
-- If another transaction committed version 45001 first, PostgreSQL throws:
-- ERROR: duplicate key value violates unique constraint "domain_events_agg_ver_idx"
```
When this unique violation occurs, the command handler simply reloads the latest snapshot, re-verifies business invariants against the updated balance, and retries the command.

---

## Frequently Asked Questions (FAQ)

{{< faq q="How does Event Sourcing ensure compliance with banking audit regulations?" >}}
Event Sourcing stores every financial mutation as an immutable, permanent domain event with strict metadata (originator timestamp, operator identity, IP, and reason code). Because events are never overwritten or deleted, regulatory examiners can reconstruct the complete mathematical state of any customer account down to the exact millisecond, satisfying Basel III, PCI-DSS, and central bank forensic standards.
{{< /faq >}}

{{< faq q="How do downstream consumers handle eventual consistency projection lag in banking apps?" >}}
While the write-side event store is immediately consistent, read-side projections in Redis or Elasticsearch update asynchronously with a typical lag of 10ms to 40ms. Banking mobile applications mitigate this by applying optimistic UI updates (displaying the predicted balance immediately) or utilizing read-your-own-writes session tokens: the API gateway returns the committed event version, and query endpoints read from the primary database or block until the projection catches up.
{{< /faq >}}

{{< faq q="How are breaking changes in financial event schemas handled over a 10-year period?" >}}
Financial events must remain readable for decades. Banks manage event schema evolution by using Protobuf or Apache Avro paired with a Confluent Schema Registry that enforces backward and forward compatibility rules (e.g., fields can never be deleted or renamed, and new fields must have default values). For legacy events with fundamentally obsolete schemas, event upcasters intercept events during deserialization in memory, translating older payloads into current domain models on the fly without mutating on-disk event records.
{{< /faq >}}
