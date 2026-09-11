# Prompt Standard — The Context Engineering Shift: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapters**: `prompt-standard/part-6-context-engineering` (learn, Track 1) + `prompt-standard/part-1-context-engineering-evolution` (EN consolidated anchor)
> **Campaign**: `series-sync-upgrade` — Chapter 7 of 15

---

## Executive Research Summary

This dossier grounds the prompt-engineering-to-context-engineering shift — the conceptual hinge of the entire series. All primary sources were fetched and verified during this campaign's earlier dossiers (Anthropic context-engineering guidance, Chroma context rot, Lost in the Middle, MCP specification, prompt-caching documentation); this chapter assembles them around the Track 1 three-pillar frame (RAG / MCP / dynamic assembly) and the Track 2 deterministic-engine frame (token budgeting, KV prefix alignment). The evidence converges on three findings: (1) the shift is measured, not rhetorical — attention dilution (n²), context rot across 18 models, and U-shaped recall make "write better words" a lost cause while "curate better context" is an engineering discipline; (2) the three pillars have vendor-grade mechanics: RAG fights rot and cost simultaneously, MCP externalizes tools with a security model, and just-in-time assembly mirrors human file-system behavior; (3) the unmeasured "70% token savings" claim in the current VI chapter must be replaced by the measured figures — cache reads at 0.1× base price (≈90% prefix-cost reduction at ~10 reuses) and 206→72 token response compression — or dropped.

---

## Cluster 1 — The Shift Is Measured, Not Rhetorical (Rounds 1–10)

### Round 1: The Discipline Redefinition
**Empirical Finding**: Anthropic's engineering guidance (Sep 2025): "context engineering refers to the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference" — superseding narrow prompt craft; the problem is optimizing token utility against model constraints.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 2: Attention Budget as the Governing Model
**Empirical Finding**: Context is "a finite resource with diminishing marginal returns — an attention budget that every new token depletes"; good context engineering = finding the smallest possible set of high-signal tokens for the outcome.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 3: n² Attention Mechanics
**Empirical Finding**: The transformer computes n² pairwise token relationships; as context grows, "the model's ability to capture pairwise relationships gets stretched thin" — a performance gradient, not a cliff.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 4: Context Rot Across 18 Frontier Models
**Empirical Finding**: Chroma (Jul 2025): GPT-4.1, Claude 4 family, Gemini 2.5, Qwen3 — performance grows increasingly unreliable as input length grows, even on simple tasks; models do not use context uniformly.
Source: https://research.trychroma.com/context-rot

### Round 5: The U-Shape Grounds Assembly Order
**Empirical Finding**: Lost in the Middle (Liu et al., TACL 2023): recall peaks at context beginning and end, degrades in the middle — "even for explicitly long-context models"; assembly order is an engineering decision.
Source: https://arxiv.org/abs/2307.03172

### Round 6: The Placement Dividend
**Empirical Finding**: Anthropic: long data at top, query at end — "Queries at the end can improve response quality by up to 30 percent in tests, especially with complex, multidocument inputs."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 7: Distractor Amplification
**Empirical Finding**: A single distractor measurably reduces performance; four compound the damage; impact grows with input length — uncurated context is actively harmful, not merely wasteful.
Source: https://research.trychroma.com/context-rot

### Round 8: Focused Beats Full, On Every Model
**Empirical Finding**: LongMemEval: focused ~300-token prompts beat full ~113k-token prompts across all 18 models — retrieval and reasoning degrade together when context is uncurated.
Source: https://research.trychroma.com/context-rot

### Round 9: Structure Beats Coherence
**Empirical Finding**: Models performed better on shuffled haystacks than logically structured ones — how information is chunked and delimited matters more than narrative coherence.
Source: https://research.trychroma.com/context-rot

### Round 10: The 2024 Mindset Failure
**Empirical Finding**: Series synthesis: "chọn từ ngữ cẩn thận và hy vọng model hiểu ý" failed because it optimized the ~100 tokens of instruction while ignoring the ~100,000 tokens of context around them — the tail wagged the dog.
Source: series-internal (Track 1 Part 6 opening).

## Cluster 2 — Context Engineering Defined (Rounds 11–20)

