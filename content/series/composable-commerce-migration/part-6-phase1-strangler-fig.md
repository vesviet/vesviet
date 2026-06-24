---
title: "Part 6: Phase 1 — Strangler Fig: Read-Only Migration + CDC"
description: "Phase 1 of the 3-phase Magento migration: deploy read-only Go microservices behind the API Gateway, implement Debezium CDC for real-time sync from Magento MySQL (without Kafka), use feature flags for zero-risk traffic routing, and automatic fallback on failure."
date: 2026-05-13T10:00:00+07:00
lastmod: 2026-06-24T10:00:00+07:00
draft: false
weight: 7
slug: "part-6-phase1-strangler-fig"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Backend Architecture", "Migration"]
tags: ["Strangler Fig", "CDC", "Debezium", "Dapr", "Feature Flags", "Magento Migration", "Zero Downtime"]
series: ["Composable Commerce Migration"]
series_order: 6
author: "Lê Tuấn Anh"
---

Phase 1 is the safest phase of the migration — by design. No write operation touches the new microservices. Magento remains the source of truth for all data modifications. The only thing Phase 1 does is prove that your microservices can serve *reads* faster and more reliably than Magento.

**Answer-first:** Phase 1 deploys Go microservices in read-only mode, routes GET requests to them via the API Gateway's per-domain feature flags (with automatic fallback to Magento if the service is unhealthy), and uses Debezium — running in embedded engine mode without a standalone Kafka cluster — to stream Magento MySQL changes to the microservices via Dapr PubSub on Redis Streams. Writes continue to go to Magento. Data latency target: < 2 seconds.

## 1. Phase 1 Architecture

```
Client App (browser/mobile)
         │
         ▼
┌─────────────────────────────────────┐
│         API Gateway :8000            │
│                                      │
│  GET /products/* ──► feature_flag   │
│                    [catalog_read]?   │
│           ┌─────────────────────┐    │
│           │ Enabled + Healthy?  │    │
│           └─────────────────────┘    │
│               │           │          │
│               ▼           ▼          │
│      Catalog Service  Magento API   │
│          :8005        (fallback)    │
│                                      │
│  POST/PUT/DELETE /* ──► Magento API │  ← ALL writes go to Magento
└─────────────────────────────────────┘
         │                │
         ▼                ▼
  Microservices DB    Magento MySQL
  (read replica)     (source of truth)
         ▲
         │ Debezium CDC + Dapr PubSub
         │ (every row change in Magento → published to microservices)
         └──────────────────────────────
```

The key constraint: **no write path reaches the microservices in Phase 1**. The Gateway routes all POST/PUT/DELETE to Magento, regardless of feature flags.

## 2. Why Not Just Use `updated_at` Polling?

The first instinct for syncing Magento data is to poll `updated_at`:

```sql
-- ❌ Polling: misses DELETEs, vulnerable to timestamp skew
SELECT entity_id FROM catalog_product_entity
WHERE updated_at > :last_check_time
ORDER BY updated_at ASC
LIMIT 1000;
```

This fails in three ways:
1. **DELETEs are invisible**: A deleted product has no `updated_at` entry — it simply disappears from the table
2. **Clock skew**: If Magento MySQL is on a different server with a slightly different clock, records can fall in gaps between polling windows
3. **High database load**: Frequent full-table timestamp scans on a production e-commerce database causes contention

The solution from `sync-service-implementation.md`:

> *"Why Debezium instead of `updated_at` polling? Polling on `updated_at` misses DELETE operations entirely and is vulnerable to clock skew and timestamp collisions. Debezium reads MySQL binary logs, capturing every row-level change reliably with exact before/after state."*

## 3. Debezium CDC Setup

Debezium reads MySQL's binary log (binlog) — the same append-only log that MySQL replication uses. Every INSERT, UPDATE, and DELETE on any tracked table produces a change event.

### Step 1: Enable MySQL Binlog on Magento DB

Add to `/etc/mysql/conf.d/binlog.cnf` on the Magento MySQL server:

```ini
[mysqld]
log_bin           = mysql-bin
binlog_format     = ROW           # Must be ROW — captures exact before/after values
binlog_row_image  = FULL          # Capture complete row state, not just changed columns
expire_logs_days  = 7
server_id         = 1             # Must be unique across your MySQL replica set
```

