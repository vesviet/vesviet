# Prompt Standard — Versioning & Evals: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapters**: `prompt-standard/part-4-versioning-and-evals` (learn, Track 1) + EN consolidated anchor (upgrade of existing Track 2 `part-6-promptops-evals-and-security` eval sections, with cross-link)
> **Campaign**: `series-sync-upgrade` — Chapter 5 of 15

---

## Executive Research Summary

This dossier grounds prompt versioning and evaluation — the discipline that turns prompts from folklore into measured assets. The evidence base: Anthropic's tool-evaluation engineering guidance (eval tasks grounded in real-world uses, verifiers that avoid over-constraining, metrics beyond accuracy: runtime, tool-call counts, token consumption, errors), the held-out-test-set discipline (internal Slack/Asana tools optimized by Claude Code gained beyond expert-written implementations), OWASP LLM09 (overreliance as the unaudited-output risk), and Chroma's LLM-as-a-Judge methodology (GPT-4.1 judge aligned >99% with human judgment in their benchmark methodology). The convergence: "looks better" is not a signal; pass-rate on a golden dataset is. Versioning makes regressions bisectable; evals make improvements provable; the two together are the minimum viable PromptOps.

---

## Cluster 1 — From Vibes to Signals (Rounds 1–10)

### Round 1: The Vibes Problem
**Empirical Finding**: Series observation: teams judge prompts by "bản này có vẻ hay hơn," "mình thấy trả lời mượt hơn," "lần này agent có vẻ thông minh hơn" — none of these repeat, none transfer between people, none survive a model update.
Source: series-internal (Track 1 Part 4 opening).

### Round 2: Prompt Improvement Must Be Operationalized
**Empirical Finding**: "Prompt tốt hơn" must decompose into checkable deltas: bớt sai hơn, đúng format hơn, ít vượt scope hơn, ít cần sửa tay hơn — each phrasing names a measurable rate.
Source: series-internal (Track 1 Part 4 definitions).

### Round 3: The Finance Translation of Better
**Empirical Finding**: For accounting contexts: ít lệch số hơn, ít bỏ sót cột bắt buộc hơn, ít kết luận khi chưa đủ chứng từ hơn, ít phải sửa tay báo cáo hơn — the same four deltas, one register shift.
Source: series-internal (Track 1 Part 4 analogy).

### Round 4: Anthropic's Eval-Driven Discipline
**Empirical Finding**: "Building an evaluation allows you to systematically measure the performance of your tools... You can use Claude Code to automatically optimize your tools against this evaluation" — the loop (prototype → eval → analyze → refine) is the vendor's own engineering method, applied identically to prompts.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 5: Eval Tasks Must Be Real-World-Grounded
**Empirical Finding**: "Start by generating lots of evaluation tasks, grounded in real world uses... avoid overly simplistic 'sandbox' environments that don't stress-test your tools with sufficient complexity. Strong evaluation tasks might require multiple tool calls—potentially dozens."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 6: Strong vs Weak Eval Tasks
**Empirical Finding**: Documented contrast — strong: "Customer ID 9182 reported triple charge... find all relevant log entries and determine if other customers were affected"; weak: "Search the payment logs for purchase_complete and customer_id=9182" — the strong task requires reasoning across data, the weak one a single lookup.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 7: Verifiers Must Not Over-Constrain
**Empirical Finding**: "Avoid overly strict verifiers that reject correct responses due to spurious differences like formatting, punctuation, or valid alternative phrasings" — a verifier that demands byte-identical prose fails valid answers; verify the contract, not the wording.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 8: LLM-as-a-Judge With Rubrics
**Empirical Finding**: Chroma's benchmark methodology used an aligned GPT-4.1 judge with >99% alignment to human judgment for grading model outputs — judge-based scoring at rubric level is production-viable.
Source: https://research.trychroma.com/context-rot (judge methodology).
[INFERENCE] Judge alignment figures come from Chroma's benchmark setup; a team's judge needs its own calibration sample.