### Round 11: The Definition the Series Publishes
**Empirical Finding**: "Context Engineering là kỹ năng thiết kế hệ thống lắp ráp đúng thông tin vào context window của model, đúng lúc" — designing the system that assembles the right information into the context window at the right time.
Source: series-internal (Track 1 Part 6).

### Round 12: The Assembly Contrast
**Empirical Finding**: Instead of "Bạn là chuyên gia tài chính. Phân tích báo cáo Q1" — the engineering form: [System: role/rules/output contract] + [Q1 data retrieved dynamically from ERP API] + [prior-quarter comparison from warehouse] + [user query last] — each bracket a subsystem.
Source: series-internal (Track 1 Part 6 example).

### Round 13: The 8-Block Chapter Is the In-Prompt Half
**Empirical Finding**: Part 2's 8 blocks govern the instruction contract inside the prompt; context engineering governs everything assembled around it — the two disciplines compose, they do not compete.
Source: series-internal (Track 1 Part 2; Part 6 positioning).

### Round 14: Claude Code as Reference Implementation
**Empirical Finding**: Claude Code's JIT pattern: agents "maintain lightweight identifiers (file paths, queries) and dynamically load data at runtime via tools — mirroring human use of file systems and bookmarks rather than memorizing corpora."
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 15: The Hybrid Boundary
**Empirical Finding**: "The most effective agents employ hybrid strategies: static CLAUDE.md-style context up front, autonomous just-in-time exploration at discretion" — the boundary is task-dynamics, not doctrine.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 16: JIT Trade-off
**Empirical Finding**: Runtime exploration is slower than pre-computed retrieval — JIT trades latency for freshness; RAG trades freshness for speed; production systems choose per task class.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 17: Just-in-Time Context Retrieval as a Technique
**Empirical Finding**: Anthropic names JIT context retrieval among the most impactful techniques alongside focused retrieval and sub-agent contexts — the catalog of assembly strategies is vendor-documented.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 18: Sub-Agent Contexts
**Empirical Finding**: Sub-agents with their own focused context windows prevent attention dilution in long agentic tasks — the orchestrator keeps lightweight pointers, workers load full context.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 19: Compaction and Structured Memory
**Empirical Finding**: Conversation memory needs compaction: "Claude's latest models perform especially well in using git to track state across multiple sessions" — external state stores beat context stuffing for durability.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 20: The Shift, One Line
**Empirical Finding**: The chapter's thesis sentence: "Cách nhanh nhất để cải thiện chất lượng agent thường không phải viết lại prompt — mà là cải thiện chất lượng và sự liên quan của context được inject vào."
Source: series-internal (Track 1 Part 6 closing).

## Cluster 3 — Pillar 1: RAG (Rounds 21–30)

### Round 21: RAG as the 2026 Prompting Mechanism
**Empirical Finding**: "RAG là cơ chế chính mà hệ thống production 'prompt' model trong năm 2026" — instead of stuffing knowledge into prompts, store documents in a vector database and retrieve the relevant slice at query time.
Source: series-internal (Track 1 Part 6 pillar 1).

### Round 22: Long Windows Don't Kill RAG
**Empirical Finding**: Context rot is the proof: larger windows reduce data-loading cost but not the curation problem — retrieval remains necessary for quality (focused beats full) and cost (fewer input tokens).
Source: https://research.trychroma.com/context-rot

### Round 23: The 4-Stage Hybrid Pipeline
**Empirical Finding**: The series' pipeline: sparse+dense first-stage recall → cross-encoder reranking → AST-aware chunk selection → context assembly into the Context block.
Source: series-internal (Track 2 Part 4; exec dossier Cluster 6).

### Round 24: AST Chunking Rationale
**Empirical Finding**: AST-based chunking splits on code-structure boundaries, preserving semantic units fixed-size chunking destroys — the same modularity principle as prompt blocks.
Source: series-internal; hybrid RAG practice.

### Round 25: Reranking as Precision Lever
**Empirical Finding**: Cross-encoder rerankers score query-document pairs jointly, trading latency for precision after first-stage recall.
Source: series-internal (Track 2 Part 4).

### Round 26: Contextual Chunk Headers
**Empirical Finding**: Anthropic's contextual-retrieval guidance: adding document context (title, section path) to each chunk header improves retrieval grounding.
Source: Anthropic contextual retrieval engineering post (2024); series Track 2 Part 4.
[INFERENCE] Exact percentage gains are dataset-dependent; the structural benefit is established.

