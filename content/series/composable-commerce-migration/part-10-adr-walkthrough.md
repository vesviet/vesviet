---
title: "Part 10: ADR Walkthrough — 24 Architecture Decisions"
date: 2026-06-15T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "A recap of 24 core architecture decision records behind Composable Commerce: Dapr vs Kafka, Kustomize vs Helm, go-kratos vs Gin, Goose vs golang-migrate."
categories: ["Series", "Software Engineering", "Architecture"]
tags: ["Microservices", "Golang", "System Design"]
series: ["composable-commerce-migration"]
weight: 11
slug: "part-10-adr-walkthrough"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-10-adr-walkthrough/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 10: ADR Walkthrough — 24 Architecture Decisions"
  relative: false
keywords: ["architecture decision records", "24 adr walkthrough", "dapr vs kafka", "goose vs golang migrate"]
---

[← Previous Chapter: Part 9: Transactional Outbox & Saga Pattern](/series/composable-commerce-migration/part-9-outbox-saga/) | [Series Hub](/series/composable-commerce-migration/)

---

> **Answer-first:** A recap of the 24 Architecture Decision Records (ADRs) distilled from a real-world migration project: why Dapr was chosen over Kafka for Pub/Sub, database-per-service, Wire dependency injection, and the zero-downtime cutover strategy.

---

21 services. 24 decisions. Three and a half months of weighing options, all carefully recorded in Architecture Decision Records (ADRs).

An ADR is a short, tidy document that answers one question decisively: "Why did we commit to option X when options Y and Z looked just as good?" Without ADRs, all architectural knowledge lives fragile and undocumented in engineers' heads. The day one of them resigns, that knowledge walks out the door with them — and the new team taking over will end up dismantling and rebuilding a component in exactly the same way the previous team once eagerly tried and rejected.

This article walks you through all 24 ADRs of the Composable Commerce platform, grouped by category, with emphasis on the decisions that sound counter-intuitive. Most ADRs are only a summary paragraph long; the decisions that raise the most eyebrows get a deeper dissection.

**Answer-first:** The 24 ADRs converge on three recurring philosophies: (1) **choosing resilience over simplicity** — choosing Dapr instead of raw Redis, Kustomize instead of Helm, and the outbox pattern instead of firing events directly in-process; (2) **choosing standardization over freedom** — every service must fit the same Kratos v2 five-layer mold, share the same `common` library, and use the same Goose migrations; (3) **choosing explicitness over implicit understanding** — ADR-001 (the event-driven architecture) was signed off a full 3 months before any line of code was written, guaranteeing that every service, from day one, was forced to treat events as a first-class constraint.

## The Decision Timeline: What Does It Reveal?

Before diving into the content of the decisions, look at the timeline:

```
2025-11-17: ADR-001 — Event-Driven Architecture
            (The only standalone decision made in 2025. A full 3 months ahead of everything else.)

2026-02-03: ADR-002 through ADR-020 — 19 decisions born in a single day
            (Do not misunderstand: this was the outcome of a team-wide alignment session, not 19 casual nods)

2026-02-12: ADR-021 — Who Owns Price & Stock Data
            (Surfaced after the first integration test exposed an unclear ownership boundary)

2026-03-02: ADR-022, ADR-023, ADR-024 — EAV + Caching + Inventory
            (Emerged after the EAV migration grind revealed the gaps in earlier decisions)
```

**The fact that ADR-001 sits alone on the timeline 3 months earlier is the single most revealing detail about this platform's nature.** The team committed to an event-driven architecture back in November 2025 — before any other decision existed. "Events are first-class citizens" is the founding principle; everything else grew out of it. Dapr (ADR-003), the saga pattern (Part 9), dual-write via events (Part 7), and the Transactional Outbox (Part 9) are all downstream descendants of ADR-001.

The burst of 19 decisions on February 3 was in reality an architecture alignment session: the things teams had already informally agreed upon during design were finally put down on paper and made official.

## Group 1: Architecture & Design (ADR-001 to ADR-004)

