---
title: "Part 4 — DISCO & Matching Engine: The Ride Dispatch Algorithm"
date: 2026-05-06T20:00:00+07:00
draft: false
description: "DISCO — Uber's dispatch brain — doesn't just find the closest driver. Learn about Batched Matching, Ringpop, and how the system solves the global optimal assignment problem."
weight: 5
---

## The Problem: Why Not Just Pick the Closest Driver?

The first instinct when designing a matching system is to pair every customer with their nearest driver. However, this **Greedy** approach causes massive losses at a system-wide scale:

```
Example: 3 riders (R1, R2, R3) and 3 drivers (D1, D2, D3)

Greedy Matching (closest driver):
  R1 ← D1 (ETA 2 mins)  ✓
  R2 ← D3 (ETA 8 mins)  ← D2 was "taken" by R1, even though D2 is closer to R2
  R3 ← D2 (ETA 10 mins) ← Terrible outcome

  Total ETA: 2 + 8 + 10 = 20 minutes

Optimal Matching (global optimal):
  R1 ← D2 (ETA 3 mins)
  R2 ← D1 (ETA 3 mins)
  R3 ← D3 (ETA 4 mins)

  Total ETA: 3 + 3 + 4 = 10 minutes  ← 50% better!
```

Uber refers to this problem as **Global Optimization** — finding an assignment strategy that minimizes the **total ETA of the entire system**, rather than optimizing just for individual pairs.

---

## DISCO — Dispatch Optimization

**DISCO** (Dispatch Optimization) is Uber's matching system, responsible for pairing millions of ride requests with drivers every day.

### Overall Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Rider App      │     │  Driver App      │
│  "Book Ride"    │     │  GPS, Status     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Demand Service │     │  Supply Service  │
│  (Ride Requests)│     │  (Driver Pool)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └──────────┬────────────┘
                    ▼
         ┌─────────────────────┐
         │    DISCO Engine      │
         │                     │
         │  1. Candidate Filter │ ← S2/H3 Geospatial Query
         │  2. ETA Calculator   │ ← Routing Service
         │  3. Batch Optimizer  │ ← Hungarian Algorithm
         │  4. Dispatch         │ ← RAMEN Push
         └─────────────────────┘
```

### Step 1: Candidate Filtering

When a ride request arrives, DISCO doesn't check every driver. It uses the rider's **S2 Cell ID** (or H3) to rapidly narrow down the list:

```
Input:  Rider location → S2 Cell Level 12
Action: Find all neighboring S2 cells (covering circle radius ~3km)
Query:  Redis/Memory → Retrieve list of drivers in those cells

Filters:
  ✓ Status = AVAILABLE (not currently carrying a passenger)
  ✓ Vehicle type matches (Car, Bike, SUV, etc.)
  ✓ Capacity is sufficient (if a group ride)
  ✓ Not blocked by the rider

Output: ~10-30 candidate drivers
```

### Step 2: ETA Calculation

Straight-line (crow-fly) distance is meaningless in the real world — 500m straight-line might be a 3km drive (due to bridges, intersections, or one-way streets).

```
Candidate drivers: [D1, D2, D3, D4, D5]
Rider position: R1

Routing Service calculates actual ETA based on:
  - Digitized road network graph
  - Real-time traffic data
  - One-way streets, overpasses, tunnels
  - Rush hours / historical traffic patterns

Results:
  D1: 800m crow-fly → 2.3km road → ETA 4 mins (heavy traffic)
  D2: 1.2km crow-fly → 1.5km road → ETA 3 mins (clear roads)  ← Better!
  D3: 600m crow-fly → 3.8km road → ETA 7 mins (must U-turn)
```

Uber developed **DeepETA** — a deep learning model that predicts ETA much more accurately than traditional routing engines by learning from billions of historical trips.

### Step 3: Batched Matching

This is the most crucial and complex step. Instead of processing each request individually, DISCO **batches requests** within a short time window (a few seconds) and solves the optimal assignment problem for the entire batch.

```
Batching Window: 2 seconds

Within 2 seconds, the system receives:
  Ride Requests: [R1, R2, R3, R4, R5]
  Available Drivers: [D1, D2, D3, D4, D5, D6, D7]

