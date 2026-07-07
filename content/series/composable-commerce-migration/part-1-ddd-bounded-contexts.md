---
title: "Part 1: DDD Bounded Contexts — Magento to 21 Services"
description: "Map Magento 2's 240+ modules to 21 bounded contexts using DDD: Checkout ≠ Order, Pricing ≠ Promotion, and why 21 services is the right number."
date: 2026-04-08T10:00:00+07:00
lastmod: 2026-07-03T15:41:55+07:00
draft: false
weight: 2
slug: "part-1-ddd-bounded-contexts"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["DDD", "Bounded Contexts", "Magento", "Microservices", "Domain-Driven Design", "Golang", "Architecture"]
series: ["Composable Commerce Migration"]
series_order: 1
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/ecommerce-composable-cover.png"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
---

Every Magento team that decides to migrate to microservices faces the same first question: **how many services?**

The industry says 4–6. *"Catalog service, Order service, Customer service, Inventory service, Payment service, and maybe CMS."* Every blog post, every conference talk converges on this list. It's a reasonable starting point — and it's wrong for serious e-commerce at scale.

The Composable Commerce Platform we're documenting in this series has **21 microservices** across 6 bounded context groups. That's 3–4× the industry recommendation. This article explains why — with a complete Magento module → service mapping table, and the two counter-intuitive domain splits that Magento engineers almost always get wrong.

**Answer-first:** The number of services you need is determined by your **team structure, scaling profile, and the boundaries of your business invariants** — not by convention. At 10,000+ SKUs, 20+ warehouses, and 10,000+ orders/day with multiple independent engineering teams, 21 services is correct. The same platform for a 500-order/day shop should have 5–7.

## 1. Why DDD Boundaries, Not Database Tables

The most common decomposition mistake Magento engineers make is to look at Magento's database tables and draw service boundaries around them.

> "We have `catalog_product_entity`, so we need a Product Service."  
> "We have `sales_order`, so we need an Order Service."  
> "We have `customer_entity`, so we need a Customer Service."

This produces **anemic services** — services that are just thin REST wrappers over database tables with no real domain logic. They don't reduce coupling; they just move the coupling from Magento's PHP code to API calls between services.

Domain-Driven Design takes a different approach: group code around **business capabilities and their invariants**, not data structures.

The test is: *"Can this business rule be enforced within a single service's database transaction?"* If yes, the service boundary is correct. If the invariant requires coordination between multiple services, you need a Saga or Domain Event.

For example:
- "An order cannot be placed if the customer's email is unverified" → Order Service must read Customer Service data. This is a **read query**, acceptable via synchronous gRPC call.
- "Stock cannot go negative across multiple warehouses" → Warehouse Service owns all stock. The invariant is *within* one service. Correct boundary.
- "A coupon can only be used once per customer" → Promotion Service owns coupon redemption. The invariant is *within* one service. Correct boundary.

## 2. The 6 Bounded Context Groups

The platform organizes 21 services into 6 domain groups. Here is the complete mapping — including which Magento modules each service replaces:

### 🛒 Group 1: Commerce Flow (3 services)

| Service | HTTP Port | gRPC Port | Replaces Magento Modules |
|---|---|---|---|
| **Checkout Service** | 8004 | 9004 | `Magento_Checkout`, `Magento_Quote` |
| **Order Service** | 8001 | 9001 | `Magento_Sales`, `Magento_SalesSequence` |
| **Payment Service** | 8003 | 9003 | `Magento_Payment`, `Magento_Braintree`, `Magento_Paypal` |

### 📦 Group 2: Product & Content (4 services)

| Service | HTTP Port | gRPC Port | Replaces Magento Modules |
|---|---|---|---|
| **Catalog Service** | 8005 | 9005 | `Magento_Catalog`, `Magento_CatalogImportExport` |
| **Pricing Service** | 8002 | 9002 | `Magento_CatalogRule`, `Magento_CatalogPrice`, `Magento_Tax` |
| **Promotion Service** | 8011 | 9011 | `Magento_SalesRule`, `Magento_Coupon`, `Magento_Reward` (partial) |
| **Search Service** | 8012 | 9012 | `Magento_Search`, `Magento_CatalogSearch`, `Magento_Elasticsearch` |

### 🔐 Group 3: Identity & Access (3 services)

| Service | HTTP Port | gRPC Port | Replaces Magento Modules |
|---|---|---|---|
| **Auth Service** | 8013 | 9013 | `Magento_Authorization`, `Magento_JwtUserToken` |
| **User Service** | 8014 | 9014 | `Magento_User`, `Magento_Backend` (admin users) |
| **Customer Service** | 8006 | 9006 | `Magento_Customer`, `Magento_CustomerBalance` |

### 🚚 Group 4: Logistics (3 services)

