---
title: "Part 6: Phase 1 — Strangler Fig: Read-Only Migration"
date: 2026-05-12T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "Magento migration Phase 1 (Strangler Fig): Go microservices in read-only mode, Debezium CDC syncing MySQL without Kafka, feature flags and safe fallback."
categories: ["Series", "Software Engineering", "Architecture"]
tags: ["Strangler Fig", "Cloudflare", "Edge Computing", "Redis", "Golang", "Microservices"]
series: ["composable-commerce-migration"]
weight: 7
slug: "part-6-phase1-strangler-fig"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-6-phase1-strangler-fig/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 6: Phase 1 — Strangler Fig: Offloading the Product Catalog"
  relative: false
keywords: ["strangler fig pattern ecommerce", "cloudflare edge routing microservices", "catalog offloading magento", "zero downtime migration"]
mermaid: true
---

[← Previous Chapter: Part 5: Migrating the Magento EAV Schema](/series/composable-commerce-migration/part-5-eav-schema-migration/) | [Series Table of Contents](/series/composable-commerce-migration/) | [Next Chapter: Part 7: Phase 2 — Dual-Write with Dapr PubSub →](/series/composable-commerce-migration/part-7-phase2-dual-write/)

---

> **Answer-first:** Phase 1 of the Strangler Fig model migrates only the read/query path (Catalog, Search) to Go microservices, using Change Data Capture (Debezium CDC) to sync data from Magento's MySQL in near real time without disrupting the business write path.

---

Phase 1 is the safest stage of the entire migration — and that is by design. No write operation ever touches the new microservice system. Magento remains the single source of truth for every data modification. The only thing Phase 1 has to prove is that your pile of microservices can serve *read* operations faster and more reliably than Magento.

