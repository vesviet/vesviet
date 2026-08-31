---
title: "Part 6: Human-in-the-Loop (HITL) Gateways & Security Boundaries"
date: 2026-08-22T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Architecting asynchronous Human-in-the-Loop (HITL) approval gateways: state suspension, privilege elevation, webhook notifications, and tamper-proof audit trails."
categories: ["Series", "AI Security", "Architecture"]
tags: ["Human-in-the-Loop", "HITL", "AI Safety", "Approval Gates", "Temporal"]
series: ["agentic-system-architecture"]
weight: 8
slug: "part-6-human-in-the-loop"
canonicalURL: "https://tanhdev.com/series/agentic-system-architecture/part-6-human-in-the-loop/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 6: Human-in-the-Loop (HITL) Gateways & Security Boundaries"
  relative: false
keywords: ["human in the loop architecture", "hitl approval gateway", "agent state pausing temporal"]
---

[← Previous Chapter: Part 5: Agent Evals](/series/agentic-system-architecture/part-5-agent-evals/) | [Series Hub](/series/agentic-system-architecture/)

---

> **Answer-first:** For high-risk operations (financial fund transfers, database drop commands, production deployments), agents must pause execution state and request asynchronous human authorization through a durable workflow engine (Temporal / Dapr Workflows).

---
