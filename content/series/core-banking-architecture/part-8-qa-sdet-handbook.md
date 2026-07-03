---
title: "QA & SDET Handbook: Testing Distributed Core Banking"
date: 2026-06-18T12:10:00+07:00
lastmod: 2026-07-03T15:41:55+07:00
draft: false
description: "SDET handbook for Core Banking: double-spend, split-brain, clock skew, saga DLQ, DPoP replay, Flink TestHarness — 6 test categories for distributed fintech systems."
weight: 8
series: ["core-banking-architecture"]
keywords: ["core banking testing strategy", "distributed systems SDET", "split-brain simulation testing", "clock skew injection libfaketime", "fintech QA testing"]
author: "Tuan Anh"
schema: ["Article", "TechArticle", "HowTo", "FAQPage"]
---

> **Series (Part 8 of 8):** This concluding article compiles a comprehensive testing strategy specifically tailored for each layer of the Core Banking Architecture covered in previous parts — from ledger consistency to distributed SQL, Sagas, ISO 20022, API Security, and Streaming Fraud Detection.

## Why Does Core Banking Need a Dedicated SDET?

Testing distributed financial systems requires specialized skills beyond standard unit tests. The most critical bugs usually only appear under **high concurrency**, **network failures**, **clock drift**, or **partial system failures** — conditions that cannot be reproduced using simple integration tests.

The **6 test strategy categories** in this article correspond directly to each part of the series:

| Test Category | Corresponds to Part | Risk if ignored |
|--------------|-------------------|----------------|
| **Double-Entry Invariant** | Part 1 (Ledger) | Double-spend, unbalanced GL |
| **Distributed SQL & Clock** | Part 2 (Distributed SQL) | Split-brain, stale reads |
| **Event Replay & Outbox** | Part 3 (Event Sourcing) | Data inconsistency, lost events |
| **Saga Compensation** | Part 4 (Saga) | Orphaned holds, money stuck |
| **Idempotency & API** | Parts 5, 6 (ISO 20022, Security) | Double-charge, token theft |
| **Flink State & SLA** | Part 7 (Fraud Detection) | Undetected fraud, false positives |

---

## Category 1: Double-Entry Invariant Auditing

### Test 1.1: Concurrent Double-Spend Prevention

**Objective**: 100 goroutines concurrently withdrawing money from an account — only a number of requests equal to the available balance are allowed to succeed.

```go
func TestConcurrentDoubleSpend(t *testing.T) {
    const (
        numWorkers     = 100
        withdrawAmount = 10_000   // 10,000 VND
        initialBalance = 100_000  // 100,000 VND
    )
    
    // Setup: create account with fixed balance
    accountID := createTestAccount(initialBalance)
    
    var (
        successCount atomic.Int64
        wg           sync.WaitGroup
    )
    
    // Run 100 concurrent withdrawals
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            err := withdrawFromAccount(accountID, withdrawAmount)
            if err == nil {
                successCount.Add(1)
            }
        }()
    }
    wg.Wait()
    
    // Exactly 10 requests should be allowed to succeed
    assert.Equal(t, int64(10), successCount.Load(),
        "Exactly 10 withdrawals are allowed with a balance of 100,000 VND")
    
    // Final balance must be 0 — no negative balance, no double-counting
    finalBalance := getAccountBalance(accountID)
    assert.Equal(t, int64(0), finalBalance,
        "Balance after all funds withdrawn must be 0, not negative")
    
    // Ledger invariant: SUM(DEBIT) = SUM(CREDIT)
    imbalance := checkLedgerBalance(accountID)
    assert.Equal(t, int64(0), imbalance,
        "Ledger must be balanced: SUM(DEBIT) = SUM(CREDIT)")
}
```

### Test 1.2: Continuous Reconciliation Job

```go
// Run every 5 minutes in production monitoring
func RunLedgerReconciliation(ctx context.Context, db *sql.DB) ([]DiscrepancyReport, error) {
    query := `
        SELECT
            transaction_id,
            SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END) AS discrepancy
        FROM entries
        GROUP BY transaction_id
        HAVING SUM(CASE WHEN direction = 'DEBIT' THEN amount ELSE -amount END) <> 0
        LIMIT 100
    `
    
    rows, err := db.QueryContext(ctx, query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var reports []DiscrepancyReport
    for rows.Next() {
        var report DiscrepancyReport
        rows.Scan(&report.TransactionID, &report.Discrepancy)
        reports = append(reports, report)
    }
    
    if len(reports) > 0 {
        // CRITICAL: Fire P1 alert — ledger balance violated
        fireP1Alert(ctx, "LEDGER_IMBALANCE", reports)
    }
    
    return reports, nil
}
```

