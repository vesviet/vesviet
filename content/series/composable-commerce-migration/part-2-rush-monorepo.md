---
title: "Phần 2: Rush Monorepo - Quản trị 21 Go & 2 Next.js Apps"
date: 2026-04-15T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Lý do Rush đánh bại Nx & Turborepo cho monorepo Go + Next.js: quản trị dependency, biên dịch tăng dần (incremental builds) và tự sinh TypeScript SDK."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Rush", "Monorepo", "Golang", "Next.js", "TypeScript SDK", "DevOps"]
series: ["composable-commerce-migration"]
weight: 3
slug: "part-2-rush-monorepo"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-2-rush-monorepo/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 2: Rush Monorepo - Quản trị 21 Go & 2 Next.js Apps"
  relative: false
keywords: ["microsoft rush monorepo", "go nextjs monorepo", "incremental builds", "proto code generation"]
---

[← Chương trước: Phần 1: Phân Rã Magento 21 Services bằng DDD](/series/composable-commerce-migration/part-1-ddd-bounded-contexts/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 3: Go + Kratos v2 Framework Deep Dive →](/series/composable-commerce-migration/part-3-golang-kratos/)

---

> **Answer-first:** Quản trị monorepo đa ngôn ngữ (21 Go microservices và 2 Next.js frontend) bằng Microsoft Rush giúp kiểm soát dependency nghiêm ngặt, thực hiện biên dịch tăng dần (incremental builds) và tự động sinh TypeScript SDK từ các file proto mà không bị xung đột phiên bản.

---

Khi bạn sở hữu 21 Go microservices và 2 ứng dụng frontend, câu hỏi hạ tầng đầu tiên không phải là Kubernetes hay CI/CD — mà là **làm thế nào để bạn quản lý chính bản thân phần source code?**

Hai lựa chọn sau sẽ thất bại ngay lập tức: polyrepo (hơn 21 repo Git rời rạc, bất khả thi để duy trì phiên bản đồng nhất) và một monorepo ngây ngô (vứt tất tần tật mọi thứ vào chung một thư mục, dependency ma ám ngập tràn). Bạn cần một công cụ quản lý monorepo thực thụ.

> **Lưu ý về phạm vi:** Rush quản lý lớp frontend (Next.js, các package TypeScript). Các Go microservice được quản lý độc lập thông qua `go.mod` và Go workspaces. Cấu trúc dưới đây phản ánh cách tiếp cận được khuyến nghị của nền tảng — hãy kiểm chứng lại các chi tiết cấu hình `rush.json` với thực tế kho lưu trữ của team bạn trước khi bê nguyên xi vào áp dụng.

**Answer-first:** Microsoft Rush là lựa chọn đúng đắn cho một nền tảng có yêu cầu quản trị dependency nghiêm ngặt, có sự pha trộn giữa Go services và TypeScript frontends, và có nhu cầu xuất bản các package nội bộ (như `api-client` TypeScript SDK được generate từ các định nghĩa Go protobuf của bạn). Bài viết này sẽ ghi chép lại cách thiết lập, cấu trúc thư mục, và điểm tích hợp then chốt giữa Go protos và các kiểu dữ liệu (types) của frontend.

## 1. Tại sao lại là Rush thay vì Nx hay Turborepo?

So sánh nhanh:

| Tính năng | Rush | Nx | Turborepo |
|---|---|---|---|
| **Quản trị Dependency** | ✅ `common-versions.json` — cưỡng chế (enforced) | ⚠️ Cấp độ project | ⚠️ Cấp độ project |
| **Ngăn chặn Phantom dependency** | ✅ Cô lập PNPM nghiêm ngặt | ⚠️ Có thể cấu hình | ✅ Nghiêm ngặt |
| **Đa ngôn ngữ (Go + TS)** | ✅ Custom bulk commands | ✅ Plugins | ⚠️ Thuần JS (native) |
| **Xuất bản (Publishing) package** | ✅ Lệnh `rush publish` xịn sò (first-class) | ⚠️ Cần cài plugin | ⚠️ Chạy tay (manual) |
| **Đường cong học tập (Learning curve)**| 🔴 Dốc (Steeper) | 🟡 Trung bình | 🟢 Thấp |
| **Công ty "chống lưng"** | Microsoft (Rush Stack) | Nrwl (đã bị VSHN mua lại)| Vercel |

