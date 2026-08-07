---
title: "Phase 2 Dual-Write Sync & Dapr Conflict Resolution"
description: "Phase 2 Magento migration strategy implementing Dapr PubSub dual-write event synchronization, 5-policy conflict resolution, and DLQ monitoring."
date: "2026-05-20T10:00:00+07:00"
lastmod: "2026-07-03T15:41:55+07:00"
draft: false
weight: 8
slug: "part-7-phase2-dual-write"
ShowToc: true
TocOpen: true
categories: ["Software Engineering", "Backend", "Migration"]
tags: ["Dual Write", "Dapr", "PubSub", "Conflict Resolution", "Feature Flags", "Magento Migration", "Event-Driven"]
series: ["Composable Commerce Migration"]
series_order: 7
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/ecommerce-composable-cover.png"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-7-phase2-dual-write/"
---

> **Prerequisite:** Familiarity with the concepts introduced in [Part 6 — Phase1 Strangler Fig](/series/composable-commerce-migration/part-6-phase1-strangler-fig/). Review it first if the terminology in this part is unfamiliar.

In Phase 1, both systems existed but only one wrote data: Magento. In Phase 2, both systems write data simultaneously. This is the most technically complex phase — and the one where most migrations introduce data corruption if they don't have an explicit conflict resolution strategy.

**Answer-first:** Phase 2 implements event-driven dual-write where microservices update PostgreSQL and publish domain events to Dapr PubSub. The sync adapter service updates legacy Magento asynchronously. Concurrent write conflicts are resolved through deterministic conflict resolution policies tailored to specific domain data types.

> **Phase 2 Technical Guide:** For the full end-to-end migration architecture and topology, see [Migrating Monoliths to Microservices](/posts/ecommerce-architecture-composable-migration/).

## 1. Why Not Raw Dual Write?

Raw application-level dual writing causes data drift and distributed deadlock during network partition failures; event-driven sync is mandatory.

Raw dual write attempts to mutate both legacy MySQL and microservice PostgreSQL directly within a single application HTTP request handler:

```go
// ❌ WRONG: Raw dual write — partial failure corrupts state
func (h *CustomerHandler) CreateCustomer(ctx context.Context, req *Request) (*Response, error) {
    // Write 1: Microservice PostgreSQL
    customer, err := h.customerRepo.Create(ctx, req)
    if err != nil { return nil, err }

    // Write 2: Magento API (called synchronously)
    _, err = h.magentoClient.CreateCustomer(ctx, customer)
    if err != nil {
        // Magento call failed — but customer ALREADY exists in microservice DB
        // State is now inconsistent. No recovery path.
        return nil, err
    }
    return customer, nil
}
```

This pattern introduces catastrophic state corruption in distributed architectures for three fundamental reasons:
1. **Lack of Distributed Atomicity**: Two-Phase Commit (2PC) protocols across heterogeneous HTTP APIs create blocking locks, extreme latency spikes, and low availability.
2. **Network Partitions & Split-Brain**: If the legacy Magento API suffers transient timeouts (e.g. 500ms GC pause), the microservice transaction commits while the monolith write fails, leaving system state permanently desynchronized.
3. **Unbounded Retry Failure**: Retrying failed synchronous writes in the HTTP request thread exhausts gateway connection pools and triggers cascading backend outages.

## 2. Event-Driven Dual Write: The Safe Pattern

Event-driven dual write uses asynchronous Dapr PubSub channels and transactional outbox logs to synchronize state changes safely.

To guarantee zero data loss during dual-write operation, the architecture splits mutation handling into three asynchronous, isolated stages. The ASCII sequence diagram below illustrates the decoupled event lifecycle:

```
Step 1: Client → Gateway → Customer Service
Step 2: Customer Service:
    a. Write to PostgreSQL (primary — microservice is authoritative)
    b. Publish "customer.updated" event to Dapr PubSub (in outbox transaction)
Step 3: magento-sync-adapter:
    a. Subscribes to "customer.updated"
    b. Writes to Magento REST API
    c. On failure → DLQ → manual review
```

In 2026 architectures, Step 2 is backed by Change Data Capture (CDC) utilizing Debezium Server streaming to lightweight event brokers like Redpanda or NATS JetStream. Using the Debezium Outbox Single Message Transform (SMT), database outbox table inserts are transformed directly into structured CloudEvents without requiring manual outbox polling loops.

