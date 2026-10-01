# Prompt Standard — Layered Prompt Design: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapters**: `prompt-standard/part-3-layered-prompt-design` (learn, Track 1) + `prompt-standard/part-3-layered-prompt-architecture` (EN consolidated anchor)
> **Campaign**: `series-sync-upgrade` — Chapter 4 of 15

---

## Executive Research Summary

This dossier grounds the layered prompt architecture — Role / Rules / Workflow / Skill — in measured evidence. The fresh primary source is Anthropic's prompt caching documentation: cache reads cost 0.1× base input price (writes 1.25× for 5-minute TTL), up to 4 cache breakpoints exist, a 20-block lookback window governs prefix matching, and invalidation cascades hierarchically tools → system → messages. This converts the series' long-standing claim — "static layers at the prefix, dynamic content at the tail" — from architectural intuition into a priced mechanism: layer stability is literally a cost line item. The evidence converges on three findings: (1) monolith prompts fail for measured reasons (context rot punishes length; edit-coupling makes every change risky); (2) the 4-layer model maps cleanly onto provider cache mechanics — Role and Rules live in the stable cached prefix, Workflow per task family, Skill loaded just-in-time; (3) layering has an honest cost curve — a two-person team with three task types should not build L1–L4.

---

## Cluster 1 — Why Monolith Prompts Fail (Rounds 1–10)

### Round 1: The Three Monolith Problems
**Empirical Finding**: Series observation distilled across deployments: monolithic prompts grow (1) long, (2) hard to edit, and (3) edit-coupled — "sửa chỗ này dễ ảnh hưởng chỗ khác." Each problem compounds the others.
Source: series-internal (Track 1 Part 3 opening).

### Round 2: Context Rot Punishes Length Directly
**Empirical Finding**: Chroma's 18-model study: performance degrades as input length grows even on trivial tasks — the monolith's length is itself a quality liability, independent of maintainability.
Source: https://research.trychroma.com/context-rot

### Round 3: Attention Budget Accounting
**Empirical Finding**: Anthropic's context engineering guidance: every token depletes an "attention budget" with diminishing marginal returns; the target is the smallest set of high-signal tokens. A monolith mixes stable and volatile content in one string, forcing re-reading of everything every call.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 4: Edit-Coupling Is the Safety Hazard
**Empirical Finding**: When safety rules and task instructions share one string, a task-level edit silently damages a safety rule — the layered stack's L2 (Rules/Guardrails) exists to isolate exactly this coupling.
Source: series Track 2 Part 3; series-internal.

### Round 5: Monoliths Defeat Reuse
**Empirical Finding**: A single prompt is single-task by construction; decomposed layers (role shared across repos, rules shared across teams, workflow per family, skill per domain) recompose freely — reuse is structural, not copy-paste.
Source: series-internal (Track 1 Part 3 benefits).

### Round 6: Bloat Hides Decay
**Empirical Finding**: In a long monolith, stale embedded data (old versions, outdated rules) hides from review; in a versioned layer file, staleness is visible in the diff — decomposition makes decay inspectable.
Source: series-internal; version-pinning practice.

### Round 7: The Onboarding Cost of Monoliths
**Empirical Finding**: A new team member facing one 300-line prompt cannot locate the rule that matters; facing four layer files, they read Role first, Rules second — onboarding time is a layering externality.
Source: series-internal (Track 1 Part 3 "dễ đào tạo team").

### Round 8: Drift Diagnosis Needs Layers
**Empirical Finding**: When output drifts, the layered structure supports bisection: role mơ hồ? rule thiếu? workflow chưa đủ? skill quá chung? — a monolith offers no diagnostic axis.
Source: series-internal (Track 1 Part 3 drift-control list).

