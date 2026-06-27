---
title: "Modern Core Banking Architecture: From Double-Entry Ledger to Fintech Microservices"
description: "In-depth series on modern Core Banking system architecture — Immutable Double-Entry Ledger, ACID transactions on distributed SQL, Event Sourcing, ISO 20022, FAPI 2.0, and Streaming Fraud Detection with Apache Flink."
date: 2026-06-18T11:00:00+07:00
lastmod: 2026-06-18T11:00:00+07:00
draft: false
weight: 50
slug: "core-banking-architecture"
categories: ["Series", "Core Banking", "Fintech Architecture"]
tags: ["TigerBeetle", "TiDB", "CockroachDB", "ISO 20022", "FAPI 2.0", "Apache Flink", "Event Sourcing", "Distributed SQL"]
---

# Modern Core Banking Architecture

This series is designed for **Software Architects, Senior Backend Engineers, and SDETs** who want to dive deep into the technical foundations of production-grade financial systems. We won't stop at theory — each article includes real-world database schemas, specific latency benchmarks (in ms), executable code samples, and specialized testing strategies (QA/SDET) for every topic.

References include: [TigerBeetle Docs](https://docs.tigerbeetle.com/), [Mambu GL API](https://api.mambu.com/), [PingCAP Blog](https://www.pingcap.com/), [Monzo Engineering](https://monzo.com/blog/), [OpenID FAPI 2.0 Spec](https://openid.net/specs/fapi-2_0-profile.html), [Apache Flink Docs](https://nightlies.apache.org/flink/), [Martin Kleppmann's Blog](https://martin.kleppmann.com/), and [Google Spanner Docs](https://cloud.google.com/spanner/docs/).

---

## Series Content

1. **[Part 1 — Double-Entry Ledger: Schema, Immutability & Locking](/series/core-banking-architecture/part-1-double-entry-ledger-schema/)**
2. **[Part 2 — Distributed SQL & ACID Latency: TiDB vs CockroachDB vs Spanner](/series/core-banking-architecture/part-2-distributed-sql-acid-latency/)**
3. **[Part 3 — Event Sourcing & CQRS: Immutable Ledger Design for Microservices](/series/core-banking-architecture/part-3-event-sourcing-cqrs/)**
4. **[Part 4 — Saga Pattern: Distributed Transactions Without 2PC](/series/core-banking-architecture/part-4-saga-pattern/)**
5. **[Part 5 — ISO 20022 & Payment Gateways: Parsing pacs.008, Idempotency, and Gateway Latency](/series/core-banking-architecture/part-5-iso-20022-payment-gateways/)**
6. **[Part 6 — FAPI 2.0 & API Security: DPoP, mTLS, and Sender-Constrained Tokens](/series/core-banking-architecture/part-6-fapi-2-api-security/)**
7. **[Part 7 — Streaming Fraud Detection: Apache Flink CEP, RocksDB & ML Inference](/series/core-banking-architecture/part-7-streaming-fraud-detection/)**
8. **[Part 8 — QA & SDET Handbook: Testing Distributed Financial Systems](/series/core-banking-architecture/part-8-qa-sdet-handbook/)**

---

## Who Should Read This Series?

| Role | Where to Start |
|---------|------------------|
| **Backend Engineers** entering the Fintech space | Part 1 → Part 3 |
| **Database Engineers / DBAs** interested in Distributed SQL | Part 2 |
| **Architects** designing Event-Driven systems | Part 3 → Part 4 |
| **Security Engineers** working on API Auth | Part 6 |
| **Data Engineers** building Fraud Detection | Part 7 |
| **QA / SDETs** needing testing strategies for Fintech | Part 8 |
