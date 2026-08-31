---
title: "Part 3A: Enterprise RAG Architecture & Codebase Vector Indexing"
date: 2026-08-19T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Architecting enterprise Retrieval-Augmented Generation (RAG) over millions of lines of proprietary code: AST chunking, hybrid BM25 + dense vector search, and reranking."
categories: ["Series", "AI Infrastructure", "Data Architecture"]
tags: ["Enterprise RAG", "Vector Search", "AST Chunking", "Hybrid Search", "Qdrant"]
series: ["ai-driven-playbook"]
weight: 7
slug: "part-3a-enterprise-rag-architecture"
canonicalURL: "https://tanhdev.com/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 3A: Enterprise RAG Architecture"
  relative: false
keywords: ["enterprise rag codebase", "ast code chunking rag", "hybrid search vector bm25"]
---

[← Previous Chapter: Part 3A: Cursor Rules](/series/ai-driven-playbook/part-3a-context-engineering-cursor-rules/) | [Series Hub](/series/ai-driven-playbook/) | [Next Chapter: Part 3B: AI Automation for Internal Ops →](/series/ai-driven-playbook/part-3b-ai-automation-internal-ops/)

---

> **Answer-first:** Codebase RAG requires **Abstract Syntax Tree (AST)** chunking to preserve function and class boundaries, combined with Hybrid Search (BM25 for exact symbols + dense embeddings for semantic search) and cross-encoder reranking.

---
