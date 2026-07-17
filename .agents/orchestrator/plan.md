# Project Plan: System Design Articles Sprint

This plan details the implementation strategy for creating three system design articles under the Hugo content directory `content/posts/` of the `vesviet` workspace.

## Objectives
Write and publish 3 technical system design articles matching SEO and E-E-A-T criteria:
1. `dapr-state-store-consistency-tradeoffs`
2. `multi-region-geo-distributed-api-routing`
3. `high-throughput-go-framework-benchmarks-gin-fiber-kratos`

Each article must:
- Be >= 1,400 prose words.
- Contain `ShowToc: true`, `TocOpen: true` and appropriate metadata dates in `+07:00`.
- Open with the specified Answer-first block (<= 60 words).
- Integrate raw files (YAML, Go, Terraform, Mermaid) from `_internal/research/`.
- Feature the FAQ Q&A from `research_qa_system_design.md` at the end.
- Include proper internal links per briefs.
- Pass the local verification suite (`python3 _internal/verify_posts.py`).

## Milestones

| ID | Milestone Name | Focus | Output / Verification | Status |
|----|----------------|-------|-----------------------|--------|
| M1 | Discovery & Plan Setup | Setup PROJECT.md, plan.md, and read inputs | plan.md & progress.md | **COMPLETE** |
| M2 | Article 1 Creation | Dapr State Store consistency post | `content/posts/dapr-state-store-consistency-tradeoffs.md` | **COMPLETE** |
| M3 | Article 2 Creation | Multi-region Geo-distributed routing post | `content/posts/multi-region-geo-distributed-api-routing.md` | **COMPLETE** |
| M4 | Article 3 Creation | High-throughput Go framework benchmarks post | `content/posts/high-throughput-go-framework-benchmarks-gin-fiber-kratos.md` | **COMPLETE** |
| M5 | Cross-Verification & Audit | Run `verify_posts.py`, review via Content Manager, run Forensic Audit | Passing checks & `posts_audit_report.json` | **COMPLETE** |

## Detailed Milestone Execution

### M2: Article 1 - Dapr State Store consistency
- **Worker Prompt**: Write `dapr-state-store-consistency-tradeoffs.md` using the SEO brief and Topic 1 Q&A.
- **Assets to Integrate**: `_internal/research/dapr/dapr-redis-state.yaml`, `_internal/research/dapr/dapr-cockroach-state.yaml`, `_internal/research/dapr/dapr-occ-flow.mermaid`.
- **Word count**: >=1400 prose words.

### M3: Article 2 - Multi-region routing
- **Worker Prompt**: Write `multi-region-geo-distributed-api-routing.md` using the SEO brief and Topic 2 Q&A.
- **Assets to Integrate**: `_internal/research/routing/geo-routing-flow.mermaid`, `_internal/research/routing/latency-routing.tf`.
- **Word count**: >=1400 prose words.

### M4: Article 3 - Go benchmarks
- **Worker Prompt**: Write `high-throughput-go-framework-benchmarks-gin-fiber-kratos.md` using the SEO brief and Topic 3 Q&A.
- **Assets to Integrate**: `_internal/research/go-benchmarks/benchmark_test.go`, `_internal/research/go-benchmarks/k6-load-test.js`, `_internal/research/go-benchmarks/wrk_header.lua`.
- **Word count**: >=1400 prose words.

### M5: Cross-Verification & Audit
- **Verify**: Run `verify_posts.py` to check for broken links, word counts, and formatting.
- **Reviewer**: Verify content flow and layout against requirements.
- **Auditor**: Run forensic integrity checks.
