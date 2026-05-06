---
title: "Part 7 — Practice: Build a Mini Core Banking System from Scratch"
date: 2026-05-06T18:00:00+07:00
draft: false
description: "A comprehensive hands-on project — build a miniature Core Banking system integrating a Double-Entry Ledger, ACID Transactions, CASA, Lending, and REST APIs, applying all the knowledge from the series."
weight: 8
---

## Project Objectives

This is the final capstone project. You will build a complete **Mini Core Banking** system, simultaneously applying all the principles we've covered:

- ✅ **Part 1:** Double-entry bookkeeping with an immutable Ledger
- ✅ **Part 2:** CIF, CASA, and Lending domain models
- ✅ **Part 3:** ACID transactions, Pessimistic Locking, and Idempotency
- ✅ **Part 4:** Event-driven design with the Outbox Pattern
- ✅ **Part 5:** Standardized message structures (ISO-inspired)
- ✅ **Part 6:** Audit trails and data classification

You can use any language: Go, Java, Python, Node.js, .NET — the architectural principles remain the same.

---

## Step 1: Design the Database Schema

This is the foundation. Get this right, and everything else flows naturally.

```sql
-- ============================================================
-- 1. CUSTOMERS (CIF)
-- ============================================================
CREATE TABLE customers (
    cif_number      VARCHAR(20)  PRIMARY KEY,
    customer_type   VARCHAR(15)  NOT NULL CHECK (customer_type IN ('INDIVIDUAL','CORPORATE')),
    full_name       VARCHAR(255) NOT NULL,
    id_number       VARCHAR(30)  UNIQUE NOT NULL,
    kyc_status      VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. ACCOUNTS (CASA)
-- ============================================================
CREATE TABLE accounts (
    account_number    VARCHAR(20)  PRIMARY KEY,
    cif_number        VARCHAR(20)  NOT NULL REFERENCES customers(cif_number),
    account_type      VARCHAR(30)  NOT NULL,
    currency          CHAR(3)      NOT NULL DEFAULT 'VND',
    status            VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    current_balance   BIGINT       NOT NULL DEFAULT 0,
    available_balance BIGINT       NOT NULL DEFAULT 0,
    version           BIGINT       NOT NULL DEFAULT 1,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. LEDGER ENTRIES (Double-Entry Bookkeeping)
-- ============================================================
CREATE TABLE ledger_entries (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id  UUID        NOT NULL,
    account_number  VARCHAR(20) NOT NULL REFERENCES accounts(account_number),
    entry_type      CHAR(6)     NOT NULL CHECK (entry_type IN ('DEBIT','CREDIT')),
    amount          BIGINT      NOT NULL CHECK (amount > 0),
    currency        CHAR(3)     NOT NULL,
    balance_after   BIGINT      NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent edits to the ledger
CREATE RULE no_update_ledger AS ON UPDATE TO ledger_entries DO INSTEAD NOTHING;
CREATE RULE no_delete_ledger AS ON DELETE TO ledger_entries DO INSTEAD NOTHING;

-- ============================================================
-- 4. TRANSACTIONS (Idempotency Control)
-- ============================================================
CREATE TABLE financial_transactions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key VARCHAR(64) UNIQUE NOT NULL,
    type            VARCHAR(30) NOT NULL, -- 'DEPOSIT','WITHDRAWAL','TRANSFER','FEE'
    status          VARCHAR(20) NOT NULL DEFAULT 'PROCESSING',
    from_account    VARCHAR(20),
    to_account      VARCHAR(20),
    amount          BIGINT      NOT NULL,
    currency        CHAR(3)     NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ============================================================
-- 5. OUTBOX (At-Least-Once Event Publishing)
-- ============================================================
CREATE TABLE outbox_events (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    topic        VARCHAR(100) NOT NULL,
    payload      JSONB        NOT NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- ============================================================
-- 6. AUDIT LOG
-- ============================================================
CREATE TABLE audit_logs (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id   VARCHAR(50) NOT NULL,
    action      VARCHAR(50) NOT NULL,
    actor_id    VARCHAR(50) NOT NULL,
    before_data JSONB,
    after_data  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Step 2: Implement the Money Transfer Logic

This is the most critical use case. **All steps below must happen within a single Database Transaction**:

```
FLOW: POST /v1/transfers
  Header: Idempotency-Key: <uuid-from-client>

STEP 1: Check Idempotency Key
  → If already completed: return old result (200 OK)
  → If processing: return 409 Conflict
  → If new: proceed

STEP 2: Validate Input
  → amount > 0
  → from_account != to_account
  → currency is valid

