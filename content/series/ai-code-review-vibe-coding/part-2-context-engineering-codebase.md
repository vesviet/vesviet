---
title: "Context Engineering for AI Coding: AGENTS.md, Cursor Rules & RAG"
date: 2026-05-31T17:00:00+07:00
lastmod: 2026-05-31T17:00:00+07:00
draft: false
weight: 3
categories:
  - AI Engineering
  - Context Engineering
tags:
  - context engineering
  - AGENTS.md
  - CLAUDE.md
  - Cursor Rules
  - RAG
  - ContextOps
  - MCP
  - memory bank
  - codebase indexing
  - agentic coding
description: "Make AI coding agents reliable on real codebases: AGENTS.md, Cursor Rules, memory banks, RAG pipelines, ContextOps, and MCP servers. Go examples included."
aliases:
  - /series/ai-code-review-vibe-coding/part-2-context-engineering-codebase/
---

In 2025, METR — an AI safety and capability research organization — ran a rigorous randomized controlled trial. Sixteen experienced open-source developers worked on 246 real-world tasks, each randomly assigned to either use AI coding tools freely or not at all.

The result was counterintuitive: developers using AI tools were **19% slower** on complex tasks.

Before the study, those same developers predicted AI would make them **24% faster**. After completing the experiment — still believing they had gone faster — their subjective confidence remained completely unshaken.

The finding did not make headlines for the reason people assumed. The headline was not "AI is useless." The headline was this: **the bottleneck is not model quality. It is context quality.**

The developers who slowed down were spending significant time on what researchers call "verification overhead" and "workflow friction" — the effort required to correct AI output that did not understand the architectural constraints, naming conventions, existing utility functions, and established patterns of the codebase they were working in. The AI was generating code. It was generating code for an imaginary system.

This part of the series is about solving that problem.

> **Series Orientation:** This article is Part 2 of the **AI Code Review & Vibe Coding** series, detailing the context engineering practices needed to align AI generation with codebase conventions. For the preceding guide on initial tools and non-technical vibe coding, see [Part 1 — Vibe Coding & The Production Wall](/series/ai-code-review-vibe-coding/part-1-vibe-coding-non-technical/).
>
> **Scope note:** This article focuses specifically on *code-review-level* context engineering — the practices individual engineers and teams use to make AI agents produce reviewable, architecturally correct code on an existing codebase. If you are interested in *platform-level* context infrastructure — building an organizational AI Platform layer, internal RAG systems at scale, or enterprise knowledge management — see [Context Engineering: Domain-Driven Design for AI](/series/ai-driven-playbook/part-1-context-engineering-ddd/) in the AI-Driven Playbook series.

---

## The Fundamental Problem: AI Operates on a Blank Slate

Every time you open a new session with an AI coding tool, you begin from zero. The model knows nothing about:

- Your architectural decisions and why you made them
- Which patterns you have standardized on and which you are migrating away from
- What your team calls a "service" versus a "handler" versus a "controller"
- Which utility functions already exist in your shared library
- What a "successful" PR looks like in your codebase — what passes review and what gets rejected

Without this information, the AI operates like a very fast, very confident junior developer who has never seen your codebase before and will reproduce whatever pattern was most common in its training data — not whatever pattern is correct for your system.

**Context engineering** is the discipline of structuring and delivering organizational knowledge to AI agents in a form they can reliably use. It is, as the industry consensus now describes it, the "DevOps moment" for AI — the operational layer that separates experimental AI assistance from reliable production-grade AI collaboration.

---

## The Context Hierarchy: From Files to RAG Pipelines

Modern AI coding environments support context at multiple layers. Understanding the hierarchy is the foundation of any effective context strategy.

### Layer 1: Rule Files (Always-On, Zero Overhead)

Rule files are plain-text configuration files that are automatically injected into every AI interaction. They are the most important and most underutilized form of context.

**AGENTS.md (or CLAUDE.md / GEMINI.md)**

These files — stored at the root of your repository — are read by AI agents before they begin any task. They function as the agent's standing orders: architectural constraints, behavioral standards, and explicit prohibitions that apply to everything the agent does.

