---
title: "Deconstructing the Ecosystem: Service Details by Domain"
slug: "deconstructing-ecommerce-service-details-domain"
author: "Lê Tuấn Anh"
date: "2026-04-12T08:00:00+07:00"
lastmod: "2026-04-12T08:00:00+07:00"
draft: false
tags: ["Domain-Driven Design", "Microservices", "System Design", "Architecture"]
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/ecommerce-microservices-blueprint-cover.png"
  alt: "Deconstructing E-commerce by Domain: service responsibilities, data ownership, and API contracts"
  relative: false
canonicalURL: "https://tanhdev.com/posts/deconstructing-ecommerce-service-details-domain/"
---

**Answer-first:** We partition the e-commerce domain into six logical business domains—Identity, Catalog, Cart, Checkout, Order, and Fulfillment—containing 21 isolated services. Each service owns its database exclusively, communicating asynchronously via event brokers to ensure scalability and prevent tight coupling.

### What You'll Learn That AI Won't Tell You
- Why microservices must own their schema migrations (via Golang-Migrate) independently, and the specific event schemas that prevent transactional coupling.
- Real-world database deadlocks encountered when segregating order history from the catalog database, and how they were solved using CQRS.

---

"Why 21 services? Isn't that overkill?" 

This is the most common question I get when discussing the Golang microservice architecture we built to handle massive scale. The short answer is: **No, because Conway's Law is real.** 

When you have multiple squads touching the same codebase, feature overlap creates friction. By rigidly enforcing **Domain-Driven Design (DDD)**, we sliced our e-commerce monolith into 6 highly cohesive, loosely coupled Business Domains. Each domain is completely self-sufficient and owns its own Postgres databases.

Below, we go beyond the high-level diagrams to deconstruct the exact business capabilities, storage choices, and operational profiles of the 21 individual microservices that power this ecosystem.

---

## 1. The Transactional Commerce Flow

This domain is the financial engine of the company. It operates under strict transactional guarantees. If any service here experiences elevated latency, checkout drop-off rates spike immediately.

```
+-------------------------------------------------------------+
|                  TRANSACTIONAL COMMERCE FLOW                |
+---------------------+-----------------+---------------------+
|  Checkout Service   |  Order Service  |   Payment Service   |
| (Saga Orchestration)|  (Order State)  |  (Gateway Integr.)  |
+---------------------+-----------------+---------------------+
|      Postgres       |    Postgres     |      Postgres       |
+---------------------+-----------------+---------------------+
```

### Checkout Service
* **Role**: Stateless orchestrator of order creation.
* **Capabilities**: Coordinates the multi-step checkout workflow. It pulls transient cart states, queries the Pricing Service to revalidate catalog prices, calls the Promotion Service to check coupons, and hits the Warehouse Service to request pessimistic stock reservations. 
* **Storage**: Redis for distributed checkout session locking (preventing duplicate submissions) and temporary Saga state logs.
* **Key Challenge**: If a downstream service fails mid-checkout, it must coordinate compensating transactions (e.g., releasing inventory) to avoid inconsistent states.

### Order Service
* **Role**: Ledger of record for customer purchases.
* **Capabilities**: Maintains the life history of orders through 8 state transitions: `PENDING`, `RESERVED`, `PAID`, `PROCESSING`, `SHIPPED`, `DELIVERED`, `CANCELLED`, and `REFUNDED`. It publishes the critical `order.created` and `order.status_updated` events.
* **Storage**: PostgreSQL with transactional isolation set to `READ COMMITTED` and indexed on `customer_id` and `created_at` for rapid retrieval.
* **Key Challenge**: Emitting events reliably. We use the **Transactional Outbox pattern** to write both the order record and the event payload in a single local database transaction, which a separate relay process publishes to Kafka.

