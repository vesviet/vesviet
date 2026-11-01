---
title: "Part 4: gRPC Internal + REST Gateway — API Contracts"
date: 2026-04-29T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "High-performance gRPC internal communication, Protobuf conventions, Money type decimal safety, cursor pagination, and REST Gateway configuration."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["gRPC", "Protobuf", "Golang"]
series: ["composable-commerce-migration"]
weight: 5
slug: "part-4-grpc-rest-gateway"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-4-grpc-rest-gateway/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 4: gRPC Internal + REST Gateway — The API Contract Lifecycle"
  relative: false
keywords: ["grpc gateway", "protobuf contract lifecycle", "money pattern protobuf", "cursor pagination grpc"]
mermaid: true
---

[← Previous Chapter: Part 3: Go + Kratos v2 Framework Deep Dive](/series/composable-commerce-migration/part-3-golang-kratos/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 5: Migrating the Magento EAV Schema →](/series/composable-commerce-migration/part-5-eav-schema-migration/)

---

> **Answer-first:** Every API in the Composable Commerce system starts from a Protocol Buffers (`.proto`) contract, using gRPC for high-speed internal communication between services and gRPC-Gateway to automatically expose JSON REST endpoints for Web and Mobile applications.

---

Every public-facing API in the Composable Commerce platform starts from a `.proto` file. The code — including the gRPC handler functions written in Go, the TypeScript SDK, the HTTP routes, request validation, and the error codes — is all automatically generated from that contract. This article documents the conventions behind the scenes that keep the whole system running smoothly.

**Answer-first:** In a modern 2026 architecture, internal services talk to each other over gRPC (type-safe, binary format, roughly 7x faster than JSON over REST). External clients (browsers, mobile apps) use REST through a Gateway Service (using `grpc-gateway` or Connect by Buf, running on port 8000). The proto file is the Single Source of Truth for the API contract — it automatically generates OpenAPI 3.1 documentation, and there are three proto conventions that engineers coming from Magento must pay special attention to: the Money type (never use floats to store prices, to avoid rounding errors), cursor-based pagination (never use offsets, to guarantee O(1) performance), and field validation declared at the proto level (validation lives in the contract itself, not in the business logic).

## 1. The Proto File: The Contract Always Comes First

Before writing a single line of Go or TypeScript code, the API contract must be defined in proto3:

```protobuf
// api/order/v1/order.proto
syntax = "proto3";

package api.order.v1;

import "google/api/annotations.proto";       // Annotations for the Gateway's HTTP transcoding
import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";
import "validate/validate.proto";            // Field-level validation rules

option go_package = "gitlab.com/ta-microservices/order-service/api/order/v1;orderv1";

// gRPC service definition with HTTP annotations
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

The `(google.api.http)` annotations allow the Gateway Service to automatically generate the HTTP ↔ gRPC transcoding layer. A single proto definition can serve both transports: gRPC for internal service-to-service calls, and REST for the external API.

## 2. Message Design: Three Conventions You Must Know by Heart

### Convention 1: The Money Type (Never Use Floats)

This is the design decision that surprises Magento engineers the most. In Magento, prices are stored as `decimal(12,4)` in MySQL and handled as floats in PHP code. But at the proto API layer, we use Google's standard Money type:

```protobuf
// api/order/v1/order_types.proto

message Money {
    string currency_code = 1;   // ISO 4217 standard: "VND", "USD", "THB"
    int64 units = 2;            // Whole currency units
    int32 nanos = 3;            // Fractional part (0–999,999,999)
}
```

Why not use `double` or `float`?

```
// The fatal flaw of floating point:
0.1 + 0.2 = 0.30000000000000004  // True in JavaScript and Go's float64
// For an e-commerce platform, an error like this is Unacceptable.
// Try computing a 10% promotional discount on 999,999 VND = 99,999.9 VND — a number that cannot be represented exactly as a float