STEP 3: BEGIN DATABASE TRANSACTION
  
  STEP 3a: Lock both accounts (order by ID to prevent deadlocks)
    → SELECT ... FOR UPDATE WHERE account_number IN (from, to) ORDER BY account_number

  STEP 3b: Check business rules
    → available_balance(from) >= amount
    → status(from) = 'ACTIVE'
    → status(to) = 'ACTIVE'

  STEP 3c: Update Balances
    → UPDATE accounts SET current_balance -= amount, available_balance -= amount WHERE from
    → UPDATE accounts SET current_balance += amount, available_balance += amount WHERE to

  STEP 3d: Write Double-Entry Ledger (2 entries)
    → INSERT DEBIT entry (from_account, amount, balance_after_deduction)
    → INSERT CREDIT entry (to_account, amount, balance_after_addition)

  STEP 3e: Insert financial_transaction record (status = COMPLETED)

  STEP 3f: Insert idempotency_key record

  STEP 3g: Insert outbox_events (topic: 'transfer.completed')

  STEP 3h: Insert audit_log

STEP 4: COMMIT TRANSACTION

STEP 5: Return 202 Accepted + transaction_id
```

---

## Step 3: Write the Invariant Check

Create an internal endpoint (or a cron job) to continuously verify ledger integrity:

```sql
-- Run this daily, trigger alerts if imbalance != 0
SELECT
    currency,
    SUM(CASE WHEN entry_type = 'DEBIT'  THEN amount ELSE 0 END) AS total_debits,
    SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END) AS total_credits,
    SUM(CASE WHEN entry_type = 'DEBIT'  THEN amount ELSE 0 END) -
    SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END) AS imbalance
FROM ledger_entries
GROUP BY currency
HAVING SUM(CASE WHEN entry_type = 'DEBIT'  THEN amount ELSE 0 END) !=
       SUM(CASE WHEN entry_type = 'CREDIT' THEN amount ELSE 0 END);
```

---

## Step 4: Stress Testing — The Final Exam

Once built, you MUST stress test the system by sending highly concurrent requests:

```bash
# Using k6 (JavaScript load testing tool)
# Scenario: 100 users transferring money simultaneously from Account A to B

k6 run --vus 100 --duration 30s transfer_test.js

# After testing, verify:
# 1. Did the total amount of money in the system change?
# 2. Is the ledger balanced? (DEBIT = CREDIT)
# 3. Were there any duplicate transactions?
# 4. Did any account balance drop below zero?
```

```javascript
// transfer_test.js
import http from 'k6/http';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

export default function () {
    http.post('http://localhost:8080/v1/transfers', JSON.stringify({
        from_account: 'ACC001',
        to_account:   'ACC002',
        amount:       1000,
        currency:     'VND',
        description:  'Stress test transfer'
    }), {
        headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': uuidv4(),  // Unique key per request
        }
    });
}
```

---

## Project Completion Checklist

### Core Banking Logic
- [ ] Double-entry ledger works correctly (DEBIT = CREDIT after every transaction)
- [ ] Ledger entries are immutable (no UPDATE/DELETE possible)
- [ ] Balance invariant check runs and returns 0

### Concurrency & Safety
- [ ] Pessimistic locking prevents race conditions
- [ ] Lock ordering is consistent (prevents deadlocks)
- [ ] Idempotency key works (sending 10 identical keys → exactly 1 transaction)
- [ ] Accounts can never have a negative balance

### Reliability
- [ ] Outbox pattern guarantees no events are lost
- [ ] API returns 202 Accepted quickly (non-blocking)
- [ ] Audit log meticulously records all actions

### Stress Test
- [ ] 100 concurrent transfers → no money lost or magically created
- [ ] Ledger remains perfectly balanced
- [ ] No deadlock errors in application logs

---

## What's Next?

Once you have a functional Mini Core Banking system, you can extend it:

1. **Add a Lending module:** Create loans, calculate daily interest, process repayments.
2. **Integrate ISO 8583:** Build a simple Payment Switch to receive card messages and route them to the Core.
3. **CQRS Read Side:** Add Elasticsearch for ultra-fast transaction history lookups.
4. **Rate Limiting & Fraud Detection:** Detect anomalous transactions using a Rule Engine.
5. **Study Apache Fineract:** Dive into the open-source code of a real-world Core Banking system.

> *Congratulations on completing the series! You now have a solid foundation to begin your journey as a Core Banking Developer. Remember: in this field, **meticulousness and systems thinking are vastly more important than coding speed.***