### Payment Service
* **Role**: Secured gateway to payment networks.
* **Capabilities**: Integrates with external payment processors (Stripe, VNPay, MoMo, PayPay). It handles cryptographic webhook validation, manages payment redirect sessions, and tracks refund authorizations.
* **Storage**: PostgreSQL (highly encrypted and tokenized, storing no raw card numbers) with audit logging on all ledger operations.
* **Key Challenge**: Handling network timeouts during API handshake. Implementations must be fully idempotent so that a retried callback from a payment gateway never triggers duplicate credit ledger updates.

---

## 2. Product Catalog & Pricing

Unlike the transactional commerce flow, the Product Catalog domain is read-heavy. Reads outnumber writes by a factor of 10,000:1. The architecture prioritizing sub-millisecond page rendering and high cache-hit ratios.

### Catalog Service
* **Role**: Single source of truth for product taxonomy.
* **Capabilities**: Manages complex product details, specifications, nested category structures, and brand data. It supports bulk catalog updates from suppliers.
* **Storage**: MongoDB for the flexible document-based catalog structure, allowing custom specifications per category without database schema alterations.
* **Key Challenge**: Syncing catalog changes. Any update to a product must immediately invalidate corresponding Redis cache keys globally and push updates to the Search Service.

### Pricing Service
* **Role**: Volatile price calculation engine.
* **Capabilities**: Isolates pricing matrices from the catalog. It evaluates tiered prices, warehouse-specific pricing (e.g., different pricing for northern vs. southern warehouses), dynamic discount overrides, and tax calculations.
* **Storage**: Redis cache backed by PostgreSQL.
* **Key Challenge**: High-concurrency throughput. Since every search result and cart item requires price verification, this service runs entirely in memory, utilizing local Go maps refreshed every 60 seconds from database tables.

### Promotion Service
* **Role**: Marketing and coupon engine.
* **Capabilities**: Evaluates discount codes, runs cart-wide rules (e.g., "Spend $100, get $10 off"), evaluates buy-one-get-one (BOGO) campaigns, and tracks individual coupon redemption limits.
* **Storage**: PostgreSQL for coupon definition, Redis for counting active usage of highly contested codes.
* **Key Challenge**: Race conditions when multiple users redeem the final remaining coupon code simultaneously.

---

## 3. Logistics & Warehouse Management

This domain translates digital orders into physical routing actions. It must maintain a high degree of real-world accuracy.

### Warehouse Service
* **Role**: Inventory and multi-warehouse stock allocator.
* **Capabilities**: Tracks inventory quantity per SKU across multiple geographic distribution hubs. It processes inventory allocation requests and manages physical stock levels.
* **Storage**: PostgreSQL.
* **Key Challenge**: Preventing overselling. The service uses pessimistic database locks (`SELECT ... FOR UPDATE`) during the reservation phase of checkout.

### Fulfillment Service
* **Role**: Warehouse floor operations coordinator.
* **Capabilities**: Directs pick-pack-ship flows. It generates optimized picking routes based on warehouse layouts and manages packaging material allocation.
* **Storage**: PostgreSQL.
* **Key Challenge**: Minimizing human steps. It coordinates batch picking routines, grouping orders that share close bin coordinates.

### Shipping Service
* **Role**: Logistics courier gateway.
* **Capabilities**: Communicates with external shipping API providers (e.g., GrabExpress, local delivery partners). It calculates live shipping quotes, prints labels, and normalizes carrier tracking webhook updates.
* **Storage**: PostgreSQL for tracking carrier history.
* **Key Challenge**: Standardizing status events from diverse courier webhooks. It normalizes all third-party payloads into standard internal events (`shipping.dispatched`, `shipping.delivered`).

---

## 4. Post-Purchase Customer Experience

Post-purchase services are asynchronous and designed to drive customer retention.

### Return Service
* **Role**: Return Merchandise Authorization (RMA) orchestrator.
* **Capabilities**: Handles returns, coordinates restock checks with the Warehouse Service, and initiates partial or full refunds through the Payment Service.
* **Storage**: PostgreSQL.
* **Key Challenge**: Ensuring proper accounting. It must lock return tickets to prevent double-refund executions.

