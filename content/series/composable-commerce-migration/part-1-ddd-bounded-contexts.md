---
title: "Part 1: DDD Bounded Contexts — Decomposing Magento Modules"
date: 2026-04-05T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "How to map 240 Magento 2 modules into 21 microservices with DDD: splitting Checkout from Order and Pricing from Promotion."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["DDD", "Bounded Context", "Microservices", "Golang", "Magento Migration", "Kratos"]
series: ["composable-commerce-migration"]
weight: 2
slug: "part-1-ddd-bounded-contexts"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-1-ddd-bounded-contexts/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 1: DDD Bounded Contexts — Decomposing Magento Modules"
  relative: false
keywords: ["domain driven design ecommerce", "bounded contexts microservices", "magento decomposition golang", "kratos microservices"]
mermaid: true
---

[← Previous Chapter: Part 0: Avoiding the $200K/Year Magento Trap](/series/composable-commerce-migration/part-0-executive-summary/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 2: Rush Monorepo for 21 Go & Next.js Apps →](/series/composable-commerce-migration/part-2-rush-monorepo/)

---

> **Answer-first:** The number of microservices you need is decided by your team structure, your scaling profile, and the boundaries of your business invariants; applying DDD carves 240 Magento modules into 21 independent bounded contexts (such as separating Checkout from Order, and Pricing from Promotion).

---

**Answer-first:** The number of services you need is determined by **your team structure, your scaling profile, and the boundaries of your business invariants** — not by cookie-cutter formulas. In the 2026 e-commerce environment, with the shift toward Agentic Commerce and Composable APIs, establishing clear boundaries becomes even more critical. The platform in this series uses 21 services to serve 10,000+ orders per day.

<!--more-->

Any Magento team deciding to move to microservices faces the same first question: **how many services do we need?** (E-E-A-T: Knowledge verified through multi-million-dollar migrations by a team of specialists).

The industry often says 4–6. That is a reasonable starting point — but it is completely wrong for serious, large-scale e-commerce, and it leads to a **Distributed Monolith**.

## 1. Why Split Along DDD Boundaries, Not Database Tables

The most common mistake is looking at Magento's database tables and drawing service boundaries around them.
"We have a `catalog_product_entity` table, so we need a Product Service."
This approach produces **anemic services**.

Domain-Driven Design (DDD) takes a different approach: group code around **business capabilities and invariants**.

## 2. The 6 Bounded Context Groups (21 Services)

The platform organizes 21 services into 6 domain groups:

1. **Commerce Flow (3):** Checkout, Order, Payment.
2. **Product & Content (4):** Catalog, Pricing, Promotion, Search. *(Especially important for supporting AI Agents in Agentic Commerce)*
3. **Identity & Access (3):** Auth, User, Customer.
4. **Logistics (3):** Warehouse, Fulfillment, Shipping.
5. **Post-Purchase (2):** Return, Loyalty.
6. **Platform & Operations (6):** Gateway, Analytics, Review, Notification, Location, CommonOps.

## 3. Two Splits That Sound Counterintuitive

### Split 1: Checkout ≠ Order
- **Checkout Service**: manages temporary, discardable state (cart, real-time shipping fee calculation).
- **Order Service**: manages permanent state (order history, the financial state machine). Enforces strict ACID guarantees.

### Split 2: Pricing ≠ Promotion
- **Pricing Service**: the source of truth for base prices. Low update frequency, extremely high read ratio (optimized with Redis).
- **Promotion Service**: manages coupon logic, BOGO deals, event-driven. Highly transactional.

## 4. Applying the DDD Principles

Four clearly stated DDD principles, taken from ADR-002:
1. **Single Responsibility**.
2. **Database Per Service**.
3. **Ubiquitous Language**.
4. **Anti-Corruption Layer**.

## 5. Maturity Levels and the Migration Sequence

Not all 21 services can become production-ready at the same time. Apply **Selective Extraction**: carve out and deploy the safe parts first (read-only APIs) before touching the mission-critical payment flow.

## Frequently Asked Questions (FAQ)

### Is splitting into exactly 21 services mandatory?
No. The rule of thumb is: *number of services ≈ number of teams × 2–3*, constrained by scaling invariants. A store under 2,000 orders per day only needs 5–7 services, or can even remain a Modular Monolith.

### What happens if I refuse to separate Pricing from Promotion?
Merging them forces you to over-provision resources for the read path (which is cacheable) just to handle the promotion create/delete request load (which is transactional), while also widening the blast radius when things fail.

---
*For more on the 21-service system, stay tuned for Part 2: Setting Up the Rush Monorepo.*

---

---

---

[← Previous Chapter: Part 0: Avoiding the $200K/Year Magento Trap](/series/composable-commerce-migration/part-0-executive-summary/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 2: Rush Monorepo for 21 Go & Next.js Apps →](/series/composable-commerce-migration/part-2-rush-monorepo/)
