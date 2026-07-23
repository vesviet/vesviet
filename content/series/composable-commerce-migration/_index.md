---
title: "Composable Commerce Migration: Magento 2 → Microservices Golang"
description: "Escape Magento with 21 Go microservices: DDD bounded contexts, Strangler Fig migration, EAV schema extraction, Dapr PubSub, and GitOps with ArgoCD."
date: "2026-04-01T10:00:00+07:00"
lastmod: "2026-06-24T10:00:00+07:00"
draft: false
weight: 145
slug: "composable-commerce-migration"
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Magento", "Microservices", "Golang", "DDD", "Strangler Fig", "Rush Monorepo", "Dapr", "Kratos"]
cover:
  image: "images/posts/ecommerce-composable-cover.png"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/"
---

# Composable Commerce Migration: Magento 2 → Microservices Golang

Is your Magento 2 store costing you **$125,000–$200,000/year** in Enterprise license fees? Are your engineers spending 60% of their sprint chasing PHP compatibility issues and writing hacky module overrides instead of shipping features? Are you hitting the ceiling on flash-sale traffic because you can only scale the entire monolith at once?

Welcome to the definitive playbook for **Composable Commerce Migration** — how to surgically disassemble a Magento 2 monolith into a production-grade microservices platform built on **Go 1.25, Kratos v2, Dapr PubSub, and Rush monorepo**, without losing a single order in transit.

> **About this Series**
>
> This content is distilled from building a real **Composable Commerce Platform** — 21 Go microservices + 2 frontends handling the complete commerce journey: Browse → Search → Cart → Checkout → Pay → Fulfill → Ship → Return — with zero Magento license fees and full data ownership. Every architecture decision in this series is backed by one of our **24 Architecture Decision Records (ADRs)**.

---

## 🎯 Migration Consulting

Is your team planning to exit Magento or evaluating a migration to a composable commerce architecture? Need an Architecture Review of your current platform before committing to a migration strategy?

👉 **[Book a 1:1 Architecture Consultation](/hire/)** with Senior Architect Lê Tuấn Anh — 17+ years building enterprise e-commerce platforms across Vietnam and SEA.

---

## 📚 Core Curriculum

Magento 2's EAV schema, integer primary keys, and PHP module coupling make migration uniquely treacherous. This series gives you the complete 3-phase Strangler Fig playbook with working Go code:

1. **[Part 0: Executive Summary — Why $200K/Year Is a Trap](/posts/ecommerce-architecture-composable-migration/)**
   *The real cost of Magento Enterprise, and why the composable architecture pays for itself in Year 1.*

2. **[Part 1: DDD Bounded Contexts — Decomposing Magento Modules](/posts/ecommerce-architecture-composable-migration/)**
   *How to map Magento's module structure to 21 bounded contexts using Domain-Driven Design — without a Big Bang rewrite.*

3. **[Part 2: Rush Monorepo — Managing 21 Go Services + 2 Frontends](/posts/ecommerce-architecture-composable-migration/)**
   *Why we chose Microsoft Rush over Nx/Turborepo for a mixed Go + Next.js + React monorepo, and how to set it up.*

4. **[Part 3: Golang + Kratos v2 — Microservice Framework Internals](/posts/ecommerce-architecture-composable-migration/)**
   *How Kratos v2 handles transport, dependency injection, and the common library pattern across 21 services.*

5. **[Part 4: gRPC Internal + REST Gateway Architecture](/posts/ecommerce-architecture-composable-migration/)**
   *Service-to-service communication in gRPC, REST exposure via gRPC-Gateway, and the API Gateway routing strategy.*

