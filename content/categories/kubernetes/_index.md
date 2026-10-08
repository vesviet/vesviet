---
title: "Kubernetes"
description: "Kubernetes in production: GitOps with ArgoCD, in-place pod resizing, eBPF Cilium networking, and custom operators by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/kubernetes/"
cover:
  image: "/images/posts/kubernetes.jpg"
---

> **Answer-first:** The Kubernetes category provides operational engineering guides for container platforms at scale, focusing on In-Place Pod Resizing without restarts, GitOps continuous delivery with ArgoCD, custom Go operators, eBPF network security with Cilium, and cost-optimized AWS EKS Graviton deployments, detailing production cluster topologies, auto-scaling thresholds, pod disruption budgets, and kernel-level network observability.

## Core Focus Areas

- **Cluster Orchestration & Pod Scaling:** In-Place Pod Resizing (K8s v1.27+ feature gate), vertical pod autoscaling (VPA), and horizontal pod autoscaling (HPA).
- **GitOps Continuous Delivery:** Managing declarative Kubernetes manifests, multi-cluster syncing, and automated canary deployments using ArgoCD.
- **Advanced Networking & eBPF:** Cilium service mesh, kernel-level packet inspection, and custom Go Kubernetes operator development.

## Featured Series & Masterclasses

- [Cornerstone Technologies](/series/cornerstone-technologies/) — Deep infrastructure foundations: Linux cgroups, namespaces, and container runtime interfaces (CRI).

## Core Technical Essays

- [AWS EKS vs ECS: Architecture, Cost & Real-World Use Cases](/posts/aws-eks-vs-ecs-comparison/) — In-depth architectural evaluation and Graviton compute cost optimization.
- [Kubernetes In-Place Pod Resizing: Scale CPU & Memory Without Restart](/posts/kubernetes-in-place-pod-resizing-guide/) — Dynamic container vertical scaling without restarting running pods.
- [Building Custom Kubernetes Operators with eBPF, Go & Cilium](/posts/building-custom-kubernetes-operators-ebpf-golang-cilium/) — Developing controllers and automating eBPF network security rules.
- [GitOps at Scale: Kubernetes & ArgoCD for Microservices](/posts/gitops-at-scale-kubernetes-argocd-microservices/) — Declarative orchestration for 21 microservices in production clusters.
- [What's New in Argo CD 3.4 & 3.3: Cluster Pause & Upgrades](/posts/argo-cd-updates-2026/) — Progressive delivery features, automated rollouts, and cluster management.
- [Self-Hosting GraphHopper on Kubernetes with OSM Data](/posts/graphhopper-kubernetes-self-hosting-osm/) — Deploying memory-intensive geospatial routing pods with persistent volume storage.