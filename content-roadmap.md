# VesViet Sitewide Content Quality & SEO Audit Roadmap (2026 Q3–Q4)

**Role:** SEO Analyst & Content Roadmap Lead  
**Scope:** Sitewide Content Audit (`vesviet/content/` — 338 total markdown pages)  
**Target Publication File:** `/home/user/personalized/vesviet/content-roadmap.md`  
**Date of Audit:** July 23, 2026  

---

## Executive Summary & Audit Baseline Metrics

### Purpose & Mandate
A comprehensive sitewide content quality, frontmatter schema, GEO/AEO optimization, and internal link topology audit was conducted across all **338 markdown pages** within the `vesviet` Hugo content repository (`/home/user/personalized/vesviet/content/`). 

The strategic objective of this roadmap is to elevate `vesviet` into an authoritative, enterprise-grade software engineering publication. To achieve this, the content operations team will execute a structured, 4-sprint roadmap focusing on four core pillars:
1. **100% Schema Completeness:** Ensuring all content files contain complete frontmatter metadata (`author`, `date`, `tags`, `categories`, `cover`).
2. **GEO/AEO Answer-First Optimization:** Standardizing upfront summary callout blocks (`**Answer-first:**` or equivalent TL;DR) and FAQ sections across all articles to maximize visibility in AI search engines (Perplexity, ChatGPT, Gemini, Google AI Overviews).
3. **Content Depth Baseline:** Expanding underperforming articles to a minimum word count of **≥ 1,400 words**, enriched with production-grade code, architecture diagrams, and benchmark data.
4. **Link Topology & Orphan Elimination:** Implementing a strict hub-and-spoke internal linking matrix to eliminate **124 orphan pages** (36.7% of the site) and rebalance over-linked conversion pages.

---

### Audit Baseline Metrics

The table below summarizes the sitewide content quality baseline across all 338 audited content pages:

| Audit Category | Metric / Dimension | Total Pages | Percentage (%) | Baseline Status & Action Summary |
|---|---|---|---|---|
| **Sitewide Page Inventory** | Total Content Pages Audited | **338** | 100.0% | Full repository scan (`posts/`, `series/`, `radar/`, root pages) |
| **Content Tier Classification** | Refresh Candidates | **162** | 47.9% | Requires word count expansion, schema fixes, or GEO formatting |
| | Prune / Merge Targets | **92** | 27.2% | Thin content (<1,000w) targeted for consolidation & 301 redirects |
| | Pillar / Evergreen Articles | **84** | 24.9% | High-performing anchor content (≥1,400w, full schema, deep tech) |
| **Word Count Distribution** | Sufficient (≥ 1,400 words) | **121** | 35.8% | Meets or exceeds length requirements for technical authority |
| | Underperforming (1,000–1,399 words) | **102** | 30.2% | Requires 200–400 word technical depth expansion |
| | Thin (< 1,000 words) | **115** | 34.0% | High pruning/merging priority (includes 46 daily radar posts) |
| **Frontmatter Schema Status** | Schema Complete (5/5 fields) | **179** | 53.0% | Contains `author`, `date`, `tags`, `categories`, `cover` |
| | Schema Incomplete (1+ missing) | **159** | 47.0% | Missing frontmatter fields (primarily series sub-articles) |
| **GEO / AEO Answer-First** | Formatted Upfront Summary | **65** | 19.2% | Contains explicit bold answer block upfront |
| | Missing Upfront Block | **273** | 80.8% | Needs `> **Answer-first:**` summary block added immediately below frontmatter |
| **Internal Link Graph** | Total Internal Links Discovered | **1,856** | — | Average 5.5 internal links per page |
| | Orphan Pages (0 Inbound Links) | **124** | 36.7% | Isolated content pages requiring hub-and-spoke link injection |
| | Over-Linked Pages (High Ratio) | **85** | 25.1% | Requires link rebalancing and anchor text diversification |

---

