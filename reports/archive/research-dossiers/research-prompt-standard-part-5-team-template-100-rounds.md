# Prompt Standard — The Minimum Team Kit: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapters**: `prompt-standard/part-5-team-template` (learn, Track 1) + NEW EN twin `part-5-team-starter-kit` (vesviet — no consolidated candidate exists; authored fresh per executive-summary precedent)
> **Campaign**: `series-sync-upgrade` — Chapter 6 of 15

---

## Executive Research Summary

This dossier grounds the team starter kit — the minimum deployable Prompt Standard. The evidence converges on three findings. First, the five-part kit (roles/, rules/, workflows/, skills/, evals/) is not arbitrary: it is the layer model of Part 3 collapsed into a directory tree, with evals/ added because Part 4 proved measurement is half the system. Second, the kit has production precedent at scale: the agent-skills pack runs 108 skills, 34 roles, 24 workflows under exactly this shape (roles as files with identity/responsibilities/boundaries, rules centralized, workflows stepwise, skills trigger-gated) — the structure survives 5x growth without restructuring. Third, the adoption sequence is pain-triggered: one repeated use case first, template second, eval-then-fix over 1–2 weeks — and the honest anti-doctrine ("đừng chuẩn hóa tất cả ngay ngày đầu") is the difference between adoption and shelfware. Role-specific entry templates (developer, reviewer, accounting, CS) are the non-engineer bridge: one standard, five doors.

---

## Cluster 1 — Why a Starter Kit Exists (Rounds 1–10)

### Round 1: The Delay Trap
**Empirical Finding**: Series observation: teams delay standardization believing they must build a large system first — the actual requirement is a five-directory minimum kit deployable in an afternoon.
Source: series-internal (Track 1 Part 5 opening).

### Round 2: The Five Parts Map the Layer Model
**Empirical Finding**: `roles/` = L1 (identity), `rules/` = L2 (invariants), `workflows/` = L3 (procedures), `skills/` = L4 (domain depth), `evals/` = the Part 4 measurement half — the kit is the series' architecture collapsed into a file tree.
Source: series-internal (Track 1 Part 5; layer mapping from part-3 dossier).

### Round 3: Production Precedent at 5x Scale
**Empirical Finding**: The agent-skills pack runs 108 skills, 34 roles, 24 workflows in this exact shape — centralized rules propagate to all roles without per-file edits; the starter structure survives growth without restructure.
Source: agent-skills pack structure (validate-all gates: 16/16 PASS at this scale).

### Round 4: The 30–60 Minute Timebox
**Empirical Finding**: The kit's setup cost from the series' cost-honesty framing: 30–60 minutes to structure one task's prompt plus a one-page conventions note — the starter kit's five directories are the afternoon version.
Source: series-internal (Track 1 Part 1 cost FAQ).

### Round 5: Starter Kit vs Full Stack Boundary
**Empirical Finding**: The kit deliberately excludes: layer compilers, MCP gateways, DSPy pipelines, CI/CD gates — "tooling follows demonstrated need"; the kit is the demonstrated-need detector.
Source: series-internal (Track 1 Part 5; adoption sequencing).

### Round 6: The Five Metrics Kit
**Empirical Finding**: Adoption metrics from the series: prompt reuse rate, output pass rate, incident count from format breaks, onboarding time — four numbers the kit makes countable from week one.
Source: series-internal (Track 2 Part 6 metrics; exec summary Round 94).

### Round 7: Common First-Week Failures
**Empirical Finding**: Observed first-week failure modes: standardizing everything at once (shelfware), writing templates no task matches (aspirational fiction), skipping evals/ (unmeasurable from day one), no owner per file (folklore by week two).
Source: series-internal (Track 1 Part 5 pitfalls).

### Round 8: The Takeover Test Applies to the Kit
**Empirical Finding**: The two-week takeover test extends to the kit itself: a new member should locate the right template, rules, and eval from the tree alone — directory naming is the onboarding UX.
Source: series-internal (Track 1 Part 1 takeover test).

