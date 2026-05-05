---
title: "Part 4 — Operations: SRE & Resilience"
date: 2026-05-05T21:00:00+07:00
draft: false
description: "How PayPay's Platform team ensures 99.99% uptime using observability, circuit breakers, and chaos engineering."
weight: 5
---

## Designing for Failure

At PayPay's scale (100+ microservices, thousands of pods, distributed databases), hardware failure, network partitions, and pod crashes are not edge cases—they happen constantly. The architecture must embrace failure.

### Circuit Breakers & Fallbacks
If a downstream service (e.g., the external Bank Integration service) experiences an outage, it could cause cascading failures. Threads in the calling service would hang, eventually exhausting memory and taking down the whole app.

PayPay utilizes **Circuit Breakers**. If the Bank service times out repeatedly, the circuit trips. Subsequent requests fail fast, returning an error immediately rather than waiting. This protects the core systems. In some domains, a fallback response is provided (e.g., showing cached data instead of real-time data).

## Chaos Engineering

You don't know if your fallbacks and retry mechanisms actually work until they are tested in a real environment. PayPay practices **Chaos Engineering**.

The SRE (Site Reliability Engineering) team intentionally injects faults into the staging (and sometimes production) environments:
- Randomly killing Kubernetes Pods.
- Introducing artificial network latency.
- Simulating database failovers.

By constantly testing how the system reacts to these injected failures, engineers discover hidden dependencies and fix them before a real outage occurs during a critical campaign.

## Observability

To manage this complexity, comprehensive observability is mandatory.
- **Tracing:** Distributed tracing allows engineers to track a single user request as it traverses API Gateways, gRPC calls across 10 microservices, Kafka topics, and finally to the database.
- **Metrics & Alerting:** Granular metrics (TPS, Latency, Error Rates) are monitored continuously. Alerts are routed to on-call engineers long before the end-user notices a degradation in service.

This discipline in SRE and Platform Engineering is what allows PayPay to confidently execute massive marketing campaigns without fear of system collapse.
