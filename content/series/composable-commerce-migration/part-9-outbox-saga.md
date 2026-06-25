---
title: "Part 9: Transactional Outbox & Saga for Guaranteed Delivery"
description: "How the Checkout→Order→Payment→Warehouse saga runs with guaranteed delivery: PostgreSQL outbox, choreography saga, idempotency keys, and circuit breaker."
date: 2026-06-03T10:00:00+07:00
lastmod: 2026-06-24T10:00:00+07:00
draft: false
weight: 10
slug: "part-9-outbox-saga"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Backend Architecture", "Distributed Systems"]
tags: ["Saga Pattern", "Outbox Pattern", "Transactional Outbox", "Dapr", "Event-Driven", "Golang", "Idempotency", "Circuit Breaker"]
series: ["Composable Commerce Migration"]
series_order: 9
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
---

When a customer places an order on the Composable Commerce Platform, seven events need to happen in sequence across four independent services: Order created → Payment authorized → Stock reserved → Fulfillment triggered → Notification sent → Loyalty points awarded → Shipping label generated. Any of these can fail. The network can fail. The database can fail. A third-party payment gateway can time out.

Without a reliability mechanism, a 2% failure rate on any step means 2% of all orders are stuck in an inconsistent state, requiring manual intervention.

**Answer-first:** The platform uses a **choreography-based saga** (not orchestration) with a **custom PostgreSQL transactional outbox** (not Dapr's native outbox component). Events are published atomically within the same database transaction as the business state change. The `common/worker` OutboxProcessor polls the outbox table every 500ms, publishes to Dapr PubSub, and marks events delivered. Failed sagas trigger compensation transactions via dedicated compensation events. Every event handler is idempotent — duplicate delivery is handled by `processed_events` deduplication.

## 1. Why Choreography, Not Orchestration?

Two saga implementation styles:

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

The platform uses **choreography** for three reasons:
1. No single point of failure (no orchestrator to go down)
2. Services remain fully decoupled — Order Service doesn't know Payment Service exists
3. Each service can define its own retry and failure handling independently

The trade-off: debugging is harder (event chains are harder to trace than a single orchestrator's log). This is mitigated by OpenTelemetry distributed tracing — every event carries a `correlation_id` that links the entire saga chain.

## 2. The Order Saga Flow

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

## 3. The Custom PostgreSQL Outbox

The platform deliberately avoids Dapr's native outbox component (`dapr-outbox`). The reason: Dapr's outbox is tightly coupled to Dapr's actor state store, which adds operational complexity and reduces visibility into what's in the outbox. The custom approach uses a simple PostgreSQL table:

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

The critical pattern: **outbox event is inserted in the same transaction as the business state change**:

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

If the `CreateOrder` database write fails (disk full, constraint violation, etc.), the transaction rolls back — and the outbox event is never inserted. No phantom event published for an order that doesn't exist.

## 4. The OutboxProcessor: Publishing with Guarantees

The `common/worker` OutboxProcessor runs as a background goroutine in each service:

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

The processor loop:

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

`FOR UPDATE SKIP LOCKED` is key: multiple Order Service pods can run the OutboxProcessor simultaneously without conflicts. Each pod grabs a different batch of events.

## 5. Idempotency: Handling Duplicate Delivery

Dapr PubSub with Redis Streams provides at-least-once delivery — an event can be delivered more than once (rare, but possible during network retries). Every event handler must be idempotent:

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

The deduplication key pattern: `{order_id}:{handler_name}`. This allows different handlers in the same service to process the same event independently (e.g., `order-123:stock-reserve` and `order-123:loyalty-check`).

## 6. Compensation: When the Saga Fails

If stock reservation fails after payment was already captured, a compensation chain runs:

```
warehouse.stock.insufficient (published by Warehouse Svc)
        │
        ├──► Order Svc: set status → CANCELLED, emit "order.cancelled"
        │
        └──► Payment Svc: subscribes to "order.cancelled" → issue refund
                          → emit "payment.refunded"
```

The compensation events are also transactional outbox events — guaranteed delivery even if the compensating service is temporarily down.

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

Payment Service subscribes to `orders.order.cancelled` and issues a refund automatically — no manual intervention required for stock-out compensation.

## 7. Resilience: Circuit Breaker + Retry

The `common/errors` package implements circuit breakers for all external calls (payment gateways, shipping APIs):

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

The circuit breaker states:
- **Closed** (normal): all requests pass through
- **Open** (tripped): requests fail fast immediately (no waiting), saga compensates
- **Half-Open** (recovery): 5 test requests allowed, if they succeed → Closed

This prevents a slow payment gateway from causing 30-second timeouts on every order — the circuit breaker trips after 5 failures and fails fast for 30 seconds before retrying.

## 8. Distributed Tracing: Following a Saga

Every event carries a `correlation_id` (set at checkout time, propagated through all events):

```go
// All events include correlation_id for tracing
type OrderCreated struct {
    OrderID       string    `json:"order_id"`
    CustomerID    string    `json:"customer_id"`
    CorrelationID string    `json:"correlation_id"`  // Same across entire saga chain
    // ...
}
```

In Jaeger (OpenTelemetry), you can search by `correlation_id` and see the complete saga timeline:

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

Total saga completion time: ~230ms for a successful order (no payment delays). With a slow payment gateway: 2–5 seconds. With circuit breaker tripped: immediate failure + compensation chain in ~50ms.

## Why Not Dapr's Native Outbox?

Dapr v1.11 introduced a native outbox component. The platform uses a custom PostgreSQL outbox instead, for three reasons documented in the codebase:

1. **Visibility**: `SELECT * FROM outbox_events WHERE status = 'FAILED'` shows exactly what's stuck. Dapr's native outbox requires inspecting actor state, which is less transparent.

2. **Control**: Custom retry intervals, per-event-type MaxRetries, and the ability to manually reprocess a specific event ID without re-triggering the entire outbox.

3. **Atomicity guarantee**: The PostgreSQL `FOR UPDATE SKIP LOCKED` pattern guarantees exactly-once processing across multiple service replicas without external locking infrastructure.

The trade-off: more code to maintain (`common/worker/outbox_processor.go` = ~150 lines). The `common/worker` library makes this a zero-cost abstraction for individual services — they call `worker.NewOutboxProcessor(...)` in `main.go` and never think about the implementation.

## What's Next

[Part 10: ADR Walkthrough](/series/composable-commerce-migration/part-10-adr-walkthrough/) reviews all 24 Architecture Decision Records — the documented reasoning behind every major technology choice in this platform, from "why Dapr over raw Kafka" to "why Kustomize over Helm" to "why go-kratos over Gin." Each ADR is a window into the trade-offs that shaped the platform you've been reading about.

## FAQ

### Saga pattern vs two-phase commit — when do you use each?

**Two-phase commit (2PC)** provides ACID guarantees across distributed resources using a coordinator and participants — but it blocks all participants until the coordinator resolves, making it slow and sensitive to coordinator failure. **Saga** provides eventual consistency through compensating transactions, without a global lock. Use 2PC when: you need synchronous consistency and can tolerate 50–200ms latency per transaction. Use Saga when: you need high throughput, your services are independently deployable, or you cannot afford a blocking coordinator (e-commerce checkout, order processing). At 10,000+ orders/day with sub-100ms latency targets, 2PC is a non-starter.

### What is the difference between the Outbox pattern and Event Sourcing?

**Event Sourcing** stores the entire history of state changes as events — the current state is derived by replaying events from the beginning. Every entity has an append-only event log; there is no separate "current state" table. **The Transactional Outbox** is a delivery guarantee mechanism — it ensures events are published reliably *alongside* a primary state change, but the primary state is still stored normally in a relational table. This platform uses the Outbox pattern (not Event Sourcing): services have normal `orders`, `products`, and `customers` tables for current state, with `outbox_events` ensuring reliable delivery of state-change notifications to other services.

### How do idempotency keys prevent double-charging on payment retry?

Every `CreateOrder` request includes a `request_id` (UUID generated by the client). When Payment Service processes the `order.created` event, it stores `{order_id}:{payment-capture}` in the deduplication table with a 7-day TTL. If the same event is delivered twice (network retry), the second processing attempt finds the key already in the dedup table and returns early — the payment capture code never runs. The first capture's result is returned instead. This guarantees the customer's card is charged exactly once even if Dapr PubSub delivers the event multiple times.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? â†’ [Book a 1:1 Architecture Consultation](/hire/)*