Additionally, production validation leverages **Shadow Traffic Verification (Dark Traffic)**: production write traffic payloads are cloned asynchronously to test microservice environments to compare state mutations against legacy outputs prior to enabling live dual-write flags.

The Go application code below demonstrates how domain updates and outbox records commit within a single local database transaction:

```go
// customer-service/internal/biz/customer_usecase.go

func (uc *CustomerUseCase) CreateCustomer(ctx context.Context, c *Customer) (*Customer, error) {
    var created *Customer

    // Transactional: write customer + outbox event in same transaction
    err := uc.tx.Execute(ctx, func(tx *sql.Tx) error {
        var err error
        created, err = uc.repo.CreateWithTx(ctx, tx, c)
        if err != nil { return err }

        // Insert outbox event — captured by Debezium Outbox SMT / OutboxProcessor
        return uc.outbox.InsertWithTx(ctx, tx, events.OutboxEvent{
            Topic:   "customer.updated",
            Payload: marshalCustomer(created),
            Source:  "microservices",
        })
    })
    if err != nil { return nil, err }

    return created, nil
}
```

## 3. The magento-sync-adapter

The `magento-sync-adapter` Go service listens to Dapr event channels, translating microservice domain events back into Magento REST API calls.

The `magento-sync-adapter` operates as a dedicated bridge service between Dapr PubSub channels and legacy Magento REST endpoints. To protect Magento from REST API rate-limiting and connection saturation, the adapter implements client-side rate limiting (100 req/sec bucket), exponential backoff retries with jitter, and circuit breaker isolation.

The Kubernetes deployment manifest below configures the adapter service alongside Dapr sidecar annotations and environment credentials:

```yaml
# k8s/magento-sync-adapter.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: magento-sync-adapter
  namespace: migration
spec:
  replicas: 2
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "magento-sync-adapter"
        dapr.io/app-port: "8080"
    spec:
      containers:
      - name: magento-sync-adapter
        image: magento-sync-adapter:v1.0.0
        env:
        - name: MAGENTO_BASE_URL
          value: "https://magento.internal"
        - name: MAGENTO_TOKEN
          valueFrom:
            secretKeyRef:
              name: magento-api-creds
              key: token
        - name: CONFLICT_RESOLUTION_MODE
          value: "timestamp"   # Options: timestamp | microservices-wins | magento-wins
```

Dapr subscription CRDs bind domain event topics to specific adapter HTTP handler endpoints:

```yaml
# dapr-subscriptions.yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: reverse-sync-customer
  namespace: migration
spec:
  pubsubname: pubsub
  topic: customer.updated
  route: /reverse-sync/customer
  deadLetterTopic: migration.dlq    # Failed syncs land here for manual review
---
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: reverse-sync-order
  namespace: migration
spec:
  pubsubname: pubsub
  topic: order.placed
  route: /reverse-sync/order
  deadLetterTopic: migration.dlq
```

## 4. The Conflict Resolution Matrix

The conflict resolution matrix defines 5 deterministic policies (e.g. timestamp priority, authority tier) to resolve concurrent state updates.

When dual-writing across legacy monoliths and microservices, state mutations can collide. Modern 2026 architectures replace raw NTP timestamps with **Hybrid Logical Clocks (HLC)** to guarantee causality ordering despite physical clock drift. Background reconciliation processes periodically calculate Merkle tree / SHA256 checksums between MySQL and PostgreSQL tables to catch and repair silent state drift automatically.

| Entity | Conflict Policy | Rationale |
|---|---|---|
| **Customer profile** (name, email, phone) | Timestamp-based (HLC): newer write wins | Both systems can legitimately update customer data |
| **Order status** | Microservices wins | Order state machine lives entirely in Order Service |
| **Inventory / stock quantity** | Microservices wins | Real-time reservations managed by Warehouse Service |
| **Product price** | Admin decision (Pricing Service) | Prices are only written from Seller Centre via Pricing Service |
| **Coupon usage count** | Sum + reconcile (CRDT Max) | Both systems may increment the count concurrently |

### Timestamp-Based Resolution (Customer Profile)

The Go conflict resolver below evaluates incoming event timestamps against stored entity state, determining whether to update the local microservice repository or trigger a reverse update back to Magento:

