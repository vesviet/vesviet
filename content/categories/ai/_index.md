---
title: "AI"
description: "Explore deep-dive guides on AI Engineering, RAG architecture, agentic workflows, and production LLM gateways by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/ai/"
cover:
  image: "/images/posts/ai.jpg"
---

> **Answer-first:** The AI category explores production-grade artificial intelligence systems, including Model Context Protocol (MCP) server architectures, multi-agent swarms with LiteLLM/OpenClaw, enterprise GraphRAG vs Naive RAG trade-offs, and small language model (SLM) on-device inference optimization, providing empirical benchmarks, security guardrails against prompt injection, and actionable architectural patterns for building autonomous enterprise agent swarms.

## Core Focus Areas

- **Agentic Architectures & Swarms:** Autonomous multi-agent coordination, LiteLLM gateways, fallback protocols, and sandboxed tool execution.
- **Model Context Protocol (MCP) & Generative UI:** Standardized client-server context communication, tool registries, and real-time streaming UI composition.
- **RAG & Knowledge Retrieval:** Comparing vector indexing, hybrid BM25 search, GraphRAG knowledge graphs, and custom HNSW vector databases in Go.

## Featured Series & Masterclasses

- [MCP Engineering in Production Series](/series/mcp-engineering-in-production/) — Deep dive into production Model Context Protocol servers, identity, and transport protocols.
- [Agentic System Architecture](/series/agentic-system-architecture/) — Design patterns for autonomous agent workflows, state machines, and tool dispatching.
- [Generative UI Architecture Series](/series/generative-ui-architecture/) — Dynamic UI generation with component registries, streaming JSON specs, and CSP isolation.
- [SLM Playbook: Small Language Models](/series/slm-playbook/) — On-device SLM deployment, quantization, distillation, and hybrid routing.
- [AI Code Review & Vibe Coding](/series/ai-code-review-vibe-coding/) — Context engineering, AST codebase indexing, and automated AI quality gates.
- [Agentic E-Commerce Search](/series/agentic-ecommerce-search/) — Vector embeddings, hybrid lexical-semantic retrieval, and reranking pipelines.
- [AI-Driven Playbook](/series/ai-driven-playbook/) — Operational frameworks, cost governance, DLP security, and prompt injection defense.

## Core Technical Essays

- [Generative UI with MCP: Architecting AI-Native Frontends](/posts/generative-ui-with-mcp-ai-native-frontend/) — Streaming structured UI components over MCP tool protocols.
- [Deploying Autonomous AI Swarm: OpenClaw & LiteLLM](/posts/deploying-autonomous-ai-swarm-openclaw-litellm/) — High-availability agent swarms with multi-provider fallbacks.
- [GraphRAG vs Naive RAG: Enterprise Architecture Guide](/posts/graphrag-vs-naive-rag-enterprise-guide/) — Architectural trade-offs between knowledge graphs and vector databases.
- [High-Throughput Local LLM Infrastructure: vLLM & Go Gateway](/posts/high-throughput-local-llm-infrastructure-vllm-golang-gateway/) — Optimizing PagedAttention, KV cache pooling, and low-latency proxying.
- [Building Custom Golang Vector Database Engine with HNSW](/posts/building-custom-golang-vector-database-engine-hnsw/) — Hierarchical Navigable Small World vector search implementation in pure Go.
- [Prompt Engineering vs Fine-Tuning: Decision Framework](/posts/slm-fine-tune-vs-prompt-engineering/) — Quantitative evaluation metrics for choosing in-context learning vs LoRA fine-tuning.