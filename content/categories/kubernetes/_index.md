---
title: "Kubernetes"
description: "Kubernetes in production: GitOps with ArgoCD, in-place pod resizing, eBPF Cilium networking, and custom operators by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/kubernetes/"
cover:
  image: "/images/posts/kubernetes.jpg"
---

> **Answer-first:** The Kubernetes category covers production cluster operations, in-place pod resizing, Zero-Trust SPIFFE/SPIRE service mesh architectures, and custom controller development using Kubebuilder and eBPF. Engineering teams applying these techniques eliminate unnecessary container restarts, protect inter-service communications with automatic mTLS, and streamline telemetry streaming directly from the Linux kernel with less than 0.5% CPU overhead.

## Core Technical Focus Areas

- **Resource Governance & Autoscaling:** Precise CPU/Memory resource limits, HPA/VPA configuration, Karpenter node autoscaling, and in-place pod resizing.
- **Service Mesh & Zero-Trust Security:** Automatic mTLS with Istio, SPIFFE/SPIRE cryptographic workload attestation, and Cilium network policies.
- **Kernel Observability & Custom Controllers:** Kubebuilder v4 controller architecture, zero-copy BPF ringbuffers, and sidecarless ambient telemetry.

## Featured Series & Masterclasses

- [Cornerstone Technologies](/series/cornerstone-technologies/) — Zero-Trust service mesh security, cryptographic identity, and container infrastructure.

## Core Technical Essays

- [AWS EKS vs ECS: Architecture, Cost & Real-World Use Cases (2026)](/posts/aws-eks-vs-ecs-comparison/) — In-depth architectural and financial comparison of AWS container orchestration engines.
- [Kubernetes In-Place Pod Resizing: Scale CPU & Memory Without Restart](/posts/kubernetes-in-place-pod-resizing-guide/) — Dynamic vertical pod scaling eliminating disruptive pod evictions.
- [Custom Kubernetes Operators in Go: Kubebuilder & eBPF](/posts/building-custom-kubernetes-operators-ebpf-golang-cilium/) — Production guide for kernel-level telemetry controllers and zero-copy ringbuffers.
- [Zero-Trust Service Mesh Security with SPIFFE/SPIRE & Istio](/posts/zero-trust-service-mesh-security-spiffe-spire-istio-golang/) — Automated cryptographic identity issuance and mTLS enforcement.
- [OSRM Shared Memory on Kubernetes for Live Traffic Updates](/posts/osrm-shared-memory-kubernetes-live-traffic/) — IPC shared memory segment swapping for zero-downtime routing updates.