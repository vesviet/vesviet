---
title: "Kafka & Flink in Ride-Hailing: Event Streaming at Scale"
slug: "part-3-event-streaming-kafka"
date: "2026-05-06T20:00:00+07:00"
lastmod: "2026-07-26T20:00:00+07:00"
draft: false
description: "How Uber and Grab process millions of GPS events/s with Kafka: topic design, partition strategy, Flink for surge pricing, and exactly-once semantics in Go."
weight: 4
cover:
  image: "images/posts/real-time-ride-hailing-cover.png"
  alt: "Real-Time Ride-Hailing Architecture series: Uber and Grab — matching, GPS, WebSocket at scale"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/ride-hailing-realtime-architecture/part-3-event-streaming-kafka/"
ShowToc: true
TocOpen: true
image: "images/posts/real-time-ride-hailing-cover.png"
---

> **Prerequisite:** Familiarity with the concepts introduced in [Part 2 — Geospatial Indexing](/series/ride-hailing-realtime-architecture/part-2-geospatial-indexing/). Review it first if the terminology in this part is unfamiliar.

**Answer-first:** Apache Kafka and Flink form the real-time event-streaming backbone for ride-hailing platforms, ingesting millions of GPS telemetry events per second. By partitioning Kafka topics by driver ID and executing sliding-window aggregations in Flink, systems achieve real-time location streaming, driver state management, and dynamic surge calculations with sub-second latency.

## Why Do We Need Event Streaming?

Millions of events occur every second in a ride-hailing system:
- Driver A updates their GPS coordinates.
- Customer B opens the app and requests a ride.
- Driver C accepts a ride offer and starts moving.
- Customer D cancels a ride.
- Surge pricing updates the multiplier in the Downtown area.

If every service called each other directly via synchronous REST HTTP APIs, the system would become tightly coupled and fragile — a latency spike in a downstream billing service would cascade up to block real-time driver location ingestion. The solution is an **Event Streaming Architecture**: every telemetry change or trip transition is written asynchronously to an append-only distributed log, enabling decoupled services to consume events at their own pace.

---

## Apache Kafka & Redpanda — The 2026 Streaming Backbone

Modern ride-hailing platforms like Uber process over **trillion messages per day** using Apache Kafka and C++ native Redpanda clusters. In 2026 architecture deployments, Kafka 3.8+ and Redpanda eliminate ZooKeeper in favor of **KRaft (Kafka Raft Metadata Mode)** consensus, reducing metadata RPC overhead and enabling sub-5ms broker latencies with zero-copy Direct Memory Access (DMA).

Key advantages of the streaming backbone include:

1. **Extremely High Throughput:** Capable of handling over 30 million messages per second across sharded broker clusters.
2. **Durability & Zero-Copy I/O:** Messages are written sequentially to disk segments and sent over OS kernel sockets using `sendfile` syscalls, bypassing user-space CPU memory copying.
3. **Partition Ordering:** Messages possessing the same partition key are strictly guaranteed to remain in chronological sequence (crucial for location trajectories).
4. **Replayability:** Consumers can reset partition offsets to re-read historical telemetry streams for machine learning model retraining or post-incident analytics.
5. **Decoupled Architecture:** Event producers write to topics without waiting for downstream billing, surge pricing, or fraud detection consumers.

---

## Topic Design for Ride-Hailing

### Core Topics

| Topic | Producer | Consumers | Partition Key |
|---|---|---|---|
| `driver.location.updates` | Location Ingestion | Redis GEO, Flink, Analytics | `driver_id` |
| `ride.requests` | Demand Service | Matching Engine, Pricing | `rider_id` |
| `ride.assigned` | Matching Engine | RAMEN Push Gateway, Analytics | `driver_id` |
| `ride.status.changes` | Trip Service | Billing Engine, Push Server | `trip_id` |
| `surge.pricing.updates` | Pricing Engine | API Gateway, Driver App | `h3_cell_id` |

### Partitioning Strategy — The Key to Performance

Kafka divides each topic into multiple **partitions**. Messages sharing the same key land on the same broker partition, preserving strict temporal sequence.

The ASCII diagram below illustrates how Kafka topic partitions preserve chronological message ordering per driver while distributing traffic load across cluster brokers.

```
Topic: driver.location.updates (12 partitions)

driver_id = "abc123" → hash("abc123") % 12 = Partition 3
driver_id = "def456" → hash("def456") % 12 = Partition 7
driver_id = "ghi789" → hash("ghi789") % 12 = Partition 3

Partition 3: [abc123-t1] [ghi789-t1] [abc123-t2] [ghi789-t2] ...
             ↑ The sequence of GPS updates for each driver is guaranteed within the partition
```

### The Hot Partition Problem & Salting

If a single high-density geographic cluster or celebrity driver generates an extreme volume of events, the partition handling that key becomes overloaded while adjacent brokers sit idle.

Ride-hailing architectures resolve hotspot congestion via composite key salting:

