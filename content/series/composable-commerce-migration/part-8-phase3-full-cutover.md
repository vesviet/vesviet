---
title: "Part 8: Phase 3 — Full Cutover and Zero-Downtime Migration"
date: 2026-05-28T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "Shift 25%→100% of order traffic to Go microservices, keep Magento on a 30-day hot standby for instant rollback, and automate deploys with ArgoCD GitOps."
categories: ["Series", "Software Engineering", "DevOps"]
tags: ["DevOps", "Microservices"]
series: ["composable-commerce-migration"]
weight: 9
slug: "part-8-phase3-full-cutover"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-8-phase3-full-cutover/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 8: Phase 3 — Full Cutover & Decommissioning the Monolith"
  relative: false
keywords: ["monolith decommissioning", "cutover runbook ecommerce", "zero downtime cutover", "magento sunset"]
---

[← Previous Chapter: Part 7: Phase 2 — Dual-Write Dapr PubSub](/series/composable-commerce-migration/part-7-phase2-dual-write/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 9: Transactional Outbox & Saga Pattern →](/series/composable-commerce-migration/part-9-outbox-saga/)

---

> **Answer-first:** Phase 3 completes the migration: 100% of checkout and order traffic is routed to the Go microservices, Magento is kept on a 30-day hot standby for instant rollback, and deployments are fully automated through ArgoCD GitOps.

---

Phase 3 is the finale: 100% of traffic moves over to the microservice system, Magento formally steps back into the role of a passive archive, and the entire platform runs on the Go microservices through a GitOps workflow. There will be no trace of PHP left in any critical request path. And it also puts an end to the days of paying Magento license renewal fees.

**Answer-first:** A GitOps-driven cutover with ArgoCD and Kustomize is the 2026 best practice for guaranteeing zero downtime. Steering well clear of the "Big Bang migration" trap, Customer Service and Catalog Service are cut over to 100% first. Order Service alone is ramped up gradually (graduated ramp) 25%→50%→75%→100% over 10 days, with strict guardrail checks at every step. Magento is kept on hot standby for 30 days, synced one-way by the `archive-service`. All deployment and configuration operations live in a Git repository (single source of truth); ArgoCD (combined with Sync Waves and Hooks) automatically enforces the desired state onto the cluster, entirely preventing configuration drift.

## 1. The 6-Week Cutover Calendar

```
Week 1–2: Customer Service → 100% pushed into microservices
Week 3–4: Catalog Service → 100% pushed into microservices
Week 5–6: Order Service → Gradually ramped 25% → 50% → 75% → 100%
Week 7+:  Magento moves to hot standby (event bus off, archive-service runs hourly)
Week 11:  Magento formally decommissioned (Day 30 of the hot standby period)
```

By Week 5, Customer and Catalog have been fully migrated and have had 3+ weeks of real production mileage. The Debezium sync pipeline has been switched off entirely for these two domains (the microservices are now the single source of truth, no longer the follower). Only Order Service still has to move carefully step by step (graduated ramp), because orders are financial transactions involving real money — miss by an inch and you are off by a mile.

## 2. Customer + Catalog: Immediate 100% Cutover

```bash
#!/bin/bash
# week-1-customer-cutover.sh

echo "Week 1: Full cutover for Customer Service"

# Turn off the reverse-sync flag of the dual-write mechanism
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_magento_sync": "false"}}'

# Route 100% of customer traffic into the microservices
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_write": "true", "customer_read": "true", "customer_cutover": "true"}}'

# Start the archive service for customer (one-way sync to Magento every hour for 30 days)
curl -X POST "http://archive-service:8080/api/v1/start-archive" \
  -d '{"domain": "customer", "interval_seconds": 3600}'

# Monitor closely for 7 days
./scripts/monitor-cutover.sh --service=customer --duration=604800
echo "Customer Service cutover complete. Entering 7 days of monitoring."
```

