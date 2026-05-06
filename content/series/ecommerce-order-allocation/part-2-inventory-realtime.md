---
title: "Part 2 — Inventory Management: Real-time Stock Sync"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "A real-time inventory system is the foundation of all allocation decisions. Learn how to handle overselling, stock reservation, and eventual consistency in distributed inventory."
weight: 3
---

## Why is Inventory a Hard Problem?

Imagine: A warehouse has exactly **1 iPhone left in stock**. At 14:00:00.000, two customers in different cities click "Buy" simultaneously. If the system isn't designed correctly, both orders are confirmed → **overselling** → one customer's order will inevitably be canceled later → terrible user experience.

This isn't a theoretical issue; it happens daily across e-commerce platforms.

---

## Inventory Model: The 4 Types of Quantities

```text
For SKU: "IPHONE-16-256GB" at Warehouse NY:

┌──────────────────────────────────────────────────────────┐
│  Physical Stock (What's actually on shelves): 100        │
│  ├── Reserved (Held for pending orders):      -15        │
│  ├── Safety Stock (Do not sell buffer):       -5         │
│  │                                                       │
│  └── Available to Sell (ATP):                  80        │
│      (= Physical - Reserved - Safety)                    │
│                                                          │
│  On-Order (Inbound shipments from suppliers):  50        │
│  Available to Promise (Future availability):  130        │
│  (= ATP + On-Order)                                      │
└──────────────────────────────────────────────────────────┘
```

| Type | Meaning | Who uses it? |
|---|---|---|
| **Physical Stock** | Actual physical items in the warehouse | Warehouse team |
| **Reserved** | Items "held" for orders currently being processed but not yet shipped | Allocation Engine |
| **Safety Stock** | Minimum buffer—never sold (accounts for damages, shrinkage) | Inventory Manager |
| **ATP (Available to Sell)** | The actual number of items that can be sold immediately | Storefront (shown to customers) |

---

## Stock Reservation — Preventing Overselling

### The Reservation Flow

```text
Customer clicks "Buy":

1. Order Service → Inventory Service: "Reserve 1 IPHONE-16 at WH NY"

2. Inventory Service:
   BEGIN TRANSACTION
     SELECT atp FROM inventory
       WHERE sku = 'IPHONE-16' AND warehouse = 'NY'
       FOR UPDATE;  -- Pessimistic lock

     IF atp >= 1:
       UPDATE inventory SET reserved = reserved + 1 WHERE ...
       INSERT INTO reservations (order_id, sku, qty, expires_at)
         VALUES ('ORD-001', 'IPHONE-16', 1, NOW() + INTERVAL '30 minutes');
       RETURN: RESERVED
     ELSE:
       RETURN: OUT_OF_STOCK
   COMMIT

3. If RESERVED: Proceed to payment checkout
   If OUT_OF_STOCK: Notify customer item is unavailable
```

### Reservation Expiry — Auto-Release

If the customer holds the item in their cart but abandons checkout for 30 minutes, the reservation expires automatically:

```sql
-- Cron job running every minute
UPDATE inventory
SET reserved = reserved - r.qty
FROM reservations r
WHERE r.sku = inventory.sku
  AND r.warehouse = inventory.warehouse
  AND r.status = 'ACTIVE'
  AND r.expires_at < NOW();

UPDATE reservations
SET status = 'EXPIRED'
WHERE status = 'ACTIVE'
  AND expires_at < NOW();
```

---

## Database Schema for Inventory