### Key Performance Indicators (KPIs) for Q3–Q4
- **100% Frontmatter Schema Compliance:** 338 of 338 active pages fully populated with schema metadata.
- **100% GEO/AEO Answer-First Coverage:** All published articles feature an upfront summary block.
- **Zero Orphan Pages:** 124 orphan pages connected to Pillar Hubs and `reading-map.md`.
- **Zero Underperforming Posts:** Standalone technical posts expanded to ≥ 1,400 words.
- **301 Redirect Precision:** 100% of pruned/merged thin URLs mapped to canonical pillar targets.

---

## Section 1: Refresh Candidates Action Plan

### Strategy Overview
A total of **162 Refresh Candidates** were identified. This includes 9 standalone posts in `content/posts/`, 126 series sub-articles in `content/series/`, and 27 tech radar briefings in `content/radar/`. The primary objective is to upgrade these pages into authoritative pillar assets through word count expansion (target **≥ 1,400 words**), schema metadata repair, GEO/AEO block addition, and contextual internal link injection.

---

### Subsection 1.1: Standalone Post Refresh Action Plan (9 Key Posts)

The table below details the specific refresh requirements for underperforming or schema-incomplete standalone technical posts:

| # | File Path (`content/posts/...`) | Current Word Count | Target Word Count | Schema Status | Specific Refresh & Expansion Tasks | Contextual Link Additions |
|---|---|---|---|---|---|---|
| 1 | `agentic-ecommerce-search-golang-vector-databases.md` | 1,042w | **1,500w+** | Complete | Expand section on Qdrant gRPC connection pooling, vector payload filtering, and re-ranking performance. Add Go struct code for hybrid BM25 + Qdrant search router. | Link to `/series/agentic-ecommerce-search/`, `/posts/go-microservices/`, and `/posts/graphrag-vs-naive-rag-enterprise-guide/`. |
| 2 | `argo-cd-updates-2026.md` | 1,120w | **1,500w+** | Complete | Add deep dive on Kargo event-driven continuous delivery, ApplicationSet UI enhancements, and breaking change migration risk matrix for Argo CD 3.4. | Link to `/posts/gitops-at-scale-kubernetes-argocd-microservices/` and `/posts/kubernetes-in-place-pod-resizing-guide/`. |
| 3 | `dapr-state-store-consistency-tradeoffs.md` | 1,560w | **1,560w** | ❌ Incomplete | **Schema Fix:** Populate missing `tags: ["Dapr", "Distributed Systems", "Database"]`, `categories: ["Architecture", "Engineering"]`, and `cover: {image: "images/posts/dapr-state-store-cover.png", alt: "Dapr state store consistency tradeoffs"}`. | Link to `/posts/banking-microservices-architecture/` and `/posts/mastering-event-driven-architecture-dapr/`. |
| 4 | `database-impact-on-programming-languages.md` | 980w | **1,500w+** | Complete | Expand content by 520+ words detailing Go `database/sql` connection pool tuning, Rust SQLx compile-time query verification, and Node.js event loop blocking during heavy database ORM serialization. | Link to `/posts/go-microservices/` and `/posts/high-throughput-go-framework-benchmarks-gin-fiber-kratos/`. |
| 5 | `deconstructing-microfinance-core-banking-architecture.md` | 1,250w | **1,500w+** | Complete | Add technical breakdown of declining balance EMI interest math, compulsory savings hold logic, and loan state machine transition table. | Link to `/posts/banking-microservices-architecture/`, `/posts/composable-banking-architecture/`, and `/series/core-banking-developer/`. |
| 6 | `deploying-autonomous-ai-swarm-openclaw-litellm.md` | 1,150w | **1,500w+** | Complete | Add 350+ words on Docker Compose Linux capability drops (`cap_drop: ALL`), LiteLLM multi-key fallback routing, and gVisor container security isolation. | Link to `/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/` and `/posts/production-ai-apis-oauth-versioning-meta-predictions/`. |
| 7 | `osrm-shared-memory-kubernetes-live-traffic.md` | 1,150w | **1,500w+** | ❌ Incomplete | **Schema Fix & Expansion:** Add `cover: {image: "images/posts/osrm-k8s-cover.png", alt: "OSRM Shared Memory on Kubernetes"}`. Expand by 350w on IPC shared memory segment sizing, `sysctl kernel.shmmax`, and Prometheus memory metrics. | Link to `/posts/osrm-vs-graphhopper-architecture-comparison/` and `/posts/graphhopper-kubernetes-self-hosting-osm/`. |
| 8 | `surge-pricing-optimization-architecture.md` | 1,150w | **1,500w+** | Complete | Expand on Uber H3 spatial index resolution math, Apache Flink streaming window logic, and Proportional-Integral-Derivative (PID) damping controller math for price stabilization. | Link to `/posts/real-time-ride-hailing-architecture/` and `/posts/order-fulfillment-algorithm-warehouse-last-mile/`. |
| 9 | `vibe-coding-and-ai-code-review-future.md` | 1,050w | **1,500w+** | Complete | Expand by 450w covering OWASP Top 10 for LLMs (LLM05 Supply Chain, LLM06 Excessive Agency), slopsquatting package hijacking attacks, and multi-agent code review CI gates. | Link to `/posts/ai-native-frontend-architecture-predictions-2028/` and `/posts/generative-ui-with-mcp-ai-native-frontend/`. |