Yếu tố mang tính quyết định đối với Nền tảng Composable Commerce: **`common-versions.json`**. Khi bạn có một storefront (trang cửa hàng) và một admin dashboard cùng consume (sử dụng) một package `api-client`, bạn không thể cho phép bên này chạy `react@19.0.0` còn bên kia chạy `react@19.1.0`. Rush cưỡng chế (enforces) các phiên bản dependency giống hệt nhau trên toàn bộ repo — trong khi Nx và Turborepo đòi hỏi bạn phải tự cấu hình việc này cho từng project.

Yếu tố thứ hai: hệ sinh thái PHP của Magento đã dạy chúng tôi cái giá phải trả cho những **bóng ma dependency (phantom dependencies)** — nơi mà một package chạy ngon ơ ở máy local vì nó tình cờ được cài đâu đó trong `node_modules`, nhưng lại "tạch" khi lên production bởi vì nó không phải là một dependency được khai báo chính thức. Sự cô lập nghiêm ngặt của Rush + PNPM ngăn chặn triệt để nhóm lỗi này.

## 2. Cấu trúc Repository

```
composable-commerce/               ← Thư mục gốc của monorepo
├── rush.json                      ← Cấu hình Rush: phiên bản pnpm, danh sách project
├── .npmrc                         ← Cấu hình PNPM
├── common/                        ← Do Rush quản lý (TUYỆT ĐỐI KHÔNG sửa bằng tay)
│   ├── config/
│   │   ├── rush/
│   │   │   └── common-versions.json   ← Chốt (pin) phiên bản cho toàn bộ dependency dùng chung
│   │   └── .npmrc
│   └── temp/                      ← Thư mục làm việc của Rush (đã gitignored)
│
├── apps/
│   ├── storefront/                ← Cửa hàng Next.js (SSR)
│   │   └── package.json
│   └── admin-dashboard/           ← Bảng điều khiển admin React
│       └── package.json
│
├── packages/
│   ├── ui-components/             ← Hệ thống thiết kế dùng chung (Radix + Tailwind)
│   │   └── package.json
│   ├── api-client/                ← TypeScript SDK sinh ra từ Go proto
│   │   ├── package.json
│   │   └── generated/             ← Code tự generate, không được sửa bằng tay
│   └── utils/                     ← Các hàm validate, format dùng chung
│       └── package.json
│
└── services/                      ← Các Go microservices (Rush quản lý việc build)
    ├── order-service/
    │   ├── go.mod
    │   └── ...
    ├── catalog-service/
    │   ├── go.mod
    │   └── ...
    └── ... (tổng cộng 21 service)
```

Ràng buộc quan trọng: `services/` chứa các module Go. Rush không quản lý `go.mod` — nó chỉ điều phối việc build thông qua các lệnh custom trong `rush.json` (bằng cách gọi shell chạy `go build`). Việc quản lý dependency của Go (`go mod tidy`, `go.sum`) hoàn toàn là một chuyện tách biệt.

