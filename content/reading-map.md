---
title: "Reading Map"
date: "2026-07-07T10:00:00+07:00"
lastmod: "2026-07-07T10:00:00+07:00"
draft: false
description: "Curated reading map of production-grade technical essays on microservices, AI systems, commerce modernization, and platform engineering."
author: "Lê Tuấn Anh"
cover:
  image: "images/posts/reading-map-cover.png"
  alt: "tanhdev.com Reading Map — Production Architecture & AI Systems"
ShowToc: true
TocOpen: true
---

# Reading Map – tanhdev.com

If you're new here, this page is the fastest way to understand what I build and how I think. It groups 57 long-form essays into focused **content pillars** with explicit **Information Gain** — what this site offers that top SERP results and current LLM-generated content cannot replicate.

## Start Here (Recommended Reading Order)

1. [Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/) – zero-downtime Strangler Fig + CDC migration playbook.
2. [Deconstructing the Ecosystem: Service Details by Domain](/posts/deconstructing-ecommerce-service-details-domain/) – bounded contexts that actually survived production.
3. [Blueprint of a 21-Service E-commerce Edge](/posts/blueprint-ecommerce-microservices-architecture-diagram/) – high-level architecture + traffic/event flow.
4. [Architecting a 21-Service E-commerce Ecosystem with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) – real Kratos + Clean Architecture implementation.
5. [GitOps at Scale: Orchestrating 21 Microservices](/posts/gitops-at-scale-kubernetes-argocd-microservices/) – how we actually ship safely at this scale.

## Pillar 1 – Commerce Modernization (Magento → Composable)

**Information Gain**: Concrete zero-downtime migration patterns, exact EAV bypass SQL, cost/real-world timelines from Vietnam-based migrations that most “migrate from monolith” articles skip.

- [Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/)
- [Why Migrate Magento to Microservices (and When You Shouldn’t)](/posts/why-migrate-magento-to-microservices/)
- [Ecommerce Architecture 2026: Overcoming Tech Debt in Composable Commerce Migration](/posts/ecommerce-architecture-composable-migration/)
- [Exporting Magento 2 Data with Clean SQL](/posts/exporting-magento-2-data-flat-sql-nodejs/)
- [Is Magento Worth It in 2026? The 2.4.9 Reality](/posts/magento-still-worth-investing-2026/)
- [Magento AI Integration: Modernize Without Rebuilding](/posts/magento-ai-integration-strategy-architecture/)
- [Deconstructing the Ecosystem: Service Details by Domain](/posts/deconstructing-ecommerce-service-details-domain/)
- [Composable Banking Architecture: From Monolith to Modular Core](/posts/composable-banking-architecture/)
- [Laravel in the AI Era: 10 Predictions for 2028](/posts/the-future-of-laravel-development-in-ai-era/)

## Pillar 2 – Microservices Architecture (Production 21-service Blueprint)

**Information Gain**: Real boundary decisions, exact failure modes we hit, and the DDD + Kratos patterns that kept the platform stable under high concurrency.

- [Blueprint of a 21-Service E-commerce Edge](/posts/blueprint-ecommerce-microservices-architecture-diagram/)
- [Architecting a 21-Service E-commerce Ecosystem with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Go Microservices Production Guide](/posts/go-microservices/)
- [Golang gRPC Microservices: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/)
- [Banking Microservices Architecture: Go, Saga & Event Sourcing](/posts/banking-microservices-architecture/)
- [Microfinance Core Banking System: Architecture & Engineering Guide](/posts/deconstructing-microfinance-core-banking-architecture/)
- [Alipay Double 11: 583,000 TPS Architecture Explained](/posts/alipay-double-11-architecture-tps/)
- [PayPay Architecture: Scaling Payments to 70M Users](/posts/paypay-architecture-scaling/)
- [Real-Time Ride-Hailing Architecture: Uber & Grab Stack](/posts/real-time-ride-hailing-architecture/)

## Pillar 3 – Event-driven Reliability, Observability & Performance

**Information Gain**: Battle-tested saga, idempotency, and distributed tracing patterns that survived real Double-11-scale traffic, not theoretical diagrams.

- [Mastering Event-Driven Architecture with Dapr Pub/Sub](/posts/mastering-event-driven-architecture-dapr/)
- [Dapr Workflow Go Tutorial: Orchestrated Saga Pattern](/posts/dapr-workflow-saga-orchestration-guide/)
- [Go Microservices Distributed Tracing (2026)](/posts/go-microservices-distributed-tracing-architecture/)
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/)
- [Goroutine Pool Patterns in Go: errgroup & Backpressure](/posts/golang-goroutine-pool-errgroup-worker/)
- [Go pprof in Kubernetes: Remote Profiling & Flame Graphs](/posts/go-pprof-kubernetes-remote-profiling/)
- [Go pprof in Kubernetes: CPU & Memory Profiling](/posts/golang-pprof-profiling-memory-cpu-tutorial/)
- [Go 1.26: Green Tea GC, Faster CGO & Goroutine Leak Detection](/posts/go-126-green-tea-gc-cgo-performance-guide/)
- [Real-Time Inventory Synchronization: Kafka, CDC & Redis for E-commerce](/posts/real-time-inventory-ecommerce-architecture/)
- [Shopee Flash Sale Architecture: Rate Limiting & Redis](/posts/shopee-flash-sale-architecture/)
- [Surge Pricing Algorithm & Spatial Indexing Architecture](/posts/surge-pricing-optimization-architecture/)
- [Order Fulfillment Algorithm: Warehouse to Last-Mile](/posts/order-fulfillment-algorithm-warehouse-last-mile/)

