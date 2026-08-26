---
title: "Phần 3: Golang + Kratos v2 — Đi sâu vào Framework Microservice"
date: 2026-04-22T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Kiến trúc Go microservice chuẩn production với Kratos v2: cấu trúc 5 lớp, dependency injection bằng Wire, HTTP+gRPC transport và thư viện dùng chung."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Golang", "Kratos", "Microservices", "Wire", "Clean Architecture", "gRPC"]
series: ["composable-commerce-migration"]
weight: 4
slug: "part-3-golang-kratos"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-3-golang-kratos/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 3: Golang + Kratos v2 — Đi sâu vào Framework Microservice"
  relative: false
keywords: ["go kratos v2", "kratos 5 layer architecture", "google wire di", "kratos common library"]
---

[← Chương trước: Phần 2: Rush Monorepo 21 Go & Next.js Apps](/series/composable-commerce-migration/part-2-rush-monorepo/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 4: gRPC Internal + REST Gateway →](/series/composable-commerce-migration/part-4-grpc-rest-gateway/)

---

> **Answer-first:** Kiến trúc Go microservice chuẩn enterprise trên nền tảng Kratos v2 áp dụng mô hình 5 lớp nghiêm ngặt, dependency injection bằng Google Wire, hỗ trợ song song HTTP/REST và gRPC transport, cùng thư viện dùng chung chuẩn hóa logging và middleware.

---

Đối với các kỹ sư chuyển từ Magento PHP sang, việc chuyển dịch sang Go microservices không chỉ đơn thuần là đổi ngôn ngữ lập trình — mà nó là một cách thức tổ chức code khác biệt về mặt bản chất. Magento có controller, model, block, helper, và plugin. Còn Go với Kratos v3 (tối ưu hóa hoàn toàn cho Go 1.25) sở hữu chính xác 5 lớp (layer), mỗi lớp mang một trách nhiệm được định nghĩa rạch ròi.

**Answer-first:** Một Go microservice đạt chuẩn production trên nền tảng này tuân theo quy chuẩn thư mục của Kratos v3 (`api/ → cmd/ → internal/biz/ → internal/data/ → internal/server/`), sử dụng Google Wire để tiêm phụ thuộc lúc biên dịch (compile-time dependency injection), phơi bày (expose) cả HTTP và gRPC đồng thời trên các cổng (port) khác nhau (8xxx/9xxx), và import một bộ thư viện `common` dùng chung (đang ở version `v1.9.5`) chuyên cung cấp outbox, caching, worker, metrics, và logging — được tiêu chuẩn hóa trên toàn bộ 21 service.

## 1. Cấu trúc Thư mục 5 Lớp

Từng service một trong số 21 service đều tuân theo cùng một layout này:

```
order-service/
├── api/
│   └── order/
│       └── v1/
│           ├── order.proto           ← Định nghĩa gRPC + HTTP API
│           ├── order_types.proto     ← Các Enum dùng chung (OrderStatus, v.v.)
│           └── order_errors.proto    ← Các mã lỗi (Error codes)
│
├── cmd/
│   └── order-service/
│       ├── main.go                   ← Điểm neo đầu vào (Entry point)
│       ├── wire.go                   ← Khai báo tiêm phụ thuộc Wire (có build tag)
│       └── wire_gen.go               ← Tự động sinh ra bởi lệnh wire
│
├── internal/
│   ├── biz/                          ← Logic nghiệp vụ (use cases, domain entities)
│   │   ├── order.go                  ← Thực thể (Entity) Order + các quy tắc nghiệp vụ
│   │   ├── order_usecase.go          ← Use cases: CreateOrder, CancelOrder...
│   │   └── order_repo.go             ← Interface của Repository (chỉ định nghĩa, không phải bản implement)
│   │
│   ├── data/                         ← Truy cập dữ liệu (bản implement của repository)
│   │   ├── order_repo.go             ← Bản implement PostgreSQL
│   │   ├── order_cache.go            ← Tầng cache Redis
│   │   └── data.go                   ← Thiết lập kết nối DB, client Redis
│   │
│   ├── service/                      ← Các handler xử lý gRPC/HTTP
│   │   └── order.go                  ← Ánh xạ từ proto requests → biz use cases
│   │
│   └── server/
│       ├── grpc.go                   ← Server gRPC (port 9001)
│       └── http.go                   ← Server HTTP (port 8001)
│
├── migrations/
│   └── 00001_create_orders.sql       ← File migration của Goose
│
└── go.mod                            ← Module: gitlab.com/ta-microservices/order-service
```

