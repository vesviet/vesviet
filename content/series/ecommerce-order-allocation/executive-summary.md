---
title: "Executive Summary — The Big Picture of Order Allocation"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "An overview of the e-commerce order allocation problem — from inventory management and warehouse selection to driver allocation, cost optimization, and delivery speed."
weight: 1
---

## The Core Problem

You open Amazon, add 3 items to your cart, and click "Checkout." In a matter of milliseconds, the system must answer several complex questions simultaneously:

1. **Which warehouse should fulfill the order?** — Item A is available in New York, Chicago, and Los Angeles. Where should it be shipped from?
2. **Consolidate or Split?** — 3 items are in 3 different warehouses → ship as 3 separate packages (higher shipping cost) or transfer items internally to consolidate into 1 package (slower delivery)?
3. **Which driver delivers it?** — Driver A is near the warehouse but their van is almost full. Driver B is further away but has a spacious truck.
4. **When to deliver?** — Did the customer select 2-hour delivery, same-day, or standard (3-5 days)?

This is not a simple CRUD operation. This is a **Combinatorial Optimization** problem — specifically NP-hard — and it is arguably more complex than Uber's ride-matching algorithm.

---

## Overall Architecture

```text
┌───────────────────────────────────────────────────────────────────┐
│                      CUSTOMER                                      │
│  "Buy 3 items, deliver in 2 hours"                                │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                   ORDER MANAGEMENT SYSTEM (OMS)                   │
│                                                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐ │
│  │ Order Intake   │  │ Payment Check  │  │ Fraud Detection     │ │
│  │ (Validate)     │  │ (Authorize)    │  │ (Risk Score)        │ │
│  └───────┬────────┘  └───────┬────────┘  └─────────┬───────────┘ │
│          └───────────────────┼──────────────────────┘             │
│                              ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              ORDER ALLOCATION ENGINE                       │   │
│  │                                                             │   │
│  │  Input:                                                     │   │
│  │    - Order items (SKU, quantity, dimensions, weight)        │   │
│  │    - Customer location                                      │   │
│  │    - Delivery SLA (2h / same-day / 3-5 days)                │   │
│  │                                                             │   │
│  │  Queries:                                                   │   │
│  │    - Inventory Service → Which warehouse has stock?         │   │
│  │    - Driver Pool → Who is available? What's their capacity? │   │
│  │    - Routing Service → Cost + time for each route           │   │
│  │                                                             │   │
│  │  Output:                                                    │   │
│  │    - Fulfillment Plan: [{warehouse, items, driver, route}]  │   │
│  └───────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  Warehouse A  │ │  Warehouse B  │ │  Warehouse C  │
   │  (New York)   │ │  (Chicago)    │ │  (Los Angeles)│
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          ▼                ▼                ▼
   ┌──────────────────────────────────────────┐
   │           DRIVER POOL                     │
   │  Driver 1: capacity 50kg, at WH A        │
   │  Driver 2: capacity 30kg, currently out  │
   │  Driver 3: capacity 80kg, available at B │
   └──────────────────────┬───────────────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ CUSTOMER │
                    │ 📦 Receives│
                    └──────────┘
```

---

## The Five Pillars of the System

### 1. Order Fulfillment — The Journey from "Buy" to "Receive"
Understanding the entire lifecycle of an order: from checkout → validation → payment authorization → warehouse selection → pick & pack → driver handoff → delivery → confirmation.

### 2. Inventory Management — Real-time Stock
You cannot allocate an order if you don't know exactly how much stock is where. The inventory system must resolve: overselling, reserved stock (held for unconfirmed orders), and safety stock.

### 3. Allocation Algorithms — The Brain of the System
Three core algorithm families:
- **Assignment Problem** (Hungarian Algorithm): Optimal 1-to-1 matching.
- **Bin Packing**: Fitting multiple orders into drivers based on capacity.
- **Vehicle Routing Problem (VRP)**: Finding the optimal delivery route for multiple drivers.

### 4. Amazon CONDOR & Anticipatory Shipping
Two legendary Amazon systems:
- **CONDOR**: Continuously re-optimizing fulfillment plans within a 5-6 hour window.
- **Anticipatory Shipping**: Using ML to predict and move goods closer to customers BEFORE they even place an order.

### 5. Split Shipment & Last-Mile Delivery
Deciding whether to consolidate or split orders and optimizing last-mile delivery — the most expensive leg of the journey (accounting for 53% of total logistics costs).

---

## Comparison with Other Domains

| Characteristic | Uber Matching | Order Allocation |
|---|---|---|
| **Entities** | 1 Customer ↔ 1 Driver | N Items ↔ M Warehouses ↔ K Drivers |
| **Constraints** | Location, vehicle type | Inventory, capacity, SLA, cost |
| **Decision Time** | < 2 seconds | Milliseconds → 6 hours (CONDOR) |
| **Objective** | Minimize ETA | Minimize (cost + time), subject to SLA |
| **Problem Type** | Assignment Problem | Bin Packing + VRP + Assignment |
| **Physical Data** | None (digital matching) | Yes (inventory, weight, dimensions) |

---

## Final Hands-on Project: Mini Order Allocation Engine

In Part 6, you will build a complete order allocation system with the following conditions:
- **1 single warehouse** (simplifying warehouse selection).
- **N drivers**, each with a **min capacity** and **max capacity**.
- Each order has a distinct **capacity cost** (e.g., 3 cases of water = capacity 3, 1 smartphone = capacity 1).
- Objective: Allocate orders to drivers such that:
  - All orders are delivered.
  - No driver exceeds their max capacity.
  - Every dispatched driver meets their min capacity (to ensure the trip is profitable).
  - Total cost/time is minimized.

> *Begin the journey with [Part 1 — Order Fulfillment: From "Buy" Click to Delivery](/series/ecommerce-order-allocation/part-1-order-fulfillment-fundamentals/).*
