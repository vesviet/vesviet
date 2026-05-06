---
title: "Part 1 — Order Fulfillment: From Buy Click to Delivery"
date: 2026-05-06T20:30:00+07:00
draft: false
description: "Understand the lifecycle of an e-commerce order — from the moment a customer clicks buy, through the OMS, to pick-pack-ship and final delivery."
weight: 2
---

## The Order Lifecycle

Every order on Amazon, eBay, or Shopify goes through **8 stages** from the moment the customer clicks "Buy" until they receive the package:

```text
┌─────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐
│ 1. ORDER │──►│ 2. PAYMENT│──►│ 3. FRAUD  │──►│ 4. ALLOC │
│ CREATED  │   │ AUTH     │   │ CHECK     │   │ ENGINE   │
└─────────┘   └──────────┘   └───────────┘   └────┬─────┘
                                                    │
┌─────────┐   ┌──────────┐   ┌───────────┐   ┌────▼─────┐
│ 8. DELI- │◄──│ 7. IN    │◄──│ 6. PACKED │◄──│ 5. PICK  │
│ VERED    │   │ TRANSIT  │   │ & LABELED │   │ & PACK   │
└─────────┘   └──────────┘   └───────────┘   └──────────┘
```

### Stage 1: Order Created — Intake

```text
Customer clicks "Buy Now"
  │
  ▼
Validate:
  ✓ Are products in stock? (preliminary stock check)
  ✓ Is the shipping address valid?
  ✓ Is the payment method valid?
  ✓ Applied promo codes correctly?
  │
  ▼
Create Order record in DB:
  order_id: "ORD-2026-05-06-001"
  status: PENDING
  items: [
    {sku: "WATER-5L", qty: 2, capacity: 4},  -- 2 cases of 5L water, capacity = 4
    {sku: "PHONE-X", qty: 1, capacity: 1},    -- 1 phone, capacity = 1
  ]
  total_capacity: 5
  customer_location: {lat: 40.71, lng: -74.00}
  delivery_sla: "SAME_DAY"
```

### Stage 2: Payment Authorization

The system does not charge the money immediately. It only **authorizes** (places a hold on) the funds to ensure the customer has sufficient balance. The money is only captured (actually deducted) after the item ships.

```text
Flow:
  Order Service → Payment Gateway → Bank
  
  Authorization Request: "Hold $50.00 from card XXXX-1234"
  Bank Response: "AUTH_CODE: A12345, HOLD: $50.00"
  
  Order status: PENDING → AUTHORIZED
```

### Stage 3: Fraud Check

```text
Fraud Score = f(
  customer_history,       -- New or returning customer?
  order_value,            -- Unusually high value?
  shipping_address,       -- Blacklisted address?
  payment_method,         -- Brand new card?
  device_fingerprint,     -- Flagged device?
  velocity_check          -- How many orders placed in the last hour?
)

if fraud_score > 0.8:  → REJECT (auto-cancel)
if fraud_score > 0.5:  → MANUAL_REVIEW (flag for human review)
if fraud_score < 0.5:  → APPROVED (continue processing)
```

### Stage 4: Allocation Engine — The Fulfillment Brain

**This is the most critical stage** — deciding which warehouse ships the items and which driver delivers them. Parts 3 and 6 will dive deep into this phase.

```text
Input:
  - Order: {items, total_capacity: 5, customer_location, sla: SAME_DAY}
  - Warehouses: [{id: "WH-NY", inventory: {...}, location: {...}}]
  - Drivers: [
      {id: "D1", current_load: 3, max_capacity: 10, min_capacity: 2, location: ...},
      {id: "D2", current_load: 8, max_capacity: 10, min_capacity: 2, location: ...},
    ]

Decision:
  Warehouse: WH-NY (has stock, closest to customer)
  Driver: D1 (current_load 3 + order_capacity 5 = 8 ≤ max 10) ✓
  D2: (current_load 8 + order_capacity 5 = 13 > max 10) ✗

Output:
  Fulfillment Plan:
    warehouse: WH-NY
    driver: D1
    estimated_pickup: 14:00
    estimated_delivery: 15:30
```

#### Pricing-Driven Allocation Architecture

The decision of *when* to run the allocation algorithm depends entirely on the Board of Directors' (BOD) pricing strategy for **Multi-Depot** fulfillment. When an item has different costs or retail prices at different warehouses, the system architecture branches into 3 main models:

1. **Pre-Checkout Allocation (Hyperlocal Model):**
   - *Examples:* Instacart, GrabMart, local grocery delivery.
   - *How it works:* The system forces the user to enter a delivery address immediately upon opening the app. Using geo-fencing, the system "locks" the user's session to the nearest specific warehouse. The prices and inventory shown belong exclusively to that warehouse.
   - *Characteristics:* Warehouse allocation happens **before** checkout. The system cannot dynamically change the warehouse after the order is placed.

