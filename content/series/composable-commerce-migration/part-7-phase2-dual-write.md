---
title: "Phần 7: Giai đoạn 2 — Ghi Kép (Dual-Write): Dapr PubSub + Xử lý"
date: 2026-05-20T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Kích hoạt API ghi trên Go microservice khi Magento vẫn chạy live: kỹ thuật dual-write event-driven qua Dapr PubSub, phân xử xung đột và magento-sync."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Dual-Write", "Dapr", "PubSub", "Transactional Outbox", "Event-Driven", "Conflict Resolution"]
series: ["composable-commerce-migration"]
weight: 8
slug: "part-7-phase2-dual-write"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-7-phase2-dual-write/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 7: Giai đoạn 2 — Ghi Kép (Dual-Write): Dapr PubSub + Xử lý"
  relative: false
keywords: ["dual-write migration", "dapr pubsub", "magento sync worker", "conflict resolution dual write"]
---

[← Chương trước: Phần 6: Giai Đoạn 1 — Strangler Fig Read-Only](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 8: Giai Đoạn 3 — Full Cutover Zero Downtime →](/series/composable-commerce-migration/part-8-phase3-full-cutover/)

---

> **Answer-first:** Giai đoạn 2 kích hoạt API ghi trên hệ thống Go microservice song song với Magento nhờ cơ chế Dual-Write bất đồng bộ qua Dapr Pub/Sub và Transactional Outbox, có cờ tính năng (feature flags) và phân xử xung đột dữ liệu tự động.

---

Ở Giai đoạn 1, cả hai hệ thống đều tồn tại song song nhưng chỉ có duy nhất một thằng được phép ghi dữ liệu: Magento. Sang Giai đoạn 2, cả hai hệ thống sẽ cùng thi nhau ghi dữ liệu cùng một lúc (simultaneously). Đây là giai đoạn phức tạp nhất về mặt kỹ thuật — và cũng là nơi mà phần lớn các dự án di dời tự tay làm hỏng (corrupt) dữ liệu của chính mình nếu họ không chuẩn bị sẵn một chiến lược phân xử xung đột (conflict resolution strategy) rõ ràng sòng phẳng.

**Answer-first:** Theo tiêu chuẩn kiến trúc hướng sự kiện năm 2026, Giai đoạn 2 sử dụng kỹ thuật **ghi kép hướng sự kiện (event-driven dual-write)** thông qua Transactional Outbox — tuyệt đối tránh kiểu ghi kép thô (raw dual-write) dễ gây sai lệch (silent inconsistency). Các microservice sẽ ghi vào PostgreSQL của nó trước, sau đó bắn (publish) một domain event vào Dapr PubSub một cách nguyên tử (atomically). Một service có tên `magento-sync-adapter` sẽ đăng ký nghe (subscribe) các event đó và ghi ngược trở lại vào Magento, đảm bảo tính nhất quán sau cùng (eventual consistency). Những ca xung đột (khi cả hai hệ thống cùng xúm vào sửa một bản ghi cùng một lúc) sẽ được phân xử bởi một ma trận gồm 5 chính sách (policy): so kè timestamp cho hồ sơ khách hàng, microservices-mặc-định-thắng cho trạng thái đơn hàng, và cộng dồn đối soát cho số lượt sử dụng mã giảm giá. Kinh nghiệm từ các ca chuyển đổi quy mô lớn cho thấy, việc thiết kế các consumer có tính lũy đẳng (idempotent) là chìa khóa sống còn ở giai đoạn này.

## 1. Tại Sao Không Dùng "Ghi Kép Thô" (Raw Dual Write)?

Ghi kép thô (Raw dual write) nghĩa là: gọi lệnh ghi thẳng vào cả hai database ngay trong cùng một request handler:

