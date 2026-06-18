---
title: "Part 2 — The 8 Core Blocks of an Agent Prompt"
date: 2026-05-09T10:40:00+07:00
lastmod: 2026-05-09T10:40:00+07:00
draft: false
description: "A simple 8-block framework that any team can use to start standardizing prompts for AI agents."
categories:
  - Engineering
tags:
  - prompt-standard
weight: 3
ShowToc: true
TocOpen: true
---

## Start with a Framework, Not a Long Prompt

A manageable prompt is usually divided into small blocks. You do not need all of them on day one, but this is a highly practical framework:

## 1. Identity

Who is the agent?

Examples:
- You are a Senior Backend Engineer
- You are a QA Reviewer
- You are a Technical Writer

This shapes the agent's perspective and decision-making approach.

## 2. Mission

Why does the agent exist?

Examples:
- Write correct, maintainable code with tests
- Review changes with a focus on bugs and regressions
- Write documentation that is easy for newcomers to understand

Mission gives the agent a persistent objective beyond processing individual commands.

## 3. Scope

What is the agent allowed to do and not allowed to do?

Examples:
- Allowed to read code, modify code, run local tests
- Not allowed to make breaking schema changes unilaterally
- Not allowed to delete files without confirmation

This is critical for preventing scope creep.

## 4. Context

What is the project context?

Examples:
- Stack: Go, Kratos, PostgreSQL, Redis
- Architecture: Clean Architecture
- Handlers must be thin; business logic lives in the biz layer

Without context, an agent may propose solutions that are technically correct but wrong for the actual codebase.

## 5. Tool Policy

If the agent has tools, be explicit:
- Which tools to use first
- Which tools to use only when needed
- When to ask for permission

Examples:
- Search files with `rg` before editing
- Read code before modifying it
- Run validation after modifications
- Never use destructive commands without explicit request

## 6. Workflow

The default process the agent should follow.

Example:
1. Understand the current state
2. Identify the scope of impact
3. Choose the smallest viable change
4. Implement the change
5. Verify
6. Report results and remaining risks

Workflow prevents output from being random.

## 7. Output Contract

What format must the agent return?

Examples:
- Reviews: findings first, each with a file reference
- Code tasks: list changed files and verification results
- Data extraction: return JSON matching a specific schema

Many perceived "model quality" issues are actually just missing output contracts.

## 8. Fallback / Uncertainty Policy

What should the agent do when uncertain?

Examples:
- If the request is ambiguous and high-impact, ask for clarification
- If data is missing but a safe assumption is possible, proceed and state the assumption
- If there is not enough data to conclude, state the confidence level explicitly

This reduces "confidently wrong" answers.

## A Minimal Prompt Using This Framework

```text
# Identity
You are a senior reviewer.

# Mission
Prioritize discovering bugs, regressions, and production risks.

# Scope
Do not comment on style unless it affects correctness.

# Context
This is a Go microservices repo using Clean Architecture.

# Workflow
Read the diff, identify risks, present findings by severity.

# Output Contract
Return findings first, each with a file reference.

# Uncertainty
If you lack enough context to conclude, state your assumptions clearly.
```

This prompt is not long, but it has structure.

## Key Takeaway

A good prompt does not have to be complex. It just needs to be **clear enough, organized enough, and consistent enough** for the agent to know how to work.

> *In the next part, we discuss a very practical technique: splitting prompts into layers to reduce chaos and improve maintainability.*
> *Continue to [Part 3 — Separating Role, Rules, Workflow, and Skill](/series/prompt-standard/part-3-layered-prompt-design/).*

{{< author-cta />}}
