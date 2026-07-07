---
title: "Part 8: Phase 3 — Full Cutover: Zero Downtime + ArgoCD GitOps"
description: "Full Magento cutover: 25%→100% traffic migration for Order Service, 30-day rollback window, archive service, and ArgoCD+Kustomize GitOps deployment."
date: 2026-05-27T10:00:00+07:00
lastmod: 2026-07-03T15:41:55+07:00
draft: false
weight: 9
slug: "part-8-phase3-full-cutover"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Backend Architecture", "Migration", "DevOps"]
tags: ["GitOps", "ArgoCD", "Kustomize", "Zero Downtime", "Cutover", "Magento Migration", "Kubernetes"]
series: ["Composable Commerce Migration"]
series_order: 8
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/ecommerce-composable-cover.png"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
---

Phase 3 is the final act: 100% of traffic moves to microservices, Magento becomes a passive archive, and the platform runs entirely on Go microservices via GitOps. No PHP in the critical path. No Magento license renewal needed.

**Answer-first:** Customer and Catalog services cut over at 100% immediately (they've been stable through all of Phase 2). Order Service uses a graduated 25%→50%→75%→100% ramp over 10 days, with a monitoring hold at each step. Magento stays alive as a hot standby for 30 days — an `archive-service` syncs microservice data to Magento hourly (one-way, for regulatory compliance). All deployments use ArgoCD + Kustomize; a git commit triggers a production deployment within minutes.

## 1. The 6-Week Cutover Calendar

```
Week 1–2: Customer Service → 100% microservices
Week 3–4: Catalog Service → 100% microservices
Week 5–6: Order Service → 25% → 50% → 75% → 100%
Week 7+:  Magento hot standby (event bus stops, archive-service runs hourly)
Week 11:  Magento decommissioned (Day 30 of hot standby)
```

By Week 5, Customer and Catalog are fully migrated and have been running in production for 3+ weeks. The Debezium sync has been turned off for these domains (microservices are now the source of truth, no longer followers). Only Order Service still needs the graduated ramp because orders are irreversible financial transactions.

## 2. Customer + Catalog: Immediate 100% Cutover

```bash
#!/bin/bash
# week-1-customer-cutover.sh

echo "Week 1: Customer Service Full Cutover"

# Disable dual-write reverse sync for customer
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_magento_sync": "false"}}'

# Route 100% customer traffic to microservices
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_write": "true", "customer_read": "true", "customer_cutover": "true"}}'

# Start customer archive (hourly sync to Magento for 30 days)
curl -X POST "http://archive-service:8080/api/v1/start-archive" \
  -d '{"domain": "customer", "interval_seconds": 3600}'

# Monitor for 7 days
./scripts/monitor-cutover.sh --service=customer --duration=604800
echo "Customer Service cutover complete. Monitoring for 7 days."
```

The archive service (new in Phase 3) writes microservice data → Magento on a 1-hour schedule. This is a **one-way, read-only sync** — Magento can no longer write back. It serves as a warm backup and satisfies any regulatory requirements to keep data in the legacy system for a defined period.

## 3. Order Service: Graduated Traffic Ramp

Order Service gets special treatment because orders involve real money. The `order_cutover` feature flag accepts a `percentage` parameter that controls what fraction of new orders go to the microservice:

```go
// gateway-service/internal/router/order_router.go

func routeOrderRequest(c *gin.Context, clients *ServiceClients, flags *FlagStore) {
    flag := flags.Get("order_cutover")

    if !flag.Enabled || flag.Percentage == 0 {
        // Phase 2 mode: all orders to Order Service with Magento sync
        handleOrderViaMicroservice(c, clients.Order, true /* syncToMagento */)
        return
    }

    // Graduated ramp: hash customer ID to determine routing
    // (same customer always goes to same system during transition)
    customerID := c.GetHeader("X-Customer-ID")
    hash := fnv.New32a()
    hash.Write([]byte(customerID))
    bucket := hash.Sum32() % 100

    if bucket < uint32(flag.Percentage) {
        // This customer's orders go to microservice (no Magento sync)
        handleOrderViaMicroservice(c, clients.Order, false /* cutover: no sync */)
    } else {
        // Still routing to Magento for this customer
        proxyToMagento(c)
    }
}
```

Using customer ID hash (rather than random) ensures a customer's orders don't split between systems — all orders from `customer_id=X` go to the same system throughout the ramp period.

**The ramp schedule for Order Service (Week 5–6):**

| Day | Cutover % | Action on each step |
|---|---|---|
| Day 1 (Monday) | 25% | Enable flag, monitor for 3 days |
| Day 4 (Thursday) | 50% | Validate consistency, check DLQ=0, increment |
| Day 7 (Sunday) | 75% | Validate, check payment reconciliation |
| Day 10 (Wednesday) | 100% | Final cutover, disable Magento routing |

At each step, these conditions must be met before incrementing:
1. DLQ message count = 0 (no failed events)
2. p99 write latency < 200ms (Phase 3 SLA, tighter than Phase 2's 500ms)
3. Payment reconciliation: total revenue in microservice DB matches Magento
4. Zero customer complaints related to order creation

## 4. The Archive Service

```yaml
# k8s/archive-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: archive-service
  namespace: production
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: archive-service
        image: archive-service:v1.0.0
        args: ["--final-sync", "--compress"]
        env:
        - name: MICRO_DB_HOST
          value: "platform-db.production.svc.cluster.local"
        - name: MAGENTO_DB_HOST
          value: "magento-db.production.svc.cluster.local"
        - name: ARCHIVE_INTERVAL
          value: "3600"   # 1 hour
        - name: ARCHIVE_DOMAINS
          value: "customer,catalog,order,inventory"
```

Archive service behavior:
- Runs once per hour
- Reads from microservice PostgreSQL (authoritative)
- Writes to Magento MySQL (archive only, Magento writes disabled)
- Compresses data (JSON → gzip) for long-term storage
- Stops automatically after 30 days (Day 30 = Magento decommission)

## 5. ArgoCD GitOps: The Deployment Model After Migration

With Magento gone, all ongoing deployments use ArgoCD's GitOps model. The complete flow for a code change:

```
1. Developer: git push to feature branch
2. GitLab CI:
    a. Run unit tests + integration tests
    b. Build Docker image → push to registry
    c. Open MR → code review
3. MR merged to main:
    a. CI runs full test suite
    b. Builds image: order-service:v1.2.3
    c. Updates GitOps repo:
       git commit -m "Update order-service to v1.2.3"
       # Changes: gitops/apps/order-service/overlays/production/kustomization.yaml
       # From: newTag: v1.2.2
       # To:   newTag: v1.2.3
4. ArgoCD detects change in GitOps repo:
    a. Kustomize build: base + production overlay
    b. kubectl apply to production cluster
    c. Rolling update: 1 pod at a time, health check between each
5. ArgoCD rollback if unhealthy:
    git revert HEAD  # Reverts the image tag in GitOps repo
    ArgoCD detects revert → rolls back deployment automatically
```

No SSH to production servers. No manual `kubectl apply`. No "works on my machine" deployments. **Every production change is traceable to a Git commit.**

## 6. Kustomize: Base + Overlays Pattern

Each service has environment-specific overlays:

```
gitops/apps/order-service/
├── base/
│   ├── deployment.yaml          ← Common: service definition, port, probes
│   ├── service.yaml
│   ├── configmap.yaml           ← Non-secret config
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml  ← replicas: 1, resources: small
    └── production/
        ├── kustomization.yaml
        └── patch-replicas.yaml  ← replicas: 3, resources: production-sized
```

```yaml
# gitops/apps/order-service/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - path: patch-replicas.yaml
images:
  - name: order-service
    newTag: v1.2.3                 ← Updated by CI on every release
```

```yaml
# gitops/apps/order-service/base/deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: order-service
        image: order-service           # Tag set by overlay
        ports:
        - containerPort: 8001          # HTTP
        - containerPort: 9001          # gRPC
        livenessProbe:
          grpc:
            port: 9001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 7. Sync Waves: Ordered Deployment

ArgoCD Sync Waves ensure infrastructure components start before service components:

```yaml
# gitops/apps/order-service/base/deployment.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"   # Wave 2: services start after wave 1

# gitops/infrastructure/databases/postgresql.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # Wave 0: databases first

# gitops/infrastructure/dapr-components.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"   # Wave 1: Dapr before services
```

Sync wave order: `Databases (0) → Dapr components (1) → Services (2) → Gateway (3)`

## 8. Performance Validation: The 10× Load Test

Phase 3 success criterion: *"Handle 10× current production load."* The K6 load test runs during off-peak hours before declaring Phase 3 complete:

```javascript
// tests/load/phase3-validation.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    stages: [
        { duration: '5m', target: 100 },   // Ramp up
        { duration: '10m', target: 1000 }, // 10× normal load
        { duration: '5m', target: 0 },     // Ramp down
    ],
    thresholds: {
        'http_req_duration': ['p99<200'],  // 200ms p99 SLA
        'http_req_failed': ['rate<0.001'], // < 0.1% error rate
    },
};

