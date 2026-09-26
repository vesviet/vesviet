# Master Reports Catalog — Vesviet Technical Corpus (tanhdev.com)

> **Publication Date**: 2026-09-26  
> **Corpus Authority**: Vesviet Engineering & Content Operations  
> **Scope**: `vesviet/reports/` (Flagship Technical Portfolio)  
> **Language**: English (`en-us`)  
> **Total Cataloged Assets**: **356 files** (313 Deep Research Dossiers, 17 Series Indexes, 9 GSC Audits/SOPs, 15 Editorial/Governance Audits, 2 Maintenance Scripts)  
> **Total Disk Footprint**: **17.57 MB** | **Total Markdown Word Count**: **795,990 words**  
> **Coverage Epoch**: 2026-07-25 → 2026-09-26  

---

## Executive Summary

The `vesviet/reports/` directory serves as the centralized, immutable research repository and engineering audit backbone for the `tanhdev.com` technical publishing ecosystem. All reporting assets are maintained in a **strictly flat directory hierarchy (0 subdirectories)**. This architectural invariant guarantees 100% link integrity across all published markdown posts in `content/posts/`, series chapters in `content/series/`, technology radar briefs in `content/radar/`, and cross-repository GitHub tree permalinks.

### Corpus Macro Metrics
- **Total Cataloged Files**: 356 files (Post-R2 Hygiene: ephemeral logs purged; Master Catalog integrated).
- **Research Dossier Corpus**: 313 files (157 `.md` narratives + 156 `.json` structured payloads; 729,846 words; 17.01 MB).
- **Series Quality Indexes**: 17 `.md` files (16,846 words; 118.0 KB) covering all 17 flagship technical series with 8-gate quality compliance.
- **Search Console & SEO Audits**: 9 files (6 `.md` + 3 `.json`; 20,124 words; 219.9 KB) covering Google Search Console indexing, crawl health, redirect graphs, and re-validation runbooks.
- **Editorial & Governance Audits**: 15 files (including `CONTENT_INDEX.md`, `radar-corpus-review-2026-09-26.md`, and `REPORTS_MASTER_CATALOG.md`; 29,174 words; 214.4 KB).
- **Automation & Verification Scripts**: 2 Python scripts (23.8 KB) enforcing style guide linting and post-generation quality gates.
- **Link Integrity Guarantee**: 0 broken links sitewide across all 375 content markdown documents.

### Thematic Cluster Architecture
Every asset within `vesviet/reports/` is categorized into one of five rigorous engineering clusters:
1. **Cluster 1: 100-Round Deep Research Dossiers**: Methodological investigations consisting of paired JSON execution records and publication-grade Markdown briefs, spanning 21 multi-part series, 5 standalone 2027 SOTA Masterclass posts, and 3 Tech Radar editions.
2. **Cluster 2: Series Content Indexes (`*-content-index.md`)**: Comprehensive 8-gate quality audit matrices validating Answer-first architecture, Mermaid diagrams, code snippet correctness, internal link equity, and SEO frontmatter.
3. **Cluster 3: Google Search Console (GSC) Audits, Datasets & SOPs**: Authoritative indexing diagnostic logs, redirect graph verifications (422 rules, 0 chains, 0 loops), and GSC Webmaster re-validation SOPs.
4. **Cluster 4: Editorial & Quality Audits**: Structural audits of post length, buzzword compliance, category taxonomic mapping, and content strategy reviews.
5. **Cluster 5: Maintenance & Verification Scripts**: Executable Python harnesses (`check_posts.py`, `generate_report.py`) enforcing automated pre-commit and CI/CD quality standards.

---

## Cluster 1: 100-Round Deep Research Dossiers

Cluster 1 constitutes the intellectual foundation of the platform. Each dossier represents 100 continuous research rounds synthesizing authoritative software architecture, production benchmarks, and architectural tradeoffs. 155 dossiers exist as symmetric `.md` and `.json` pairs, with 1 consolidated multi-phase synthesis (`research-alipay-phases-consolidated-100-rounds.md`).