The archive service (the newcomer in Phase 3) is responsible for hauling data from the microservices → writing into Magento on an hourly schedule. This is a **one-way, read-only sync** — Magento has been stripped of any write-back authority. It acts as a warm backup and satisfies audit/regulatory requirements that mandate keeping data on the legacy system for a fixed period.

## 3. Order Service: Graduated Traffic Ramp

Order Service gets special treatment because orders touch real money directly. The `order_cutover` feature flag takes an extra `percentage` parameter to control what fraction of new orders gets thrown over to the microservice:

```go
// gateway-service/internal/router/order_router.go

func routeOrderRequest(c *gin.Context, clients *ServiceClients, flags *FlagStore) {
    flag := flags.Get("order_cutover")

    if !flag.Enabled || flag.Percentage == 0 {
        // Phase 2 mode: all orders go to Order Service and sync back to Magento
        handleOrderViaMicroservice(c, clients.Order, true /* syncToMagento */)
        return
    }

    // Graduated ramp: hash the customer ID to decide which way to route
    // (the same buyer must always land in the same system for the whole cutover window)
    customerID := c.GetHeader("X-Customer-ID")
    hash := fnv.New32a()
    hash.Write([]byte(customerID))
    bucket := hash.Sum32() % 100

    if bucket < uint32(flag.Percentage) {
        // This customer's orders go to the microservice (NO sync back to Magento anymore)
        handleOrderViaMicroservice(c, clients.Order, false /* cutover: no sync */)
    } else {
        // Still route to Magento for this customer
        proxyToMagento(c)
    }
}
```

Hashing the customer ID (instead of random sampling) guarantees that one person's orders are never split across two systems — every order originating from `customer_id=X` always lands in exactly one system for the entire ramp period.

**Order Service ramp schedule (Week 5–6):**

| Day | Cutover % | Action required at each step |
|---|---|---|
| Day 1 (Monday) | 25% | Flip the flag, watch closely for 3 days |
| Day 4 (Thursday) | 50% | Validate data consistency, check DLQ=0, raise the number |
| Day 7 (Sunday) | 75% | Validate, run payment reconciliation |
| Day 10 (Wednesday) | 100% | Final cutover, shut down the Magento routing path entirely |

At each step, the following conditions must be satisfied before moving to the next tier:
1. DLQ message count = 0 (no failed events)
2. Write latency p99 < 200ms (this is the Phase 3 SLA, stricter than the 500ms level from Phase 2)
3. Payment reconciliation: total revenue in the microservice database must match Magento down to the last cent
4. Zero customer complaints related to order creation

## 4. Archive Service

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
- Runs on an hourly schedule
- Reads data from the microservices' PostgreSQL (the source of authority)
- Writes data into Magento's MySQL (for archival purposes only, Magento's own write ability has been revoked)
- Compresses the data (JSON → gzip) for long-term storage
- Automatically stops after 30 days (Day 30 = Magento is formally decommissioned)

## 5. ArgoCD GitOps: The Post-Migration Deployment Model

Once Magento is a thing of the past, all subsequent deployments follow the ArgoCD GitOps model. The full lifecycle of a code change:

```
1. Developer: git push code to a feature branch
2. GitLab CI:
    a. Run unit tests + integration tests
    b. Build the Docker image → push to the registry
    c. Open an MR (Merge Request) → team reviews the code
3. MR is merged into main:
    a. CI runs the full test suite one more time
    b. Build the final image: order-service:v1.2.3
    c. Update the GitOps repo:
       git commit -m "Update order-service to v1.2.3"
       # File changed: gitops/apps/order-service/overlays/production/kustomization.yaml
       # From: newTag: v1.2.2
       # To:   newTag: v1.2.3
4. ArgoCD detects the change in the GitOps repo:
    a. Run Kustomize build: merge base + production overlay
    b. Run kubectl apply against the production cluster
    c. Rolling update: update one pod, verify health, then update the next
5. ArgoCD auto-rolls-back if something goes wrong (unhealthy):
    git revert HEAD  # Undo the image tag update commit in the GitOps repo
    ArgoCD sees the revert → automatically restores the previous deployment
```

