---
title: "OSRM vs GraphHopper: Architecture Comparison and Routing Engine Selection for Large Logistics"
slug: "osrm-vs-graphhopper-architecture-comparison"
author: "Lê Tuấn Anh"
date: "2026-07-17T14:00:00+07:00"
lastmod: "2026-07-18T08:00:00+07:00"
draft: false
aliases:
  - "/posts/graphhopper-distance-matrix-routing/"
categories:
  - "Architecture"
  - "Geospatial"
tags:
  - "OSRM"
  - "GraphHopper"
  - "Routing Engine"
  - "Logistics"
description: "In-depth comparison of OSRM and GraphHopper from an architect's perspective. Analyzing CH, MLD, LM algorithms, custom routing profiles, and real-world memory performance."
ShowToc: true
TocOpen: true
---

## Introduction: When Do You Outgrow Cloud Route APIs?

In the early stages of building a logistics, delivery, or ride-hailing system, leveraging cloud services like the Google Maps Directions API, HERE Maps API, or Mapbox is the undeniable safe bet. They provide highly accurate ETAs, excellent documentation, and require zero infrastructure maintenance. However, as the system scales past 100,000 requests per day or when you start needing massive Distance Matrices for multi-vehicle route optimization (VRP), the Total Cost of Ownership (TCO) inflates uncontrollably. 

Not only are they prohibitively expensive at scale, but these proprietary APIs also lack the flexibility required to inject custom routing rules. For instance, if your logistics fleet consists of 5-ton trucks that cannot enter certain city districts between 6 AM and 8 AM, or if you need to strictly penalize left turns at specific intersections to optimize fuel consumption, standard APIs fall short. They offer generic profiles for 'driving' or 'bicycling', but they do not allow you to define the exact physics and legal constraints of your unique vehicles.

This is the tipping point where software architects must consider self-hosting an OpenStreetMap (OSM) based routing engine on their own infrastructure. The two most formidable open-source contenders in this arena today are **OSRM** (Open Source Routing Machine) and **GraphHopper**. Both are extremely powerful, but they are built on fundamentally different philosophies regarding speed, memory management, and runtime flexibility.

## OSRM: The C++ Titan of Speed and Memory Optimization

Written entirely in C++, OSRM is renowned in the geospatial industry for its blistering, sub-millisecond response times. It achieves this by shifting the computational heavy lifting to an offline pre-processing phase, resulting in a highly optimized graph structure that can be queried instantly.

### Contraction Hierarchies (CH): The Speed Demon

OSRM's primary claim to fame is its implementation of the **Contraction Hierarchies (CH)** algorithm. 

The core concept of CH revolves around 'node ordering' and 'shortcut creation'. During the offline pre-processing phase (`osrm-contract`), the algorithm ranks all intersections (nodes) in the map based on their importance. It then "contracts" the less important nodes one by one. When a node is contracted, the algorithm adds a direct "shortcut" edge between its neighbors if the shortest path between them went through the contracted node. 

As a result, a routing query from Point A to Point B no longer needs to traverse every small street node. Instead, it quickly jumps onto the "shortcuts" (which usually correspond to major highways), drastically pruning the search space. This yields astonishing query speeds, often under 1 millisecond even for transcontinental routes. 

However, CH has a massive drawback: **extreme rigidity**. Any change to the road network—such as modifying edge weights due to a live traffic jam or a sudden road closure—requires recalculating the entire hierarchy. This offline compilation can take hours for a planet-sized map, making CH unsuitable for real-time traffic updates.

### Multi-Level Dijkstra (MLD): Balancing Speed and Updates

To mitigate the extreme rigidity of CH, OSRM introduced **Multi-Level Dijkstra (MLD)**, also known as Customizable Route Planning (CRP).

MLD relies on hierarchical graph partitioning. It divides the global graph into nested cells (e.g., cell level 1 might be a neighborhood, level 2 a city, level 3 a state). During the pre-processing phase (`osrm-partition` and `osrm-customize`), MLD calculates the optimal travel times between all boundary nodes of each cell. 

