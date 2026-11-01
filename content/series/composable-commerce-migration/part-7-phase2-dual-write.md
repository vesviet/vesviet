---
title: "Part 7: Phase 2 — Dual-Write with Dapr PubSub"
date: 2026-05-20T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "Enable write APIs on Go microservices while Magento runs live: event-driven dual-write via Dapr PubSub, Transactional Outbox, and conflict resolution."
categories: ["Series", "Software Engineering", "Data Architecture"]
tags: ["Debezium", "CDC", "Kafka", "MySQL", "PostgreSQL"]
series: ["composable-commerce-migration"]
weight: 8
slug: "part-7-phase2-dual-write"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-7-phase2-dual-write/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 7: Phase 2 — Dual-Write: CDC & Kafka Synchronization"
  relative: false
keywords: ["change data capture debezium", "kafka dual write ecommerce", "data reconciliation microservices", "zero data loss migration"]
mermaid: true
---

[← Previous Chapter: Part 6: Phase 1 — Strangler Fig Read-Only](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) | [Series Table of Contents](/series/composable-commerce-migration/) | [Next Chapter: Part 8: Phase 3 — Full Cutover Zero Downtime →](/series/composable-commerce-migration/part-8-phase3-full-cutover/)

---

> **Answer-first:** Phase 2 enables write APIs on the Go microservice system alongside Magento thanks to asynchronous Dual-Write via Dapr Pub/Sub and the Transactional Outbox, with feature flags and automatic data conflict resolution.

---

In Phase 1, both systems existed side by side but only one of them was allowed to write data: Magento. In Phase 2, both systems write at the same time. This is the most technically complex stage — and the place where most migration projects corrupt their own data if they do not have a crystal-clear conflict resolution strategy prepared up front.

**Answer-first:** Following 2026 event-driven architecture standards, Phase 2 uses **event-driven dual-write** through the Transactional Outbox — strictly avoiding raw dual-write, which silently produces inconsistency. Each microservice writes to its own PostgreSQL first, then publishes a domain event to Dapr PubSub atomically. A service called `magento-sync-adapter` subscribes to those events and writes them back into Magento, ensuring eventual consistency. Conflict cases (when both systems modify the same record at the same time) are settled by a matrix of 5 policies: timestamp comparison for customer profiles, microservices-win for order state, and sum-and-reconcile for coupon usage counts. Experience from large-scale migrations shows that designing idempotent consumers is the key to survival at this stage.

## 1. Why Not Use Raw Dual-Write?

Raw dual-write means: call the write against both databases directly inside the same request handler:

```go
// ❌ DEAD WRONG: Raw dual-write — if either half fails, the data is corrupted
func (h *CustomerHandler) CreateCustomer(ctx context.Context, req *Request) (*Response, error) {
    // Write #1: Into the microservice's PostgreSQL
    customer, err := h.customerRepo.Create(ctx, req)
    if err != nil { return nil, err }

    // Write #2: Into the Magento API (synchronous call)
    _, err = h.magentoClient.CreateCustomer(ctx, customer)
    if err != nil {
        // The call to Magento failed — BUT the customer IS ALREADY SAVED in the microservice's DB
        // The data is now inconsistent. There is no recovery path.
        return nil, err
    }
    return customer, nil
}
```

This falls apart because no atomic transaction can span two independent systems. Suppose the Magento API hiccups (goes down) for about 200ms right at the moment of the call (timeouts happen all the time) — you end up with a customer sitting plainly in the microservice's database yet completely invisible in Magento. This is a silent inconsistency — the microservice throws no error in the response, and the customer's account appears to work normally until they attempt an operation that requires Magento to know they exist.

## 2. Event-Driven Dual-Write: The Safe Design Pattern

Phase 2 uses a three-step process:

```
Step 1: Client → Gateway → Customer Service
Step 2: Customer Service:
    a. Write to PostgreSQL (the master data — the microservice now holds life-and-death control)
    b. Publish a "customer.updated" event to Dapr PubSub (wrapped inside the outbox transaction)
Step 3: magento-sync-adapter:
    a. Subscribes to the "customer.updated" event
    b. Writes back to Magento's REST API
    c. On failure → drop into the DLQ → wait for manual review
```

The Outbox design pattern in Step 2 (explained plainly in [Part 9](/series/composable-commerce-migration/part-9-outbox-saga/)) carries an ironclad set of guarantees: if the PostgreSQL transaction commits successfully, the event WILL be published eventually. If the transaction rolls back, no event escapes.