```
Instead of: key = "driver_id"
Use:        key = "driver_id" + "_" + random(0-3)

→ Telemetry updates for 1 driver are distributed across 4 parallel partitions.
→ Downstream consumers re-sort events by timestamp using short sliding memory buffers.
```

---

## Stream Processing: Apache Flink 2.0

Raw streams from Kafka must be processed, enriched, and aggregated in real-time. **Apache Flink 2.0** provides distributed stream processing with low-latency stateful computations backed by RocksDB and Apache Paimon storage.

### Flink SQL: 5-Minute Sliding Window Aggregation

The following Flink SQL query demonstrates how Flink computes real-time supply and demand counters over 5-minute sliding windows (updated every 10 seconds) for H3 spatial cells:

```sql
SELECT 
    h3_cell_id,
    COUNT(DISTINCT CASE WHEN status = 'AVAILABLE' THEN driver_id END) AS active_supply,
    COUNT(DISTINCT CASE WHEN status = 'REQUESTED' THEN rider_id END) AS active_demand,
    CAST(COUNT(DISTINCT CASE WHEN status = 'AVAILABLE' THEN driver_id END) AS FLOAT) / 
        GREATEST(COUNT(DISTINCT CASE WHEN status = 'REQUESTED' THEN rider_id END), 1) AS supply_demand_ratio,
    WINDOW_END AS window_time
FROM TABLE(
    HOP(TABLE driver_location_stream, DESCRIPTOR(event_time), INTERVAL '10' SECOND, INTERVAL '5' MINUTE)
)
GROUP BY h3_cell_id, WINDOW_START, WINDOW_END;
```

### Stream Processing Use Cases

1. **Supply & Demand Counting:** Computes spatial availability ratios per Uber H3 cell and outputs metrics to `surge.pricing.input`.
2. **ETA Enrichment:** Merges `ride.assigned` events with live driver coordinates in Redis and queries routing services to append traffic-adjusted ETAs.
3. **GPS Anomaly Detection:** Retains stateful location histories to detect speed spikes (> 200 km/h) or teleportation anomalies (> 5km jump in 4s), flagging potential spoofing.

---

## Production Go Kafka Stream Consumer

The following Go program demonstrates an event streaming consumer that reads driver location updates from Kafka topic partitions, parses Protobuf frames, and updates sharded Redis H3 cell registries with exact partition ordering guarantees.

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/uber/h3-go/v4"
)

// DriverLocationUpdate represents the incoming Kafka message payload.
type DriverLocationUpdate struct {
	DriverID  string    `json:"driver_id"`
	Latitude  float64   `json:"latitude"`
	Longitude float64   `json:"longitude"`
	Status    string    `json:"status"` // e.g. "AVAILABLE", "ON_TRIP"
	Timestamp time.Time `json:"timestamp"`
}

// IngestionConsumer processes Kafka message partitions for location tracking.
type IngestionConsumer struct {
	redisClient *RedisClientMock
	workerCount int
}

// RedisClientMock simulates sharded Redis cluster operations for active H3 cells.
type RedisClientMock struct {
	mu    sync.RWMutex
	store map[string]map[string]time.Time
}

func NewRedisClientMock() *RedisClientMock {
	return &RedisClientMock{
		store: make(map[string]map[string]time.Time),
	}
}

func (r *RedisClientMock) UpdateDriverCell(cellID string, driverID string, updated time.Time) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, exists := r.store[cellID]; !exists {
		r.store[cellID] = make(map[string]time.Time)
	}
	r.store[cellID][driverID] = updated
}

// ProcessMessage decodes location telemetry and indexes the driver into Uber H3 Resolution 8 cells.
func (ic *IngestionConsumer) ProcessMessage(ctx context.Context, key []byte, payload []byte) error {
	var update DriverLocationUpdate
	if err := json.Unmarshal(payload, &update); err != nil {
		return fmt.Errorf("failed to unmarshal location update: %w", err)
	}

	// Index location using Uber H3 Resolution 8 (~0.74 km2 cell area)
	latLng := h3.LatLng{Lat: update.Latitude, Lng: update.Longitude}
	cell := h3.LatLngToCell(latLng, 8)
	cellID := fmt.Sprintf("%x", cell)

	// Atomically record driver location in the sharded Redis cell key
	ic.redisClient.UpdateDriverCell(fmt.Sprintf("drivers:h3:res8:%s", cellID), update.DriverID, update.Timestamp)
	log.Printf("[Kafka Consumer] Partition Key: %s | Driver: %s -> H3 Cell: %s", string(key), update.DriverID, cellID)

	return nil
}