### Review & Rating Service
* **Role**: Customer feedback engine.
* **Capabilities**: Stores reviews, calculates average ratings per SKU, and runs automated content moderation to filter spam or offensive words.
* **Storage**: MongoDB for review documents, Redis for aggregate rating scores.
* **Key Challenge**: Spam protection. The service runs incoming comments through a moderation pipeline before publishing.

### Loyalty Service
* **Role**: Customer points and tier manager.
* **Capabilities**: Listens for `order.completed` events, updates loyalty points, manages VIP status levels, and issues reward coupons when tiers are reached.
* **Storage**: PostgreSQL.
* **Key Challenge**: Processing events asynchronously without double-counting points in case of message duplicates.

---

## 5. Identity & Access Management

This domain handles the security boundary of the platform.

### Auth Service
* **Role**: Core security controller.
* **Capabilities**: Handles registration, login, multi-factor authentication (MFA), and token generation. It issues RS256-signed JWTs containing role claims.
* **Storage**: PostgreSQL for credentials, Redis for token blocklists and rate-limiting.
* **Key Challenge**: Secure cryptographical signatures. The service rotates signing keys daily without interrupting active client sessions.

### Customer Service
* **Role**: Customer profile store.
* **Capabilities**: Manages customer profile data, shipping addresses, communication preferences, and lifetime value metrics.
* **Storage**: PostgreSQL.
* **Key Challenge**: Privacy compliance (e.g., GDPR right-to-be-forgotten). It must be able to hard-delete customer records while preserving anonymous order ledger records for accounting.

### User Service
* **Role**: Admin and employee account store.
* **Capabilities**: Manages administrative accounts, back-office roles, and tracks audit logs of actions taken in the admin portal.
* **Storage**: PostgreSQL.
* **Key Challenge**: Granular permission validation. It enforces strict Role-Based Access Control (RBAC).

---

## 6. Platform Operations & Shared Services

These are utilities that keep the system running.

### Gateway Service
* **Role**: Single entry point for external traffic.
* **Capabilities**: Route matching, TLS termination, API key verification, dynamic rate-limiting, and circuit breaking.
* **Storage**: Stateless.
* **Key Challenge**: Low latency. It must route requests in less than 5 milliseconds.

### Search Service
* **Role**: Catalog query interface.
* **Capabilities**: Performs full-text search, filtering, and faceted search.
* **Storage**: Elasticsearch.
* **Key Challenge**: Data freshness. It uses Change Data Capture (CDC) to sync Catalog edits to Elasticsearch within 500 milliseconds.

### Notification Service
* **Role**: Communication queue.
* **Capabilities**: Sends transactional emails, SMS, and push notifications via providers like SendGrid or Twilio.
* **Storage**: PostgreSQL for notification history, RabbitMQ for queues.
* **Key Challenge**: Handing third-party API outages without losing notifications.

---

## Cross-Domain Communication via Go Interfaces

To prevent direct coupling, microservices interact via defined gRPC contracts or event-driven messages. Below is the Go interface definition showing how the Checkout service abstracts communication with the Catalog and Warehouse domains.

