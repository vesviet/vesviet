# Posts Corpus Content Audit Report — 2027 SOTA Masterclass Standards

> **Domain:** `vesviet` — English Flagship (`https://tanhdev.com/`)  
> **Snapshot Date:** 2026-10-05  
> **Audited Files:** 66 Standalone Posts  
> **Overall SOTA 2027 Compliance (7/7 Gates):** **17/66 (25.8%)**  
> **Archive Reference:** Supersedes `reports/archive/historical-audits/posts-corpus-audit-2026-10-04.md`  

---

## 1. Executive Summary & Aggregate Quality Gate Statistics

Comprehensive automated evaluation of all 66 standalone technical posts in `vesviet/content/posts` against the **7 SOTA 2027 Quality Gates** defined in `learn/tests/verify_target_posts_sota.py` and `agent-skills/core/rules/knowledge.md`. All checks executed against live filesystem assets.

| Gate | Standard & Description | Passing Files | Pass Rate | Status / Recommended Action |
| :--- | :--- | :---: | :---: | :--- |
| **Gate 1** | Depth & Volume: Size > 20.5 KB (20,992 B) & Body Words $\ge 2,500$ | 49 / 66 | 74.2% | Needs depth expansion for thin legacy posts |
| **Gate 2** | Answer-First: Single-line `> **Answer-first:**` (48–62 words) | 29 / 66 | 43.9% | Requires word tuning / injection to meet 48-62w boundary |
| **Gate 3** | Prerequisite Callout: `> **Prerequisite:**` | 17 / 66 | 25.8% | Deficit: 17 SOTA posts have prerequisite blocks; remaining 49 require injection |
| **Gate 4** | Visual Architecture: `mermaid: true` & $\ge 2$ valid Mermaid diagrams | 38 / 66 | 57.6% | Inject valid architectural flowcharts / sequence diagrams |
| **Gate 5** | Structured FAQ: $\ge 3$ `{{< faq >}}` schema shortcodes | 36 / 66 | 54.5% | Inject Schema.org FAQ shortcodes for rich search snippets |
| **Gate 6** | Production Code Realism: $\ge 1$ code block, 0 pseudocode/mock markers | 63 / 66 | 95.5% | Review and replace pseudo-code with version-pinned code |
| **Gate 7** | Authority & Link Topology: 0 leaks to learn & $\ge 1$ Anchor Pillar link | 48 / 66 | 72.7% | Inject Anchor Pillar backlinks / reciprocal upstream badges |

### SOTA 2027 Score Distribution

| Score (Passing Gates) | Count | Percentage | Classification |
| :---: | :---: | :---: | :--- |
| **7/7** | 17 | 25.8% | **2027 SOTA Certified** (Fully Compliant) |
| **6/7** | 1 | 1.5% | Near SOTA (Deficient in 1 gate, typically Prerequisite) |
| **5/7** | 13 | 19.7% | Substantial Draft (Missing Prerequisite + AF or Mermaids) |
| **4/7** | 4 | 6.1% | Intermediate (Missing FAQs, Prerequisite, and Visuals) |
| **3/7** | 16 | 24.2% | Basic Article (Missing multiple technical gates) |
| **2/7** | 11 | 16.7% | Legacy Stub / Thin Post |
| **1/7** | 4 | 6.1% | Minimal Legacy Stub / Unformatted Draft |
| **0/7** | 0 | 0.0% | Incomplete Raw Markdown |

---

## 2. Full Post Inventory Scorecard Table (66 Rows)