### Round 9: Overreliance Is the Risk Being Managed
**Empirical Finding**: OWASP LLM09: "failing to critically assess LLM outputs can lead to compromised decision making, security vulnerabilities, and legal liabilities" — evals are the systematic form of critical assessment; skipping evals institutionalizes overreliance.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 10: The Two Halves
**Empirical Finding**: Versioning without evals = you know what changed but not whether it hurt; evals without versioning = you know it hurt but cannot find the cause — the pair is the minimum viable PromptOps unit.
Source: series-internal (Track 1 Part 4 thesis).

## Cluster 2 — Versioning Discipline (Rounds 11–20)

### Round 11: Prompt-as-Code Properties
**Empirical Finding**: A prompt influencing answers, generated code, or agent behavior "không còn là mẹo cá nhân nữa" — it needs version, change history, owner, evaluation criteria: the four asset properties from Part 1.
Source: series-internal (Track 1 Part 4).

### Round 12: Repo + Pull Request + Rationale
**Empirical Finding**: The minimal versioning recipe: store prompts in the repo, every change through a PR, state the reason, attach before/after examples when possible — "tốt hơn phần lớn các nhóm đang prompt theo trí nhớ."
Source: series-internal (Track 1 Part 4).

### Round 13: The Changelog Format
**Empirical Finding**: Reference changelog entry: "v1.2 — làm rõ fallback khi thiếu dữ liệu / yêu cầu findings có file reference / giảm lan man bằng length constraint" — semantic, per-change, human-reviewable.
Source: series-internal (Track 1 Part 4 changelog example).

### Round 14: Bisectable Regressions
**Empirical Finding**: With Git history on prompt files, a quality drop bisects like code: diff the prompt change log against the eval timeline, find the offending commit — the mechanism that makes "rollback" a real operation on prompts.
Source: series Track 2 Part 6; software engineering practice.

### Round 15: Block-Level Diffs Are the Review Unit
**Empirical Finding**: An 8-block (or layered) prompt diffs at block granularity — "changed Constraints, kept Workflow" — review evaluates the delta, not the whole artifact, keeping review scalable as prompts grow.
Source: series-internal (Track 1 Parts 1–2).

### Round 16: Version Pinning Prevents Silent Drift
**Empirical Finding**: Version-pinned prompts (like version-pinned dependencies) make "which prompt version produced this output" answerable per output — the audit-trail precondition.
Source: series-internal; software supply-chain practice.

### Round 17: Git as State Backbone
**Empirical Finding**: "Use git for state tracking: Git provides a log of what's been done and checkpoints that can be restored. Claude's latest models perform especially well in using git to track state across multiple sessions."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 18: Snapshot Tests for Prompts
**Empirical Finding**: Golden-dataset runs on every prompt change are the prompt analogue of snapshot tests: any behavior delta must be intentional and visible in the eval report before merge.
Source: series Track 2 Part 6; testing practice.

### Round 19: Tags for Known-Good
**Empirical Finding**: Tag prompt versions ("v1.3-known-good") at high pass-rates; production incidents roll back to the tag, not to memory — the deploy/rollback loop for prompts.
Source: series-internal; release-management practice.

### Round 20: Ownership in the File Header
**Empirical Finding**: Each prompt file declares owner in frontmatter — "3 giờ sáng ai sửa?" is answered by the file, not by Slack archaeology.
Source: series-internal (Track 1 Part 1 asset model).

## Cluster 3 — The Golden Dataset (Rounds 21–30)

### Round 21: Eval Defined
**Empirical Finding**: Series definition: an eval is "một tập bài kiểm tra nhỏ để xem prompt có đạt mục tiêu không" — small, targeted, owned by the same team as the prompt.
Source: series-internal (Track 1 Part 4).

### Round 22: The Five-Case Review Eval
**Empirical Finding**: Reference review-agent eval: (1) diff có bug null pointer, (2) regression performance, (3) chỉ thay đổi format, (4) thiếu context, (5) thay đổi bảo mật — five cases, five distinct failure probes.
Source: series-internal (Track 1 Part 4 eval example).