```go
package checkout

import (
	"context"
	"time"
)

// Product represents a read-only snapshot of a catalog item.
type Product struct {
	SKU       string
	Name      string
	PriceUnit int64 // Price in cents to avoid floating-point issues
	IsActive  bool
}

// ReservationRequest defines the schema to temporarily lock inventory.
type ReservationRequest struct {
	OrderUUID string
	SKU       string
	Quantity  int
	Timeout   time.Duration
}

// ReservationResponse contains the result of the inventory booking.
type ReservationResponse struct {
	ReservationID string
	IsSuccess     bool
	ErrorMessage  string
}

// CatalogClient defines the contract for pulling product data.
type CatalogClient interface {
	GetProductBySKU(ctx context.Context, sku string) (*Product, error)
	ValidateSKUs(ctx context.Context, skus []string) (map[string]*Product, error)
}

// WarehouseClient defines the contract for booking inventory.
type WarehouseClient interface {
	ReserveStock(ctx context.Context, req *ReservationRequest) (*ReservationResponse, error)
	ReleaseStock(ctx context.Context, reservationID string) error
}

// CheckoutOrchestrator coordinates the domain transaction.
type CheckoutOrchestrator struct {
	catalog   CatalogClient
	warehouse WarehouseClient
}

func NewCheckoutOrchestrator(c CatalogClient, w WarehouseClient) *CheckoutOrchestrator {
	return &CheckoutOrchestrator{
		catalog:   c,
		warehouse: w,
	}
}

// ExecuteCheckout verifies details and reserves stock.
func (co *CheckoutOrchestrator) ExecuteCheckout(ctx context.Context, orderID string, sku string, qty int) (bool, error) {
	// 1. Verify product exists and get price
	prod, err := co.catalog.GetProductBySKU(ctx, sku)
	if err != nil || !prod.IsActive {
		return false, err
	}

	// 2. Reserve inventory
	resReq := &ReservationRequest{
		OrderUUID: orderID,
		SKU:       sku,
		Quantity:  qty,
		Timeout:   15 * time.Minute,
	}
	res, err := co.warehouse.ReserveStock(ctx, resReq)
	if err != nil || !res.IsSuccess {
		return false, err
	}

	return true, nil
}
```

---

## Domain Database Isolation

Sharing databases between microservices is a critical architectural anti-pattern. If two services query the same tables, they are functionally coupled, violating the core promise of microservices. 

To demonstrate this isolation, here are the separate SQL schemas for the `orders` database and the `warehouse` database. Notice that the `orders` table only references the `sku` as a string and the `warehouse_id` as an identifier, without any foreign key constraints pointing to the other database.

### Orders Database Schema (`orders_db`)
```sql
-- Schema for Order Service Database
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount INT8 NOT NULL, -- Price in cents
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    unit_price INT8 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

### Warehouse Database Schema (`warehouse_db`)
```sql
-- Schema for Warehouse Inventory Database
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE inventory_stocks (
    id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(id),
    sku VARCHAR(100) NOT NULL,
    allocated_qty INT NOT NULL DEFAULT 0,
    available_qty INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(warehouse_id, sku)
);

CREATE TABLE inventory_reservations (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL,
    warehouse_id INT NOT NULL REFERENCES warehouses(id),
    sku VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    status VARCHAR(50) NOT NULL, -- RESERVED, COMPLETED, RELEASED
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inventory_sku ON inventory_stocks(sku);
CREATE INDEX idx_reservations_expires_at ON inventory_reservations(expires_at) WHERE status = 'RESERVED';
```

By ensuring that the databases are completely separated, each team can modify their schema independently. When a customer places an order, the Checkout Service calls the gRPC client to perform a stock reservation in `warehouse_db` and inserts the order record in `orders_db`. If the reservation fails, the transaction is aborted at the application level. Eventual consistency is maintained via messaging.

---

## FAQ

{{< faq q="How do you define bounded context boundaries when segregating an e-commerce monolith?" >}}
We map domain boundaries using Event Storming to identify business events and their corresponding commands. Each bounded context is defined by a shared, ubiquitous language and strict transactional consistency requirements. For example, Order Placement and Inventory Reservation form separate contexts connected asynchronously via an event broker.
{{< /faq >}}

{{< faq q="What database strategy should be used to maintain isolation between the 21 microservices?" >}}
Each microservice must own its database schema exclusively. Sharing database tables across service boundaries is a strict anti-pattern that creates tight coupling. Services communicate only via public API contracts (gRPC/Protobuf) or asynchronous events (Kafka/RabbitMQ), using schema migration tools like Golang-Migrate independently.
{{< /faq >}}