// With the Money type:
{ units: 999999, nanos: 900000000, currency_code: "VND" }
// Perfectly exact representation. No rounding errors, ever.
```

The conversion functions in Go:

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

Collection pagination in Magento uses `?page=1&per_page=20` — that is, offset-based pagination. The Composable Commerce platform uses cursor-based pagination for ALL list endpoints:

```protobuf
message ListOrdersRequest {
    string customer_id = 1;
    int32 page_size = 2 [(validate.rules).int32 = {gte: 1, lte: 100}];
    string page_token = 3;   // Cursor from the previous response (empty = first page)

    // Filter parameters
    OrderStatus status_filter = 4;
    google.protobuf.Timestamp created_after = 5;
}

message ListOrdersResponse {
    repeated Order orders = 1;
    int32 total_count = 2;
    string next_page_token = 3;   // Pass this back as page_token in the next request
    string prev_page_token = 4;   // For backward navigation
}
```

Why cursors instead of offset? Two reasons:

**1. Consistency**: Offset pagination can skip or duplicate records if the data changes while the user is moving between pages. Cursor pagination is stable — you always see exactly the records that existed up to the cursor position.

**2. Performance**: The query `SELECT * FROM orders OFFSET 10000 LIMIT 20` scans and... throws away 10,000 rows before returning 20. Cursor pagination instead uses `WHERE id > $cursor_id ORDER BY id LIMIT 20` — an extremely efficient index seek.

For a merchant with 500,000 orders, clicking through to page 500 with offset pagination forces the database to grind through 9,980,000 rows. With cursor pagination it is always a lightweight index seek, no matter which page you are on.

### Convention 3: Validate Fields at the Proto Level

Validation rules are declared directly in the proto file, not in the business logic:

```protobuf
message CreateOrderRequest {
    // Required fields — enforced before the handler is ever called
    string customer_id = 1 [(validate.rules).string.min_len = 1];
    repeated OrderItem items = 2 [(validate.rules).repeated.min_items = 1];
    Address shipping_address = 3 [(validate.rules).message.required = true];

    // Optional fields — no validation rule means optional
    string coupon_code = 5;
    string payment_method_id = 6;

    // Idempotency key — mandatory for POST commands
    string request_id = 7 [(validate.rules).string.min_len = 1];
}
```

Kratos's `validate.Validator()` middleware (wired into both the HTTP and gRPC servers in Part 3) evaluates these rules right before the handler runs. If the `customer_id` field is empty, the request is rejected with a 400 Bad Request before it ever gets close to the `internal/biz/` layer.

This has a major implication: **the business logic layer is always entitled to assume the input data is clean and valid**. No more stuffing the `biz/` layer with defensive checks like `if req.CustomerID == ""`. Validation has become the contract's responsibility.

## 3. Enum Naming: The Trap of Proto3 Default Values

Status codes in Magento are strings: `"pending"`, `"processing"`, `"complete"`. Proto3 enums require a zero value meaning "unspecified":

```protobuf
enum OrderStatus {
    ORDER_STATUS_UNSPECIFIED = 0;    // MUST be 0 — the proto3 default value
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

The iron rule: **the value 0 must ALWAYS be `UNSPECIFIED`**. The reason is that proto3 uses 0 as the default value for any unset enum field. If you assign `ORDER_STATUS_PENDING = 0`, you can no longer tell the difference between "this field is set to PENDING" and "this field has never been set at all."

The naming convention (with the `ORDER_STATUS_` prefix) prevents name collisions when multiple enums are imported into the same Go package.

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

When written in Go:

```go
// Errors are mapped automatically: Kratos error code → HTTP status → gRPC status
errors.NotFound("ORDER_NOT_FOUND", "order %s not found", orderID)
// → Returns: HTTP 404, gRPC NOT_FOUND
// → JSON: {"code": 404, "reason": "ORDER_NOT_FOUND", "message": "order xyz not found"}

errors.BadRequest("INSUFFICIENT_STOCK", "product %s has only %d left in stock",
    productID, available)
// → Returns: HTTP 400, gRPC INVALID_ARGUMENT

errors.Forbidden("PERMISSION_DENIED", "this endpoint is admin-only")
// → Returns: HTTP 403, gRPC PERMISSION_DENIED
```

The `reason` field is the code the frontend pulls out to pattern-match against and decide how to respond:

```typescript
// apps/storefront/src/hooks/useOrder.ts
try {
    const order = await orderClient.createOrder(req);
} catch (err) {
    if (err.reason === "INSUFFICIENT_STOCK") {
        // Show an out-of-stock warning and ask the user to update the cart
        showStockWarning(err.message);
    } else if (err.reason === "TOO_MANY_UNPAID_ORDERS") {
        // Send the user to their unpaid-orders page
        router.push("/account/orders?filter=unpaid");
    } else {
        // Generic error
        showErrorToast(err.message);
    }
}
```

## 5. The Gateway Service: The REST → gRPC Bridge

External clients (browsers, mobile apps) connect to the Gateway Service on port 8000 over HTTPS + JSON. The Gateway does the following:

1. **Validates JWT** (signature, expiry, and scope)
2. **Rate limits** (per-IP and per-user request limits, managed with Redis)
3. **Routes** into the correct internal service over gRPC
4. **Transforms** gRPC errors into the corresponding REST response errors
5. **Feature flag routing** (Phase 1: some routes are still served by Magento, others by the microservices)

```
External client (HTTPS/JSON)
    ↓
Gateway Service :8000 (JWT auth + rate limit)
    ↓ gRPC call to :9001
Order Service (internal gRPC)
    ↓
PostgreSQL
```

The Gateway Service is the ONLY service granted a public IP address. All 20 remaining services run inside a private Kubernetes namespace and refuse any inbound traffic from the outside.

Example route configuration:

```go
// gateway-service/internal/router/router.go
func setupRoutes(r *gin.Engine, clients *ServiceClients) {
    v1 := r.Group("/api/v1", middleware.JWT(), middleware.RateLimit())

    // Order routes → forwarded to Order Service over gRPC
    v1.POST("/orders",              handler.CreateOrder(clients.Order))
    v1.GET("/orders/:order_id",     handler.GetOrder(clients.Order))
    v1.GET("/orders",               handler.ListOrders(clients.Order))
    v1.POST("/orders/:id/cancel",   handler.CancelOrder(clients.Order))

    // Catalog routes → forwarded to Catalog Service over gRPC
    v1.GET("/products",             handler.ListProducts(clients.Catalog))
    v1.GET("/products/:sku",        handler.GetProduct(clients.Catalog))
}
```

## 6. Internal Service Discovery

Services find each other using Kubernetes DNS (there is no need to stand up a separate service registry for these internal calls):

```go
// order-service: calling warehouse-service internally
import "google.golang.org/grpc"

conn, err := grpc.Dial(
    "warehouse-service.production.svc.cluster.local:9008",
    grpc.WithTransportCredentials(insecure.NewCredentials()),  // mTLS is handled by the Istio sidecar
    grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(4*1024*1024)),
)
warehouseClient := warehousev1.NewWarehouseServiceClient(conn)
```

The DNS structure looks like: `{service-name}.{namespace}.svc.cluster.local:{grpc-port}`

ADR-006 selected Consul as the service discovery mechanism for multi-cluster scenarios — but for same-cluster interactions (by far the most common case), K8s DNS is both simpler and faster. Consul only steps in to handle service registration for cross-cluster and external traffic.

## 7. The Full API Lifecycle

From the `.proto` file to the browser response:

```
1. api/order/v1/order.proto       ← Contract definition
         ↓ run protoc + kratos-proto generate
2. api/order/v1/order.pb.go       ← Generated: Go message types
   api/order/v1/order_grpc.pb.go  ← Generated: Go gRPC server/client interfaces
   api/order/v1/order_http.pb.go  ← Generated: HTTP handler stubs
   packages/api-client/generated/ ← Generated: TypeScript SDK (via buf)
         ↓ the service implements the interface
3. internal/service/order.go      ← Implements the OrderServiceServer interface
         ↓ registered with the server
4. internal/server/grpc.go        ← Starts the gRPC server: port :9001
   internal/server/http.go        ← Starts the HTTP server: port :8001
         ↓ gateway routes
5. Gateway Service :8000          ← External REST entry point
         ↓ browser/mobile
6. apps/storefront/               ← Consumes the TypeScript SDK from packages/api-client
```

Any tiny change in the `.proto` file instantly propagates through this entire chain at **compile time**. For example, if you add a required field to `CreateOrderRequest`, it will immediately break the TypeScript SDK build — forcing the frontend team to handle the brand-new field before the update can be deployed.

## Next Steps

With the API contract layer firmly in place, we are ready for the real migration itself. [Part 5: The EAV Schema Migration](/series/composable-commerce-migration/part-5-eav-schema-migration/) is the obstacle that knocks out most Magento migration projects — an EAV schema with more than 40 tables, attribute IDs specific to each individual instance, and the headache-inducing problem of converting identifiers from integers to UUIDs. We will show the raw SQL extraction queries that actually succeeded on production.

## Frequently Asked Questions (FAQ)

### How much faster is service-to-service gRPC than REST+JSON internally?

In production-grade microservice systems, gRPC is typically **3–7x faster** than REST+JSON for the same payload. The advantage comes from two sides: Protobuf's binary serialization (vastly better than parsing JSON text) and HTTP/2 multiplexing (vastly better than HTTP/1.1's per-request connection overhead). Roughly speaking, for a Checkout → Order → Warehouse call chain, gRPC consumes around ~15ms of latency, while REST+JSON takes ~60–90ms for the same logical chain — and that gap compounds across every 3-4 cross-service calls in a checkout flow.

