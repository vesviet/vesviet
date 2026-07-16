---
title: "Uber RAMEN: Real-Time Push to Millions of Devices"
slug: "part-6-realtime-push-ramen"
date: "2026-05-06T20:00:00+07:00"
lastmod: "2026-06-11T20:00:00+07:00"
draft: false
description: "How Uber pushes ride offers to millions of drivers in <100ms via RAMEN: gRPC over QUIC, Apache Helix sharding, and Cassandra+Redis at-least-once delivery."
weight: 7
cover:
  image: "images/posts/real-time-ride-hailing-cover.png"
  alt: "Real-Time Ride-Hailing Architecture series: Uber and Grab — matching, GPS, WebSocket at scale"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/ride-hailing-realtime-architecture/part-6-realtime-push-ramen/"
ShowToc: true
TocOpen: true
---

**Answer-first:** Scaling real-time dispatch pushes requires a stateful WebSocket gateway layer that maintains millions of persistent TCP connections. Terminating mTLS at high-performance reverse proxies (Envoy) and tracking socket locations in a distributed Redis connection registry allows backend dispatchers to push targeted ride offers under 10ms.

## The Problem: Pushing Instant Notifications to Millions of Devices

When DISCO decides to match you with Driver John Doe, the system must:
1. Send the ride offer to **exactly** John Doe's phone (out of millions of connected phones).
2. Deliver it in **milliseconds** (not seconds).
3. Ensure the driver **receives it** even if their 4G connection is weak.
4. Simultaneously push the driver's location back to your app so you can watch the car move on the map.

There are two main approaches: **Polling** (asking continuously) and **Push** (proactively sending).

---

## Polling vs. Push

### Polling (The Old Way — Inefficient)

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

```
┌────────────────────────────────────────────────────────────┐
│                     RAMEN Architecture                      │
│                                                              │
│  ┌──────────────────┐                                       │
│  │  Fireball Service │  "When to push?"                     │
│  │  (Decision Engine)│  • Consumes Kafka events              │
│  │                    │  • Evaluates business rules           │
│  │                    │  • Handles priority, localization     │
│  └────────┬─────────┘                                       │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │  API Gateway      │  "What to push?"                     │
│  │  (Payload Builder)│  • Aggregates data from services      │
│  │                    │  • Builds message payloads            │
│  │                    │  • Serializes (Protobuf)              │
│  └────────┬─────────┘                                       │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │  RAMEN Server     │  "How to push?"                      │
│  │  (Delivery Layer) │  • Manages millions of connections    │
│  │                    │  • Routes to the correct device       │
│  │                    │  • Guarantees at-least-once delivery  │
│  └──────────────────┘                                       │
│           │                                                  │
│           ▼                                                  │
│     Mobile Devices (Millions)                                │
└────────────────────────────────────────────────────────────┘
```

---

## The Evolution of the Transport Protocol

### Generation 1: Server-Sent Events (SSE) over HTTP/1.1

```
Client ──── HTTP/1.1 Connection ────► RAMEN Server
       ◄═══ SSE (Server → Client only) ═══

Characteristics:
  ✓ Simple, browser-friendly
  ✗ Unidirectional: only Server → Client
  ✗ ACK (acknowledgments) must be sent via separate HTTP POST requests (wasting connections)
  ✗ Head-of-line blocking: large messages block smaller heartbeats
  ✗ Text-based JSON: heavy payloads
```

### Generation 2: gRPC over QUIC/HTTP3 (Current)

```
Client ◄══ gRPC Bidirectional Stream ══► RAMEN Server
              (HTTP/3 + QUIC)

Characteristics:
  ✓ Full-duplex: both sides send data simultaneously on the same connection
  ✓ Binary framing (Protobuf): small payloads, low CPU usage
  ✓ Multiplexing: multiple streams on 1 connection, no head-of-line blocking
  ✓ QUIC: UDP-based, much more resilient on weak mobile networks
  ✓ ACKs sent right on the current stream (no separate connection needed)
  ✓ Connection migration: switching networks (WiFi → 4G) doesn't break the connection
```

---

## Scalability: Managing Millions of Connections

### Apache Helix + ZooKeeper

RAMEN cannot run on a single server — it requires a cluster of hundreds of servers, each holding tens of thousands of live connections.

```
RAMEN Cluster Management:

ZooKeeper: Stores topology metadata (which servers are alive?)
Apache Helix: Manages sharding and automatic rebalancing

User UUID "abc123" → hash() → Shard 42 → RAMEN Server #7
User UUID "def456" → hash() → Shard 18 → RAMEN Server #3

If server #7 dies:
  1. Helix detects it (heartbeat timeout)
  2. Helix moves Shard 42 to server #9
  3. Client "abc123" reconnects → Load Balancer → server #9
  4. Continues receiving messages seamlessly
```