```go
// magento-sync-adapter/internal/resolver/customer_resolver.go

func (r *ConflictResolver) ResolveCustomerChange(ctx context.Context, event MigrationEvent) error {
    // Fetch current state from microservice DB
    current, err := r.customerRepo.FindByMagentoID(ctx, event.MagentoID)
    if err != nil && !errors.Is(err, ErrNotFound) {
        return fmt.Errorf("fetching current customer: %w", err)
    }

    // No conflict: new record
    if current == nil {
        return r.customerRepo.UpsertFromEvent(ctx, event)
    }

    magentoUpdatedAt := event.UpdatedAt
    microUpdatedAt := current.UpdatedAt

    switch {
    case magentoUpdatedAt.After(microUpdatedAt):
        // Magento change is newer → apply Magento data to microservice
        return r.customerRepo.UpsertFromEvent(ctx, event)

    case microUpdatedAt.After(magentoUpdatedAt):
        // Microservice change is newer → push micro data back to Magento
        return r.magentoAdapter.UpdateCustomer(ctx, current)

    default:
        // Equal timestamps → idempotent, both systems agree
        return nil
    }
}
```

### Coupon Usage Reconciliation

For shared counter aggregations like promo coupon redemption limits, neither system's counter is strictly authoritative. The Go implementation below applies maximum-value convergence to ensure coupon quotas are strictly respected across environments:

```go
// magento-sync-adapter/internal/resolver/coupon_resolver.go

func (r *ConflictResolver) ResolveCouponUsage(ctx context.Context, event MigrationEvent) error {
    magentoCount := event.Data["times_used"].(int64)
    microCount, err := r.promotionRepo.GetUsageCount(ctx, event.CouponCode)
    if err != nil { return err }

    // Neither system's count is authoritative — take the maximum
    // (safer: prevents over-redeeming; slightly over-reports if there's a lag)
    maxCount := max(magentoCount, microCount)

    if err := r.promotionRepo.SetUsageCount(ctx, event.CouponCode, maxCount); err != nil {
        return err
    }

    return r.magentoAdapter.UpdateCouponUsage(ctx, event.CouponCode, maxCount)
}
```

## 5. Per-Service Migration Sequence

Per-service migration sequences order domain transitions logically: Catalog first, Customer second, Cart third, and Checkout last.

Enabling dual-write mode proceeds incrementally following a strict domain dependency tree. Low-risk peripheral services transition first, allowing engineering teams to validate outbox event propagation before enabling mission-critical transactional domains.

### Step 1: Customer Service (Lowest Risk)

The shell script below patches the production ConfigMap to activate customer domain writes and kicks off real-time validation monitoring:

```bash
#!/bin/bash
# Enable customer writes on microservice

# Enable write flag
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_write": "true"}}'

# Monitor for 30 minutes
./scripts/monitor-dual-write.sh --service=customer --duration=1800

# Validate: sample 1000 records for consistency
./scripts/validate-dual-write.sh --service=customer --sample=1000
```

Monitoring inspects three vital metrics: p99 write latency (< 500ms SLA), data consistency lag (< 5s between PostgreSQL and MySQL), and zero accumulated messages in `migration.dlq`.

### Step 2: Catalog Service (Medium Risk)

Catalog write migration initiates after Customer Service maintains 72 consecutive hours of zero-drift dual-write execution. The command snippet below patches the catalog write feature flag:

```bash
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"catalog_write": "true"}}'

./scripts/monitor-dual-write.sh --service=catalog --duration=1800
./scripts/validate-dual-write.sh --service=catalog --sample=500
```

Catalog is medium risk because product metadata changes (e.g. title updates, category assignments) affect store presentation but do not directly mutate active financial ledger entries.

### Step 3: Order Service (Highest Risk)

Order Service dual-write represents the highest operational risk. The activation script below mandates fresh database backups and interactive engineering sign-off prior to flag enablement:

```bash
#!/bin/bash
# HIGH RISK — requires CTO/Engineering Lead sign-off

echo "⚠️  Order Service dual-write requires manual approval"
read -p "Have you taken a Magento DB backup in the last 30 minutes? [yes/no]: " CONFIRM
[ "$CONFIRM" != "yes" ] && echo "Aborting. Take backup first." && exit 1

# Stricter feature flag: 10-second health check interval, strict validation
kubectl patch configmap feature-flags -n production \
  --patch '{
    "data": {
      "order_write": "true",
      "order_health_check_interval": "10",
      "order_strict_validation": "true"
    }
  }'

# Extended monitoring: 1 hour instead of 30 minutes
./scripts/monitor-dual-write.sh --service=order --duration=3600
./scripts/validate-dual-write.sh --service=order --sample=1000
```

