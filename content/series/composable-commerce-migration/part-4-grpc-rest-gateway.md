---
title: "Phần 4: gRPC Internal + REST Gateway — Vòng đời của Hợp đồng API"
date: 2026-04-29T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Giao tiếp gRPC internal, quy ước proto, kiểu Money chống sai số thập phân, phân trang cursor, và cách cấu hình REST Gateway cho client."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["gRPC", "Protobuf", "gRPC Gateway", "API Contract", "Golang", "REST"]
series: ["composable-commerce-migration"]
weight: 5
slug: "part-4-grpc-rest-gateway"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-4-grpc-rest-gateway/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 4: gRPC Internal + REST Gateway — Vòng đời của Hợp đồng API"
  relative: false
keywords: ["grpc gateway", "protobuf contract lifecycle", "money pattern protobuf", "cursor pagination grpc"]
---

[← Chương trước: Phần 3: Go + Kratos v2 Framework Deep Dive](/series/composable-commerce-migration/part-3-golang-kratos/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 5: Chuyển Đổi Schema EAV Magento →](/series/composable-commerce-migration/part-5-eav-schema-migration/)

---

> **Answer-first:** Mọi API trong hệ thống Composable Commerce khởi đầu từ hợp đồng Protocol Buffers (`.proto`), sử dụng gRPC cho giao tiếp nội bộ tốc độ cao giữa các services và gRPC-Gateway để tự động phơi bày REST endpoints JSON cho ứng dụng Web và Mobile.

---

Mọi API hướng ra công chúng (public-facing) trong Nền tảng Composable Commerce đều bắt đầu từ một file `.proto`. Phần code — bao gồm các hàm handler gRPC viết bằng Go, TypeScript SDK, các route HTTP, kiểm tra tính hợp lệ của request (request validation), các mã lỗi — tất cả đều được tự động generate ra từ bản hợp đồng (contract) đó. Bài viết này sẽ ghi chép lại những quy ước đằng sau để hệ thống đó vận hành mượt mà.

**Answer-first:** Trong kiến trúc hiện đại năm 2026, các service nội bộ giao tiếp với nhau qua gRPC (type-safe - an toàn kiểu dữ liệu, dạng nhị phân, và nhanh hơn khoảng 7 lần so với dùng JSON qua REST). Các client bên ngoài (trình duyệt, ứng dụng di động) sẽ sử dụng REST thông qua Gateway Service (sử dụng `grpc-gateway` hoặc Connect by Buf, chạy ở cổng 8000). File proto là Nguồn Sự Thật Duy Nhất (Single Source of Truth) cho bản hợp đồng API — nó tự động sinh ra OpenAPI 3.1 documentation và có ba quy ước về proto đòi hỏi các kỹ sư chuyển từ Magento sang phải đặc biệt lưu tâm: kiểu dữ liệu Money (tuyệt đối không dùng float để lưu giá tiền nhằm tránh sai số), phân trang bằng con trỏ (tuyệt đối không dùng offset để đảm bảo O(1) performance), và validate các trường (field) ngay ở cấp độ proto (việc validate được khai báo thẳng vào hợp đồng, không viết trong logic nghiệp vụ).

## 1. File Proto: Hợp đồng Luôn Đi Trước

Trước khi viết bất kỳ dòng code Go hay TypeScript nào, hợp đồng API phải được định nghĩa bằng proto3:

```protobuf
// api/order/v1/order.proto
syntax = "proto3";

package api.order.v1;

import "google/api/annotations.proto";       // Các annotation để Gateway chuyển ra HTTP
import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";
import "validate/validate.proto";            // Các quy tắc validate ở cấp độ field

option go_package = "gitlab.com/ta-microservices/order-service/api/order/v1;orderv1";

// Định nghĩa dịch vụ gRPC kèm theo các annotation dành cho HTTP
service OrderService {
    rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse) {
        option (google.api.http) = {
            post: "/api/v1/orders"
            body: "*"
        };
    };

    rpc GetOrder (GetOrderRequest) returns (GetOrderResponse) {
        option (google.api.http) = {
            get: "/api/v1/orders/{order_id}"
        };
    };

    rpc ListOrders (ListOrdersRequest) returns (ListOrdersResponse) {
        option (google.api.http) = {
            get: "/api/v1/orders"
        };
    };

    rpc CancelOrder (CancelOrderRequest) returns (CancelOrderResponse) {
        option (google.api.http) = {
            post: "/api/v1/orders/{order_id}/cancel"
            body: "*"
        };
    };
}
```

