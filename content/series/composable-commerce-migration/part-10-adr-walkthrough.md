---
title: "Part 10: ADR Walkthrough — 24 Architecture Decisions Explained"
description: "24 architecture decisions for Composable Commerce: why Dapr over Kafka, Kustomize over Helm, go-kratos over Gin, and the event-driven founding decision."
date: "2026-06-10T10:00:00+07:00"
lastmod: "2026-06-24T10:00:00+07:00"
draft: false
weight: 11
slug: "part-10-adr-walkthrough"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Architecture"]
tags: ["ADR", "Architecture Decision Records", "Dapr", "ArgoCD", "Kratos", "Golang", "Kustomize", "Microservices Architecture"]
series: ["Composable Commerce Migration"]
series_order: 10
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
cover:
  image: "images/posts/ecommerce-composable-cover.png"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-10-adr-walkthrough/"
---

21 services. 24 decisions. 3.5 months of deliberation captured in Architecture Decision Records.

An ADR (Architecture Decision Record) is a short document that answers the question: "Why did we choose X when Y and Z were also options?" Without ADRs, architectural knowledge lives in engineers' heads. When they leave, the knowledge leaves too — and the next team rewrites the same component in the way that was already tried and rejected.

This article walks through all 24 ADRs of the Composable Commerce Platform, grouped by category, with the counter-intuitive choices highlighted. Most ADRs are one-paragraph summaries; the ones that are genuinely surprising get deeper treatment.

**Answer-first:** The 24 ADRs cluster around three recurring themes: (1) **resilience over simplicity** — Dapr over raw Redis, Kustomize over Helm, outbox over in-process event dispatch; (2) **standardization over flexibility** — every service uses the same 5-layer Kratos v2 layout, the same `common` library, the same Goose migrations; (3) **explicit over implicit** — ADR-001 (event-driven) was decided 3 months before any code, ensuring every service was designed with events as a first-class constraint from day one.

## The Decision Timeline: What It Reveals

Before the decisions themselves, the timeline:

```
2025-11-17: ADR-001 — Event-Driven Architecture
            (The only decision made in 2025. 3 months before everything else.)

2026-02-03: ADR-002 through ADR-020 — 19 decisions in one day
            (This is a team alignment session, not 19 independent decisions)

2026-02-12: ADR-021 — Price & Stock Data Ownership
            (Discovered after first integration testing revealed ownership ambiguity)

2026-03-02: ADR-022, ADR-023, ADR-024 — EAV + Caching + Inventory
            (After the EAV migration spike revealed gaps in earlier decisions)
```

**ADR-001 being 3 months earlier is the most revealing fact about the platform.** The team decided on event-driven architecture in November 2025 — before they had any other decisions. "Events as first-class citizens" was the founding principle; everything else was derived from it. Dapr (ADR-003), saga pattern (Part 9), dual-write via events (Part 7), and the Transactional Outbox (Part 9) are all downstream of ADR-001.

The Feb 3 batch of 19 decisions represents an architecture alignment session where decisions made informally during design were formally documented.

## Category 1: Architecture & Design (ADR-001 to ADR-004)

### ADR-001: Event-Driven Architecture (2025-11-17)
**Decision**: Dapr Pub/Sub with Redis Streams for ALL transactional events

This is the thesis decision. The ADR establishes that every significant state change — order created, payment captured, stock reserved, customer updated — must be represented as a domain event. Services react to events, not to direct calls. Direct calls (gRPC) are allowed only for synchronous user-facing flows where latency matters.

The implication: **events are contracts, not implementation details**. Changing an event schema is a breaking change that requires all subscribers to be updated. The team committed to this discipline in November 2025.

### ADR-002: Microservices Architecture
**Decision**: 21 services across 6 bounded context groups

The ADR explicitly documents Conway's Law as a justification: *"Service count ≈ team count × 2–3."* With multiple engineering teams, 21 services is the right size. For a 5-person team, the same platform should have 5–7 services.

