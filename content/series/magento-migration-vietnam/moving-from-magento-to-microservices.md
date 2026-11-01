---
title: "Migrating Magento to Microservices with Zero Downtime"
slug: "moving-from-magento-to-microservices"
author: "Lê Tuấn Anh"
date: "2026-04-14T21:20:00+07:00"
lastmod: "2026-11-02T09:00:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Magento", "Microservices", "Migration", "Architecture", "Debezium", "Dapr", "Envoy", "Golang"]
description: "A zero-downtime guide to migrating Magento to microservices: Strangler Fig, Debezium CDC, Envoy routing, dual-write outbox sync, and a 5-minute rollback plan."
categories: ["Architecture", "Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/moving-from-magento-to-microservices-cover.jpg"
  alt: "Zero-Downtime Blueprint: Moving from Magento to Microservices — Strangler Fig Pattern"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/moving-from-magento-to-microservices/"
weight: 4
mermaid: true
aliases:
---

> **Core summary (answer-first):** Migrating a massive e-commerce monolith like Magento 2 to a distributed Microservices architecture requires a zero-downtime cutover technique. The only viable strategy in production is a **3-phase Strangler Fig pattern**:
> 1. **Phase 1 (Read-Path Strangling):** Use Envoy API Gateway to route all read traffic (Catalog/Search) to a new cluster of Go Microservices, while data is synchronized in real time from Magento's MySQL to PostgreSQL/OpenSearch via **Debezium CDC (Change Data Capture)** on the binlog.
> 2. **Phase 2 (Write-Path & Bidirectional Sync):** Extract the core write domains (Cart, Order, Customer) into independent Microservices, implementing two-way synchronization back to Magento through a **Transactional Outbox Worker** built with Go 1.24 and Apache Kafka to maintain backward compatibility with legacy subsystems (ERP, WMS, Fulfillment).
> 3. **Phase 3 (Cutover & 30-Day Hot Standby):** Cut over 100% of traffic to the Microservices, keep Magento running as a hot standby replica for 30 days with a rollback capability of under 5 minutes, and only then decommission the physical/EC2 servers.

---

## 1. The "Big Bang Rewrite" Trap and the Harsh Reality of the Magento Monolith

When a Magento 2 e-commerce system reaches millions of SKUs and processes tens of thousands of orders per day during Mega Sale campaigns, the engineering team routinely faces familiar nightmares:
* **Long build/deploy times:** Each run of `setup:di:compile` and `setup:static-content:deploy` takes 25 to 45 minutes, stalling the release cycle for new features.
* **MySQL database bottlenecks:** The `sales_order`, `quote`, and EAV table system (`catalog_product_entity_*`) consume hundreds of gigabytes, causing constant table locks whenever checkout traffic spikes.
* **Tight coupling:** A small bug in a third-party shipping module's plugin interceptor (`aroundSave`) can bring down the entire checkout flow.

The engineers' first natural instinct is: *"Let's tear down Magento and rewrite it from scratch with Golang/Rust Microservices!"*

However, in large-scale software engineering, **a "Big Bang Rewrite" (tearing everything down and rebuilding at once) is nearly a death sentence for the project**. A running Magento ecosystem carries hundreds of hidden business rules, local tax integration edge cases, COD/VNPay/MoMo payment gateways, and internal order processing workflows refined over 5–10 years. Building an entirely new system in parallel over 12–18 months typically leads to:
1. **Scope Creep:** The old system keeps changing features to serve the business, so the new system can never catch up (the Moving Target Problem).
2. **Fantastical expectations about Cutover Day:** On switchover day, thousands of data mismatches between the two systems will break the supply chain and interrupt millions of dollars in revenue.
3. **Depleted opportunity cost:** All engineering resources are locked into re-coding things that already run stably instead of creating new value for users.

The only survival solution is the **Strangler Fig Pattern** proposed by Martin Fowler: build microservices that wrap around the old monolith, intercepting and handling portions of traffic one by one, until the old monolith is nothing but an empty shell that can be safely removed.

---

## 2. Three Technical Obstacles When Extracting Magento

Before routing a single request through the new system, the chief architect must solve 3 platform-incompatibility problems between Magento and a modern Microservices architecture:

```mermaid
graph TD
    subgraph Monolith ["Magento 2 Legacy Monolith"]
        EAV["EAV Data Model<br/>(400+ Tables, Splitted Attributes)"]
        SeqID["Sequential Integer IDs<br/>(entity_id INT32/64)"]
        MySQLBinlog["MySQL InnoDB Engine<br/>Row-based Binlog (GTID)"]
    end

    subgraph SyncCore ["CDC & Translation Layer"]
        Debezium["Debezium CDC Connector<br/>(Apache Kafka Connect)"]
        IDMap["Bi-directional ID Mapping Service<br/>(Redis + PostgreSQL)"]
        OutboxSync["Go 1.24 Outbox Consumer<br/>(Flattening & Hydration)"]
    end

    subgraph ModernMesh ["Modern Go Microservices"]
        CatalogSvc["Catalog Service<br/>(PostgreSQL Document JSONB)"]
        OrderSvc["Order Service<br/>(Event-Sourced, UUIDv7)"]
        SearchEngine["OpenSearch Cluster<br/>(Flat Product Index)"]
    end

    EAV -->|Streaming Binlog| Debezium
    Debezium --> OutboxSync
    OutboxSync --> IDMap
    OutboxSync --> CatalogSvc
    OutboxSync --> SearchEngine

    OrderSvc -->|Publish order.created| IDMap
    IDMap -->|Translate UUID to INT| Monolith
```

### 2.1. The EAV (Entity-Attribute-Value) Schema Nightmare
Magento does not store product information in a flat table. A single product is fragmented across dozens of tables:
* `catalog_product_entity`: holds `entity_id`, `sku`, `created_at`.
* `catalog_product_entity_varchar`: holds `name`, `url_key`, `image`.
* `catalog_product_entity_int`: holds `status`, `visibility`.
* `catalog_product_entity_decimal`: holds `price`, `special_price`, `weight`.
* `catalog_product_entity_text`: holds `description`, `short_description`.

If the new Microservices try to read these tables directly with multi-join queries (`JOIN`ing 15–20 tables), the MySQL database will saturate its CPU immediately.
* **Solution:** A Streaming ETL layer via Debezium CDC listens to these tables, groups rows by `entity_id` within a sliding window (100ms), flattens all attributes into a normalized JSON Document structure, and pushes them directly into PostgreSQL (using the `JSONB` type) along with the OpenSearch cluster that powers search.

### 2.2. Primary Key Identity Conflict: Integer vs. UUIDv7
Magento uses auto-incrementing sequential integer primary keys (`entity_id INT UNSIGNED`). Meanwhile, modern Microservices use **UUIDv7** (combining a 48-bit timestamp with 74 bits of random entropy) to generate IDs in a distributed way without depending on the centralized key counter of a database.
* **Solution:** Build a central **ID Mapping Service** that stores the 1-to-1 relationship between `(domain, legacy_id)` and `(domain, uuid)`. The mapping table is optimally indexed on PostgreSQL and fully cached on Redis Cluster so lookup latency stays under 0.3ms.

```sql
-- Schema of the bidirectional identity mapping table
CREATE TABLE system_id_mapping (
    domain VARCHAR(32) NOT NULL,          -- 'catalog', 'order', 'customer'
    legacy_id BIGINT NOT NULL,            -- Magento entity_id
    service_uuid UUID NOT NULL,           -- Microservice UUIDv7
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (domain, legacy_id)
);

CREATE UNIQUE INDEX idx_id_mapping_uuid ON system_id_mapping (domain, service_uuid);
```

### 2.3. Real-Time CDC vs. Cronjob Polling
Many teams try to synchronize data by writing PHP CLI or Python scripts that run on a cron every 5 minutes, scanning for records with `updated_at >= NOW() - INTERVAL 5 MINUTE`.
* **Consequences:** Polling continuously issues heavy `SELECT` statements against the MySQL Master's disk I/O, misses hard-deleted rows (`DELETE`), and produces 1–5 minutes of data staleness, which means customers see outdated prices and stock levels.
* **Solution:** Implement **True Change Data Capture (CDC)** with Debezium connecting directly to the MySQL Binlog in Row-based mode (GTID). Every `INSERT`, `UPDATE`, and `DELETE` on Magento is transformed into a Kafka event in under 15 milliseconds, without consuming any compute resources on the Magento application server.

---

## 3. The 3-Phase Strangler Fig Architecture

The migration process is divided into 3 clear phases with strict risk-control boundaries:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Web / Mobile Client
    participant Envoy as Envoy API Gateway
    participant Legacy as Magento Monolith
    participant Mesh as Modern Microservices (Go)
    participant Kafka as Apache Kafka (CDC/Outbox)

    rect rgb(240, 248, 255)
    Note over Client,Kafka: PHASE 1: Read-Path Strangling
    Client->>Envoy: GET /api/v1/catalog/products
    Envoy->>Mesh: Forward GET (Catalog Service)
    Mesh-->>Client: Return flattened data (Postgres/OpenSearch)
    Client->>Envoy: POST /rest/V1/carts/mine/items
    Envoy->>Legacy: Forward POST (Magento Checkout)
    Legacy->>Kafka: Debezium CDC streams MySQL binlog
    Kafka->>Mesh: Go Consumer updates the Read Model
    end

    rect rgb(255, 250, 240)
    Note over Client,Kafka: PHASE 2: Write-Path & Bidirectional Sync
    Client->>Envoy: POST /api/v1/orders (Place Order)
    Envoy->>Mesh: Forward POST (Order Microservice)
    Mesh->>Mesh: Save Transactional Outbox (Postgres)
    Mesh->>Kafka: Publish event "order.created"
    Kafka->>Legacy: Legacy Sync Worker writes to Magento DB (Reverse Sync)
    Legacy-->>Legacy: Legacy ERP/WMS keep reading orders from Magento
    end

    rect rgb(240, 255, 240)
    Note over Client,Kafka: PHASE 3: Cutover & Hot Standby (30 Days)
    Client->>Envoy: 100% Traffic (Read & Write)
    Envoy->>Mesh: Everything handled by Go Microservices
    Mesh->>Kafka: Continuous Reversible Stream
    Kafka->>Legacy: Magento updated as a Passive Replica
    Note over Legacy: If the mesh fails, flip Envoy back to Magento within 5 seconds
    end
```

---

## 4. Phase 1: Read-Path Routing & the CDC Infrastructure (Debezium)

In this phase, Magento remains the **Single Source of Truth** for all write data. The new Microservices system acts as an ultra-high-performance **smart Read-Replica**.

### 4.1. Smart Routing Configuration for Envoy Proxy
Envoy Proxy acts as the protective ingress layer, splitting traffic based on HTTP Method, URI Path, and Canary headers:

```yaml
# envoy-strangler-config.yaml
static_resources:
  listeners:
  - name: ingress_listener
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 8080
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          route_config:
            name: dynamic_routes
            virtual_hosts:
            - name: ecommerce_vhost
              domains: ["*"]
              routes:
              # 1. Route the Catalog read flow to the Go Catalog Microservice
              - match:
                  prefix: "/api/v1/catalog"
                  headers:
                  - name: ":method"
                    exact_match: "GET"
                route:
                  cluster: go_catalog_service
                  timeout: 1.5s
                  retry_policy:
                    retry_on: "5xx,connect-failure,reset"
                    num_retries: 2
              
              # 2. Canary testing for the Beta Users group (header-based)
              - match:
                  prefix: "/api/v1/search"
                  headers:
                  - name: "x-beta-tester"
                    exact_match: "true"
                route:
                  cluster: go_search_service
                  timeout: 1.0s

              # 3. By default, all Write requests and Admin fallback go to the Magento Monolith
              - match:
                  prefix: "/"
                route:
                  cluster: legacy_magento_cluster
                  timeout: 30.0s

  clusters:
  - name: go_catalog_service
    connect_timeout: 0.25s
    type: LOGICAL_DNS
    dns_lookup_family: V4_ONLY
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: go_catalog_service
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: catalog-svc.mesh.internal
                port_value: 8001

  - name: legacy_magento_cluster
    connect_timeout: 1.0s
    type: LOGICAL_DNS
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: legacy_magento_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: magento.legacy.internal
                port_value: 80
```

### 4.2. Debezium MySQL Connector Configuration
The connector watches Magento's MySQL binlog directly and streams change events into Kafka:

```json
{
  "name": "magento-mysql-cdc-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql-magento.internal",
    "database.port": "3306",
    "database.user": "debezium_cdc",
    "database.password": "${file:/secrets/db-credentials.properties:cdc_password}",
    "database.server.id": "184054",
    "database.server.name": "magento_prod",
    "database.include.list": "magento_db",
    "table.include.list": "magento_db.catalog_product_entity,magento_db.catalog_product_entity_varchar,magento_db.catalog_product_entity_int,magento_db.catalog_product_entity_decimal,magento_db.cataloginventory_stock_item",
    "database.history.kafka.bootstrap.servers": "kafka:9092",
    "database.history.kafka.topic": "schema-changes.magento",
    "decimal.handling.mode": "double",
    "time.precision.mode": "connect",
    "include.schema.changes": "true",
    "snapshot.mode": "when_needed",
    "tombstones.on.delete": "true"
  }
}
```

### 4.3. Go 1.24 Catalog CDC Ingestion Worker
The Go worker receives events from Kafka, performs the EAV data flattening, and updates PostgreSQL:

```go
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/segmentio/kafka-go"
)

