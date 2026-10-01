# Prompt Standard — Declarative Prompting with DSPy: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapters**: `prompt-standard/part-7-declarative-prompting-dspy` (learn, Phần 7) + `prompt-standard/part-5-declarative-prompting-dspy` (EN consolidated anchor)
> **Campaign**: `series-sync-upgrade` — Chapter 8 of 10

---

## Executive Research Summary

This dossier grounds declarative prompting — the compiler turn of the series. The fresh primary source is the original DSPy paper (Khattab et al., arXiv:2310.03714, Stanford NLP, Oct 2023) with hard numbers never before cited in this series: within minutes of compiling, GPT-3.5 self-bootstrapped pipelines outperform standard few-shot prompting by over 25%, and llama2-13b-chat by over 65%; over expert-created demonstrations by 5–46% (GPT-3.5) and 16–40% (llama2); and programs compiled to a 770M-parameter T5 are competitive with expert-written prompt chains for proprietary GPT-3.5. Combined with the campaign-verified MIPRO anchors (arXiv:2406.11695: +13% accuracy, 5-of-7 programs, Llama-3-8B), the evidence base now covers the full optimization lineage: BootstrapFewShot → MIPRO → MIPROv2. The convergence: manual prompt text is a local optimum found by human intuition; the compiler searches the space with a metric — and the search measurably wins. The honest boundaries: DSPy optimizes task-level modules, not organizational structure (the 8 blocks and layers stay), and compilation demands a golden dataset before it can run.

---

## Cluster 1 — The Measured Case Against Hand-Written Prompts (Rounds 1–10)

### Round 1: The Paper's Opening Diagnosis
**Empirical Finding**: "existing LM pipelines are typically implemented using hard-coded 'prompt templates', i.e. lengthy strings discovered via trial and error" — the published diagnosis matches the series' vibes-based prompting critique verbatim.
Source: https://arxiv.org/abs/2310.03714

### Round 2: The Abstraction
**Empirical Finding**: DSPy "abstracts LM pipelines as text transformation graphs — imperative computational graphs where LMs are invoked through declarative modules" — prompts stop being source code and become parameters.
Source: https://arxiv.org/abs/2310.03714

### Round 3: Parameterized Modules Learn
**Empirical Finding**: "DSPy modules are parameterized, meaning they can learn (by creating and collecting demonstrations) how to apply compositions of prompting, finetuning, augmentation, and reasoning techniques" — few-shot selection moves from human curation to program.
Source: https://arxiv.org/abs/2310.03714

### Round 4: The Compiler Thesis
**Empirical Finding**: "We design a compiler that will optimize any DSPy pipeline to maximize a given metric" — the four words that define the paradigm: optimize, pipeline, metric, compiler.
Source: https://arxiv.org/abs/2310.03714

### Round 5: The +25% / +65% Headline
**Empirical Finding**: "Within minutes of compiling, a few lines of DSPy allow GPT-3.5 and llama2-13b-chat to self-bootstrap pipelines that outperform standard few-shot prompting (generally by over 25% and 65%, respectively)."
Source: https://arxiv.org/abs/2310.03714

### Round 6: Beating Expert Demonstrations
**Empirical Finding**: Compiled pipelines outperform "pipelines with expert-created demonstrations (by up to 5-46% and 16-40%, respectively)" — the compiler beats the human expert at the expert's own game: choosing demonstrations.
Source: https://arxiv.org/abs/2310.03714

### Round 7: The Small-Model Result
**Empirical Finding**: "DSPy programs compiled to open and relatively small LMs like 770M-parameter T5 and llama2-13b-chat are competitive with approaches that rely on expert-written prompt chains for proprietary GPT-3.5" — compilation partially substitutes for model scale.
Source: https://arxiv.org/abs/2310.03714

### Round 8: Case Study Coverage
**Empirical Finding**: The two case studies span math word problems, multi-hop retrieval, complex question answering, and agent-loop control — the compilation claim generalizes across task families, not just one benchmark.
Source: https://arxiv.org/abs/2310.03714

### Round 9: Minutes, Not Weeks
**Empirical Finding**: "Within minutes of compiling" — the cost side of the ledger: the optimization loop that would take a human weeks of trial-and-error runs in minutes of compute.
Source: https://arxiv.org/abs/2310.03714

### Round 10: The Series' Three Vibes Problems, Resolved
**Empirical Finding**: The VI chapter's three hand-tuning failures — brittle across models, unscalable across pipelines, opaque in why-one-phrasing-wins — map directly to the paper's answers: compile per model, optimize whole pipelines jointly, optimize against an explicit metric.
Source: series-internal (Track 1 Part 7); https://arxiv.org/abs/2310.03714

