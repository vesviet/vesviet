---
title: "Phần 1 — Order Fulfillment: Từ click \"Mua hàng\" đến giao tận tay"
slug: "part-1-order-fulfillment-fundamentals"
date: 2026-05-06T20:30:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
description: "Hiểu rõ vòng đời đơn hàng e-commerce — từ khi khách bấm mua, qua hệ thống OMS, đến khi hàng được pick-pack-ship và giao tận tay khách."
weight: 2
ShowToc: true
TocOpen: true
series:
  - "ecommerce-order-allocation"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-1-order-fulfillment-fundamentals/"
categories:
  - "Series"
  - "E-Commerce"
  - "Logistics & Supply Chain"
tags:
  - "Order Allocation"
  - "Fulfillment"
  - "OMS"
  - "WMS"
  - "Logistics"
cover:
  image: "/images/posts/default-post.png"
  alt: "Order Fulfillment: Từ click Mua hàng đến giao tận tay"
  relative: false
---

[← Chương trước: Tóm tắt — Tổng quan Kiến trúc](/series/ecommerce-order-allocation/executive-summary/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 2 — Inventory Management →](/series/ecommerce-order-allocation/part-2-inventory-realtime/)

---

> **Answer-first:** Quy trình Order Fulfillment trải qua 8 giai đoạn từ tiếp nhận đơn (Order Created), xác thực thanh toán (Payment Authorization), kiểm tra gian lận, phân bổ kho và tài xế (Allocation Engine), đến lấy hàng (Pick & Pack), vận chuyển (In Transit) và giao thành công, vận hành trên nền tảng Event-Driven Architecture.

---

## Vòng đời đơn hàng (Order Lifecycle)

Mỗi đơn hàng trên Amazon, Shopee hay Lazada đều trải qua **8 giai đoạn** từ lúc khách bấm "Mua" đến lúc nhận hàng:

```
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

### Giai đoạn 1: Order Created — Tiếp nhận đơn

```
Khách bấm "Mua hàng"
  │
  ▼
Validate:
  ✓ Sản phẩm còn hàng? (preliminary stock check)
  ✓ Địa chỉ giao hàng hợp lệ?
  ✓ Phương thức thanh toán hợp lệ?
  ✓ Có mã giảm giá? Áp dụng đúng?
  │
  ▼
Tạo Order record trong DB:
  order_id: "ORD-2026-05-06-001"
  status: PENDING
  items: [
    {sku: "WATER-5L", qty: 2, capacity: 4},  -- 2 thùng nước 5L, capacity = 4
    {sku: "PHONE-X", qty: 1, capacity: 1},    -- 1 điện thoại, capacity = 1
  ]
  total_capacity: 5
  customer_location: {lat: 10.77, lng: 106.70}
  delivery_sla: "SAME_DAY"
```

### Giai đoạn 2: Payment Authorization — Xác thực thanh toán

Hệ thống không charge tiền ngay. Nó chỉ **authorize** (giữ tiền) để đảm bảo khách có đủ số dư. Tiền chỉ bị capture (trừ thật) sau khi hàng được gửi đi.

```
Flow:
  Order Service → Payment Gateway → Bank
  
  Authorization Request: "Giữ 500.000 VND từ thẻ XXXX-1234"
  Bank Response: "AUTH_CODE: A12345, HOLD: 500.000 VND"
  
  Order status: PENDING → AUTHORIZED
```

### Giai đoạn 3: Fraud Check — Kiểm tra gian lận

```
Fraud Score = f(
  customer_history,       -- Khách mới hay cũ?
  order_value,            -- Đơn có giá trị bất thường?
  shipping_address,       -- Địa chỉ lạ?
  payment_method,         -- Thẻ mới chưa dùng bao giờ?
  device_fingerprint,     -- Thiết bị có bị flag?
  velocity_check          -- Đặt bao nhiêu đơn trong 1 giờ?
)

if fraud_score > 0.8:  → REJECT (tự động hủy)
if fraud_score > 0.5:  → MANUAL_REVIEW (chuyển nhân viên kiểm tra)
if fraud_score < 0.5:  → APPROVED (tiếp tục xử lý)
```

### Giai đoạn 4: Allocation Engine — Bộ não phân bổ

**Đây là phần quan trọng nhất** — quyết định kho nào gửi và tài xế nào giao. Toàn bộ Phần 3 và Phần 6 sẽ đi sâu vào giai đoạn này.

```
Input:
  - Order: {items, total_capacity: 5, customer_location, sla: SAME_DAY}
  - Warehouses: [{id: "WH-HCM", inventory: {...}, location: {...}}]
  - Drivers: [
      {id: "D1", current_load: 3, max_capacity: 10, min_capacity: 2, location: ...},
      {id: "D2", current_load: 8, max_capacity: 10, min_capacity: 2, location: ...},
    ]

Decision:
  Warehouse: WH-HCM (có hàng, gần khách)
  Driver: D1 (current_load 3 + order_capacity 5 = 8 ≤ max 10) ✓
  D2: (current_load 8 + order_capacity 5 = 13 > max 10) ✗

Output:
  Fulfillment Plan:
    warehouse: WH-HCM
    driver: D1
    estimated_pickup: 14:00
    estimated_delivery: 15:30
