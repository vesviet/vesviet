---
title: "GPS Ingestion at Scale: gRPC Streaming, MQTT & Kalman Filter"
slug: "part-1-location-ingestion"
date: 2026-05-06T20:00:00+07:00
lastmod: 2026-06-11T20:00:00+07:00
draft: false
description: "How Uber and Grab ingest 1.25M GPS/s from 5M drivers: gRPC streaming vs MQTT, Kalman Filter noise reduction, GPS batching, and Kafka pipeline."
weight: 2
---

## The Challenge: Millions of Drivers, Every 4 Seconds

**Answer-first:** Uber and Grab handle 1.25 million GPS write operations per second from ~5 million active drivers. HTTP REST fails at this scale due to per-request TCP+TLS handshake overhead. The solution is persistent connections (gRPC streams or MQTT) with Protobuf serialization, Kalman Filter noise reduction, and batched coordinate uploads — cutting network calls by 67% while maintaining sub-200ms end-to-end latency.

Grab has approximately **5 million drivers** operating in Southeast Asia. Uber has over **5 million drivers** globally. If every driver sends a GPS coordinate every 4 seconds, the system must receive:

```
5,000,000 drivers ÷ 4 seconds = 1,250,000 GPS packets / second
```

That is **1.25 million write operations per second** — just for location data alone, not counting other requests. Traditional HTTP REST cannot handle this load efficiently.

---

## Why is HTTP REST Unsuitable?

### Connection Overhead
Every HTTP request requires:
1. **TCP Handshake** (3-way handshake)
2. **TLS Handshake** (an additional 1-2 round trips if using HTTPS)
3. **HTTP Headers** (~200-800 bytes of overhead per request)
4. **Closing the connection** (or keep-alive timeouts)

With a GPS payload of only about **50-100 bytes** (latitude, longitude, timestamp, speed, heading), the HTTP overhead is 5-10 times larger than the actual data.

### Battery Drain
Every time a new HTTP connection is established, the phone's radio chip (4G/5G) must transition from an idle state to an active state, consuming significant energy. If a driver works 8-12 hours a day, the battery will drain rapidly.

---

## The Solution: Ultra-lightweight Protocols

### 1. MQTT (Message Queuing Telemetry Transport)

MQTT was originally designed for IoT devices with limited bandwidth and small batteries — perfect for continuous GPS tracking.

**Why MQTT is efficient:**
- **Persistent Connection:** Handshakes only once, then continuously sends coordinates without re-establishing the connection.
- **Tiny Headers:** Only 2 bytes of overhead compared to hundreds of bytes for HTTP.
- **Flexible Quality of Service (QoS):**
  - QoS 0: Fire-and-forget — suitable for GPS because a new coordinate will arrive a few seconds later anyway.
  - QoS 1: Guarantees delivery at least once.
- **Last Will and Testament (LWT):** If a driver loses connection abruptly, the MQTT broker automatically notifies the server that the driver has gone offline.

```
MQTT Data Flow:

Driver App → MQTT Publish → MQTT Broker Cluster → Kafka
  Topic: "driver/{driver_id}/location"
  Payload: {
    "lat": 10.7769,
    "lng": 106.7009,
    "ts": 1717689600,
    "speed": 35.2,
    "heading": 127,
    "accuracy": 8
  }
```

### 2. gRPC Bidirectional Streaming

Uber later transitioned to using **gRPC Streams** (and QUIC/HTTP3) instead of MQTT for many real-time data streams.

**Advantages over MQTT:**
- **Protobuf serialization:** Binary payloads are 3-10 times smaller than JSON.
- **Bidirectional:** The server can push data back (ride offers, navigation) over the same connection.
- **Flow control:** gRPC has built-in backpressure, crucial when servers are overloaded.
- **Multiplexing:** HTTP/2 allows multiple streams over a single TCP connection, avoiding head-of-line blocking.

```protobuf
// gRPC service definition for Location Streaming
service LocationService {
  // Driver sends a continuous stream of coordinates
  rpc StreamLocation(stream LocationUpdate) returns (stream ServerCommand);
}

message LocationUpdate {
  double latitude = 1;
  double longitude = 2;
  int64 timestamp_ms = 3;
  float speed_mps = 4;       // meters/second
  float heading_degrees = 5;  // direction (0-360)
  float accuracy_meters = 6;  // GPS accuracy
  string driver_id = 7;
}

message ServerCommand {
  oneof command {
    NewRideOffer ride_offer = 1;
    NavigationUpdate nav = 2;
    PingRequest ping = 3;
  }
}
```

---

## Optimization Techniques on the Mobile App

### Batching — Grouping Coordinates

Instead of sending each coordinate individually, the app batches 3-5 GPS points and sends them together:

```
Without batching:      With batching:
GPS 1 → Send          GPS 1 ─┐
GPS 2 → Send          GPS 2 ─┤ → Send 1 batch
GPS 3 → Send          GPS 3 ─┘
GPS 4 → Send          GPS 4 ─┐
GPS 5 → Send          GPS 5 ─┤ → Send 1 batch
GPS 6 → Send          GPS 6 ─┘

6 network calls        2 network calls (67% savings)
```

### Adaptive Frequency

The app doesn't need to send coordinates at a strict 4-second interval. It adjusts the frequency based on context:

| Driver State | GPS Frequency | Reason |
|---|---|---|
| Waiting for a ride (idle) | Every 15-30 seconds | Saves battery, driver isn't moving much |
| Moving to find passengers | Every 4-5 seconds | Needs updated location for matching |
| On-trip (carrying a passenger) | Every 2-3 seconds | Needs high accuracy for ETA and mapping |
| High speed (>60 km/h) | Every 1-2 seconds | Moving fast, location changes rapidly |
| Stationary (at a red light) | Paused | GPS hasn't changed, 100% savings |

### Dead Reckoning — Position Interpolation

Between receiving GPS points, the rider app uses **Dead Reckoning** (trajectory prediction) to make the car appear to move smoothly on the map:

```
Actual received GPS positions: ● (every 4 seconds)
Interpolated positions: ○ (every 100ms)

●───○───○───○───○───○───○───●───○───○───○───○───●
t=0                         t=4s                t=8s

Simple interpolation formula:
  predicted_lat = last_lat + (speed × cos(heading) × Δt)
  predicted_lng = last_lng + (speed × sin(heading) × Δt)
```

---

## Filtering GPS Noise: The Kalman Filter

GPS signals from phones are often **noisy** — especially in cities with tall buildings where signals reflect (the urban canyon effect). The result: cars on the map jump erratically or appear to drive through buildings.

### How the Kalman Filter Works

The Kalman Filter is a continuous **predict → update** algorithm:

```
Loop for every new GPS point:

1. PREDICT:
   Based on the previous position, speed, and heading,
   predict the current position using a physics model.

   predicted_position = previous_position + velocity × Δt

2. UPDATE (Correct):
   Compare the prediction with the actual received GPS point.
   Assign weights: trust the prediction more, or the GPS more?

   If GPS accuracy = 5m (accurate): trust the GPS more
   If GPS accuracy = 50m (noisy):   trust the prediction more

   final_position = weighted_average(predicted, gps_measured)
```

Lyft Engineering described in their technical blog that they use a **Marginalized Particle Filter** — a more advanced version of the Kalman Filter — which can track multiple possible trajectories simultaneously when it's uncertain which road the car is on (e.g., a main road vs. a parallel frontage road).

### Map Matching — Snapping to the Road

After filtering the noise, the system performs **Map Matching** — snapping the filtered coordinates onto a digitized road network:

```
Raw GPS (after Kalman):   Map Matched:

    ○  ○                     ●──●
   ○    ○                   ●    ●
  ○      ○   ──────►       ●      ●
   ○    ○                   ●    ●
    ○  ○                     ●──●

(Scattered coordinates)   (Snapped closely to the road)
```

---

## The Complete Location Pipeline Architecture

```
Driver Phone GPS Sensor
        │
        ▼
  ┌───────────────┐
  │  Kalman Filter │ (On the phone)
  │  + Batching    │
  └───────┬───────┘
          │ gRPC Stream / MQTT
          ▼
  ┌───────────────┐
  │  Load Balancer │ (Nginx / Envoy)
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │  Location     │ → Validate, enrich, convert to H3 index
  │  Service      │
  └───────┬───────┘
          │ Produce to Kafka
          ▼
  ┌───────────────┐
  │  Apache Kafka  │  Topic: "driver.location.updates"
  └───┬───┬───┬───┘
      │   │   │
      ▼   ▼   ▼
   Redis  Flink  Data Lake
   GEO    (Stream  (S3/HDFS
   Cache  Processing) Analytics)
```

## Real-world Numbers

| Metric | Estimated Value |
|---|---|
| Concurrent online drivers (Grab SEA) | ~1.5 million |
| Average GPS frequency | Every 4 seconds |
| Location Service Throughput | ~375,000 msg/s |
| GPS payload size (Protobuf) | ~40-60 bytes |
| Raw GPS bandwidth | ~15-22 MB/s |
| End-to-end latency (phone → Redis) | < 200ms |

> *Next, we will explore how Uber uses the H3 algorithm to divide the map into millions of hexagons and find the closest driver in the blink of an eye. Continue reading [Part 2 — Geospatial Indexing: H3, S2 Geometry & Redis GEO](/series/ride-hailing-realtime-architecture/part-2-geospatial-indexing/).*