Các annotation `(google.api.http)` cho phép Gateway Service tự động generate cơ chế biên dịch chéo HTTP ↔ gRPC. Cùng một bản định nghĩa proto có thể phục vụ cho cả hai phương thức giao tiếp (transport): gRPC dành cho các lời gọi nội bộ giữa các service, và REST dành cho API đối ngoại (external API).

## 2. Thiết kế Message: Ba Quy ước Bắt buộc Phải Nằm Lòng

### Quy ước 1: Kiểu dữ liệu Money (Tuyệt đối Không Dùng Float)

Đây là một quyết định thiết kế gây ngạc nhiên nhất đối với các kỹ sư Magento. Trong Magento, giá tiền được lưu ở định dạng `decimal(12,4)` trong MySQL và được xử lý dưới dạng số thực (float) trong code PHP. Nhưng ở tầng proto API, chúng tôi dùng kiểu dữ liệu Money chuẩn của Google:

```protobuf
// api/order/v1/order_types.proto

message Money {
    string currency_code = 1;   // Chuẩn ISO 4217: "VND", "USD", "THB"
    int64 units = 2;            // Đơn vị tiền tệ làm tròn
    int32 nanos = 3;            // Phần thập phân (0–999,999,999)
}
```

Tại sao không xài `double` hay `float`?

```
// Lỗ hổng chết người của số dấu phẩy động (floating point):
0.1 + 0.2 = 0.30000000000000004  // Áp dụng trong JavaScript và kiểu float64 của Go
// Đối với một nền tảng thương mại điện tử, lỗi thế này là Không Thể Chấp Nhận.
// Thử tính chiết khấu khuyến mãi 10% cho số tiền 999,999 VND = 99,999.9 VND — con số này không thể biểu diễn chính xác bằng kiểu float

// Nếu dùng kiểu Money:
{ units: 999999, nanos: 900000000, currency_code: "VND" }
// Biểu diễn chính xác tuyệt đối. Không bao giờ phát sinh lỗi làm tròn.
```

Hàm chuyển đổi trong Go:

```go
// common/money/money.go
func FromFloat(currency string, amount float64) *moneyv1.Money {
    units := int64(amount)
    nanos := int32(math.Round((amount - float64(units)) * 1e9))
    return &moneyv1.Money{CurrencyCode: currency, Units: units, Nanos: nanos}
}

func ToFloat(m *moneyv1.Money) float64 {
    return float64(m.Units) + float64(m.Nanos)/1e9
}

// $59.98 = { currency_code: "USD", units: 59, nanos: 980000000 }
// 99,999 VND = { currency_code: "VND", units: 99999, nanos: 0 }
```

### Quy ước 2: Phân trang bằng con trỏ - Cursor Pagination (Tuyệt đối Không Dùng Offset)

Phân trang danh sách (collection) trong Magento dùng kiểu `?page=1&per_page=20` — tức là phân trang dựa trên offset. Nền tảng Composable Commerce sử dụng phân trang bằng con trỏ (cursor-based pagination) cho TOÀN BỘ các endpoint trả về danh sách:

```protobuf
message ListOrdersRequest {
    string customer_id = 1;
    int32 page_size = 2 [(validate.rules).int32 = {gte: 1, lte: 100}];
    string page_token = 3;   // Nhận cursor từ response trước đó (bỏ trống = trang đầu tiên)

    // Các tham số Filter (lọc)
    OrderStatus status_filter = 4;
    google.protobuf.Timestamp created_after = 5;
}

message ListOrdersResponse {
    repeated Order orders = 1;
    int32 total_count = 2;
    string next_page_token = 3;   // Gửi cái này ngược lại vào page_token của request tiếp theo
    string prev_page_token = 4;   // Dành cho việc bấm lùi (backward navigation)
}
```

Tại sao phải dùng con trỏ, mà không xài offset? Có hai lý do:

**1. Tính nhất quán (Consistency)**: Phân trang Offset có thể gây ra hiện tượng bỏ sót (skip) hoặc lặp lại (duplicate) bản ghi nếu dữ liệu trong hệ thống thay đổi ngay giữa lúc người dùng chuyển trang. Phân trang bằng con trỏ thì bất di bất dịch (stable) — bạn sẽ luôn luôn nhìn thấy những bản ghi đã tồn tại tính tới đúng vị trí của con trỏ đó.

