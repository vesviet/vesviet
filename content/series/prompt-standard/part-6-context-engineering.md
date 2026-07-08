---
title: "Part 6 — From Prompting to Context Engineering"
date: "2026-05-09T11:00:00+07:00"
lastmod: "2026-05-09T11:00:00+07:00"
draft: false
description: "In 2026, the industry moved from prompt engineering to context engineering."
categories:
  - Engineering
tags:
  - prompt-standard
  - context-engineering
  - rag
  - mcp
weight: 7
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/prompt-engineering-benchmark-cover.png"
  alt: "Prompt Standard series: product, engineering, and ops guide for production LLM prompting"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/prompt-standard/part-6-context-engineering/"
---

## The Biggest Shift in 2026: Context Over Phrasing

If you have been writing prompts by carefully choosing words and hoping the model "gets it," you are operating on a 2024 mental model.

In 2026, the industry consensus is clear: **the quality of the context you assemble matters far more than the phrasing of your instructions.**

This shift has a name: **Context Engineering.**

## What Is Context Engineering?

Context Engineering is the discipline of designing systems that assemble the right information into the model's context window at the right time.

Instead of this:

```text
You are a financial analyst. Analyze the Q1 report.
```

A context-engineered system does this:

```text
[System Prompt: role, rules, output contract]
[Dynamically retrieved: Q1 revenue data from the ERP API]
[Dynamically retrieved: prior quarter comparison from the data warehouse]
[User query: "What are the key risk areas in Q1?"]
```

The model receives structured, verified data alongside the instruction — not a vague request to "figure it out."

## Three Pillars of Context Engineering

### 1. RAG (Retrieval-Augmented Generation)

RAG is the primary mechanism through which production systems "prompt" their models in 2026.

Instead of cramming knowledge into the prompt, you:
- store documents, data, and knowledge in a vector database or search index
- at query time, retrieve only the relevant chunks
- inject those chunks into the context window alongside the user's question

This keeps the model grounded in real data and dramatically reduces hallucination (See details on enterprise RAG pipelines in [Series: Enterprise AI Data Pipeline & GraphRAG Architecture](/series/ai-data-engineering-pipeline/)).

### 2. MCP (Model Context Protocol)

MCP is an open protocol (originally introduced by Anthropic) that standardizes how AI agents connect to external tools, databases, and enterprise systems.

Think of it as **USB-C for AI agents**: one protocol, any tool (See details on building MCP servers in [Series: MCP Engineering In Production](/series/mcp-engineering-in-production/)).

Before MCP, every agent-tool integration was custom-built. MCP provides:
- a standard discovery mechanism (the agent can ask "what tools are available?")
- a standard authentication and authorization layer
- a standard input/output contract for tool calls

For teams building internal agents, MCP means you can write a tool server once and any MCP-compatible agent can use it.

### 3. Dynamic Context Assembly

Static prompts have a fixed context. Dynamic context assembly means your system decides what to inject based on:
- the user's current query
- the agent's current state in a multi-step workflow
- what tools have already been called and what they returned
- what the agent's "working memory" contains

This is analogous to how a human expert does not read every document before answering a question — they pull the right reference at the right time.

## The Old Way vs. The New Way

| Dimension | Old Way (2024) | New Way (2026) |
| :--- | :--- | :--- |
| **Primary goal** | "Write a perfect prompt" | "Build a reliable context system" |
| **Context source** | Hardcoded in the prompt | Dynamically retrieved (RAG/MCP) |
| **Output format** | Unstructured / conversational | Schema-enforced (JSON, tables) |
| **Maintenance** | Ad-hoc edits | Version-controlled and monitored |
| **Role title** | "Prompt Engineer" | "AI Developer / Context Engineer" |

## How This Connects to Prompt Standard

Prompt Standard (Parts 1–5) gives you the **structural foundation**: identity, rules, workflow, output contract, fallback behavior.

Context Engineering gives you the **operational reality**: how to fill that structure with real, dynamic, verified data instead of static text.

A well-designed agent in 2026 combines both:
- a standardized prompt skeleton (from your `roles/`, `rules/`, `skills/` directories)
- a dynamic context assembly layer (RAG pipelines, MCP tool servers, working memory)

## Key Takeaway

The fastest way to improve agent quality is usually not to rewrite the prompt. It is to improve the quality and relevance of the context being injected.

If your agent is hallucinating, the first question should not be "is the prompt clear enough?" but rather "is the agent receiving the right data?"

> *Next, we will look at a radical approach: what if you stopped writing prompts entirely and let a framework optimize them for you?*
> *Continue to [Part 7 — Declarative Prompting with DSPy](/series/prompt-standard/part-7-declarative-prompting-dspy/).*

{{< author-cta >}}
