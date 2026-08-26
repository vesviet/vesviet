---
title: "Phần 9: Transactional Outbox & Saga đảm bảo giao sự kiện"
date: 2026-06-03T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Cách chuỗi saga Checkout→Order→Payment vận hành: transactional outbox PostgreSQL, saga choreography, idempotency keys và circuit breaker."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Transactional Outbox", "Saga Pattern", "Choreography", "Idempotency", "Circuit Breaker", "PostgreSQL"]
series: ["composable-commerce-migration"]
weight: 10
slug: "part-9-outbox-saga"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-9-outbox-saga/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 9: Transactional Outbox & Saga đảm bảo giao sự kiện"
  relative: false
keywords: ["transactional outbox go", "saga choreography ecommerce", "checkout saga flow", "idempotency keys"]
---

[← Chương trước: Phần 8: Giai Đoạn 3 — Full Cutover Zero Downtime](/series/composable-commerce-migration/part-8-phase3-full-cutover/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 10: 24 Quyết Định Kiến Trúc (ADRs) →](/series/composable-commerce-migration/part-10-adr-walkthrough/)

---

> **Answer-first:** Xử lý giao dịch phân tán khi khách hàng đặt hàng bằng cách kết hợp Transactional Outbox pattern trong PostgreSQL và Saga Choreography qua Dapr Pub/Sub, đảm bảo tính nhất quán cuối cùng giữa Giỏ hàng, Đơn hàng, Thanh toán và Kho vận.

---

Khi một khách hàng bấm nút đặt hàng trên nền tảng Composable Commerce, có tới 7 sự kiện bắt buộc phải diễn ra theo chuỗi vắt ngang qua 4 service hoàn toàn độc lập: Tạo Đơn hàng (Order created) → Duyệt Thanh toán (Payment authorized) → Giữ chỗ Tồn kho (Stock reserved) → Kích hoạt Giao nhận (Fulfillment triggered) → Bắn Thông báo (Notification sent) → Cộng Điểm thưởng (Loyalty points awarded) → Tạo Mã vận đơn (Shipping label generated). Bất kỳ mắc xích nào trong số này cũng có thể đứt. Mạng có thể rớt. Database có thể sập. Một cái cổng thanh toán (payment gateway) của bên thứ ba có thể bị timeout.

Nếu không có một cơ chế đảm bảo độ tin cậy (reliability mechanism), chỉ cần tỷ lệ lỗi là 2% ở bất kỳ bước nào thì đồng nghĩa với việc sẽ có 2% tổng số đơn hàng bị kẹt lại ở một trạng thái lơ lửng, vênh váo (inconsistent state), buộc con người phải nhảy vào dọn rác bằng tay (manual intervention).

**Answer-first:** Để phá giải triệt để bài toán "ghi kép" (dual-write) theo tiêu chuẩn 2026, nền tảng sử dụng mô hình **Saga theo kiểu vũ đạo (choreography)** kết hợp **Transactional Outbox trên PostgreSQL** (thay vì phụ thuộc vào outbox có sẵn của Dapr). Sự kiện (events) được ghi vào bảng outbox một cách nguyên tử (atomically) trong cùng một transaction với nghiệp vụ. Việc relay (bốc sự kiện) được thực hiện bởi OutboxProcessor chạy ngầm (sử dụng tuyệt kỹ `SELECT ... FOR UPDATE SKIP LOCKED` của PostgreSQL để tránh đụng độ giữa các replicas), sau đó bắn lên Dapr PubSub. Dù CDC (Change Data Capture) với Debezium là lựa chọn phổ biến, giải pháp Polling + SKIP LOCKED vẫn tỏ ra vô cùng hiệu quả và dễ vận hành cho các team không muốn gồng gánh thêm hạ tầng Kafka Connect. Mọi event handler đều phải thiết kế lũy đẳng (idempotent) để hóa giải giao đúp (duplicate delivery), và bất kỳ lỗi nào đều tự động kích hoạt giao dịch đền bù (compensating transactions).

## 1. Tại Sao Lại Chọn Choreography Mà Không Phải Orchestration?

Có hai trường phái để triển khai (implementation) Saga:

**Orchestration (Nhạc trưởng)**: Dựng lên một service "Order Saga Orchestrator" đứng giữa làm trung tâm, lão này sẽ chỉ tay năm ngón ra lệnh (commands) cho từng service theo thứ tự và tự tay xử lý nếu có biến:
```
Orchestrator → "Giữ chỗ tồn kho đi" → Warehouse Service
Orchestrator ← "Đã giữ chỗ xong" ← Warehouse Service
Orchestrator → "Trừ tiền đi" → Payment Service
...
```

**Choreography (Vũ đạo)**: Các service tự động hét lên (emit) các domain event và những service khác hóng hớt được sẽ tự biết đường mà nhảy vào múa theo:
```
Order Service hét: "order.created"
  → Warehouse Service hóng được → giữ chỗ tồn kho → hét lại "warehouse.stock.reserved"
  → Payment Service hóng được → trừ tiền → hét lại "payment.captured"
  → Fulfillment Service hóng được → tạo tác vụ giao nhận → hét lại "fulfillment.created"
```

Nền tảng của chúng ta chọn theo phe **choreography** vì ba lý do:
1. Không có điểm mù chết người (no single point of failure - không có lão orchestrator nào sập là đi bụi cả đám)
2. Các service hoàn toàn cắt đứt quan hệ với nhau (fully decoupled) — Order Service thậm chí còn không thèm biết là Payment Service có tồn tại trên cõi đời này
3. Mỗi service tự do quyết định cách retry và xử lý lỗi của riêng mình mà không bị ai quản

Cái giá phải trả (The trade-off): việc rò lỗi (debugging) sẽ khoai hơn (truy vết một mớ sự kiện hỗn độn khó hơn nhiều so với việc đọc log của một lão orchestrator duy nhất). Nhưng đừng lo, đã có OpenTelemetry distributed tracing đứng ra dàn xếp — mỗi sự kiện đều cõng theo một cái mã `correlation_id` để xâu chuỗi (links) toàn bộ dây chuyền saga lại với nhau.

## 2. Luồng Chảy Của Order Saga

```
Khách hàng chốt đơn
        │
        ▼
┌─────────────────┐
│  Checkout Svc   │  Validate giỏ hàng, tính tổng tiền cuối cùng
│                 │  Gọi sang Order Service thông qua gRPC
└────────┬────────┘
         │ gRPC: CreateOrder
         ▼
┌─────────────────┐
│   Order Svc     │  Đẻ ra một order với trạng thái: PENDING
│                 │  Nhét một event vào outbox: "orders.order.created"
└────────┬────────┘
         │ Dapr Pub/Sub (bất đồng bộ - async)
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────┐                ┌─────────────────┐
│  Warehouse Svc  │                │   Payment Svc   │
│ Giữ chỗ Tồn kho │                │ Trừ tiền khách  │
│ Hét lên (Emits):│                │ Hét lên:        │
│ "stock.reserved"│                │ "payment.       │
└────────┬────────┘                │  captured"      │
         │                         └────────┬────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        │ Cả hai event đều bay về lại Order Service
                        ▼
               ┌─────────────────┐
               │   Order Svc     │  Trạng thái → CONFIRMED
               │                 │  Hét lên: "order.confirmed"
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  Fulfillment    │  Tạo nhiệm vụ nhặt hàng (picking task)
               │  Svc            │  Hét lên: "fulfillment.created"
               └────────┬────────┘
                        │
                        ├── Notification Svc → gửi email xác nhận cho khách
                        └── Loyalty Svc → cộng điểm thưởng
```

## 3. Transactional Outbox Tự Trồng Bằng PostgreSQL

Hệ thống cố tình tẩy chay (deliberately avoids) cái outbox component có sẵn của Dapr (`dapr-outbox`). Lý do: cái outbox của Dapr bị trói chặt (tightly coupled) vào hệ thống lưu trữ state (actor state store) của nó, làm phình to độ phức tạp khi vận hành (operational complexity) và che khuất tầm nhìn (reduces visibility) không cho ta thấy rõ cái gì đang nằm chờ trong outbox. Thay vào đó, ta chơi đồ tự chế bằng một cái bảng PostgreSQL cực kỳ giản dị:

```sql
-- migrations/00005_create_outbox_events.sql
CREATE TABLE outbox_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic           VARCHAR(256) NOT NULL,     -- vd: "orders.order.created"
    payload         JSONB NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    retry_count     INT NOT NULL DEFAULT 0,
    last_error      TEXT,
    correlation_id  UUID,                       -- Cuộn dây xâu chuỗi các event của saga để trace
    
    -- Index giúp outbox processor mò tìm cho lẹ
    CONSTRAINT outbox_status_check CHECK (status IN ('PENDING', 'DELIVERED', 'FAILED'))
);

CREATE INDEX idx_outbox_pending ON outbox_events (status, created_at)
WHERE status = 'PENDING';
```