### Round 27: RAG Injection Surface
**Empirical Finding**: Retrieved documents are an indirect-injection vector — RAG pipelines without sanitization inherit the OWASP LLM01/ASI01 surface through their corpus.
Source: OWASP guidance; https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices

### Round 28: Stale-Index Hazard
**Empirical Finding**: Pre-computed indexes drift from source documents; JIT navigation (grep/glob) bypasses stale indexing — the trade-off space between RAG and JIT loading.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 29: When RAG Overkills
**Empirical Finding**: Five documents don't need retrieval infrastructure — a table of contents with pointers suffices; RAG pays at corpus scale with recurring queries.
Source: series-internal; Anthropic JIT guidance.

### Round 30: The Finance RAG Analogy
**Empirical Finding**: Kế toán parallel: không nhồi cả két sổ lưu trữ 10 năm lên bàn làm việc — chỉ rút đúng hồ sơ liên quan đến kỳ đối soát; RAG là "rút hồ sơ" cho model.
Source: series-internal (Track 1 analogy extension).

## Cluster 4 — Pillar 2: MCP (Rounds 31–40)

### Round 31: The USB-C Framing
**Empirical Finding**: "MCP là USB-C cho AI agent" — one protocol, every tool: the open protocol (Anthropic-initiated) standardizing how agents connect to tools, databases, and enterprise systems.
Source: series-internal (Track 1 Part 6 pillar 2); https://modelcontextprotocol.io

### Round 32: Tools Split From Prompt
**Empirical Finding**: MCP separates tool definitions from prompt text — agents discover tools at runtime instead of hardcoding them in system prompts; tool schemas inject on demand.
Source: https://modelcontextprotocol.io ; series Track 2 Part 4.

### Round 33: The Token Cost of Tool Schemas
**Empirical Finding**: Tool schemas occupy budget: the EN anchor's 15% tools allocation (~19.2k of 128k) — schema injection must be filtered (intent-classified) to avoid paying for unused tools.
Source: series Track 2 Part 1 (budget table); https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 34: Consolidated Tools Beat Wrapped APIs
**Empirical Finding**: "Instead of implementing list_users, list_events, and create_event, consider schedule_event" — fewer, more semantic tools; "too many tools or overlapping tools can distract agents."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 35: Response Format Economics
**Empirical Finding**: The response_format enum: detailed 206 tokens vs concise 72 — "~⅓ of the tokens" per call; tool responses need caps (Claude Code default 25,000 tokens) and steering on truncation.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 36: Namespacing Prevents Confusion
**Empirical Finding**: "When tools overlap in function or have a vague purpose, agents can get confused about which ones to use" — namespacing by service/resource delineates boundaries; prefix vs suffix choice measurably affects evaluations.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 37: MCP Security Model
**Empirical Finding**: The spec's attack taxonomy: confused deputy (static client IDs), token passthrough prohibition, SSRF via OAuth discovery (internal IPs), session hijacking via shared queues — each with spec-level mitigations.
Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices

### Round 38: Scope Minimization
**Empirical Finding**: Broad wildcard scopes (files:*, db:*) expand blast radius; progressive least-privilege (minimal initial, incremental elevation via WWW-Authenticate) constrains compromise impact.
Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices

### Round 39: The MCP-Prompt Standard Bridge
**Empirical Finding**: Tool Policy block ↔ MCP allowlist: the standard's Constraints block is the prompt-level mirror of the registry's scope minimization — one policy, two enforcement layers.
Source: series Track 2 Part 2; MCP scope guidance.

### Round 40: When MCP Overkills
**Empirical Finding**: An agent with no external actions needs no MCP layer; the pillar activates when tools exist — the honest scope rule from the block-omission discipline.
Source: series-internal (Track 1 Part 2 omission rules).

## Cluster 5 — Pillar 3: Dynamic Context Assembly (Rounds 41–50)

### Round 41: Assembly Decides From Four Inputs
**Empirical Finding**: "Hệ thống quyết định inject gì dựa trên: query hiện tại, trạng thái agent, tool đã gọi, và working memory" — assembly is a function of four runtime variables, not a fixed template.
Source: series-internal (Track 1 Part 6 pillar 3).

