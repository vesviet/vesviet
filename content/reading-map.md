---
title: "Reading Map"
date: 2026-05-02T12:00:00+07:00
draft: false
description: "A curated reading map that groups my essays into focused clusters: commerce modernization, microservices architecture, event-driven reliability, GitOps operations, AI systems, and scale case studies."
ShowToc: true
TocOpen: true
---

If you're new here, this page is the fastest way to understand what I build and how I think. It groups my long-form posts into focused clusters. (Tech Radar lives separately at [/radar/](/radar/).)

## Start Here (5 posts)

Read these in order for a coherent end-to-end view:

1. [Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/) - a zero-downtime migration playbook (Strangler Fig, CDC, rollback).
2. [Deconstructing the Ecosystem: Service Details by Domain](/posts/deconstructing-ecommerce-service-details-domain/) - splitting a monolith into bounded contexts and domains.
3. [Blueprint of a 21-Service E-commerce Edge: Architecture & Traffic Flow](/posts/blueprint-ecommerce-microservices-architecture-diagram/) - high-level architecture and request/event flow.
4. [Architecting a 21-Service E-commerce Ecosystem with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) - Kratos + Clean Architecture, sagas, idempotency, race conditions.
5. [GitOps at Scale: Orchestrating 21 Microservices with Kubernetes & ArgoCD](/posts/gitops-at-scale-kubernetes-argocd-microservices/) - how to deploy and operate many services safely.

## Cluster 1 - Commerce Modernization (Magento -> Microservices)

Battle-tested patterns for migrating a revenue-critical commerce monolith without downtime:

- [Why You Should Migrate from Magento to Microservices (And When You Shouldn't)](/posts/why-migrate-magento-to-microservices/)
- [Moving from Magento to Microservices](/posts/moving-from-magento-to-microservices/)
- [Exporting Magento 2 Orders: Bypassing the EAV Model with Clean SQL & Node.js](/posts/exporting-magento-2-data-flat-sql-nodejs/)

## Cluster 2 - Microservices Architecture (21-service blueprint)

How a composable commerce platform is structured and why the boundaries matter:

- [Deconstructing the Ecosystem: Service Details by Domain](/posts/deconstructing-ecommerce-service-details-domain/)
- [Blueprint of a 21-Service E-commerce Edge: Architecture & Traffic Flow](/posts/blueprint-ecommerce-microservices-architecture-diagram/)
- [Architecting a 21-Service E-commerce Ecosystem with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)

## Cluster 3 - Event-driven Reliability (Dapr, Sagas, Idempotency)

The "hard parts" of distributed commerce: failure, retries, consistency, and never losing events:

- [Mastering Event-Driven Architecture with Dapr Pub/Sub](/posts/mastering-event-driven-architecture-dapr/)
- [Architecting a 21-Service E-commerce Ecosystem with Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/) (Saga + idempotency sections)

## Cluster 4 - Platform Operations (GitOps, Kubernetes)

How to make 20+ services boring to ship: repeatable deployments, rollbacks, and operational discipline:

- [GitOps at Scale: Orchestrating 21 Microservices with Kubernetes & ArgoCD](/posts/gitops-at-scale-kubernetes-argocd-microservices/)

## Cluster 5 - AI Systems (real pipelines and product thinking)

How I build agentic systems and autonomous pipelines with production constraints:

- [Architecting an Autonomous Hybrid-AI Pipeline: From Hobby Cron to Production State-Machine](/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/)
- [LeaseInVietnam: Building an AI-Powered Expat Relocation Hub with a B2B Lead Engine](/posts/leaseinvietnam-ai-powered-expat-rental-intelligence-system/)

## Cluster 6 - Hiring / Team Capability (Vietnam)

How to evaluate real Magento and platform capability beyond theme work:

- [Magento Development in Vietnam: Cost, Capability, and When It Actually Fits](/posts/magento-development-in-vietnam/)
- [Magento Developers in Vietnam: What to Look For Beyond Theme Work](/posts/magento-developers-in-vietnam/)

## Cluster 7 - Planet-scale Case Study (Alipay Double 11)

A structured research series on planet-scale throughput, reliability, and operations:

- [Alipay Double 11 Architecture](/series/alipay-double-11/)

## Tech Radar (separate lane)

Tech Radar is for fast-moving signals (AI infra, agents, cloud-native). If you prefer "what changed this week" over long-form guides, go to:

- [/radar/](/radar/)
