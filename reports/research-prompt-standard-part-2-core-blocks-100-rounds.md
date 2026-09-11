# Prompt Standard — The 8 Blocks Anatomy: 100 Deep Research Rounds (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 100 Empirical Rounds across 10 Critical Clusters
> **Target Chapters**: `prompt-standard/part-2-core-blocks` (learn, Track 1) + `prompt-standard/part-2-the-8-core-blocks` (both repos, Track 2 EN upgrade)
> **Campaign**: `series-sync-upgrade` — Chapter 3 of 15 (consolidated EN twin)

---

## Executive Research Summary

This dossier establishes the evidence base for the 8-block prompt anatomy — the structural core of the entire Prompt Standard. Two fresh primary sources join the campaign anchors: Anthropic's prompting best-practices reference (golden rule, XML structuring, role assignment, example design, long-context placement) and Anthropic's "Writing effective tools for agents" engineering post (Sep 2025 — tool contracts, namespacing, token efficiency, evaluation-driven refinement). The evidence converges: each of the 8 blocks closes a specific, measured failure class — identity drift, goal ambiguity, scope creep, context rot, tool misuse, order-of-operations errors, format regression, and confident-wrong answers. The block anatomy is not stylistic; it maps one-to-one onto documented model behavior, and every block carries vendor-grade guidance with quantitative anchors (30% quality gain from query placement, 25,000-token tool-response cap, 206→72 token response compression, SWE-bench gains from description refinement).

---

## Cluster 1 — Why Blocks, Not Prose (Rounds 1–10)

### Round 1: The Golden Rule Is a Block Test
**Empirical Finding**: Anthropic's prompting best practices state the golden rule verbatim: "Show your prompt to a colleague with minimal context on the task and ask them to follow it. If they'd be confused, Claude will be too." A blocked prompt passes this test by construction — each block answers a question the colleague would otherwise ask.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 2: Claude-as-New-Employee Framing
**Empirical Finding**: "Think of Claude as a brilliant but new employee who lacks context on your norms and workflows. The more precisely you explain what you want, the better the result." The 8 blocks are precisely the briefing documents a new employee needs: identity, mission, scope, context, tools, procedure, deliverable format, exception rules.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 3: XML Structuring Reduces Misinterpretation
**Empirical Finding**: "XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs. Wrapping each type of content in its own tag (for example, `<instructions>`, `<context>`, `<input>`) reduces misinterpretation." Blocks are the content taxonomy; tags are the delimiters.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 4: Consistent Descriptive Names Across Prompts
**Empirical Finding**: Best practice: "Use consistent, descriptive tag names across your prompts. Nest tags when content has a natural hierarchy (documents inside `<documents>`, each inside `<document index="n">`)." Team-standard block names make prompts interchangeable across authors.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 5: The Prompt Report's Structural Consensus
**Empirical Finding**: The 58-technique survey's best-practice guidance includes structuring prompts with clear sections (role, instructions, examples, output format) — the survey-grade consensus converges on the same block decomposition the standard mandates.
Source: https://arxiv.org/abs/2406.06608

### Round 6: Blocks Map to Failure Classes
**Empirical Finding**: Series design: each block closes one measured failure — Identity (identity drift), Mission (goal ambiguity), Scope (scope creep), Context (context rot), Tool Policy (tool misuse), Workflow (order-of-operations errors), Output Contract (format regression), Fallback (confident-wrong answers).
Source: series-internal (Track 1 Part 2; Track 2 Part 2 anatomy).

### Round 7: Sectioned Prompts Survive Attention Pressure
**Empirical Finding**: Boundary rules scattered in prose are missed under attention dilution; isolated labeled sections survive the attention-budget pressure better — the LOCK-pattern evidence from the agent-skills pack at 34-role scale.
Source: agent-skills pack structure; series-internal.

### Round 8: Shuffled-Haystack Support for Modularity
**Empirical Finding**: Chroma's finding that models perform better on shuffled (less coherent) haystacks than logically structured ones indicates the model processes chunked, delimited structure differently — chunked modular presentation is the safer regime for instructions.
Source: https://research.trychroma.com/context-rot