6. **[Part 5: EAV Schema Migration — Magento's Biggest Trap](/series/composable-commerce-migration/part-5-eav-schema-migration/)**
   *Untangling `catalog_product_entity_varchar`, integer → UUID identity mapping, and the exact SQL extraction queries that work.*

7. **[Part 6: Phase 1 — Strangler Fig: Read-Only Migration + CDC](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)**
   *Deploy read-only Go services behind an API Gateway, implement real-time CDC sync from Magento MySQL, and use feature flags to route traffic with zero risk.*

8. **[Part 7: Phase 2 — Dual-Write: Dapr PubSub + Feature Flags](/series/composable-commerce-migration/part-7-phase2-dual-write/)**
   *Enable write APIs on microservices, implement bidirectional sync via Dapr PubSub + Transactional Outbox, and resolve conflicts with timestamp-wins policy.*

9. **[Part 8: Phase 3 — Full Cutover: Zero Downtime + GitOps](/series/composable-commerce-migration/part-8-phase3-full-cutover/)**
   *Gradual 25/50/75/100% traffic cutover per service, Magento hot-standby for 30-day rollback window, and ArgoCD GitOps deployment.*

10. **[Part 9: Transactional Outbox + Saga Pattern Across Services](/series/composable-commerce-migration/part-9-outbox-saga/)**
    *How the Checkout → Order → Payment → Warehouse saga runs with guaranteed delivery using Transactional Outbox and Dapr PubSub Dead Letter Queue.*

11. **[Part 10: ADR Walkthrough — 24 Architecture Decisions Explained](/series/composable-commerce-migration/part-10-adr-walkthrough/)**
    *Every major decision — Dapr vs Kafka, database-per-service, gRPC vs REST, monorepo vs polyrepo — with the trade-offs that led to each.*

---

## 🆚 What This Platform Replaces

| Capability | Magento Enterprise | This Platform |
|---|---|---|
| **License cost** | $125,000–$200,000/year | $0 |
| **VNPay / MoMo payments** | Third-party plugins, unreliable | Native, circuit breaker, failover |
| **Flash sale scaling** | Scale entire monolith 10× | Scale only Order + Payment 10× |
| **Multi-warehouse WMS** | Enterprise add-on only | Built-in: bin location, batch picking |
| **Event reliability** | Webhooks miss, synchronous hooks | Transactional Outbox + Dapr PubSub + DLQ |
| **Data ownership** | Vendor-hosted | Self-hosted, full control |

---

## 🧭 Where Should You Start?

| Your Profile | Recommended Entry Point | Why |
|---|---|---|
| **PM / BA / CTO** | [Part 0: Executive Summary](https://tanhdev.com/posts/ecommerce-architecture-composable-migration/) | Business case, cost comparison, migration ROI |
| **Backend engineer (Magento)** | [Part 5: EAV Schema Migration](https://tanhdev.com/series/composable-commerce-migration/part-5-eav-schema-migration/) | The technical trap most teams hit first |
| **Golang engineer** | [Part 3: Kratos v2 Internals](https://tanhdev.com/posts/ecommerce-architecture-composable-migration/) | Framework deep-dive with real service code |
| **Architect / Tech Lead** | [Part 1: DDD Bounded Contexts](https://tanhdev.com/posts/ecommerce-architecture-composable-migration/) | Domain decomposition before writing a line of code |
| **DevOps / SRE** | [Part 8: Phase 3 Cutover + GitOps](https://tanhdev.com/series/composable-commerce-migration/part-8-phase3-full-cutover/) | Zero-downtime cutover and ArgoCD deployment model |

---

## Frequently Asked Questions (FAQ)

{{< faq q="Does this series assume I'm already running Magento 2?" >}}
Yes. The migration guides target Magento 2.x (Open Source or Commerce). The EAV schema, integer primary keys, and module coupling patterns are all Magento 2-specific. If you're on Magento 1, the DDD and Golang patterns still apply but the SQL extraction queries will differ.
{{< /faq >}}

{{< faq q="What Golang version and framework does the platform use?" >}}
The Composable Commerce Platform runs on **Go 1.25** with **Kratos v2** (go-kratos), Google's production microservice framework used in Bilibili and other large-scale Go deployments. All 21 services share a `common` library (v1.10.0) that standardizes outbox, idempotency, health checks, and config management.
{{< /faq >}}

{{< faq q="What is Rush and why not use a standard Go workspace or Nx?" >}}
**Microsoft Rush** is a polyglot monorepo manager that handles both Go services and Node.js frontends (Next.js + React) under a single repo with incremental builds, workspace policies, and changeset management. We chose Rush over Nx because of its superior handling of mixed-language repos and its first-class support for PNPM workspaces on the frontend side.
{{< /faq >}}

{{< faq q="Can the migration be done without downtime?" >}}
Yes. The 3-phase Strangler Fig approach (Read-Only → Dual-Write → Cutover) is designed for zero downtime. Phase 1 routes only reads to microservices; writes still go to Magento. Phase 2 introduces dual-write with feature flags for instant rollback in under 10 seconds. Phase 3 gradually shifts traffic 25% → 50% → 75% → 100% per service with Magento on hot standby for a 30-day rollback window.
{{< /faq >}}
