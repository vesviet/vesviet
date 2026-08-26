---
title: "Chuyển đổi sang Composable Commerce"
slug: "composable-commerce-migration"
description: "Thoát khỏi Magento lên Go Microservices (2026): DDD Bounded contexts, Strangler Fig 3 giai đoạn, Dapr PubSub, Agentic Commerce."
date: 2026-04-01T10:00:00+07:00
lastmod: "2026-08-16T12:00:00+07:00"
draft: false
weight: 145
author: "Lê Tuấn Anh"
ShowToc: true
TocOpen: true
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/"
cover:
  image: "/images/posts/default-post.png"
  alt: "Chuyển đổi sang Composable Commerce"
  relative: false
categories: ['Series', 'Software Engineering', 'Backend Architecture']
tags: ['Magento', 'Microservices', 'Golang', 'DDD', 'Strangler Fig', 'Rush Monorepo', 'Dapr', 'Kratos', 'Agentic Commerce', '2026 Trends']
---

> **Answer-first:** Chuyển đổi từ Magento Enterprise sang Composable Commerce áp dụng mô hình Strangler Fig 3 giai đoạn kết hợp Go 1.25, Kratos v2 và Dapr Pub/Sub giúp loại bỏ hoàn toàn phí bản quyền $200k/năm, tách 21 Bounded Contexts theo DDD, bảo đảm zero-downtime và hỗ trợ Agentic Commerce.

---

Chào mừng bạn đến với cẩm nang toàn tập về **Chuyển đổi sang Composable Commerce (Thương mại lắp ghép)** — cách phẫu thuật tháo dỡ một khối monolith Magento 2 thành một nền tảng microservices chuẩn production, không làm rơi rớt một đơn hàng nào trong quá trình chuyển đổi, sẵn sàng cho xu hướng **Agentic Commerce** (thương mại được tối ưu hóa cho cả người dùng và AI agent).

<!--more-->

> **Về Series này (E-E-A-T & Thực tiễn)**
>
> Nội dung này được đúc kết từ quá trình xây dựng một **Nền tảng Composable Commerce** thực tế — 21 Go microservices + 2 frontend đảm nhiệm toàn bộ quy trình nghiệp vụ thương mại: Duyệt (Browse) → Tìm kiếm (Search) → Giỏ hàng (Cart) → Thanh toán (Checkout) → Trả tiền (Pay) → Hoàn tất (Fulfill) → Vận chuyển (Ship) → Hoàn hàng (Return). Với hơn 17 năm kinh nghiệm xây dựng e-commerce, tác giả Lê Tuấn Anh đem đến cẩm nang thực chiến, loại bỏ 0 đồng phí bản quyền Magento. Mọi quyết định kiến trúc trong series này đều được đúc kết từ một trong **24 Hồ sơ Quyết định Kiến trúc (ADRs)** của chúng tôi.

---

## 🎯 Tư vấn Chuyển đổi

Đội ngũ của bạn đang lên kế hoạch thoát khỏi Magento hay đang đánh giá việc chuyển đổi sang kiến trúc composable commerce khi các hệ thống AI đang tái định hình e-commerce năm 2026? 

👉 **[Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)** với Senior Architect Lê Tuấn Anh — Hơn 17 năm kinh nghiệm xây dựng các nền tảng e-commerce enterprise tại Việt Nam và Đông Nam Á.

---

## 📚 Chương trình Cốt lõi

Lược đồ EAV, khóa chính dạng số nguyên (integer primary keys), và sự phụ thuộc module PHP của Magento làm cho việc chuyển đổi trở nên đặc biệt hiểm nghèo. Series này mang đến cho bạn cẩm nang Strangler Fig 3 giai đoạn hoàn chỉnh:

1. **[Phần 0: Tóm tắt cho Quản lý — Tại sao $200K/Năm lại là một Cái Bẫy](/series/composable-commerce-migration/part-0-executive-summary/)**
   *Chi phí thực sự của Magento Enterprise, và tại sao kiến trúc composable lại tự hoàn vốn ngay trong Năm 1, cũng như giúp bạn tránh cạm bẫy "Distributed Monolith".*