Create the Debezium replication user:

```sql
-- Run on Magento MySQL
CREATE USER 'debezium'@'%' IDENTIFIED BY '${DEBEZIUM_PASSWORD}';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT
  ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;
```

Verify binlog is enabled:

```sql
SHOW VARIABLES LIKE 'log_bin';
-- Expected: log_bin = ON
SHOW VARIABLES LIKE 'binlog_format';
-- Expected: binlog_format = ROW
```

### Step 2: Debezium Connector Configuration

The platform runs Debezium in **embedded engine mode** — no standalone Kafka Connect cluster required. The connector runs as a sidecar to the sync consumer service:

```yaml
# configs/debezium-connector.json — loaded by the sync consumer at startup
{
  "connector.class": "io.debezium.connector.mysql.MySqlConnector",
  "database.hostname": "${MAGENTO_DB_HOST}",
  "database.port": "3306",
  "database.user": "debezium",
  "database.password": "${DEBEZIUM_PASSWORD}",
  "database.server.id": "184054",
  "database.server.name": "magento",
  "database.include.list": "${MAGENTO_DB_NAME}",

  "table.include.list": [
    "${MAGENTO_DB_NAME}.customer_entity",
    "${MAGENTO_DB_NAME}.customer_address_entity",
    "${MAGENTO_DB_NAME}.catalog_product_entity",
    "${MAGENTO_DB_NAME}.catalog_product_entity_varchar",
    "${MAGENTO_DB_NAME}.catalog_product_entity_decimal",
    "${MAGENTO_DB_NAME}.catalog_product_entity_int",
    "${MAGENTO_DB_NAME}.sales_order",
    "${MAGENTO_DB_NAME}.cataloginventory_stock_item"
  ],

  "snapshot.mode": "initial",           // Full snapshot on first run, then incremental
  "include.schema.changes": "false",

  // Offset storage: remembers binlog position for resume after restart
  "offset.storage": "org.apache.kafka.connect.storage.FileOffsetBackingStore",
  "offset.storage.file.filename": "/var/debezium/offsets/offsets.dat",
  "offset.flush.interval.ms": "1000"
}
```

**Critical note on `snapshot.mode: initial`**: On first startup, Debezium takes a full snapshot of all rows in the tracked tables before switching to binlog streaming. This initial snapshot can take 15–60 minutes for a Magento database with millions of products. Plan Phase 1 deployment accordingly.

## 4. The CDC → Dapr Pipeline

Instead of the Kafka-based pipeline common in industry tutorials, the platform uses:

```
Magento MySQL binlog
    ↓ Debezium embedded engine (no Kafka Connect cluster)
Sync Consumer Service (Go)
    ↓ Integer → UUID translation via magento_id_map
    ↓ EAV flattening (varchar + int + decimal → single product record)
Dapr PubSub Publisher
    ↓ Redis Streams (platform's existing event infrastructure)
Microservice Consumers
```

Migration event topics (verified in `sync-service-implementation.md`):

| Topic | Published By | Consumed By |
|---|---|---|
| `migration.customer.changed` | Sync Service | Customer Service |
| `migration.product.changed` | Sync Service | Catalog Service |
| `migration.order.changed` | Sync Service | Order Service |
| `migration.stock.changed` | Sync Service | Warehouse Service |
| `migration.dlq` | Dapr (auto) | Ops team via DLQ handler |

The sync consumer code for the product pipeline:

```go
// sync-service/internal/consumer/product_consumer.go

func (c *ProductConsumer) HandleChange(ctx context.Context, event debezium.ChangeEvent) error {
    if event.Table != "catalog_product_entity" {
        return nil
    }

    // Step 1: Translate Magento integer ID → UUID
    magentoID := event.After["entity_id"].(int64)
    uuid, err := c.idMapper.GetOrCreate(ctx, "product", magentoID)
    if err != nil {
        return fmt.Errorf("id mapping failed for product %d: %w", magentoID, err)
    }

    // Step 2: Fetch full product data (EAV pivot query)
    product, err := c.extractor.ExtractProduct(ctx, magentoID)
    if err != nil {
        return fmt.Errorf("EAV extraction failed for product %d: %w", magentoID, err)
    }
    product.ID = uuid

    // Step 3: Publish to Dapr PubSub
    payload, _ := json.Marshal(product)
    return c.daprClient.PublishEvent(ctx, "pubsub", "migration.product.changed", payload)
}
```

