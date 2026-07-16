---
title: "Chapter 7: Designing Idempotency APIs for Payment Systems"
date: "2026-06-09T10:30:00+07:00"
lastmod: "2026-06-09T10:30:00+07:00"
draft: false
series: ["Mastering High-Concurrency Systems in Production"]
series_order: 7
tags: ["golang", "idempotency", "redis", "api design"]
mermaid: true
slug: "idempotency-api-design-payments"
description: "Prevent double-charging customers by implementing robust Idempotency Keys and Atomic Redis locks in your HTTP POST transactions."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/realtime-inventory-cover.png"
  alt: "High Concurrency Systems Masterclass series: queues, caches, and distributed B2B commerce"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/high-concurrency-systems/idempotency-api-design-payments/"
---

> **Prerequisite:** Before reading this chapter, please ensure you have read the previous article in this series: [Chapter 6: API Gateway vs Service Mesh in Microservices Architecture]({{< ref "article_6_api_gateway.md" >}}).

In E-commerce or Fintech, the ultimate nightmare is not a system crash, but **charging a customer twice for a single order**. This is usually caused by network lag, an impatient user double-clicking "Pay", or automated app retry logic.

The mandatory solution for any transactional API (Payment/Order) is **Idempotency**.

---

## 1. What is Idempotency?

An operation is idempotent if executing it once or N times yields the exact same system state and outcome. While GET and PUT are natively idempotent, POST requires explicit engineering.

With HTTP REST APIs:
- `GET`, `PUT`, `DELETE`: Inherently idempotent. (Deleting a user 10 times results in the same state: the user is gone).
- `POST`: **Not idempotent**. Calling POST `/charge` 10 times will execute 10 financial deductions.

---

## 2. Idempotency-Key and the Request Lifecycle

Clients must attach a unique `Idempotency-Key` UUID to their requests. The server validates this key against Redis to determine if the transaction is new, processing, or already completed.

To enforce idempotency on a POST API, the Client (Mobile/Web) must generate a Unique ID (typically a UUID v4) and attach it to the Request Header: `Idempotency-Key: 123e4567...`

The Golang server handles this via 3 strict states:

1. **State 1 (New Key):** 
   - The server registers the Key in Redis with an `IN_FLIGHT` state.
   - It executes the business logic (calling payment gateways, deducting balances).
   - Upon completion, it updates the Key to `DONE` and **stores the entire Response Payload** in Redis. It returns the result to the Client.
2. **State 2 (Key is IN_FLIGHT):**
   - The user double-clicks. Request 2 arrives while Request 1 is still processing.
   - The server checks Redis, sees `IN_FLIGHT`, instantly blocks Request 2, and returns an `HTTP 409 Conflict` (or 423 Locked) error.
3. **State 3 (Key is DONE):**
   - The user drops connection after Request 1 finishes, missing the response. The user retries the request with the identical Key.
   - The server checks Redis, sees `DONE`. The server **DOES NOT** re-run the deduction logic. Instead, it pulls the cached Response Payload from Redis and returns it immediately. The user receives the exact success payload they missed.

```mermaid
stateDiagram-v2
    [*] --> NewRequest
    NewRequest --> CheckRedis: Header contains Idempotency-Key
    
    CheckRedis --> IN_FLIGHT: Key Not Exists (SET NX)
    CheckRedis --> CONFLICT: Key == IN_FLIGHT
    CheckRedis --> DONE: Key == DONE
    
    IN_FLIGHT --> ExecuteLogic: Process Payment
    ExecuteLogic --> SaveResponse: Update Key to DONE
    SaveResponse --> ReturnNewResponse
    
    CONFLICT --> Return409Error: "Processing"
    
    DONE --> ReturnCachedResponse: Return old payload
```

---

## 3. Idempotency State Machine: Hardening with Retriability

To build a production-grade billing system, the idempotency engine must support transient failure retries. This is handled by modeling explicit state transitions:

