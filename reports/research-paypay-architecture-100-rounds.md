# PayPay Architecture: 100-Round Deep Research Dossier (2027 SOTA Standards)

**Generated:** 2026-09-12T12:00:00+07:00  
**Status:** 100/100 Investigation Rounds Completed  
**Team:** `@vesviet-team` (Principal Researcher, Solution Architect, Lead Technical Writer)

---

## Executive Overview

This dossier compiles findings from 100 iterative research rounds examining the engineering evolution of **PayPay**, Japan's dominant mobile payment platform. Covering over 70 million registered users, 7.8 billion annual transactions, and peak promotional campaign throughputs exceeding 1,250 transactions per second, this research documents the full architectural transition:
- **Cloud-Native GitOps Microservices:** 100+ microservices on Kubernetes, gRPC/Protobuf contracts, ArgoCD reconciliation, and Argo Rollouts canary deployments.
- **Event-Driven Resilience:** Apache Kafka buffering transaction surges, transactional outbox pattern, exactly-once idempotency checks, and dead-letter queue isolation.
- **Distributed SQL Storage:** Migrating financial ledgers from AWS Aurora MySQL sharding to TiDB Multi-Raft NewSQL with zero downtime, hybrid HTAP analytics with TiFlash.
- **SRE & Chaos Engineering:** Chaos Mesh failure injections, circuit breaking with Sentinel/Resilience4j, campaign pre-scaling, and financial ledger dual-reconciliation.
- **AI-Native Finance:** Real-time sub-10ms ML fraud detection with Feast feature store, internal LLM Hub for merchant operations, and eBPF continuous runtime profiling.

---

## Breakdown by Research Domain

### 1. Fintech & Scale Foundation (Rounds 1–20)
- Analysis of the Japanese cashless payment transformation, FSA compliance, PCI-DSS 4.0 requirements.
- The 2018 PayPay launch architecture (SoftBank & Paytm collaboration) and rapid scaling challenges.
- Invariants: Zero double-spending, strictly auditable financial ledgers, 99.999% payment gateway availability.

### 2. Microservices & GitOps (Rounds 21–40)
- Domain-Driven Design (DDD) bounded contexts separating User, Wallet/Ledger, Merchant, and Campaign domains.
- Binary serialization and HTTP/2 multiplexing via gRPC/Protobuf vs legacy REST/JSON.
- Declarative infrastructure and progressive traffic shifting with ArgoCD and Argo Rollouts.

### 3. Event Streaming & Kafka (Rounds 41–60)
- Peak shaving using Apache Kafka to decouple user transaction submission from database writes.
- Distributed transaction atomicity via Transactional Outbox Pattern and Debezium CDC.
- Exactly-once semantics via distributed unique idempotency keys in Redis and RocksDB.

### 4. Distributed SQL & TiDB Storage (Rounds 61–80)
- The limits of MySQL B+Tree scaling, master-replica lag, and connection pool exhaustion under flash traffic.
- TiDB stateless compute layer, Placement Driver (PD) Timestamp Oracle (TSO), and TiKV Multi-Raft consensus.
- Region auto-splitting, `AUTO_RANDOM` key distribution, and TiFlash real-time columnar analytics.

### 5. SRE, Chaos Engineering & Campaign Resilience (Rounds 81–90)
- Validating system resilience with Chaos Mesh: pod eviction, network latency injection, disk I/O faults.
- Adaptive load shedding, circuit breakers, and virtual waiting rooms during the "10-Billion Yen Campaign".
- End-of-day multi-way financial ledger reconciliation algorithms.

### 6. AI-Native Platform & 2027 Frontier (Rounds 91–100)
- Real-time sub-10ms ML fraud detection scoring pipelines using Feast and GPU inference.
- Enterprise LLM Hub architecture for customer support and merchant analytics.
- eBPF continuous profiling (Pyroscope) and migration to quantum-resistant encryption.