## 5. Feature Flag Routing

The Gateway Service routes traffic based on per-domain feature flags, evaluated on each request:

```go
// gateway-service/internal/middleware/feature_flag.go

func FeatureFlagMiddleware(flagStore FlagStore) gin.HandlerFunc {
    return func(c *gin.Context) {
        // Determine which domain this request belongs to
        domain := extractDomain(c.Request.URL.Path)

        flag, err := flagStore.Get(c, fmt.Sprintf("%s_read", domain))
        if err != nil || !flag.Enabled {
            // Flag not found or disabled → proxy to Magento
            proxyToMagento(c)
            return
        }

        // Check if the target microservice is healthy
        if !isHealthy(domain) {
            // Service unhealthy → automatic fallback
            proxyToMagento(c)
            return
        }

        c.Next() // Forward to microservice handler
    }
}
```

Feature flags are stored in a Kubernetes ConfigMap and hot-reloaded:

```yaml
# configmap/feature-flags.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: feature-flags
  namespace: production
data:
  catalog_read: "true"     # Route GET /products/* to Catalog Service
  customer_read: "false"   # Still routing to Magento (not ready yet)
  order_read: "false"      # Still routing to Magento
```

Enabling a flag for a domain takes effect within 30 seconds (ConfigMap refresh interval) — no deployment required.

## 6. Automatic Fallback: Self-Healing Gateway

The Gateway implements a 3-failure automatic fallback:

```go
// gateway-service/internal/health/monitor.go

type HealthMonitor struct {
    failureCounts sync.Map  // domain → consecutive failure count
    flagStore     FlagStore
}

func (m *HealthMonitor) RecordFailure(domain string) {
    count, _ := m.failureCounts.LoadOrStore(domain, int64(0))
    newCount := count.(int64) + 1
    m.failureCounts.Store(domain, newCount)

    if newCount >= 3 {
        // 3 consecutive failures → auto-disable feature flag
        m.flagStore.Disable(domain + "_read")
        log.Warnf("Auto-disabled %s_read after %d consecutive failures", domain, newCount)
        // Alert sent to #migration-issues Slack
        alert.Send(fmt.Sprintf("⚠️ %s_read auto-disabled — check service health", domain))
    }
}

func (m *HealthMonitor) RecordSuccess(domain string) {
    m.failureCounts.Store(domain, int64(0))
}
```

Re-enabling a flag after automatic disable requires manual intervention (review logs, verify service health, then edit the ConfigMap). This prevents a flapping service from automatically re-enabling itself.

## 7. Phase 1 Success Criteria

Before declaring Phase 1 complete and beginning Phase 2:

| Metric | Target | How to Measure |
|---|---|---|
| Data sync latency | < 2 seconds | `check-data-consistency.sh catalog 100` |
| Fallback time | < 5 seconds | Disable service pod, measure time to Magento fallback |
| Read operation success rate | > 99.9% | Prometheus `http_request_duration_seconds` |
| Zero write errors | 0 | All POSTs returning 2xx from Magento |
| 7-day monitoring period | Zero auto-disables | Review flag history in ConfigMap events |

Data consistency validation script (runs every 15 minutes via cronjob in Phase 1):