**2. Hiệu năng (Performance)**: Câu truy vấn `SELECT * FROM orders OFFSET 10000 LIMIT 20` sẽ quét qua và... vứt đi 10,000 dòng dữ liệu trước khi lấy ra 20 dòng. Trong khi đó, phân trang bằng con trỏ dùng `WHERE id > $cursor_id ORDER BY id LIMIT 20` — đây là một phép dò index (index seek) cực kỳ hiệu quả.

Đối với một nhà bán hàng (merchant) có 500,000 đơn hàng, việc bấm vào trang 500 nếu dùng offset sẽ buộc database phải cày ải (scan) 9,980,000 dòng. Còn phân trang bằng con trỏ thì luôn luôn là một phép dò index nhẹ hều bất kể số trang là bao nhiêu.

### Quy ước 3: Validate (Xác thực) Field Ngay ở Cấp độ Proto

Quy tắc validate được khai báo thẳng vào file proto, chứ không viết trong logic nghiệp vụ:

```protobuf
message CreateOrderRequest {
    // Các trường Bắt buộc (Required fields) — bị cưỡng chế kiểm tra trước cả khi gọi tới handler
    string customer_id = 1 [(validate.rules).string.min_len = 1];
    repeated OrderItem items = 2 [(validate.rules).repeated.min_items = 1];
    Address shipping_address = 3 [(validate.rules).message.required = true];

    // Các trường Không bắt buộc (Optional fields) — không khai rule validate = là optional
    string coupon_code = 5;
    string payment_method_id = 6;

    // Khóa Lũy đẳng (Idempotency key) — bắt buộc phải có cho các lệnh POST
    string request_id = 7 [(validate.rules).string.min_len = 1];
}
```

Thành phần `validate.Validator()` middleware của Kratos (đã được móc vào cả HTTP lẫn gRPC server ở Phần 3) sẽ đánh giá các bộ quy tắc này ngay trước khi handler được gọi chạy. Nếu trường `customer_id` bị rỗng, request sẽ bị đá về kèm lỗi 400 Bad Request trước cả khi nó kịp bén mảng tới thư mục `internal/biz/`.

Điều này mang một ý nghĩa lớn: **tầng logic nghiệp vụ luôn được quyền mặc định rằng dữ liệu đầu vào đã sạch sẽ hợp lệ (valid)**. Không cần phải nhét cả đống lệnh rào trước đón sau kiểu `if req.CustomerID == ""` trong tầng `biz/` nữa. Việc xác thực dữ liệu nay đã trở thành trách nhiệm của bản Hợp đồng.

## 3. Đặt tên Enum: Cái Bẫy của Giá trị Mặc định Proto3

Các mã trạng thái (status codes) trong Magento là các chuỗi string: `"pending"`, `"processing"`, `"complete"`. Enum trong Proto3 yêu cầu bắt buộc phải có một giá trị zero (số 0) mang ý nghĩa "chưa được xác định" (unspecified):

```protobuf
enum OrderStatus {
    ORDER_STATUS_UNSPECIFIED = 0;    // BẮT BUỘC phải là 0 — giá trị mặc định của proto3
    ORDER_STATUS_PENDING = 1;
    ORDER_STATUS_CONFIRMED = 2;
    ORDER_STATUS_PAYMENT_CAPTURED = 3;
    ORDER_STATUS_PROCESSING = 4;
    ORDER_STATUS_FULFILLMENT_STARTED = 5;
    ORDER_STATUS_SHIPPED = 6;
    ORDER_STATUS_DELIVERED = 7;
    ORDER_STATUS_COMPLETED = 8;
    ORDER_STATUS_CANCELLED = 9;
    ORDER_STATUS_REFUNDED = 10;
}
```

Luật thép: **giá trị 0 LUÔN LUÔN phải là `UNSPECIFIED`**. Lý do là vì proto3 sử dụng số 0 làm giá trị mặc định (default) cho những trường enum chưa được gán giá trị (unset). Nếu bạn gán `ORDER_STATUS_PENDING = 0`, bạn sẽ không thể nào phân biệt nổi giữa "trường này đang được set là PENDING" hay là "trường này hoàn toàn chưa được set cái gì cả."

Quy ước đặt tên (có kèm tiền tố `ORDER_STATUS_`) giúp ngăn chặn tình trạng xung đột tên gọi (collisions) khi bạn có nhiều enum khác nhau cùng được import vào chung một package của Go.