### Why use the `google.api.http` protobuf annotations instead of running a separate standalone `grpc-gateway` binary?

A standalone `grpc-gateway` binary adds an extra network hop: `Client → grpc-gateway → gRPC service`. The annotation approach generates HTTP handlers that run in the same Kratos process as the gRPC server — the network latency is zero. The Gateway Service (written in Gin, on port 8000) handles auth and routing; once a request is inside the cluster, the HTTP-to-gRPC translation happens in-process inside each service. This structure eliminates a critical failure point and saves roughly ~5–10ms of added latency per service call.

*2026 update (E-E-A-T context): While `grpc-gateway` remains the gold standard in the Go community, the trend since 2025 has been to consider **Connect (by Buf)** for greenfield projects, since Connect natively supports gRPC, gRPC-Web, and HTTP/JSON from a single server without generating complex proxy code, and it integrates smoothly with automatic OpenAPI 3.1 generation via `protoc-gen-openapiv2`.*

### For order history, how does cursor pagination differ from offset pagination?

**Offset pagination:** `SELECT * FROM orders OFFSET 10000 LIMIT 20` — grinds through and discards 10,000 rows just to fetch 20. Extremely slow at scale, and if someone creates an order while the user is moving between pages, you get duplicated or skipped records.  
**Cursor pagination:** `SELECT * FROM orders WHERE id > $cursor ORDER BY id LIMIT 20` — an index seek that dives straight to the cursor position. Extremely accurate (no gaps, no duplicates) with O(1) complexity no matter the page number. For a merchant with 500,000 orders, cursor pagination is mandatory; using offset pagination to jump to page 500 is effectively asking the database for a full-table scan.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full table of contents for the complete architectural context.*

*Need help assessing the risks of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 3: Go + Kratos v2 Framework Deep Dive](/series/composable-commerce-migration/part-3-golang-kratos/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 5: Migrating the Magento EAV Schema →](/series/composable-commerce-migration/part-5-eav-schema-migration/)
