---
title: "Part 9: Transactional Outbox & Sagas for Event Delivery"
date: 2026-06-05T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "How the Checkout→Order→Payment saga works: a PostgreSQL transactional outbox, saga choreography, idempotency keys, and circuit breakers."
categories: ["Series", "Software Engineering", "Distributed Systems"]
tags: ["Transactional Outbox", "Saga Pattern", "Distributed Systems", "Kafka", "Golang", "Microservices"]
series: ["composable-commerce-migration"]
weight: 10
slug: "part-9-outbox-saga"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-9-outbox-saga/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 9: Transactional Outbox & Distributed Sagas in Composable Commerce"
  relative: false
keywords: ["transactional outbox pattern", "orchestrated saga ecommerce", "distributed transactions golang", "kafka outbox"]
mermaid: true
---

[← Previous Chapter: Part 8: Phase 3 — Full Cutover Zero Downtime](/series/composable-commerce-migration/part-8-phase3-full-cutover/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 10: 24 Architecture Decisions (ADRs) →](/series/composable-commerce-migration/part-10-adr-walkthrough/)

---

> **Answer-first:** Handle distributed transactions when a customer places an order by combining the Transactional Outbox pattern in PostgreSQL with Saga Choreography over Dapr Pub/Sub, guaranteeing eventual consistency across Cart, Order, Payment, and Fulfillment.

---

When a customer hits the order button on the Composable Commerce platform, up to 7 events must fire in sequence across 4 fully independent services: Order created → Payment authorized → Stock reserved → Fulfillment triggered → Notification sent → Loyalty points awarded → Shipping label generated. Any single link in this chain can snap. The network can drop. The database can crash. A third-party payment gateway can time out.

Without a reliability mechanism, a mere 2% error rate at any step means 2% of all orders end up stuck in a dangling, inconsistent state, forcing humans to jump in and clean up by hand.

**Answer-first:** To decisively solve the dual-write problem to 2026 standards, the platform uses a **choreography-based Saga** combined with a **Transactional Outbox on PostgreSQL** (instead of relying on Dapr's built-in outbox). Events are written to the outbox table atomically within the same transaction as the business change. Relaying is done by a background OutboxProcessor (leveraging PostgreSQL's `SELECT ... FOR UPDATE SKIP LOCKED` trick to avoid contention between replicas), which then publishes to Dapr PubSub. While CDC (Change Data Capture) with Debezium is the popular choice, the Polling + SKIP LOCKED approach proves remarkably effective and easy to operate for teams that do not want to shoulder extra Kafka Connect infrastructure. Every event handler must be designed to be idempotent to neutralize duplicate delivery, and any failure automatically triggers compensating transactions.

## 1. Why Choreography Instead of Orchestration?

There are two schools of thought for implementing a Saga:

**Orchestration**: Stand up an "Order Saga Orchestrator" service in the middle, and this maestro points fingers and issues commands to each service in order, handling any trouble itself:
```
Orchestrator → "Reserve the stock" → Warehouse Service
Orchestrator ← "Stock reserved" ← Warehouse Service
Orchestrator → "Charge the card" → Payment Service
...
```

**Choreography**: Services shout out (emit) domain events on their own, and other services that are listening know to jump in and dance along:
```
Order Service shouts: "order.created"
  → Warehouse Service hears it → reserves stock → shouts back "warehouse.stock.reserved"
  → Payment Service hears it → charges the customer → shouts back "payment.captured"
  → Fulfillment Service hears it → creates a fulfillment task → shouts back "fulfillment.created"
```

Our platform sides with **choreography** for three reasons:
1. No deadly single point of failure (no orchestrator that, if it dies, takes the whole crowd down with it)
2. Services are fully decoupled from each other — Order Service does not even care whether Payment Service exists
3. Each service freely decides its own retry and error-handling strategy without anyone micromanaging