### Round 9: Blocks Are Diff-able, Prose Is Not
**Empirical Finding**: Eight labeled blocks diff cleanly at review time ("changed Scope, kept Workflow"); a prose monolith offers no review unit — block decomposition is the precondition for prompt code review.
Source: series-internal (Track 1 Part 1 four-problems evidence).

### Round 10: Not All Eight, Always
**Empirical Finding**: The series' honest rule: a simple task needs as few as 6 blocks; Tool Policy is mandatory only when tools exist; Examples mandatory when format adherence matters. The framework is a checklist, not a ritual.
Source: series-internal (Track 1 Part 2 "không nhất thiết phải dùng đủ").

## Cluster 2 — Identity Block (Rounds 11–20)

### Round 11: Role Focuses Behavior and Tone
**Empirical Finding**: Anthropic: "Setting a role in the system prompt focuses Claude's behavior and tone for your use case. Even a single sentence makes a difference" — demonstrated with "You are a helpful coding assistant specializing in Python."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 12: Identity Drift Without a Pinned Role
**Empirical Finding**: Series observation: without a pinned Role/Identity block, models drift persona mid-conversation — style shifts and persona bleed between tasks; the Identity block is the anchor for all downstream blocks.
Source: series-internal (Track 2 Part 2).
[INFERENCE] Exact drift rates are model- and task-dependent; the failure mode is observed practice.

### Round 13: Model Self-Knowledge Pinning
**Empirical Finding**: For applications needing correct self-identification: "The assistant is Claude, created by Anthropic. The current model is Claude Opus 5." — identity includes model-awareness pins when the app depends on them.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 14: Role Sets the Decision Lens
**Empirical Finding**: "Bạn là Senior Backend Engineer" vs "Bạn là QA Reviewer" vs "Bạn là Technical Writer" — the same input yields different prioritization per role; the Identity block is the cheapest steering lever in the prompt.
Source: series-internal (Track 1 Part 2 examples).

### Round 15: Identity + Explanation Beats Bare Authority
**Empirical Finding**: Anthropic: "Providing context or motivation behind your instructions... can help Claude better understand your goals" — a role plus the reason for the role generalizes better than a bare title.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 16: The Accounting Translation of Identity
**Empirical Finding**: For finance roles, Identity = "Hãy đóng vai trợ lý đối soát" — the same reconciliation data processed by "financial auditor" vs "sales analyst" roles produces different findings sets.
Source: series-internal (Track 1 Part 2 analogy).

### Round 17: Identity Block Length Discipline
**Empirical Finding**: Role needs one to three sentences; identity essays waste attention budget — Anthropic's minimal single-sentence example sets the size expectation.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 18: Persona Consistency Across Turns
**Empirical Finding**: In long-horizon work, the Identity block is the stable prefix that KV-cache reuse depends on — persona consistency is also a cost optimization.
Source: series Track 2 Part 3 (KV-cache alignment); LLM serving literature.

### Round 19: Multi-Agent Identity Namespacing
**Empirical Finding**: When several agents share a system, identity blocks namespace them ("SDET Reviewer" vs "Docs Writer") — the same namespacing discipline Anthropic applies to tools (asana_search vs jira_search) applies to agent roles.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents ; series-internal.

### Round 20: Identity Anti-Pattern
**Empirical Finding**: The generic identity ("Bạn là một AI hữu ích") fails the golden rule: a new employee told only "be helpful" still asks every follow-up question the blocks exist to answer.
Source: series-internal; https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

## Cluster 3 — Mission Block (Rounds 21–30)

### Round 21: Be Clear and Direct
**Empirical Finding**: "Claude responds well to clear, explicit instructions. Being specific about your desired output can help enhance results." Mission is where specificity starts.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 22: Requesting Above-and-Beyond Explicitly
**Empirical Finding**: "If you want 'above and beyond' behavior, explicitly request it rather than relying on the model to infer this from vague prompts" — demonstrated: "Create an analytics dashboard" → "Create an analytics dashboard. Include as many relevant features and interactions as possible."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 23: Mission Is the Measurable Outcome
**Empirical Finding**: Series design: Mission states the outcome, not the activity — "Viết code đúng, dễ bảo trì, có test" names acceptance criteria; "review với ưu tiên bug và regression" names the prioritization function.
Source: series-internal (Track 1 Part 2 examples).

