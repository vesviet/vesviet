---
title: "Part 3 — Allocation Algorithms: Assignment, Bin Packing & VRP"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "The three core algorithm families for order allocation: Assignment Problem (optimal matching), Bin Packing (fitting orders into vehicles), and Vehicle Routing Problem (VRP)."
weight: 4
---

## The Three Sub-Problems

Allocating orders to drivers is essentially a combination of three classic optimization problems:

```text
Step 1: ASSIGNMENT — Which order goes to which driver?
Step 2: BIN PACKING — How many orders can fit in a driver's vehicle? (capacity constraint)
Step 3: VRP — What is the optimal route for the driver to deliver them? (routing)

In practice, all three are often solved simultaneously.
```

---

## Problem 1: Assignment Problem

### Definition
Given **N orders** and **M drivers**, every (order, driver) pair has an associated **cost** (distance, time, or money). Find an assignment that minimizes the **total cost**.

### Cost Matrix

```text
            Driver 1   Driver 2   Driver 3   Driver 4
Order A  [    5          8          3          7     ]
Order B  [    9          4          6          2     ]
Order C  [    3          7          8          5     ]
Order D  [    6          2          4          9     ]

Goal: Assign each Order to exactly 1 Driver such that the total sum is minimized.
```

### Hungarian Algorithm — O(n³)

```text
Step 1: Subtract the row minimum from each row
            D1   D2   D3   D4
  A  [   2    5    0    4  ]   (subtracted 3)
  B  [   7    2    4    0  ]   (subtracted 2)
  C  [   0    4    5    2  ]   (subtracted 3)
  D  [   4    0    2    7  ]   (subtracted 2)

Step 2: Subtract the column minimum from each column
            D1   D2   D3   D4
  A  [   2    5    0    4  ]
  B  [   7    2    4    0  ]
  C  [   0    4    5    2  ]
  D  [   4    0    2    7  ]
  (Col 1 already has 0, Col 2 has 0, Col 3 has 0, Col 4 has 0)

Step 3: Find an assignment such that each row and column selects exactly one 0
  A → D3 (original cost 3)
  B → D4 (original cost 2)
  C → D1 (original cost 3)
  D → D2 (original cost 2)

  Total cost: 3 + 2 + 3 + 2 = 10 (Optimal)
```

### Real-world Limitations
The Hungarian Algorithm assumes each driver takes **exactly 1 order**. In reality, a driver takes **multiple orders** (bounded by vehicle capacity) → requiring Bin Packing.

---

## Problem 2: Bin Packing

### Definition
Given **N orders** (each with a capacity cost) and **M drivers** (each with a max capacity). Pack all orders into the drivers' vehicles such that:
- No driver exceeds their max capacity.
- The number of drivers used is minimized (or wasted capacity is minimized).

### Visual Example

```text
Orders (capacity cost):
  Order A: 3  (3 cases of water)
  Order B: 1  (1 phone)
  Order C: 4  (4 cartons of milk)
  Order D: 2  (2 cosmetic boxes)
  Order E: 5  (5 cases of beer)
  Order F: 2  (2 shoeboxes)

Drivers (min_capacity=2, max_capacity=8):

  Driver 1 [████████] max=8
  Driver 2 [████████] max=8
  Driver 3 [████████] max=8

First Fit Decreasing Algorithm:
  Sort orders DESC: E(5), C(4), A(3), D(2), F(2), B(1)

  Driver 1: E(5) + A(3) = 8/8 ████████ (Full)
  Driver 2: C(4) + D(2) + F(2) = 8/8 ████████ (Full)
  Driver 3: B(1) = 1/8 █        ← Only 1 unit, < min_capacity(2)!

  Problem: Driver 3 is assigned only 1 unit, below the min capacity required to make the trip profitable!
```

### Min-Max Capacity Bin Packing

This is a specific variation of the problem common in logistics:

```text
Constraint:
  ∀ driver d:  min_capacity(d) ≤ Σ order_capacity ≤ max_capacity(d)

If you cannot assign enough orders to meet a driver's min_capacity, you cannot use that driver.
```

### Improved Greedy Algorithm