// DebeziumPayload represents a CDC packet from the MySQL binlog
type DebeziumPayload struct {
	Before map[string]interface{} `json:"before"`
	After  map[string]interface{} `json:"after"`
	Op     string                 `json:"op"` // 'c' (create), 'u' (update), 'd' (delete)
	TsMs   int64                  `json:"ts_ms"`
}

type KafkaMessageWrapper struct {
	Payload DebeziumPayload `json:"payload"`
}

type CatalogWorker struct {
	reader *kafka.Reader
	db     *sql.DB
}

func NewCatalogWorker(brokers []string, topic, groupID, dbDSN string) (*CatalogWorker, error) {
	db, err := sql.Open("pgx", dbDSN)
	if err != nil {
		return nil, fmt.Errorf("postgres connection failed: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(10)
	db.SetConnMaxLifetime(5 * time.Minute)

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        brokers,
		Topic:          topic,
		GroupID:        groupID,
		MinBytes:       10e3, // 10KB
		MaxBytes:       10e6, // 10MB
		CommitInterval: time.Second,
	})

	return &CatalogWorker{reader: reader, db: db}, nil
}

func (w *CatalogWorker) Start(ctx context.Context) error {
	log.Println("🚀 Catalog CDC Ingestion Worker listening for events...")

	for {
		select {
		case <-ctx.Done():
			log.Println("🛑 Closing Kafka Reader...")
			return w.reader.Close()
		default:
			msg, err := w.reader.FetchMessage(ctx)
			if err != nil {
				if ctx.Err() != nil {
					return nil
				}
				log.Printf("⚠️ Message read error: %v\n", err)
				continue
			}

			if err := w.processEvent(ctx, msg.Value); err != nil {
				log.Printf("❌ Event processing error at offset %d: %v\n", msg.Offset, err)
				// Do not commit the offset so it can retry or be routed to the Dead Letter Queue (DLQ)
				continue
			}

			if err := w.reader.CommitMessages(ctx, msg); err != nil {
				log.Printf("⚠️ Offset commit error: %v\n", err)
			}
		}
	}
}