```sql
-- Main inventory table
CREATE TABLE inventory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(50) NOT NULL,
    warehouse_id    VARCHAR(20) NOT NULL,
    physical_qty    INT NOT NULL DEFAULT 0,
    reserved_qty    INT NOT NULL DEFAULT 0,
    safety_stock    INT NOT NULL DEFAULT 0,

    -- Available to Sell = physical - reserved - safety
    -- Computed column or calculated at runtime
    
    version         BIGINT NOT NULL DEFAULT 1,  -- Optimistic locking
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sku, warehouse_id),
    CONSTRAINT positive_physical CHECK (physical_qty >= 0),
    CONSTRAINT positive_reserved CHECK (reserved_qty >= 0),
    CONSTRAINT no_oversell CHECK (physical_qty - reserved_qty - safety_stock >= 0)
);

-- Reservation table
CREATE TABLE stock_reservations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        VARCHAR(50) NOT NULL,
    sku             VARCHAR(50) NOT NULL,
    warehouse_id    VARCHAR(20) NOT NULL,
    quantity        INT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    -- 'ACTIVE', 'COMMITTED' (shipped), 'EXPIRED', 'CANCELLED'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    committed_at    TIMESTAMPTZ
);

CREATE INDEX idx_reservation_expiry ON stock_reservations(status, expires_at)
    WHERE status = 'ACTIVE';
```

---

## Eventual Consistency in Distributed Inventory

When a system has multiple warehouses and various microservices reading/writing inventory, using strong consistency (like two-phase commits) is too slow. The solution: **Eventual Consistency** via event-driven updates:

```text
Event-Driven Flow:

1. Order Service: "Order ORD-001 Confirmed"
   → Publishes event: order.confirmed {sku: IPHONE-16, qty: 1, warehouse: NY}

2. Inventory Service (Consumer):
   → Receives event → reservation status: ACTIVE → COMMITTED
   → physical_qty -= 1, reserved_qty -= 1

3. Warehouse Service (Consumer):
   → Receives event → Generates pick list for warehouse workers

4. Analytics Service (Consumer):
   → Receives event → Updates sales dashboard

Each service updates its state asynchronously, resulting in eventual consistency.
```

### Conflict Resolution: Optimistic Locking

```go
// Optimistic locking: check version before updating
func (r *InventoryRepo) Reserve(ctx context.Context, sku, warehouse string, qty int) error {
    for retries := 0; retries < 3; retries++ {
        inv, err := r.GetBySKU(ctx, sku, warehouse)
        if err != nil { return err }

        atp := inv.PhysicalQty - inv.ReservedQty - inv.SafetyStock
        if atp < qty {
            return ErrOutOfStock
        }

        // Update with version check
        result := r.db.Exec(`
            UPDATE inventory
            SET reserved_qty = reserved_qty + ?, version = version + 1
            WHERE sku = ? AND warehouse_id = ? AND version = ?`,
            qty, sku, warehouse, inv.Version)

        if result.RowsAffected == 1 {
            return nil // Success
        }
        // Version mismatch → someone else updated the record → retry
    }
    return ErrConcurrencyConflict
}
```

---

## Multi-Channel Inventory Sync

When selling across Amazon, Shopify, and a physical store simultaneously, sharing the same SKU pool creates race conditions:

```text
         ┌──────────┐
         │ Inventory │  ← Source of truth
         │ Service   │
         └─────┬─────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Amazon │ │ Shopify│ │Physical│
│ Channel│ │Channel │ │ Store  │
│ ATP: 80│ │ATP: 80 │ │ATP: 80 │
└────────┘ └────────┘ └────────┘

Problem: If Amazon sells 1 unit, Shopify and Physical Store ATPs must decrement immediately.
→ Solution: Event-driven sync OR Channel-specific allocation.

Channel Allocation Strategy:
  Amazon: max 40 units (50% quota)
  Shopify: max 24 units (30% quota)
  Physical: max 16 units (20% quota)
  → Each channel operates within its quota → No cross-channel overselling.
```

---

## Key Inventory Metrics

| Metric | Meaning | Target |
|---|---|---|
| **Stockout Rate** | % of time an SKU is out of stock | < 2% |
| **Oversell Rate** | % of orders canceled due to lack of stock | < 0.1% |
| **Inventory Turnover** | How many times inventory is sold/replaced per year | > 12 (monthly) |
| **Reservation Expiry Rate** | % of reservations that expire (cart abandonment) | < 15% |
| **ATP Accuracy** | Accuracy of the "Available to Sell" quantity | > 99.5% |

> *Next, we dive into the true brain of the system — the order allocation algorithms. Read [Part 3 — Allocation Algorithms: Assignment, Bin Packing & VRP](/series/ecommerce-order-allocation/part-3-allocation-algorithms/).*