```text
Algorithm: MinMax-BinPacking

Input: orders[] (sorted by capacity DESC), drivers[] (sorted by max_capacity DESC)

1. Sort orders by capacity descending
2. For each order:
   a. Find a driver with enough remaining_capacity
   b. Priority: drivers closest to meeting their min_capacity but haven't yet
   c. If no driver fits → open a new driver (if available)

3. Post-processing:
   a. For drivers with total capacity < min_capacity → attempt to steal orders from other drivers
   b. If they still can't meet min_capacity → unassign their orders and leave them for the next batch
```

---

## Problem 3: Vehicle Routing Problem (VRP)

### Definition
Once we know which driver takes which orders, we must find the **optimal delivery sequence** for each driver (visiting all delivery points, returning to the depot, minimizing total distance).

```text
Driver 1 takes 4 orders: A (Zone 1), B (Zone 3), C (Zone 7), D (Zone 5)

Naive Route:  Depot → A → B → C → D → Depot   (20 miles)
Optimal:      Depot → A → D → C → B → Depot   (14 miles)

VRP = Travelling Salesman Problem (TSP) × M drivers + capacity constraints
```

### Capacitated VRP (CVRP)

CVRP adds capacity constraints to the classic routing problem:

```text
CVRP:
  Minimize: Total distance traveled by all drivers
  Subject to:
    - Each order is visited exactly once
    - Each driver starts and ends at the depot
    - Total order capacity on any vehicle never exceeds max capacity
    - (Optional) Delivery time ≤ SLA (VRPTW - VRP with Time Windows)
```

### VRP Solving Algorithms

| Algorithm | Type | Speed | Quality |
|---|---|---|---|
| **Brute Force** | Exact | O(n!) | Optimal, but only works for n < 15 |
| **Branch & Bound** | Exact | O(2^n) | Optimal, works for n < 30 |
| **Clarke-Wright Savings**| Heuristic | O(n²) | Good, fast |
| **Google OR-Tools** | Meta-heuristic| O(n² log n) | Excellent, industry standard |
| **Genetic Algorithm** | Meta-heuristic| Custom | Good for very large datasets |

---

## Synthesis: Order-Driver Assignment with Capacity & Routing

In modern systems, all 3 problems are solved **simultaneously** or **iteratively**:

```text
Combined Algorithm Pipeline:

Round 1: Assignment
  - Compute distance matrix
  - Cluster orders geographically (e.g., K-Means or DBSCAN)

Round 2: Bin Packing
  - Assign each cluster to a driver
  - Check: min_capacity ≤ cluster_total ≤ max_capacity
  - If cluster is too large → split it
  - If cluster is too small → merge with a neighboring cluster

Round 3: VRP
  - Optimize the sequence for each driver's assigned orders (TSP)

Round 4: Local Search / Re-optimization
  - Attempt to swap orders between drivers
  - If a swap improves total cost → accept the swap
  - Repeat until no further improvements are found
```

---

## Industry Tools

| Tool | Description | Language |
|---|---|---|
| **Google OR-Tools** | The most powerful open-source optimization suite. Solves VRP, Bin Packing, Assignment. | C++, Python, Java, Go |
| **OptaPlanner** | AI planning framework for Java, excellent for VRPTW. | Java |
| **VROOM** | Fast routing optimization engine. | C++ |
| **OSRM** | Open Source Routing Machine (calculates actual road distances). | C++ |

### Google OR-Tools: VRP Example (Python)

```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def solve_vrp(distance_matrix, demands, vehicle_capacities, depot=0):
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), len(vehicle_capacities), depot)
    routing = pywrapcp.RoutingModel(manager)

    # Distance callback
    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return distance_matrix[from_node][to_node]

    transit_id = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_id)

    # Capacity constraint
    def demand_callback(idx):
        node = manager.IndexToNode(idx)
        return demands[node]

    demand_id = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_id, 0, vehicle_capacities, True, 'Capacity')

    # Solve
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    solution = routing.SolveWithParameters(search_params)
    return solution
```

> *Next, we look at how Amazon solves this at a massive global scale using CONDOR and Anticipatory Shipping. Read [Part 4 — Amazon CONDOR & Anticipatory Shipping](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/).*