| Service | HTTP Port | gRPC Port | Replaces Magento Modules |
|---|---|---|---|
| **Warehouse Service** | 8008 | 9008 | `Magento_InventoryAdminUi`, `Magento_InventoryApi`, `Magento_CatalogInventory` |
| **Fulfillment Service** | 8009 | 9009 | `Magento_InventoryShipping`, `Magento_InventorySourceDeductionApi` |
| **Shipping Service** | 8010 | 9010 | `Magento_Shipping`, `Magento_OfflineShipping`, `Magento_ShippingCore` |

### 🔄 Group 5: Post-Purchase (2 services)

| Service | HTTP Port | gRPC Port | Replaces Magento Modules |
|---|---|---|---|
| **Return Service** | 8015 | 9015 | `Magento_Rma`, `Magento_SalesRuleSample` |
| **Loyalty Service** | 8016 | 9016 | `Magento_Reward`, `Magento_CustomerBalance` (partial) |

### ⚙️ Group 6: Platform & Operations (6 services)

| Service | HTTP Port | gRPC Port | Role |
|---|---|---|---|
| **Gateway Service** | 8000 | 9000 | API Gateway, JWT auth, rate limiting |
| **Analytics Service** | 8017 | 9017 | Purchase events, reporting (no Magento equivalent) |
| **Review Service** | 8018 | 9018 | `Magento_Review`, `Magento_Rating` |
| **Notification Service** | 8019 | 9019 | `Magento_Email`, `Magento_SendFriend` |
| **Location Service** | 8007 | 9007 | Geographic data, address validation |
| **CommonOps** | — | — | Shared ops tooling, not deployed as a service |

## 3. The Two Counter-Intuitive Splits

### Split 1: Checkout ≠ Order

This is the decomposition that Magento engineers resist most strongly. In Magento, `Magento_Checkout` and `Magento_Sales` are technically separate modules — but they share database tables and are deeply coupled. Engineers naturally want to keep "checkout and order" as a single service.

Here's why they must be separate:

**Checkout Service** manages *temporary, expendable state*:
- Shopping cart lifecycle (add item, update qty, apply coupon, get totals)
- Price revalidation at checkout time (preventing stale prices)
- Stock reservation check (soft reserve, not permanent)
- Shipping cost calculation orchestration
- Payment method selection

**Order Service** manages *permanent, critical state*:
- Order lifecycle with 8 states: `PENDING → CONFIRMED → PAYMENT_CAPTURED → PROCESSING → FULFILLMENT_STARTED → SHIPPED → DELIVERED → COMPLETED`
- Order cancellation with compensation events
- Return and refund state machine
- Historical order data (never deleted, audited)

The invariant difference is decisive: **Checkout can lose state without business consequence** (an abandoned cart is fine). **Order cannot lose state under any circumstances** (a lost order is revenue lost and a customer complaint).

This separation enables independent scaling: during a flash sale, Order processing spikes *after* checkout completes. With separate services, you scale Order pods from 3 → 30 without touching Checkout pods. With a combined service, you scale everything.

### Split 2: Pricing ≠ Promotion

Most architecture guides (and most SERP results) merge these into a single "Pricing & Promotions" service. The Composable Commerce Platform keeps them separate because they have fundamentally different characteristics:

**Pricing Service:**
- Source of truth for *base prices* — what a product costs before any discount
- Handles: base price, tiered pricing (B2B), multi-currency, tax calculation
- Update frequency: low (product prices change infrequently)
- Scaling profile: **extremely high read rate** (every catalog page call hits pricing)
- Technology optimization: Redis cache with write-through, TTL = 1 hour

**Promotion Service:**
- Applies *discount rules* — reducing prices, not defining them
- Handles: coupon codes, BOGO rules, cart-level discounts, loyalty point redemptions
- Update frequency: high (promotions created/expired constantly)
- Scaling profile: **event-driven** — consumes `order.cancelled` events to reverse redemptions
- Technology optimization: PostgreSQL for transactional coupon redemption tracking

The ADR-021 documents this explicitly: *"Pricing Service owns the price; Warehouse Service owns the stock level; Promotion Service owns the discount application logic."* When ownership is clear, there are no distributed transaction problems for simple read operations.

## 4. DDD Principles Applied

Four explicit DDD principles from [ADR-002](/series/composable-commerce-migration/part-10-adr-walkthrough/):

**1. Single Responsibility**: Each service owns exactly one business domain. Order Service = order lifecycle only. Payment Service = payment transactions only. No service is a general-purpose utility.