The trade-off: debugging gets harder (tracing a pile of scattered events is much tougher than reading one orchestrator's logs). But no worries — OpenTelemetry distributed tracing sorts that out — every event carries a `correlation_id` that stitches the whole saga chain together.

## 2. The Order Saga Flow

```
Customer checks out
        │
        ▼
┌─────────────────┐
│  Checkout Svc   │  Validate cart, compute the final total
│                 │  Call Order Service over gRPC
└────────┬────────┘
         │ gRPC: CreateOrder
         ▼
┌─────────────────┐
│   Order Svc     │  Spawn an order with status: PENDING
│                 │  Drop an event into the outbox: "orders.order.created"
└────────┬────────┘
         │ Dapr Pub/Sub (async)
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────┐                ┌─────────────────┐
│  Warehouse Svc  │                │   Payment Svc   │
│ Reserve stock   │                │ Charge customer │
│ Emits:          │                │ Emits:          │
│ "stock.reserved"│                │ "payment.       │
└────────┬────────┘                │  captured"      │
         │                         └────────┬────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        │ Both events fly back to Order Service
                        ▼
               ┌─────────────────┐
               │   Order Svc     │  Status → CONFIRMED
               │                 │  Emits: "order.confirmed"
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  Fulfillment    │  Create the picking task
               │  Svc            │  Emits: "fulfillment.created"
               └────────┬────────┘
                        │
                        ├── Notification Svc → send the customer a confirmation email
                        └── Loyalty Svc → award loyalty points
```

## 3. A Homegrown Transactional Outbox on PostgreSQL

The system deliberately avoids Dapr's built-in outbox component (`dapr-outbox`). Why: Dapr's outbox is tightly coupled to its state store (actor state store), inflates operational complexity, and reduces visibility — you cannot clearly see what is sitting in the outbox waiting. Instead, we roll our own with a wonderfully simple PostgreSQL table:

```sql
-- migrations/00005_create_outbox_events.sql
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic           VARCHAR(256) NOT NULL,     -- e.g. "orders.order.created"
    payload         JSONB NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    retry_count     INT NOT NULL DEFAULT 0,
    last_error      TEXT,
    correlation_id  UUID,                       -- The thread stitching the saga's events together for tracing

    -- Index so the outbox processor can find pending events fast
    CONSTRAINT outbox_status_check CHECK (status IN ('PENDING', 'DELIVERED', 'FAILED'))
);

CREATE INDEX idx_outbox_pending ON outbox_events (status, created_at)
WHERE status = 'PENDING';
```

The critical pattern here is: **the outbox event must be INSERTed within the SAME transaction as the business state change**:

```go
// order-service/internal/biz/order_usecase.go

func (uc *OrderUseCase) CreateOrder(ctx context.Context, order *Order) (*Order, error) {
    var created *Order

    err := uc.db.WithTx(ctx, func(tx *sql.Tx) error {
        var err error

        // 1. Write the order to the orders table
        created, err = uc.repo.CreateWithTx(ctx, tx, order)
        if err != nil {
            return fmt.Errorf("creating order: %w", err)
        }

        // 2. Insert the outbox event within that SAME transaction
        //    If this transaction rolls back, the event vanishes with it — atomically
        return uc.outbox.InsertWithTx(ctx, tx, outbox.Event{
            Topic:         "orders.order.created",
            CorrelationID: order.RequestID,  // Doubles as the idempotency key and the tracing ID
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

If the `CreateOrder` database write fails (disk full, constraint violation, etc.), the transaction rolls back immediately — which means the outbox event was never inserted. There will never be a phantom event announcing an order that does not exist.

## 4. OutboxProcessor: Publishing Events With a Delivery Guarantee

The `common/worker` OutboxProcessor quietly runs in the background inside every service:

```go
// order-service/cmd/order-service/main.go

processor := worker.NewOutboxProcessor(db, daprClient, worker.OutboxConfig{
    PollInterval: 500 * time.Millisecond,   // Peek at the table every half second for new events
    BatchSize:    100,                       // Grab 100 events per batch
    MaxRetries:   5,                         // Stubbornly retry 5 times, then seal it away as FAILED
    RetryBackoff: worker.ExponentialBackoff(1*time.Second, 16*time.Second),
})
processor.Start(ctx)
```

The processor's loop:

```go
// common/worker/outbox_processor.go

func (p *OutboxProcessor) processOnce(ctx context.Context) {
    // Pick up pending events (locking them so other processors cannot interfere)
    events, err := p.db.QueryWithLock(ctx, `
        SELECT id, topic, payload, correlation_id, retry_count
        FROM outbox_events
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED  -- The masterstroke that lets many processors work in parallel without stepping on each other
    `, p.config.BatchSize)
    if err != nil { return }

    for _, event := range events {
        // Publish to Dapr PubSub (backed by Redis Streams)
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

        // Stamp as delivered
        p.db.Exec(ctx, `
            UPDATE outbox_events
            SET status = 'DELIVERED', processed_at = NOW()
            WHERE id = $1
        `, event.ID)
    }
}
```

The magic is in `FOR UPDATE SKIP LOCKED`: it lets a whole squad of Order Service pods run OutboxProcessor simultaneously with zero conflicts. Every pod grabs its own private batch of events.

## 5. Idempotency: The Nemesis of Duplicate Delivery

Dapr PubSub, backed by Redis Streams, promises at-least-once delivery — meaning an event may knock on the door twice (rare, but entirely possible when flaky network conditions force retries). Therefore, every event handler must strictly follow the idempotency principle:

```go
// warehouse-service/internal/biz/stock_usecase.go

func (uc *StockUseCase) HandleOrderCreated(ctx context.Context, event *events.OrderCreated) error {
    // Check whether we have already processed this event
    if processed, _ := uc.dedup.Has(ctx, event.OrderID + ":stock-reserve"); processed {
        log.Debugf("Caught a duplicate event for order %s, skipping", event.OrderID)
        return nil
    }

    // Proceed: reserve stock for each item in the order
    for _, item := range event.Items {
        if err := uc.ReserveStock(ctx, item.ProductID, item.Quantity); err != nil {
            // Out of stock → shout the compensation event
            return uc.events.Publish(ctx, "warehouse.stock.insufficient", &events.StockInsufficient{
                OrderID:   event.OrderID,
                ProductID: item.ProductID,
                Requested: item.Quantity,
            })
        }
    }

    // Mark as processed (TTL: 7 days — wide enough to span any retry window)
    uc.dedup.Set(ctx, event.OrderID + ":stock-reserve", 7*24*time.Hour)

    // Publish the happy-path event
    return uc.events.Publish(ctx, "warehouse.stock.reserved", &events.StockReserved{
        OrderID: event.OrderID,
        Items:   event.Items,
    })
}
```

The deduplication key pattern: `{order_id}:{handler_name}`. This lets multiple handlers within the same service process the same event completely independently of each other (e.g. `order-123:stock-reserve` and `order-123:loyalty-check`).

## 6. Compensation: When the Saga Breaks Down Midway

If the stock reservation collapses (out of stock) while the Payment Service has already charged the customer, a compensation chain fires immediately:

```
warehouse.stock.insufficient (shouted by Warehouse Svc)
        │
        ├──► Order Svc: flip status → CANCELLED, shout "order.cancelled"
        │
        └──► Payment Svc: hears "order.cancelled" → dutifully issues a refund
                          → shouts "payment.refunded"
```

These compensation events also go into the transactional outbox — guaranteeing delivery even if the service responsible for compensation is down and gasping for recovery.

```go
// order-service/internal/biz/order_usecase.go

func (uc *OrderUseCase) HandleStockInsufficient(ctx context.Context, event *events.StockInsufficient) error {
    return uc.db.WithTx(ctx, func(tx *sql.Tx) error {
        // Cancel the order
        if err := uc.repo.UpdateStatusWithTx(ctx, tx, event.OrderID, OrderStatusCancelled); err != nil {
            return err
        }

        // Insert the compensation event within the SAME transaction
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

The Payment Service catches a whiff of `orders.order.cancelled` and automatically refunds the customer in full — no human needs to wade in and manually handle out-of-stock cases.

## 7. Resilience: Circuit Breaker + Retry Shields

The `common/errors` package comes fully armed with circuit breakers for every outbound call (payment gateways, shipping APIs):

```go
// common/client/resilience.go — mandatory for all service-to-service calls

// Circuit breaker configuration (locked in by ADR-020)
cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    Name:        "payment-gateway",
    MaxRequests: 5,                           // Half-open: let 5 test requests through
    Interval:    60 * time.Second,            // Reset the failure count every 60s
    Timeout:     30 * time.Second,            // Stay open (tripped) for 30s before trying again
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures >= 5 // 5 consecutive failures trips the breaker immediately
    },
})

// Retry with exponential backoff (ADR-020)
retrier := retry.New(
    retry.WithMaxRetries(3),
    retry.WithBackoff(retry.ExponentialBackoff(1*time.Second, 16*time.Second)),
    retry.WithJitter(0.2),  // Add ±20% jitter to avoid the thundering herd effect
)
```

Circuit breaker states:
- **Closed** (normal): calls flow freely, nothing blocks them
- **Open** (tripped): fail fast immediately, no waiting around, the saga triggers compensation on its own
- **Half-Open** (recovering): let 5 brave test requests through; if they survive → Closed

Thanks to this, one slow payment gateway cannot drag every order through 30-second timeouts — after tasting 5 failures, the circuit breaker trips and chokes off all new calls for 30 seconds (fail fast), then tentatively tries again.

## 8. Distributed Tracing: Stalking a Saga's Footprints

Every event must carry a `correlation_id` (minted right at checkout, propagated through all downstream events):

```go
// Every single event carries a correlation_id for tracing
type OrderCreated struct {
    OrderID       string    `json:"order_id"`
    CustomerID    string    `json:"customer_id"`
    CorrelationID string    `json:"correlation_id"`  // One ID shared by the entire saga family
    // ...
}
```

Open Jaeger (OpenTelemetry), paste the `correlation_id` into the search box, and admire the full saga timeline:

```
Trace: order-saga-correlation-id-xyz
├── [0ms]    Checkout Service: gRPC CreateOrder call
├── [12ms]   Order Service: CreateOrder (PostgreSQL write + outbox insert)
├── [14ms]   OutboxProcessor: publishes the orders.order.created event
├── [20ms]   Warehouse Service: handles HandleOrderCreated (reserves stock)
├── [25ms]   Payment Service: handles HandleOrderCreated (charges the customer)
├── [180ms]  Payment Service: runs ProcessPayment (calls the external gateway)
├── [200ms]  Payment Service: publishes the payment.captured event
├── [22ms]   Warehouse Service: publishes the warehouse.stock.reserved event
├── [210ms]  Order Service: handles HandlePaymentCaptured + HandleStockReserved
├── [215ms]  Order Service: flips status → CONFIRMED, publishes order.confirmed
└── [230ms]  Fulfillment Service: handles HandleOrderConfirmed (picking task created)
```

Total time to run the full saga course: ~230ms for a smooth-sailing order (no payment gateway congestion). If the payment gateway turns sluggish: roughly 2–5 seconds. And if you are unlucky enough to trip the circuit breaker: immediate failure + a compensation chain that fires in just ~50ms.

## Why Build Outbox Polling Yourself Instead of Using Dapr or Debezium CDC?

Dapr has a native outbox and the 2026 market loves CDC (Change Data Capture) with Debezium. But this platform hand-builds Outbox Polling on PostgreSQL, for three core reasons:

1. **Visibility & Control**: With polling, a single `SELECT * FROM outbox_events WHERE status = 'FAILED'` instantly surfaces stuck events. It is easy to intervene, tweak retry counts, or reprocess by hand. Dapr buries state inside actors, and Debezium requires digging through Kafka admin tooling (far more complicated).

2. **Infra Simplicity**: CDC requires feeding an extra Kafka Connect cluster and Debezium workers. For a small team or a system not yet scaling to tens of thousands of TPS, building the background worker directly inside each service's pod saves a mountain of operational cost.

3. **Atomicity with PostgreSQL**: `FOR UPDATE SKIP LOCKED` acts as the perfect barrier, letting dozens of replicas poll the outbox simultaneously with zero row contention, solving the coordination problem without a distributed lock.

The price: you grow extra code you have to maintain (`common/worker/outbox_processor.go`). However, packaging it into the shared `common/worker` library keeps the whole microservice ecosystem running smoothly.

## Next Steps

[Part 10: ADR Walkthrough](/series/composable-commerce-migration/part-10-adr-walkthrough/) shines a light on all 24 Architecture Decision Records — the documents that back every major technology call on this platform, from "why hug Dapr instead of raw Kafka" to "why Kustomize outshines Helm" to "why we dropped Gin for go-kratos." Each ADR is a window into the trade-offs that shaped the platform you have been following.

## FAQ

### Saga pattern vs two-phase commit — when do you use which?

**Two-phase commit (2PC)** promises strict ACID guarantees across distributed resources by puppeteering a coordinator and participants — the catch being that it blocks everyone until the coordinator finishes its verdict, it is slow, and it falls over if the coordinator dies suddenly. **Saga** is more nimble: it delivers eventual consistency through compensating transactions without a global lock. Use 2PC when: you demand strict synchronous consistency and can stomach 50–200ms of latency per transaction. Use Saga when: you want high throughput, your services need to be independently deployable, or you lack the patience for a limping coordinator in the way (typical for e-commerce checkout and order processing). Facing 10,000+ orders/day with sub-100ms latency targets, 2PC was a non-starter from day one.

### What is the real difference between the Outbox pattern and Event Sourcing?

**Event Sourcing** stores the entire history of state changes as a stream of events — the current state is rebuilt by replaying from the beginning. Each entity gets an append-only event log; and naturally there is no separate "current state" table at all. **The Transactional Outbox**, on the other hand, is a delivery guarantee mechanism — it guarantees that events are published right alongside the primary state change, but that state itself is still stored normally in good old relational tables. This platform swipes the card on the Outbox pattern (Event Sourcing is overkill): the services happily keep using regular `orders`, `products`, and `customers` tables for current state, with the `outbox_events` trailer hitched on as the delivery vehicle for state-change notifications to the rest of the gang.

### How do idempotency keys prevent double-charging when a payment is retried?

Every `CreateOrder` call carries a `request_id` (a UUID generated client-side). When the Payment Service receives the `order.created` event, it stamps `{order_id}:{payment-capture}` into the deduplication table with a 7-day TTL. If that pesky event comes around a second time (a network-triggered retry), the second attempt returns early because the key is already registered in the dedup table — the payment capture code never runs. Instead, the result of the earlier successful capture is fetched and returned. This guarantees the customer's wallet gets charged exactly once, no matter how many times Dapr PubSub re-delivers the event.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. See the full table of contents to get the complete architectural context.*

*Need help assessing the risks of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 8: Phase 3 — Full Cutover Zero Downtime](/series/composable-commerce-migration/part-8-phase3-full-cutover/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 10: 24 Architecture Decisions (ADRs) →](/series/composable-commerce-migration/part-10-adr-walkthrough/)