## 3. Cấu hình rush.json

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/rush/v5/rush.schema.json",
  "rushVersion": "5.150.0",
  "pnpmVersion": "11.0.0",
  "nodeSupportedVersionRange": ">=20.0.0 <23.0.0",

  "projects": [
    { "packageName": "@composable/storefront",       "projectFolder": "apps/storefront" },
    { "packageName": "@composable/admin-dashboard",  "projectFolder": "apps/admin-dashboard" },
    { "packageName": "@composable/ui-components",    "projectFolder": "packages/ui-components" },
    { "packageName": "@composable/api-client",       "projectFolder": "packages/api-client" },
    { "packageName": "@composable/utils",            "projectFolder": "packages/utils" }
  ]
}
```

Các service Go được thêm vào dưới dạng các lệnh bulk (chạy hàng loạt) custom, chứ không phải với tư cách một project của Rush — bởi vì chúng đâu có file `package.json`:

```json
{
  "commands": [
    {
      "commandKind": "bulk",
      "name": "build:go",
      "description": "Biên dịch toàn bộ Go microservices",
      "enableParallelism": true,
      "allowWarningsInSuccessfulBuild": false,
      "shellCommand": "go build ./..."
    },
    {
      "commandKind": "bulk",
      "name": "test:go",
      "description": "Chạy unit test của Go",
      "shellCommand": "go test ./... -race -count=1"
    }
  ]
}
```

## 4. Quản trị Phiên bản Dependency

File `common/config/rush/common-versions.json` ghim (pin) các dependency dùng chung:

```json
{
  "preferredVersions": {
    "typescript":          "~5.5.0",
    "react":               "^19.0.0",
    "react-dom":           "^19.0.0",
    "next":                "^15.0.0",
    "@tanstack/react-query": "^5.50.0",
    "zod":                 "^3.24.0",
    "tailwindcss":         "^3.4.0",
    "@radix-ui/react-dialog": "^1.1.0"
  },
  "allowedAlternativeVersions": {}
}
```

Khi một developer chạy lệnh `rush add -p react@18.2.0` ở bất kỳ project nào, Rush sẽ từ chối nếu phiên bản ưu tiên (preferred version) đang là `^19.0.0`. Đây chính là tính năng quản trị quy mô doanh nghiệp giúp biện minh cho đường cong học tập dốc đứng của Rush.

## 5. Cầu nối api-client: Từ Go Proto → TypeScript

Đây là quyết định cấu trúc đáng giá nhất trong toàn bộ quy trình thiết lập monorepo: **các type TypeScript của bạn được tự động generate từ các định nghĩa Go proto**.

Luồng hoạt động:

```
services/order-service/api/order/v1/order.proto
    ↓ buf generate (buf.gen.yaml)
packages/api-client/generated/
    ├── order/v1/order_pb.ts          ← Các Message type của Proto
    ├── order/v1/order_connect.ts     ← ConnectRPC client (hoặc grpc-gateway)
    └── index.ts                      ← File xuất (Re-exports)
    ↓ rush build --to @composable/api-client
apps/storefront/                      ← import @composable/api-client
apps/admin-dashboard/                 ← import @composable/api-client
```

File `buf.gen.yaml` ở thư mục gốc của repo:

```yaml
version: v2
plugins:
  - plugin: es
    out: packages/api-client/generated
    opt: target=ts
  - plugin: connect-es
    out: packages/api-client/generated
    opt: target=ts
inputs:
  - directory: services
    paths:
      - "*/api/**/*.proto"
```

Chạy lệnh `buf generate` từ thư mục gốc của repo sẽ generate lại toàn bộ các client TypeScript mỗi khi có bất kỳ file proto nào thay đổi. Tác vụ này được cấu hình chạy như một khâu kiểm tra trong CI: nếu các file được generate ra có sự khác biệt so với các file đã được commit, bản build sẽ bị fail (đánh lỗi). **Protobuf là bản hợp đồng (contract); các type TypeScript là phái sinh từ nó.**

Kết quả bên trong storefront:

```typescript
import { OrderServiceClient } from "@composable/api-client/order/v1";
import { CreateOrderRequest } from "@composable/api-client/order/v1";