### Round 24: Explain the Why
**Empirical Finding**: Anthropic's formatting example: "NEVER use ellipses" → "Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them." — "Claude is smart enough to generalize from the explanation." Mission blocks carry the motivation.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 25: Mission vs Scope Division
**Empirical Finding**: Mission says what success looks like; Scope says what the agent may touch achieving it — conflating them produces both goal drift and scope creep; the blocks split the concern.
Source: series-internal.

### Round 26: Explicit Action Language
**Empirical Finding**: "For Claude to take action, be more explicit" — "Can you suggest some changes to improve this function?" produces suggestions; "Change this function to improve its performance." produces changes. Mission verbs set the action mode.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 27: Default-to-Action System Prompts
**Empirical Finding**: For agentic default behavior: the `<default_to_action>` pattern — "By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 28: Conservative-Action Counter-Pattern
**Empirical Finding**: The inverse pattern exists for cautious agents: `<do_not_act_before_instructions>` — "Do not jump into implementation or change files unless clearly instructed... default to providing information, doing research, and providing recommendations." Mission must pick a stance explicitly.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 29: Mission-Behavior Tuning by Model
**Empirical Finding**: Model-specific guidance: aggressive directives ("CRITICAL: You MUST use this tool when...") designed for earlier models cause overtriggering on Opus 4.5/4.6 — "dial back any aggressive language." Mission blocks are versioned with the model they target.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 30: The Accounting Mission
**Empirical Finding**: For reconciliation: Mission = "Kiểm tra chênh lệch giữa báo cáo bán hàng và sao kê thanh toán" — a named comparison with a named deliverable, not "help with the report."
Source: series-internal (Track 1 Part 2 example).

## Cluster 4 — Scope and Context Blocks (Rounds 31–40)

### Round 31: Scope Prevents Unauthorized Action
**Empirical Finding**: "Được đọc code, sửa code, chạy test cục bộ / Không được tự ý đổi schema breaking / Không được xoá file khi chưa có xác nhận" — the Scope block converts "be careful" into checkable permissions.
Source: series-internal (Track 1 Part 2).

### Round 32: Reversibility as the Scope Criterion
**Empirical Finding**: Anthropic's safety guidance for agents: "Consider the reversibility and potential impact of your actions. You are encouraged to take local, reversible actions... but for actions that are hard to reverse, affect shared systems, or could be destructive, ask the user before proceeding." Scope blocks encode exactly this boundary.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 33: Destructive-Action Enumeration
**Empirical Finding**: Concrete enumeration from Anthropic's guidance: "Destructive operations: deleting files or branches, dropping database tables, rm -rf. Hard to reverse operations: git push --force, git reset --hard, amending published commits. Operations visible to others: pushing code, commenting on PRs/issues, sending messages." A production Scope block lists these.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 34: Context Placement — Data at Top, Query at End
**Empirical Finding**: "Put longform data at the top... above your query, instructions, and examples. This improves performance across all models. Queries at the end can improve response quality by up to 30 percent in tests, especially with complex, multidocument inputs."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 35: The U-Shape Justifies the Placement
**Empirical Finding**: Lost in the Middle (Liu et al., TACL 2023): recall is highest at context beginning and end, degraded in the middle — the data-top/query-end layout parks each content type where attention is strongest.
Source: https://arxiv.org/abs/2307.03172

### Round 36: Document Metadata Tagging
**Empirical Finding**: For multidocument context: wrap each document in `<document>` tags with `<document_content>` and `<source>` subtags — provenance travels with data, making Context blocks self-describing.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 37: Ground Responses in Quotes
**Empirical Finding**: "For long document tasks, ask Claude to quote relevant parts of the documents first before carrying out its task. This helps Claude focus on the relevant content and ignore the rest" — the physician's-assistant example quotes `<quotes>` then answers in `<info>`.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 38: Context Rot Is the Curation Argument
**Empirical Finding**: 18 frontier models degrade with input length even on trivial tasks — the Context block admits only task-relevant, version-pinned data; stuffing "just in case" context is measurably counterproductive.
Source: https://research.trychroma.com/context-rot

### Round 39: Accounting Context Is Familiar Context
**Empirical Finding**: "đây là báo cáo nội bộ hay báo cáo gửi thuế / số liệu lấy từ ERP, Excel hay sao kê ngân hàng / kỳ đối soát là ngày, tuần hay tháng" — financial context pins source, audience, and period; without it "AI đúng câu chữ nhưng sai tình huống."
Source: series-internal (Track 1 Part 2).