### Test 1.3: Deadlock Prevention Verification

```go
func TestDeadlockFreeTransfers(t *testing.T) {
    // Create 2 accounts
    accountA := createTestAccount(1_000_000)
    accountB := createTestAccount(1_000_000)
    
    var wg sync.WaitGroup
    errs := make(chan error, 100)
    
    // 50 goroutines: A → B
    for i := 0; i < 50; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            err := transferBetween(accountA, accountB, 1000)
            if err != nil {
                errs <- err
            }
        }()
    }
    
    // 50 goroutines: B → A (creates a deadlock condition if lock order is wrong)
    for i := 0; i < 50; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            err := transferBetween(accountB, accountA, 1000)
            if err != nil {
                errs <- err
            }
        }()
    }
    
    // Run with timeout to detect deadlocks
    done := make(chan struct{})
    go func() { wg.Wait(); close(done) }()
    
    select {
    case <-done:
        // No deadlock — all goroutines finished
    case <-time.After(10 * time.Second):
        t.Fatal("DEADLOCK DETECTED: transfers did not finish in 10s")
    }
    
    // Total balance must remain unchanged
    totalBalance := getAccountBalance(accountA) + getAccountBalance(accountB)
    assert.Equal(t, int64(2_000_000), totalBalance,
        "Total balance must remain unchanged after all transfers")
}
```

---

## Category 2: Distributed SQL & Clock Resilience Testing

### Test 2.1: Network Partition (Split-Brain) Simulation

```bash
#!/bin/bash
# Simulation: 5-node CockroachDB cluster partitioned into 3 + 2

MINORITY_NODES=("node4" "node5")
MAJORITY_NODES=("node1" "node2" "node3")

echo "=== Starting network partition simulation ==="

# Drop packets between minority and majority nodes
for node in "${MINORITY_NODES[@]}"; do
    # SSH into node and drop packets to majority
    ssh "$node" "sudo tc qdisc add dev eth0 root netem loss 100%"
    echo "Partitioned: $node disconnected from cluster"
done

sleep 5  # Wait for partition to take effect

echo "=== Testing write behavior during partition ==="

# Test: Write on majority side must succeed
echo "Testing majority write..."
cockroach sql --host=node1:26257 --insecure \
    --execute="INSERT INTO test_transactions VALUES (gen_random_uuid(), 1000, 'VND', NOW())"
echo "Majority write: EXPECTED SUCCESS"

# Test: Write on minority side must fail
echo "Testing minority write..."
cockroach sql --host=node4:26257 --insecure --timeout=5s \
    --execute="INSERT INTO test_transactions VALUES (gen_random_uuid(), 1000, 'VND', NOW())" \
    && echo "FAIL: Minority write succeeded (should have failed!)" \
    || echo "PASS: Minority write correctly rejected"

echo "=== Healing partition ==="
for node in "${MINORITY_NODES[@]}"; do
    ssh "$node" "sudo tc qdisc del dev eth0 root"
done

sleep 10  # Wait for cluster to sync

# Verify: Minority nodes must catch up to consistent state
cockroach node status --host=node1:26257 --insecure
echo "All nodes should show consistent RANGES count"
```

### Test 2.2: Clock Skew Injection (libfaketime)

```bash
#!/bin/bash
# Inject clock drift exceeding CockroachDB's max_clock_offset (500ms)

# Install libfaketime
apt-get install -y libfaketime

# Test with 600ms clock drift (exceeding 500ms threshold)
echo "=== Testing with 600ms clock drift ==="
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1 \
FAKETIME="+0.6s" \
go test ./distributed/... -run TestClockSkewResilience -v 2>&1

# Expectation: Database must detect and reject or retry
# MUST NOT: return stale/out-of-order data

# Test with TiDB: inject drift > TSO timestamp
echo "=== Testing TiDB clock skew ==="
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1 \
FAKETIME="+2s" \
go test ./tidb/... -run TestTSOClockDrift -v 2>&1
```

