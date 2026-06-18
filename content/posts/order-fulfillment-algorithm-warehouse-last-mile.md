---
title: "Order Fulfillment Algorithm: Warehouse to Last-Mile"
slug: "order-fulfillment-algorithm-warehouse-last-mile"
date: "2026-06-01T10:00:00+07:00"
lastmod: "2026-06-01T10:00:00+07:00"
draft: false
mermaid: true
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
description: "How e-commerce giants decide which warehouse fulfills your order. Covers Amazon CONDOR, VRP solvers, split shipment logic, and last-mile routing."
ShowToc: true
TocOpen: true
---


**Answer-first:** How e-commerce giants decide which warehouse fulfills your order. Covers Amazon CONDOR, VRP solvers, split shipment logic, and last-mile routing.

When you place an order on Amazon at 11:47 PM and it arrives at your door the next morning, every step of that delivery was orchestrated by a set of algorithms making real-time decisions across a network of hundreds of warehouses, thousands of drivers, and millions of items in inventory. None of it happens by chance, and none of it is primarily a human decision.

This post covers the six-step algorithmic decision chain that transforms a confirmed order into a physical package at your door: from inventory availability checks and warehouse selection, through Amazon's CONDOR constraint optimizer and split shipment logic, to the vehicle routing problem solvers that plan the last mile.

For the complete series on e-commerce order allocation architecture, explore the [E-Commerce Order Allocation Series](/series/ecommerce-order-allocation/).

---

## The Order Allocation Problem: Why Millisecond Decisions Cost Millions

The warehouse selection decision sounds simple: check which warehouses have the item in stock, pick the closest one. In practice, it is a multi-objective optimization problem with interdependent constraints that must be solved in under 200ms per order, at a rate of millions of orders per day.