## 4. Xử lý Lỗi: Các Mã Dành cho Máy Đọc (Machine-Readable Codes)

```protobuf
// api/order/v1/order_errors.proto — Các mã lỗi dạng máy-đọc-được
enum OrderErrorReason {
    ORDER_NOT_FOUND = 0;
    ORDER_ALREADY_CANCELLED = 1;
    INSUFFICIENT_STOCK = 2;
    CUSTOMER_NOT_FOUND = 3;
    INVALID_COUPON = 4;
    TOO_MANY_UNPAID_ORDERS = 5;
}
```

Khi được viết trong Go:

```go
// Các lỗi sẽ tự động được ánh xạ: Mã lỗi Kratos → Mã HTTP status → Mã trạng thái gRPC
errors.NotFound("ORDER_NOT_FOUND", "không tìm thấy đơn hàng %s", orderID)
// → Trả ra: HTTP 404, gRPC NOT_FOUND
// → JSON: {"code": 404, "reason": "ORDER_NOT_FOUND", "message": "không tìm thấy đơn hàng xyz"}

errors.BadRequest("INSUFFICIENT_STOCK", "sản phẩm %s hiện chỉ còn %d món",
    productID, available)
// → Trả ra: HTTP 400, gRPC INVALID_ARGUMENT

errors.Forbidden("PERMISSION_DENIED", "endpoint này chỉ dành cho admin")
// → Trả ra: HTTP 403, gRPC PERMISSION_DENIED
```

Cái trường `reason` chính là cái mã (code) mà frontend sẽ lôi ra để đối chiếu (pattern-match) và đưa ra hướng xử lý:

```typescript
// apps/storefront/src/hooks/useOrder.ts
try {
    const order = await orderClient.createOrder(req);
} catch (err) {
    if (err.reason === "INSUFFICIENT_STOCK") {
        // Hiện cảnh báo hết hàng, yêu cầu người dùng cập nhật lại giỏ
        showStockWarning(err.message);
    } else if (err.reason === "TOO_MANY_UNPAID_ORDERS") {
        // Đá người dùng về trang danh sách đơn chưa thanh toán
        router.push("/account/orders?filter=unpaid");
    } else {
        // Lỗi chung chung (Generic error)
        showErrorToast(err.message);
    }
}
```

## 5. Gateway Service: Cây cầu nối REST → gRPC

Các client bên ngoài (trình duyệt, mobile app) sẽ kết nối vào Gateway Service ở cổng 8000 thông qua HTTPS + JSON. Gateway sẽ làm các việc sau:

1. **Xác thực JWT (Validates JWT)** (kiểm tra chữ ký, thời hạn, và phạm vi quyền hạn)
2. **Giới hạn tốc độ (Rate limits)** (giới hạn số request theo IP và theo User, được quản lý bằng Redis)
3. **Điều hướng (Routes)** vào đúng cái service nội bộ ở bên trong thông qua gRPC
4. **Chuyển đổi (Transforms)** các lỗi gRPC thành các lỗi REST response tương ứng
5. **Định tuyến theo cờ (Feature flag routing)** (Giai đoạn 1: một số route đẩy về Magento, số khác đẩy sang microservices)

```
Client bên ngoài (HTTPS/JSON)
    ↓
Gateway Service :8000 (JWT auth + rate limit)
    ↓ Bắn qua gRPC vào cổng :9001
Order Service (gRPC nội bộ)
    ↓
PostgreSQL
```

Gateway Service là dịch vụ DUY NHẤT được cấp một địa chỉ IP public. Toàn bộ 20 service còn lại đều chạy ngầm trong một namespace Kubernetes private và hoàn toàn không cho phép bất kỳ truy cập nào từ bên ngoài.

Ví dụ về cấu hình route:

```go
// gateway-service/internal/router/router.go
func setupRoutes(r *gin.Engine, clients *ServiceClients) {
    v1 := r.Group("/api/v1", middleware.JWT(), middleware.RateLimit())

    // Các route của Order → Bắn về gRPC của Order Service
    v1.POST("/orders",              handler.CreateOrder(clients.Order))
    v1.GET("/orders/:order_id",     handler.GetOrder(clients.Order))
    v1.GET("/orders",               handler.ListOrders(clients.Order))
    v1.POST("/orders/:id/cancel",   handler.CancelOrder(clients.Order))

    // Các route của Catalog → Bắn về gRPC của Catalog Service
    v1.GET("/products",             handler.ListProducts(clients.Catalog))
    v1.GET("/products/:sku",        handler.GetProduct(clients.Catalog))
}
```

