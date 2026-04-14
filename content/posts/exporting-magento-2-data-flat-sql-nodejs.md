---
title: "Exporting Magento 2 Orders: Bypassing the EAV Model with Clean SQL & Node.js"
date: "2024-03-09T03:38:22+00:00"
draft: false
tags: ["Magento", "SQL", "Node.js", "Data Migration"]
description: "A quick technical snippet for flattening Magento 2's complex EAV order database into a clean CSV utilizing robust SQL joins and Node.js parsing."
categories: ["Engineering"]
---

When migrating away from Magento 2 to a microservices architecture, one of the biggest hurdles is extracting data from its heavily fragmented Entity-Attribute-Value (EAV) database model. 

Using Magento's admin-facing export utilities often falls short, especially when dealing with custom product types, bundled items, or deeply nested order relationships extending into payments and shipments. The most deterministic way to extract clean, migratable data is by querying the database directly.

Below is a robust SQL snippet that flattens core `sales_order` tables, directly mapping shipments and payments to a unified dataset. This is highly useful for generating `.csv` manifests of legacy orders to seed your new databases.

## The SQL Export Script

```sql
SELECT 
    sales_order.entity_id AS "Order ID",
    sales_order_payment.entity_id AS "Payment ID",
    sales_shipment.entity_id AS "Shipment ID",
    sales_order.status AS "Order Status",
    sales_order.grand_total AS "Total"
FROM sales_order
LEFT JOIN sales_order_payment 
    ON (sales_order.entity_id = sales_order_payment.parent_id)
LEFT JOIN sales_shipment 
    ON (sales_order.entity_id = sales_shipment.entity_id)
-- Filter out test data or specific timelines here
ORDER BY sales_order.created_at ASC;
```

*Note: For the product catalog, you should switch Magento to use a 'Flat Catalog' in the admin panel prior to running data extraction, as this pre-caches the insane EAV relationships into a single queryable table.*

## Ingesting the Export via Node.js

Once exported to a `.csv` file, the legacy data needs to be structured and inserted into your new microservices (e.g., PostgreSQL or MongoDB). A robust and highly readable way to stream and parse this CSV is using Node.js and the `csv-parse` package.

Using a stream, rather than loading the whole CSV into RAM, prevents Out-of-Memory (OOM) errors when processing gigabytes of historical order data. We also structure it to batch database inserts, protecting your connection pool.

```javascript
const db = require('./database');
const fs = require('fs');
const parse = require('csv-parse');

const BATCH_SIZE = 500;
let batch = [];

// Initialize parser with column mapping
const parser = parse({ columns: true }, async function (err, orders) {
    if (err) {
        console.error("CSV Parsing Error:", err);
        return;
    }

    // Process the orders iteratively
    for (const order of orders) {
        batch.push(order);
        
        // Save in batches to prevent hammering the new database connection pool
        if (batch.length >= BATCH_SIZE) {
            await db.saveBatch(batch);
            batch = []; 
        }
    }
    
    // Process remaining
    if (batch.length > 0) {
        await db.saveBatch(batch);
    }
    console.log("Migration complete.");
});

// Stream the massive CSV natively avoiding Memory Limits
fs.createReadStream(__dirname + '/orders.csv').pipe(parser);
```

By maintaining total control over the SQL queries and managing the ingestion stream programmatically, you can confidently scrub, normalize, and shape legacy Magento data exactly to your new Domain Driven boundaries.
