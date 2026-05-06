---
title: "Part 3 — Event Streaming: The Apache Kafka & Flink Backbone"
date: 2026-05-06T20:00:00+07:00
draft: false
description: "Apache Kafka is the backbone that processes millions of events per second at Uber and Grab. Learn how to design topics, partitioning, and stream processing with Flink for real-time data."
weight: 4
---

## Why Do We Need Event Streaming?

Millions of events occur every second in a ride-hailing system:
- Driver A updates their GPS coordinates.
- Customer B opens the app and requests a ride.
- Driver C accepts a ride offer and starts moving.
- Customer D cancels a ride.
- Surge pricing updates the multiplier in the Downtown area.

If every service called each other directly (synchronous communication), the system would become **tightly coupled** and **fragile** — one slow service would bring down the entire chain. The solution is **Event Streaming**: every event is pushed into a central "pipeline," and services independently subscribe to listen to the events they care about.

---

## Apache Kafka — The Backbone

Uber processes **over one trillion messages per day** through Kafka. Grab processes hundreds of billions of messages. Kafka is chosen because of:

1. **Extremely High Throughput:** Capable of millions of messages/second on a single cluster.
2. **Durability:** Messages are written to disk and are not lost when servers restart.
3. **Ordering:** Messages within the same partition are guaranteed to remain in order (crucial for GPS timelines).
4. **Replayability:** Consumers can re-read messages from the past (useful for debugging or retraining ML models).
5. **Decoupling:** Producers and Consumers operate completely independently.

---

## Topic Design for Ride-Hailing

### Core Topics

| Topic | Producer | Consumers | Partition Key |
|---|---|---|---|
| `driver.location.updates` | Location Service | Redis GEO, Flink, Analytics | `driver_id` |
| `ride.requests` | Demand Service | Matching Engine, Pricing | `rider_id` |
| `ride.assigned` | Matching Engine | RAMEN Push, Analytics | `driver_id` |
| `ride.status.changes` | Trip Service | Billing, Analytics, Push | `trip_id` |
| `surge.pricing.updates` | Pricing Engine | API Gateway, Driver App | `h3_cell_id` |

### Partitioning Strategy — The Key to Performance

Kafka divides each topic into multiple **partitions**. Messages with the same key will always go to the same partition → ensuring order.

```
Topic: driver.location.updates (12 partitions)

driver_id = "abc123" → hash("abc123") % 12 = Partition 3
driver_id = "def456" → hash("def456") % 12 = Partition 7
driver_id = "ghi789" → hash("ghi789") % 12 = Partition 3

Partition 3: [abc123-t1] [ghi789-t1] [abc123-t2] [ghi789-t2] ...
             ↑ The sequence of GPS updates for each driver is guaranteed within the partition
```

**Why use `driver_id` as the partition key?**
- It ensures all GPS updates from the same driver go into the same partition.
- A consumer processing partition 3 will see a continuous GPS timeline for driver abc123.
- Otherwise, GPS points might arrive out of order: timestamp 10:00:03 arriving before 10:00:01.

### The Hot Partition Problem

The problem: If a popular driver (or a small, busy area) generates too many events, the partition handling it will be overloaded while other partitions remain idle.

```
The Solution: Composite Key + Salting

Instead of: key = "driver_id"
Use:        key = "driver_id" + "_" + random(0-3)

→ Events from 1 driver are spread evenly across 4 partitions.
→ Absolute ordering is lost, but each 4-second batch still has timestamps for reordering.
```

---

## Stream Processing: Apache Flink

Raw data from Kafka must be **processed, enriched, and aggregated** before downstream services can utilize it. This is the job of **Apache Flink** — a distributed stream processing framework.

### Use Case 1: Real-time Supply & Demand Counting (for Surge Pricing)

```
Flink Job: Supply-Demand Counter

Input:  Kafka topic "driver.location.updates"
        Kafka topic "ride.requests"

Sliding Window: 5 minutes, updating every 30 seconds

Logic:
  For each H3 cell (resolution 7):
    supply_count = Count the number of PRESENT drivers in the cell (status = AVAILABLE)
    demand_count = Count the number of ride requests IN THE LAST 5 mins in the cell

    supply_demand_ratio = supply_count / demand_count

Output: Kafka topic "surge.pricing.input"
        { h3_cell: "872a100d6ffffff", supply: 12, demand: 45, ratio: 0.27 }
```