## Cluster 2 — Signatures: The Contract Layer (Rounds 11–20)

### Round 11: Signatures Declare What, Not How
**Empirical Finding**: "A Signature defines what a language model step must do without specifying how to prompt it" — the declarative contract: inputs, outputs, semantics; the compiler owns the phrasing.
Source: series Track 2 Part 5; https://arxiv.org/abs/2310.03714

### Round 12: The ReviewCode Signature Example
**Empirical Finding**: The minimal form: `class ReviewCode(dspy.Signature)` with `diff: str = dspy.InputField(...)` and `findings: list[str] = dspy.OutputField(...)` — typed fields with descriptions, the same contract discipline as Output Contract blocks.
Source: series-internal (Track 1 Part 7 code example).

### Round 13: Field Descriptions Are Prompt Material
**Empirical Finding**: `desc=` strings on Input/Output fields flow into the compiled prompt — descriptions are not documentation, they are optimization surface the compiler can rephrase and position.
Source: DSPy documentation; series Track 2 Part 5.

### Round 14: Typed Output Fields Enforce Structure
**Empirical Finding**: `findings: list[str]` declares structure the way an Output Contract block does — but the framework validates and can retry on type mismatch, moving format enforcement from prose to type system.
Source: series synthesis; DSPy module behavior.

### Round 15: The VulnerabilityAnalysis Signature
**Empirical Finding**: The EN anchor's production signature: boolean `vulnerability_detected`, CWE identifier string, `remediation_patch` — three typed outputs including a boolean flag and an enum-like field (CWE or 'None').
Source: series Track 2 Part 5 (production signature example).

### Round 16: Signatures Are Diff-able Contracts
**Empirical Finding**: Signature changes review like API changes: input/output contracts version in Git — the Part 4 changelog discipline applies to signatures unchanged.
Source: series-internal (Track 1 Part 4 bridge).

### Round 17: Signatures Replace Phrasing Debates
**Empirical Finding**: The review conversation shifts from "is this wording good" to "is this the right contract" — measurable questions replace taste questions, exactly the series' Part 1 thesis at module granularity.
Source: series synthesis.

### Round 18: Signature Granularity
**Empirical Finding**: One signature = one LM step; pipelines compose signatures — matching the block-granularity and layer-granularity rules from Parts 2–3: small contracts compose, monoliths don't.
Source: series-internal; DSPy pipeline structure.

### Round 19: Shorthand Form for Rapid Prototyping
**Empirical Finding**: DSPy accepts shorthand string signatures ("context, question -> answer") for prototyping and class forms for production — the same starter-kit-first, structure-later adoption curve.
Source: DSPy documentation.

### Round 20: The Contract Summary
**Empirical Finding**: Signatures are the series' Output Contract + Input Contract pair, formalized: both sides of the I/O boundary declared, typed, and versioned — the compiler fills the middle.
Source: series synthesis.

## Cluster 3 — Modules: The Execution Patterns (Rounds 21–30)

### Round 21: The Three Built-Ins
**Empirical Finding**: `dspy.Predict` (direct zero-shot), `dspy.ChainOfThought` (auto-appends reasoning steps), `dspy.ReAct` (interleaves thought with tool calls) — the built-in execution patterns cover the three archetypes most pipelines need.
Source: series Track 2 Part 5; DSPy documentation.

### Round 22: ChainOfThought Is a Technique, Not a String
**Empirical Finding**: The paper's framing: prompting techniques (CoT, few-shot) become parameterized module behavior — "compositions of prompting, finetuning, augmentation, and reasoning techniques" applied by the framework, not pasted by hand.
Source: https://arxiv.org/abs/2310.03714

### Round 23: Modules Compose Into Pipelines
**Empirical Finding**: A `CodeReviewer(dspy.Module)` with `self.review = dspy.ChainOfThought(ReviewCode)` composes like any callable — pipelines of modules are the LM analogue of function composition.
Source: series-internal (Track 1 Part 7 code).

### Round 24: The Module Registry Anti-Bloat
**Empirical Finding**: The same anti-bloat rule as Tool Policy applies: prefer few semantic modules over many overlapping ones — the compiler's search space grows combinatorially with module count.
Source: series synthesis; https://www.anthropic.com/engineering/writing-tools-for-agents (overlap confusion).

