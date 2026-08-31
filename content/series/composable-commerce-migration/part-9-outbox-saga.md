---
title: "Part 9: Transactional Outbox & Distributed Sagas in Composable Commerce"
date: 2026-06-05T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Guaranteeing distributed data consistency across Order, Payment, and Inventory microservices using the Transactional Outbox pattern and Orchestrated Sagas."
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
---

[← Previous Chapter: Part 8: Phase 3 — Full Cutover](/series/composable-commerce-migration/part-8-phase3-full-cutover/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 10: ADR Walkthrough — 24 Architecture Decisions →](/series/composable-commerce-migration/part-10-adr-walkthrough/)

---

> **Answer-first:** In a distributed e-commerce architecture without 2-Phase Commit (2PC), distributed consistency is achieved via the **Transactional Outbox Pattern** (saving domain events in the same SQL ACID transaction as business state) and **Orchestrated Sagas** (executing compensating transactions upon payment or inventory failure).

---
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer
    participant Order as Order Service (Saga Orchestrator)
    participant Inventory as Inventory Service
    participant Payment as Payment Service

    Customer->>Order: Create Order
    Order->>Order: Save Order (PENDING) + Outbox Event (Atomic ACID)
    Order->>Inventory: Reserve Stock (gRPC)
    alt Inventory Available
        Inventory-->>Order: Stock Reserved OK
        Order->>Payment: Authorize Payment (gRPC)
        alt Payment Succeeded
            Payment-->>Order: Payment Captured OK
            Order->>Order: Update Order (CONFIRMED)
            Order-->>Customer: Order Placed Successfully!
        else Payment Failed
            Payment-->>Order: Card Declined
            Order->>Inventory: Compensating Tx: Release Reserved Stock
            Order->>Order: Update Order (CANCELLED)
            Order-->>Customer: Payment Failed
        end
    else Out of Stock
        Inventory-->>Order: Insufficient Stock
        Order->>Order: Update Order (CANCELLED)
        Order-->>Customer: Item Out of Stock
    end
```