### ADR-003: Dapr over Raw Redis Streams
**Counter-intuitive choice.** Most Go microservices tutorials use Redis directly:

```go
// ❌ Raw Redis Streams — what most tutorials show
client := redis.NewClient(...)
client.XAdd(ctx, &redis.XAddArgs{Stream: "orders", Values: event})
```

```go
// ✅ Dapr PubSub — what the platform uses
daprClient.PublishEvent(ctx, "pubsub", "orders.order.created", payload)
```

The difference: Dapr abstracts the underlying broker. Today it's Redis Streams. Tomorrow it could be Azure Service Bus or AWS SNS — with zero code change. The `pubsub` component name in the Dapr manifest is the only thing that changes.

The risk accepted: Dapr adds a sidecar container to every pod (memory overhead ~64MB per service). For 21 services on 3-node cluster: ~1.3GB additional memory. The team accepted this cost for the portability benefit.

### ADR-004: Database Per Service
**Decision**: Each service owns its own PostgreSQL instance. No cross-service database queries.

This is what makes the EAV migration necessary (Part 5). Without database-per-service, the Catalog Service could continue querying Magento's MySQL tables directly. With it, the Catalog Service must have its own normalized schema — requiring the EAV extraction pipeline from Part 5.

The discipline: services that need data from another service's domain must either (a) call that service via gRPC or (b) maintain a local read model updated via domain events. No `JOIN` across service databases.

## Category 2: Technology Stack (ADR-005 to ADR-007)

### ADR-005: Go 1.25 + go-kratos v2
**Counter-intuitive choice.** Three Go HTTP frameworks were considered:

| Framework | Strengths | Rejected because |
|---|---|---|
| **Gin** | Fast, popular, large ecosystem | No native gRPC transport; dual HTTP+gRPC requires 2× code |
| **Echo** | Clean API, middleware chain | Same gRPC limitation as Gin |
| **go-kratos v2** | DDD convention, dual transport, Wire DI | Steeper learning curve |

Kratos won because ADR-002 mandated dual HTTP+gRPC transport for every service. With Gin or Echo, you'd write HTTP handlers AND a separate gRPC server — effectively duplicating every endpoint. Kratos makes HTTP and gRPC both first-class citizens from the same proto definition.

### ADR-006: Service Discovery with Consul
**Counter-intuitive choice.** Most Kubernetes-native platforms rely entirely on K8s DNS. The platform uses both:
- K8s DNS for same-cluster service discovery (the common case)
- Consul for cross-cluster and external service registration

Consul was chosen because the platform has a multi-datacenter future roadmap. K8s DNS doesn't span clusters. Consul's service mesh health checks are also richer than K8s liveness probes for service discovery purposes.

### ADR-007: Docker Multi-Stage + Distroless
**Decision**: Docker multi-stage builds with distroless base images for production

```dockerfile
# Two-stage: build in Go, run in distroless
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o /app/service ./cmd/order-service

FROM gcr.io/distroless/base-debian12
COPY --from=builder /app/service /service
ENTRYPOINT ["/service"]
```

Distroless images have no shell, no package manager, no `curl` — attack surface ~10× smaller than Alpine. The trade-off: debugging requires `kubectl exec` with a debug sidecar, not `bash`.

## Category 3: Deployment & Operations (ADR-008 to ADR-010)

### ADR-008: GitLab CI (not GitHub Actions)
The team was already on GitLab for code hosting. GitLab CI's reusable pipeline templates (`.gitlab-ci.yml` `include:`) allow a central DevOps team to define shared build + test + deploy pipelines that all 21 service repos inherit.

### ADR-009: ArgoCD + Kustomize (not Helm)
**Counter-intuitive choice.** Helm is the most widely adopted Kubernetes package manager. Why Kustomize?