### Round 9: The Conventions One-Pager
**Empirical Finding**: Alongside the tree, the kit ships one page of conventions: file naming (lowercase-hyphen), owner-in-frontmatter, review rule (who signs off which file), version note — four lines that prevent drift.
Source: series-internal (Track 1 Part 5).

### Round 10: Definition of Kit Success
**Empirical Finding**: Kit success is behavioral: two colleagues independently produce compatible prompts from the same template, and the third member onboards from the tree alone — both observable within a sprint.
Source: series-internal.

## Cluster 2 — Roles/ Directory (Rounds 11–20)

### Round 11: Role File Anatomy
**Empirical Finding**: Each role file carries: identity (who), responsibilities (what), decision boundaries (authority), communication style (how) — the four fields Track 1 Part 3 defined.
Source: series-internal (Track 1 Part 3 layer 1).

### Round 12: The Golden Rule as Role Test
**Empirical Finding**: Anthropic's golden rule — "Show your prompt to a colleague with minimal context... If they'd be confused, Claude will be too" — is the acceptance test for each role file.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 13: One Role, One Lens
**Empirical Finding**: The role fix: "Bạn là Senior Backend Engineer" vs "QA Reviewer" vs "Technical Writer" — same input, different prioritization; the kit's roles/ encodes the lenses the team actually uses.
Source: series-internal (Track 1 Part 2 role examples).

### Round 14: Role Length Discipline
**Empirical Finding**: Anthropic: "Even a single sentence makes a difference" for role focus — role files stay short (1–3 sentences of identity); essays waste attention budget.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 15: Reviewer Role Starter
**Empirical Finding**: The kit's reviewer.md: prioritizes bugs/regressions/production risk; findings-first format; severity + file references; assumptions stated when uncertain — the Part 2 minimal prompt, file-permanized.
Source: series-internal (Track 1 Part 2 minimal template).

### Round 16: Writer Role Starter
**Empirical Finding**: The kit's writer.md: audience-first, structure per repo docs conventions, tone pinned by the target doc type — one role file per recurring persona the team needs.
Source: series-internal (Track 1 Part 5 tree).

### Round 17: Developer Role Starter
**Empirical Finding**: The kit's developer.md: correctness/safety/maintainability priority order, local validation authority, no breaking changes without confirmation — the engineering template from Part 5's example.
Source: series-internal (Track 1 Part 5 template).

### Round 18: Role Reuse Across Repos
**Empirical Finding**: One reviewer role serves many repos — the reuse payoff: marginal cost of the Nth repo is zero role-file edits.
Source: series-internal (Track 1 Part 3 reuse).

### Round 19: Persona Drift Detection
**Empirical Finding**: When output voice drifts, roles/ is the first diagnostic stop — the blast-radius table from Part 3 operationalized for the kit.
Source: series-internal (layer drift table).

### Round 20: Roles Are the Kit's Cheap Win
**Empirical Finding**: Roles files are the fastest kit win: 10 minutes of writing changes every downstream prompt that includes them — highest leverage per token of any kit file.
Source: series-internal synthesis.

## Cluster 3 — Rules/ Directory (Rounds 21–30)

### Round 21: Rules File Anatomy
**Empirical Finding**: Each rules file: clear prohibitions, safety principles, internal invariants — short, clear, rarely changing; security-owned.
Source: series-internal (Track 1 Part 3 layer 2).

### Round 22: Safety Rules Starter Set
**Empirical Finding**: The kit's safety.md: no editing generated files by hand, no destructive commands, no fabricated test results, no secret exposure — four prohibitions covering the four commonest agent accidents.
Source: series-internal (Track 1 Part 5 rules examples).