### Round 23: Expectations Are Behavioral, Not Literal
**Empirical Finding**: "Kỳ vọng không phải là output giống hệt nhau từng chữ" — the contract checked is: phát hiện đúng lỗi chính? giữ đúng format? không bịa khi thiếu context?
Source: series-internal (Track 1 Part 4).

### Round 24: Boundary Cases Belong in the Set
**Empirical Finding**: Golden datasets carry input/output pairs plus boundary cases — the series standard from the exec summary; boundary behavior is where silent failures hide.
Source: series-internal (Track 2 Part 6; exec summary Round 71).

### Round 25: Grounded in Real Tasks
**Empirical Finding**: Anthropic's method: eval prompts "inspired by real-world uses and based on realistic data sources and services (for example, internal knowledge bases and microservices)" — synthetic toy tasks prove nothing about production behavior.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 26: Generating Eval Tasks With Agents
**Empirical Finding**: "With your early prototype, Claude Code can quickly explore your tools and create dozens of prompt and response pairs" — eval-set construction itself is agent-accelerated; the human curates.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 27: Multiple Valid Paths
**Empirical Finding**: "There might be multiple valid paths to solving tasks correctly, try to avoid overspecifying or overfitting to strategies" — checking expected tool calls is optional instrumentation, not the pass condition.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 28: Held-Out Sets Prevent Overfitting
**Empirical Finding**: "We relied on held-out test sets to ensure we did not overfit to our 'training' evaluations. These test sets revealed that we could extract additional performance improvements even beyond what we achieved with 'expert' tool implementations."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 29: Dataset Size Starter
**Empirical Finding**: The series' starter guidance: a few dozen canonical pairs for the top 3 recurring tasks — small enough to maintain, large enough to catch format breaks.
Source: series-internal (Track 1 Part 5 starter kit).

### Round 30: Dataset Decay
**Empirical Finding**: Golden datasets rot: business rules change, edge cases emerge, models shift — schedule dataset review with each prompt version bump; a stale dataset fails good prompts.
Source: series-internal; eval practice.

## Cluster 4 — Metrics That Matter (Rounds 31–40)

### Round 31: The Starter Metric Set
**Empirical Finding**: Series starter metrics: tỷ lệ output đúng format, tỷ lệ phát hiện đúng lỗi quan trọng, tỷ lệ cần user sửa lại, tỷ lệ vượt scope, tỷ lệ nói rõ khi không chắc — five rates, all countable from ordinary runs.
Source: series-internal (Track 1 Part 4).

### Round 32: The Finance Metric Extensions
**Empirical Finding**: For data/accounting work: tỷ lệ giữ đúng cấu trúc bảng, tỷ lệ đánh dấu đúng dòng "thiếu căn cứ", tỷ lệ không tự điền số liệu trống — domain-faithful variants of the same rates.
Source: series-internal (Track 1 Part 4).

### Round 33: Beyond Accuracy
**Empirical Finding**: Anthropic: "As well as top-level accuracy, we recommend collecting other metrics like the total runtime of individual tool calls and tasks, the total number of tool calls, the total token consumption, and tool errors."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 34: Token Consumption Is a Prompt Quality Metric
**Empirical Finding**: Token counts per task reveal prompt bloat and verbosity drift — a prompt whose outputs balloon after an edit failed a cost gate even when accuracy held.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents ; cache usage fields (cache_read/creation/input_tokens) extend this to prefix economics.
[INFERENCE] Cost-gate thresholds are team-set; the metric's existence is the vendor-documented part.

### Round 35: Redundant Calls Reveal Design Flaws
**Empirical Finding**: "Lots of redundant tool calls might suggest some rightsizing of pagination or token limit parameters is warranted; lots of tool errors for invalid parameters might suggest tools could use clearer descriptions."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 36: Read the Transcripts, Not Just Scores
**Empirical Finding**: "Observe where your agents get stumped or confused. Read through your evaluation agents' reasoning and feedback (or CoT)... What agents omit in their feedback and responses can often be more important than what they include."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 37: Pass-Rate Thresholds
**Empirical Finding**: The series standard: pass rate >95% before production merge, borderline candidates to human review — the gate that converts evals from dashboards into controls.
Source: series Track 2 Part 6 (series standard).

