---
title: "Double-Entry Ledger: Immutable Schema & Concurrency"
date: 2026-06-18T11:00:00+07:00
lastmod: 2026-07-03T15:41:55+07:00
draft: false
description: "Real-world double-entry ledger schema: TigerBeetle Zig 128-byte struct, PostgreSQL NUMERIC(18,4), invariant enforcement triggers, and locking strategies for 1M TPS."
weight: 1
series: ["core-banking-architecture"]
keywords: ["double entry ledger database schema", "TigerBeetle architecture", "pessimistic vs optimistic locking ledger", "Mambu GL schema"]
author: "Tuan Anh"
schema: ["Article", "TechArticle", "FAQPage"]
cover:
  image: "/images/posts/banking-microservices-cover.png"
  alt: "Modern Core Banking Architecture series: Go, event sourcing, Saga pattern, and distributed ledger"
  relative: false
---

> **Series (Part 1 of 8):** This series dives deep into production-grade Core Banking architecture. This article focuses on the most critical foundation: schema design for a Double-Entry Ledger and concurrency locking strategies. If you are new to Core Banking, please read the [Core Banking Developer Series](/series/core-banking-developer/) first.

> **⚠️ Note:** This article is synthesized from official documentation, engineering blogs, and published benchmark papers. The latency figures and schema designs reflect the source material at the time of writing. Always verify with your team's architect or lead engineer before applying them to a production system.


## What is a Double-Entry Ledger Database Schema?

A database schema for a double-entry ledger requires immutability, ACID guarantees, and precise locking mechanisms to avoid race conditions. Modern systems like TigerBeetle eliminate traditional pessimistic locking by utilizing a single-threaded state machine, achieving 1,000,000 TPS on a single CPU core. For scaling into a distributed environment, see [Part 2 — Distributed SQL & ACID Latency](/series/core-banking-architecture/part-2-distributed-sql-acid-latency/) for a comparison between TiDB, CockroachDB, and Spanner.


---

## The Core Problem: Why is a Ledger Schema More Complex Than You Think?

Most developers entering Fintech think a ledger simply consists of two operations:

```sql
UPDATE accounts SET balance = balance - 1000000 WHERE id = 'A';
UPDATE accounts SET balance = balance + 1000000 WHERE id = 'B';
```

This is a **completely flawed design** for three reasons:

1. **No audit trail**: It is impossible to know which transactions formed the current balance.
2. **Not immutable**: Any `UPDATE` destroys accounting history — violating GAAP standards and Central Bank regulations.
3. **Race condition**: Two concurrent transactions reading the same balance → overwriting each other → double-spend.

The correct standard is to write **journal entries** into a ledger table, where each transaction creates at least two Debit/Credit entries (double-entry), and the sum must equal zero.

---

## Mambu GL Schema: A Real-World Production Schema