## 6. Cơ chế Khám phá Service (Service Discovery) Nội bộ

Các service tìm thấy nhau bằng cách sử dụng Kubernetes DNS (hoàn toàn không cần phải dựng một service registry riêng biệt cho các cuộc gọi nội bộ này):

```go
// order-service: đang gọi sang warehouse-service trong nội bộ
import "google.golang.org/grpc"

conn, err := grpc.Dial(
    "warehouse-service.production.svc.cluster.local:9008",
    grpc.WithTransportCredentials(insecure.NewCredentials()),  // mTLS được lo bởi Istio sidecar
    grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(4*1024*1024)),
)
warehouseClient := warehousev1.NewWarehouseServiceClient(conn)
```

Cấu trúc DNS có dạng: `{service-name}.{namespace}.svc.cluster.local:{grpc-port}`

Tài liệu ADR-006 đã chọn Consul làm service discovery cho các kịch bản chạy đa cụm (multi-cluster scenarios) — nhưng đối với các tương tác nằm trong cùng một cụm (same-cluster - vốn là trường hợp phổ biến nhất), dùng K8s DNS vừa đơn giản vừa nhanh hơn. Consul chỉ nhảy vào để lo việc đăng ký service cho các luồng giao tiếp ngoại cụm và bên ngoài (cross-cluster/external).

## 7. Vòng đời Hoàn chỉnh của API

Từ file `.proto` cho đến trình duyệt (browser) response:

```
1. api/order/v1/order.proto       ← Định nghĩa Hợp đồng
         ↓ chạy protoc + kratos-proto generate
2. api/order/v1/order.pb.go       ← File gen ra: Các kiểu dữ liệu Message trong Go
   api/order/v1/order_grpc.pb.go  ← File gen ra: Interface dành cho gRPC server/client trong Go
   api/order/v1/order_http.pb.go  ← File gen ra: Phác thảo luồng của HTTP handler
   packages/api-client/generated/ ← File gen ra: TypeScript SDK (nhờ buf)
         ↓ service tiến hành implement cái interface đó
3. internal/service/order.go      ← Implement cái OrderServiceServer interface
         ↓ đăng ký với server
4. internal/server/grpc.go        ← Khởi động gRPC server: cổng :9001
   internal/server/http.go        ← Khởi động HTTP server: cổng :8001
         ↓ Các route của gateway
5. Gateway Service :8000          ← Cánh cổng REST vào từ bên ngoài (External entry point)
         ↓ trình duyệt/mobile
6. apps/storefront/               ← Bắt đầu sử dụng TypeScript SDK từ packages/api-client
```

Bất cứ một sự thay đổi nhỏ nhoi nào nằm trong file `.proto` cũng sẽ lập tức lan truyền xuyên suốt toàn bộ chuỗi mắt xích này ngay tại **thời điểm biên dịch (compile time)**. Ví dụ, nếu bạn thêm một trường Required (bắt buộc) vào trong `CreateOrderRequest`, nó sẽ ngay lập tức bóp nát tiến trình biên dịch của cục TypeScript SDK — buộc đội ngũ frontend phải ngoan ngoãn xử lý cái trường mới toanh kia trước khi bản update có thể được deploy.

## Bước Tiếp Theo

Với lớp hợp đồng API đã được thiết lập chặt chẽ, chúng ta giờ đã sẵn sàng cho cuộc chuyển đổi thực sự. [Phần 5: Chuyển đổi Lược đồ (Schema) EAV](/series/composable-commerce-migration/part-5-eav-schema-migration/) chính là chướng ngại vật khiến phần lớn các dự án di dời khỏi Magento bị đánh gục — cấu trúc EAV schema với hơn 40 bảng, các ID thuộc tính (attribute IDs) tùy biến theo từng instance cụ thể, và bài toán đau đầu mang tên chuyển đổi mã định danh từ số nguyên (integer) sang chuỗi UUID. Chúng tôi sẽ trưng ra nguyên xi những câu SQL extraction thực sự đã thành công trên môi trường production.

## Câu Hỏi Thường Gặp (FAQ)