// Các type phản chiếu chính xác Go proto của bạn — không phải gõ tay (duplicate)
const req: CreateOrderRequest = {
  customerId: session.userId,
  items: cart.items.map(item => ({
    productId: item.id,
    quantity: item.qty,
    unitPrice: item.price, // Kiểu Money: { currencyCode, units, nanos }
  })),
  shippingAddress: shippingAddr,
  requestId: crypto.randomUUID(), // Idempotency key (Khóa lũy đẳng)
};
```

Khi team backend Go thêm một trường (field) vào `CreateOrderRequest`, type TypeScript sẽ tự động được cập nhật sau lần chạy `buf generate` tiếp theo — đi kèm với đó là các lỗi lúc compile (compile-time errors) ở mã nguồn frontend nếu nó chưa được sửa để xử lý trường mới kia.

## 6. Build Chọn lọc trong CI (Selective Builds)

CI chính là nơi mà khoản đầu tư vào monorepo sinh lời:

```bash
# Build toàn bộ (dùng cho nhánh main, hoặc sau bất kỳ thay đổi nào)
rush build

# Incremental (Build tăng dần): chỉ build những thứ bị ảnh hưởng bởi những thay đổi trong PR này
rush build --from packages/api-client  # Build lại api-client và mọi thứ phụ thuộc vào nó
rush build --to apps/storefront         # Chỉ build storefront và các dependency của nó

