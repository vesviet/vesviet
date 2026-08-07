---
title: "Strangler Fig Read-Only Migration with Debezium CDC"
description: "Phase 1 migration guide for decoupling Magento reads using API Gateway routing, Debezium CDC event streams, and Dapr pub/sub event pipelines."
date: "2026-05-13T10:00:00+07:00"
lastmod: "2026-07-03T15:41:55+07:00"
draft: false
weight: 3
slug: "part-6-phase1-strangler-fig"
ShowToc: true
TocOpen: true
categories: ["Software Engineering", "Backend", "Migration"]
tags: ["Strangler Fig", "CDC", "Debezium", "Dapr", "Feature Flags", "Magento Migration", "Zero Downtime"]
series: ["composable-commerce-migration"]
series_order: 6
ShowPostNavLinks: false
author: "Lê Tuấn Anh"
cover:
  image: "/images/posts/ecommerce-composable-cover.jpg"
  alt: "Composable Commerce Migration series: Magento 2 to microservices Golang step-by-step"
  relative: false
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-6-phase1-strangler-fig/"
---


> **Prerequisite:** Familiarity with the concepts introduced in [Part 5 — Eav Schema Migration](/series/composable-commerce-migration/part-5-eav-schema-migration/). Review it first if the terminology in this part is unfamiliar.

Phase 1 is the safest phase of the migration — by design. No write operation touches the new microservices. Magento remains the source of truth for all data modifications. The only thing Phase 1 does is prove that your microservices can serve *reads* faster and more reliably than Magento.

**Answer-first:** Phase 1 deploys read-only Go microservices alongside legacy Magento. API Gateway feature flags route read requests to Go with automatic fallback to Magento on failure. Embedded Debezium streams MySQL binary log updates to Redis Streams with sub-2-second sync latency. Adopting this pattern guarantees sub-50ms P99 latency bounds, zero-allocation memory optimization, and fault-tolerant event-driven state synchronization across production systems.

> **Phase 1 Playbook:** Featured in the **[Composable Migration Architecture Guide](/series/magento-migration-vietnam/ecommerce-architecture-composable-migration/)**. Read the main post for full system context.

## 1. Phase 1 Architecture

Phase 1 architecture deploys read-only Go microservices behind an API Gateway, keeping Magento as the write master while decoupling reads.

The architectural topology below demonstrates how incoming client HTTP traffic is intercepted by the API Gateway layer, dynamically routing read-only requests to high-performance Go microservices while strictly keeping legacy Magento as the authoritative write master.

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

The core constraint during Phase 1 is absolute write isolation: **no write path reaches the microservices**. The API Gateway forces all POST, PUT, and DELETE mutations to legacy Magento regardless of flag states.

In modern 2026 cloud-native architecture, this gateway layer is powered by either Envoy Proxy or YARP (Yet Another Reverse Proxy):
- **Envoy Proxy**: Standard for Kubernetes ingress and sidecar meshes. Envoy uses dynamic xDS APIs (Route Discovery Service - RDS, Cluster Discovery Service - CDS) to update routing rules in memory without process restarts or dropping active TCP connections.
- **YARP Reverse Proxy**: Ideal for .NET / C# enterprise ecosystems or Windows/Linux hybrid stacks, delivering high-throughput HTTP route matching, destination health probing, and custom middleware request transformation.
- **Zero-Downtime Decoupling**: Persistent connection keep-alives, HTTP/2 multiplexing, and graceful connection draining (`drain_time_ms: 15000`) prevent HTTP 502 Bad Gateway errors when shifting traffic dynamically between Magento and Go services.

## 2. Why Not Just Use `updated_at` Polling?

Polling `updated_at` fields misses hard deletes and causes severe database CPU spikes, whereas Debezium CDC streams binary log events in real time.

The conventional approach for database synchronization relies on timestamp queries. The following SQL snippet illustrates the typical `updated_at` polling query pattern that fails under high-throughput production workloads:

```sql
-- ❌ Polling: misses DELETEs, vulnerable to timestamp skew
SELECT entity_id FROM catalog_product_entity
WHERE updated_at > :last_check_time
ORDER BY updated_at ASC
LIMIT 1000;
```

This polling pattern fails fundamentally in enterprise e-commerce environments for four critical technical reasons:
1. **DELETE operations are invisible**: When a merchant deletes a product or order line, the physical row is deleted. There is no updated timestamp row left behind to signal the change to downstream services.
2. **Transaction rollbacks & uncommitted reads**: If a long-running transaction updates `updated_at` to `10:00:01` but commits at `10:00:05`, a polling query running at `10:00:03` will skip that record permanently.
3. **Clock skew & timestamp collisions**: NTP drift between application hosts and database servers causes windowing gaps, while sub-second batch writes share identical timestamps.
4. **Database contention & index fragmentation**: Repeatedly executing windowed range queries over indexed timestamp columns causes lock escalation, buffer pool eviction, and severe MySQL CPU saturation during peak traffic.