A well-structured `AGENTS.md` covers:

```markdown
# Project Architecture
This is a Kratos v2 microservice using Clean Architecture.
Layer rules:
- api/ = contracts only (proto + generated code)
- internal/service/ = adapter layer only, no business logic
- internal/biz/ = business logic, NO direct database calls
- internal/data/ = persistence only, GORM + PostgreSQL

# Mandatory Standards
- All context must propagate through function parameters
- Use errgroup for managed goroutines only
- SQL queries must use parameterized inputs — NEVER string concatenation
- Secrets come from environment variables or Kratos Config — NEVER hardcode

# What NOT To Do
- Do not use global state
- Do not expose raw database errors to HTTP/gRPC responses
- Do not create new patterns without checking internal/util first
```

The specificity is the point. A generic instruction like "follow clean architecture" produces inconsistent results. A specific instruction like "the biz layer must never import `gorm.DB` directly" produces deterministic ones.

**Cursor Rules (`.cursorrules`)**

Cursor's rule files work similarly to AGENTS.md but are native to the Cursor IDE. They support scoped rules — you can define different behavior for different file patterns, enforce language-specific standards, and specify which files should never be modified by the AI.

```
[rules]
name = Go Microservice Standards
glob = **/*.go

[security]
never_hardcode_secrets = true
require_parameterized_queries = true
forbid_global_state = true

[architecture]
enforce_layer_boundaries = true
require_context_propagation = true
```

The practical effect: your AI assistant now operates with your standards embedded, not as an afterthought you patch into every prompt.

### How Rule Files Prevent Architectural Leakage (A Go / Kratos Example)

Consider a request: *"Retrieve a user profile by email in the service layer."*

*   **Without a Rule File (`AGENTS.md`)**: The AI will write a GORM query directly inside the adapter service layer, bypassing Clean Architecture design:
    ```go
    // File: internal/service/user.go
    func (s *UserService) GetProfileByEmail(ctx context.Context, req *pb.GetProfileReq) (*pb.GetProfileReply, error) {
        var user biz.User
        // VIOLATION: Direct database access leaking into the service layer
        if err := s.db.WithContext(ctx).Where("email = ?", req.Email).First(&user).Error; err != nil {
            return nil, err
        }
        return &pb.GetProfileReply{Name: user.Name, Email: user.Email}, nil
    }
    ```
*   **With a Rule File (`AGENTS.md`)**: The AI enforces layer isolation, routing GORM access exclusively through the persistence domain (repository) and business use case:
    ```go
    // File: internal/service/user.go
    func (s *UserService) GetProfileByEmail(ctx context.Context, req *pb.GetProfileReq) (*pb.GetProfileReply, error) {
        // CORRECT: Service calls the biz layer orchestrator (UseCase)
        user, err := s.userUseCase.FindByEmail(ctx, req.Email)
        if err != nil {
            return nil, err
        }
        return &pb.GetProfileReply{Name: user.Name, Email: user.Email}, nil
    }
    ```

---

### Layer 2: Session Management (Active Context Control)

Even with rule files in place, long sessions degrade. This is the "context rot" phenomenon: as a session accumulates failed attempts, corrected errors, and discarded planning notes, the signal-to-noise ratio in the context window drops. The model may prioritize recent noise over foundational constraints.

**The Fresh Session Strategy**

High-performing engineering teams treat AI sessions like stateless functions: one distinct task per session. When you complete a bug fix, close the session. When you begin a new feature, open a fresh one. The operational rule: task boundaries are session boundaries.

**Structured Handovers**

When a session grows long before the task is complete, perform a structured handover:

1. Ask the AI to summarize: "What decisions have we made? What is the current state? What remains to be done?"
2. Capture that output in a `PLAN.md` or `HANDOVER.md` file in your project directory
3. Open a fresh session and load the summary alongside your core rule files

This eliminates context rot while preserving all meaningful progress.

**Compaction Commands**