### Round 38: Confidence Tiers Make Outputs Gated
**Empirical Finding**: Requiring confidence tiers in output lets evals measure "tỷ lệ nói rõ khi không chắc" mechanically and lets downstream systems route low-confidence outputs to human review.
Source: series-internal (Track 1 Part 2 Fallback rules).

### Round 39: Metrics on Real Distributions
**Empirical Finding**: Production metrics must sample real task distributions, not synthetic favorites — sampling bias in the metric set silently redirects prompt optimization toward the sample.
Source: synthesis of Anthropic eval guidance; eval practice.
[INFERENCE] Distribution drift between eval sample and production traffic is a standing risk needing periodic re-sampling.

### Round 40: The Metric Minimum
**Empirical Finding**: Honest floor: one format-compliance rate and one correctness rate on a few dozen real tasks already beats every vibe-based process — metric sophistication grows with stakes.
Source: series-internal (Track 1 Part 4 "không cần hệ thống đo quá phức tạp").

## Cluster 5 — Change One Thing at a Time (Rounds 41–50)

### Round 41: The Isolation Rule
**Empirical Finding**: Series rule: "Khi sửa prompt, đừng đổi 5 chỗ cùng lúc. Hãy đổi từng phần nhỏ... Sau đó test lại. Làm vậy bạn mới biết thay đổi nào thực sự có ích."
Source: series-internal (Track 1 Part 4).

### Round 42: Block-Level Change Discipline
**Empirical Finding**: The 8-block structure operationalizes isolation: one change = one block edit — "thêm output contract / sửa fallback behavior / rút gọn scope" as separate, separately-evaluated diffs.
Source: series-internal (Track 1 Part 4 examples).

### Round 43: Attribution Failure Without Isolation
**Empirical Finding**: When five simultaneous edits ship and quality drops 8%, no one can say which edit caused it — the change is unattributable, the fix is guesswork; isolation makes causality cheap.
Source: series-internal.

### Round 44: A/B as the Two-Version Eval
**Empirical Finding**: Two prompt versions differ by one block each; both run the golden dataset; the delta is the edit's measured effect — the minimal A/B unit is one block, not one prompt.
Source: series Track 2 Part 6; experiment design practice.

### Round 45: Model Updates Are Confounders
**Empirical Finding**: Provider model updates change behavior under a fixed prompt — pin model versions in eval runs, or attribute regressions to the right layer (prompt vs model) before reacting.
Source: series-internal; vendor model-version practice.

### Round 46: Eval Cost Discipline
**Empirical Finding**: LLM-as-a-Judge runs cost tokens; the series budget rule: evals fire on prompt change (not continuously), on a sample (not the full suite) — "cadence discipline keeps eval spend proportionate."
Source: series Track 2 Part 6; exec summary Round 76.

### Round 47: Parallel Call Instrumentation
**Empirical Finding**: Tool-call counts and parallelism in eval transcripts reveal whether the agent pursues efficient strategies — "track common workflows agents pursue and offer opportunities to consolidate."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 48: The Interleaved-Thinking Probe
**Empirical Finding**: "Instructing agents to output reasoning and feedback blocks before tool call and response blocks may increase LLMs' effective intelligence by triggering chain-of-thought behaviors" — eval harnesses can demand visible reasoning for diagnosis.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 49: Small Refinements, Dramatic Effects
**Empirical Finding**: "Even small refinements to tool descriptions can yield dramatic improvements" (SWE-bench Verified state-of-the-art after description refinements) — evals are how you notice which small refinement was the dramatic one.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 50: The Improvement Loop
**Empirical Finding**: The full loop: detect bad output → locate block → edit one block → review → eval → merge or revert — improvement as procedure, not personality.
Source: series-internal (Track 1 Part 4 synthesis).

## Cluster 6 — LLM-as-a-Judge in Practice (Rounds 51–60)