Bí kíp cốt lõi (critical pattern) ở đây là: **sự kiện outbox (outbox event) phải được INSERT vào CÙNG CHUNG một transaction với cái thay đổi trạng thái nghiệp vụ (business state change)**:

```go
// order-service/internal/biz/order_usecase.go

func (uc *OrderUseCase) CreateOrder(ctx context.Context, order *Order) (*Order, error) {
    var created *Order

    err := uc.db.WithTx(ctx, func(tx *sql.Tx) error {
        var err error

        // 1. Ghi order vào bảng orders
        created, err = uc.repo.CreateWithTx(ctx, tx, order)
        if err != nil {
            return fmt.Errorf("creating order: %w", err)
        }

        // 2. Nhét luôn outbox event vào TRONG CÙNG MỘT transaction đó
        //    Nếu cái transaction này xịt (rolls back), thì cái event cũng bốc hơi theo — một cách đồng bộ (atomically)
        return uc.outbox.InsertWithTx(ctx, tx, outbox.Event{
            Topic:         "orders.order.created",
            CorrelationID: order.RequestID,  // Vừa dùng làm Idempotency vừa để tracing
            Payload: map[string]interface{}{
                "order_id":    created.ID,
                "customer_id": created.CustomerID,
                "items":       created.Items,
                "total":       created.Total,
                "created_at":  created.CreatedAt,
            },
        })
    })
    if err != nil {
        return nil, err
    }

    return created, nil
}
```

Nếu lệnh ghi `CreateOrder` vào database bị tạch (do đầy ổ cứng, vi phạm constraint, v.v.), transaction đó sẽ lập tức cuộn ngược (rolls back) — kéo theo việc cái outbox event chưa bao giờ được insert. Sẽ tuyệt đối không bao giờ có cái thứ gọi là "sự kiện ma" (phantom event) vô tình lọt ra ngoài thông báo về một cái đơn hàng không hề tồn tại.

## 4. OutboxProcessor: Bắn Sự Kiện Kèm Giấy Chứng Nhận Tới Nơi

Cục `common/worker` OutboxProcessor sẽ âm thầm chạy ngầm (background goroutine) trong lòng mỗi service:

```go
// order-service/cmd/order-service/main.go

processor := worker.NewOutboxProcessor(db, daprClient, worker.OutboxConfig{
    PollInterval: 500 * time.Millisecond,   // Cứ nửa giây lại lôi bảng ra ngó xem có event mới không
    BatchSize:    100,                       // Bốc một nắm 100 event mỗi mẻ
    MaxRetries:   5,                         // Ngoan cố 5 lần, nếu vẫn xịt thì phong ấn thành FAILED
    RetryBackoff: worker.ExponentialBackoff(1*time.Second, 16*time.Second),
})
processor.Start(ctx)
```

Vòng lặp của processor:

```go
// common/worker/outbox_processor.go

func (p *OutboxProcessor) processOnce(ctx context.Context) {
    // Vớt mấy cái event đang nằm chờ (Khóa cổ không cho các processor khác can thiệp)
    events, err := p.db.QueryWithLock(ctx, `
        SELECT id, topic, payload, correlation_id, retry_count
        FROM outbox_events
        WHERE status = 'PENDING'
        ORDER BY created_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED  -- Món võ đỉnh cao giúp nhiều con processor cày cùng lúc mà không dẫm chân lên nhau
    `, p.config.BatchSize)
    if err != nil { return }

    for _, event := range events {
        // Bắn lên Dapr PubSub (Nằm trên Redis Streams)
        err := p.daprClient.PublishEvent(ctx, "pubsub", event.Topic, event.Payload,
            dapr.PublishEventWithMetadata(map[string]string{
                "correlationId": event.CorrelationID.String(),
            }),
        )

        if err != nil {
            p.db.Exec(ctx, `
                UPDATE outbox_events
                SET retry_count = retry_count + 1,
                    last_error = $2,
                    status = CASE WHEN retry_count + 1 >= $3 THEN 'FAILED' ELSE status END
                WHERE id = $1
            `, event.ID, err.Error(), p.config.MaxRetries)
            continue
        }

        // Đóng dấu đã giao (delivered)
        p.db.Exec(ctx, `
            UPDATE outbox_events
            SET status = 'DELIVERED', processed_at = NOW()
            WHERE id = $1
        `, event.ID)
    }
}
```