Modern coding agents (Claude Code, Cursor) include `/compact` or `/summarize` commands. Use them proactively when a session runs long — before the model hits its context limit and before performance degrades. A compacted summary is a much higher-quality input than an accumulating stream of raw conversation.

---

### Layer 3: Repository Indexing (Selective Context Injection)

Rule files establish standards. Session management controls noise. Repository indexing solves a different problem: giving the AI accurate knowledge of what already exists in your codebase.

**The N+1 Discovery Problem**

Without repository context, AI agents routinely implement functions that already exist. They create new database tables that duplicate existing ones. They define error types that collide with established patterns. They import packages that violate your dependency graph. Not because they are incapable of doing better — because they do not know what already exists.

**Manual Selection vs. Full-Repo Scanning**

Most AI coding tools offer the ability to scan an entire repository automatically. This sounds valuable and is often counterproductive. A large codebase injected wholesale into context adds significant noise — irrelevant files, outdated patterns, deprecated modules. The principle: manually select only the files directly relevant to the task.

For a task modifying user authentication, the relevant context is:
- The authentication service interface
- The existing user repository implementation
- The session management middleware
- The relevant error type definitions

Not the entire codebase.

**Semantic Memory Banks**

More sophisticated teams maintain curated "memory bank" files — structured markdown documents that describe the codebase's architecture, key patterns, and important decisions in a form optimized for AI consumption:

```markdown
# Memory Bank: Authentication Domain

## Architecture
- Auth service handles JWT issuance and validation
- User identity stored in PostgreSQL via GORM, users table
- Sessions use Redis with 24h TTL (see internal/data/session_repo.go)
- MFA implemented via TOTP (internal/service/mfa_service.go)

## Key Patterns
- All auth errors return domain errors, never raw DB errors
- Rate limiting is middleware-level (internal/middleware/rate_limiter.go)
- Refresh tokens are hashed before storage (see HashToken in internal/util/crypto.go)

## Common Mistakes to Avoid
- Do NOT check password directly — always use bcrypt.CompareHashAndPassword
- Do NOT log token values — only log token IDs
- Do NOT implement new crypto — use internal/util/crypto.go exclusively
```

These memory banks are updated when significant architectural decisions are made and committed to the repository alongside code.

---

### Layer 4: RAG Pipelines (Enterprise-Scale Context)

For large engineering organizations — those with hundreds of services, mature documentation, and complex architectural standards — static rule files are insufficient. The relevant context for any given task changes too rapidly and exists in too many places to manage manually.

**Retrieval-Augmented Generation (RAG)** for code context works by:

1. Indexing your codebase, Architecture Decision Records (ADRs), runbooks, and internal documentation into a vector database
2. When an AI agent begins a task, automatically querying that index for the most semantically relevant context
3. Injecting retrieved context into the session alongside the task description

The operational result: an AI agent working on a payments feature automatically retrieves the relevant payment service interfaces, the ADR explaining why you chose the current transaction model, and the runbook for the payment provider integration — without the engineer manually curating that context.

**ADRs as Machine-Readable Judgment**

Architecture Decision Records deserve special attention. When committed in a structured format and indexed into a RAG pipeline, ADRs transform from static documentation into active constraints:

```markdown
# ADR-047: Event-Sourcing for Order State Transitions

## Status: Accepted (2025-03)
## Context
Direct state mutation of order records creates audit trail gaps and makes rollback scenarios complex.
## Decision
All order state transitions are implemented as events, appended to the events table.
The current state is derived by replaying events, not by direct column updates.
## Consequences
- New order state logic MUST add new event types, NOT modify existing ones
- Order queries require projection logic (see internal/projection/order_projector.go)
- Do NOT write directly to orders.status — always publish an OrderStateTransitioned event
```

An AI agent with access to this ADR will not generate direct `UPDATE orders SET status = ?` queries for order state changes. Without it, it almost certainly will.

**MCP Servers as Context Infrastructure**

The Model Context Protocol (MCP), released by Anthropic and now adopted across the industry, provides a standardized interface for serving context to AI agents. Rather than building bespoke integrations for each AI tool, organizations build MCP servers — lightweight services that expose specific organizational knowledge (documentation, code patterns, ticket context) through a standard protocol.

