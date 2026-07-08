---
title: "Part 1: Core Routing Algorithms — A* & Dijkstra Visualized"
description: "A deep dive into the core algorithms powering modern logistics. Learn why Dijkstra beats A* for Distance Matrices and how Contraction Hierarchies work."
date: "2026-06-14T22:35:00+07:00"
lastmod: "2026-06-14T22:35:00+07:00"
draft: false
tags: ["golang", "graphhopper", "routing", "algorithms"]
series: ["Routing & Geospatial Architecture"]
series_order: 1
cover:
  image: "images/posts/graphhopper-cover.png"
  alt: "Geospatial and Routing Engine Architecture series: Go and GraphHopper for production routing"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/routing-geospatial-architecture/part-1-core-algorithms/"
---

When building a high-scale logistics or delivery system, generic algorithm tutorials often lead developers astray. They tell you that A* is universally better than Dijkstra. However, in the real world of **Routing Engines** and **Distance Matrices**, the truth is much more complex.

In this first part of our masterclass, we will move beyond academic theory. We will visualize the exact lifecycle of a routing request—from snapping a GPS coordinate to the road, to bypassing traffic, and finally calculating routes in milliseconds using Contraction Hierarchies.

## Map Matching: Snapping GPS to the Graph

**Answer-first:** Before algorithms can route you, the engine must map your raw GPS coordinate to a physical road segment using **Map Matching**. Industry-standard systems use **R-Trees** (spatial bounding boxes) combined with **Hidden Markov Models (HMM)** to infer the correct road based on your trajectory.

When your phone sends a GPS ping, it might be off by 10 or 20 meters. If you are driving on a highway overpass, your raw coordinate might look like you are on the local street below.

A naive routing engine calculates the distance to every road in the city. This is computationally impossible. Instead, modern engines like Graphhopper use **R-Trees**. R-trees group road segments into Minimum Bounding Rectangles (MBRs). The engine queries the tree to find all roads within a 50-meter radius in logarithmic time.

To prevent snapping to the wrong road (like the underpass), engines use **Hidden Markov Models (HMM)** and the Viterbi algorithm. HMMs evaluate the *probability* of your path by looking at your historical trajectory and the network topology, ensuring you stay on the logical road.

## Dijkstra vs A*: The Reality for Logistics

**Answer-first:** **A*** is faster for Point-to-Point navigation (A to B) because it uses a heuristic to guide the search. However, **Dijkstra** is superior for Distance Matrix generation (1 to N) because it naturally builds a shortest-path tree to all reachable nodes simultaneously.

Academic tutorials love to praise A*. A* uses a **heuristic function $h(n)$**, usually Euclidean distance (for city routing) or Haversine distance (for global routing), to guess the remaining distance. This acts like a compass, forcing the algorithm to search aggressively toward the destination.

But logistics systems like Grab or ShopeeXpress rarely do pure Point-to-Point routing. They compute **Distance Matrices** (e.g., finding the closest 10 drivers to 1 passenger). 
If you use A* for a 1-to-10 matrix, you must run the algorithm 10 separate times. If you use **Single-Source Dijkstra**, you run it exactly *once*. Dijkstra expands outward like a ripple, finding the shortest path to every node it touches. The search stops the moment the 10th driver is found, making it exponentially cheaper for matrix calculations.

## Edge-Based Graphs and Turn Restrictions

**Answer-first:** To handle real-world rules like "No U-Turns" or "No Left Turns," routing engines convert Node-based graphs into **Edge-Based graphs**. This allows the algorithm to track the transition state between two specific road segments.

Standard graph theory treats intersections as nodes and roads as edges. But what happens if an intersection forbids left turns? In a node-based graph, the algorithm only knows it reached the node; it forgets which road it came from. 

Routing engines solve this by making the *roads* the nodes, and the *turns* the edges. This is called an **Edge-Based Graph**. When the algorithm evaluates a turn, it checks an internal penalty table. If a left turn is forbidden, the transition cost is set to infinity, forcing the route to go straight. This is also why you sometimes see "zigzag" routes on grid cities if the engine applies heavy penalties to left turns across traffic.