### Round 23: Coding Standards as Rules
**Empirical Finding**: The kit's coding-standards.md carries team conventions (style, architecture rules) — the "invariant" class that changes quarterly, not daily; separate file from safety for change-frequency separation.
Source: series-internal.

### Round 24: Reversibility Enumeration
**Empirical Finding**: Scope rules import Anthropic's action classes: destructive (delete files/branches, drop tables), hard-to-reverse (force push, reset --hard, amend published), visible-to-others (push, comment, message) — each requires confirmation.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 25: Rules Propagate Without Copy-Paste
**Empirical Finding**: The pack's evidence: centralized rules reach all 34 roles without per-file edits — the kit's rules/ gives the same one-edit propagation at team scale.
Source: agent-skills pack structure.

### Round 26: The Accounting Rules Translation
**Empirical Finding**: Finance rules register: "không bỏ qua chứng từ" (never skip documents), "không tự hạch toán khi chưa đủ căn cứ" (never post without basis) — the invariants department policy already states, imported verbatim.
Source: series-internal (Track 1 analogy).

### Round 27: Rules Diff Severity
**Empirical Finding**: A rules/ edit is a fleet-wide event — every prompt including the file changes behavior; rules diffs need the widest review circle (the L2 lock discipline).
Source: series-internal (Track 2 Part 3 guardrail isolation).

### Round 28: Prohibition-Only Anti-Pattern
**Empirical Finding**: Anthropic's positive-framing rule applies to rules files: state target behaviors, reserve prohibitions for hard guardrails paired with the positive — "prompt the positive" from the agent-facing discipline.
Source: agent-skills pack writing discipline; Anthropic framing guidance.

### Round 29: Rules and Injection Defense
**Empirical Finding**: Rules/ is the Constraints-block home in kit form: scope locks and tool policies that make OWASP ASI01 injection tests part of the eval loop.
Source: series Track 2 Part 6; OWASP ASI framing.

### Round 30: Rules File Length
**Empirical Finding**: Rules stay under ~10 lines per file in the kit — long rule files get skimmed, short ones get enforced; the pack's LOCK pattern (labeled, one-line-per-lock) is the format evidence.
Source: agent-skills pack guardrail format.

## Cluster 4 — Workflows/ Directory (Rounds 31–40)

### Round 31: Workflow File Anatomy
**Empirical Finding**: Each workflow answers: when to use (trigger), execution steps, expected output — the three fields Track 1 Part 3 specified.
Source: series-internal (Track 1 Part 3 layer 3).

### Round 32: The Kit's Three Starter Workflows
**Empirical Finding**: debug-issue.md, code-review.md, quick-docs.md — three recurring work types; each ships numbered steps where order matters.
Source: series-internal (Track 1 Part 5 tree).

### Round 33: Numbered Steps Rule
**Empirical Finding**: Anthropic: "Provide instructions as sequential steps using numbered lists when the order or completeness of steps matters" — workflows are exactly that pattern at procedure scale.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 34: Completion Criteria Per Step
**Empirical Finding**: Every workflow step ends on a checkable condition — "every modified model accounted for" beats "produce a change list" (agent-facing discipline).
Source: agent-skills pack writing discipline.

### Round 35: Self-Check as Final Step
**Empirical Finding**: "Before you finish, verify your answer against [test criteria]" — the kit's workflows close with verification (Anthropic's self-check guidance).
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 36: Incremental Progress for Long Work
**Empirical Finding**: "Emphasize incremental progress: Explicitly ask Claude to keep track of its progress and focus on incremental work" — long workflows get progress notes and git state.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 37: General Over Prescriptive
**Empirical Finding**: "Prefer general instructions over prescriptive steps... Claude's reasoning frequently exceeds what a human would prescribe" — kit workflows bound outcomes, not reasoning chains.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 38: Workflow vs Skill Boundary
**Empirical Finding**: Workflow = the procedure (how work moves); skill = domain depth (specialty knowledge) — the kit keeps them in separate directories for the same reason layers exist: different change frequencies.
Source: series-internal (Track 1 Part 3 boundary).