| # | Dossier Narrative (`.md`) | Companion JSON Payload (`.json`) | Rounds | Associated Series / Post Slug | MD Size | JSON Size | Twin Parity (`learn/`) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---:|
| 1 | `research-agentic-ecommerce-search-executive-summary-100-rounds.md` | `research-agentic-ecommerce-search-executive-summary-100-rounds.json` | 100 | `series/agentic-ecommerce-search/executive-summary.md` | 40.6 KB | 64.6 KB | Mirrored in `learn/` |
| 2 | `research-agentic-ecommerce-search-part-1-golang-orchestration-100-rounds.md` | `research-agentic-ecommerce-search-part-1-golang-orchestration-100-rounds.json` | 100 | `series/agentic-ecommerce-search/part-1-golang-orchestration.md` | 40.8 KB | 64.4 KB | Mirrored in `learn/` |
| 3 | `research-agentic-ecommerce-search-part-2-ingestion-chunking-100-rounds.md` | `research-agentic-ecommerce-search-part-2-ingestion-chunking-100-rounds.json` | 100 | `series/agentic-ecommerce-search/part-2-ingestion-chunking.md` | 41.3 KB | 64.9 KB | Mirrored in `learn/` |
| 4 | `research-agentic-ecommerce-search-part-3-qdrant-hybrid-search-100-rounds.md` | `research-agentic-ecommerce-search-part-3-qdrant-hybrid-search-100-rounds.json` | 100 | `series/agentic-ecommerce-search/part-3-qdrant-hybrid-search.md` | 41.2 KB | 64.9 KB | Mirrored in `learn/` |
| 5 | `research-agentic-ecommerce-search-part-4-active-rag-tool-calling-100-rounds.md` | `research-agentic-ecommerce-search-part-4-active-rag-tool-calling-100-rounds.json` | 100 | `series/agentic-ecommerce-search/part-4-active-rag-tool-calling.md` | 40.5 KB | 63.8 KB | Mirrored in `learn/` |
| 6 | `research-agentic-ecommerce-search-part-5-critique-loop-100-rounds.md` | `research-agentic-ecommerce-search-part-5-critique-loop-100-rounds.json` | 100 | `series/agentic-ecommerce-search/part-5-critique-loop.md` | 41.3 KB | 64.9 KB | Mirrored in `learn/` |
| 7 | `research-agentic-ecommerce-search-part-6-production-operations-100-rounds.md` | `research-agentic-ecommerce-search-part-6-production-operations-100-rounds.json` | 100 | `series/agentic-ecommerce-search/part-6-production-operations.md` | 41.3 KB | 64.9 KB | Mirrored in `learn/` |
| 8 | `research-agentic-system-architecture-executive-summary-100-rounds.md` | `research-agentic-system-architecture-executive-summary-100-rounds.json` | 100 | `series/agentic-system-architecture/executive-summary.md` | 53.1 KB | 57.7 KB | Mirrored in `learn/` |
| 9 | `research-agentic-system-architecture-part-1-topology-100-rounds.md` | `research-agentic-system-architecture-part-1-topology-100-rounds.json` | 100 | `series/agentic-system-architecture/part-1-topology.md` | 47.2 KB | 54.5 KB | Mirrored in `learn/` |
| 10 | `research-agentic-system-architecture-part-2-memory-100-rounds.md` | `research-agentic-system-architecture-part-2-memory-100-rounds.json` | 100 | `series/agentic-system-architecture/part-2-memory.md` | 46.6 KB | 53.8 KB | Mirrored in `learn/` |
| 11 | `research-agentic-system-architecture-part-3-tool-calling-100-rounds.md` | `research-agentic-system-architecture-part-3-tool-calling-100-rounds.json` | 100 | `series/agentic-system-architecture/part-3-tool-calling.md` | 46.4 KB | 53.4 KB | Mirrored in `learn/` |
| 12 | `research-agentic-system-architecture-part-4-agentops-100-rounds.md` | `research-agentic-system-architecture-part-4-agentops-100-rounds.json` | 100 | `series/agentic-system-architecture/part-4-agentops.md` | 46.5 KB | 53.0 KB | Mirrored in `learn/` |
| 13 | `research-agentic-system-architecture-part-5-agent-evals-100-rounds.md` | `research-agentic-system-architecture-part-5-agent-evals-100-rounds.json` | 100 | `series/agentic-system-architecture/part-5-agent-evals.md` | 46.0 KB | 53.6 KB | Mirrored in `learn/` |
| 14 | `research-agentic-system-architecture-part-6-human-in-the-loop-100-rounds.md` | `research-agentic-system-architecture-part-6-human-in-the-loop-100-rounds.json` | 100 | `series/agentic-system-architecture/part-6-human-in-the-loop.md` | 48.2 KB | 53.5 KB | Mirrored in `learn/` |
| 15 | `research-ai-code-review-vibe-coding-executive-summary-100-rounds.md` | `research-ai-code-review-vibe-coding-executive-summary-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/executive-summary.md` | 45.8 KB | 125.7 KB | Mirrored in `learn/` |
| 16 | `research-ai-code-review-vibe-coding-part-1-vibe-coding-paradigm-100-rounds.md` | `research-ai-code-review-vibe-coding-part-1-vibe-coding-paradigm-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/part-1-vibe-coding-paradigm.md` | 43.2 KB | 121.4 KB | Mirrored in `learn/` |
| 17 | `research-ai-code-review-vibe-coding-part-2-context-engineering-100-rounds.md` | `research-ai-code-review-vibe-coding-part-2-context-engineering-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/part-2-context-engineering.md` | 45.1 KB | 123.9 KB | Mirrored in `learn/` |
| 18 | `research-ai-code-review-vibe-coding-part-3-ai-bug-taxonomy-100-rounds.md` | `research-ai-code-review-vibe-coding-part-3-ai-bug-taxonomy-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy.md` | 44.5 KB | 122.5 KB | Mirrored in `learn/` |
| 19 | `research-ai-code-review-vibe-coding-part-4-multi-agent-review-pipeline-100-rounds.md` | `research-ai-code-review-vibe-coding-part-4-multi-agent-review-pipeline-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/part-4-multi-agent-review-pipeline.md` | 45.6 KB | 123.6 KB | Mirrored in `learn/` |
| 20 | `research-ai-code-review-vibe-coding-part-5-ai-code-security-supply-chain-100-rounds.md` | `research-ai-code-review-vibe-coding-part-5-ai-code-security-supply-chain-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/part-5-ai-code-security-supply-chain.md` | 45.8 KB | 125.4 KB | Mirrored in `learn/` |
| 21 | `research-ai-code-review-vibe-coding-part-6-governance-career-100-rounds.md` | `research-ai-code-review-vibe-coding-part-6-governance-career-100-rounds.json` | 100 | `series/ai-code-review-vibe-coding/part-6-governance-career.md` | 44.8 KB | 123.4 KB | Mirrored in `learn/` |
| 22 | `research-ai-data-engineering-pipeline-100-rounds.md` | `research-ai-data-engineering-pipeline-100-rounds.json` | 100 | `series/ai-data-engineering-pipeline/` | 42.8 KB | 67.3 KB | **Exclusive to `vesviet/`** |
| 23 | `research-ai-driven-engineer-100-rounds.md` | `research-ai-driven-engineer-100-rounds.json` | 100 | `series/ai-driven-engineer/` | 37.8 KB | 63.5 KB | **Exclusive to `vesviet/`** |
| 24 | `research-ai-driven-playbook-100-rounds.md` | `research-ai-driven-playbook-100-rounds.json` | 100 | `series/ai-driven-playbook/` | 33.5 KB | 38.1 KB | **Exclusive to `vesviet/`** |
| 25 | `research-alipay-double-11-100-rounds.md` | `research-alipay-double-11-100-rounds.json` | 100 | `series/alipay-double-11/` | 3.1 KB | 91.2 KB | Mirrored in `learn/` |
| 26 | `research-alipay-executive-summary-100-rounds.md` | `research-alipay-executive-summary-100-rounds.json` | 100 | `series/alipay-double-11/executive-summary.md` | 8.5 KB | 7.6 KB | Mirrored in `learn/` |
| 27 | `research-alipay-modern-tech-comparison-100-rounds.md` | `research-alipay-modern-tech-comparison-100-rounds.json` | 100 | `alipay-modern-tech-comparison` | 8.5 KB | 7.6 KB | Mirrored in `learn/` |
| 28 | `research-alipay-phase-1-timeline-100-rounds.md` | `research-alipay-phase-1-timeline-100-rounds.json` | 100 | `series/alipay-double-11/phase-1-timeline.md` | 7.9 KB | 6.7 KB | Mirrored in `learn/` |
| 29 | `research-alipay-phase-2-architecture-100-rounds.md` | `research-alipay-phase-2-architecture-100-rounds.json` | 100 | `series/alipay-double-11/phase-2-architecture.md` | 8.1 KB | 7.0 KB | Mirrored in `learn/` |
| 30 | `research-alipay-phase-3-operations-100-rounds.md` | `research-alipay-phase-3-operations-100-rounds.json` | 100 | `series/alipay-double-11/phase-3-operations.md` | 8.1 KB | 7.1 KB | Mirrored in `learn/` |
| 31 | `research-alipay-phase-4a-technology-100-rounds.md` | `research-alipay-phase-4a-technology-100-rounds.json` | 100 | `series/alipay-double-11/phase-4-technology.md` | 8.0 KB | 6.9 KB | Mirrored in `learn/` |
| 32 | `research-alipay-phase-4b-deep-dive-100-rounds.md` | `research-alipay-phase-4b-deep-dive-100-rounds.json` | 100 | `series/alipay-double-11/phase-4-deep-dive.md` | 8.3 KB | 7.3 KB | Mirrored in `learn/` |
| 33 | `research-alipay-phase-5-synthesis-100-rounds.md` | `research-alipay-phase-5-synthesis-100-rounds.json` | 100 | `series/alipay-double-11/phase-5-synthesis.md` | 8.1 KB | 7.0 KB | Mirrored in `learn/` |
| 34 | `research-alipay-phases-consolidated-100-rounds.md` | *None (Consolidated)* | 800 | `series/alipay-double-11/ (Consolidated Synthesis)` | 7.5 KB | — | Mirrored in `learn/` |
| 35 | `research-beyond-quick-commerce-15-second-customer-intelligence-architecture-100-rounds.md` | `research-beyond-quick-commerce-15-second-customer-intelligence-architecture-100-rounds.json` | 100 | `posts/beyond-quick-commerce-15-second-customer-intelligence-architecture.md` | 54.9 KB | 139.2 KB | Mirrored in `learn/` |
| 36 | `research-core-banking-architecture-100-rounds.md` | `research-core-banking-architecture-100-rounds.json` | 100 | `series/core-banking-architecture/` | 32.9 KB | 52.0 KB | Mirrored in `learn/` |
| 37 | `research-core-banking-developer-100-rounds.md` | `research-core-banking-developer-100-rounds.json` | 100 | `series/core-banking-architecture/developer-guide.md` | 33.3 KB | 38.0 KB | Mirrored in `learn/` |
| 38 | `research-core-banking-part-1-double-entry-ledger-schema-100-rounds.md` | `research-core-banking-part-1-double-entry-ledger-schema-100-rounds.json` | 100 | `series/core-banking-architecture/part-1-double-entry-ledger-schema.md` | 59.7 KB | 81.3 KB | Mirrored in `learn/` |
| 39 | `research-core-banking-part-1-double-entry-ledger-schema-immutability-100-rounds.md` | `research-core-banking-part-1-double-entry-ledger-schema-immutability-100-rounds.json` | 100 | `series/core-banking-architecture/part-1-double-entry-ledger-schema-immutability.md` | 59.7 KB | 81.3 KB | Mirrored in `learn/` |
| 40 | `research-core-banking-part-2-distributed-sql-acid-latency-100-rounds.md` | `research-core-banking-part-2-distributed-sql-acid-latency-100-rounds.json` | 100 | `series/core-banking-architecture/part-2-distributed-sql-acid-latency.md` | 58.3 KB | 79.8 KB | Mirrored in `learn/` |
| 41 | `research-core-banking-part-2-distributed-sql-multiregion-acid-latency-raft-100-rounds.md` | `research-core-banking-part-2-distributed-sql-multiregion-acid-latency-raft-100-rounds.json` | 100 | `series/core-banking-architecture/part-2-distributed-sql-acid-latency.md` | 58.3 KB | 79.8 KB | Mirrored in `learn/` |
| 42 | `research-core-banking-part-3-event-sourcing-cqrs-100-rounds.md` | `research-core-banking-part-3-event-sourcing-cqrs-100-rounds.json` | 100 | `series/core-banking-architecture/part-3-event-sourcing-cqrs.md` | 58.6 KB | 79.9 KB | Mirrored in `learn/` |
| 43 | `research-core-banking-part-3-event-sourcing-cqrs-nats-jetstream-outbox-100-rounds.md` | `research-core-banking-part-3-event-sourcing-cqrs-nats-jetstream-outbox-100-rounds.json` | 100 | `series/core-banking-architecture/part-3-event-sourcing-cqrs-nats-jetstream-outbox.md` | 58.6 KB | 79.9 KB | Mirrored in `learn/` |
| 44 | `research-core-banking-part-4-saga-pattern-100-rounds.md` | `research-core-banking-part-4-saga-pattern-100-rounds.json` | 100 | `series/core-banking-architecture/part-4-saga-pattern.md` | 57.3 KB | 78.7 KB | Mirrored in `learn/` |
| 45 | `research-core-banking-part-4-saga-pattern-distributed-compensation-100-rounds.md` | `research-core-banking-part-4-saga-pattern-distributed-compensation-100-rounds.json` | 100 | `series/core-banking-architecture/part-4-saga-pattern-distributed-compensation.md` | 57.3 KB | 78.7 KB | Mirrored in `learn/` |
| 46 | `research-core-banking-part-5-iso-20022-financial-messaging-payment-gateways-100-rounds.md` | `research-core-banking-part-5-iso-20022-financial-messaging-payment-gateways-100-rounds.json` | 100 | `series/core-banking-architecture/part-5-iso-20022-payment-gateways.md` | 58.9 KB | 80.4 KB | Mirrored in `learn/` |
| 47 | `research-core-banking-part-5-iso-20022-payment-gateways-100-rounds.md` | `research-core-banking-part-5-iso-20022-payment-gateways-100-rounds.json` | 100 | `series/core-banking-architecture/part-5-iso-20022-payment-gateways.md` | 58.9 KB | 80.4 KB | Mirrored in `learn/` |
| 48 | `research-core-banking-part-6-fapi-2-api-security-100-rounds.md` | `research-core-banking-part-6-fapi-2-api-security-100-rounds.json` | 100 | `series/core-banking-architecture/part-6-fapi-2-api-security.md` | 58.5 KB | 80.1 KB | Mirrored in `learn/` |
| 49 | `research-core-banking-part-6-fapi-2-security-profile-mtls-dpop-100-rounds.md` | `research-core-banking-part-6-fapi-2-security-profile-mtls-dpop-100-rounds.json` | 100 | `series/core-banking-architecture/part-6-fapi-2-api-security.md` | 58.5 KB | 80.1 KB | Mirrored in `learn/` |
| 50 | `research-core-banking-part-7-realtime-streaming-fraud-detection-flink-go-100-rounds.md` | `research-core-banking-part-7-realtime-streaming-fraud-detection-flink-go-100-rounds.json` | 100 | `series/core-banking-architecture/part-7-streaming-fraud-detection.md` | 58.7 KB | 80.3 KB | Mirrored in `learn/` |
| 51 | `research-core-banking-part-7-streaming-fraud-detection-100-rounds.md` | `research-core-banking-part-7-streaming-fraud-detection-100-rounds.json` | 100 | `series/core-banking-architecture/part-7-streaming-fraud-detection.md` | 58.7 KB | 80.3 KB | Mirrored in `learn/` |
| 52 | `research-core-banking-part-8-deterministic-concurrency-testing-go-synctest-100-rounds.md` | `research-core-banking-part-8-deterministic-concurrency-testing-go-synctest-100-rounds.json` | 100 | `series/core-banking-architecture/part-8-qa-sdet-handbook.md` | 57.7 KB | 79.2 KB | Mirrored in `learn/` |
| 53 | `research-core-banking-part-8-qa-sdet-handbook-100-rounds.md` | `research-core-banking-part-8-qa-sdet-handbook-100-rounds.json` | 100 | `series/core-banking-architecture/part-8-qa-sdet-handbook.md` | 57.7 KB | 79.2 KB | Mirrored in `learn/` |
| 54 | `research-cornerstone-technologies-executive-summary-100-rounds.md` | `research-cornerstone-technologies-executive-summary-100-rounds.json` | 100 | `series/cornerstone-technologies/executive-summary.md` | 43.9 KB | 66.6 KB | Mirrored in `learn/` |
| 55 | `research-cornerstone-technologies-part-1-nats-jetstream-100-rounds.md` | `research-cornerstone-technologies-part-1-nats-jetstream-100-rounds.json` | 100 | `series/cornerstone-technologies/part-1-nats-jetstream.md` | 41.5 KB | 64.0 KB | Mirrored in `learn/` |
| 56 | `research-cornerstone-technologies-part-2-temporal-workflow-100-rounds.md` | `research-cornerstone-technologies-part-2-temporal-workflow-100-rounds.json` | 100 | `series/cornerstone-technologies/part-2-temporal-workflow.md` | 42.7 KB | 65.1 KB | Mirrored in `learn/` |
| 57 | `research-cornerstone-technologies-part-3-zero-trust-microservices-100-rounds.md` | `research-cornerstone-technologies-part-3-zero-trust-microservices-100-rounds.json` | 100 | `series/cornerstone-technologies/part-3-zero-trust-microservices.md` | 42.4 KB | 64.9 KB | Mirrored in `learn/` |
| 58 | `research-cornerstone-technologies-part-4-vector-database-qdrant-100-rounds.md` | `research-cornerstone-technologies-part-4-vector-database-qdrant-100-rounds.json` | 100 | `series/cornerstone-technologies/part-4-vector-database-qdrant.md` | 43.3 KB | 66.1 KB | Mirrored in `learn/` |
| 59 | `research-cornerstone-technologies-part-5-cloudflare-workers-edge-100-rounds.md` | `research-cornerstone-technologies-part-5-cloudflare-workers-edge-100-rounds.json` | 100 | `series/cornerstone-technologies/part-5-cloudflare-workers-edge.md` | 44.4 KB | 67.2 KB | Mirrored in `learn/` |
| 60 | `research-deploying-autonomous-ai-swarm-openclaw-litellm-100-rounds.md` | `research-deploying-autonomous-ai-swarm-openclaw-litellm-100-rounds.json` | 100 | `posts/deploying-autonomous-ai-swarm-openclaw-litellm.md` | 55.7 KB | 141.0 KB | Mirrored in `learn/` |
| 61 | `research-ecommerce-order-allocation-100-rounds.md` | `research-ecommerce-order-allocation-100-rounds.json` | 100 | `series/ecommerce-order-allocation/.md` | 8.0 KB | 124.0 KB | Mirrored in `learn/` |
| 62 | `research-ecommerce-order-allocation-executive-summary-100-rounds.md` | `research-ecommerce-order-allocation-executive-summary-100-rounds.json` | 100 | `series/ecommerce-order-allocation/executive-summary.md` | 7.4 KB | 121.4 KB | Mirrored in `learn/` |
| 63 | `research-ecommerce-order-allocation-part-1-100-rounds.md` | `research-ecommerce-order-allocation-part-1-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-1.md` | 7.3 KB | 119.8 KB | Mirrored in `learn/` |
| 64 | `research-ecommerce-order-allocation-part-10-100-rounds.md` | `research-ecommerce-order-allocation-part-10-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-10.md` | 7.4 KB | 124.6 KB | Mirrored in `learn/` |
| 65 | `research-ecommerce-order-allocation-part-2-100-rounds.md` | `research-ecommerce-order-allocation-part-2-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-2.md` | 7.3 KB | 120.9 KB | Mirrored in `learn/` |
| 66 | `research-ecommerce-order-allocation-part-3-100-rounds.md` | `research-ecommerce-order-allocation-part-3-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-3.md` | 7.3 KB | 122.0 KB | Mirrored in `learn/` |
| 67 | `research-ecommerce-order-allocation-part-4-100-rounds.md` | `research-ecommerce-order-allocation-part-4-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-4.md` | 7.3 KB | 122.6 KB | Mirrored in `learn/` |
| 68 | `research-ecommerce-order-allocation-part-5-100-rounds.md` | `research-ecommerce-order-allocation-part-5-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-5.md` | 7.3 KB | 123.4 KB | Mirrored in `learn/` |
| 69 | `research-ecommerce-order-allocation-part-6-100-rounds.md` | `research-ecommerce-order-allocation-part-6-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-6.md` | 7.2 KB | 120.9 KB | Mirrored in `learn/` |
| 70 | `research-ecommerce-order-allocation-part-7-100-rounds.md` | `research-ecommerce-order-allocation-part-7-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-7.md` | 7.2 KB | 121.6 KB | Mirrored in `learn/` |
| 71 | `research-ecommerce-order-allocation-part-8-100-rounds.md` | `research-ecommerce-order-allocation-part-8-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-8.md` | 7.3 KB | 122.4 KB | Mirrored in `learn/` |
| 72 | `research-ecommerce-order-allocation-part-9-100-rounds.md` | `research-ecommerce-order-allocation-part-9-100-rounds.json` | 100 | `series/ecommerce-order-allocation/part-9.md` | 7.4 KB | 123.8 KB | Mirrored in `learn/` |
| 73 | `research-generative-ui-architecture-100-rounds.md` | `research-generative-ui-architecture-100-rounds.json` | 100 | `series/generative-ui-architecture/.md` | 1.8 KB | 32.3 KB | Mirrored in `learn/` |
| 74 | `research-genui-executive-summary-100-rounds.md` | `research-genui-executive-summary-100-rounds.json` | 100 | `genui-executive-summary` | 3.8 KB | 54.4 KB | Mirrored in `learn/` |
| 75 | `research-genui-part-1-beyond-chatbots-100-rounds.md` | `research-genui-part-1-beyond-chatbots-100-rounds.json` | 100 | `genui-part-1-beyond-chatbots` | 3.6 KB | 53.5 KB | Mirrored in `learn/` |
| 76 | `research-genui-part-2-state-management-100-rounds.md` | `research-genui-part-2-state-management-100-rounds.json` | 100 | `genui-part-2-state-management` | 3.6 KB | 54.2 KB | Mirrored in `learn/` |
| 77 | `research-genui-part-3-component-registry-100-rounds.md` | `research-genui-part-3-component-registry-100-rounds.json` | 100 | `genui-part-3-component-registry` | 3.6 KB | 54.4 KB | Mirrored in `learn/` |
| 78 | `research-genui-part-4-security-a11y-100-rounds.md` | `research-genui-part-4-security-a11y-100-rounds.json` | 100 | `genui-part-4-security-a11y` | 3.7 KB | 54.0 KB | Mirrored in `learn/` |
| 79 | `research-genui-part-5-human-in-the-loop-100-rounds.md` | `research-genui-part-5-human-in-the-loop-100-rounds.json` | 100 | `genui-part-5-human-in-the-loop` | 3.6 KB | 53.2 KB | Mirrored in `learn/` |
| 80 | `research-genui-part-6-e2e-testing-edge-100-rounds.md` | `research-genui-part-6-e2e-testing-edge-100-rounds.json` | 100 | `genui-part-6-e2e-testing-edge` | 3.6 KB | 53.5 KB | Mirrored in `learn/` |
| 81 | `research-genui-part-7-reference-repo-migration-100-rounds.md` | `research-genui-part-7-reference-repo-migration-100-rounds.json` | 100 | `genui-part-7-reference-repo-migration` | 3.6 KB | 53.8 KB | Mirrored in `learn/` |
| 82 | `research-golang-pprof-profiling-memory-cpu-tutorial-100-rounds.md` | `research-golang-pprof-profiling-memory-cpu-tutorial-100-rounds.json` | 100 | `posts/golang-pprof-profiling-memory-cpu-tutorial.md` | 55.8 KB | 141.2 KB | Mirrored in `learn/` |
| 83 | `research-high-concurrency-systems-executive-summary-100-rounds.md` | `research-high-concurrency-systems-executive-summary-100-rounds.json` | 100 | `series/high-concurrency-systems/executive-summary.md` | 48.5 KB | 57.9 KB | Mirrored in `learn/` |
| 84 | `research-high-concurrency-systems-part-1-how-systems-handle-c10m-100-rounds.md` | `research-high-concurrency-systems-part-1-how-systems-handle-c10m-100-rounds.json` | 100 | `series/high-concurrency-systems/part-1-how-systems-handle-c10m.md` | 46.8 KB | 54.2 KB | Mirrored in `learn/` |
| 85 | `research-high-concurrency-systems-part-2-caching-vulnerabilities-penetration-breakdown-avalanche-100-rounds.md` | `research-high-concurrency-systems-part-2-caching-vulnerabilities-penetration-breakdown-avalanche-100-rounds.json` | 100 | `series/high-concurrency-systems/part-2-caching-vulnerabilities-penetration-breakdown-avalanche.md` | 47.9 KB | 53.4 KB | Mirrored in `learn/` |
| 86 | `research-high-concurrency-systems-part-3-distributed-rate-limiting-redis-gcra-100-rounds.md` | `research-high-concurrency-systems-part-3-distributed-rate-limiting-redis-gcra-100-rounds.json` | 100 | `series/high-concurrency-systems/part-3-distributed-rate-limiting-redis-gcra.md` | 47.2 KB | 53.3 KB | Mirrored in `learn/` |
| 87 | `research-high-concurrency-systems-part-4-transactional-outbox-pattern-dual-write-100-rounds.md` | `research-high-concurrency-systems-part-4-transactional-outbox-pattern-dual-write-100-rounds.json` | 100 | `series/high-concurrency-systems/part-4-transactional-outbox-pattern-dual-write.md` | 47.6 KB | 52.9 KB | Mirrored in `learn/` |
| 88 | `research-high-concurrency-systems-part-5-golang-database-connection-pool-optimization-100-rounds.md` | `research-high-concurrency-systems-part-5-golang-database-connection-pool-optimization-100-rounds.json` | 100 | `series/high-concurrency-systems/part-5-golang-database-connection-pool-optimization.md` | 44.8 KB | 52.2 KB | Mirrored in `learn/` |
| 89 | `research-high-concurrency-systems-part-6-api-gateway-vs-service-mesh-100-rounds.md` | `research-high-concurrency-systems-part-6-api-gateway-vs-service-mesh-100-rounds.json` | 100 | `series/high-concurrency-systems/part-6-api-gateway-vs-service-mesh.md` | 46.1 KB | 52.5 KB | Mirrored in `learn/` |
| 90 | `research-high-concurrency-systems-part-7-idempotency-api-design-payments-100-rounds.md` | `research-high-concurrency-systems-part-7-idempotency-api-design-payments-100-rounds.json` | 100 | `series/high-concurrency-systems/part-7-idempotency-api-design-payments.md` | 48.4 KB | 52.7 KB | Mirrored in `learn/` |
| 91 | `research-high-concurrency-systems-part-8-distributed-locking-redlock-zookeeper-100-rounds.md` | `research-high-concurrency-systems-part-8-distributed-locking-redlock-zookeeper-100-rounds.json` | 100 | `series/high-concurrency-systems/part-8-distributed-locking-redlock-zookeeper.md` | 45.2 KB | 52.1 KB | Mirrored in `learn/` |
| 92 | `research-high-concurrency-systems-part-9-database-sharding-read-write-splitting-100-rounds.md` | `research-high-concurrency-systems-part-9-database-sharding-read-write-splitting-100-rounds.json` | 100 | `series/high-concurrency-systems/part-9-database-sharding-read-write-splitting.md` | 44.2 KB | 52.2 KB | Mirrored in `learn/` |
| 93 | `research-magento-migration-vietnam-100-rounds.md` | `research-magento-migration-vietnam-100-rounds.json` | 100 | `series/magento-migration-vietnam/` | 57.6 KB | 174.9 KB | Mirrored in `learn/` |
| 94 | `research-mcp-20-agentic-mesh-100-rounds.md` | `research-mcp-20-agentic-mesh-100-rounds.json` | 100 | `radar/2026-09/radar-2026-09-08-mcp-20-agentic-mesh-distributed-systems.md` | 16.0 KB | 4.8 KB | **Exclusive to `vesviet/`** |
| 95 | `research-mcp-engineering-executive-summary-100-rounds.md` | `research-mcp-engineering-executive-summary-100-rounds.json` | 100 | `mcp-engineering-executive-summary` | 30.1 KB | 47.1 KB | Mirrored in `learn/` |
| 96 | `research-mcp-engineering-part-1-protocol-100-rounds.md` | `research-mcp-engineering-part-1-protocol-100-rounds.json` | 100 | `mcp-engineering-part-1-protocol` | 30.2 KB | 47.2 KB | Mirrored in `learn/` |
| 97 | `research-mcp-engineering-part-2-build-100-rounds.md` | `research-mcp-engineering-part-2-build-100-rounds.json` | 100 | `mcp-engineering-part-2-build` | 29.6 KB | 46.7 KB | Mirrored in `learn/` |
| 98 | `research-mcp-engineering-part-3-identity-100-rounds.md` | `research-mcp-engineering-part-3-identity-100-rounds.json` | 100 | `mcp-engineering-part-3-identity` | 29.8 KB | 46.8 KB | Mirrored in `learn/` |
| 99 | `research-mcp-engineering-part-4-gateway-100-rounds.md` | `research-mcp-engineering-part-4-gateway-100-rounds.json` | 100 | `mcp-engineering-part-4-gateway` | 29.0 KB | 46.0 KB | Mirrored in `learn/` |
| 100 | `research-mcp-engineering-part-5-security-100-rounds.md` | `research-mcp-engineering-part-5-security-100-rounds.json` | 100 | `mcp-engineering-part-5-security` | 29.5 KB | 46.5 KB | Mirrored in `learn/` |
| 101 | `research-mcp-engineering-part-6-observability-100-rounds.md` | `research-mcp-engineering-part-6-observability-100-rounds.json` | 100 | `mcp-engineering-part-6-observability` | 28.9 KB | 45.9 KB | Mirrored in `learn/` |
| 102 | `research-mcp-engineering-part-7-enterprise-100-rounds.md` | `research-mcp-engineering-part-7-enterprise-100-rounds.json` | 100 | `mcp-engineering-part-7-enterprise` | 29.4 KB | 46.4 KB | Mirrored in `learn/` |
| 103 | `research-modular-monolith-microservices-reversal-100-rounds.md` | `research-modular-monolith-microservices-reversal-100-rounds.json` | 100 | `series/modular-monolith-architecture/ & posts/microservices-delusion-why-golang-modular-monolith-is-the-destination.md` | 83.9 KB | 154.6 KB | Mirrored in `learn/` |
| 104 | `research-mysql-horizontal-scaling-100-rounds.md` | `research-mysql-horizontal-scaling-100-rounds.json` | 100 | `posts/mysql-horizontal-scaling.md` | 56.8 KB | 143.4 KB | Mirrored in `learn/` |
| 105 | `research-paypay-architecture-100-rounds.md` | `research-paypay-architecture-100-rounds.json` | 100 | `series/paypay-architecture/` | 3.5 KB | 88.6 KB | Mirrored in `learn/` |
| 106 | `research-prompt-standard-executive-summary-100-rounds.md` | `research-prompt-standard-executive-summary-100-rounds.json` | 100 | `series/prompt-standard/executive-summary.md` | 41.7 KB | 55.7 KB | Mirrored in `learn/` |
| 107 | `research-prompt-standard-part-1-what-is-prompt-standard-100-rounds.md` | `research-prompt-standard-part-1-what-is-prompt-standard-100-rounds.json` | 100 | `series/prompt-standard/part-1-what-is-prompt-standard.md` | 37.9 KB | 50.8 KB | Mirrored in `learn/` |
| 108 | `research-prompt-standard-part-2-core-blocks-100-rounds.md` | `research-prompt-standard-part-2-core-blocks-100-rounds.json` | 100 | `series/prompt-standard/part-2-core-blocks.md` | 43.7 KB | 59.5 KB | Mirrored in `learn/` |
| 109 | `research-prompt-standard-part-3-layered-prompt-design-100-rounds.md` | `research-prompt-standard-part-3-layered-prompt-design-100-rounds.json` | 100 | `series/prompt-standard/part-3-layered-prompt-design.md` | 38.7 KB | 50.6 KB | Mirrored in `learn/` |
| 110 | `research-prompt-standard-part-4-versioning-and-evals-100-rounds.md` | `research-prompt-standard-part-4-versioning-and-evals-100-rounds.json` | 100 | `series/prompt-standard/part-4-versioning-and-evals.md` | 36.4 KB | 48.2 KB | Mirrored in `learn/` |
| 111 | `research-prompt-standard-part-5-team-template-100-rounds.md` | `research-prompt-standard-part-5-team-template-100-rounds.json` | 100 | `series/prompt-standard/part-5-team-template.md` | 34.4 KB | 44.1 KB | Mirrored in `learn/` |
| 112 | `research-prompt-standard-part-6-context-engineering-100-rounds.md` | `research-prompt-standard-part-6-context-engineering-100-rounds.json` | 100 | `series/prompt-standard/part-6-context-engineering.md` | 38.6 KB | 52.2 KB | Mirrored in `learn/` |
| 113 | `research-prompt-standard-part-7-declarative-prompting-dspy-100-rounds.md` | `research-prompt-standard-part-7-declarative-prompting-dspy-100-rounds.json` | 100 | `series/prompt-standard/part-7-declarative-prompting-dspy.md` | 37.4 KB | 49.7 KB | Mirrored in `learn/` |
| 114 | `research-prompt-standard-part-8-production-promptops-100-rounds.md` | `research-prompt-standard-part-8-production-promptops-100-rounds.json` | 100 | `series/prompt-standard/part-8-production-promptops.md` | 26.6 KB | 44.6 KB | Mirrored in `learn/` |
| 115 | `research-prompt-standard-part-9-mcp-and-hybrid-rag-100-rounds.md` | `research-prompt-standard-part-9-mcp-and-hybrid-rag-100-rounds.json` | 100 | `series/prompt-standard/part-9-mcp-and-hybrid-rag.md` | 27.1 KB | 45.3 KB | Mirrored in `learn/` |
| 116 | `research-routing-geospatial-part-1-core-algorithms-100-rounds.md` | `research-routing-geospatial-part-1-core-algorithms-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-1-core-algorithms.md` | 57.3 KB | 78.6 KB | Mirrored in `learn/` |
| 117 | `research-routing-geospatial-part-1-osrm-vs-graphhopper-contraction-hierarchies-100-rounds.md` | `research-routing-geospatial-part-1-osrm-vs-graphhopper-contraction-hierarchies-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-1-core-algorithms.md` | 57.3 KB | 78.6 KB | Mirrored in `learn/` |
| 118 | `research-routing-geospatial-part-2-distance-matrix-api-keyset-pagination-100-rounds.md` | `research-routing-geospatial-part-2-distance-matrix-api-keyset-pagination-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-2-environment-setup.md` | 57.3 KB | 78.6 KB | Mirrored in `learn/` |
| 119 | `research-routing-geospatial-part-2-environment-setup-100-rounds.md` | `research-routing-geospatial-part-2-environment-setup-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-2-environment-setup.md` | 57.3 KB | 78.6 KB | Mirrored in `learn/` |
| 120 | `research-routing-geospatial-part-3-spatial-indexing-100-rounds.md` | `research-routing-geospatial-part-3-spatial-indexing-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-3-spatial-indexing.md` | 56.4 KB | 77.5 KB | Mirrored in `learn/` |
| 121 | `research-routing-geospatial-part-3-spatial-indexing-h3-s2-rtree-100-rounds.md` | `research-routing-geospatial-part-3-spatial-indexing-h3-s2-rtree-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-3-spatial-indexing-h3-s2-rtree.md` | 56.4 KB | 77.5 KB | Mirrored in `learn/` |
| 122 | `research-routing-geospatial-part-4-golang-microservices-100-rounds.md` | `research-routing-geospatial-part-4-golang-microservices-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-4-golang-microservices.md` | 58.0 KB | 79.3 KB | Mirrored in `learn/` |
| 123 | `research-routing-geospatial-part-4-valhalla-dynamic-costing-edge-routing-100-rounds.md` | `research-routing-geospatial-part-4-valhalla-dynamic-costing-edge-routing-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-4-golang-microservices.md` | 58.0 KB | 79.3 KB | Mirrored in `learn/` |
| 124 | `research-routing-geospatial-part-5-realtime-vehicle-telemetry-kalman-ingestion-100-rounds.md` | `research-routing-geospatial-part-5-realtime-vehicle-telemetry-kalman-ingestion-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-5-visualization-ui.md` | 58.2 KB | 79.7 KB | Mirrored in `learn/` |
| 125 | `research-routing-geospatial-part-5-visualization-ui-100-rounds.md` | `research-routing-geospatial-part-5-visualization-ui-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-5-visualization-ui.md` | 58.2 KB | 79.7 KB | Mirrored in `learn/` |
| 126 | `research-routing-geospatial-part-6-redis-geospatial-semantic-caching-vector-clustering-100-rounds.md` | `research-routing-geospatial-part-6-redis-geospatial-semantic-caching-vector-clustering-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-6-redis-semantic-caching.md` | 58.6 KB | 80.1 KB | Mirrored in `learn/` |
| 127 | `research-routing-geospatial-part-6-redis-semantic-caching-100-rounds.md` | `research-routing-geospatial-part-6-redis-semantic-caching-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-6-redis-semantic-caching.md` | 58.6 KB | 80.1 KB | Mirrored in `learn/` |
| 128 | `research-routing-geospatial-part-7-load-testing-k6-benchmarks-routing-100-rounds.md` | `research-routing-geospatial-part-7-load-testing-k6-benchmarks-routing-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-7-load-testing-production.md` | 56.6 KB | 78.0 KB | Mirrored in `learn/` |
| 129 | `research-routing-geospatial-part-7-load-testing-production-100-rounds.md` | `research-routing-geospatial-part-7-load-testing-production-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-7-load-testing-production.md` | 56.6 KB | 78.0 KB | Mirrored in `learn/` |
| 130 | `research-routing-geospatial-part-8-zero-downtime-k8s-100-rounds.md` | `research-routing-geospatial-part-8-zero-downtime-k8s-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-8-zero-downtime-k8s.md` | 60.5 KB | 82.3 KB | Mirrored in `learn/` |
| 131 | `research-routing-geospatial-part-8-zero-downtime-k8s-shared-memory-engines-100-rounds.md` | `research-routing-geospatial-part-8-zero-downtime-k8s-shared-memory-engines-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-8-zero-downtime-k8s-shared-memory-engines.md` | 60.5 KB | 82.3 KB | Mirrored in `learn/` |
| 132 | `research-routing-geospatial-part-9-core-algorithms-100-rounds.md` | `research-routing-geospatial-part-9-core-algorithms-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-9-urban-canyon-gps-multipath-map-matching.md` | 56.7 KB | 143.0 KB | Mirrored in `learn/` |
| 133 | `research-routing-geospatial-part-9-urban-canyon-gps-multipath-map-matching-100-rounds.md` | `research-routing-geospatial-part-9-urban-canyon-gps-multipath-map-matching-100-rounds.json` | 100 | `series/routing-geospatial-architecture/part-9-urban-canyon-gps-multipath-map-matching.md` | 56.7 KB | 143.0 KB | Mirrored in `learn/` |
| 134 | `research-sglang-eagle-2-speculative-decoding-100-rounds.md` | `research-sglang-eagle-2-speculative-decoding-100-rounds.json` | 100 | `radar/2026-09/radar-2026-09-23-sglang-eagle-2-speculative-decoding.md` | 3.2 KB | 66.0 KB | Mirrored in `learn/` |
| 134b | `research-disaggregated-prefill-decode-100-rounds.md` | `research-disaggregated-prefill-decode-100-rounds.json` | 100 | `radar/2026-09/radar-2026-09-26-disaggregated-prefill-decode.md` | 4.3 KB | 48.0 KB | Mirrored in `learn/` |
| 135 | `research-shopee-architecture-100-rounds.md` | `research-shopee-architecture-100-rounds.json` | 100 | `series/shopee-architecture/` | 33.0 KB | 36.7 KB | Mirrored in `learn/` |
| 136 | `research-slm-playbook-executive-summary-100-rounds.md` | `research-slm-playbook-executive-summary-100-rounds.json` | 100 | `series/slm-playbook/executive-summary.md` | 33.9 KB | 57.3 KB | Mirrored in `learn/` |
| 137 | `research-slm-playbook-part-1-slm-hybrid-architecture-100-rounds.md` | `research-slm-playbook-part-1-slm-hybrid-architecture-100-rounds.json` | 100 | `series/slm-playbook/part-1-slm-hybrid-architecture.md` | 31.4 KB | 54.6 KB | Mirrored in `learn/` |
| 138 | `research-slm-playbook-part-2-sft-data-engineering-100-rounds.md` | `research-slm-playbook-part-2-sft-data-engineering-100-rounds.json` | 100 | `series/slm-playbook/part-2-sft-data-engineering.md` | 32.2 KB | 55.1 KB | Mirrored in `learn/` |
| 139 | `research-slm-playbook-part-3-lora-qlora-tuning-100-rounds.md` | `research-slm-playbook-part-3-lora-qlora-tuning-100-rounds.json` | 100 | `series/slm-playbook/part-3-lora-qlora-tuning.md` | 31.4 KB | 54.4 KB | Mirrored in `learn/` |
| 140 | `research-slm-playbook-part-4-knowledge-distillation-r1-100-rounds.md` | `research-slm-playbook-part-4-knowledge-distillation-r1-100-rounds.json` | 100 | `series/slm-playbook/part-4-knowledge-distillation-r1.md` | 31.7 KB | 54.6 KB | Mirrored in `learn/` |
| 141 | `research-slm-playbook-part-5-preference-alignment-100-rounds.md` | `research-slm-playbook-part-5-preference-alignment-100-rounds.json` | 100 | `series/slm-playbook/part-5-preference-alignment.md` | 31.9 KB | 54.8 KB | Mirrored in `learn/` |
| 142 | `research-slm-playbook-part-6-vllm-deployment-evals-100-rounds.md` | `research-slm-playbook-part-6-vllm-deployment-evals-100-rounds.json` | 100 | `series/slm-playbook/part-6-vllm-deployment-evals.md` | 32.4 KB | 55.7 KB | Mirrored in `learn/` |
| 143 | `research-slm-playbook-sota-standards-100-rounds.md` | `research-slm-playbook-sota-standards-100-rounds.json` | 100 | `series/slm-playbook/sota-standards.md` | 61.1 KB | 112.2 KB | Mirrored in `learn/` |
| 144 | `research-system-design-01-introduction-system-design-golang-100-rounds.md` | `research-system-design-01-introduction-system-design-golang-100-rounds.json` | 100 | `series/system-design/01-introduction-system-design-golang.md` | 56.1 KB | 76.3 KB | Mirrored in `learn/` |
| 145 | `research-system-design-02-load-balancing-api-gateway-go-100-rounds.md` | `research-system-design-02-load-balancing-api-gateway-go-100-rounds.json` | 100 | `series/system-design/02-load-balancing-api-gateway-go.md` | 56.2 KB | 76.4 KB | Mirrored in `learn/` |
| 146 | `research-system-design-03-caching-strategies-redis-golang-100-rounds.md` | `research-system-design-03-caching-strategies-redis-golang-100-rounds.json` | 100 | `series/system-design/03-caching-strategies-redis-golang.md` | 58.1 KB | 78.5 KB | Mirrored in `learn/` |
| 147 | `research-system-design-04-database-scaling-sharding-100-rounds.md` | `research-system-design-04-database-scaling-sharding-100-rounds.json` | 100 | `series/system-design/04-database-scaling-sharding.md` | 57.5 KB | 77.8 KB | Mirrored in `learn/` |
| 148 | `research-system-design-05-async-message-queues-kafka-go-100-rounds.md` | `research-system-design-05-async-message-queues-kafka-go-100-rounds.json` | 100 | `series/system-design/05-async-message-queues-kafka-go.md` | 58.9 KB | 79.5 KB | Mirrored in `learn/` |
| 149 | `research-system-design-06-distributed-locks-concurrency-100-rounds.md` | `research-system-design-06-distributed-locks-concurrency-100-rounds.json` | 100 | `series/system-design/06-distributed-locks-concurrency.md` | 59.6 KB | 80.2 KB | Mirrored in `learn/` |
| 150 | `research-system-design-07-idempotency-api-design-go-100-rounds.md` | `research-system-design-07-idempotency-api-design-go-100-rounds.json` | 100 | `series/system-design/07-idempotency-api-design-go.md` | 57.7 KB | 78.1 KB | Mirrored in `learn/` |
| 151 | `research-system-design-08-saga-pattern-distributed-transactions-go-100-rounds.md` | `research-system-design-08-saga-pattern-distributed-transactions-go-100-rounds.json` | 100 | `series/system-design/08-saga-pattern-distributed-transactions-go.md` | 59.0 KB | 79.5 KB | Mirrored in `learn/` |
| 152 | `research-system-design-09-consistent-hashing-sharding-100-rounds.md` | `research-system-design-09-consistent-hashing-sharding-100-rounds.json` | 100 | `series/system-design/09-consistent-hashing-sharding.md` | 58.7 KB | 79.2 KB | Mirrored in `learn/` |
| 153 | `research-system-design-10-observability-pprof-golang-100-rounds.md` | `research-system-design-10-observability-pprof-golang-100-rounds.json` | 100 | `series/system-design/10-observability-pprof-golang.md` | 57.4 KB | 77.7 KB | Mirrored in `learn/` |
| 154 | `research-system-design-11-security-api-rate-limiting-100-rounds.md` | `research-system-design-11-security-api-rate-limiting-100-rounds.json` | 100 | `series/system-design/11-security-api-rate-limiting.md` | 58.9 KB | 79.4 KB | Mirrored in `learn/` |
| 155 | `research-system-design-12-communication-protocols-microservices-100-rounds.md` | `research-system-design-12-communication-protocols-microservices-100-rounds.json` | 100 | `series/system-design/12-communication-protocols-microservices.md` | 59.5 KB | 80.1 KB | Mirrored in `learn/` |
| 156 | `research-urban-canyon-gps-multipath-map-matching-architecture-100-rounds.md` | `research-urban-canyon-gps-multipath-map-matching-architecture-100-rounds.json` | 100 | `posts/urban-canyon-gps-multipath-map-matching-architecture.md` | 56.7 KB | 143.0 KB | Mirrored in `learn/` |

