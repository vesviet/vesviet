---
title: "Part 7: Build a Mini Core Banking System in Go"
date: "2026-05-06T18:00:00+07:00"
lastmod: "2026-06-10T16:00:00+07:00"
draft: false
description: "Build a complete mini Core Banking system in Go: double-entry ledger, ACID transactions, CASA accounts, loan management, and REST APIs — end-to-end."
weight: 8
cover:
  image: "images/posts/banking-microservices-cover.png"
  alt: "Core Banking Developer Roadmap series: architecture patterns, fintech microservices, and Go"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/core-banking-developer/part-7-build-mini-core-banking/"
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

ShowToc: true
TocOpen: true
cover:
  image: "images/posts/banking-microservices-cover.png"
  alt: "Core Banking Developer Roadmap series: architecture patterns, fintech microservices, and Go"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/core-banking-developer/part-7-build-mini-core-banking/"
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

This is the most critical use case. Below is the complete Go implementation of the HTTP handler processing funds transfer under strict concurrency control.

```go
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"github.com/google/uuid"
)

type TransferRequest struct {
	FromAccount string `json:"from_account"`
	ToAccount   string `json:"to_account"`
	Amount      int64  `json:"amount"`
	Currency    string `json:"currency"`
	Description string `json:"description"`
}

type TransferResponse struct {
	TransactionID string `json:"transaction_id"`
	Status        string `json:"status"`
}

type TransferHandler struct {
	db *sql.DB
}

func (h *TransferHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	idempotencyKey := r.Header.Get("Idempotency-Key")
	if idempotencyKey == "" {
		http.Error(w, "Missing Idempotency-Key header", http.StatusBadRequest)
		return
	}

	var req TransferRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate inputs
	if req.Amount <= 0 || req.FromAccount == req.ToAccount || req.Currency == "" {
		http.Error(w, "Validation failed: invalid fields", http.StatusBadRequest)
		return
	}

	ctx := r.Context()

	// 1. Check Idempotency Table
	var txID string
	var status string
	var cachedResult []byte
	err := h.db.QueryRowContext(ctx, 
		"SELECT id, status FROM financial_transactions WHERE idempotency_key = $1", 
		idempotencyKey).Scan(&txID, &status)
	
	if err == nil {
		if status == "COMPLETED" {
			w.Header().Set("Content-Type", "application/json")
			w.Write(cachedResult)
			return
		}
		http.Error(w, "Transaction currently processing", http.StatusConflict)
		return
	} else if !errors.Is(err, sql.ErrNoRows) {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// 2. Begin Transaction
	tx, err := h.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
	if err != nil {
		http.Error(w, "Failed to begin transaction", http.StatusInternalServerError)
		return
	}
	defer tx.Rollback()

	// 3. Lock Accounts Deterministically to prevent deadlocks
	firstAcc, secondAcc := req.FromAccount, req.ToAccount
	if req.FromAccount > req.ToAccount {
		firstAcc, secondAcc = req.ToAccount, req.FromAccount
	}

	var firstBalance, firstAvailable, secondBalance, secondAvailable int64
	var firstStatus, secondStatus string

	// Lock first account
	err = tx.QueryRowContext(ctx, 
		"SELECT current_balance, available_balance, status FROM accounts WHERE account_number = $1 FOR UPDATE", 
		firstAcc).Scan(&firstBalance, &firstAvailable, &firstStatus)
	if err != nil {
		http.Error(w, "Failed to lock first account", http.StatusInternalServerError)
		return
	}

	// Lock second account
	err = tx.QueryRowContext(ctx, 
		"SELECT current_balance, available_balance, status FROM accounts WHERE account_number = $1 FOR UPDATE", 
		secondAcc).Scan(&secondBalance, &secondAvailable, &secondStatus)
	if err != nil {
		http.Error(w, "Failed to lock second account", http.StatusInternalServerError)
		return
	}

	// Re-verify balances on source account
	var srcAvailable int64
	var srcStatus string
	err = tx.QueryRowContext(ctx, 
		"SELECT available_balance, status FROM accounts WHERE account_number = $1", 
		req.FromAccount).Scan(&srcAvailable, &srcStatus)
	if err != nil || srcStatus != "ACTIVE" || srcAvailable < req.Amount {
		http.Error(w, "Insufficient available funds or account inactive", http.StatusBadRequest)
		return
	}

	newTxID := uuid.New().String()

	// 4. Update Balances
	_, err = tx.ExecContext(ctx, 
		"UPDATE accounts SET current_balance = current_balance - $1, available_balance = available_balance - $1 WHERE account_number = $2", 
		req.Amount, req.FromAccount)
	if err != nil {
		return
	}
	_, err = tx.ExecContext(ctx, 
		"UPDATE accounts SET current_balance = current_balance + $1, available_balance = available_balance + $1 WHERE account_number = $2", 
		req.Amount, req.ToAccount)
	if err != nil {
		return
	}

	// Fetch balances after transaction for ledger reporting
	var fromBalAfter, toBalAfter int64
	tx.QueryRowContext(ctx, "SELECT current_balance FROM accounts WHERE account_number = $1", req.FromAccount).Scan(&fromBalAfter)
	tx.QueryRowContext(ctx, "SELECT current_balance FROM accounts WHERE account_number = $1", req.ToAccount).Scan(&toBalAfter)

	// 5. Insert double-entry ledger postings
	ledgerQuery := `
		INSERT INTO ledger_entries (transaction_id, account_number, entry_type, amount, currency, balance_after, description) 
		VALUES ($1, $2, $3, $4, $5, $6, $7)`
	_, err = tx.ExecContext(ctx, ledgerQuery, newTxID, req.FromAccount, "DEBIT", req.Amount, req.Currency, fromBalAfter, req.Description)
	if err != nil {
		return
	}
	_, err = tx.ExecContext(ctx, ledgerQuery, newTxID, req.ToAccount, "CREDIT", req.Amount, req.Currency, toBalAfter, req.Description)
	if err != nil {
		return
	}

	// 6. Record transaction with completed status
	_, err = tx.ExecContext(ctx, `
		INSERT INTO financial_transactions (id, idempotency_key, type, status, from_account, to_account, amount, currency, description, completed_at) 
		VALUES ($1, $2, 'TRANSFER', 'COMPLETED', $3, $4, $5, $6, $7, $8)`,
		newTxID, idempotencyKey, req.FromAccount, req.ToAccount, req.Amount, req.Currency, req.Description, time.Now())
	if err != nil {
		return
	}

	// 7. Insert outbox event
	eventPayload, _ := json.Marshal(req)
	_, err = tx.ExecContext(ctx, 
		"INSERT INTO outbox_events (topic, payload) VALUES ('transfer.completed', $1)", 
		eventPayload)
	if err != nil {
		return
	}

	if err := tx.Commit(); err != nil {
		http.Error(w, "Failed to commit transaction", http.StatusInternalServerError)
		return
	}

	resp := TransferResponse{
		TransactionID: newTxID,
		Status:        "COMPLETED",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(resp)
}
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

> *Congratulations on completing the series! The final step is learning how to document these complex systems. Continue reading **[Part 8 — Writing a Core Banking PRD: Developer Guide]({{< ref "part-8-core-banking-prd.md" >}})** to master the art of specification.*

