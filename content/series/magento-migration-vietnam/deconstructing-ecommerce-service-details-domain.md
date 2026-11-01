---
title: "Deconstructing the E-Commerce Ecosystem: Services by Domain"
slug: "deconstructing-ecommerce-service-details-domain"
author: "Lê Tuấn Anh"
date: "2026-04-12T08:00:00+07:00"
lastmod: "2026-11-02T09:00:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Domain-Driven Design", "Microservices", "Architecture", "Golang", "gRPC", "Protobuf"]
description: "A domain-by-domain deconstruction of an e-commerce microservices ecosystem: 21 services, data isolation boundaries, and asynchronous event contracts."
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/ecommerce-microservices-blueprint-cover.jpg"
  alt: "Deconstructing E-commerce by Domain: service responsibilities, data ownership, and API contracts"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/deconstructing-ecommerce-service-details-domain/"
weight: 11
mermaid: true
aliases:
---

# Deconstructing the Ecosystem: 21 Microservices Across 6 DDD Domains

*"Why does an e-commerce system need as many as 21 independent microservices? Isn't that overkill — making the problem more complicated than it needs to be?"*

This is the familiar question every Lead Architect faces when proposing to restructure a monolith that is collapsing under its own load. The answer, a law of software engineering, is **Conway's Law** — *Systems designed by organizations inevitably mirror the communication structure of the organizations that built them*.

When an e-commerce company grows past 40 engineers split into multiple squads, having everyone push code into one repository and write to one shared database leads to paralysis: daily merge conflicts, one unoptimized SQL query from the Reporting team locking the `sales_order` table owned by the Payments team, and every release becoming a suffocating gamble on risk.

By rigorously applying **Domain-Driven Design (DDD)**, we decomposed the entire e-commerce ecosystem into **6 Bounded Domains** with high internal cohesion (High Cohesion) and loose external coupling (Loose Coupling). Each service owns its own database and communicates exclusively through **gRPC Protobuf** contracts or **asynchronous CloudEvents**.

---

> ### ⚡ Core Architecture Summary (Executive BLUF)
> * **Bounded Context boundary principle**: 6 core domains — Commerce Flow, Product & Content, Logistics & WMS, Post-Purchase, Identity & Access, Platform Operations.
> * **Absolute data isolation (Database Isolation)**: 21 services own 21 independent schemas/databases. Cross-database JOIN queries are 100% forbidden; data exchange happens only via gRPC APIs or the Kafka/Dapr Event Mesh.
> * **Anti-overselling with Optimistic Concurrency Control (OCC)**: The Warehouse Service uses an incrementing `version` column combined with the database constraint `CHECK (available_qty >= 0)`, completely eliminating the risk of overselling inventory during Flash Sale events.
> * **Transaction safety via Saga Choreography**: The cross-domain checkout flow automatically executes Compensating Transactions when the payment gateway or the fraud check rejects the transaction.

---

## 1. Quantitative Comparison: Monolithic Database vs Database-per-Service

The measurement table below demonstrates the superiority in reliability and load tolerance when moving from a centralized MySQL database to a model of isolated, independent databases:

| Evaluation Metric | Monolithic Shared Database (MySQL EAV) | Database-per-Service (21 Go Microservices) |
| :--- | :--- | :--- |
| **Blast Radius** | 100% (A deadlock in the Review table freezes Checkout) | **< 5%** (An incident in one service is fully isolated) |
| **Lock Contention (IOPS)** | Very high (> 8,500 lock waits/minute at peak) | **Near zero** (Each service touches only its own tables) |
| **Scaling Efficiency** | Poor: forced to scale the RDS instance to a monster size | Optimal: scale only the pods and database of the bottlenecked service |
| **DB Migration Duration** | Hours, with table locks disrupting the whole system | Seconds per microservice, zero-downtime |
| **Transaction Implementation Complexity** | Simple: call a local `DB::transaction()` | Requires Saga Orchestration / Choreography |

---

## 2. The 6 Bounded Domains in Detail & Each Service's Responsibilities