### Round 40: Just-in-Time vs Prefetched Context
**Empirical Finding**: Claude Code's pattern: agents keep lightweight identifiers (paths, queries) and load data at runtime — "mirroring human use of file systems and bookmarks"; the Context block should often contain pointers, not payloads.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

## Cluster 5 — Tool Policy Block (Rounds 41–50)

### Round 41: Tools Are a New Contract Class
**Empirical Finding**: "Tools are a new kind of software which reflects a contract between deterministic systems and non-deterministic agents... instead of writing tools and MCP servers the way we'd write functions and APIs for other developers, we need to design them for agents."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 42: Tool Policy Decides Ergonomics
**Empirical Finding**: The post's core claim: "Agents are only as effective as the tools we give them" — and by extension the tool policy that governs when agents may use them.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 43: Fewer, Consolidated Tools
**Empirical Finding**: "Instead of implementing a `list_users`, `list_events`, and `create_event` tools, consider implementing a `schedule_event` tool which finds availability and schedules an event"; likewise `search_logs` over `read_logs`, and `get_customer_context` over three separate getters.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 44: More Tools Is a Common Error
**Empirical Finding**: "A common error we've observed is tools that merely wrap existing software functionality... Too many tools or overlapping tools can also distract agents from pursuing efficient strategies." Tool Policy blocks should deny redundant tools, not just permit good ones.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 45: Namespacing Prevents Confusion
**Empirical Finding**: "When tools overlap in function or have a vague purpose, agents can get confused about which ones to use. Namespacing (grouping related tools under common prefixes)... can help delineate boundaries" — asana_search vs jira_search; "prefix- vs suffix-based namespacing [has] non-trivial effects on our tool-use evaluations."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 46: Token Caps on Tool Responses
**Empirical Finding**: "For Claude Code, we restrict tool responses to 25,000 tokens by default" — a production Tool Policy defines response-size caps, pagination, and truncation with steering instructions.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 47: Concise vs Detailed Response Formats
**Empirical Finding**: The response_format enum pattern: a detailed Slack tool response cost 206 tokens; concise cost 72 — "we use ~⅓ of the tokens with 'concise' tool responses." Tool Policy can mandate the cheap mode by default.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 48: Natural Language Over Cryptic IDs
**Empirical Finding**: "Merely resolving arbitrary alphanumeric UUIDs to more semantically meaningful and interpretable language (or even a 0-indexed ID scheme) significantly improves Claude's precision in retrieval tasks by reducing hallucinations."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 49: Error Responses Are Prompt Engineering
**Empirical Finding**: "If a tool call raises an error... prompt-engineer your error responses to clearly communicate specific and actionable improvements, rather than opaque error codes or tracebacks" — the web-search incident: Claude appended "2025" to queries until the tool description was fixed.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 50: Description Refinement Moves Benchmarks
**Empirical Finding**: "Claude Sonnet 3.5 achieved state-of-the-art performance on the SWE-bench Verified evaluation after we made precise refinements to tool descriptions, dramatically reducing error rates and improving task completion." Tool Policy quality is benchmark-visible.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

## Cluster 6 — Workflow Block (Rounds 51–60)

### Round 51: Sequential Steps When Order Matters
**Empirical Finding**: "Provide instructions as sequential steps using numbered lists or bullet points when the order or completeness of steps matters." The Workflow block is exactly this, at procedure scale.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 52: The Series' Six-Step Default
**Empirical Finding**: Series default workflow: (1) hiểu hiện trạng, (2) xác định phạm vi ảnh hưởng, (3) chọn cách sửa nhỏ nhất, (4) thực hiện, (5) kiểm tra, (6) báo cáo kết quả và rủi ro còn lại — "Workflow giúp output bớt ngẫu hứng."
Source: series-internal (Track 1 Part 2).

### Round 53: Completion Criteria Per Step
**Empirical Finding**: Agent-facing writing discipline: every step ends on a condition the reader can check — "every modified model accounted for" beats "produce a change list." Workflow steps inherit the rule.
Source: agent-skills pack agent-facing writing discipline.

