---
title: "Part 7: Phase 2 — Dual-Write: Dapr PubSub + Conflict Resolution"
description: "Enable write APIs on Go microservices while Magento stays live: event-driven dual-write via Dapr PubSub, a 5-policy conflict resolution matrix, magento-sync-adapter, and per-service migration sequence."
date: 2026-05-20T10:00:00+07:00
lastmod: 2026-06-24T10:00:00+07:00
draft: false
weight: 8
slug: "part-7-phase2-dual-write"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Backend Architecture", "Migration"]
tags: ["Dual Write", "Dapr", "PubSub", "Conflict Resolution", "Feature Flags", "Magento Migration", "Event-Driven"]
series: ["Composable Commerce Migration"]
series_order: 7
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
---

In Phase 1, both systems existed but only one wrote data: Magento. In Phase 2, both systems write data simultaneously. This is the most technically complex phase — and the one where most migrations introduce data corruption if they don't have an explicit conflict resolution strategy.

**Answer-first:** Phase 2 uses event-driven dual-write — not raw database dual-write. Microservices write to their PostgreSQL first, then publish a domain event to Dapr PubSub. The `magento-sync-adapter` service subscribes to those events and writes back to Magento. Conflicts (both systems update the same record concurrently) are resolved by a 5-policy matrix that differs by data type: timestamp-based for customer profiles, microservices-wins for order status and stock levels, and summation reconciliation for coupon usage counts.

## 1. Why Not Raw Dual Write?

Raw dual write means: write to both databases in the same request handler:

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

This fails because there is no atomic transaction spanning two independent systems. If Magento's API is down for 200ms during the call (timeouts happen), you have a customer in the microservice database that doesn't exist in Magento. The inconsistency is silent — no error in the microservice response, and the customer appears to work normally until they try to do something that requires Magento to know about them.

## 2. Event-Driven Dual Write: The Safe Pattern

Phase 2 uses a three-step pattern:

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

The outbox pattern in Step 2 (from [Part 9](/series/composable-commerce-migration/part-9-outbox-saga/)) guarantees: if the PostgreSQL transaction commits, the event will eventually be published. If the transaction rolls back, no event is published.

```go
// customer-service/internal/biz/customer_usecase.go

func (uc *CustomerUseCase) CreateCustomer(ctx context.Context, c *Customer) (*Customer, error) {
    var created *Customer

    // Transactional: write customer + outbox event in same transaction
    err := uc.tx.Execute(ctx, func(tx *sql.Tx) error {
        var err error
        created, err = uc.repo.CreateWithTx(ctx, tx, c)
        if err != nil { return err }

        // Insert outbox event — will be published by common/worker OutboxProcessor
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

This new service subscribes to microservice domain events and syncs them back to Magento:

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

Dapr subscription configuration:

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

During Phase 2, both Magento and microservices can update the same record. The conflict resolver handles this by data type:

| Entity | Conflict Policy | Rationale |
|---|---|---|
| **Customer profile** (name, email, phone) | Timestamp-based: newer write wins | Both systems can legitimately update customer data |
| **Order status** | Microservices wins | Order state machine lives entirely in Order Service |
| **Inventory / stock quantity** | Microservices wins | Real-time reservations managed by Warehouse Service |
| **Product price** | Admin decision (Pricing Service) | Prices are only written from Seller Centre via Pricing Service |
| **Coupon usage count** | Sum + reconcile | Both systems may increment the count concurrently |

### Timestamp-Based Resolution (Customer Profile)

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

Phase 2 enables write flags one service at a time, in order of risk:

### Step 1: Customer Service (Lowest Risk)

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

Monitoring looks for: write latency > 500ms (SLA breach), data consistency lag > 5s, `migration.dlq` message count > 0 (any failed sync needs investigation before proceeding).

### Step 2: Catalog Service (Medium Risk)

Run after Customer Service has been stable for 72 hours:

```bash
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"catalog_write": "true"}}'

./scripts/monitor-dual-write.sh --service=catalog --duration=1800
./scripts/validate-dual-write.sh --service=catalog --sample=500
```

Catalog is medium risk because product data is less critical than order data — a brief inconsistency on a product description page is visible but not financially damaging.

### Step 3: Order Service (Highest Risk)

Order Service migration requires an explicit database backup before enabling:

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

The 10-second health check interval (vs 30 seconds for Customer) means Order Service's automatic fallback triggers faster — critical because a lost order is a customer complaint and potentially a refund.

## 6. DLQ Monitoring: Your Early Warning System

Any event that fails to sync to Magento ends up in `migration.dlq`. During Phase 2, the DLQ must be **treated as zero-tolerance**. A non-empty DLQ means data inconsistency:

```bash
# Check DLQ message count (run as pre-shift check)
dapr publish --publish-app-id ops-tool --pubsub pubsub \
  --topic migration.dlq.stats --data '{}'

# Expected: 0 messages
# If > 0: investigate before enabling next service's write flag
```

A DLQ handler service processes failed events and sends alerts to `#migration-issues` Slack channel with the event payload and error message.

## 7. Phase 2 Success Criteria

| Metric | Target | When to Measure |
|---|---|---|
| Write performance | < 500ms p99 | Continuously via Prometheus |
| Data consistency lag | < 5 seconds for critical data | Every 15 minutes via consistency check |
| DLQ message count | 0 | Before enabling each service's write flag |
| Automatic rollback time | < 10 seconds to fallback | Tested during deployment rehearsal |
| Zero downtime | 0 errors on any write operation | Throughout Phase 2 |

## What's Next

With Phase 2 complete, all writes go to microservices first, then sync back to Magento. Magento is now a follower, not the source of truth. [Part 8: Phase 3 — Full Cutover](/series/composable-commerce-migration/part-8-phase3-full-cutover/) disables the reverse sync, shifts 100% of traffic to microservices with Magento on hot standby, and completes the decommission using ArgoCD GitOps.

## FAQ

### What is the main risk of dual-write and how does this approach mitigate it?

The main risk is **partial failure**: microservice writes succeed but the Magento sync fails, leaving data inconsistent between systems. The event-driven pattern mitigates this with the Transactional Outbox: the outbox event is written in the same database transaction as the business change. If either fails, both fail — atomically. The `magento-sync-adapter` then retries the sync asynchronously with exponential backoff, and failed events land in the DLQ for investigation rather than being silently lost.

### Why is the conflict resolution policy different for customer data vs order data?

Customer data can legitimately be updated by both systems concurrently — a customer might update their address on the Magento storefront while a microservice API updates their phone number. Timestamp-based resolution handles this safely: whichever update is more recent wins. Order data is different: once an order is created in the microservice, Magento should never override its status because the microservice's state machine is the authoritative source of order lifecycle events. That's why Order status uses microservices-wins policy regardless of timestamps.

### How long does Phase 2 typically take?

The minimum safe timeline is **3–4 weeks** when each service gets proper monitoring time: Customer Service (1 week stabilization), Catalog Service (1 week), and Order Service (10 days graduated ramp). Teams that try to compress Phase 2 into days tend to miss edge cases in the conflict resolver — particularly for coupon usage counts and inventory levels during concurrent updates. The extended timeline is not bureaucracy; it is the minimum observation window needed to catch anomalies before they compound.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? â†’ [Book a 1:1 Architecture Consultation](/hire/)*
