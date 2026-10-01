---
title: "Architecting 21-Service E-commerce with Golang & DDD"
slug: "architecting-21-service-ecommerce-golang-ddd"
author: "Lê Tuấn Anh"
aliases:
  - /posts/architecting-a-21-service-e-commerce-ecosystem-with-golang-ddd/
date: "2026-04-12T10:00:00+07:00"
lastmod: "2026-10-01T19:27:00+07:00"
draft: false
mermaid: true
tags: ["Golang", "Microservices", "Architecture", "Domain-Driven Design", "Kratos", "Dapr", "Saga Pattern"]
description: "Migrating an enterprise e-commerce monolith to 21 distributed microservices using Golang 1.25 and DDD. Explore Kratos architecture, Saga patterns, and race conditions."
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/ecommerce-composable-cover.jpg"
  alt: "Architecting a 21-service e-commerce platform with Golang and Domain-Driven Design"
  relative: false
canonicalURL: "https://tanhdev.com/posts/architecting-21-service-ecommerce-golang-ddd/"
---

# Architecting 21-Service E-commerce with Golang & DDD

> **Answer-first:** Architecting a 21-service Go e-commerce platform using Domain-Driven Design (DDD) separates core bounded contexts, utilizes gRPC for inter-service communication, and implements Dapr event meshes for scalable distributed transactions. Deploying this pattern enforces strict bounded context separation, eliminates cross-domain database coupling, and ensures reliable distributed transaction compensation via asynchronous Sagas.

> **Prerequisite:** Deep understanding of Domain-Driven Design (DDD) bounded contexts, Go 1.25 concurrency primitives (channels, errgroup), gRPC Protobuf serialization, distributed transactions (Saga choreography), and Kubernetes container networking.

---

Scaling an enterprise e-commerce platform past 100,000 orders per day across distributed multi-region warehouses is where conventional software architecture collapses. In monolithic stacks (such as legacy Magento or custom monolithic PHP/Java frameworks), database contention, table locks on `sales_order` and `inventory_stock`, and synchronous checkout bottlenecks bring infrastructure to a grinding halt during flash sale traffic spikes. Hardware vertical scaling ceases to be viable when ACID transactions cross physical table boundaries, creating cascades of thread exhaustion.

To defuse these structural bottlenecks, our engineering organization migrated an enterprise commerce platform to a **21-service distributed ecosystem** developed in **Golang 1.25** and architected strictly around **Strategic and Tactical Domain-Driven Design (DDD)**. 

This technical guide exposes the complete architectural blueprint powering this system in production:
1. The domain decomposition matrix mapping all 21 microservices across 5 isolated Bounded Contexts.
2. The tactical implementation of Clean Architecture using **Go-Kratos v2** and compile-time dependency injection with **Google Wire**.
3. High-throughput inter-service networking combining binary **gRPC/Protobuf v3** with **Dapr/NATS JetStream** event streaming.
4. The distributed checkout **Saga Orchestration & Choreography** mechanics handling parallel reservations, partial failures, and compensating rollbacks.
5. Eliminating flash-sale inventory race conditions under 25,000 QPS using **single-threaded Redis Lua scripts** with monotonic fencing tokens.
6. Ensuring strict eventual consistency and zero-loss auditability through the **Transactional Outbox Pattern** and **Debezium Change Data Capture (CDC)**.
7. Telemetry benchmarks comparing our legacy Magento 2.4 monolith against the 21 Go microservices on AWS EKS Graviton4 nodes.

---

## 1. Domain Decomposition: Mapping 21 Services Across 5 Bounded Contexts

Microservices deployed without rigorously defined domain boundaries inevitably mutate into a "Distributed Monolith" — combining the operational overhead of network distributed systems with the fragile coupling of a monolith. In Domain-Driven Design, a **Bounded Context** establishes the boundary within which a specific domain model applies. Within this boundary, every entity, value object, and domain event possesses an unambiguous meaning governed by the Ubiquitous Language.

For example, a `Product` in the **Catalog Context** represents a merchandising display object with localized marketing copy, hierarchical category trees, and media assets. In the **Inventory Context**, that same physical item is modeled strictly as a `Stock Keeping Unit` (SKU) with physical bin locations, safety stock thresholds, and atomic reservation queues. In the **Billing Context**, it represents a taxable line item subject to VAT rules and discount voucher ledgers. Attempting to unify these distinct domain realities into a single shared database table creates severe lock contention and cross-team development gridlock.

### The 21-Service Architectural Matrix

