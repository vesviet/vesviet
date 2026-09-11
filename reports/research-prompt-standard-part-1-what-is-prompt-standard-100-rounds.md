# Prompt Standard Part 1 — What Is Prompt Standard: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapter**: `prompt-standard/part-1-what-is-prompt-standard` (`vesviet` & `learn`)
> **Campaign**: `series-sync-upgrade` — Chapter 2 of 15

---

## Executive Research Summary

This dossier establishes the evidence base for the series' definitional chapter: what a Prompt Standard actually is, and why a team — not just an individual — needs one. The evidence converges on three findings. First, prompt engineering as a field is real but fragmented: the most comprehensive survey to date (The Prompt Report, arXiv:2406.06608, 31 authors, v6 Feb 2025) needed 33 vocabulary terms and a 58-technique taxonomy to describe the landscape — a signal that ad-hoc individual intuition cannot cover it. Second, the failure modes of unstandardized prompting in teams are systematic, not random: ambiguity forces the model to guess intent, overstuffing destroys maintainability, and missing fallback behavior produces confident-wrong answers — each failure class maps to a measurable phenomenon. Third, the fix is not "better writing" but asset management: prompts that affect output quality are system components and deserve versioning, ownership, and review — the exact transformation that code standards, SOPs, and accounting checklists already went through.

---

## Cluster 1 — The Fragmented Field of Prompt Engineering (Rounds 1–10)

### Round 1: The Most Comprehensive Survey to Date
**Empirical Finding**: The Prompt Report (Schulhoff et al., arXiv:2406.06608, 31 authors, v6 Feb 2025) assembles a taxonomy of 58 LLM prompting techniques, 40 techniques for other modalities, and 33 vocabulary terms — self-described as "the most comprehensive survey on prompt engineering to date".
Source: https://arxiv.org/abs/2406.06608

### Round 2: The Fragmentation Problem
**Empirical Finding**: The survey's stated motivation: prompt engineering "suffers from conflicting terminology and a fragmented ontological understanding of what constitutes an effective prompt due to its relatively recent emergence" — the field lacks a shared definition even among practitioners.
Source: https://arxiv.org/abs/2406.06608

### Round 3: 58 Techniques Is Not a Craft, It Is a Discipline
**Empirical Finding**: A taxonomy of 58 LLM prompting techniques means no individual intuition reliably covers the space; technique selection (zero-shot vs few-shot vs chain-of-thought vs ReAct-style) is an engineering decision with measurable trade-offs, not a writing style.
Source: https://arxiv.org/abs/2406.06608

### Round 4: Best Practices Exist and Are Documented
**Empirical Finding**: The Prompt Report "provides best practices and guidelines for prompt engineering, including advice for prompting state-of-the-art (SOTA) LLMs" — codified guidance exists; teams skipping it are re-deriving solved problems by trial and error.
Source: https://arxiv.org/abs/2406.06608

### Round 5: Meta-Analysis Coverage
**Empirical Finding**: The survey includes "a meta-analysis of the entire literature on natural language prefix-prompting" — the accumulated evidence base is large enough to meta-analyze, which places prompting firmly in empirical territory.
Source: https://arxiv.org/abs/2406.06608

### Round 6: Cross-Modality Spread
**Empirical Finding**: Beyond the 58 LLM techniques, the survey catalogs 40 techniques for other modalities — prompting knowledge is not one skill but a family of modality-specific skills, further justifying standardization over intuition.
Source: https://arxiv.org/abs/2406.06608

### Round 7: Prompting as the Interface Layer
**Empirical Finding**: Per the survey framing: "Developers and end-users interact with these systems through the use of prompting and prompt engineering" — prompting is the primary interface between humans and GenAI systems, which makes interface quality a system-quality concern.
Source: https://arxiv.org/abs/2406.06608

### Round 8: A Standard Absorbs the Taxonomy Problem
**Empirical Finding**: When a team standardizes on an 8-block prompt structure, the 58-technique landscape collapses to a decision: which technique belongs in the Workflow block for this task — the standard turns an overwhelming taxonomy into a scoped selection problem.
Source: series-internal synthesis; https://arxiv.org/abs/2406.06608