### Nội bộ các service gọi nhau bằng gRPC thì nhanh hơn gọi bằng REST+JSON cỡ bao nhiêu?

Trong các hệ thống microservice ở tầm production, gRPC thường nhanh hơn từ **3–7 lần** so với REST+JSON đối với cùng một khối lượng payload. Lợi thế này đến từ hai phía: quá trình tuần tự hóa dữ liệu nhị phân (binary serialization) của Protobuf (trội hơn hẳn so với việc còng lưng ngồi parse nội dung văn bản (text) của JSON) và cơ chế ghép kênh (multiplexing) của HTTP/2 (trội hơn hẳn chi phí khởi tạo kết nối (connection overhead) của HTTP/1.1 ở mỗi request). Tính sương sương chuỗi gọi hàm Checkout → Order → Warehouse, gRPC chỉ ngốn cỡ ~15ms độ trễ (latency), trong khi REST+JSON mất tới ~60–90ms cho cùng một chuỗi logic xử lý — và độ lệch này sẽ còn tăng theo cấp số nhân (compounded) qua mỗi nhịp 3-4 cú gọi hàm chéo nhau trong một luồng checkout.

### Tại sao lại xài annotation `google.api.http` của protobuf thay vì dựng hẳn một cục binary `grpc-gateway` đứng riêng độc lập?

Một cục binary `grpc-gateway` đứng riêng độc lập sẽ đẻ thêm một nhịp nhảy mạng (network hop) nữa: `Client → grpc-gateway → dịch vụ gRPC`. Còn cách làm xài annotation `google.api.http` sẽ tạo ra các HTTP handler nằm và chạy chung trong cùng cái Kratos process với cái gRPC server kia — độ trễ mạng phát sinh là bằng không (zero). Gateway Service (viết bằng Gin, nằm ở cổng 8000) gánh phần auth và phần route; khi request đã vào được bên trong cụm (cluster), quá trình dịch chép chéo (translation) từ HTTP-sang-gRPC sẽ xảy ra chạy ngầm (in-process) bên trong lòng mỗi service. Cấu trúc này triệt tiêu hẳn một điểm yếu trí mạng (failure point) và bớt đi được cỡ ~5–10ms tiền độ trễ cho mỗi lần service bị gọi (service call).

*Cập nhật 2026 (E-E-A-T Context): Mặc dù `grpc-gateway` vẫn là tiêu chuẩn vàng của cộng đồng Go, xu hướng mới từ năm 2025 là cân nhắc sử dụng **Connect (by Buf)** cho các dự án mới (greenfield) do Connect hỗ trợ bản địa cả gRPC, gRPC-Web, và HTTP/JSON từ cùng một server mà không cần gen ra proxy code phức tạp, đồng thời tích hợp mượt mà với tính năng gen OpenAPI 3.1 tự động bằng `protoc-gen-openapiv2`.*

### Lấy lịch sử mua hàng, vậy phân trang bằng con trỏ (cursor pagination) với phân trang bằng offset (offset pagination) khác nhau chỗ nào?

**Phân trang Offset:** `SELECT * FROM orders OFFSET 10000 LIMIT 20` — cày ải (scan) quét sạch 10,000 dòng chỉ để moi ra 20 dòng. Cực rùa bò ở quy mô lớn, và nếu trong lúc người dùng bấm chuyển trang có ai đó đang tạo thêm đơn hàng vào giữa chừng, bạn sẽ bị lấy dư (duplicate) hoặc lặp lại dữ liệu.  
**Phân trang Con trỏ (Cursor):** `SELECT * FROM orders WHERE id > $cursor ORDER BY id LIMIT 20` — index dò (index seek) phi thẳng cắm phập vào ngay vị trí con trỏ. Chuẩn xác cực kỳ (không dư thừa, không trùng lắp) và độ phức tạp tính toán O(1) bất kể trang nằm ở con số bao nhiêu. Đối với một nhà bán hàng có trong tay 500,000 đơn hàng, phân trang bằng con trỏ là quy tắc bắt buộc; nếu xài offset pagination để nhảy sang trang 500 thì chẳng khác nào bắt database phải thực hiện quét toàn bộ bảng (full-table scan).

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 3: Go + Kratos v2 Framework Deep Dive](/series/composable-commerce-migration/part-3-golang-kratos/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 5: Chuyển Đổi Schema EAV Magento →](/series/composable-commerce-migration/part-5-eav-schema-migration/)
