---
title: "Order Fulfillment Algorithm: Warehouse to Last-Mile"
slug: "order-fulfillment-algorithm-warehouse-last-mile"
author: "Lê Tuấn Anh"
date: "2026-06-01T10:00:00+07:00"
lastmod: "2026-07-23T13:34:42+07:00"
draft: false
categories:
  - "Engineering"
  - "Architecture"
  - "E-Commerce"
tags:
  - "Order Fulfillment"
  - "Warehouse"
  - "Last-Mile Delivery"
  - "VRP"
  - "Amazon"
  - "Logistics"
  - "Algorithms"
aliases:
  - /series/ecommerce-order-allocation/executive-summary/
  - /series/ecommerce-order-allocation/part-1-order-fulfillment-fundamentals/
  - /series/ecommerce-order-allocation/part-2-inventory-realtime/
  - /series/ecommerce-order-allocation/part-3-allocation-algorithms/
  - /series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/
description: "How e-commerce giants decide which warehouse fulfills your order. Covers Amazon CONDOR, VRP solvers, split shipment logic, and last-mile routing."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/order-fulfillment-cover.png"
  alt: "Order fulfillment algorithm: warehouse selection and last-mile optimization for e-commerce"
  relative: false
canonicalURL: "https://tanhdev.com/posts/order-fulfillment-algorithm-warehouse-last-mile/"
---

**Answer-first:** High-throughput e-commerce requires routing order fulfillment using a multi-criteria optimization model. By calculating stock availability, warehouse proximity, labor costs, and split-shipment constraints via a Vehicle Routing Problem (VRP) solver, systems minimize shipping costs while strictly meeting customer delivery SLAs.

---

## Executive Summary & Fulfillment Fundamentals

When an order is confirmed, the fulfillment system executes a multi-step decision pipeline:

1. **Available-to-Promise (ATP) Check**: Filter candidate warehouses by real-time uncommitted stock.
2. **Cost & Proximity Scoring**: Evaluate shipping distance, labor rate, carrier capacity, and SLA risk.
3. **Split vs. Consolidate Trade-Off**: Determine whether to ship from multiple warehouses or wait for inventory consolidation.
4. **CONDOR & Anticipatory Dispatch**: Pre-position stock globally based on probabilistic ML demand forecasts.
5. **Last-Mile VRP Solving**: Optimize driver routes using vehicle routing solvers (OR-Tools / GraphHopper).

---

## Step 1 — Real-Time Inventory & Available-to-Promise (ATP)

Physical stock on hand does not equal sellable stock. Fulfillment systems distinguish:
- **Physical On-Hand**: Total inventory units located inside the warehouse bin.
- **Available-to-Promise (ATP)**: Physical stock minus hard-committed and soft-reserved units.

### Soft Reservations with TTL
When a customer enters checkout, a **soft reservation** decrements ATP in an in-memory Redis cluster. The reservation carries a TTL (typically 5–15 minutes). If payment fails or the session times out, the reservation automatically expires and ATP is restored.

---

## Step 2 — Warehouse Selection Cost Function

The allocation engine evaluates candidate warehouses using a multi-criteria objective function:

$$\text{Cost}(W, O) = (d \cdot r_{\text{carrier}}) + c_{\text{labor}} + P_{\text{SLA}} + S_{\text{capacity}} - B_{\text{eco}}$$

Where:
- $d$: Distance from warehouse $W$ to delivery destination
- $r_{\text{carrier}}$: Carrier rate per km
- $c_{\text{labor}}$: Warehouse pick/pack labor cost per unit
- $P_{\text{SLA}}$: Penalty score if fulfillment time risks missing delivery window
- $S_{\text{capacity}}$: Carrier surcharge when daily outbound volume exceeds 85% capacity
- $B_{\text{eco}}$: Eco-bonus for green fulfillment locations

---

## Step 3 — Amazon CONDOR & Constraint Optimization

CONDOR operates globally above per-order routing:
- **Inputs**: Real-time ATP across all fulfillment centers, historical demand signals, regional ML demand forecasts (14-day window), carrier contract tiers.
- **Outputs**: Proactive inventory transfer recommendations (rebalancing stock from central FCs to regional sortation centers before orders are placed).

---

## Step 4 — Anticipatory & Predictive Shipping

Anticipatory shipping uses predictive ML models (browsing patterns, wishlist items, regional trends) to ship high-probability items to regional hub centers *before* the customer places the order. When the order occurs, the package is already in the buyer's metro area, enabling same-day delivery at minimal expedited freight cost.

---

## Step 5 — Split Shipment vs. Consolidation Logic

| Trade-Off Scenario | Selected Strategy | Rationale |
|---|---|---|
| All SKUs at same FC | **Consolidate** | Single package, minimal freight cost |
| SKUs at separate FCs, tight SLA | **Split Shipment** | Meet SLA; dual freight cost accepted |
| Secondary SKU restocking in 24h | **Delay & Consolidate** | Avoid split; customer prefers single delivery |

---

## Step 6 — Last-Mile Vehicle Routing Problem (VRP) Solver

The last-mile dispatch calculates optimal driver routes using Google OR-Tools / GraphHopper VRP solvers:

```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def solve_vrp(distance_matrix, num_vehicles, depot):
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), num_vehicles, depot
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,       # no slack
        3000,    # maximum distance per vehicle
        True,    # start cumul to zero
        dimension_name,
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(30)

    solution = routing.SolveWithParameters(search_parameters)
    return solution, routing, manager
```

---

## Frequently Asked Questions (FAQ)

{{< faq q="How does Amazon decide which warehouse to ship from?" >}}
Amazon's warehouse selection algorithm evaluates every fulfillment center with available-to-promise inventory against a cost function that combines shipping distance, carrier rates, labor costs, SLA risk, and carrier capacity utilization.
{{< /faq >}}

{{< faq q="What is the Vehicle Routing Problem (VRP) in e-commerce?" >}}
The VRP is a combinatorial optimization problem: given a fleet of vehicles, a depot, and a set of delivery locations, find the routes that minimize total distance while respecting vehicle capacity constraints and serving every location exactly once.
{{< /faq >}}

{{< faq q="What is Amazon Anticipatory Shipping and how does it work?" >}}
Anticipatory shipping ships products to regional distribution centers before a customer places an order, based on ML-predicted demand. If the prediction is correct, the item is already in the customer's metro area, enabling same-day delivery.
{{< /faq >}}

{{< author-cta >}}