By contrast, Debezium CDC attaches directly to MySQL's binary logging engine. As documented in the architecture specification:

> *"Why Debezium instead of `updated_at` polling? Polling on `updated_at` misses DELETE operations entirely and is vulnerable to clock skew and timestamp collisions. Debezium reads MySQL binary logs with GTID auto-positioning, capturing every row-level change reliably with exact before/after state and sub-2-second sync latency."*

## 3. Debezium CDC Setup

Debezium CDC monitors Magento MySQL binlogs, streaming insert, update, and delete events into Kafka/Dapr without touching application code.

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

The CDC-to-Dapr pipeline converts raw MySQL row mutations into structured CloudEvents, updating Go microservice read replicas instantaneously.

Rather than deploying complex, multi-node Kafka Connect clusters common in legacy tutorials, modern 2026 architectures adopt lightweight streaming streams using Debezium embedded engine or Debezium Server streaming directly into high-throughput brokers such as Redpanda (C++ Kafka API replacement) or NATS JetStream. 

The data pipeline architecture below illustrates the stream transformation sequence from raw MySQL binary log events down to microservice read store ingestion:

```
Magento MySQL binlog
    ↓ Debezium embedded engine (no Kafka Connect cluster)
Sync Consumer Service (Go)
    ↓ Integer → UUID translation via magento_id_map
    ↓ EAV flattening (varchar + int + decimal → single product record)
Dapr PubSub Publisher
    ↓ Redis Streams / NATS JetStream (sub-5ms event propagation)
Microservice Read Replicas
```

Standardized CloudEvent envelopes wrap each domain mutation, specifying event versioning (`v1.0.0`), event source (`magento.cdc.catalog`), and schema payload structure.

Migration event topics (verified in `sync-service-implementation.md`):

| Topic | Published By | Consumed By |
|---|---|---|
| `migration.customer.changed` | Sync Service | Customer Service |
| `migration.product.changed` | Sync Service | Catalog Service |
| `migration.order.changed` | Sync Service | Order Service |
| `migration.stock.changed` | Sync Service | Warehouse Service |
| `migration.dlq` | Dapr (auto) | Ops team via DLQ handler |

The Go implementation of the sync consumer handles integer-to-UUID translation, pivots fragmented Magento EAV tables (`catalog_product_entity_varchar`, `int`, `decimal`) into unified JSON models, and dispatches events to Dapr:

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

API Gateway feature flags dynamically route catalog read requests between legacy Magento and Go microservices, enabling instant traffic shifting and immediate rollback capability during migration testing.

The Gateway layer utilizes path-based and header-based canary evaluation. In 2026 architectures, routing controls leverage Envoy dynamic Route Discovery Service (RDS) or YARP HTTP matching rules, allowing header-based canary inspection (`X-Canary-User: true`) and weighted cluster shifts (e.g. 95% traffic to Magento monolith, 5% to Go catalog microservice).

The Go HTTP middleware below inspects active feature flags and target service health before routing incoming requests:

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

Feature flag definitions are encapsulated inside a Kubernetes ConfigMap, enabling zero-downtime, sub-30-second hot-reloads across API Gateway pod replicas without requiring binary re-deployments:

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

Enabling a flag for a domain takes effect dynamically within seconds across all gateway instances. If anomalies occur during testing, flipping `catalog_read` back to `"false"` instantly restores 100% traffic flow to Magento monolith without dropping connected user sessions.

To prevent cascading failures and guarantee high availability, the API Gateway incorporates circuit breaker patterns and automated outlier detection. In 2026 Envoy deployments, passive health checking ejection combined with active gRPC/HTTP health checking automatically ejects failing microservice instances from upstream clusters.

The Go health monitoring component below tracks consecutive upstream failure counters and automatically trips feature flags back to Magento fallback routing when error rates exceed threshold limits:

```go
// gateway-service/internal/middleware/health_monitor.go

type DomainHealth struct {
    failures atomic.Uint64
}

type HealthMonitor struct {
    mu        sync.RWMutex
    domains   map[string]*DomainHealth
    flagStore FlagStore
}

func NewHealthMonitor(flagStore FlagStore) *HealthMonitor {
    return &HealthMonitor{
        domains:   make(map[string]*DomainHealth),
        flagStore: flagStore,
    }
}

func (m *HealthMonitor) RecordFailure(domain string) {
    m.mu.Lock()
    dh, exists := m.domains[domain]
    if !exists {
        dh = &DomainHealth{}
        m.domains[domain] = dh
    }
    m.mu.Unlock()

    newCount := dh.failures.Add(1)
    if newCount >= 3 {
        // 3 consecutive failures → auto-disable feature flag
        m.flagStore.Disable(domain + "_read")
        log.Warnf("Auto-disabled %s_read after %d consecutive failures", domain, newCount)
        alert.Send(fmt.Sprintf("⚠️ %s_read auto-disabled — check service health", domain))
    }
}

func (m *HealthMonitor) RecordSuccess(domain string) {
    m.mu.RLock()
    dh, exists := m.domains[domain]
    m.mu.RUnlock()
    if exists {
        dh.failures.Store(0)
    }
}
```

When a circuit breaker trips, requests are transparently rerouted to legacy Magento. Re-enabling the feature flag requires explicit operator intervention after checking service logs and telemetry dashboard metrics, preventing service flapping.

## 7. Phase 1 Success Criteria

Phase 1 success criteria require offloading 80% of catalog read traffic to Go microservices while maintaining zero write inconsistencies.

Before declaring Phase 1 complete and transitioning to Phase 2 dual-write synchronization, the deployment must meet strict operational SLAs tracked via Prometheus metrics and automated validation tools:

| Metric | Target | How to Measure |
|---|---|---|
| Data sync latency | < 2 seconds | `check-data-consistency.sh catalog 100` |
| Fallback time | < 5 seconds | Disable service pod, measure time to Magento fallback |
| Read operation success rate | > 99.9% | Prometheus `http_request_duration_seconds` |
| Zero write errors | 0 | All POSTs returning 2xx from Magento |
| 7-day monitoring period | Zero auto-disables | Review flag history in ConfigMap events |

Automated data consistency validation runs continuously via Kubernetes CronJob. The shell script below performs randomized sample verification comparing primary key records between legacy MySQL and microservice PostgreSQL:

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

The Phase 1 deployment checklist verifies Debezium connector stability, Dapr PubSub topics, API Gateway feature flags, and health probes.

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

Phase 2 advances from read-only migration to event-driven dual-write sync for order processing and customer state mutations.

Phase 1 is running. Reads are served by microservices. Magento still owns all writes. In [Part 7: Phase 2 — Dual-Write](/series/composable-commerce-migration/part-7-phase2-dual-write/), we enable write operations on microservices — starting with Customer Service (lowest risk) and ending with Order Service (highest risk). The challenge: both Magento and microservices can now mutate the same data concurrently. We'll cover the conflict resolution strategy that handles it without data loss.

## FAQ

Strangler Fig read-only migration reduces legacy monolith load immediately without risking checkout or payment write integrity.

{{< faq q="What is the difference between Debezium and Kafka Connect?" >}}
Debezium is a **CDC connector library** — it reads database change logs (MySQL binlog, PostgreSQL WAL, etc.) and produces change events. Kafka Connect is a **framework for running connectors**, typically used to deploy Debezium at scale with full fault-tolerance, distributed workers, and REST management API. This platform runs Debezium in **embedded engine mode** — the connector runs inside the sync-consumer Go service process, eliminating the need to operate a Kafka Connect cluster. The trade-off: embedded mode has lower fault tolerance (single process), but is significantly simpler to operate for a team that doesn't already run Kafka infrastructure.
{{< /faq >}}

{{< faq q="How does the Strangler Fig pattern avoid downtime during migration?" >}}
The Strangler Fig works by routing traffic at the proxy/gateway layer — not by switching systems. During Phase 1, the same domain name responds to all traffic. The CDN or API Gateway inspects each request: if the feature flag is enabled and the target service is healthy, the request goes to microservices; otherwise it falls through to Magento. There is no DNS switch, no maintenance window, and no user-visible disruption. The migration happens behind the routing layer over weeks, not hours.
{{< /faq >}}

{{< faq q="How do you handle the initial Debezium snapshot without blocking production MySQL?" >}}
Debezium's `snapshot.mode: initial` reads all rows using a consistent snapshot — it uses MySQL's `REPEATABLE READ` isolation level, which means it doesn't lock the table. However, it does consume significant I/O bandwidth during the snapshot phase (reading millions of rows sequentially). Best practice: run the initial snapshot during off-peak hours, monitor MySQL I/O metrics, and configure Debezium's `max.batch.size` to throttle the read rate if needed.

{{< /faq >}}

🔗 **Next Step:** Continue to [Part 7 — Phase2 Dual Write](/series/composable-commerce-migration/part-7-phase2-dual-write/) for the following module in the series.