---

## Cluster 2: Series Content Indexes

Cluster 2 contains 17 standardized series audit indexes (`*-content-index.md`). Each file tracks all chapters in a series against the 8-Gate Quality Assurance standard (Answer-first, Zero AI Buzzwords, Minimum Length, Production Code, Mermaid Architecture Diagrams, Internal Link Equity, Schema Parity, and Research Dossier Mapping).

| # | Index File (`.md`) | Target Series | Size | Word Count | Gate Coverage | Parity (`learn/`) |
|:---:|:---|:---|:---:|:---:|:---|:---:|
| 1 | `agentic-ecommerce-search-content-index.md` | `series/agentic-ecommerce-search/` | 8.4 KB | 1,278 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 2 | `agentic-system-architecture-content-index.md` | `series/agentic-system-architecture/` | 10.0 KB | 1,345 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 3 | `ai-code-review-vibe-coding-content-index.md` | `series/ai-code-review-vibe-coding/` | 10.7 KB | 1,417 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 4 | `alipay-double-11-content-index.md` | `series/alipay-double-11/` | 1.8 KB | 335 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 5 | `core-banking-architecture-content-index.md` | `series/core-banking-architecture/` | 5.9 KB | 751 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 6 | `core-banking-developer-content-index.md` | `series/core-banking-developer/` | 6.2 KB | 662 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 7 | `cornerstone-technologies-content-index.md` | `series/cornerstone-technologies/` | 7.9 KB | 1,186 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 8 | `ecommerce-order-allocation-content-index.md` | `series/ecommerce-order-allocation/` | 6.0 KB | 701 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 9 | `generative-ui-architecture-content-index.md` | `series/generative-ui-architecture/` | 6.4 KB | 812 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 10 | `high-concurrency-systems-content-index.md` | `series/high-concurrency-systems/` | 11.1 KB | 1,420 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 11 | `magento-migration-vietnam-content-index.md` | `series/magento-migration-vietnam/` | 5.1 KB | 1,015 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 12 | `mcp-engineering-in-production-content-index.md` | `series/mcp-engineering-in-production/` | 8.1 KB | 1,292 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 13 | `paypay-architecture-content-index.md` | `series/paypay-architecture/` | 1.5 KB | 274 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 14 | `prompt-standard-content-index.md` | `series/prompt-standard/` | 4.8 KB | 703 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 15 | `shopee-architecture-content-index.md` | `series/shopee-architecture/` | 6.0 KB | 770 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 16 | `slm-playbook-content-index.md` | `series/slm-playbook/` | 8.2 KB | 1,296 words | 8-Gate Audit Matrix | Mirrored in `learn/` |
| 17 | `system-design-content-index.md` | `series/system-design/` | 9.9 KB | 1,589 words | 8-Gate Audit Matrix | Mirrored in `learn/` |

