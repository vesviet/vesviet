---
title: "Exporting Magento 2 Data: Flattening the EAV Model with SQL and Node.js"
slug: "exporting-magento-2-data-flat-sql-nodejs"
date: "2024-03-09T03:38:22+00:00"
draft: false
tags: ["Magento", "SQL", "Node.js", "Data Migration", "EAV", "ETL"]
description: "Production-grade guide to extracting data from Magento 2's EAV model. Includes direct SQL queries and a resilient Node.js streaming pipeline."
categories: ["Engineering"]
ShowToc: true
TocOpen: true
---

When migrating off Magento 2, the first obstacle is always the database schema. Magento does not store data in clean flat rows — it uses an **Entity-Attribute-Value (EAV)** model that spreads data across dozens of tables with store-scope inheritance. Understanding this before writing SQL will save you days.

This guide covers two extraction problems: **order export** (the simpler case) and **product catalog export** (the genuinely hard case), followed by a production-grade Node.js pipeline to ingest that data into your new service databases.

## Part 1: Exporting Orders

Order data lives across `sales_order`, `sales_order_address`, `sales_order_payment`, and `sales_order_item`. Unlike the product catalog, this is standard foreign-key joins — not full EAV pivoting.

### Full Order + Payment + Shipping Export

```sql
SELECT
    so.entity_id            AS order_id,
    so.increment_id         AS magento_order_number,
    so.status               AS order_status,
    so.grand_total          AS total_amount,
    so.base_currency_code   AS currency,
    so.created_at           AS order_created_at,
    so.customer_email,
    so.customer_firstname   AS customer_first,
    so.customer_lastname    AS customer_last,

    -- Shipping address (denormalized)
    soa.street              AS ship_street,
    soa.city                AS ship_city,
    soa.region              AS ship_region,
    soa.postcode            AS ship_postcode,
    soa.country_id          AS ship_country,
    soa.telephone           AS ship_phone,

    -- Payment method
    sop.method              AS payment_method,
    sop.last_trans_id       AS payment_transaction_id,

    -- Shipment (NULL if not yet fulfilled)
    sos.entity_id           AS shipment_id,
    sos.created_at          AS shipped_at

FROM sales_order so
LEFT JOIN sales_order_address soa
    ON soa.parent_id = so.entity_id AND soa.address_type = 'shipping'
LEFT JOIN sales_order_payment sop
    ON sop.parent_id = so.entity_id
LEFT JOIN sales_shipment sos
    ON sos.order_id = so.entity_id

WHERE so.status NOT IN ('canceled', 'fraud')
  AND so.created_at >= '2022-01-01 00:00:00'
ORDER BY so.created_at ASC;
```

### Order Line Items (Second Pass)

```sql
SELECT
    soi.order_id,
    soi.sku,
    soi.name                AS product_name,
    soi.qty_ordered,
    soi.qty_shipped,
    soi.qty_refunded,
    soi.price               AS unit_price,
    soi.row_total,
    soi.product_type,
    soi.parent_item_id      -- non-null for configurable child rows

FROM sales_order_item soi

WHERE soi.parent_item_id IS NULL  -- skip phantom child rows for configurables
ORDER BY soi.order_id ASC, soi.item_id ASC;
```

Join on `order_id` in your ingestion script to reconstruct the full order object.

---

## Part 2: Exporting the Product Catalog (The Hard Part)

This is where most migration engineers underestimate the effort. The product catalog uses full EAV with **store scope inheritance**: a value at `store_id = 0` (Admin/Global) is the default; a value at a specific `store_id` overrides it for that store view. A naive `SELECT *` will return corrupted or incomplete data.

The correct approach is a two-step process.

### Step 1: Materialize Attribute IDs

The `attribute_id` values are **environment-specific** — they differ between Magento installations. Run this once and use the result to populate your export query:

```sql
SELECT attribute_id, attribute_code, backend_type
FROM eav_attribute
WHERE entity_type_id = (
    SELECT entity_type_id FROM eav_entity_type
    WHERE entity_type_code = 'catalog_product'
)
AND attribute_code IN (
    'name', 'url_key', 'description', 'short_description',
    'price', 'special_price', 'status', 'visibility', 'weight'
);
```

### Step 2: Flattened Product Export with Store-Scope Fallback

This query exports products for store `store_id = 1`. For each attribute, it prefers the store-specific value and falls back to the global default (`store_id = 0`). Replace the `attribute_id` values with results from Step 1:

```sql
SELECT
    e.entity_id,
    e.sku,
    e.type_id                                           AS product_type,
    e.created_at,

    -- Name (varchar): prefer store-specific, fallback to global
    COALESCE(v_name_s.value, v_name_g.value)            AS name,
    COALESCE(v_url_s.value, v_url_g.value)              AS url_key,

    -- Status: 1=Enabled, 2=Disabled (int)
    COALESCE(i_status_s.value, i_status_g.value)        AS status,
    -- Visibility: 1=Not visible, 4=Catalog+Search (int)
    COALESCE(i_vis_s.value, i_vis_g.value)              AS visibility,

    -- Price (decimal — always global scope in Magento)
    d_price.value                                       AS price,
    d_special.value                                     AS special_price,
    d_weight.value                                      AS weight

FROM catalog_product_entity e

-- === VARCHAR: name ===
LEFT JOIN catalog_product_entity_varchar v_name_s
    ON v_name_s.entity_id = e.entity_id AND v_name_s.attribute_id = 73 AND v_name_s.store_id = 1
LEFT JOIN catalog_product_entity_varchar v_name_g
    ON v_name_g.entity_id = e.entity_id AND v_name_g.attribute_id = 73 AND v_name_g.store_id = 0

-- === VARCHAR: url_key ===
LEFT JOIN catalog_product_entity_varchar v_url_s
    ON v_url_s.entity_id = e.entity_id AND v_url_s.attribute_id = 120 AND v_url_s.store_id = 1
LEFT JOIN catalog_product_entity_varchar v_url_g
    ON v_url_g.entity_id = e.entity_id AND v_url_g.attribute_id = 120 AND v_url_g.store_id = 0

-- === INT: status ===
LEFT JOIN catalog_product_entity_int i_status_s
    ON i_status_s.entity_id = e.entity_id AND i_status_s.attribute_id = 96 AND i_status_s.store_id = 1
LEFT JOIN catalog_product_entity_int i_status_g
    ON i_status_g.entity_id = e.entity_id AND i_status_g.attribute_id = 96 AND i_status_g.store_id = 0

-- === INT: visibility ===
LEFT JOIN catalog_product_entity_int i_vis_s
    ON i_vis_s.entity_id = e.entity_id AND i_vis_s.attribute_id = 99 AND i_vis_s.store_id = 1
LEFT JOIN catalog_product_entity_int i_vis_g
    ON i_vis_g.entity_id = e.entity_id AND i_vis_g.attribute_id = 99 AND i_vis_g.store_id = 0

-- === DECIMAL: price, special_price, weight (global only) ===
LEFT JOIN catalog_product_entity_decimal d_price
    ON d_price.entity_id = e.entity_id AND d_price.attribute_id = 77 AND d_price.store_id = 0
LEFT JOIN catalog_product_entity_decimal d_special
    ON d_special.entity_id = e.entity_id AND d_special.attribute_id = 78 AND d_special.store_id = 0
LEFT JOIN catalog_product_entity_decimal d_weight
    ON d_weight.entity_id = e.entity_id AND d_weight.attribute_id = 80 AND d_weight.store_id = 0

-- Only export enabled products
WHERE COALESCE(i_status_s.value, i_status_g.value) = 1
ORDER BY e.entity_id ASC;
```

> **Performance:** On catalogs with 25,000+ SKUs, this query will be slow. Run `EXPLAIN ANALYZE` first, ensure composite indexes exist on `(entity_id, attribute_id, store_id)` for each EAV value table, and batch by `entity_id` ranges (`WHERE e.entity_id BETWEEN 1 AND 5000`) to avoid locking your production database.

---

## Part 3: The Production Node.js Ingestion Pipeline

With data exported to CSV, you need a streaming pipeline that handles gigabytes without OOM, with batching, retry logic, idempotency, and a dead-letter queue for failed rows.

### Pipeline Architecture

```
CSV File → Readable Stream → csv-parse → Batch Collector → DB Upsert (with retry)
                                                         ↓ (on max retries)
                                                   Dead-Letter File (JSONL)
```

### Implementation