### ADR-001: Event-Driven Architecture (2025-11-17)
**Decision**: Use Dapr Pub/Sub backed by Redis Streams for ALL transactional events

This is the thesis decision. This ADR establishes the constitutional law: every meaningful state change — an order created, a payment captured, an inventory reservation confirmed, a customer profile updated — must be expressed as a domain event. Services react to events; direct service-to-service calling is forbidden. Direct calls (gRPC) are only permitted for synchronous, user-facing flows where latency is critical.

The implication: **events are contracts, not buried implementation details**. Changing an event's schema is a breaking change, forcing all 500 subscribers to update in lockstep. The team strapped this iron discipline on back in November 2025.

### ADR-002: Microservices Architecture
**Decision**: 21 services divided into 6 bounded context groups

This ADR invokes Conway's Law quite openly: *"number of services ≈ number of teams × 2–3."* With a handful of engineering teams, 21 services is a tailored fit. Hand this platform to a 5-person team, and the right number of services would be around 5–7.

### ADR-003: Dapr Instead of Raw Redis Streams
**Counter-intuitive decision.** Most Go microservices tutorials go straight at raw Redis:

```go
// ❌ Raw Redis Streams — the style found in countless tutorials
client := redis.NewClient(...)
client.XAdd(ctx, &redis.XAddArgs{Stream: "orders", Values: event})
```

```go
// ✅ Dapr PubSub — the style this platform uses
daprClient.PublishEvent(ctx, "pubsub", "orders.order.created", payload)
```

The difference: Dapr puts an abstraction wall in front of the underlying broker. Today it is Redis Streams. Tomorrow it could become Azure Service Bus or AWS SNS — without moving a single line of code. The only thing that changes is the `pubsub` component name declared in the Dapr manifest.

The price to swallow: Dapr injects a sidecar container into every pod (costing ~64MB of RAM per service). Multiplied across 21 services on a 3-node cluster: roughly 1.3GB of RAM. The team agreed to pay this tax in exchange for portability — the freedom to run anywhere.

### ADR-004: Database-Per-Service
**Decision**: Each service owns its own PostgreSQL database. Cross-database queries are strictly forbidden.

This is the root cause that produced the sweat-drenched EAV migration saga (Part 5). Without the database-per-service rule, Catalog Service could have quietly queried Magento's legacy MySQL tables directly. Forced down this path, Catalog Service had to build its own normalized schema — which gave birth to the entire EAV extraction pipeline in Part 5.

Iron discipline: any service that covets data owned by another has exactly two options: (a) swallow its pride and make a gRPC call, or (b) maintain its own read model — a denormalized copy continuously warmed by domain events. Cross-boundary `JOIN` queries are absolutely forbidden.

## Group 2: Technology Ecosystem (ADR-005 to ADR-007)

### ADR-005: Go 1.25 + go-kratos v3
**Counter-intuitive decision.** The finals featured three Go HTTP frameworks facing off:

| Framework | Strengths | Rejected because |
|---|---|---|
| **Gin** | Fast, hugely popular, enormous ecosystem | No native gRPC transport; supporting it means writing double the code (HTTP + gRPC) |
| **Echo** | Elegant API, excellent middleware pipeline | Same missing-gRPC situation as Gin |
| **go-kratos v3** | DDD-style code layout, dual transport out of the box, Wire DI, perfect Go 1.25 compatibility | Steeper learning curve |

Kratos won decisively because ADR-002 mandated that every service speak both protocols (HTTP+gRPC). With Gin or Echo, you would implement a full set of HTTP handlers AND THEN have to build a separate gRPC server — effectively coding every endpoint twice. Kratos v3 goes further: from a single proto file, it generates both HTTP and gRPC as first-class citizens, while taking advantage of Go 1.25's automatic container-aware GOMAXPROCS optimization.

### ADR-006: Service Discovery With Consul
**Counter-intuitive decision.** Most Kubernetes-native platforms entrust their lives to K8s DNS. This platform greedily uses both:
- K8s DNS for discovering neighbors within the same cluster
- Consul for cross-cluster connections and calling external services