---

### Subsection 1.2: Pillar Posts Frontmatter Schema Fixes (4 Additional Posts)
In addition to word count refresh candidates, 4 high-performing pillar posts require urgent frontmatter schema repairs to achieve 100% schema completeness:

1. `content/posts/high-throughput-go-framework-benchmarks-gin-fiber-kratos.md` (2,500w)
   - **Fix:** Add `tags: ["Go", "Benchmarks", "Gin", "Fiber", "Kratos", "HTTP"]`, `categories: ["Engineering", "Golang"]`, and `cover: {image: "images/posts/go-framework-benchmarks-cover.png", alt: "Go HTTP framework benchmarks Gin vs Fiber vs Kratos"}`.
2. `content/posts/multi-region-geo-distributed-api-routing.md` (2,100w)
   - **Fix:** Add `tags: ["Multi-Region", "Anycast", "Cloudflare", "API Gateway", "Architecture"]`, `categories: ["Architecture", "Cloudflare"]`, and `cover: {image: "images/posts/multi-region-routing-cover.png", alt: "Multi-region geo-distributed API routing"}`.
3. `content/posts/osrm-vs-graphhopper-architecture-comparison.md` (1,450w)
   - **Fix:** Add `cover: {image: "images/posts/osrm-vs-graphhopper-cover.png", alt: "OSRM vs GraphHopper architecture comparison"}`.
4. `content/posts/temporal-saga-pattern-golang-distributed-transactions.md` (1,450w)
   - **Fix:** Add `cover: {image: "images/posts/temporal-saga-cover.png", alt: "Temporal Saga pattern Go distributed transactions"}`.

---

### Subsection 1.3: Series & Tech Radar Refresh Protocol (153 Pages)
- **Frontmatter Standardization:** Standardize series sub-article YAML frontmatter by inheriting `tags`, `categories`, and `cover` images from their parent series `_index.md`.
- **GEO/AEO Answer Block Rollout:** Insert formatted summary callouts immediately below frontmatter:
  ```markdown
  > **Answer-first:** [Concise 2-sentence summary answering the core architectural question of the article, formatted for AI search engines and search snippet extraction.]
  ```
- **Content Expansion:** Expand all underperforming series sub-articles (1,000–1,399 words) to ≥ 1,400 words by adding working code samples, configuration manifests, and system design sequence diagrams.

---

## Section 2: Prune / Merge Action Plan

### Strategy Overview
A total of **92 Prune / Merge Targets** (<1,000 words thin content) were identified across the repository. To avoid search engine penalties for thin content while retaining domain authority and internal link equity, thin pages will be systematically consolidated into parent series hubs or monthly digests, supported by a 100% complete **301 Permanent Redirect Map**.

---

### Breakdown of Prune / Merge Scope
- **46 Thin Daily Tech Radar Briefings:** Daily news summaries (<1,000w) in `content/radar/` (e.g., `radar-2026-05-03.md` 717w) will be merged into monthly Tech Radar digest hubs (`content/radar/2026-04/_index.md`, `content/radar/2026-05/_index.md`, `content/radar/2026-06/_index.md`, `content/radar/2026-07/_index.md`).
- **44 Thin Series Sub-Articles:** Fragmented 300–800 word series parts (e.g. `series/prompt-standard/*`, `series/composable-commerce-migration/*`, `series/ecommerce-order-allocation/*`, `series/high-concurrency-systems/*`) will be consolidated into comprehensive parent series pillar guides.
- **2 Root Utility Pages:** `content/newsletter.md` (60w) and `content/privacy-policy.md` (764w).

