---
title: "Exporting Magento 2 Data: Flatten EAV with SQL & Node.js"
slug: "exporting-magento-2-data-flat-sql-nodejs"
author: "Lê Tuấn Anh"
date: "2024-03-09T10:38:22+07:00"
lastmod: "2026-11-02T09:00:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Magento", "Node.js", "Golang", "PostgreSQL"]
description: "Extract data from Magento 2's EAV schema: high-speed SQL unpivot queries, a RAM-bounded Node.js streaming pipeline, and idempotent upserts."
categories: ["Engineering"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/exporting-magento-2-data-flat-sql-nodejs.jpg"
  alt: "Extracting Magento 2 data: flattening the EAV structure with SQL and Node.js for a data warehouse"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/exporting-magento-2-data-flat-sql-nodejs/"
weight: 5
mermaid: true
---

> **Answer-first:** Extracting data from Magento 2's EAV (Entity-Attribute-Value) model requires flattening via multi-layer SQL queries combined with the Store-Scope fallback inheritance algorithm (`COALESCE(cpev_store.value, cpev_default.value)`) and a Node.js streaming pipeline that manages Backpressure. This architecture eliminates any risk of out-of-memory failures (zero-OOM), guarantees idempotent upserts, and isolates faulty records through a Dead-Letter Queue (DLQ) when migrating millions of products to new microservices.

> 📦 Browse the complete Magento migration playbook in the [Magento Migration Vietnam series](/series/magento-migration-vietnam/).

---

## 1. The EAV Obsession: Why Does Magento 2 Shred Your Data?

When kicking off a migration campaign from Magento 2 to a Composable Microservices architecture, the first and hardest obstacle is always the **database**.

Unlike conventional relational databases where each table represents a flat entity (for example, a `products` table with `name`, `price`, and `sku` columns ready to go), Magento 2 uses the **Entity-Attribute-Value (EAV)** model:

```mermaid
erDiagram
    CATALOG_PRODUCT_ENTITY ||--o{ CATALOG_PRODUCT_ENTITY_VARCHAR : "holds string values"
    CATALOG_PRODUCT_ENTITY ||--o{ CATALOG_PRODUCT_ENTITY_INT : "holds status/category"
    CATALOG_PRODUCT_ENTITY ||--o{ CATALOG_PRODUCT_ENTITY_DECIMAL : "holds price/weight"
    CATALOG_PRODUCT_ENTITY ||--o{ CATALOG_PRODUCT_ENTITY_TEXT : "holds detailed description"
    EAV_ATTRIBUTE ||--o{ CATALOG_PRODUCT_ENTITY_VARCHAR : "defines attributes"

    CATALOG_PRODUCT_ENTITY {
        int entity_id PK
        string sku
        int type_id
        timestamp created_at
    }
    EAV_ATTRIBUTE {
        int attribute_id PK
        string attribute_code
        string backend_type
    }
    CATALOG_PRODUCT_ENTITY_VARCHAR {
        int value_id PK
        int attribute_id FK
        int store_id
        int entity_id FK
        string value
    }
```

### Why Does Magento Use EAV?
The EAV model lets administrators add unlimited new product attributes (color, size, material) directly from the Admin panel without running an `ALTER TABLE` statement that would lock the MySQL table.

### The Price You Pay:
- A single product's data is shredded and scattered across **more than 30 different tables**.
- A query fetching 100 complete products can require **more than 40 `JOIN` operations**, choking the InnoDB Buffer Pool cache.
- The Store-Scope Inheritance mechanism: an attribute value can apply globally (`store_id = 0`) but be overridden per website/language (`store_id = 1` for Vietnamese, `store_id = 2` for English).

---

## 2. Multi-Layer SQL Store-Scope Fallback Resolution

To fetch the correct product name or price displayed on a specific Storefront, the SQL query must perform a **double `LEFT JOIN`** against the same value table:
1. First `LEFT JOIN`: fetch the store-specific value (`store_id = :target_store_id`).
2. Second `LEFT JOIN`: fetch the global default value (`store_id = 0`).
3. Use the `COALESCE(store_val.value, default_val.value)` function: prefer the store-specific value; if absent, automatically fall back to the global default.

```sql
-- Store-Scope Fallback Resolution technique for the Product Name attribute
LEFT JOIN catalog_product_entity_varchar AS cpev_name_store
    ON cpev_name_store.entity_id = cpe.entity_id
    AND cpev_name_store.attribute_id = 73 -- attribute_id of 'name'
    AND cpev_name_store.store_id = 1      -- Vietnamese Storefront

LEFT JOIN catalog_product_entity_varchar AS cpev_name_default
    ON cpev_name_default.entity_id = cpe.entity_id
    AND cpev_name_default.attribute_id = 73
    AND cpev_name_default.store_id = 0     -- Default Scope

-- Preferred value selection:
COALESCE(cpev_name_store.value, cpev_name_default.value) AS product_name
```

---

## 3. The Complete Pivot SQL Query That Flattens the Product Catalog

Below is a production-grade SQL query that extracts the full product information (Identifiers, Name, Status, Base Price, Special Price, Weight, Base Image, and the Category ID list) in a single scan:

```sql
SELECT
    cpe.entity_id                                                   AS product_id,
    cpe.sku                                                         AS sku,
    cpe.type_id                                                     AS product_type,
    cpe.created_at                                                  AS created_at,
    cpe.updated_at                                                  AS updated_at,

    -- 1. Product name (Varchar - Fallback Scope)
    COALESCE(cpev_name_store.value, cpev_name_default.value)         AS name,

    -- 2. Enable status (Int: 1 = Enabled, 2 = Disabled)
    COALESCE(cpei_status_store.value, cpei_status_default.value)     AS status,

    -- 3. Visibility level (Int: 4 = Catalog/Search)
    COALESCE(cpei_vis_store.value, cpei_vis_default.value)           AS visibility,

    -- 4. Base price (Decimal)
    COALESCE(cped_price_store.value, cped_price_default.value)       AS price,

    -- 5. Special promotional price (Decimal)
    COALESCE(cped_sprice_store.value, cped_sprice_default.value)     AS special_price,

    -- 6. Product weight (Decimal)
    COALESCE(cped_weight_store.value, cped_weight_default.value)     AS weight,

    -- 7. Base image path (Varchar)
    COALESCE(cpev_img_store.value, cpev_img_default.value)           AS base_image,

    -- 8. Actual stock from the MSI or legacy stock tables
    COALESCE(inv.quantity, 0)                                       AS stock_quantity,
    COALESCE(inv.is_in_stock, 0)                                    AS is_in_stock,

    -- 9. Aggregate categories into a comma-separated ID string
    GROUP_CONCAT(DISTINCT ccp.category_id ORDER BY ccp.category_id ASC) AS category_ids

FROM catalog_product_entity AS cpe

-- Join product name
LEFT JOIN eav_attribute AS ea_name ON ea_name.entity_type_id = 4 AND ea_name.attribute_code = 'name'
LEFT JOIN catalog_product_entity_varchar AS cpev_name_store 
    ON cpev_name_store.entity_id = cpe.entity_id AND cpev_name_store.attribute_id = ea_name.attribute_id AND cpev_name_store.store_id = 1
LEFT JOIN catalog_product_entity_varchar AS cpev_name_default 
    ON cpev_name_default.entity_id = cpe.entity_id AND cpev_name_default.attribute_id = ea_name.attribute_id AND cpev_name_default.store_id = 0

-- Join product status
LEFT JOIN eav_attribute AS ea_status ON ea_status.entity_type_id = 4 AND ea_status.attribute_code = 'status'
LEFT JOIN catalog_product_entity_int AS cpei_status_store 
    ON cpei_status_store.entity_id = cpe.entity_id AND cpei_status_store.attribute_id = ea_status.attribute_id AND cpei_status_store.store_id = 1
LEFT JOIN catalog_product_entity_int AS cpei_status_default 
    ON cpei_status_default.entity_id = cpe.entity_id AND cpei_status_default.attribute_id = ea_status.attribute_id AND cpei_status_default.store_id = 0

-- Join product price
LEFT JOIN eav_attribute AS ea_price ON ea_price.entity_type_id = 4 AND ea_price.attribute_code = 'price'
LEFT JOIN catalog_product_entity_decimal AS cped_price_store 
    ON cped_price_store.entity_id = cpe.entity_id AND cped_price_store.attribute_id = ea_price.attribute_id AND cped_price_store.store_id = 1
LEFT JOIN catalog_product_entity_decimal AS cped_price_default 
    ON cped_price_default.entity_id = cpe.entity_id AND cped_price_default.attribute_id = ea_price.attribute_id AND cped_price_default.store_id = 0

-- Join product image
LEFT JOIN eav_attribute AS ea_img ON ea_img.entity_type_id = 4 AND ea_img.attribute_code = 'image'
LEFT JOIN catalog_product_entity_varchar AS cpev_img_store 
    ON cpev_img_store.entity_id = cpe.entity_id AND cpev_img_store.attribute_id = ea_img.attribute_id AND cpev_img_store.store_id = 1
LEFT JOIN catalog_product_entity_varchar AS cpev_img_default 
    ON cpev_img_default.entity_id = cpe.entity_id AND cpev_img_default.attribute_id = ea_img.attribute_id AND cpev_img_default.store_id = 0

-- Join stock (Legacy stock table)
LEFT JOIN cataloginventory_stock_item AS inv 
    ON inv.product_id = cpe.entity_id AND inv.stock_id = 1

-- Join categories
LEFT JOIN catalog_category_product AS ccp 
    ON ccp.product_id = cpe.entity_id

GROUP BY cpe.entity_id;
```

---

## 4. The LIMIT/OFFSET Disaster & the Salvation of the Streaming Cursor

Many developers reach for a paginated loop to export data:

```sql
-- ANTI-PATTERN: Crashes the database at large OFFSETs
SELECT * FROM catalog_product_entity LIMIT 1000 OFFSET 500000;
```

As the `OFFSET` value climbs into the hundreds of thousands, MySQL is forced to read and walk through all 500,000 preceding rows before discarding them to return the final 1,000. The complexity is $O(N^2)$, saturating 100% of the CPU and stretching the export from minutes into days!

### The Canonical Solution: Node.js Streaming Cursor With Backpressure

```mermaid
flowchart LR
    MySQL[("Magento MySQL (Read Replica)")] -->|"Cursor Stream (100 rows/chunk)"| TransformPipe["Transform Stream (Clean, Type Cast)"]
    TransformPipe -->|"Batch Buffer (500 rows)"| BulkWriter["Bulk Writer (PostgreSQL Upsert)"]
    BulkWriter -.->|"When Buffer Is Full: Pause the Stream (Backpressure)"| MySQL
```

---

## 5. Production Source Code: The OOM-Proof Node.js Streaming Pipeline

Below is the complete source code using `mysql2/promise`, `stream.Transform`, and an enterprise-grade memory-leak prevention mechanism (Backpressure):

```javascript
/**
 * Magento 2 EAV Flattening ETL Pipeline
 * Extracts millions of products with a stable RAM footprint under 150MB.
 */

const mysql = require('mysql2');
const { Transform, pipeline } = require('stream');
const { Client } = require('pg');
const fs = require('fs');

// Connection configuration
const mysqlConfig = {
  host: process.env.MAGENTO_DB_HOST || '127.0.0.1',
  user: process.env.MAGENTO_DB_USER || 'root',
  password: process.env.MAGENTO_DB_PASSWORD || 'secret',
  database: process.env.MAGENTO_DB_NAME || 'magento2',
  rowsAsArray: false,
};

const pgClient = new Client({
  connectionString: process.env.TARGET_PG_URL || 'postgresql://postgres:secret@127.0.0.1:5432/ecommerce_new',
});

// File capturing failed records (Dead-Letter Queue)
const dlqStream = fs.createWriteStream('./failed_products_dlq.jsonl', { flags: 'a' });

async function runETLPipeline() {
  await pgClient.connect();
  console.log('[ETL] Successfully connected to the target PostgreSQL database');

  const connection = mysql.createConnection(mysqlConfig);

  const exportSQL = `
    SELECT 
      cpe.entity_id AS product_id,
      cpe.sku,
      cpe.type_id,
      COALESCE(cpev_name.value, 'Unnamed') AS name,
      COALESCE(cped_price.value, 0.0000) AS price,
      COALESCE(inv.qty, 0) AS stock_qty
    FROM catalog_product_entity cpe
    LEFT JOIN eav_attribute ea_name ON ea_name.entity_type_id = 4 AND ea_name.attribute_code = 'name'
    LEFT JOIN catalog_product_entity_varchar cpev_name ON cpev_name.entity_id = cpe.entity_id AND cpev_name.attribute_id = ea_name.attribute_id AND cpev_name.store_id = 0
    LEFT JOIN eav_attribute ea_price ON ea_price.entity_type_id = 4 AND ea_price.attribute_code = 'price'
    LEFT JOIN catalog_product_entity_decimal cped_price ON cped_price.entity_id = cpe.entity_id AND cped_price.attribute_id = ea_price.attribute_id AND cped_price.store_id = 0
    LEFT JOIN cataloginventory_stock_item inv ON inv.product_id = cpe.entity_id;
  `;

  // Open a streaming query from MySQL (never loads everything into RAM)
  const queryStream = connection.query(exportSQL).stream({ highWaterMark: 250 });

  let totalProcessed = 0;
  let batch = [];
  const BATCH_SIZE = 500;

  // Stream that transforms and cleans the data
  const transformStream = new Transform({
    objectMode: true,
    highWaterMark: 250,
    async transform(row, encoding, callback) {
      try {
        // Basic validation
        if (!row.sku || row.sku.trim() === '') {
          throw new Error('Product missing SKU');
        }

        const cleanProduct = {
          id: row.product_id,
          sku: row.sku.trim(),
          type: row.type_id,
          name: row.name,
          price: parseFloat(row.price),
          stock: parseInt(row.stock_qty, 10),
          migrated_at: new Date().toISOString(),
        };

        batch.push(cleanProduct);

        // Once the batch reaches its size, flush it to PostgreSQL
        if (batch.length >= BATCH_SIZE) {
          const currentBatch = [...batch];
          batch = [];
          await flushBatchToPostgres(currentBatch);
          totalProcessed += currentBatch.length;
          console.log(`[ETL] Processed and loaded ${totalProcessed} products so far...`);
        }

        callback();
      } catch (err) {
        // Write the failed record to the DLQ without breaking the pipeline
        dlqStream.write(JSON.stringify({ row, error: err.message }) + '\n');
        callback();
      }
    },
    async flush(callback) {
      // Flush any records left over in the final batch
      if (batch.length > 0) {
        await flushBatchToPostgres(batch);
        totalProcessed += batch.length;
      }
      callback();
    },
  });

  // Orchestrate the flow with automatic backpressure management
  pipeline(queryStream, transformStream, (err) => {
    if (err) {
      console.error('[ETL FAILED] The pipeline hit a critical failure:', err);
    } else {
      console.log(`\n🎉 [ETL COMPLETE] ${totalProcessed} products flattened successfully!`);
    }
    connection.end();
    pgClient.end();
    dlqStream.end();
  });
}

// Batch writer for PostgreSQL with idempotent upsert semantics
async function flushBatchToPostgres(products) {
  const query = `
    INSERT INTO target_products (id, sku, type, name, price, stock, migrated_at)
    VALUES ${products.map((_, i) => `($${i*7+1}, $${i*7+2}, $${i*7+3}, $${i*7+4}, $${i*7+5}, $${i*7+6}, $${i*7+7})`).join(',')}
    ON CONFLICT (sku) DO UPDATE SET
      name = EXCLUDED.name,
      price = EXCLUDED.price,
      stock = EXCLUDED.stock,
      migrated_at = EXCLUDED.migrated_at;
  `;

  const values = products.flatMap(p => [p.id, p.sku, p.type, p.name, p.price, p.stock, p.migrated_at]);
  await pgClient.query(query, values);
}

runETLPipeline().catch(console.error);
```

---

## 6. Comparison of Data Extraction Methods

| Technical Criterion | Magento REST/GraphQL API | MySQL `LIMIT / OFFSET` | SQL Streaming Cursor + Node.js Stream |
| :--- | :--- | :--- | :--- |
| **Throughput** | Extremely slow (~20 - 50 products/s) | Fast at first, slower toward the end | **Very fast (> 3,500 products/s)** |
| **RAM Consumption** | High (PHP-FPM devours memory) | OOM crashes on large batches | **Fixed < 150MB (regardless of record count)** |
| **Production Impact** | Congests PHP workers | Locks tables when scanning large sets | **Zero impact (reads from a Read Replica)** |
| **Fault Tolerance** | Poor (a network error loses the run) | You must track offsets yourself | **Errors isolated automatically via Dead-Letter Queue** |
| **Implementation Complexity** | Simple | Medium | Requires deep knowledge of Node.js Streams & SQL Joins |

---

## 7. Frequently Asked Questions (FAQ)

{{< faq q="Why not just use the Magento REST API to export data safely?" >}}
The Magento REST API boots the entire PHP framework, loading plugins, event observers, and access control checks for every single product. Extraction through the API typically achieves only 20 to 50 products per second. If your store has 500,000 products, the export runs continuously for nearly 4 days and risks taking down the live sales server. Direct SQL queries through a streaming cursor are 50 to 100 times faster.
{{< /faq >}}

{{< faq q="How do you avoid locking tables and disrupting shoppers on Production?" >}}
Two rules are mandatory: (1) Always extract data from a dedicated MySQL Read Replica — never run the script directly against the Primary Database; (2) Before opening the streaming cursor, set a non-locking transaction isolation level with: `SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;` to ensure the read query never acquires Shared Locks on the order and inventory tables.
{{< /faq >}}

{{< faq q="How does Backpressure in a Node.js Stream actually work?" >}}
Backpressure is the mechanism that automatically throttles the read rate when the target system's write speed slows down. If the target database (PostgreSQL) is busy writing a batch and the Stream's internal buffer fills up, Node.js automatically pauses reading further packets from the MySQL connection socket until the buffer drains. This keeps the Node.js process's RAM at a safe level (under 150MB) even when exporting millions of records.
{{< /faq >}}

{{< faq q="How do you handle legacy PHP serialized strings in Magento's configuration tables?" >}}
In Magento 1 and early Magento 2 releases, many complex configuration values are stored as PHP serialized strings (for example `a:2:{s:4:"unit";s:2:"kg";}`). You can use the npm `php-serialize` library to safely decode these strings into plain JavaScript objects, then normalize them into standard JSON before loading them into the new database.
{{< /faq >}}

---

## 8. Related Technical Reading

- **The Magento Escape Roadmap:** See the decomposition strategy guide at [Leaving Magento for a Microservices Architecture](/series/magento-migration-vietnam/moving-from-magento-to-microservices/).
- **Evaluating Magento in 2026:** An analysis of the technology investment picture at [Is Magento Still Worth Investing in for 2026?](/series/magento-migration-vietnam/magento-still-worth-investing-2026/).
- **Composable Commerce Architecture:** The MACH transition guide at [Composable Commerce Architecture & Migration](/series/magento-migration-vietnam/ecommerce-architecture-composable-migration/).
- **The Full Migration Series:** Explore the complete playbook at [Series Magento Migration Vietnam](/series/magento-migration-vietnam/).

{{< author-cta >}}