Consul was chosen because the platform's future roadmap includes multi-datacenter expansion. K8s DNS is blind across clusters. Consul's service mesh health checking also decisively outclasses K8s's modest liveness probes for service discovery purposes.

### ADR-007: Docker Multi-Stage + Distroless
**Decision**: Multi-stage Docker builds with a distroless base image for production

```dockerfile
# Two clear stages: build with Go, run on distroless
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o /app/service ./cmd/order-service

FROM gcr.io/distroless/base-debian12
COPY --from=builder /app/service /service
ENTRYPOINT ["/service"]
```

A distroless image is stripped bare: no shell, no package manager, no `curl` — shrinking the attack surface roughly 10x compared to Alpine. The trade-off: if you ever need to debug, you have to attach a debug sidecar via `kubectl exec`; there is no casually shelling in with `bash`.

## Group 3: Deployment & Operations (ADR-008 to ADR-010)

### ADR-008: GitLab CI (over GitHub Actions)
The team was already rooted in GitLab for code hosting. GitLab CI's reusable pipeline templates (via the `include:` keyword in `.gitlab-ci.yml`) let the central DevOps team forge polished build + test + deploy pipelines that all 21 service repos automatically inherit.

### ADR-009: ArgoCD + Kustomize (instead of Helm)
**Counter-intuitive decision.** Helm reigns as Kubernetes' package manager. Why defect to Kustomize?

| Criterion | Helm | Kustomize |
|---|---|---|
| **Templates** | Go templates littered with `{{ }}` brackets | Strategic merge patches |
| **Complexity** | High (tangled template functions, if/else conditions) | Low (well-behaved YAML patches) |
| **Debugging** | You must run `helm template` to see what YAML it produces | Pure YAML from top to bottom, right before your eyes |
| **Learning curve** | Fairly steep | Nearly flat (as long as you can read K8s YAML) |

With one team managing 24 services, Helm's templating complexity quickly becomes technical debt. Kustomize's pure-YAML patches are approachable for anyone with basic Kubernetes knowledge — including junior engineers who have never touched Helm. The base+overlay pattern also fits the team's dev, staging, production environment-splitting habits perfectly.

### ADR-010: The Prometheus + Grafana + Jaeger Trinity
A standard, uncontroversial observability stack. The nice part: Jaeger integrates with OpenTelemetry embedded deep at the `common/metrics` library level — meaning all 21 services automatically get distributed tracing for free the moment they import `common v1.9.5`.

## Group 4: API & Integration (ADR-011 to ADR-013)

### ADR-011: Both gRPC + REST (Dual Protocol)
A single proto file yields both gRPC handlers and HTTP routes (via the magic of `google/api/annotations.proto`). No duplication. External clients are welcomed with REST; internal services call gRPC for speed. This technique was laid out in detail in Part 4 of the series.