---

### 301 Permanent Redirect Map Table

The table below outlines the canonical target mapping and redirect rules for pruned and merged content:

| Source URL (Pruned / Merged Page) | Action Type | Target Canonical URL (Consolidated Pillar Hub) | Redirect Code | Strategic Rationale |
|---|---|---|---|---|
| `/newsletter/` | Merge | `/hire/` | 301 Permanent | `newsletter.md` (60w) is thin. Merge conversion intent into `/hire/` newsletter CTA block. |
| `/privacy-policy/` | Consolidation | `/about/` (or Footer modal) | 301 Permanent | Low traffic utility page (764w). Consolidate sitewide policy info into `about.md`. |
| `/radar/2026-04/radar-2026-04-14/` | Digest Merge | `/radar/2026-04/` | 301 Permanent | Consolidate daily briefing into April 2026 Tech Radar Digest hub. |
| `/radar/2026-05/radar-2026-05-03/` | Digest Merge | `/radar/2026-05/` | 301 Permanent | Consolidate thin daily briefing (717w) into May 2026 Tech Radar Digest hub. |
| `/radar/2026-06/radar-2026-06-06/` | Digest Merge | `/radar/2026-06/` | 301 Permanent | Consolidate thin daily briefing into June 2026 Tech Radar Digest hub. |
| `/radar/2026-07/radar-2026-07-01/` | Digest Merge | `/radar/2026-07/` | 301 Permanent | Consolidate thin daily briefing into July 2026 Tech Radar Digest hub. |
| `/series/prompt-standard/part-1/` | Series Merge | `/series/prompt-standard/` | 301 Permanent | Merge thin sub-part (<800w) into unified Prompt Standard master guide. |
| `/series/prompt-standard/part-2/` | Series Merge | `/series/prompt-standard/` | 301 Permanent | Merge thin sub-part (<800w) into unified Prompt Standard master guide. |
| `/series/composable-commerce-migration/part-1/` | Series Merge | `/posts/ecommerce-architecture-composable-migration/` | 301 Permanent | Consolidate thin series part into main Composable Commerce migration pillar post. |
| `/series/ecommerce-order-allocation/part-1/` | Series Merge | `/posts/order-fulfillment-algorithm-warehouse-last-mile/` | 301 Permanent | Consolidate thin order allocation snippet into main Order Fulfillment pillar post. |
| `/series/high-concurrency-systems/article_1_system_design/` | Series Merge | `/posts/shopee-flash-sale-architecture/` | 301 Permanent | Consolidate thin high-concurrency intro into Shopee Flash Sale pillar post. |
| `/series/agentic-system-architecture/part-1/` | Series Merge | `/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/` | 301 Permanent | Consolidate thin agentic architecture intro into Autonomous Hybrid-AI Pipeline post. |
| `/series/ai-driven-playbook/part-1/` | Series Merge | `/posts/ai-native-frontend-architecture-predictions-2028/` | 301 Permanent | Consolidate thin AI playbook snippet into AI-Native Frontend predictions post. |
| `/series/slm-playbook/part-1/` | Series Merge | `/posts/slm-fine-tune-vs-prompt-engineering/` | 301 Permanent | Consolidate thin SLM part into Prompt Engineering vs Fine-Tuning pillar post. |

---

### Implementation Instructions for Server & Hugo Configuration

1. **Hugo Frontmatter Aliases (Repository Level):**
   Add `aliases` to target consolidated pages' frontmatter:
   ```yaml
   aliases:
     - /radar/2026-05/radar-2026-05-03/
     - /series/prompt-standard/part-1/
   ```
2. **Nginx Web Server Directives (`nginx.conf`):**
   ```nginx
   rewrite ^/radar/2026-05/radar-2026-05-03/?$ /radar/2026-05/ permanent;
   rewrite ^/newsletter/?$ /hire/ permanent;
   ```