### Round 51: Judge Use Cases
**Empirical Finding**: Judge-based grading applies where outputs are long, comparative, or rubric-scored; exact-match and schema checks handle the deterministic layer beneath.
Source: synthesis; https://research.trychroma.com/context-rot (judge usage).

### Round 52: Rubric Design
**Empirical Finding**: Effective rubrics are quantitative (score per criterion), behavioral (name observable properties), and few (3–5 criteria) — mirroring Anthropic's strong-task guidance: enough complexity to discriminate, not so much as to become noise.
Source: synthesis of eval guidance; series Track 2 Part 6 rubric practice.

### Round 53: Judge Calibration
**Empirical Finding**: Calibrate the judge on a sample where humans scored first; measure agreement; only then promote judge scores to gate status — Chroma's >99% figure describes a calibrated setup, not a default.
Source: https://research.trychroma.com/context-rot.
[INFERENCE] Calibration sample size is team-dependent; the discipline, not the number, transfers.

### Round 54: Judge Drift
**Empirical Finding**: The judge is itself a model output subject to version drift — pin the judge model version and recalibrate on model changes, or gates silently loosen.
Source: synthesis; model-version practice.

### Round 55: Deterministic + Probabilistic Layering
**Empirical Finding**: Production gates layer both: schema/format assertions (deterministic, free) beneath judge rubric scores (probabilistic, priced) — "pure determinism misses quality, pure judgment misses regressions."
Source: series Track 2 Part 6.

### Round 56: Prompt-Injection Resistance of Judges
**Empirical Finding**: Judge prompts see untrusted content (the outputs being graded) — judges need the same Constraints/Fallback discipline as any production prompt; a compromised judge loosens every gate it grades.
Source: series Track 2 Part 6; OWASP LLM01 context.

### Round 57: Structured Judge Output
**Empirical Finding**: Judges output structured verdicts (score per criterion, pass/fail, rationale) — the judge's output contract is itself schema-enforced for aggregation.
Source: series Track 2 Part 6 practice.

### Round 58: Human Review Boundaries
**Empirical Finding**: Borderline scores route to humans; the series threshold practice: evals recommend, humans decide at the edge — automation replaces triage, not judgment at the boundary.
Source: series Track 2 Part 6; IRREVERSIBLE ACTION LOCK parallel.

### Round 59: Judge as Regression Baseline
**Empirical Finding**: Judge scores trend over versions — a slow rubric-score decline across three "improvements" is the regression no single diff caught; trends are the judge's best product.
Source: series-internal; metrics practice.

### Round 60: The Judge Costs What It Saves
**Empirical Finding**: The economics: a judge pass on a few hundred graded outputs is cheaper than one production incident caused by an unaudited prompt change — overreliance (LLM09) priced both ways.
Source: synthesis; OWASP LLM09 framing.

## Cluster 7 — Regression Management (Rounds 61–70)

### Round 61: The Regression Definition
**Empirical Finding**: A regression is a measurable delta on a defined metric after a specific change — without metrics there are no regressions, only anecdotes; the definition is the gift versioning+evals give.
Source: series-internal.

### Round 62: The Bisection Procedure
**Empirical Finding**: Procedure: metric drops → list prompt commits since last known-good → bisect commits against the golden dataset → offending edit found in O(log n) eval runs.
Source: series Track 2 Part 6; Git bisect practice.

### Roll 63: [Audit-note] Label typo ("Roll 63") — content stands as Round 63.

### Round 63: Known-Good Tags
**Empirical Finding**: Tagging known-good versions makes rollback a `git checkout` — the recovery path is a command, not a rewrite session.
Source: series-internal (Round 19 of this dossier).

### Round 64: Eval Timeline vs Change Timeline
**Empirical Finding**: Overlaying eval history on commit history turns "khi nào output bắt đầu xấu?" into a join query — the two logs are one system.
Source: series-internal.

### Round 65: The 2-Week Prompt and Silent Data Rot
**Empirical Finding**: The recurring incident: prompt unchanged for weeks, output drifts anyway — because embedded data went stale (schema moved, sources changed); evals on real data catch what code review cannot.
Source: series-internal (Track 1 Part 1 production failure).

