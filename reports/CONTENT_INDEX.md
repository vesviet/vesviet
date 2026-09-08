# Vesviet Content Index (tanhdev.com)

> Snapshot date: 2026-09-08 · Branch `main` @ `f4e1e62` · Total content files: **367**
> Site: Hugo + PaperMod, `en` default, canonical host `https://tanhdev.com/`
> English flagship portfolio. Regenerate this index after every batch upgrade.

## Corpus At A Glance

| Section | Files | Notes |
|---|---|---|
| `content/posts/` | 66 | 61 with Answer-first; 5 legacy missing |
| `content/series/` | 246 | 25 series (mirrors `learn` set, minus `prompt-standard` reduced to 7) |
| `content/radar/` | 33 | 26 radar editions 2026-04 → 2026-09 + 7 `_index.md` |
| `content/categories/` | 15 | ai, architecture, backend, cloudflare, database, devops, e-commerce, engineering, fintech, golang, kubernetes, microservices, observability, payments, tech-radar |
| Root pages | ~7 | `_index`, `about`, `hire`, `reading-map`, `categories`, `legal-notice`, `terms-of-service`, `privacy-policy` |

## Anchor Pillar Hubs (link topology backbone)

The 10 hubs from `agent-skills/overlays/vesviet-content/rules/link-topology.md` map to live files:

1. `posts/go-microservices.md` — Go & Microservices Architecture Hub
2. `posts/architecting-21-service-ecommerce-golang-ddd.md` — System Design & E-Commerce Hub
3. `posts/aws-eks-vs-ecs-comparison.md` — Cloud Native & Container Infrastructure Hub
4. `posts/banking-microservices-architecture.md` — FinTech & Core Banking Hub
5. `posts/cloudflare-d1-durable-objects-realtime-cart.md` — Edge Serverless & Cloudflare Hub
6. `posts/deploying-astro-on-cloudflare-full-stack-edge-architecture.md` — AI Frontend & Edge Hub
7. `posts/generative-ui-with-mcp-ai-native-frontend.md` — Generative UI & MCP Hub
8. `posts/alipay-double-11-architecture-tps.md` — Distributed Systems & High Concurrency Hub
9. `reading-map.md` — Sitewide Curated Learning Directory (6 pillars, 57 essays)
10. `hire.md` — Commercial Consulting Conversion Hub

## Radar Editions (Tech Radar)

| Month | Editions | Highlights |
|---|---|---|
| 2026-04 | 9 | Claude Sonnet, Mistral Small, Creative MCP |
| 2026-05 | 3 | DigitalOcean AI-native cloud, Gateway API v1.5 |
| 2026-06 | 3 | — |
| 2026-07 | 3 | — |
| 2026-08 | 7 | Stateless MCP K8s gateway, OWASP/NIST AI agent gateway, Go synctest, vLLM context routing MLA, eBPF Tetragon agent security |
| 2026-09 | 2 | WASI 0.3 component model/wasmtime, DeepSeek v3 MLA |

## Recent Upgrade Campaigns (git log)

| Commit | Campaign |
|---|---|
| `f4e1e62` | Upgrade 10 architecture/systems engineering posts to masterclass guides |
| `7102a4d` | AdSense replicated-content remediation, bidirectional hreflang, E-E-A-T unification |
| `434872b` | Series Part 10 Envoy vs Cilium, hreflang + Cloudflare Edge redirect map |
| `d87b844` | Legacy series aliases, relative links, chapter navigation fixes |
| `b568289` | Phase 2 AEO definitions, technical FAQs, contextual backlinks |
| `97e87c3` | 6 playbooks translated to pure English; one-way SEO authority flow enforced |

## Masterclass Twin Mapping (learn ⇄ vesviet)

Each flagship topic exists as a Vietnamese twin on `learn` (canonical there for notes) and an expanded English masterclass on `vesviet` (authority site). Recent Batch 5 upgrades synchronized: `alipay-double-11-architecture-tps`, `banking-microservices-architecture`, `composable-banking-architecture`, `dapr-workflow-saga-orchestration-guide`, NATS JetStream CQRS, strangler fig, gRPC production, SPIFFE/SPIRE zero-trust, K8s operators/eBPF/Cilium, pprof remote profiling, D1 durable objects cart, Astro edge, Go 1.26 GC, zero-alloc tuning, goroutine leaks, framework benchmarks, vector DB HNSW, MCP servers, generative UI, GraphRAG.

## Compliance Snapshot

| Gate | Status |
|---|---|
| Answer-first block | 61/66 posts, 244/246 series files, 14/33 radar editions (older radars exempt) |
| Frontmatter schema | ~100% (audits in `reports/` are green; `content-audit-report.json`: 275 files scanned, 0 spam) |
| Word depth | Flagships 4,600+ words post-upgrade |
| Mermaid | 56 posts |
| Orphan policy | 0 orphans per latest crawls; `reading-map.md` curates 6 learning pillars |
| One-way authority | `vesviet` → no links to `learn.tanhdev.com` (0 occurrences); keep it one-way |

## Known Gaps (next sprint candidates)

1. 5 posts missing Answer-first: `beyond-quick-commerce-15s`, `deploying-autonomous-ai-swarm-openclaw-litellm`, `golang-pprof-profiling-memory-cpu-tutorial`, `mysql-horizontal-scaling`, `urban-canyon-gps-multipath-map-matching-architecture`, `go-microservices.md` + tracing + MCP + pprof remote (verify against current list: 5 files total).
2. `prompt-standard` series has 7 English parts vs 16 Vietnamese — candidate for translation completion.
3. Radar pre-2026-08 editions lack Answer-first (acceptable per radar format) but check `mermaid`/frontmatter consistency.
4. `content-audit-report.json` last full scan covered 275 files vs 367 now — rerun `reports/check_posts.py` after next batch.
