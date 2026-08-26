---
title: "Phần 2 — Inventory Management: Quản lý tồn kho thời gian thực"
slug: "part-2-inventory-realtime"
date: 2026-05-06T20:30:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
description: "Hệ thống tồn kho thời gian thực là nền tảng cho mọi quyết định phân bổ. Tìm hiểu cách xử lý overselling, stock reservation, và eventual consistency trong tồn kho lớn."
weight: 3
ShowToc: true
TocOpen: true
series:
  - "ecommerce-order-allocation"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-2-inventory-realtime/"
categories:
  - "Series"
  - "E-Commerce"
  - "Logistics & Supply Chain"
tags:
  - "Inventory"
  - "Realtime"
  - "Stock Reservation"
  - "Concurrency"
  - "E-Commerce"
cover:
  image: "/images/posts/default-post.png"
  alt: "Inventory Management: Quản lý tồn kho thời gian thực"
  relative: false
---

[← Chương trước: Phần 1 — Order Fulfillment](/series/ecommerce-order-allocation/part-1-order-fulfillment-fundamentals/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 3 — Thuật toán phân bổ →](/series/ecommerce-order-allocation/part-3-allocation-algorithms/)

---

> **Answer-first:** Quản lý tồn kho thời gian thực phân tách 4 trạng thái cốt lõi: Physical Stock, Reserved Stock, Safety Stock và ATP (Available to Promise). Bằng cách kết hợp Stock Reservation có thời hạn (TTL), Optimistic/Pessimistic Locking và kiến trúc Eventual Consistency, hệ thống ngăn chặn triệt để hiện tượng overselling trong các đợt flash sale tốc độ cao.

---

## Tại sao tồn kho là bài toán khó?

Tưởng tượng: kho còn **1 chiếc iPhone cuối cùng**. Lúc 14:00:00.000, hai khách hàng ở hai thành phố khác nhau cùng bấm "Mua" đồng thời. Nếu hệ thống không xử lý đúng, cả hai đều được xác nhận → **overselling** → một khách sẽ bị hủy đơn → trải nghiệm tệ, mất khách.

Đặc biệt trong môi trường sản xuất 2026, với sự phát triển của Livestream Shopping và Flash Sales tốc độ cao, cùng sự tích hợp IoT và AI dự báo nhu cầu đa kênh (Omnichannel), áp lực xử lý tồn kho thời gian thực càng trở nên khắc nghiệt. Việc từ bỏ mô hình đồng bộ batch (cuối ngày) để chuyển sang cập nhật stream tức thời không còn là lựa chọn mà là yêu cầu bắt buộc để giữ thị phần. Đội ngũ kho bãi cũng dần thay thế sức người bằng các xe tự hành (AMR) để theo kịp tốc độ của Allocation Engine.

---

## Mô hình tồn kho: 4 loại số lượng

```
Với SKU: "IPHONE-16-256GB" tại Kho TP.HCM:

┌──────────────────────────────────────────────────────────┐
│  Physical Stock (Tồn kho vật lý):        100             │
│  ├── Reserved (Đã giữ cho đơn chưa giao): -15           │
│  ├── Safety Stock (Dự phòng tối thiểu):   -5            │
│  │                                                        │
│  └── Available to Sell (ATP):             80             │
│      (= Physical - Reserved - Safety)                     │
│                                                           │
│  On-Order (Hàng đang nhập về):            50             │
│  Available to Promise (Tương lai):        130            │
│  (= ATP + On-Order)                                      │
└──────────────────────────────────────────────────────────┘
```

| Loại | Ý nghĩa | Ai dùng? |
|---|---|---|
| **Physical Stock** | Số hàng thực tế trong kho (đếm được) | Warehouse team |
| **Reserved** | Hàng đã "giữ chỗ" cho đơn hàng đang xử lý nhưng chưa xuất kho | Allocation Engine |
| **Safety Stock** | Dự phòng tối thiểu — không bao giờ bán (phòng sai sót, hàng lỗi) | Inventory Manager |
| **ATP (Available to Sell)** | Số hàng thực sự có thể bán ngay | Storefront (hiển thị cho khách) |

---

## Stock Reservation — Chống overselling

### Luồng Reserve Stock

```
Khách bấm "Mua":

1. Order Service → Inventory Service: "Reserve 1 IPHONE-16 tại kho HCM"

2. Inventory Service:
   BEGIN TRANSACTION
     SELECT atp FROM inventory
       WHERE sku = 'IPHONE-16' AND warehouse = 'HCM'
       FOR UPDATE;  -- Pessimistic lock

     IF atp >= 1:
       UPDATE inventory SET reserved = reserved + 1 WHERE ...
       INSERT INTO reservations (order_id, sku, qty, expires_at)
         VALUES ('ORD-001', 'IPHONE-16', 1, NOW() + INTERVAL '30 minutes');
       RETURN: RESERVED
     ELSE:
       RETURN: OUT_OF_STOCK
   COMMIT

3. Nếu RESERVED: tiếp tục thanh toán
   Nếu OUT_OF_STOCK: thông báo hết hàng
```

