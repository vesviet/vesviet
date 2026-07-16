---
title: "Software Architecture & System Design Series"
description: "Deep dive into real-world software architecture, microservices, system design, and AI engineering. Technical case studies and tutorials."
lastmod: "2026-06-01T10:00:00+07:00"
cover:
  image: "images/posts/ecommerce-microservices-blueprint-cover.png"
  alt: "Software Architecture and System Design Series — Go, microservices, AI engineering, and distributed systems"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/"
ShowToc: true
TocOpen: true
---

Welcome to the definitive hub for system design case studies and software architecture deep dives. Drawing from over 17 years of experience in backend engineering and building resilient platforms, these **21 in-depth series** break down complex [distributed systems](/posts/mastering-event-driven-architecture-dapr/) into digestible, actionable lessons — from e-commerce flash sales to core banking, from ride-hailing real-time systems to production AI agents.

## Exploring Real-World Software Architecture & Microservices

System design is more than just drawing boxes on a whiteboard. It's about understanding trade-offs, handling millions of requests per second, and designing for failure. In these series, we tear down the architecture of global tech giants to understand how they scale their databases, route their traffic, and process events in real time.

Whether you are preparing for a system design interview or actively architecting [microservices](/posts/architecting-21-service-ecommerce-golang-ddd/) for your organization, these resources will bridge the gap between theory and production reality.

---

## 🏗️ E-Commerce & High-Scale Systems

Scaling an e-commerce platform during flash sales is one of the toughest challenges in backend engineering. These series dissect how billion-dollar platforms survive extreme traffic spikes while maintaining data consistency.

- **[Mastering High-Concurrency Systems]({{< ref "/series/high-concurrency-systems/_index.md" >}})** — The definitive guide to building ultra-scalable Golang architectures. Learn how to solve the C10M problem, neutralize Thundering Herds with `singleflight`, implement Transactional Outbox, and utilize Distributed Locks and Sharding.

- **[Shopee Architecture: Scaling for Flash Sales]({{< ref "/series/shopee-architecture/_index.md" >}})** — A structured series on how Shopee evolved its architecture to handle extreme high concurrency during 11.11 and Flash Sales, covering microservices foundations, flash sale engines, traffic shielding, and [database scaling patterns](/posts/mysql-scaling-sharding-tidb-architecture/).

- **[E-commerce Order Allocation Architecture (Amazon, eBay)]({{< ref "/series/ecommerce-order-allocation/_index.md" >}})** — An in-depth series on the order allocation problem — from Amazon's CONDOR and Anticipatory Shipping to building a Mini Order Allocation Engine with Google OR-Tools, distance matrix routing, and real-time inventory synchronization.

- **[Agentic E-commerce Search Engine Architecture]({{< ref "/series/agentic-ecommerce-search/_index.md" >}})** — A hands-on series guiding you through building an Agentic Search system for e-commerce using Golang, Qdrant Hybrid Search, Redis Caching, and the Eino (CloudWeGo) Multi-Agent orchestration framework.

- **[Composable Commerce Migration: Magento 2 → Microservices Golang]({{< ref "/series/composable-commerce-migration/_index.md" >}})** — The definitive playbook for escaping Magento Enterprise ($125K–200K/year): DDD bounded contexts, 3-phase Strangler Fig migration (CDC → Dual-write → Cutover), EAV schema extraction, Dapr PubSub + Transactional Outbox, Rush monorepo for 21 Go services, and GitOps with ArgoCD — drawn from a real production platform.

- **[E-Commerce Re-Architecture in Vietnam: Magento to Go Microservices]({{< ref "/series/magento-migration-vietnam/_index.md" >}})** — The CTO playbook for migrating a Magento monolith to production Go microservices with a Vietnam engineering team. Covers team vetting (Go vs PHP), phase-by-phase cost models (Vietnam vs US/EU), zero-downtime Strangler Fig execution, remote team management, and post-migration SRE operations.

- **[Alipay Double 11 Architecture]({{< ref "/series/alipay-double-11/_index.md" >}})** — How Alipay scaled Double 11 to 61M QPS: LDC unitization, OceanBase, RocketMQ, SOFAStack, and annual stress testing for planet-scale payment reliability.

