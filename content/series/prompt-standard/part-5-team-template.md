---
title: "Part 5 — A Minimum Viable Prompt Standard Kit for Immediate Deployment"
date: 2026-05-09T10:55:00+07:00
lastmod: 2026-05-09T10:55:00+07:00
draft: false
description: "A simple, practical Prompt Standard kit that any team — product, engineering, or operations — can deploy today."
categories:
  - Engineering
tags:
  - prompt-standard
weight: 6
ShowToc: true
TocOpen: true
---

## The Goal Is Not Perfection — It Is Getting Started

Many teams delay because they think they need a massive prompt system.

In reality, to get started you only need five directories:
- `roles/`
- `rules/`
- `workflows/`
- `skills/`
- `evals/`

## Suggested Directory Structure

```text
.agent/
  roles/
    developer.md
    reviewer.md
    writer.md
  rules/
    safety.md
    coding-standards.md
  workflows/
    debug-issue.md
    code-review.md
    quick-docs.md
  skills/
    add-api-endpoint/
      SKILL.md
    write-tests/
      SKILL.md
  evals/
    review-agent-cases.md
    docs-agent-cases.md
```

## Minimum Content for Each Layer

### Role
Each role should contain:
- identity
- responsibilities
- decision boundaries
- communication style

### Rules
Each rule file should contain:
- clear prohibitions
- safety principles
- internal invariants

### Workflow
Each workflow should answer:
- when to use it
- what steps to follow
- what output is expected

### Skill
Each skill should specify:
- which tasks it applies to
- which tasks it does not apply to
- implementation checklist
- common pitfalls

### Evals
Each eval set should have:
- sample inputs
- pass/fail criteria
- mandatory issues that must be detected

## A Short Prompt Template for Teams

```text
# Identity
You are an engineering agent working in a Go microservices repository.

# Mission
Prioritize correctness, safety, and maintainability.

# Scope
Allowed to read code, modify code, and run local validation.
Not allowed to make breaking changes without confirmation.

# Context
The repo uses Clean Architecture, DDD, Kratos, PostgreSQL, Redis, and Dapr.

# Workflow
Understand the current state, choose the smallest change, implement, verify, report.

# Output Contract
Clearly state changes made, related files, verification results, and remaining risks.

# Uncertainty
If you lack data for a major decision, stop and ask a concise question.
```

This template is not final, but it is enough for a team to start working consistently.

## A 3-Step Adoption Roadmap

### Step 1
Choose the 1 or 2 use cases your team repeats most often.

Examples:
- code review
- writing docs

### Step 2
Create the first standard prompt for those use cases.

### Step 3
Monitor output for 1–2 weeks, then iterate based on recurring errors.

Do not try to standardize everything on day one.

## Final Takeaway

A good Prompt Standard is one that the entire team can use, understand, and maintain.

If only one person understands the prompt system, it is not truly standardized.

A good standard should be:
- clear
- just enough
- easy to maintain
- tied to real work

> *If you have mastered the foundations, continue to the advanced sections:*
> *Read [Part 6 — From Prompting to Context Engineering](/series/prompt-standard/part-6-context-engineering/).*

{{< author-cta />}}