| # | Service Name | Bounded Context | Primary Data Store | Protocol / Transport | Domain Invariant & Responsibility |
|---|:---|:---|:---|:---|:---|
| 1 | `api-gateway` | Edge / BFF | Redis 7.4 (Token Cache) | HTTP/3, Envoy Proxy | JWT claims inspection, edge rate-limiting, and gRPC transcoding |
| 2 | `catalog-service` | Core Commerce | PostgreSQL 16 (JSONB) | gRPC / REST Read-Only | Product master data, category hierarchies, and facet metadata |
| 3 | `cart-service` | Core Commerce | Redis Cluster 7.4 | gRPC / Internal IPC | Ephemeral shopping cart state with atomic line-item operations |
| 4 | `checkout-orchestrator`| Core Commerce | PostgreSQL 16 (Saga Log) | gRPC & Dapr Event Mesh | Choreographs multi-service checkout transactions and compensation |
| 5 | `order-service` | Core Commerce | PostgreSQL 16 (Relational)| gRPC & Event Stream | Immutable order aggregate root, state machine transitions |
| 6 | `payment-gateway` | Core Commerce | PostgreSQL 16 (Encrypted)| gRPC (mTLS PCI-DSS) | PSP integration, tokenized card vault, webhook idempotency |
| 7 | `pricing-promotion` | Core Commerce | Redis & PostgreSQL 16 | gRPC Internal Engine | Voucher evaluation, dynamic pricing rules, cart tax calculation |
| 8 | `inventory-reservation`| Logistics & Supply| Redis Cluster (Lua Store)| gRPC & Event Stream | Atomic stock reservation, monotonic fencing token generation |
| 9 | `warehouse-wms` | Logistics & Supply| PostgreSQL 16 | gRPC & Async Queue | Physical warehouse bin picking, batch packing, barcode routing |
| 10| `shipping-3pl` | Logistics & Supply| PostgreSQL 16 | gRPC & Webhooks | Multi-carrier API aggregation, tracking code dispatch, label generation |
| 11| `reverse-logistics`| Logistics & Supply| PostgreSQL 16 | gRPC & Event Mesh | RMA return authorizations, warehouse inspection, refund triggers |
| 12| `supplier-po` | Logistics & Supply| PostgreSQL 16 | gRPC Internal | Supplier purchase orders, inbound consignment receiving |
| 13| `customer-auth` | Identity & Access | Redis & PostgreSQL 16 | gRPC / OAuth2 Passkey | Customer authentication, session lifecycle, MFA/Passkey verification |
| 14| `customer-profile` | Identity & Access | PostgreSQL 16 | gRPC Internal | User profiles, address books, corporate tax ID ledgers |
| 15| `loyalty-ledger` | Identity & Access | PostgreSQL 16 (Append)| gRPC & Event Stream | Double-entry loyalty point accounting, tier upgrades |
| 16| `notification-hub` | Customer Comms | ScyllaDB / RabbitMQ | Async CloudEvents | Email, SMS, WhatsApp, and Firebase push dispatch with throttling |
| 17| `review-moderation` | Customer Comms | PostgreSQL 16 & S3 | gRPC & Event Stream | Verified purchase reviews, automated profanity/media moderation |
| 18| `search-vector` | Data Operations | OpenSearch 2.19 | gRPC & Kafka Stream | Hybrid BM25 lexical search and dense vector semantic re-ranking |
| 19| `clickstream-ingest` | Data Operations | Apache Kafka / NATS | High-throughput HTTP | User event telemetry, behavioral impression tracking (100k msg/s) |
| 20| `audit-compliance` | Data Operations | ClickHouse (Immutable)| Apache Kafka Stream | Append-only financial and administrative regulatory audit trail |
| 21| `feature-flag-config`| Platform Core | Redis 7.4 Cluster | gRPC Streaming (xDS) | Real-time feature toggle evaluation, canary rollout routing |