**Vai trò của từng lớp:**

- **`api/`**: Nơi chứa Hợp đồng (Contract). Hãy định nghĩa proto của bạn ở đây trước — trước khi viết bất kỳ dòng code Go nào. Lớp này không chứa mã nguồn Go, chỉ có các file `.proto`.
- **`cmd/`**: Điểm neo đầu vào và cũng là gốc rễ để Wire thực hiện tiêm (injection). File `main.go` thường dài chưa tới 20 dòng. Toàn bộ việc khởi tạo được ủy thác cho Wire.
- **`internal/biz/`**: Logic nghiệp vụ thuần túy (Pure business logic). Không có lời gọi database nào, không có HTTP handler nào nằm đây. Các package trong biz chỉ import các kiểu dữ liệu của domain và *interface* của repository.
- **`internal/data/`**: Các bản implement thực sự của repository. Các câu truy vấn database sống ở đây. Đây là nơi thực hiện các tương tác với PostgreSQL, Redis, và đẩy sự kiện (event publishing) qua Dapr.
- **`internal/service/`**: Cây cầu nối giữa tầng giao tiếp (transport) và tầng logic nghiệp vụ. Lớp này nhận một proto request, gọi các use case trong biz, và trả về một proto response.
- **`internal/server/`**: Nơi thiết lập HTTP và gRPC server cùng với các middleware, và khởi động chúng lên.

Sự phân tách này không phải mang tính hình thức. Nó mang ý nghĩa: **tầng biz không bao giờ biết rằng nó đang chạy đằng sau gRPC**. Bạn có thể cắm thêm một transport dạng CLI, một queue consumer, hoặc một bộ test harness trực tiếp gọi vào `biz` — mà không cần phải thay đổi một dòng logic nghiệp vụ nào.

## 2. Wire: Tiêm phụ thuộc lúc Biên dịch (Compile-Time DI)

Trong Magento, container tiêm phụ thuộc (dependency injection container) hoạt động lúc chạy (runtime) — Magento sẽ dựng cây đồ thị DI khi ứng dụng khởi động, phân giải các dependency từ các file cấu hình XML. Cách này vừa chậm, dễ sinh lỗi, vừa đẻ ra những con bug mà chỉ khi chạy thực tế (runtime) mới chịu lòi ra.

Go Wire giải quyết vấn đề này ngay **lúc biên dịch (compile time)**. Cây đồ thị dependency được sinh ra dưới dạng code (code-generated) trước cả khi file nhị phân (binary) được build. Nếu thiếu mất một dependency nào, quá trình build sẽ bị lỗi (fail) ngay lập tức — thay vì ném ra lỗi lúc runtime.

Đây là cách nó hoạt động cho Order Service:

```go
// cmd/order-service/wire.go
//go:build wireinject
// +build wireinject

package main

import (
    "github.com/go-kratos/kratos/v2"
    "github.com/google/wire"

    "gitlab.com/ta-microservices/order-service/internal/biz"
    "gitlab.com/ta-microservices/order-service/internal/data"
    "gitlab.com/ta-microservices/order-service/internal/server"
    "gitlab.com/ta-microservices/order-service/internal/service"
)

func initApp(logger log.Logger, conf *conf.Bootstrap) (*kratos.App, func(), error) {
    wire.Build(
        data.ProviderSet,    // Kết nối DB, Redis, các bản implement repo
        biz.ProviderSet,     // Các Use case
        service.ProviderSet, // Các service handler cho gRPC/HTTP
        server.ProviderSet,  // Các server HTTP + gRPC
        newApp,
    )
    return nil, nil, nil
}
```

