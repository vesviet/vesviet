---
title: "Observability"
description: "Distributed tracing with OpenTelemetry, Go pprof CPU/memory profiling, Prometheus metrics, and system monitoring by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/observability/"
cover:
  image: "/images/posts/observability.jpg"
---

> **Answer-first:** The Observability category covers end-to-end production telemetry across distributed systems, focusing on W3C trace propagation with OpenTelemetry across gRPC and Kafka boundaries, live Go pprof profiling in Kubernetes, Prometheus SLI/SLO metrics, and AI pipeline monitoring, delivering actionable practices for flame graph analysis, distributed context injection, sampling budget governance, and alert fatigue reduction in high-scale environments.

## Core Focus Areas

- **Distributed Tracing & Context Propagation:** OpenTelemetry SDK, W3C trace context across HTTP/gRPC/Kafka boundaries, and Grafana Tempo ingestion.
- **Runtime Profiling & Diagnostic Analysis:** Go runtime `pprof`, heap allocation profiles, CPU flame graphs, and goroutine leak detection.
- **Production Metrics & Service-Level Objectives:** Prometheus metrics instrumentations, Golden Signals monitoring, and alert engineering.

## Featured Series & Masterclasses

- [Cornerstone Technologies](/series/cornerstone-technologies/) — Deep infrastructure foundations: Linux performance counters, eBPF tracing, and kernel instrumentation.

## Core Technical Essays

- [Go Microservices Distributed Tracing Architecture](/posts/go-microservices-distributed-tracing-architecture/) — Complete OpenTelemetry tracing implementation across 21 services.
- [Go pprof in Kubernetes: Remote Profiling & Flame Graphs](/posts/go-pprof-kubernetes-remote-profiling/) — Connecting live profilers to production Kubernetes pods without disruption.
- [Go pprof in Kubernetes: CPU & Memory Profiling](/posts/golang-pprof-profiling-memory-cpu-tutorial/) — Step-by-step diagnostic workflows for pinpointing high allocations.
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/) — Automated CI testing with goleak and runtime goroutine telemetry.
- [Production AI Observability: OpenTelemetry, Go & LLM Tracing](/posts/production-ai-observability-opentelemetry-golang-llm-tracing/) — Tracing token latencies, tool execution hops, and model inference costs.
- [Zero-Trust Service Mesh Security: SPIFFE/SPIRE & Istio](/posts/zero-trust-service-mesh-security-spiffe-spire-istio-golang/) — Secure mutual TLS identity tracking and service mesh observability.