**Answer-first:** The Strangler Fig pattern remains the industry's gold standard for de-risking monolith migrations in 2026. In Phase 1, we deploy the Go microservices in read-only mode, routing GET requests to them through per-domain feature flags on the API Gateway (with an automatic fallback mechanism back to Magento). The heart of the data decomposition is Change Data Capture (CDC) via Debezium — running as an embedded engine to stream changes from Magento's MySQL to the microservices through Dapr PubSub (no heavyweight Kafka required). Every write operation continues to hit Magento directly, and all consumers are designed to be idempotent by requirement. Target data latency: < 2 seconds.

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
│           │ Flag on + Healthy?   │    │
│           └─────────────────────┘    │
│               │           │          │
│               ▼           ▼          │
│      Catalog Service  Magento API   │
│          :8005        (fallback)    │
│                                      │
│  POST/PUT/DELETE /* ──► Magento API │  ← ALL write requests go straight to Magento
└─────────────────────────────────────┘
         │                │
         ▼                ▼
  Microservices DB    Magento MySQL
  (read replica)     (source of truth)
         ▲
         │ Debezium CDC + Dapr PubSub
         │ (every changed row in Magento → published to the microservices)
         └──────────────────────────────
```

The key constraint: **absolutely no write path may reach the microservices in Phase 1**. The Gateway shovels every POST/PUT/DELETE back to Magento, regardless of whether the feature flag is on or off.

## 2. Why Not Just Poll the `updated_at` Column?

Everyone's first instinct when syncing Magento data is to write a polling loop over the `updated_at` column:

```sql
-- ❌ Polling: blind to DELETEs, breaks badly if server clocks drift
SELECT entity_id FROM catalog_product_entity
WHERE updated_at > :last_check_time
ORDER BY updated_at ASC
LIMIT 1000;
```

This approach collapses in three ways:
1. **DELETEs are invisible**: A deleted product leaves no trace in the `updated_at` column — it simply vanishes from the table.
2. **Clock skew**: If Magento's MySQL lives on a server whose clock drifts even slightly, rows can fall into the gap between two scans.
3. **High database load**: Continuously running timestamp-based full-table scans against a production e-commerce database causes contention.

Here is the rationale quoted from `sync-service-implementation.md`:

> *"Why choose Debezium over polling `updated_at`? Polling the `updated_at` column misses every DELETE outright and is extremely fragile against clock skew or duplicate timestamps. Debezium reads MySQL's binary logs directly, capturing every row-level change with precise before/after state."*

## 3. Setting Up Debezium CDC

Debezium reads MySQL's binary log (binlog) — the append-only log file that MySQL's own replication mechanism uses. Every INSERT, UPDATE, and DELETE hitting any watched table produces a change event.

### Step 1: Enable the MySQL Binlog on the Magento DB

Add this to `/etc/mysql/conf.d/binlog.cnf` on Magento's MySQL server:

```ini
[mysqld]
log_bin           = mysql-bin
binlog_format     = ROW           # Must be ROW — to capture exact before/after values
binlog_row_image  = FULL          # Capture the entire row, not just the changed columns
expire_logs_days  = 7
server_id         = 1             # Must be unique across your entire MySQL replica cluster
```

Create a dedicated user for Debezium replication:

```sql
-- Run this on Magento's MySQL
CREATE USER 'debezium'@'%' IDENTIFIED BY '${DEBEZIUM_PASSWORD}';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT
  ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;
```

Verify that the binlog is enabled:

```sql
SHOW VARIABLES LIKE 'log_bin';
-- Expected result: log_bin = ON
SHOW VARIABLES LIKE 'binlog_format';
-- Expected result: binlog_format = ROW
```

### Step 2: Configure the Debezium Connector

Our platform runs Debezium in **embedded engine mode** — no need to herd a separate Kafka Connect cluster. The connector runs as a sidecar attached to the sync consumer service:

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

  "snapshot.mode": "initial",           // Full snapshot on first run, then incremental streaming
  "include.schema.changes": "false",

  // Offset storage: remembers the binlog position so it can resume after a restart
  "offset.storage": "org.apache.kafka.connect.storage.FileOffsetBackingStore",
  "offset.storage.file.filename": "/var/debezium/offsets/offsets.dat",
  "offset.flush.interval.ms": "1000"
}
```

**A make-or-break note on `snapshot.mode: initial`**: On first startup, Debezium snapshots ALL rows in the watched tables before it switches to streaming the binlog. That initial snapshot can take 15–60 minutes on a Magento database with millions of products. Plan your Phase 1 deployment carefully around this number.

## 4. The CDC → Dapr Pipeline

Instead of the heavyweight Kafka-centric pipeline that pervades online tutorials, our platform uses:

```
Magento MySQL binlog
    ↓ Debezium embedded engine (no Kafka Connect cluster)
Sync Consumer Service (written in Go)
    ↓ Translate integer → UUID via the magento_id_map table
    ↓ Flatten EAV (merge varchar + int + decimal → a single product record)
Dapr PubSub Publisher
    ↓ Redis Streams (the platform's existing event infrastructure)
Microservice Consumers
```

The event topics serving the migration (validated in `sync-service-implementation.md`):

| Topic | Publisher | Consumer |
|---|---|---|
| `migration.customer.changed` | Sync Service | Customer Service |
| `migration.product.changed` | Sync Service | Catalog Service |
| `migration.order.changed` | Sync Service | Order Service |
| `migration.stock.changed` | Sync Service | Warehouse Service |
| `migration.dlq` | Dapr (automatic) | Ops team via the DLQ handler |

The sync consumer code carrying the product pipeline:

```go
// sync-service/internal/consumer/product_consumer.go

func (c *ProductConsumer) HandleChange(ctx context.Context, event debezium.ChangeEvent) error {
    if event.Table != "catalog_product_entity" {
        return nil
    }

    // Step 1: Translate the Magento integer ID → UUID
    magentoID := event.After["entity_id"].(int64)
    uuid, err := c.idMapper.GetOrCreate(ctx, "product", magentoID)
    if err != nil {
        return fmt.Errorf("id mapping failed for product %d: %w", magentoID, err)
    }

    // Step 2: Extract the full product data (run the EAV pivot query)
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

The Gateway Service performs traffic routing based on per-domain feature flags, evaluated on EVERY request:

```go
// gateway-service/internal/middleware/feature_flag.go

func FeatureFlagMiddleware(flagStore FlagStore) gin.HandlerFunc {
    return func(c *gin.Context) {
        // Determine the domain of this request
        domain := extractDomain(c.Request.URL.Path)

        flag, err := flagStore.Get(c, fmt.Sprintf("%s_read", domain))
        if err != nil || !flag.Enabled {
            // Flag missing or disabled → proxy straight to Magento
            proxyToMagento(c)
            return
        }

        // Check whether the target microservice is healthy
        if !isHealthy(domain) {
            // Service is down → automatic fallback
            proxyToMagento(c)
            return
        }

        c.Next() // Continue into the microservice handler
    }
}
```

Feature flags are stored in a Kubernetes ConfigMap and support hot-reload (updates without a restart):

```yaml
# configmap/feature-flags.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: feature-flags
  namespace: production
data:
  catalog_read: "true"     # Route GET /products/* to the Catalog Service
  customer_read: "false"   # Still routed to Magento (not ready yet)
  order_read: "false"      # Still routed to Magento
```

Flipping the flag for a domain takes effect within 30 seconds (the ConfigMap refresh interval) — no deployment required whatsoever.

## 6. Automatic Fallback: The Gateway's Self-Healing Behavior

The Gateway is wired with a counter that trips the fallback after 3 consecutive failures:

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
        // 3 consecutive failures → disable the feature flag automatically
        m.flagStore.Disable(domain + "_read")
        log.Warnf("Automatically disabled flag %s_read after %d consecutive failures", domain, newCount)
        // Fire an alert into the #migration-issues Slack channel
        alert.Send(fmt.Sprintf("⚠️ %s_read was disabled automatically — please check the service health", domain))
    }
}

func (m *HealthMonitor) RecordSuccess(domain string) {
    m.failureCounts.Store(domain, int64(0))
}
```

Once a flag has been disabled automatically, re-enabling it requires human intervention (read the logs, verify the service is healthy again, then manually edit the ConfigMap file). This mechanism prevents a flapping service from repeatedly re-enabling its flag and dragging requests down with it.

## 7. Phase 1 Acceptance Criteria

Before you can confidently declare Phase 1 complete and move on to Phase 2:

| Metric | Target | How to Measure |
|---|---|---|
| Data sync latency | < 2 seconds | `check-data-consistency.sh catalog 100` |
| Fallback time | < 5 seconds | Kill the service pod and measure how long it takes to route back to Magento |
| Read success rate | > 99.9% | Prometheus `http_request_duration_seconds` |
| Write errors | 0 | Ensure every POST routed to Magento returns 2xx |
| 7-day observation window | Zero automatic flag disabling | Review flag-change history in ConfigMap events |

The data consistency verification script (run as a cronjob every 15 minutes throughout Phase 1):

```bash
#!/bin/bash
# scripts/check-data-consistency.sh

SERVICE=$1       # e.g. "catalog"
SAMPLE_SIZE=$2   # e.g. 100

echo "Checking data consistency for $SERVICE ($SAMPLE_SIZE samples)..."

# Sample record IDs from Magento
MAGENTO_IDS=$(mysql -h $MAGENTO_DB -e "
    SELECT entity_id FROM catalog_product_entity
    ORDER BY RAND() LIMIT $SAMPLE_SIZE
" | tail -n +2)

MISMATCH_COUNT=0

while IFS= read -r magento_id; do
    # Resolve the UUID from magento_id_map
    UUID=$(psql $PLATFORM_DB -t -c "
        SELECT platform_uuid FROM magento_id_map
        WHERE entity_type = '${SERVICE}' AND magento_id = $magento_id
    ")

    # Compare the two updated_at timestamps (must differ by less than 2 seconds)
    MAGENTO_TS=$(mysql -h $MAGENTO_DB -e "
        SELECT UNIX_TIMESTAMP(updated_at) FROM catalog_product_entity
        WHERE entity_id = $magento_id
    " | tail -1)

    PLATFORM_TS=$(psql $PLATFORM_DB -t -c "
        SELECT EXTRACT(EPOCH FROM updated_at) FROM products WHERE id = '${UUID}'
    ")

    LAG=$(echo "$PLATFORM_TS - $MAGENTO_TS" | bc | tr -d '-')

    if (( $(echo "$LAG > 2" | bc -l) )); then
        echo "⚠️  Product $magento_id lagging: ${LAG}s"
        ((MISMATCH_COUNT++))
    fi
done <<< "$MAGENTO_IDS"

echo "Check complete. Failing samples: $MISMATCH_COUNT / $SAMPLE_SIZE"
[ $MISMATCH_COUNT -eq 0 ] && echo "✅ All samples meet the < 2s SLA"
```

## 8. Deployment Checklist

**Before deploying (1–2 weeks ahead of the Phase 1 go-live):**
- [ ] Enable the MySQL binlog for Magento (`log_bin = ON`, `binlog_format = ROW`)
- [ ] Create the Debezium replication user and grant sufficient privileges
- [ ] Populate `magento_id_map` (verify the row count matches Magento's entity count)
- [ ] Run the full EAV extraction and validate it (count match)
- [ ] Deploy the Sync Consumer Service and run the initial snapshot backfill
- [ ] Verify all Dapr migration topics are receiving events
- [ ] Create a Kubernetes PersistentVolumeClaim to hold the Debezium offset file

**Phase 1 go-live:**
- [ ] Feature flags: all default to `"false"` (everything flows through Magento)
- [ ] Enable `catalog_read: "true"` for 10% of the test team
- [ ] Monitor closely for 24h: no automatic flag disabling, latency < 2s
- [ ] Enable the flag for 100% of traffic
- [ ] Stand up the monitoring dashboard for Phase 1 metrics

**End of Phase 1 (criteria to advance to Phase 2):**
- [ ] All domains enabled: a clean 7-day run with no automatic flag disabling
- [ ] Data consistency verification: 1,000 random samples with 0 failures
- [ ] Performance: p99 latency < 200ms across all read endpoints

## Next Steps

Phase 1 is running at full speed. The microservices have taken over the read path. Magento still holds life-and-death control over the write path. In [Part 7: Phase 2 — Dual-Write](/series/composable-commerce-migration/part-7-phase2-dual-write/), we start enabling writes on the microservices — opening with the Customer Service (lowest risk) and closing with the Order Service (highest risk). The expensive challenge: both Magento and the microservices will now be modifying the same data concurrently. We will dissect the conflict resolution strategy needed to handle this mess without losing a single bit of data.

## FAQ

### How is Debezium different from Kafka Connect?

Debezium is a **CDC connector library** — it mines the database's change logs (MySQL binlog, PostgreSQL WAL, etc.) and produces change events using log-based CDC. Kafka Connect, on the other hand, is a **framework for running those connectors**, commonly used to deploy Debezium at scale with all the bells and whistles: automatic failure recovery, a distributed worker fleet, and a REST API.

*Operational perspective for 2026 (E-E-A-T context): CDC is now regarded as an enterprise infrastructure discipline, not merely a data-copy tool. Our platform runs Debezium in **embedded engine mode** — the connector lives inside the Go process of the sync-consumer, eliminating the need to operate a Kafka Connect cluster. The trade-off is lower fault tolerance (it is a single process), in exchange for dramatically simpler operations. Note that because CDC synchronization is at-least-once by nature, every consumer on the target microservices must be designed for idempotency, combined with reconciliation loops, to guarantee data is neither corrupted nor duplicated.*

### How does the Strangler Fig pattern avoid downtime during a migration?

Strangler Fig works by shifting traffic at the proxy/gateway layer — not by switching one system off and another on. Throughout Phase 1, the same domain continues to receive all traffic. The CDN or API Gateway inspects each request: if the feature flag is enabled and the target service is healthy, the request goes to the microservice; otherwise, it falls back to Magento. No DNS switch, no maintenance window, and not a single user-visible moment of interruption. The migration happens quietly behind the routing layer for weeks — not in a dramatic few-hour cutover.

### How do you run Debezium's initial snapshot without blocking the production MySQL?

Debezium's `snapshot.mode: initial` reads the entire dataset via a consistent snapshot — it uses MySQL's `REPEATABLE READ` isolation level, meaning it does **not** lock the tables. However, it does consume a great deal of I/O bandwidth during the snapshot (it has to chew through millions of rows sequentially). Best practice: run the initial snapshot during off-peak hours, watch MySQL I/O metrics closely, and tune Debezium's `max.batch.size` to throttle the read rate if needed.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. See the full table of contents for the complete architectural context.*

*Need help assessing the risk of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 5: Migrating the Magento EAV Schema](/series/composable-commerce-migration/part-5-eav-schema-migration/) | [Series Table of Contents](/series/composable-commerce-migration/) | [Next Chapter: Part 7: Phase 2 — Dual-Write with Dapr PubSub →](/series/composable-commerce-migration/part-7-phase2-dual-write/)