2. **[Phần 1: Bounded Contexts trong DDD — Phân rã các Module Magento](/series/composable-commerce-migration/part-1-ddd-bounded-contexts/)**
   *Cách ánh xạ cấu trúc module của Magento thành 21 bounded context sử dụng Domain-Driven Design.*

3. **[Phần 2: Rush Monorepo — Quản lý 21 Go Services + 2 Frontends](/series/composable-commerce-migration/part-2-rush-monorepo/)**
   *Tại sao chúng tôi chọn Microsoft Rush thay vì Nx/Turborepo cho một monorepo trộn lẫn Go + Next.js + React.*

4. **[Phần 3: Golang + Kratos v2 — Đi sâu vào Framework Microservice](/series/composable-commerce-migration/part-3-golang-kratos/)**
   *Kratos v2 xử lý transport, tiêm phụ thuộc (dependency injection), và mô hình common library.*

5. **[Phần 4: Kiến trúc gRPC Internal + REST Gateway](/series/composable-commerce-migration/part-4-grpc-rest-gateway/)**
   *Giao tiếp service-to-service bằng gRPC, REST qua gRPC-Gateway.*

6. **[Phần 5: Chuyển đổi Lược đồ EAV — Cạm bẫy Lớn nhất của Magento](/series/composable-commerce-migration/part-5-eav-schema-migration/)**
   *Gỡ rối `catalog_product_entity_varchar`, ánh xạ định danh integer → UUID.*

7. **[Phần 6: Giai đoạn 1 — Strangler Fig: Chuyển đổi Read-Only + CDC](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)**
   *Triển khai Go service dưới dạng read-only, sử dụng CDC từ Magento MySQL.*

8. **[Phần 7: Giai đoạn 2 — Dual-Write: Dapr PubSub + Feature Flags](/series/composable-commerce-migration/part-7-phase2-dual-write/)**
   *Kích hoạt write APIs, đồng bộ qua Dapr PubSub + Transactional Outbox.*

9. **[Phần 8: Giai đoạn 3 — Chuyển đổi Hoàn toàn: Zero Downtime + GitOps](/series/composable-commerce-migration/part-8-phase3-full-cutover/)**
   *Chuyển dịch traffic tăng dần, Magento về hot-standby.*

10. **[Phần 9: Transactional Outbox + Saga Pattern Giữa các Service](/series/composable-commerce-migration/part-9-outbox-saga/)**
    *Cách luồng saga Checkout → Order → Payment → Warehouse vận hành.*

11. **[Phần 10: Điểm lại các ADR — Giải thích 24 Quyết định Kiến trúc](/series/composable-commerce-migration/part-10-adr-walkthrough/)**
    *Mọi quyết định lớn — Dapr vs Kafka, database-per-service, gRPC vs REST.*

---

## 🆚 Nền tảng này Thay thế cho cái gì

| Tính năng | Magento Enterprise | Nền tảng này (2026 Standard) |
|---|---|---|
| **Chi phí bản quyền** | $125,000–$200,000/năm | $0 |
| **Thanh toán VNPay / MoMo** | Dùng plugin bên thứ ba | Tích hợp gốc, có circuit breaker |
| **Khả năng chịu tải Flash sale** | Scale toàn bộ monolith gấp 10 lần | Chỉ scale riêng Order + Payment |
| **Agentic AI & LLMs** | Khó tích hợp, schema phức tạp | API-first, Citation-ready cho AI |
| **Quyền sở hữu dữ liệu** | Vendor-hosted (bị phụ thuộc) | Tự host, kiểm soát toàn diện 100% |

---

## 🧭 Bạn Nên Bắt đầu Từ đâu?