```mermaid
stateDiagram-v2
    [*] --> IN_FLIGHT : Client submits Request (SET NX)
    IN_FLIGHT --> DONE : Processing Succeeds
    IN_FLIGHT --> RETRIABLE_FAIL : Transient Failure (e.g., Timeout)
    IN_FLIGHT --> NON_RETRIABLE_FAIL : Hard Business Error (e.g., Insufficient Balance)
    RETRIABLE_FAIL --> IN_FLIGHT : Client Retries Request
    NON_RETRIABLE_FAIL --> [*] : Key Locked (Cannot retry)
```

- **`RETRIABLE_FAIL`**: If the downstream payment gateway returns a timeout (HTTP 504), the transaction is incomplete. The idempotency engine deletes the key or marks it as `RETRIABLE`. This allows the client to submit another request with the exact same key.
- **`NON_RETRIABLE_FAIL`**: If the transaction fails due to a validation error (e.g., product out of stock), the state transitions to `DONE` with the failed response cached. Any retry with the same key returns the cached failure payload immediately without re-checking inventory.

---

## 4. PostgreSQL Unique Index Locks

In Core Banking and high-value payments, relying solely on in-memory systems like Redis is a security risk. If Redis restarts or evicts keys under memory pressure, the system could allow duplicate transactions. Therefore, financial systems implement **distributed transactional deduplication** using the relational database.

This is achieved by maintaining an `idempotency_keys` table inside PostgreSQL with a `UNIQUE` constraint:

```sql
CREATE TABLE idempotency_keys (
    key_id VARCHAR(255) PRIMARY KEY,
    request_hash CHAR(64) NOT NULL,
    status VARCHAR(50) NOT NULL,
    response_code INT NOT NULL,
    response_body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### The Database Lock Flow
When two concurrent requests attempt to insert the same key, PostgreSQL handles the synchronization at the database level:
1. **Transaction 1** executes: `INSERT INTO idempotency_keys (key_id, ...) VALUES ('key_abc', ...)`
2. PostgreSQL acquires an exclusive write lock on the index leaf node for `'key_abc'`.
3. **Transaction 2** attempts to insert the same key. Because of the `UNIQUE` constraint, Transaction 2 blocks, waiting for Transaction 1 to complete.
4. If Transaction 1 commits, Transaction 2 instantly fails with a unique constraint violation error (PostgreSQL error code `23505`).
5. If Transaction 1 aborts (rolls back), the lock is released, and Transaction 2 proceeds to insert the key.

To prevent thread pool exhaustion on the application side while waiting for locks to release, you should set a strict lock timeout inside your database session:
```sql
SET lock_timeout = '2000'; -- 2 seconds max wait
```

---

## 5. High-Security Edge Case: Payload Hashing

Malicious clients can exploit idempotency by reusing an old Key with a new, expensive payload. Counter this by storing a SHA256 Hash of the Request Body alongside the Idempotency Key.

A common exploit involves a malicious client reusing an old `DONE` `Idempotency-Key` but transmitting a new payload (e.g., purchasing an expensive TV). If the system only checks the Key, it will return the old success response (for a cheap item) while ignoring the new payload entirely!

**The Defense:** Hash (e.g., SHA256) the entire Request Body. Store this Hash value alongside the `Idempotency-Key` in Redis or PostgreSQL. If a duplicate Key arrives but the Body Hash differs, block it instantly and return `HTTP 400 Bad Request`.

---

## Go Implementation: Resilient Database Deduplication Middleware

The following Go code implements an API idempotency layer using PostgreSQL unique constraints to guarantee transactional safety.

```go
package main

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/jackc/pgconn"
	_ "github.com/jackc/pgx/v4/stdlib"
)

// IdempotencyRecord maps to the DB schema.
type IdempotencyRecord struct {
	KeyId        string
	RequestHash  string
	Status       string
	ResponseCode int
	ResponseBody string
}

type PaymentHandler struct {
	db *sql.DB
}

// ComputeHash computes the SHA256 hash of the request body.
func ComputeHash(body []byte) string {
	hash := sha256.Sum256(body)
	return hex.EncodeToString(hash[:])
}