```javascript
// k6/idempotency-stress.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 100, // 100 Virtual Users
  duration: '30s',
  thresholds: {
    'checks': ['rate==1.0'], // 100% checks must pass
  },
};

// A single unique idempotency_key for all VUs
const IDEMPOTENCY_KEY = `idem-stress-test-${Date.now()}`;
const results = new SharedArray('results', () => []);

export default function () {
  const res = http.post(
    `${__ENV.BASE_URL}/api/v1/transfers`,
    JSON.stringify({
      idempotency_key: IDEMPOTENCY_KEY,  // SAME key!
      source_account:  'ACC-001',
      target_account:  'ACC-002',
      amount:          50000,
      currency:        'VND',
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  const body = JSON.parse(res.body);

  check(res, {
    // Only accept 201 (first create) or 200 (idempotent return)
    'valid status (201 or 200)': (r) => r.status === 201 || r.status === 200,
    // transaction_id must be consistent — cannot have 2 different values
    'same transaction_id always': () => {
      const txId = body.transaction_id;
      if (results.length === 0) {
        results.push(txId);
        return true;
      }
      return txId === results[0]; // Every response must have the same transaction_id
    },
  });
}
```

---

### Test 3: Payment Gateway Latency Profile (k6 + thresholds per endpoint)

```javascript
// k6/gateway-latency-profile.js
import http from 'k6/http';
import { check, group } from 'k6';

export const options = {
  vus: 200,
  duration: '5m',
  thresholds: {
    // Per-endpoint SLA based on ISO 20022 integration requirements
    'http_req_duration{endpoint:pacs008_parse}':  ['p(99)<100'], // XML parse < 100ms
    'http_req_duration{endpoint:transfer_submit}': ['p(99)<200'], // Submit < 200ms
    'http_req_duration{endpoint:status_query}':    ['p(95)<20'],  // Status check < 20ms (hot path)
    'http_req_failed': ['rate<0.001'],
  },
};

export default function () {
  group('pacs.008 Parse', () => {
    const res = http.post(
      `${__ENV.BASE_URL}/api/v1/payments/parse`,
      open('./fixtures/pacs008-sample.xml'),
      {
        headers: { 'Content-Type': 'application/xml' },
        tags: { endpoint: 'pacs008_parse' },
      }
    );
    check(res, { 'parse ok': (r) => r.status === 200 });
  });

  group('Transfer Submit', () => {
    const res = http.post(
      `${__ENV.BASE_URL}/api/v1/transfers`,
      JSON.stringify({ /* transfer payload */ }),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { endpoint: 'transfer_submit' },
      }
    );
    check(res, { 'submit ok': (r) => r.status === 201 });
  });

  group('Status Query', () => {
    const txId = `test-${__VU}-${__ITER - 1}`;
    const res = http.get(
      `${__ENV.BASE_URL}/api/v1/transfers/${txId}/status`,
      { tags: { endpoint: 'status_query' } }
    );
    check(res, { 'status ok': (r) => r.status === 200 || r.status === 404 });
  });
}
```

---

### Pre-Production Load Testing Gates

```bash
#!/bin/bash
# scripts/pre-prod-load-gate.sh
# Run in CI/CD pipeline before deploying to production

set -e

echo "=== Core Banking Load Testing Gate ==="

# 1. Ledger throughput SLA
k6 run --quiet \
  --env BASE_URL=$STAGING_URL \
  --env API_TOKEN=$STAGING_TOKEN \
  k6/ledger-throughput.js
echo "✅ Ledger throughput: P99 < 50ms"

# 2. Idempotency stress
k6 run --quiet \
  --env BASE_URL=$STAGING_URL \
  k6/idempotency-stress.js
echo "✅ Idempotency: no duplicate transactions under 100-VU storm"

# 3. Gateway latency profile
k6 run --quiet \
  --env BASE_URL=$STAGING_URL \
  k6/gateway-latency-profile.js
echo "✅ Gateway latency: pacs.008 parse < 100ms, transfer < 200ms, query < 20ms"

echo ""
echo "All load testing gates PASSED — safe to deploy to production"
```

**KPIs for the Load Testing phase:**