### Round 66: Model-Swap Regressions
**Empirical Finding**: Model swaps regress prompt behavior: "prompts tuned for earlier models misbehave on newer ones" — the migration guidance exists per model; evals are the swap's safety net.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices (migration considerations).

### Round 67: Layer-Attributed Regressions
**Empirical Finding**: In layered stacks, regressions attribute to layers: prefix change → Role/Rules; procedure change → Workflow; domain change → Skill — attribution is a directory lookup.
Source: series-internal (layer blast radius).

### Round 68: Canary Rollouts for Prompts
**Empirical Finding**: High-stakes prompt changes ship canary-style: new version takes a sampled production slice first; golden-dataset parity plus canary metrics gate the full rollout.
Source: series Track 2 Part 6 practice; deployment practice.

### Round 69: Rollback Etiquette
**Empirical Finding**: Rollbacks ship as PRs too — with a postmortem note in the changelog ("v1.3 reverted: Constraints edit broke tool allowlist") — the history teaches the team.
Source: series-internal.

### Round 70: The Regression Ledger
**Empirical Finding**: Teams that log regressions (symptom → block → fix → eval proof) accumulate a pattern library that makes the next diagnosis faster — compounding institutional memory.
Source: series-internal.

## Cluster 8 — Accounting-Grade Verification (Rounds 71–80)

### Round 71: The Reconciliation Parallel
**Empirical Finding**: Finance already runs golden datasets: sao kê mẫu (sample statements), báo cáo chuẩn (reference reports), ca biên (boundary cases like missing vouchers) — eval is "đối soát cho prompt."
Source: series-internal (Track 1 analogy).

### Round 72: Không Tự Điền Số Liệu = Fallback Eval
**Empirical Finding**: The accounting rule "không tự điền số liệu còn trống" is testable: feed the eval a case with missing data, assert the output flags instead of filling — Fallback behavior is eval-able, not aspirational.
Source: series-internal (Track 1 Part 4 metric extension).

### Round 73: Missing-Voucher Boundary Cases
**Empirical Finding**: Every finance eval set should carry the canonical boundary: partially missing documents, ambiguous periods, duplicate entries — the cases that separate a trustworthy assistant from a confident-fabricator.
Source: series-internal.

### Round 74: The Audit Trail Requirement
**Empirical Finding**: "Which prompt version produced this posting?" — version-pinned prompts answer per output; the audit trail is a byproduct of versioning, not extra work.
Source: series-internal (Track 1 Part 1; Part 4).

### Round 75: Sample Sizes Familiar to Finance
**Empirical Finding**: A few dozen cases is exactly the scale of a monthly reconciliation sample — finance teams already reason about sampling adequacy; the eval conversation needs no statistics lecture.
Source: series-internal.

### Round 76: Materiality Thresholds = Pass-Rate Gates
**Empirical Finding**: Finance's materiality concept maps to pass-rate thresholds: how much error is tolerable before escalation — the >95% gate is a materiality policy for prompts.
Source: series-internal; accounting practice.

### Round 77: Segregation of Duties in the Pipeline
**Empirical Finding**: Author, reviewer, and evaluator are three roles in code review; prompts need the same separation — the person who wrote the change is not the sole judge of its eval.
Source: series-internal; accounting control practice.

### Round 78: The Period-End Eval
**Empirical Finding**: Borrowing month-end close: schedule a recurring eval pass over top prompts (dataset freshness, threshold health, judge calibration) — the prompt estate gets its closing procedure.
Source: series-internal.

### Round 79: What Finance Would Ask
**Empirical Finding**: The four audit questions port directly: prompt nào đang chạy (inventory)? phiên bản nào (versioning)? đo bằng gì (metrics)? ai duyệt (ownership)? — the finance auditor's checklist is the PromptOps checklist.
Source: series-internal.

### Round 80: The Ops Pitch
**Empirical Finding**: The adoption line for non-engineers: "eval là đối soát cho AI — bạn đã làm điều này mỗi kỳ đóng sổ" — familiar work, new subject.
Source: series-internal.