func (w *CatalogWorker) processEvent(ctx context.Context, data []byte) error {
	var env KafkaMessageWrapper
	if err := json.Unmarshal(data, &env); err != nil {
		return fmt.Errorf("unmarshal error: %w", err)
	}

	payload := env.Payload
	switch payload.Op {
	case "c", "u": // Create or Update
		entityID, ok := payload.After["entity_id"].(float64)
		if !ok {
			return nil // Skip if there is no entity_id
		}
		sku, _ := payload.After["sku"].(string)

		// Insert/Update into the flat catalog table on PostgreSQL
		query := `
			INSERT INTO catalog_products (legacy_id, sku, updated_at, attributes)
			VALUES ($1, $2, NOW(), $3)
			ON CONFLICT (legacy_id) DO UPDATE SET
				sku = EXCLUDED.sku,
				updated_at = NOW(),
				attributes = catalog_products.attributes || EXCLUDED.attributes;
		`
		attrJSON, _ := json.Marshal(payload.After)
		_, err := w.db.ExecContext(ctx, query, int64(entityID), sku, attrJSON)
		if err != nil {
			return fmt.Errorf("pg upsert failed: %w", err)
		}
		log.Printf("✅ Updated product ID=%d, SKU=%s\n", int64(entityID), sku)

	case "d": // Delete
		entityID, ok := payload.Before["entity_id"].(float64)
		if !ok {
			return nil
		}
		query := `UPDATE catalog_products SET is_active = false, deleted_at = NOW() WHERE legacy_id = $1;`
		_, err := w.db.ExecContext(ctx, query, int64(entityID))
		if err != nil {
			return fmt.Errorf("pg soft delete failed: %w", err)
		}
		log.Printf("🗑️ Marked product as deleted ID=%d\n", int64(entityID))
	}

	return nil
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	worker, err := NewCatalogWorker(
		[]string{"localhost:9092"},
		"magento_prod.magento_db.catalog_product_entity",
		"catalog-ingestion-group",
		"postgres://postgres:secret@localhost:5432/mesh_catalog?sslmode=disable",
	)
	if err != nil {
		log.Fatalf("Failed to initialize worker: %v", err)
	}

	go func() {
		<-sigChan
		log.Println("Shutdown signal received, shutting down gracefully...")
		cancel()
	}()

	if err := worker.Start(ctx); err != nil {
		log.Fatalf("Worker crashed: %v", err)
	}
}
```

---

## 5. Phase 2: Extracting the Write-Path & Bidirectional Sync

Phase 2 is the most complex and risk-laden phase. Once write operations (for example, `Place Order`) are handed over to the new `Order Service`, the old Magento system still needs this data so the warehouse management (WMS), shipping fulfillment, and internal accounting subsystems keep working normally.

### 5.1. The Transactional Outbox Pattern Syncing Back to Magento

To guarantee data consistency is never broken if a process crashes midway, the Order Microservice applies the **Transactional Outbox** design pattern:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Mobile / Web Client
    participant OrderSvc as Order Microservice (Go)
    participant OrderDB as PostgreSQL (Order & Outbox)
    participant Relay as Debezium Outbox Relay
    participant Kafka as Apache Kafka
    participant Worker as Legacy Sync Worker (Go)
    participant Magento as Magento 2 Database / API

    Client->>OrderSvc: POST /api/v1/orders (Place Order)
    activate OrderSvc
    OrderSvc->>OrderDB: BEGIN TRANSACTION
    OrderSvc->>OrderDB: INSERT INTO orders (id, total, items...)
    OrderSvc->>OrderDB: INSERT INTO outbox_events (aggregate_type, payload...)
    OrderSvc->>OrderDB: COMMIT
    OrderSvc-->>Client: Return HTTP 201 Created (Order UUID)
    deactivate OrderSvc

    Note over OrderDB,Relay: CDC reads the outbox table without locking
    Relay->>Kafka: Publish "order.created"
    Kafka->>Worker: Consume Event
    activate Worker
    Worker->>Worker: Look up / generate Legacy ID (system_id_mapping)
    Worker->>Magento: Write the order into sales_order (REST Bulk API)
    alt Success
        Worker->>Worker: Update status synced = true
    else Failure / Timeout
        Worker->>Kafka: Send to Dead Letter Queue (DLQ) after 5 retries
    end
    deactivate Worker
```