```go
// customer-service/internal/biz/customer_usecase.go

func (uc *CustomerUseCase) CreateCustomer(ctx context.Context, c *Customer) (*Customer, error) {
    var created *Customer

    // Transactional: write the customer + insert the event into the outbox in ONE transaction
    err := uc.tx.Execute(ctx, func(tx *sql.Tx) error {
        var err error
        created, err = uc.repo.CreateWithTx(ctx, tx, c)
        if err != nil { return err }

        // Insert the outbox event — the OutboxProcessor worker will pick it up and send it later
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

## 3. The magento-sync-adapter Service

This is an entirely new service whose sole job is to subscribe to domain events from the microservices and sync them back into Magento:

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
          value: "timestamp"   # Modes: timestamp | microservices-wins | magento-wins
```

The Dapr subscription configuration:

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
  deadLetterTopic: migration.dlq    # Failed syncs land here and wait for manual review
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

Throughout Phase 2, both Magento and the microservices have permission to modify the same records. The conflict resolver cleans up this battlefield according to the data type:

| Entity | Conflict Policy | Rationale |
|---|---|---|
| **Customer profile** (name, email, phone number) | Timestamp-based: last write wins | Both systems have legitimate reasons to update customer data |
| **Order status** | Microservices win | The entire order state machine has already been moved into the Order Service |
| **Stock quantity** | Microservices win | Real-time stock reservations are now owned outright by the Warehouse Service |
| **Product price** | Admin decision (Pricing Service) | Basket prices may only be modified from the Seller Centre via the Pricing Service |
| **Coupon usage count** | Sum + reconcile | Both systems legitimately increment this counter at the same time |

### Timestamp-Based Resolution (For Customer Profiles)

```go
// magento-sync-adapter/internal/resolver/customer_resolver.go

func (r *ConflictResolver) ResolveCustomerChange(ctx context.Context, event MigrationEvent) error {
    // Fetch the current state from the microservice's DB
    current, err := r.customerRepo.FindByMagentoID(ctx, event.MagentoID)
    if err != nil && !errors.Is(err, ErrNotFound) {
        return fmt.Errorf("fetching current customer: %w", err)
    }

    // No conflict: this is a brand-new record
    if current == nil {
        return r.customerRepo.UpsertFromEvent(ctx, event)
    }

    magentoUpdatedAt := event.UpdatedAt
    microUpdatedAt := current.UpdatedAt

    switch {
    case magentoUpdatedAt.After(microUpdatedAt):
        // The Magento change is newer → overwrite the microservice's data with Magento's
        return r.customerRepo.UpsertFromEvent(ctx, event)

    case microUpdatedAt.After(magentoUpdatedAt):
        // The microservice change is newer → push the microservice's data back to Magento
        return r.magentoAdapter.UpdateCustomer(ctx, current)

    default:
        // Timestamps are exactly equal → idempotent, both sides already in sync, do nothing
        return nil
    }
}
```

### Coupon Usage Reconciliation

```go
// magento-sync-adapter/internal/resolver/coupon_resolver.go

func (r *ConflictResolver) ResolveCouponUsage(ctx context.Context, event MigrationEvent) error {
    magentoCount := event.Data["times_used"].(int64)
    microCount, err := r.promotionRepo.GetUsageCount(ctx, event.CouponCode)
    if err != nil { return err }

    // Neither side's number is absolute truth — just take the max
    // (This is the safe choice: it prevents over-redeeming; it may slightly overcount if a sync lags)
    maxCount := max(magentoCount, microCount)

    if err := r.promotionRepo.SetUsageCount(ctx, event.CouponCode, maxCount); err != nil {
        return err
    }

    return r.magentoAdapter.UpdateCouponUsage(ctx, event.CouponCode, maxCount)
}
```

## 5. Migration Order Service by Service

Phase 2 does not enable the write flags all at once — it follows an ascending risk order:

### Step 1: Customer Service (Lowest Risk)

```bash
#!/bin/bash
# Enable customer writes on the microservice

# Turn on the write feature flag
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_write": "true"}}'

# Monitor closely for 30 minutes
./scripts/monitor-dual-write.sh --service=customer --duration=1800

# Validate: sample 1,000 random records to check consistency
./scripts/validate-dual-write.sh --service=customer --sample=1000
```

Monitoring watches for: write latency > 500ms (an SLA violation), data consistency lag > 5s, and any messages stuck in `migration.dlq` > 0 (any failed sync must be investigated before proceeding).

### Step 2: Catalog Service (Medium Risk)

Only run this after the Customer Service has been stable for a full 72 hours:

```bash
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"catalog_write": "true"}}'

./scripts/monitor-dual-write.sh --service=catalog --duration=1800
./scripts/validate-dual-write.sh --service=catalog --sample=500
```

Catalog sits in the medium-risk tier because product data is less sensitive than order data — a briefly inaccurate product description may be an eyesore, but it does not cause financial damage.

### Step 3: Order Service (Ceiling-Level Risk)