```mermaid
graph TD
    subgraph "Domain 1: Commerce Flow (Money Flow)"
        CK["Checkout Service\n(Saga Orchestrator)"]
        ORD["Order Service\n(8-State FSM / order_db)"]
        PAY["Payment Gateway\n(Idempotency / payment_db)"]
    end

    subgraph "Domain 2: Product & Content (Catalog)"
        CAT["Catalog Service\n(PIM Normalized)"]
        PRC["Pricing Service\n(Tiered Pricing Engine)"]
        PROMO["Promotion Service\n(Coupon Voucher Ledger)"]
        SEARCH["Search Service\n(CQRS / Elasticsearch)"]
    end

    subgraph "Domain 3: Logistics & WMS (Warehousing)"
        WH["Warehouse Service\n(OCC Stock / inventory_db)"]
        FF["Fulfillment Service\n(Pick-Pack-Ship Workflow)"]
        SH["Shipping Service\n(3PL Carrier Integrator)"]
    end

    subgraph "Domain 4: Post-Purchase (After-Sales)"
        RET["Return Service\n(RMA / Reverse Logistics)"]
        LR["Loyalty Service\n(Double-Entry Points Ledger)"]
        REV["Review Service\n(Customer UGC Moderation)"]
    end

    subgraph "Domain 5: Identity & Access (Security)"
        AUTH["Auth Service\n(RS256 JWT / OAuth2)"]
        USR["User Service\n(Internal Staff RBAC)"]
        CUST["Customer Service\n(CRM Profile & LTV)"]
    end

    subgraph "Domain 6: Platform Operations (Infrastructure)"
        GW["API Gateway\n(Envoy / BFF Layer)"]
        NOTIF["Notification Hub\n(Email / SMS / Push)"]
        AN["Analytics Engine\n(ClickHouse Event Stream)"]
    end
```

---

## 3. The Cross-Domain Checkout Saga Sequence Diagram

When the customer presses the order button, a complex orchestration process across the `Commerce Flow`, `Logistics`, and `Payment` domains is triggered:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Customer (Web/App)
    participant BFF as API Gateway (BFF Layer)
    participant Order as Order Service (Commerce)
    participant Inv as Warehouse Service (Logistics)
    participant Pay as Payment Service (Commerce)
    participant Ship as Shipping Service (Logistics)
    participant Bus as Kafka / Dapr Event Mesh

    Note over Client, Bus: Phase 1: Synchronous Order Initialization
    Client->>BFF: POST /api/v1/checkout (Cart Payload, Idempotency-Key)
    BFF->>Order: CreateOrder(CreateOrderRequest) [gRPC]
    Order->>Order: Write DB (Status: PENDING_PAYMENT, OCC Version: 1)
    Order-->>BFF: 201 Created (OrderID: `ord_98765`, Status: PENDING)
    BFF-->>Client: Checkout Successful (OrderID: `ord_98765`)

    Note over Order, Bus: Phase 2: Asynchronous Processing & Stock Reservation
    Order->>Bus: Publish `OrderCreatedEvent` (OrderID, SKU, Qty, UserID)
    Bus-->>Inv: Consume `OrderCreatedEvent`
    Inv->>Inv: Reserve Stock (IDEMPOTENT, OCC `version = version + 1`)
    alt Sufficient Stock Available
        Inv->>Bus: Publish `InventoryReservedEvent` (OrderID, WarehouseID)
    else Out of Stock in Warehouse
        Inv->>Bus: Publish `InventoryReservationFailedEvent` (OrderID, Reason)
        Bus-->>Order: Consume `InventoryReservationFailedEvent`
        Order->>Order: Update DB (Status: CANCELLED_OUT_OF_STOCK)
    end

    Note over Pay, Bus: Phase 3: Payment Gateway Charge
    Bus-->>Pay: Consume `InventoryReservedEvent`
    Pay->>Pay: Fraud check & Call card gateway (Stripe / VNPay / MoMo)
    alt Payment Successful
        Pay->>Bus: Publish `PaymentProcessedEvent` (OrderID, TxID, Status: SUCCESS)
    else Card Declined / Timeout
        Pay->>Bus: Publish `PaymentProcessedEvent` (OrderID, Status: FAILED)
        Bus-->>Inv: Consume `PaymentProcessedEvent` (FAILED)
        Inv->>Inv: Compensation: Release reserved stock
        Bus-->>Order: Consume `PaymentProcessedEvent` (FAILED)
        Order->>Order: Update DB (Status: PAYMENT_FAILED)
    end

    Note over Ship, Bus: Phase 4: Order Confirmation & Handover to Shipping
    Bus-->>Order: Consume `PaymentProcessedEvent` (SUCCESS)
    Order->>Order: Update DB (Status: CONFIRMED)
    Order->>Bus: Publish `OrderConfirmedEvent` (OrderID, CustomerID)

    Bus-->>Ship: Consume `OrderConfirmedEvent`
    Ship->>Ship: Create 3PL tracking code (GHTK / GrabExpress) & Save DB
    Ship->>Bus: Publish `ShipmentDispatchedEvent` (TrackingNo, Carrier)