The constraints include:
- **Stock availability**: Is the item available at each candidate warehouse?
- **Fulfillment cost**: Shipping from a closer warehouse costs less, but labor costs vary by facility.
- **Delivery SLA**: Can this warehouse get the package on a carrier truck in time to meet the promised delivery date?
- **Carrier capacity**: Is the carrier serving this warehouse's zone at capacity? Is there scheduled pickup capacity remaining today?
- **Carbon and sustainability targets**: Some SKU categories carry emissions-based routing preferences.
- **Anticipated demand**: CONDOR (Amazon's constraint optimizer) considers not just current orders but probabilistic future orders when allocating inventory.

Getting this decision wrong — choosing a warehouse that cannot meet the SLA, or one with stock that is actually reserved for a different fulfillment channel — results in carrier delays, customer experience failures, and financial penalties.

---

## Step 1 — Inventory Availability Check: Real-Time Stock Sync Across Warehouses

Before the allocation algorithm runs, the system needs an accurate, real-time view of inventory. This is harder than it sounds.

Amazon's warehouse inventory system maintains two distinct counts:
- **Physical on-hand**: Units physically present in the warehouse
- **Available-to-promise (ATP)**: Physical on-hand minus units already committed to other orders (reserved, being picked, in transit to packing)

The ATP count is the relevant number for new orders. An item that appears in stock based on physical count may have zero ATP if all units are already allocated to orders being processed.

At Amazon's scale, the ATP count is updated continuously via a stream of inventory events: picks, putaways, returns, inbound receipts, and cross-docking events. These events flow through a real-time streaming pipeline (similar to the Kafka + Flink pattern described in the [Real-Time Ride-Hailing Architecture](/posts/real-time-ride-hailing-architecture/) post) into an in-memory inventory cache that serves the allocation lookup.

### Soft Reservations

When an order is placed, a **soft reservation** is created immediately in the cache — decrementing the ATP counter before the order is formally confirmed in the database. This prevents two orders from being allocated to the same last unit simultaneously. The soft reservation has a TTL (typically 5–15 minutes); if the order fails payment or fraud checks, the reservation expires and the inventory is released.

This pattern is identical to the Redis atomic counter pattern used in flash sales — see [Shopee Flash Sale Architecture: Rate Limiting & Redis](/posts/shopee-flash-sale-architecture/) for the detailed implementation.

---

## Step 2 — Warehouse Selection Algorithm: Distance, Cost, and SLA Trade-Offs

With the inventory availability map established, the warehouse selection algorithm evaluates candidate fulfillment centers against a cost function.

The naive version of this cost function is:

```
cost(warehouse, order) = shipping_distance * shipping_rate_per_km + labor_cost(warehouse)
```

The production version adds a set of multipliers and constraints:

```
cost(warehouse, order) = 
    (shipping_distance * carrier_rate_per_km)
    + (labor_cost_per_unit(warehouse))
    + (SLA_risk_penalty if fulfillment_time > SLA_threshold)
    + (carrier_capacity_surcharge if capacity_utilization > 0.85)
    - (carbon_credit if warehouse_in_green_zone)
```

This cost function is evaluated for every candidate warehouse that has ATP > 0 for the ordered item. The warehouse with the minimum cost is selected.

For items with availability at only one warehouse, the selection is trivial. For items available at dozens of warehouses (common for high-velocity SKUs), the optimization across a large candidate set requires pruning strategies — discarding warehouses outside the plausible SLA radius before evaluating the full cost function.

---

## Step 3 — Amazon CONDOR: The Constraint Optimizer for Global Fulfillment

CONDOR (Constraint Optimizer for Network Distribution of Orders and Replenishment) is Amazon's internal system for solving the global fulfillment allocation problem. It operates above the per-order warehouse selection layer and solves the **network-wide inventory allocation problem**: how should Amazon position its inventory across its fulfillment network to minimize total fulfillment cost for anticipated future orders?

### CONDOR as a Global Optimizer

CONDOR ingests:
- Current ATP inventory at every fulfillment center globally
- Historical demand signals by SKU, geography, and day-of-week
- Probabilistic demand forecasts (ML models predicting order volumes by region and SKU for the next 14 days)
- Carrier capacity schedules, truck lane rates, and fulfillment center labor cost models

It outputs:
- Inventory transfer recommendations (move X units of SKU Y from FC A to FC B by date Z)
- Carrier lane reservation targets
- Replenishment order suggestions to vendors

CONDOR's recommendations are not applied automatically — they are reviewed by Amazon's supply chain operations team and executed via replenishment workflows. But the outputs drive the majority of Amazon's proactive inventory positioning decisions.

### Why This Matters for Per-Order Allocation

CONDOR's influence on per-order fulfillment is indirect but profound. Because CONDOR continuously rebalances inventory to minimize expected shipping distance for anticipated orders, the warehouse selection algorithm typically finds that the optimal warehouse is already nearby. The real-time per-order optimizer runs faster and produces better results because CONDOR has done the strategic pre-positioning work.

For a deep dive into CONDOR's constraint optimization models, see [Part 4 — Amazon CONDOR & Anticipatory Shipping](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/).

---

## Step 4 — Anticipatory Shipping: Predicting Orders Before They're Placed

Anticipatory shipping (Amazon holds a patent on the concept under the name "predictive shipping") takes CONDOR's forecasting one step further: instead of waiting for an order to be placed and then shipping, Amazon ships products to regional distribution centers before an order has been placed, based on predicted demand.

### How Anticipatory Shipping Works

The ML model driving anticipatory shipping considers:
- User browsing and wishlist behavior
- Regional seasonal demand patterns (winter coats in northern cities in November)
- Recent marketing campaign schedules
- Subscribe & Save and scheduled repeat order patterns

When the model's confidence score for a user ordering a specific product exceeds a threshold, Amazon ships a unit from a central fulfillment center to a regional sortation center or a Prime Now delivery station near the predicted buyer. If the user then places an order, the item is already in their metro area — enabling same-day or next-morning delivery without express shipping costs.

If the prediction is wrong and the user does not order, the pre-positioned unit is reabsorbed into regional inventory and may be sold to another buyer in the area — or shipped back to the central FC if demand does not materialize.

The financial viability of anticipatory shipping depends on high prediction accuracy. The cost of an incorrect pre-shipment (wasted forward shipping + potential return shipping) must be less than the average revenue improvement from converting users who would otherwise choose a competitor with faster delivery.

---

## Step 5 — Split Shipment vs. Consolidation: When to Ship in Multiple Packages

Multi-item orders create a fulfillment decision: should all items ship from the same warehouse (consolidation), or should each item ship from the warehouse that stocks it (split shipment)?

### The Trade-Off Matrix

| Scenario | Best Choice | Reasoning |
|---|---|---|
| All items at same FC, SLA met | **Consolidation** | Single package cost, single delivery event |
| Item A at FC-West, Item B at FC-East, SLA tight | **Split Shipment** | Both items arrive on time; consolidation would delay one |
| Item B available at FC-West in 2 days (replenishment) | **Delay + Consolidate** | If SLA allows, avoid split for customer convenience |
| High-value + fragile item, rest are bulky | **Split** | Separate handling reduces damage risk |

Amazon's split shipment algorithm models the full cost of each option:
- **Consolidation cost**: Shipping cost + potential SLA violation penalty
- **Split cost**: Two shipping costs + reduced customer experience score (studies show customers perceive split deliveries as service failures even when both arrive on time)

The algorithm weights customer experience signals heavily: a customer who received a split shipment previously has a measurably higher churn probability, so avoiding splits for high-LTV customers gets a priority boost.

---

## Step 6 — Last-Mile Delivery: VRP Solvers and Distance Matrix Calculation

Once the warehouse decision is made, the physical package begins its journey. The last-mile routing problem — assigning packages to drivers and planning the optimal delivery sequence for each driver — is a classic **Vehicle Routing Problem (VRP)**.

### The Vehicle Routing Problem (VRP)

The VRP asks: given a set of delivery locations, a fleet of vehicles with capacity constraints, and a central depot, find the set of routes that minimizes total distance (or time) while ensuring every location is served exactly once and no vehicle exceeds its capacity.

The VRP is NP-hard in general — there is no polynomial-time exact solution. At Amazon's scale (millions of deliveries per day), exact optimization is computationally intractable. The practical approaches are:
- **Heuristic solvers**: Clarke-Wright Savings algorithm, or-opt, 2-opt improvement heuristics
- **Google OR-Tools**: An open-source constraint programming and routing solver that applies meta-heuristics (LNS — Large Neighborhood Search) to find near-optimal solutions
- **ML-augmented routing**: Using learned value functions to prioritize promising search directions during heuristic optimization

### Distance Matrix Calculation

VRP solvers require a distance (or travel time) matrix between all delivery points and the depot. This matrix cannot be computed using straight-line (Euclidean) distances — road network distances differ significantly, especially in urban areas with one-way streets, traffic signals, and physical barriers.

Amazon uses a combination of GraphHopper (self-hosted on the road network data from OpenStreetMap) and proprietary HERE Maps APIs to pre-compute realistic road-network travel times between all pairs of delivery locations in a zone. This distance matrix computation happens the night before, so routes are planned by morning.

For a detailed breakdown of GraphHopper's distance matrix API and how it is deployed in production, see [GraphHopper vs CARTO: Order Fulfillment Routing Engine](/posts/graphhopper-distance-matrix-routing/) and the full [Geospatial & Routing Engine Architecture series](/series/routing-geospatial-architecture/).

### The "A-to-Z" Driver App and Sequence Optimization

Amazon's delivery drivers use the Amazon Flex "A-to-Z" app, which presents an optimized sequence of stops. The sequence is pre-computed by the VRP solver but can be dynamically adjusted in real time based on:
- Live traffic data (Google Maps or HERE Traffic APIs)
- Successful deliveries (removing completed stops)
- Failed deliveries (reattempt scheduling or locker redirect)
- Customer reschedules or OTP (One-Time Password) requests

This dynamic re-optimization runs continuously during the delivery window, ensuring that a mid-route traffic jam or access failure triggers a re-route rather than a missed SLA.

---

## Building Your Own Mini Allocation Engine (Google OR-Tools)

For engineers building warehouse allocation or last-mile routing for a smaller-scale platform, Google OR-Tools provides a production-grade open-source foundation.

A minimal Python implementation of the VRP solver using OR-Tools:

```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def solve_vrp(distance_matrix, num_vehicles, depot):
    """
    distance_matrix: NxN matrix of travel times between locations
    num_vehicles: number of available delivery vehicles
    depot: index of the depot location in the matrix
    """
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

    # Add Distance constraint (capacity of each route in time units)
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

This solver is capable of handling hundreds of delivery locations per route plan. For production use at thousands of locations per day, OR-Tools can be deployed as a containerized microservice with a REST API — scalable independently from the order management system. The architecture for such a service integrates naturally with the Kubernetes-based Go microservices stack described in [Architecting a 21-Service E-Commerce Ecosystem](/posts/architecting-21-service-ecommerce-golang-ddd/).

---

## Frequently Asked Questions

### How does Amazon decide which warehouse to ship from?
Amazon's warehouse selection algorithm evaluates every fulfillment center with available-to-promise inventory against a cost function that combines shipping distance, carrier rates, labor costs, SLA risk, and carrier capacity utilization. CONDOR, Amazon's global constraint optimizer, pre-positions inventory across the network based on demand forecasts, so the optimal warehouse is usually already nearby when the real-time allocation runs.

### What is the Vehicle Routing Problem (VRP) in e-commerce?
The VRP is a combinatorial optimization problem: given a fleet of vehicles, a depot, and a set of delivery locations, find the routes that minimize total distance while respecting vehicle capacity constraints and serving every location exactly once. It is the core algorithm behind every last-mile delivery routing system. It is NP-hard, so production systems use heuristic solvers (like Google OR-Tools) that find near-optimal solutions within time constraints.

### What is Amazon Anticipatory Shipping and how does it work?
Anticipatory shipping (patented as "predictive shipping") ships products to regional distribution centers before a customer places an order, based on ML-predicted demand. The model considers browsing behavior, regional seasonal patterns, and scheduled repeat orders. If the prediction is correct, the item is already in the customer's metro area, enabling same-day or next-morning delivery at standard shipping cost.

---

**Related Reading:** For the demand-side of logistics platforms — how real-time driver supply and demand signals are used to dynamically adjust pricing — see [Surge Pricing Algorithm & Spatial Indexing Architecture](/posts/surge-pricing-optimization-architecture/). For the full routing engine deep-dive, the [Geospatial & Routing Engine Architecture series](/series/routing-geospatial-architecture/) covers GraphHopper deployment, H3 indexing, and production Distance Matrix APIs end-to-end.

{{< author-cta >}}
