---
title: "Part 4: gRPC Internal + REST Gateway — API Contract Lifecycle"
description: "Service-to-service gRPC communication, proto naming conventions, the Money type that prevents floating-point pricing bugs, cursor pagination, and how the Gateway Service bridges REST clients to internal gRPC services."
date: 2026-04-29T10:00:00+07:00
lastmod: 2026-06-24T10:00:00+07:00
draft: false
weight: 5
slug: "part-4-grpc-rest-gateway"
ShowToc: true
TocOpen: true
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["gRPC", "REST", "API Gateway", "Protobuf", "Golang", "Microservices", "API Design"]
series: ["Composable Commerce Migration"]
series_order: 4
author: "Lê Tuấn Anh"
---

Every public-facing API in the Composable Commerce Platform starts as a `.proto` file. The code — Go gRPC handlers, TypeScript SDK, HTTP routes, request validation, error codes — is generated from that contract. This article documents the conventions that make that system work.

**Answer-first:** Internal services communicate via gRPC (type-safe, binary, ~7× faster than JSON over REST). External clients (browser, mobile app) use REST via the Gateway Service (port 8000). The proto file is the single source of truth for the API contract — and three proto conventions require special attention for engineers coming from Magento: the Money type (never use float for prices), cursor-based pagination (never use offset), and proto-level field validation (validation declared in the contract, not in business logic).

## 1. Proto File: The Contract First

Before writing a single line of Go or TypeScript, the API contract is defined in proto3:

```protobuf
// api/order/v1/order.proto
syntax = "proto3";

package api.order.v1;

import "google/api/annotations.proto";       // HTTP gateway annotations
import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";
import "validate/validate.proto";            // Field-level validation rules

option go_package = "gitlab.com/ta-microservices/order-service/api/order/v1;orderv1";

// The gRPC service definition with HTTP annotations
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

The `(google.api.http)` annotations allow the Gateway Service to automatically generate HTTP ↔ gRPC translation. The same proto definition serves both transports: gRPC for internal service calls, REST for the external API.

## 2. Message Design: Three Conventions to Internalize

### Convention 1: The Money Type (Never Use Float)

This is the most surprising design decision for Magento engineers. In Magento, prices are stored as `decimal(12,4)` in MySQL and handled as PHP floats in code. In the proto API layer, we use a Google standard Money type:

```protobuf
// api/order/v1/order_types.proto

message Money {
    string currency_code = 1;   // ISO 4217: "VND", "USD", "THB"
    int64 units = 2;            // Whole monetary units
    int32 nanos = 3;            // Fractional part (0–999,999,999)
}
```

Why not `double` or `float`?

```
// The floating point problem:
0.1 + 0.2 = 0.30000000000000004  // In JavaScript and Go float64
// For an e-commerce platform, this is unacceptable.
// Promotional discount of 10% on 999,999 VND = 99,999.9 VND — not representable in float

// With Money type:
{ units: 999999, nanos: 900000000, currency_code: "VND" }
// Exact representation. No rounding error.
```

The conversion in Go:

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

### Convention 2: Cursor Pagination (Never Use Offset)

Magento's collection pagination uses `?page=1&per_page=20` — offset-based. The Composable Commerce Platform uses cursor-based pagination for all list endpoints:

```protobuf
message ListOrdersRequest {
    string customer_id = 1;
    int32 page_size = 2 [(validate.rules).int32 = {gte: 1, lte: 100}];
    string page_token = 3;   // Cursor from previous response (empty = first page)

    // Filter options
    OrderStatus status_filter = 4;
    google.protobuf.Timestamp created_after = 5;
}