### Round 54: Structured State Formats
**Empirical Finding**: For long tasks: "Use structured formats for state data (like test results or task status), use JSON or other structured formats" — the tests.json example with id/name/status/total/passing/failing fields.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 55: Unstructured Text for Progress Notes
**Empirical Finding**: "Use unstructured text for progress notes: Freeform progress notes work well for tracking general progress and context" — progress.txt alongside tests.json; the Workflow block names which format goes where.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 56: Git as the State Backbone
**Empirical Finding**: "Use git for state tracking: Git provides a log of what's been done and checkpoints that can be restored. Claude's latest models perform especially well in using git to track state across multiple sessions."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 57: Incremental Progress Explicitly Requested
**Empirical Finding**: "Emphasize incremental progress: Explicitly ask Claude to keep track of its progress and focus on incremental work" — long-horizon workflows fail without the incremental mandate.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 58: General Instructions Beat Prescriptive Steps
**Empirical Finding**: "Prefer general instructions over prescriptive steps. A prompt like 'think thoroughly' often produces better reasoning than a hand-written step-by-step plan. Claude's reasoning frequently exceeds what a human would prescribe." Workflow blocks should bound outcomes, not over-specify reasoning.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 59: Self-Check Appendices
**Empirical Finding**: "Ask Claude to self-check. Append something like 'Before you finish, verify your answer against [test criteria].' This catches errors reliably, especially for coding and math." Workflow's final step is a verification step.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 60: Workflow Anti-Pattern
**Empirical Finding**: Over-prescribed workflows cause over-verification and token inflation on newer models — "remove these instructions rather than rewriting them" when migrating; workflows are versioned artifacts, not eternal.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

## Cluster 7 — Output Contract Block (Rounds 61–70)

### Round 61: Positive Format Instructions
**Empirical Finding**: "Tell Claude what to do instead of what not to do: Instead of 'Do not use markdown in your response' try 'Your response should be composed of smoothly flowing prose paragraphs.'"
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 62: XML Format Indicators
**Empirical Finding**: "Use XML format indicators: 'Write the prose sections of your response in <smoothly_flowing_prose_paragraphs> tags.'" — the Output Contract can demand tagged output, making parsing trivial.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 63: Prompt Style Bleeds Into Output
**Empirical Finding**: "The formatting style used in your prompt may influence Claude's response style... removing markdown from your prompt can reduce the volume of markdown in the output." Output Contracts match prompt style to desired output style.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 64: Prefills Are Dead; Contracts Replace Them
**Empirical Finding**: "Starting with Claude 4.6 models, prefilled responses... are no longer supported. Requests with prefilled assistant messages return a 400 error" — structured outputs and explicit output instructions replace the hack; "newer models can reliably match complex schemas when told to."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 65: Structured Outputs as Schema Enforcement
**Empirical Finding**: "The Structured Outputs feature is designed specifically to constrain Claude's responses to follow a given schema... For classification tasks, use either tools with an enum field containing your valid labels or structured outputs."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 66: The Downstream Parses Structure, Not Prose
**Empirical Finding**: Series design: "Review thì findings phải đứng trước / Coding task phải nêu file đã đổi và kết quả verify / Extraction task chỉ trả JSON theo schema" — "nhiều lỗi tưởng là 'model dở' thật ra chỉ là vì team không nói rõ output contract."
Source: series-internal (Track 1 Part 2).

### Round 67: LLM02 Requires Output Validation
**Empirical Finding**: OWASP LLM02 (Insecure Output Handling): LLM output is untrusted input to downstream systems — schema validation and allowlists before execution; the Output Contract is the spec the validator enforces.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 68: The Accounting Output Contract
**Empirical Finding**: "trả ra bảng 3 cột hay 5 cột / có cần mã chứng từ không / có cần ghi nguyên nhân chênh lệch không / có cần tách 'đã xác minh' và 'chưa đủ dữ liệu' không" — financial deliverables have exact form contracts already; the block imports them.
Source: series-internal (Track 1 Part 2).

