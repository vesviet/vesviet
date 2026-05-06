---
title: "Part 4 — Amazon CONDOR & Anticipatory Shipping"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "A deep dive into Amazon's legendary fulfillment systems: CONDOR (continuous 6-hour re-optimization) and Anticipatory Shipping (shipping before you click buy)."
weight: 5
---

## Amazon Fulfillment: The Three Tiers of Optimization

Amazon processes **billions of orders annually** through a network of over **175 fulfillment centers** globally. To maintain their 1-2 day (or same-day) delivery guarantees, they built a 3-tier optimization architecture:

```text
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: ANTICIPATORY SHIPPING (Long-term — weeks/months)  │
│  → ML predicts demand → Moves inventory close to customers │
│     BEFORE they place an order                             │
├─────────────────────────────────────────────────────────────┤
│  TIER 2: REGIONALIZATION (Medium-term — days/weeks)        │
│  → Partitions the fulfillment network into autonomous zones│
│  → Ensures 70-80% of orders are fulfilled intra-region     │
├─────────────────────────────────────────────────────────────┤
│  TIER 3: CONDOR (Short-term — hours)                       │
│  → Continuously re-optimizes the fulfillment plan within   │
│     a 5-6 hour window before pick-and-pack begins.         │
└─────────────────────────────────────────────────────────────┘
```

---

## Anticipatory Shipping — Shipping Before You Buy

### A Crazy but Effective Idea

Amazon holds a patent (US Patent 8,615,473) describing a system that **begins shipping items BEFORE a customer places an order**. It sounds like science fiction, but it's a reality.

```text
Traditional Model:
  Customer orders → Warehouse processes → Ships → Delivered (2-5 days)

Anticipatory Shipping:
  ML predicts: "Customers in Region X will buy 200 iPhone 16s in the next 3 days"
  → Amazon ships 200 iPhones from a central hub to local delivery hubs in Region X
  → Customer places order → The item is already locally staged → Delivered same-day!
```

### ML Model Input Features

| Input Feature | Significance |
|---|---|
| Purchase history | What do they buy, and how often? |
| Browsing behavior | What are they looking at? Cart abandonment? |
| Wishlists | Explicitly desired items |
| Seasonal patterns | Winter coats in November, sunscreen in June |
| Regional demographics | High-income areas? Young families? College towns? |
| Trending products | Items going viral on social media |
| Weather forecast | Rain forecasted → move umbrellas to local hubs |
| Events calendar | Black Friday, Prime Day, major sports events |

### Late-Select Addressing — The Key Technique

```text
The Anticipatory Flow:

1. ML Model: "Zip code 10001 (NY) has an 87% probability of ordering 200 cases of water in the next 3 days."

2. System: Ships 200 cases from the Midwest Central Hub → NY Local Hub.
   These packages DO NOT HAVE A SPECIFIC CUSTOMER ADDRESS YET → They are just labeled "Destination: NY Hub".

3. Customer A in NY orders 2 cases of water:
   → The system assigns an address to 2 of the pre-staged cases at the NY Hub.
   → Delivered in 2 hours!

4. If predictions are slightly off (e.g., 50 cases remain unsold):
   → Amazon might run a targeted flash sale for that zip code.
   → Or re-route them back to the central hub.
```

---

## CONDOR — Customer Order and Network Density OptimizeR

### The Problem CONDOR Solves

When you place an order, Amazon doesn't process it immediately. There is a **5-6 hour window** between the order being placed and the warehouse actually starting the pick-and-pack process. CONDOR exploits this window to optimize delivery routes.

```text
17:00 — Order A is placed in Zone 1
  → CONDOR Plan v1: Ship from WH Alpha, individual truck.

17:15 — Order B is placed in Zone 1 (near Order A)
  → CONDOR Plan v2: Consolidate A+B onto the same route → saves 1 truck trip.

17:30 — Order C is placed in Zone 2 (along the same route)
  → CONDOR Plan v3: Consolidate A+B+C → highly dense, efficient route.

17:45 — Order D is placed in Zone 9 (opposite direction)
  → CONDOR Plan v4: Route 1 (A+B+C) + Route 2 (D only).

→ Every 15 minutes, CONDOR re-evaluates the entire network to find better plans.
→ Deadline: When the window closes (e.g., 23:00), the warehouse executes the final optimized plan.
```