---

## Cluster 3: Google Search Console (GSC) Audits, Datasets & SOPs

Cluster 3 houses diagnostic audits and verification contracts governing Google Search Console indexing health, canonical normalization, 404 eradication, and edge routing compliance.

| # | File Name | Type | Coverage Date | Size | Words | Core Function & Scope | Parity (`learn/`) |
|:---:|:---|:---:|:---:|:---:|:---:|:---|:---:|
| 1 | `GSC_AUDIT_UPGRADE_2026.md` | Audit SOP | 2026-09-17 | 62.4 KB | 6,449 words | Exhaustive site-wide GSC coverage upgrade, redirect audit, and indexation strategy. | **Exclusive to `vesviet/`** |
| 2 | `GSC_INDEXING_AUDIT_2026_09_17.md` | Audit Report | 2026-09-17 | 47.7 KB | 5,145 words | Deep diagnostic of 109 404s, 67 redirect anomalies, and canonical normalization. | Twin of `learn/GSC_COVERAGE_AUDIT_REPORT_2026_09_17.md` |
| 3 | `GSC_INDEXING_AUDIT_2026_09_21.md` | Audit Report | 2026-09-21 | 21.7 KB | 2,705 words | Follow-up crawl audit verifying 46 unindexed URLs and edge routing fixes. | Mirrored in `learn/` |
| 4 | `GSC_INDEXING_AUDIT_2026_09_24.md` | Audit Report | 2026-09-24 | 12.3 KB | 1,770 words | Latest snapshot audit evaluating 20 Crawled-Not-Indexed URLs and internal link equity. | Mirrored in `learn/` |
| 5 | `GSC_PERFORMANCE_AUDIT_REPORT_2026_09_14.md` | Performance Audit | 2026-09-14 | 17.7 KB | 2,495 words | Search query CTR, impressions, average position, and top landing page performance. | Mirrored in `learn/` |
| 6 | `GSC_REVALIDATION_SOP_2026.md` | Standard Runbook | 2026-09-21 | 11.6 KB | 1,560 words | Step-by-step engineer runbook for initiating and monitoring GSC UI re-validation requests. | Mirrored in `learn/` |
| 7 | `seo-audit-report.json` | Data Contract | 2026-09-13 | 39.1 KB | N/A (JSON) | Machine-readable site-wide audit validating metadata, OpenGraph tags, and canonical URLs. | Mirrored in `learn/` |
| 8 | `seo_audit_report_2026_09_13_upgrades.json` | Data Contract | 2026-09-13 | 2.7 KB | N/A (JSON) | Schema delta validation following 2027 SOTA Masterclass standalone post upgrades. | Mirrored in `learn/` |
| 9 | `seo_audit_report_gsc_2026_09_14.json` | Data Contract | 2026-09-14 | 4.8 KB | N/A (JSON) | Programmatic GSC coverage classification mapping URL status to redirect rules. | Mirrored in `learn/` |