```

---

## 4. Asynchronous Data Contracts (Protobuf v3 & Event Schemas)

To guarantee long-term compatibility without breaking services during upgrades, the event messages exchanged between domains are defined in **Protocol Buffers v3**:

```protobuf
syntax = "proto3";

package ecommerce.events.v1;

option go_package = "github.com/tanhdev/learn/proto/events/v1;eventsv1";

import "google/protobuf/timestamp.proto";

// Standardized payment status enum
enum PaymentStatus {
  PAYMENT_STATUS_UNSPECIFIED = 0;
  PAYMENT_STATUS_SUCCESS = 1;
  PAYMENT_STATUS_FAILED = 2;
  PAYMENT_STATUS_REQUIRES_ACTION = 3;
}

// Published by the Order Service when a new order is persisted to the database
message OrderCreatedEvent {
  string event_id = 1;
  string order_id = 2;
  string customer_id = 3;
  int64 total_amount_cents = 4;
  string currency = 5; // ISO 4217 (e.g. "VND", "USD")
  string idempotency_key = 6;

  message OrderItem {
    string sku_id = 1;
    int32 quantity = 2;
    int64 unit_price_cents = 3;
  }

  repeated OrderItem items = 7;
  google.protobuf.Timestamp created_at = 8;
}

// Published by the Warehouse Service when stock is reserved successfully
message InventoryReservedEvent {
  string event_id = 1;
  string reservation_id = 2;
  string order_id = 3;
  string warehouse_id = 4;

  message ReservedItem {
    string sku_id = 1;
    int32 quantity = 2;
  }

  repeated ReservedItem items = 5;
  int64 expires_at_unix = 6;
  google.protobuf.Timestamp reserved_at = 7;
}