### Stateful Servers — The Unique Challenge

Unlike standard REST API servers (which are stateless), RAMEN servers are **stateful** — each server holds specific TCP/gRPC sockets for specific users. Routing must be exact: a message for user "abc123" must reach the **exact server** holding that user's socket.

```
Routing Flow:

Fireball: "Push ride offer to driver abc123"
  │
  ▼
Routing Layer: hash("abc123") → Server #7
  │
  ▼
Server #7: Finds the socket for abc123 in memory → Pushes the message
```

---

## Ensuring Reliability

### At-Least-Once Delivery

Mobile networks are notoriously unreliable — 4G signals can drop for a few seconds and return. RAMEN guarantees that a message is delivered **at least once** by using:

```
Persistence Layer:

  Cassandra (Durable Storage)     Redis (In-Memory Cache)
  ┌────────────────────┐         ┌────────────────────┐
  │ Source of truth     │         │ Absorb traffic     │
  │ Stores messages    │◄───────│ bursts             │
  │ permanently for     │         │ Thundering herd    │
  │ retries             │         │ protection         │
  └────────────────────┘         └────────────────────┘

Flow:
  1. Message arrives → Written to Cassandra (backup)
  2. Cached in Redis (fast access)
  3. Pushed via gRPC stream to the device
  4. Device sends an ACK
  5. If no ACK is received within 10s → Retry from Cassandra
  6. Receives ACK → Marks as delivered
```

### Sequence Numbers — Handling Reconnects

When a client loses its connection and reconnects, how does the server know which messages it has already received?

```
Every message has an incrementing sequence number:

Server → Client:
  [seq=1] Ride offer
  [seq=2] ETA update
  [seq=3] Driver location  ← Connection lost here

Client reconnects:
  "Last received: seq=2"

Server:
  → Resends everything from seq=3 onwards (doesn't resend seq=1, seq=2)
  [seq=3] Driver location (retry)
  [seq=4] Driver location (new)
  ...
```

---

## Connection Draining — Preventing Thundering Herds

When deploying new code or scaling down a cluster, RAMEN cannot simply drop millions of connections at once — this would cause a **thundering herd** (millions of clients reconnecting simultaneously, crashing the entire system).

```
Graceful Shutdown Flow:

1. RAMEN Server #7 needs to shut down
2. Server #7 stops accepting NEW connections
3. Sends a "Graceful Disconnect" to all currently connected clients
   Message: { type: "DISCONNECT", backoff_hint_ms: random(1000, 30000) }
4. Each client receives a different backoff_hint:
   - Client A: waits 2.3 seconds, then reconnects
   - Client B: waits 15.7 seconds, then reconnects
   - Client C: waits 8.1 seconds, then reconnects
5. Reconnections are spread evenly over 30 seconds → no thundering herd
```

---

## Fallback: Silent Push Notifications

When a driver app is pushed to the background by the operating system (due to Android/iOS power management), the gRPC stream will be closed. In this scenario, RAMEN uses **Silent Push Notifications** via APNs (Apple) / FCM (Google) to "wake up" the app:

```
Primary Flow (App in foreground):
  RAMEN Server ══► gRPC Stream ══► Driver App  ✓ (< 100ms)

Fallback Flow (App in background):
  RAMEN Server ──► FCM/APNs ──► OS wakes app ──► App reconnects gRPC
                                                    (Takes 1-5 seconds)
```

---

## Grab's Approach: WebSocket + Istio

Grab didn't build a massive custom system like RAMEN; they use a simpler approach:

- **WebSockets** for real-time bidirectional communication.
- **Istio Service Mesh** manages routing, load balancing, and mTLS.
- **FCM/APNs** act as fallbacks when the app is backgrounded.

Pros: Simpler to maintain, uses open standards. Cons: WebSockets over HTTP/1.1 suffer from head-of-line blocking and aren't as robust as gRPC/QUIC on weak networks.

---

## Summary of the End-to-End Real-Time Flow

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

## WebSocket Gateway Load Balancing and Connection State Persistence

Maintaining millions of persistent TCP connections requires a highly scalable WebSocket gateway layer. The WebSocket nodes act as stateful connection terminators, streaming telemetry from mobile clients and pushing dispatch commands from backend servers.

### WebSocket Load Balancing and mTLS Termination