```go
// ❌ SAI BÉT: Ghi kép thô — chỉ cần xịt một nửa là dữ liệu hỏng bét
func (h *CustomerHandler) CreateCustomer(ctx context.Context, req *Request) (*Response, error) {
    // Ghi phát 1: Vào PostgreSQL của Microservice
    customer, err := h.customerRepo.Create(ctx, req)
    if err != nil { return nil, err }

    // Ghi phát 2: Vào Magento API (gọi đồng bộ - synchronous)
    _, err = h.magentoClient.CreateCustomer(ctx, customer)
    if err != nil {
        // Cuộc gọi sang Magento bị tạch — NHƯNG khách hàng ĐÃ ĐƯỢC LƯU vào DB của microservice rồi
        // Trạng thái dữ liệu lúc này đã bị vênh (inconsistent). Không có cách nào cứu vãn (recovery path).
        return nil, err
    }
    return customer, nil
}
```

Cách làm này sẽ toang vì không có bất kỳ một giao dịch nguyên tử (atomic transaction) nào có khả năng vắt ngang qua hai hệ thống độc lập cả. Giả sử API của Magento bị khựng lại (down) tầm 200ms đúng lúc đang gọi (lỗi timeout diễn ra như cơm bữa), bạn sẽ đẻ ra một khách hàng nằm chình ình trong database của microservice nhưng lại hoàn toàn vô hình trong Magento. Sự sai lệch này diễn ra trong câm lặng (silent inconsistency) — microservice không hề ném ra lỗi nào trong response, và tài khoản của khách hàng đó có vẻ như vẫn hoạt động bình thường cho đến khi họ thử làm một thao tác nào đó đòi hỏi Magento phải biết tới sự tồn tại của họ.

## 2. Ghi Kép Hướng Sự Kiện: Design Pattern An Toàn

Giai đoạn 2 sử dụng một quy trình ba bước:

```
Bước 1: Client → Gateway → Customer Service
Bước 2: Customer Service:
    a. Ghi vào PostgreSQL (dữ liệu gốc — microservice giờ là bên nắm quyền sinh sát)
    b. Bắn (Publish) sự kiện "customer.updated" vào Dapr PubSub (nằm gói trong một outbox transaction)
Bước 3: magento-sync-adapter:
    a. Đăng ký nghe (Subscribes) sự kiện "customer.updated"
    b. Ghi ngược vào REST API của Magento
    c. Nếu tạch → Ném vào DLQ → chờ người vào xử lý bằng tay (manual review)
```

Design pattern Outbox ở Bước 2 (được giải ngố ở [Phần 9](/series/composable-commerce-migration/part-9-outbox-saga/)) gửi gắm một lời thề sắt đá (guarantees): nếu transaction trên PostgreSQL commit thành công, cái sự kiện kia CHẮC CHẮN sớm muộn gì cũng sẽ được gửi đi (eventually published). Còn nếu transaction bị rollback (hủy), sẽ không có bất kỳ sự kiện nào bị tuột ra ngoài.

```go
// customer-service/internal/biz/customer_usecase.go

func (uc *CustomerUseCase) CreateCustomer(ctx context.Context, c *Customer) (*Customer, error) {
    var created *Customer

    // Transactional: ghi customer + nhét event vào outbox chung trong MỘT transaction duy nhất
    err := uc.tx.Execute(ctx, func(tx *sql.Tx) error {
        var err error
        created, err = uc.repo.CreateWithTx(ctx, tx, c)
        if err != nil { return err }

        // Nhét outbox event — thằng này sẽ được con worker OutboxProcessor bốc đi gửi sau
        return uc.outbox.InsertWithTx(ctx, tx, events.OutboxEvent{
            Topic:   "customer.updated",
            Payload: marshalCustomer(created),
            Source:  "microservices",
        })
    })
    if err != nil { return nil, err }

    return created, nil
}
```

## 3. Service magento-sync-adapter

Đây là một service hoàn toàn mới, chuyên làm nhiệm vụ ngồi rình (subscribe) các domain event từ microservice và đồng bộ (sync) chúng ngược trở lại Magento:

```yaml
# k8s/magento-sync-adapter.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: magento-sync-adapter
  namespace: migration
spec:
  replicas: 2
  template:
    metadata:
      annotations:
        dapr.io/enabled: "true"
        dapr.io/app-id: "magento-sync-adapter"
        dapr.io/app-port: "8080"
    spec:
      containers:
      - name: magento-sync-adapter
        image: magento-sync-adapter:v1.0.0
        env:
        - name: MAGENTO_BASE_URL
          value: "https://magento.internal"
        - name: MAGENTO_TOKEN
          valueFrom:
            secretKeyRef:
              name: magento-api-creds
              key: token
        - name: CONFLICT_RESOLUTION_MODE
          value: "timestamp"   # Các chế độ: timestamp | microservices-wins | magento-wins
```

Cấu hình đăng ký (subscription) của Dapr:

```yaml
# dapr-subscriptions.yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: reverse-sync-customer
  namespace: migration
spec:
  pubsubname: pubsub
  topic: customer.updated
  route: /reverse-sync/customer
  deadLetterTopic: migration.dlq    # Các ca đồng bộ tạch sẽ hạ cánh ở đây chờ người tới khám (manual review)
---
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: reverse-sync-order
  namespace: migration
spec:
  pubsubname: pubsub
  topic: order.placed
  route: /reverse-sync/order
  deadLetterTopic: migration.dlq
```

## 4. Ma Trận Phân Xử Xung Đột (Conflict Resolution Matrix)

Trong suốt Giai đoạn 2, cả Magento lẫn microservices đều có quyền sửa chung một bản ghi. Bộ phân xử xung đột (conflict resolver) sẽ dọn dẹp bãi chiến trường này tùy theo từng loại dữ liệu:

| Thực thể (Entity) | Chính sách Phân xử (Conflict Policy) | Lý do (Rationale) |
|---|---|---|
| **Hồ sơ khách hàng** (tên, email, số điện thoại) | Dựa trên Timestamp: thằng nào ghi sau thằng đó thắng | Cả hai hệ thống đều có lý do chính đáng để cập nhật dữ liệu khách hàng |
| **Trạng thái đơn hàng** | Microservices thắng | Toàn bộ cỗ máy trạng thái (state machine) của đơn hàng đã được bứng sang sống trong Order Service rồi |
| **Số lượng Tồn kho** | Microservices thắng | Tồn kho giữ chỗ theo thời gian thực (Real-time reservations) nay do Warehouse Service nắm trùm |
| **Giá sản phẩm** | Quyết định của Admin (Pricing Service) | Giá rổ giờ chỉ được phép sửa từ Seller Centre thông qua Pricing Service |
| **Lượt dùng mã giảm giá** | Cộng dồn + đối soát (Sum + reconcile) | Cả hai hệ thống đều có quyền cộng dồn (increment) biến đếm này cùng một lúc |

### Phân xử bằng Timestamp (Dành cho Hồ sơ khách hàng)

```go
// magento-sync-adapter/internal/resolver/customer_resolver.go

func (r *ConflictResolver) ResolveCustomerChange(ctx context.Context, event MigrationEvent) error {
    // Móc trạng thái hiện tại (current state) từ DB của microservice lên
    current, err := r.customerRepo.FindByMagentoID(ctx, event.MagentoID)
    if err != nil && !errors.Is(err, ErrNotFound) {
        return fmt.Errorf("fetching current customer: %w", err)
    }

    // Không có xung đột: đây là bản ghi mới toanh
    if current == nil {
        return r.customerRepo.UpsertFromEvent(ctx, event)
    }

    magentoUpdatedAt := event.UpdatedAt
    microUpdatedAt := current.UpdatedAt

    switch {
    case magentoUpdatedAt.After(microUpdatedAt):
        // Thay đổi bên Magento diễn ra sau (newer) → đè dữ liệu từ Magento sang microservice
        return r.customerRepo.UpsertFromEvent(ctx, event)

    case microUpdatedAt.After(magentoUpdatedAt):
        // Thay đổi bên Microservice diễn ra sau (newer) → đẩy dữ liệu microservice ngược lại Magento
        return r.magentoAdapter.UpdateCustomer(ctx, current)

    default:
        // Timestamp bằng nhau y xì → Lũy đẳng (idempotent), hai bên đã đồng bộ, khỏi làm gì cả
        return nil
    }
}
```