2. **User-Driven Allocation (Buy Box Marketplace Model):**
   - *Examples:* Amazon Buy Box, Shopee.
   - *How it works:* The system acknowledges multiple warehouses/sellers. The algorithm calculates the real-time `(Item Price + Estimated Shipping)` for each warehouse. The warehouse offering the lowest total cost to the customer "wins" the default "Add to Cart" button. The customer ultimately decides who to buy from.
   - *Characteristics:* Shifts the allocation decision power to the customer.

3. **Post-Checkout Cost Absorption (Omnichannel Model):**
   - *Examples:* Multi-channel retail chains.
   - *How it works:* Customers see a single standard price on the website. After checkout, an Allocation Engine (like OR-Tools) runs in the background to calculate: *Is it more profitable to ship from a further warehouse (higher shipping cost) with very low item cost, or a closer warehouse (low shipping) with high item cost?*
   - *Characteristics:* The platform automatically absorbs the shipping loss or pockets the cost difference to optimize the overall Profit Margin. The customer experience remains seamless and uniform.

### Stage 5: Pick & Pack

At the warehouse, the **Warehouse Management System (WMS)** coordinates the physical labor:

```text
Pick List for Order ORD-2026-05-06-001:
  ┌─────────────────────────────────────────────┐
  │  Aisle B, Shelf 3, Bin 12: WATER-5L × 2    │
  │  Aisle D, Shelf 1, Bin 05: PHONE-X × 1     │
  └─────────────────────────────────────────────┘

Pick Path Optimization:
  Instead of walking randomly → WMS calculates the shortest path across all bins
  (A variation of the Travelling Salesman Problem inside the warehouse)

Pack:
  - Select the right box size (avoid oversized boxes to save shipping volume)
  - Print shipping label with barcode + address
  - Weigh the package → verify items are correct
  - Scan → update status: PACKED
```

### Stages 6-7: Handoff → In Transit

```text
Driver D1 arrives at warehouse WH-NY:
  1. Scans package barcode → Confirms receipt
  2. Driver app displays optimal routing (if multiple packages)
  3. Order status: PACKED → IN_TRANSIT
  4. Customer receives notification: "Your order is out for delivery!"
  5. Driver's GPS begins streaming → Customer tracks on map
```

### Stage 8: Delivered

```text
Driver arrives at destination:
  1. Customer confirms receipt (signature / OTP / photo proof)
  2. Order status: IN_TRANSIT → DELIVERED
  3. Payment capture: $50.00 is officially deducted from the card
  4. Inventory: SKU physical counts are permanently decremented
  5. Driver capacity: 5 capacity units are freed up
```

---

## Order Management System (OMS) — The Central Coordinator

The OMS is the "brain" that manages the entire order lifecycle. In a microservices architecture, the OMS is often split into several sub-services:

```text
┌──────────────────────────────────────────────────┐
│                     OMS                           │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Order Service │  │ Inventory    │              │
│  │ (CRUD orders) │  │ Service      │              │
│  └──────┬───────┘  │ (Stock mgmt) │              │
│         │          └──────┬───────┘              │
│         │                 │                       │
│  ┌──────▼─────────────────▼──────┐               │
│  │   Allocation Engine           │               │
│  │   (Warehouse + Driver routing)│               │
│  └──────────────┬────────────────┘               │
│                 │                                 │
│  ┌──────────────▼────────────────┐               │
│  │   Fulfillment Service         │               │
│  │   (Pick, Pack, Ship tracking) │               │
│  └──────────────┬────────────────┘               │
│                 │                                 │
│  ┌──────────────▼────────────────┐               │
│  │   Delivery Service            │               │
│  │   (Driver dispatch, tracking) │               │
│  └───────────────────────────────┘               │
└──────────────────────────────────────────────────┘
```

---

## Event-Driven Architecture

Each stage emits **domain events** via a message broker like Kafka:

| Event | Producer | Consumers |
|---|---|---|
| `order.created` | Order Service | Inventory (reserve stock), Fraud Check |
| `order.authorized` | Payment Service | Allocation Engine |
| `order.allocated` | Allocation Engine | WMS (pick list generation), Driver Service |
| `order.picked` | WMS | Packing Station |
| `order.packed` | WMS | Driver Dispatch |
| `order.in_transit` | Delivery Service | Customer Notification, Tracking |
| `order.delivered` | Delivery Service | Payment (capture), Inventory (commit), Analytics |

> *Next, we will explore real-time inventory management — the foundational data required for any allocation decision. Read [Part 2 — Inventory Management: Real-time Stock Sync](/series/ecommerce-order-allocation/part-2-inventory-realtime/).*