### Round 39: The Accounting Workflow
**Empirical Finding**: Finance workflow example: month-end reconciliation — fixed sequence on calendar trigger; the kit's workflows/ accepts business-event-triggered procedures unchanged.
Source: series-internal (Track 1 Part 3 analogy).

### Round 40: Workflow Coverage Signal
**Empirical Finding**: When the same ad-hoc procedure gets typed three times in a week, it graduates to workflows/ — pain-triggered growth, the kit's only promotion rule.
Source: series-internal (adoption sequencing).

## Cluster 5 — Skills/ Directory (Rounds 41–50)

### Round 41: Skill File Anatomy
**Empirical Finding**: Each skill states: which tasks it serves, which it does not, execution checklist, common pitfalls — the four-field contract.
Source: series-internal (Track 1 Part 5 skill spec).

### Round 42: The Kit's Two Starter Skills
**Empirical Finding**: add-api-endpoint/SKILL.md and write-tests/SKILL.md — two deep, narrow domains; each loaded only on trigger match.
Source: series-internal (Track 1 Part 5 tree).

### Round 43: Trigger Front-Loading
**Empirical Finding**: "A line that names out-of-context material must front-load its trigger words and list the distinct branches that should fire it — one trigger per branch" — kit skills follow the pointer discipline.
Source: agent-skills pack writing discipline.

### Round 44: Skill Bodies Load Just-in-Time
**Empirical Finding**: The pack's evidence: only trigger lines occupy always-on context; bodies load on match — the attention-budget argument for the skill directory's existence.
Source: agent-skills pack structure; Anthropic JIT guidance.

### Round 45: Skill Granularity
**Empirical Finding**: One skill = one task family; overlapping skills create trigger collisions — the overlap-confusion documented for tools applies to skills.
Source: series Track 1 Part 3; https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 46: The Accounting Skill
**Empirical Finding**: reconcile-report/SKILL.md: permitted data sources, "chưa đủ dữ liệu" flag rule, mandatory diff-table format, no-guess-on-missing-amounts — the finance skill contract from Part 5's example.
Source: series-internal (Track 1 Part 5 reconciliation skill).

### Round 47: Skill Ownership
**Empirical Finding**: Each skill names a domain owner in frontmatter — the question "who fixes the VAT skill at quarter close" answered by the file.
Source: series-internal (ownership model).

### Round 48: Skill Registry Discipline
**Empirical Finding**: A README index lists active skills with owners — unregistered skills don't load (the allowlist discipline at prompt level).
Source: series-internal; MCP scope-minimization parallel.

### Round 49: Skill Deprecation
**Empirical Finding**: Superseded skills archive with migration notes; stale triggers are silent context pollution.
Source: series-internal (asset lifecycle).

### Round 50: The Pack as Skill Evidence
**Empirical Finding**: 108 skills coexist in the pack with distinct triggers and zero cross-firing — the granularity and registry disciplines scale past the starter kit's two.
Source: agent-skills pack structure.

## Cluster 6 — Evals/ Directory (Rounds 51–60)

### Round 51: Why Evals Ships in the Kit
**Empirical Finding**: The kit includes evals/ from day one because Part 4's thesis: standardization without measurement is half a system — "evals fire on change" starts with the first prompt.
Source: series-internal (Track 1 Part 5; Part 4 thesis).

### Round 52: Eval Case File Anatomy
**Empirical Finding**: Each eval file: sample inputs, pass/fail criteria, mandatory-detection list (critical errors the agent must catch) — three fields per case set.
Source: series-internal (Track 1 Part 5 eval spec).

### Round 53: The Kit's Two Starter Case Sets
**Empirical Finding**: review-agent-cases.md and docs-agent-cases.md — matching the two starter workflows; each holds the five-probe pattern (happy, performance, format-only, missing-context, security).
Source: series-internal (Track 1 Part 4 five-case recipe).

