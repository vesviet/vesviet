---
title: "Part 7: Load Testing and Performance Tuning for Production"
description: "How to survive 20,000 requests per second. We uncover Linux Kernel network tuning, K6 Coordinated Omission, and Golang CPU bottlenecks."
date: 2026-06-15T07:20:00+07:00
lastmod: 2026-06-15T07:20:00+07:00
draft: false
tags: ["k6", "load testing", "linux", "performance", "golang", "system design"]
series: ["Routing & Geospatial Architecture"]
series_order: 7
---

Load testing is the final boss of System Design. A junior engineer runs a script, sees "20,000 RPS" with 0 errors, and assumes the system is ready. A Principal Engineer knows that unless you tune the Linux Kernel, bypass Coordinated Omission, and simulate realistic chaos, that number is a complete lie.

**Answer-first:** Load testing a routing engine is not just about testing your Go code. It is a brutal stress test of the Linux Kernel network stack (sockets, TCP reuse, SOMAXCONN), the Go runtime scheduler, and the memory footprint of your load testing tool itself.

---

## 1. The Lies Your Load Tester Tells You

### The Coordinated Omission Trap
If you configure K6 with a "Closed Model" (`constant-vus: 1000`), the Virtual Users will wait for the slow server to respond before firing the next request. If your API degrades from 50ms to 5,000ms latency, the load generator inherently slows down to "protect" the server. The test reports 0 errors, but production will crash.
**The Fix:** You MUST use an "Open Model" (`constant-arrival-rate`). This forces K6 to ruthlessly blast 10,000 requests per second precisely on schedule, exposing the true failure point of the system queue.

### Benchmarking the Cache, Not the Engine
If your K6 script uses hardcoded lat/lng coordinates, the first request is computed by Graphhopper, and the next 19,999 requests are instantly served by Redis. You are benchmarking Redis, not your routing engine.
**The Fix:** You must use K6's `SharedArray` to inject realistic, randomized GPS traces from an external JSON file, forcing Graphhopper to calculate thousands of unique paths.

### K6 Metric Cardinality OOM
When testing with dynamic, random GPS coordinates (e.g., `/api/route?lat=X&lng=Y`), K6 attempts to track every unique URL variation as a separate time-series metric in RAM. This triggers a "High Cardinality" explosion, crashing the K6 injector process with an Out of Memory (OOM) error. You MUST group requests using K6's `name` tag.

---

## 2. Linux Kernel & Go Runtime Tuning

You cannot achieve 20,000 RPS on default OS settings. The Linux kernel will protect itself by dropping your connections.

### Socket Exhaustion & `somaxconn`
When K6 hits your Golang API, you might see `Connection Refused` errors even if the Golang CPU is sitting at 10%. This happens because the OS "Listen Backlog" queue is full. You must increase the kernel parameter `sysctl -w net.core.somaxconn=65535` to allow the OS to queue more incoming TCP handshakes.

### `nf_conntrack` Silent Packet Drops
If K6 reports timeouts, CPU is low, and `somaxconn` is high, check your `dmesg` logs for `nf_conntrack: table full, dropping packet`. The kernel's firewall tracks every connection state. Under extreme load testing, this table fills up and drops packets silently. You must either increase `net.netfilter.nf_conntrack_max` or use `iptables -j NOTRACK` to bypass it.

*Now that the system is fully optimized under high load, the final step is production deployment. Head to [Part 8: Zero-Downtime Map Updates & Multi-Region Kubernetes](/series/routing-geospatial-architecture/part-8-zero-downtime-k8s/) to configure self-healing Kubernetes infrastructure, zero-downtime map updates, and multi-region routing.*

---

## FAQ: Golang Performance Bottlenecks

{{< faq q="My Golang API on Kubernetes experiences severe latency spikes and 'CPU Throttled' alerts, but CPU usage is low. Why?" >}}
This is the `GOMAXPROCS` mismatch. Go reads the host Node's CPU count (e.g., 64 cores) instead of the Pod's limit (e.g., 2 cores) and spawns 64 threads. The Linux kernel (CFS Quota) aggressively throttles this, causing massive context-switching latency. Use `go.uber.org/automaxprocs` (or upgrade to Go 1.25+) to align the Go runtime with K8s limits.
{{< /faq >}}

{{< faq q="At 10,000 RPS, my API CPU maxes out just establishing connections. How do I fix this?" >}}
Golang's `http.Transport` has a default `MaxIdleConnsPerHost = 2`. Under heavy load, it violently tears down and rebuilds 9,998 TCP connections every second, destroying CPU via TLS handshakes. You must explicitly increase `MaxIdleConnsPerHost` to 100 or higher to maintain the connection pool.
{{< /faq >}}

{{< faq q="My API crashes with 100% CPU when forwarding a 50MB GeoJSON route. How do I optimize this?" >}}
This is the **JSON Reflection Bottleneck**. If you use `json.Unmarshal` to read the response, Golang uses massive reflection and heap allocations. You MUST use `io.Copy` or `httputil.ReverseProxy` to stream the bytes directly from Graphhopper to the client, bypassing Golang's JSON parser entirely.
{{< /faq >}}

{{< faq q="I enabled Gzip compression to save bandwidth, but now my CPU is maxed out!" >}}
The standard library `compress/gzip` in Go lacks hardware SIMD optimization and burns CPU trying to compress large JSON responses. You MUST switch to `github.com/klauspost/compress/gzip` (which uses SSE 4.2 assembly instructions) or offload the compression entirely to an Nginx Edge Proxy.
{{< /faq >}}