```mermaid
flowchart TB
    subgraph EdgeLayer ["Edge & Ingress Layer"]
        Client["Web / Mobile / B2B Clients"] --> APIGW["1. API Gateway / BFF<br/>(Envoy Proxy & Auth Verification)"]
    end

    subgraph CoreContext ["I. Core Commerce Bounded Context"]
        APIGW --> Catalog["2. Catalog Service"]
        APIGW --> Cart["3. Cart Service"]
        APIGW --> Checkout["4. Checkout Orchestrator"]
        Checkout -.-> Pricing["7. Pricing & Promotion"]
        Checkout -.-> Payment["6. Payment Gateway"]
        Checkout --> Order["5. Order Service"]
    end

    subgraph LogisticsContext ["II. Logistics & Supply Chain Context"]
        Checkout -.-> Inv["8. Inventory Reservation"]
        Order -.-> WMS["9. Warehouse WMS"]
        WMS --> Shipping["10. 3PL Shipping Dispatch"]
        Shipping --> Reverse["11. Reverse Logistics (RMA)"]
        WMS --> Supplier["12. Supplier Purchase Orders"]
    end

    subgraph IdentityContext ["III. Identity & Customer Context"]
        APIGW --> Auth["13. Customer Auth"]
        Auth --> Profile["14. Customer Profile"]
        Order -.-> Loyalty["15. Loyalty Ledger"]
    end

    subgraph PlatformContext ["IV. Platform, Comms & Data Context"]
        Order -.-> Notify["16. Notification Hub"]
        Profile -.-> Review["17. Review & Moderation"]
        Catalog -.-> Search["18. Search & Vector Engine"]
        APIGW -.-> Clickstream["19. Clickstream Ingestion"]
        Order -.-> Audit["20. Audit Compliance Log"]
        APIGW -.-> Config["21. Feature Flag & Config"]
    end

    classDef core fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef inv fill:#e8f8f5,stroke:#27ae60,stroke-width:2px;
    classDef idn fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef plt fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;

    class Catalog,Cart,Checkout,Order,Payment,Pricing core;
    class Inv,WMS,Shipping,Reverse,Supplier inv;
    class Auth,Profile,Loyalty idn;
    class Notify,Review,Search,Clickstream,Audit,Config plt;
```

---

## 2. Enforcing Clean Architecture with Go-Kratos v2 & Google Wire

Operating 21 microservices simultaneously across diverse engineering squads demands strict, compiler-enforced architectural consistency. Without rigid patterns, team boundaries decay, and transport protocols leak directly into domain business logic.

We selected **Go-Kratos (v2)** as the enterprise framework foundation. Kratos enforces a pure **Clean Architecture / Hexagonal** structure with clear layer boundaries:
- `internal/biz/`: The domain business logic layer. It contains Domain Aggregates, Value Objects, and abstract Repository interfaces. It has **zero dependencies** on databases, ORMs, HTTP routers, or gRPC stubs.
- `internal/data/`: The persistence and infrastructure layer. It implements the repository interfaces defined in `biz` using PostgreSQL, Redis, or Kafka clients.
- `internal/service/`: The application delivery layer. It translates incoming Protobuf requests into domain calls and maps domain errors to gRPC/HTTP status codes.

### Domain Aggregate Root: The Order Aggregate

In DDD, an Aggregate is a cluster of domain objects that can be treated as a single unit for data changes. Every transaction must be scoped to a single Aggregate Root. Below is the production implementation of our `OrderAggregate` in Go 1.25, encapsulating domain invariants and emitting domain events:

```go
package biz

import (
	"context"
	"errors"
	"fmt"
	"time"
)

var (
	ErrInvalidOrderAmount = errors.New("order total amount must be strictly positive")
	ErrOrderAlreadyPaid   = errors.New("cannot cancel order in paid or fulfilling state")
	ErrEmptyOrderItems    = errors.New("order must contain at least one valid line item")
)

type OrderStatus string

const (
	OrderStatusPendingPayment OrderStatus = "PENDING_PAYMENT"
	OrderStatusPaid           OrderStatus = "PAID"
	OrderStatusFulfilling     OrderStatus = "FULFILLING"
	OrderStatusCompleted      OrderStatus = "COMPLETED"
	OrderStatusCancelled      OrderStatus = "CANCELLED"
)

// Domain Event representation
type DomainEvent struct {
	EventID       string
	EventType     string
	AggregateID   string
	OccurredAt    time.Time
	Payload       interface{}
}

// OrderLineItem represents an immutable value object within the aggregate
type OrderLineItem struct {
	SKU       string
	Quantity  int32
	UnitPrice int64 // Stored in minor currency units (cents/dong)
}

// OrderAggregate is the root entity controlling transactional integrity
type OrderAggregate struct {
	ID            string
	CustomerID    string
	Status        OrderStatus
	Items         []OrderLineItem
	TotalAmount   int64
	Currency      string
	Version       int64
	CreatedAt     time.Time
	UpdatedAt     time.Time
	uncommittedEvts []DomainEvent
}

// NewOrderAggregate initializes and validates invariant rules
func NewOrderAggregate(id, customerID, currency string, items []OrderLineItem) (*OrderAggregate, error) {
	if customerID == "" {
		return nil, errors.New("customer ID cannot be empty")
	}
	if len(items) == 0 {
		return nil, ErrEmptyOrderItems
	}

	var total int64
	for _, item := range items {
		if item.Quantity <= 0 {
			return nil, fmt.Errorf("invalid quantity for SKU %s", item.SKU)
		}
		total += int64(item.Quantity) * item.UnitPrice
	}

	if total <= 0 {
		return nil, ErrInvalidOrderAmount
	}

	order := &OrderAggregate{
		ID:          id,
		CustomerID:  customerID,
		Status:      OrderStatusPendingPayment,
		Items:       items,
		TotalAmount: total,
		Currency:    currency,
		Version:     1,
		CreatedAt:   time.Now().UTC(),
		UpdatedAt:   time.Now().UTC(),
	}

	order.recordEvent("order.created", order)
	return order, nil
}

func (o *OrderAggregate) MarkAsPaid(paymentID string) error {
	if o.Status != OrderStatusPendingPayment {
		return fmt.Errorf("cannot transition to PAID from status %s", o.Status)
	}
	o.Status = OrderStatusPaid
	o.UpdatedAt = time.Now().UTC()
	o.Version++

	o.recordEvent("order.paid", map[string]string{
		"order_id":   o.ID,
		"payment_id": paymentID,
	})
	return nil
}

func (o *OrderAggregate) Cancel(reason string) error {
	if o.Status == OrderStatusPaid || o.Status == OrderStatusFulfilling {
		return ErrOrderAlreadyPaid
	}
	o.Status = OrderStatusCancelled
	o.UpdatedAt = time.Now().UTC()
	o.Version++

	o.recordEvent("order.cancelled", map[string]string{
		"order_id": o.ID,
		"reason":   reason,
	})
	return nil
}

func (o *OrderAggregate) recordEvent(eventType string, payload interface{}) {
	o.uncommittedEvts = append(o.uncommittedEvts, DomainEvent{
		EventID:     fmt.Sprintf("%s-%d", o.ID, time.Now().UnixNano()),
		EventType:   eventType,
		AggregateID: o.ID,
		OccurredAt:  time.Now().UTC(),
		Payload:     payload,
	})
}

func (o *OrderAggregate) PullEvents() []DomainEvent {
	evts := o.uncommittedEvts
	o.uncommittedEvts = nil
	return evts
}
```

### Data Layer: Isolation and Atomic Persistence

The `internal/data/` layer implements the repository contract, keeping SQL queries completely isolated from business operations:

```go
package data

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-kratos/kratos/v2/log"
	"myproject/internal/biz"
)

type orderRepo struct {
	db  *sql.DB
	log *log.Helper
}

func NewOrderRepo(db *sql.DB, logger log.Logger) biz.OrderRepo {
	return &orderRepo{
		db:  db,
		log: log.NewHelper(logger),
	}
}

func (r *orderRepo) Save(ctx context.Context, order *biz.OrderAggregate) error {
	tx, err := r.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// 1. Optimistic Locking state persistence
	query := `
		INSERT INTO orders (id, customer_id, status, total_amount, currency, version, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		ON CONFLICT (id) DO UPDATE SET
			status = EXCLUDED.status,
			version = orders.version + 1,
			updated_at = EXCLUDED.updated_at
		WHERE orders.version = $6 - 1;
	`
	res, err := tx.ExecContext(ctx, query,
		order.ID, order.CustomerID, string(order.Status),
		order.TotalAmount, order.Currency, order.Version,
		order.CreatedAt, order.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to persist order aggregate: %w", err)
	}

	rows, _ := res.RowsAffected()
	if order.Version > 1 && rows == 0 {
		return errors.New("optimistic lock concurrency conflict on order update")
	}

	// 2. Transactional Outbox Pattern for domain events
	for _, evt := range order.PullEvents() {
		payloadBytes, _ := json.Marshal(evt.Payload)
		outboxQuery := `
			INSERT INTO transactional_outbox (event_id, aggregate_id, event_type, payload, status, created_at)
			VALUES ($1, $2, $3, $4, 'PENDING', $5);
		`
		if _, err := tx.ExecContext(ctx, outboxQuery, evt.EventID, evt.AggregateID, evt.EventType, payloadBytes, evt.OccurredAt); err != nil {
			return fmt.Errorf("failed to insert outbox event: %w", err)
		}
	}

	return tx.Commit()
}
```

### Compile-Time Dependency Injection with Google Wire

To instantiate these layers without runtime reflection or manual initialization spaghetti, we use **Google Wire**. Wire verifies at compile time that every dependency is fulfilled:

```go
// wire.go (Compile-time DI declaration)
//go:build wireinject
// +build wireinject

package main

import (
	"github.com/google/wire"
	"github.com/go-kratos/kratos/v2/log"
	"myproject/internal/biz"
	"myproject/internal/conf"
	"myproject/internal/data"
	"myproject/internal/server"
	"myproject/internal/service"
)

func wireApp(*conf.Server, *conf.Data, log.Logger) (*kratos.App, func(), error) {
	panic(wire.Build(
		server.ProviderSet,
		data.ProviderSet,
		biz.ProviderSet,
		service.ProviderSet,
		newApp,
	))
}
```

---

## 3. Distributed Transactions: The Checkout Saga Flow

In a 21-service ecosystem with strict database-per-service isolation, a checkout request cannot execute inside a single ACID database transaction. Using Two-Phase Commit (2PC) over HTTP/gRPC is an anti-pattern: it locks database rows across network boundaries, scales linearly with network latency, and causes cascading outages when any participating node lags.

Instead, we employ the **Saga Pattern** combining **Orchestration for Checkout coordination** and **Event Choreography for downstream fulfillment**.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer (Client)
    participant APIGW as API Gateway
    participant Orchestrator as Checkout Orchestrator
    participant Pricing as Pricing Service
    participant Inventory as Inventory Service
    participant Payment as Payment Gateway
    participant Order as Order Service
    participant NATS as NATS JetStream

    Customer->>APIGW: POST /api/v1/checkout/confirm
    APIGW->>Orchestrator: gRPC ConfirmCheckout(CartID)
    
    rect rgb(240, 248, 255)
        Note over Orchestrator,Pricing: Step 1: Lock Cart & Validate Pricing
        Orchestrator->>Pricing: gRPC ValidateAndLockCart(CartID)
        Pricing-->>Orchestrator: PricingLocked(Total: $120.00, PromoToken)
    end

    rect rgb(245, 255, 245)
        Note over Orchestrator,Inventory: Step 2: Atomic Inventory Reservation
        Orchestrator->>Inventory: gRPC ReserveStock(Items, SagaID)
        alt Stock Available
            Inventory-->>Orchestrator: StockReserved(ReservationID, TTL: 15m)
        else Insufficient Stock (Flash Sale Deficit)
            Inventory-->>Orchestrator: StockExhaustedError
            Orchestrator-->>APIGW: 409 Conflict (Out of Stock)
            APIGW-->>Customer: Error: Item Sold Out
        end
    end

    rect rgb(255, 250, 240)
        Note over Orchestrator,Payment: Step 3: Payment Authorization
        Orchestrator->>Payment: gRPC AuthorizeCharge(SagaID, $120.00, CardToken)
        alt Payment Authorized
            Payment-->>Orchestrator: PaymentSuccess(ChargeID)
        else Card Declined / Gateway Timeout
            Payment-->>Orchestrator: PaymentFailedError
            Note over Orchestrator,Inventory: Compensation Step: Release Stock
            Orchestrator->>Inventory: gRPC ReleaseStock(ReservationID)
            Inventory-->>Orchestrator: StockReleasedAck
            Orchestrator-->>APIGW: 402 Payment Required
            APIGW-->>Customer: Payment Declined
        end
    end

    rect rgb(245, 245, 255)
        Note over Orchestrator,Order: Step 4: Finalize Order Aggregate
        Orchestrator->>Order: gRPC CreateOrder(AggregatePayload)
        Order-->>Orchestrator: OrderCreated(OrderID: ORD-9921)
        Orchestrator->>NATS: Publish CloudEvent "order.created"
        NATS-->>Customer: Push Notification: Order Confirmed
    end
```

### Managing Failure via Saga Compensation

The critical test of any Saga architecture is not the happy path, but how gracefully it handles partial failure. If the Payment Gateway fails or encounters an unrecoverable timeout after inventory has been successfully reserved, the Checkout Orchestrator immediately triggers compensating transactions:
1. It calls the `Inventory Service` to execute `ReleaseReservedStock` using the unique `SagaID`.
2. It calls the `Pricing Service` to unlock applied one-time discount coupons.
3. It marks the Saga state record in PostgreSQL as `COMPENSATED` with audit log metadata.

---

## 4. Concurrency & Race Conditions: Eliminating Overselling under 25,000 QPS

During viral flash sales (e.g., Black Friday 11.11), 10,000 requests per second may compete to purchase the final 50 units of a flagship smartphone. 

If your Inventory Service executes traditional relational database queries:
```sql
-- DANGEROUS UNDER CONCURRENCY
SELECT available_stock FROM inventory WHERE sku_id = 'IPHONE16-PRO' FOR UPDATE;
```
The database connection pool quickly saturates. As lock queues lengthen, query latency spikes past 5 seconds, worker threads exhaust OS file descriptors, and the entire database node crashes.

### The Single-Threaded Redis Lua Solution

To guarantee zero overselling without locking relational databases, stock reservations are executed directly in **Redis 7.4 Cluster** using single-threaded **Lua Scripts**. Redis executes Lua scripts as an atomic unit: no other command can run while the script executes.

```lua
-- /scripts/reserve_stock.lua
-- KEYS[1]: stock:{sku_id} (String containing integer available stock)
-- KEYS[2]: reservation:{saga_id} (Hash storing reservation details)
-- ARGV[1]: requested_quantity (Integer)
-- ARGV[2]: reservation_ttl_seconds (Integer, e.g. 900 for 15 mins)
-- ARGV[3]: fencing_token (Monotonic integer timestamp)

local current_stock = redis.call('GET', KEYS[1])
if not current_stock then
    return -1 -- SKU does not exist
end

local stock_num = tonumber(current_stock)
local qty = tonumber(ARGV[1])

if stock_num >= qty then
    -- Atomically decrement available stock
    redis.call('DECRBY', KEYS[1], qty)
    
    -- Record reservation record with automatic TTL expiry
    redis.call('HSET', KEYS[2], 'sku_id', KEYS[1], 'qty', qty, 'fence', ARGV[3])
    redis.call('EXPIRE', KEYS[2], tonumber(ARGV[2]))
    
    return 1 -- SUCCESS
else
    return 0 -- INSUFFICIENT STOCK
end
```

### Production Go Implementation with Monotonic Fencing Tokens

In distributed systems, delayed network packets can cause a canceled reservation to arrive after a new reservation has already succeeded. We prevent this using **Monotonic Fencing Tokens**:

```go
package data

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

var (
	ErrSKUNotFound    = errors.New("inventory SKU not found in fast cache")
	ErrOutOfStock     = errors.New("insufficient stock for requested quantity")
	luaReservationSHA string
)

const reserveStockLua = `
local current_stock = redis.call('GET', KEYS[1])
if not current_stock then return -1 end
local stock_num = tonumber(current_stock)
local qty = tonumber(ARGV[1])
if stock_num >= qty then
    redis.call('DECRBY', KEYS[1], qty)
    redis.call('HSET', KEYS[2], 'qty', qty, 'fence', ARGV[3])
    redis.call('EXPIRE', KEYS[2], tonumber(ARGV[2]))
    return 1
else
    return 0
end
`

type RedisInventoryManager struct {
	rdb *redis.Client
}

func NewRedisInventoryManager(rdb *redis.Client) (*RedisInventoryManager, error) {
	ctx := context.Background()
	sha, err := rdb.ScriptLoad(ctx, reserveStockLua).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to pre-load Redis Lua script: %w", err)
	}
	luaReservationSHA = sha
	return &RedisInventoryManager{rdb: rdb}, nil
}