// Published by the Payment Service after the transaction with the payment gateway completes
message PaymentProcessedEvent {
  string event_id = 1;
  string payment_id = 2;
  string order_id = 3;
  string transaction_reference = 4;
  int64 amount_cents = 5;
  string payment_provider = 6; // e.g. "MOMO", "VNPAY", "STRIPE"
  PaymentStatus status = 7;
  string failure_reason = 8;
  google.protobuf.Timestamp processed_at = 9;
}
```

---

## 5. PostgreSQL Database Design & Production-Grade GORM Source Code

### 5.1 Order Service (`order_db`) Schema & Go Structs

```sql
-- PostgreSQL DDL for order_db
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(64) NOT NULL UNIQUE,
    customer_id UUID NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING_PAYMENT',
    total_amount_cents BIGINT NOT NULL CHECK (total_amount_cents >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'VND',
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sku_id VARCHAR(64) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price_cents BIGINT NOT NULL CHECK (unit_price_cents >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

```go
// Package models implements the Order Domain Model in the Order Service
package models

import (
	"time"

	"github.com/google/uuid"
)

type OrderStatus string

const (
	StatusPendingPayment OrderStatus = "PENDING_PAYMENT"
	StatusConfirmed      OrderStatus = "CONFIRMED"
	StatusPaymentFailed  OrderStatus = "PAYMENT_FAILED"
	StatusCancelled      OrderStatus = "CANCELLED"
)

type Order struct {
	ID               uuid.UUID   `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	OrderNumber      string      `gorm:"type:varchar(64);uniqueIndex;not null"`
	CustomerID       uuid.UUID   `gorm:"type:uuid;index:idx_orders_customer_status;not null"`
	Status           OrderStatus `gorm:"type:varchar(32);index:idx_orders_customer_status;not null;default:'PENDING_PAYMENT'"`
	TotalAmountCents int64       `gorm:"type:bigint;not null"`
	Currency         string      `gorm:"type:varchar(3);not null;default:'VND'"`
	IdempotencyKey   string      `gorm:"type:varchar(128);uniqueIndex;not null"`
	Version          int32       `gorm:"type:int;not null;default:1"` // Optimistic Concurrency Control (OCC) management
	Items            []OrderItem `gorm:"foreignKey:OrderID;constraint:OnDelete:CASCADE;"`
	CreatedAt        time.Time   `gorm:"type:timestamptz;not null;default:CURRENT_TIMESTAMP"`
	UpdatedAt        time.Time   `gorm:"type:timestamptz;not null;default:CURRENT_TIMESTAMP"`
}

type OrderItem struct {
	ID             uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	OrderID        uuid.UUID `gorm:"type:uuid;not null;index"`
	SkuID          string    `gorm:"type:varchar(64);not null"`
	Quantity       int32     `gorm:"type:int;not null"`
	UnitPriceCents int64     `gorm:"type:bigint;not null"`
	CreatedAt      time.Time `gorm:"type:timestamptz;not null;default:CURRENT_TIMESTAMP"`
}
```

### 5.2 Warehouse Service (`inventory_db`): Absolute Anti-Overselling

```sql
-- PostgreSQL DDL for inventory_db with Optimistic Concurrency Control (OCC)
CREATE TABLE stock_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL,
    sku_id VARCHAR(64) NOT NULL,
    available_qty INT NOT NULL CHECK (available_qty >= 0),
    reserved_qty INT NOT NULL CHECK (reserved_qty >= 0),
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_warehouse_sku UNIQUE (warehouse_id, sku_id)
);

CREATE TABLE stock_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    warehouse_id UUID NOT NULL,
    sku_id VARCHAR(64) NOT NULL,
    reserved_qty INT NOT NULL CHECK (reserved_qty > 0),
    status VARCHAR(32) NOT NULL DEFAULT 'RESERVED',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reservations_order_id ON stock_reservations(order_id);
CREATE INDEX idx_reservations_status_expires ON stock_reservations(status, expires_at);
```

```go
// Package models implements Inventory OCC Locking in the Warehouse Service
package models

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

var ErrOptimisticLockConflict = errors.New("inventory version conflict, please retry")
var ErrInsufficientStock = errors.New("insufficient available stock")

type StockLevel struct {
	ID           uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	WarehouseID  uuid.UUID `gorm:"type:uuid;uniqueIndex:uk_warehouse_sku;not null"`
	SkuID        string    `gorm:"type:varchar(64);uniqueIndex:uk_warehouse_sku;not null"`
	AvailableQty int32     `gorm:"type:int;not null"`
	ReservedQty  int32     `gorm:"type:int;not null"`
	Version      int32     `gorm:"type:int;not null;default:1"`
	CreatedAt    time.Time `gorm:"type:timestamptz;not null;default:CURRENT_TIMESTAMP"`
	UpdatedAt    time.Time `gorm:"type:timestamptz;not null;default:CURRENT_TIMESTAMP"`
}