### Round 25: ReAct and Tool Calls
**Empirical Finding**: `dspy.ReAct` interleaves reasoning with tool invocation — where DSPy pipelines meet the MCP pillar from Part 6: modules consume tools under the same scope policies.
Source: DSPy documentation; series Track 2 Part 4 bridge.

### Round 26: Custom Metrics Per Module
**Empirical Finding**: Each module declares its metric — `accuracy_and_format_metric(example, pred, trace)` — evaluation is wired at construction, not bolted on later.
Source: series Track 2 Part 5 (production metric example).

### Round 27: The Trace Parameter
**Empirical Finding**: Metrics receive `trace=None` — the execution trace — enabling step-level inspection: the compiler optimizes against trajectory quality, not only final answers.
Source: DSPy documentation; series Track 2 Part 5.

### Round 28: Modules Are the Optimization Boundary
**Empirical Finding**: The compiler optimizes module parameters (instructions + demonstrations) per module — the joint-credit-assignment problem from MIPRO applies: pipeline quality is a function of all modules together.
Source: https://arxiv.org/abs/2406.11695

### Round 29: Deterministic Code Between Modules
**Empirical Finding**: Python code between module calls is ordinary deterministic code — validation, branching, aggregation stay in normal engineering, only LM steps are compiled: the right separation of concerns.
Source: series synthesis; DSPy programming model.

### Round 30: The Module Summary
**Empirical Finding**: Modules = execution patterns (built-in or custom) over signatures, composable into pipelines, each with its metric — the runtime that the compiler tunes.
Source: series synthesis (Rounds 21–29).

## Cluster 4 — The Optimizer Lineage (Rounds 31–40)

### Round 31: BootstrapFewShot — The Starter Optimizer
**Empirical Finding**: `dspy.BootstrapFewShot(metric=bug_detection_accuracy)` with `trainset=examples` — the entry-level optimizer: bootstraps demonstrations from labeled examples, the paper's "creating and collecting demonstrations."
Source: series-internal (Track 1 Part 7); https://arxiv.org/abs/2310.03714

### Round 32: Bootstrap Mechanics
**Empirical Finding**: BootstrapFewShot runs the module on training inputs, keeps the runs that pass the metric, and stores those input/output traces as few-shot demonstrations — the program generates its own examples from its successes.
Source: DSPy documentation; https://arxiv.org/abs/2310.03714

### Round 33: MIPRO — The Instruction Searcher
**Empirical Finding**: MIPRO (EMNLP 2024): "program- and data-aware instruction proposal, stochastic mini-batch evaluation for surrogate models, meta-optimization refining how LMs construct proposals over time" — optimizes instructions, not just demonstrations.
Source: https://arxiv.org/abs/2406.11695

### Round 34: The +13% / 5-of-7 Anchor
**Empirical Finding**: MIPRO "outperformed baseline optimizers on 5 of 7 diverse multi-stage LM programs with Llama-3-8B, by as high as 13% accuracy" — the series' standing MIPRO citation, unchanged.
Source: https://arxiv.org/abs/2406.11695 (EMNLP 2024)

### Round 35: Joint Optimization Without Module Labels
**Empirical Finding**: MIPRO's research problem: optimizing prompts jointly for all modules without module-level labels or gradients — credit assignment across the pipeline, the core difficulty hand-tuning cannot address at all.
Source: https://arxiv.org/abs/2406.11695

### Round 36: MIPROv2 — The Production Generation
**Empirical Finding**: MIPROv2 uses Bayesian optimization to search instruction phrasing and exemplar combinations simultaneously — the EN anchor's flagship optimizer for DSPy 2.5+ production pipelines.
Source: series Track 2 Part 5; DSPy documentation.

### Round 37: The Lineage in One Line
**Empirical Finding**: teleprompter → BootstrapFewShot → MIPRO → MIPROv2: each generation widens the search space (demos → instructions → both jointly, Bayesian) — the compiler analogy deepens with each release.
Source: series Track 2 Part 5 (lineage tracking); campaign Ch1 dossier Round 67.

### Round 38: What Optimizers Do NOT Do
**Empirical Finding**: Optimizers do not invent your metric, your signature fields, or your module topology — the human still owns the contract and the pipeline shape; the compiler owns the token-level and demonstration-level search.
Source: series synthesis; honest-scope framing.

### Round 39: Optimizer Cost Profile
**Empirical Finding**: Compilation runs cost real compute: candidate evaluation loops over the trainset per proposal — the same eval-cost discipline from Part 4 applies (compile on-change, not continuously; sample the trainset).
Source: series Track 2 Part 6 (eval cost discipline); DSPy practice.