## Cluster 9 — Tooling Landscape, Honestly (Rounds 81–90)

### Round 81: No Tools Needed to Start
**Empirical Finding**: The starter kit needs zero platforms: files in Git, a runner script, a results table — "không cần hệ thống đo quá phức tạp ngay từ đầu."
Source: series-internal (Track 1 Part 4).

### Round 82: The Agentic Loop Runner
**Empirical Finding**: Anthropic's recommended harness: "simple agentic loops (while-loops wrapping alternating LLM API and tool calls): one loop for each evaluation task" — a few dozen lines, no framework.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 83: Programmatic Over UI
**Empirical Finding**: "We recommend running your evaluation programmatically with direct LLM API calls" — repeatable, diffable, CI-integrable; UI-based evals do not scale to gates.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 84: Agent-Accelerated Analysis
**Empirical Finding**: "Simply concatenate the transcripts from your evaluation agents and paste them into Claude Code. Claude is an expert at analyzing transcripts and refactoring lots of tools all at once" — analysis is delegated; decisions stay human.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 85: What Platforms Add Later
**Empirical Finding**: Eval platforms add value at scale: dataset versioning, judge dashboards, trend alerts, team workflows — after the manual process exists, not before.
Source: series-internal (adoption sequencing).

### Round 86: The DIY Trap
**Empirical Finding**: The inverse trap: building a bespoke eval framework for months before the first gate runs — the runner script plus a table is the honest v1.
Source: series-internal.

### Round 87: CI Integration Shape
**Empirical Finding**: The gate shape in CI: prompt PR → run golden dataset (sampled) → pass-rate check → block merge below threshold — the mechanical form of "evals fire on change."
Source: series Track 2 Part 6.

### Round 88: OWASP-Aligned Gate Content
**Empirical Finding**: Gate suites align to OWASP categories: LLM01 injection probes, LLM02 output-schema validation, LLM09 overreliance spot-checks — security tests are evals with attack intent.
Source: series Track 2 Part 6; OWASP Top 10.

### Round 89: Eval Infrastructure Budget
**Empirical Finding**: Budget the pipeline itself: judge tokens, run time, dataset storage — the meta-metric "eval cost per prompt change" keeps the measurement system honest.
Source: synthesis; metrics practice.

### Round 90: When Manual Beats Platform
**Empirical Finding**: For <5 prompts and <50 cases, a spreadsheet of runs is faster than any platform — tooling follows demonstrated need, the recurring adoption rule.
Source: series-internal (Track 1 Part 5 principle).

## Cluster 10 — The Chapter's Deliverables (Rounds 91–100)

### Round 91: The Changelog Template
**Empirical Finding**: Deliverable 1: the changelog format (version, block touched, reason, before/after) — shipped in the article as a copyable template.
Source: series-internal (Track 1 Part 4).

### Round 92: The Five-Case Eval Recipe
**Empirical Finding**: Deliverable 2: the review-agent five-case eval, generalized: one happy path, one performance case, one format-only case, one missing-context case, one security case — the five failure probes.
Source: series-internal (Track 1 Part 4 eval example).

### Round 93: The Metric Starter Table
**Empirical Finding**: Deliverable 3: the five starter rates + finance extensions, in a copyable table — what to count from day one.
Source: series-internal (Track 1 Part 4).

### Round 94: The One-Change Rule Card
**Empirical Finding**: Deliverable 4: the isolation rule as a review-checklist line: "does this PR change exactly one block?" — the discipline made mechanical.
Source: series-internal (Track 1 Part 4).

### Round 95: The Rollback Recipe
**Empirical Finding**: Deliverable 5: the rollback procedure (tag known-good, checkout on regression, postmortem line in changelog) — recovery as routine.
Source: series-internal (this dossier Cluster 7).

### Round 96: The Pass-Rate Gate
**Empirical Finding**: Deliverable 6: the >95% gate statement with borderline-to-human routing — the control that turns all other deliverables into a system.
Source: series Track 2 Part 6 (series standard).

