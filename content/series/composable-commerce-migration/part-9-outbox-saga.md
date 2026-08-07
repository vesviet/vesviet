---
title: "Transactional Outbox & Saga Pattern for E-commerce"
description: "In-depth technical guide implementing PostgreSQL outbox patterns, choreography Sagas, idempotency keys, and circuit breakers in Go Checkout."
date: "2026-06-03T10:00:00+07:00"
lastmod: "2026-07-03T15:41:55+07:00"
draft: false
weight: 10
slug: "part-9-outbox-saga"
ShowToc: true
TocOpen: true
categories: ["Software Engineering", "Backend", "Distributed Systems"]
tags: ["Saga Pattern", "Outbox Pattern", "Transactional Outbox", "Dapr", "Event-Driven", "Golang", "Idempotency", "Circuit Breaker"]
series: ["Composable Commerce Migration"]
series_order: 9
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/ecommerce-composable-cover.jpg"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-9-outbox-saga/"
mermaid: true
---

> **Prerequisite:** Familiarity with the concepts introduced in [Part 8 — Phase3 Full Cutover](/series/composable-commerce-migration/part-8-phase3-full-cutover/). Review it first if the terminology in this part is unfamiliar.

> **Answer-first:** Distributed transaction consistency is achieved using a choreography-based saga paired with a PostgreSQL transactional outbox. Business mutations write to the outbox atomically. Background workers publish events to Dapr PubSub every 500ms, while idempotent consumer handlers process compensation events on failure.

When a customer places an order on the Composable Commerce Platform, seven events need to happen in sequence across four independent services: Order created → Payment authorized → Stock reserved → Fulfillment triggered → Notification sent → Loyalty points awarded → Shipping label generated. Any of these can fail. The network can fail. The database can fail. A third-party payment gateway can time out.

Without a reliability mechanism, a 2% failure rate on any step means 2% of all orders are stuck in an inconsistent state, requiring manual intervention.

## 1. Why Choreography, Not Orchestration?

**Answer-first:** Choreography Saga decoupling allows microservices to react to domain events independently without creating single-point-of-failure orchestrators.

In distributed microservice architectures, developers must evaluate two primary saga execution styles depending on workflow complexity, operational overhead, and coupling tolerances.

The following architectural structural diagrams contrast the central command flow of an Orchestrated Saga against the event-driven reaction model of a Choreographed Saga:

**Orchestration**: A central "Order Saga Orchestrator" service sends commands to each service in sequence and handles failures:
```
Orchestrator → "Reserve stock" → Warehouse Service
Orchestrator ← "Stock reserved" ← Warehouse Service
Orchestrator → "Capture payment" → Payment Service
...
```

**Choreography**: Services emit domain events and other services react:
```
Order Service emits: "order.created"
  → Warehouse Service subscribes → reserves stock → emits "warehouse.stock.reserved"
  → Payment Service subscribes → captures payment → emits "payment.captured"
  → Fulfillment Service subscribes → creates fulfillment → emits "fulfillment.created"
```

The platform mandates **choreography** for core checkout and fulfillment flows for three key reasons:
1. **No Single Point of Failure (SPOF)**: Eliminates a central coordinator bottleneck or stateful orchestrator service that could block all system checkouts if disrupted.
2. **Strict Microservice Decoupling**: Services remain completely autonomous — Order Service has zero compile-time or runtime knowledge of Payment Service or Warehouse Service existence.
3. **Independent Failure Handling**: Each microservice maintains complete authority over its own retry policies, backoff limits, and localized error recovery strategies.

**2026 Architectural Evaluation**: While dedicated workflow engines like **Temporal.io** or Go Watermill orchestrators excel at long-running, multi-day B2B procurement sagas with complex branch conditional logic, choreography combined with distributed tracing remains the gold standard for ultra-low latency B2C e-commerce checkout pipelines under 500ms.

The primary trade-off in choreography is visualization complexity: event chains are harder to trace than a single orchestrator log. This is mitigated by OpenTelemetry W3C trace context propagation — every event carries a unified `correlation_id` header linking the entire distributed saga span tree.

## 2. The Order Saga Flow

The order saga flow coordinates Checkout, Inventory, Payment, and Shipping services via asynchronous event publication and compensation events.

The sequence flow diagram below outlines the exact event publication sequence and asynchronous service interactions executed during a successful order placement workflow:

```
Customer places order
        │
        ▼
┌─────────────────┐
│  Checkout Svc   │  Validates cart, calculates final price
│                 │  Calls Order Service via gRPC
└────────┬────────┘
         │ gRPC: CreateOrder
         ▼
┌─────────────────┐
│   Order Svc     │  Creates order with status: PENDING
│                 │  Inserts outbox event: "orders.order.created"
└────────┬────────┘
         │ Dapr Pub/Sub (async)
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────┐                ┌─────────────────┐
│  Warehouse Svc  │                │   Payment Svc   │
│ Reserve stock   │                │ Capture payment │
│ Emits:          │                │ Emits:          │
│ "stock.reserved"│                │ "payment.       │
└────────┬────────┘                │  captured"      │
         │                         └────────┬────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        │ Both events received by Order Service
                        ▼
               ┌─────────────────┐
               │   Order Svc     │  Status → CONFIRMED
               │                 │  Emits: "order.confirmed"
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  Fulfillment    │  Creates picking task
               │  Svc            │  Emits: "fulfillment.created"
               └────────┬────────┘
                        │
                        ├── Notification Svc → sends order confirmation email
                        └── Loyalty Svc → awards points
```

When Checkout Service receives the user checkout submission, it validates the cart and issues a synchronous gRPC call (`CreateOrder`) to Order Service. Order Service writes the initial order record with status `PENDING` and inserts an `orders.order.created` event into its PostgreSQL transactional outbox. 

The background OutboxProcessor picks up the pending event and relays it to Dapr PubSub. Both Warehouse Service and Payment Service subscribe asynchronously to `orders.order.created`. Warehouse Service places a 15-minute stock hold and emits `warehouse.stock.reserved`, while Payment Service authorizes the customer's credit card and emits `payment.captured`. 

Order Service consumes both events. Upon receiving both confirmations, Order Service updates the order status from `PENDING` to `CONFIRMED` in a database transaction and emits `orders.order.confirmed`. Downstream services (Fulfillment, Notification, Loyalty) consume the confirmation event to generate warehouse picking tickets, send customer emails, and calculate reward points.

## 3. The Custom PostgreSQL Outbox

Transactional outbox tables write event payloads in the same database transaction as business state changes, guaranteeing event delivery.

The platform deliberately avoids Dapr's native outbox component (`dapr-outbox`). Dapr's native outbox ties event state directly to Dapr actor state stores, adding operational complexity and restricting direct SQL query visibility into outbox queues. Instead, the platform standardizes on an explicit PostgreSQL relational outbox table.

The DDL snippet below defines the production schema for the `outbox_events` table used across all Go microservices:

```sql
-- migrations/00005_create_outbox_events.sql
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic           VARCHAR(256) NOT NULL,     -- e.g., "orders.order.created"
    payload         JSONB NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    retry_count     INT NOT NULL DEFAULT 0,
    last_error      TEXT,
    correlation_id  UUID,                       -- Links saga events for tracing

    -- Index for outbox processor polling
    CONSTRAINT outbox_status_check CHECK (status IN ('PENDING', 'DELIVERED', 'FAILED'))
);

CREATE INDEX idx_outbox_pending ON outbox_events (status, created_at)
WHERE status = 'PENDING';
```

The fundamental reliability invariant: **the outbox event insert executes within the exact same database transaction (`sql.Tx`) as the primary business entity mutation**:

The Go implementation code below demonstrates wrapping the order insert and outbox event creation inside a single atomic database transaction:

```go
// order-service/internal/biz/order_usecase.go

func (uc *OrderUseCase) CreateOrder(ctx context.Context, order *Order) (*Order, error) {
    var created *Order

    err := uc.db.WithTx(ctx, func(tx *sql.Tx) error {
        var err error

        // 1. Write order to orders table
        created, err = uc.repo.CreateWithTx(ctx, tx, order)
        if err != nil {
            return fmt.Errorf("creating order: %w", err)
        }

        // 2. Insert outbox event in SAME transaction
        //    If this transaction rolls back, the event is also rolled back — atomically
        return uc.outbox.InsertWithTx(ctx, tx, outbox.Event{
            Topic:         "orders.order.created",
            CorrelationID: order.RequestID,  // Idempotency + tracing
            Payload: map[string]interface{}{
                "order_id":    created.ID,
                "customer_id": created.CustomerID,
                "items":       created.Items,
                "total":       created.Total,
                "created_at":  created.CreatedAt,
            },
        })
    })
    if err != nil {
        return nil, err
    }

    return created, nil
}
```