### Đối soát Số lượt Dùng Mã giảm giá (Coupon Usage)

```go
// magento-sync-adapter/internal/resolver/coupon_resolver.go

func (r *ConflictResolver) ResolveCouponUsage(ctx context.Context, event MigrationEvent) error {
    magentoCount := event.Data["times_used"].(int64)
    microCount, err := r.promotionRepo.GetUsageCount(ctx, event.CouponCode)
    if err != nil { return err }

    // Không có con số của bên nào là chân lý tuyệt đối cả — cứ lấy số lớn nhất (max)
    // (Làm vậy cho an toàn: ngăn chặn tình trạng xài lố (over-redeeming); có thể hơi báo khống một chút nếu bị trễ nhịp đồng bộ)
    maxCount := max(magentoCount, microCount)

    if err := r.promotionRepo.SetUsageCount(ctx, event.CouponCode, maxCount); err != nil {
        return err
    }

    return r.magentoAdapter.UpdateCouponUsage(ctx, event.CouponCode, maxCount)
}
```

## 5. Trình Tự Di Dời Theo Từng Service

Giai đoạn 2 không bật cờ ghi dữ liệu (write flags) một lượt mà làm theo thứ tự rủi ro tăng dần:

### Bước 1: Customer Service (Rủi ro Thấp Nhất)

```bash
#!/bin/bash
# Kích hoạt quyền ghi (write) cho customer trên microservice

# Bật cờ tính năng write
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_write": "true"}}'

# Dán mắt theo dõi trong 30 phút
./scripts/monitor-dual-write.sh --service=customer --duration=1800

# Nghiệm thu: lấy 1000 mẫu ngẫu nhiên để đối chiếu độ nhất quán
./scripts/validate-dual-write.sh --service=customer --sample=1000
```

Phần theo dõi (Monitoring) sẽ rình rập các lỗi: độ trễ ghi (write latency) > 500ms (vi phạm SLA), độ trễ đồng bộ dữ liệu (data consistency lag) > 5s, số tin nhắn kẹt trong `migration.dlq` > 0 (bất kỳ cú sync nào xịt cũng cần phải lôi ra điều tra trước khi được phép đi tiếp).

### Bước 2: Catalog Service (Rủi ro Trung Bình)

Chỉ được chạy sau khi Customer Service đã êm ru (stable) trong suốt 72 giờ:

```bash
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"catalog_write": "true"}}'

./scripts/monitor-dual-write.sh --service=catalog --duration=1800
./scripts/validate-dual-write.sh --service=catalog --sample=500
```

Catalog nằm ở nhóm rủi ro trung bình vì dữ liệu sản phẩm ít nhạy cảm hơn dữ liệu đơn hàng — một mô tả sản phẩm bị lệch lạc trong thoáng chốc có thể gây ngứa mắt, nhưng không gây thiệt hại về mặt tài chính (financially damaging).

### Bước 3: Order Service (Rủi ro Chạm Nóc)

Để di dời Order Service, bạn bắt buộc phải có một bản backup database (sao lưu) rõ ràng trước khi bấm nút bật:

```bash
#!/bin/bash
# RỦI RO CAO — Yêu cầu chữ ký xác nhận của CTO hoặc Tech Lead

echo "⚠️  Tính năng Ghi Kép (Dual-write) cho Order Service yêu cầu phải phê duyệt bằng tay"
read -p "Bạn đã tạo bản backup DB cho Magento trong vòng 30 phút đổ lại đây chưa? [yes/no]: " CONFIRM
[ "$CONFIRM" != "yes" ] && echo "Hủy lệnh. Đi backup đi đã." && exit 1

# Bật cờ với chế độ gắt gao (Stricter): cứ 10s check sức khỏe một lần, validate khắt khe
kubectl patch configmap feature-flags -n production \
  --patch '{
    "data": {
      "order_write": "true",
      "order_health_check_interval": "10",
      "order_strict_validation": "true"
    }
  }'

# Thời gian theo dõi kéo dài ra: 1 tiếng thay vì 30 phút
./scripts/monitor-dual-write.sh --service=order --duration=3600
./scripts/validate-dual-write.sh --service=order --sample=1000
```

