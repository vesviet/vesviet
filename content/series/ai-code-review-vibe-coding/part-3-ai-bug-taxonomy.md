---
title: "Part 3: The AI Bug Taxonomy — 7 Failure Modes of Generated Code"
date: 2026-08-19T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "A comprehensive taxonomy of AI-generated bugs: Phantom package hallucinations, subtle off-by-one errors, state mutation leaks, and security oversights."
categories: ["Series", "Software Engineering", "QA Engineering"]
tags: ["AI Bugs", "Code Quality", "Static Analysis", "Bug Taxonomy"]
series: ["ai-code-review-vibe-coding"]
weight: 5
slug: "part-3-ai-bug-taxonomy"
canonicalURL: "https://tanhdev.com/series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 3: The AI Bug Taxonomy"
  relative: false
keywords: ["ai code bugs taxonomy", "phantom dependencies llm", "ai generated code vulnerabilities"]
---

[← Previous Chapter: Part 2: Context Engineering](/series/ai-code-review-vibe-coding/part-2-context-engineering-codebase/) | [Series Hub](/series/ai-code-review-vibe-coding/) | [Next Chapter: Part 4: Multi-Agent Review Pipelines →](/series/ai-code-review-vibe-coding/part-4-review-pipeline-multi-agent/)

---

> **Answer-first:** AI-generated code suffers from distinct failure modes rarely seen in human junior developers: hallucinated API parameters, silent exception swallows, and plausible-looking but non-existent package imports (Package Hallucination).

---