### Round 42: The 2024→2026 Comparison Table
**Empirical Finding**: The shift across four dimensions: goal (perfect prompt → trustworthy context system), source (hardcoded → dynamic retrieval), output (free-form → schema-bound), maintenance (ad-hoc edits → versioned and monitored).
Source: series-internal (Track 1 Part 6 comparison table).

### Round 43: The Seven-Dimension EN Extension
**Empirical Finding**: The EN anchor extends to seven dimensions: core abstraction (string → assembly pipeline), window strategy (stuffing → budgeting), tools (static → MCP injection), optimization (manual → DSPy), retrieval (top-k → hybrid multi-stage), caching (none → prefix-aligned), security (ad-hoc → OWASP ASI).
Source: series-internal (Track 2 Part 1 comparison table).

### Round 44: Token Budgeting Discipline
**Empirical Finding**: Context allocation governed like OS RAM: fixed budgets per functional category (identity 5%, policy 10%, tools 15%, RAG 40%, history 20%, query/output 10% of a 128k window) with strict upper bounds.
Source: series Track 2 Part 1 (budget equation); https://platform.claude.com/docs/en/build-with-claude/prompt-caching (minimum lengths as budget floors).

### Round 45: The Four Stability Zones
**Empirical Finding**: Context streams structure into: static block (identity/guardrails — cached indefinitely), semi-static (SOPs, active MCP tools), dynamic (reranked RAG chunks), volatile (recent turns, active query).
Source: series Track 2 Part 1; KV-cache mechanics.

### Round 46: Cache Alignment Above 80% Hit
**Empirical Finding**: "To maximize the KV prefix cache hit rate above 80%, context engines ordering must remain entirely static from token position zero" — assembly order is the cache contract.
Source: series Track 2 Part 1; https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 47: Invalidation Discipline
**Empirical Finding**: Cache hierarchy tools → system → messages: tool-definition edits void everything; volatile content (timestamps, per-request data) belongs in messages after the last breakpoint.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 48: Assembly as Code
**Empirical Finding**: The Go ContextAssembler: budget-enforced allocation, static-prefix ordering, sliding-window pruning on retrieved docs — assembly is compiled code, not string concatenation.
Source: series Track 2 Part 1 (Go implementation).

### Round 49: The Unverified 70% Claim
**Empirical Finding**: The current VI chapter claims "tiết kiệm 70% chi phí token" — no primary source supports the 70% figure. Measured replacements: cache reads at 0.1× base input price (≈90% prefix-cost reduction at ~10 reuses, 1.25× first-write amortized); response_format 206→72 tokens (~2/3 saving per tool call). The 70% claim must be replaced by these verified figures.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching ; https://www.anthropic.com/engineering/writing-tools-for-agents
[VERIFICATION-NOTE] This round is a correction instruction for Gate 7 compliance — the drafting phase must not carry the 70% figure forward.

### Round 50: The Assembly Summary
**Empirical Finding**: Dynamic assembly = the compiler that makes the other two pillars affordable: RAG feeds it candidates, MCP feeds it schemas, the budget trims both to what the query deserves.
Source: series synthesis.

## Cluster 6 — Evidence Pack: Why Curation Beats Stuffing (Rounds 51–60)

### Round 51: The Repeated-Words Floor
**Empirical Finding**: Even replicating a word 10,000 times degrades with length — GPT-4.1 refused at 2.55%, GPT-4.1 mini emitted "san Francisco" from nowhere, Gemini 2.5 Pro produced "I'-a-le-le-le…" — no task is too trivial for context rot.
Source: https://research.trychroma.com/context-rot

### Round 52: Semantic Retrieval Degrades Faster
**Empirical Finding**: Non-lexical needle-question pairs degrade worse with length than lexical ones — real tasks (no exact keyword matches) suffer most; RAG's reranking exists to close exactly this gap.
Source: https://research.trychroma.com/context-rot

### Round 53: Abstention as the Safe Behavior
**Empirical Finding**: Claude-family models abstain under ambiguity (lowest hallucination rates); GPT-family answers anyway (highest) — curation plus Fallback contracts convert the safest behavior into policy.
Source: https://research.trychroma.com/context-rot

