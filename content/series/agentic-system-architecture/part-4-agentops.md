---
title: "Part 4: AgentOps & Production Observability"
date: 2026-08-20T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Full-stack observability for multi-agent systems: OpenTelemetry distributed tracing, token FinOps accounting, latency attribution, and deadlock detection."
categories: ["Series", "DevOps", "AI Infrastructure"]
tags: ["AgentOps", "OpenTelemetry", "Distributed Tracing", "FinOps", "Prometheus"]
series: ["agentic-system-architecture"]
weight: 6
slug: "part-4-agentops"
canonicalURL: "https://tanhdev.com/series/agentic-system-architecture/part-4-agentops/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 4: AgentOps & Production Observability"
  relative: false
keywords: ["agentops observability", "opentelemetry ai agents", "token cost tracking agentops"]
---

[← Previous Chapter: Part 3: Resilient Tool Calling](/series/agentic-system-architecture/part-3-tool-calling/) | [Series Hub](/series/agentic-system-architecture/) | [Next Chapter: Part 5: Agent Evals →](/series/agentic-system-architecture/part-5-agent-evals/)

---

> **Answer-first:** AgentOps observability requires capturing entire agent execution trees (spans for LLM inference, tool invocations, and memory lookups) using OpenTelemetry AI semantic conventions to detect runaway infinite loops and attribute token costs.

---