### Round 54: Five-Case Minimum
**Empirical Finding**: The five probes per task: happy path, performance case, format-only change, missing-context case, security case — five distinct failure classes, five cases.
Source: series-internal (Track 1 Part 4 eval example generalized).

### Round 55: Accounting Eval Cases
**Empirical Finding**: reconciliation-cases.md: include the missing-voucher case, assert "chưa đủ chứng từ để kết luận" flagged instead of auto-filled — Fallback behavior tested, not hoped.
Source: series-internal (Track 1 Part 5; Part 4 accounting eval).

### Round 56: Eval Grounded in Real Tasks
**Empirical Finding**: "Grounded in real world uses... avoid overly simplistic 'sandbox' environments" — kit evals use the team's actual recurring inputs, not toy samples.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 57: Verifiers Check Contracts
**Empirical Finding**: "Avoid overly strict verifiers that reject correct responses due to spurious differences" — kit evals verify format + critical detection, not prose identity.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 58: A Few Dozen Pairs to Start
**Empirical Finding**: Kit scale: a few dozen input/output pairs for the top 2–3 tasks — small enough to maintain, large enough to catch format breaks.
Source: series-internal (starter-kit guidance).

### Round 59: Eval-Then-Fix Cadence
**Empirical Finding**: The adoption loop: run the task 1–2 weeks, collect repeated failures, fix the matching block — "sửa dựa trên lỗi lặp lại" is eval-lite that graduates to case files.
Source: series-internal (Track 1 Part 5 rollout step 3).

### Round 60: The Kit's Gate
**Empirical Finding**: The kit's gate is manual: a pass-rate check on the case file before adopting a prompt change — the >95% threshold arrives with CI, the discipline arrives with the kit.
Source: series Track 2 Part 6 (threshold); series-internal (kit scoping).

## Cluster 7 — The Conventions Page (Rounds 61–70)

### Round 61: The One-Pager Contents
**Empirical Finding**: Four lines: naming (lowercase-hyphen), owner (frontmatter field), review rule (who signs off what), versioning (changelog header) — the conventions page is the kit's constitution.
Source: series-internal (Track 1 Part 5 conventions).

### Round 62: Naming Is Onboarding UX
**Empirical Finding**: Consistent file names are how new members find the right template without asking — the takeover test's mechanical precondition.
Source: series-internal (Round 8 of this dossier).

### Round 63: Owner Field Format
**Empirical Finding**: Frontmatter: `owner: <github-handle>` per file — the 3am question answered structurally.
Source: series-internal (ownership model).

### Round 64: Review-Rule Routing
**Empirical Finding**: The routing table: roles/workflows → team lead; rules/ → security; skills/ → domain owner; evals/ → task owner — each directory's review authority named on the page.
Source: series-internal (layer ownership).

### Round 65: Changelog Header Format
**Empirical Finding**: Every file opens with a version header + dated change list — the Part 4 changelog format, embedded per-file.
Source: series-internal (Track 1 Part 4 changelog).

### Round 66: The Page Stays One Page
**Empirical Finding**: Conventions bloat kills adoption — the page stays under ~1 screen; anything longer belongs in the docs site, not the kit's front door.
Source: series-internal.
[INFERENCE] The one-screen limit is a series heuristic, not a measured constant.

### Round 67: Conventions as Diff Guard
**Empirical Finding**: The conventions page is what reviewers cite in review comments ("naming violation", "missing owner") — it converts taste disputes into checklist items.
Source: series-internal (review practice).

### Round 68: Kit Bootstrap Commit
**Empirical Finding**: The kit lands as one commit (tree + conventions + two templates + two case sets) — reviewable in a single PR, adoptable in a single merge.
Source: series-internal (bootstrap recipe).