Setting a 10-second health check probe interval ensures the API Gateway trips automatic fallback within 10 seconds of any upstream anomaly, protecting live customer checkout flows.

## 6. DLQ Monitoring: Your Early Warning System

Dead-letter queue (DLQ) monitoring alerts engineering teams to failed event sync attempts, providing manual retry interfaces and payload inspection.

Events failing serialization or encountering persistent Magento API errors land in `migration.dlq`. During Phase 2, DLQ depth must be strictly enforced as zero. Accumulated DLQ messages indicate active data drift between microservice PostgreSQL and legacy MySQL.

Operators execute the following command script to query active DLQ queue metrics across pub/sub channels:

```bash
# Check DLQ message count (run as pre-shift check)
dapr publish --publish-app-id ops-tool --pubsub pubsub \
  --topic migration.dlq.stats --data '{}'

# Expected: 0 messages
# If > 0: investigate before enabling next service's write flag
```

A dedicated DLQ handler worker service parses unroutable CloudEvents, formats structured alert payloads, and triggers high-priority alerts to operational channels with event context and stack traces. Automated replay tooling allows engineers to re-inject fixed events into Dapr PubSub channels once underlying API issues are resolved.

## 7. Phase 2 Success Criteria

Phase 2 success requires zero un-reconciled data drift across dual-written domains over a continuous 14-day operational window.

Before advancing to Phase 3 full traffic cutover, the architecture must maintain absolute stability across all dual-written domains according to the following metric SLAs:

| Metric | Target | When to Measure |
|---|---|---|
| Write performance | < 500ms p99 | Continuously via Prometheus |
| Data consistency lag | < 5 seconds for critical data | Every 15 minutes via consistency check |
| DLQ message count | 0 | Before enabling each service's write flag |
| Automatic rollback time | < 10 seconds to fallback | Tested during deployment rehearsal |
| Zero downtime | 0 errors on any write operation | Throughout Phase 2 |

## What's Next

Phase 3 completes the migration by executing full traffic cutover and decommissioning legacy Magento infrastructure.

With Phase 2 complete, all writes go to microservices first, then sync back to Magento. Magento is now a follower, not the source of truth. [Part 8: Phase 3 — Full Cutover](/series/composable-commerce-migration/part-8-phase3-full-cutover/) disables the reverse sync, shifts 100% of traffic to microservices with Magento on hot standby, and completes the decommission using ArgoCD GitOps.

## FAQ

Event-driven dual write enables safe multi-phase migration by ensuring eventual consistency between legacy monoliths and new Go microservices.

{{< faq q="What is the main risk of dual-write and how does this approach mitigate it?" >}}
The main risk is **partial failure**: microservice writes succeed but the Magento sync fails, leaving data inconsistent between systems. The event-driven pattern mitigates this with the Transactional Outbox: the outbox event is written in the same database transaction as the business change. If either fails, both fail — atomically. The `magento-sync-adapter` then retries the sync asynchronously with exponential backoff, and failed events land in the DLQ for investigation rather than being silently lost.
{{< /faq >}}

{{< faq q="Why is the conflict resolution policy different for customer data vs order data?" >}}
Customer data can legitimately be updated by both systems concurrently — a customer might update their address on the Magento storefront while a microservice API updates their phone number. Timestamp-based resolution handles this safely: whichever update is more recent wins. Order data is different: once an order is created in the microservice, Magento should never override its status because the microservice's state machine is the authoritative source of order lifecycle events. That's why Order status uses microservices-wins policy regardless of timestamps.
{{< /faq >}}

{{< faq q="How long does Phase 2 typically take?" >}}
The minimum safe timeline is **3–4 weeks** when each service gets proper monitoring time: Customer Service (1 week stabilization), Catalog Service (1 week), and Order Service (10 days graduated ramp). Teams that try to compress Phase 2 into days tend to miss edge cases in the conflict resolver — particularly for coupon usage counts and inventory levels during concurrent updates. The extended timeline is not bureaucracy; it is the minimum observation window needed to catch anomalies before they compound.

{{< /faq >}}

---

🔗 **Next Step:** Continue to [Part 8 — Phase3 Full Cutover](/series/composable-commerce-migration/part-8-phase3-full-cutover/) for the following module in the series.
