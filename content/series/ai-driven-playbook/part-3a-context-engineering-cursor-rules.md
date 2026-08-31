---
title: "Part 3A: Advanced Context Engineering & Modular Cursor Rules"
date: 2026-08-19T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Engineering modular `.cursorrules` and `.mdc` rule files with file-glob matching, architectural constraints, and deterministic anti-patterns."
categories: ["Series", "Software Engineering", "Context Engineering"]
tags: ["Cursor Rules", "MDC Rules", "Context Engineering", "Developer Experience"]
series: ["ai-driven-playbook"]
weight: 6
slug: "part-3a-context-engineering-cursor-rules"
canonicalURL: "https://tanhdev.com/series/ai-driven-playbook/part-3a-context-engineering-cursor-rules/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 3A: Advanced Context Engineering"
  relative: false
keywords: ["modular cursor rules mdc", "glob matching cursor rules", "context engineering best practices"]
---

[← Previous Chapter: Part 2: Modern AI Stack](/series/ai-driven-playbook/part-2-modern-ai-engineering-stack/) | [Series Hub](/series/ai-driven-playbook/) | [Next Chapter: Part 3A: Enterprise RAG →](/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/)

---

> **Answer-first:** Instead of maintaining monolithic flat `.cursorrules` files, modern repositories deploy scoped `.mdc` rule files matching specific directory globs (e.g. `domain/**/*.ts`), cutting context pollution by 80%.

---