Chạy lệnh `wire ./cmd/order-service/` sẽ sinh ra file `wire_gen.go`:

```go
// cmd/order-service/wire_gen.go — CODE TỰ ĐỘNG SINH (AUTO-GENERATED), KHÔNG ĐƯỢC SỬA BẰNG TAY

func initApp(logger log.Logger, conf *conf.Bootstrap) (*kratos.App, func(), error) {
    db, cleanup, err := data.NewDatabase(conf.Data)
    if err != nil { return nil, nil, err }

    redisClient := data.NewRedisClient(conf.Data)
    orderRepo := data.NewOrderRepository(db, redisClient)

    orderUseCase := biz.NewOrderUseCase(orderRepo)

    orderService := service.NewOrderService(orderUseCase)

    grpcServer := server.NewGRPCServer(conf.Server, orderService, logger)
    httpServer := server.NewHTTPServer(conf.Server, orderService, logger)

    app, cleanup2, err := newApp(logger, grpcServer, httpServer)
    // ...
    return app, func() { cleanup2(); cleanup() }, nil
}
```

Không dùng reflection. Không có DI container ở runtime. Trình tự khởi tạo được quyết định ngay tại lúc biên dịch, và hệ thống type của Go đứng ra bảo lãnh (guarantee) rằng mọi dependency đều đã được thỏa mãn. Nếu bạn thêm một dependency mới vào `OrderUseCase` nhưng lại quên khai báo (provide) nó trong `ProviderSet`, lệnh `go build` sẽ đánh fail ngay.

## 3. Giao tiếp Kép: HTTP + gRPC trên các Port Khác nhau

Mỗi service đều phơi bày hai port (cổng) chạy đồng thời cùng lúc:

```go
// internal/server/grpc.go
func NewGRPCServer(c *conf.Server, os *service.OrderService, logger log.Logger) *grpc.Server {
    srv := grpc.NewServer(
        grpc.Address(c.Grpc.Addr),              // Cổng :9001
        grpc.Timeout(c.Grpc.Timeout.AsDuration()),
        grpc.Middleware(
            recovery.Recovery(),
            tracing.Server(),
            logging.Server(logger),
            validate.Validator(),               // Validate các field ở cấp độ proto
        ),
    )
    orderv1.RegisterOrderServiceServer(srv, os)
    return srv
}

// internal/server/http.go
func NewHTTPServer(c *conf.Server, os *service.OrderService, logger log.Logger) *http.Server {
    srv := http.NewServer(
        http.Address(c.Http.Addr),              // Cổng :8001
        http.Timeout(c.Http.Timeout.AsDuration()),
        http.Middleware(
            recovery.Recovery(),
            tracing.Server(),
            logging.Server(logger),
            jwt.Server(keyFunc),                // Validate JWT (chỉ áp dụng cho HTTP)
        ),
    )
    orderv1.RegisterOrderServiceHTTPServer(srv, os)
    return srv
}
```

Các annotation của proto tự động lo luôn phần sinh ra các HTTP route:

```go
// cmd/order-service/main.go
func newApp(logger log.Logger, gs *grpc.Server, hs *http.Server) (*kratos.App, func(), error) {
    app := kratos.New(
        kratos.Name("order-service"),
        kratos.Version("v1.0.0"),
        kratos.Logger(logger),
        kratos.Server(gs, hs),  // Cả hai server đều được đăng ký khởi chạy
    )
    return app, app.Stop, nil
}
```

