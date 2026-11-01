---
title: "Part 5: EAV Schema Migration — Magento's Biggest Trap"
date: 2026-05-06T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "Extracting Magento's EAV schema: int-to-UUID identifier mapping, no hardcoded attribute IDs, dynamic pivot SQL, and battle-tested query templates."
categories: ["Series", "Software Engineering", "Database Architecture"]
tags: ["PostgreSQL", "EAV Migration", "Magento", "Database", "Golang"]
series: ["composable-commerce-migration"]
weight: 6
slug: "part-5-eav-schema-migration"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-5-eav-schema-migration/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 5: Migrating Magento EAV Schema to Clean Relational PostgreSQL"
  relative: false
keywords: ["magento eav migration", "eav to jsonb postgresql", "gin indexing postgresql", "database decomposition ecommerce"]
mermaid: true
---

[← Previous Chapter: Part 4: gRPC Internal + REST Gateway](/series/composable-commerce-migration/part-4-grpc-rest-gateway/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 6: Phase 1 — Strangler Fig Read-Only →](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)

---

> **Answer-first:** Escaping Magento's complex Entity-Attribute-Value (EAV) structure requires extracting data through dynamic pivot SQL statements, mapping integer IDs to UUIDs, and restructuring into a normalized relational schema in PostgreSQL to optimize query performance.

---

The EAV schema is the reason most Magento migration projects fail.

From the outside, it looks easy to handle: product data is shredded across `catalog_product_entity`, `catalog_product_entity_varchar`, `catalog_product_entity_int`, `catalog_product_entity_decimal`, `catalog_product_entity_datetime`, and `catalog_product_entity_text`. Six tables — write a simple ETL job, get it done over a weekend.

But then you discover that `attribute_id = 75` means "product name" in *your* database, yet means "color" in the staging database. Every attribute ID is generated automatically at install time and is completely different between environments. Any ETL script that dares to hardcode these attribute IDs will instantly produce a pile of corrupted data the moment it runs against production.

**Answer-first:** Migrating Magento's complex EAV architecture to a flat relational database (PostgreSQL) cannot be done with a naive 1-1 approach because, as of 2026, Magento still has no native PostgreSQL support. To migrate EAV successfully to a microservices system, follow these steps: (1) build a `magento_id_map` table to translate Magento's integer IDs into UUIDs, (2) use `eav_attribute.attribute_code` (never `attribute_id`) as the stable lookup key, (3) apply dynamic SQL pivot techniques to flatten/normalize the structure into JSONB data or flat columns at runtime instead of hardcoding, and (4) run the data extraction through three stages: initial full load via an ETL pipeline → incremental delta sync → cutover validation.

## 1. The EAV Data Model

