---
title: "Phần 5 — Split Shipment, Consolidation & Last-Mile Delivery"
slug: "part-5-split-consolidation-lastmile"
date: 2026-05-06T20:30:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
description: "Quyết định gộp hay tách đơn hàng, và tối ưu hóa giao hàng chặng cuối — phần tốn kém nhất chiếm 53% tổng chi phí logistics."
weight: 6
ShowToc: true
TocOpen: true
series:
  - "ecommerce-order-allocation"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-5-split-consolidation-lastmile/"
categories:
  - "Series"
  - "E-Commerce"
  - "Logistics & Supply Chain"
tags:
  - "Split Shipment"
  - "Consolidation"
  - "Last-Mile"
  - "Logistics"
  - "Supply Chain"
cover:
  image: "/images/posts/default-post.png"
  alt: "Split Shipment, Consolidation & Last-Mile Delivery"
  relative: false
---

[← Chương trước: Phần 4 — Amazon CONDOR & Anticipatory Shipping](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 6 — Xây dựng Mini Allocation Engine →](/series/ecommerce-order-allocation/part-6-build-mini-allocation-engine/)

---

> **Answer-first:** Quyết định Split vs Consolidation cân bằng giữa chi phí vận hành và cam kết SLA giao hàng. Last-Mile chiếm đến 53% tổng chi phí logistics, đòi hỏi tối ưu hóa mật độ giao hàng (delivery density), gom nhóm đơn thông minh theo SKU Affinity, và áp dụng mạng lưới Delivery Lockers để cắt giảm chi phí chặng cuối.

---

## Split vs. Consolidation — Trade-off cốt lõi

Khi đơn hàng có nhiều món nhưng các món nằm ở nhiều kho khác nhau, hệ thống phải đối mặt với quyết định kinh điển:

```
Đơn hàng: 3 món (A ở kho HN, B ở kho HCM, C ở kho ĐN)
Giao cho khách ở Hà Nội

Phương án 1: SPLIT (Tách gửi từ 3 kho)
  Kho HN → Khách: A (1 kiện)     — 30.000đ, 2 giờ
  Kho HCM → Khách: B (1 kiện)    — 85.000đ, 2 ngày
  Kho ĐN → Khách: C (1 kiện)     — 65.000đ, 1.5 ngày
  Tổng: 180.000đ, 3 lần giao, 3 hộp

Phương án 2: CONSOLIDATE (Gom về 1 kho rồi gửi)
  Kho HCM → Kho HN: B (nội bộ)   — 40.000đ, 1 ngày
  Kho ĐN → Kho HN: C (nội bộ)    — 35.000đ, 1 ngày
  Kho HN → Khách: A+B+C (1 kiện) — 45.000đ, 2 giờ
  Tổng: 120.000đ, 1 lần giao, 1 hộp, nhưng chậm hơn 1-2 ngày

Trade-off: Nhanh + tốn  vs.  Chậm + tiết kiệm
```

### Decision Matrix

| Yếu tố | Ưu tiên Split | Ưu tiên Consolidate |
|---|---|---|
| **SLA** | Giao nhanh (same-day, 2h) | Giao tiêu chuẩn (3-5 ngày) |
| **Chi phí** | Khách trả phí ship | Free shipping (seller chịu) |
| **Trải nghiệm** | Khách cần gấp từng món | Khách muốn nhận đủ 1 lần |
| **Giá trị đơn** | Đơn nhỏ (không đáng gom) | Đơn lớn (gom tiết kiệm đáng kể) |
| **Loại hàng** | Hàng tươi/khẩn cấp | Hàng khô, không gấp |

---

## Thuật toán quyết định Split/Consolidate

```
Function: decideFulfillmentStrategy(order, warehouses)

  // Bước 1: Kiểm tra xem có kho nào có ĐỦ tất cả items không
  single_source = findWarehouseWithAllItems(order.items, warehouses)
  if single_source exists:
    return SINGLE_SOURCE(single_source)  // Lý tưởng nhất

  // Bước 2: Tính chi phí cho mỗi phương án
  split_cost = calculateSplitCost(order)
  consolidate_cost = calculateConsolidateCost(order)

  // Bước 3: Kiểm tra SLA
  if order.sla == "SAME_DAY" or order.sla == "2_HOURS":
    return SPLIT  // Không đủ thời gian gom

  // Bước 4: So sánh chi phí
  savings = split_cost - consolidate_cost
  consolidation_delay = estimateConsolidationDelay(order)

  // Chỉ gom nếu tiết kiệm > ngưỡng VÀ delay chấp nhận được
  if savings > THRESHOLD and consolidation_delay <= order.max_acceptable_delay:
    return CONSOLIDATE
  else:
    return SPLIT
```

---

## Last-Mile Delivery — Chặng cuối đắt đỏ

**Last-mile** là chặng cuối từ hub/kho đến tay khách hàng. Dù chỉ dài vài km, nó chiếm **53% tổng chi phí logistics** vì:

```
Vận chuyển đường dài (Line-haul):
  1 xe tải chở 10.000 kiện, đi 500km
  Chi phí/kiện: ~5.000đ

Last-mile:
  1 tài xế giao 20-30 kiện, đi 50km quanh thành phố
  Chi phí/kiện: ~15.000-25.000đ  ← Đắt gấp 3-5 lần!

Lý do:
  - Tốc độ thấp (kẹt xe, đèn đỏ)
  - Nhiều điểm dừng (mỗi kiện 1 địa chỉ)
  - Thời gian chờ (khách không ở nhà)
  - Chi phí nhân công cao (1 tài xế/20-30 kiện)
```

### Tối ưu Last-Mile

**1. Delivery Density — Mật độ giao hàng:**
```
Mật độ thấp:                Mật độ cao:
  ○                            ○ ○
     ○                         ○ ○ ○
  ○       ○                    ○ ○
                               ○ ○ ○
  10 kiện, 30km                10 kiện, 5km
  Chi phí/kiện: 25.000đ       Chi phí/kiện: 8.000đ

CONDOR tăng mật độ bằng cách gom đơn cùng khu vực → giảm cost.
```

**2. Time Windows — Khung giờ giao:**
```
Cho khách chọn khung giờ giao:
  8:00-10:00  | 10:00-12:00 | 14:00-16:00 | 18:00-20:00

Lợi ích: Tài xế biết chính xác khi nào khách ở nhà
→ Giảm giao lại (re-delivery) từ 15% xuống 3%
→ Tối ưu lộ trình theo time window
```

**3. Delivery Locker / Pickup Points:**
```
Thay vì giao tận nhà (last-mile tốn kém):
  → Khách đến lấy tại tủ locker gần nhà
  → 1 chuyến tài xế giao 50 kiện vào 1 locker (thay vì 50 địa chỉ)
  → Chi phí/kiện giảm 60-70%
```

### Xu hướng Tối ưu Last-Mile (2026)

Trong môi trường sản xuất 2026, chiến lược Last-Mile có những sự dịch chuyển đáng kể:
- **Từ "Speed of Now" sang "Right-Speed":** Bán lẻ không còn chạy đua giao hàng siêu tốc bằng mọi giá. Khách hàng sẵn lòng chờ 2-3 ngày nếu khung giờ giao được cam kết chuẩn xác (precision) và miễn phí, tạo khoảng trống thời gian quý giá để logistics gom đơn và tối ưu lộ trình.
- **AI-Driven Orchestration:** AI đảm nhận toàn bộ quá trình điều phối ghép nhóm đơn (dynamic order batching) theo thời gian thực thay vì chỉ tối ưu lộ trình tĩnh. AI đánh giá thời tiết, giao thông, khả năng xe, và ưu tiên đơn hàng để tạo nhóm đi tối ưu nhất.
- **Sustainable Consolidation:** Gom đơn và tăng mật độ điểm dừng (delivery density) được coi là chiến lược phát triển bền vững cốt lõi, giúp giảm lượng khí thải carbon và tuân thủ các quy định môi trường đô thị khắt khe tại nhiều quốc gia.

---

## SKU Affinity — Xếp hàng thông minh

Sản phẩm thường được mua cùng nhau nên được đặt cùng kho:

```
Phân tích dữ liệu mua hàng:

  iPhone thường mua cùng: ốp lưng (78%), cáp sạc (65%), tai nghe (45%)
  Bột giặt thường mua cùng: nước xả (82%), khăn giấy (40%)
  Sữa tươi thường mua cùng: ngũ cốc (55%), trứng (48%)

→ Đặt iPhone + ốp lưng + cáp sạc CÙNG KHO
→ Giảm xác suất split shipment từ 30% xuống 12%
```

```sql
-- Tính SKU affinity từ dữ liệu order
SELECT
    a.sku AS sku_a,
    b.sku AS sku_b,
    COUNT(DISTINCT a.order_id) AS co_occurrence,
    COUNT(DISTINCT a.order_id)::float / 
      (SELECT COUNT(DISTINCT order_id) FROM order_items WHERE sku = a.sku) AS affinity_score
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.sku < b.sku
GROUP BY a.sku, b.sku
HAVING COUNT(DISTINCT a.order_id) > 100
ORDER BY affinity_score DESC;
```

---

## Metrics Last-Mile

| Metric | Ý nghĩa | Mục tiêu |
|---|---|---|
| **Cost per delivery** | Chi phí trung bình mỗi lần giao | < 15.000đ |
| **Stops per route** | Số điểm dừng mỗi lộ trình | > 25 |
| **Delivery density** | Số kiện/km² | > 5 |
| **First attempt success** | % giao thành công lần đầu | > 95% |
| **Split shipment rate** | % đơn bị tách | < 15% |
| **On-time delivery** | % giao đúng hẹn | > 98% |

---

[← Chương trước: Phần 4 — Amazon CONDOR & Anticipatory Shipping](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/) | [Mục lục Series](/series/ecommerce-order-allocation/) | [Chương tiếp theo: Phần 6 — Xây dựng Mini Allocation Engine →](/series/ecommerce-order-allocation/part-6-build-mini-allocation-engine/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 5 — Split Shipment, Consolidation & Last-Mile Delivery giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Quyết định gộp hay tách đơn hàng, và tối ưu hóa giao hàng chặng cuối — phần tốn kém nhất chiếm 53% tổng chi phí logistics.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
