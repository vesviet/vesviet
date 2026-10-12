---
title: "Observability"
description: "Distributed tracing with OpenTelemetry, Go pprof CPU/memory profiling, Prometheus metrics, and system monitoring by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/observability/"
cover:
  image: "/images/posts/observability.jpg"
---

> **Answer-first:** The Observability category explores distributed tracing with OpenTelemetry, continuous CPU and memory profiling using Go pprof in Kubernetes, and Prometheus metric aggregation. Applying these observability practices enables site reliability teams to diagnose elusive memory leaks, visualize production bottleneck flame graphs, and reduce Mean Time to Resolution (MTTR) by 65% during mission-critical high-traffic incidents.

## Core Technical Focus Areas

- **Distributed Tracing (OpenTelemetry):** W3C tracecontext propagation, gRPC interceptor instrumentation, spans, and tail-based sampling.
- **Continuous Profiling & Diagnostics:** Remote Go pprof HTTP profiling in Kubernetes, CPU flame graphs, heap memory analysis, and block profiling.
- **Kernel-Level Observability:** Low-overhead eBPF kprobes, tracepoints, zero-copy ringbuffers, and sidecarless ambient telemetry.

## Core Technical Essays

- [Go Microservices Distributed Tracing with OpenTelemetry](/posts/go-microservices-distributed-tracing-architecture/) — Full instrumentation pipeline across gRPC and HTTP boundaries.
- [Go pprof in Kubernetes: Remote Profiling & Flame Graphs](/posts/go-pprof-kubernetes-remote-profiling/) — Safe production profiling on Kubernetes clusters without pod restarts.
- [Go pprof in Kubernetes: CPU & Memory Profiling Tutorial](/posts/golang-pprof-profiling-memory-cpu-tutorial/) — Step-by-step diagnostic guide for analyzing Go memory allocations and CPU consumption.
- [Goroutine Leak Detection and Fix in Production Go Services](/posts/goroutine-leak-detection-production-golang/) — Detecting and resolving leaked channels, deadlocks, and hung goroutines.
- [Custom Kubernetes Operators in Go: Kubebuilder & eBPF](/posts/building-custom-kubernetes-operators-ebpf-golang-cilium/) — Sidecarless Linux kernel telemetry controllers with <0.5% CPU overhead.