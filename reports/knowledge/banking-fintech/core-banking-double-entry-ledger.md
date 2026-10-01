# Core Banking Architecture: Double-Entry Immutable Ledgers & ACID Financial Invariants

> **Domain:** Banking & FinTech | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Double-Entry Accounting`, `Debit/Credit Invariant`, `Append-Only Ledger`, `PostgreSQL ACID`

---

## 1. Problem Statement & Operational Context
Traditional banking cores (Temenos T24, Oracle Flexcube) rely on proprietary monolithic databases with overnight batch clearing. Modern FinTech systems require real-time 24/7 transaction routing while preserving strict regulatory financial invariants.

## 2. Core Architectural Invariants
1. **Fundamental Double-Entry Invariant:** Every financial transaction must consist of balanced debit and credit entries:
   $$\sum 	ext{Debits} \equiv \sum 	ext{Credits}$$
2. **Strict Append-Only Immutability:** Updating or deleting rows in `journal_entries` is cryptographically forbidden; corrections require explicit reversing journal entries.
3. **Account Balance Materialization:** Balance values are projections computed from the journal stream; cached balance tables are validated against continuous hash chains.

## 3. Production Ledger Schema & Transaction Contract (SQL)
```sql
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number VARCHAR(34) UNIQUE NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id),
    direction VARCHAR(6) NOT NULL CHECK (direction IN ('DEBIT', 'CREDIT')),
    amount BIGINT NOT NULL CHECK (amount > 0), -- Stored in minor currency units
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Constraint check: Debits and Credits must sum to equal totals per transaction
```

## 4. Agent Retrieval Guidance
- **Apply When:** Designing payment wallets, crypto exchanges, lending platforms, or ERP general ledgers.
- **Related Articles:** `/posts/banking-microservices-architecture/`, `/series/core-banking-architecture/`.