| # | Post Filename | Twin Status | Date/Lastmod | Size (KB) | Words | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Link Topology | Staleness | Overall SOTA Status |
|:---:|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|:---:|
| 1 | `agentic-ecommerce-search-golang-vector-databases.md` | Twin Present | 2026-05-10 / 2026-07-23 | 15.71 | 2139 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 1/7 Gates |
| 2 | `ai-native-frontend-architecture-predictions-2028.md` | Twin Present | 2026-05-16 / 2026-07-23 | 11.92 | 1502 | FAIL | FAIL | FAIL | PASS | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 3/7 Gates |
| 3 | `alipay-double-11-architecture-tps.md` | Twin Present | 2026-06-01 / 2026-09-06 | 20.65 | 2644 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2027 SOTA |
| 4 | `architecting-21-service-ecommerce-golang-ddd.md` | Twin Present | 2026-04-12 / 2026-10-01 | 33.9 | 4239 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (3) | Fresh (2026) | 2027 SOTA |
| 5 | `architecting-an-autonomous-hybrid-ai-content-pipeline.md` | Twin Present | 2026-05-18 / 2026-07-26 | 13.17 | 1731 | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 2/7 Gates |
| 6 | `argo-cd-updates-2026.md` | Twin Present | 2026-05-18 / 2026-07-23 | 15.97 | 2191 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2/7 Gates |
| 7 | `aws-eks-vs-ecs-comparison.md` | Twin Present | 2026-06-26 / 2026-08-23 | 33.45 | 4646 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2027 SOTA |
| 8 | `aws-mysql-8-eol-magento-2-4-8-upgrade-architecture.md` | Twin Present | 2026-08-12 / 2026-10-01 | 26.69 | 3421 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2027 SOTA |
| 9 | `banking-microservices-architecture.md` | Twin Present | 2026-06-01 / 2026-07-18 | 24.95 | 3071 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2027 SOTA |
| 10 | `beyond-quick-commerce-15-second-customer-intelligence-architecture.md` | Twin Present | 2026-08-13 / 2026-09-06 | 27.58 | 3597 | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | Missing Anchor | Fresh (2026) | 5/7 Gates |
| 11 | `blueprint-ecommerce-microservices-architecture-diagram.md` | Twin Present | 2026-04-12 / 2026-08-23 | 21.7 | 2751 | PASS | PASS | FAIL | PASS | PASS | FAIL | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 12 | `building-custom-golang-vector-database-engine-hnsw.md` | Twin Present | 2026-07-23 / 2026-07-23 | 51.93 | 6900 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2027 SOTA |
| 13 | `building-custom-kubernetes-operators-ebpf-golang-cilium.md` | Twin Present | 2026-08-06 / 2026-08-23 | 47.55 | 5055 | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | Missing Anchor | Go <1.24 | 3/7 Gates |
| 14 | `building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs.md` | Twin Present | 2026-07-23 / 2026-07-23 | 28.28 | 3587 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 3/7 Gates |
| 15 | `cloudflare-d1-durable-objects-realtime-cart.md` | Twin Present | 2026-06-01 / 2026-07-21 | 33.04 | 3982 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (3) | Fresh (2026) | 2027 SOTA |
| 16 | `cloudflare-zero-devops-ecommerce.md` | Twin Present | 2026-06-17 / 2026-06-24 | 20.84 | 2636 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 3/7 Gates |
| 17 | `composable-banking-architecture.md` | Twin Present | 2026-06-10 / 2026-08-23 | 35.0 | 4515 | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 6/7 Gates |
| 18 | `cvrp-vrptw-alns-fleet-optimization-golang-architecture.md` | Twin Present | 2026-08-15 / 2026-08-15 | 26.22 | 3355 | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 19 | `dapr-state-store-consistency-tradeoffs.md` | Twin Present | 2026-05-22 / 2026-07-23 | 21.29 | 3045 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 3/7 Gates |
| 20 | `dapr-workflow-saga-orchestration-guide.md` | Twin Present | 2026-06-01 / 2026-07-03 | 25.68 | 2998 | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 4/7 Gates |
| 21 | `database-impact-on-programming-languages.md` | Twin Present | 2026-05-25 / 2026-07-23 | 13.7 | 1888 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 1/7 Gates |
| 22 | `deconstructing-microfinance-core-banking-architecture.md` | Twin Present | 2026-05-28 / 2026-07-23 | 18.16 | 2389 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2/7 Gates |
| 23 | `deploying-astro-on-cloudflare-full-stack-edge-architecture.md` | Twin Present | 2026-04-24 / 2026-08-23 | 27.68 | 3799 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (3) | Fresh (2026) | 2027 SOTA |
| 24 | `deploying-autonomous-ai-swarm-openclaw-litellm.md` | Twin Present | 2026-05-30 / 2026-09-06 | 27.09 | 3390 | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | Missing Anchor | Fresh (2026) | 5/7 Gates |
| 25 | `generative-ui-with-mcp-ai-native-frontend.md` | Twin Present | 2026-06-01 / 2026-09-06 | 22.54 | 2602 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (4) | Fresh (2026) | 2027 SOTA |
| 26 | `gitops-at-scale-kubernetes-argocd-microservices.md` | Twin Present | 2026-04-12 / 2026-07-03 | 16.42 | 2068 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2/7 Gates |
| 27 | `go-126-green-tea-gc-cgo-performance-guide.md` | Twin Present | 2026-06-12 / 2026-07-03 | 17.41 | 2522 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2/7 Gates |
| 28 | `go-mcp-server-development-production-guide.md` | Twin Present | 2026-07-15 / 2026-07-15 | 29.79 | 4039 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 3/7 Gates |
| 29 | `go-microservices-distributed-tracing-architecture.md` | Twin Present | 2026-06-08 / 2026-07-03 | 20.69 | 2630 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Go <1.24 | 3/7 Gates |
| 30 | `go-microservices.md` | Twin Present | 2026-06-12 / 2026-08-23 | 51.69 | 6782 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (3) | Fresh (2026) | 2027 SOTA |
| 31 | `go-pprof-kubernetes-remote-profiling.md` | Twin Present | 2026-06-01 / 2026-07-21 | 29.49 | 4126 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2027 SOTA |
| 32 | `golang-goroutine-pool-errgroup-worker.md` | Twin Present | 2026-06-01 / 2026-07-21 | 22.18 | 2889 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Go <1.24 | 3/7 Gates |
| 33 | `golang-grpc-microservices-production-guide.md` | Twin Present | 2026-06-11 / 2026-07-18 | 32.05 | 3744 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 3/7 Gates |
| 34 | `golang-pprof-profiling-memory-cpu-tutorial.md` | Twin Present | 2026-06-02 / 2026-09-06 | 27.29 | 3557 | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | Missing Anchor | Fresh (2026) | 5/7 Gates |
| 35 | `goroutine-leak-detection-production-golang.md` | Twin Present | 2026-05-26 / 2026-07-03 | 24.7 | 3319 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (2) | Go <1.24 | 3/7 Gates |
| 36 | `graphhopper-distance-matrix-production-guide.md` | Twin Present | 2026-06-11 / 2026-08-23 | 31.6 | 4003 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2027 SOTA |
| 37 | `graphhopper-kubernetes-self-hosting-osm.md` | Twin Present | 2026-06-01 / 2026-06-01 | 19.09 | 2432 | FAIL | PASS | FAIL | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 38 | `graphrag-vs-naive-rag-enterprise-guide.md` | Twin Present | 2026-06-01 / 2026-06-01 | 21.51 | 2752 | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 4/7 Gates |
| 39 | `high-throughput-go-framework-benchmarks-gin-fiber-kratos.md` | Twin Present | 2026-07-17 / 2026-07-17 | 25.25 | 3623 | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 40 | `high-throughput-local-llm-infrastructure-vllm-golang-gateway.md` | Twin Present | 2026-08-06 / 2026-08-23 | 41.38 | 4988 | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | Missing Anchor | Fresh (2026) | 3/7 Gates |
| 41 | `kubernetes-in-place-pod-resizing-guide.md` | Twin Present | 2026-06-12 / 2026-07-08 | 21.04 | 2603 | PASS | FAIL | FAIL | PASS | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 3/7 Gates |
| 42 | `leaseinvietnam-ai-powered-expat-rental-intelligence-system.md` | Twin Present | 2026-04-24 / 2026-04-24 | 21.99 | 2994 | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 4/7 Gates |
| 43 | `mastering-event-driven-architecture-dapr.md` | Twin Present | 2026-04-12 / 2026-07-18 | 26.11 | 3511 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 3/7 Gates |
| 44 | `microservices-delusion-why-golang-modular-monolith-is-the-destination.md` | Twin Present | 2026-08-13 / 2026-09-16 | 24.28 | 2961 | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 45 | `modern-golang-123-124-high-performance-zero-alloc-gc-tuning.md` | Twin Present | 2026-08-06 / 2026-08-23 | 28.49 | 3763 | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | Missing Anchor | Go <1.24 | 3/7 Gates |
| 46 | `multi-region-geo-distributed-api-routing.md` | Twin Present | 2026-07-17 / 2026-07-17 | 20.96 | 2978 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 3/7 Gates |
| 47 | `mysql-horizontal-scaling.md` | Twin Present | 2026-06-01 / 2026-09-06 | 29.1 | 3782 | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | Missing Anchor | Fresh (2026) | 5/7 Gates |
| 48 | `mysql-scalability-guide.md` | Twin Present | 2026-06-10 / 2026-08-23 | 28.33 | 3802 | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 49 | `mysql-scaling-sharding-tidb-architecture.md` | Twin Present | 2026-05-26 / 2026-08-23 | 24.91 | 3392 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2027 SOTA |
| 50 | `order-fulfillment-algorithm-warehouse-last-mile.md` | Twin Present | 2026-06-01 / 2026-09-06 | 21.54 | 2635 | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 51 | `osrm-shared-memory-kubernetes-live-traffic.md` | Twin Present | 2026-05-15 / 2026-07-23 | 22.24 | 3221 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2027 SOTA |
| 52 | `osrm-vs-graphhopper-architecture-comparison.md` | Twin Present | 2026-07-17 / 2026-10-04 | 28.73 | 3677 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (5) | Fresh (2026) | 2027 SOTA |
| 53 | `paypay-architecture-scaling.md` | Twin Present | 2026-06-01 / 2026-06-01 | 18.48 | 2537 | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | PASS | Anchor Pillar (1) | Fresh (2026) | 2/7 Gates |
| 54 | `production-ai-apis-oauth-versioning-meta-predictions.md` | Twin Present | 2026-05-18 / 2026-05-18 | 20.89 | 2999 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 2/7 Gates |
| 55 | `production-ai-observability-opentelemetry-golang-llm-tracing.md` | Twin Present | 2026-08-06 / 2026-08-23 | 43.53 | 4466 | PASS | FAIL | FAIL | FAIL | PASS | PASS | FAIL | Missing Anchor | Go <1.24 | 3/7 Gates |
| 56 | `real-time-inventory-ecommerce-architecture.md` | Twin Present | 2026-06-08 / 2026-07-08 | 16.9 | 2234 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2/7 Gates |
| 57 | `real-time-ride-hailing-architecture.md` | Twin Present | 2026-06-01 / 2026-06-10 | 19.94 | 2844 | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | Missing Anchor | Fresh (2026) | 1/7 Gates |
| 58 | `serverless-ecommerce-cloudflare-d1.md` | Twin Present | 2026-05-25 / 2026-07-18 | 14.78 | 2007 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | PASS | Anchor Pillar (2) | Fresh (2026) | 2/7 Gates |
| 59 | `shopee-flash-sale-architecture.md` | Twin Present | 2026-06-01 / 2026-09-06 | 21.3 | 2868 | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 5/7 Gates |
| 60 | `slm-fine-tune-vs-prompt-engineering.md` | Twin Present | 2026-06-01 / 2026-07-23 | 15.69 | 1929 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 1/7 Gates |
| 61 | `surge-pricing-optimization-architecture.md` | Twin Present | 2026-05-12 / 2026-07-23 | 15.26 | 2138 | FAIL | PASS | FAIL | FAIL | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 4/7 Gates |
| 62 | `temporal-saga-pattern-golang-distributed-transactions-guide.md` | Twin Present | 2026-07-23 / 2026-07-23 | 45.55 | 5118 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (1) | Fresh (2026) | 2027 SOTA |
| 63 | `the-future-of-laravel-development-in-ai-era.md` | Twin Present | 2026-05-16 / 2026-05-16 | 11.48 | 1549 | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 2/7 Gates |
| 64 | `urban-canyon-gps-multipath-map-matching-architecture.md` | Twin Present | 2026-08-12 / 2026-09-06 | 29.25 | 3981 | PASS | PASS | FAIL | PASS | PASS | PASS | FAIL | Missing Anchor | Fresh (2026) | 5/7 Gates |
| 65 | `vibe-coding-and-ai-code-review-future.md` | Twin Present | 2026-05-31 / 2026-08-26 | 19.81 | 2726 | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | Missing Anchor | Fresh (2026) | 2/7 Gates |
| 66 | `zero-trust-service-mesh-security-spiffe-spire-istio-golang.md` | Twin Present | 2026-07-23 / 2026-07-23 | 35.28 | 4524 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Anchor Pillar (5) | Fresh (2026) | 2027 SOTA |