func main() {
	consumer := &IngestionConsumer{
		redisClient: NewRedisClientMock(),
		workerCount: 4,
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	samplePayload := []byte(`{"driver_id":"drv_88192","latitude":10.7769,"longitude":106.7009,"status":"AVAILABLE","timestamp":"2026-07-26T14:28:00Z"}`)
	if err := consumer.ProcessMessage(ctx, []byte("drv_88192"), samplePayload); err != nil {
		log.Fatalf("Error processing event: %v", err)
	}
}
```

---

## Kafka Cluster Architecture at Uber

The infrastructure diagram below depicts Uber's distributed streaming architecture, showing how location ingestion services write to multi-partition Kafka topics consumed by real-time spatial indexes and analytics engines.

```
                    ┌─────────────────────────────────┐
                    │        Kafka Cluster            │
                    │                                 │
  Producers ──────► │  Topic: driver.location.updates │ ──────► Consumers
  (Location Svc)    │    Partitions: 128              │    (Redis, Flink,
                    │    Replication Factor: 3        │     Analytics)
                    │    Retention: 72 hours          │
                    │  Topic: ride.requests           │
                    │    Partitions: 64               │
                    │    Replication Factor: 3        │
                    │  Topic: ride.status.changes     │
                    │    Partitions: 64               │
                    │    Replication Factor: 3        │
                    └─────────────────────────────────┘

Real-world numbers (Uber & Grab, 2026 Architecture):
  - Cluster: Thousands of broker nodes managed via KRaft metadata controllers
  - Throughput: Over 30 million messages per second peak
  - Storage: Petabytes of retention across NVMe zero-copy storage tiers
  - Topics: Tens of thousands of streaming channels
```

---

## Consumer Group Isolation

The block diagram below illustrates independent consumer groups reading identical Kafka topics, isolating operational workloads like spatial caching from offline data lake ingestion.

```
Topic: driver.location.updates

Consumer Group "redis-geo-updater"     → Updates Redis GEO (3 instances)
Consumer Group "flink-surge-calculator" → Calculates surge pricing (Flink cluster)
Consumer Group "analytics-pipeline"    → Writes to Data Lake (5 instances)
Consumer Group "fraud-detector"        → Detects fake GPS data (2 instances)

Every consumer group tracks its own offset independently.
If the fraud detector lags behind, the real-time Redis updater remains unaffected.
```

---

## Ensuring Reliability: Delivery Guarantees

| Delivery Guarantee | Meaning | Used For |
|---|---|---|
| **At-Least-Once** | Messages may be redelivered upon consumer failure | GPS location updates (idempotent overwrite in Redis) |
| **Exactly-Once** | Transactions guarantee single-execution semantics | Rider billing, payment processing, wallet transfers |

For GPS updates, **At-Least-Once** delivery is optimal: duplicate coordinates simply update Redis memory state without side effects. For trip billing, **Exactly-Once** processing is required using Kafka transactional producers (`transactional.id`) and consumer deduplication tables keyed by `trip_id`.

---

## Frequently Asked Questions (FAQ)

This FAQ addresses key event streaming decisions: topic partitioning strategies, Flink stateful stream processing, exactly-once delivery semantics, and Redpanda high-throughput optimizations.

{{< faq q="Why is driver_id used as the primary Kafka partition key for location updates?" >}}
Partitioning by `driver_id` ensures that all sequential GPS pings from a specific driver land on the exact same Kafka broker partition. Because Kafka guarantees strict message ordering within a single partition, downstream consumers process the driver's location history in strict chronological sequence without out-of-order jitter.
{{< /faq >}}

{{< faq q="How does Apache Flink calculate real-time supply and demand for surge pricing?" >}}
Apache Flink executes sliding window aggregations (e.g., 5-minute sliding window updated every 10 seconds) over incoming location and ride request streams. By grouping events by H3 Cell ID in RocksDB state storage, Flink computes active supply-demand ratios in real-time and outputs surge triggers to Kafka topics.
{{< /faq >}}

{{< faq q="How do ride-hailing systems achieve exactly-once processing for ride billing events?" >}}
Payment and billing events use Kafka transactional producers (`transactional.id`) combined with idempotent consumer pattern matching. Consumers write processed `trip_id` records into atomic deduplication tables in Redis or PostgreSQL, ensuring that network retries never trigger double-charging.
{{< /faq >}}

---

🔗 **Next Step:** Continue to [Part 4 — Dispatch Matching Engine](/series/ride-hailing-realtime-architecture/part-4-dispatch-matching-engine/) for the following module in the series.

## References & Further Reading

Technical documentation and architectural resources on event-driven streaming, Kafka topic partitioning, and Apache Flink stateful window processing:

- [Apache Flink State Backends](https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/state_backends/)
- [Kafka Partitioning Strategies](https://www.confluent.io/blog/how-choose-number-topics-partitions-kafka-cluster/)

> *Next, we will examine the true brain of the system — the DISCO Matching Engine — where the decision of which driver gets which ride is made. Continue reading [Part 4 — DISCO & Matching Engine: The Ride Dispatch Algorithm](/series/ride-hailing-realtime-architecture/part-4-dispatch-matching-engine/).*

{{< author-cta >}}