Because of this encapsulation, if a traffic jam occurs deep inside a specific cell, you only need to recalculate the metrics for that single cell and its parents, rather than the entire planet. This drops the update time from hours to mere seconds, allowing OSRM to support live traffic updates (see our guide on [OSRM Shared Memory on Kubernetes for Live Traffic]({{< ref "osrm-shared-memory-kubernetes-live-traffic" >}})).

### OSRM's Memory-Mapped Files (mmap)

Another architectural brilliance of OSRM is its memory management. Instead of loading massive graphs (which can be tens of gigabytes) entirely into physical RAM, OSRM utilizes the `mmap` syscall to directly map the binary graph file from disk into virtual memory.

When you run multiple OSRM worker processes on the same Kubernetes Node to handle high concurrency, the Linux kernel shares the memory pages across all processes. This drastically reduces the physical RAM footprint. You could run 10 OSRM workers, and they would collectively use only slightly more RAM than a single worker.

### The Achilles' Heel: Rigid Lua Profiles

OSRM defines routing logic—such as max speeds, road penalties, and access restrictions—via Lua scripts (e.g., `car.lua`, `bicycle.lua`). If you want to alter a rule, you must edit the Lua file and rerun the entire extraction and compilation pipeline. This offline rigidity makes dynamic, per-request routing logic incredibly cumbersome.

## GraphHopper: The Java Soul with Infinite Runtime Flexibility

GraphHopper, written in Java, takes a different approach. It trades a slight amount of raw speed and RAM efficiency for absolute flexibility at runtime.

### Custom Models and Dynamic Weighting

GraphHopper's crown jewel is its **Custom Models** feature. By passing a JSON payload directly inside your HTTP API request, you can dynamically alter route priorities on the fly.

For example, you can send a request that says: "Multiply the speed on all roads with `surface=gravel` by 0.5, and add a strict penalty for any road tagged as a `residential` zone." Unlike OSRM's static Lua compilation, GraphHopper evaluates these Custom Models at runtime. This makes it the undisputed champion for logistics companies managing diverse fleets (vans, heavy trucks, motorbikes) where each delivery request might have entirely different vehicle constraints.

### Landmarks Algorithm (LM / ALT)

To balance query speed with flexibility, GraphHopper heavily leverages the ALT (A*, Landmarks, Triangle Inequality) algorithm, commonly referred to as the **Landmarks (LM)** algorithm.

During preparation, GraphHopper selects a set of "Landmark" nodes spread across the map and pre-computes the distances from all nodes to these landmarks. When executing an A* search from Point A to Point B, it utilizes the triangle inequality theorem combined with the landmark distances to calculate a highly accurate heuristic. 

This heuristic severely prunes the A* search space. Crucially, the LM algorithm tolerates dynamic edge weight adjustments (like those from Custom Models) at runtime without requiring a full graph reprocessing, provided the new weights don't drop below the base distances.

### Optimizing JVM Heap & Off-heap Memory (RAMDirectory)

Being a Java application, GraphHopper must deal with the JVM's Garbage Collection (GC). A massive routing graph living inside the JVM heap would cause catastrophic Stop-The-World (STW) GC pauses.

GraphHopper elegantly tackles this using `RAMDirectory` backed by Java's `DirectByteBuffer`. This allocates the massive graph memory **Off-heap**, completely bypassing the Garbage Collector. The JVM only manages the small, short-lived objects created during the actual query execution. While GraphHopper consumes more RAM than OSRM's shared memory model, this off-heap strategy keeps latencies stable. [Check out our guide on tuning JVM RAM for GraphHopper on Kubernetes](/posts/graphhopper-kubernetes-self-hosting-osm/).

## Performance Benchmarks & Operational Costs

Let's look at the real-world operational characteristics when hosting these engines on a standard cloud instance (e.g., 8 vCPUs, 32GB RAM):