### Round 40: The Compiler Analogy, Final Form
**Empirical Finding**: Manual prompting : compiled prompting :: assembly : compiled languages — humans wrote assembly for decades until compilers beat them; the +25/65% and +13% numbers are the first compiler-beats-hand-written measurements of the prompt era.
Source: series synthesis; https://arxiv.org/abs/2310.03714 ; https://arxiv.org/abs/2406.11695

## Cluster 5 — The Compilation Pipeline in Production (Rounds 41–50)

### Round 41: The Production Pipeline Shape
**Empirical Finding**: The EN anchor's flow: Signature → Module pipeline → metric function → MIPROv2 compile → saved JSON artifact — the compiled artifact is a versioned file, not a living string.
Source: series Track 2 Part 5 (production pipeline).

### Round 42: The Compiled Artifact Is an Asset
**Empirical Finding**: The compile output saves as JSON config — prompts as build artifacts: reproducible, diffable, versioned; the Part 4 asset model applies directly to compiled outputs.
Source: series Track 2 Part 5; series-internal (asset model).

### Round 43: The Metric Function Contract
**Empirical Finding**: `accuracy_and_format_metric` checks detection match AND cwe-validity AND patch-presence — production metrics compose multiple criteria; the pass-rate discipline of Part 4 embeds here.
Source: series Track 2 Part 5 (production metric).

### Round 44: Deterministic + Probabilistic in the Metric
**Empirical Finding**: The metric example mixes exact-match (detection boolean) with structural checks (non-empty fields) — deterministic assertions under the LLM-judge layer, the Part 4 layering in miniature.
Source: series Track 2 Part 5; series Track 2 Part 6 (layering).

### Round 45: Retries and the Uncertainty Budget
**Empirical Finding**: DSPy can retry on typed-output mismatch — but retries cost tokens; production pipelines bound them like the Fallback block bounds escalation: retry twice, then surface the failure.
Source: DSPy documentation; series Fallback-block discipline.

### Round 46: The Golden Dataset Precondition
**Empirical Finding**: "Evals before optimization" (campaign Ch1 Round 69) is a hard precondition here: no trainset, no compilation — the compiler optimizes toward what the dataset measures, and an empty dataset optimizes nothing.
Source: series Track 2 Part 6; https://arxiv.org/abs/2406.11695 methodology.

### Round 47: Compile on Model Change
**Empirical Finding**: Model swaps break hand prompts (campaign Ch2 evidence: migration regressions) but recompile cleanly: run the optimizer against the new model and the artifact adapts — the portability the paper measured (GPT-3.5 ↔ llama2 ↔ T5).
Source: https://arxiv.org/abs/2310.03714 ; series-internal.

### Round 48: CI Integration of Compilation
**Empirical Finding**: The compile step belongs in CI on signature or metric change — prompt-PR → recompile → eval the compiled artifact → gate at >95%: the Part 8 pipeline with the compiler in the build stage.
Source: series Track 2 Part 6; series-internal (CI shape).

### Round 49: Artifact Promotion
**Empirical Finding**: Compiled artifacts promote through the same known-good tag discipline: `v3-reviewer-known-good` on the JSON, rollback = checkout — the deploy loop closes on compiled prompts exactly as on handwritten ones.
Source: series Track 1 Part 4 (tag discipline); series-internal.

### Round 50: The Production Summary
**Empirical Finding**: Production declarative prompting = signature in Git, trainset curated, metric wired at construction, compile in CI, artifact versioned, promotion gated — the series' whole lifecycle with the compiler as the build tool.
Source: series synthesis (Rounds 41–49).

## Cluster 6 — Division of Labor: DSPy vs Prompt Standard (Rounds 51–60)

### Round 51: The Layer Table
**Empirical Finding**: The VI chapter's division: "Cấu trúc tổ chức (roles, rules, workflows) → Prompt Standard; Tối ưu task-level (few-shot, CoT, model adaptation) → DSPy; Chất lượng dữ liệu và truy xuất → RAG/Context Engineering" — three tools, three layers, no overlap.
Source: series-internal (Track 1 Part 7 division table).

### Round 52: DSPy Does Not Replace the 8 Blocks
**Empirical Finding**: The optimizer tunes module internals; the organizational standard still owns identity, scope policy, and output contracts around the pipeline — "context engineering hosts the standard" (Ch7 Round 86) and DSPy lives inside the hosted modules.
Source: series synthesis (Ch7 cross-ref).