### Reservation Expiry — Tự hủy giữ chỗ

Nếu khách giữ hàng nhưng không thanh toán trong 30 phút, reservation tự động hết hạn:

```sql
-- Cron job chạy mỗi phút
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

## Database Schema cho Inventory

```sql
-- Bảng tồn kho chính
CREATE TABLE inventory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(50) NOT NULL,
    warehouse_id    VARCHAR(20) NOT NULL,
    physical_qty    INT NOT NULL DEFAULT 0,
    reserved_qty    INT NOT NULL DEFAULT 0,
    safety_stock    INT NOT NULL DEFAULT 0,

    -- Available to Sell = physical - reserved - safety
    -- Computed column hoặc tính runtime
    
    version         BIGINT NOT NULL DEFAULT 1,  -- Optimistic locking
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sku, warehouse_id),
    CONSTRAINT positive_physical CHECK (physical_qty >= 0),
    CONSTRAINT positive_reserved CHECK (reserved_qty >= 0),
    CONSTRAINT no_oversell CHECK (physical_qty - reserved_qty - safety_stock >= 0)
);

-- Bảng reservation (giữ chỗ)
CREATE TABLE stock_reservations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        VARCHAR(50) NOT NULL,
    sku             VARCHAR(50) NOT NULL,
    warehouse_id    VARCHAR(20) NOT NULL,
    quantity        INT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    -- 'ACTIVE', 'COMMITTED' (đã xuất kho), 'EXPIRED', 'CANCELLED'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    committed_at    TIMESTAMPTZ
);

CREATE INDEX idx_reservation_expiry ON stock_reservations(status, expires_at)
    WHERE status = 'ACTIVE';
```

---

## Eventual Consistency trong tồn kho phân tán

Khi hệ thống có nhiều kho và nhiều service cùng đọc/ghi tồn kho, không thể dùng strong consistency (quá chậm). Giải pháp: **Eventual Consistency** với event-driven updates:

```
Luồng Event-Driven:

1. Order Service: "Đã confirm đơn ORD-001"
   → Publish event: order.confirmed {sku: IPHONE-16, qty: 1, warehouse: HCM}

2. Inventory Service (Consumer):
   → Nhận event → reservation status: ACTIVE → COMMITTED
   → physical_qty -= 1, reserved_qty -= 1

3. Warehouse Service (Consumer):
   → Nhận event → Tạo pick list cho nhân viên kho

4. Analytics Service (Consumer):
   → Nhận event → Cập nhật dashboard doanh số

Mỗi service cập nhật state riêng, async, eventually consistent.
```

### Xử lý xung đột: Optimistic Locking

```go
// Optimistic locking: kiểm tra version trước khi update
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
        // Version mismatch → ai đó đã update trước → retry
    }
    return ErrConcurrencyConflict
}
```

---

## Inventory Sync giữa nhiều kênh bán

Khi bán trên cả Shopee, Lazada, và website riêng, cùng một SKU:

```
         ┌──────────┐
         │ Inventory │  ← Source of truth
         │ Service   │
         └─────┬─────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Shopee │ │ Lazada │ │Website │
│ Channel│ │Channel │ │Channel │
│ ATP: 80│ │ATP: 80 │ │ATP: 80 │
└────────┘ └────────┘ └────────┘

Vấn đề: Nếu Shopee bán 1, phải giảm ATP ở Lazada và Website ngay
→ Giải pháp: Event-driven sync hoặc Channel-specific allocation

Channel Allocation:
  Shopee: max 40 (50%)
  Lazada: max 24 (30%)
  Website: max 16 (20%)
  → Mỗi kênh có "quota" riêng → Không xung đột
```

---

## Metrics quan trọng

| Metric | Ý nghĩa | Mục tiêu |
|---|---|---|
| **Stockout Rate** | % thời gian SKU hết hàng | < 2% |
| **Oversell Rate** | % đơn bị hủy do bán vượt tồn | < 0.1% |
| **Inventory Turnover** | Số lần xoay vòng hàng tồn/năm | > 12 (monthly) |
| **Reservation Expiry Rate** | % reservation bị expire (khách không thanh toán) | < 15% |
| **ATP Accuracy** | Độ chính xác của số hàng có thể bán | > 99.5% |

---

[← Chương trước: Phần 1 — Order Fulfillment](/series/ecommerce-order-allocation/part-1-order-fulfillment-fundamentals/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 3 — Thuật toán phân bổ →](/series/ecommerce-order-allocation/part-3-allocation-algorithms/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 2 — Inventory Management: Quản lý tồn kho thời gian thực giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Hệ thống tồn kho thời gian thực là nền tảng cho mọi quyết định phân bổ. Tìm hiểu cách xử lý overselling, stock reservation, và eventual consistency trong tồn kho lớn.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