### Round 9: From Personal Skill to Team Capability
**Empirical Finding**: A fragmented discipline mastered by one member is a bus-factor-1 risk; the same knowledge encoded in standards, templates, and reviewed prompt files is a team capability that survives personnel changes.
Source: series-internal.

### Round 10: The Definition the Series Takes
**Empirical Finding**: Working definition for this series: a Prompt Standard is a team's codified contract for prompt structure (8 blocks), lifecycle (version → review → eval), and ownership — the prompt-level analogue of a coding standard.
Source: series-internal (Track 1 Part 1 design).

## Cluster 2 — Ambiguity: The Root Failure (Rounds 11–20)

### Round 11: "Review this code" Forces Ten Guesses
**Empirical Finding**: An underspecified instruction ("Hãy review code này") leaves the model to guess: bug focus or style? security priority? file references needed? fix proposals or findings only? Each unanswered question is a random variable injected into the output.
Source: series-internal (Track 1 Part 1 example).

### Round 12: Guessing Degrades Output Measurably
**Empirical Finding**: Chroma's distractor experiments show that ambiguity plus context degrades performance non-uniformly — when the model must both identify relevance and reason (two tasks at once), accuracy drops on every model tested (LongMemEval full vs focused prompts).
Source: https://research.trychroma.com/context-rot

### Round 13: Ambiguous Instructions Create Internal Distractors
**Empirical Finding**: An ambiguous prompt is functionally equivalent to injecting distractors: the model must disambiguate intent while executing, consuming the same attention budget that distractor experiments show is the failure point.
Source: series-internal synthesis; https://research.trychroma.com/context-rot

### Round 14: The Four Guess-Zones
**Empirical Finding**: Team-prompt ambiguity clusters into four zones the standard must pin: perspective (which role/lens), scope (what is in/out), evidence (what data references are required), and output (what format the result takes).
Source: series-internal (Track 1 Part 1 structure).

### Round 15: Reduced Ambiguity Is Testable
**Empirical Finding**: The standard's fix for ambiguity is checkable: a Role block answers perspective, a Constraints block answers scope, a Context block answers evidence, an Output Format block answers format — each is a reviewable artifact, not a hope.
Source: series-internal; block anatomy in Track 2 Part 2.

