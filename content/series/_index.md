---
title: "Software Architecture & System Design Series"
description: "Deep dive into real-world software architecture, microservices, system design, and AI engineering. Technical case studies and tutorials."
lastmod: 2026-06-01T10:00:00+07:00
---

Welcome to the definitive hub for system design case studies and software architecture deep dives. Drawing from over 17 years of experience in backend engineering and building resilient platforms, these **16 in-depth series** break down complex [distributed systems](/posts/mastering-event-driven-architecture-dapr/) into digestible, actionable lessons — from e-commerce flash sales to core banking, from ride-hailing real-time systems to production AI agents.

## Exploring Real-World Software Architecture & Microservices

System design is more than just drawing boxes on a whiteboard. It's about understanding trade-offs, handling millions of requests per second, and designing for failure. In these series, we tear down the architecture of global tech giants to understand how they scale their databases, route their traffic, and process events in real time.

Whether you are preparing for a system design interview or actively architecting [microservices](/posts/architecting-21-service-ecommerce-golang-ddd/) for your organization, these resources will bridge the gap between theory and production reality.

---

## 🏗️ E-Commerce & High-Scale Systems

Scaling an e-commerce platform during flash sales is one of the toughest challenges in backend engineering. These series dissect how billion-dollar platforms survive extreme traffic spikes while maintaining data consistency.

- **[Shopee Architecture: Scaling for Flash Sales](/series/shopee-architecture/)** — A structured series on how Shopee evolved its architecture to handle extreme high concurrency during 11.11 and Flash Sales, covering microservices foundations, flash sale engines, traffic shielding, and [database scaling patterns](/posts/mysql-scaling-sharding-tidb-architecture/).

- **[E-commerce Order Allocation Architecture (Amazon, eBay)](/series/ecommerce-order-allocation/)** — An in-depth series on the order allocation problem — from Amazon's CONDOR and Anticipatory Shipping to building a Mini Order Allocation Engine with Google OR-Tools, distance matrix routing, and real-time inventory synchronization.

- **[Agentic E-commerce Search Engine Architecture](/series/agentic-ecommerce-search/)** — A hands-on series guiding you through building an Agentic Search system for e-commerce using Golang, Qdrant Hybrid Search, Redis Caching, and the Eino (CloudWeGo) Multi-Agent orchestration framework.

- **[Alipay Double 11 Architecture](/series/alipay-double-11/)** — How Alipay scaled Double 11 to 61M QPS: LDC unitization, OceanBase, RocketMQ, SOFAStack, and annual stress testing for planet-scale payment reliability.

---

## 🏦 FinTech & Core Banking

Financial systems demand the highest levels of data integrity, ACID compliance, and regulatory rigor. These series cover the intersection of distributed systems and financial engineering.

- **[Learning Path to Become a Core Banking Developer](/series/core-banking-developer/)** — Learn core banking development from the ground up: double-entry ledger, transaction processing, microservices architecture, ISO 8583/20022 standards, and building a mini banking system from scratch.

- **[PayPay Architecture: Scaling for Planet-Scale Campaigns](/series/paypay-architecture/)** — How PayPay scales for 70M users and 7.8B annual transactions: microservices, Kafka idempotency, TiDB migration, SRE chaos engineering, campaign pre-scaling, and AI-native architecture.

---

## 🚗 Real-Time & Event-Driven Architecture

When milliseconds matter, asynchronous event streaming becomes the backbone of the system. This series covers the engineering behind location-aware, latency-critical platforms.

- **[Real-Time Ride-Hailing Architecture: Uber & Grab](/series/ride-hailing-realtime-architecture/)** — How Uber and Grab handle millions of GPS updates per second: H3 geospatial indexing, Kafka event streaming, DISCO matching engine, surge pricing algorithms, and RAMEN real-time push notifications.

---

## 🤖 AI Engineering & Agentic Systems

The landscape of software development is shifting rapidly with the introduction of LLMs and autonomous agents. These series cover the full spectrum — from the mindset shift every engineer must make, to hands-on playbooks for building AI-native organizations, to the emerging discipline of reviewing, securing, and shipping AI-generated code responsibly.

- **[AI-Driven Engineer: From Code Typist to Architect](/series/ai-driven-engineer/)** — The essential roadmap for software engineers in the AI era: mindset shift from code typist to system architect, AI tool mastery, system design as a survival territory, and building AI-native applications.

- **[The AI-Driven Engineer: Enterprise Playbook](/series/ai-driven-playbook/)** — The hands-on execution playbook for applying AI to real engineering workflows: IDE setup, internal RAG, AI Platform layer, Policy-as-Code CI/CD, AI observability, and comprehensive AI-native system architecture.

- **[Vibe Coding & AI Code Review: Prototype to Production](/series/ai-code-review-vibe-coding/)** — The most urgent question of 2025–2026: how do engineers audit, secure, and ship AI-generated code to production — and how far can non-technical builders (CEOs, PMs, BAs) go with vibe coding before they hit the Production Wall?

- **[Enterprise AI Data Pipeline & GraphRAG Architecture](/series/ai-data-engineering-pipeline/)** — Build enterprise AI data pipelines that go beyond Naive RAG: GraphRAG, multimodal ingestion, semantic caching, streaming CDC, security guardrails, vLLM inference, and production Evals.

- **[Agentic System Architecture: Multi-Agent in Production](/series/agentic-system-architecture/)** — Design and operate multi-agent systems in production: topology and orchestration patterns, memory management, secure tool calling, guardrails, and AgentOps observability with Go.