## Time-Dependent Routing for Real-time Traffic

**Answer-first:** Classical algorithms assume static distances. **Time-Dependent Dijkstra (TDD)** dynamically updates the weight of an edge $w(u,v,t)$ based on the vehicle's calculated *arrival time* $t$ at that specific intersection.

Traffic is not static. If a route takes 2 hours, the traffic at your destination will be completely different by the time you arrive. Time-Dependent routing solves this by applying the **FIFO (First-In-First-Out)** property. As the algorithm traverses the graph, it calculates the arrival time at each node and queries a time-varying speed matrix to get the true travel cost for the next segment.

## Contraction Hierarchies (CH): The Secret to Millisecond Scale

**Answer-first:** To bypass the $N^2$ scaling problem of A* and Dijkstra, modern engines use **Contraction Hierarchies (CH)**. CH pre-calculates "shortcuts" between major intersections, allowing queries to skip local roads and resolve in milliseconds.

Think of CH using the **Airport Analogy**. If you travel from Ho Chi Minh City to Hanoi, you don't drive through every local alleyway along the route. You take local roads to the airport, fly directly to the destination city, and take local roads to your hotel.

Contraction Hierarchies does exactly this mathematically:
1. **Preprocessing (The Study Phase):** The engine strips away "unimportant" local roads (cul-de-sacs) and creates direct **Shortcuts** between major highway nodes.
2. **Query Phase:** When you request a route, the engine runs a **Bidirectional Search** (forward from origin, backward from destination). The search only climbs "up" the hierarchy of important roads. 

This drops calculation times from seconds to single-digit milliseconds. However, standard CH is static. If a road closes due to an accident, the hierarchy must be rebuilt. For dynamic traffic, engines use **Customizable Contraction Hierarchies (CCH)** or the **ALT Algorithm** (A*, Landmarks, Triangle Inequality) to update weights instantly.

*Ready to put theory into practice? Head over to [Part 2: Zero to Hero Environment Setup (Docker, OSM, Golang)](/series/routing-geospatial-architecture/part-2-environment-setup/) to set up your local development environment and prepare your OpenStreetMap data.*

---

## FAQ: Routing Algorithms & Real-World Edge Cases

{{< faq q="Why does my routing engine give me weird 'zigzag' routes on a grid?" >}}
Because the heuristic in A* might be overestimating the straight-line distance, or the graph is using an Edge-based configuration to heavily penalize turn costs (e.g., making straight lines cheaper than waiting to turn left, resulting in zigzags).
{{< /faq >}}

{{< faq q="If Contraction Hierarchies (CH) is so fast, why doesn't everyone use it all the time?" >}}
Because standard CH is static. If a road closes or a severe traffic jam occurs, the entire hierarchy requires an expensive computational rebuild. High-end systems use Customizable Contraction Hierarchies (CCH) or ALT algorithms for dynamic traffic.
{{< /faq >}}

{{< faq q="How does the engine know I'm driving on a bridge and not the road underneath it?" >}}
Through Map Matching using Hidden Markov Models (HMM) and the Viterbi algorithm. It doesn't just snap to the nearest road coordinates; it evaluates your historical trajectory (transition probability) and elevation to calculate the most logical path.
{{< /faq >}}

{{< faq q="What happens if I want a route for a truck instead of a car? Do I need a whole new graph?" >}}
No. You use Weighting Profiles. The physical graph topology remains the same, but the internal cost function is swapped to heavily penalize or outright forbid edges that have low bridge clearance or vehicle weight limits.
{{< /faq >}}

{{< faq q="Does 1-to-N Dijkstra mean the server computes the shortest path for the entire map?" >}}
No. The shortest-path tree algorithm intelligently stops expanding its search radius as soon as the N-th target destination is reached, saving massive amounts of CPU compute compared to calculating the full city grid.
{{< /faq >}}