Chân ái nằm ở cái lệnh `FOR UPDATE SKIP LOCKED`: nó cho phép hàng tá pod của Order Service cùng lao vào chạy OutboxProcessor một lúc (simultaneously) mà chẳng thèm xảy ra xung đột (conflicts). Con pod nào cũng tự bốc được một mẻ event riêng tư của mình.

## 5. Tính Lũy Đẳng (Idempotency): Khắc Tinh Của Giao Đúp (Duplicate Delivery)

Dapr PubSub chống lưng bằng Redis Streams mang đến lời hứa giao-ít-nhất-một-lần (at-least-once delivery) — tức là một sự kiện có nguy cơ bị gõ cửa giao tới 2 lần (dù hiếm, nhưng lúc kết nối mạng chập chờn phải retry thì hoàn toàn có thể xảy ra). Vì vậy, tất cả event handler phải tuyệt đối tuân thủ nguyên tắc lũy đẳng (idempotent):

```go
// warehouse-service/internal/biz/stock_usecase.go

func (uc *StockUseCase) HandleOrderCreated(ctx context.Context, event *events.OrderCreated) error {
    // Kiểm tra xem hình như mình xử lý cái event này rồi thì phải?
    if processed, _ := uc.dedup.Has(ctx, event.OrderID + ":stock-reserve"); processed {
        log.Debugf("Túm được event giao đúp của đơn hàng %s, skip nhẹ", event.OrderID)
        return nil
    }

    // Tiến hành: giữ chỗ tồn kho cho từng món hàng trong đơn
    for _, item := range event.Items {
        if err := uc.ReserveStock(ctx, item.ProductID, item.Quantity); err != nil {
            // Hết hàng mất rồi → hét toáng lên cái event đền bù (compensation event)
            return uc.events.Publish(ctx, "warehouse.stock.insufficient", &events.StockInsufficient{
                OrderID:   event.OrderID,
                ProductID: item.ProductID,
                Requested: item.Quantity,
            })
        }
    }

    // Đánh dấu là đã xử lý xong (TTL: 7 ngày — đủ sức bao trọn bất kỳ khung giờ retry nào)
    uc.dedup.Set(ctx, event.OrderID + ":stock-reserve", 7*24*time.Hour)

    // Bắn event báo tin vui
    return uc.events.Publish(ctx, "warehouse.stock.reserved", &events.StockReserved{
        OrderID: event.OrderID,
        Items:   event.Items,
    })
}
```

Kiểu định danh cho biến khử trùng lặp (deduplication key pattern): `{order_id}:{handler_name}`. Cách này bật đèn xanh cho nhiều tay handler trong cùng một service có thể xử lý độc lập cùng một sự kiện một cách hoàn toàn độc lập với nhau (vd: `order-123:stock-reserve` và `order-123:loyalty-check`).

## 6. Đền Bù (Compensation): Khi Saga Đứt Gánh Giữa Đường

Nếu pha giữ chỗ tồn kho vỡ lở (hết hàng) trong khi Payment Service lại nhanh tay trừ tiền cmnr, thì một dây chuyền đền bù (compensation chain) sẽ lập tức được kích hoạt:

```
warehouse.stock.insufficient (do Warehouse Svc hét lên)
        │
        ├──► Order Svc: đổi trạng thái → CANCELLED, hét lên "order.cancelled"
        │
        └──► Payment Svc: hóng được "order.cancelled" → ngoan ngoãn ói tiền ra (issue refund)
                          → hét lên "payment.refunded"
```

Mấy cái sự kiện đền bù (compensation events) này cũng được nhét vào transactional outbox nốt — đảm bảo giao hàng tận răng kể cả khi cái service chịu trách nhiệm đền bù hiện đang bận nằm thở chờ hồi sinh.