---

## 🔧 Platform Engineering & DevOps

Modern AI-era platforms require new standards for tool integration, prompt management, and developer experience. These series bridge the gap between traditional DevOps and AI-native infrastructure.

- **[MCP Engineering in Production: Go SDK to Enterprise](/series/mcp-engineering-in-production/)** — Deploy MCP servers in production with Go: protocol fundamentals, OAuth 2.1 identity, gateway architecture, OWASP MCP Top 10 security, and enterprise observability — turning MCP from a code editor plugin into enterprise infrastructure.

- **[Prompt Standard: Product, Engineering & Ops Guide](/series/prompt-standard/)** — Master Prompt Standard for your whole team: foundations, versioning, Context Engineering, DSPy declarative prompting, and Production PromptOps pipelines — designed for developers, PMs, BAs, and anyone working with AI agents.

---

## 🖥️ Frontend Architecture & Edge AI

The frontend is no longer just a rendering layer — it's becoming an AI-native interface. These series explore the convergence of generative AI and user experience engineering.

- **[Roadmap: Generative UI & AI-Native Frontend Architecture](/series/generative-ui-architecture/)** — A 7-part series on building Generative UI with Astro + Svelte: replacing chatbot interfaces with dynamic AI-driven UI components, MCP integration, WebSocket streaming, and semantic caching at the edge.

- **[The SLM Playbook: Fine-Tuning & Model Distillation](/series/slm-playbook/)** — A practical guide to selecting, fine-tuning (LoRA/QLoRA), aligning (DPO/KTO/GRPO), and deploying Small Language Models on self-hosted vLLM infrastructure — optimizing TCO while retaining full technology control.

---

## 🧭 Where Should You Start?

Choosing the right starting point depends on your background and goals:

| Your Profile | Recommended Starting Series | Why |
|---|---|---|
| **New to distributed systems** | [Shopee Architecture](/series/shopee-architecture/) or [Ride-Hailing Architecture](/series/ride-hailing-realtime-architecture/) | Foundational patterns: caching, [message queues (Kafka)](/posts/mastering-event-driven-architecture-dapr/), geofencing, and database sharding |
| **Senior backend engineer** | [Core Banking Developer](/series/core-banking-developer/) or [E-Commerce Order Allocation](/series/ecommerce-order-allocation/) | Domain-specific complexity: OSRM routing matrices, Saga patterns, idempotent financial transactions |
| **Engineer adapting to AI** | [AI-Driven Engineer](/series/ai-driven-engineer/) → [AI-Driven Playbook](/series/ai-driven-playbook/) | Mindset shift first, then hands-on execution with IDE setup, RAG, and CI/CD |
| **Building AI products** | [Agentic System Architecture](/series/agentic-system-architecture/) → [MCP Engineering](/series/mcp-engineering-in-production/) | Multi-agent topology, tool calling, and production MCP infrastructure |
| **Non-technical builder (CEO/PM/BA)** | [Vibe Coding & AI Code Review](/series/ai-code-review-vibe-coding/) | Understand your limits with AI-generated code and when to hand off to engineers |
| **Data/ML engineer** | [AI Data Engineering Pipeline](/series/ai-data-engineering-pipeline/) → [SLM Playbook](/series/slm-playbook/) | Enterprise RAG, GraphRAG, fine-tuning, and model deployment at scale |
| **Frontend architect** | [Generative UI Architecture](/series/generative-ui-architecture/) | Build AI-native UIs beyond chatbots with Astro, Svelte, and MCP |

---

## Frequently Asked Questions (FAQ)

{{< faq q="Are these system design case studies based on real companies?" >}}
Yes, the case studies heavily reference the published engineering blogs and whitepapers of global companies like Shopee, Grab, Uber, Alipay, PayPay, and Amazon, combined with practical implementation details from over 17 years of building enterprise platforms.
{{< /faq >}}

{{< faq q="What is the best architecture series for senior engineers?" >}}
Senior engineers should explore the [E-Commerce Order Allocation](/series/ecommerce-order-allocation/) series and the [Core Banking Developer](/series/core-banking-developer/) guide for domain-specific complexity. For AI-era skills, the [Agentic System Architecture](/series/agentic-system-architecture/) and [MCP Engineering in Production](/series/mcp-engineering-in-production/) series cover advanced multi-agent patterns and production infrastructure.
{{< /faq >}}

{{< faq q="How are the AI series connected to each other?" >}}
The AI series follow a deliberate learning path: start with [AI-Driven Engineer](/series/ai-driven-engineer/) (mindset), then [AI-Driven Playbook](/series/ai-driven-playbook/) (execution), [Vibe Coding & AI Code Review](/series/ai-code-review-vibe-coding/) (shipping AI code safely), [AI Data Engineering Pipeline](/series/ai-data-engineering-pipeline/) (data layer), [Agentic System Architecture](/series/agentic-system-architecture/) (multi-agent design), and finally [MCP Engineering](/series/mcp-engineering-in-production/) (production infrastructure). The [SLM Playbook](/series/slm-playbook/) and [Generative UI](/series/generative-ui-architecture/) series complement this path with model deployment and frontend architecture.
{{< /faq >}}

{{< faq q="Do I need to read all 16 series?" >}}
No. Each series is self-contained and can be read independently. Use the **Where Should You Start?** table above to find the best entry point for your profile. However, series within the same category often cross-reference each other, so exploring related series will deepen your understanding.
{{< /faq >}}
