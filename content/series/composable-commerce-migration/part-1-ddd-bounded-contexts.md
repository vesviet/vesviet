---
title: "Phần 1: Phân rã Magento thành 21 Go Microservices bằng DDD"
date: 2026-04-08T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Cách ánh xạ 240 module Magento 2 thành 21 microservices bằng DDD: chia tách Checkout ≠ Order, Pricing ≠ Promotion để tối ưu kiến trúc."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Magento", "DDD", "Domain-Driven Design", "Bounded Context", "Microservices", "Golang"]
series: ["composable-commerce-migration"]
weight: 2
slug: "part-1-ddd-bounded-contexts"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-1-ddd-bounded-contexts/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 1: Phân rã Magento thành 21 Go Microservices bằng DDD"
  relative: false
keywords: ["ddd bounded contexts", "magento decomposition", "checkout vs order service", "pricing promotion ddd"]
---

[← Chương trước: Phần 0: Tránh Bẫy $200K/Năm Magento](/series/composable-commerce-migration/part-0-executive-summary/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 2: Rush Monorepo 21 Go & Next.js Apps →](/series/composable-commerce-migration/part-2-rush-monorepo/)

---

> **Answer-first:** Số lượng microservices cần thiết được quyết định bởi cấu trúc đội ngũ, đặc tả chịu tải và ranh giới bất biến nghiệp vụ; áp dụng DDD bóc tách 240 module Magento thành 21 Bounded Contexts độc lập (như tách Checkout khỏi Order, Pricing khỏi Promotion).

---

**Answer-first:** Số lượng service bạn cần được quyết định bởi **cấu trúc đội ngũ, đặc tả chịu tải (scaling profile), và ranh giới của các bất biến nghiệp vụ (business invariants)** của bạn — chứ không phải bởi các khuôn mẫu sáo rỗng. Trong môi trường e-commerce năm 2026, với việc chuyển dịch sang Agentic Commerce và Composable APIs, việc thiết lập ranh giới rõ ràng càng trở nên cốt lõi. Nền tảng trong series này sử dụng 21 services để đáp ứng 10,000+ đơn hàng/ngày.

<!--more-->

Bất kỳ team Magento nào khi quyết định chuyển dịch sang microservices cũng đều phải đối mặt với cùng một câu hỏi đầu tiên: **cần bao nhiêu service?** (E-E-A-T: Kiến thức được kiểm chứng từ các đợt chuyển đổi hàng triệu đô bởi đội ngũ chuyên gia).

Ngành công nghiệp thường bảo là 4–6. Đó là một điểm khởi đầu hợp lý — nhưng hoàn toàn sai lầm khi áp dụng cho e-commerce nghiêm túc ở quy mô lớn, dẫn đến hiện tượng **Distributed Monolith**.

## 1. Tại sao lại chia theo Ranh giới DDD, mà không phải Bảng Database

Sai lầm phổ biến nhất là nhìn vào các bảng database của Magento và vẽ ranh giới service.
"Chúng ta có bảng `catalog_product_entity`, vậy ta cần một Product Service." 
Cách làm này tạo ra những **service thiếu máu (anemic services)**.

Thiết kế Hướng Miền (Domain-Driven Design - DDD) áp dụng một cách tiếp cận khác: gom nhóm code xoay quanh các **năng lực nghiệp vụ (business capabilities) và những quy tắc bất biến (invariants)**.

## 2. Nhóm 6 Bounded Context (21 Services)

Nền tảng này tổ chức 21 service thành 6 nhóm domain:

1. **Luồng Thương mại (3):** Checkout, Order, Payment.
2. **Sản phẩm & Nội dung (4):** Catalog, Pricing, Promotion, Search. *(Đặc biệt quan trọng để support AI Agents trong Agentic Commerce)*
3. **Định danh & Truy cập (3):** Auth, User, Customer.
4. **Hậu cần (3):** Warehouse, Fulfillment, Shipping.
5. **Hậu mãi (2):** Return, Loyalty.
6. **Nền tảng & Vận hành (6):** Gateway, Analytics, Review, Notification, Location, CommonOps.

## 3. Hai Pha Chia Tách Nghe Có Vẻ Ngược Đời

### Chia tách 1: Checkout ≠ Order
- **Checkout Service**: quản lý trạng thái tạm thời, có thể bỏ đi được (giỏ hàng, tính giá phí vận chuyển thời gian thực).
- **Order Service**: quản lý trạng thái vĩnh viễn (lịch sử đơn hàng, cỗ máy trạng thái tài chính). Đảm bảo tính ACID khắt khe.

### Chia tách 2: Pricing ≠ Promotion
- **Pricing Service**: Nguồn sự thật cho giá gốc. Tần suất cập nhật thấp, tỷ lệ đọc cực cao (được tối ưu với Redis).
- **Promotion Service**: Quản lý logic mã giảm giá, BOGO, event-driven. Có tính transactional cao.

## 4. Ứng dụng các Nguyên tắc DDD

Bốn nguyên tắc DDD cực kỳ rõ ràng trích từ ADR-002:
1. **Đơn nhiệm (Single Responsibility)**.
2. **Database Per Service (Mỗi service một DB)**.
3. **Ngôn ngữ Phổ quát (Ubiquitous Language)**.
4. **Lớp Chống tham nhũng (Anti-Corruption Layer)**.

## 5. Mức độ Trưởng thành (Maturity) và Trình tự Chuyển đổi

Không phải cả 21 service đều có thể đạt chuẩn production-ready cùng một lúc. Hãy áp dụng **Selective Extraction**: bóc tách và deploy những phần an toàn trước (Read-only APIs) trước khi động đến luồng thanh toán sinh tử.

## Câu Hỏi Thường Gặp (FAQ)

### Có bắt buộc phải chia đúng 21 service không?
Không. Nguyên tắc là: *Số lượng service ≈ Số lượng team × 2–3*, bị giới hạn bởi các bất biến về chịu tải. Cửa hàng dưới 2,000 đơn/ngày chỉ cần 5-7 services, hoặc thậm chí giữ ở dạng Modular Monolith.

### Điều gì xảy ra nếu tôi không chịu tách Pricing ra khỏi Promotion?
Gộp chung chúng lại sẽ ép bạn phải cấp phát thừa mứa tài nguyên cho luồng đọc (vốn cache được) chỉ để tải lượng request tạo/xóa của promotion (transactional), đồng thời mở rộng "vùng nổ" khi hệ thống gặp lỗi.

---
*Để tham khảo thêm về hệ thống 21 services, hãy đón đọc Phần 2: Thiết lập Rush Monorepo.*

---

---

---

[← Chương trước: Phần 0: Tránh Bẫy $200K/Năm Magento](/series/composable-commerce-migration/part-0-executive-summary/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 2: Rush Monorepo 21 Go & Next.js Apps →](/series/composable-commerce-migration/part-2-rush-monorepo/)
