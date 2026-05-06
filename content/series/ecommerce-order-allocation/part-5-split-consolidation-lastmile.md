---
title: "Part 5 — Split Shipment, Consolidation & Last-Mile Delivery"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "The core trade-off: Should you split an order or consolidate it? Plus, optimizing the last-mile delivery, which accounts for 53% of total logistics costs."
weight: 6
---

## Split vs. Consolidation — The Core Trade-off

When a customer's order contains multiple items, and those items reside in different warehouses, the system faces a classic logistics dilemma:

```text
Order: 3 items (A in WH New York, B in WH Chicago, C in WH Miami)
Destination: Customer in New York

Option 1: SPLIT SHIPMENT (Ship directly from 3 warehouses)
  WH NY → Customer: Item A (1 box)      — $3.00, 2 hours
  WH Chicago → Customer: Item B (1 box) — $8.50, 2 days
  WH Miami → Customer: Item C (1 box)   — $6.50, 1.5 days
  Total: $18.00, 3 separate deliveries, 3 boxes

Option 2: CONSOLIDATE (Transfer internally, ship once)
  WH Chicago → WH NY: Item B (internal) — $4.00, 1 day
  WH Miami → WH NY: Item C (internal)   — $3.50, 1 day
  WH NY → Customer: A+B+C (1 box)       — $4.50, 2 hours
  Total: $12.00, 1 delivery, 1 box, BUT delayed by 1-2 days

The Trade-off: Fast & Expensive vs. Slow & Cheap
```

### Decision Matrix

| Factor | Favors Split | Favors Consolidation |
|---|---|---|
| **SLA Requirements** | Urgent (same-day, 2-hour) | Standard (3-5 days) |
| **Shipping Costs** | Customer pays for shipping | Free shipping (Platform absorbs cost) |
| **Customer Preference**| Wants items ASAP | Wants everything in one box |
| **Order Value** | Small items (not worth consolidating)| Large orders (significant savings) |
| **Item Type** | Perishables / Medical supplies | Non-urgent dry goods |

---

## The Split/Consolidate Algorithm

```text
Function: decideFulfillmentStrategy(order, warehouses)

  // Step 1: Is there a single warehouse with ALL items?
  single_source = findWarehouseWithAllItems(order.items, warehouses)
  if single_source exists:
    return SINGLE_SOURCE(single_source)  // The ideal scenario

  // Step 2: Calculate costs for both strategies
  split_cost = calculateSplitCost(order)
  consolidate_cost = calculateConsolidateCost(order)

  // Step 3: Check SLA bounds
  if order.sla == "SAME_DAY" or order.sla == "2_HOURS":
    return SPLIT  // No time to transfer inventory internally

  // Step 4: Compare cost vs. delay
  savings = split_cost - consolidate_cost
  consolidation_delay = estimateConsolidationDelay(order)

  // Only consolidate if savings exceed a threshold AND delay is acceptable
  if savings > THRESHOLD and consolidation_delay <= order.max_acceptable_delay:
    return CONSOLIDATE
  else:
    return SPLIT
```

---

## Last-Mile Delivery — The Most Expensive Mile

The **last-mile** is the final leg of delivery from the local distribution hub to the customer's doorstep. Even though it's usually just a few miles, it accounts for **53% of total logistics costs**. Why?

```text
Line-haul (Long distance):
  1 massive truck carries 10,000 packages for 500 miles.
  Cost per package: ~$0.50

Last-mile:
  1 driver delivers 20-30 packages across 30 miles of city traffic.
  Cost per package: ~$1.50 - $2.50  ← 3x to 5x more expensive!

Reasons for high cost:
  - Low speeds (traffic jams, stoplights)
  - Many stops (each package requires stopping, parking, walking)
  - Dwell time (waiting for customers, navigating apartment complexes)
  - High labor costs (1 driver per 20 packages vs 1 driver per 10,000)
```

### Optimizing the Last-Mile

**1. Delivery Density:**
```text
Low Density:                High Density:
  ○                            ○ ○
     ○                         ○ ○ ○
  ○       ○                    ○ ○
                               ○ ○ ○
  10 packages, 30 miles        10 packages, 5 miles
  Cost/pkg: $2.50              Cost/pkg: $0.80

Amazon's CONDOR algorithm specifically optimizes for density, batching nearby orders together.
```

**2. Time Windows:**
```text
Allowing customers to pick delivery slots:
  8:00-10:00  | 10:00-12:00 | 14:00-16:00 | 18:00-20:00

Benefit: Drivers know the customer will be home.
→ Reduces re-delivery attempts from 15% to under 3%.
→ Allows the VRP solver to cluster routes around these time windows.
```

**3. Delivery Lockers / Pickup Points (PUDO):**
```text
Instead of delivering to 50 separate houses:
  → Customers pick up from a centralized locker.
  → 1 driver delivers 50 packages to 1 locker in a single stop.
  → Cost per package drops by 60-70%.
```

---

## SKU Affinity — Smart Inventory Placement

Products that are frequently bought together should be stored together:

```text
Data Analysis:
  iPhones are bought with: cases (78%), chargers (65%), AirPods (45%)
  Laundry detergent bought with: fabric softener (82%), paper towels (40%)

Action: Store the iPhone + Case + Charger in the SAME WAREHOUSE BIN.
Result: Reduces the probability of a split shipment from 30% to 12%.
```

```sql
-- Calculating SKU affinity from historical order data
SELECT
    a.sku AS sku_a,
    b.sku AS sku_b,
    COUNT(DISTINCT a.order_id) AS co_occurrence,
    COUNT(DISTINCT a.order_id)::float / 
      (SELECT COUNT(DISTINCT order_id) FROM order_items WHERE sku = a.sku) AS affinity_score
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.sku < b.sku
GROUP BY a.sku, b.sku
HAVING COUNT(DISTINCT a.order_id) > 100
ORDER BY affinity_score DESC;
```

---

## Last-Mile Metrics

| Metric | Meaning | Target |
|---|---|---|
| **Cost per delivery** | Average cost to fulfill the last-mile | < $1.50 |
| **Stops per route** | Number of delivery stops a driver makes | > 25 |
| **Delivery density** | Packages per square mile | > 5 |
| **First attempt success** | % of packages delivered on the first try | > 95% |
| **Split shipment rate** | % of multi-item orders split into >1 box | < 15% |
| **On-time delivery** | % of orders delivered within SLA | > 98% |

> *Finally, it's time to build! In the last part, you will build a Mini Order Allocation Engine using Python and Google OR-Tools to solve min/max capacity constraints and order priorities. Read [Part 6 — Hands-on: Building a Mini Allocation Engine with Google OR-Tools](/series/ecommerce-order-allocation/part-6-build-mini-allocation-engine/).*
