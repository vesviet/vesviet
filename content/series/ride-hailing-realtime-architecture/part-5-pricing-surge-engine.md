---
title: "Part 5 — Surge Pricing: Dynamic Pricing Based on Real-time Supply and Demand"
date: 2026-05-06T20:00:00+07:00
draft: false
description: "Decoding Surge Pricing — a system that continuously monitors supply and demand in every H3 hexagon and automatically adjusts prices to balance the market within seconds."
weight: 6
---

## Why is Surge Pricing Necessary?

On New Year's Eve, during heavy rain, or at rush hour — the demand for rides skyrockets, but the number of available drivers remains unchanged. If prices were kept fixed:
- Riders wouldn't be able to book a ride because there are no available drivers.
- Drivers in other areas would have no incentive to move to the hot zones.
- The system would be overwhelmed, leading to massive wait times.

**Surge Pricing** (or Dynamic Pricing) is not merely a tool to increase revenue — it is a **marketplace equilibrium mechanism**:

```
Price increases → Two simultaneous effects:

1. SUPPLY INCREASES: Drivers see red zones (high prices) on their heatmap
                     → They move toward those areas to earn more
                     → The number of available drivers in the area increases

2. DEMAND DECREASES: Riders see high prices → Some choose to wait, take a bus,
                     or walk → The number of ride requests drops

→ Supply and demand gradually return to EQUILIBRIUM
→ Wait times are reduced for riders who truly need a car
```

---

## Surge Pricing Engine Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      DATA PIPELINE                              │
│                                                                  │
│  Kafka Topic              Flink Stream Processing                │
│  "driver.location"  ───►  ┌────────────────────┐                │
│  "ride.requests"    ───►  │  Supply-Demand      │                │
│                           │  Aggregator         │                │
│                           │  (per H3 cell,      │                │
│                           │   5-min window)     │                │
│                           └─────────┬──────────┘                │
│                                     │                            │
│                                     ▼                            │
│                           ┌────────────────────┐                │
│                           │  Pricing Engine     │                │
│                           │  (Surge Calculator) │                │
│                           └─────────┬──────────┘                │
│                                     │                            │
│                           ┌─────────▼──────────┐                │
│                           │  Redis Cache        │                │
│                           │  (Surge Multipliers) │                │
│                           └─────────┬──────────┘                │
│                                     │                            │
│                    ┌────────────────┼────────────────┐           │
│                    ▼                ▼                ▼           │
│              Rider App        Driver App       Matching Engine   │
│              (Shows price)    (Heatmap)        (Weighs cost)    │
└────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Geofencing with H3

Surge pricing is not calculated for an entire city — it is calculated for **individual H3 hexagons**. Uber uses Resolution 7 (each cell ~5 km²), which is large enough to be statistically significant but small enough to reflect hyper-local conditions.

```
Ho Chi Minh City is divided into ~200 H3 cells (Resolution 7)

Cell A (District 1 - Center): Supply=5,  Demand=30  → Surge 3.2x
Cell B (District 7 - Suburb): Supply=20, Demand=15  → Surge 1.0x (normal)
Cell C (Airport):             Supply=8,  Demand=40  → Surge 4.0x
Cell D (District 9 - Outskirts): Supply=12, Demand=3   → Surge 1.0x
```

---

## Step 2: Calculating the Surge Multiplier

### The Basic Model: Supply-Demand Ratio

```
surge_multiplier = f(demand / supply)

Where:
  supply  = Number of AVAILABLE drivers in the H3 cell (last 5 mins)
  demand  = Number of ride requests in the H3 cell (last 5 mins)

Example simple formula (illustrative):
  ratio = demand / supply

  if ratio <= 1.0:  surge = 1.0 (normal price)
  if ratio == 2.0:  surge = 1.5
  if ratio == 3.0:  surge = 2.0
  if ratio >= 5.0:  surge = 3.5 (maximum cap)
```

### Advanced Model: Machine Learning

In reality, Uber doesn't use a simple linear formula. They use **ML models** to calculate optimal prices based on a multitude of factors:

| Input Feature | Meaning |
|---|---|
| Supply count | Number of idle drivers in the cell |
| Demand count | Number of requests in a sliding window |
| Historical patterns | Supply-demand patterns by hour/day of the week |
| Weather data | Raining → demand rises, supply drops |
| Events | Large events (concerts, football games)? |
| Conversion rate | What % of riders still book at the current surge price? |
| Neighboring cells | Surge levels in adjacent cells (spillover effect) |

### The Feedback Loop — Preventing Over-Pricing