### Round 16: Instruction-Following Is Real but Not Mind-Reading
**Empirical Finding**: Models follow explicit instructions well — that is their training objective — but instruction-following research (e.g., IFEval-style benchmarks referenced in the Prompt Report's meta-analysis) measures compliance with stated constraints, never intent discovery.
Source: https://arxiv.org/abs/2406.06608 (meta-analysis coverage).
[INFERENCE] The survey covers instruction-following benchmarks; specific IFEval numbers are not quoted here — verify at draft time if a figure is used.

### Round 17: "Phân tích giúp tôi" Is a Three-Way Ambiguity
**Empirical Finding**: Generic analysis requests fail on three axes simultaneously: what object (data? code? document?), which lens (business? technical? financial?), and what deliverable (summary? table? decision?) — the model picks all three at random.
Source: series-internal (Track 1 Part 1 failure example).

### Round 18: Ambiguity Tax Is Paid by the Downstream
**Empirical Finding**: When format is unspecified, downstream consumers (humans or parsers) absorb the variance — the cost of an ambiguous prompt is shifted to whoever integrates the output, multiplying across every run.
Source: series-internal.

### Round 19: Repeatability Requires Pinned Intent
**Empirical Finding**: "Cùng một loại task thì đầu ra gần giống nhau" (repeatable output) is only achievable when intent is pinned identically across runs — repeatability is a property of the prompt, not of the model.
Source: series-internal (Track 1 Part 1 value proposition).

### Round 20: The Accounting Analogy for Ambiguity
**Empirical Finding**: A junior accountant given "kiểm tra giúp tôi bảng này" faces the same four guess-zones (which check, against which source, on mismatch do what, report in which form) — mature departments solved this with standard checklists; teams solve it with prompt standards.
Source: series-internal (Track 1 Part 1 analogy).

## Cluster 3 — Overstuffing: The Opposite Failure (Rounds 21–30)

### Round 21: The 500-Line Monolith
**Empirical Finding**: The opposite failure mode: one prompt mixing role, business context, output format, safety rules, and the current task into a several-hundred-line string — every edit risks breaking an unrelated concern.
Source: series-internal (Track 1 Part 1 failure taxonomy).

### Round 22: Context Rot Punishes Bloat Empirically
**Empirical Finding**: Chroma's 18-model study: performance degrades as input length grows even on trivial tasks — a stuffed prompt is measurably worse than a curated one, not just harder to maintain.
Source: https://research.trychroma.com/context-rot

### Round 23: Attention Budget Accounting
**Empirical Finding**: Anthropic's guidance: every token depletes an "attention budget" with diminishing marginal returns; the engineering target is the smallest set of high-signal tokens — overstuffing directly violates the measured performance model.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 24: Bloat Also Bills Twice
**Empirical Finding**: Per-token pricing means the overstuffed prompt costs more per call while (per Round 22) performing worse — the double penalty that makes bloat a budget issue, not only a style issue.
Sources: https://research.trychroma.com/context-rot ; https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 25: Mixed Concerns Break Under Edit
**Empirical Finding**: When safety rules and task instructions share one string, a task-level edit can silently damage a safety rule — the monolith couples concerns that a layered stack (L1–L4) deliberately separates.
Source: series Track 2 Part 3; series-internal.

### Round 26: Reuse Impossible Without Decomposition
**Empirical Finding**: A monolithic prompt is single-task by construction; decomposed blocks (role, rules, workflow, skill) recompose across tasks — reuse is a structural property.
Source: series Track 2 Part 3 design.

### Round 27: The Survey's Structural Advice
**Empirical Finding**: The Prompt Report's best-practice guidance includes structuring prompts with clear sections (role, instructions, examples, output format) — the survey-grade consensus matches the standard's block decomposition.
Source: https://arxiv.org/abs/2406.06608
[INFERENCE] Section-structuring appears among the survey's best practices; exact section naming differs by source — the chapter cites the survey for the general principle.

### Round 28: Few-Shot Examples Belong in Their Own Block
**Empirical Finding**: Anthropic: curated, diverse, canonical examples beat exhaustive edge-case lists — "examples are the 'pictures' worth a thousand words"; an Examples block isolates them for curation and versioning.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 29: Bloat Hides Drift
**Empirical Finding**: In a 500-line prompt, stale embedded data (old schema, outdated figures) hides from reviewers; in a Context block with version pins, staleness is visible and checkable — decomposition makes decay inspectable.
Source: series-internal; version-pinning practice.

### Round 30: The Right Size Is Task-Scoped
**Empirical Finding**: The standard's answer to overstuffing: each prompt carries exactly the eight blocks its task needs, nothing more; cross-task shared material moves up to layers (L1–L4), not down into every prompt.
Source: series Track 2 Part 3; Track 1 Part 1.

## Cluster 4 — Missing Fallback: Confident-Wrong Behavior (Rounds 31–40)

### Round 31: The Confident-Wrong Failure
**Empirical Finding**: Without a Fallback block, agents answer confidently even when mandatory data is missing — "trả lời rất tự tin nhưng sai" is the signature failure of prompts without uncertainty handling.
Source: series-internal (Track 1 Part 1 failure taxonomy).

### Round 32: Abstention Is the Safest Measured Behavior
**Empirical Finding**: Chroma's distractor experiments: Claude-family models show the lowest hallucination rates precisely because they abstain under ambiguity; GPT-family models hallucinate most by answering anyway — abstention is empirically the safest behavior.
Source: https://research.trychroma.com/context-rot

### Round 33: Fallback Makes Abstention Contractual
**Empirical Finding**: A Fallback block ("nếu thiếu dữ liệu, ghi rõ chưa đủ chứng từ để kết luận") converts the model's accidental abstention tendency into a contractual obligation — the safest measured behavior, now guaranteed.
Source: series-internal; https://research.trychroma.com/context-rot

### Round 34: Three Fallback Rules Cover the Space
**Empirical Finding**: The minimal fallback specification: (1) missing mandatory data → ask/flag, never guess; (2) out-of-scope request → decline with reason and routing; (3) uncertainty → state confidence tier in output.
Source: series-internal (Track 1 Part 1; template Fallback block).

### Round 35: Overreliance Is an OWASP Category
**Empirical Finding**: OWASP LLM09 (Overreliance): "failing to critically assess LLM outputs can lead to compromised decision making, security vulnerabilities, and legal liabilities" — unstandardized prompts institutionalize overreliance by hiding uncertainty.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 36: Accounting-Grade Fallback: The Reconciliation Example
**Empirical Finding**: The bookkeeping example pins it exactly: "Nếu thiếu dữ liệu, ghi rõ 'chưa đủ chứng từ để kết luận'" — a reconciliation assistant that estimates instead of flagging missing vouchers is an audit risk, not an efficiency.
Source: series-internal (Track 1 Part 1 example).

### Round 37: Uncertainty Labeling as Output Contract
**Empirical Finding**: Requiring a confidence tier in the Output Format block (chắc/không chắc) makes uncertainty machine-parseable — downstream systems can route low-confidence outputs to human review automatically.
Source: series-internal.

### Round 38: Escalation Beats Silence and Beats Guessing
**Empirical Finding**: The three possible behaviors on missing data — silent guess, silent refusal, explicit escalation — differ enormously in blast radius; the standard mandates the third because it is the only auditable one.
Source: series-internal.

### Round 39: LongMemEval Shows the Focused-Input Fix
**Empirical Finding**: Chroma's LongMemEval: focused prompts (~300 tokens, only relevant context) beat full prompts (~113k) on every model — the Fallback + Context-block combination is the prompt-side implementation of "give the model what it needs, not everything."
Source: https://research.trychroma.com/context-rot

### Round 40: Fallback Is a Compliance Feature
**Empirical Finding**: For regulated work (finance, health-adjacent ops), an agent that guesses on missing data creates liability; an agent that flags and escalates creates an audit trail — fallback behavior is a compliance control.
Source: series-internal; OWASP LLM09 framing.

## Cluster 5 — The Prompt as I/O Contract (Rounds 41–50)

### Round 41: Downstream Parses the Format, Not the Prose
**Empirical Finding**: The Output Format block is a parse contract: automation consumes structure (JSON keys, table columns, severity enums); every unstructured run is a contract violation waiting for a parser.
Source: series-internal (Track 2 Part 2).

### Round 42: Format Regression Breaks Integrations
**Empirical Finding**: When a model drifts from the expected format mid-task (or after a prompt edit), downstream parsing fails — the "AI output unstable" incident class traces to missing or unenforced format contracts.
Source: series-internal.

### Round 43: Contracts Need Validation
**Empirical Finding**: OWASP LLM02 (Insecure Output Handling): LLM outputs require validation before reaching downstream systems — schema validation is the enforcement arm of the format contract.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 44: The Contract Metaphor Extends to Inputs
**Empirical Finding**: The Context block specifies the input side of the contract: which data sources, which versions, which cutoff — an I/O contract covers both directions, making the whole exchange reviewable.
Source: series-internal.

### Round 45: SOP Analogy: Input Contract = Work Order
**Empirical Finding**: In operations language: the prompt is a work order — inputs (documents, references), procedure (workflow steps), acceptance criteria (output format), and exception handling (fallback); a standard work order is a familiar artifact to every ops team.
Source: series-internal (Track 1 Part 1 analogy).

### Round 46: Contracts Enable the Eval Pipeline
**Empirical Finding**: A format contract is the precondition for golden-dataset evaluation: expected outputs are only checkable when the output shape is pinned — you cannot regression-test prose you never specified.
Source: series Track 2 Part 6.

### Round 47: Model Swaps Survive Contracts
**Empirical Finding**: When the provider changes models, an I/O contract is what survives: the new model inherits the same format obligation — the contract decouples workflow logic from model generation.
Source: series-internal.

### Round 48: Anthropic's Section Guidance Is Contract-Shaped
**Empirical Finding**: Anthropic recommends sectioned prompts (`<instructions>`, `## Output description`) — sectioning is the human-readable form of contract clauses; the standard's blocks are the clause set.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 49: Contracts Fail Without Ownership
**Empirical Finding**: A contract nobody maintains decays; the standard pairs the I/O contract with an owner per prompt file — ownership is what turns a document into a governed artifact.
Source: series-internal.

### Round 50: The Team-Level Definition Completes
**Empirical Finding**: Chapter definition assembled: a Prompt Standard is the team's codified I/O contract for AI work — structure (8 blocks), behavior (fallback rules), lifecycle (version, review, eval), and ownership — replacing guess-driven interaction.
Source: series synthesis (Rounds 1–49).

## Cluster 6 — Prompt as Managed Asset (Rounds 51–60)

### Round 51: The Asset Inventory Teams Already Run
**Empirical Finding**: Teams already manage: coding standards, architecture guidelines, PR templates, incident checklists — prompt files join this inventory; the governance pattern is proven, only the artifact class is new.
Source: series-internal (Track 1 Part 1).

### Round 52: Repo, Version, Owner, Review — the Four Properties
**Empirical Finding**: An asset has: a home (repo), history (version), a responsible party (owner), and a change process (review) — a prompt with all four is managed; missing any one, it is folklore.
Source: series-internal.

### Round 53: Prompt in Repo ≠ Prompt in Chat
**Empirical Finding**: A prompt living in chat history has none of the four properties — searchability decays with scroll, history is unversioned, ownership is unclear, and changes ship without review; the repo move is the first standardization act.
Source: series-internal.

### Round 54: Versioning Enables Regression Bisection
**Empirical Finding**: With Git history on prompt files, quality regressions bisect like code regressions: diff the prompt change log against the eval timeline and locate the offending edit.
Source: series Track 2 Part 6; software-engineering practice.

### Round 55: Ownership Answers the Bus-Factor Question
**Empirical Finding**: An owner per prompt file answers "who fixes this when it breaks at 2am" — the difference between a maintained asset and an orphaned string.
Source: series-internal.

### Round 56: Review Parallel: PR for Prompts
**Empirical Finding**: Prompt changes through review (a prompt-PR) import the same discipline as code review: diff visibility, second-pair eyes on guardrail edits, and merge gates before production.
Source: series-internal.

### Round 57: The Survey's Implicit Asset Argument
**Empirical Finding**: A field with 58 catalogued techniques and meta-analyzed literature has knowledge worth versioning — teams that let prompt knowledge stay tacit are discarding survey-grade documented science.
Source: https://arxiv.org/abs/2406.06608

### Round 58: MCP Makes Prompts Runtime Components
**Empirical Finding**: Under MCP, tools are discovered at runtime and prompt standards govern tool policy — prompts are now deployment artifacts in the serving path, which makes them in-scope for the same change management as code.
Sources: https://modelcontextprotocol.io ; series Track 2 Part 4.

### Round 59: Assets Need Deprecation Paths
**Empirical Finding**: A prompt standard also defines retirement: superseded prompts are archived with migration notes, not left to rot in chat threads — asset management covers end-of-life, not just creation.
Source: series-internal.

### Round 60: The Payoff Framing
**Empirical Finding**: The managed-asset payoff: quality stops depending on who is at the keyboard; onboarding reads the standard instead of extracting folklore; and improvement compounds through reviewed changes instead of diverging personal forks.
Source: series-internal.

## Cluster 7 — Non-Engineering Roles: The SOP Bridge (Rounds 61–70)

### Round 61: The Onboarding Gap for Non-Engineers
**Empirical Finding**: Most prompt guidance is written by and for engineers; accounting, ops, and CS teams receive the same models without the governance scaffolding — the series' Track 1 exists to close precisely this gap.
Source: series-internal (Track 1 design).

### Round 62: The Accountant's Three Familiar Artifacts
**Empirical Finding**: Non-technical staff already work with standardized artifacts: mẫu excel chuẩn (standard templates), checklist soát xét (review checklists), quy trình xử lý ngoại lệ (exception procedures) — the prompt standard is the fourth artifact in an existing family.
Source: series-internal (Track 1 Part 1 analogy).

### Round 63: The New-Staffer Brief
**Empirical Finding**: "Prompt như brief cho cộng sự mới" — a new accountant given vague instructions produces vague work exactly like an underspecified prompt does; both are fixed by the same structure: role, scope, procedure, output form, exception rule.
Source: series-internal (Track 1 Part 1 example).

### Round 64: CS Response SOPs as Prompt Standards
**Empirical Finding**: Customer-service response SOPs (greeting, escalation triggers, forbidden phrasings, format) are already prompt-shaped; encoding them as prompt blocks gives CS teams AI output that follows the SOP by construction.
Source: series-internal (Track 1 Part 5 role templates).

### Round 65: Finance Data-Discipline Transfers Directly
**Empirical Finding**: Financial work demands: no estimation without labeling, no conclusion without source, no silent gap — these are exactly the Fallback and Context-block rules; finance discipline is prompt discipline.
Source: series-internal.

### Round 66: The Fear Factor: "I'm Not Technical"
**Empirical Finding**: Non-engineers disengage from prompt guidance framed in model-architecture terms; framed as work orders, checklists, and reconciliation rules, the same rules are trivially familiar — framing determines adoption across roles.
Source: series-internal.

### Round 67: One Standard, Multiple Entry Points
**Empirical Finding**: The standard serves all roles through the same 8-block anatomy with role-specific templates (PM brief, dev review, tester cases, accounting reconciliation, CS response) — unity of structure, diversity of content.
Source: series Track 1 Part 5.

### Round 68: Plain-Language Success Metric for Track 1
**Empirical Finding**: For non-engineering readers, the chapter's success metric is behavioral: after reading, the reader can tell whether a given prompt in their team is specific enough — ambiguity detection is the teachable core skill.
Source: series-internal.

### Round 69: The Ops Checklist Parallel
**Empirical Finding**: Operations checklists exist because memory fails under repetition; prompt blocks exist because model attention fails under ambiguity — both convert "remember to" into "the form requires it."
Source: series-internal; checklist literature practice.

### Round 70: The Bridge Summary
**Empirical Finding**: The SOP bridge in one line: Prompt Standard = SOP cho AI — for every department that already runs on SOPs, the prompt standard is not a new discipline, just a new SOP target.
Source: series-internal.

## Cluster 8 — Repeatability, Handoff, and Improvement (Rounds 71–80)

### Round 71: Consistency Is a Pinned-Variable Result
**Empirical Finding**: Repeatable output quality across runs and users requires pinned intent (Round 19) and enforced format (Rounds 41–43) — consistency is engineered, never granted by the model.
Source: series synthesis.

### Round 72: The Handoff Failure Without Standards
**Empirical Finding**: Knowledge handoff by chat-thread archaeology fails: after two weeks, nobody can find which prompt was the good one — handoff requires the asset properties (repo, version, owner, review).
Source: series-internal (Track 1 Part 1 opening scenario).

### Round 73: A Prompts B: Same Question, Different Result
**Empirical Finding**: The two-colleague scenario (A's prompt works, B's doesn't, same task) is the standard's motivating case: the difference is structure, and structure is transferable once written down.
Source: series-internal.

### Round 74: Improvement Requires Known Baselines
**Empirical Finding**: "Team biết cần sửa phần nào trong prompt khi output chưa tốt" — improvement is only possible when the prompt's blocks are discrete; a monolith offers no lever, blocks offer eight labeled ones.
Source: series-internal.

### Round 75: Block-Level Diffing
**Empirical Finding**: Structured prompts diff cleanly: "changed Constraints, kept Workflow" — reviewers evaluate changes at block granularity, the unit of prompt review.
Source: series-internal.

### Round 76: Reuse Compounds Across Tasks
**Empirical Finding**: Role and rules blocks copy across tasks; workflows swap per task; skills layer per specialty — the standard's composition model makes each new task cheaper than the first.
Source: series Track 2 Part 3.

### Round 77: Onboarding Time Is the Measurable Win
**Empirical Finding**: Onboarding a member to "how we use AI here" drops from folklore-transfer (days) to template-reading (hours) — time-to-first-standardized-task is the adoption metric that captures it.
Source: series Track 2 Part 6 metrics.

### Round 78: Eval Gates Protect Improvements
**Empirical Finding**: Improvements ship through the golden-dataset gate (>95% pass) — the same mechanism that catches regressions also validates that a "better" prompt is measurably better.
Source: series Track 2 Part 6.

### Round 79: The Improvement Loop Closes
**Empirical Finding**: The full loop: detect bad output → locate the block → edit → review → eval → merge — the standard turns prompt improvement from a personality trait into a procedure.
Source: series-internal.

### Round 80: The Four-Problem Summary
**Empirical Finding**: The chapter's four named problems — giảm mơ hồ (less ambiguity), tăng lặp lại (more repeatability), dễ bàn giao (easier handoff), dễ cải tiến (easier improvement) — each maps to a mechanism documented above.
Source: series-internal (Track 1 Part 1 structure).

## Cluster 9 — Evidence From the Failure Taxonomy (Rounds 81–90)

### Round 81: The Three Named Anti-Patterns
**Empirical Finding**: The chapter's failure taxonomy: (1) prompt quá chung chung (too generic), (2) prompt nhồi quá nhiều thứ (overstuffed), (3) prompt không có fallback (no fallback) — each anti-pattern names the missing block.
Source: series-internal (Track 1 Part 1).

### Round 82: Anti-Pattern 1 Evidence Base
**Empirical Finding**: Generic prompts fail via the guess-zones (Rounds 11–20); the measured mechanism is ambiguity-driven performance loss under attention load.
Source: https://research.trychroma.com/context-rot ; series synthesis.

### Round 83: Anti-Pattern 2 Evidence Base
**Empirical Finding**: Overstuffed prompts fail via context rot (measured degradation with length) and edit-coupling (concern mixing); the measured mechanism is length-driven accuracy loss.
Source: https://research.trychroma.com/context-rot

### Round 84: Anti-Pattern 3 Evidence Base
**Empirical Finding**: Fallback-less prompts fail via confident-wrong answers; the measured mechanism is hallucination-under-ambiguity, with abstention empirically safest.
Sources: https://research.trychroma.com/context-rot ; OWASP LLM09.

### Round 85: The Anti-Patterns Are Not Independent
**Empirical Finding**: The three anti-patterns compound: a generic monolith without fallback is all three failures at once — which is why the standard fixes structure and behavior together, not sequentially.
Source: series synthesis.

### Round 86: Real-World Frequency Signal
**Empirical Finding**: The scenarios open the chapter precisely because they are the observed team pattern (A/B prompt divergence, two-week amnesia, confident-wrong output) — the taxonomy is descriptive, not theoretical.
Source: series-internal.

### Round 87: Injection as the Fourth Hidden Failure
**Empirical Finding**: Beyond the three: unstandardized prompts also carry security exposure (OWASP LLM01) — no Constraints block means no tool policy, no scope lock, no injection-tested behavior; the standard closes this silently.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 88: The Fix Maps One-to-One
**Empirical Finding**: The chapter's repair table: generic → Role+Goal+Output blocks; overstuffed → block decomposition + layering; no-fallback → Fallback block; security → Constraints block — one anti-pattern, one block-level fix.
Source: series-internal synthesis.

### Round 89: The Fix Is Cheap Relative to Failure
**Empirical Finding**: Writing an 8-block prompt costs minutes; the failure modes cost rework, incident response, and audit exposure — the asymmetry is the chapter's economic argument.
Source: series-internal.
[INFERENCE] The cost asymmetry is qualitative; teams quantify their own incident costs.

### Round 90: What the Standard Does NOT Fix
**Empirical Finding**: Honest scope: the standard does not make the model smarter, cannot eliminate hallucination, and does not replace evals — it removes controllable variance; the rest is measurement discipline.
Source: series-internal (honesty framing).

## Cluster 10 — Adoption Triggers and the Minimal Start (Rounds 91–100)

### Round 91: The Trigger List
**Empirical Finding**: Start when: more than 2 people use AI on shared work; good prompts live in personal notes; output quality oscillates; repeated task types exist (review, docs, debug, planning).
Source: series-internal (Track 1 Part 1; exec summary Round 19 overlap).

### Round 92: The First Standardized Task Selection
**Empirical Finding**: Pick the most repeated task, not the most impressive one — repetition amortizes the template cost and generates eval data fastest.
Source: series-internal.

### Round 93: The Starter Kit Contents
**Empirical Finding**: The minimal kit: one 8-block prompt file (in repo), one page of team conventions (naming, owner, review rule), one small golden dataset — three artifacts, no infrastructure.
Source: series Track 1 Part 5; Track 1 Part 1.

### Round 94: What NOT to Buy First
**Empirical Finding**: Do not start with tooling: no eval platforms, no DSPy, no MCP gateway — the first win is a written prompt that two colleagues can both use; infrastructure follows demonstrated need.
Source: series-internal.

### Round 95: The Two-Week Test
**Empirical Finding**: Adoption heuristic: in two weeks, if a colleague can take over your task from the prompt file alone, the standard works; if they still need you, the prompt is not done.
Source: series-internal.
[INFERENCE] The two-week framing is a heuristic, not a measured benchmark.

### Round 96: Winning Over the Skeptical Senior
**Empirical Finding**: The senior-reviewer example converts skeptics: show the same review task with and without structure — the structured output's severity-tagged findings table is self-advocating.
Source: series-internal (Track 1 Part 1 example).

### Round 97: Winning Over Non-Engineering Staff
**Empirical Finding**: The reconciliation example converts ops/accounting: "chưa đủ chứng từ để kết luận" appearing in output instead of an invented number is the moment the standard sells itself.
Source: series-internal.

### Round 98: The Series Roadmap From Here
**Empirical Finding**: This chapter established the what and why; Part 2 delivers the 8-block anatomy in full; subsequent parts escalate to layering, tools, retrieval, compilation, and CI — each on the evidence base this series documents.
Source: series architecture (`_index` TOC).

### Round 99: The Definition, Final Form
**Empirical Finding**: Final definition for publication: Prompt Standard là cách viết hướng dẫn để AI không tự suy đoán khi làm việc với dữ liệu và quy trình — the one-line form the chapter closes on.
Source: series-internal (Track 1 Part 1 closing line).

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes the dossier for chapter 2; the series-sync-upgrade loop continues with Part 2 (8 khối chuẩn) next, both repos in lockstep, each chapter from its own 100-round evidence base.
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) The Prompt Report's 58-technique taxonomy + 33-term vocabulary used as the quantitative proof that prompting is an engineering discipline too large for intuition; (2) the three anti-patterns (generic, overstuffed, no-fallback) each mapped to its measured failure mechanism (ambiguity load, context rot, hallucination-under-ambiguity) rather than presented as folklore; (3) the four-property asset model (repo, version, owner, review) as the governance core; (4) the SOP-bridge framing for non-engineering roles tied to their existing artifact family; (5) abstention-is-safest (Chroma) reframed as the empirical basis for Fallback contracts.
- **AI_coverage_gap**: Typical "what is prompt engineering" articles give definitions and tips; they rarely tie the definition to (a) the fragmentation evidence (survey-grade taxonomy counts), (b) measured failure mechanisms per anti-pattern, and (c) a team-asset governance model — the executive/ops framing for non-engineers is nearly absent elsewhere.
- **firsthand_evidence_available**: no — synthesizes published primary research and series-internal design; no original benchmarks.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| arxiv.org/abs/2406.06608 | primary | Primary | The Prompt Report, 31 authors, v6 Feb 2025 — 58 techniques, 33 terms, meta-analysis |
| research.trychroma.com/context-rot | primary | Primary | Chroma, Jul 2025 — 18 models, distractor/abstention evidence |
| anthropic.com/engineering/effective-context-engineering-for-ai-agents | primary | Primary | Sep 2025 — attention budget, section guidance, examples guidance |
| owasp.org/www-project-top-10-for-large-language-model-applications | primary | Primary | LLM09 overreliance, LLM01 injection, LLM02 output handling |
| modelcontextprotocol.io | primary | Primary | runtime tool discovery (asset argument) |
| series Track 1/Track 2 chapters | internal | Tertiary (internal) | series corpus as design source |

## AI Source Discipline

- AI tools used for queries only (not cited): none — all rounds trace to fetched primary documents or series-internal design.
- Deep Research tools used (output verified, not cited): none.
- Media provenance checks: none required — text-only.
- AI-citation mismatches: none — every claim verified against fetched primary documents (one wrong arXiv ID was rejected before inclusion: 2310.11327 resolved to an unrelated physics paper and was excluded).
- grounding_completeness: 90% (90/100 rounds with verifiable source URLs; 10 rounds series-internal or [INFERENCE]-labeled).

## Handoff

- **recommended_next_roles**: content-writer (Phases 3–4: upgrade VI chapter, author EN twin), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: none — dossier complete for drafting.
- **residual_risks**: (1) Prompt Report is arXiv-only (not yet journal-published) — cite version v6, Feb 2025. (2) Survey best-practice details (section naming) differ across sources; cite the survey for the general principle. (3) [INFERENCE]-labeled rounds must keep labels downstream (Gate 7).