```go
// order-service/internal/biz/order_usecase.go

func (uc *OrderUseCase) HandleStockInsufficient(ctx context.Context, event *events.StockInsufficient) error {
    return uc.db.WithTx(ctx, func(tx *sql.Tx) error {
        // Hủy bỏ đơn hàng
        if err := uc.repo.UpdateStatusWithTx(ctx, tx, event.OrderID, OrderStatusCancelled); err != nil {
            return err
        }

        // Nhét luôn cái event đền bù vào TRONG CÙNG một transaction
        return uc.outbox.InsertWithTx(ctx, tx, outbox.Event{
            Topic: "orders.order.cancelled",
            Payload: map[string]interface{}{
                "order_id": event.OrderID,
                "reason":   "INSUFFICIENT_STOCK",
                "product_id": event.ProductID,
            },
        })
    })
}
```

Payment Service ngửi thấy mùi `orders.order.cancelled` là tự giác xì tiền ra trả (refund) tự động toàn phần — chẳng cần con người phải mó tay vào khóc lóc xử lý mấy ca kho hết hàng.

## 7. Khả Năng Chống Chịu (Resilience): Khiên Chắn Circuit Breaker + Retry

Gói `common/errors` được vũ trang tận răng với các khiên chắn (circuit breakers) cho toàn bộ các cuộc gọi ra bên ngoài (cổng thanh toán, API vận chuyển):

```go
// common/client/resilience.go — ép dùng cho toàn bộ các cuộc gọi service-to-service

// Cấu hình Circuit breaker (được chốt trong ADR-020)
cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    Name:        "payment-gateway",
    MaxRequests: 5,                           // Mở hé hé (half-open) cho 5 request đi qua thử
    Interval:    60 * time.Second,            // Cứ 60s là xí xóa đếm lại (Reset failure count)
    Timeout:     30 * time.Second,            // Phạt đứng yên 30s sau khi toang (open) rồi mới cho thử lại
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures >= 5 // Rớt 5 phát liên tiếp là giật nổ (Open) ngay
    },
})

// Chày cối thử lại (Retry) với khoảng thời gian dãn cách tăng dần (exponential backoff) (ADR-020)
retrier := retry.New(
    retry.WithMaxRetries(3),
    retry.WithBackoff(retry.ExponentialBackoff(1*time.Second, 16*time.Second)),
    retry.WithJitter(0.2),  // Trộn thêm ±20% độ lệch (jitter) để tránh hiện tượng hiệu ứng đàn trâu (thundering herd)
)
```

Các trạng thái của circuit breaker:
- **Đóng (Closed)** (bình thường): cứ gọi vô tư, không cản
- **Mở (Open)** (bị kích hoạt - tripped): thẳng tay đuổi về ngay lập tức (fail fast immediately), không cho ngâm chờ, saga tự kích hoạt đền bù
- **Nửa Mở (Half-Open)** (đang hồi phục - recovery): hé cửa cho 5 dũng sĩ (test requests) lọt qua, nếu sống sót trở về (succeed) → Đóng (Closed)

Nhờ trò này mà một cái cổng thanh toán chậm rề rề (slow payment gateway) sẽ không có cửa báo hại khiến mọi đơn hàng phải chịu ảnh hưởng bởi cảnh timeout 30 giây ròng rã — circuit breaker nếm đòn đủ 5 lần là nó sập cầu dao và bóp nghẹt mọi cuộc gọi mới trong suốt 30 giây (fail fast), rồi sau đó mới rón rén thử lại.

## 8. Distributed Tracing: Rình Dấu Vết Của Một Saga

Mọi sự kiện (event) đều phải cõng theo một cái `correlation_id` (được đúc ra ngay từ lúc checkout, rải đều (propagated) qua tất cả các event hậu bối):

```go
// Tất tần tật các event đều phải có mặt correlation_id để phục vụ tracing
type OrderCreated struct {
    OrderID       string    `json:"order_id"`
    CustomerID    string    `json:"customer_id"`
    CorrelationID string    `json:"correlation_id"`  // Xài chung một mã cho cả dòng họ nhà saga
    // ...
}
```

Mở Jaeger (OpenTelemetry) lên, nhét cái `correlation_id` vào ô search, và chiêm ngưỡng toàn bộ dòng thời gian hoàng tráng của saga (saga timeline):