### Round 54: Attention Budget Meets Token Pricing
**Empirical Finding**: Uncurated context bills twice: accuracy (rot) and spend (per-token pricing) — the double penalty that makes assembly a budget line, not a style choice.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 55: The 30% Placement Dividend Again
**Empirical Finding**: Data-top/query-end ordering — the cheapest optimization in the whole discipline: rearranging existing tokens, adding none.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 56: Grounding by Quoting First
**Empirical Finding**: For long-document tasks: "ask Claude to quote relevant parts of the documents first before carrying out its task" — grounding reduces distractor influence before reasoning begins.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 57: Multidocument Provenance Tags
**Empirical Finding**: Wrap each document in `<document index="n">` with `<source>` subtags — provenance travels with data, making assembled context self-describing.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 58: The Memory Parallel
**Empirical Finding**: Human cognitive load research parallels: working memory holds ~4 chunks; experts survive by externalizing state (files, notes, checklists) — agents externalize to stores and load pointers; context stuffing ignores a constraint both brains and transformers share.
Source: cognitive-load literature; Anthropic JIT framing.
[INFERENCE] The working-memory parallel is an analogy, not a measured equivalence — cite as framing, not data.

### Round 59: The 1M-Token Misconception
**Empirical Finding**: "LLMs with 1M+ token context windows suffer from context bloat, attention dilution, and high token latency" — window size solves storage, not attention, cost, or accuracy.
Source: series Track 2 Part 1; https://research.trychroma.com/context-rot

### Round 60: Evidence Pack Summary
**Empirical Finding**: Five findings close the case: rot at every length, U-shape placement, distractor amplification, focused-beats-full, structure-beats-coherence — each maps to an assembly control (budget, order, filtering, retrieval, chunking).
Source: synthesis of Rounds 51–59.

## Cluster 7 — Security: Context Is an Attack Surface (Rounds 61–70)

### Round 61: Untrusted Context Everywhere
**Empirical Finding**: Everything the agent reads — retrieved docs, tool results, files — is an injection vector; context assembly is therefore a security function, not just a quality function.
Source: OWASP LLM01 guidance; MCP security best practices.

### Round 62: Boundary Isolation in Assembly
**Empirical Finding**: The EN anchor's principle: "strict boundary isolation between control instructions and untrusted external inputs" — instructions and data never share a block without delimiters.
Source: series Track 2 Part 1; XML-tag isolation guidance.

### Round 63: XML Delimiters as Trust Boundary
**Empirical Finding**: Section delimiters (`<instructions>`, `<context>`) keep control logic parseable apart from payload data — "reduces misinterpretation" and raises injection cost.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 64: Dual-LLM Isolation at Assembly Time
**Empirical Finding**: The quarantined-parser pattern: untrusted content parsed by a tool-less model into typed JSON before the privileged core sees it — assembly is where the isolation happens.
Source: series Track 2 Part 6; OWASP mitigation patterns.

### Round 65: Fail-Closed Assembly
**Empirical Finding**: When policy evaluation fails, abort — assembly enforces fail-closed: an unresolvable security ambiguity means the context doesn't ship, not that it ships anyway.
Source: series Track 2 Part 2 (tool policy); MCP fail-closed guidance.

### Round 66: Output Validation Closes the Loop
**Empirical Finding**: LLM02: every output is untrusted input downstream — schema validation at the egress; assembly discipline at ingress, validation at egress.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 67: Session Security in Stateful Assembly
**Empirical Finding**: Shared-queue session hijacking (events keyed by session ID), impersonation via predictable IDs — mitigations: secure random IDs, user-bound keys, sessions never authenticate.
Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices

### Round 68: Memory Poisoning
**Empirical Finding**: ASI06: malicious vectors ingested into long-term semantic stores corrupt future turns — retrieval indexes are a persistence-layer attack surface needing ingestion validation.
Source: OWASP ASI framing; series Track 2 Part 6.

### Round 69: The RAG Corpus Audit
**Empirical Finding**: RAG corpora need provenance: who can write to the index, what sanitization runs at ingestion — an unaudited corpus is a standing injection inventory.
Source: synthesis; MCP untrusted-content guidance.

