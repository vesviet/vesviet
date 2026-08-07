---
title: "Uber RAMEN Architecture: Real-Time Push Messaging"
slug: "part-6-realtime-push-ramen"
date: "2026-05-06T20:00:00+07:00"
lastmod: "2026-07-26T20:00:00+07:00"
draft: false
description: "How Uber pushes ride offers to millions of drivers in <100ms via RAMEN: gRPC over QUIC, Apache Helix sharding, and Cassandra+Redis at-least-once delivery."
weight: 7
cover:
  image: "/images/posts/real-time-ride-hailing-cover.jpg"
  alt: "Real-Time Ride-Hailing Architecture series: Uber and Grab — matching, GPS, WebSocket at scale"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/ride-hailing-realtime-architecture/part-6-realtime-push-ramen/"
ShowToc: true
TocOpen: true
image: "/images/posts/real-time-ride-hailing-cover.jpg"
---

> **Prerequisite:** Familiarity with the concepts introduced in [Part 5 — Pricing Surge Engine](/series/ride-hailing-realtime-architecture/part-5-pricing-surge-engine/). Review it first if the terminology in this part is unfamiliar.

**Answer-first:** Scaling real-time dispatch pushes requires a stateful WebSocket gateway layer that maintains millions of persistent TCP connections. Terminating mTLS at high-performance reverse proxies (Envoy) and tracking socket locations in a distributed Redis connection registry allows backend dispatchers to push targeted ride offers under 10ms.

## The Problem: Pushing Instant Notifications to Millions of Devices

When DISCO decides to match a rider with a driver, the system must:
1. Send the ride offer to **exactly** the target driver's phone out of millions of connected devices.
2. Deliver the notification within **milliseconds** to preserve dispatcher responsiveness.
3. Ensure the driver receives the payload even over unstable cellular connections.
4. Stream live driver location updates back to the rider app in real-time.

There are two main transport patterns: **Polling** (asking continuously) and **Push** (proactively streaming).

---

## Polling vs. Push

### Polling (The Old Way — Inefficient)

The following text diagram illustrates the high request frequency and latency delays inherent in client-side polling:

```
The Driver App asks the server every 3 seconds: "Do you have any rides for me?"

GET /api/v1/offers?driver_id=abc123
→ Response: { "offers": [] }  ← Nothing here

GET /api/v1/offers?driver_id=abc123  (3 seconds later)
→ Response: { "offers": [] }  ← Still nothing

GET /api/v1/offers?driver_id=abc123  (3 seconds later)
→ Response: { "offers": [...] }  ← Got a ride! But it's already 0-3 seconds delayed

The Issues:
  - 5 million drivers × 1 request/3s = 1.67 million requests/second (just asking)
  - 99% of requests return empty → Massive waste of server resources
  - Latency of 0-3 seconds → Another driver might accept the ride first
  - Battery drain: the radio chip must be constantly active
```

### Push (RAMEN — Efficient)

The following text diagram demonstrates the persistent stream architecture and lower latency of push-based delivery:

```
The server maintains an OPEN connection with every driver app.
When a ride offer is ready, the server PROACTIVELY pushes it down instantly.

Driver App ◄═══ gRPC Stream (live connection) ═══► RAMEN Server

Advantages:
  - Latency: < 100ms (near-instantaneous)
  - No wasted empty requests
  - The radio chip is only active when there's actual data to receive
  - Significant battery savings
```

---

## RAMEN — Real-time Asynchronous Messaging Network

**RAMEN** is the push messaging infrastructure built in-house by Uber. It maintains millions of concurrent persistent connections to push real-time data to rider and driver apps.

### Three-Tier Architecture

The architecture diagram below illustrates RAMEN's three-tier push infrastructure, separating decision evaluation (Fireball), payload serialization (API Gateway), and socket delivery (RAMEN Server):

```
┌────────────────────────────────────────────────────────────┐
│                     RAMEN Architecture                     │
│                                                            │
│  ┌──────────────────┐                                     │
│  │  Fireball Service│  "When to push?"                   │
│  │  (Decision Engine│  • Consumes Kafka events            │
│  │                  │  • Evaluates business rules         │
│  │                  │  • Handles priority, localization   │
│  └────────┬─────────┘                                     │
│           │                                                │
│           ▼                                                │
│  │  API Gateway     │  "What to push?"                   │
│  │  (Payload Builder│  • Aggregates data from services    │
│  │                  │  • Builds message payloads          │
│  │                  │  • Serializes (Protobuf)            │
│  └────────┬─────────┘                                     │
│  │  RAMEN Server    │  "How to push?"                    │
│  │  (Delivery Layer)│  • Manages millions of connections  │
│  │                  │  • Routes to the correct device     │
│  │                  │  • Guarantees at-least-once delivery│
│  └──────────────────┘                                     │
│     Mobile Devices (Millions)                              │
└────────────────────────────────────────────────────────────┘
```

---

## The Evolution of the Transport Protocol

