---
title: "FinTech"
description: "Financial technology architecture, core banking design, distributed Saga transactions, and double-entry ledgers by Lê Tuấn Anh."
canonicalURL: "https://tanhdev.com/categories/fintech/"
cover:
  image: "/images/posts/fintech.jpg"
---

> **Answer-first:** The FinTech category covers core banking systems engineering, immutable double-entry ledger designs, ISO 20022 financial messaging compliance, distributed transaction isolation, and high-throughput payment architectures proven under national-scale transaction volumes, examining cryptographic audit trails, regulatory compliance, reconciliation algorithms, and multi-region disaster recovery protocols designed to prevent data corruption and financial loss.

## Core Focus Areas

- **Core Banking Architecture:** Decoupling monolithic cores into event-driven services compliant with BIAN and ISO 20022 standards.
- **Double-Entry Financial Ledgers:** Designing immutable balanced debit/credit posting streams that guarantee zero fund creation or balance loss.
- **Transaction Isolation & High Concurrency:** Mitigating database row-level locking on hot merchant accounts via bucketed ledgers and batch settlement.

## Featured Series & Masterclasses

- [Core Banking Architecture: Modern Distributed Ledger](/series/core-banking-architecture/) — Comprehensive architecture guide for modern core banking engines, event-driven ledgers, and audit compliance.
- [Core Banking Developer Handbook](/series/core-banking-developer/) — Practical implementation patterns for financial engineers: ISO 20022 messaging and ledger state machines.
- [PayPay Architecture: Scaling Distributed Payments](/series/paypay-architecture/) — Scaling Japan's #1 QR payment super-app to 70M users with TiDB Multi-Raft NewSQL and asynchronous queues.
- [Alipay Double 11 Masterclass](/series/alipay-double-11/) — Unitized cell architectures and distributed consensus at 583,000 peak TPS.

## Core Technical Essays

- [Banking Microservices Architecture: Go, Saga & Event Sourcing](/posts/banking-microservices-architecture/) — Production architecture for fault-tolerant banking services.
- [Composable Banking Architecture: From Monolith to Modular Core](/posts/composable-banking-architecture/) — Deconstructing legacy financial cores into decoupled domain services.
- [Microfinance Core Banking System: Architecture & Engineering Guide](/posts/deconstructing-microfinance-core-banking-architecture/) — Building resilient loan origination, savings accounts, and repayment schedules.
- [Temporal Saga Pattern in Go: FinTech Distributed Transactions](/posts/temporal-saga-pattern-golang-distributed-transactions-guide/) — Orchestrating financial transfers with guaranteed compensation and replay safety.
- [PayPay Architecture: Scaling Payments to 70M Users](/posts/paypay-architecture-scaling/) — High-availability payment processing and database horizontal scaling.
- [Alipay Double 11: 544,000 TPS Architecture Explained](/posts/alipay-double-11-architecture-tps/) — Extreme transaction processing, memory caches, and automated multi-region failover.