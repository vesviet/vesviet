---
title: "Part 3: Resilient Tool Calling — Model Context Protocol (MCP) & Sandboxing"
date: 2026-08-19T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Standardizing tool integrations with Model Context Protocol (MCP), schema validation, idempotent execution, and kernel-level Wasm sandboxing."
categories: ["Series", "AI Security", "Software Engineering"]
tags: ["MCP", "Model Context Protocol", "Tool Calling", "Sandboxing", "Wasm"]
series: ["agentic-system-architecture"]
weight: 5
slug: "part-3-tool-calling"
canonicalURL: "https://tanhdev.com/series/agentic-system-architecture/part-3-tool-calling/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 3: Resilient Tool Calling — Model Context Protocol (MCP) & Sandboxing"
  relative: false
keywords: ["model context protocol mcp", "agent tool calling resilience", "wasm tool sandbox"]
---

[← Previous Chapter: Part 2: Hierarchical Memory](/series/agentic-system-architecture/part-2-memory/) | [Series Hub](/series/agentic-system-architecture/) | [Next Chapter: Part 4: AgentOps & Observability →](/series/agentic-system-architecture/part-4-agentops/)

---

> **Answer-first:** Standardizing agent tools on the **Model Context Protocol (MCP)** provides type-safe JSON-RPC contracts, token-budget enforcement, and secure capability boundaries. Code execution tools must run inside isolated WebAssembly (WASI 0.2) or micro-VM sandboxes.

---