**Quy ước về Port** (đồng nhất trên toàn bộ 21 service):
- HTTP: `8xxx` (ví dụ: Order = 8001, Payment = 8003, Catalog = 8005)
- gRPC: `9xxx` (ví dụ: Order = 9001, Payment = 9003, Catalog = 9005)

Quy ước này không phải được chọn bừa — mà là để dễ dò (discoverable). Bất kỳ kỹ sư nào biết port HTTP của một service thì sẽ lập tức biết ngay port gRPC của nó bằng cách cộng thêm 1000.

## 4. Tầng biz: Nơi Logic Nghiệp vụ Trú ngụ

Đây là nơi thực thi các công việc mang tính domain thực sự. Nếu so sánh với thuật ngữ của Magento, `biz` chính là sự kết hợp giữa Service Layer (service contracts) của bạn, các Model (thực thể domain), và bộ máy cưỡng chế các quy tắc nghiệp vụ — nhưng nó bị cô lập một cách cực kỳ nghiêm ngặt, tuyệt đối không dính dáng gì đến các thao tác I/O.

```go
// internal/biz/order.go

// Thực thể Domain (Domain entity) — không có annotation của ORM, không xài kiểu dữ liệu proto
type Order struct {
    ID         string
    CustomerID string
    Status     OrderStatus
    Items       []OrderItem
    Total      money.Money
    CreatedAt  time.Time
    UpdatedAt  time.Time
}

type OrderStatus string
const (
    OrderStatusPending   OrderStatus = "PENDING"
    OrderStatusConfirmed OrderStatus = "CONFIRMED"
    OrderStatusCancelled OrderStatus = "CANCELLED"
    // ... 5 trạng thái nữa
)

// Interface của Repository — tầng biz định ra hợp đồng, tầng data sẽ code bản implement
type OrderRepository interface {
    Create(ctx context.Context, order *Order) (*Order, error)
    FindByID(ctx context.Context, id string) (*Order, error)
    UpdateStatus(ctx context.Context, id string, status OrderStatus) error
    // ...
}
```

```go
// internal/biz/order_usecase.go

type OrderUseCase struct {
    repo     OrderRepository    // Trỏ tới Interface — chứ không phải bản implement PostgreSQL
    events   events.Publisher   // Từ thư viện dùng chung (common library)
    log      *log.Helper
}

func (uc *OrderUseCase) CreateOrder(ctx context.Context, order *Order) (*Order, error) {
    // Quy tắc nghiệp vụ: không được tạo đơn nếu khách hàng có lượng đơn chưa thanh toán > 3
    count, err := uc.repo.CountUnpaidByCustomer(ctx, order.CustomerID)
    if err != nil { return nil, err }
    if count >= 3 {
        return nil, errors.BadRequest("TOO_MANY_UNPAID_ORDERS",
            "khách hàng %s đang có %d đơn chưa thanh toán", order.CustomerID, count)
    }

    // Tạo vào trong DB (thông qua interface của repo)
    created, err := uc.repo.Create(ctx, order)
    if err != nil { return nil, err }

    // Bắn sự kiện domain (thông qua common/events)
    uc.events.Publish(ctx, "orders.order.created", &events.OrderCreated{
        OrderID:    created.ID,
        CustomerID: created.CustomerID,
        Items:      created.Items,
    })

    return created, nil
}
```

Lưu ý: `biz` hoàn toàn không có lệnh import nào dành cho `database/sql`, `pgxpool`, hay bất kỳ thư viện PostgreSQL nào. Nó chỉ phụ thuộc duy nhất vào các interface. Đó là lý do tại sao bạn có thể viết test cho tầng `biz` với một repository giả (mock) — mà không cần phải móc nối tới database thật.

## 5. Thư viện common (dùng chung): v1.9.5

Với 21 service, mỗi một design pattern mà bạn đẻ ra ở một service sẽ phải được lặp lại ở cả 21 chỗ. Nền tảng này giải quyết bài toán đó bằng một Go module dùng chung:

```go
// File go.mod của bất kỳ service nào
require gitlab.com/ta-microservices/common v1.9.5
```

Tài liệu ADR-023 ghi nhận rằng bản `common v1.9.5` đã loại bỏ được tới **4,150 dòng code thủ tục (boilerplate) lặp đi lặp lại** trên khắp 19 service nếu so với bản v1.0.0. Dưới đây là những gì có bên trong nó:

```
common/
├── cache/        ← Cache-Aside kèm theo cơ chế single-flight chặn bão truy vấn (stampede protection)
├── config/       ← Các tiện ích Config cho go-kratos
├── database/     ← Khởi tạo kết nối PostgreSQL, công cụ hỗ trợ Goose migration
├── events/       ← Đẩy sự kiện qua Dapr + tích hợp luồng outbox
├── middleware/   ← Các gRPC/HTTP middleware lo vụ Auth, logging, tracing
├── auth/         ← Validate JWT
├── logging/      ← Log có cấu trúc (Structured logging) đính kèm các ID truy vết (correlation IDs)
├── metrics/      ← Metrics Prometheus: đếm request, đo độ trễ, đo tỷ lệ lỗi
├── errors/       ← Các mã lỗi (error codes) được chuẩn hóa
├── validation/   ← Các tiện ích xác thực đầu vào (input validation)
├── worker/       ← Bộ xử lý Outbox + cron phân tán (dùng RedLock)
└── utils/        ← Các tiện ích linh tinh khác
```

**Package đáng tiền: `common/cache`**

```go
import "gitlab.com/ta-microservices/common/cache"

// Cache-Aside với cơ chế bảo vệ single-flight (ngăn bão cache - cache stampede)
product, err := cache.GetOrFetch(ctx, cache.Key("product", productID), func() (*Product, error) {
    return repo.FindByID(ctx, productID)
}, cache.TTL(1*time.Hour))
```

Nguyên thủy single-flight này đảm bảo rằng nếu có 1,000 request ập đến cùng lúc chọc vào cùng một cache key (vừa bị hết hạn), thì chỉ có **đúng một** câu query PostgreSQL được phép chạy. 999 request còn lại sẽ phải đứng chờ và nhận lại kết quả từ câu query đầu tiên kia. Nếu không có lớp khiên này, mỗi lần một cache bị hết hạn (expiry) ngay giữa mùa flash sale sẽ tạo ra một cơn bão kinh hoàng (thundering herd) đánh sập database.

**Package đáng tiền: `common/worker`**

```go
import "gitlab.com/ta-microservices/common/worker"

// Bộ xử lý Outbox (Outbox processor): quét bảng outbox_events và đẩy sang Dapr
processor := worker.NewOutboxProcessor(db, daprClient, worker.Config{
    PollInterval: 500 * time.Millisecond,
    BatchSize:    100,
    MaxRetries:   5,
})
processor.Start(ctx)

// Cron phân tán (RedLock): chạy một cron job trên đúng MỘT instance (bản thể) duy nhất
cron := worker.NewDistributedCron(redisClient)
cron.Schedule("0 * * * *", "cleanup-expired-carts", func(ctx context.Context) error {
    return cartRepo.DeleteExpired(ctx, 24*time.Hour)
})
```

## 6. Xử lý Lỗi trong Kratos: Hơn Cả HTTP Status Codes

Hệ thống xử lý lỗi của Magento ném ra các PHP exception, sau đó bắt (catch) lại và chuyển đổi thành HTTP response. Hệ thống lỗi của Kratos thì chuẩn xác hơn nhiều:

```go
import "github.com/go-kratos/kratos/v2/errors"

// Mỗi cái error đều cõng theo: mã HTTP status, mã máy đọc được (machine-readable), và lời nhắn cho người đọc
errors.NotFound("ORDER_NOT_FOUND", "không tìm thấy đơn hàng %s", orderID)
// → Trả ra: HTTP 404, grpc.Code = NOT_FOUND
// → JSON: {"code": 404, "reason": "ORDER_NOT_FOUND", "message": "không tìm thấy đơn hàng xyz"}

errors.BadRequest("INVALID_CUSTOMER_ID", "bắt buộc phải có customer_id")
// → Trả ra: HTTP 400, grpc.Code = INVALID_ARGUMENT

errors.Forbidden("PERMISSION_DENIED", "đòi hỏi quyền orders:delete")
// → Trả ra: HTTP 403, grpc.Code = PERMISSION_DENIED

errors.InternalServer("DB_ERROR", "database tạm thời không phản hồi")
// → Trả ra: HTTP 500, grpc.Code = INTERNAL
```

Trường `reason` (`ORDER_NOT_FOUND`) là cái mã dành cho máy đọc (machine-readable code). Code frontend sẽ đối chiếu (pattern-match) dựa trên trường `reason` này để đưa ra cách hành xử phù hợp (ví dụ: tự động văng về trang giỏ hàng nếu gặp mã `CART_EXPIRED`), trong khi trường `message` được dùng để hiển thị cho người dùng xem.

## 7. Cấu hình: go-kratos Config

Mỗi service đọc cấu hình (configuration) từ:
1. `configs/config.yaml` (cấu hình cơ sở, được commit thẳng vào repo)
2. Biến môi trường - Environment variables (từ Kubernetes ConfigMaps / Secrets)
3. Kho cấu hình của Dapr (Dapr Configuration store - dùng cho các feature flag chạy runtime)

```yaml
# configs/config.yaml
server:
  http:
    addr: ":8001"
    timeout: 30s
  grpc:
    addr: ":9001"
    timeout: 10s

data:
  database:
    source: "postgres://order_svc:${DB_PASS}@${DB_HOST}:5432/order_db?sslmode=require"
    max_open_conns: 20
    max_idle_conns: 10

  redis:
    addr: "${REDIS_ADDR}"
    db: 1  # Mỗi service xài một số DB Redis khác nhau
```

```go
// cmd/order-service/main.go
func main() {
    c := config.New(
        config.WithSource(
            file.NewSource("configs/config.yaml"),
            env.NewSource("APP_"),  // Quét các biến APP_DB_PASS, APP_REDIS_ADDR v.v.
        ),
    )
    var bc conf.Bootstrap
    c.Scan(&bc)
    // ...
}
```

## Những Điều Các Kỹ sư Magento Phải Học Cách "Quên Đi" (Unlearn)

Khi đến từ hệ sinh thái Magento, có bốn mô hình tư duy (mental models) bắt buộc phải thay đổi:

| Kiến trúc Magento | Kiến trúc Kratos v3 |
|---|---|
| Container DI được cấu hình trong `di.xml` | Wire sinh code DI ngay tại thời điểm biên dịch |
| Controller lo tuốt luồng HTTP + logic nghiệp vụ | Tầng `service/` lo bẻ HTTP; tầng `biz/` lo logic — hai thằng không bao giờ giẫm chân nhau |
| Model được quyền phi thẳng vào database | Các thực thể ở tầng `biz/` không có import database — việc đó là của tầng `data/` |
| Hệ thống plugin chạy thời gian thực (Plugins/Interceptors) | Không hề có chuyện chọc ngoáy chắp vá lúc runtime (monkey-patching); mọi sự chắp nối phải xảy ra lúc Wire thực thi việc tiêm |

Cấu trúc của Kratos cứng nhắc hơn nhiều so với sự linh hoạt của Magento — và đó chính là điểm cốt lõi. Sự cứng nhắc mang lại tính dễ đoán (predictability). Mỗi khi có kỹ sư mới gia nhập team, họ biết chính xác phải chui vào đâu để tìm logic nghiệp vụ (`internal/biz/`), truy vấn database (`internal/data/`), và ranh giới hứng API (`internal/service/`). Họ không còn phải bới tung các thư mục `Model/ResourceModel/`, `Block/`, `Helper/`, và `Plugin/` lên để tìm lỗi nữa.