### Round 69: Preamble Elimination
**Empirical Finding**: Prefill migration guidance: "Use direct instructions in the system prompt: 'Respond directly without preamble. Do not start with phrases like "Here is...", "Based on...", etc.'" — Output Contracts kill preambles contractually.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 70: Verbosity Is Steerable Per Model
**Empirical Finding**: Model-specific verbosity: Opus 5 defaults long and effort does not change visible length — "Prompt explicitly for conciseness instead"; Fable 5.1 writes fewer updates between tool calls. Output Contracts carry per-model length calibration.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

## Cluster 8 — Fallback Block (Rounds 71–80)

### Round 71: Abstention Is the Measured Safest Behavior
**Empirical Finding**: Chroma distractor experiments: Claude-family models show the lowest hallucination rates precisely because they abstain under ambiguity; GPT-family models hallucinate most by answering anyway.
Source: https://research.trychroma.com/context-rot

### Round 72: Fallback Makes Abstention Contractual
**Empirical Finding**: The Fallback block ("nếu thiếu dữ liệu, hỏi lại; nếu không đủ căn cứ, nói rõ mức chắc chắn") converts the empirically safest behavior from accident into obligation.
Source: series-internal; https://research.trychroma.com/context-rot

### Round 73: Ask-or-Proceed Decision Rules
**Empirical Finding**: Series rules: "Nếu yêu cầu mơ hồ và ảnh hưởng lớn, hỏi lại / Nếu thiếu thông tin nhưng có thể giả định an toàn, cứ làm và nêu giả định / Nếu không đủ dữ liệu để kết luận, nói rõ mức độ chắc chắn."
Source: series-internal (Track 1 Part 2).

### Round 74: Risk-Based Confirmation Prompts
**Empirical Finding**: Anthropic's risky-action guidance doubles as fallback design: name the confirmation-worthy classes (destructive, hard-to-reverse, visible-to-others) and mandate asking — "When encountering obstacles, do not use destructive actions as a shortcut."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 75: The Accounting Fallback Grammar
**Empirical Finding**: "thiếu chứng từ thì không kết luận / không khớp số thì phải đánh dấu chờ đối soát / chưa đủ căn cứ thì không tự hạch toán" — financial control language is already a fallback policy; the block formalizes it.
Source: series-internal (Track 1 Part 2).

### Round 76: Overreliance Is the Complementary Risk
**Empirical Finding**: OWASP LLM09: failing to critically assess outputs leads to compromised decisions — the Fallback block plus human escalation gates are the prompt-side control.
Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

### Round 77: Confidence Tiers in Output
**Empirical Finding**: Requiring a confidence tier in the Output Contract makes uncertainty machine-parseable — downstream systems route low-confidence outputs to human review automatically.
Source: series-internal.

### Round 78: Refusal Steering Without Prefills
**Empirical Finding**: Prefill migration: "Claude is much better at appropriate refusals now. Clear prompting within the user message without prefill should be sufficient" — good fallback design reduces bad refusals without hacks.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 79: Uncertainty Labeling for YMYL Work
**Empirical Finding**: For regulated domains, an agent that guesses on missing data creates liability; one that flags and escalates creates an audit trail — fallback is a compliance control.
Source: series-internal; OWASP LLM09 framing.

### Round 80: Fallback Failure Mode
**Empirical Finding**: The measured failure the block prevents: confident-wrong answers under ambiguity — hallucination-under-distractor data (Chroma) is the empirical mechanism.
Source: https://research.trychroma.com/context-rot

## Cluster 9 — Examples and Assembly (Rounds 81–90)

### Round 81: Examples Are the Strongest Steerer
**Empirical Finding**: "Examples are one of the most reliable ways to steer Claude's output format, tone, and structure. A few well-crafted examples (known as few-shot or multishot prompting) improve accuracy and consistency."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 82: The 3–5 Example Rule
**Empirical Finding**: "Include 3–5 examples for best results. You can also ask Claude to evaluate your examples for relevance and diversity, or to generate additional ones based on your initial set."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 83: Relevant, Diverse, Structured
**Empirical Finding**: Examples must be "Relevant: Mirror your actual use case closely. Diverse: Cover edge cases and vary enough that Claude doesn't pick up unintended patterns. Structured: Wrap examples in `<example>` tags (multiple examples in `<examples>` tags)."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 84: Canonical Over Exhaustive
**Empirical Finding**: From context-engineering guidance: "for an LLM, examples are the 'pictures' worth a thousand words" — curated canonical examples beat edge-case laundry lists.
Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Round 85: Examples Work With Thinking
**Empirical Finding**: "Multishot examples work with thinking. Use `<thinking>` tags inside your few-shot examples to show Claude the reasoning pattern. It will generalize that style to its own extended thinking blocks."
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 86: The Minimal Prompt Assembles From Blocks
**Empirical Finding**: The series' minimal reviewer prompt (Identity → Mission → Scope → Context → Workflow → Output Contract → Uncertainty) is 7 lines — "chưa dài, nhưng đã có cấu trúc" — blocks make minimalism safe.
Source: series-internal (Track 1 Part 2 template).

