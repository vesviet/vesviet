---
title: "Composable E-Commerce Migration: Overcoming Tech Debt"
slug: "ecommerce-architecture-composable-migration"
author: "Lê Tuấn Anh"
date: "2026-07-06T00:00:00+07:00"
lastmod: "2026-09-08T20:30:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
mermaid: true
description: "Composable commerce migration lessons: Strangler Fig via Envoy, Debezium CDC double-write, Redis BFF locking, Rush monorepo, and Kratos Go architecture."
categories: ["Architecture", "E-Commerce", "Engineering"]
tags: ["Composable Commerce", "MACH", "Magento", "Microservices", "Debezium", "Kafka", "Migration", "Golang", "Kratos"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/ecommerce-composable-cover.jpg"
  alt: "E-commerce composable architecture migration: from Magento monolith to MACH modular services"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/ecommerce-architecture-composable-migration/"
weight: 3
---

[📖 Bản tiếng Việt (Vietnamese Edition)](https://learn.tanhdev.com/series/magento-migration-vietnam/ecommerce-architecture-composable-migration/)

---

> **Prerequisite:** Read [Part 2 — Migrating Magento to Microservices: When & Why](/series/magento-migration-vietnam/why-migrate-magento-to-microservices/) to understand monolithic database bottlenecks.

# Composable E-Commerce Migration: Overcoming Tech Debt with MACH Architecture

**Answer-first:** Composable MACH architecture decomposes monolithic e-commerce platforms into modular, independently scalable services across three primary functional tiers: **Core Transactional Domains** (Catalog, Pricing, Cart, Checkout, Order), **Supporting Engagement Domains** (Customer, Reviews, Wishlist, Promotions), and **Generic Utility Domains** (Notifications, Audit, Search, Analytics). Implementing strict Domain-Driven Design (DDD) bounded contexts with gRPC Protobuf contracts eliminates monolithic coupling, elevates deployment velocity by 4x, and bounds P99 API response times below 45ms.

Decomposing a 500-table Magento database cannot be accomplished by randomly carving out PHP modules. Without rigorous **Domain-Driven Design (DDD)** bounded contexts, teams accidentally build a "distributed monolith" — retaining all the complexity of network calls with none of the benefits of decoupled scalability.

---

## 1. The 21-Service Domain Architecture Topology

A production-grade composable e-commerce platform partitions commerce capabilities across specialized domain clusters:

```mermaid
flowchart TD
    subgraph Ingress_Layer ["Edge Gateway & Ingress Layer"]
        WebStore["Headless Next.js Storefront"]
        MobileApp["Mobile App (Flutter)"]
        EnvoyIngress["Envoy Edge Gateway & W3C Tracing"]
    end

    WebStore --> EnvoyIngress
    MobileApp --> EnvoyIngress

    subgraph Core_Domains ["1. Core Transactional Domains (Go / gRPC)"]
        Catalog["Catalog Service (LanceDB + Flat Cache)"]
        Pricing["Dynamic Pricing Engine (Redis Cache)"]
        Cart["Cart & Session Service (Redis Cluster)"]
        Inventory["Inventory Reservation (Distributed Lock)"]
        Checkout["Checkout Orchestrator (Saga Coordinator)"]
        Order["Order Management Service (PostgreSQL 16)"]
    end

    subgraph Supporting_Domains ["2. Supporting Domains (Go / Laravel 12)"]
        Customer["Customer Identity & RBAC Service"]
        Promotions["Coupon & Tier Rule Engine"]
        Fulfillment["Shipping & Warehouse Integration"]
        Payment["Payment Gateway Orchestrator"]
    end

    subgraph Data_Sync_Backbone ["3. Event-Driven Backbone"]
        Kafka["Redpanda / Kafka Event Stream"]
        Debezium["Debezium 3.0+ CDC Sync"]
        MagentoLegacy["Magento 2.4.9 Monolith (Hot Standby)"]
    end

    EnvoyIngress --> Core_Domains
    EnvoyIngress --> Supporting_Domains
    Core_Domains --> Kafka
    Supporting_Domains --> Kafka
    MagentoLegacy --> Debezium
    Debezium --> Kafka
```

---

## 2. Bounded Context Domain Matrix

To prevent leaky abstractions, every service maintains its own isolated database schema:

| Domain Category | Microservice Name | Primary Storage | Responsibilities & Boundaries |
| :--- | :--- | :--- | :--- |
| **Core** | **Catalog Service** | LanceDB + PostgreSQL | Product master, categories, variants, visual search embeddings |
| **Core** | **Pricing Engine** | Redis + Memory Table | Customer-specific tier pricing, B2B volume rules, VAT calculation |
| **Core** | **Cart Service** | Redis Cluster | High-speed anonymous session cart, quote item persistence |
| **Core** | **Inventory Service** | PostgreSQL + Redlock | Multi-warehouse stock tracking, optimistic stock reservations |
| **Core** | **Checkout Orchestrator**| Stateless (Go) | Step-by-step Saga coordinator, payment-to-order transition |
| **Core** | **Order Service** | PostgreSQL 16 Partitioned | Immutable order lifecycle, invoices, credit memos, fulfillment status |
| **Supporting** | **Customer Service** | PostgreSQL | User profiles, addresses, company account hierarchies, JWT auth |
| **Generic** | **Notification Service** | RabbitMQ / NATS | Asynchronous email, SMS, and webhook delivery |

---

## 3. Production gRPC Protocol Contract: Catalog & Pricing

Instead of brittle REST payloads, domain services communicate over binary **gRPC Protobuf v2** contracts:

```protobuf
syntax = "proto3";

package commerce.catalog.v1;
option go_package = "github.com/vesviet/commerce/catalog/v1;catalogv1";

service CatalogService {
  rpc GetProductBySKU (GetProductRequest) returns (ProductResponse);
  rpc BatchGetPrices (BatchPriceRequest) returns (BatchPriceResponse);
}

message GetProductRequest {
  string sku = 1;
  string customer_group_id = 2;
  string currency_code = 3;
}

message ProductResponse {
  string product_id = 1;
  string sku = 2;
  string name = 3;
  int64 base_price_cents = 4;
  int64 final_price_cents = 5;
  int32 available_stock = 6;
  repeated string categories = 7;
  map<string, string> custom_attributes = 8;
}

message BatchPriceRequest {
  repeated string skus = 1;
  string customer_tier_id = 2;
}

message BatchPriceResponse {
  map<string, int64> prices_cents = 1;
}
```

---

## 4. Envoy Gateway Routing Mesh for Incremental Migration

```mermaid
flowchart LR
    Client["Client Request"] --> Envoy["Envoy Gateway 1.30+"]
    
    Envoy --> RoutePath{"Match Request Path"}
    RoutePath -->|"/api/v1/catalog/*"| GoCatalog["Go Catalog Service (Pod Pool)"]
    RoutePath -->|"/api/v1/cart/*"| GoCart["Go Cart Service (Pod Pool)"]
    RoutePath -->|"/api/v1/checkout/*"| GoCheckout["Go Checkout Service"]
    RoutePath -->|"Default Fallback (/admin, /checkout/onepage)"| MagentoMonolith["Magento Monolith (PHP-FPM)"]

    style GoCatalog fill:#d5f5e3,stroke:#27ae60,stroke-width:2px
    style GoCart fill:#d5f5e3,stroke:#27ae60,stroke-width:2px
    style GoCheckout fill:#d5f5e3,stroke:#27ae60,stroke-width:2px
    style MagentoMonolith fill:#fadbd8,stroke:#e74c3c,stroke-width:2px
```

---

## ❓ Frequently Asked Questions (FAQ)

{{< faq q="How do bounded contexts prevent the microservices architecture from devolving into a distributed monolith?" >}}
Bounded contexts enforce strict domain ownership: no microservice is ever permitted to read or write directly to another service's private database. All cross-domain collaboration occurs strictly via versioned gRPC protocol contracts or asynchronous Kafka events, eliminating hidden relational foreign key dependencies.
{{< /faq >}}

{{< faq q="How does comsuming gRPC compare to GraphQL or REST in an e-commerce microservices mesh?" >}}
Internal service-to-service communication over gRPC Protobuf executes 7x to 10x faster than REST/JSON, consuming up to 80% less network bandwidth due to binary serialization and HTTP/2 multiplexing. While GraphQL remains valuable for frontend BFF (Backend-For-Frontend) aggregation, gRPC is the gold standard for backend microservice fabrics.
{{< /faq >}}

{{< faq q="What happens to complex B2B pricing rules when moving away from Magento?" >}}
In Magento, complex pricing rules rely on heavy SQL joins against `catalogrule_product_price`. In the composable Go architecture, pricing logic is isolated into a dedicated Pricing Engine microservice that evaluates customer group rules and volume discount matrices entirely in RAM using pre-computed Redis hash structures, returning calculated prices in under 5ms.
{{< /faq >}}

---

🔗 **Next Step:** Continue to [Part 4 — Why Migrate Magento to Microservices: Zero-Downtime Guide](/series/magento-migration-vietnam/moving-from-magento-to-microservices/).