| Aspect | Helm | Kustomize |
|---|---|---|
| **Templates** | Go templates with `{{ }}` | Strategic merge patches |
| **Complexity** | High (template functions, conditionals) | Low (YAML patches) |
| **Debugging** | `helm template` to see rendered YAML | Vanilla YAML throughout |
| **Learning curve** | Steep | Minimal (pure K8s YAML knowledge) |

For a team managing 24 services, Helm's templating complexity creates a maintenance burden. Kustomize's pure-YAML patches are readable by anyone with Kubernetes knowledge — including junior engineers who don't know Helm. The base+overlay pattern also maps cleanly to the team's environment structure (dev, staging, production).

### ADR-010: Prometheus + Grafana + Jaeger
Standard observability stack. Notable: Jaeger with OpenTelemetry instrumented at the `common/metrics` library level — all 21 services get distributed tracing for free by importing `common v1.9.5`.

## Category 4: APIs & Integration (ADR-011 to ADR-013)

### ADR-011: gRPC + REST (Dual Protocol)
The proto file generates both gRPC handlers and HTTP routes (via `google/api/annotations.proto`). No duplication. External clients get REST; internal services get gRPC. This is documented in Part 4 of this series.

### ADR-012: Elasticsearch for Search
**Decision**: Elasticsearch (not Meilisearch, Typesense, or PostgreSQL full-text)

At 10,000+ SKUs with EAV attributes and Vietnamese language support (diacritic-heavy), Elasticsearch's Vietnamese analyzer and multi-field aggregation support were decisive. The Search Service indexes products from Catalog Service events — zero direct database access.

### ADR-013: JWT + RBAC Authentication
JWT tokens issued by Auth Service, validated at the Gateway before any request reaches internal services. RBAC (not ABAC) for permission management — permissions defined at the role level (`orders:create`, `products:edit`) rather than resource level.

## Category 5: Configuration & Data (ADR-014 to ADR-015)

### ADR-014: go-kratos Config + K8s ConfigMaps
Configuration hierarchy: `configs/config.yaml` (base, committed) → K8s ConfigMap (environment-specific, not committed) → K8s Secrets (credentials, managed by Vault/SOPS).

### ADR-015: Goose for Schema Migrations
**Counter-intuitive choice.** Two alternatives rejected:

- **golang-migrate**: Popular but doesn't wrap each migration in a transaction by default. A failed migration can leave the schema in a partial state.
- **Atlas**: Automatic schema diffing (inspects DB and generates diffs). Powerful but removes explicit developer control over migration steps.

Goose wraps every migration in `BEGIN; ... COMMIT;` — if a migration fails halfway, the entire step rolls back. For an e-commerce database with financial data, atomicity is non-negotiable.

## Category 6: Frontend & Development (ADR-016 to ADR-020)

### ADR-016: React + Next.js
**Decision**: React 18 + Next.js 14 (App Router + RSC)

Next.js Server-Side Rendering is critical for SEO on the public storefront. Vietnamese e-commerce customers predominantly discover products via Google. A pure CSR (Create React App) storefront would rank poorly. The admin dashboard uses React without SSR (no SEO requirement for internal tools).

### ADR-017: Common Library Architecture
As detailed in Part 3, the `gitlab.com/ta-microservices/common v1.9.5` library eliminated 4,150 lines of duplicate code across 19 services. The key insight: *"Don't copy-paste middleware. Abstract it."*

### ADR-018: K3d + Tilt for Local Development
**Decision**: K3d (lightweight K3s in Docker) + Tilt hot reload — not Docker Compose

Docker Compose doesn't simulate Dapr sidecar injection, K8s resource limits, or ConfigMap/Secret mounting. Developers who run Compose locally and Kubernetes in staging constantly hit "it works on Compose, fails on K8s" issues. K3d local gives a complete Kubernetes environment on a laptop (8GB RAM required for all 21 services).