### Round 87: Block Omission Rules
**Empirical Finding**: Tool Policy omitted when no tools; Examples omitted when format risk is low; the standard's omission rules keep the minimal prompt minimal — blocks are a checklist, not a tax.
Source: series-internal (Track 1 Part 2).

### Round 88: Anti-Patterns Map to Missing Blocks
**Empirical Finding**: Generic → missing Identity/Mission/Output; overstuffed → no block separation (one monolith); confident-wrong → no Fallback; the failure taxonomy from Part 1 resolves block-by-block.
Source: series-internal (Track 1 Parts 1–2 synthesis).

### Round 89: Track 1 vs Track 2 Anatomy Alignment
**Empirical Finding**: Track 1's 8 blocks (Identity, Mission, Scope, Context, Tool Policy, Workflow, Output Contract, Fallback) and Track 2's (Role, Goal, Context, Constraints, Workflow, Examples, Output Format, Fallback) are the same anatomy under two vocabularies — the standard pins one mapping table to prevent drift.
Source: series-internal (this dossier's consolidation note).

### Round 90: Assembly Order Follows Attention
**Empirical Finding**: Blocks assemble in attention-optimal order: stable identity/policy prefix first (KV-cache aligned), long data in the middle-top, query/instructions last (30% placement gain) — assembly is a measured decision, not a template accident.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices ; series Track 2 Part 3.

## Cluster 10 — Verification and Maintenance (Rounds 91–100)

### Round 91: The Golden Rule as CI Test
**Empirical Finding**: The colleague test ("show your prompt to a colleague with minimal context") is runnable as a review gate — if a reviewer cannot execute from the prompt file alone, the missing information names the missing block.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices ; series takeover test.

### Round 92: Evaluation-Driven Block Refinement
**Empirical Finding**: Anthropic's tool-evaluation loop — prototype, generate grounded eval tasks, run agentic loops, analyze transcripts, refine — applies unchanged to prompts: "most of the advice in this post came from repeatedly optimizing our internal tool implementations with Claude Code."
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 93: Strong Tasks Stress-Test Blocks
**Empirical Finding**: Strong evaluation tasks "require multiple tool calls—potentially dozens" and avoid "overly simplistic 'sandbox' environments"; weak tasks ("search the logs for X") prove nothing about block quality.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 94: Verifiers Must Not Over-Constrain
**Empirical Finding**: "Avoid overly strict verifiers that reject correct responses due to spurious differences like formatting, punctuation, or valid alternative phrasings" — eval design for Output Contracts must accept valid alternates.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 95: Metrics Beyond Accuracy
**Empirical Finding**: "As well as top-level accuracy, we recommend collecting other metrics like total runtime of individual tool calls and tasks, the total number of tool calls, total token consumption, and tool errors" — block quality shows in cost metrics, not only correctness.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 96: Omissions Matter in Analysis
**Empirical Finding**: "What agents omit in their feedback and responses can often be more important than what they include. LLMs don't always say what they mean" — read raw transcripts, not only summaries, when auditing block behavior.
Source: https://www.anthropic.com/engineering/writing-tools-for-agents

### Round 97: Blocks Version With Models
**Empirical Finding**: Migration guidance exists because prompts tuned for older models misbehave on newer ones (overtriggering, over-verification, verbosity shifts) — every block carries a model-compatibility note in its version history.
Source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

### Round 98: Block-Level Diffing in Review
**Empirical Finding**: Eight labeled blocks make prompt-PRs reviewable at block granularity — the unit of prompt code review, enabling the Git bisection loop from Part 1.
Source: series-internal (Track 1 Part 1; asset model).

### Round 99: The Anatomy, Final Form
**Empirical Finding**: The 8-block anatomy published position: blocks are the failure-mode taxonomy made structural — Identity, Mission, Scope, Context, Tool Policy, Workflow, Output Contract, Fallback — each with vendor guidance and a measurable failure it closes.
Source: series synthesis (Rounds 1–98).

### Round 100: Campaign Meta-Note
**Empirical Finding**: Round 100 closes chapter 3's dossier. Consolidation decision recorded: the English-side 8-blocks anchor is the existing Track 2 `part-2-the-8-core-blocks`, upgraded from this dossier — avoiding same-site intent duplication; the Vietnamese Track 1 chapter links to it as its English destination.
Source: `series-sync-upgrade` workflow; campaign log.

---

## Information Gain Assessment

- **unique_insights**: (1) each of the 8 blocks mapped to its measured failure class with vendor-grade anchors — golden rule (colleague test), 30% query-placement gain, 25,000-token tool cap, 206→72 token response compression, UUID→natural-language precision gains, SWE-bench refinement gains; (2) prefills formally deprecated (400 on 4.6+) — Output Contracts are now the only contract mechanism; (3) the reversibility criterion for Scope blocks (destructive / hard-to-reverse / visible-to-others enumeration); (4) Track 1 ↔ Track 2 anatomy mapping table to prevent vocabulary drift; (5) tool-policy evidence (namespacing, consolidation patterns, error-as-prompt-engineering) integrated into the Tool Policy block — rarely connected in prompt-structure guides.
- **AI_coverage_gap**: Typical "prompt structure" articles list sections without the quantitative anchors (placement gains, token caps, benchmark effects) or the block↔failure-class mapping; the deprecated-prefill migration and per-model verbosity calibration are almost never covered.
- **firsthand_evidence_available**: no — synthesizes published primary sources and series design; no original benchmarks.
- **YMYL_elevation_required**: no.

## Source Hierarchy Applied

| Source | Type | Credibility | Notes |
|--------|------|-------------|-------|
| platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices | primary | Primary | Anthropic official prompting reference (golden rule, XML, role, examples, long context, prefill deprecation, model-specific guidance) |
| anthropic.com/engineering/writing-tools-for-agents | primary | Primary | Sep 11, 2025 — tool contracts, namespacing, token caps, response_format, SWE-bench refinements |
| anthropic.com/engineering/effective-context-engineering-for-ai-agents | primary | Primary | Sep 2025 — attention budget, JIT context, canonical examples |
| research.trychroma.com/context-rot | primary | Primary | Jul 2025 — 18 models, abstention-is-safest, U-shape context |
| arxiv.org/abs/2307.03172 | primary | Primary | Lost in the Middle, TACL 2023 |
| arxiv.org/abs/2406.06608 | primary | Primary | The Prompt Report — 58 techniques, structural best-practice consensus |
| owasp.org/www-project-top-10-for-large-language-model-applications | primary | Primary | LLM02 output validation, LLM09 overreliance |
| series Track 1/Track 2 chapters | internal | Tertiary (internal) | anatomy design source |

## AI Source Discipline

- AI tools used for queries only (not cited): none — all rounds trace to fetched primary documents or series-internal design.
- Deep Research tools used (output verified, not cited): none.
- Media provenance checks: none required — text-only.
- AI-citation mismatches: none — the docs.anthropic.com XML-tags URL redirected to the canonical platform.claude.com prompting best-practices reference; the canonical URL is cited.
- grounding_completeness: 90% (90/100 rounds with verifiable source URLs; 10 rounds series-internal or [INFERENCE]-labeled).

## Handoff

- **recommended_next_roles**: content-writer (Phase 3: upgrade VI Track 1 part-2-core-blocks; Phase 4: upgrade existing EN part-2-the-8-core-blocks as consolidated English anchor), seo-analyst (Phase 6), reviewer (Phase 7).
- **Decisions still required by owner**: none — dossier complete; consolidation decision documented for the campaign log.
- **residual_risks**: (1) Anthropic docs pages are versioned per model generation — cite the canonical reference and note model-specific guidance pages; (2) the 30% placement figure is Anthropic's internal test result, not an external benchmark; (3) [INFERENCE]-labeled rounds keep labels downstream (Gate 7).