| Architectural Criteria | OSRM (C++) | GraphHopper (Java) |
|------------------------|------------|--------------------|
| **Raw Query Speed (A-B)** | Unbeatable (0.5 - 2ms) via CH | Fast (10-40ms) with LM / Custom Models |
| **Throughput (RPS/core)** | ~800 - 1000 RPS per core | ~200 - 400 RPS per core |
| **Memory Footprint**| Extremely low due to OS-level `mmap` | High, requires careful JVM Off-heap tuning |
| **Routing Logic Changes** | Requires offline Lua recompilation (rigid) | Extremely High (JSON Custom Models per request) |
| **Large Distance Matrix** | Outstanding (sub-second for 500x500 matrices) | [Needs specific tuning to avoid OOM crashes](/posts/graphhopper-distance-matrix-production-guide/) |
| **Startup Time** | Fast with `mmap` or Shared Memory | Slower due to JVM warmup and index loading |

## Decision Matrix: Which Engine Should You Choose?

Choosing between OSRM and GraphHopper is rarely about "which is better overall," but rather "which fits my exact business domain."

### You should definitely choose OSRM when:
- You are building a core **Ride-hailing application** (like Uber or Grab clones) where the routing rules for cars and motorcycles are largely static.
- You demand the absolute minimum latency (< 2ms) to ensure your mobile apps feel instantaneously responsive.
- You rely heavily on generating massive Distance Matrices (e.g., 1000x1000) every few seconds to feed into an external driver-dispatching or ETA-matching algorithm.
- You want to maximize your infrastructure ROI by running many worker processes on a single node sharing the same `mmap` memory.

### You should definitely choose GraphHopper when:
- You are architecting a complex **3PL (Third-Party Logistics) or Last-Mile Delivery** platform.
- You need to serve a highly diverse fleet (e.g., small vans, 10-ton trucks, refrigerated vehicles), each requiring unique road restrictions, height limits, and weight limits.
- You require the immense flexibility to inject dynamic priority weights per individual delivery request using Custom Models without recompiling the graph.
- Your developers are primarily familiar with the Java ecosystem and prefer an engine that is easier to extend programmatically through Java APIs rather than C++.

Both engines represent the pinnacle of open-source geospatial engineering. Evaluate your requirements against their architectural trade-offs to make the right call for your infrastructure.

## SME Field Notes: Urban Routing Realities in Ho Chi Minh City

Running a last-mile delivery fleet or ride-hailing service in high-density, rapidly growing cities like **Ho Chi Minh City (HCMC)** exposes the severe limitations of standard academic routing models. Straight-line (Euclidean) or simple Manhattan distance approximations are practically useless here.

```
                  [ Binh Thanh District ]
                            ||
                     (Saigon Bridge)
                            ||
       =================== Saigon River ===================
                            ||
                     (Thu Thiem Bridge)
                            ||
                    [ Thu Duc City ]
```

### The Saigon River Barrier
Saigon River divides the central districts (District 1, Binh Thanh, District 4) from the rapidly developing eastern urban area (Thu Duc City / old District 2). 
* A customer standing in Binh Thanh is geographically less than 800 meters from a driver located in Thu Duc City. 
* However, because they are separated by the river, the driver must travel several kilometers to cross either the **Saigon Bridge** or the **Thu Thiem Bridge**. 
* Any VRP solver that uses straight-line distance will constantly assign Thu Duc drivers to Binh Thanh orders, leading to massive delivery delays and frustrated drivers. Running a real-time routing Matrix query is mandatory to capture the true topological constraint.

### Two-Wheel (Motorcycle) vs. Four-Wheel (Truck/Car) Routing
In Vietnam, two-wheel vehicles handle over 90% of last-mile deliveries. Their routing profiles are radically different from cars:
* **One-Way Streets**: Central HCMC (District 1 and District 3) is packed with narrow, one-way roads. Motorcycles can bypass many traffic jams by navigating specific alleyway systems (hems) where cars cannot fit.
* **Turn Restrictions**: Many major intersections prohibit cars from turning left during peak hours (e.g., 06:00 - 09:00 and 16:00 - 19:00) to prevent gridlock. Motorcycles, however, are exempt from these restrictions. Custom profiles must reflect these conditional rules to prevent routing errors.
* **Alleyway (Hem) Routing**: HCMC's housing structure is dominated by deep, labyrinthine alley networks. In many cases, these alleys are narrower than 1.5 meters. The routing engine must exclude these paths when executing truck profiles, but include them for motorcycle couriers.