3. **Netlify / Cloudflare Pages Redirects (`public/_redirects`):**
   ```text
   /radar/2026-05/radar-2026-05-03/  /radar/2026-05/  301
   /newsletter/                      /hire/            301
   ```

---

## Section 3: Pillar Content Reinforcement & Link Topology

### Topology Baseline
The sitewide internal link graph audit revealed **1,856 total internal links** across 338 pages. However, the link distribution is heavily skewed:
- **124 Orphan Pages (36.7% of site):** Received **0 inbound internal links** from markdown body content.
- **85 Over-Linked Pages:** Concentrated excessive inbound/outbound links (e.g. `hire.md` with 125 inbound links, `reading-map.md` with 43 outbound links).

---

### Subsection 3.1: Hub-and-Spoke Architecture Framework

To establish a resilient internal link topology, content will be organized around **10 Anchor Pillar Hubs**. Each Pillar Hub links down to related Series Chapters (Spokes) and Tech Radar Digests, while Spokes link back to their parent Pillar Hub.

```
                    [ vesviet /reading-map/ ]
                                |
       +------------------------+------------------------+
       |                                                 |
[ Go & Microservices ]                        [ AI & Agentic Systems ]
  Pillar: go-microservices.md                   Pillar: hybrid-ai-pipeline.md
       |                                                 |
  +----+----+                                       +----+----+
  |         |                                       |         |
[Spoke 1] [Spoke 2]                               [Spoke 1] [Spoke 2]
```

#### The 10 Anchor Pillar Hubs:
1. `content/posts/go-microservices.md` — Go & Microservices Architecture Hub
2. `content/posts/architecting-21-service-ecommerce-golang-ddd.md` — System Design & E-Commerce Hub
3. `content/posts/aws-eks-vs-ecs-comparison.md` — Cloud Native & Container Infrastructure Hub
4. `content/posts/banking-microservices-architecture.md` — FinTech & Core Banking Systems Hub
5. `content/posts/cloudflare-d1-durable-objects-realtime-cart.md` — Edge Serverless & Cloudflare Hub
6. `content/posts/deploying-astro-on-cloudflare-full-stack-edge-architecture.md` — AI Frontend & Edge Hub
7. `content/posts/generative-ui-with-mcp-ai-native-frontend.md` — Generative UI & MCP Engineering Hub
8. `content/posts/alipay-double-11-architecture-tps.md` — Distributed Systems & High Concurrency Hub
9. `content/reading-map.md` — Sitewide Curated Learning Directory Hub
10. `content/hire.md` — Commercial Architecture Consulting Conversion Hub

---

### Subsection 3.2: Complete 124 Orphan Page Resolution Matrix

The table below defines the exact link injection plan to eliminate all 124 orphan pages by connecting them to parent Pillar Hubs, Series Index pages, and `/reading-map.md`:

| Orphan Page Directory Cluster | Orphan Count | Target Inbound Link Sources (Pillar Hubs & Series Index Pages) | Section in `reading-map.md` for Integration | Strategic Link Anchor Text |
|---|---|---|---|---|
| `content/radar/2026-05/*` | 19 pages | `/radar/2026-05/` (Monthly Digest), `/posts/gitops-at-scale-kubernetes-argocd-microservices/` | `## Tech Radar Archives -> May 2026` | "May 2026 Tech Radar Briefings" |
| `content/radar/2026-04/*` | 16 pages | `/radar/2026-04/` (Monthly Digest), `/posts/mastering-event-driven-architecture-dapr/` | `## Tech Radar Archives -> April 2026` | "April 2026 Tech Radar Briefings" |
| `content/series/high-concurrency-systems/*` | 10 pages | `/posts/architecting-21-service-ecommerce-golang-ddd/`, `/posts/shopee-flash-sale-architecture/` | `## High Concurrency & Systems Architecture` | "High-Concurrency Systems Engineering Guide" |
| `content/series/ai-data-engineering-pipeline/*` | 9 pages | `/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/`, `/posts/exporting-magento-2-data-flat-sql-nodejs/` | `## AI Infrastructure & Data Pipelines` | "Autonomous AI Data Pipeline Architecture" |
| `content/series/modular-monolith-architecture/*` | 9 pages | `/posts/laravel-vs-golang-when-to-add-features/`, `/posts/ecommerce-architecture-composable-migration/` | `## Software Architecture & Modular Monoliths` | "Modular Monolith to Microservices Roadmap" |
| `content/series/routing-geospatial-architecture/*` | 9 pages | `/posts/graphhopper-distance-matrix-production-guide/`, `/posts/real-time-ride-hailing-architecture/` | `## Geospatial Engineering & Routing Engines` | "Geospatial Routing Architecture Matrix" |
| `content/radar/2026-06/*` | 8 pages | `/radar/2026-06/` (Monthly Digest), `/posts/go-pprof-kubernetes-remote-profiling/` | `## Tech Radar Archives -> June 2026` | "June 2026 Tech Radar Briefings" |
| `content/radar/2026-07/*` | 8 pages | `/radar/2026-07/` (Monthly Digest), `/posts/dapr-state-store-consistency-tradeoffs/` | `## Tech Radar Archives -> July 2026` | "July 2026 Tech Radar Briefings" |
| `content/series/alipay-double-11/*` | 8 pages | `/posts/alipay-double-11-architecture-tps/`, `/posts/paypay-architecture-scaling/` | `## High Availability & Financial Scale` | "Alipay 583K TPS High Availability Blueprint" |
| `content/series/generative-ui-architecture/*` | 7 pages | `/posts/generative-ui-with-mcp-ai-native-frontend/`, `/posts/ai-native-frontend-architecture-predictions-2028/` | `## Generative UI & Model Context Protocol` | "Generative UI System Architecture Guide" |
| `content/series/ai-code-review-vibe-coding/*` | 6 pages | `/posts/vibe-coding-and-ai-code-review-future/`, `/posts/go-mcp-server-development-production-guide/` | `## AI-Assisted Engineering & Vibe Coding` | "Multi-Agent AI Code Review Pipeline" |
| `content/series/magento-migration-vietnam/*` | 4 pages | `/posts/magento-development-in-vietnam/`, `/posts/magento-vietnam/` | `## E-Commerce Migration & Software Outsourcing` | "Magento Development & Migration Playbook Vietnam" |
| `content/series/shopee-architecture/*` | 3 pages | `/posts/shopee-flash-sale-architecture/`, `/posts/mysql-scalability-guide/` | `## E-Commerce High-Concurrency Case Studies` | "Shopee Flash Sale Infrastructure Blueprint" |
| Standalone Orphan Posts (7 Files: `cloudflare-zero-devops-ecommerce.md`, `dapr-state-store-consistency-tradeoffs.md`, `database-impact-on-programming-languages.md`, `go-mcp-server-development-production-guide.md`, `laravel-vs-golang-when-to-add-features.md`, `multi-region-geo-distributed-api-routing.md`, `osrm-shared-memory-kubernetes-live-traffic.md`) | 7 pages | Cross-link directly from related Pillar Hubs (e.g. link `cloudflare-zero-devops-ecommerce.md` from `serverless-ecommerce-cloudflare-d1.md`). | `## Featured Technical Pillars` | Exact article title anchors |

---

### Subsection 3.3: Link Rebalancing & Anchor Text Diversification

- **Rebalancing `content/hire.md` (125 Inbound Links):** Currently, `hire.md` receives 125 internal inbound links, predominantly using repetitive "Hire Me" anchor text in article footers.
  - *Action:* Replace site-wide boilerplate footer links with context-sensitive callout blocks (e.g., "Consult on Go Microservices", "Audit your Core Banking Architecture", "Review Cloudflare Edge Migration").
- **Optimizing `content/reading-map.md` (43 Outbound Links):**
  - *Action:* Re-structure `/reading-map.md` into 6 curated visual learning paths (Go Backend, Microservices, AI/MCP, FinTech, Edge Computing, DevOps), embedding links to all series chapters and pillar guides.

---

## Section 4: Sprint Schedule & Operational Roadmap