### ADR-012: Elasticsearch Guards the Search Domain
**Decision**: Use Elasticsearch (turning away Meilisearch, Typesense, and PostgreSQL's full-text tricks)

When you have to carry more than 10,000 SKUs stuffed with EAV attributes and support the Vietnamese language (a diacritic-heavy, finicky language), Elasticsearch's Vietnamese analyzer and multi-field aggregation capabilities are what seal the deal. Search Service listens to events from Catalog Service to build its indexes — never touching each other's databases.

### ADR-013: JWT + RBAC Authentication
JWT tokens are issued by the Auth Service and strictly verified at the Gateway before being allowed into the internal services. Authorization uses RBAC (no ABAC) — permissions are granted at the role level (e.g. `orders:create`, `products:edit`) rather than inspected down to the resource level.

## Group 5: Configuration & Data (ADR-014 to ADR-015)

### ADR-014: go-kratos Configuration Paired With K8s ConfigMaps
The configuration hierarchy: `configs/config.yaml` (the sensible defaults, committed to git) → K8s ConfigMap (environment-specific values, never committed) → K8s Secrets (credentials, managed by Vault/SOPS).

### ADR-015: Goose Handles All Schema Migrations
**Counter-intuitive decision.** Two formidable rivals were passed over:

- **golang-migrate**: quite popular, but it does not wrap each migration in a transaction by default. If a migration dies halfway, your schema is stuck in a partial state.
- **Atlas**: automatic analysis and diffing. Impressive, but it strips developers of explicit control over each migration step.

Goose wisely wraps every migration in a `BEGIN; ... COMMIT;` sandwich — if a migration chokes midway, it rolls back entirely. For an e-commerce database that stores money, atomicity is non-negotiable.

## Group 6: Frontend & Development (ADR-016 to ADR-020)

### ADR-016: React + Next.js
**Decision**: React 19 + Next.js 15 (App Router + RSC)

Next.js 15's Server-Side Rendering (SSR) and React Server Components (RSC) are lifelines for SEO. Beyond that, React 19's React Compiler automatically optimizes performance (memoization) without sprinkling `useMemo` everywhere. Online shoppers in Vietnam overwhelmingly find products through Google. A pure-CSR storefront (Create React App style) would rank poorly. The admin dashboard, on the other hand, can happily use React without SSR.

### ADR-017: The Common Library Architecture
As analyzed in Part 3, the `gitlab.com/ta-microservices/common v1.9.5` library has eliminated 4,150 duplicated lines across 19 services. The commandment: *"Do not copy-paste middleware. Extract and abstract it."*

### ADR-018: K3d + Tilt Is Enough for Local Development
**Decision**: Use K3d (lightweight K3s running in Docker) + Tilt hot reload — throw Docker Compose in the trash

Docker Compose has a habit of failing to simulate Dapr sidecar injection, shrugging at K8s resource limits, and giving up on ConfigMap/Secret mounts. Developers who cling to Compose locally invariably sing the same tune when shipping to Kubernetes staging: "it works on Compose, fails on K8s." K3d squeezes a complete Kubernetes environment onto a laptop (requiring 8GB of RAM to carry all 21 services).

### ADR-019: Structured Logging With Correlation IDs
Every log line must be stamped with the full set: `service`, `trace_id`, `correlation_id`, `user_id`, `request_id`. These correlation IDs propagate into event metadata over Dapr. Drop one `correlation_id` into Grafana Loki's search box and the entire request journey across 5+ services is laid bare.

### ADR-020: Error Handling & Resilience
Circuit breaker configuration (ADR-020): 5 consecutive failures → reject all new calls for 60 seconds (open) → let 5 trial requests through (half-open) → if they survive, close the gates as usual (closed). Exponential backoff: 1s → 2s → 4s → 8s → 16s → give up.

## Group 7: Data & Domain (ADR-021 to ADR-024)

### ADR-021: Price & Stock Data Ownership
**Decision**: Pricing Service rules the price domain; Warehouse Service controls stock quantities; Promotion Service legislates discounts.

This decision targets a classic architectural blunder of Magento: forcing both price and stock to live as attributes subordinate to a product. In this composable platform, they are liberated into independent entities belonging to separate business capabilities. Catalog Service only knows what a product *looks like* (what). Pricing Service knows what it *costs* (how much). And Warehouse Service is the only one that can count *how many exist*.

### ADR-022: Dynamic SQL Pivoting for EAV
A foundational decision underpinning Part 5 of the series: hardcoding attribute IDs is absolutely forbidden. The pattern of looking up attributes via `eav_attribute.attribute_code` is the safe migration approach. This ADR was written on March 2, 2026 — immediately after the EAV spike exposed a bad habit: the team's initial extraction scripts were brazenly hardcoding IDs.

### ADR-023: Standardizing the Caching Layer + Worker Patterns
This ADR is the key that unlocked the `common v1.9.5` library: bundling single-flight cache stampede protection, a RedLock distributed cronjob, and the outbox processor into one common library. Before this ADR was signed (March 2026), 10 services had produced 10 self-declared outbox implementations with slight variations.

### ADR-024: Inventory Data Ownership (17KB Long — The Biggest Battle)
At a lean 17KB, ADR-024 is more than 3x longer than any other ADR. Who would own inventory data ignited the most contested decision in the platform's design history: would Catalog Service pocket stock information (the Magento way, treating the `cataloginventory_stock_item` table as a vassal of the catalog), or would it be handed to Warehouse Service?

The verdict: **Warehouse Service owns stock; Catalog Service may only display a read-only stock indicator** (e.g. in_stock: true/false) populated by the events Warehouse Service emits.

The contested alternative originally floated was "Catalog should call Warehouse synchronously over gRPC to fetch the stock level every time someone loads a product page." This idea was ridiculed and rejected: it would handcuff product page load speed to Warehouse Service's health — if Warehouse went down, the entire storefront would go down with it, no ifs or buts. By pre-computing the `in_stock` flag into Catalog's own database (via events), catalog pages gained a stubborn resilience that survives even a full Warehouse Service outage.

## The 5 Most Counter-Intuitive Decisions

| Decision | What most engineers would choose | What was chosen | Key reason |
|---|---|---|---|
| Event messaging | Raw Redis Streams | Dapr abstraction layer | Broker portability, easy vendor swap |
| HTTP framework | Gin or Echo | go-kratos v3 | Native dual transport (gRPC + HTTP) |
| K8s config | Helm | Kustomize | Lightweight, pure YAML |
| Schema migrations | golang-migrate | Goose | Careful transaction wrapping |
| Inventory ownership | Inside Catalog Service | Split out to Warehouse Service | Protects catalog page availability from cascading failure |

## Final Word

24 decisions, all accepted, none rejected, none superseded — that could be a sign of brilliant upfront design, or it could be a sign that the team hasn't been honest about quietly rethinking things after the fact. The cluster of three ADRs from March 2026 (ADR-022, 023, 024) exposes an uncomfortable truth: those decisions sprang up like mushrooms after the rain to patch gaps discovered during implementation, not from any prophetic upfront design.

The decision with the grandest vision still belongs to ADR-001 — conceived 3 months before anything else. The **event-driven first** philosophy shaped the entire migration strategy: CDC with Debezium, dual-write via events, the infamous Transactional Outbox, all the way to the graceful saga choreography. Without this founding commitment, the celebrated 3-phase Strangler Fig migration at the heart of this series probably wouldn't have worked at all.

---

*This part officially brings the Composable Commerce Migration series to a close. If you are also planning to replace your aging Magento platform, follow the [series hub](/series/composable-commerce-migration/) — CTOs should start grinding from Part 0, Magento backend engineers should roll up their sleeves at Part 5, and Golang engineers can dive straight in from Part 3.*

*Need someone to pressure-test the architecture (architecture consulting) before your next big swing? → [Book a 1:1 consulting session](/hire/)*

---

### 🔗 Read more related deep dives:
- [Golang Microservices Architecture & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Deploying an Agentic AI Swarm in Production with OpenClaw & LiteLLM](/posts/deploying-autonomous-ai-swarm-openclaw-litellm/)
- [Golang gRPC Microservices Architecture: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/)

---

---

---

[← Previous Chapter: Part 9: Transactional Outbox & Saga Pattern](/series/composable-commerce-migration/part-9-outbox-saga/) | [Series Hub](/series/composable-commerce-migration/)


---

## ❓ Frequently Asked Questions (FAQ)

### Q1: What core architectural problem does this ADR walkthrough solve?
It recaps the 24 core architecture decision records (ADRs) made while building Composable Commerce: Dapr vs Kafka, Kustomize vs Helm, go-kratos vs Gin, Goose vs golang-migrate.

### Q2: What are the most important considerations for real-world implementation?
Focus on layering bounded context boundaries, establishing fallback mechanisms, and monitoring closely through OpenTelemetry metrics to detect bottlenecks early.

### Q3: How do you test and evaluate effectiveness after applying these decisions?
Apply load testing, benchmark P95/P99 latency before and after deployment, and combine distributed tracing to verify stability under high load.
