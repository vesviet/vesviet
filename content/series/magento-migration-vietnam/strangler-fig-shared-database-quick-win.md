---
title: "Magento Migration: Shared DB, CDC, or Event Bus?"
slug: "strangler-fig-shared-database-quick-win"
description: "Magento database migration decision guide: compare Shared DB, CDC + Debezium, and Event Bus separation with a 16-dimension risk evaluation matrix."
date: "2026-07-18T18:00:00+07:00"
lastmod: "2026-09-08T20:30:00+07:00"
author: "Lê Tuấn Anh"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Magento", "Strangler Fig", "Shared Database", "CDC", "Debezium", "Event Bus", "Kafka", "Outbox Pattern", "Migration", "Architecture", "Golang"]
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/strangler-fig-shared-database-quick-win.jpg"
  alt: "Magento database migration decision: Shared DB vs CDC vs Event Bus — Architecture Comparison"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/strangler-fig-shared-database-quick-win/"
weight: 6
mermaid: true
---

[📖 Bản tiếng Việt (Vietnamese Edition)](https://learn.tanhdev.com/series/magento-migration-vietnam/strangler-fig-shared-database-quick-win/)

---

> **Prerequisite:** Read [Part 5 — Exporting Magento 2 Data: Flatten EAV with SQL & Node](/series/magento-migration-vietnam/exporting-magento-2-data-flat-sql-nodejs/) for data unpivoting fundamentals.

# Magento Database Migration: Shared DB, CDC, or Event Bus?

**Answer-first:** While connecting new microservices directly to the existing Magento database (Shared Database pattern) appears tempting as a quick win, it introduces severe schema coupling, cross-service deadlock hazards, and violates core microservice boundaries. The 2027 production standard uses **Debezium 3.0+ Change Data Capture (CDC)** streaming row changes via **Redpanda/Kafka** into independent domain databases. This decouples schemas, guarantees sub-50ms data synchronization latency, and maintains dual-write integrity via the Transactional Outbox pattern.

When decomposing a monolithic commerce architecture, the database sync strategy dictates whether the migration succeeds smoothly or devolves into a data-corrupting distributed nightmare.

Teams often succumb to the "Shared Database" shortcut: pointing their new Go catalog service directly at Magento's MySQL tables. Within weeks, indexer locks clash with Go connection pools, schema patches break microservice queries, and the team finds itself trapped in the worst of both worlds.

---

## 1. Architectural Topology: Shared DB Antipattern vs CDC Mesh

```mermaid
flowchart TD
    subgraph Antipattern ["1. Shared Database Antipattern (High Risk)"]
        MagentoPHP1["Magento Monolith"] --> MySQL_Shared["Single Shared MySQL Database"]
        GoCatalog1["Go Catalog Service"] --> MySQL_Shared
        GoCart1["Go Cart Service"] --> MySQL_Shared
        MySQL_Shared --> Deadlock["Schema Coupling & Cross-Service Deadlocks"]
    end

    subgraph Recommended_CDC ["2. Debezium 3.0+ CDC Architecture (Production Standard)"]
        MagentoPHP2["Magento Monolith"] --> MySQL_Source["Magento MySQL 8.4 (Binlog Enabled)"]
        MySQL_Source --> Debezium["Debezium 3.0+ CDC Engine"]
        Debezium --> Redpanda["Redpanda / Kafka Event Stream"]
        
        Redpanda --> Worker1["Catalog Sync Worker"]
        Redpanda --> Worker2["Inventory Sync Worker"]
        
        Worker1 --> CatalogDB["Private PostgreSQL Catalog DB"]
        Worker2 --> InventoryDB["Private Redis / PostgreSQL Inventory DB"]
    end
```

---

## 2. Transactional Outbox Pattern for Go Microservices

When Go microservices update domain state, they must emit events to Kafka without risking split-brain discrepancies. The **Transactional Outbox Pattern** ensures that database state changes and event records commit atomically in a single local transaction:

```mermaid
sequenceDiagram
    autonumber
    participant App as "Order Service (Go)"
    participant DB as "PostgreSQL Private DB"
    participant Relay as "Outbox Polling Relay / Debezium"
    participant Kafka as "Redpanda / Kafka Bus"

    App->>DB: BEGIN Transaction
    App->>DB: INSERT INTO orders (...)
    App->>DB: INSERT INTO outbox_events (event_id, payload, status='PENDING')
    App->>DB: COMMIT Transaction
    
    Note over DB: Atomically committed! Zero risk of ghost events.
    Relay->>DB: SELECT * FROM outbox_events WHERE status='PENDING'
    Relay->>Kafka: Publish Event to 'commerce.orders.v1'
    Relay->>DB: UPDATE outbox_events SET status='PUBLISHED' WHERE event_id=...
```

---

## 3. Production Debezium Connector Configuration

The following JSON configuration registers a high-speed Debezium MySQL connector monitoring Magento order and quote changes:

```json
{
  "name": "magento-cdc-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "aurora-mysql.internal.net",
    "database.port": "3306",
    "database.user": "debezium_cdc",
    "database.password": "${env:CDC_PASSWORD}",
    "database.server.id": "184054",
    "topic.prefix": "magento_cdc",
    "table.include.list": "magento2.sales_order,magento2.sales_order_item,magento2.cataloginventory_stock_item",
    "schema.history.internal.kafka.bootstrap.servers": "redpanda.internal.net:9092",
    "schema.history.internal.kafka.topic": "schema-changes.magento",
    "decimal.handling.mode": "double",
    "tombstones.on.delete": "true"
  }
}
```

---

## 4. 16-Dimension Synchronization Strategy Evaluation Matrix

| Evaluation Dimension | Shared Database | Event Bus (App-Level Dual Write) | Debezium CDC Streaming (2027 SOTA) |
| :--- | :--- | :--- | :--- |
| **Initial Implementation Time** | 1–2 Weeks | 4–6 Weeks | 2–3 Weeks |
| **Schema Decoupling** | Zero (Locked to EAV) | Moderate | **Complete Decoupling** |
| **Dual-Write Split-Brain Risk** | N/A (Single DB) | Severe (App crashes mid-write)| **Zero (Log-based capture)** |
| **Impact on Magento Core Code** | Zero | High (Plugins required) | **Zero (Reads MySQL binlog)** |
| **Latency of Data Sync** | Instant | 100ms - 500ms | **Sub-50ms** |
| **Handling of Hard Deletes** | Instant | Often missed | **Automatic Tombstone Events** |
| **Production Rollback Safety** | Poor | Moderate | **High (Bi-directional sync)** |

---

## ❓ Frequently Asked Questions (FAQ)

{{< faq q="Why is the Shared Database pattern considered an antipattern for microservices?" >}}
While connecting a new service directly to the legacy database saves initial ETL setup time, it tightly binds the new service to Magento's complex, un-optimized schema. Any future Magento upgrade or table restructuring will break the microservice. Furthermore, shared connection pools and concurrent table locks will continue degrading overall platform stability.
{{< /faq >}}

{{< faq q="How does Debezium capture changes without impacting Magento's database performance?" >}}
Debezium operates as a non-invasive daemon that tails the MySQL Binary Log (binlog) at the storage engine layer, acting essentially like a standard MySQL replication slave. It executes zero `SELECT` queries against live tables, generating near-zero CPU and memory overhead on the database master.
{{< /faq >}}

{{< faq q="What happens if the Kafka event bus goes down during a heavy traffic spike?" >}}
Because MySQL transaction commits occur independently of Kafka, no user-facing transactions are blocked. Debezium records its exact position in the binlog using byte offsets. Once Kafka recovers, Debezium resumes streaming from the exact checkpoint without dropping a single event, guaranteeing eventual consistency.
{{< /faq >}}

---

🔗 **Next Step:** Proceed to [Part 7 — Laravel vs Golang: When to Add Features in Each?](/series/magento-migration-vietnam/laravel-vs-golang-when-to-add-features/).