export default function() {
    // Test Order creation (the highest-risk endpoint)
    const res = http.post('https://api.platform.com/api/v1/orders', JSON.stringify({
        customer_id: randomCustomerID(),
        items: [{ product_id: randomProductID(), quantity: 1 }],
        shipping_address: testAddress(),
        request_id: crypto.randomUUID(),
    }));

    check(res, { 'order created': (r) => r.status === 201 });
}
```

## 9. Magento Decommission: Day 30

After 30 days of hot standby without a rollback event:

```bash
#!/bin/bash
# day-30-decommission.sh

echo "Day 30: Decommissioning Magento hot standby"

# Step 1: Stop archive service
kubectl delete deployment archive-service -n production

# Step 2: Stop Debezium connector (if still running for any domain)
kubectl delete deployment sync-service -n migration

# Step 3: Export final Magento database backup
mysqldump --all-databases > /backup/magento-final-$(date +%Y%m%d).sql.gz

# Step 4: Shut down Magento application servers
kubectl delete namespace magento

# Step 5: Remove Magento feature flags from Gateway
kubectl patch configmap feature-flags -n production \
  --type=json \
  -p='[{"op": "remove", "path": "/data/catalog_read"},
       {"op": "remove", "path": "/data/customer_read"},
       {"op": "remove", "path": "/data/order_read"}]'