### Generation 1: Server-Sent Events (SSE) over HTTP/1.1

The text diagram below outlines the unidirectional transport flow of Server-Sent Events over HTTP/1.1 connections:

```
Client ──── HTTP/1.1 Connection ────► RAMEN Server
       ◄═══ SSE (Server → Client only) ═══
```

### Generation 2: gRPC over QUIC / HTTP/3 (Current 2026 Standard)

In 2026 architectures, gRPC streaming operates over **HTTP/3 QUIC**, utilizing 64-bit Connection IDs for uninterrupted network migration (4G $\leftrightarrow$ 5G $\leftrightarrow$ Wi-Fi) without dropping sockets.

---

## Production Go Push Gateway & Connection Registry

The following Go program implements a concurrent WebSocket/gRPC push gateway server that tracks active client socket connections in a thread-safe registry, executes 30-second ping-pong heartbeats, and dispatches real-time push payloads.

```go
package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"
)

// PushMessage represents a real-time dispatch notification payload.
type PushMessage struct {
	TripID    string    `json:"trip_id"`
	DriverID  string    `json:"driver_id"`
	Payload   string    `json:"payload"`
	Timestamp time.Time `json:"timestamp"`
}

// ClientSession manages an active WebSocket/gRPC socket connection.
type ClientSession struct {
	DriverID string
	NodeID   string
	LastPing time.Time
	SendChan chan PushMessage
	IsActive bool
}

// PushGatewayRegistry maintains an in-memory directory of stateful client sockets.
type PushGatewayRegistry struct {
	nodeID   string
	sessions map[string]*ClientSession
	mu       sync.RWMutex
}

func NewPushGatewayRegistry(nodeID string) *PushGatewayRegistry {
	return &PushGatewayRegistry{
		nodeID:   nodeID,
		sessions: make(map[string]*ClientSession),
	}
}

func (pgr *PushGatewayRegistry) RegisterClient(driverID string) *ClientSession {
	pgr.mu.Lock()
	defer pgr.mu.Unlock()

	session := &ClientSession{
		DriverID: driverID,
		NodeID:   pgr.nodeID,
		LastPing: time.Now(),
		SendChan: make(chan PushMessage, 100),
		IsActive: true,
	}
	pgr.sessions[driverID] = session
	log.Printf("[Push Gateway %s] Connected driver: %s", pgr.nodeID, driverID)
	return session
}

func (pgr *PushGatewayRegistry) DispatchPush(driverID string, msg PushMessage) bool {
	pgr.mu.RLock()
	session, exists := pgr.sessions[driverID]
	pgr.mu.RUnlock()

	if !exists || !session.IsActive {
		log.Printf("[Push Gateway %s] Driver %s offline. Triggering APNs/FCM fallback.", pgr.nodeID, driverID)
		return false
	}

	select {
	case session.SendChan <- msg:
		log.Printf("[Push Gateway %s] Delivered push payload to driver %s (Trip: %s)", pgr.nodeID, driverID, msg.TripID)
		return true
	default:
		log.Printf("[Push Gateway %s] Client buffer full for driver %s. Triggering APNs fallback.", pgr.nodeID, driverID)
		return false
	}
}

func main() {
	gateway := NewPushGatewayRegistry("gateway-node-01")
	session := gateway.RegisterClient("drv_99210")

	// Simulate receiving a dispatch push message
	msg := PushMessage{
		TripID:    "trip_77812",
		DriverID:  "drv_99210",
		Payload:   "New Ride Offer: Downtown -> Airport ($25.00)",
		Timestamp: time.Now(),
	}

	go func() {
		received := <-session.SendChan
		fmt.Printf("--> Mobile Client Received: %s\n", received.Payload)
	}()

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	if !gateway.DispatchPush("drv_99210", msg) {
		log.Println("Fallback triggered")
	}
	<-ctx.Done()
}
```

---

## Scalability: Managing Millions of Connections

The infrastructure diagram below illustrates cluster topology sharding across RAMEN server nodes managed via Apache Helix and ZooKeeper consensus:

```
RAMEN Cluster Management:

ZooKeeper: Stores topology metadata (which servers are alive?)
Apache Helix: Manages sharding and automatic rebalancing

User UUID "abc123" → hash() → Shard 42 → RAMEN Server #7
User UUID "def456" → hash() → Shard 18 → RAMEN Server #3

If server #7 fails:
  1. Helix detects node loss (heartbeat timeout)
  2. Helix reassigns Shard 42 to server #9
  3. Client "abc123" reconnects via load balancer to server #9
  4. Telemetry stream continues without dropping state
```

---

## Ensuring Reliability: Persistence & Fallbacks

The block diagram below traces message persistence through Redis caches and Cassandra stores for at-least-once push guarantees:

```
Persistence Layer:

  Cassandra (Durable Storage)     Redis (In-Memory Cache)
  ┌────────────────────┐         ┌────────────────────┐
  │ Source of truth    │         │ Absorb traffic     │
  │ Stores messages    │◄───────│ bursts             │
  │ permanently for    │         │ Thundering herd    │
  │ retries            │         │ protection         │
  └────────────────────┘         └────────────────────┘
```

