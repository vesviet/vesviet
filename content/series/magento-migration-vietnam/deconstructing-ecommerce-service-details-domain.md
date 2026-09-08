---
title: "Deconstructing the Ecosystem: Service Details by Domain"
slug: "deconstructing-ecommerce-service-details-domain"
author: "Lê Tuấn Anh"
date: "2026-04-12T08:00:00+07:00"
lastmod: "2026-09-08T20:30:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Domain-Driven Design", "Microservices", "Architecture", "Golang", "gRPC", "Protobuf"]
description: "Detailed domain deconstruction: 8 core commerce microservices specifications, database isolation boundaries, and asynchronous event contracts."
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
---

[📖 Bản tiếng Việt (Vietnamese Edition)](https://learn.tanhdev.com/series/magento-migration-vietnam/deconstructing-ecommerce-service-details-domain/)

---

> **Prerequisite:** Read [Part 10 — Magento Enterprise Project Scoping](/series/magento-migration-vietnam/magento-development-in-vietnam/) for domain effort allocations.

# Deconstructing the Ecosystem: Service Details by Domain

**Answer-first:** Deconstructing Magento's monolithic data model into high-performance Go microservices requires establishing strict Domain-Driven Design (DDD) bounded contexts across eight core commerce domains: **Catalog & Search**, **Dynamic Pricing**, **Cart & Session**, **Inventory Reservation**, **Checkout Orchestrator**, **Order Management**, **Customer & Identity**, and **Fulfillment Integration**. Enforcing strict database-per-service isolation with gRPC Protobuf synchronous APIs and Kafka asynchronous events eliminates inter-service lock contention and guarantees sub-35ms P99 query latency.

In a monolithic architecture, boundaries between data domains are soft and easily violated. Magento code routinely joins customer tables, inventory tables, and order tables in a single SQL query.

When migrating to distributed microservices, this relational entanglement must be severed. Each domain service becomes the sole authority over its data store.

---

## 1. Core Commerce Domain Decomposition Map

```mermaid
flowchart TD
    subgraph Client_Interaction ["Client Ingress Layer"]
        BFF["GraphQL / Envoy Gateway BFF Layer"]
    end

    subgraph Domain_Services ["Decoupled Microservice Domains"]
        BFF --> Catalog["1. Catalog Service (LanceDB / PG)"]
        BFF --> Pricing["2. Pricing Engine (Redis In-Memory)"]
        BFF --> Cart["3. Cart Service (Redis Cluster)"]
        BFF --> Inventory["4. Inventory Service (Redlock + PG)"]
        BFF --> Checkout["5. Checkout Orchestrator (Saga Engine)"]
        BFF --> Order["6. Order Service (PostgreSQL 16)"]
        BFF --> Customer["7. Customer Service (PostgreSQL)"]
        BFF --> Fulfillment["8. Fulfillment Service (Kafka Sync)"]
    end

    subgraph Event_Mesh ["Kafka Asynchronous Event Backbone"]
        Catalog -.->|"catalog.product.updated"| Kafka["Redpanda / Kafka Cluster"]
        Inventory -.->|"inventory.stock.reserved"| Kafka
        Order -.->|"order.created.v1"| Kafka
        Order -.->|"order.cancelled.v1"| Kafka
        Kafka -.-> Fulfillment
        Kafka -.-> Pricing
    end
```

---

## 2. Granular Domain Specifications & Data Ownership

| Domain Service | Primary Storage | Synchronous Inbound API | Emitted Asynchronous Events | Internal State Managed |
| :--- | :--- | :--- | :--- | :--- |
| **Catalog Service** | LanceDB + PostgreSQL | gRPC `GetProduct`, `SearchCatalog` | `catalog.product.created` | Flat SKU attributes, categories, media, embeddings |
| **Pricing Engine** | Redis Hash + RAM | gRPC `CalculateCartPrice` | None (Consumer of rules) | Customer group rules, tier discounts, VAT tables |
| **Cart Service** | Redis Cluster | gRPC `AddToCart`, `GetCart` | `cart.abandoned.detected` | Ephemeral user sessions, items, applied coupons |
| **Inventory Service** | PostgreSQL + Redlock | gRPC `ReserveStock`, `ReleaseStock`| `inventory.stock.depleted` | Warehouse stock levels, active temporary reservations |
| **Checkout Orchestrator**| Stateless (Go) | REST `POST /v1/checkout/submit`| None (Drives Saga workflow) | Transient saga state machines, payment tokens |
| **Order Service** | PostgreSQL 16 | gRPC `CreateOrder`, `GetOrder` | `order.confirmed.v1` | Immutable orders, shipments, invoices, line items |
| **Customer Service** | PostgreSQL | gRPC `Authenticate`, `GetProfile`| `customer.registered.v1` | Passwords (Argon2id), address books, company trees |
| **Fulfillment Service**| PostgreSQL | gRPC `DispatchShipment` | `fulfillment.package.shipped`| 3PL warehouse tracking numbers, courier dispatches |

---

## 3. Production gRPC Protocol Schema: Inventory Reservation

The following Protobuf contract enforces strict distributed inventory locking with automatic expiration TTLs to prevent overselling during flash sales:

```protobuf
syntax = "proto3";

package commerce.inventory.v1;
option go_package = "github.com/vesviet/commerce/inventory/v1;inventoryv1";

service InventoryService {
  rpc ReserveStock (ReserveStockRequest) returns (ReserveStockResponse);
  rpc ReleaseStock (ReleaseStockRequest) returns (ReleaseStockResponse);
  rpc CommitStock (CommitStockRequest) returns (CommitStockResponse);
}

message ReserveStockRequest {
  string order_id = 1;
  repeated StockItem items = 2;
  int64 ttl_seconds = 3; // Lock expiration (e.g. 900s for checkout)
}

message StockItem {
  string sku = 1;
  int32 quantity = 2;
  string warehouse_id = 3;
}

message ReserveStockResponse {
  bool success = 1;
  string reservation_id = 2;
  repeated string out_of_stock_skus = 3;
}

message ReleaseStockRequest {
  string reservation_id = 1;
}

message ReleaseStockResponse {
  bool released = 1;
}

message CommitStockRequest {
  string reservation_id = 1;
  string order_id = 2;
}

message CommitStockResponse {
  bool committed = 1;
}
```

---

---

## 3. High-Concurrency Checkout gRPC Sequence

The sequence diagram below illustrates how decomposed domain microservices communicate via non-blocking gRPC during an order placement transaction:

```mermaid
sequenceDiagram
    autonumber
    participant Gateway as Envoy API Gateway / BFF
    participant Cart as Cart Service (Go)
    participant Pricing as Pricing Engine
    participant Inventory as Inventory Service (Go)
    participant Payment as Payment Gateway Service
    participant Order as Order Service (PostgreSQL)
    participant Kafka as Apache Kafka Event Bus

    Gateway->>Cart: ValidateCart(CartID)
    Cart-->>Gateway: CartItems & CustomerID
    Gateway->>Pricing: CalculateTotal(CartItems, CustomerTier)
    Pricing-->>Gateway: FinalTaxAndDiscounts
    Gateway->>Inventory: ReserveStock(ReservationID, Items)
    Inventory-->>Gateway: StockReserved (TTL 15m)
    Gateway->>Payment: AuthorizePayment(Amount, Token)
    Payment-->>Gateway: PaymentAuthorized
    Gateway->>Order: CreateOrder(OrderPayload)
    Order->>Kafka: Publish OrderCreatedEvent (Transactional Outbox)
    Order-->>Gateway: OrderConfirmation (OrderID)
```

## 4. Cross-Domain Communication Rules

To maintain high throughput and resilience, inter-service interactions adhere to strict protocol invariants:
1. **Zero Database Cross-Querying**: No service possesses credentials to access another service's private database.
2. **Command vs Query Segregation (CQRS)**: Heavy read paths (Product Listing Pages) read directly from read-optimized LanceDB and Redis caches, bypassing transactional SQL tables.
3. **Idempotent Event Consumers**: All asynchronous Kafka consumers track event UUIDs in Redis with a 24-hour deduplication window, ensuring duplicate delivery causes zero data corruption.

---

## ❓ Frequently Asked Questions (FAQ)

{{< faq q="How is inventory prevented from overselling when high concurrency traffic hits the Inventory Service?" >}}
The Inventory Service combines PostgreSQL row versioning with distributed locks implemented in Redis using Redlock. When a customer begins checkout, stock is decremented in memory with a 15-minute expiration lease (TTL). If payment fails or the session times out, the lease expires and stock is returned automatically without database deadlocks.
{{< /faq >}}

{{< faq q="Where do customer addresses live in this decomposed architecture?" >}}
Customer addresses reside strictly inside the Customer & Identity Service. During checkout, the Checkout Orchestrator fetches the verified address via gRPC and creates an immutable snapshot of that address inside the Order Management Service, ensuring that future customer profile edits never alter historical order records.
{{< /faq >}}

{{< faq q="How do we handle order reporting and analytics without running SQL joins across all microservice databases?" >}}
Rather than executing cross-database joins in production, all domain services stream their state change events (`order.created`, `inventory.adjusted`, `customer.updated`) to Kafka. A dedicated Analytics Ingestion Worker consumes these streams and loads denormalized analytical tables into ClickHouse or an Apache Iceberg lakehouse for high-speed reporting.
{{< /faq >}}

---

🔗 **Next Step:** Continue to [Part 12 — Go Engineers in Vietnam: Vetting for Magento Migration](/series/magento-migration-vietnam/go-engineers-vietnam-migration-vetting/).