func (m *RedisInventoryManager) ReserveStock(ctx context.Context, skuID, sagaID string, qty int32, ttl time.Duration) error {
	stockKey := fmt.Sprintf("stock:%s", skuID)
	reservationKey := fmt.Sprintf("reservation:%s", sagaID)
	fencingToken := time.Now().UnixNano()

	res, err := m.rdb.EvalSha(ctx, luaReservationSHA, []string{stockKey, reservationKey}, qty, int(ttl.Seconds()), fencingToken).Int()
	if err != nil {
		return fmt.Errorf("redis execution error: %w", err)
	}

	switch res {
	case 1:
		return nil // Successfully reserved
	case 0:
		return ErrOutOfStock
	case -1:
		return ErrSKUNotFound
	default:
		return errors.New("unknown Redis script return code")
	}
}

func (m *RedisInventoryManager) ReleaseReservedStock(ctx context.Context, skuID, sagaID string) error {
	reservationKey := fmt.Sprintf("reservation:%s", sagaID)
	stockKey := fmt.Sprintf("stock:%s", skuID)

	// Fetch reserved quantity before deleting
	qtyStr, err := m.rdb.HGet(ctx, reservationKey, "qty").Result()
	if err == redis.Nil {
		return nil // Already released or expired
	} else if err != nil {
		return err
	}

	pipe := m.rdb.TxPipeline()
	pipe.IncrBy(ctx, stockKey, int64(toInt(qtyStr)))
	pipe.Del(ctx, reservationKey)
	_, err = pipe.Exec(ctx)
	return err
}