## Pillar 4 – Platform Operations (GitOps, Kubernetes, Edge)

**Information Gain**: Concrete ArgoCD + Kubernetes patterns at 21-service scale, EKS vs ECS real cost/control trade-offs, Cloudflare Workers zero-devops patterns.

- [GitOps at Scale: Kubernetes & ArgoCD for Microservices](/posts/gitops-at-scale-kubernetes-argocd-microservices/)
- [What's New in Argo CD 3.4 & 3.3: Cluster Pause & Upgrades](/posts/argo-cd-updates-2026/)
- [AWS EKS vs ECS: Architecture, Cost & Real-World Use Cases (2026)](/posts/aws-eks-vs-ecs-comparison/)
- [Kubernetes In-Place Pod Resizing: Scale CPU & Memory Without Restart](/posts/kubernetes-in-place-pod-resizing-guide/)
- [Zero DevOps E-commerce with Cloudflare Workers & Turborepo](/posts/cloudflare-zero-devops-ecommerce-architecture/)
- [Cloudflare D1 + Durable Objects: Build a Real-Time Cart](/posts/cloudflare-d1-durable-objects-realtime-cart/)
- [Serverless E-Commerce: Cloudflare Workers & D1 Architecture](/posts/serverless-ecommerce-cloudflare-d1/)
- [Astro on Cloudflare: Full-Stack Edge Architecture](/posts/deploying-astro-on-cloudflare-full-stack-edge-architecture/)
- [MySQL Scalability: Read Replicas, Sharding & TiDB](/posts/mysql-scalability-guide/)
- [Vitess vs GORM Sharding: MySQL Write Scaling in Go](/posts/mysql-horizontal-scaling/)
- [Replace MySQL Sharding with TiDB: Distributed SQL Migration Guide](/posts/mysql-scaling-sharding-tidb-architecture/)
- [GraphHopper Distance Matrix: Self-Host & Replace Google Maps API](/posts/graphhopper-distance-matrix-production-guide/)
- [Self-Hosting GraphHopper on Kubernetes with OSM Data](/posts/graphhopper-kubernetes-self-hosting-osm/)
- [GraphHopper vs CARTO: Order Fulfillment Routing Engine](/posts/graphhopper-distance-matrix-routing/)

## Pillar 5 – AI Systems & Agentic Pipelines (2026 Focus)

**Information Gain**: Production cost/latency benchmarks of prompt engineering vs LoRA fine-tuning, real agentic swarm and hybrid AI pipeline architectures that actually run reliably.

- [Autonomous Hybrid-AI Pipeline: Cron to State-Machine](/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/)
- [Production Agentic AI Swarm: OpenClaw & LiteLLM](/posts/deploying-autonomous-ai-swarm-openclaw-litellm/)
- [Generative UI with MCP: Architecting AI-Native Frontends](/posts/generative-ui-with-mcp-ai-native-frontend/)
- [GraphRAG vs Naive RAG: Enterprise Architecture Guide](/posts/graphrag-vs-naive-rag-enterprise-guide/)
- [Architecting Agentic E-commerce Search with Golang](/posts/agentic-ecommerce-search-golang-vector-databases/)
- [OAuth 2.1 & Prompt Versioning for Production AI Agents](/posts/production-ai-apis-oauth-versioning-meta-predictions/)
- [Prompt Engineering vs Fine-Tuning: When to Use Each (GPT-5 Era Decision Guide)](/posts/slm-fine-tune-vs-prompt-engineering/)
- [AI-Native Frontend in 2028: 10 Architecture Predictions](/posts/ai-native-frontend-architecture-predictions-2028/)
- [What is Vibe Coding? Why AI Code Review is the Future](/posts/vibe-coding-and-ai-code-review-future/)
- [LeaseInVietnam: AI-Powered Expat Rental & B2B Lead Engine](/posts/leaseinvietnam-ai-powered-expat-rental-intelligence-system/)

## Pillar 6 – Hiring & Capability (Vietnam Context)

**Information Gain**: What “senior Magento/architecture” talent in Vietnam actually looks like in 2026, concrete vetting signals beyond theme work.

- [Magento Development in Vietnam: 2026 Guide — Cost, Hiring & Upgrade](/posts/magento-vietnam/)
- [How to Technically Vet Magento Developers in Vietnam: Interview Playbook 2026](/posts/magento-developers-in-vietnam/)
- [Magento Agency & Development in Vietnam: Scoping Guide](/posts/magento-development-in-vietnam/)

## Tech Radar

For fast-moving signals (new tools, AI infra, cloud-native patterns) → [/radar/](/radar/)

---

**Distribution Note**: Every pillar post should have a repurposing plan before publishing (LinkedIn thread, newsletter deep-dive, YouTube script, or Twitter/X technical thread).

**Next Review**: 2026-10-01
