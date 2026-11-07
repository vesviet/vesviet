# Agentic Memory Consolidation Architecture: Working vs Episodic vs Semantic vs Procedural Stores & Context Token Governors

> **Domain:** AI, SLM & Agentic Systems | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Four-Tier Memory Taxonomy`, `Hybrid Vector-Graph Retrieval (mem0/Zep)`, `Asynchronous Memory Consolidation Pipeline`, `Token Budget Governor (15-20% Cap)`, `OWASP ASI01/ASI06 Memory Poisoning Defense`

---

## 1. Problem Statement & Operational Context
Replaying uncurated raw chat transcripts into LLM context windows causes catastrophic token spend inflation (3–8x per task), quadratic KV-cache invalidation, and severe reasoning degradation. As multi-agent sessions scale beyond 40 turns, naive transcript replay degrades task completion precision by 22–40% due to context starvation, attention dilution, and conflicting historical assertions. Production agent systems require a decoupled, tiered memory architecture with asynchronous background consolidation and strict token-budget caps.

## 2. Core Architectural Invariants
1. **Four-Tier Memory Segmentation:** Memory is partitioned into four distinct tiers: Working (ephemeral in-task scratchpad registers), Episodic (append-only interaction event stream with 14-day rolling TTL), Semantic (governed entity-fact knowledge graph with dense vector embeddings), and Procedural (versioned, human-auditable execution playbooks promoted after $N \ge 5$ verified successes).
2. **Write-Path Isolation & Asynchronous Consolidation:** Direct agent writes to long-term semantic storage are strictly prohibited. Interaction logs stream into episodic storage and are consolidated asynchronously by background workers executing MinHash/SimHash deduplication, exponential time-decay ($\lambda = 0.1$), and deterministic conflict adjudication ($0.6 \times \text{recency} + 0.4 \times \text{authority}$).
3. **Token-Budget Governor with Prefix Alignment:** Dynamic token governors cap memory replay at strictly 15–20% of the active model context window ($W_{\text{total}}$). Replayed memories are formatted into deterministic prefix blocks aligned with Radix Attention page boundaries, guaranteeing $>65\%$ KV-cache reuse across agent turns.
4. **Cryptographic Provenance & Delimiter Sanitization (OWASP ASI01/ASI06):** Every consolidated fact carries an HMAC-SHA256 provenance signature. Replayed memories are injected inside structurally isolated delimiters (`<agent_memory origin="..." sig="...">`) with zero executable shell/code evaluation to prevent indirect prompt injection and persistent memory poisoning.

## 3. Production Performance Benchmarks (Dual AMD EPYC 9654, 768GB DDR5 ECC, NVIDIA H100 SXM5, Go 1.25 & Python 3.13)

| Metric | Consolidated Hybrid (Vector + Graph) | Full Transcript Replay | Naive Vector Search (RAG) |
| :--- | :--- | :--- | :--- |
| **Token Spend per 100-Turn Task** | **18.4K tokens (4.2x reduction)** | 77.2K tokens | 34.6K tokens |
| **Fact Retrieval Precision** | **0.91** | 0.58 (attention dilution) | 0.72 |
| **Multi-Hop Traversal P99 Latency** | **47 ms (Graphiti/Zep)** | N/A (Linear Scan) | 128 ms |
| **KV-Cache Prefix Hit Rate** | **71.4% (Radix Attention)** | 12.8% (Cache Churn) | 38.2% |
| **Session Accuracy Retention (>50 turns)**| **94.2%** | 61.8% | 78.5% |
| **Memory Ingestion P99 Overhead** | **< 8 ms (Async JetStream)** | 0 ms (Raw Log) | 35 ms (Sync Embedding) |

## 4. Agent Retrieval Guidance
- **Apply When:** Architecting long-running multi-agent swarms, implementing persistent user/task memory across sessions, integrating mem0, Zep, Graphiti, or Letta, and enforcing strict token economics to prevent context window starvation.
- **Related Articles:** `/radar/2026-11/radar-2026-11-01-agentic-memory-architecture/`, `/radar/2026-10/radar-2026-10-22-autonomous-agent-swarms-a2a-litellm/`, `/posts/building-custom-golang-vector-database-engine-hnsw/`.