**2. Database Per Service** ([ADR-004](/series/composable-commerce-migration/part-10-adr-walkthrough/#adr-004-database-per-service)): No direct database access between services. Enforced at the infrastructure level — each service has its own PostgreSQL instance. Cross-service data access is exclusively via gRPC (synchronous) or Dapr PubSub events (asynchronous).

**3. Ubiquitous Language**: Each domain uses consistent terminology. Warehouse Service uses *"stock allocation"* and *"bin location"*. Order Service uses *"reservation"* and *"fulfillment request"*. These terms don't bleed across service boundaries.

**4. Anti-Corruption Layer**: The Gateway Service (port 8000) protects all microservices from external client schema changes. Frontend teams work against the Gateway's REST API contract; internal service contracts evolve independently.

## 5. Why 21 Services Is Right at This Scale

ADR-002 explicitly justifies the service count against four business requirements:

| Requirement | Implication |
|---|---|
| 10,000+ SKUs with dynamic EAV attributes | Catalog + Pricing must be separated from Checkout (read profile vs write profile) |
| 20+ warehouses with bin-level tracking | Warehouse cannot be part of Catalog (inventory ownership is separate business domain) |
| 10,000+ orders/day with independent payment gateways | Order, Payment, and Checkout must scale independently |
| Multiple engineering teams working in parallel | Service count ≈ team count × 2–3 (Conway's Law) |

ADR-002 also acknowledges the risk: *"Service Explosion: Mitigated by clear domain boundaries and DDD principles."* For teams smaller than 20 engineers or platforms processing fewer than 2,000 orders/day, a 5–7 service decomposition is more appropriate.

## 6. Cross-Domain Communication Matrix

| From | To | Protocol | When |
|---|---|---|---|
| Checkout | Order, Payment, Pricing, Shipping | gRPC (sync) | Real-time checkout flow |
| Order | Warehouse, Fulfillment, Customer | Dapr events (async) | Post-order processing |
| Warehouse | Fulfillment | Dapr events (async) | Stock allocation triggers |
| Payment | External gateways (VNPay, MoMo) | REST (sync) | Payment processing |
| Catalog | Search | Dapr events (async) | Search index sync |
| Promotion | Order, Customer | Dapr events (async) | Redemption reversal on cancellation |

The pattern: **synchronous gRPC for real-time user-facing flows, asynchronous events for post-transaction processing**.

## 7. Service Maturity at Migration Start

Not all 21 services are production-ready simultaneously. The migration playbook in Part 6 uses service maturity as a proxy for migration sequencing:

**🟢 Production-ready first** (migrate in Phase 1 and 2):
Auth, Customer, Catalog, Pricing, Gateway, Search, Location

**🟡 Near-production** (migrate in Phase 2 and 3):
Order, Payment, Warehouse, Shipping, Return, Loyalty

**🔵 Parallel development** (complete during migration, deploy in Phase 3):
Promotion, Fulfillment, Analytics, Review, Notification

Starting Strangler Fig with production-ready services reduces risk: if the migration approach fails, you've exposed it on lower-stakes domains first (catalog browsing) before it reaches Order creation.

## What's Next

You now have the domain map: 21 services, 6 groups, clear ownership boundaries, and the rationale for the two counter-intuitive splits.

The next question is tooling: how do you manage 21 Go services + 2 React frontends in a single repository, maintain consistent dependency versions, and run incremental builds in CI? That's [Part 2: Rush Monorepo Setup](/series/composable-commerce-migration/part-2-rush-monorepo/).

Or, if you want to go straight to the implementation layer: [Part 3: Kratos v2 Internals](/series/composable-commerce-migration/part-3-golang-kratos/) shows exactly what a single Go microservice looks like from `main.go` to database query.

---

## FAQ


{{< faq q="Do I need exactly 21 services for a Magento-to-microservices migration?" >}}
No. 21 services is the right number for a platform processing 10,000+ orders/day with multiple independent engineering teams. For a shop with fewer than 2,000 orders/day and a team under 10 engineers, 5–7 services is more appropriate. The principle is: service count ≈ team count × 2–3, bounded by your actual scaling invariants.
{{< /faq >}}

{{< faq q="Why must Checkout and Order be separate services?" >}}
Checkout manages temporary, expendable state (shopping cart). Order manages permanent, audited financial state. They have opposite failure tolerance: an abandoned cart is acceptable; a lost order is a revenue loss. Separating them also enables independent scaling — during flash sales, Order pods scale 10× while Checkout pods stay constant.
{{< /faq >}}

{{< faq q="What happens if I don't separate Pricing from Promotion?" >}}
Merging them creates a single service with two incompatible scaling profiles: Pricing reads happen on every catalog page (extremely high read rate, cache-friendly), while Promotion applies discount rules with transactional coupon deduplication (event-driven, write-heavy). A combined service forces you to over-provision resources for the lower-traffic workload and creates a tighter blast radius when either component fails.
{{< /faq >}}

{{< faq q="How do I validate my bounded context boundaries before writing code?" >}}
Apply the transaction test: *"Can this business rule be enforced within a single service's database transaction?"* If yes, the boundary is correct. If the rule requires coordinating two services, you need a Saga or a read query — and that coordination cost is the price you pay for keeping those services separate.

---

*This series documents a real production platform. Every service port, every ADR reference, and every domain boundary in this article reflects the actual implementation — not a theoretical exercise.*

*For a comparison of how a regional super-app decomposed similar domains at 100× the order volume, see the [Shopee Architecture Series](/series/shopee-architecture/) — particularly useful when deciding whether your service count should scale with transaction volume or team topology.*

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? â†’ [Book a 1:1 Architecture Consultation](/hire/)*
{{< /faq >}}