To migrate the Order Service, you are required to have an explicit database backup before flipping the switch:

```bash
#!/bin/bash
# HIGH RISK — Requires sign-off from the CTO or Tech Lead

echo "⚠️  Dual-write for the Order Service requires manual approval"
read -p "Have you created a Magento DB backup within the last 30 minutes? [yes/no]: " CONFIRM
[ "$CONFIRM" != "yes" ] && echo "Aborting. Go take a backup first." && exit 1

# Enable the flag with stricter settings: health check every 10s, strict validation
kubectl patch configmap feature-flags -n production \
  --patch '{
    "data": {
      "order_write": "true",
      "order_health_check_interval": "10",
      "order_strict_validation": "true"
    }
  }'

# Extended monitoring window: 1 hour instead of 30 minutes
./scripts/monitor-dual-write.sh --service=order --duration=3600
./scripts/validate-dual-write.sh --service=order --sample=1000
```

The health check interval shrinks to 10 seconds (versus 30 seconds for Customer), which means the Order Service's automatic fallback trips far earlier — a life-or-death factor, because dropping an order means an enraged customer and refund liability.

## 6. Monitoring the DLQ: Your Early Warning System

Any event that cannot be synced to Magento lands in `migration.dlq`. Throughout Phase 2, this DLQ must be treated as a **zero-tolerance zone**. If the DLQ is non-empty, your data is already inconsistent:

```bash
# Check the DLQ message count (run this at the start of every on-call shift)
dapr publish --publish-app-id ops-tool --pubsub pubsub \
  --topic migration.dlq.stats --data '{}'

# Expected result: 0 messages
# If > 0: halt everything, investigate until resolved before enabling the next service's write flag
```

A DLQ handler service takes on the job of processing failed events and blaring alerts into the `#migration-issues` Slack channel, attaching the event payload and the error message.

## 7. Phase 2 Acceptance Criteria

| Metric | Target | When to Measure |
|---|---|---|
| Write performance | < 500ms p99 | Monitored continuously in Prometheus |
| Data sync lag | < 5 seconds for critical data | Consistency check script every 15 minutes |
| DLQ message count | 0 | Must be checked before enabling each service's write flag |
| Automatic rollback time | < 10 seconds to trip the fallback | Thoroughly tested in deployment rehearsals |
| Zero downtime | 0 errors on any write operation | Across the entirety of Phase 2 |

## Next Steps

With Phase 2 complete, every write hits a microservice first and is then synced back to Magento. Magento has now been formally demoted to a follower — it is no longer the source of truth. In [Part 8: Phase 3 — Full Cutover](/series/composable-commerce-migration/part-8-phase3-full-cutover/), we switch off the reverse sync entirely, steer 100% of traffic into the microservices while keeping Magento on hot standby, and complete the decommissioning using ArgoCD GitOps.

## FAQ

### What is the biggest risk of dual-write, and how does this approach address it?

The biggest risk is **partial failure**: the microservice writes successfully, but the sync path to Magento breaks midway, leaving the two sides' data quietly diverged. The event-driven pattern solves this with the Transactional Outbox: the event in the outbox is written to the database within the SAME transaction as the business change. If one fails, both fail — atomically. The `magento-sync-adapter` then stubbornly (asynchronously) retries the sync with exponential backoff, and any stubbornly failing events are dropped into the DLQ for human investigation — they are never silently lost.

### Why does the conflict resolution policy for customer data differ from order data?

Customer data may quite legitimately be modified by both systems concurrently — a customer can update their address on the Magento storefront while, at the same moment, a microservice API call overwrites their phone number. Timestamp-based resolution handles this case smoothly: the update that arrives last wins. Order data is a different beast: once an order has been created on the microservice, Magento is absolutely NOT ALLOWED to touch its state, because the microservice's state machine is the authoritative source for the order lifecycle. That is why order status uses the strict microservices-win policy, regardless of timestamps.

### How long does Phase 2 typically take?

The minimum safe budget is **3–4 weeks** if you want every service to get its full monitoring soak time: Customer Service (1 week to stabilize), Catalog Service (1 week), and Order Service (10 days, stepped gradually). Any team dreaming of cramming Phase 2 into a few days usually gets beaten black and blue by edge cases that slip past the conflict resolver — especially coupon usage counts and inventory levels under concurrent updates. Stretching the timeline is not bureaucracy; it is the minimum observation window required to catch anomalies before they compound into catastrophe.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. See the full table of contents for the complete architectural context.*

*Need help assessing the risk of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 6: Phase 1 — Strangler Fig Read-Only](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) | [Series Table of Contents](/series/composable-commerce-migration/) | [Next Chapter: Part 8: Phase 3 — Full Cutover Zero Downtime →](/series/composable-commerce-migration/part-8-phase3-full-cutover/)