---

## 🏦 FinTech & Core Banking

Financial systems demand the highest levels of data integrity, ACID compliance, and regulatory rigor. These series cover the intersection of distributed systems and financial engineering.

- **[Learning Path to Become a Core Banking Developer]({{< ref "/series/core-banking-developer/_index.md" >}})** — Learn core banking development from the ground up: double-entry ledger, transaction processing, microservices architecture, ISO 8583/20022 standards, and building a mini banking system from scratch.

- **[PayPay Architecture: Scaling for Planet-Scale Campaigns]({{< ref "/series/paypay-architecture/_index.md" >}})** — How PayPay scales for 70M users and 7.8B annual transactions: microservices, Kafka idempotency, TiDB migration, SRE chaos engineering, campaign pre-scaling, and AI-native architecture. See also: [PayPay architecture deep-dive post](/posts/paypay-architecture-scaling/).

- **[Core Banking Architecture]({{< ref "/series/core-banking-architecture/_index.md" >}})** — Kiến trúc Core Banking hiện đại: từ nguyên lý Double-Entry Ledger, ACID transactions, và tích hợp ISO 20022 đến triển khai Microservices-based Core Banking trên cloud. Đọc thêm về [microfinance core banking architecture](/posts/deconstructing-microfinance-core-banking-architecture/).

---

## 🚗 Real-Time & Event-Driven Architecture

When milliseconds matter, asynchronous event streaming becomes the backbone of the system. This series covers the engineering behind location-aware, latency-critical platforms.

- **[Real-Time Ride-Hailing Architecture: Uber & Grab]({{< ref "/series/ride-hailing-realtime-architecture/_index.md" >}})** — How Uber and Grab handle millions of GPS updates per second: H3 geospatial indexing, Kafka event streaming, DISCO matching engine, surge pricing algorithms, and RAMEN real-time push notifications.

- **[Geospatial & Routing Engine Architecture]({{< ref "/series/routing-geospatial-architecture/_index.md" >}})** — A definitive masterclass on building a high-scale Distance Matrix API and Routing Engine from scratch: algorithms, Golang implementation, GraphHopper self-hosting on Kubernetes, Mapbox visualization, Redis caching, and H3 Geospatial Indexing for [order fulfillment](/posts/order-fulfillment-algorithm-warehouse-last-mile/) and [surge pricing systems](/posts/surge-pricing-optimization-architecture/).

---

## 🤖 AI Engineering & Agentic Systems

The landscape of software development is shifting rapidly with the introduction of LLMs and autonomous agents. These series cover the full spectrum — from the mindset shift every engineer must make, to hands-on playbooks for building AI-native organizations, to the emerging discipline of reviewing, securing, and shipping AI-generated code responsibly.

- **[AI-Driven Engineer: From Code Typist to Architect]({{< ref "/series/ai-driven-engineer/_index.md" >}})** — The essential roadmap for software engineers in the AI era: mindset shift from code typist to system architect, AI tool mastery, system design as a survival territory, and building AI-native applications.

- **[The AI-Driven Engineer: Enterprise Playbook]({{< ref "/series/ai-driven-playbook/_index.md" >}})** — The hands-on execution playbook for applying AI to real engineering workflows: IDE setup, internal RAG, AI Platform layer, Policy-as-Code CI/CD, AI observability, and comprehensive AI-native system architecture.

- **[Vibe Coding & AI Code Review: Prototype to Production]({{< ref "/series/ai-code-review-vibe-coding/_index.md" >}})** — The most urgent question of 2025–2026: how do engineers audit, secure, and ship AI-generated code to production — and how far can non-technical builders (CEOs, PMs, BAs) go with vibe coding before they hit the Production Wall?

- **[Enterprise AI Data Pipeline & GraphRAG Architecture]({{< ref "/series/ai-data-engineering-pipeline/_index.md" >}})** — Build enterprise AI data pipelines that go beyond Naive RAG: GraphRAG, multimodal ingestion, semantic caching, streaming CDC, security guardrails, vLLM inference, and production Evals.

