---
title: "Part 1 — The Double-Entry Ledger Foundation"
date: 2026-05-06T18:00:00+07:00
draft: false
description: "Before writing any code for Core Banking, you must understand double-entry bookkeeping — a 700-year-old principle that remains the bedrock of all modern financial systems."
weight: 2
---

## Why does a developer need to learn accounting?

Most developers hear "accounting" and assume it's a job for the finance department. But in Core Banking, **double-entry bookkeeping is the most critical business logic** your code must execute. If your code is wrong and the ledger is unbalanced, the bank cannot report to the Central Bank, leading to severe legal consequences.

## The Principle of Double-Entry Bookkeeping

Invented in the 15th century by Italian mathematician Luca Pacioli, this principle has **only one rule**:

> **Every financial transaction must be recorded in at least two accounts, one as a Debit and one as a Credit, and the total value of both sides must be equal.**

### Real-world example: Customer A transfers 1,000,000 VND to Customer B

In a conventional mindset, a developer might simply think:
```
account_A.balance -= 1_000_000
account_B.balance += 1_000_000
```

This is **incorrect from an accounting perspective**. The correct way is to record entries in the General Ledger (GL):

| ID  | Account | Entry Type | Amount |
|-----|---------|------------|--------|
| TX1 | Account A | **Debit** | 1,000,000 |
| TX1 | Account B | **Credit** | 1,000,000 |

**Total Debits = Total Credits = 1,000,000** → The ledger is balanced ✅

## The General Ledger (GL) Table — The Heart of Core Banking

The entire Core Banking system essentially revolves around writing data to the GL table with absolute precision. Here is the most basic design of a GL table:

```sql
CREATE TABLE ledger_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID        NOT NULL,  -- Groups entries of the same transaction
    account_id      UUID        NOT NULL,  -- Which account is affected
    entry_type      VARCHAR(6)  NOT NULL,  -- 'DEBIT' or 'CREDIT'
    amount          BIGINT      NOT NULL,  -- Stored in the smallest unit (e.g., cents, dong)
    currency        CHAR(3)     NOT NULL,  -- 'VND', 'USD', 'JPY'
    balance_after   BIGINT      NOT NULL,  -- Balance after this entry
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description     TEXT,
    
    CONSTRAINT chk_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_entry_type CHECK (entry_type IN ('DEBIT', 'CREDIT'))
);
```

> **Crucial Note:** Always store money in integer units — dong, cents, satoshis. **Never use `FLOAT` or `DOUBLE`** to store currency because floating-point precision errors will unbalance the ledger after thousands of transactions.

## Ledger Health Check: The Balance Invariant

This is a query you must be able to run at any time to verify the ledger is not corrupted:

```sql
-- Total of all Debit entries MUST ALWAYS equal the total of all Credit entries
SELECT
    SUM(CASE WHEN entry_type = 'DEBIT'  THEN amount ELSE 0 END) AS total_debits,
    SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credits,
    SUM(CASE WHEN entry_type = 'DEBIT'  THEN amount ELSE 0 END) -
    SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END) AS imbalance
FROM ledger_entries;

-- Expected result: imbalance = 0
```

If `imbalance ≠ 0`, it means your code missed an entry somewhere — this is the **most critical bug** possible in Core Banking.

## Account Structures in a Bank

Not every account belongs to a customer. Inside a bank, there are multiple internal account types:

| Account Type | Meaning | Example |
|---|---|---|
| **Asset** | Money the bank holds | Cash in Vault, Customer Loans |
| **Liability** | Money the bank owes customers | Customer Account Balances |
| **Income** | Revenue of the bank | Transaction fees, Interest earned |
| **Expense** | Costs of the bank | Interest paid on savings |
| **Equity** | Shareholders' capital | Charter capital |

When a customer deposits 10 million into a savings account, the system must record:
- **Debit** the Cash Account (Asset increases)
- **Credit** the Customer Savings Account (Liability increases — the bank owes the customer)

## Core Lessons

1. **Never update balances directly** (`UPDATE accounts SET balance = balance - X`). Always write entries to the ledger, then derive the balance from the ledger.
2. **Every transaction is an atomic unit** — all entries must succeed or fail together (Database Transaction).
3. **The Ledger is immutable** — never UPDATE or DELETE an entry once recorded. To fix a mistake, you must post a reversal entry.

> *Next, we will apply the double-entry bookkeeping mindset to the most specific banking operations. Continue reading [Part 2 — Core Banking Domain: CIF, CASA & Lending](/series/core-banking-developer/part-2-banking-domain-casa-lending/).*