```
Trace: order-saga-correlation-id-xyz
├── [0ms]    Checkout Service: Cuộc gọi gRPC CreateOrder
├── [12ms]   Order Service: CreateOrder (Ghi PostgreSQL + nhét outbox)
├── [14ms]   OutboxProcessor: Bắn sự kiện orders.order.created
├── [20ms]   Warehouse Service: Xử lý HandleOrderCreated (giữ chỗ tồn kho)
├── [25ms]   Payment Service: Xử lý HandleOrderCreated (Trừ tiền)
├── [180ms]  Payment Service: Chạy ProcessPayment (Gọi thẳng ra gateway ngoài)
├── [200ms]  Payment Service: Bắn sự kiện payment.captured
├── [22ms]   Warehouse Service: Bắn sự kiện warehouse.stock.reserved
├── [210ms]  Order Service: Xử lý HandlePaymentCaptured + HandleStockReserved
├── [215ms]  Order Service: Đổi trạng thái Status → CONFIRMED, Bắn sự kiện order.confirmed
└── [230ms]  Fulfillment Service: Xử lý HandleOrderConfirmed (Tạo xong nhiệm vụ nhặt hàng)
```

Tổng thời gian dọn dẹp trọn vẹn một mâm saga: ~230ms cho một đơn hàng xuôi chèo mát mái (không bị kẹt cổng thanh toán). Nếu cổng thanh toán trở chứng chậm chạp: tầm 2–5 giây. Còn nếu xui đến mức bị cái circuit breaker giật nổ: văng ra lỗi cái rầm (immediate failure) + kích hoạt chuỗi đền bù chỉ tốn có ~50ms.

## Tại Sao Tự Build Outbox Polling Thay Vì Dùng Dapr Hay Debezium CDC?

Dapr có outbox native và thị trường 2026 thì chuộng CDC (Change Data Capture) với Debezium. Nhưng nền tảng này lại tự build Outbox Polling trên PostgreSQL thủ công, vì ba nguyên nhân cốt lõi:

1. **Khả năng Giám sát (Visibility) & Kiểm soát (Control)**: Với polling, chỉ cần `SELECT * FROM outbox_events WHERE status = 'FAILED'` là tìm ra ngay các sự kiện tắc nghẽn. Ta dễ dàng can thiệp, chỉnh sửa số lần thử lại (retries) hoặc reprocess bằng tay. Dapr giấu state vào actor, còn Debezium cần phải lôi công cụ quản trị Kafka ra soi (phức tạp hơn nhiều).

2. **Đơn giản hóa Hạ tầng (Infra Simplicity)**: CDC yêu cầu phải nuôi thêm cụm Kafka Connect và Debezium workers. Với đội ngũ nhỏ hoặc hệ thống chưa cần scale đến mức hàng vạn TPS, việc tự build worker chạy ngầm ngay trong pod của service tiết kiệm hàng núi chi phí vận hành.

3. **Tuyệt kỹ Đồng bộ (Atomicity) với PostgreSQL**: Tính năng `FOR UPDATE SKIP LOCKED` đóng vai trò rào chắn hoàn hảo, cho phép hàng chục replicas cùng poll outbox mà không xảy ra tranh chấp dữ liệu (row contention), xử lý dứt điểm bài toán đồng bộ mà không cần hệ thống khóa phân tán (distributed lock).

Cái giá phải trả: Mọc ra thêm đống code bắt bạn phải duy trì (`common/worker/outbox_processor.go`). Tuy nhiên, đóng gói nó thành một thư viện dùng chung `common/worker` sẽ mang lại sự trơn tru cho toàn bộ ecosystem microservice.

## Bước Tiếp Theo

[Phần 10: Dạo Quanh ADR (ADR Walkthrough)](/series/composable-commerce-migration/part-10-adr-walkthrough/) sẽ lôi hết 24 bản Quyết định Kiến trúc (Architecture Decision Records) ra ánh sáng — những tài liệu đanh thép chống lưng cho toàn bộ những cú chốt hạ công nghệ (technology choice) tầm cỡ nhất trên cái nền tảng này, từ chuyện "sao thà ôm Dapr chứ nhất quyết không chơi raw Kafka" cho đến "tại sao Kustomize lại vượt mặt Helm" hay "cớ gì bỏ Gin để theo go-kratos." Mỗi bản ADR là một lăng kính (window) soi thấu những trò đánh đổi (trade-offs) ma mảnh đã nhào nặn nên cái nền tảng mà bạn đang theo dõi.

## Câu Hỏi Thường Gặp (FAQ)

### Saga pattern vs two-phase commit — khi nào xài cái nào?