## Bước Tiếp Theo

Với nội thất của một service đã được phơi bày rõ ràng, chúng ta có thể chuyển tầm ngắm sang tầng API: cách các service giao tiếp với nhau bằng gRPC, và cách Gateway Service phơi bày các endpoint REST cho client bên ngoài như thế nào. [Phần 4: Kiến trúc gRPC Internal + REST Gateway](/series/composable-commerce-migration/part-4-grpc-rest-gateway/) sẽ đi qua các quy chuẩn của protobuf, kiểu dữ liệu Money, kỹ thuật phân trang bằng con trỏ (cursor pagination), và toàn bộ vòng đời của một API từ file `.proto` cho đến khi biến thành HTTP response.

## Câu Hỏi Thường Gặp (FAQ)

### go-kratos so với Gin — cái nào nhanh hơn?

Gin nhỉnh hơn một chút về thông lượng HTTP thuần trong các bài test benchmark (độ trễ thấp hơn cỡ ~15–20% trong các bài test giả lập - synthetic tests). Nhưng đối với các microservice chạy trong thế giới thực, sự chênh lệch này là muối bỏ bể — database và độ trễ mạng (network latency) mới là kẻ làm chủ cuộc chơi, chứ không phải chi phí overhead của framework. Lợi thế áp đảo của go-kratos trước Gin nằm ở tính năng giao tiếp kép (dual transport): Kratos hứng được cả HTTP lẫn gRPC chung từ một file định nghĩa proto duy nhất. Gin bắt bạn phải nai lưng ra viết riêng từng bộ handler cho HTTP và từng bộ code server cho gRPC — làm khối lượng boilerplate (code thủ tục) cho mỗi endpoint tăng lên gấp đôi.

### Hệ thống tiêm phụ thuộc (dependency injection) bằng Wire khác gì so với DI chạy lúc runtime của Spring hay Magento?

Wire sinh code Go ngay lúc biên dịch (compile time) — hoàn toàn không có reflection, không có file cấu hình XML, và chẳng có cái DI container nào chạy ở runtime cả. Nếu bạn làm rớt mất một dependency (ví dụ: bạn thêm một tham số mới vào hàm khởi tạo nhưng lại quên update bộ Provider set), thì lệnh `go build` sẽ đánh fail ngay lập tức. Trong Spring hay Magento, cùng một lỗi y hệt đó sẽ chỉ chịu nhè ra một runtime exception — và thường là nó sẽ nổ cái bùm ngay trên môi trường production. Sự bảo lãnh ở cấp độ compile-time này của Wire chính là lý do cốt lõi khiến go-kratos chọn nó thay vì các giải pháp thay thế như dig (dùng DI runtime).

### Tôi có thể dùng một kratos service duy nhất để hứng cả REST và gRPC mà không cần phải cắm hai process server chạy riêng biệt không?

Có — đó chính xác là cái mà đoạn code `kratos.Server(gs, hs)` thực hiện. Cả server gRPC (cổng `:9001`) và server HTTP (cổng `:8001`) cùng chạy chung dưới dạng các goroutine nằm trong chung một process duy nhất. Chúng dùng chung một tầng `biz` và xài chung một pool kết nối (connection pool) database. Các annotation của proto (`google.api.http`) sẽ tự động gánh vác phần điều hướng chéo HTTP↔gRPC (routing) để bạn chỉ phải cắm đầu viết logic cho hàm handler đúng một lần duy nhất.

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 2: Rush Monorepo 21 Go & Next.js Apps](/series/composable-commerce-migration/part-2-rush-monorepo/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 4: gRPC Internal + REST Gateway →](/series/composable-commerce-migration/part-4-grpc-rest-gateway/)