# Ví dụ: một developer sửa file packages/utils/src/formatters.ts
# CI tự động phát hiện ra thay đổi này ảnh hưởng đến:
# - @composable/utils (package vừa bị sửa)
# - @composable/api-client (có import utils để làm validation)
# - @composable/storefront (có import api-client)
# - @composable/admin-dashboard (có import api-client)
# Rush sẽ build lại và test lại chính xác 4 package này, và bỏ qua phần còn lại
```

Điều này cực kỳ quan trọng ở quy mô lớn: một thay đổi trong `packages/ui-components/Button.tsx` không được phép kích hoạt build lại `packages/api-client` hay `services/order-service`. Đồ thị dependency (dependency graph) của Rush đảm bảo điều đó không xảy ra.

## 7. Strangler Fig cho Frontend

Rush monorepo cũng triển khai mẫu thiết kế Strangler Fig ở **tầng frontend** — phản chiếu y hệt các giai đoạn chuyển đổi của backend từ [Phần 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) qua đến [Phần 8](/series/composable-commerce-migration/part-8-phase3-full-cutover/).

Trong Giai đoạn 1 (chuyển đổi read-only), cấu hình CDN sẽ điều hướng (route):
```
GET /products/*  → storefront Next.js mới (đọc từ Catalog Service)
GET /checkout/*  → frontend Magento (luồng ghi - writes - vẫn đi vào Magento)
POST /*          → frontend Magento (toàn bộ luồng ghi)
```

Storefront Next.js nằm trong `apps/storefront/` chỉ xử lý những trang đã được migrate. Các route chưa được xử lý sẽ rơi tuột (fall through) xuống một reverse proxy của Magento. Khi quá trình chuyển đổi tiến triển qua Giai đoạn 2 và Giai đoạn 3, ngày càng có nhiều route được điều hướng sang storefront mới — mà không cần phải build lại frontend hay thực hiện deployment nào.

```typescript
// apps/storefront/next.config.ts
const nextConfig = {
  async rewrites() {
    return {
      fallback: [
        {
          source: "/:path*",
          destination: `${process.env.MAGENTO_URL}/:path*`, // Tuyến dự phòng (fallback) về Magento
        },
      ],
    };
  },
};
```

## 8. Các Câu lệnh Rush Cần thiết

```bash
# Thiết lập lần đầu
npm install -g @microsoft/rush
rush install         # Cài toàn bộ dependencies (pnpm)

# Phát triển (Development)
rush build           # Build toàn bộ package theo thứ tự dependency
rush test            # Test toàn bộ package
rush rebuild         # Ép build lại (bỏ qua cache)
rush watch           # Chế độ watch cho development

# Thêm dependencies
rush add -p react --make-consistent          # Thêm vào project hiện tại + ghim global luôn
rush add -p @composable/utils --caret        # Thêm dependency của một package nội bộ

# Publishing (Xuất bản)
rush publish --apply --target-branch main   # Tăng version và publish

# Go services
rush build:go        # Build toàn bộ 21 Go microservices
rush test:go         # Test toàn bộ 21 Go microservices

# CI
rush build --to apps/storefront              # Chỉ build những gì storefront cần
rush build --from packages/api-client       # Build mọi thứ đang xài api-client
```

## 9. Một Lưu Ý Quan Trọng (Caveat)

Rush monorepo trong series này mô tả **cấu trúc được khuyến nghị** để quản lý tầng frontend của Nền tảng Composable Commerce. Các tài liệu kiến trúc dành cho backend Go (`Composable-Commerce-Service-Architecture`) là cực kỳ đầy đủ — 24 ADRs, các hướng dẫn API toàn diện, cẩm nang chuyển đổi. Còn các chi tiết cấu hình monorepo của frontend được suy diễn ra từ các mục tiêu thiết kế tổng thể của nền tảng.

Nếu bạn đang triển khai mô hình này cho đợt chuyển đổi của riêng bạn, hãy validate (xác thực) lại phần setup `buf.gen.yaml` so với cấu trúc thư mục proto cụ thể của bạn và phiên bản ConnectRPC mà team bạn ưa dùng. Cấu trúc thì đã được chứng minh; còn phiên bản cụ thể của toolchain thì luôn luôn tiến hóa.

## Bước Tiếp Theo

Với cấu trúc repository đã được thiết lập, chúng ta có thể đào sâu vào việc một Go microservice đơn lẻ trông sẽ như thế nào. [Phần 3: Kratos v2 Internals](/series/composable-commerce-migration/part-3-golang-kratos/) sẽ mổ xẻ toàn bộ — từ cấu trúc thư mục 5 lớp, tính năng Wire dependency injection cho đến bộ thư viện `common` (dùng chung) giúp loại bỏ tới 4,150 dòng code lặp đi lặp lại (boilerplate) trên toàn bộ 21 service.

## Câu Hỏi Thường Gặp (FAQ)

### Khi nào thì dùng Rush sẽ tốt hơn so với pnpm workspaces thông thường?

Hãy dùng pnpm workspaces thông thường nếu bạn có ≤4 package và không có yêu cầu quản trị version (version governance) nào khắt khe. Rush bắt đầu phát huy giá trị từ 5 package trở lên khi bạn cần tính năng cưỡng chế của `common-versions.json` (ngăn chặn việc một package đã lên React đời mới trong khi package kia vẫn kẹt ở đời cũ), vòng đời `rush publish`, và bộ cache build ở cấp độ project. Đối với nền tảng này — 2 ứng dụng (app), 3 package dùng chung, 21 Go service — các tính năng quản trị của Rush là cực kỳ đáng tiền.

### Các Go service có nằm trong đồ thị project (project graph) của Rush không?

Không. Rush chỉ quản lý các package có file `package.json`. Các Go service sống trong thư mục `services/` và được điều phối qua các lệnh custom `rush.json` dạng bulk (gọi shell chạy `go build ./...`). Rush có theo dõi các artifact build ra từ Go trong cache của nó nhưng không hề parse (đọc hiểu) các file `go.mod` hay `go.sum`. Việc quản lý dependency của Go vẫn hoàn toàn thuộc thẩm quyền của toolchain tiêu chuẩn của Go.

### Điều gì xảy ra nếu không chạy `buf generate` sau khi một file proto bị sửa đổi?

TypeScript SDK nằm trong `packages/api-client/generated/` sẽ bị "thiu" (stale - lỗi thời). CI sẽ cưỡng chế sự "tươi mới" (freshness): nếu các file được generate ra khác với các file đã được commit, pipeline sẽ đánh fail bằng lệnh `buf lint` + `buf generate --check`. Điều này giúp ngăn chặn việc frontend được xuất xưởng (shipping) với một type TypeScript không còn khớp với cái hợp đồng (contract) proto ở phía backend.

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 1: Phân Rã Magento 21 Services bằng DDD](/series/composable-commerce-migration/part-1-ddd-bounded-contexts/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 3: Go + Kratos v2 Framework Deep Dive →](/series/composable-commerce-migration/part-3-golang-kratos/)