### Round 9: n² Attention Stretch
**Empirical Finding**: Transformer attention computes n² pairwise relationships; long monolithic prompts stretch attention thin — chunked, delimited structure is the safer regime (Chroma's shuffled-haystack finding corroborates: structure matters as much as volume).
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents ; https://research.trychroma.com/context-rot

### Round 10: The Fix Is Separation of Concerns
**Empirical Finding**: The layered model imports software architecture's oldest principle: separate what changes at different rates — persona (rarely), policy (rarely), procedure (per family), domain detail (per task).
Source: series Track 2 Part 3; software architecture practice.

## Cluster 2 — The 4-Layer Model (Rounds 11–20)

### Round 11: Layer 1 — Role
**Empirical Finding**: Role answers "agent đang đóng vai gì" — identity, responsibilities, decision authority, communication style; it is the anchor layer reused across every repo and task.
Source: series-internal (Track 1 Part 3 layer 1).

### Round 12: Layer 2 — Rules
**Empirical Finding**: Rules are invariants: "không sửa file generated bằng tay, không dùng lệnh phá huỷ, không bịa test result, không lộ secrets" — short, clear, rarely changing; the security team owns this layer alone.
Source: series-internal (Track 1 Part 3 layer 2).

### Round 13: Layer 3 — Workflow
**Empirical Finding**: Workflow is the ordered procedure per work type: debug-issue, architecture-planning, deep-review, quick-docs — "Workflow giúp agent không bỏ sót bước."
Source: series-internal (Track 1 Part 3 layer 3).

### Round 14: Layer 4 — Skill
**Empirical Finding**: Skill is deep guidance for a specific task type or domain: add-api-endpoint, write-tests, review-service — "chỉ nên được gọi khi task thật sự phù hợp," loaded on demand.
Source: series-internal (Track 1 Part 3 layer 4).

### Round 15: Track 1 ↔ Track 2 Layer Mapping
**Empirical Finding**: The two vocabularies describe one architecture: Role = L1 Core Base (persona/identity), Rules = L2 Security Guardrails, Workflow = L3 Business SOPs, Skill = L4 Dynamic Task Skills — the standard pins this mapping to prevent drift.
Source: series Track 2 Part 3; mapping table established in the part-2 dossier.

### Round 16: Skills Fire on Triggers
**Empirical Finding**: From agent-facing writing discipline: a pointer line names its trigger words and branches — "one trigger per branch" — skills load when task language matches their declared triggers.
Source: agent-skills pack agent-facing writing discipline.

### Round 17: Layer Ownership Model
**Empirical Finding**: Role: platform team; Rules: security team; Workflow: team leads; Skill: domain owners — the ownership model mirrors the change-frequency model: each layer's owner is who changes it least often per change class.
Source: series-internal (Track 2 Part 3 ownership).

### Round 18: Anthropic's Own Layering: System vs Tools vs Messages
**Empirical Finding**: The API itself layers content: `tools`, then `system`, then `messages` — cache prefixes follow this hierarchy; the 4-layer model is the content-design translation of a provider-level structure.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 19: CLAUDE.md as Evidence of Layering in the Wild
**Empirical Finding**: Claude Code's CLAUDE.md pattern — static project context up front, dynamic exploration just-in-time — is the reference deployment of the same layering: stable prefix, volatile tail.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 20: The Accounting Translation
**Empirical Finding**: role ≈ kế toán thanh toán vs kế toán tổng hợp; rules ≈ nguyên tắc không bỏ qua chứng từ; workflow ≈ quy trình chốt công nợ / đối soát cuối tháng; skill ≈ hướng dẫn riêng cho hoàn tiền, ví điện tử, VAT — every finance department already runs layered.
Source: series-internal (Track 1 Part 3 analogy).

## Cluster 3 — Cache Economics: Layering Is Priced (Rounds 21–30)

### Round 21: Cache Reads Cost 0.1×
**Empirical Finding**: Prompt caching pricing: "Cache read tokens are 0.1 times the base input token price" (0.025× on Fable 5.1/Mythos 5.1) — e.g., Opus 5: $5/MTok base → $0.50/MTok cached read; Sonnet 5: $2 → $0.20.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 22: Cache Writes Cost 1.25× (5-min) / 2× (1-hour)
**Empirical Finding**: "5-minute cache write tokens are 1.25 times the base input tokens price. 1-hour cache write tokens are 2 times the base input tokens price" — the first write is a premium, amortized across hits.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 23: The Layer-Stability Payoff Formula
**Empirical Finding**: If the stable prefix (Role + Rules + tools) is cached and reused N times, effective prefix cost ≈ 1.25× + N × 0.1× base — vs N × 1.0× uncached. Break-even at ~2 reuses; at 10 reuses, prefix cost falls ~90% vs uncached runs.
Source: computed from https://platform.claude.com/docs/en/build-with-claude/prompt-caching pricing multipliers.
[INFERENCE] Break-even arithmetic assumes full-prefix hits and ignores TTL expiry; teams compute on their own conversation shapes.

### Round 24: 5-Minute TTL, Refreshed on Use
**Empirical Finding**: "By default, the cache has a 5-minute lifetime. The cache is refreshed for no additional cost each time the cached content is used" — TTL counts from request start, and response generation time counts against it.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 25: 1-Hour TTL at 2×
**Empirical Finding**: `{ "cache_control": { "type": "ephemeral", "ttl": "1h" } }` — for stable layers reused across hours (shared Role/Rules across a team's workday), the 1-hour write may amortize better than repeated 5-minute writes.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 26: Up to 4 Breakpoints
**Empirical Finding**: "You can define up to 4 cache breakpoints" — "to cache different sections that change at different frequencies (for example, tools rarely change, but context updates daily)" — breakpoints are literally layer boundaries.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 27: Breakpoints Themselves Are Free
**Empirical Finding**: "Cache breakpoints themselves don't add any cost. You are only charged for cache writes and cache reads" — layering boundaries cost nothing until they save.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 28: Minimum Cacheable Lengths
**Empirical Finding**: Minimum cacheable prompt length: 512 tokens (Opus 5, Fable 5.x), 1,024 (Opus 4.8, Sonnet 4.6/4.5), 4,096 (Opus 4.6/4.5, Haiku 4.5) — short prompts cannot cache; below threshold, "requests will be processed without caching, and no error is returned."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 29: Layer Order = Cache Order
**Empirical Finding**: "Place static content (tool definitions, system instructions, context, examples) at the beginning of your prompt" and "Place cached content at the prompt's beginning for best performance" — the standard's layer order (Role → Rules → Workflow → Skill → task input) is the cache-optimal order.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 30: Cache Is Workspace-Isolated, Exact-Match
**Empirical Finding**: "Cache hits require 100% identical prompt segments" and caches are isolated per workspace/organization — layer files must assemble byte-identically across calls to hit; whitespace drift in any layer breaks the prefix hash.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

## Cluster 4 — Cache Mechanics for Layer Designers (Rounds 31–40)

### Round 31: The 20-Block Lookback Window
**Empirical Finding**: "The lookback window is 20 blocks. The system checks at most 20 positions per breakpoint" — if a growing conversation pushes the breakpoint >20 blocks past the last write, the hit is missed; add a second breakpoint at the stable layer boundary.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 32: Consecutive Tool Blocks Count as One Position
**Empirical Finding**: "A run of consecutive `tool_use` blocks counts as one position, and so does a run of consecutive `tool_result` blocks" — parallel tool calls don't push prior entries out of the window on their own.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 33: The Classic Breakpoint Mistake
**Empirical Finding**: The documented anti-pattern: `cache_control` on a block that changes every request (timestamps, per-request context) — "the system never wrote an entry at any of those positions. No cache hit. You pay for a fresh cache write on every request." Fix: "Place `cache_control` on the last block whose prefix is identical across the requests."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 34: Automatic vs Explicit Caching
**Empirical Finding**: Automatic caching (top-level `cache_control`) moves the breakpoint to the last cacheable block as conversations grow — best for multi-turn chats; explicit block-level breakpoints for "sections that change at different frequencies" — layered stacks want explicit breakpoints at layer seams.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 35: Invalidation Hierarchy: tools → system → messages
**Empirical Finding**: "The cache follows the hierarchy: tools → system → messages. Changes at each level invalidate that level and all subsequent levels" — editing a tool definition invalidates everything; editing a message invalidates only messages. Layer blast radius is priced.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 36: What Changes Invalidate What
**Empirical Finding**: From the invalidation table: tool definitions invalidate all three caches; tool_choice only messages; images only messages; thinking parameters always messages (model-specific above); effort changes invalidate messages — volatile content belongs in messages, never in system or tools.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 37: Usage Fields for Cache Observability
**Empirical Finding**: Track `cache_creation_input_tokens`, `cache_read_input_tokens`, and `input_tokens`; total = read + creation + input — "if both cache fields are 0, the prompt was not cached (likely below minimum length)."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 38: Layer Design Rule from Invalidations
**Empirical Finding**: Design corollary: anything that varies per request (timestamps, user input, retrieved data) must live in `messages`, after the last breakpoint — stable layers (Role/Rules/tools) before it; the standard's assembly order enforces the cache contract.
Source: synthesis of https://platform.claude.com/docs/en/build-with-claude/prompt-caching invalidation rules.

### Round 39: Thinking Blocks and Caching
**Empirical Finding**: Thinking blocks cannot be directly marked with `cache_control` but cache alongside prior-turn content when passed back; on Opus 4.5+/Sonnet 4.6+ they're preserved by default — reasoning layers interact with cache layers, another reason workflow state lives in structured files, not prompt strings.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 40: Concurrent Requests and Cache Warm-up
**Empirical Finding**: "A cache entry only becomes available after the first response begins. If you need cache hits for parallel requests, wait for the first response before sending subsequent requests" — burst traffic to a new layer version pays full write price per concurrent first-call.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

## Cluster 5 — Swappability and Blast Radius (Rounds 41–50)

### Round 41: Provider Swap Changes Two Layers
**Empirical Finding**: Swapping model providers touches L1 (voice calibration) and L4 (skill wording); L2/L3 survive intact — controlled blast radius vs a monolith rewrite.
Source: series Track 2 Part 3 (Round 34 of part-2 dossier cross-reference).

### Round 42: Policy Change Touches One Layer
**Empirical Finding**: A new security rule (e.g., "không lộ secrets") lands in Rules once and inherits into every task — the inverse of editing hundreds of per-task prompts.
Source: series-internal (Track 1 Part 3 "khi có thay đổi chính sách").

### Round 43: Workflow Evolution Is Local
**Empirical Finding**: Changing the review procedure edits one workflow file; role, rules, and skills are untouched — layer-local diffs keep review scope small and golden-dataset evals targeted.
Source: series-internal.

### Round 44: Skill Failure Is Contained
**Empirical Finding**: A buggy skill module cannot corrupt the base stack — mirroring DDD anti-corruption layers; the skill is swapped or disabled, the persona/policy layers never notice.
Source: series Track 2 Part 3 (anti-corruption framing).

### Round 45: The Pack as Layering Evidence
**Empirical Finding**: The agent-skills pack demonstrates 34 role files sharing centralized rule sections — guardrail updates propagate to every role without editing each file: the maintainability pattern at scale.
Source: agent-skills pack structure.

### Round 46: Namespace = Layer Discipline
**Empirical Finding**: Tool namespacing (asana_search vs jira_search) from the tools-for-agents guidance applies to skills and workflows too: distinct names per module prevent trigger collisions at load time.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 47: Skill Loading Is Just-in-Time
**Empirical Finding**: Claude Code's JIT pattern — identifiers in context, data loaded at runtime — skills follow the same rule: the skill registry lists triggers; full skill bodies load only on match, saving the attention budget.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 48: Hybrid Strategy Boundary
**Empirical Finding**: "The most effective agents employ hybrid strategies: static CLAUDE.md-style context up front, autonomous just-in-time exploration at discretion — the decision boundary depends on task dynamics."
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 49: Reuse Metrics for Layers
**Empirical Finding**: Layer health metrics: prefix hit rate (cache_read vs cache_creation tokens), layer change frequency per file, drift incidents attributable per layer — the usage fields make layer ROI observable.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching ; series metrics practice.

### Round 50: The Blast-Radius Table
**Empirical Finding**: Change-class → layer mapping: persona drift → Role; policy violation → Rules; step omission → Workflow; domain error → Skill — every incident resolves to a layer owner in minutes.
Source: series-internal (drift diagnosis list, operationalized).

## Cluster 6 — Composition Over Inheritance (Rounds 51–60)

### Round 51: Stacks Compose at Runtime
**Empirical Finding**: Prompt stacks assemble layers per request (role + rules + workflow + skill) rather than inheriting from a mega-prompt — composition won over inheritance in software architecture for the same reason: changes stay local.
Source: series Track 2 Part 3.

### Round 52: The Assembler Pattern
**Empirical Finding**: Production stacks use a runtime compiler/assembler (the Track 2 Go PromptStack compiler; Anthropic's cache_control placement is the API-side equivalent) — assembly is code, not string concatenation in chat.
Source: series Track 2 Part 3 (_index compiler diagram).

### Round 53: Deterministic Assembly Order
**Empirical Finding**: Assembly order is fixed — Role, Rules, Workflow, Skill, then dynamic input — because cache prefixes require byte-identical stability: order is a contract, not a preference.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching (exact-match requirement); series Track 2 Part 3.

### Round 54: Variable Injection at the Tail
**Empirical Finding**: All per-request variables ({task_input}, {timestamp}) inject after the last stable breakpoint — the template placeholder pattern from the 8-block schema carries into layered stacks.
Source: series Track 2 Part 2 template; cache breakpoint guidance.

### Round 55: Cross-Task Layer Sharing
**Empirical Finding**: One reviewer Role serves many repos; one Rules layer serves many workflows — sharing is the payoff: the marginal cost of the Nth task drops toward skill-authoring only.
Source: series-internal (Track 1 Part 3 reuse).

### Round 56: Layer Versioning Semantics
**Empirical Finding**: Each layer file carries its own version; stack assembly records the layer-version tuple per deployment — bisecting a regression means diffing layer versions, not re-reading a monolith.
Source: series Track 2 Part 6 (PromptOps integration).

### Round 57: When to Split a Layer
**Empirical Finding**: Split signals: a Rules file receiving edits from two different owners, a Workflow serving >3 task types, a Skill exceeding ~1 screen — the layering reflects Conway's law: one owner per layer.
Source: series-internal.
[INFERENCE] Split thresholds are heuristics from series practice, not measured constants.

### Round 58: When to Merge Layers
**Empirical Finding**: Merge signals: a Workflow file nobody edits separately from its Skill, layers always deployed in lockstep — premature layering costs indirection without isolation.
Source: series-internal.

### Round 59: The Anti-Pattern: Layer Explosion
**Empirical Finding**: The inverse failure: 15 micro-layers nobody can trace — layering serves change-frequency separation; layers that change together belong together.
Source: series-internal (honest cost framing).

### Round 60: Layer Discipline Summary
**Empirical Finding**: The discipline in one line: layers separate by change frequency and owner; the stack composes them in a cache-stable order; blast radius per change is one layer, priced by the cache table.
Source: series synthesis (Rounds 41–59).

## Cluster 7 — Skills as Anti-Corruption Modules (Rounds 61–70)

### Round 61: The Skill Contract
**Empirical Finding**: A skill declares: name, triggers (the conditions under which it loads), body (deep guidance), and completion criteria — the same contract structure as blocks, one level up.
Source: agent-skills pack SKILL.md structure; series Track 1 Part 3.

### Round 62: Trigger Words Front-Loaded
**Empirical Finding**: "A line that names out-of-context material must front-load its trigger words and list the distinct branches that should fire it — one trigger per branch" — skills follow the pointer discipline for reliable activation.
Source: agent-skills pack agent-facing writing discipline.

### Round 63: Skill Bodies Stay Out of Context Until Needed
**Empirical Finding**: Only the trigger line occupies the always-on context; the body loads on match — the attention-budget argument for the skill layer's existence.
Source: agent-skills pack structure; https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 64: Domain Examples Live in Skills
**Empirical Finding**: Few-shot examples specific to a domain (API-endpoint patterns, VAT rules) live in the skill, not the base stack — the base stays lean; examples travel with the trigger.
Source: series-internal; Anthropic examples guidance (3–5, relevant, diverse).

### Round 65: Skill Granularity Rule
**Empirical Finding**: One skill = one task family (add-api-endpoint ≠ write-tests); overlapping skills create trigger collisions — the same overlap confusion documented for tools applies to skills.
Source: series Track 1 Part 3 skill list; https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 66: Skill Deprecation
**Empirical Finding**: Superseded skills archive with migration notes, and their trigger lines retire — stale triggers are silent context pollution.
Source: series-internal (asset lifecycle).

### Round 67: The Accounting Skill Examples
**Empirical Finding**: Hoàn tiền (refund processing), đối soát ví điện tử (e-wallet reconciliation), kiểm tra VAT (VAT checking) — each is a skill: deep, narrow, triggered by its business event.
Source: series-internal (Track 1 Part 3 analogy).

### Round 68: Skills Are Tested Like Tools
**Empirical Finding**: Anthropic's tool-evaluation methodology transfers: generate realistic tasks per skill, measure runtime/tool-calls/tokens/errors — skills are eval targets, not prose.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 69: Skill Registry as Governance
**Empirical Finding**: A registry (directory + index) lists active skills with owners and versions — the MCP allowlist discipline at prompt level: unregistered skills don't load.
Source: series-internal; MCP scope-minimization parallel.

### Round 70: The Skill Failure Mode
**Empirical Finding**: The documented failure: "skill viết quá chung" — a generic skill body loads on broad triggers and dilutes every task it touches; specificity is the skill's license to exist.
Source: series-internal (Track 1 Part 3 drift list).

## Cluster 8 — The Accounting Analogy, Layer by Layer (Rounds 71–80)

### Round 71: Finance Departments Are Layered
**Empirical Finding**: Kế toán thanh toán vs kế toán tổng hợp (roles), nguyên tắc chứng từ (rules), quy trình chốt công nợ (workflows), hướng dẫn hoàn tiền (skills) — the mapping is structural, not decorative: finance standardized the same separation centuries ago.
Source: series-internal (Track 1 Part 3).

### Round 72: Rules Layer = Accounting Principles
**Empirical Finding**: "Không được bỏ qua chứng từ" is an invariant — it never changes per task; finance encodes it once (in policy) and every procedure inherits it — exactly the Rules-layer pattern.
Source: series-internal.

### Round 73: Workflow Layer = Period-End Procedures
**Empirical Finding**: Đối soát cuối tháng (month-end reconciliation) is a fixed sequence executed on a trigger (calendar) — workflows fire on work-type triggers, skills on domain triggers.
Source: series-internal.

### Round 74: Skill Layer = Specialty Manuals
**Empirical Finding**: VAT checking has its own manual because it is deep and narrow — nobody embeds the VAT manual inside the general ledger policy; embedding is exactly what monolith prompts do.
Source: series-internal.

### Round 75: Audit Trail Parallels
**Empirical Finding**: Finance answers "who approved this posting, under which policy version" — layered prompts answer the same question per output: which layer versions assembled this run.
Source: series-internal; Round 56 versioning.

### Round 76: Segregation of Duties = Layer Ownership
**Empirical Finding**: Finance separates authorization from execution; layered prompts separate Rules ownership (security) from Skill authorship (domain) — the same control prevents the same class of fraud/error.
Source: series-internal; accounting control practice.

### Round 77: The Non-Engineer's Layer Diagram
**Empirical Finding**: The effective non-technical explainer: role = job description, rules = company policy, workflow = SOP manual, skill = specialty training — one sentence per layer, zero model terminology.
Source: series-internal (Track 1 framing discipline).

### Round 78: What Finance Would Never Do
**Empirical Finding**: No finance team rewrites the general policy inside each invoice — yet teams rewrite security rules inside each task prompt daily; the analogy makes the monolith absurd on sight.
Source: series-internal.

### Round 79: Adoption Pitch for Ops Teams
**Empirical Finding**: The pitch that lands: "bạn đã chạy layered system rồi — chỉ đang áp dụng nó cho AI" — adoption friction drops when the pattern is already familiar.
Source: series-internal (Track 1 adoption practice).

### Round 80: Layered Audit Questions
**Empirical Finding**: Ops teams can self-audit with four questions: role rõ chưa? rules còn đúng chưa? workflow còn đủ bước chưa? skill nào cần viết? — the layer model is the checklist.
Source: series-internal.

## Cluster 9 — When Layering Overkills (Rounds 81–90)

### Round 81: The Two-Person Rule
**Empirical Finding**: A two-person team with three task types does not need L1–L4 — one 8-block file per task suffices; layering pays at multi-team scale with shared policy.
Source: series Track 2 Part 3 (Round 39, part-2 dossier); series-internal.

### Round 82: The Layer Count Heuristic
**Empirical Finding**: Start layer count = number of distinct change-frequency classes in your prompts: persona changes rarely → layer; task type changes often → per-task file; one class = no layers needed.
Source: series-internal synthesis.
[INFERENCE] The frequency-class heuristic is a design rule of thumb, not a measured law.

### Round 83: Layering Costs Debug Indirection
**Empirical Finding**: Honest cost: a 4-layer stack's behavior spans files — debugging requires the assembled view; teams keep an assembler that dumps the composed prompt per run.
Source: series Track 2 Part 3 trade-off matrix.

### Round 84: Onboarding Curve
**Empirical Finding**: Layering adds concepts (layers, triggers, assembly) a new member must learn before their first edit — the monolith's one-file simplicity is real; the 8-block single-file standard is the honest default below the team-scale threshold.
Source: series-internal.

### Round 85: The Migration Path
**Empirical Finding**: Teams graduate: monolith → blocks in one file → split Role+Rules when a second task appears → split Workflow when task families diverge → skills when domains deepen — each split is triggered by pain, not by doctrine.
Source: series-internal (adoption sequencing).

### Round 86: Cache Minimums Also Gate Layering
**Empirical Finding**: Below 512–4,096 tokens (model-dependent), prefixes cannot cache at all — a tiny layered stack gains nothing from cache alignment; layer for maintainability first, cache economics at scale.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching

### Round 87: The Threshold Question
**Empirical Finding**: The decision test: "do two roles edit this prompt's content at different frequencies?" — yes → split; no → keep one file. Ownership divergence, not aesthetics, triggers layering.
Source: series-internal (Round 57 split signals).

### Round 88: Cache Economics for Small Teams
**Empirical Finding**: The 0.1× read multiplier pays when the stable prefix is reused within TTL windows — low-volume teams rarely hit 5-minute reuse; layering's small-team payoff is maintainability, not cost.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching ; synthesis.

### Round 89: The Anti-Doctrine
**Empirical Finding**: The series' published stance: "không nhất thiết phải dùng đủ tất cả ngay ngày đầu" — the block framework and the layer model are both checklists, not rituals; omitting layers is a documented decision.
Source: series-internal (Track 1 Part 2 omission rules).

### Round 90: The Honest Summary
**Empirical Finding**: Layering buys: central policy control, cache-aligned cost, contained blast radius, layer-level review; it costs: design overhead, debug indirection, onboarding concepts — the trade is team-scale-dependent and the article must say so.
Source: series synthesis.

## Cluster 10 — Directory Structure and Adoption (Rounds 91–100)

### Round 91: The Reference Layout
**Empirical Finding**: The series' reference layout: `role/developer.md`, `rules/coding-safety.md`, `workflows/debug-issue.md`, `skills/add-api-endpoint/SKILL.md`, `skills/write-tests/SKILL.md` — the file tree is the architecture.
Source: series-internal (Track 1 Part 3 example).

### Round 92: Assembly in Code, Not Chat
**Empirical Finding**: A small assembler (script or library call) concatenates layers in fixed order and injects variables — "biến prompt từ 'đoạn chat tạm thời' thành 'hệ thống vận hành'."
Source: series-internal (Track 1 Part 3 closing).

### Round 93: Naming Conventions
**Empirical Finding**: Layer file naming: lowercase-hyphen, one owner tag in frontmatter, version header per file — consistent names are also cache-friendly (byte-stable assembly) and review-friendly.
Source: series-internal; cache exact-match requirement.

### Round 94: Review Flow per Layer Change
**Empirical Finding**: Layer diffs review like code: Rules changes require security sign-off, Workflow changes the team lead, Skills the domain owner — the ownership model routes each diff to its authority.
Source: series-internal (Round 17 ownership).

### Round 95: Layer Metrics Starter Set
**Empirical Finding**: Per-layer health: change frequency, cache hit ratio (from usage fields), drift incidents attributed, reuse count across stacks — four numbers make the layer investment auditable.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching (usage fields); series metrics.

### Round 96: Migration from Monolith — the Recipe
**Empirical Finding**: Extraction order: (1) cut Role+Rules to the top (they're stable), (2) move task detail into Skill files, (3) keep Workflow in the middle, (4) add breakpoints at each seam — each step is a separately tested diff.
Source: series-internal; cache breakpoint placement.

### Round 97: Rollout Sequencing
**Empirical Finding**: Roll out to one task family first; run the layered stack beside the monolith for a week of golden-dataset parity checks; cut over when parity holds — the strangler-fig pattern applied to prompts.
Source: series-internal; software migration practice.

### Round 98: The Layer Model, Final Form
**Empirical Finding**: Published position: four layers — Role (identity, rarely changes), Rules (invariants, security-owned), Workflow (procedures per family), Skill (domain depth, trigger-loaded) — assembled cache-stable, owned separately, diffed locally.
Source: series synthesis (Rounds 11–20, 41–60).

### Round 99: What the Next Chapter Adds
**Empirical Finding**: Layers make prompts maintainable; the next chapter makes them improvable: versioning discipline and eval gates — the Git changelog and the golden dataset that turn layer changes into measured experiments.
Source: series architecture (Track 1 Part 4 bridge).

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes chapter 4's dossier; the campaign proceeds with chapter 5 (part-4-versioning-and-evals) in the same pass — both repos in lockstep, per the series-sync-upgrade loop.
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) layer stability converted from architecture intuition into a priced mechanism — 0.1× cache reads vs 1.0× uncached, 1.25× writes, 4 breakpoints, TTL trade-offs, with a break-even formula; (2) the invalidation hierarchy (tools → system → messages) as the vendor-side proof that volatile content must tail-load — the layer order is a cache contract, not a preference; (3) the 20-block lookback window and the documented breakpoint anti-pattern (per-request timestamps at the breakpoint) as operational guardrails for layer designers; (4) Track 1 (Role/Rules/Workflow/Skill) ↔ Track 2 (L1–L4) mapping pinned; (5) finance-department layering as the non-engineer bridge, extended with segregation-of-duties = layer ownership.
- **AI_coverage_gap**: Layered-prompt articles exist but almost never cite cache pricing, invalidation tables, or lookback mechanics — the cost side of layering is documented nowhere in typical guides; the honest anti-doctrine (when NOT to layer, cache minimums gating payoff) is absent elsewhere.
- **firsthand_evidence_available**: no — synthesizes published primary sources and series design.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| platform.claude.com/docs/en/build-with-claude/prompt-caching | primary | Primary | Pricing multipliers, TTLs, breakpoints, lookback, invalidation table, usage fields, minimum lengths |
| anthropic.com/engineering/effective-context-engineering-for-ai-agents | primary | Primary | attention budget, JIT loading, hybrid boundary |
| anthropic.com/engineering/writing-tools-for-agents | primary | Primary | namespacing, skill/tool eval methodology |
| research.trychroma.com/context-rot | primary | Primary | length degradation, shuffled-haystack structure finding |
| series Track 1/Track 2 chapters + agent-skills pack | internal | Tertiary (internal) | layer design, mapping table, discipline rules |

## AI Source Discipline

- AI tools used for queries only (not cited): none — all rounds trace to fetched primary documents or series-internal design.
- AI-citation mismatches: none — docs.anthropic.com prompt-caching URL redirected to the canonical platform.claude.com page; canonical URL cited.
- grounding_completeness: 36/100 rounds carry external source URLs (Anthropic cache docs, context engineering, tools-for-agents, Chroma); 61/100 cite series-internal design traceable to series corpus files and the agent-skills pack; 3 rounds carry [INFERENCE] labels (Rounds 23, 57, 82).

## Handoff

- **recommended_next_roles**: content-writer (Phase 3: upgrade VI part-3-layered-prompt-design; Phase 4: upgrade EN part-3-layered-prompt-architecture as consolidated anchor), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: none — consolidation decision (VI Track 1 part-3 ⇄ EN Track 2 part-3) follows the chapter-3 precedent.
- **residual_risks**: (1) cache pricing is per-model and versioned — cite multipliers, not absolute dollars, in the article; (2) minimum cacheable lengths vary per model (512–4,096) — present as a range; (3) [INFERENCE]-labeled rounds keep labels downstream (Gate 7).