Khoảng thời gian kiểm tra sức khỏe rụt lại còn 10 giây (so với 30 giây của Customer) có nghĩa là cơ chế tự động xả kèo (automatic fallback) của Order Service sẽ nhạy cò và kích hoạt nhanh hơn hẳn — yếu tố sống còn vì làm rơi mất một cái đơn hàng đồng nghĩa với việc khách hàng nổi điên và nguy cơ phải ói tiền ra hoàn trả (refund).

## 6. Theo dõi DLQ: Hệ Thống Cảnh Báo Sớm Của Bạn

Bất kỳ sự kiện (event) nào không thể đồng bộ sang Magento sẽ đều hạ cánh ở `migration.dlq`. Suốt Giai đoạn 2, cái DLQ này phải được coi là **vùng cấm không khoan nhượng (zero-tolerance)**. Nếu DLQ khác rỗng (non-empty), nghĩa là dữ liệu của bạn đã bị lệch (data inconsistency):

```bash
# Kiểm tra số lượng tin nhắn trong DLQ (Nên chạy kiểm tra vào đầu mỗi ca trực)
dapr publish --publish-app-id ops-tool --pubsub pubsub \
  --topic migration.dlq.stats --data '{}'

# Kết quả kỳ vọng: 0 messages
# Nếu > 0: đình chỉ mọi hoạt động, lôi ra điều tra bằng được trước khi cho phép bật cờ write của service tiếp theo
```

Một service DLQ handler sẽ đứng ra nhận nhiệm vụ xử lý các sự kiện bị xịt (failed events) và hú còi ầm ĩ (alerts) vào kênh Slack `#migration-issues`, đính kèm luôn nội dung của sự kiện đó (payload) và thông báo lỗi.

## 7. Tiêu Chí Nghiệm Thu Giai Đoạn 2

| Chỉ Số (Metric) | Mục Tiêu (Target) | Thời điểm Đo |
|---|---|---|
| Hiệu năng Ghi (Write performance) | < 500ms p99 | Theo dõi liên tục trên Prometheus |
| Độ trễ đồng bộ dữ liệu | < 5 giây đối với dữ liệu quan trọng | Cứ 15 phút check một lần bằng script consistency check |
| Số lượng tin nhắn trong DLQ | 0 | Phải check trước khi bật cờ write cho mỗi service |
| Thời gian tự động rollback | < 10 giây để xả về fallback | Được test thật kỹ trong các buổi diễn tập deploy (rehearsal) |
| Thời gian chết (Zero downtime) | 0 lỗi trên bất kỳ thao tác ghi nào | Xuyên suốt toàn bộ Giai đoạn 2 |

## Bước Tiếp Theo

Với Giai đoạn 2 đã hòm hòm, toàn bộ lệnh ghi (write) đều đâm thẳng vào microservice trước, sau đó mới đồng bộ ngược (sync back) lại Magento. Magento giờ đây đã chính thức giáng cấp xuống làm kẻ bám đuôi (follower), không còn là nguồn sự thật duy nhất (source of truth) nữa. Ở [Phần 8: Giai đoạn 3 — Chuyển Đổi Hoàn Toàn (Full Cutover)](/series/composable-commerce-migration/part-8-phase3-full-cutover/), chúng ta sẽ dập cầu dao tắt luôn cái luồng đồng bộ ngược (reverse sync), bẻ lái 100% traffic đổ xô vào microservice trong khi dựng Magento đứng ngó ở chế độ chờ nóng (hot standby), và hoàn tất việc rút ống thở (decommission) thông qua kỹ thuật ArgoCD GitOps.