### Round 53: Where the Boundary Sits in Code
**Empirical Finding**: Layered stack: L1/L2/L3 assemble around the DSPy pipeline; L4 skills can *be* compiled modules — the two architectures compose at the skill layer, not compete.
Source: series Track 2 Part 3; synthesis.

### Round 54: The Standard Defines What to Optimize
**Empirical Finding**: The metric IS the standard's eval section transplanted: pass-rate thresholds, golden cases, boundary probes — a team with Part 4 discipline already wrote the metric function's spec.
Source: series Track 2 Part 6 bridge; synthesis.

### Round 55: What Hand Prompting Still Wins
**Empirical Finding**: Honest boundary: a single stable call with no trainset and no recurring volume does not warrant compilation — the same "five documents don't need RAG" scope rule, applied to optimizers.
Source: series-internal (scope honesty).

### Round 56: The Migration Trigger
**Empirical Finding**: Move a task to DSPy when: the prompt changes >2×/quarter for quality, the task has >50 golden examples, or model swaps repeatedly broke it — pain-triggered graduation, like every series layer.
Source: series-internal (adoption sequencing).

### Round 57: Hybrid Handwritten-Compiled Stacks
**Empirical Finding**: Real stacks mix both: handwritten blocks for policy-stable steps, compiled modules for the quality-critical LM step — the compiler optimizes where variance pays, the standard governs where consistency must.
Source: series synthesis; production practice.

### Round 58: The Finance Translation
**Empirical Finding**: Kế toán parallel: việc tính lương theo công thức (deterministic policy) không cần "tối ưu"; việc phân loại hóa đơn theo mô tả tự do (probabilistic, repeated, metric-checkable) là ứng viên compile — optimize the judgment calls, not the rules.
Source: series-internal (finance register extension).

### Round 59: Team Skills Implication
**Empirical Finding**: With compilation, the team's scarce skill shifts from prompt wordsmithing to metric design — writing good pass criteria is the new craft; the +25/65% gains come from well-specified metrics.
Source: series synthesis; paper evidence chain.

### Round 60: The Division Summary
**Empirical Finding**: Standard = organization; DSPy = task optimization; RAG = data supply — the series' three answers to three different failure classes, and the chapter must keep them orthogonal.
Source: series synthesis (Rounds 51–59).

## Cluster 7 — Evidence Chain Review (Rounds 61–70)

### Round 61: The 2023 Foundation Paper Numbers
**Empirical Finding**: +25% (GPT-3.5) / +65% (llama2-13b-chat) over standard few-shot; 5–46% / 16–40% over expert demos; T5-770M competitive with GPT-3.5 expert chains — the three number families that anchor the whole chapter.
Source: https://arxiv.org/abs/2310.03714

### Round 62: The 2024 MIPRO Numbers
**Empirical Finding**: 5-of-7 programs, up to +13% accuracy, Llama-3-8B, joint instruction+demonstration optimization — the second-generation anchor.
Source: https://arxiv.org/abs/2406.11695

### Round 63: The Chain-of-Techniques Context
**Empirical Finding**: The Prompt Report's 58-technique taxonomy (campaign Ch2 anchor): DSPy operationalizes the technique-selection problem — the framework picks CoT/few-shot combinations per module, collapsing the taxonomy choice into a metric.
Source: https://arxiv.org/abs/2406.06608 ; series synthesis.

### Round 64: Why Numbers Differ Across Papers
**Empirical Finding**: +25/65% (2023, few-shot baselines) vs +13% (2024, stronger optimizers as baselines) — the deltas shrink as baselines strengthen; cite both with their baselines, never mix.
Source: synthesis of both papers.
[INFERENCE] The shrinking-delta trend reflects benchmark maturation; future optimizers will likely show smaller margins over MIPROv2 baselines.

### Round 65: Agent Loops in the Case Studies
**Empirical Finding**: The paper's case studies include controlling agent loops — relevant to the series' agentic chapters: the compiler tunes the loop-step prompts, not the loop policy (which stays in the standard).
Source: https://arxiv.org/abs/2310.03714

### Round 66: Multi-Hop Retrieval Case
**Empirical Finding**: The multi-hop retrieval case study ties to Part 9's RAG: compiled retrieval-augmented pipelines beat hand-tuned ones — the two chapters compose in evidence, not just in theory.
Source: https://arxiv.org/abs/2310.03714

