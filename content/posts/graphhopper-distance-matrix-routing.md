---
title: "GraphHopper vs CARTO: Order Fulfillment Routing Engine"
slug: "graphhopper-distance-matrix-routing"
date: "2026-06-01T15:05:00+07:00"
lastmod: "2026-06-01T15:05:00+07:00"
draft: false
mermaid: true
categories:
  - "Architecture"
  - "Logistics"
  - "GIS"
tags:
  - "GraphHopper"
  - "CARTO"
  - "Routing Engine"
  - "VRP"
  - "Distance Matrix"
  - "Logistics"
  - "GIS"
description: "A comparison between the GraphHopper Distance Matrix API and CARTO Spatial Analytics. A guide to building an order fulfillment routing engine (VRP)."
ShowToc: true
TocOpen: true
---

In last-mile delivery and logistics, calculating a route is not just about finding the shortest path from point A to point B. When a system needs to coordinate thousands of drivers and orders simultaneously, computational costs can explode exponentially. 

This article will compare two popular approaches: utilizing **GraphHopper** for lightning-fast **GraphHopper distance matrix calculation**, and leveraging the **CARTO Spatial Platform** (focused on spatial analysis in Cloud Data Warehouses). We will also explore how to integrate this routing data into [Real-time Surge Pricing Calculation](/posts/surge-pricing-optimization-architecture) to optimize operational costs.

---

## What is a Route Matrix and its Role in Logistics?

A **Route Matrix** is a computational table containing information about *travel time* and *distance* between multiple origins and destinations. 

If you have 10 delivery vehicles and 50 orders to deliver, the system needs to calculate a 10x50 matrix (500 route pairs) as the input for a **Vehicle Routing Problem (VRP)** algorithm. Without an accurate Distance Matrix based on the actual road network (rather than just straight-line distance), optimization algorithms will return completely unrealistic routes.

---

## Deep Dive into the GraphHopper Routing Engine

**GraphHopper** is an open-source routing engine written in Java. It is famous for its incredibly fast local routing queries based on OpenStreetMap (OSM) data.

### Lightning-Fast Distance Calculation with Contraction Hierarchies (CH)

The core strength of GraphHopper is the **Contraction Hierarchies (CH)** algorithm. CH works by pre-processing the road network graph: it identifies important "chokepoints" (e.g., highways, major roads) and creates shortcuts in memory. 

Thanks to CH, when an application calls the Matrix API for 500 point pairs, GraphHopper can return the result in a few milliseconds instead of several seconds like standard Dijkstra or A* algorithms. The trade-off is that using CH requires routing weights (such as speed limits, restricted roads) to be hardcoded during server startup, meaning they cannot be dynamically changed on a per-request basis.

> **Time-Dependent Routing:** For use cases that require dynamic weights (e.g., rush-hour traffic patterns), GraphHopper also supports the **Landmark (LM)** algorithm. LM sacrifices some speed compared to CH but allows weights to be recalculated per-request, making it suitable for scenarios where current traffic conditions must be reflected in real-time route calculations.

### Customizing Vehicle Profiles (Motorcycles, Trucks) and Speed Limits

In logistics, the travel time for a truck versus a motorcycle is vastly different. GraphHopper supports configuring multiple **Vehicle Profiles**. You can customize:
- Vehicle dimensions (avoiding low bridges or roads restricting heavy trucks).
- Speed limits on different types of roads.
- Road surfaces (avoiding dirt or unpaved roads for light trucks).

---

## Comparing the CARTO Spatial Platform Routing Solution

Unlike GraphHopper, which is a dedicated routing engine, **CARTO** is a cloud-native Spatial Analytics platform.

### CARTO Analytics Toolbox for BigQuery

Instead of managing your own servers (e.g. via a [GitOps deployment system](/posts/argo-cd-updates-2026)) and calculating distances in your application backend, CARTO allows you to execute routing functions directly inside **Google BigQuery** or **Snowflake** via the CARTO Analytics Toolbox. This solution is ideal for analyzing historical data, generating reports, and simulating macro strategies (e.g., deciding where to open a new warehouse).

### Integrating Third-Party Routing APIs (TomTom, Mapbox, HERE)

CARTO does not develop its own internal routing engine; instead, it connects directly to commercial map providers like TomTom, Mapbox, or HERE Technologies. 

**Cost and Applicability Comparison:**
- **GraphHopper (Self-Hosted):** Fixed cost (server rental), suitable for VRP systems continuously generating tens of thousands of matrix requests per minute.
- **CARTO / Commercial APIs:** Pay-per-API-call. Suitable for BI analysis, but if used for real-time route optimization, API costs can skyrocket to tens of thousands of dollars per month. A [scalable database architecture](/posts/mysql-horizontal-scaling) is also needed to cache this high volume of requests.

---

## Building an Order Fulfillment Routing Engine

To build a complete Order Fulfillment optimization system for an enterprise, you need to combine both a Routing Engine and an optimization algorithm.

### Using Matrix API Results as Input for VRP Solvers

The standard architecture of a VRP system:
1. **Order Intake:** Collect the list of driver locations and delivery coordinates.
2. **Call Matrix API:** The backend system sends the list of coordinates to GraphHopper. GraphHopper returns the time and distance matrix.
3. **Run VRP Solver:** The system feeds this matrix into an optimization library (e.g., Google OR-Tools, Jsprit). OR-Tools uses heuristics/meta-heuristics to allocate orders to drivers in a way that minimizes total time and cost.
4. **Dispatch:** Send the exact routes to the drivers' mobile devices.

### RAM Considerations when Self-Hosting GraphHopper with OpenStreetMap (OSM) Data

Self-hosting GraphHopper brings massive financial benefits, but you must clearly understand the infrastructure risks. 

GraphHopper loads the entire road network graph into RAM (In-Memory Routing) to guarantee speed. 
- A small city map might only consume a few hundred MB of RAM.
- A nationwide map (e.g., Vietnam) can consume **4-8 GB of RAM**.
- A global map requires servers with **tens or even hundreds of GB of RAM** to process smoothly with the CH algorithm.

You should divide the map (Bounding Box) according to your business operation areas (e.g., only load maps for Hanoi and HCMC) to optimize cloud server costs.

---

## Conclusion

The choice between GraphHopper and CARTO depends entirely on the use case. If your system needs macro spatial analysis, CARTO is the perfect choice. But for Dispatch and Fulfillment systems that require **real-time Distance Matrices at minimal cost**, self-hosting GraphHopper on Kubernetes is the most optimal architectural strategy.