### APNs / FCM Background Fallback

When a driver app is pushed to the background by the operating system, the gRPC stream terminates. In this scenario, RAMEN fallbacks to compact Silent Push Notifications (< 4KB binary payload) via Apple APNs or Google FCM v1 to wake up the handset app.

---

## Summary of the End-to-End Real-Time Pipeline

The sequence diagram below traces the end-to-end data trajectory from driver location pings to Kafka streaming, Redis spatial indexing, DISCO bipartite matching, and RAMEN push notification:

```
 THE COMPLETE REAL-TIME PIPELINE:

 ① Driver moves
    → GPS Sensor → Kalman Filter → Batches 3 points
    → gRPC Stream → Load Balancer → Location Service

 ② Location Service
    → Converts GPS → H3 Index
    → Produces to Kafka "driver.location.updates"

 ③ Kafka → Consumers:
    ├── Redis GEO (updates driver's location)
    ├── Flink (calculates supply-demand → Surge Pricing)
    └── Analytics Pipeline (Data Lake)

 ④ Rider requests a car
    → Demand Service → Kafka "ride.requests"

 ⑤ DISCO Matching Engine
    → Queries Redis (finds nearby drivers)
    → Routing Service (calculates actual ETA)
    → Hungarian Algorithm (batched matching)
    → Selects the optimal driver

 ⑥ RAMEN Push
    → Fireball (decision) → API Gateway (payload)
    → RAMEN Server → gRPC Stream → Driver Phone
    → "You have a new ride request!"

 ⑦ Driver accepts
    → Trip Service → Kafka "ride.status.changes"
    → RAMEN Push → Rider App: "Your driver is on the way!"
    → Location stream starts pushing driver's position to the Rider App
    → Car moves smoothly on the map 🚗

 Total elapsed time: < 2 seconds
```

---

## Frequently Asked Questions (FAQ)

This FAQ addresses key push messaging topics: gRPC/QUIC transport advantages, stateful connection routing, thundering herd prevention, and background push fallbacks.

{{< faq q="Why are persistent gRPC/QUIC streams preferred over HTTP long polling for mobile push notifications?" >}}
gRPC over HTTP/3 QUIC provides full-duplex, multiplexed binary streaming with minimal header overhead, delivering push notifications in under 10ms. HTTP long polling requires continuous connection handshake loops and heavy text headers, causing high CPU load on servers and rapidly draining mobile device battery life.
{{< /faq >}}

{{< faq q="How do push gateways route messages to stateful client socket connections?" >}}
Push gateways maintain a distributed connection registry in Redis (`driver:session -> gateway_node_id`). When a dispatch service needs to send a ride offer to a specific driver, it queries the registry to identify the exact gateway node holding the active socket connection and routes the payload directly to that server.
{{< /faq >}}

{{< faq q="How does RAMEN prevent thundering herd reconnection storms during server restarts?" >}}
When a gateway node initiates a graceful shutdown, it sends a disconnect signal to connected clients containing a randomized backoff hint (e.g., between 1 and 30 seconds). Mobile clients stagger their reconnection attempts according to their assigned backoff delay, distributing traffic evenly across remaining cluster nodes.
{{< /faq >}}

---

## Official Reference Sources

| Source | Content |
|---|---|
| [Uber Eng: H3 Hexagonal Index](https://eng.uber.com/h3/) | Hexagonal gridding algorithm |
| [Uber Eng: RAMEN](https://eng.uber.com/real-time-push-platform/) | Push messaging architecture |
| [Uber Eng: DISCO](https://eng.uber.com/disco/) | Matching Engine |
| [Uber Eng: DeepETA](https://eng.uber.com/deepeta/) | ML model for ETA prediction |
| [Grab Eng: Fulfilment Platform](https://engineering.grab.com/) | Dispatch platform architecture |
| [Grab Eng: DispatchGym](https://engineering.grab.com/) | RL framework for dispatch |
| [Lyft Eng: Real-time Map Matching](https://eng.lyft.com/) | Kalman Filters & Map Matching |
| [H3 Documentation](https://h3geo.org/) | API reference for H3 |
| [Google S2 Geometry](https://s2geometry.io/) | API reference for S2 |

> *Congratulations on completing the series! You now thoroughly understand every architectural layer behind that smoothly moving car on your map. From the GPS sensor → Kalman Filter → Kafka → H3 → DISCO → RAMEN → Your App. **Every layer represents a fascinating distributed engineering challenge.***

Return to the [Real-Time Ride-Hailing Architecture series hub](/series/ride-hailing-realtime-architecture/) to revisit the full location, matching, and dispatch flow.

---

{{< author-cta >}}

🔗 **Next Step:** You have reached the final part of this series. Revisit the series index at [/series/ride-hailing-realtime-architecture/](/series/ride-hailing-realtime-architecture/) or explore other series linked below.