echo "✅ Magento decommissioned. Platform running 100% on microservices."
echo "💰 License savings: starting from next renewal cycle"
```

## Phase 3 Completion Checklist

**Week 5 (Order Service cutover complete):**
- [ ] 10 consecutive days at 100% without auto-rollback
- [ ] Payment reconciliation: zero discrepancy between microservice and Magento ledgers
- [ ] DLQ message count: 0 throughout Week 5

**Week 7 (Pre-decommission):**
- [ ] Archive service running for 30 days without error
- [ ] Final load test: 10× production load, p99 < 200ms, error rate < 0.1%
- [ ] All domain teams sign off on migration completion

**Day 30 (Decommission):**
- [ ] Final Magento DB backup stored in long-term storage
- [ ] Magento infrastructure shutdown
- [ ] Feature flag Gateway config simplified
- [ ] Platform license renewal notification cancelled

## What You've Built

After Phase 3, the platform is:
- **21 Go microservices** on Kubernetes, deployed via ArgoCD GitOps
- **Zero PHP** in the critical request path
- **Zero Magento license cost** starting next renewal
- **Independent scaling**: Order Service scales independently during flash sales
- **< 200ms p99** response time on all critical endpoints
- **30-day rollback capability** → proven that rollback was never needed

[Part 9](/series/composable-commerce-migration/part-9-outbox-saga/) dives into the event reliability mechanism that made this migration possible without data loss: the Transactional Outbox + Saga pattern that guarantees every order event is delivered exactly once, and every failed transaction has a compensating action.

---

*If you're exploring similar distributed systems patterns, the [Shopee Architecture Series](/series/shopee-architecture/) documents how a regional super-app handles 10M+ concurrent users with a comparable microservices decomposition — useful reference for sizing and SLO decisions.*

## FAQ


{{< faq q="Why use ArgoCD GitOps instead of deploying directly with kubectl or Helm?" >}}
Direct kubectl applies are manual, error-prone, and leave no audit trail. Helm works for templating but doesn't enforce the target state continuously. ArgoCD enforces **desired state = actual state** at every reconciliation cycle (default: 3 minutes). If a pod crashes and restarts with a different image tag (e.g., from a hotfix applied manually), ArgoCD detects the drift and restores the committed state. During a high-stakes cutover, this continuous enforcement is the difference between a reproducible rollback and a "it was working but now it's different" incident.
{{< /faq >}}

{{< faq q="What does \"zero-downtime cutover\" actually guarantee?" >}}
Zero-downtime means: **no HTTP 5xx errors during the traffic shift, no queued or dropped user requests, no maintenance page**. It does not mean "no latency increase" — the first requests after a traffic shift typically see 10–20% higher p99 latency as new pods warm up their connection pools. The warm-up period is why the platform pre-warms instances 5 minutes before each traffic increment. After the warm-up period (typically 2–5 minutes), latency returns to baseline.
{{< /faq >}}

{{< faq q="How long should Magento run as a hot standby after cutover?" >}}
A minimum of **30 days** in read-only archive mode. This covers: (1) billing cycles that reference Magento order IDs, (2) customer service escalations about historical orders, (3) the window to detect any edge-case data missing from the migration. After 30 days, shut down Magento's application tier but keep the database snapshot for an additional 90 days in cold storage before permanent deletion.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? â†’ [Book a 1:1 Architecture Consultation](/hire/)*
{{< /faq >}}