In a production environment, load balancing WebSocket connections differs from standard stateless HTTP traffic:
- **L4 Load Balancing (IP Hash):** Layer 4 load balancers (e.g., HAProxy or AWS NLB) distribute TCP connections based on client IP hashing. This ensures connection sticky routing, preventing reconnection storms.
- **mTLS Termination:** The WebSocket gateway terminates Mutual TLS (mTLS) to secure data transport. High-performance terminators (such as Envoy) offload cryptographic decryption using hardware-accelerated SSL modules, preventing CPU bottlenecks on app servers.

### Distributed Connection State Registries

Because clients can reside on any gateway node, the matching engine needs to know where to route push notifications. A distributed connection state registry (built on Redis or Consul) tracks client-to-gateway mapping:

```
Client (Driver:123)  ──►  WebSocket Gateway Node B  (Establishes Connection)
Gateway Node B       ──►  SADD gateway:connections:node_b "driver:123"
                          HSET driver:session "driver:123" "node_b"
```

When the dispatch engine needs to push a ride offer to `driver:123`, it queries `driver:session` in Redis, identifies `node_b` as the active connection host, and routes the message to the corresponding Node B push broker.

### Backpressure Handling and Notification Fallbacks

Stateful connections are vulnerable to network fluctuations and device sleeps:
- **Backpressure Handling:** Gateway nodes monitor client connection write buffers. If a client's network link slows down, the gateway queues non-essential telemetry and drops duplicate pings, preventing memory exhaustion.
- **APNs/FCM Fallback Loop:** If a WebSocket connection drops during dispatch matching, the gateway marks the connection dead and fallbacks to push notification systems (FCM for Android, APNs for iOS). This ensures ride offers are delivered even if the persistent socket is disconnected.

### WebSocket Connection Lifecycle and Keep-Alive (Heartbeat) Protocol Optimization

Maintaining persistent TCP connections for millions of active mobile devices requires careful optimization of the WebSocket connection lifecycle. Mobile devices frequently switch between cellular towers and Wi-Fi networks, leading to silent connection drops where the server believes the connection is active but the client is unreachable (half-open sockets).

To detect half-open sockets quickly without exhausting mobile battery life, the WebSocket gateway implements a customized keep-alive (heartbeat) protocol:
- **Ping-Pong Frames:** The gateway server sends a WebSocket Ping frame to the client every 30 seconds. The client device must respond with a Pong frame within a 5-second window. If no Pong is received, the server terminates the socket.
- **TCP Keep-Alive Fallback:** At the OS level, TCP keep-alives are configured with short probes. This ensures that dead TCP connections are cleaned up by the operating system kernel, releasing file descriptors.
- **Connection Churn and Sharding:** Under high connection churn (e.g., during a rainstorm when thousands of users open and close the app), the gateway experiences a connection storm. To prevent connection-tracking databases (such as Redis session store) from lockups, session keys are sharded using consistent hashing over multiple Redis instances. Session writes are batched in memory and flushed asynchronously.

### APNs/FCM Fallback Loop and Push Reliability

If a WebSocket connection terminates while the matching engine is attempting to dispatch a ride offer, the system initiates a fallback loop:
1. **Status Verification:** The engine queries the connection registry. If the socket is marked disconnected or if a WebSocket push fails to write to the socket buffer, the state changes to offline.
2. **Push Notification Dispatch:** The engine immediately routes the dispatch payload to the platform-specific push notification service: Apple Push Notification service (APNs) for iOS devices, or Firebase Cloud Messaging (FCM) for Android devices.
3. **Payload Optimization:** The push notification payload is minimal, containing only a secure notification token and the trip ID. The mobile client intercepts this background push, wakes up the app, and re-establishes a secure WebSocket connection to retrieve the full dispatch offer details.

### APNs/FCM Fallback Push Payload Optimization

To ensure high delivery rates under extreme conditions, the push payloads are restricted to minimal sizes. Heavy JSON payloads are avoided because APNs enforces a strict 4KB maximum payload size for HTTP/2 requests, and FCM enforces 4KB for data messages. The fallback gateway formats payloads using compact binary tokens where possible or optimized string mappings, letting the client retrieve the full JSON metadata asynchronously.

## FAQ

{{< faq q="Why are persistent WebSocket connections preferred over HTTP long polling for dispatch?" >}}
WebSockets provide low-overhead bi-directional transport, enabling sub-10ms push notifications. HTTP polling introduces latency and requires continuous connection handshake overhead, which quickly degrades mobile battery life and increases server resource use.
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

> *Congratulations on completing the series! You now deeply understand every architectural layer behind that smoothly moving car on your map. From the GPS sensor → Kalman Filter → Kafka → H3 → DISCO → RAMEN → Your App. **Every layer represents a fascinating distributed engineering challenge.***
---

{{< author-cta >}}