Build Cost Matrix (ETA between every rider-driver pair):

         D1   D2   D3   D4   D5   D6   D7
  R1  [  3    5    8    2    7    9    4  ]
  R2  [  6    2    4    7    3    5    8  ]
  R3  [  4    7    3    5    6    2    9  ]
  R4  [  8    4    6    3    5    7    2  ]
  R5  [  5    6    2    8    4    3    7  ]

The Problem: Find a 1-to-1 assignment such that the total cost is minimized.
→ Hungarian Algorithm (or Auction Algorithm)
```

### The Hungarian Algorithm

This is a classic algorithm used to solve the **Assignment Problem** with a time complexity of **O(n³)**:

```
Input: N×M Cost Matrix (N riders, M drivers, M ≥ N)
Output: Optimal 1-to-1 assignment

Optimal Results:
  R1 ← D4 (ETA 2 mins)
  R2 ← D2 (ETA 2 mins)
  R3 ← D6 (ETA 2 mins)
  R4 ← D7 (ETA 2 mins)
  R5 ← D3 (ETA 2 mins)

  Total ETA: 10 minutes (compared to a Greedy approach which might yield 20+ minutes)
```

---

## Ringpop — Distributed Coordination

DISCO runs on multiple servers. How do we ensure two different DISCO servers don't attempt to assign the exact same driver to two different riders?

Uber developed **Ringpop** — a consistent hashing library based on the **SWIM** (gossip) protocol:

```
Ringpop Hash Ring:

Server A ────── Server B ────── Server C ────── Server A
   │                │                │
   ▼                ▼                ▼
  Riders &       Riders &         Riders &
  Drivers        Drivers          Drivers
  in Zone 1      in Zone 2        in Zone 3

Each S2 Cell is hashed to a specific DISCO server.
→ All requests and drivers within the same area are processed by the SAME DISCO server.
→ No conflict during assignment.
```

**SWIM Protocol:** Every DISCO node periodically "pings" other nodes to check if they are alive. If a node goes down, the ring auto-rebalances — the S2 cells of the dead node are transferred to neighboring nodes in the ring.

---

## Fault Tolerance: State Digest

The problem: If an Uber data center goes down abruptly, will the states of all in-flight trips be lost?

Uber's clever solution: **Encrypted State Digest** — DISCO periodically pushes the trip state (encrypted) down to be stored directly on **the driver's phone**.

```
Normal Flow:
  DISCO Server ◄──── state ────► Driver Phone
  (Source of truth)               (Backup copy)

When a data center crashes:
  1. A new DISCO Server boots up
  2. Driver phones reconnect
  3. DISCO requests driver phones to send back the state digest
  4. DISCO decrypts and restores the state of all in-flight trips
  5. The system continues operating without dropping a single ride
```

---

## Grab's Approach: Fulfilment Platform + DispatchGym

Grab doesn't use DISCO, but they have an equivalent system:

### Fulfilment Platform
Initially, every vertical (ride-hailing, food delivery, express) had its own matching engine. Grab consolidated them into a unified **Fulfilment Platform** that manages dispatching for all verticals.

### DispatchGym — Reinforcement Learning
Grab developed **DispatchGym** — a framework allowing data scientists to train Reinforcement Learning (RL) models. It optimizes dispatch algorithm hyperparameters (e.g., optimal search radius, batch wait times, weight of ETA vs. driver ratings) in a simulated environment before deploying them to production.

```
DispatchGym Loop:

1. Simulated Environment (replaying historical data)
2. RL Agent chooses actions (tuning hyperparameters)
3. Environment returns rewards (e.g., total ETA drops, acceptance rate rises)
4. Agent learns and improves
5. Once reward stabilizes → Deploy to production (A/B testing)
```

---

## Key Metrics for the Matching Engine

| Metric | Meaning | Target |
|---|---|---|
| **P50/P99 Matching Latency** | Time from request received to dispatch | < 2 seconds (P99) |
| **Acceptance Rate** | % of drivers accepting when offered | > 85% |
| **ETA Accuracy** | Error margin between predicted and actual ETA | < 20% |
| **Match Rate** | % of requests successfully matched | > 95% |
| **Total Wait Time** | Total time a rider waits (rider + driver travel time) | Minimize |

> *Next, we will look into Surge Pricing — the dynamic pricing system based on real-time supply and demand ratios. Continue reading [Part 5 — Surge Pricing: Dynamic Pricing Based on Real-time Supply and Demand](/series/ride-hailing-realtime-architecture/part-5-pricing-surge-engine/).*