## Câu Hỏi Thường Gặp (FAQ)

### Rủi ro lớn nhất của ghi kép (dual-write) là gì và cách tiếp cận này giải quyết nó ra sao?

Rủi ro lớn nhất chính là **thất bại cục bộ (partial failure)**: microservice ghi xong ngon ơ nhưng cái luồng sync sang Magento lại đứt gánh giữa đường, bỏ mặc dữ liệu hai bên vênh nhau móm mém. Mẫu thiết kế (pattern) hướng sự kiện (event-driven) giải bài toán này bằng kỹ thuật Transactional Outbox: cái sự kiện (event) nằm trong outbox được ghi vào database CÙNG CHUNG một giao dịch (transaction) với sự kiện biến đổi nghiệp vụ (business change). Trượt chân một cái là cả hai cùng xịt — xịt một cách đồng bộ (atomically). Sau đó, thằng `magento-sync-adapter` sẽ lầm lũi (asynchronously) gõ cửa thử lại (retries) cú sync đó với khoảng thời gian dãn cách tăng dần (exponential backoff), và những event bướng bỉnh vẫn xịt sẽ bị gắp bỏ vào DLQ chờ con người tới điều tra, chứ tuyệt đối không bao giờ có chuyện bị thất lạc trong im lặng (silently lost).

### Tại sao chính sách phân xử xung đột của Customer data lại khác với Order data?

Dữ liệu khách hàng (Customer data) có quyền được sửa chữa bởi cả hai hệ thống cùng một lúc (concurrently) một cách hoàn toàn hợp pháp — một khách hàng có thể lên storefront của Magento cập nhật địa chỉ nhà, trong khi cùng lúc đó một lệnh gọi API microservice lại đè sdt mới vào tài khoản của họ. Kiểu phân xử dựa trên Timestamp (Timestamp-based resolution) giải quyết ca này êm ru: cái update nào đến sau thì cái đó ăn. Dữ liệu Đơn hàng (Order data) thì lại là một phạm trù khác: một khi đơn hàng đã được đẻ ra trên microservice, Magento tuyệt đối KHÔNG ĐƯỢC PHÉP thò tay vào sửa trạng thái của nó nữa, bởi vì cỗ máy trạng thái (state machine) của microservice mới chính là nguồn sự thật duy nhất (authoritative source) cho vòng đời của đơn hàng. Đó là lý do tại sao trạng thái Đơn hàng lại xài cái chính sách microservices-thắng-chặt bất chấp timestamp.

### Giai đoạn 2 này thường kéo dài bao lâu?

Quỹ thời gian an toàn tối thiểu là **3–4 tuần** nếu bạn muốn mỗi service đều có đủ thời gian ngâm (monitoring time): Customer Service (1 tuần để êm), Catalog Service (1 tuần), và Order Service (10 ngày nhích từng tí một). Bất kỳ team nào ảo tưởng đòi dồn cục Phase 2 vào giải quyết trong vài ngày thường sẽ ăn đủ hành ngập mặt với mấy cái edge case (trường hợp hi hữu) lọt lưới bộ conflict resolver — nhất là mấy ca đếm số lượt xài coupon (usage counts) hay kẹt số lượng tồn kho (inventory levels) lúc bị gọi cập nhật đồng thời (concurrent updates). Kéo dài thời gian ra không phải là biểu hiện của căn bệnh quan liêu (bureaucracy); đó là khoảng thời gian quan sát (observation window) tối thiểu bắt buộc phải có để tóm cổ các dị thường (anomalies) trước khi chúng kịp phình to (compound) thành thảm họa.

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 6: Giai Đoạn 1 — Strangler Fig Read-Only](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 8: Giai Đoạn 3 — Full Cutover Zero Downtime →](/series/composable-commerce-migration/part-8-phase3-full-cutover/)