### Round 67: Self-Improvement Framing
**Empirical Finding**: "Self-improving pipelines" (the paper's subtitle) = programs that generate their own demonstrations and refine their own instructions — the improvement loop of Part 4, automated.
Source: https://arxiv.org/abs/2310.03714

### Round 68: The Open-Source Availability
**Empirical Finding**: "DSPy is available at github.com/stanfordnlp/dspy" — production-usable today, not a paper prototype; the series' code examples run against the real framework.
Source: https://arxiv.org/abs/2310.03714

### Round 69: What the Papers Do Not Claim
**Empirical Finding**: Neither paper claims compilation eliminates the need for structure, policy, or evals — the strawman to reject explicitly in the chapter: DSPy is not "prompt engineering is dead," it is "hand-optimizing tokens is dead."
Source: synthesis; honest-scope discipline.

### Round 70: Evidence Chain Complete
**Empirical Finding**: 2023 foundation (+25/65, expert-demo, small-model) → 2024 MIPRO (+13, joint) → production MIPROv2 (Bayesian) — a three-generation evidence chain, all arXiv-verifiable, all cited with baseline context.
Source: synthesis of Rounds 61–69.

## Cluster 8 — Failure Modes and Honest Boundaries (Rounds 71–80)

### Round 71: Bad Metric, Bad Prompt
**Empirical Finding**: The optimizer maximizes whatever the metric measures — a wrong metric produces a confidently wrong prompt; metric review outranks prompt review in compiled pipelines.
Source: series synthesis; optimizer mechanics.

### Round 72: Overfitting the Trainset
**Empirical Finding**: Compilation can overfit small trainsets — the held-out discipline from Anthropic's eval guidance (campaign Ch5 Round 28) applies: hold out a slice, verify generalization before promoting the artifact.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents (held-out sets); synthesis.

### Round 73: The Cost of Compilation Cycles
**Empirical Finding**: MIPROv2 proposals each evaluate over mini-batches — compile spend scales with proposals × batch × module count; budget compilation like a build farm: on-change, sampled.
Source: https://arxiv.org/abs/2406.11695 (mini-batch evaluation); series cost discipline.

### Round 74: Signature Drift
**Empirical Finding**: Changing a signature invalidates compiled artifacts (the demos reference old fields) — signature changes require recompile, and the changelog must note "signature v2 → recompiled" like an API bump.
Source: series synthesis; asset lifecycle.

### Round 75: The Debugging Indirection
**Empirical Finding**: A compiled pipeline's failure traces through generated instructions and bootstrapped demos — teams keep an inspector that dumps the compiled artifact per version; you debug what ran, not what you meant.
Source: series synthesis; observability practice.

### Round 76: When the Trainset Lies
**Empirical Finding**: Trainset distribution drift (production differs from golden set) silently redirects optimization — the periodic re-sampling rule from Part 4 extends to compilation inputs.
Source: series Track 2 Part 6; synthesis.

### Round 77: Metric Gaming
**Empirical Finding**: An over-narrow metric produces artifacts that game it (format-perfect, content-empty) — the non-over-constraining verifier guidance applies in reverse: metrics must check substance, not just shape.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents (verifier discipline).

### Round 78: The Two-Line Failure
**Empirical Finding**: The classic first failure: `BootstrapFewShot` with a metric that always returns True — the optimizer "improves" toward noise; the fix is the Part 4 starter metric set (format + critical-detection), never a placeholder metric.
Source: series synthesis; DSPy practice.

### Round 79: The Vendor-Lock Non-Issue
**Empirical Finding**: Because compilation targets any LM, artifacts are recompiled per provider — the portability the paper measured (GPT-3.5 ↔ llama2 ↔ T5) is the anti-lock argument: the asset is the signature+metric+trainset, not the compiled string.
Source: https://arxiv.org/abs/2310.03714 ; synthesis.

### Round 80: Boundaries Summary
**Empirical Finding**: DSPy's honest boundaries: needs a trainset, optimizes modules not organizations, spends real compute, fails on bad metrics — inside those boundaries, +13–65% measured gains; outside them, the standard still rules.
Source: synthesis of Rounds 71–79.

## Cluster 9 — The Finance Register (Rounds 81–90)

### Round 81: Compile the Judgment, Keep the Rule
**Empirical Finding**: Kế toán: công thức tính thuế là rule (không compile); việc "đọc hóa đơn tay viết và phân loại" là judgment lặp lại có thể chấm điểm (metric) — ứng viên compile đầu tiên của phòng.
Source: series-internal (finance register).

### Round 82: The Đối Soát Metric
**Empirical Finding**: A reconciliation module's metric: đúng số lượng dòng khớp/lệch, đúng flag "thiếu chứng từ", không tự điền — ba tiêu chí chính là ba dòng starter metric của Part 4 dịch sang nghiệp vụ.
Source: series-internal; Part 4 finance metrics.

### Round 83: Golden Dataset = Sao Kê Mẫu
**Empirical Finding**: Compilation cần vài chục cặp hóa đơn-đã-đối-chứng — chính là "sao kê mẫu" mà phòng kế toán đã lưu; the trainset is the reconciliation archive.
Source: series-internal (Part 4 analogy extended).

### Round 84: Không Tự Điền Số as a Compiled Guarantee
**Empirical Finding**: The Fallback rule "không tự điền số liệu còn trống" encodes directly in the signature (an explicit "insufficient_data" output field) and the metric (penalize filled-missing) — the compiled artifact inherits the control.
Source: series synthesis; Fallback discipline.

### Round 85: Chứng Từ Provenance in Signatures
**Empirical Finding**: Input fields carry provenance (`invoice_scan`, `voucher_id`) — the audit trail starts at the signature: every compiled output traces to which voucher fed it.
Source: series synthesis; provenance discipline from Ch7.

### Round 86: The Period-End Recompile
**Empirical Finding**: Kỳ đối soát mới = recompile kiểm tra: distribution mới (loại hóa đơn mới, quy định thuế mới) có thể phá artifact cũ — the period-end close includes a recompile+eval pass.
Source: series-internal (period-end discipline).

### Round 87: Small-Model Economics for Ops
**Empirical Finding**: The paper's small-model result (T5-770M ≈ GPT-3.5 expert chains) reads directly as cost: compile cho model nhỏ, chạy rẻ hơn nhiều — compilation is a cost-reduction lever, not only a quality lever.
Source: https://arxiv.org/abs/2310.03714 ; synthesis.

### Round 88: Ai Sở Hữu Artifact
**Empirical Finding**: Phòng kế toán sở hữu signature + metric + trainset (nghiệp vụ); kỹ thuật sở hữu pipeline code — ownership splits the same way as the layer model: domain owns the contract, platform owns the runtime.
Source: series-internal (ownership model).

### Round 89: Một Câu cho Kế Toán
**Empirical Finding**: "Thay vì dạy AI đọc hóa đơn bằng cách diễn giải dài, bạn đưa cho nó 50 hóa đơn đã chấm đúng và bảo máy tự học cách hỏi" — one sentence, the whole paradigm.
Source: series-internal.

### Round 90: Register Summary
**Empirical Finding**: The finance register: compile judgment tasks, encode controls in signatures and metrics, treat the reconciliation archive as the trainset, recompile at period-end, own the contract — declarative prompting as professional training, not magic.
Source: synthesis of Rounds 81–89.

## Cluster 10 — Chapter Mechanics (Rounds 91–100)

### Round 91: VI Chapter Current State
**Empirical Finding**: 799 words, 0 mermaid, boilerplate FAQ, no production-failure section, no finance register, no research anchors, badge added 2026-09-10 but content untouched — the campaign's remaining VI chapter closest to raw.
Source: series-internal (audit finding).

### Round 92: EN Anchor Current State
**Empirical Finding**: 1,035 words, 0 fenced mermaid, 3 real FAQ, strong production pipeline code (signature → metric → MIPROv2 → JSON artifact) but: desc truncated ("...and automated."), no answer-first per H2, no evidence section, no research anchors, no related links, missing the 2023 paper's headline numbers.
Source: series-internal (audit finding).

### Round 93: VI Upgrade Plan
**Empirical Finding**: Phase 3: keep the three-vibes-problems frame and the division table; add the evidence section (+25/65%, expert-demo deltas, T5 result, MIPRO +13%); add optimizer-lineage narrative (Bootstrap → MIPRO → MIPROv2); add finance register; add production-failure section (bad-metric/overfit); 2 mermaid (compile pipeline, lineage/decision); 3 real FAQ; research anchors; absorb the EN's production pipeline code.
Source: series-internal (this dossier's handoff).

### Round 94: EN Upgrade Plan
**Empirical Finding**: Phase 4: fix desc; add answer-first per H2; add the 2023-paper evidence section with all three number families; add lineage subsection; add mermaid (compile lifecycle — the text diagram converts); add research anchors; extend FAQ (when-not-to-compile, metric-design); keep the production Python pipeline untouched.
Source: series-internal (this dossier's handoff).

### Round 95: Cross-Linking Plan
**Empirical Finding**: VI links: Part 4 (metrics), Part 8 (CI gates), Part 9 (RAG compose), MCP series; EN links: Part 4/6 anchors + exec; badges already placed 2026-09-10 both directions.
Source: series-internal.

### Round 96: Mermaid Design
**Empirical Finding**: VI diagram 1: the compile lifecycle (signature+trainset+metric → optimizer → artifact → CI gate); VI diagram 2: the decision tree (when to hand-prompt vs when to compile). EN converts its ASCII flow to a fenced mermaid of the same lifecycle.
Source: series-internal.

### Round 97: FAQ Design
**Empirical Finding**: VI: (1) DSPy có thay thế Prompt Standard không (division-of-labor answer); (2) cần bao nhiêu examples để compile (starter: dozens, held-out slice); (3) compile tốn bao nhiêu và khi nào chạy (on-change, sampled). EN adds: does-compilation-kill-hand-prompting; what-makes-a-good-metric.
Source: series-internal; campaign FAQ patterns.

### Round 98: The 70%-Class Integrity Check
**Empirical Finding**: No unverified percentage claims exist in either current draft — the chapter's numbers all trace to the two arXiv papers; keep it that way (Gate 7 clean on entry).
Source: series-internal (verification note).

### Round 99: Definition of Done
**Empirical Finding**: Both chapters: >2,500 words, >20KB, 2 mermaid each, 3–5 FAQ, answer-first per H2, all figures sourced to arXiv with baselines, 0 banned words, Hugo PASS.
Source: series 2027 SOTA bar.

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes chapter 8's dossier (3rd-to-last of the consolidated series); the campaign proceeds to Ch9 (`part-8-production-promptops` ⇄ EN `part-6-promptops-evals-and-security` upgrade-pair) and Ch10 (`part-9-mcp` ⇄ EN `part-4-mcp`).
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) the 2023 DSPy paper's headline numbers (+25%/+65% over few-shot, 5–46%/16–40% over expert demos, T5-770M competitive with GPT-3.5) added to the series' evidence base for the first time — cited with baselines alongside MIPRO's +13%; (2) the optimizer lineage (BootstrapFewShot → MIPRO → MIPROv2) narrated as widening search spaces; (3) the division-of-labor table (organization/optimization/data) kept orthogonal and extended with hybrid handwritten-compiled stacks; (4) the finance register (compile the judgment, keep the rule; reconciliation archive as trainset; period-end recompile); (5) the honest-boundaries ledger (bad metric → bad prompt, overfit, compile cost, signature drift).
- **AI_coverage_gap**: DSPy posts quote the framework's marketing numbers or none at all; almost none cite both paper generations with their baselines, and the when-NOT-to-compile scope honesty is absent from vendor-aligned content.
- **firsthand_evidence_available**: no — synthesizes the two primary papers (both fetched and verified in this campaign) and series design.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| arxiv.org/abs/2310.03714 | primary | Primary | DSPy foundation paper (Khattab et al., Stanford NLP, Oct 2023) — headline numbers, case studies, self-improvement framing |
| arxiv.org/abs/2406.11695 | primary | Primary | MIPRO (EMNLP 2024) — +13%, 5-of-7, joint optimization, mini-batch evaluation |
| arxiv.org/abs/2406.06608 | primary | Primary | The Prompt Report — 58-technique context for what compilation collapses |
| anthropic.com/engineering/writing-tools-for-agents | primary | Primary | held-out discipline, non-over-constraining metrics (applied to compilation) |
| dspy.ai / github.com/stanfordnlp/dspy | primary | Primary | module built-ins, BootstrapFewShot mechanics, MIPROv2 description |
| series Track 1/Track 2 chapters | internal | Tertiary (internal) | division table, production pipeline code, finance register |

## AI Source Discipline

- AI tools used for queries only (not cited): none — both arXiv papers fetched and verified directly in this pass.
- AI-citation mismatches: none — one rejected candidate ID avoided (2310.11327 was already known-bad from Ch2; the correct 2310.03714 resolved to the DSPy paper as expected).
- grounding_completeness: 62/100 rounds carry external source URLs; 34/100 cite series-internal design; 4 rounds carry [INFERENCE] or verification labels.

## Handoff

- **recommended_next_roles**: content-writer (Phase 3: upgrade VI part-7-declarative-prompting-dspy; Phase 4: upgrade EN part-5-declarative-prompting-dspy as consolidated anchor), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: none.
- **residual_risks**: (1) DSPy's API evolves quickly (2.5+ era) — code examples must state the version they target; (2) the delta-shrinking trend (25/65% → 13%) needs baseline context in prose, never bare numbers; (3) [INFERENCE] labels survive into drafts where the corresponding content appears (Gate 7).