---

## 3. 10 Anchor Pillar Hubs SOTA 2027 Certification Scorecard

The 10 Anchor Pillar Hubs form the structural link topology backbone of the entire publication network. With the completion of Batch 7 on 2026-10-05, all 10 Anchor Pillar Hubs achieve 100.0% certification under 2027 SOTA standards:

| # | Anchor Pillar Hub Path | Topical Domain & Focus | `vesviet` Metrics (Disk) | `learn` Metrics (Disk) | Certification Status |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 1 | `posts/go-microservices.md` | Go & Microservices Architecture Hub | 51.69 KB / 6,782w | 68.13 KB / 9,694w | 7/7 PASS ✅ |
| 2 | `posts/architecting-21-service-ecommerce-golang-ddd.md` | System Design & E-Commerce Hub | 33.90 KB / 4,239w | 21.52 KB / 2,705w | 7/7 PASS ✅ |
| 3 | `posts/aws-eks-vs-ecs-comparison.md` | Cloud Native & Container Infrastructure Hub | 33.45 KB / 4,646w | 20.98 KB / 2,905w | 7/7 PASS ✅ |
| 4 | `posts/banking-microservices-architecture.md` | FinTech & Core Banking Systems Hub | 24.95 KB / 3,071w | 31.65 KB / 4,379w | 7/7 PASS ✅ |
| 5 | `posts/cloudflare-d1-durable-objects-realtime-cart.md` | Edge Serverless & Cloudflare Hub | 33.04 KB / 3,982w | 35.63 KB / 4,763w | 7/7 PASS ✅ |
| 6 | `posts/deploying-astro-on-cloudflare-full-stack-edge-architecture.md` | AI Frontend & Edge Full-Stack Hub (Batch 7) | 27.68 KB / 3,799w | 35.75 KB / 5,267w | 7/7 PASS ✅ |
| 7 | `posts/generative-ui-with-mcp-ai-native-frontend.md` | Generative UI & MCP Architecture Hub (Batch 7) | 22.54 KB / 2,602w | 34.08 KB / 4,389w | 7/7 PASS ✅ |
| 8 | `posts/alipay-double-11-architecture-tps.md` | Distributed Systems & High Concurrency Hub | 20.65 KB / 2,644w | 37.56 KB / 5,800w | 7/7 PASS ✅ |
| 9 | `reading-map.md` | Sitewide Curated Learning Directory (Root Hub) | 16.91 KB / 2,139w | 14.85 KB / 2,257w | Root Hub PASS ✅ |
| 10 | `hire.md` | Commercial Consulting Intake Portal (Root Hub) | 10.25 KB / 1,296w | 6.45 KB / 929w | Root Hub PASS ✅ |

