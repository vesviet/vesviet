# Distributed Financial Sagas & Asynchronous Reconciliation Workflows

> **Domain:** Banking & FinTech | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Orchestrated Saga`, `Temporal Workflows`, `Compensating Actions`, `End-of-Day Reconciliation`

---

## 1. Problem Statement & Operational Context
Inter-bank transfers (e.g. SWIFT, SEPA, NAPAS 24/7) span multiple financial institutions with variable settlement latencies. Distributed 2PC cannot span corporate firewalls; systems require robust asynchronous Sagas with daily reconciliation batches.

## 2. Core Architectural Invariants
1. **Idempotent Payment Workflows:** Retrying an interrupted workflow must never create duplicate charges or disbursements.
2. **Explicit Compensation Handlers:** Every forward step in the payment sequence (`Reserve`, `Authorize`, `Capture`) must have a corresponding, verified reverse step (`Unreserve`, `Void`, `Refund`).
3. **Automated T+1 Reconciliation:** Transaction logs must reconcile daily against third-party clearing files; anomalies automatically create reconciliation tickets.

## 3. Agent Retrieval Guidance
- **Apply When:** Integrating payment gateways, building inter-bank routing engines, or handling multi-currency settlements.
- **Related Articles:** `/posts/dapr-workflow-saga-orchestration-guide/`, `/posts/banking-microservices-architecture/`.