### Round 97: The Maturity Note
**Empirical Finding**: Position honestly: this chapter is manual PromptOps — the Phase 6 deep-dive automates it (CI gates, judge pipelines, OWASP suites); teams graduate when volume demands, not for prestige.
Source: series architecture (Track 1 → Track 2 bridge).

### Round 98: The Definition, Final Form
**Empirical Finding**: Published position: prompt trưởng thành khi nó "có thể đo, có thể review, và có thể cải tiến có kiểm soát" — measurable, reviewable, controlled-improvable: the chapter's three verbs.
Source: series-internal (Track 1 Part 4 closing).

### Round 99: The Next-Chapter Bridge
**Empirical Finding**: Next: the team template kit — everything from chapters 1–4 assembled into the minimum deployable standard for a whole team.
Source: series architecture (Track 1 Part 5 bridge).

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes chapters 4–5's dossiers (parallel pass per the series-sync-upgrade workflow); the campaign continues with chapter 6 (part-5-team-template) next.
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) the eval methodology transplanted whole from Anthropic's tool-evaluation engineering guidance — real-world-grounded tasks, non-over-constraining verifiers, metrics beyond accuracy (runtime, tool calls, tokens, errors), held-out sets, agent-accelerated analysis — rarely connected to prompt evals in typical guides; (2) LLM-as-a-Judge with calibration discipline (Chroma's >99% aligned GPT-4.1 judge as the calibration existence proof, not a default); (3) the isolation rule (one block per change) as the causality-preserving discipline that makes A/B meaningful at block granularity; (4) the finance register: reconciliation as eval, materiality as pass-rate gate, period-end close as the recurring audit — the non-engineer bridge extended to measurement; (5) pass-rate >95% + borderline-to-human as the gate that converts dashboards into controls.
- **AI_coverage_gap**: Prompt-eval guides either stop at "write good tests" or pitch platforms; the changelog/rollback/bisect mechanics (versioning as regression forensics), judge-calibration discipline, and the honest no-tools starter kit are nearly absent from mainstream coverage.
- **firsthand_evidence_available**: no — synthesizes published primary sources and series design.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| anthropic.com/engineering/writing-tools-for-agents | primary | Primary | eval methodology: grounded tasks, verifiers, metrics, held-out sets, agentic runner, transcript analysis |
| platform.claude.com/docs (prompting best practices) | primary | Primary | git state tracking, migration regressions, self-check |
| research.trychroma.com/context-rot | primary | Primary | LLM-as-a-Judge calibration (>99% aligned GPT-4.1 in methodology) |
| owasp.org Top 10 for LLM Applications | primary | Primary | LLM09 overreliance; LLM01/LLM02 gate alignment |
| series Track 1/Track 2 chapters | internal | Tertiary (internal) | changelog format, eval recipes, metrics, thresholds |

## AI Source Discipline

- AI tools used for queries only (not cited): none — all rounds trace to fetched primary documents or series-internal design.
- AI-citation mismatches: none.
- grounding_completeness: 24/100 rounds carry external source URLs (Anthropic eval guidance, prompting docs, Chroma judge methodology, OWASP); 72/100 cite series-internal methodology traceable to series corpus files (this chapter codifies the series' own PromptOps practice — series-internal is the primary source class by design); 4 rounds carry [INFERENCE] labels (Rounds 8, 34, 39, 53).

## Handoff

- **recommended_next_roles**: content-writer (Phase 3: upgrade VI part-4-versioning-and-evals; Phase 4: upgrade EN consolidated anchor — the eval sections of `part-6-promptops-evals-and-security`, with a cross-link from this chapter), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: none — consolidation follows precedent: Track 1 part-4 links to the Track 2 part-6 EN as its English destination for the evals/security overlap; the versioning/changelog material is new information gain on the EN side.
- **residual_risks**: (1) the >99% judge-alignment figure describes Chroma's benchmark setup — present as calibration evidence, not a portable number; (2) pass-rate >95% is the series' published standard, not a vendor number — label as such; (3) [INFERENCE]-labeled rounds keep labels downstream (Gate 7).