---

## Cluster 4: Editorial & Quality Audits

Cluster 4 encompasses editorial management reports, content taxonomy inventories, tone-of-voice compliance audits, and master index records spanning the July–September 2026 publication lifecycle.

| # | File Name | Date | Size | Word Count | Scope & Objectives | Parity (`learn/`) |
|:---:|:---|:---:|:---:|:---:|:---|:---:|
| 1 | `CONTENT_AUDIT_REPORT_2026_09_13.md` | 2026-09-13 | 13.4 KB | 1,575 words | Corpus-wide substantive audit validating Answer-first architecture and code block authenticity. | **Exclusive to `vesviet/`** |
| 2 | `CONTENT_INDEX.md` | 2026-09-24 | 18.2 KB | 2,517 words | Master content inventory tracking all 375 published content files and 353 reports assets. | Mirrored in `learn/` |
| 3 | `REPORTS_MASTER_CATALOG.md` | 2026-09-24 | 56.0 KB | 5,512 words | Authoritative Master Synthesis Catalog indexing 100% of reports files across 5 clusters. | Mirrored in `learn/` |
| 4 | `categories_audit_2026-07-28.md` | 2026-07-28 | 6.4 KB | 990 words | Taxonomic audit verifying 16 category hubs, frontmatter taxonomy tags, and slug parity. | **Exclusive to `vesviet/`** |
| 5 | `content_posts_audit.md` | 2026-07-27 | 12.7 KB | 2,064 words | Automated lint scan analyzing 66 posts for buzzword violations, H2 structure, and word counts. | **Exclusive to `vesviet/`** |
| 6 | `content_quality_audit_report.md` | 2026-07-28 | 3.4 KB | 473 words | Quality scorecards evaluating readability index, technical depth, and code example clarity. | **Exclusive to `vesviet/`** |
| 7 | `content_radar_audit.md` | 2026-07-28 | 13.7 KB | 2,001 words | Evaluation of Tech Radar editions (2026-04 to 2026-07) for conciseness and citation rigor. | **Exclusive to `vesviet/`** |
| 8 | `content_strategy_report.md` | 2026-07-27 | 52.6 KB | 6,113 words | Strategic editorial roadmap defining flagship pillar hubs, topic clusters, and content cadence. | **Exclusive to `vesviet/`** |
| 9 | `content_substance_audit_2026-07-27.md` | 2026-07-27 | 19.7 KB | 2,464 words | Substance-over-fluff verification evaluating information density across early posts. | **Exclusive to `vesviet/`** |
| 10 | `per_post_deep_audit.md` | 2026-07-28 | 31.3 KB | 4,868 words | Exhaustive per-article breakdown detailing readability, headings, links, and code snippets. | **Exclusive to `vesviet/`** |
| 11 | `posts_audit_2026-07-27.md` | 2026-07-27 | 11.4 KB | 1,512 words | Initial quality screening of baseline posts following migration. | **Exclusive to `vesviet/`** |
| 12 | `posts_content_manager_audit.md` | 2026-07-28 | 10.5 KB | 1,151 words | Content Manager sign-off report reviewing author personas and editorial integrity. | **Exclusive to `vesviet/`** |
| 13 | `radar-corpus-review-2026-09-23.md` | 2026-09-23 | 10.2 KB | 1,876 words | Comprehensive review of all 28 Tech Radar editions through September 2026. | Mirrored in `learn/` |
| 13b | `radar-corpus-review-2026-09-26.md` | 2026-09-26 | 10.8 KB | 1,940 words | Comprehensive review of all 29 Tech Radar editions through September 2026 (including Disaggregated Prefill-Decode). | Mirrored in `learn/` |
| 14 | `radar_audit_2026-07-28.md` | 2026-07-28 | 11.1 KB | 1,570 words | Mid-year audit of radar pipeline and monthly roll-up summaries. | **Exclusive to `vesviet/`** |