// HandlePayment processes payments with database deduplication.
func (h *PaymentHandler) HandlePayment(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	idemKey := r.Header.Get("Idempotency-Key")
	if idemKey == "" {
		http.Error(w, "Missing Idempotency-Key header", http.StatusBadRequest)
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Bad Request", http.StatusBadRequest)
		return
	}
	reqHash := ComputeHash(body)

	ctx := r.Context()

	// 1. Attempt to insert IN_FLIGHT status to claim ownership of the key
	tx, err := h.db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
	if err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}
	defer tx.Rollback()

	// Set session-level lock timeout to protect connection pool
	_, _ = tx.ExecContext(ctx, "SET LOCAL lock_timeout = '1500'")

	query := `INSERT INTO idempotency_keys (key_id, request_hash, status, response_code, response_body) 
	          VALUES ($1, $2, 'IN_FLIGHT', 0, '')`
	_, err = tx.ExecContext(ctx, query, idemKey, reqHash)

	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" { // Unique Constraint Violation
			// 2. Key exists, fetch current status and response
			record, fetchErr := h.fetchIdempotencyRecord(ctx, idemKey)
			if fetchErr != nil {
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}

			// Validate if the request body matches the original request
			if record.RequestHash != reqHash {
				http.Error(w, "Idempotency Key reused with different payload", http.StatusBadRequest)
				return
			}

			if record.Status == "IN_FLIGHT" {
				// Request is still processing in another thread
				w.Header().Set("Retry-After", "2")
				http.Error(w, "Concurrent request processing", http.StatusConflict)
				return
			}

			// Return the cached response
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Cache-Lookup", "HIT - Idempotent Response")
			w.WriteHeader(record.ResponseCode)
			_, _ = w.Write([]byte(record.ResponseBody))
			return
		}

		http.Error(w, "Database Lock Timeout / Error", http.StatusGatewayTimeout)
		return
	}

	// Commit claiming the key
	if err := tx.Commit(); err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	// 3. Execute the actual payment transaction
	code, respPayload := h.executePayment()

	// 4. Update the key to DONE along with response payload
	updateQuery := `UPDATE idempotency_keys 
	                SET status = 'DONE', response_code = $1, response_body = $2 
	                WHERE key_id = $3`
	_, err = h.db.ExecContext(ctx, updateQuery, code, respPayload, idemKey)
	if err != nil {
		fmt.Printf("Failed to update idempotency key: %v\n", err)
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_, _ = w.Write([]byte(respPayload))
}

func (h *PaymentHandler) fetchIdempotencyRecord(ctx context.Context, key string) (*IdempotencyRecord, error) {
	var record IdempotencyRecord
	query := "SELECT key_id, request_hash, status, response_code, response_body FROM idempotency_keys WHERE key_id = $1"
	err := h.db.QueryRowContext(ctx, query, key).Scan(
		&record.KeyId, &record.RequestHash, &record.Status, &record.ResponseCode, &record.ResponseBody,
	)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (h *PaymentHandler) executePayment() (int, string) {
	// Simulate billing processing time
	time.Sleep(200 * time.Millisecond)
	resp := map[string]interface{}{
		"transaction_id": "tx_99281729",
		"status":         "SUCCESS",
		"billed_at":      time.Now().Format(time.RFC3339),
	}
	payload, _ := json.Marshal(resp)
	return http.StatusOK, string(payload)
}

func main() {
	db, err := sql.Open("pgx", "postgres://user:pass@localhost:5432/payment_db?sslmode=disable")
	if err != nil {
		panic(err)
	}
	defer db.Close()

	handler := &PaymentHandler{db: db}
	http.HandleFunc("/charge", handler.HandlePayment)
	_ = http.ListenAndServe(":8080", nil)
}
```

This database-backed idempotency mechanism guarantees absolute consistency, preventing duplicate charges even during concurrent network retries.

---

## 🎯 Architecture Review & Consulting (Hire Me)

If your enterprise e-commerce or B2B platform is struggling with slow database queries, checkout timeouts, or scaling bottlenecks, don't let it jeopardize your business revenue.

👉 **[Book a 1:1 Architecture Consultation this week](/hire/)** with Lê Tuấn Anh (Vesviet) to identify bottlenecks and implement proven scaling strategies.

---

[← Previous]({{< ref "article_6_api_gateway.md" >}}) | [Series hub]({{< ref "_index.md" >}}) | [Next →]({{< ref "article_8_distributed_locking.md" >}})