```bash
#!/bin/bash
# scripts/check-data-consistency.sh

SERVICE=$1       # e.g., "catalog"
SAMPLE_SIZE=$2   # e.g., 100

echo "Checking $SERVICE data consistency ($SAMPLE_SIZE samples)..."

# Get sample record IDs from Magento
MAGENTO_IDS=$(mysql -h $MAGENTO_DB -e "
    SELECT entity_id FROM catalog_product_entity
    ORDER BY RAND() LIMIT $SAMPLE_SIZE
" | tail -n +2)

MISMATCH_COUNT=0

while IFS= read -r magento_id; do
    # Get UUID from magento_id_map
    UUID=$(psql $PLATFORM_DB -t -c "
        SELECT platform_uuid FROM magento_id_map
        WHERE entity_type = '${SERVICE}' AND magento_id = $magento_id
    ")

    # Compare updated_at timestamps (must be within 2 seconds)
    MAGENTO_TS=$(mysql -h $MAGENTO_DB -e "
        SELECT UNIX_TIMESTAMP(updated_at) FROM catalog_product_entity
        WHERE entity_id = $magento_id
    " | tail -1)

    PLATFORM_TS=$(psql $PLATFORM_DB -t -c "
        SELECT EXTRACT(EPOCH FROM updated_at) FROM products WHERE id = '${UUID}'
    ")

    LAG=$(echo "$PLATFORM_TS - $MAGENTO_TS" | bc | tr -d '-')

    if (( $(echo "$LAG > 2" | bc -l) )); then
        echo "⚠️  Product $magento_id lag: ${LAG}s"
        ((MISMATCH_COUNT++))
    fi
done <<< "$MAGENTO_IDS"

echo "Validation complete. Mismatches: $MISMATCH_COUNT / $SAMPLE_SIZE"
[ $MISMATCH_COUNT -eq 0 ] && echo "✅ All samples within 2s SLA"
```

## 8. Deployment Checklist

**Pre-deployment (1–2 weeks before Phase 1 go-live):**
- [ ] Magento MySQL binlog enabled (`log_bin = ON`, `binlog_format = ROW`)
- [ ] Debezium replication user created with correct grants
- [ ] `magento_id_map` populated (count matches Magento entity count)
- [ ] Full EAV extraction completed and validated (count match)
- [ ] Sync Consumer Service deployed, initial snapshot complete
- [ ] All migration Dapr topics confirmed receiving events
- [ ] Kubernetes PersistentVolumeClaim for Debezium offset file created

**Phase 1 go-live:**
- [ ] Feature flags: all set to `"false"` (Magento routing)
- [ ] Enable `catalog_read: "true"` for 10% of team to verify
- [ ] Monitor for 24 hours: no auto-disables, latency < 2s
- [ ] Enable for 100% traffic
- [ ] Set up monitoring dashboard for Phase 1 metrics

**Phase 1 complete (prerequisites for Phase 2):**
- [ ] All enabled domains: 7 consecutive days without auto-disable
- [ ] Data consistency validation: 0 mismatches on 1000-sample check
- [ ] Performance: p99 latency < 200ms for all read endpoints

## What's Next

Phase 1 is running. Reads are served by microservices. Magento still owns all writes. In [Part 7: Phase 2 — Dual-Write](/series/composable-commerce-migration/part-7-phase2-dual-write/), we enable write operations on microservices — starting with Customer Service (lowest risk) and ending with Order Service (highest risk). The challenge: both Magento and microservices can now mutate the same data concurrently. We'll cover the conflict resolution strategy that handles it without data loss.

## FAQ

### What is the difference between Debezium and Kafka Connect?

Debezium is a **CDC connector library** — it reads database change logs (MySQL binlog, PostgreSQL WAL, etc.) and produces change events. Kafka Connect is a **framework for running connectors**, typically used to deploy Debezium at scale with full fault-tolerance, distributed workers, and REST management API. This platform runs Debezium in **embedded engine mode** — the connector runs inside the sync-consumer Go service process, eliminating the need to operate a Kafka Connect cluster. The trade-off: embedded mode has lower fault tolerance (single process), but is significantly simpler to operate for a team that doesn't already run Kafka infrastructure.

### How does the Strangler Fig pattern avoid downtime during migration?

The Strangler Fig works by routing traffic at the proxy/gateway layer — not by switching systems. During Phase 1, the same domain name responds to all traffic. The CDN or API Gateway inspects each request: if the feature flag is enabled and the target service is healthy, the request goes to microservices; otherwise it falls through to Magento. There is no DNS switch, no maintenance window, and no user-visible disruption. The migration happens behind the routing layer over weeks, not hours.

### How do you handle the initial Debezium snapshot without blocking production MySQL?

Debezium's `snapshot.mode: initial` reads all rows using a consistent snapshot — it uses MySQL's `REPEATABLE READ` isolation level, which means it doesn't lock the table. However, it does consume significant I/O bandwidth during the snapshot phase (reading millions of rows sequentially). Best practice: run the initial snapshot during off-peak hours, monitor MySQL I/O metrics, and configure Debezium's `max.batch.size` to throttle the read rate if needed.
