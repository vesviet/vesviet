---
title: "Part 4 — Operations: SRE & Resilience"
date: 2026-05-05T21:00:00+07:00
draft: false
description: "How PayPay SRE maintains 99.99% uptime: Datadog, OpenTelemetry, chaos engineering, circuit breakers, and a security posture forged by the 2018 incident."
weight: 5
---

## Designing for Failure

At PayPay's scale — 100+ microservices, thousands of Kubernetes pods, a distributed TiDB cluster spanning three Availability Zones, Kafka clusters under constant write pressure — hardware failure, network partitions, and pod crashes are not edge cases. They are **daily operational reality**. The architecture must not merely tolerate failures; it must be designed to **embrace and absorb them** without service disruption.

The Platform SRE team owns this problem. Their mandate is to ensure that the payment platform maintains **99.99%+ availability** — which means less than 53 minutes of downtime per year — regardless of what the underlying infrastructure does.

### Circuit Breakers & Fallbacks

In a microservices architecture, every service call is a potential failure point. PayPay's payment flow touches multiple downstream services: the core Ledger Service, Bank Integration services for linked accounts, the Fraud Detection service, and the Campaign Promo service. If any of these experiences an outage, requests will stack up — threads waiting for responses that never come, eventually exhausting thread pools and memory, causing cascading failures back through the entire call chain.

PayPay implements **Circuit Breakers** on all inter-service calls. The pattern works like an electrical circuit breaker:

```
Normal state (CLOSED): requests flow through normally
Failure threshold exceeded → circuit OPENS
OPEN state: requests fail fast (immediate error) — no waiting
After timeout → circuit goes HALF-OPEN
HALF-OPEN: limited test requests flow through
If successful → circuit CLOSES (normal operation resumes)
If failures continue → circuit OPENS again
```

When the Bank Integration service experiences an outage, the circuit breaker on the Payment Service's bank integration call trips open within seconds. Subsequent calls fail immediately (in microseconds) rather than timing out after 30 seconds. This protects the Payment Service's thread pool and keeps the core payment path — wallet-to-wallet, QR code payment — fully operational even when the bank integration layer is degraded.

In some domains, circuit breakers return **fallback responses** instead of errors: showing a cached account balance rather than real-time data, or displaying a "processing" state that resolves once the downstream service recovers. The user experience degrades gracefully rather than failing completely.

## The Observability Stack

You cannot debug what you cannot see. Managing 100+ microservices, a distributed database, and Kafka clusters requires comprehensive observability — not just monitoring, but the ability to trace a single user's payment request across every component it touches.

### Datadog: Unified Observability Platform

PayPay's primary observability platform is **Datadog**, which provides:

- **APM (Application Performance Monitoring):** Distributed tracing across all microservices, with automatic instrumentation of gRPC calls, database queries, and Kafka producer/consumer operations.
- **Infrastructure Monitoring:** CPU, memory, and disk metrics for every EC2 instance in the TiDB cluster and every Kubernetes node.
- **Log Management:** Centralized log ingestion and search across all services.
- **Alerting:** Real-time alerts routed to on-call engineers before user-visible degradation occurs.

### OpenTelemetry: Vendor-Neutral Telemetry Collection

Alongside Datadog, PayPay has adopted **OpenTelemetry (OTel)** as the standard instrumentation framework for all services. OpenTelemetry is an open-source, vendor-neutral standard for collecting metrics, logs, and traces. By instrumenting services with OpenTelemetry rather than Datadog's proprietary SDK, PayPay maintains flexibility to route telemetry to different backends without re-instrumenting code.

The OTel collector aggregates telemetry from all services and forwards it to Datadog (and potentially other backends) — providing a consistent data model across the entire distributed system.

### What the Team Actually Monitors

The key Service Level Indicators (SLIs) that the PayPay SRE team watches in real time:

| SLI | Why It Matters |
|---|---|
| TPS (Transactions Per Second) | Primary throughput signal; sudden drops indicate upstream failures |
| p99 Latency | Tail latency hides the worst user experience; p50 is misleading |
| Error rate (per service) | Circuit breaker trigger signal; SERP for cascading failures |
| Kafka consumer lag | **Leading indicator** — lag spike means payment processing is falling behind before users notice |
| TiDB write throughput | Spots data layer bottlenecks before TPS drops |
| TiKV Raft leader elections | Indicates storage layer instability |

The critical insight is the distinction between **leading and lagging indicators**. A lagging indicator (like error rate) tells you something has already gone wrong. A leading indicator (like consumer lag growing) tells you something is *about to go wrong* — while there is still time to intervene by scaling consumers, throttling upstream traffic, or rolling back a recent deployment.

### Distributed Tracing in Practice

When an engineer investigates a payment failure report, distributed tracing allows them to reconstruct the exact path of that specific user's request:

```
API Gateway (12ms)
  → Payment Service gRPC (8ms)
    → Redis idempotency check (1ms) ✓
    → Kafka produce (2ms) ✓
  → Consumer Service (delayed 340ms) ← bottleneck here
    → TiDB write (15ms) ✓
    → Campaign Service gRPC (280ms) ← second bottleneck
```

Without distributed tracing across this many services, debugging a 340ms latency spike would take hours of log correlation. With it, the bottleneck is visible in seconds.

## Chaos Engineering

Circuit breakers and fallbacks only work if they are *actually tested*. Most engineering teams discover that their fallback mechanisms are misconfigured, their circuit breaker thresholds are wrong, or their downstream dependencies have hidden coupling — at the worst possible moment: during a real outage, during a campaign, with millions of users watching.

PayPay's SRE team avoids this through **Chaos Engineering**: deliberately injecting faults into the system in a controlled way, before real outages reveal the same weaknesses.

### What They Inject

- **Random Kubernetes Pod Kills:** Terminate pods mid-request to test whether downstream services handle partial failures gracefully.
- **Network Latency Injection (tc netem):** Add artificial 500ms latency to specific service connections to test timeout configurations and circuit breaker thresholds.
- **TiDB Failover Simulation:** Take down TiKV nodes in one AZ to verify that the Raft consensus mechanism elects new leaders and that the application recovers automatically.
- **Kafka Consumer Group Restart:** Simulate a consumer group restart during peak load to test offset recovery and duplicate-processing defense.

### Environment Strategy

Chaos experiments run first in staging, where failures have no user impact. For higher confidence, selected experiments run in **production** during low-traffic windows — with an engineer on alert and a clear abort procedure. Production chaos experiments uncover dependencies that staging simply cannot reveal, because real production traffic patterns expose real coupling.

### What They Discover

The most valuable insight from chaos engineering is not confirming what works — it is discovering what unexpectedly breaks. Example scenario:

> *The Campaign Promo service fails. The Payment Service, which calls Campaign Promo to grant cashback points, should circuit-break and complete the payment without the cashback.*

Running this chaos experiment revealed that the timeout configuration on the Campaign Promo gRPC call was 30 seconds — meaning payment completion was delayed by 30 seconds per transaction during the outage. The fix: reduce the timeout to 2 seconds (acceptable for a non-critical call) and implement a fallback that grants cashback points asynchronously via a retry queue. The campaign resilience improved dramatically. This discovery would have been a production incident during the next billion-yen campaign.

## Security: From 2018 Incident to Current Posture

PayPay's security architecture is shaped by a pivotal incident in December 2018, immediately following the 10-Billion-Yen campaign launch.

**What happened:** Fraudsters obtained stolen Japanese credit card data (card numbers, expiration dates, CVV codes) from dark-market sources. PayPay's initial launch lacked account lockout controls after repeated CVV validation failures. Fraudsters ran automated scripts that iterated through stolen card data against the PayPay API — a classic credential stuffing attack — successfully registering fraudulent accounts and making purchases at merchants.

**The response:** The engineering team shipped account lockout controls — locking accounts after repeated CVV failures — within a **2-week emergency sprint**. The incident became a defining event in PayPay's engineering culture: a reminder that security is not a post-launch concern but an architectural property that must be validated before every major campaign.

**Current security posture:**

- **PCI DSS Certified:** PayPay holds Payment Card Industry Data Security Standard certification — the highest security standard in the payments industry.
- **ISMS Certified:** Information Security Management System certification confirms systematic security governance.
- **Fraud rate:** Reported at approximately **0.0015%** — significantly below the Japanese credit card industry average — achieved through 24/7 monitoring, AI-based anomaly detection, and real-time transaction risk scoring.
- **Forensics team:** Dedicated incident response and forensics capability for rapid investigation of security events.

## Load Testing as a Campaign Prerequisite

The SRE team operates a mandatory **load testing gate** before every major campaign. No campaign is allowed to launch without passing a load test that simulates its expected traffic.

The test procedure:
1. **Synthesize peak load:** Generate traffic at 2–3x the expected peak TPS using load testing tools against a production-like staging environment.
2. **Observe the full stack:** Monitor Kafka consumer lag, TiDB write throughput, circuit breaker trip counts, Kubernetes pod CPU/memory, and p99 latency across all payment-path services.
3. **Identify bottlenecks:** Any service that degrades under simulated campaign load is a mandatory fix before campaign launch.
4. **Validate chaos fallbacks:** During the load test, inject failures (kill pods, add latency) to confirm that circuit breakers and fallbacks behave exactly as designed.

This gate has prevented multiple would-be incidents. It embodies the engineering culture shift that the 2018 campaign crash initiated: from reactive firefighting to proactive resilience engineering.
