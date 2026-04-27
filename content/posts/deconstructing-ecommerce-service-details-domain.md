---
title: "Deconstructing the Ecosystem: Service Details by Domain"
date: 2026-04-12T08:00:00+07:00
draft: false
tags: ["Domain-Driven Design", "Microservices", "System Design", "Architecture"]
description: "A detailed technical breakdown of how a monolithic e-commerce application is segregated into 6 logical Business Domains with 21 isolated microservices."
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
---

"Why 21 services? Isn't that overkill?" 

This is the most common question I get when discussing the Golang microservice architecture we built to handle massive scale. The short answer is: **No, because Conway's Law is real.** 

When you have multiple squads touching the same codebase, feature overlap creates friction. By rigidly enforcing **Domain-Driven Design (DDD)**, we sliced our e-commerce monolith into 6 highly cohesive, loosely coupled Business Domains. Each domain is completely self-sufficient and owns its own Postgres databases.

Here is the technical breakdown of the 6 core domains and their underlying services.

### 1. The Commerce Flow
This is the transactional heart of the platform. If this domain goes down, money stops flowing.
* **Checkout Service:** The orchestrator. It manages volatile cart states, revalidates catalog pricing in real-time, and initiates the checkout Saga.
* **Order Service:** This service strictly handles the post-checkout lifecycle. It dictates the 8 states of an order (Pending, Confirmed, Paid, Cancelled, etc.) and acts as the central event publisher.
* **Payment Service:** Highly secured. Integrates heavily with external APIs (Stripe, PayPal, VNPay, MoMo). It also runs our custom GeoIP + VPN detection logic for automated fraud scoring.

### 2. Product & Content
A read-heavy domain tailored for extremely low latency.
* **Catalog Service:** The single source of truth for PIM (Product Information Management). It handles complex EAV (Entity-Attribute-Value) structures, nested categories, and brand data.
* **Pricing Service:** Extracts volatile pricing logic away from the Catalog. It manages multi-currency conversions, taxation, and layered overrides (e.g., Warehouse-specific vs. SKU-specific pricing).
* **Promotion Service:** Houses our BOGO logic, tiered discount calculations, and coupon redemption ledgers.

### 3. Logistics
Moving physical bits in the real world.
* **Warehouse Service:** A mini-WMS (Warehouse Management System). It handles multi-warehouse inventory segmentation, bin locators, and tracks idempotent stock-reservation events so overselling is mathematically impossible.
* **Fulfillment Service:** Dictates the internal operational workflow: Picking, Packing, and Hand-off.
* **Shipping Service:** An edge-agent that speaks to physical carriers (Grab, specific couriers) and normalizes webhook tracking updates so internal systems only digest standard payloads.

### 4. Post-Purchase
Where customer retention happens.
* **Return Service:** A frighteningly complex domain that orchestrates restock coordination with the Warehouse, initiates refund gRPC calls to the Payment service, and handles RMA creation.
* **Loyalty Service:** A high-throughput database that ingests 'order completed' events to increment point tiers and orchestrate referral payouts via Transactional Outbox patterns.

### 5. Identity & Access
The gatekeepers. 
* **Auth Service:** Issues stateless RS256 JWTs, handles OAuth2 flows (Google/Github), and manages MFA logic strictly using Redis caching.
* **User Service & Customer Service:** Segregated so internal RBAC tools for employees (User) do not pollute external customer profile data and lifetime-value (LTV) analytics databases (Customer).

### 6. Platform Operations
Shared infrastructure utilities that the other domains lean heavily on.
* **Gateway Service:** The entry point performing API routing, global rate-limiting, and circuit breaking.
* **Search Service:** A CQRS read-model built on Elasticsearch. It consumes Dapr events from the Catalog and Pricing services to build flattened, lightning-fast indexed documents.
* **Analytics & Notification:** Passive observers. They sit at the end of the Dapr queues waiting for system events to either increment business dashboards or fire out SendGrid/Twilio communication to customers.

### The Value of Separation

By looking at the ecosystem through the lens of these 6 domains, 21 services don't seem like chaos—they look like an organized factory line. A bug in the **Review** system can't bring down the **Payment** system. A localized spike during a Flash Sale means we can simply spin up 10 extra pods for the **Order** and **Checkout** services without wasting money scaling the stationary **Catalog** or **Platform** services. This is the true enterprise value of Domain-Driven Design!

{{< author-cta >}}