### Round 69: The Bootstrap Checklist
**Empirical Finding**: Bootstrap in seven steps: mkdir five dirs → write conventions page → write 2 role files → write safety.md → write 2 workflows → write 2 skills → write 2 eval case sets — an afternoon's work with checkpoints.
Source: series-internal (Track 1 Part 5 recipe).

### Round 70: Done Definition for the Kit
**Empirical Finding**: Kit done = takeover test passes (a member runs a task from the tree alone) + two colleagues produce compatible prompts from the same template.
Source: series-internal (Round 10).

## Cluster 8 — Role-Specific Entry Templates (Rounds 71–80)

### Round 71: One Standard, Five Doors
**Empirical Finding**: The kit's role templates: PM (product brief), Developer (code change), Tester (test case generation), Accounting (reconciliation), CS (customer response) — same 8-block anatomy, five entry vocabularies.
Source: series-internal (Track 1 Part 5 role templates).

### Round 72: The Engineering Template
**Empirical Finding**: The engineering agent template: Go microservices identity, correctness/safety/maintainability mission, local-validation scope, Clean Architecture/DDD/Kratos context, five-step workflow, change-report output contract, stop-and-ask uncertainty.
Source: series-internal (Track 1 Part 5 engineering template).

### Round 73: The Accounting Template
**Empirical Finding**: The reconciliation template: financial-data assistant identity, accuracy/no-guessing mission, compare-and-flag scope, sales-report/statement/internal-lead-sheet context, khớp/lệch/thiếu output contract, "chưa đủ dữ liệu" uncertainty rule.
Source: series-internal (Track 1 Part 5 accounting template).