| Metric | Pass Threshold | Fail → Action |
|--------|---------------|---------------|
| Transfer P99 | ≤ 50ms | Investigate DB locking, connection pool |
| Error Rate | ≤ 0.1% | Check idempotency logic, retry policy |
| Idempotency | 100% same tx_id | Bug in unique constraint / cache logic |
| pacs.008 parse P99 | ≤ 100ms | Profile XML streaming parser |
| Status query P95 | ≤ 20ms | Check Redis cache hit rate |

---

## Appendix: Testing Tools & Libraries


| Tool | Used For | Language |
|------|---------|----------|
| **libfaketime** | Clock drift injection | C/Linux |
| **tc (traffic control)** | Network partition simulation | Linux |
| **toxiproxy** | Programmable network conditions | Multi-language |
| **Flink TestHarness** | Operator unit testing | Java |
| **Flink MiniCluster** | Integration testing | Java |
| **Go testing/iotest** | I/O failure injection | Go |
| **testcontainers-go** | DB containers for integration tests | Go |
| **k6** | Load testing HTTP APIs | JavaScript |
| **chaos-mesh** | Kubernetes chaos engineering | YAML/Go |

---

## FAQ


{{< faq q="How much coverage is enough for a Core Banking system?" >}}
There is no absolute number, but follow the **3-layer rule**:
- **Unit tests**: ≥90% coverage for business logic (balance calculations, state machines).
- **Integration tests**: Entire happy path + top 5 failure scenarios for each API.
- **Chaos engineering**: At least once per sprint involving network partitions and clock skew.

More important than coverage % is **coverage of failure modes** — specifically concurrent scenarios that cannot be tested with sequential unit tests.
{{< /faq >}}

{{< faq q="Can Flink TestHarness test the entire pipeline?" >}}
TestHarness is good for **operator-level unit tests** (testing a single operator in isolation with mock inputs). But to test the entire pipeline (Kafka source → CEP → ML inference → Kafka sink), you need to use a **MiniCluster** or a staging environment with a real Kafka/Flink cluster.
{{< /faq >}}

{{< faq q="Should I mock or integration-test the database in ledger tests?" >}}
**Do not mock the database** for ledger invariant tests. Use **testcontainers-go** to spin up a real PostgreSQL/TiDB instance in Docker — this actually tests race conditions, deadlocks, and ACID properties that a mock cannot reproduce. Mocks are only appropriate for external services (Kafka, SWIFT/NAPAS gateway, notification service).
{{< /faq >}}

{{< faq q="How do I detect silent data corruption in production?" >}}
Run **continuous reconciliation** — a background job that reads from the event store and recomputes the balance, comparing it against the CQRS read model. Any difference → P1 alert. The interval depends on transaction volume: 5 minutes for large systems, 1 hour for smaller systems. This acts as the "immune system" of Core Banking.

---
{{< /faq >}}
## Series Conclusion: Core Banking Architecture

Throughout the 8 parts of this series, we have traversed the entire stack of a production-grade Core Banking system:

| Part | Core Concepts | Key Benchmarks |
|------|------------------|---------------------|
| 1 | Double-Entry Ledger Schema, TigerBeetle Zig | 1M TPS single-threaded |
| 2 | Distributed SQL, TrueTime, HLC, Percolator | 1-3ms TSO overhead |
| 3 | Event Sourcing, CQRS, Outbox Pattern | <1ms vs 200ms balance lookup |
| 4 | Saga Orchestration, Temporal, DLQ | 10-50ms per orchestration hop |
| 5 | ISO 20022, XML streaming parser | JSON 10-30x faster than XML |
| 6 | FAPI 2.0, DPoP, mTLS | <0.1ms pooled mTLS overhead |
| 7 | Flink CEP, RocksDB, ML inference | 50-100ms fraud scoring SLA |
| 8 | SDET handbook, chaos engineering | 0 double-spends, 0 imbalances |

**Related Content to Explore Next:**
- [Composable Banking Architecture](/posts/composable-banking-architecture/) — From monolith to modular core
- [PayPay Architecture](/series/paypay-architecture/) — Scaling to 70M users with TiDB and Kafka idempotency
- [High Concurrency Systems](/series/high-concurrency-systems/) — Distributed locking and idempotency APIs
