---
title: "PayPay Architecture: Scaling for Planet-Scale Campaigns"
date: 2026-05-05T21:00:00+07:00
lastmod: 2026-07-03T15:41:55+07:00
draft: false
weight: 150
description: "How PayPay scales for 70M users: microservices, Kafka idempotency, TiDB migration, SRE chaos engineering, campaign pre-scaling, and AI-native architecture."
ShowToc: true
TocOpen: true
---

This is a deep-dive research series exploring the backend architecture of PayPay, Japan's leading mobile payment platform with over 70 million users and 7.8 billion annual transactions. We analyze how they handle massive spike traffic during promotional campaigns, ensure strict ACID data consistency, operate a reliable GitOps platform at 100+ microservices scale, and — as of 2025 — how they are becoming AI-native.

## Series Contents

- [Executive Summary — PayPay's Engineering Evolution](/series/paypay-architecture/executive-summary/)
- [Part 1 — The Foundation: Microservices & GitOps](/series/paypay-architecture/part-1-microservices-gitops/)
- [Part 2 — Handling the Surge: Event-Driven & Kafka](/series/paypay-architecture/part-2-event-driven-kafka/)
- [Part 3 — The Data Layer: From Aurora to TiDB](/series/paypay-architecture/part-3-data-layer-tidb/)
- [Part 4 — Operations: SRE & Resilience](/series/paypay-architecture/part-4-sre-chaos-engineering/)
- [Part 5 — Surviving the Billion-Yen Campaign: Scaling for Extreme Traffic](/series/paypay-architecture/part-5-campaign-architecture/)
- [Part 6 — PayPay Goes AI-Native: LLM Hub, RAG & Agentic Finance (2025)](/series/paypay-architecture/part-6-ai-integration-2025/)

## Related Analysis

Companion research that extends specific topics from this series:

- **[PayPay Architecture: Scaling Payments to 70M Users](/posts/paypay-architecture-scaling/)** — Standalone engineering analysis of PayPay's scaling decisions: why they migrated from Aurora to TiDB, how they pre-scale for campaign spikes, and the tradeoffs in their Kafka idempotency model.

---

*Looking for a practical guide to migrating a legacy monolith to a distributed architecture? See our **[Composable Commerce Migration Series](/series/composable-commerce-migration/)** for a step-by-step production case study.*

---

## FAQ


{{< faq q="How does PayPay handle 7.8 billion transactions per year without downtime?" >}}
PayPay uses three layers of reliability: (1) microservices with circuit breakers isolate failures to individual services without cascading; (2) Kafka-backed event sourcing with idempotency keys prevents double-processing on retry; (3) campaign pre-scaling — before major promotions, PayPay pre-warms the compute fleet based on historical traffic models, avoiding cold-start latency during traffic spikes. Source: PayPay Engineering Blog (2023–2024).
{{< /faq >}}

{{< faq q="Why did PayPay migrate from Amazon Aurora to TiDB?" >}}
PayPay migrated from Aurora to TiDB to eliminate the read/write replica lag that caused stale reads during high-concurrency campaigns. TiDB's Raft-based distributed SQL provides multi-master writes with linearizable consistency — every replica is always up-to-date. The migration also removed the Aurora storage limit per cluster (128TB) and enabled horizontal scaling of the storage tier without application changes.
{{< /faq >}}

{{< faq q="What is PayPay's approach to campaign pre-scaling?" >}}
Before a major promotion (e.g., ¥10 billion cashback campaign), PayPay's SRE team runs a capacity planning model against historical campaign data: projected peak RPS, p99 latency budget per service, and expected cache miss rate. 48 hours before the campaign, they scale the compute fleet to 150–200% of projected peak and run chaos engineering drills (Chaos Monkey-style fault injection) to validate that circuit breakers and fallback paths work under synthetic load.
{{< /faq >}}