[Mambu](https://api.mambu.com/) — one of the leading Core Banking SaaS platforms — designs their GL (General Ledger) table with the following principles:

**Mandatory columns in `gl_journal_entries`:**

| Column | Type | Meaning |
|--------|------|---------|
| `entryid` | `BIGINT AUTO_INCREMENT` | Sequential primary key |
| `encodedkey` | `VARCHAR(36) UNIQUE` | Immutable UUID of the entry — never changes |
| `transactionid` | `VARCHAR(36)` | Link to the origin transaction |
| `accountkey` | `VARCHAR(36)` | The affected account |
| `type` | `ENUM('DEBIT','CREDIT')` | Entry type |
| `amount` | `DECIMAL(18,4)` | The amount (non-negative) |
| `reversalentrykey` | `VARCHAR(36) NULL` | Points back to the origin entry if this is a reversal |
| `created_at` | `TIMESTAMPTZ` | Immutable timestamp |

**Mambu's Immutability Principle**: Once an `entryid` is written to the database, no `UPDATE` or `DELETE` is permitted. To correct a mistake, the system creates a **new reversal entry** pointing to the flawed entry's `encodedkey` via the `reversalentrykey` column. This is the true mechanism of an audit trail.

---

## TigerBeetle: The 1,000,000 TPS Ledger Architecture

[TigerBeetle](https://docs.tigerbeetle.com/concepts/performance/) is a purpose-built database for financial ledgers, written in Zig. It achieves **1,000,000 TPS on a single CPU core** by completely avoiding database locking through a single-threaded state machine architecture.

### TigerBeetle Account Struct (128 bytes, C ABI aligned)

```zig
// TigerBeetle Account Struct — exactly 128 bytes, CPU cache-line aligned
pub const Account = extern struct {
    id: u128,                 // 16 bytes: Unique identifier (UUIDv4/v7 or custom monotonic ID)
    debits_pending: u128,     // 16 bytes: Amount reserved in pending transfers
    debits_posted: u128,      // 16 bytes: Total debit fully committed
    credits_pending: u128,    // 16 bytes: Amount reserved on the credit side
    credits_posted: u128,     // 16 bytes: Total credit fully committed
    user_data_128: u128,      // 16 bytes: Custom metadata (e.g., customer_id)
    user_data_64: u64,        //  8 bytes: Custom metadata
    user_data_32: u32,        //  4 bytes: Custom metadata
    reserved: u32 = 0,        //  4 bytes: Padding to hit exactly 128 bytes
    ledger: u32,              //  4 bytes: Grouping accounts by currency / asset type
    code: u16,                //  2 bytes: Chart of Accounts code (e.g., 1001 = cash)
    flags: u16,               //  2 bytes: Business rules flags
    timestamp: u64,           //  8 bytes: Nanosecond timestamp (managed by the cluster)
};

// TigerBeetle Transfer Struct — 128 bytes, same alignment
pub const Transfer = extern struct {
    id: u128,                 // 16 bytes: Unique transfer ID
    debit_account_id: u128,   // 16 bytes: Account being debited
    credit_account_id: u128,  // 16 bytes: Account being credited
    amount: u128,             // 16 bytes: Asset amount to transfer
    pending_id: u128,         // 16 bytes: ID of the pending transfer (used in two-phase)
    user_data_128: u128,      // 16 bytes: Custom metadata
    user_data_64: u64,        //  8 bytes: Custom metadata
    user_data_32: u32,        //  4 bytes: Custom metadata
    timeout: u32 = 0,         //  4 bytes: Auto-void timeout in seconds
    ledger: u32,              //  4 bytes: Must match the ledger of both accounts
    code: u16,                //  2 bytes: Custom category code
    flags: u16,               //  2 bytes: Config flags (pending, post_pending, void_pending)
    timestamp: u64,           //  8 bytes: Nanosecond timestamp upon commit to log
};
```

**Why 128 bytes?** So each struct occupies exactly one CPU cache line (64–128 bytes depending on architecture), maximizing throughput during batch processing. TigerBeetle batches up to **8,190 requests** per call to kernel I/O (`io_uring`).

### Two-Phase Transfer: The Real Math

When a `Transfer` has the `pending` flag, the database reserves the funds but does not post them:

**Phase 1 — Pending (Reserve):**
```
debit_account.debits_pending  += transfer.amount
credit_account.credits_pending += transfer.amount
```

**Phase 2A — Post Pending (Successful Commit):**
```
debit_account.debits_pending  -= transfer.amount
debit_account.debits_posted   += transfer.amount
credit_account.credits_pending -= transfer.amount
credit_account.credits_posted  += transfer.amount
```

**Phase 2B — Void Pending (Cancellation):**
```
debit_account.debits_pending  -= transfer.amount
credit_account.credits_pending -= transfer.amount
```

---

## PostgreSQL DDL: Double-Entry Schema With Enforcement

For a system using PostgreSQL (instead of TigerBeetle), here is a production-grade schema:

```sql
-- Accounts Table: Defines accounts within the Chart of Accounts
CREATE TABLE accounts (
    id              UUID PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    currency        CHAR(3) NOT NULL,           -- ISO 4217: 'VND', 'USD', 'JPY'
    debit_balance   NUMERIC(18, 4) DEFAULT 0.0000 NOT NULL 
                    CHECK (debit_balance >= 0),
    credit_balance  NUMERIC(18, 4) DEFAULT 0.0000 NOT NULL 
                    CHECK (credit_balance >= 0),
    type            VARCHAR(20) NOT NULL 
                    CHECK (type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactions Table: Header for each group of journal entries
CREATE TABLE transactions (
    id              UUID PRIMARY KEY,
    description     VARCHAR(255),
    posted_at       TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Entries Table: Individual Debit/Credit lines (the "legs" of a transaction)
CREATE TABLE entries (
    id              UUID PRIMARY KEY,
    transaction_id  UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    account_id      UUID NOT NULL REFERENCES accounts(id),
    amount          NUMERIC(18, 4) NOT NULL CHECK (amount <> 0),
    direction       VARCHAR(6) NOT NULL CHECK (direction IN ('DEBIT', 'CREDIT')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes to speed up balance lookups
CREATE INDEX idx_entries_account_id     ON entries(account_id);
CREATE INDEX idx_entries_transaction_id ON entries(transaction_id);

-- Trigger: Enforce balance invariant — total DEBIT must = total CREDIT in the same transaction
CREATE OR REPLACE FUNCTION verify_transaction_balance()
RETURNS TRIGGER AS $$
DECLARE
    balance_sum NUMERIC(18, 4);
BEGIN
    SELECT COALESCE(
        SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END),
        0
    )
    INTO balance_sum
    FROM entries
    WHERE transaction_id = NEW.transaction_id;

    IF balance_sum <> 0 THEN
        RAISE EXCEPTION 
            'Transaction unbalanced: SUM(DEBIT) - SUM(CREDIT) = %. Transaction ID: %',
            balance_sum, NEW.transaction_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verify_balance
AFTER INSERT ON entries
FOR EACH ROW EXECUTE FUNCTION verify_transaction_balance();
```

> **Note:** Always use `NUMERIC(18, 4)` or `BIGINT` (for the smallest denomination, e.g., cents). **Never use `FLOAT` or `DOUBLE`** — floating-point precision errors will accumulate over millions of transactions and cause the ledger to unbalance.

---

## Balance Invariants: Three Mathematical Rules

TigerBeetle enforces three invariants on every transfer:

**1. Basic Rule (non-negative):**
$$\text{debits\_pending} + \text{debits\_posted} \ge 0$$
$$\text{credits\_pending} + \text{credits\_posted} \ge 0$$

**2. Asset Account Rule (customer accounts — cannot overdraw beyond credit):**
$$\text{debits\_pending} + \text{debits\_posted} \le \text{credits\_posted}$$

**3. Liability Account Rule (bank capital — cannot borrow beyond capital):**
$$\text{credits\_pending} + \text{credits\_posted} \le \text{debits\_posted}$$

---

## Concurrency Locking: Pessimistic vs Optimistic vs TigerBeetle

### Real-World Benchmarks

| Strategy | TPS (low contention) | TPS (high contention, 1000+ TPS) | Risks |
|----------|---------------------|----------------------------------|--------|
| **Pessimistic Locking** (SELECT FOR UPDATE) | ~5,000 TPS | <100 TPS (deadlock risk) | Deadlocks if not locked in order |
| **Optimistic Locking** (version column) | ~20,000 TPS | Retry rate >90% | Retry storms, livelocks |
| **TigerBeetle Single-Threaded** | 1,000,000 TPS | 1,000,000 TPS (unchanged) | No locking — sequential by design |

Source: [TigerBeetle Concepts](https://docs.tigerbeetle.com/concepts/performance/), ACM benchmark papers.

### PostgreSQL Pessimistic Locking (Production Pattern)

```sql
BEGIN;

-- Lock both accounts in ID order to avoid deadlocks
-- Rule: ALWAYS lock the account with the smaller ID first
SELECT id, debit_balance, credit_balance
FROM accounts
WHERE id IN ('account-A', 'account-B')
ORDER BY id  -- Deterministic order — prevents deadlocks
FOR UPDATE;

-- Check if balance is sufficient
-- INSERT into transactions
-- INSERT into entries (Debit and Credit)
-- UPDATE account balances

COMMIT;
```

### Why Doesn't TigerBeetle Need Locking?

TigerBeetle uses a **single-threaded state machine** — the entire ledger runs on a single CPU core with `io_uring` for async I/O. No concurrent writes, no locks, no deadlocks. All requests are **batched** and processed sequentially with deterministic execution.

---

## Lessons from Production Systems

**Immutable rules for a Double-Entry Ledger:**

1. **Only INSERT, never UPDATE/DELETE** on committed ledger entries.
2. **Every transaction must be atomic** — all entries commit together or rollback together.
3. **Store money as integers** (BIGINT or NUMERIC) — never FLOAT.
4. **Verify invariants periodically** using reconciliation queries.
5. **Lock in deterministic order** when pessimistically locking multiple accounts.

**Health check query for the ledger (run every 5 minutes):**

```sql
-- Detect any transaction where SUM(DEBIT) != SUM(CREDIT)
SELECT
    transaction_id,
    SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END) AS discrepancy
FROM entries
GROUP BY transaction_id
HAVING SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END) <> 0;

-- Expected result: 0 rows. If rows exist -> trigger P1 alert immediately.
```

---

## QA & SDET Testing Strategy

### Test 1: Concurrent Double-Spend Prevention

```go
// Run 100 concurrent goroutines to withdraw $10 from an account with a $100 balance
func TestConcurrentWithdrawal(t *testing.T) {
    const (
        numWorkers     = 100
        withdrawAmount = 10_000   // $10 in cents
        initialBalance = 100_000  // $100 in cents
    )
    
    var (
        successCount atomic.Int64
        wg           sync.WaitGroup
    )
    
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            err := withdrawFunds("account-A", withdrawAmount)
            if err == nil {
                successCount.Add(1)
            }
        }()
    }
    wg.Wait()
    
    // Exactly 10 requests should succeed
    assert.Equal(t, int64(10), successCount.Load(),
        "Only 10 withdrawals permitted with a $100 balance")
    
    // No double-spend: final balance must be $0
    balance := getBalance("account-A")
    assert.Equal(t, int64(0), balance, "Balance after all funds withdrawn must be 0")
}
```

### Test 2: Continuous Reconciliation Job

```go
func reconcileAllTransactions(db *sql.DB) ([]UnbalancedTx, error) {
    query := `
        SELECT transaction_id, 
               SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END) AS discrepancy
        FROM entries
        GROUP BY transaction_id
        HAVING SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END) <> 0
    `
    rows, err := db.Query(query)
    if err != nil {
        return nil, err
    }
    // Parse rows and fire P1 alert if any discrepancy exists
    // ...
}
```

---

## FAQ


{{< faq q="Is TigerBeetle suitable for every Fintech application?" >}}
Not necessarily. TigerBeetle is optimized for **high-throughput financial ledgers** (>100,000 TPS), but lacks SQL query flexibility. If you need complex reporting queries, joins, or integration with traditional ORMs, PostgreSQL + a double-entry schema remains an excellent choice.
{{< /faq >}}

{{< faq q="Why not use FLOAT to store money?" >}}
Floating-point numbers (IEEE 754) cannot represent many decimal fractions precisely. For example: `0.1 + 0.2 = 0.30000000000000004` in most programming languages. Over millions of calculations, these precision errors accumulate and unbalance the ledger. Use `NUMERIC(18,4)` or `BIGINT` (storing values as cents/pennies).
{{< /faq >}}

{{< faq q="What is the difference between a Reversal Entry and a Void Entry?" >}}
- **Reversal Entry**: Creating a new, opposite entry pointing back to the original entry via `reversalentrykey`. Used to correct errors after a transaction has already settled.
- **Void Pending**: Canceling a transfer that is currently in a `pending` state (unsettled). This only modifies `debits_pending`/`credits_pending` without affecting `posted` fields.

---

*Up Next: [Part 2 — Distributed SQL & ACID Latency: TiDB vs CockroachDB vs Spanner](/series/core-banking-architecture/part-2-distributed-sql-acid-latency/) — Detailed analysis of 2PC overhead, TrueTime math, and Percolator lock recovery.*
{{< /faq >}}
