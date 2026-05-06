---
title: "Part 6 — Hands-on: Building a Mini Allocation Engine with Google OR-Tools"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "A comprehensive hands-on project — building a professional order allocation system using Python and Google OR-Tools to solve Min/Max Capacity and Priority constraints."
weight: 7
---

## Problem Statement

You are a software engineer at a logistics company. Every day, the warehouse dispatches hundreds of orders. You need to allocate these orders to a fleet of drivers such that:

### Input
- **1 single warehouse** (The Depot/Starting Point).
- **N drivers**, where each driver has:
  - `min_capacity`: The minimum number of units they must carry (for the trip to be profitable).
  - `max_capacity`: The physical limit of their vehicle (weight/volume).
- **M orders**, where each order has:
  - `capacity_cost`: The capacity footprint of the order (e.g., 1 case of water = 3 units, 1 smartphone = 1 unit).
  - `destination`: The delivery coordinates (to calculate distance).
  - `priority`: Delivery urgency (EXPRESS, STANDARD).

### Real-world Constraints
```text
1. Capacity Constraint:
   ∀ used driver d: min_capacity(d) ≤ sum_of_assigned_order_capacity ≤ max_capacity(d)

2. Delivery Guarantee:
   Maximize the number of delivered orders. If over-capacity occurs, the system must drop STANDARD orders and absolutely guarantee EXPRESS orders are delivered.

3. Objective:
   Minimize the total driving distance across the entire fleet.
```

---

## Step 1: Database Schema

We use a standard relational database schema to manage states:

```sql
-- DRIVERS
CREATE TABLE drivers (
    id              VARCHAR(20) PRIMARY KEY,
    min_capacity    INT NOT NULL,
    max_capacity    INT NOT NULL,
    status          VARCHAR(20) DEFAULT 'AVAILABLE'
);

-- ORDERS
CREATE TABLE orders (
    id              VARCHAR(20) PRIMARY KEY,
    capacity_cost   INT NOT NULL,
    priority        VARCHAR(20) DEFAULT 'STANDARD',
    status          VARCHAR(20) DEFAULT 'PENDING',
    dest_latitude   DECIMAL(10,7),
    dest_longitude  DECIMAL(10,7)
);

-- ALLOCATIONS
CREATE TABLE allocations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id        VARCHAR(50) NOT NULL,
    driver_id       VARCHAR(20) NOT NULL REFERENCES drivers(id),
    order_id        VARCHAR(20) NOT NULL REFERENCES orders(id),
    sequence_num    INT NOT NULL
);
```

---

## Step 2: Allocation Algorithm with Google OR-Tools (Python)

Instead of writing a custom Greedy algorithm which often falls into local optima, we will use the world-class **Google OR-Tools** library. 

The system is designed as a Python microservice:

### 1. Initializing the Data Model

```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_data_model(orders, drivers, distance_matrix):
    data = {}
    data['distance_matrix'] = distance_matrix  # Pre-computed distance matrix
    
    # Demands at each node (Node 0 = Depot)
    # E.g.: Depot=0, Order1=3, Order2=1, Order3=4
    data['demands'] = [0] + [order['capacity_cost'] for order in orders]
    
    # Priority penalty (Cost applied if an order is NOT delivered)
    # EXPRESS = 1,000,000 | STANDARD = 10,000
    data['penalties'] = [0] + [
        1000000 if order['priority'] == 'EXPRESS' else 10000 
        for order in orders
    ]
    
    # Vehicles (Drivers)
    data['vehicle_capacities'] = [driver['max_capacity'] for driver in drivers]
    data['vehicle_min_capacities'] = [driver['min_capacity'] for driver in drivers]
    data['num_vehicles'] = len(drivers)
    data['depot'] = 0
    return data
```

### 2. Setting Up the Solver and Max Capacity

```python
def solve_allocation(data):
    # Initialize Routing Index Manager and Model
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']), data['num_vehicles'], data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    # Distance callback
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Capacity callback
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    # Add Dimension to manage Max Capacity per vehicle
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # Max capacities array
        True,  # start cumul to zero
        'Capacity'
    )
```

### 3. Handling Disjunctions (EXPRESS Priority)

To handle scenarios where the fleet cannot carry all orders, we allow the system to "drop" nodes, but it will incur a penalty. OR-Tools will try to minimize the total penalty, thus it will naturally drop STANDARD orders and keep EXPRESS orders.

```python
    # Allow dropping orders subject to penalties
    for node in range(1, len(data['distance_matrix'])):
        routing.AddDisjunction([manager.NodeToIndex(node)], data['penalties'][node])
```

### 4. Solving the Min-Capacity Constraint (The Hardest Part)

OR-Tools does not have a built-in `AddMinCapacity` function. We must implement this at the solver level using constraint variables.

