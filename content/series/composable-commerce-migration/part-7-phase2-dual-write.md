---
title: "Part 7: Phase 2 — Dual-Write: CDC & Kafka Synchronization"
date: 2026-05-20T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Implementing Change Data Capture (CDC) with Debezium and Apache Kafka to synchronize mutations between legacy Magento MySQL and new PostgreSQL microservices."
categories: ["Series", "Software Engineering", "Data Architecture"]
tags: ["Debezium", "CDC", "Kafka", "Dual Write", "Data Synchronization", "MySQL", "PostgreSQL"]
series: ["composable-commerce-migration"]
weight: 8
slug: "part-7-phase2-dual-write"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-7-phase2-dual-write/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 7: Phase 2 — Dual-Write: CDC & Kafka Synchronization"
  relative: false
keywords: ["change data capture debezium", "kafka dual write ecommerce", "data reconciliation microservices", "zero data loss migration"]
---

[← Previous Chapter: Part 6: Phase 1 — Strangler Fig](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 8: Phase 3 — Full Cutover →](/series/composable-commerce-migration/part-8-phase3-full-cutover/)

---

> **Answer-first:** Dual-writing at the application layer creates race conditions and split-brain states. Instead, Phase 2 implements **Change Data Capture (CDC)** via Debezium reading the MySQL binlog directly, streaming event deltas through Apache Kafka to populate PostgreSQL microservice databases asynchronously.

---
```mermaid
flowchart LR
    MagentoAdmin["Magento Admin Update"] --> MySQL["Magento MySQL"]
    MySQL -->|"Binlog Stream"| Debezium["Debezium CDC Connector"]
    Debezium -->|"JSON Event Deltas"| Kafka["Kafka Topic: magento.catalog.products"]
    Kafka -->|"Consumer Group"| GoSync["Go Catalog Sync Worker"]
    GoSync -->|"Upsert JSONB"| Postgres["Target PostgreSQL"]
```