```

#### Kiến trúc Allocation dựa trên Chiến lược giá (Pricing-Driven Allocation)

Việc quyết định *khi nào* chạy thuật toán Allocation phụ thuộc rất lớn vào chiến lược giá của Ban Giám Đốc (BOD) đối với bài toán **Đa kho (Multi-Depot)**. Khi một món hàng có giá nhập hoặc giá bán khác nhau ở từng kho, kiến trúc hệ thống sẽ rẽ nhánh thành 3 mô hình chính:

1. **Pre-Checkout Allocation (Mô hình Hyperlocal):**
   - *Ví dụ:* GrabMart, Bách Hóa Xanh, Instacart.
   - *Cách hoạt động:* Hệ thống buộc khách nhập địa chỉ giao hàng ngay khi mở app. Dựa vào địa chỉ (Geo-fencing), hệ thống sẽ "khóa" (Lock) session của khách vào 1 kho cụ thể gần nhất. Giá và tồn kho hiển thị là của riêng kho đó.
   - *Đặc điểm:* Việc phân bổ kho diễn ra **trước** checkout. Hệ thống không tự động đổi kho sau khi khách đã đặt.

2. **User-Driven Allocation (Mô hình Buy Box Marketplace):**
   - *Ví dụ:* Amazon Buy Box, Shopee.
   - *Cách hoạt động:* Hệ thống công khai việc có nhiều kho/seller. Thuật toán tính toán real-time `(Giá Item tại Kho + Phí Ship dự kiến)` cho từng kho. Kho nào mang lại tổng chi phí thấp nhất cho khách sẽ được đẩy lên nút "Add to Cart" mặc định. Khách tự quyết định mua của ai.
   - *Đặc điểm:* Đẩy quyền quyết định allocation sang cho khách hàng.

3. **Post-Checkout Cost Absorption (Mô hình Omnichannel):**
   - *Ví dụ:* Các chuỗi bán lẻ đa kênh.
   - *Cách hoạt động:* Khách hàng thấy 1 giá chuẩn duy nhất trên website. Sau khi checkout, Allocation Engine (như OR-Tools) chạy ngầm để tính toán: *Giao từ kho A xa hơn (tốn tiền ship) nhưng giá vốn nhập hàng cực rẻ, hay giao từ kho B gần hơn (ship rẻ) nhưng giá vốn đắt?*
   - *Đặc điểm:* Nền tảng tự động "bù lỗ" tiền ship hoặc ăn lời chênh lệch giá vốn để tối ưu hóa Profit Margin tổng thể. Trải nghiệm khách hàng đồng nhất.

### Giai đoạn 5: Pick & Pack — Lấy hàng và đóng gói

Tại kho, hệ thống **Warehouse Management System (WMS)** điều phối:

```
Pick List cho Order ORD-2026-05-06-001:
  ┌─────────────────────────────────────────────┐
  │  Aisle B, Shelf 3, Bin 12: WATER-5L × 2    │
  │  Aisle D, Shelf 1, Bin 05: PHONE-X × 1     │
  └─────────────────────────────────────────────┘

Tối ưu hóa Pick Path:
  Thay vì đi lung tung → WMS tính đường đi ngắn nhất qua tất cả bin
  (Travelling Salesman Problem phiên bản trong kho)

Pack:
  - Chọn hộp phù hợp (không quá lớn gây lãng phí)
  - In label với barcode + địa chỉ
  - Cân trọng lượng → xác nhận đúng hàng
  - Scan → cập nhật status: PACKED
```

### Giai đoạn 6-7: Handoff → In Transit

```
Driver D1 đến kho WH-HCM:
  1. Scan barcode kiện hàng → Xác nhận nhận hàng
  2. App tài xế hiển thị lộ trình tối ưu (nếu có nhiều kiện)
  3. Order status: PACKED → IN_TRANSIT
  4. Khách nhận notification: "Đơn hàng đang được giao!"
  5. GPS tài xế bắt đầu stream → Khách theo dõi trên bản đồ
```

### Giai đoạn 8: Delivered — Giao hàng thành công

```
Tài xế đến nơi:
  1. Khách xác nhận nhận hàng (chữ ký / OTP / ảnh)
  2. Order status: IN_TRANSIT → DELIVERED
  3. Payment capture: 500.000 VND bị trừ thật từ thẻ
  4. Inventory: SKU counts giảm vĩnh viễn
  5. Driver capacity: giải phóng 5 đơn vị capacity
```

---

## Order Management System (OMS) — Bộ điều phối trung tâm

Trong xu hướng **Unified Commerce** (2026), OMS không chỉ quản lý đơn hàng mà còn đóng vai trò là "bộ đầu não chiến lược" điều phối tồn kho đa kênh (cửa hàng vật lý, 3PL, kho trung tâm) theo thời gian thực. Trong kiến trúc microservices, OMS thường được chia thành nhiều service con:

```
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
│  │   (Phân bổ kho + tài xế)     │               │
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

Mỗi giai đoạn phát ra **domain events** qua Kafka:

| Event | Producer | Consumers |
|---|---|---|
| `order.created` | Order Service | Inventory (reserve stock), Fraud Check |
| `order.authorized` | Payment Service | Allocation Engine |
| `order.allocated` | Allocation Engine | WMS (pick list), Driver Service |
| `order.picked` | WMS | Packing Station |
| `order.packed` | WMS | Driver Dispatch |
| `order.in_transit` | Delivery Service | Customer Notification, Tracking |
| `order.delivered` | Delivery Service | Payment (capture), Inventory (commit), Analytics |

---

[← Chương trước: Tóm tắt — Tổng quan Kiến trúc](/series/ecommerce-order-allocation/executive-summary/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 2 — Inventory Management →](/series/ecommerce-order-allocation/part-2-inventory-realtime/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 1 — Order Fulfillment: Từ click \ giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Hiểu rõ vòng đời đơn hàng e-commerce — từ khi khách bấm mua, qua hệ thống OMS, đến khi hàng được pick-pack-ship và giao tận tay khách.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
