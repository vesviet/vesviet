---
title: "Executive Summary — The Big Picture of Real-time Ride-Hailing Systems"
date: 2026-05-06T20:00:00+07:00
draft: false
description: "An architectural overview of ride-hailing super apps — from GPS ingestion, spatial indexing, event streaming, matching, and pricing, to real-time communication."
weight: 1
---

## The Engineering Challenge

Imagine you are an engineer at Uber or Grab. Your system must:

- **Ingest** GPS coordinates from **millions of drivers** every 4 seconds.
- **Store** and **index** all these positions in memory to query them in **under 10ms**.
- When a user requests a ride, **find and rank** the best drivers within a few kilometers, **calculate the Estimated Time of Arrival (ETA)** based on real-time traffic, and **push the ride offer to the driver's phone instantly** — all within **2 seconds**.
- Simultaneously, continuously calculate **dynamic pricing (surge pricing)** based on the supply-demand ratio in each area, updating every few seconds.

This is not a typical CRUD application. It is one of the most complex distributed systems in the world.

## Overall Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        MOBILE APPS                                │
│  Rider App ◄──── WebSocket/gRPC ────► Driver App                 │
│  (Book ride, view map)               (Receive offers, send GPS) │
└───────────────────────┬──────────────────────┬───────────────────┘
                        │                      │
                   REST/gRPC              MQTT/gRPC Stream
                        │                      │ (GPS every 4s)
┌───────────────────────▼──────────────────────▼───────────────────┐
│                      API GATEWAY + Load Balancer                  │
└───────────────────────┬──────────────────────┬───────────────────┘
                        │                      │
         ┌──────────────▼────┐    ┌────────────▼──────────────┐
         │  Demand Service   │    │  Supply/Location Service   │
         │  (Ride Requests)  │    │  (GPS Ingestion)           │
         └────────┬──────────┘    └────────────┬──────────────┘
                  │                             │
                  └──────────┬──────────────────┘
                             ▼
              ┌──────────────────────────────┐
              │     Apache Kafka             │
              │  (Event Streaming Backbone)  │
              └──────┬───────┬───────┬───────┘
                     │       │       │
           ┌─────────▼──┐ ┌─▼──────────┐ ┌──▼──────────────┐
           │ Redis GEO   │ │  DISCO     │ │ Pricing Engine  │
           │ + H3 Index  │ │  Matching  │ │ (Surge Pricing) │
           │ (Locations) │ │  Engine    │ │                 │
           └─────────────┘ └────────────┘ └─────────────────┘
                                │
                                ▼
              ┌──────────────────────────────┐
              │     RAMEN Push Service       │
              │  (gRPC/QUIC → Mobile App)    │
              └──────────────────────────────┘
```

## The Six Architectural Pillars

### 1. Location Ingestion — Optimized GPS Collection
Driver apps send coordinates every 4 seconds using ultra-lightweight protocols (MQTT, gRPC Streams). Batching techniques group multiple GPS points into a single packet to save battery and bandwidth. Noisy GPS signals are filtered using a **Kalman Filter** before processing.

### 2. Geospatial Indexing — Map Gridding
Instead of scanning the entire database, Uber divides the map into millions of **hexagons (H3)** or **squares (S2 Geometry)**. When a user requests a ride, the system only needs to search for drivers in that specific hexagon and its neighbors — reducing the search space from millions to a few dozen.

### 3. Event Streaming — The Kafka Backbone
Every event (new GPS, ride requested, ride accepted) flows through **Apache Kafka**. From Kafka, data branches out to multiple consumers: Redis GEO, Matching Engine, Pricing Engine, and Analytics Pipelines. **Apache Flink** handles real-time stream processing.

### 4. DISCO Matching Engine — Ride Dispatch
Uber's **DISCO** (Dispatch Optimization) system doesn't simply find the absolute closest driver. It utilizes **Batched Matching** — collecting requests over a few seconds and solving the **Global Assignment Problem** to minimize the overall ETA for all rider-driver pairs simultaneously.

### 5. Surge Pricing — Dynamic Pricing
The system continuously calculates the supply (available drivers) / demand (riders requesting) ratio in each H3 hexagon. When demand exceeds supply, the surge multiplier automatically increases, encouraging drivers to move to that area while filtering out non-essential demand.

### 6. RAMEN — Real-time Communication
**RAMEN** (Real-time Asynchronous Messaging Network) is Uber's push notification infrastructure. Initially using SSE (Server-Sent Events), it later migrated to **gRPC over QUIC/HTTP3** for full-duplex communication. It maintains millions of concurrent live connections, ensuring ride offers are pushed to drivers in milliseconds.

## Technology Stack Comparison

| Component | Uber | Grab | Lyft |
|---|---|---|---|
| **Geospatial Index** | H3 (in-house) | Geohash + S2 | S2 Geometry |
| **Event Bus** | Kafka | Kafka | Kafka + Flink |
| **Matching** | DISCO (Node.js + Ringpop) | Fulfilment Platform (Go) | Marketplace (Python + C++) |
| **Push System** | RAMEN (gRPC/QUIC) | WebSocket + FCM | gRPC Streams |
| **AI/ML** | ETA DeepETA, Batched Matching | DispatchGym (RL) | Map Matching + ML Residual |
| **Service Mesh** | Custom | Consul → Istio | Envoy |
| **Frameworks** | Go, Java, Node.js | Grab-Kit (Go) | Python, Go |

## Official Engineering Blog Sources

This entire series is synthesized from official technical sources:

- **Uber Engineering:** *"H3: Uber's Hexagonal Hierarchical Spatial Index"*, *"DISCO: The Brain Behind Every Driver Match"*, *"RAMEN: Real-time Asynchronous Messaging"*, *"DeepETA"*
- **Grab Engineering:** *"Grab's Fulfilment Platform Architecture"*, *"DispatchGym"*, *"From Consul to Istio"*
- **Lyft Engineering:** *"Real-time Map Matching"*, *"ETA Prediction"*

> *Begin the journey with [Part 1 — Location Ingestion: Collecting Millions of GPS Coordinates Per Second](/series/ride-hailing-realtime-architecture/part-1-location-ingestion/). We will explore why HTTP REST is insufficient and the alternative protocols used by Uber/Grab.*