*All 8 standalone technical article hubs (#1–#8) satisfy 100% of the 7 SOTA Quality Gates (>20.5 KB, >=2,500 words, Answer-first, Prerequisite, >=2 Mermaids, >=3 FAQs, production code, zero leaks). The 2 Root Hubs (#9 reading-map and #10 hire) serve as sitewide navigation and consulting intake hubs.*

---

## 4. Technical Series SOTA 2027 Compliance (25 Series, 251 Files, 21 SOTA / 4 Baseline)

The technical series corpus comprises 25 series across 225 content chapters, 25 subindices, and 1 root index (251 markdown files per repository). Exactly 21 of 25 series (84.0%) are fully upgraded to 2027 SOTA Masterclass:

| # | Series Slug | Chapters | Total Files | Total Words | Domain Focus | SOTA Upgrade Status |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | `agentic-ecommerce-search` | 7 | 8 | ~22,861 | AI & Vector Retrieval | Complete (2027 SOTA) |
| 2 | `agentic-system-architecture` | 7 | 8 | ~27,164 | Multi-Agent Systems | Complete (2027 SOTA) |
| 3 | `ai-code-review-vibe-coding` | 7 | 8 | ~30,351 | AI Governance & AST | Complete (2027 SOTA) |
| 4 | `ai-data-engineering-pipeline` | 11 | 12 | ~33,587 | Data Engineering & AI | Complete (2027 SOTA, Sprint 3) |
| 5 | `ai-driven-engineer` | 11 | 12 | ~32,858 | Engineering Career & AI | Complete (2027 SOTA, Sprint 3) |
| 6 | `ai-driven-playbook` | 14 | 15 | ~41,561 | AI Engineering Playbook | Complete (2027 SOTA, Sprint 4) |
| 7 | `alipay-double-11` | 8 | 9 | ~26,106 | High-TPS FinTech Scaling | Complete (2027 SOTA) |
| 8 | `architectural-tradeoffs-showdowns` | 10 | 11 | ~50,382 | Distributed Tradeoffs | Complete (2027 SOTA, Sprint 1) |
| 9 | `composable-commerce-migration` | 11 | 12 | ~4,420 | Composable Architecture | Baseline Legacy |
| 10 | `core-banking-architecture` | 8 | 9 | ~27,132 | FinTech Ledger & BIAN | Complete (2027 SOTA) |
| 11 | `core-banking-developer` | 9 | 10 | ~25,228 | Core Banking Dev Guide | Complete (2027 SOTA, Sprint 4) |
| 12 | `cornerstone-technologies` | 5 | 6 | ~16,271 | Foundation Infrastructure | Complete (2027 SOTA) |
| 13 | `ecommerce-order-allocation` | 11 | 12 | ~32,266 | Logistics & Graph Theory | Complete (2027 SOTA) |
| 14 | `generative-ui-architecture` | 8 | 9 | ~23,625 | AI Edge Frontend & MCP | Complete (2027 SOTA) |
| 15 | `high-concurrency-systems` | 10 | 11 | ~42,338 | High Concurrency Patterns | Complete (2027 SOTA) |
| 16 | `magento-migration-vietnam` | 15 | 16 | ~15,971 | E-Commerce Modernization | Complete Baseline |
| 17 | `mcp-engineering-in-production` | 8 | 9 | ~24,658 | MCP Protocols & Edge | Complete (2027 SOTA) |
| 18 | `modular-monolith-architecture` | 9 | 10 | ~28,309 | Go Architecture | Baseline |
| 19 | `paypay-architecture` | 6 | 7 | ~17,856 | Payment Scaling (TiDB) | Complete (2027 SOTA, Sprint 2) |
| 20 | `prompt-standard` | 10 | 11 | ~30,190 | Prompt Engineering DSL | Complete (2027 SOTA) |
| 21 | `ride-hailing-realtime-architecture` | 7 | 8 | ~22,823 | Realtime Ride-Hailing | Complete (2027 SOTA, Sprint 1) |
| 22 | `routing-geospatial-architecture` | 9 | 10 | ~33,523 | Geospatial GIS & Routing | Complete (2027 SOTA) |
| 23 | `shopee-architecture` | 5 | 6 | ~21,473 | E-Commerce Microservices | Complete (2027 SOTA, Sprint 2) |
| 24 | `slm-playbook` | 7 | 8 | ~20,365 | Small Language Models | Complete (2027 SOTA) |
| 25 | `system-design` | 12 | 13 | ~48,190 | Go System Design | Complete (2027 SOTA) |

*Summary:* **21 Series SOTA Complete** (~643,466 words across 190 chapters), **4 Series Baseline** (`composable-commerce-migration` [11 ch], `magento-migration-vietnam` [15 ch], `modular-monolith-architecture` [9 ch], `cornerstone-technologies` [5 ch]).

---

## 5. Tech Radar Editions Breakdown (32 Vesviet / 68 Learn Editions)

The Tech Radar architecture tracks production engineering paradigms across four quadrants (ADOPT, TRIAL, ASSESS, HOLD). All editions adhere to the 2027 SOTA Radar standard:

| Month | Active Editions (`vesviet`) | Flagship Technical Highlights |
| :---: | :---: | :--- |
| **2026-04** | 8 | Claude Sonnet, Mistral Small, Creative MCP |
| **2026-05** | 3 | DigitalOcean AI-native cloud, Gateway API v1.5 |
| **2026-06** | 3 | Emerging WASI 0.3 runtime patterns |
| **2026-07** | 3 | LLM evaluation frameworks & Agent governance |
| **2026-08** | 7 | Stateless MCP K8s gateway, OWASP/NIST AI agent gateway, Go synctest, vLLM context routing MLA, eBPF Tetragon agent security |
| **2026-09** | 6 | WASI 0.3 component model/wasmtime, MCP 2.0 agentic mesh, DeepSeek-V3 MLA, SGLang EAGLE-2, Disaggregated Prefill-Decode, vLLM v1 Production KV Cache (2026-09-30) |
| **2026-10** | 2 | Cilium 1.17 & Tetragon 1.4 eBPF Sandboxing (2026-10-02), Kratos v2.9 & Dapr 1.15 Microservices Go 1.25 (2026-10-05) |

*Corpus Distribution:* `vesviet` hosts **32 active editions** (40 total markdown files including monthly `_index.md` and root `_index.md`); `learn` hosts **68 active editions** (76 total markdown files). Flagship radar `radar-2026-09-30-vllm-v1-production-kv-cache.md` certified 7/7 SOTA gates on both sites.

---

## 6. Per-Repo Orphan & Mismatch Analysis

### Vesviet Repository Alignment
- **Total Standalone Posts:** 66 files in `vesviet/content/posts`.
- **Twin Presence:** 66 / 66 (100.0%) of posts have verified Vietnamese twins in `learn/content/posts`.
- **Orphan Count:** **0 orphan posts**. No posts exist in `vesviet/content/posts` without a corresponding entry in `learn`.
- **Cross-Repo Asymmetry:** `learn/content/posts` contains 86 files (a net surplus of +20 files compared to `vesviet/content/posts`). See breakdown below.

### Detailed Categorization of the 20 Surplus Files in `learn`

| Category | File Count | Filenames | Architectural Rationale & Destination |
| :--- | :---: | :--- | :--- |
| **Section Index** | 1 | `_index.md` | Hugo branch bundle section descriptor for `/posts/`. Contains navigation metadata and series summaries. In `vesviet`, section list templates render without a dedicated `_index.md`. |
| **Internal Draft Reports** | 7 | `content-audit-report.md`, `deep-audit-upgrade-summary.md`, `deep-research-100-rounds-report.md`, `deep-research-batch-3-100-rounds-report.md`, `deep-research-batch-4-100-rounds-report.md`, `deep-research-batch-5-100-rounds-report.md`, `upgrade-summary.md` | Internal audit working papers with `draft: true`. They reside in `learn/content/posts/` but should eventually be relocated to `learn/reports/archive/` to keep content directories focused solely on published articles. |
| **Duplicate Slug Variant** | 1 | `temporal-saga-pattern-golang-distributed-transactions.md` | Legacy 20.4 KB post duplicating `temporal-saga-pattern-golang-distributed-transactions-guide.md` (47.9 KB). Both link upstream to the same English guide. Candidate for alias redirect consolidation. |
| **Magento Series Migration** | 11 | `deconstructing-ecommerce-service-details-domain.md`, `ecommerce-architecture-composable-migration.md`, `exporting-magento-2-data-flat-sql-nodejs.md`, `laravel-vs-golang-when-to-add-features.md`, `magento-ai-integration-strategy-architecture.md`, `magento-development-in-vietnam.md`, `magento-still-worth-investing-2026.md`, `magento-vietnam.md`, `moving-from-magento-to-microservices.md`, `strangler-fig-shared-database-quick-win.md`, `why-migrate-magento-to-microservices.md` | In `learn`, these 11 eCommerce migration chapters reside in `content/posts/`. In `vesviet`, they are structured under `vesviet/content/series/magento-migration-vietnam/`. Both have upstream reciprocity, but taxonomy structure differs between twin repos. |

---

## 7. Upgraded Posts Census (17 Certified SOTA Posts)

Census of all 17 standalone technical articles that have been systematically upgraded to the 2027 SOTA Masterclass standard through deep research dossiers and multi-agent peer review:

| Campaign | Post Filename | `vesviet` Metrics (Disk) | `learn` Metrics (Disk) | 7 Quality Gates | Research Dossier |
| :--- | :--- | :---: | :---: | :---: | :--- |
| Prior Upgrades | `architecting-21-service-ecommerce-golang-ddd.md` | 33.90 KB / 4,239w | 21.52 KB / 2,705w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Prior Upgrades | `aws-mysql-8-eol-magento-2-4-8-upgrade-architecture.md` | 26.69 KB / 3,421w | 24.46 KB / 3,505w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Milestone 3 | `osrm-vs-graphhopper-architecture-comparison.md` | 28.73 KB / 3,677w | 33.80 KB / 4,791w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Milestone 3 | `zero-trust-service-mesh-security-spiffe-spire-istio-golang.md` | 35.28 KB / 4,524w | 39.53 KB / 5,454w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Milestone 3 | `alipay-double-11-architecture-tps.md` | 20.65 KB / 2,644w | 37.56 KB / 5,800w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Milestone 3 | `cloudflare-d1-durable-objects-realtime-cart.md` | 33.04 KB / 3,982w | 35.63 KB / 4,763w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Milestone 3 | `building-custom-golang-vector-database-engine-hnsw.md` | 51.93 KB / 6,900w | 48.54 KB / 6,750w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 6 (2026-10-05) | `go-pprof-kubernetes-remote-profiling.md` | 29.49 KB / 4,126w | 35.12 KB / 4,890w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 6 (2026-10-05) | `banking-microservices-architecture.md` | 24.95 KB / 3,071w | 31.65 KB / 4,379w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 6 (2026-10-05) | `aws-eks-vs-ecs-comparison.md` | 33.45 KB / 4,646w | 20.98 KB / 2,905w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 6 (2026-10-05) | `osrm-shared-memory-kubernetes-live-traffic.md` | 22.24 KB / 3,221w | 25.79 KB / 3,587w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 6 (2026-10-05) | `go-microservices.md` | 51.69 KB / 6,782w | 68.13 KB / 9,694w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 7 (2026-10-05) | `mysql-scaling-sharding-tidb-architecture.md` | 24.91 KB / 3,392w | 27.34 KB / 3,998w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 7 (2026-10-05) | `graphhopper-distance-matrix-production-guide.md` | 31.60 KB / 4,003w | 37.75 KB / 5,254w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 7 (2026-10-05) | `temporal-saga-pattern-golang-distributed-transactions-guide.md` | 45.55 KB / 5,118w | 50.81 KB / 6,453w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 7 (2026-10-05) | `generative-ui-with-mcp-ai-native-frontend.md` | 22.54 KB / 2,602w | 34.08 KB / 4,389w | 7/7 PASS ✅ | 100-Round Research Dossier |
| Batch 7 (2026-10-05) | `deploying-astro-on-cloudflare-full-stack-edge-architecture.md` | 27.68 KB / 3,799w | 35.75 KB / 5,267w | 7/7 PASS ✅ | 100-Round Research Dossier |

*Total Certified SOTA Standalone Posts:* **17 posts** on `vesviet` (17/66 = 25.8%) and **17 posts** on `learn` (17/86 = 19.8%). 100% verified passing `learn/tests/verify_target_posts_sota.py --scope all`.

---

## 8. Strategic Upgrade Prioritization & Candidate Ranking

Connecting corpus findings with the refreshed roadmap defined in `reports/legacy-posts-upgrade-plan-2026-10-05.md`. With all 17 target posts from Prior, M3, Batch 6, and Batch 7 certified SOTA, the remaining **49 baseline standalone posts** are ranked using the 100-Point Composite Scoring Rubric:

### Immediate Next Step: Batch 8 Target Candidates (Top 5 Priority Posts)
1. **`shopee-flash-sale-architecture.md`** (Total: **83 pts** · C1: 24, C2: 20, C3: 15, C4: 12, C5: 12) — High-traffic eCommerce inventory deduction, Kitex Go zero-copy, Redis Lua atomic concurrency.
2. **`cvrp-vrptw-alns-fleet-optimization-golang-architecture.md`** (Total: **81 pts** · C1: 22, C2: 21, C3: 15, C4: 11, C5: 12) — Vehicle routing problem with time windows, ALNS metaheuristics in Go 1.25.
3. **`composable-banking-architecture.md`** (Total: **81 pts** · C1: 21, C2: 22, C3: 14, C4: 12, C5: 12) — Event-driven core banking, distributed ledger double-entry, BIAN service domains.
4. **`golang-goroutine-pool-errgroup-worker.md`** (Total: **80 pts** · C1: 23, C2: 18, C3: 15, C4: 11, C5: 13) — High-concurrency worker pool, bounded memory goroutines, errgroup context lifecycle.
5. **`blueprint-ecommerce-microservices-architecture-diagram.md`** (Total: **78 pts** · C1: 20, C2: 20, C3: 15, C4: 11, C5: 12) — 21-service microservices architecture blueprint, C4 diagram visual modeling.

### Full Ranking Reference (Ranks 6–20)
Ranks 6 through 20 comprise: `mysql-horizontal-scaling.md` (78), `golang-pprof-profiling-memory-cpu-tutorial.md` (77), `urban-canyon-gps-multipath-map-matching-architecture.md` (76), `beyond-quick-commerce-15-second-customer-intelligence-architecture.md` (75), `deploying-autonomous-ai-swarm-openclaw-litellm.md` (74), `high-throughput-go-framework-benchmarks-gin-fiber-kratos.md` (74), `order-fulfillment-algorithm-warehouse-last-mile.md` (73), `microservices-delusion-why-golang-modular-monolith-is-the-destination.md` (73), `dapr-workflow-saga-orchestration-guide.md` (73), `building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs.md` (73), `high-throughput-local-llm-infrastructure-vllm-golang-gateway.md` (73), `production-ai-observability-opentelemetry-golang-llm-tracing.md` (72), `building-custom-kubernetes-operators-ebpf-golang-cilium.md` (72), `go-mcp-server-development-production-guide.md` (72), `modern-golang-123-124-high-performance-zero-alloc-gc-tuning.md` (71).
For full scoring breakdown and execution blueprint, see `reports/legacy-posts-upgrade-plan-2026-10-05.md`.

---

## 9. File Archival Strategy & Invariants Verification

### Archival Procedure
1. Previous audit report `reports/posts-corpus-audit-2026-10-04.md` is archived into `reports/archive/historical-audits/posts-corpus-audit-2026-10-04.md` across both repositories.
2. New authoritative audit report is published at `reports/posts-corpus-audit-2026-10-05.md` across both repositories.
3. Strict Invariant Check: The root directory of `vesviet/reports/` and `learn/reports/` contains **strictly $\le 5$ files**:
   - `CONTENT_INDEX.md`
   - `KNOWLEDGE_INDEX.md`
   - `legacy-posts-upgrade-plan-2026-10-05.md` (active)
   - `posts-corpus-audit-2026-10-05.md` (active)
   - *Total root file count:* Exactly **4 files** (100% compliant with $\le 5$ rule and `learn/tests/verify_knowledge_base_sota.py`).

---

*Report generated autonomously following 2027 SOTA Masterclass Standards.*