```
Continuous feedback loop:

1. Surge = 3.0x → Many riders cancel (conversion rate drops from 70% → 30%)
2. Engine realizes: price is too high, riders are abandoning
3. Lowers surge to 2.0x → Conversion rate recovers to 60%
4. Simultaneously, drivers arrive (supply increases) → ratio drops
5. Surge continues dropping to 1.5x → 1.0x

This entire process happens automatically over a few minutes.
```

---

## Step 3: The Driver Heatmap

Surge pricing doesn't just affect the cost for the rider — it generates a **Heatmap** displayed on the driver's app, guiding them to areas with high demand.

```
Heatmap Visualization:

  ┌────────────────────────────────────┐
  │                                    │
  │      🟢          🟡               │
  │            🟢         🟡          │
  │      🟢   District 7     🔴       │
  │            🟢    🟡  🔴 District 1│
  │      🟢        🟡  🔴 🔴         │
  │                   🔴              │
  │               🟡                  │
  │                                    │
  └────────────────────────────────────┘

  🟢 = 1.0x (normal, surplus of drivers)
  🟡 = 1.5-2.0x (moderate demand)
  🔴 = 2.5x+ (very high demand, great earning potential)
```

### Real-time Heatmap Updates

The heatmap is pushed to the driver app via **WebSockets** (or gRPC streams):

```
Server → WebSocket Push → Driver App

Payload every 30 seconds:
{
  "heatmap": [
    {"h3": "872a100d6ffffff", "surge": 3.2, "color": "#FF0000"},
    {"h3": "872a100d7ffffff", "surge": 1.0, "color": "#00FF00"},
    {"h3": "872a100d8ffffff", "surge": 1.8, "color": "#FFAA00"}
  ],
  "updated_at": "2026-05-06T20:30:00Z"
}
```

---

## Predictive Surge — Anticipating Demand

Uber and Grab don't just react to current surges — they **predict surges** before they happen:

```
Predictive Model:

Inputs:
  - Current time: 17:00 (rush hour approaching)
  - Day: Friday (weekend → demand rises)
  - Weather: Rain forecasted at 17:30
  - Events: Concert at the Stadium at 20:00
  - History: The last 4 Fridays also surged to 2.5x at 17:30

Output:
  - Prediction: Surge will hit 2.8x in the Stadium area at 17:30
  - Action: Send notifications to nearby drivers 15 minutes BEFORE
    "High demand expected near the Stadium soon, drive there to earn more!"
```

---

## Upfront Pricing vs. Surge Multiplier

### The Old Model: Surge Multiplier (Uber before 2017)
```
Price shown to rider: "Surge 2.5x"
Final Price = Base Fare × 2.5
Problem: Riders didn't know the total cost before getting in → Surprises, complaints
```

### The New Model: Upfront Pricing (Current Uber, Grab)
```
Shown to rider: "Price: 125,000 VND" (fixed before booking)

Price is calculated from:
  base_fare + (distance × per_km_rate) + (time × per_min_rate)
  + surge_premium
  + route_specific_adjustments (e.g., predicted traffic jams)

The rider knows the exact price upfront → Much more transparent
```

---

## Storing the Surge State

```redis
-- Redis: Stores the surge multiplier for each H3 cell
-- Key pattern: surge:{resolution}:{h3_cell_id}
-- TTL: 60 seconds (auto-expires if not updated → falls back to 1.0x)

SET surge:7:872a100d6ffffff "3.2" EX 60
SET surge:7:872a100d7ffffff "1.0" EX 60
SET surge:7:872a100d8ffffff "1.8" EX 60

-- When Rider App requests a price:
GET surge:7:872a100d6ffffff → "3.2"
-- The API Gateway uses this value to calculate the Upfront Price
```

---

## Anti-Abuse Mechanisms

| Risk | Solution |
|---|---|
| Drivers deliberately turning off apps to create artificial scarcity | Detect patterns: many drivers going offline simultaneously → flag |
| Drivers only accepting high surge rides, rejecting normal rides | Low acceptance rate → lower priority in matching algorithm |
| Extremely high surges causing massive backlash | Maximum cap (e.g., 5.0x), soft caps based on conversion rates |
| "Flickering" surge (rapidly fluctuating prices) | Smoothing: surge can only increase/decrease by a max of 0.5x every 30 seconds |

> *In the final part, we will explore RAMEN — Uber's real-time communication infrastructure, which solves the problem of pushing instant notifications to millions of devices simultaneously. Continue reading [Part 6 — RAMEN & Real-time Communication](/series/ride-hailing-realtime-architecture/part-6-realtime-push-ramen/).*