If the `CreateOrder` database write fails (e.g., foreign key violation, disk full, or connection drop), the entire transaction rolls back — eliminating phantom event publication for non-existent orders. Conversely, if the network drops immediately after the database commit, the outbox record remains safely stored in PostgreSQL ready for background publication.

## 4. The OutboxProcessor: Publishing with Guarantees

The OutboxProcessor worker polls outbox database records using row locks with `SKIP LOCKED`, publishing domain events to Dapr messaging channels to guarantee at-least-once event delivery.

The `common/worker` library package provides a standardized OutboxProcessor goroutine instantiated during microservice bootstrap.

The code block below highlights the initial worker configuration established in the main entrypoint of each microservice:

```go
// order-service/cmd/order-service/main.go

processor := worker.NewOutboxProcessor(db, daprClient, worker.OutboxConfig{
    PollInterval: 500 * time.Millisecond,   // Check for new events every 500ms
    BatchSize:    100,                       // Process up to 100 events per cycle
    MaxRetries:   5,                         // After 5 failures, mark as FAILED
    RetryBackoff: worker.ExponentialBackoff(1*time.Second, 16*time.Second),
})
processor.Start(ctx)
```

The core polling loop executes concurrent-safe event retrieval and publishing using PostgreSQL row-level locks:

The Go code below details the worker loop implementation utilizing `FOR UPDATE SKIP LOCKED` for lock contention avoidance:

```go
// common/worker/outbox_processor.go

func (p *OutboxProcessor) processOnce(ctx context.Context) {
    // Fetch pending events (locked for this processor instance)
    events, err := p.db.QueryWithLock(ctx, `
        SELECT id, topic, payload, correlation_id, retry_count
        FROM outbox_events
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED  -- Allows multiple processor instances without conflicts
    `, p.config.BatchSize)
    if err != nil { return }

    for _, event := range events {
        // Publish to Dapr PubSub (Redis Streams)
        err := p.daprClient.PublishEvent(ctx, "pubsub", event.Topic, event.Payload,
            dapr.PublishEventWithMetadata(map[string]string{
                "correlationId": event.CorrelationID.String(),
            }),
        )

        if err != nil {
            p.db.Exec(ctx, `
                UPDATE outbox_events
                SET retry_count = retry_count + 1,
                    last_error = $2,
                    status = CASE WHEN retry_count + 1 >= $3 THEN 'FAILED' ELSE status END
                WHERE id = $1
            `, event.ID, err.Error(), p.config.MaxRetries)
            continue
        }

        // Mark as delivered
        p.db.Exec(ctx, `
            UPDATE outbox_events
            SET status = 'DELIVERED', processed_at = NOW()
            WHERE id = $1
        `, event.ID)
    }
}
```

The inclusion of `FOR UPDATE SKIP LOCKED` is critical for horizontal scaling. When multiple Kubernetes pods run the Order Service concurrently, each pod locks and processes a distinct batch of pending outbox rows without blocking other worker pods or incurring database deadlocks. Batch size tuning (100 items per 500ms cycle) allows a single service replica to handle up to 200 events/second with negligible CPU overhead.

## 5. Idempotency: Handling Duplicate Delivery

Idempotency keys stored in Redis or PostgreSQL prevent duplicate event execution on consumer microservices during network retries.

Messaging infrastructures (Redis Streams, NATS, Kafka) operating under distributed network conditions guarantee **at-least-once delivery**. In rare cases (e.g., ACK packet lost during network hiccup), the message broker re-delivers an event. Consequently, all consumer event handlers must be strictly idempotent.

The Go implementation code below demonstrates a dual-layer idempotency guard implemented inside the Warehouse Service stock reservation handler:

```go
// warehouse-service/internal/biz/stock_usecase.go

func (uc *StockUseCase) HandleOrderCreated(ctx context.Context, event *events.OrderCreated) error {
    // Check if we've already processed this event
    if processed, _ := uc.dedup.Has(ctx, event.OrderID + ":stock-reserve"); processed {
        log.Debugf("Duplicate event for order %s, skipping", event.OrderID)
        return nil
    }

    // Process: reserve stock for each order item
    for _, item := range event.Items {
        if err := uc.ReserveStock(ctx, item.ProductID, item.Quantity); err != nil {
            // Stock insufficient → publish compensation event
            return uc.events.Publish(ctx, "warehouse.stock.insufficient", &events.StockInsufficient{
                OrderID:   event.OrderID,
                ProductID: item.ProductID,
                Requested: item.Quantity,
            })
        }
    }

    // Mark as processed (TTL: 7 days — covers any retry window)
    uc.dedup.Set(ctx, event.OrderID + ":stock-reserve", 7*24*time.Hour)

    // Publish success event
    return uc.events.Publish(ctx, "warehouse.stock.reserved", &events.StockReserved{
        OrderID: event.OrderID,
        Items:   event.Items,
    })
}
```

The platform standardizes on a structured deduplication key pattern: `{entity_id}:{handler_name}` (e.g. `order-9821:stock-reserve`). 

**2026 Dual-Layer Deduplication Standard**:
1. **Fast-Path Cache Layer**: Distributed Redis key with a 7-day TTL checks incoming event keys in sub-millisecond time.
2. **Durable Database Layer**: A `processed_events` table with a composite primary key `(event_id, handler_name)` executed inside the consumer's SQL transaction ensures absolute consistency even if Redis fails or evicted memory under pressure.

Out-of-order delivery protection is also enforced by comparing incoming event timestamps against existing aggregate modification dates (`event.timestamp >= entity.updated_at`), ignoring stale out-of-order events.

## 6. Compensation: When the Saga Fails

Compensation transactions automatically reverse partial saga state changes (e.g. releasing inventory holds) if payment processing fails.

When a downstream step in a saga encounters an unrecoverable business failure (e.g. credit card declined, stock exhausted during parallel checkout), the system must execute compensating transactions to roll back previously completed steps in reverse order.

The diagram below illustrates the compensation flow triggered when Warehouse Service detects insufficient inventory:

```
warehouse.stock.insufficient (published by Warehouse Svc)
        │
        ├──► Order Svc: set status → CANCELLED, emit "order.cancelled"
        │
        └──► Payment Svc: subscribes to "order.cancelled" → issue refund
                          → emit "payment.refunded"
```

To maintain fault tolerance, compensating events are published using the exact same transactional outbox pattern as forward events:

The Go code below shows Order Service processing an inventory failure by cancelling the order and committing a compensating outbox event in one transaction:

```go
// order-service/internal/biz/order_usecase.go

func (uc *OrderUseCase) HandleStockInsufficient(ctx context.Context, event *events.StockInsufficient) error {
    return uc.db.WithTx(ctx, func(tx *sql.Tx) error {
        // Cancel the order
        if err := uc.repo.UpdateStatusWithTx(ctx, tx, event.OrderID, OrderStatusCancelled); err != nil {
            return err
        }

        // Insert compensation event in same transaction
        return uc.outbox.InsertWithTx(ctx, tx, outbox.Event{
            Topic: "orders.order.cancelled",
            Payload: map[string]interface{}{
                "order_id": event.OrderID,
                "reason":   "INSUFFICIENT_STOCK",
                "product_id": event.ProductID,
            },
        })
    })
}
```

Compensating transactions must obey three mandatory invariants:
1. **Idempotent Execution**: Running a refund or stock-release compensation multiple times produces identical state as running it once.
2. **Unconditional Success**: Compensating handlers must accept all valid compensation requests without raising secondary business validation rejections.
3. **Dead-Letter Queue (DLQ) Governance**: If a compensation handler fails due to persistent technical outages (e.g. payment gateway API offline for hours), the event routes to a Dead-Letter Queue (`dlq.orders.compensation`) for manual administrative intervention via the platform operations dashboard.

## 7. Resilience: Circuit Breaker + Retry

Combining circuit breakers with exponential backoff retries prevents transient microservice RPC failures from breaking active Sagas.

External integration points (payment gateways, shipping API providers, tax calculation endpoints) are inherently prone to transient latency spikes and third-party outages. The `common/errors` library wraps inter-service client connections with resilience policies.

The Go code block below demonstrates configuring a production circuit breaker and exponential backoff retry policy using `gobreaker` and `retry`:

```go
// common/client/resilience.go — applied to all service-to-service calls

// Circuit breaker configuration (ADR-020)
cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    Name:        "payment-gateway",
    MaxRequests: 5,                           // Allow 5 requests in half-open state
    Interval:    60 * time.Second,            // Reset failure count every 60 seconds
    Timeout:     30 * time.Second,            // Wait 30s before trying again after open
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures >= 5 // Open after 5 consecutive failures
    },
})

// Retry with exponential backoff (ADR-020)
retrier := retry.New(
    retry.WithMaxRetries(3),
    retry.WithBackoff(retry.ExponentialBackoff(1*time.Second, 16*time.Second)),
    retry.WithJitter(0.2),  // ±20% jitter to prevent thundering herd
)
```

The circuit breaker operates across three standardized state transitions:
- **Closed** (Normal Operation): Requests execute normally. Failure counters are evaluated against thresholds.
- **Open** (Tripped): When consecutive failures hit the threshold (5 failures), the breaker trips. All subsequent calls fail fast immediately (0ms delay) without burning network sockets, triggering immediate saga compensation.
- **Half-Open** (Recovery Validation): After the 30-second timeout expires, 5 probe requests are permitted through. If all 5 succeed, the breaker resets to **Closed**; if any fail, it reverts to **Open**.

Adding exponential backoff with random jitter (±20%) ensures that when thousands of concurrent checkout requests experience a momentary downstream glitch, retries are distributed smoothly across time rather than flooding downstream services in a thundering herd.

## 8. Distributed Tracing: Following a Saga

Distributed tracing propagates OpenTelemetry trace context headers across Saga events, rendering full end-to-end execution spans in Tempo.

Because choreographed sagas execute asynchronously across detached microservices and event brokers, maintaining visibility requires end-to-end distributed tracing header propagation.

The Go struct snippet below shows standardizing the `correlation_id` property across all domain event contracts:

```go
// All events include correlation_id for tracing
type OrderCreated struct {
    OrderID       string    `json:"order_id"`
    CustomerID    string    `json:"customer_id"`
    CorrelationID string    `json:"correlation_id"`  // Same across entire saga chain
    // ...
}
```

The text diagram below depicts a complete OpenTelemetry end-to-end trace span tree captured in Grafana Tempo for an order saga execution:

```
Trace: order-saga-correlation-id-xyz
├── [0ms]    Checkout Service: CreateOrder gRPC call
├── [12ms]   Order Service: CreateOrder (PostgreSQL write + outbox insert)
├── [14ms]   OutboxProcessor: Publish orders.order.created
├── [20ms]   Warehouse Service: HandleOrderCreated (stock reservation)
├── [25ms]   Payment Service: HandleOrderCreated (payment capture)
├── [180ms]  Payment Service: ProcessPayment (external gateway call)
├── [200ms]  Payment Service: Publish payment.captured
├── [22ms]   Warehouse Service: Publish warehouse.stock.reserved
├── [210ms]  Order Service: HandlePaymentCaptured + HandleStockReserved
├── [215ms]  Order Service: Status → CONFIRMED, Publish order.confirmed
└── [230ms]  Fulfillment Service: HandleOrderConfirmed (picking task created)
```

Total saga completion time averages ~230ms for happy-path orders. In cases involving third-party payment gateway latency, total duration scales to 2–5 seconds while remaining completely non-blocking to the HTTP client thread. If a circuit breaker trips, execution terminates within ~50ms and initiates automated compensation.

## Why Not Dapr's Native Outbox?

A custom PostgreSQL outbox provides fine-grained control over polling intervals, table indexes, and manual DLQ re-queueing.

Dapr v1.11 introduced a built-in outbox pattern feature. However, the platform engineering team chose a custom PostgreSQL relational outbox implementation based on three production architectural trade-offs:

1. **Direct Operational Visibility**: A simple SQL query (`SELECT * FROM outbox_events WHERE status = 'FAILED'`) provides instant operational insight into stuck events. Dapr's native outbox stores outbox states inside state store key-value abstractions, making manual inspection and ad-hoc SQL updates significantly harder.
2. **Granular Execution Control**: Custom outbox code allows fine-tuned polling intervals (500ms), tailored batch sizes (100 records), and selective per-event retry rules without requiring Dapr sidecar configuration deployments.
3. **Database Native Lock Mechanics**: Utilizing PostgreSQL `FOR UPDATE SKIP LOCKED` guarantees clean, multi-pod worker concurrency directly inside the relational engine without adding external distributed lock infrastructure.