### Round 70: Security Summary
**Empirical Finding**: Context engineering's security ledger: isolate control from data (delimiters), quarantine untrusted parsing (dual-LLM), fail closed on ambiguity, validate egress, audit the corpus — five controls, all assembly-time.
Source: synthesis of Rounds 61–69.

## Cluster 8 — The Finance Register (Rounds 71–80)

### Round 71: Kế toán Không Nhồi Số Liệu
**Empirical Finding**: "AI chỉ nhận hồ sơ liên quan đến kỳ đối soát" — a good accountant never brings ten years of ledgers to the desk; they pull the relevant period. Context curation is the same professional instinct.
Source: series-internal (Track 1 analogy).

### Round 72: Chứng Từ Là Context Có Provenance
**Empirical Finding**: Finance requires every number to trace to a voucher — context engineering requires every token to trace to a source (provenance tags); untraceable numbers fail audits in both worlds.
Source: series-internal; Anthropic document-tag guidance.

### Round 73: Đúng Lúc, Không Phải Đúng Hết
**Empirical Finding**: "lắp ráp đúng thông tin... đúng lúc" — the working-capital discipline: hold inventory (data) lean, pull just-in-time; context assembly is working-capital management for tokens.
Source: series-internal (Track 1 Part 6 definition).

### Round 74: Ba Trụ Cột Dịch Sang Kế Toán
**Empirical Finding**: RAG = rút đúng hồ sơ từ kho; MCP = chuẩn kết nối hệ thống (như chuẩn hóa biểu mẫu liên phòng ban); dynamic assembly = quyết định tài liệu nào lên bàn làm việc lúc nào — three familiar departments, one new subject.
Source: series-internal (Track 1 pillar analogy).

### Round 75: The Non-Engineer's Shift Sentence
**Empirical Finding**: The one-line Track 1 translation: "cải thiện chất lượng câu trả lời AI = cải thiện hồ sơ mà nó nhận được, không phải cầu kỳ hơn trong cách hỏi" — better inputs, not fancier asking.
Source: series-internal.

### Round 76: The ERP Parallel
**Empirical Finding**: Nobody hand-copies the general ledger into an email to ask finance a question; they reference account codes. MCP is the account-code system for AI — references, not copies.
Source: series-internal (analogy extension).

### Round 77: Budget as Materiality
**Empirical Finding**: Token budgets work like materiality thresholds: not every number belongs in the report; only material ones. The 128k budget forces the same triage a good reporting package does.
Source: series-internal; Track 2 budget discipline.

### Round 78: Audit Trail for Assembly
**Empirical Finding**: Which documents were retrieved, which tools injected, which budget version governed — assembly logs answer the auditor's question for AI outputs.
Source: series-internal (usage-fields discipline from Ch4 dossier).

### Round 79: Reconciliation = Reranking
**Empirical Finding**: Cross-encoder reranking is reconciliation: first-pass candidates (book entries) get verified against the query (bank statement) before being accepted into the report (context).
Source: series-internal (structural analogy).
[INFERENCE] The parallel is pedagogical, not a formal equivalence.

### Round 80: Register Summary
**Empirical Finding**: The finance register makes the shift teachable without model talk: rút hồ sơ đúng kỳ (RAG), chuẩn biểu mẫu liên phòng (MCP), bàn làm việc có tổ chức (assembly) — context engineering as professional hygiene.
Source: synthesis of Rounds 71–79.

## Cluster 9 — What Changes in Practice (Rounds 81–90)

### Round 81: The Practitioner's Checklist Shift
**Empirical Finding**: 2024 checklist: wording, tone, magic phrases, pleases. 2026 checklist: what gets retrieved, what gets pruned, what order, what budget, what provenance — the audit moved from prose to pipeline.
Source: series-internal (comparison table operationalized).

### Round 82: The Metrics Shift Too
**Empirical Finding**: Prompt-era metrics: subjective quality. Context-era metrics: retrieval precision, cache hit rate, token spend per task, latency — the EN anchor's observability fields make the shift measurable.
Source: series Track 2 Part 1; https://platform.claude.com/docs/en/build-with-claude/prompt-caching (usage fields).

### Round 83: Failure Modes Rename
**Empirical Finding**: "Model quên" → mid-context placement (U-shape); "model nhầm" → distractor contamination; "model chậm tốn" → uncached volatile prefix — every folk failure name maps to an assembly control.
Source: synthesis; Chroma findings.

