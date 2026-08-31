---
title: "Part 2: Context Engineering — Structuring Codebases for Maximum AI Precision"
date: 2026-08-18T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Structuring modern repositories for AI coding assistants: modular `.cursorrules`, schema contracts, architectural boundaries, and semantic indexing."
categories: ["Series", "Software Engineering", "Context Engineering"]
tags: ["Context Engineering", "Cursor Rules", "Prompt Engineering", "Developer Experience"]
series: ["ai-code-review-vibe-coding"]
weight: 4
slug: "part-2-context-engineering-codebase"
canonicalURL: "https://tanhdev.com/series/ai-code-review-vibe-coding/part-2-context-engineering-codebase/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 2: Context Engineering"
  relative: false
keywords: ["context engineering cursor", "modular cursor rules", "ai friendly codebase architecture"]
---

[← Previous Chapter: Part 1: Vibe Coding for Leaders](/series/ai-code-review-vibe-coding/part-1-vibe-coding-non-technical/) | [Series Hub](/series/ai-code-review-vibe-coding/) | [Next Chapter: Part 3: The AI Bug Taxonomy →](/series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/)

---

> **Answer-first:** Context Engineering is the discipline of feeding LLMs the minimum necessary, highest-signal information. Splitting monolithic prompt rules into scoped glob-matched `.cursorrules` (e.g. `domain/**/*.ts`) cuts AI context contamination by **85%**.

---
