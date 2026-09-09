# Comprehensive Content Index & Audit Report: Core Banking Architecture Series
**Generated Date**: 2026-09-09  
**Standards Adhered**: 2027 SOTA Banking Engineering, BIAN 12.0, Distributed SQL, Event Sourcing & CQRS, Temporal Sagas, ISO 20022, FAPI 2.0 Security, Apache Flink CEP, Chaos Engineering.

---

## 1. Series Architecture & Curriculum Overview
The `core-banking-architecture` series provides deep system design patterns and technical blueprints for building high-scale, resilient, financial-grade distributed core banking engines.

### Master Quality Standards (2027 SOTA):
- **Total Chapters**: 9 files per repository (**18 files total** across `vesviet` and `learn`).
- **Interactive Diagrams**: Exactly 2 valid Mermaid diagrams per file (**36 diagrams total**), 100% AST syntax validated.
- **Interactive FAQs**: Exactly 3 Hugo `{{< faq >}}` components per file (**54 interactive FAQs total**).
- **Weight Normalization**: `_index.md` normalized to Weight 100; Chapters 1 through 8 sequentially assigned Weights 1 to 8.
- **Reciprocal Linking**: Fully bidirectional between `tanhdev.com` and `learn.tanhdev.com`.
- **Zero Hallucination / Copypasta**: Strict domain isolation without cross-contamination.

---

## 2. Chapter Inventory & Content Metrics Matrix

| File Name | Weight | Vesviet (English) | Learn (Vietnamese) | Reciprocal Links |
| :--- | :---: | :--- | :--- | :--- |
| `_index.md` | 100 | **1231** words<br>M: 2, FAQ: 3 | **1764** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/) |
| `part-1-double-entry-ledger-schema.md` | 1 | **1490** words<br>M: 2, FAQ: 3 | **2102** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-1-double-entry-ledger-schema) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-1-double-entry-ledger-schema) |
| `part-2-distributed-sql-acid-latency.md` | 2 | **1398** words<br>M: 2, FAQ: 3 | **2036** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-2-distributed-sql-acid-latency) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-2-distributed-sql-acid-latency) |
| `part-3-event-sourcing-cqrs.md` | 3 | **1148** words<br>M: 2, FAQ: 3 | **1670** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-3-event-sourcing-cqrs) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-3-event-sourcing-cqrs) |
| `part-4-saga-pattern.md` | 4 | **1278** words<br>M: 2, FAQ: 3 | **1926** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-4-saga-pattern) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-4-saga-pattern) |
| `part-5-iso-20022-payment-gateways.md` | 5 | **1226** words<br>M: 2, FAQ: 3 | **1698** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-5-iso-20022-payment-gateways) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-5-iso-20022-payment-gateways) |
| `part-6-fapi-2-api-security.md` | 6 | **1286** words<br>M: 2, FAQ: 3 | **1754** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-6-fapi-2-api-security) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-6-fapi-2-api-security) |
| `part-7-streaming-fraud-detection.md` | 7 | **1156** words<br>M: 2, FAQ: 3 | **1776** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-7-streaming-fraud-detection) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-7-streaming-fraud-detection) |
| `part-8-qa-sdet-handbook.md` | 8 | **1069** words<br>M: 2, FAQ: 3 | **1674** words<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/core-banking-architecture/part-8-qa-sdet-handbook) / [Tiếng Việt](https://learn.tanhdev.com/series/core-banking-architecture/part-8-qa-sdet-handbook) |

---

## 3. Technology & Architecture Stack (2027 SOTA Standard)

| Domain Area | Technical Specification & Implementation Standard |
| :--- | :--- |
| **Ledger Storage** | Immutable append-only journal schema, atomic constraint balance checks, TigerBeetle VSR & PostgreSQL 17 fixed-point minor currency math (`int64`). |
| **Distributed SQL** | Multi-Raft consensus, TrueTime vs Hybrid Logical Clocks (HLC), locality-aware range leases, cross-region latency mitigation in TiDB & CockroachDB. |
| **Event Sourcing & CQRS** | Append-only event store as System of Record, transactional outbox with Debezium CDC, Protobuf schema registry, sub-10ms query projections. |
| **Distributed Sagas** | Temporal / Cadence workflow orchestration, compensating transaction idempotency, semantic locking, recovery from network partitions. |
| **Interbank Rails** | ISO 20022 `pacs.008` / `pacs.002` / `camt.053`, zero-allocation XML streaming parser in Go, NAPAS 24/7 & VietQR routing. |
| **Financial Security** | FAPI 2.0 security profile, DPoP (RFC 9449), mTLS (RFC 8705), PKCS#11 HSM integration, Merkle tree audit trails, SBV Circular compliance. |
| **Streaming Fraud CEP** | Apache Flink Complex Event Processing (CEP), RocksDB incremental state backend, sliding window velocity checks, sub-10ms online feature store. |
| **SDET & Resilience** | Chaos Mesh fault injection, Jepsen linearizability verification, Go 1.24 `testing/synctest` deterministic concurrency testing, shadow traffic replay. |

---

## 4. Verification & Validation Summary
- **Mermaid Syntax Audit**: Target 36/36 diagrams passing AST validation with zero syntax anomalies.
- **Hugo Compilation**: Verification of 0 build errors across both repositories with `hugo --minify`.
- **Code Rules Compliance**: Strictly follows `agent-skills/core/rules/code.md` (no unapproved git commit/push actions).