No more SSH-ing and clacking away on production servers. No more hand-run `kubectl apply`. The phrase "but it works on my machine" has been permanently banished from deploys. **Every change on production is traceable back to an exact Git commit.**

## 6. Kustomize: The Base + Overlays Picture

Every service has its own overlay files per environment:

```
gitops/apps/order-service/
├── base/
│   ├── deployment.yaml          ← Shared pieces: service definition, ports, health probes
│   ├── service.yaml
│   ├── configmap.yaml           ← Non-sensitive configuration
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml  ← Just 1 replica, tiny resource footprint
    └── production/
        ├── kustomization.yaml
        └── patch-replicas.yaml  ← 3 replicas, full production-grade resources
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
    newTag: v1.2.3                 ← CI updates this automatically on every new release
```

```yaml
# gitops/apps/order-service/base/deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: order-service
        image: order-service           # The tag is handled by the overlay above
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

## 7. Sync Waves: Starting Up in Order

ArgoCD Sync Waves guarantees that infrastructure components boot up first, and only then do the services come online:

```yaml
# gitops/apps/order-service/base/deployment.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"   # Wave 2: services start after wave 1 finishes
---
# gitops/infrastructure/databases/postgresql.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # Wave 0: databases wake up first
---
# gitops/infrastructure/dapr-components.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"   # Wave 1: Dapr must be alive before the services
```

Sync wave order: `Databases (0) → Dapr components (1) → Services (2) → Gateway (3)`

## 8. Performance Acceptance: The 10× Load Test

The Phase 3 acceptance criterion: *"Handle 10× current production load."* This K6 load test script is unleashed during off-peak hours before anyone declares Phase 3 done:

```javascript
// tests/load/phase3-validation.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    stages: [
        { duration: '5m', target: 100 },   // Ramp up
        { duration: '10m', target: 1000 }, // Slam with 10× normal load
        { duration: '5m', target: 0 },     // Ramp down
    ],
    thresholds: {
        'http_req_duration': ['p99<200'],  // SLA requires p99 < 200ms
        'http_req_failed': ['rate<0.001'], // Error rate must be < 0.1%
    },
};