- **[Agentic System Architecture: Multi-Agent in Production]({{< ref "/series/agentic-system-architecture/_index.md" >}})** — Design and operate multi-agent systems in production: topology and orchestration patterns, memory management, secure tool calling, guardrails, and AgentOps observability with Go.

---

## 🔧 Platform Engineering & DevOps

Modern AI-era platforms require new standards for tool integration, prompt management, and developer experience. These series bridge the gap between traditional DevOps and AI-native infrastructure.

- **[MCP Engineering in Production: Go SDK to Enterprise]({{< ref "/series/mcp-engineering-in-production/_index.md" >}})** — Deploy MCP servers in production with Go: protocol fundamentals, OAuth 2.1 identity, gateway architecture, OWASP MCP Top 10 security, and enterprise observability — turning MCP from a code editor plugin into enterprise infrastructure.

- **[Prompt Standard: Product, Engineering & Ops Guide]({{< ref "/series/prompt-standard/_index.md" >}})** — Master Prompt Standard for your whole team: foundations, versioning, Context Engineering, DSPy declarative prompting, and Production PromptOps pipelines — designed for developers, PMs, BAs, and anyone working with AI agents.

- **[Modular Monolith Architecture Playbook]({{< ref "/series/modular-monolith-architecture/_index.md" >}})** — Why are 42% of enterprises (and GitHub, Shopify) abandoning Microservices to return to the Monolith? Discover the architectural decision framework, FinOps strategies to cut 90% of costs, DDD boundaries (Packwerk/Modulith), and a zero-downtime consolidation playbook.

---

## 🖥️ Frontend Architecture & Edge AI

The frontend is no longer just a rendering layer — it's becoming an AI-native interface. These series explore the convergence of generative AI and user experience engineering.

- **[Roadmap: Generative UI & AI-Native Frontend Architecture]({{< ref "/series/generative-ui-architecture/_index.md" >}})** — A 7-part series on building Generative UI with Astro + Svelte: replacing chatbot interfaces with dynamic AI-driven UI components, MCP integration, WebSocket streaming, and semantic caching at the edge.

- **[The SLM Playbook: Fine-Tuning & Model Distillation]({{< ref "/series/slm-playbook/_index.md" >}})** — A practical guide to selecting, fine-tuning (LoRA/QLoRA), aligning (DPO/KTO/GRPO), and deploying Small Language Models on self-hosted vLLM infrastructure — optimizing TCO while retaining full technology control.

---

## 🗂️ System Design Fundamentals

For engineers who want to build a rock-solid foundation in system design patterns before diving into domain-specific series.

- **[System Design Masterclass]({{< ref "/series/system-design/_index.md" >}})** — Deep-dive into system design patterns, distributed systems, and scalable architecture — from fundamentals to production-grade implementations. The essential foundation before tackling advanced series like [High-Concurrency Systems]({{< ref "/series/high-concurrency-systems/_index.md" >}}) or [Core Banking Architecture]({{< ref "/series/core-banking-architecture/_index.md" >}}).

---

## 🧭 Where Should You Start?

Choosing the right starting point depends on your background and goals:

| Your Profile | Recommended Starting Series | Why |
|---|---|---|
| **New to distributed systems** | [Shopee Architecture]({{< ref "/series/shopee-architecture/_index.md" >}}) or [Ride-Hailing Architecture]({{< ref "/series/ride-hailing-realtime-architecture/_index.md" >}}) | Foundational patterns: caching, [message queues (Kafka)](/posts/mastering-event-driven-architecture-dapr/), geofencing, and database sharding |
| **Senior backend engineer** | [High-Concurrency Systems]({{< ref "/series/high-concurrency-systems/_index.md" >}}) or [Core Banking Developer]({{< ref "/series/core-banking-developer/_index.md" >}}) | Deep technical patterns: C10M, Thundering Herd, Distributed Locks, and Idempotency |
| **Magento / e-commerce engineer** | [Composable Commerce Migration]({{< ref "/series/composable-commerce-migration/_index.md" >}}) → [Magento to Go: Vietnam Series]({{< ref "/series/magento-migration-vietnam/_index.md" >}}) | Full migration playbook: DDD decomposition, EAV schema extraction, Strangler Fig + execution with a Vietnam Go team, cost models, and post-migration SRE |
| **Engineer adapting to AI** | [AI-Driven Engineer]({{< ref "/series/ai-driven-engineer/_index.md" >}}) → [AI-Driven Playbook]({{< ref "/series/ai-driven-playbook/_index.md" >}}) | Mindset shift first, then hands-on execution with IDE setup, RAG, and CI/CD |
| **Building AI products** | [Agentic System Architecture]({{< ref "/series/agentic-system-architecture/_index.md" >}}) → [MCP Engineering]({{< ref "/series/mcp-engineering-in-production/_index.md" >}}) | Multi-agent topology, tool calling, and production MCP infrastructure |
| **Non-technical builder (CEO/PM/BA)** | [Vibe Coding & AI Code Review]({{< ref "/series/ai-code-review-vibe-coding/_index.md" >}}) | Understand your limits with AI-generated code and when to hand off to engineers |
| **Data/ML engineer** | [AI Data Engineering Pipeline]({{< ref "/series/ai-data-engineering-pipeline/_index.md" >}}) → [SLM Playbook]({{< ref "/series/slm-playbook/_index.md" >}}) | Enterprise RAG, GraphRAG, fine-tuning, and model deployment at scale |
| **Frontend architect** | [Generative UI Architecture]({{< ref "/series/generative-ui-architecture/_index.md" >}}) | Build AI-native UIs beyond chatbots with Astro, Svelte, and MCP |

---

## Frequently Asked Questions (FAQ)

{{< faq q="Are these system design case studies based on real companies?" >}}
Yes, the case studies heavily reference the published engineering blogs and whitepapers of global companies like Shopee, Grab, Uber, Alipay, PayPay, and Amazon, combined with practical implementation details from over 17 years of building enterprise platforms.
{{< /faq >}}

{{< faq q="What is the best architecture series for senior engineers?" >}}
Senior engineers should explore the [E-Commerce Order Allocation]({{< ref "/series/ecommerce-order-allocation/_index.md" >}}) series and the [Core Banking Developer]({{< ref "/series/core-banking-developer/_index.md" >}}) guide for domain-specific complexity. For AI-era skills, the [Agentic System Architecture]({{< ref "/series/agentic-system-architecture/_index.md" >}}) and [MCP Engineering in Production]({{< ref "/series/mcp-engineering-in-production/_index.md" >}}) series cover advanced multi-agent patterns and production infrastructure.
{{< /faq >}}

{{< faq q="How are the AI series connected to each other?" >}}
The AI series follow a deliberate learning path: start with [AI-Driven Engineer]({{< ref "/series/ai-driven-engineer/_index.md" >}}) (mindset), then [AI-Driven Playbook]({{< ref "/series/ai-driven-playbook/_index.md" >}}) (execution), [Vibe Coding & AI Code Review]({{< ref "/series/ai-code-review-vibe-coding/_index.md" >}}) (shipping AI code safely), [AI Data Engineering Pipeline]({{< ref "/series/ai-data-engineering-pipeline/_index.md" >}}) (data layer), [Agentic System Architecture]({{< ref "/series/agentic-system-architecture/_index.md" >}}) (multi-agent design), and finally [MCP Engineering]({{< ref "/series/mcp-engineering-in-production/_index.md" >}}) (production infrastructure). The [SLM Playbook]({{< ref "/series/slm-playbook/_index.md" >}}) and [Generative UI]({{< ref "/series/generative-ui-architecture/_index.md" >}}) series complement this path with model deployment and frontend architecture.
{{< /faq >}}

{{< faq q="Do I need to read all 21 series?" >}}
No. Each series is self-contained and can be read independently. Use the **Where Should You Start?** table above to find the best entry point for your profile. However, series within the same category often cross-reference each other, so exploring related series will deepen your understanding.
{{< /faq >}}