| Vị trí của bạn | Điểm khởi đầu Khuyến nghị | Tại sao |
|---|---|---|
| **PM / BA / CTO** | [Phần 0: Tóm tắt cho Quản lý](/series/composable-commerce-migration/part-0-executive-summary/) | Bài toán kinh doanh, so sánh chi phí, ROI của chuyển đổi |
| **Kỹ sư Backend (Magento)** | [Phần 5: Chuyển đổi Lược đồ EAV](/series/composable-commerce-migration/part-5-eav-schema-migration/) | Cạm bẫy kỹ thuật mà hầu hết các team sẽ vấp phải đầu tiên |
| **Kỹ sư Golang** | [Phần 3: Tìm hiểu sâu về Kratos v2](/series/composable-commerce-migration/part-3-golang-kratos/) | Đi sâu vào Framework với các dòng code service thực tế |
| **Kiến trúc sư / Tech Lead** | [Phần 1: Bounded Contexts trong DDD](/series/composable-commerce-migration/part-1-ddd-bounded-contexts/) | Phân rã domain trước khi bắt tay vào viết một dòng code nào |
| **DevOps / SRE** | [Phần 8: Giai đoạn 3 Chuyển đổi + GitOps](/series/composable-commerce-migration/part-8-phase3-full-cutover/) | Quá trình chuyển đổi zero-downtime và mô hình triển khai ArgoCD |

---

## ❓ Câu Hỏi Thường Gặp (FAQ)

{{< faq q="Series này có mặc định rằng tôi đang chạy Magento 2 không?" >}}
Đúng vậy. Các hướng dẫn chuyển đổi này nhắm tới Magento 2.x. Lược đồ EAV, primary keys dạng integer, và mô hình phụ thuộc module đều là các điểm đặc thù của Magento 2. Nếu bạn đang ở trên Magento 1, các mô hình DDD và Golang vẫn có thể áp dụng nhưng các câu truy vấn trích xuất SQL sẽ khác đi.
{{< /faq >}}

{{< faq q="Nền tảng này sử dụng phiên bản Golang và framework nào?" >}}
Nền tảng Composable Commerce chạy trên **Go 1.25** với **Kratos v2** (go-kratos). Cả 21 service chia sẻ chung một thư viện `common` nhằm tiêu chuẩn hóa các tác vụ outbox, idempotency, health checks, và quản lý cấu hình.
{{< /faq >}}

{{< faq q="Quá trình chuyển đổi có thể thực hiện mà không cần ngắt hệ thống (zero downtime) không?" >}}
Có. Phương pháp tiếp cận Strangler Fig 3 giai đoạn được thiết kế chuyên biệt cho zero downtime. Giai đoạn 1 chỉ điều hướng luồng dữ liệu đọc (reads) sang microservices; luồng ghi (writes) vẫn đi vào Magento. Giai đoạn 2 đưa vào chế độ dual-write kèm feature flags. Giai đoạn 3 chuyển dịch dần traffic.
{{< /faq >}}

---

## 🔗 Series Liên Quan & Masterclass Đề Xuất

- **[Magento sang Go Microservices: Chuỗi Bài Viết Chuyển Dịch Tại Việt Nam](/series/magento-migration-vietnam/)** — Playbook tuyển dụng, đánh giá nhân sự và quản trị chi phí chuyển dịch tại Việt Nam.
- **[Masterclass: Kiến trúc Modular Monolith & Sự thoái trào của Microservices](/series/modular-monolith-architecture/)** — Khung ra quyết định khi nào nên chọn Modular Monolith thay vì Microservices.
- **[Kiến trúc Phân bổ Đơn hàng E-commerce (Amazon, eBay)](/series/ecommerce-order-allocation/)** — Thiết kế OMS/WMS phân bổ kho hàng và tối ưu giao vận.
- **[Shopee Architecture: Kiến Trúc Flash Sale](/series/shopee-architecture/)** — Kỹ thuật chịu tải cao trong hạ tầng thương mại điện tử.
- **[Đánh Đổi Kiến Trúc & Những Cuộc Đối Đầu Công Nghệ](/series/architectural-tradeoffs-showdowns/)** — Đánh đổi giữa Go vs PHP/Laravel trong E-commerce 50k RPS.