export default function() {
    // Load-test order creation (the most dangerous, most fragile endpoint)
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

After 30 days of running hot standby without ever needing to pull the rollback lever:

```bash
#!/bin/bash
# day-30-decommission.sh

echo "Day 30: Decommissioning the Magento hot standby"

# Step 1: Stop the archive service
kubectl delete deployment archive-service -n production

# Step 2: Shut down the Debezium connectors (if any are still limping along for some domain)
kubectl delete deployment sync-service -n migration

# Step 3: Export Magento's final database backup
mysqldump --all-databases > /backup/magento-final-$(date +%Y%m%d).sql.gz

# Step 4: Shut down the Magento application servers for good
kubectl delete namespace magento

# Step 5: Strip the leftover Magento feature flags out of the Gateway
kubectl patch configmap feature-flags -n production \
  --type=json \
  -p='[{"op": "remove", "path": "/data/catalog_read"},
       {"op": "remove", "path": "/data/customer_read"},
       {"op": "remove", "path": "/data/order_read"}]'

echo "✅ Magento decommissioned successfully. The platform is now running 100% on microservices."
echo "💰 License savings: will start kicking in from the next renewal cycle"
```

## Phase 3 Completion Checklist

**Week 5 (end of the Order Service cutover):**
- [ ] 10 consecutive days running smoothly at 100% with zero auto-rollbacks
- [ ] Payment reconciliation: the microservice ledger and Magento figures match 100%, not a single cent off
- [ ] DLQ message count: = 0 for the entirety of Week 5

**Week 7 (approaching decommission):**
- [ ] Archive service ran the full 30 days without throwing a single error
- [ ] Final load test: 10× production load, p99 < 200ms, error rate < 0.1%
- [ ] All domain teams have signed off that the migration is complete

**Day 30 (Decommission):**
- [ ] Final Magento DB backup wrapped up and tucked into long-term storage
- [ ] All Magento infrastructure powered down
- [ ] Feature flag configuration cleaned up on the Gateway
- [ ] Phone call placed to cancel the legacy platform's license renewal

## What You Have Built

After Phase 3, your system looks like this:
- **21 Go microservices** thriving on Kubernetes, deployed via ArgoCD GitOps
- **Zero PHP** in critical request paths
- **Zero Magento license fees** from the next renewal cycle onward
- **Independent scaling**: Order Service can scale up on its own whenever flash sales hit
- **< 200ms p99** latency for all the most critical endpoints
- **A 30-day rollback window ready and waiting** → but more importantly: we proved we never needed to use it

[Part 9](/series/composable-commerce-migration/part-9-outbox-saga/) digs deep into the event reliability mechanism — the secret weapon that let this migration succeed without dropping a single crumb of data: Transactional Outbox + the Saga pattern, which provide the golden guarantee that every order event is delivered exactly once, and every failed transaction gets a matching compensating action.

---

*If you are interested in exploring similar distributed systems design patterns, check out the [Shopee Architecture Series](/series/shopee-architecture/) — it documents how a regional super-app handles 10M+ concurrent users with a microservices decomposition that shares many traits with this one — a highly valuable reference for sizing decisions and SLO targets.*

## FAQ

### Why use ArgoCD GitOps instead of plain kubectl or Helm for speed?

Running bare `kubectl apply` by hand is a risky game that badly violates the separation of concerns in 2026 security standards. Helm is great for templating, but it does not automatically enforce a target state. ArgoCD, by contrast, works like a diligent police officer, constantly maintaining the rule **desired state = actual state** on every reconciliation cycle (usually every 3 minutes). Notably, in the 2026 Cloud Native landscape, ArgoCD combined with Sealed Secrets / External Secrets Operator handles secret injection securely. If someone hand-patches an unexpected image tag onto a pod (a manual hotfix), ArgoCD smells the drift and self-heals by restoring the declared state. This enforcement is the thin line between a controlled, reproducible rollback and a full-blown cutover disaster.

### What does a "zero-downtime cutover" actually guarantee?

Zero-downtime means: **absolutely no HTTP 5xx errors during the traffic shift, absolutely no user requests queued or dropped, and absolutely no maintenance page on display**. But remember, it does NOT mean "no latency increase" — requests fired right after the traffic shift typically see about 10–20% higher p99 latency while the new pods clatter through warming up their connection pools. That awkward warm-up period is exactly why the platform pre-warms 5 minutes ahead of every traffic increase. Once you push through those first few warm-up minutes (usually 2–5 minutes), latency immediately drops back to its ideal baseline.

### How long should Magento be kept as a hot standby after the cutover?

The safe minimum is **30 days** in read-only archive mode. This window exists to cover three things: (1) billing cycles frequently still reference old Magento order IDs, (2) customer service teams love to dig up ancient orders and raise disputes, (3) it is the golden window to catch any edge-case data missing that slipped through the migration. Past the 30-day gate, confidently shut down Magento's application tier — but do not be tempted to delete everything; keep the database snapshot in cold storage for another 90 days before permanent deletion.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. See the full table of contents to get the complete architectural context.*

*Need help assessing the risks of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 7: Phase 2 — Dual-Write Dapr PubSub](/series/composable-commerce-migration/part-7-phase2-dual-write/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 9: Transactional Outbox & Saga Pattern →](/series/composable-commerce-migration/part-9-outbox-saga/)