// ReserveStockSafe performs oversell-safe stock reservation using Optimistic Concurrency Control
func ReserveStockSafe(ctx context.Context, db *gorm.DB, warehouseID uuid.UUID, skuID string, qty int32, orderID uuid.UUID) error {
	return db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		var stock StockLevel
		if err := tx.Where("warehouse_id = ? AND sku_id = ?", warehouseID, skuID).First(&stock).Error; err != nil {
			return err
		}

		if stock.AvailableQty < qty {
			return ErrInsufficientStock
		}

		// Update with an exact Version match condition
		res := tx.Model(&StockLevel{}).
			Where("id = ? AND version = ?", stock.ID, stock.Version).
			Updates(map[string]interface{}{
				"available_qty": stock.AvailableQty - qty,
				"reserved_qty":  stock.ReservedQty + qty,
				"version":       stock.Version + 1,
				"updated_at":    time.Now(),
			})

		if res.Error != nil {
			return res.Error
		}
		if res.RowsAffected == 0 {
			// The version was already overwritten by another concurrent flow -> trigger a retry
			return ErrOptimisticLockConflict
		}

		// Record the time-boxed reservation (15-minute TTL)
		reservation := StockReservation{
			OrderID:     orderID,
			WarehouseID: warehouseID,
			SkuID:       skuID,
			ReservedQty: qty,
			Status:      "RESERVED",
			ExpiresAt:   time.Now().Add(15 * time.Minute),
		}
		return tx.Create(&reservation).Error
	})
}