### The CONDOR Algorithm

CONDOR solves a variation of the **Prize Collecting Vehicle Routing Problem (PCVRP)**, which is vastly more complex than standard VRP:

```text
PCVRP:
  Maximize: Total "prize" (value of orders delivered on time)
  Minimize: Total transportation cost
  Subject to:
    - Capacity constraints (vehicle limits)
    - Time windows (delivery SLAs)
    - Fleet size limits
    - Network density bonuses: bundling orders in the same neighborhood significantly reduces cost-per-package.

Solving Techniques:
  1. Mathematical optimization (LP/MIP relaxation)
  2. Local search heuristics (2-opt, 3-opt swaps between routes)
  3. Iterative re-optimization (running the solver continuously as new data arrives)
```

### The Major Breakthrough

Amazon has stated that CONDOR reduces the number of feasible routing decisions for a given area from **millions** to **under 10 viable options**, transforming an NP-hard problem into something solvable in near real-time.

---

## Regionalization — Partitioning the Network

Prior to 2022, if a customer in New York ordered an item, it might have shipped from a warehouse in California (3,000 miles away) if the local warehouse was out of stock. This was incredibly inefficient.

Amazon restructured its US network into **8 autonomous regions**:

```text
Pre-Regionalization:
  Customer in NY → Order fulfilled from CA (3,000 miles) → 3-5 day delivery.

Post-Regionalization:
  Customer in NY → Order fulfilled from NJ or PA (100 miles) → Same/Next day delivery.

Results:
  - Average travel distance per package dropped by ~60%
  - Significant reduction in shipping costs
  - Delivery times dropped by 1-2 days
  - Massive reduction in carbon footprint
```

### Regional Inventory Strategy

```text
SKU "IPHONE-16-256GB":
  National Demand: 100,000/month
  
  Northeast Region (NY, NJ, PA):  25,000/mo → Stock 30,000
  West Region (CA, WA, OR):       20,000/mo → Stock 25,000
  South Region (TX, FL, GA):      18,000/mo → Stock 22,000
  ...
  
  Buffer: 22,000 kept at a central cross-dock facility for overflow/rebalancing.
```

---

## Comparing Amazon vs. eBay vs. Regional Marketplaces

| Aspect | Amazon | eBay | Regional Marketplaces |
|---|---|---|---|
| **Model** | 1P + FBA (Owns warehouses) | Marketplace (Sellers ship) | Marketplace + Fulfillment (e.g., Shopee) |
| **Facilities** | 175+ Global FCs | Seller warehouses + 3PLs | Regional fulfillment hubs |
| **Allocation** | CONDOR (Global/Continuous optimization) | Rule-based (Seller-defined) | Regional matching engines |
| **Anticipatory** | Yes (Late-Select Addressing) | No | No |
| **Structure** | 8 Autonomous Regions (US) | Decentralized | Geographic partitioning |

---

## Lessons Learned for System Design

You don't need to build CONDOR to apply its principles:

1. **Batch processing over real-time:** Don't dispatch an order the second it arrives. Hold it in a 15-30 minute batch window and optimize the entire batch together. It is always mathematically superior.
2. **Re-optimization:** The best route at 17:00 may be terrible by 17:30 as new orders arrive. Run iterative optimizations.
3. **Predictive placement:** If data shows consistent regional demand, stage the inventory there beforehand.
4. **Partitioning:** Break massive NP-hard routing problems into smaller regional chunks to make them solvable.

> *Next, we explore split shipments, consolidation, and the last-mile delivery problem—which accounts for 53% of all logistics costs. Read [Part 5 — Split Shipment, Consolidation & Last-Mile Delivery](/series/ecommerce-order-allocation/part-5-split-consolidation-lastmile/).*