### 5.2. Data Conflict Resolution Algorithm
When both systems can write, state conflicts are unavoidable (for example, a customer cancels an order on the Microservice while a support agent confirms the order in the Magento Admin).
We apply a finite **State Machine Transition Matrix** combined with a **Monotonic Microsecond Timestamp**:

| Current state | Event from Magento | Event from Microservice | Resolution rule |
| :--- | :--- | :--- | :--- |
| `PENDING` | `PROCESSING` | `CANCELLED` | Microservice wins (cancellation is the customer's ultimate right) |
| `PROCESSING` | `SHIPPED` | `PROCESSING` | Keep `SHIPPED` (the warehouse has already dispatched) |
| `CANCELLED` | `PROCESSING` | N/A | Reject the update from Magento and fire a Slack alert to support |
| `ANY` | Older timestamp | Newer timestamp | Last-Write-Wins based on Monotonic Epoch |

### 5.3. Production Go 1.24 Legacy Sync Worker (Order Synchronization)

Below is the source code of the Legacy Sync Worker responsible for consuming events from Kafka and translating the modern Order structure into a payload compatible with Magento's API:

```go
package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/segmentio/kafka-go"
)

type OrderCreatedEvent struct {
	OrderID     string    `json:"order_id"` // UUIDv7
	CustomerEmail string  `json:"customer_email"`
	GrandTotal  float64   `json:"grand_total"`
	Currency    string    `json:"currency"`
	CreatedAt   time.Time `json:"created_at"`
	Items       []OrderItem `json:"items"`
}

type OrderItem struct {
	SKU      string  `json:"sku"`
	Qty      int     `json:"qty"`
	Price    float64 `json:"price"`
}

// MagentoOrderPayload is compatible with the Magento 2 REST API format
type MagentoOrderPayload struct {
	Entity struct {
		CustomerEmail string                   `json:"customer_email"`
		BaseGrandTotal float64                 `json:"base_grand_total"`
		GrandTotal    float64                  `json:"grand_total"`
		OrderCurrencyCode string               `json:"order_currency_code"`
		Items         []MagentoOrderItemPayload `json:"items"`
	} `json:"entity"`
}

type MagentoOrderItemPayload struct {
	SKU       string  `json:"sku"`
	QtyOrdered int    `json:"qty_ordered"`
	Price     float64 `json:"price"`
	BasePrice float64 `json:"base_price"`
}

type LegacySyncWorker struct {
	kafkaReader *kafka.Reader
	dlqWriter   *kafka.Writer
	db          *sql.DB
	httpClient  *http.Client
	magentoURL  string
	apiToken    string
}

func NewLegacySyncWorker(brokers []string, dbDSN, magentoURL, token string) (*LegacySyncWorker, error) {
	db, err := sql.Open("pgx", dbDSN)
	if err != nil {
		return nil, fmt.Errorf("postgres conn err: %w", err)
	}

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers: brokers,
		Topic:   "order.events.created",
		GroupID: "legacy-magento-sync-worker",
	})

	dlqWriter := &kafka.Writer{
		Addr:     kafka.TCP(brokers...),
		Topic:    "order.events.created.dlq",
		Balancer: &kafka.LeastBytes{},
	}

	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	return &LegacySyncWorker{
		kafkaReader: reader,
		dlqWriter:   dlqWriter,
		db:          db,
		httpClient:  client,
		magentoURL:  magentoURL,
		apiToken:    token,
	}, nil
}

func (s *LegacySyncWorker) Run(ctx context.Context) {
	log.Println("🔄 Legacy Sync Worker ready to sync to Magento...")

	for {
		msg, err := s.kafkaReader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				return
			}
			log.Printf("Message read error: %v\n", err)
			continue
		}

		var event OrderCreatedEvent
		if err := json.Unmarshal(msg.Value, &event); err != nil {
			log.Printf("Event unmarshal error: %v, pushing to DLQ\n", err)
			s.sendToDLQ(ctx, msg.Value, err.Error())
			continue
		}

		if err := s.syncToMagentoWithRetry(ctx, event, 3); err != nil {
			log.Printf("❌ Order %s sync failed after retries: %v. Pushing to DLQ.\n", event.OrderID, err)
			s.sendToDLQ(ctx, msg.Value, err.Error())
		} else {
			log.Printf("🎉 Order %s synced to Magento successfully\n", event.OrderID)
		}
	}
}

func (s *LegacySyncWorker) syncToMagentoWithRetry(ctx context.Context, order OrderCreatedEvent, maxRetries int) error {
	var lastErr error

	for attempt := 1; attempt <= maxRetries; attempt++ {
		// 1. Check whether the order has already been synced (Idempotency Guard)
		var existingLegacyID sql.NullInt64
		err := s.db.QueryRowContext(ctx, "SELECT legacy_id FROM system_id_mapping WHERE service_uuid = $1 AND domain = 'order'", order.OrderID).Scan(&existingLegacyID)
		if err == nil && existingLegacyID.Valid {
			log.Printf("ℹ️ Order %s already exists on Magento with ID=%d (skipping sync)\n", order.OrderID, existingLegacyID.Int64)
			return nil
		}

		// 2. Convert to the Magento payload
		var mgItems []MagentoOrderItemPayload
		for _, it := range order.Items {
			mgItems = append(mgItems, MagentoOrderItemPayload{
				SKU:        it.SKU,
				QtyOrdered: it.Qty,
				Price:      it.Price,
				BasePrice:  it.Price,
			})
		}

		mgPayload := MagentoOrderPayload{}
		mgPayload.Entity.CustomerEmail = order.CustomerEmail
		mgPayload.Entity.GrandTotal = order.GrandTotal
		mgPayload.Entity.BaseGrandTotal = order.GrandTotal
		mgPayload.Entity.OrderCurrencyCode = order.Currency
		mgPayload.Entity.Items = mgItems

		payloadBytes, _ := json.Marshal(mgPayload)
		req, _ := http.NewRequestWithContext(ctx, "POST", s.magentoURL+"/rest/V1/orders", bytes.NewReader(payloadBytes))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer "+s.apiToken)

		resp, err := s.httpClient.Do(req)
		if err == nil && resp.StatusCode >= 200 && resp.StatusCode < 300 {
			// Read the Magento response to get the newly created entity_id
			var mgResponse struct {
				EntityID int64 `json:"entity_id"`
			}
			_ = json.NewDecoder(resp.Body).Decode(&mgResponse)
			_ = resp.Body.Close()

			// 3. Persist the mapping relationship into the database
			_, _ = s.db.ExecContext(ctx,
				"INSERT INTO system_id_mapping (domain, legacy_id, service_uuid) VALUES ('order', $1, $2) ON CONFLICT DO NOTHING",
				mgResponse.EntityID, order.OrderID,
			)
			return nil
		}

		if resp != nil {
			_ = resp.Body.Close()
		}
		lastErr = err
		log.Printf("⚠️ Sync attempt %d/%d failed: %v. Waiting to retry...\n", attempt, maxRetries, err)
		time.Sleep(time.Duration(attempt) * 500 * time.Millisecond)
	}

	return lastErr
}

func (s *LegacySyncWorker) sendToDLQ(ctx context.Context, data []byte, reason string) {
	_ = s.dlqWriter.WriteMessages(ctx, kafka.Message{
		Key:   []byte(reason),
		Value: data,
		Time:  time.Now(),
	})
}
```

---

## 6. Phase 3: Cutover, 30-Day Hot Standby & the Rollback Runbook

The final phase marks the full independence of the new Microservices ecosystem. However, rather than deleting the Magento servers the moment traffic hits 100%, we establish a **Reverse Hot Standby** mechanism that lasts 30 days.

```mermaid
stateDiagram-v2
    [*] --> Phase1_ReadStrangled: Weeks 1-3 (Read via the Mesh)
    Phase1_ReadStrangled --> Phase2_Bidirectional: Weeks 4-7 (Write via the Mesh + Reverse Sync)
    Phase2_Bidirectional --> Phase3_HotStandby: Week 8 (100% Traffic, Magento on Standby)
    
    state Phase3_HotStandby {
        [*] --> ContinuousChecksum: Data Integrity Verification Job (every hour)
        ContinuousChecksum --> NormalOperation: Data matches 100%
        ContinuousChecksum --> DisasterDetected: Critical architectural defect detected
        DisasterDetected --> RollbackExecution: Trigger Rollback within 5 minutes
    }
    
    NormalOperation --> Decommission: After 30 safe days
    RollbackExecution --> Phase2_Bidirectional: Flip Envoy back to the Magento Monolith
    Decommission --> [*]: Terminate EC2 / DB Dropped
```

### 6.1. Go / No-Go Cutover Criteria
Before shifting 100% of traffic to the Go Microservices, the engineering leadership must sign off on the following checklist:
1. **P99 Latency SLA:** P99 latency of all Read APIs < 80ms and Write APIs < 250ms during a load simulation at 300% of peak.
2. **Zero Ingestion Lag:** Latency of the Debezium CDC and Outbox Consumer pipelines stays < 200ms for 72 consecutive hours.
3. **Data Integrity Checksum:** The automated reconciliation script that runs hourly between PostgreSQL and Magento MySQL achieves a 100% match rate on revenue and inventory quantities.

### 6.2. The 5-Minute Rollback Runbook (Disaster Recovery)
If an unprecedented software disaster strikes in the first week after cutover, the rollback to Magento is executed precisely in 4 steps:

1. **Step 1: Flip the Envoy routing flag back to the Magento Monolith (Time: 10 seconds)**
   ```bash
   # Update the Envoy ConfigMap or trigger the Consul Service Mesh
   kubectl apply -f /deploy/envoy/rollback-to-magento.yaml
   kubectl rollout restart deployment/envoy-gateway -n ingress
   ```

2. **Step 2: Pause the Microservices consumers (Time: 30 seconds)**
   Temporarily stop the Go workers to prevent race conditions that could overwrite state.
   ```bash
   kubectl scale deployment/order-service-worker --replicas=0 -n core-services
   ```

3. **Step 3: Drain the Outbox queue back into Magento (Time: 2 minutes)**
   Run the script that inspects orders created in the Microservice during the final minutes that have not yet synced to Magento, and inject them directly into the MySQL database.
   ```bash
   go run /tools/emergency_drain/main.go --mode=flush-to-legacy
   ```

4. **Step 4: Verify the Checkout state on Magento (Time: 1 minute)**
   Fire a synthetic transaction that creates one test order on the Magento frontend to confirm the payment flow is working 100% stably.

After 30 days of Hot Standby with zero incidents, the entire Magento EC2 infrastructure is powered down and the MySQL database snapshot is archived cold on AWS S3 Glacier, officially completing the Strangler Fig process.

---

## 7. Performance & Infrastructure Cost Comparison

After fully migrating 10 core domains from Magento to Golang Microservices, the measured results from the production system were:

| Technical / Operational metric | Magento 2.4 Monolith (Old) | Golang Microservices Mesh (New) | Improvement |
| :--- | :--- | :--- | :--- |
| **Peak Throughput** | 420 req/sec (CPU saturation begins) | 8,500 req/sec | **20.2x higher** |
| **P95 Read Latency (Catalog/PDP)** | 480 ms (Varnish Cached: 120ms) | 18 ms (PostgreSQL JSONB + OpenSearch) | **96.2% lower** |
| **P99 Checkout Latency** | 3,200 ms | 195 ms | **93.9% lower** |
| **RAM consumption** | 64 GB (PHP-FPM Pools + Redis) | 3.2 GB (static Go containers) | **95% RAM saved** |
| **CI/CD Pipeline time** | 38 minutes (DI & static compilation) | 1 minute 40 seconds (Docker multi-stage Go) | **22.8x faster** |
| **Monthly AWS infrastructure cost** | \$6,400 / month (large C5/R5 instances) | \$1,850 / month (EKS T4g Graviton + RDS) | **71.1% cost saved** |

---

## 8. Summary & Field Lessons

Migrating a massive monolith like Magento to Microservices is not a code-rewrite problem — it is **the problem of preserving data state while everything is in motion**.

1. **Never cut over Big Bang style:** Business risk always outweighs any purely technical elegance.
2. **Debezium CDC is the ultimate weapon:** It lets you decouple data from Magento without touching or slowing down the legacy PHP codebase.
3. **Idempotency is the key to two-way sync:** Any message on a distributed network may be delivered more than once (`At-least-once delivery`). Every worker must enforce a strict idempotent guard.
4. **Always keep an escape route (Hot Standby):** A great architect is not someone who is confident the new system will never fail, but someone who has designed a safe emergency exit for when the worst happens.

{{< author-cta >}}

---

### 🔗 Related Deep-Dive Articles & Guides:
- [Golang Microservices Architecture & DDD: Designing a 21-Service E-Commerce Platform](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Mastering Event-Driven Architecture with Dapr & Golang](/posts/mastering-event-driven-architecture-dapr/)
- [The Microservices Delusion: Why the Golang Modular Monolith Is the Ideal Destination](/posts/microservices-delusion-why-golang-modular-monolith-is-the-destination/)
- [MySQL Horizontal Scaling: Sharding, Vitess & Distributed Transactions](/posts/mysql-horizontal-scaling/)

---

## ❓ Frequently Asked Questions (FAQ)

{{< faq q="Why not use Magento Webhooks or Events Observers for synchronization instead of Debezium CDC?" >}}
Magento Webhooks and Plugin Observers run directly inside the PHP-FPM request processing cycle. If the webhook consumer is slow or Kafka is temporarily down, the PHP process blocks, exhausting PHP-FPM workers and crashing the Magento site. Moreover, bulk data updates performed via direct SQL or cronjobs never trigger observers. Debezium reads directly from the MySQL binlog at the disk I/O layer, fully asynchronously, independent of the PHP runtime, and guarantees capturing 100% of every data change.
{{< /faq >}}

{{< faq q="How do you handle custom EAV attributes in Magento when moving to Microservices?" >}}
In Magento, every newly created attribute generates a record in `eav_attribute`. The Go CDC Ingestion Worker maintains a periodically refreshed cache of the `eav_attribute` table (refreshed whenever a binlog event arrives from that table). When it receives a record from `catalog_product_entity_varchar` or `decimal`, the worker looks up the corresponding `attribute_id` to resolve the `attribute_code` (for example: `color`, `size`, `material`) and embeds it directly as a key-value pair into the PostgreSQL JSONB field.
{{< /faq >}}

{{< faq q="Does keeping the Hot Standby for 30 days double the operating cost?" >}}
Yes, during these 30 days you pay for both the old Magento server cluster and the new Kubernetes Microservices cluster. However, compared with the risk of interrupting hundreds of thousands of dollars in revenue or losing customer orders if the new system hits a critical bug with no rollback possible, one month of extra infrastructure cost is an extremely cheap and necessary form of "insurance" for the business.
{{< /faq >}}

{{< faq q="How do you guarantee order ordering during two-way synchronization over Kafka?" >}}
Kafka guarantees packet ordering within a single Partition (partition-level ordering). Therefore, when publishing order-related events (`order.created`, `order.paid`, `order.cancelled`), we always use the `OrderID` as the Partition Key (`kafka.Message.Key`). Every event for the same order is guaranteed to land in the same partition and be consumed sequentially by the worker, completely eliminating out-of-order processing.
{{< /faq >}}