```javascript
// migrate.js — Production-grade Magento → PostgreSQL pipeline
const { pipeline, Transform } = require('stream');
const { promisify } = require('util');
const { parse } = require('csv-parse');
const fs = require('fs');
const db = require('./db'); // your pg connection pool

const pipe = promisify(pipeline);

const BATCH_SIZE = 500;
const MAX_RETRIES = 3;
const RETRY_BASE_MS = 500;

const dlqStream = fs.createWriteStream('./failed-rows.jsonl', { flags: 'a' });
let processed = 0, failed = 0;
const startTime = Date.now();

// Exponential backoff retry
async function withRetry(fn, label) {
    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {
            return await fn();
        } catch (err) {
            if (attempt === MAX_RETRIES) throw err;
            const delay = RETRY_BASE_MS * Math.pow(2, attempt - 1);
            console.warn(`\n⚠ ${label} failed (attempt ${attempt}). Retrying in ${delay}ms…`);
            await new Promise(r => setTimeout(r, delay));
        }
    }
}

// Upsert batch — idempotent by magento_order_id
async function upsertBatch(batch) {
    const client = await db.connect();
    try {
        await client.query('BEGIN');
        for (const row of batch) {
            await client.query(`
                INSERT INTO orders (
                    magento_order_id, magento_increment_id, status,
                    total_amount, currency, customer_email, created_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7)
                ON CONFLICT (magento_order_id) DO UPDATE SET
                    status       = EXCLUDED.status,
                    total_amount = EXCLUDED.total_amount,
                    updated_at   = NOW()
            `, [
                row.order_id, row.magento_order_number, row.order_status,
                parseFloat(row.total_amount) || 0, row.currency,
                row.customer_email, row.order_created_at
            ]);
        }
        await client.query('COMMIT');
    } catch (err) {
        await client.query('ROLLBACK');
        throw err;
    } finally {
        client.release();
    }
}

// Transform stream: collect rows into batches, flush with backpressure
function createBatchCollector(batchSize, onBatch) {
    let buffer = [];

    const flush = async (rows, callback) => {
        try {
            await withRetry(() => onBatch(rows), `batch ~row ${processed}`);
            processed += rows.length;
            process.stdout.write(
                `\r✓ ${processed.toLocaleString()} rows | ✗ ${failed} failed | ` +
                `${((Date.now() - startTime) / 1000).toFixed(0)}s elapsed`
            );
        } catch (err) {
            failed += rows.length;
            console.error(`\n✗ Permanent batch failure: ${err.message}`);
            rows.forEach(r => dlqStream.write(JSON.stringify(r) + '\n'));
        }
        callback();
    };

    return new Transform({
        objectMode: true,
        async transform(row, _enc, callback) {
            buffer.push(row);
            if (buffer.length >= batchSize) {
                const toFlush = buffer.splice(0, batchSize);
                await flush(toFlush, callback);
            } else {
                callback();
            }
        },
        async flush(callback) {
            if (buffer.length > 0) await flush(buffer, callback);
            else callback();
        }
    });
}

async function migrate(csvPath) {
    console.log(`\nMigrating: ${csvPath} | Batch: ${BATCH_SIZE} | Retries: ${MAX_RETRIES}\n`);
    await pipe(
        fs.createReadStream(csvPath, { encoding: 'utf8' }),
        parse({ columns: true, skip_empty_lines: true, trim: true }),
        createBatchCollector(BATCH_SIZE, upsertBatch)
    );
    dlqStream.end();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`\n\n✅ Done in ${elapsed}s — ${processed.toLocaleString()} rows | ${failed} DLQ`);
    if (failed > 0) console.log(`   DLQ: ./failed-rows.jsonl`);
}

migrate(process.argv[2] || './orders.csv').catch(err => {
    console.error('\n✗ Fatal:', err.message);
    process.exit(1);
});
```

### Key Design Decisions

**Idempotency (`ON CONFLICT DO UPDATE`):** The pipeline can be safely restarted. If it crashes at row 47,000, rows 1–47,000 are simply updated to the same values when you re-run. No duplicates.

**Dead-Letter Queue:** Batches that exhaust all retries are written to `failed-rows.jsonl`. After the migration, inspect the file, fix the root cause, and re-run the script pointing at the DLQ file.

**Backpressure:** The `callback()` in the Transform stream is not called until `upsertBatch` resolves. Node.js automatically pauses the readable stream when the database is under pressure — no manual `pause()/resume()` needed.

**`stream.pipeline`:** Using the promisified `pipeline` instead of manually chaining `.pipe()` ensures that if any stream in the chain errors, all other streams are automatically destroyed and file handles are released.

```bash
# Run migration
node migrate.js ./exports/magento-orders.csv

# Replay only failed rows
node migrate.js ./failed-rows.jsonl
```

For the full architectural context of where this extracted data lands in a microservice ecosystem, see [Why You Should Migrate from Magento to Microservices](/posts/why-migrate-magento-to-microservices/) and the [Zero-Downtime Migration Blueprint](/posts/moving-from-magento-to-microservices/).

{{< author-cta >}}