### Round 74: Template Completeness Note
**Empirical Finding**: The engineering template runs 7 blocks (no Tool Policy — the kit's agent has no tools yet); the accounting template runs 6 (no Workflow block — single-pass comparison) — omission as documented decision per the block rules.
Source: series-internal (Track 1 Part 2 omission rules).

### Round 75: The PM Template
**Empirical Finding**: The PM brief template: product-owner identity, decision-support mission, research-and-frame scope, roadmap context, structured-brief output (problem/users/constraints/risks/asks), open-questions uncertainty.
Source: series-internal (Track 1 Part 5 role template set).

### Round 76: The Tester Template
**Empirical Finding**: The tester template: QA identity, coverage-first mission, generate-then-verify scope, codebase conventions context, case-per-behavior output contract, flag-untestable uncertainty.
Source: series-internal (Track 1 Part 5 role template set).

### Round 77: The CS Template
**Empirical Finding**: The CS template: support identity, resolve-accurately mission, never-promise scope, product-knowledge context, response-format contract (acknowledge/diagnose/resolve/escalate), escalation-trigger uncertainty.
Source: series-internal (Track 1 Part 5 role template set).

### Round 78: Template Portability
**Empirical Finding**: Templates copy between teams unchanged except Context block — the anatomy is portable, the context is local; porting is one block's work.
Source: series-internal.

### Round 79: Template as Training Material
**Empirical Finding**: The role templates double as onboarding reading: a new PM reads the PM template and knows the house style for briefs — the kit teaches by example.
Source: series-internal (onboarding function).

### Round 80: The Accounting Kit Add-On
**Empirical Finding**: The finance add-on tree: skills/reconcile-report/ + evals/reconciliation-cases.md — the kit extends by directory addition, never by restructuring.
Source: series-internal (Track 1 Part 5 add-on example).

## Cluster 9 — Adoption Mechanics (Rounds 81–90)

### Round 81: The Three-Step Rollout
**Empirical Finding**: Step 1: pick 1–2 most-repeated use cases; Step 2: write the first standard prompts for them; Step 3: watch output 1–2 weeks, fix on repeated failures — the series' published rollout.
Source: series-internal (Track 1 Part 5 rollout).

### Round 82: Use-Case Selection Rule
**Empirical Finding**: Pick by repetition, not impressiveness: code review and quick docs outrank novel demos — repetition amortizes template cost and generates eval data fastest.
Source: series-internal (Track 1 Part 5 selection rule).

### Round 83: The First Standardized Prompt
**Empirical Finding**: The first prompt ships from the role template + the use case's context — 20 minutes, not a design project; the standard proves itself in use, not in review.
Source: series-internal.

### Round 84: Week-One Metrics
**Empirical Finding**: Week one counts: how many runs used the template vs ad-hoc (reuse rate), format breaks caught by eye (pre-eval signal), questions new members asked (onboarding friction) — three observable numbers before any infrastructure.
Source: series-internal (adoption metrics, manual form).

### Round 85: The Fix Loop
**Empirical Finding**: The Part 5 loop: collect repeated failures → map to block → fix block → note in changelog — eval-lite graduating into case files when volume justifies.
Source: series-internal (Track 1 Part 5 rollout step 3).

### Round 86: Anti-Doctrine: Not Everything Day One
**Empirical Finding**: "Đừng cố chuẩn hoá tất cả mọi thứ ngay ngày đầu" — the kit's scope honesty; standardizing everything at once is the shelfware failure mode.
Source: series-internal (Track 1 Part 5 closing).

### Round 87: The Two-Colleague Signal
**Empirical Finding**: Adoption is real when two colleagues independently produce compatible prompts from the same template — the observable difference between standard and document.
Source: series-internal (Round 10).

### Round 88: Graduation Criteria
**Empirical Finding**: The kit graduates when: >5 active prompts, >3 task types, or a security review need appears — each threshold triggers the next chapter's machinery (layering, evals CI, MCP).
Source: series-internal (Track 1 Part 5 → Track 2 bridge).

### Round 89: Common Adoption Blockers
**Empirical Finding**: Blockers observed: senior resistance (answer: show the same task with/without structure), non-engineer intimidation (answer: the SOP framing), "no time" (answer: the 30–60 minute timebox and the repeated-failure tax it removes).
Source: series-internal (adoption practice).

### Round 90: The Series Position
**Empirical Finding**: The kit is Track 1's deliverable: everything before it (why, anatomy, layers, measurement) condenses into five directories and one page — the series' "deployable this afternoon" promise.
Source: series-internal (Track 1 architecture).

## Cluster 10 — Kit Maintenance and Growth (Rounds 91–100)

### Round 91: The Monthly Kit Review
**Empirical Finding**: Borrowing the period-end close: monthly pass — conventions still one page? rules still true? workflows still match practice? skills still triggered? evals still passing? — five questions, twenty minutes.
Source: series-internal (period-end eval parallel).

### Round 92: Promotion Rules Between Directories
**Empirical Finding**: Ad-hoc procedure typed 3x/week → workflows/; domain guidance outgrowing a workflow → skills/; invariant discovered in an incident → rules/; repeated failure pattern → evals/ — the kit's internal promotion ladder.
Source: series-internal (pain-triggered growth).

### Round 93: Demotion and Archival
**Empirical Finding**: Workflows nobody follows get archived, not argued about — usage is the only legitimacy test; dead files mislead new members more than missing files.
Source: series-internal.

### Round 94: Kit Anti-Patterns
**Empirical Finding**: The three kit anti-patterns: template fiction (no task matches), eval theater (case files never run), owner sprawl (files without owners) — each diagnosable by the takeover test.
Source: series-internal (failure modes).

### Round 95: Growth Path Preview
**Empirical Finding**: When the kit strains (cache economics, multi-team rules, agentic tools), the series continues: Part 6+ escalates to context engineering, MCP, RAG, DSPy, and CI-gated PromptOps — the kit is deliberately the floor, not the ceiling.
Source: series architecture (Track 1 → Track 2 bridge).

### Round 96: The Kit in One Sentence
**Empirical Finding**: The kit in one line: five directories (roles/rules/workflows/skills/evals), one conventions page, two templates, two case sets — deployable in an afternoon, growing by pain.
Source: series synthesis.

### Round 97: Success Metrics Restated
**Empirical Finding**: The four numbers that say the kit works: reuse rate up, format-break incidents down, onboarding time down, pass rate stable-or-up — measurable from week one with zero infrastructure.
Source: series-internal (adoption metrics).

### Round 98: The Honest Failure Mode
**Empirical Finding**: The most common honest failure: the kit works but stops growing — team standardizes two use cases and never promotes more; acceptable if intentional (the two use cases were the pain), a stall if the pain was larger.
Source: series-internal.
[INFERENCE] Stall-vs-satisfied is a management judgment; the kit provides the signals (repeated-failure count), not the verdict.

### Round 99: What This Chapter Delivers
**Empirical Finding**: The chapter's deliverables: the directory tree, conventions page format, five role templates (3 fully drafted: engineering, accounting, + PM/tester/CS starters), the bootstrap checklist, the rollout recipe — the copy-paste kit.
Source: series-internal (Track 1 Part 5).

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes chapter 6's dossier; the EN twin is authored fresh (no consolidated candidate — the executive-summary precedent), and the campaign continues with the Track 1 final chapter (part-6-context-engineering) next.
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) the five-directory kit grounded as the layer model collapsed into a tree — with the agent-skills pack (108 skills / 34 roles / 24 workflows, 16/16 validation gates) as production-precedent evidence that the starter structure survives 5x scale; (2) the conventions one-pager as the kit's constitution (naming = onboarding UX, owner field, review routing, changelog header) — governance mechanics almost never specified in template posts; (3) promotion/demotion rules between directories (3x/week → workflow; incident → rule; failure pattern → eval) — the kit's internal ladder; (4) five role-specific entry templates with block-omission rationale (engineering 7-block, accounting 6-block); (5) week-one adoption metrics observable with zero infrastructure.
- **AI_coverage_gap**: Team-prompt-template posts ship trees and templates but skip: the evals/ directory (measurement from day one), the conventions page as governance, ownership/review routing, promotion rules, and the honest anti-doctrine — the kit's governance half is the differentiator.
- **firsthand_evidence_available**: no — synthesizes series design and vendor guidance; the pack's own structure is cited as precedent, not as a novel benchmark.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| platform.claude.com/docs (prompting best practices) | primary | Primary | golden rule, role focus, numbered steps, self-check, incremental progress, reversibility classes |
| anthropic.com/engineering/writing-tools-for-agents | primary | Primary | eval grounding, verifier discipline, task strength |
| agent-skills pack (108 skills / 34 roles / 24 workflows) | internal | Tertiary (internal) | structure-at-scale precedent, trigger discipline, LOCK format |
| series Track 1/Track 2 chapters | internal | Tertiary (internal) | kit design, rollout, templates |

## AI Source Discipline

- AI tools used for queries only (not cited): none — all rounds trace to fetched primary documents, the pack's verifiable file structure, or series-internal design.
- AI-citation mismatches: none.
- grounding_completeness: 20/100 rounds carry external source URLs; 77/100 cite series-internal or pack-structure evidence traceable to repo files; 3 rounds carry [INFERENCE] labels (Rounds 66, 98, and one interpretation note).

## Handoff

- **recommended_next_roles**: content-writer (Phase 3: upgrade VI part-5-team-template; Phase 4: author NEW EN twin `part-5-team-starter-kit` — no consolidated candidate), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: EN slug confirmation — proposed `part-5-team-starter-kit` (distinct from Track 2 part-5-declarative-prompting-dspy; no intent collision since topic differs).
- **residual_risks**: (1) the pack-precedent claim cites the repo's own structure — verify counts (108/34/24) at draft time via validate-all output; (2) [INFERENCE] rounds keep labels downstream (Gate 7).
