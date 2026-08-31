---
title: "Part 2: Hierarchical Memory — Episodic, Semantic & Temporal Graphs"
date: 2026-08-18T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Engineering long-term agent memory: working context buffers, vector retrieval, episodic session logs, and temporal knowledge graphs."
categories: ["Series", "AI Infrastructure", "Data Architecture"]
tags: ["Agent Memory", "GraphRAG", "Vector DB", "Mem0", "Redis"]
series: ["agentic-system-architecture"]
weight: 4
slug: "part-2-memory"
canonicalURL: "https://tanhdev.com/series/agentic-system-architecture/part-2-memory/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 2: Hierarchical Memory — Episodic, Semantic & Temporal Graphs"
  relative: false
keywords: ["agent memory hierarchy", "episodic memory ai agents", "temporal graphrag memory"]
---

[← Previous Chapter: Part 1: Swarm Topologies](/series/agentic-system-architecture/part-1-topology/) | [Series Hub](/series/agentic-system-architecture/) | [Next Chapter: Part 3: Resilient Tool Calling →](/series/agentic-system-architecture/part-3-tool-calling/)

---

> **Answer-first:** Efficient agent memory requires a 3-tier hierarchy: (1) **Working Memory** (short-term buffer in Redis), (2) **Episodic Memory** (summarized past trajectories in PostgreSQL), and (3) **Semantic Memory** (entity relationships in a Temporal Knowledge Graph).

---