message ListOrdersResponse {
    repeated Order orders = 1;
    int32 total_count = 2;
    string next_page_token = 3;   // Send back in next request's page_token
    string prev_page_token = 4;   // For backward navigation
}
```

Why cursor, not offset? Two reasons:

**1. Consistency**: Offset pagination can skip or duplicate records if data changes between page requests. Cursor pagination is stable — you always see the records that existed at the cursor position.

**2. Performance**: `SELECT * FROM orders OFFSET 10000 LIMIT 20` scans and discards 10,000 rows before returning 20. Cursor-based uses `WHERE id > $cursor_id ORDER BY id LIMIT 20` — efficient index seek.

For a merchant with 500,000 orders, page 500 of offset pagination executes a scan of 9,980,000 rows. Cursor pagination executes an index seek regardless of page number.

### Convention 3: Proto-Level Field Validation

Validation is declared in the proto file, not in business logic:

```protobuf
message CreateOrderRequest {
    // Required fields — validation enforced before handler is called
    string customer_id = 1 [(validate.rules).string.min_len = 1];
    repeated OrderItem items = 2 [(validate.rules).repeated.min_items = 1];
    Address shipping_address = 3 [(validate.rules).message.required = true];

    // Optional fields — no validation rule = optional
    string coupon_code = 5;
    string payment_method_id = 6;

    // Idempotency key — required for POST operations
    string request_id = 7 [(validate.rules).string.min_len = 1];
}
```

The `validate.Validator()` Kratos middleware (added to both HTTP and gRPC servers in Part 3) evaluates these rules before the handler is invoked. If `customer_id` is empty, the request is rejected with a 400 Bad Request before it reaches `internal/biz/`.

This means: **business logic assumes valid input**. No `if req.CustomerID == ""` guards needed in `biz/`. Validation is the contract's responsibility.

## 3. Enum Naming: The proto3 Default Value Rule

Magento status codes are strings: `"pending"`, `"processing"`, `"complete"`. Proto3 enums require a zero value that means "unspecified":

```protobuf
enum OrderStatus {
    ORDER_STATUS_UNSPECIFIED = 0;    // MUST be 0 — proto3 default value
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

Rule: **value 0 is always `UNSPECIFIED`**. This is because proto3 uses 0 as the default for unset enum fields. If `ORDER_STATUS_PENDING = 0`, you cannot distinguish "this field was set to PENDING" from "this field was not set at all."

The naming convention (`ORDER_STATUS_` prefix) prevents collisions when multiple enums are imported into the same Go package.

## 4. Error Handling: Machine-Readable Codes

```protobuf
// api/order/v1/order_errors.proto — machine-readable error codes
enum OrderErrorReason {
    ORDER_NOT_FOUND = 0;
    ORDER_ALREADY_CANCELLED = 1;
    INSUFFICIENT_STOCK = 2;
    CUSTOMER_NOT_FOUND = 3;
    INVALID_COUPON = 4;
    TOO_MANY_UNPAID_ORDERS = 5;
}
```

In Go:

```go
// Errors automatically map: Kratos error code → HTTP status → gRPC status
errors.NotFound("ORDER_NOT_FOUND", "order %s not found", orderID)
// → HTTP 404, gRPC NOT_FOUND
// → JSON: {"code": 404, "reason": "ORDER_NOT_FOUND", "message": "order xyz not found"}

errors.BadRequest("INSUFFICIENT_STOCK", "product %s has only %d units available",
    productID, available)
// → HTTP 400, gRPC INVALID_ARGUMENT

errors.Forbidden("PERMISSION_DENIED", "admin only endpoint")
// → HTTP 403, gRPC PERMISSION_DENIED
```

The `reason` field is what frontend code pattern-matches on:

```typescript
// apps/storefront/src/hooks/useOrder.ts
try {
    const order = await orderClient.createOrder(req);
} catch (err) {
    if (err.reason === "INSUFFICIENT_STOCK") {
        // Show stock warning, let user update cart
        showStockWarning(err.message);
    } else if (err.reason === "TOO_MANY_UNPAID_ORDERS") {
        // Redirect to unpaid orders page
        router.push("/account/orders?filter=unpaid");
    } else {
        // Generic error
        showErrorToast(err.message);
    }
}
```

## 5. The Gateway Service: REST → gRPC Bridge

External clients (browser, mobile) connect to the Gateway Service on port 8000 via HTTPS + JSON. The Gateway:

1. **Validates JWT** (checks signature, expiry, and permission scope)
2. **Rate limits** (per-IP and per-user limits via Redis)
3. **Routes** to the appropriate internal service via gRPC
4. **Transforms** gRPC errors to REST error responses
5. **Feature flag routing** (Phase 1: some routes go to Magento, others to microservices)

```
External Client (HTTPS/JSON)
    ↓
Gateway Service :8000 (JWT auth + rate limit)
    ↓ gRPC to :9001
Order Service (internal gRPC)
    ↓
PostgreSQL
```

The Gateway Service is the only service with a public IP. All other 20 services run in a private Kubernetes namespace with no external access.

Route configuration example:

```go
// gateway-service/internal/router/router.go
func setupRoutes(r *gin.Engine, clients *ServiceClients) {
    v1 := r.Group("/api/v1", middleware.JWT(), middleware.RateLimit())

    // Order routes → Order Service gRPC
    v1.POST("/orders",              handler.CreateOrder(clients.Order))
    v1.GET("/orders/:order_id",     handler.GetOrder(clients.Order))
    v1.GET("/orders",               handler.ListOrders(clients.Order))
    v1.POST("/orders/:id/cancel",   handler.CancelOrder(clients.Order))

    // Catalog routes → Catalog Service gRPC
    v1.GET("/products",             handler.ListProducts(clients.Catalog))
    v1.GET("/products/:sku",        handler.GetProduct(clients.Catalog))
}
```

## 6. Internal Service Discovery

Services discover each other using Kubernetes DNS (no separate service registry required for internal calls):

```go
// order-service: calling warehouse-service internally
import "google.golang.org/grpc"

conn, err := grpc.Dial(
    "warehouse-service.production.svc.cluster.local:9008",
    grpc.WithTransportCredentials(insecure.NewCredentials()),  // mTLS via Istio sidecar
    grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(4*1024*1024)),
)
warehouseClient := warehousev1.NewWarehouseServiceClient(conn)
```

The DNS pattern: `{service-name}.{namespace}.svc.cluster.local:{grpc-port}`

ADR-006 chose Consul for service discovery in multi-cluster scenarios — but for same-cluster communication (which is the common case), K8s DNS is simpler and faster. Consul handles cross-cluster and external service registration.

## 7. The Complete API Lifecycle

From `.proto` to browser response:

```
1. api/order/v1/order.proto       ← Define contract
         ↓ protoc + kratos-proto generate
2. api/order/v1/order.pb.go       ← Generated: Go message types
   api/order/v1/order_grpc.pb.go  ← Generated: Go gRPC server/client interfaces
   api/order/v1/order_http.pb.go  ← Generated: HTTP handler wiring
   packages/api-client/generated/ ← Generated: TypeScript SDK (via buf)
         ↓ service implements interface
3. internal/service/order.go      ← Implement OrderServiceServer interface
         ↓ registered in server
4. internal/server/grpc.go        ← gRPC server: :9001
   internal/server/http.go        ← HTTP server: :8001
         ↓ gateway routes
5. Gateway Service :8000          ← External REST entry point
         ↓ browser/mobile
6. apps/storefront/               ← Uses TypeScript SDK from packages/api-client
```

Any change to the `.proto` file propagates through the entire chain at **compile time**. Adding a required field to `CreateOrderRequest` immediately breaks the TypeScript SDK compilation — forcing the frontend team to handle the new field before the change can be deployed.

## What's Next

With the API contract layer established, we're ready for the migration itself. [Part 5: EAV Schema Migration](/series/composable-commerce-migration/part-5-eav-schema-migration/) is where most Magento migrations fail — the EAV schema's 40+ tables, instance-specific attribute IDs, and the integer→UUID identity mapping problem. We'll show the exact SQL extraction queries that work in production.

## FAQ

### How much faster is gRPC than REST+JSON for internal service calls?

In production microservices, gRPC is typically **3–7× faster** than REST+JSON for equivalent payloads. The gains come from two sources: binary Protobuf serialization (vs JSON text parsing) and HTTP/2 multiplexing (vs HTTP/1.1 per-request connection overhead). For the Checkout → Order → Warehouse call chain, this means ~15ms gRPC latency vs ~60–90ms REST+JSON latency for the same service logic — compounded across 3–4 service hops per checkout flow.

### Why use protobuf `google.api.http` annotations instead of a standalone grpc-gateway binary?

A standalone `grpc-gateway` binary adds a network hop: `Client → grpc-gateway → gRPC service`. The `google.api.http` annotation approach generates HTTP handlers that run inside the same Kratos process as the gRPC server — zero additional network hop. The Gateway Service (Gin-based, port 8000) handles auth and routing; once inside the cluster, the HTTP-to-gRPC translation happens in-process within each service. This eliminates a failure point and reduces latency by ~5–10ms per service call.

### What is the difference between cursor pagination and offset pagination for order history?

**Offset pagination:** `SELECT * FROM orders OFFSET 10000 LIMIT 20` — scans 10,000 rows to return 20. Slow at scale, and if orders are inserted between requests, you get duplicate or skipped rows.  
**Cursor pagination:** `SELECT * FROM orders WHERE id > $cursor ORDER BY id LIMIT 20` — index seek directly to the cursor position. Consistent (no duplicates/skips) and O(1) regardless of page number. For a merchant with 500,000 orders, cursor pagination is mandatory; offset pagination at page 500 is a full-table scan.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? â†’ [Book a 1:1 Architecture Consultation](/hire/)*