### ADR-019: Structured Logging with Correlation IDs
Every log line includes: `service`, `trace_id`, `correlation_id`, `user_id`, `request_id`. Correlation IDs propagate through Dapr event metadata. A single `correlation_id` can be searched in Grafana Loki to see the complete request journey across 5+ services.

### ADR-020: Error Handling & Resilience
Circuit breaker configuration (ADR-020): 5 consecutive failures → open for 60 seconds → half-open (5 test requests) → closed. Exponential backoff: 1s → 2s → 4s → 8s → 16s → give up.

## Category 7: Data & Domain (ADR-021 to ADR-024)

### ADR-021: Price & Stock Data Ownership
**Decision**: Pricing Service owns price; Warehouse Service owns stock quantity; Promotion Service applies discount rules

This addresses a common Magento architecture mistake: treating price and stock as attributes of the product. In the composable platform, they are attributes of separate business capabilities. Catalog Service knows *what* a product is. Pricing Service knows *how much* it costs. Warehouse Service knows *how many exist*.

### ADR-022: Dynamic SQL Pivoting for EAV
The foundational decision for Part 5 of this series: attribute IDs must never be hardcoded. The `eav_attribute.attribute_code` lookup pattern is the safe migration approach. This ADR was written on March 2, 2026 — after the EAV spike revealed that the team's initial extraction scripts used hardcoded IDs.

### ADR-023: Standardized Caching + Worker Patterns
The ADR that unlocked `common v1.9.5`: single-flight cache stampede protection, RedLock distributed cron, and the outbox processor standardized into the common library. Before this ADR (March 2026), each service had its own outbox implementation with slight variations.

### ADR-024: Inventory Data Ownership (17KB — The Most Debated Decision)
At 17KB, ADR-024 is 3× longer than any other ADR. Inventory data ownership was the most contested decision in the platform's design: should Catalog Service own stock levels (as in Magento, where `cataloginventory_stock_item` is a catalog table) or should Warehouse Service own them?

The decision: **Warehouse Service owns stock; Catalog Service shows a read-only stock indicator** (in_stock: true/false) populated by Warehouse Service events.

The contested alternative was "Catalog shows stock level from Warehouse via gRPC synchronous call on every product page." This was rejected because a product page load would then be gated on Warehouse Service availability — a single service failure would take down product browsing. By pre-computing `in_stock` into Catalog's own database (via events), Catalog pages are resilient to Warehouse Service failures.

## The 5 Most Counter-Intuitive Decisions

| Decision | What most engineers would choose | What was chosen | Key reason |
|---|---|---|---|
| Event messaging | Raw Redis Streams directly | Dapr abstraction layer | Broker portability |
| HTTP framework | Gin or Echo | go-kratos v2 | Native dual HTTP+gRPC transport |
| K8s config | Helm | Kustomize | Simpler, pure YAML |
| Schema migrations | golang-migrate | Goose | Atomic transaction wrapping |
| Inventory ownership | In Catalog Service | In Warehouse Service (separate) | Catalog page resilience |

## Final Word

24 decisions, all accepted, none rejected, none superseded — that's either a sign of excellent upfront design or a sign that the team hasn't been honest about retrospective rethinking. The March 2026 batch (ADR-022, 023, 024) suggests some honest retrospective happened: these decisions document gaps found during implementation, not upfront design.

The most important single decision remains ADR-001 — made 3 months before everything else. **Event-driven first** shaped the entire migration strategy: CDC with Debezium, dual-write via events, Transactional Outbox, choreography saga. Without that founding commitment, the 3-phase Strangler Fig migration documented in this series wouldn't have worked.

---

*This concludes the Composable Commerce Migration series. If you're planning a similar migration for your own Magento platform, the [series index](/series/composable-commerce-migration/) has a navigator by role — CTOs start at Part 0, Magento backend engineers start at Part 5, and Golang engineers start at Part 3.*

*Need architecture consulting for your migration? → [Book a 1:1 session](/hire/)*
