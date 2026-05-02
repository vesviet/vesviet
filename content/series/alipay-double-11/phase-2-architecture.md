---
title: "Phase 2: Core Architecture (LDC, Unitization, Multi-Active)"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Core architecture concepts behind Alipay Double 11 scalability: LDC/unitization, multi-active design, the database layer (OceanBase), messaging, and reliability patterns."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/phase-1-timeline/) • [Next →](/series/alipay-double-11/phase-3-operations/)

This phase focuses on the *architecture* that enables peak scale while preserving correctness and operational control.

## 2.1 LDC and Unitization (Cell Architecture)

### The core idea: a “unit”

A **unit** is a self-contained slice of the system that can handle end-to-end business flows for a subset of users/traffic.

- **Complete in services**: the unit has the full set of required services.
- **Partial in data**: data is sharded so each unit owns a subset (e.g., by user-id range).

The key goal is **horizontal scaling with isolation**: add units to add capacity, and contain failures within a unit when possible.

### LDC zones (conceptual model)

Many descriptions of LDC are easiest to understand as three “zones”:

- **RZone (Regional / Unit Zone)**: the main workhorse units (multiple active).
- **GZone (Global)**: truly global, low-frequency shared data/control (minimize scope).
- **CZone (City / Common hot data)**: shared hot data needed frequently across units (optimize latency).

Conceptual sketch:

```
RZone 1 (Unit)     RZone 2 (Unit)     ...     RZone N (Unit)
 - services         - services                 - services
 - data shard       - data shard               - data shard
 - cache            - cache                    - cache

GZone: global coordination / config / truly shared data
CZone: shared hot data used frequently across units
```

### Why this matters

| Problem | Unitization/LDC response |
|--------|---------------------------|
| One shared core becomes a bottleneck | Split state and traffic into multiple units |
| One failure can cascade globally | Localize blast radius to a unit when possible |
| Scaling requires risky “bigger DB” moves | Scale by adding units + partitions |
| Cross-region latency and DR are hard | Multi-active by design, not an afterthought |

## 2.2 Database Layer: OceanBase (Why the DB became a pillar)

At peak scale, the database is not a component; it is a **platform**. The architectural thesis is:

- If the database cannot scale horizontally with strong correctness, the rest of the architecture becomes fragile.
- Financial systems require durable correctness under concurrency, not just throughput benchmarks.

OceanBase is often described as a distributed SQL system that:
- Partitions data into **table partitions / shards**.
- Replicates partitions across zones for high availability.
- Uses consensus to maintain correctness under failures.

The architectural implication: “scale out” becomes normal for the database, not a once-a-year emergency.

## 2.3 Messaging and Asynchronous Boundaries

Large peak systems rely on message-driven decoupling:
- **Soften coupling** between services during spikes.
- **Buffer** bursty workloads.
- Enable **degrade** strategies: keep the core payment path clean while deferring non-critical work.

At this scale, messaging is typically treated as a reliability layer:
- Clear topic/event naming and contracts.
- Back-pressure and throttling strategies.
- Retries, DLQs, and idempotency by design.

## 2.4 Reliability Patterns (What keeps peaks boring)

Regardless of the exact implementation, the patterns are recognizable in most peak systems:

- **Multi-active**: multiple active regions/cells; avoid single-region dependency.
- **Traffic routing**: route requests to the correct unit; enforce locality.
- **Circuit breakers / throttling / degradation**: preserve the payment core by shedding optional load.
- **Isolation by design**: separate critical paths from non-critical paths.
- **Operational determinism**: everything above is validated via full-link testing (Phase 3).

## 2.5 Cloud-native evolution (architecture → efficiency)

Once the architecture supports horizontal scaling and isolation, cloud-native adoption can improve:
- Elastic capacity (shorter provisioning windows).
- Operational automation (repeatable environments and deploys).
- Cost per transaction (efficiency becomes measurable and improvable).

## Key Takeaways

1. **Unitization is the scaling unlock**: it turns vertical ceilings into horizontal growth.
2. **The database must be designed for peak correctness**: correctness and durability are part of the product.
3. **Messaging is a reliability primitive**: it’s not only “async,” it’s peak control.
4. **Architecture only works when operations are deterministic**: that’s Phase 3.