---

## Cluster 5: Maintenance & Verification Scripts

Cluster 5 contains local Python utility scripts maintained directly within `vesviet/reports/` for on-demand validation and report generation.

| # | Script File | Runtime | Size | Operational Function & Execution Syntax | Parity (`learn/`) |
|:---:|:---|:---:|:---:|:---|:---:|
| 1 | `check_posts.py` | Python 3.10+ | 9.7 KB | Regex-based content linter checking Answer-first structure, banned AI phrases, and thin sections across `vesviet/content/posts`. Run: `python vesviet/reports/check_posts.py` | **Exclusive to `vesviet/`** (in `learn/`, scripts reside in `learn/tests/`) |
| 2 | `generate_report.py` | Python 3.10+ | 14.0 KB | Automated aggregation script generating `content_posts_audit.md` from post AST scans. Run: `python vesviet/reports/generate_report.py` | **Exclusive to `vesviet/`** (in `learn/`, scripts reside in `learn/tests/`) |

---

## Cross-Repository Twin Alignment Matrix (`vesviet` ↔ `learn`)

The `vesviet` (English flagship) and `learn` (Vietnamese technical educational platform) repositories maintain a coordinated twin publishing architecture. The matrix below defines the exact parity relationship across the two reporting directories:

| Corpus Dimension | `vesviet/reports/` (English) | `learn/reports/` (Vietnamese) | Alignment & Parity Assessment |
|:---|:---:|:---:|:---|
| **Total Files** | **353** | **331** | Parity delta = 22 files. 100% accounted for by localized audits, maintenance scripts, and 4 extra research dossiers. |
| **Cluster 1: Research Dossiers** | 311 files (156 MD + 155 JSON) | 303 files (152 MD + 151 JSON) | **100% of `learn/` dossiers (152 MD + 151 JSON) exist in `vesviet/`**. `vesviet` hosts 4 additional forward-looking dossiers. |
| **Cluster 2: Series Content Indexes** | 17 files (`*-content-index.md`) | 17 files (`*-content-index.md`) | **1:1 Exact Parity** across all 17 flagship series. |
| **Cluster 3: GSC Audits & SOPs** | 9 files (6 MD + 3 JSON) | 8 files (5 MD + 3 JSON) | Functional twin parity: `vesviet` has `GSC_INDEXING_AUDIT_2026_09_17.md` and `GSC_AUDIT_UPGRADE_2026.md`; `learn` has `GSC_COVERAGE_AUDIT_REPORT_2026_09_17.md`. Shared JSON datasets. |
| **Cluster 4: Editorial & Quality Audits** | 14 files | 3 files | `vesviet` preserves historical editorial audits from July 2026; `learn` maintains active `CONTENT_INDEX.md`, `radar-corpus-review-2026-09-23.md`, and `REPORTS_MASTER_CATALOG.md`. |
| **Cluster 5: Maintenance Scripts** | 2 files (`*.py`) | 0 files | In `learn`, test automation scripts are centralized in `learn/tests/` (e.g. `verify_gsc_remediation.py`). |
| **Directory Architecture** | Strictly Flat (0 subdirectories) | Strictly Flat (0 subdirectories) | **100% Invariant Compliant**. Zero subdirectories maintained across both repositories. |

