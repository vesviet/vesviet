---
title: "Part 1 — The Foundation: Microservices & GitOps"
date: 2026-05-05T21:00:00+07:00
draft: false
description: "How PayPay structured its microservices and adopted GitOps to deploy rapidly and safely."
weight: 2
---

## Bounded Contexts & Microservices

When PayPay launched, the architecture needed to be flexible enough to iterate rapidly. They adopted a **Microservices Architecture** hosted entirely on AWS. 

Instead of a massive monolith, the system is divided into logical business domains (Bounded Contexts in Domain-Driven Design):
- **User Domain:** Authentication, profiles, KYC.
- **Wallet/Payment Domain:** Ledger, balances, transaction processing.
- **Merchant Domain:** Merchant onboarding, store management.
- **Campaign/Promo Domain:** Handling coupons, point grants, and cashback logic.

### Internal Communication: gRPC
To ensure low latency between these 100+ microservices, PayPay standardizes on **gRPC**. The strict protobuf contracts ensure backward compatibility and clear API boundaries between teams, avoiding the payload bloat and overhead of REST/JSON for internal traffic.

## Platform Engineering & GitOps

With over a hundred microservices, manual deployments or fragile Jenkins pipelines become a massive liability. PayPay's Platform team adopted **GitOps**.

### Kubernetes & ArgoCD
All services run on Kubernetes. The state of the cluster is declaratively defined in Git repositories. 
- **ArgoCD** continuously monitors the Git repository and automatically synchronizes the cluster state with the manifest files. 
- If a developer needs to scale up a service or deploy a new image, they simply merge a Pull Request updating the manifest. ArgoCD handles the rest.

### Benefits of this approach:
1. **Auditable:** Every infrastructure change is a Git commit.
2. **Reversible:** If a deployment causes an incident, rolling back is as simple as reverting the Git commit.
3. **Developer Autonomy:** Product engineers don't need `kubectl` access to production; they just interact with Git, allowing the Platform team to secure the cluster effectively.

This exact pattern mirrors the [GitOps at Scale](/posts/gitops-at-scale-kubernetes-argocd-microservices/) approach we discussed previously for handling 20+ commerce services.