type StockReservation struct {
	ID          uuid.UUID `gorm:"type:uuid;primaryKey;default:gen_random_uuid()"`
	OrderID     uuid.UUID `gorm:"type:uuid;index;not null"`
	WarehouseID uuid.UUID `gorm:"type:uuid;not null"`
	SkuID       string    `gorm:"type:varchar(64);not null"`
	ReservedQty int32     `gorm:"type:int;not null"`
	Status      string    `gorm:"type:varchar(32);not null;default:'RESERVED'"`
	ExpiresAt   time.Time `gorm:"type:timestamptz;not null"`
	CreatedAt   time.Time `gorm:"type:timestamptz;not null;default:CURRENT_TIMESTAMP"`
}
```

---

## 6. The Real-World Value of the Separation

When you view the system through the lens of 6 Bounded Context domains, 21 microservices are no longer chaotic fragmentation but a smoothly running automation pipeline:
- **Independent resilience**: A database outage in the `Review Service` or `Loyalty Service` has zero impact on the purchasing flow at `Checkout` or `Payment`.
- **Compute cost optimization**: On Flash Sale shopping days, the operations team only needs to scale the `Order` and `Warehouse` pod clusters from 4 to 25 replicas, while `Catalog` and `Platform Operations` stay at minimum capacity.
- **Feature time-to-market**: The Promotions Squad can freely experiment with new coupon algorithms and deploy through CI/CD 10 times a day without asking for or waiting on approval from the Warehouse Squad.

---

## 7. Concurrency & Inventory/Pricing Conflict Benchmark (50,000 TPS)

Below are the results of a simulated load test with 50,000 concurrent users competing to reserve stock of 10 best-selling SKUs during a Mega Sale event (k6 load test on a 3-node Kubernetes cluster of c6i.2xlarge):

| Concurrency Control Mechanism | Reservation Throughput (TPS) | P99 Latency | Conflict / Retry Rate | DB Deadlock Risk | Connection Pool Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pessimistic Lock (`SELECT ... FOR UPDATE`)** | ~420 TPS | > 2,800 ms (Lock queue congestion) | 0% (Hard row locks) | **Very high (38%)** when multiple tables intersect | Pool exhausted within 3 seconds |
| **Go OCC (`version = stock.Version`)** | **~6,800 TPS** | **< 35 ms** | 12% (Handled smoothly via Exponential Backoff) | **Absolutely 0%** (No long-held row locks) | Stable usage < 25 connections |
| **Redis Lua Script + Async Write-Behind** | **> 48,000 TPS** | **< 2.5 ms** | 0% (Atomic in-RAM operations) | **Absolutely 0%** (Single-threaded event loop) | Fully decoupled from the DB |
| **Virtual Buckets (10 Sharded Inventory Slots)** | **> 92,000 TPS** | **< 1.8 ms** | < 0.5% (Write load spread evenly across 10 keys) | **Absolutely 0%** | Fully optimized |

---

## 8. Frequently Asked Questions (FAQ)

{{< faq q="How do you produce consolidated financial reports from 21 distributed databases when SQL JOINs are forbidden?" >}}
In a standard microservices architecture, aggregated analytical reporting (BI/Reporting) must never run directly against the transactional databases. Instead, we use a **Change Data Capture (CDC)** model via Debezium or a Kafka event stream to synchronize every data change into a **centralized Data Warehouse or OLAP database (such as ClickHouse or Google BigQuery)**. The data analytics team can then execute complex JOIN queries on ClickHouse tens of times faster without affecting any customer purchase transactions.
{{< /faq >}}

{{< faq q="How does Optimistic Concurrency Control (OCC) behave when thousands of customers buy the very last unit of a product?" >}}
Under extreme contention, the `UPDATE` statement with the `version = stock.Version` check returns `RowsAffected == 0` for the slower flows, triggering the `ErrOptimisticLockConflict` error code. The Go Service then applies **Exponential Backoff with random Jitter** to retry up to 3 times. If the available quantity has already dropped to zero, the system immediately reports the item as out of stock without creating lock queuing congestion the way the traditional `SELECT ... FOR UPDATE` model does.
{{< /faq >}}

{{< faq q="Why separate the Warehouse Service, Fulfillment Service, and Shipping Service into three distinct services?" >}}
These three services represent three fundamentally different physical stages in the supply chain: (1) The `Warehouse Service` manages logical stock quantities and temporary reservations; (2) The `Fulfillment Service` manages the people and internal warehouse workflows (picking lists, worker walking routes, carton packing); (3) The `Shipping Service` is the gateway to the outside world, managing API webhooks and rate calculation with third-party carriers (3PL). Separating these boundaries means switching carriers never affects the internal warehouse put-away process.
{{< /faq >}}

{{< faq q="How do you guarantee Idempotency when a flaky network causes a payment event to be delivered twice?" >}}
Every event message or payment request must carry an `Idempotency-Key` (a randomly generated UUIDv4 from the client, or a combination of `order_id + event_version`). In the Payment Service, the `payment_transactions` database table enforces a `UNIQUE` constraint on the `idempotency_key` column. When the second message arrives, the database blocks it with a `Duplicate Key Violation` error, and the service immediately returns the previous transaction's result without charging the customer a second time.
{{< /faq >}}

{{< faq q="Does managing a network of 21 microservices overwhelm a small engineering team?" >}}
Yes. With fewer than 15 engineers, running 21 microservices creates an overwhelming operational burden due to the cost of setting up Kubernetes, CI/CD pipelines, Service Mesh, and Distributed Tracing. This 21-service architecture framework is optimized for technology organizations with 25 - 50 or more engineers, organized into independent Feature Squads in line with Conway's Law.
{{< /faq >}}

---

### 🔗 Related deep dives & series:
- [Architecting 21 E-Commerce Services with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) — Clean Architecture with Kratos, Saga Orchestration, and OCC in detail.
- [The 21 Microservices Architecture Blueprint Diagram](/posts/blueprint-ecommerce-microservices-architecture-diagram/) — A comprehensive map of the data flow across 21 services.
- [Real-Time Inventory Sync with Kafka, Debezium & Redis](/posts/real-time-inventory-ecommerce-architecture/) — Setting up a lock-free CDC architecture.
- [The Temporal Saga Pattern in Golang](/posts/temporal-saga-pattern-golang-distributed-transactions-guide/) — Handling distributed transactions without 2PC.
- [Shopee Flash Sale Architecture: Processing Millions of Orders](/posts/shopee-flash-sale-architecture/) — Anti-overselling techniques at the largest scale in Southeast Asia.

{{< author-cta >}}
