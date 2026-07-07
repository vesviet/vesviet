---
title: "Reading Map"
date: 2026-07-07T10:00:00+07:00
lastmod: 2026-07-07T10:00:00+07:00
draft: false
description: "Curated reading map of production-grade technical essays on microservices, AI systems, commerce modernization, and platform engineering. Start here for the clearest path through the content."
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/reading-map-cover.png"
  alt: "tanhdev.com Reading Map — Production Architecture & AI Systems"
ShowToc: true
TocOpen: true
---

# Reading Map – tanhdev.com

If you're new here, this page is the fastest way to understand what I build and how I think. It groups 58 long-form essays into focused **content pillars** with explicit **Information Gain** — what this site offers that top SERP results and current LLM-generated content cannot replicate.

## Start Here (Recommended Reading Order)

1. [Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/) – zero-downtime Strangler Fig + CDC migration playbook.
2. [Deconstructing the Ecosystem: Service Details by Domain](/posts/deconstructing-ecommerce-service-details-domain/) – bounded contexts that actually survived production.
3. [Blueprint of a 21-Service E-commerce Edge](/posts/blueprint-ecommerce-microservices-architecture-diagram/) – high-level architecture + traffic/event flow.
4. [Architecting a 21-Service E-commerce Ecosystem with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) – real Kratos + Clean Architecture implementation.
5. [GitOps at Scale: Orchestrating 21 Microservices](/posts/gitops-at-scale-kubernetes-argocd-microservices/) – how we actually ship safely at this scale.

## Pillar 1 – Commerce Modernization (Magento → Composable)

**Information Gain**: Concrete zero-downtime migration patterns, exact EAV bypass SQL, cost/real-world timelines from Vietnam-based migrations that most “migrate from monolith” articles skip.

- [Why Migrate Magento to Microservices (and When You Shouldn’t)](/posts/why-migrate-magento-to-microservices/)
- [Magento Development in Vietnam 2026](/posts/magento-vietnam/)
- [Magento Still Worth Investing?](/posts/magento-still-worth-investing-2026/)
- [Exporting Magento 2 Data with Clean SQL](/posts/exporting-magento-2-data-flat-sql-nodejs/)

## Pillar 2 – Microservices Architecture (Production 21-service Blueprint)

**Information Gain**: Real boundary decisions, exact failure modes we hit, and the DDD + Kratos patterns that kept the platform stable under high concurrency.

- [Blueprint… (diagram post)](/posts/blueprint-ecommerce-microservices-architecture-diagram/)
- [Architecting 21-Service E-commerce with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Go Microservices Production Guide](/posts/go-microservices/)

## Pillar 3 – Event-driven Reliability & Observability

**Information Gain**: Battle-tested saga, idempotency, and distributed tracing patterns that survived real Double-11-scale traffic, not theoretical diagrams.

- [Mastering Event-Driven Architecture with Dapr](/posts/mastering-event-driven-architecture-dapr/)
- [Go Microservices Distributed Tracing](/posts/go-microservices-distributed-tracing-architecture/)
- Multiple pprof, goroutine leak, and profiling guides.

## Pillar 4 – Platform Operations (GitOps, Kubernetes, Edge)

**Information Gain**: Concrete ArgoCD + Kubernetes patterns at 21-service scale, EKS vs ECS real cost/control trade-offs, Cloudflare Workers zero-devops patterns.

- [GitOps at Scale with ArgoCD](/posts/gitops-at-scale-kubernetes-argocd-microservices/)
- [AWS EKS vs ECS – Practitioner’s Guide](/posts/aws-eks-vs-ecs-comparison/)
- Multiple Cloudflare D1 / Workers commerce posts.

## Pillar 5 – AI Systems & Agentic Pipelines (2026 Focus)

**Information Gain**: Production cost/latency benchmarks of prompt engineering vs LoRA fine-tuning, real agentic swarm and hybrid AI pipeline architectures that actually run reliably.

- [Architecting an Autonomous Hybrid-AI Content Pipeline](/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/)
- [Prompt Engineering vs Fine-Tuning SLM – Benchmarks](/posts/prompt-engineering-vs-fine-tuning-benchmark/)
- [AI-Native Frontend Architecture Predictions 2028](/posts/ai-native-frontend-architecture-predictions-2028/)

## Pillar 6 – Hiring & Capability (Vietnam Context)

**Information Gain**: What “senior Magento/architecture” talent in Vietnam actually looks like in 2026, concrete vetting signals beyond theme work.

- Magento Vietnam hiring series.

## Tech Radar

For fast-moving signals (new tools, AI infra, cloud-native patterns) → [/radar/](/radar/)

---

**Distribution Note (Content Manager)**: Every pillar post must have a repurposing plan before publishing (LinkedIn threads, newsletter deep-dive, YouTube script, Twitter/X technical thread). This will be formalized in the Editorial Calendar.

**Next Review**: 2026-10-01