**CDC Alternative (Debezium / PostgreSQL WAL)**: For ultra-high throughput environments (>5,000 events/sec), polling outbox tables incurs non-trivial database read/write IOPS. The platform architecture is structured so that the `outbox_events` table can directly transition from polling workers to Change Data Capture (CDC) via Debezium reading PostgreSQL Write-Ahead Logs (WAL via `pgoutput`) with zero changes to application transaction code.

The trade-off: custom outbox code requires maintaining ~150 lines of worker code (`common/worker/outbox_processor.go`). Encapsulating this inside `common/worker` makes it a reusable zero-cost abstraction across all 21 microservices.

## What's Next

Review Part 10 for complete architecture decision records (ADRs) explaining tech stack choices and migration patterns.

In the final installment of this series, [Part 10: ADR Walkthrough](/series/composable-commerce-migration/part-10-adr-walkthrough/), we examine all 24 Architecture Decision Records that govern the Composable Commerce Platform. Part 10 details the exact decision drivers, evaluated alternatives, and accepted trade-offs for critical architecture choices — including why Dapr was selected over raw Kafka, why Kustomize replaced Helm, and why go-kratos was chosen as the microservice framework.

## FAQ

The transactional outbox pattern guarantees atomic event publishing in Go microservices, eliminating lost events during network partitions.

{{< faq q="Saga pattern vs two-phase commit — when do you use each?" >}}
**Two-phase commit (2PC)** provides ACID guarantees across distributed resources using a coordinator and participants — but it blocks all participants until the coordinator resolves, making it slow and sensitive to coordinator failure. **Saga** provides eventual consistency through compensating transactions, without a global lock. Use 2PC when: you need synchronous consistency and can tolerate 50–200ms latency per transaction. Use Saga when: you need high throughput, your services are independently deployable, or you cannot afford a blocking coordinator (e-commerce checkout, order processing). At 10,000+ orders/day with sub-100ms latency targets, 2PC is a non-starter.
{{< /faq >}}

{{< faq q="What is the difference between the Outbox pattern and Event Sourcing?" >}}
**Event Sourcing** stores the entire history of state changes as events — the current state is derived by replaying events from the beginning. Every entity has an append-only event log; there is no separate "current state" table. **The Transactional Outbox** is a delivery guarantee mechanism — it ensures events are published reliably *alongside* a primary state change, but the primary state is still stored normally in a relational table. This platform uses the Outbox pattern (not Event Sourcing): services have normal `orders`, `products`, and `customers` tables for current state, with `outbox_events` ensuring reliable delivery of state-change notifications to other services.
{{< /faq >}}

{{< faq q="How do idempotency keys prevent double-charging on payment retry?" >}}
Every `CreateOrder` request includes a `request_id` (UUID generated by the client). When Payment Service processes the `order.created` event, it stores `{order_id}:{payment-capture}` in the deduplication table with a 7-day TTL. If the same event is delivered twice (network retry), the second processing attempt finds the key already in the dedup table and returns early — the payment capture code never runs. The first capture's result is returned instead. This guarantees the customer's card is charged exactly once even if Dapr PubSub delivers the event multiple times.
{{< /faq >}}

---

The Mermaid flowchart diagram below summarizes the complete end-to-end lifecycle of a transactional outbox event, tracing execution from initial SQL transaction commit to background worker relay and consumer compensation:

```mermaid
flowchart TD
    subgraph OrderService [Order Service (PostgreSQL)]
        A[Order Tx Start] --> B[Insert into orders table]
        B --> C[Insert event into outbox table]
        C --> D[Commit DB Transaction]
    end

    subgraph OutboxWorker [Outbox Relay Worker]
        D --> E[Poll outbox table every 500ms]
        E --> F[Publish Event to Dapr PubSub]
        F --> G[Mark outbox record AS PUBLISHED]
    end

    subgraph SagaConsumers [Choreographed Consumers]
        F --> H[Payment Service]
        F --> I[Warehouse Service]
        H -- Fail --> J[Publish PaymentFailed Event]
        J --> K[Order Service Compensating Tx: Cancel Order]
    end
```

🔗 **Next Step:** Continue to [Part 10 — Adr Walkthrough](/series/composable-commerce-migration/part-10-adr-walkthrough/) for the following module in the series.