### 4-Sprint Timeline Overview (8 Weeks Total)

The operational roadmap spans 4 distinct 2-week sprints designed to execute all remediation tasks systematically:

```
[Sprint 1: Weeks 1-2] --> Schema Repair & Upfront GEO Block Rollout (Top 50)
[Sprint 2: Weeks 3-4] --> Content Refresh (9 Posts + Series) to >=1,400 Words
[Sprint 3: Weeks 5-6] --> Link Topology & 124 Orphan Page Elimination
[Sprint 4: Weeks 7-8] --> Tech Radar Digest Merge & Final Automated Audit Sign-Off
```

---

### Sprint 1 (Weeks 1–2): Schema Repair, GEO Baseline & Technical Debt
- **Objective:** Eliminate frontmatter metadata debt and establish GEO/AEO answer-first formatting across top-tier pages.
- **Key Tasks:**
  1. Fix schema metadata (`tags`, `categories`, `cover`) across 159 incomplete files (including 4 standalone pillar posts: `dapr-state-store-consistency-tradeoffs.md`, `high-throughput-go-framework-benchmarks-gin-fiber-kratos.md`, `multi-region-geo-distributed-api-routing.md`, `temporal-saga-pattern-golang-distributed-transactions.md`).
  2. Implement Hugo aliases and server-level 301 redirects for `newsletter.md` and `privacy-policy.md`.
  3. Add `> **Answer-first:**` summary blocks to top 50 post pages.
- **Sprint 1 Deliverable:** 100% schema validation pass script execution; zero frontmatter errors.

---

### Sprint 2 (Weeks 3–4): Content Refresh & Technical Depth Expansion
- **Objective:** Expand all underperforming articles to ≥ 1,400 words with rich technical code, diagrams, and benchmarks.
- **Key Tasks:**
  1. Execute technical content rewrites for the 9 standalone refresh posts (adding Go structs, Qdrant gRPC code, Argo CD 3.4 manifests, OSRM sysctl configs, Uber H3 math).
  2. Expand 102 underperforming series sub-articles to ≥ 1,400 words.
  3. Complete GEO/AEO answer block rollout across remaining 223 pages.
- **Sprint 2 Deliverable:** 100% of standalone posts and active series parts satisfy word count baseline (≥ 1,400w).

---

### Sprint 3 (Weeks 5–6): Link Topology & Orphan Elimination
- **Objective:** Connect all 124 orphan pages to Pillar Hubs and re-architect sitewide internal link topology.
- **Key Tasks:**
  1. Execute internal link injection matrix connecting 124 orphan series and radar pages to 10 Anchor Pillar Hubs.
  2. Re-architect `/content/reading-map.md` into 6 curated visual learning paths.
  3. Diversify anchor text links pointing to `/hire/` across all post footer conversion blocks.
- **Sprint 3 Deliverable:** Link crawler verification confirms **0 orphan pages** remaining on site.

---

### Sprint 4 (Weeks 7–8): Tech Radar Consolidation & Final Audit Sign-Off
- **Objective:** Consolidate daily tech radar briefings and execute end-to-end automated quality checks.
- **Key Tasks:**
  1. Merge 46 thin daily tech radar briefings into 4 monthly Tech Radar Digest hubs (`2026-04`, `2026-05`, `2026-06`, `2026-07`).
  2. Deploy 301 permanent redirects for consolidated daily radar URLs.
  3. Execute automated verification test suite: Hugo build test, JSON schema validation, dead link crawler, and word count scanner.
- **Sprint 4 Deliverable:** Final publication-ready sign-off artifact; 100% green CI pipeline build.

---

## Verification & Sign-Off Protocol

To independently verify the completeness and execution of this content roadmap:
1. **File Location Verification:** Verify that `/home/user/personalized/vesviet/content-roadmap.md` exists and is non-empty.
2. **Schema Validator Execution:** Run `python3 -c "import json; data=json.load(open('.agents/teamwork_preview_explorer_m1_3/audit_part3.json'))"` to verify repository state.
3. **Hugo Clean Build:** Run `hugo --gc --minify` in `/home/user/personalized/vesviet/` to confirm zero build warnings or broken aliases.