The shift this enables: context infrastructure becomes a shared organizational asset rather than a per-engineer configuration problem.

---

## The ContextOps Discipline

The industry now has a name for operating context infrastructure at organizational scale: **ContextOps**.

The operational loop is: **Ingest → Validate → Structure → Serve → Audit → Refine**.

- **Ingest**: Pull from Confluence, Notion, ADR files, runbooks, Slack architectural discussions
- **Validate**: Confirm content is accurate, up-to-date, and not contradictory
- **Structure**: Format for AI consumption — clear headers, explicit "do/do not" sections, structured code examples
- **Serve**: Via MCP servers, rule files, or RAG retrieval
- **Audit**: Monitor whether AI outputs are adhering to the context (if the agent keeps making mistakes the context prohibits, the context is either wrong or unclear)
- **Refine**: Update context based on what the audit reveals

Organizations that treat context as throwaway configuration — updated ad hoc, inconsistently formatted, stored in unindexed markdown files — experience the METR result: AI that slows teams down. Organizations that treat context as infrastructure — versioned, validated, monitored — experience meaningfully different outcomes.

---

## Practical Implementation: Starting From Zero

If your team does not have any context infrastructure today, the practical starting point is a three-step sequence:

**Step 1: Write an AGENTS.md (one afternoon)**

Focus on the highest-value content first:
- Your layer structure and the key rules for each layer
- Your top 5 "never do this" patterns (the ones your code reviewers catch most often)
- Your top 5 "always use this instead" patterns (the shared utilities and established conventions)
- Your security non-negotiables (no hardcoded secrets, parameterized queries, etc.)

**Step 2: Establish session discipline (one team discussion)**

Agree on task-based session boundaries. Add a compaction step to your team norms: before any session exceeds 20 substantive exchanges, compact and continue in a fresh session.

**Step 3: Build your first memory bank (one sprint)**

Pick your most critical domain — authentication, payments, whatever carries the highest risk. Document it in a memory bank format. Add a rule to your code review checklist: "Was the relevant memory bank file updated as part of this PR?"

The marginal improvement from even basic context infrastructure is significant. Teams that complete these three steps report substantially fewer AI-generated PRs that violate architectural standards, require significant rework, or introduce security issues the memory bank explicitly prohibits.

---

## What Good Context Engineering Looks Like in Practice

Consider a task: "Implement a new endpoint to export user transaction history as a CSV."

**Without context engineering**, an AI agent will:
- Create a new database query that joins `users` and `transactions` directly in the service layer
- Generate all transactions at once rather than streaming (OOM risk at scale)
- Write the CSV logic inline rather than using your existing `internal/util/csv_writer.go`
- Skip the rate limiting middleware your architecture requires on all export endpoints

**With effective context engineering**, the same agent:
- Knows that data access must go through the repository layer, not direct DB queries in the service
- Retrieves the existing `csv_writer.go` and uses it rather than reimplementing
- Finds the streaming pagination pattern used by `internal/service/report_service.go` and applies it
- Applies the export endpoint rate limit from `internal/middleware/` as specified in your AGENTS.md

This is not a different model. It is the same model with correct context. The output difference is substantial.

---

## Connecting to the Review Pipeline

Context engineering is not a replacement for code review. It is a force multiplier on code review. When AI agents operate with accurate, comprehensive context, the output they produce:

- Contains fewer architectural violations (the context prohibits them explicitly)
- Reuses existing utilities more consistently (the context surfaces them)
- Makes security mistakes less frequently (the context specifies the security requirements)

The result: human reviewers spend less time on pattern violations and architectural corrections, and more time on the genuinely high-value review tasks — logical correctness, edge case handling, and the security behaviors that require judgment rather than rule application.

Part 3 covers what those high-value review tasks are: the full taxonomy of AI-generated bugs, from the ones automated tools catch to the ones that only careful human review finds.

---

*Next: [Part 3 — AI Bug Taxonomy: From Silent Logic Failures to Slopsquatting](/series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/)*