### Use Case 2: ETA Enrichment

```
Flink Job: ETA Calculator

Input:  Kafka topic "ride.assigned" (contains driver_id, rider_location)
        Redis (current driver location)
        Routing Service API (calculates ETA based on traffic)

Logic:
  1. Receive "ride.assigned" event
  2. Fetch driver location from Redis
  3. Call Routing Service: ETA = f(driver_pos, rider_pos, traffic)
  4. Enrich event with ETA

Output: Kafka topic "ride.assigned.enriched"
        { trip_id, driver_id, eta_seconds: 180, route_polyline: "..." }
```

### Use Case 3: Anomaly Detection

```
Flink Job: GPS Anomaly Detector

Input: Kafka topic "driver.location.updates"

Logic:
  Stateful processing: retain the previous position of each driver
  
  Checks:
  1. Speed > 200 km/h → GPS spoofing
  2. Teleportation: moving > 5km in 4 seconds → GPS jumping
  3. Stationary > 30 continuous minutes → Driver is offline but hasn't closed the app
  
Output:
  - Flag abnormal transactions
  - Automatically switch driver state to INACTIVE
```

---

## Kafka Cluster Architecture at Uber

Uber has published their Kafka architecture in multiple technical blogs:

```
                    ┌─────────────────────────────────┐
                    │        Kafka Cluster             │
                    │                                   │
  Producers ──────► │  Topic: driver.location.updates  │ ──────► Consumers
  (Location Svc)    │    Partitions: 128                │    (Redis, Flink,
                    │    Replication Factor: 3           │     Analytics)
                    │    Retention: 72 hours             │
                    │                                   │
                    │  Topic: ride.requests              │
                    │    Partitions: 64                  │
                    │    Replication Factor: 3           │
                    │                                   │
                    │  Topic: ride.status.changes        │
                    │    Partitions: 64                  │
                    │    Replication Factor: 3           │
                    └─────────────────────────────────┘

Real-world numbers (Uber, published 2023):
  - Cluster: Tens of thousands of broker nodes
  - Throughput: Over 30 million messages/second
  - Storage: Petabytes of data
  - Topics: Tens of thousands
```

### Grab's Stack: Kafka + Flink + Apache Pinot

Grab utilizes a specific stack for Operational Analytics:

```
Kafka (Events) → Flink (Stream Processing) → Apache Pinot (Real-time OLAP)

Apache Pinot enables:
  - SQL queries over streaming data in near real-time.
  - Ops Dashboards: "How many rides were completed in the last 5 minutes in District 1?"
  - Latency: p99 < 100ms for aggregation queries.
```

---

## Consumer Group Design

### One Use Case = One Consumer Group

```
Topic: driver.location.updates

Consumer Group "redis-geo-updater"     → Updates Redis GEO (3 instances)
Consumer Group "flink-surge-calculator" → Calculates surge pricing (Flink cluster)
Consumer Group "analytics-pipeline"    → Writes to Data Lake (5 instances)
Consumer Group "fraud-detector"        → Detects fake GPS data (2 instances)

Every group reads the ENTIRE topic but processes it independently.
If fraud-detector falls behind, it does not affect the redis-geo-updater.
```

---

## Ensuring Reliability

### At-Least-Once vs Exactly-Once

| Delivery Guarantee | Meaning | Used For |
|---|---|---|
| At-Least-Once | Messages might be processed repeatedly | GPS updates (idempotent: just overwrite old location) |
| Exactly-Once | Every message is processed exactly once | Billing, Payments (can't charge twice) |

For GPS updates, **At-Least-Once** is perfectly fine because receiving the same coordinate again simply overwrites the old position in Redis — causing no harm.

For billing (calculating the cost of a ride), you absolutely must use **Exactly-Once** processing (using Kafka transactions + idempotent consumers) or design **idempotent** consumers by using the `trip_id` as a deduplication key.

> *Next, we will delve into the true brain of the system — the DISCO Matching Engine — where the decision of which driver gets which ride is made. Continue reading [Part 4 — DISCO & Matching Engine: The Ride Dispatch Algorithm](/series/ride-hailing-realtime-architecture/part-4-dispatch-matching-engine/).*