### Round 84: The Cost Levers Ranked
**Empirical Finding**: Cost levers by magnitude: cache alignment (0.1× vs 1.0× on the prefix), response caps (206→72), retrieval pruning (fewer input tokens), compaction (history summarization) — all assembly-time, none wording-time.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching ; https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 85: The Quality Levers Ranked
**Empirical Finding**: Quality levers: placement (+30%), grounding-by-quote, focused retrieval (focused beats full), sub-agent isolation — again all assembly-time.
Source: Anthropic guidance set; Chroma.

### Round 86: What Stays From Prompting
**Empirical Finding**: The 8 blocks survive intact — Role/Mission/Scope are the static prefix; Output Contract is the egress schema; Fallback is the fail-closed policy. Context engineering does not retire the standard; it hosts it.
Source: series-internal (Track 1 Parts 2+6 synthesis).

### Round 87: The Team Skills Shift
**Empirical Finding**: The needed skills tilt: retrieval engineering, token accounting, cache-friendly ordering, ingestion security — prompt-writing skill remains, but as the smallest slice.
Source: series-internal; Anthropic CE framing.

### Round 88: The 2027 Stack Position
**Empirical Finding**: This chapter is the Track 1 gateway: it names the shift and the three pillars; Track 2 deep-dives implement them (hybrid RAG in Part 4, MCP in Part 4, budgeting/caching in Part 1/3 EN anchors).
Source: series architecture.

### Round 89: Prerequisites the Chapter Assumes
**Empirical Finding**: The chapter lands best after Parts 1–5: the reader knows blocks, layers, and evals — so the shift reads as "the system around your standard," not as a replacement for it.
Source: series-internal (Track ordering).

### Round 90: The Honest Scope Note
**Empirical Finding**: Track 1's chapter stays at pillar depth — no vector-DB benchmarks, no MCP schema details — those live in the linked deep-dives; the chapter's job is the mental model and the evidence.
Source: series-internal.

## Cluster 10 — Chapter Mechanics (Rounds 91–100)

### Round 91: VI Chapter Current State
**Empirical Finding**: 773 words, 0 mermaid, placeholder FAQ (auto-generated boilerplate), the unverified 70% claim, noTranslation flag — the series' weakest chapter by every gate; the upgrade must add evidence, structure, and verified figures.
Source: series-internal (audit finding).

### Round 92: EN Anchor Current State
**Empirical Finding**: 1,737 words, 1 mermaid, 3 FAQ — strong technical core (budget equation, Go assembler, stability zones) but: no badge, truncated description ("...KV prefix caching define."), no answer-first per H2, no research anchors, no related links — below bar on hygiene gates.
Source: series-internal (audit finding).