**Two-phase commit (2PC)** đứng ra thề thốt hứa hẹn tuân thủ nghiêm ngặt tính ACID xuyên suốt các hệ thống tài nguyên bị phân tán (distributed resources), nhờ vào việc giật dây đám bù nhìn dưới quyền (coordinator and participants) — kẹt nỗi, nó khóa mồm (blocks) toàn bộ vây cánh cho đến khi thằng coordinator phán quyết xong, chập chạp lê lết và dễ hẹo nếu tay coordinator đột tử. **Saga** thì linh động hơn, nó mang đến tính nhất quán sau cùng (eventual consistency) nhờ vào mấy trò đền bù (compensating transactions) mà không cần phải khóa mồm cả đám (without a global lock). Hãy xài 2PC khi: bạn khao khát một sự nhất quán đồng bộ tuyệt đối (synchronous consistency) và đủ sức ngậm đắng nuốt cay chịu được độ trễ (latency) 50–200ms cho từng giao dịch. Hãy xài Saga khi: bạn thèm khát thông lượng cao (high throughput), đám service của bạn thích tự do deploy riêng rẽ (independently deployable), hoặc bạn không có đủ kiên nhẫn để đợi một gã coordinator cà lăm cản đường (điển hình như mảng checkout thương mại điện tử, order processing). Đứng trước áp lực 10,000+ orders/ngày cõng theo mục tiêu xả lệnh dưới 100ms (sub-100ms latency targets), 2PC ngay từ đầu đã không có cửa (non-starter).

### Điểm khác bọt giữa Outbox pattern và Event Sourcing là gì?

**Event Sourcing** là cái trò nhồi nhét ghi nhớ toàn bộ (entire history) quá khứ biến đổi trạng thái thành một sớ sự kiện (events) — trạng thái hiện tại (current state) được nặn ra nhờ vào trò replay lại từ con số không (from the beginning). Mỗi thực thể (entity) đều được cấy một cái bảng log sự kiện chỉ-cho-phép-thêm (append-only); và dĩ nhiên chả có cái khái niệm bảng "trạng thái hiện tại" mồ côi (separate "current state" table) nào cả. **Còn Transactional Outbox** lại là cơ chế (mechanism) đưa thư bảo kê (delivery guarantee) — nó đóng dấu mộc đảm bảo mấy cái event (sự kiện) sẽ được phi đi chuẩn xác *ngay bên cạnh* màn lột xác của trạng thái gốc (primary state change), nhưng cái trạng thái gốc đó vẫn yên vị (stored normally) trong bảng cơ sở dữ liệu quan hệ đàng hoàng. Nền tảng này quẹt thẻ xài Outbox pattern (chứ thèm vào Event Sourcing): đám services vẫn chễm chệ xài mấy cái bảng `orders`, `products`, và `customers` bình thường cho trạng thái hiện tại (current state), kẹp thêm cái rơ moóc `outbox_events` đóng vai cò mồi đưa thư (delivery of state-change notifications) cho những anh em khác.

### Mấy cái Idempotency keys (từ khóa lũy đẳng) cản vụ chém tiền đúp (double-charging) kiểu gì khi payment bị retry?

Mỗi nhát cắm `CreateOrder` (tạo đơn hàng) đều được khắc kèm một cái `request_id` (được sinh ra (UUID generated) bởi phía client). Khi Payment Service ôm cái event `order.created`, nó sẽ hì hục nhét `{order_id}:{payment-capture}` vào bảng khử trùng lặp (deduplication table) kèm theo thời gian sống (TTL) 7 ngày. Nếu chẳng may cái event hãm tài kia lượn lờ tới lần 2 (do mạng mẽo retry), thì cú đáp trả lần 2 này sẽ bị đá văng (returns early) vì cái mã kia đã điểm chỉ trong bảng dedup mất tiêu — đoạn code trừ tiền (payment capture) chẳng thèm chạy (never runs). Thay vào đó, kết quả của lần trừ tiền ngon ăn hồi nãy sẽ được móc ra trả về. Cú chốt này cam kết đinh ninh (guarantees) rằng ví của khách chỉ bị chém đúng một phát đứt đuôi (exactly once), mặc cho Dapr PubSub có xả cái event đó bao nhiêu lần đi chăng nữa.

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 8: Giai Đoạn 3 — Full Cutover Zero Downtime](/series/composable-commerce-migration/part-8-phase3-full-cutover/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 10: 24 Quyết Định Kiến Trúc (ADRs) →](/series/composable-commerce-migration/part-10-adr-walkthrough/)