### Research Dossier Parity Gaps (4 Pairs Exclusive to `vesviet`)
The following 4 research dossier pairs currently reside exclusively in `vesviet/reports/`:
1. `research-ai-data-engineering-pipeline-100-rounds.{json,md}` (maps to `series/ai-data-engineering-pipeline/`)
2. `research-ai-driven-engineer-100-rounds.{json,md}` (maps to `series/ai-driven-engineer/`)
3. `research-ai-driven-playbook-100-rounds.{json,md}` (maps to `series/ai-driven-playbook/`)
4. `research-mcp-20-agentic-mesh-100-rounds.{json,md}` (maps to `radar/2026-09/radar-2026-09-08-mcp-20-agentic-mesh-distributed-systems.md`)

---

## Verification & Quality Assurance Governance

To ensure that this master catalog and all associated reporting assets remain strictly synchronized with the live website, the following automated regression suite is executed on every build:
- **Empirical Redirect Oracle**: `python -u vesviet/tests/test_redirects_oracle.py` (23/23 tests PASS: verifies 422 redirect rules, 0 loops, 0 chains, 100% 404/redirect coverage).
- **Hugo Production Build**: `hugo --minify` in `vesviet/` (1,330 pages generated with 0 errors).
- **Sitewide Link Integrity**: Automated AST regex scanner confirming 100% link resolution from `content/**` to `reports/**`.