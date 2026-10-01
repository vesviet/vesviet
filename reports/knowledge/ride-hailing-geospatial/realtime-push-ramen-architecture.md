# Real-Time Driver Location Streaming: Uber Ramen WebSocket Gateway Architecture

> **Domain:** Ride-Hailing & Geospatial | **Complexity:** Level 4/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Long-Lived Connection Multiplexing`, `Epoll Event Loops`, `Presence Tracking`

---

## 1. Problem Statement & Operational Context
Streaming real-time driver coordinates to millions of active passenger apps simultaneously over HTTP polling would incinerate server infrastructure. The system requires dedicated stateful WebSocket gateway clusters.

## 2. Core Architectural Invariants
1. **Decoupled Connection Gateways:** Connection termination nodes (Ramen) hold hundreds of thousands of idle TCP sockets using Linux `epoll` without executing business logic.
2. **Spatial Pub/Sub Channel Filtering:** Clients subscribe to discrete H3 cell channels; location broadcasts are restricted strictly to relevant spatial viewports.

## 3. Agent Retrieval Guidance
- **Apply When:** Building real-time chat, live vehicle tracking, or massive broadcast push notifications.
- **Related Articles:** `/series/ride-hailing-realtime-architecture/part-6-realtime-push-ramen/`.