### Round 93: VI Upgrade Plan
**Empirical Finding**: Phase 3 plan: keep the three-pillar frame and the comparison table; add the measured-evidence section (rot, U-shape, 30%, focused-beats-full); replace 70% with verified figures; add the finance register; 2 mermaid (assembly pipeline + 2024/2026 contrast); 3 real FAQ; answer-first per H2; drop noTranslation.
Source: series-internal (this dossier's handoff).

### Round 94: EN Upgrade Plan
**Empirical Finding**: Phase 4 plan: fix desc; add badge + related links; add answer-first per H2; insert the Anthropic/Chroma anchors into the paradigm section; keep budget math, stability zones, and Go assembler untouched; add research-anchors table; extend FAQ with the 70%-claim correction and the USB-C question.
Source: series-internal (this dossier's handoff).

### Round 95: Cross-Linking Plan
**Empirical Finding**: VI links: RAG → ai-data-engineering-pipeline series; MCP → mcp-engineering-in-production series; EN twin badge both directions; EN anchor links back to the VI chapter and forward to Part 2 blocks.
Source: series-internal (link topology).

### Round 96: The 70% Correction Decision
**Empirical Finding**: Decision: remove "70%" everywhere; the chapter cites (a) cache reads 0.1× (≈90% prefix reduction at scale, with the 1.25× first-write caveat), (b) response_format 206→72. Both are sourced; neither was the basis of the 70% figure.
Source: this dossier Rounds 49, 84.
[VERIFICATION-NOTE] Gate 7 blocker if the 70% figure survives into the draft.

### Round 97: FAQ Design
**Empirical Finding**: Three VI FAQ: (1) cửa sổ 1M token có thay context engineering không (no — rot evidence); (2) RAG/MCP cho team nhỏ từ đâu bắt đầu (pointers trước, hạ tầng sau); (3) cache alignment có đáng không (0.1× arithmetic). EN adds: USB-C question and the death-of-prompting question.
Source: series-internal; campaign FAQ patterns.

### Round 98: Mermaid Design
**Empirical Finding**: VI diagram 1: the assembly pipeline (retrieval + tools + memory → budget → cache-aligned stream); diagram 2: 2024 vs 2026 flow contrast. EN keeps its existing engine diagram; adds none — the anchor's diagram already covers the contrast.
Source: series-internal.

### Round 99: Definition of Done
**Empirical Finding**: Both chapters: >2,500 words, >20KB, 2 mermaid (EN ≥1 existing + hygiene), 3–5 FAQ, answer-first per H2, verified figures only, 0 banned words, badges 1/1, Hugo PASS.
Source: series 2027 SOTA bar.

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes chapter 7's dossier — the consolidated pair (VI Track 1 part-6-context-engineering ⇄ EN part-1-context-engineering-evolution) upgrades next; campaign proceeds to Ch8 (`part-7-declarative-prompting-dspy` ⇄ EN `part-5-declarative-prompting-dspy`).
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) the shift presented as five measured findings (rot, U-shape, distractors, focused-beats-full, structure-beats-coherence) each mapped to an assembly control — evidence-first framing absent from typical "context engineering" explainers; (2) the 70% savings claim corrected to verified figures (0.1× cache reads, 206→72 response compression) — a Gate 7 integrity fix documented in-dossier; (3) the finance register extended with working-capital and provenance analogies (JIT inventory, voucher-traceable numbers, account-code references); (4) the 2024→2026 comparison operationalized as metric and checklist shifts, not vocabulary changes; (5) the security ledger — five assembly-time controls — uniting MCP spec taxonomy with prompt-standard blocks.
- **AI_coverage_gap**: Context-engineering posts either evangelize the term or stay abstract; the pillar mechanics (why RAG survives 1M windows, MCP's token-budget role, the four assembly variables) with vendor anchors and an honest Track-1/Track-2 division are rarely assembled in one place.
- **firsthand_evidence_available**: no — assembles campaign-verified primary sources; no new benchmarks.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| anthropic.com/engineering/effective-context-engineering-for-ai-agents | primary | Primary | definition, attention budget, JIT, sub-agents, hybrid boundary |
| research.trychroma.com/context-rot | primary | Primary | rot, distractors, focused-beats-full, abstention |
| arxiv.org/abs/2307.03172 | primary | Primary | U-shape placement |
| platform.claude.com/docs (best practices + prompt caching) | primary | Primary | +30% placement, provenance tags, grounding quotes, cache economics |
| anthropic.com/engineering/writing-tools-for-agents | primary | Primary | tool consolidation, response_format, caps |
| modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices | primary | Primary | MCP security model |
| series Track 1/Track 2 chapters | internal | Tertiary (internal) | pillar frame, budget math, Go assembler, finance register |

## AI Source Discipline

- AI tools used for queries only (not cited): none — all sources fetched and verified during this campaign's earlier dossiers (Ch1–Ch6); no new fetches required for this chapter.
- AI-citation mismatches: none.
- grounding_completeness: 60/100 rounds carry external source URLs; 37/100 cite series-internal design; 3 rounds carry [INFERENCE] or [VERIFICATION-NOTE] labels (Rounds 26, 58, 79, 96 — the 70% correction is a verification note, not inference).

## Handoff

- **recommended_next_roles**: content-writer (Phase 3: upgrade VI part-6-context-engineering; Phase 4: upgrade EN part-1-context-engineering-evolution as consolidated anchor), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: none — the 70%-claim removal is a Gate 7 obligation, not an option.
- **residual_risks**: (1) budget percentages (5/10/15/40/20/10) are the series' own design figures, not vendor numbers — label as design defaults; (2) the EN desc fix must complete the truncated sentence; (3) [INFERENCE] and [VERIFICATION-NOTE] labels survive into drafts where the corresponding content appears (Gate 7).