A Magento product with the SKU `MSH-BLK-L` (Men's Black Shirt, size L) is stored like this:

**`catalog_product_entity`** (the core entity table):
```
entity_id | sku           | entity_type_id | attribute_set_id
2841      | MSH-BLK-L     | 4              | 9
```

**`catalog_product_entity_varchar`** (string-typed attributes):
```
entity_id | attribute_id | store_id | value
2841      | 75           | 0        | Men's Black Shirt
2841      | 76           | 0        | MSH-BLK-L
2841      | 97           | 0        | Men's Shirts
```

**`catalog_product_entity_int`** (integer-typed attributes):
```
entity_id | attribute_id | store_id | value
2841      | 80           | 0        | 8                ← status: 1=Enabled, 2=Disabled
2841      | 81           | 0        | 4                ← visibility
2841      | 134          | 0        | 2                ← tax_class_id
```

**`catalog_product_entity_decimal`** (decimal-typed attributes):
```
entity_id | attribute_id | store_id | value
2841      | 77           | 0        | 299000.0000     ← price
2841      | 78           | 0        | 0.0000          ← special_price
```

Here is the problem: `attribute_id = 75` means "name" in this database. But in your staging database (built from a fresh Magento install), `attribute_id = 75` could easily mean "color". **Attribute IDs are instance-specific — they are generated via `AUTO_INCREMENT` during the Magento installation process**.

## 2. The Trap: Hardcoded Attribute IDs

This is the naive approach, copied from countless Stack Overflow answers:

```sql
-- ❌ DEAD WRONG: hardcoding attribute IDs will blow up production
SELECT
    e.entity_id,
    e.sku,
    v_name.value AS name,
    d_price.value AS price
FROM catalog_product_entity e
LEFT JOIN catalog_product_entity_varchar v_name
    ON v_name.entity_id = e.entity_id AND v_name.attribute_id = 75  -- hardcoded "name"!
LEFT JOIN catalog_product_entity_decimal d_price
    ON d_price.entity_id = e.entity_id AND d_price.attribute_id = 77  -- hardcoded "price"!
WHERE v_name.store_id = 0
```

This query will return perfectly correct results in your dev environment, will possibly return wrong results in staging, and will silently return completely wrong data in production if anyone has ever re-run Magento's re-index or added attributes in a different order.

## 3. The Fix: Look Up by Attribute Code

```sql
-- ✅ CORRECT: resolve attribute IDs dynamically via the eav_attribute table
SELECT attr.attribute_id
FROM eav_attribute attr
JOIN eav_entity_type et ON et.entity_type_id = attr.entity_type_id
WHERE et.entity_type_code = 'catalog_product'
  AND attr.attribute_code = 'name';      -- 'name' never changes, while 'attribute_id' does
```

The `attribute_code` column is the only thing that stays stable across every instance. `name`, `price`, `sku`, `status`, `visibility` — these codes are defined in Magento's core and never change between installations. **Always resolve attribute IDs from the `eav_attribute` table at runtime. Never, ever hardcode them.**

## 4. The magento_id_map Table: Mapping Integers → UUIDs

Every record in Magento uses MySQL's auto-increment `AUTO_INCREMENT` integer primary keys. Every record in the new microservices platform uses UUIDs. The migration must begin by creating a cross-reference table as the very first step:

```sql
-- Migration step 1: create the identity map
CREATE TABLE magento_id_map (
    id              BIGSERIAL PRIMARY KEY,
    entity_type     VARCHAR(64) NOT NULL,    -- 'product', 'customer', 'order'
    magento_id      BIGINT NOT NULL,         -- Magento's original AUTO_INCREMENT ID
    platform_uuid   UUID NOT NULL DEFAULT gen_random_uuid(),
    migrated_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_type, magento_id)
);

-- Seed all products
INSERT INTO magento_id_map (entity_type, magento_id)
SELECT 'product', entity_id
FROM catalog_product_entity
ON CONFLICT (entity_type, magento_id) DO NOTHING;

-- Verification: ensure every product has been assigned a UUID
SELECT COUNT(*) AS total_products,
       COUNT(platform_uuid) AS mapped_products
FROM magento_id_map
WHERE entity_type = 'product';
-- Expected result: total_products = mapped_products
```

Once this step is complete, the Debezium CDC sync service (described in [Part 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)) will use this `magento_id_map` table to translate every `entity_id` appearing in CDC events into its corresponding UUID before publishing to Dapr PubSub.

## 5. Dynamic SQL Pivot: Reading Data at Runtime

Once attribute IDs are resolved dynamically, the extraction query becomes a pivot that runs cleanly against any Magento instance:

```sql
-- EAV extraction with dynamic attribute ID resolution
WITH attr_ids AS (
    -- Resolve all attribute codes to the attribute IDs of THIS Magento instance
    SELECT
        attribute_id,
        attribute_code,
        backend_type                -- 'varchar', 'int', 'decimal', 'datetime', 'text'
    FROM eav_attribute
    WHERE entity_type_id = (
        SELECT entity_type_id FROM eav_entity_type
        WHERE entity_type_code = 'catalog_product'
    )
    AND attribute_code IN ('name', 'price', 'special_price', 'status',
                           'visibility', 'description', 'short_description',
                           'tax_class_id', 'weight', 'manufacturer')
)
SELECT
    e.entity_id                                             AS magento_id,
    idmap.platform_uuid                                     AS id,
    e.sku,
    e.attribute_set_id,
    MAX(CASE WHEN a.attribute_code = 'name'
        THEN v.value END)                                   AS name,
    MAX(CASE WHEN a.attribute_code = 'description'
        THEN t.value END)                                   AS description,
    MAX(CASE WHEN a.attribute_code = 'status'
        THEN i.value END)                                   AS status,
    MAX(CASE WHEN a.attribute_code = 'price'
        THEN d.value END)                                   AS price,
    MAX(CASE WHEN a.attribute_code = 'special_price'
        THEN d2.value END)                                  AS special_price,
    MAX(CASE WHEN a.attribute_code = 'weight'
        THEN d3.value END)                                  AS weight,
    e.created_at,
    e.updated_at

FROM catalog_product_entity e
JOIN magento_id_map idmap
    ON idmap.entity_type = 'product' AND idmap.magento_id = e.entity_id

-- Varchar attributes (name, manufacturer, etc.)
LEFT JOIN catalog_product_entity_varchar v
    ON v.entity_id = e.entity_id AND v.store_id = 0
    AND v.attribute_id IN (SELECT attribute_id FROM attr_ids WHERE backend_type = 'varchar')
LEFT JOIN attr_ids a_v ON a_v.attribute_id = v.attribute_id

-- Text attributes (description, short_description)
LEFT JOIN catalog_product_entity_text t
    ON t.entity_id = e.entity_id AND t.store_id = 0
    AND t.attribute_id IN (SELECT attribute_id FROM attr_ids WHERE backend_type = 'text')
LEFT JOIN attr_ids a_t ON a_t.attribute_id = t.attribute_id AND a_t = a_v

-- Integer attributes (status, visibility, tax_class_id)
LEFT JOIN catalog_product_entity_int i
    ON i.entity_id = e.entity_id AND i.store_id = 0
    AND i.attribute_id IN (SELECT attribute_id FROM attr_ids WHERE backend_type = 'int')

-- Decimal attributes (price, special_price, weight)
LEFT JOIN catalog_product_entity_decimal d
    ON d.entity_id = e.entity_id AND d.store_id = 0
    AND d.attribute_id = (SELECT attribute_id FROM attr_ids WHERE attribute_code = 'price')
LEFT JOIN catalog_product_entity_decimal d2
    ON d2.entity_id = e.entity_id AND d2.store_id = 0
    AND d2.attribute_id = (SELECT attribute_id FROM attr_ids WHERE attribute_code = 'special_price')
LEFT JOIN catalog_product_entity_decimal d3
    ON d3.entity_id = e.entity_id AND d3.store_id = 0
    AND d3.attribute_id = (SELECT attribute_id FROM attr_ids WHERE attribute_code = 'weight')

GROUP BY e.entity_id, e.sku, e.attribute_set_id, idmap.platform_uuid, e.created_at, e.updated_at
ORDER BY e.entity_id;
```

This is a production-safe version of the query. The `WITH attr_ids AS (...)` CTE section runs exactly once at the start of the query to resolve all attribute IDs from the database's current state — absolutely no hardcoding, and no instance-specific constants anywhere.

## 6. The Go Transformation Layer

After being extracted via SQL, the data must go through a transformation step before being loaded into the Catalog Service's PostgreSQL:

```go
// migration/transformer/product_transformer.go

type MagentoProduct struct {
    MagentoID   int64
    UUID        string
    SKU         string
    Name        string
    Description string
    Status      int   // 1=Enabled, 2=Disabled
    Price       float64
    SpecialPrice *float64
    Weight      float64
    CreatedAt   time.Time
    UpdatedAt   time.Time
}

func TransformProduct(mp *MagentoProduct) *catalog.Product {
    p := &catalog.Product{
        ID:          mp.UUID,
        SKU:         mp.SKU,
        Name:        mp.Name,
        Description: mp.Description,
        Status:      transformStatus(mp.Status),
        // Convert the float64 price to the Money type (never let a float leak through the API layer)
        Price: money.FromFloat("VND", mp.Price),
        Weight: mp.Weight,
        CreatedAt: mp.CreatedAt,
        UpdatedAt: mp.UpdatedAt,
    }

    if mp.SpecialPrice != nil {
        p.SpecialPrice = money.FromFloat("VND", *mp.SpecialPrice)
    }

    return p
}

func transformStatus(magentoStatus int) catalog.ProductStatus {
    switch magentoStatus {
    case 1: return catalog.ProductStatus_ENABLED
    case 2: return catalog.ProductStatus_DISABLED
    default: return catalog.ProductStatus_UNSPECIFIED
    }
}
```

## 7. Customer EAV: Same Song, Second Verse

Customer data in Magento also uses EAV (the `customer_entity` table plus type-suffixed tables). The extraction follows exactly the same pattern as above:

```sql
-- Customer extraction with dynamic attribute resolution
WITH customer_attrs AS (
    SELECT attribute_id, attribute_code, backend_type
    FROM eav_attribute
    WHERE entity_type_id = (
        SELECT entity_type_id FROM eav_entity_type
        WHERE entity_type_code = 'customer'
    )
    AND attribute_code IN ('firstname', 'lastname', 'dob', 'gender', 'taxvat')
)
SELECT
    ce.entity_id                    AS magento_id,
    idmap.platform_uuid             AS id,
    ce.email,
    ce.group_id                     AS customer_group,
    ce.is_active,
    ce.created_at,
    MAX(CASE WHEN ca.attribute_code = 'firstname'
        THEN v.value END)           AS first_name,
    MAX(CASE WHEN ca.attribute_code = 'lastname'
        THEN v.value END)           AS last_name
FROM customer_entity ce
JOIN magento_id_map idmap
    ON idmap.entity_type = 'customer' AND idmap.magento_id = ce.entity_id
LEFT JOIN customer_entity_varchar v
    ON v.entity_id = ce.entity_id
    AND v.attribute_id IN (SELECT attribute_id FROM customer_attrs WHERE backend_type = 'varchar')
JOIN customer_attrs ca ON ca.attribute_id = v.attribute_id
GROUP BY ce.entity_id, ce.email, ce.group_id, ce.is_active, ce.created_at, idmap.platform_uuid;
```

## 8. Incremental Delta Sync

After the initial full load, the CDC pipeline (Debezium, described in [Part 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)) takes over the job of syncing incremental changes. However, during the window before Debezium is deployed, a polling-based delta sync process fills the gap:

```sql
-- Delta sync: fetch products changed since the last extraction
SELECT e.entity_id
FROM catalog_product_entity e
WHERE e.updated_at > :last_sync_timestamp
ORDER BY e.updated_at ASC
LIMIT 1000;
```

This is purely a **fallback** mechanism — it is completely blind to DELETEs and highly vulnerable to clock skew between servers. As soon as Debezium goes live (the Phase 1 milestone), this polling-based sync is switched off immediately.

## 9. Validation: The Final Gate Before Extraction Is Complete

```bash
#!/bin/bash
# validate-product-extraction.sh

MAGENTO_COUNT=$(mysql -h $MAGENTO_DB -e "
    SELECT COUNT(*) FROM catalog_product_entity
    WHERE status = 1  -- Only count Enabled (sellable) products
" | tail -1)

PLATFORM_COUNT=$(psql $PLATFORM_DB -t -c "
    SELECT COUNT(*) FROM products WHERE status = 'ENABLED'
")

echo "Enabled products on Magento: $MAGENTO_COUNT"
echo "Products on the new platform: $PLATFORM_COUNT"

# These two numbers must match exactly before we are allowed to proceed to Phase 1
if [ "$MAGENTO_COUNT" -ne "$PLATFORM_COUNT" ]; then
    echo "❌ Count mismatch — the extraction is incomplete"
    exit 1
fi

# Run sampling tests: spot-check 100 products
psql $PLATFORM_DB -c "
    SELECT p.sku, p.name, p.price
    FROM products p
    ORDER BY RANDOM()
    LIMIT 100
" > /tmp/platform_sample.csv

echo "✅ Counts match. Please review the sample file at /tmp/platform_sample.csv"
```

## Key Takeaways

1. **Never hardcode `attribute_id`** — always resolve it via `eav_attribute.attribute_code`
2. **Build the `magento_id_map` table first** — every subsequent migration step depends on this UUID cross-reference table
3. **Use dynamic SQL pivot techniques** — the CTE approach guarantees the query runs correctly against every Magento instance regardless of install order
4. **Validate counts before entering Phase 1** — even the smallest mismatch between the two counts is enough proof that your extraction has holes
5. **Price is a decimal in MySQL but must be Money in proto** — convert explicitly, never let a float slip through the API layer

EAV extraction is the most labor-intensive stage of the entire migration. But once the `magento_id_map` table is fully populated and the dynamic pivot reports the correct count, you are officially ready to enter the real migration phases. [Part 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) shows how Debezium turns incremental syncing into a continuous, highly reliable stream — by throwing out the polling-based delta sync in favor of CDC tapped directly into the binlog.

## Frequently Asked Questions (FAQ)

### Why can't I just use Magento's built-in CSV import/export instead of scraping SQL directly?

Magento's CSV import/export feature refuses to export attribute relationships, and it certainly won't produce the `magento_id_map` cross-reference table you critically need. A CSV export only gives you flat rows per product — meaning all the EAV structure is thrown away — and a vanilla Magento without extensions is capped at exactly 5,000 products per export. With more than 10,000 SKUs, querying MySQL directly with SQL is the only path that can handle this volume without modifying the code.

*2026 architecture note (E-E-A-T context): Magento/Adobe Commerce has no native PostgreSQL compatibility. Do not attempt to run the Magento core on PostgreSQL with community proof-of-concept packages. Instead, keep MySQL/MariaDB for Magento and use these SQL extraction/ETL scripts to sync and normalize the long, skinny EAV schema into a high-performance PostgreSQL schema for the target microservices system.*

### Do I have to keep the magento_id_map table alive forever?

Yes — until the Phase 3 cutover is complete. The CDC sync pipeline (Part 6), the dual-write adapter (Part 7), and the conflict resolver (Part 7) all depend on the `magento_id_map` table to translate Magento's integer IDs into UUIDs every time they process an event. Only once Phase 3 is finished and Magento is officially decommissioned is this table allowed to be archived (never dropped — it must be kept as an audit trail).

### What happens if two Magento installations use the same `attribute_code` with completely different semantics?

This happens when custom attributes created by lazy third-party extensions use meaningless code names like `custom_attribute_1`. In that situation, also check the `eav_attribute.frontend_label` and `eav_attribute.source_model` columns to disambiguate. Make sure you document all of these ambiguous attributes in a comment field inside your `magento_id_map` table before pressing the extraction button — cleaning up this mess after the extraction is finished costs a billion times more.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full table of contents for the complete architectural context.*

*Need help assessing the risks of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 4: gRPC Internal + REST Gateway](/series/composable-commerce-migration/part-4-grpc-rest-gateway/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 6: Phase 1 — Strangler Fig Read-Only →](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)