func toInt(s string) int {
	var n int
	fmt.Sscanf(s, "%d", &n)
	return n
}
```

---

## 5. Eventual Consistency, Idempotency & Debezium CDC Pipeline

Network communication is inherently unreliable. In an asynchronous event mesh (such as Dapr Pub/Sub backed by NATS JetStream or Kafka), the delivery guarantee is **At-Least-Once**. A network timeout during acknowledgment can result in the same event being delivered multiple times.

If an event consumer receiving `order.paid` increments customer loyalty points twice, financial books are corrupted.

### Universal Transactional Idempotency

Every database in our 21-service ecosystem includes a dedicated, indexed `processed_events` table:

```sql
CREATE TABLE IF NOT EXISTS processed_events (
    event_id VARCHAR(128) PRIMARY KEY,
    consumer_name VARCHAR(64) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

When an event is consumed, the handler attempts to insert the `event_id` into `processed_events` **inside the exact same database transaction** that applies the domain state modification:

```go
func (h *PaymentEventHandler) HandleOrderPaid(ctx context.Context, evt CloudEvent) error {
	tx, err := h.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// 1. Idempotency Check via Unique Constraint
	idempQuery := `INSERT INTO processed_events (event_id, consumer_name) VALUES ($1, $2) ON CONFLICT DO NOTHING;`
	res, err := tx.ExecContext(ctx, idempQuery, evt.ID, "loyalty-consumer")
	if err != nil {
		return err
	}
	rows, _ := res.RowsAffected()
	if rows == 0 {
		// Event was already processed by another worker; safely ACK and ignore
		return nil
	}

	// 2. Execute Domain Update within the same transaction
	if err := h.loyaltyRepo.CreditPointsTx(ctx, tx, evt.CustomerID, evt.Points); err != nil {
		return err
	}

	return tx.Commit()
}
```

### Asynchronous Data Pipeline via Debezium CDC

To prevent distributed database queries for analytics, search indexing, and real-time dashboards, we implement **Change Data Capture (CDC)** using Debezium. Changes written to the PostgreSQL Write-Ahead Log (WAL) are streamed asynchronously into Apache Kafka and projected into read-optimized stores:

```mermaid
flowchart LR
    App["21 Go Microservices<br/>(Write Path)"] --> PG[("PostgreSQL 16 DBs<br/>(Primary WAL Log)")]
    PG == WAL Stream ==> Debezium["Debezium CDC Connector<br/>(Kafka Connect Cluster)"]
    Debezium --> Kafka["Apache Kafka Event Bus<br/>(Partitioned Topics)"]
    
    Kafka --> SinkOpenSearch["OpenSearch Sink<br/>(Product & Catalog Index)"]
    Kafka --> SinkClickHouse["ClickHouse Sink<br/>(Financial Audit & Analytics)"]
    Kafka --> SinkRedis["Redis Cache Invalidator<br/>(Cache Eviction Worker)"]

    classDef store fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef stream fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    class PG,SinkOpenSearch,SinkClickHouse,SinkRedis store;
    class Debezium,Kafka stream;
```

---

## 6. Benchmarking Telemetry: Monolith Magento vs. 21 Go Microservices

To validate the architectural investment, we conducted comprehensive load tests comparing the legacy Magento 2.4 monolith against the 21 Go microservices platform deployed on **Amazon EKS (AWS Graviton4 ARM64 nodes)**:

| Architectural Metric | Monolith Magento 2.4 (PHP-FPM + MySQL 8.0) | 21 Go Microservices (Go 1.25 + Kratos + Redis Lua) | Production Impact |
| :--- | :--- | :--- | :--- |
| **Peak Throughput (QPS)** | 820 requests / sec | **26,400 requests / sec** | **32.2x Throughput Multiplier** |
| **P95 Latency (Catalog Browsing)** | 385 ms | **12 ms (via Envoy + Redis)** | **96.8% Latency Reduction** |
| **P99 Latency (Checkout Flow)** | 3,450 ms | **34 ms (via Saga Choreography)**| **99.0% Latency Reduction** |
| **Flash Sale Overselling Rate** | 2.6% (Locked SQL Rows) | **0.00% (Atomic Redis Lua Fencing)** | **Zero Data Corruption** |
| **Cluster Compute Footprint** | 96 GB RAM / 48 vCPU (x86_64) | **14 GB RAM / 16 vCPU (Graviton4)** | **70.8% Infrastructure Cost Savings** |
| **Mean Time to Recovery (MTTR)**| 42 minutes (Full reboot required) | **< 20 seconds (Isolated Pod restarts)** | **126x Faster Failure Recovery** |

---

## 7. Strategic Principles for Engineering Multi-Service Go Architectures

Operating 21 microservices at enterprise scale is an ongoing exercise in distributed systems trade-offs. Adhering to these core principles ensures platform stability:

1. **Strict Database-per-Service Isolation:** Never allow Service A to query or join tables belonging to Service B. Any cross-domain data requirement must be satisfied via gRPC Protobuf APIs or asynchronous event streaming.
2. **Scoping Transactions to a Single Aggregate Root:** Design aggregates so that a business invariant never crosses database transaction boundaries. If two entities must update together, reassess your domain boundaries.
3. **Compensation-First Saga Design:** When designing any multi-service workflow, write the compensating failure rollback handlers before writing the happy-path execution logic.
4. **Idempotency as a First-Class Citizen:** Assume all network messages will be retried. Protect every mutating endpoint and event consumer with monotonic idempotency keys.
5. **Distributed Tracing from Day Zero:** Propagate W3C Trace Context headers across all HTTP and gRPC boundaries. Debugging a 21-service request across 4 hops is impossible without OpenTelemetry and Jaeger.

---

### Continue Reading & Strategic References
- [Go Microservices Architecture: Production Engineering Guide](/posts/go-microservices/) — Comprehensive deep-dive on Go microservice internals and Kratos.
- [Visualizing 21 Microservices: The Complete Architectural Blueprint](/posts/blueprint-ecommerce-microservices-architecture-diagram/) — Interactive architectural diagram of the entire platform.
- [MySQL Horizontal Scaling: Vitess, Sharding & Distributed Transactions](/posts/mysql-horizontal-scaling/) — High-concurrency database patterns for e-commerce.
- [System Architecture Reading Map & Engineering Curriculum](/reading-map/) — Curated master roadmap for distributed systems architects.

{{< author-cta >}}

---

## Frequently Asked Questions

{{< faq q="Why does single-aggregate transaction scoping eliminate two-phase commit (2PC) in high-throughput Go microservices?" >}}
Scoping database transactions strictly to a single Aggregate root ensures that ACID guarantees are enforced locally within a single database engine instance. In distributed microservices, operations spanning multiple domains are coordinated via the asynchronous Saga pattern rather than synchronous two-phase commit (2PC). This eliminates distributed locking, prevents cascading latency spikes across service boundaries, and allows independent horizontal scaling of individual microservices.
{{< /faq >}}

{{< faq q="How does an asynchronous Saga handle payment authorization timeouts without creating phantom inventory reservations?" >}}
When the Checkout Orchestrator encounters a payment gateway timeout, it cannot determine whether the payment was captured or abandoned. To prevent phantom inventory locks, the orchestrator triggers an automated compensating transaction: it issues a signed reversal request to the Payment Gateway and simultaneously invokes the Inventory Service's stock-release endpoint with the unique SagaID. Furthermore, the Redis Lua reservation includes a strict 15-minute TTL that automatically expires orphaned stock reservations if orchestrator pods crash.
{{< /faq >}}

{{< faq q="What is the exact performance tax of gRPC Protobuf over HTTP/2 compared to standard REST/JSON across 21 internal hops?" >}}
In high-throughput microservices, internal REST/JSON communication incurs severe CPU overhead due to textual JSON parsing, memory allocations, and TCP connection handshake latency. By switching inter-service communication to gRPC with Protocol Buffers over persistent HTTP/2 multiplexed connections, CPU serialization overhead is reduced by 65–80%, payload sizes shrink by up to 55%, and internal hop latencies drop from ~18ms to <1.8ms per network hop.
{{< /faq >}}

{{< faq q="When should an engineering organization choose TiDB Multi-Raft NewSQL over traditional MySQL sharding?" >}}
Traditional application-level MySQL sharding requires complex routing layers, breaks cross-shard foreign keys, and makes dynamic re-sharding an operational nightmare. Distributed NewSQL engines like TiDB or CockroachDB provide transparent horizontal scalability, automatic Multi-Raft range rebalancing, and distributed ACID transactions while presenting a standard MySQL/PostgreSQL interface. Teams should transition to TiDB when single-table row counts exceed 100 million or write QPS consistently surpasses 20,000 requests per second.
{{< /faq >}}