```python
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    solver = routing.solver()

    for vehicle_id in range(data['num_vehicles']):
        # Get the variable representing the total load at the end of the vehicle's route
        end_index = routing.End(vehicle_id)
        load_var = capacity_dimension.CumulVar(end_index)
        
        # Boolean variable is_used: =1 if load > 0, =0 if load == 0
        is_used = solver.IsGreaterCstVar(load_var, 0)
        
        # Constraint: load_var >= is_used * min_capacity
        # If vehicle is unused (is_used=0) → load_var >= 0 (Always true)
        # If vehicle is used (is_used=1) → load_var >= min_capacity
        min_cap = data['vehicle_min_capacities'][vehicle_id]
        solver.Add(load_var >= is_used * min_cap)
```

### 5. Running the Algorithm

```python
    # Set search strategies
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 5  # Stop after 5 seconds of optimization

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Parse and return results
    if solution:
        return parse_solution(manager, routing, solution, data)
    return None
```

---

## Step 3: Packaging into a FastAPI Service

To integrate this Python engine with other microservices (e.g., an Order Service written in Golang), we wrap it in a REST API using **FastAPI**:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class OrderReq(BaseModel):
    id: str
    capacity_cost: int
    priority: str
    lat: float
    lng: float

class DriverReq(BaseModel):
    id: str
    min_capacity: int
    max_capacity: int

class AllocationRequest(BaseModel):
    batch_id: str
    warehouse_lat: float
    warehouse_lng: float
    orders: list[OrderReq]
    drivers: list[DriverReq]

@app.post("/api/v1/allocate")
def allocate_batch(req: AllocationRequest):
    # 1. Calculate distance matrix (using Haversine or OSRM)
    distance_matrix = build_distance_matrix(req)
    
    # 2. Build Data Model
    data = create_data_model(req.orders, req.drivers, distance_matrix)
    
    # 3. Run OR-Tools Solver
    result = solve_allocation(data)
    
    return {"batch_id": req.batch_id, "allocations": result}
```

---

## Step 4: Invariant Checks

After the Python API returns the allocation and it's saved to the Database, run these SQL checks to guarantee system integrity:

```sql
-- Check 1: No order is assigned to more than 1 driver
SELECT order_id, COUNT(DISTINCT driver_id) AS driver_count
FROM allocations
WHERE batch_id = 'BATCH-001'
GROUP BY order_id
HAVING COUNT(DISTINCT driver_id) > 1;

-- Check 2: No driver exceeds MAX capacity
SELECT
    a.driver_id, d.max_capacity, SUM(o.capacity_cost) AS total_assigned
FROM allocations a
JOIN orders o ON a.order_id = o.id
JOIN drivers d ON a.driver_id = d.id
WHERE a.batch_id = 'BATCH-001'
GROUP BY a.driver_id, d.max_capacity
HAVING SUM(o.capacity_cost) > d.max_capacity;

-- Check 3: No driver is below MIN capacity (if they were dispatched)
SELECT
    a.driver_id, d.min_capacity, SUM(o.capacity_cost) AS total_assigned
FROM allocations a
JOIN orders o ON a.order_id = o.id
JOIN drivers d ON a.driver_id = d.id
WHERE a.batch_id = 'BATCH-001'
GROUP BY a.driver_id, d.min_capacity
HAVING SUM(o.capacity_cost) < d.min_capacity;

-- Check 4: Did any EXPRESS orders get dropped?
SELECT o.id
FROM orders o
LEFT JOIN allocations a ON o.id = a.order_id AND a.batch_id = 'BATCH-001'
WHERE o.priority = 'EXPRESS' AND a.id IS NULL;
-- If this returns rows, it means the absolute maximum capacity of the entire fleet 
-- was smaller than the total capacity of EXPRESS orders alone.
```

---

## Conclusion: Why Use OR-Tools?

Transitioning from a custom heuristic to Google OR-Tools provides immense value:

1. **True Routing Optimization:** OR-Tools doesn't just pack boxes into vans (Bin Packing); it sequences the delivery stops to minimize actual driven miles.
2. **Global Search:** Thanks to `GUIDED_LOCAL_SEARCH`, if the solver gets stuck in a bad configuration, it knows how to swap orders between vehicles to escape local optima.
3. **Future-Proofing:** If the business later requires *"Ice cream must be delivered within 30 minutes"*, you simply add a `Time Window Dimension`. You don't have to rewrite the entire algorithm from scratch.

> *You've solved the vehicle assignment and capacity problem. But there's one massive bottleneck remaining: calculating the distance between thousands of points. Read [Part 7 — Distance Matrix: Routing Distance Calculation Algorithms](/series/ecommerce-order-allocation/part-7-distance-matrix-routing/).*
