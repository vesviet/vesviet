---
title: "Phần 10: Dạo Quanh ADR — Giải Ngố 24 Quyết Định Kiến Trúc"
date: 2026-06-10T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Tổng hợp 24 quyết định kiến trúc cốt lõi (ADR) khi xây dựng Composable Commerce: Dapr vs Kafka, Kustomize vs Helm, go-kratos vs Gin, Goose vs golang-migrate."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["ADR", "Architecture Decision Records", "System Design", "Microservices", "Golang", "Tradeoffs"]
series: ["composable-commerce-migration"]
weight: 11
slug: "part-10-adr-walkthrough"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-10-adr-walkthrough/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 10: Dạo Quanh ADR — Giải Ngố 24 Quyết Định Kiến Trúc"
  relative: false
keywords: ["architecture decision records", "24 adr walkthrough", "dapr vs kafka", "goose vs golang migrate"]
---

[← Chương trước: Phần 9: Transactional Outbox & Saga Pattern](/series/composable-commerce-migration/part-9-outbox-saga/) | [Mục lục Series](/series/composable-commerce-migration/)

---

> **Answer-first:** Tổng kết 24 Hồ sơ Quyết định Kiến trúc (ADRs) đúc kết từ dự án di dời thực tế: giải mã lý do lựa chọn Dapr thay vì Kafka cho Pub/Sub, database riêng biệt theo từng service, Wire dependency injection và chiến lược zero-downtime cutover.

---

21 services. 24 quyết định. 3.5 tháng trời cân lên đặt xuống được ghi chép cẩn thận vào các bản Ghi nhận Quyết định Kiến trúc (Architecture Decision Records - ADR).

ADR là một tài liệu ngắn gọn gọn gàng trả lời rạch ròi câu hỏi: "Tại sao chúng ta lại cắm đầu chọn phương án X trong khi hai thằng Y và Z cũng ngon lành không kém?" Nếu không có ADR, mọi tri thức kiến trúc (architectural knowledge) sẽ chỉ tồn tại mỏng manh trong đầu các kỹ sư. Lỡ ngày đẹp trời nào đó họ nộp đơn nghỉ việc, mớ tri thức đó cũng đội nón ra đi — và thế là team mới vào tiếp quản sẽ lại cặm cụi đập đi xây lại cái component y chang cái cách mà đội ngũ cũ đã từng hăm hở thử nghiệm rồi vứt sọt rác (tried and rejected).

Bài viết này sẽ dắt tay bạn đi dạo qua toàn bộ 24 bản ADR của nền tảng Composable Commerce, được gom nhóm theo từng danh mục, nhấn mạnh vào những quyết định nghe có vẻ ngược đời (counter-intuitive). Đa số các ADR chỉ dài cỡ một đoạn văn tóm tắt; riêng những quyết định nào gây há hốc mồm nhất thì sẽ được mổ xẻ sâu hơn.

**Answer-first:** 24 bản ADR quy tụ xung quanh 3 triết lý lặp đi lặp lại: (1) **chọn sức ỳ (resilience) vứt bỏ sự đơn giản** — chọn Dapr thay vì xài thẳng Redis raw, xài Kustomize thay vì Helm, xài outbox thay vì bắn event trực tiếp trong process; (2) **chọn khuôn phép (standardization) vứt bỏ sự tự do** — service nào cũng phải chui vào cái khuôn Kratos v2 5 tầng y hệt nhau, xài chung cái thư viện `common`, chung cái trò Goose migrations; (3) **minh bạch rạch ròi (explicit) vứt bỏ sự ngầm hiểu** — cái ADR-001 (chơi hệ event-driven) được chốt đơn sớm tận 3 tháng trước khi có bất kỳ dòng code nào được gõ, đảm bảo mọi service từ ngày đầu lọt lòng đều bị ép buộc phải coi event là công dân hạng nhất (first-class constraint).

## Dòng Thời Gian Ra Quyết Định: Nó Tiết Lộ Điều Gì?

Trước khi soi vào nội dung các quyết định, hãy ngó qua dòng thời gian (timeline):

```
17-11-2025: ADR-001 — Kiến trúc Hướng sự kiện (Event-Driven Architecture)
            (Quyết định lẻ loi duy nhất trong năm 2025. Sớm hơn mọi thứ khác tận 3 tháng.)

03-02-2026: ADR-002 đến ADR-020 — 19 cái quyết định đẻ ra trong một ngày
            (Đừng hiểu nhầm, đây là thành quả của một buổi ngồi lại chốt sổ đồng thuận (alignment session) của team, không phải 19 cú gật đầu ngẫu hứng)

12-02-2026: ADR-021 — Ai Nắm Quyền Sinh Sát Dữ Liệu Giá & Tồn Kho (Price & Stock Data Ownership)
            (Bị phát hiện ra sau khi buổi integration test đầu tiên làm lòi ra vụ đùn đẩy trách nhiệm không rõ ràng)

02-03-2026: ADR-022, ADR-023, ADR-024 — EAV + Caching + Tồn kho (Inventory)
            (Lòi ra sau khi đợt cày cuốc migration EAV phơi bày lỗ hổng của các quyết định trước đó)
```

**Việc cái ADR-001 ngự trị ở mốc thời gian sớm hơn 3 tháng chính là chi tiết đắt giá nhất tiết lộ bản chất của nền tảng này.** Cả team đã chốt hạ kiến trúc hướng sự kiện (event-driven) từ tận tháng 11/2025 — khi trong tay chưa hề có bất kỳ quyết định nào khác. "Phải coi sự kiện (Events) là công dân hạng nhất" là nguyên tắc khai quốc (founding principle); mọi thứ râu ria khác đều từ đó mà nảy nở. Dapr (ADR-003), saga pattern (Phần 9), ghi kép bằng event (Phần 7), và Transactional Outbox (Phần 9) thảy đều là đám con cháu chắt (downstream) của ADR-001.

Cái cục 19 quyết định ồ ạt vào ngày 03/02 thực chất là một buổi rà soát kiến trúc (architecture alignment session), nơi những thứ đã được gật gù ngầm với nhau trong quá trình thiết kế nay được đem ra giấy trắng mực đen chốt hạ.

## Nhóm 1: Kiến Trúc & Thiết Kế (ADR-001 đến ADR-004)

### ADR-001: Kiến Trúc Hướng Sự Kiện (2025-11-17)
**Quyết định (Decision)**: Xài Dapr Pub/Sub chống lưng bằng Redis Streams cho TẤT CẢ các sự kiện giao dịch (transactional events)

Đây là bản cương lĩnh nền tảng (thesis decision). Bản ADR này thiết quân luật: mọi thay đổi trạng thái có máu mặt — đơn hàng được tạo, thanh toán trừ tiền xong, giữ chỗ tồn kho thành công, cập nhật thông tin khách — bắt buộc phải được quy hình thành một domain event (sự kiện nghiệp vụ). Các service phản ứng (react) với sự kiện, chứ cấm tiệt trò gọi réo tên nhau (direct calls). Mấy cú gọi trực tiếp (gRPC) chỉ được cấp phép cho các luồng xử lý đồng bộ (synchronous) đối mặt với người dùng, nơi mà độ trễ (latency) là chuyện sống còn.

Hệ lụy (The implication): **sự kiện chính là bản hợp đồng (contracts), không phải chi tiết kỹ thuật chìm**. Bốc đồng đổi cấu trúc (schema) của một event đồng nghĩa với việc xé bỏ hợp đồng (breaking change), buộc toàn thể 500 anh em subscribers phải vác xác đi cập nhật theo. Cả team đã tự quàng tròng cái kỷ luật sắt này vào cổ từ tận tháng 11/2025.

### ADR-002: Kiến Trúc Microservices
**Quyết định**: 21 service chia thành 6 cụm miền giới hạn (bounded context groups)

Bản ADR này trắng trợn lôi Định luật Conway ra làm bình phong: *"Số lượng service ≈ số lượng team × 2–3."* Với việc có trong tay vài ba team engineering, con số 21 service là một chiếc áo vừa vặn. Giả sử ném cái nền tảng này cho một team 5 người, thì số lượng service chỉ nên loanh quanh 5–7 cái mà thôi.

### ADR-003: Xài Dapr Thay Vì Đâm Thẳng Vào Redis Streams (Raw Redis)
**Quyết định ngược đời (Counter-intuitive).** Đa số mấy cái tutorial dạy viết Go microservices toàn nhè thẳng Redis ra mà phang:

```go
// ❌ Cắm thẳng vào Redis Streams — kiểu tutorial nhan nhản trên mạng
client := redis.NewClient(...)
client.XAdd(ctx, &redis.XAddArgs{Stream: "orders", Values: event})
```

```go
// ✅ Dapr PubSub — kiểu nền tảng này đang chơi
daprClient.PublishEvent(ctx, "pubsub", "orders.order.created", payload)
```

Sự khác bọt: Dapr dựng lên một bức tường che chắn (abstracts) cái broker nằm bên dưới. Hôm nay mày là Redis Streams. Ngày mai mày có thể biến thành Azure Service Bus hay AWS SNS — mà code không cần phải nhúc nhích dù chỉ một dòng. Cái duy nhất phải sửa là tên component `pubsub` khai báo trong file manifest của Dapr.

Cái giá phải cắn răng chịu: Dapr nhét thêm một cục sidecar container vào chung mâm với mỗi pod (ăn chặn ~64MB RAM mỗi service). Nhân lên 21 service chạy trên cụm 3 node: tốn toi ~1.3GB RAM. Cả team gật đầu nuốt cái cục mồi này đổi lấy khả năng "ôm cục chạy đi đâu cũng sống" (portability).

### ADR-004: Mỗi Service Một Cõi Database
**Quyết định**: Thằng service nào ôm cục PostgreSQL của thằng nấy. Cấm tiệt trò query vắt ngang database của thằng khác.

Đây chính là nguyên nhân sâu xa đẻ ra cái vụ migration EAV mướt mồ hôi hột (Phần 5). Nếu không có cái luật database-per-service chết tiệt này, Catalog Service cứ việc kê cao gối chọc thẳng vào mấy cái bảng MySQL lạc hậu của Magento mà query. Bị ép vào đường cùng, Catalog Service buộc phải tự xây một bộ khung schema chuẩn hóa (normalized schema) cho riêng mình — sinh ra nguyên cái dây chuyền bốc vác EAV (EAV extraction pipeline) ở Phần 5.

Kỷ luật thép: những tay service nào thòm thèm ngó nghiêng dữ liệu thuộc địa bàn của thằng khác thì chỉ có 2 con đường: (a) muối mặt sang gõ cửa gọi gRPC xin xỏ, hoặc (b) tự giác nuôi một bản sao dữ liệu rút gọn (read model) được hâm nóng liên tục qua domain events. Cấm tuyệt đối lệnh `JOIN` vượt biên giới.

## Nhóm 2: Hệ Sinh Thái Công Nghệ (ADR-005 đến ADR-007)

### ADR-005: Go 1.25 + go-kratos v3
**Quyết định ngược đời.** Vòng chung kết có 3 gương mặt HTTP framework của Go đọ sức:

| Framework | Điểm mạnh (Strengths) | Bị loại vì (Rejected because) |
|---|---|---|
| **Gin** | Nhanh, đông fan, hệ sinh thái siêu to khổng lồ | Chả có gRPC transport native; ráng bám theo thì phải viết code gấp đôi (HTTP + gRPC) |
| **Echo** | API bao mượt, dây chuyền middleware ngon | Cùng chung cảnh ngộ cụt chân gRPC như Gin |
| **go-kratos v3** | Code chuẩn hệ DDD, chơi luôn 2 súng (dual transport), xài Wire DI, tương thích hoàn hảo Go 1.25 | Khó học, đòi hỏi tư duy cứng (Steeper learning curve) |

Kratos chiến thắng vẻ vang là nhờ cái ADR-002 đã hạ lệnh mọi service đều phải chơi 2 tay 2 súng (HTTP+gRPC). Ôm Gin hay Echo, bạn sẽ phải tốn công sức triển khai một bộ HTTP handlers XONG LẠI PHẢI đắp thêm một cái gRPC server riêng rẽ — tính ra là hì hục code đúp 2 lần cho mỗi endpoint. Kratos v3 thì bá đạo hơn: từ một cái file proto, nó tự động sinh ra HTTP và gRPC thành những công dân hạng nhất ngon ơ, đồng thời tận dụng tính năng tự động tối ưu GOMAXPROCS trong container của Go 1.25.

### ADR-006: Khám Phá Dịch Vụ (Service Discovery) Với Consul
**Quyết định ngược đời.** Hầu hết mấy nền tảng bấu víu vào Kubernetes (Kubernetes-native) đều giao phó sinh mạng cho K8s DNS. Nền tảng này thì tham lam xài cả hai:
- K8s DNS dùng để ngóng tìm anh em láng giềng trong cùng một cụm (same-cluster)
- Consul tung hoành kết nối các cụm cách trở (cross-cluster) và réo gọi các dịch vụ ngoại lai (external service)

Consul được chọn mặt gửi vàng vì lộ trình tương lai của nền tảng là bành trướng ra đa trung tâm dữ liệu (multi-datacenter). K8s DNS thì mù tịt nếu bị nhốt khác cụm. Cơ chế thăm khám sức khỏe (health checks) của Consul service mesh dĩ nhiên là ăn đứt mấy trò liveness probes lèo tèo của K8s trong nghiệp vụ service discovery.

### ADR-007: Docker Multi-Stage + Distroless
**Quyết định**: Build Docker nhiều chặng (multi-stage) múc luôn cái image gốc là distroless xài cho production

```dockerfile
# Hai chặng rõ ràng: build bằng Go, chạy trên distroless
FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o /app/service ./cmd/order-service

FROM gcr.io/distroless/base-debian12
COPY --from=builder /app/service /service
ENTRYPOINT ["/service"]
```

Image distroless là một thằng cởi trần: không shell, không package manager, không `curl` — diện tích hứng đạn (attack surface) thu hẹp ~10 lần so với Alpine. Đánh đổi lại: lỡ có biến cần rò lỗi (debugging) thì phải lôi `kubectl exec` ra kẹp thêm cục debug sidecar, chứ không có cửa gõ `bash` tàng tàng vào quậy đâu.

## Nhóm 3: Triển Khai & Vận Hành (Deployment & Operations) (ADR-008 đến ADR-010)

### ADR-008: GitLab CI (cho GitHub Actions ra rìa)
Team vốn đã cắm rễ trên mảnh đất GitLab để chứa code (code hosting). Những cái khuôn pipeline xài lại được (reusable pipeline templates) của GitLab CI (thông qua lệnh `include:` trong `.gitlab-ci.yml`) cho phép biệt đội DevOps trung tâm gò sẵn những chuỗi dây chuyền build + test + deploy xịn xò để toàn bộ 21 repo service đàn em tự động kế thừa (inherit).

### ADR-009: ArgoCD + Kustomize (thay vì Helm)
**Quyết định ngược đời.** Helm đang thống trị ngôi vương trình quản lý gói (package manager) của Kubernetes. Cớ sao lại bỏ theo Kustomize?

| Tiêu chí | Helm | Kustomize |
|---|---|---|
| **Khuôn (Templates)** | Go templates chi chít ngoặc `{{ }}` | Trộn và vá một cách chiến lược (Strategic merge patches) |
| **Độ phức tạp** | Cao (hầm bà lằng các hàm template, điều kiện if/else) | Thấp (những miếng vá YAML hiền lành) |
| **Gỡ lỗi (Debugging)** | Phải gõ `helm template` để soi xem nó nặn ra cục YAML hình thù thế nào | Đập vào mắt là YAML tinh khiết từ trên xuống dưới |
| **Độ dốc học tập** | Khá dốc | Gần như phẳng lỳ (miễn là đọc hiểu K8s YAML) |

Với một team tay ôm 24 services, độ phức tạp lằng nhằng của khuôn Helm (templating complexity) sẽ nhanh chóng biến thành gánh nặng kỹ thuật. Những miếng vá YAML thuần khiết (pure-YAML patches) của Kustomize lại quá ư là thân thiện, ai có chút vốn liếng Kubernetes là đọc hiểu ngay — bao gồm cả mấy lính mới tò te (junior engineers) chưa từng biết Helm là cái vẹo gì. Cái trò lấy nền đắp thêm lớp áo ngoài (base+overlay pattern) cũng ăn khớp hoàn hảo với thói quen phân chia môi trường (dev, staging, production) của team.

### ADR-010: Cây Đinh Ba Prometheus + Grafana + Jaeger
Một bộ đồ nghề quan sát (observability stack) chuẩn mực, chả có gì phải bàn. Điểm xịn xò: Jaeger bắt tay với OpenTelemetry được nhúng sâu ngay từ cấp thư viện `common/metrics` — tức là toàn bộ 21 service cứ hễ import `common v1.9.5` là tự động được khuyến mãi luôn bộ distributed tracing (truy vết phân tán) mà không tốn hột mồ hôi nào.

## Nhóm 4: API & Hội Nhập (Integration) (ADR-011 đến ADR-013)

### ADR-011: Chơi Cả gRPC + REST (Giao Thức Kép - Dual Protocol)
Chỉ từ một cái file proto là rặn ra đủ cả gRPC handlers lẫn HTTP routes (thông qua trò ma giáo `google/api/annotations.proto`). Tránh cày cuốc trùng lặp (No duplication). Khách vãng lai (External clients) được mời xài REST; anh em trong nhà (internal services) thì gọi gRPC cho lẹ. Mánh lới này đã được phơi bày rành rành ở Phần 4 của series.

### ADR-012: Elasticsearch Trấn Giữ Khâu Tìm Kiếm
**Quyết định**: Xài Elasticsearch (đá văng Meilisearch, Typesense, hay chiêu trò full-text của PostgreSQL)

Khi bạn phải gồng gánh hơn 10,000 mặt hàng (SKUs) chứa một đống thuộc tính EAV và còn phải bợ đỡ ngôn ngữ Tiếng Việt (một ngôn ngữ nhạy cảm rắc rối đủ trò diacritic-heavy), thì năng lực của bộ máy phân tích Tiếng Việt (Vietnamese analyzer) và tài gom nhóm bóc tách đa trường (multi-field aggregation) của Elasticsearch chính là thứ chốt hạ. Search Service sẽ đứng hóng event từ Catalog Service để lập chỉ mục (indexes) — tuyệt đối không mảy may chọc ngoáy vào database của nhau.

### ADR-013: JWT + Xác Thực RBAC
Mấy cái tem thông hành (JWT tokens) sẽ do Auth Service phát, lên tới Gateway là bị xé vé kiểm tra gắt gao trước khi được thả lọt vào mấy service bên trong. Phân quyền chơi hệ RBAC (không thèm xài ABAC) — quyền hạn được phân phát ở đẳng cấp vai vế (role level - vd: `orders:create`, `products:edit`) thay vì soi mói xuống tận cấp độ tài nguyên (resource level).

## Nhóm 5: Cấu Hình & Dữ Liệu (ADR-014 đến ADR-015)

### ADR-014: Cấu hình go-kratos Kẹp Chung K8s ConfigMaps
Phân chia giai cấp cấu hình (Configuration hierarchy): `configs/config.yaml` (dàn giáo cơ bản, được commit lên git) → K8s ConfigMap (hàng xài riêng cho từng môi trường, cấm commit) → K8s Secrets (chứa đồ quốc cấm/credentials, được trông coi bởi Vault/SOPS).

### ADR-015: Goose Cân Hết Trò Schema Migrations
**Quyết định ngược đời.** Hai đối thủ sừng sỏ bị gạt ra rìa:

- **golang-migrate**: Khá nổi tiếng nhưng mang cái tật không chịu bọc từng migration vào một cái transaction (giao dịch) mặc định. Nếu xui xẻo migration lăn ra chết giữa đường, cái schema của bạn sẽ kẹt lại ở một trạng thái dở dở ương ương (partial state).
- **Atlas**: Tự động phân tích sinh ra mã khác biệt (diffing). Quá xịn nhưng lại tước mất quyền làm chủ (explicit control) của dân dev đối với từng bước nhảy (migration steps).

Thằng Goose thì khôn ngoan bọc mọi migration vào giữa cái bánh mỳ `BEGIN; ... COMMIT;` — nếu migration nhai nghẹn giữa chừng, thì ói ra (rolls back) nguyên cục lại như cũ. Đối với một cái database thương mại điện tử chuyên trữ tiền nong, tính nguyên tử (atomicity) không phải là thứ để đem ra mặc cả (non-negotiable).

## Nhóm 6: Frontend & Phát Triển (ADR-016 đến ADR-020)

### ADR-016: React + Next.js
**Quyết định**: React 19 + Next.js 15 (App Router + RSC)

Món Server-Side Rendering (SSR) và React Server Components (RSC) của Next.js 15 là cứu cánh sống còn cho trò làm mồi SEO. Hơn thế nữa, tính năng React Compiler của React 19 giúp tự động tối ưu hóa hiệu suất (memoization) mà không cần nhồi nhét `useMemo` khắp nơi. Dân mua sắm qua mạng xứ Vịt toàn sục sạo tìm hàng qua Google. Dựng một cái storefront thuần CSR (kiểu Create React App) thì có mà chìm lỉm (rank poorly). Bảng điều khiển admin dashboard thì cứ vô tư táng React không cần SSR.

### ADR-017: Kiến Trúc Thư Viện Xài Chung (Common Library)
Như đã phân tích ở Phần 3, cái thư viện `gitlab.com/ta-microservices/common v1.9.5` đã giảm thiểu 4,150 dòng code trùng lặp khắp 19 service. Lời sấm truyền: *"Đừng có đi copy-paste middleware. Gom nó lại mà abstract."*

### ADR-018: K3d + Tilt Đủ Xài Cho Local
**Quyết định**: Xài K3d (bản K3s nhẹ hều chạy trong Docker) + Tilt hot reload — vứt Docker Compose vô sọt rác

Docker Compose có một cái tật là không bắt chước (simulate) được màn bơm (injection) Dapr sidecar, bó tay vụ giới hạn tài nguyên (K8s resource limits), và chào thua mấy trò mount ConfigMap/Secret. Mấy thanh niên dev cứ khư khư ôm Compose chạy local xong lúc vác lên Kubernetes staging (K8s) lại cứ bài ca "ủa sao ở Compose chạy ngon mà lên K8s lại tạch" (it works on Compose, fails on K8s). K3d local mang nguyên một cái Kubernetes thu nhỏ (complete Kubernetes environment) nhét vừa vặn vào cái laptop (đòi hỏi ram 8GB nếu muốn cõng hết 21 service).

### ADR-019: Ghi Log Có Tổ Chức Kèm Dây Cột Correlation IDs
Mọi dòng log rặn ra đều phải đóng đinh đủ bộ: `service`, `trace_id`, `correlation_id`, `user_id`, `request_id`. Mấy cái Correlation IDs này sẽ lây lan (propagate) sang metadata của sự kiện (event metadata) trên Dapr. Chỉ việc bốc một cái `correlation_id` vứt vào ô tìm kiếm của Grafana Loki là phơi bày cả một vòng đời (request journey) lướt sóng qua 5+ service.

### ADR-020: Bắt Lỗi & Khả Năng Sinh Tồn (Resilience)
Cấu hình khiên chắn (Circuit breaker configuration - ADR-020): Hụt 5 phát liên tiếp (consecutive failures) → hất văng mọi cú gọi mới trong 60 giây (open) → he hé cửa cho 5 dũng sĩ qua thử nghiệm (half-open) → nếu sống thì đóng cửa bưng bít như thường (closed). Thời gian chờ dãn cách (Exponential backoff): 1s → 2s → 4s → 8s → 16s → từ bỏ (give up).

## Nhóm 7: Dữ Liệu & Miền (Domain) (ADR-021 đến ADR-024)

### ADR-021: Ai Nắm Dữ Liệu Giá & Tồn Kho (Price & Stock Data Ownership)
**Quyết định**: Pricing Service trùm sò mảng giá cả; Warehouse Service thao túng số lượng tồn kho; Promotion Service thì đứng ra phán luật giảm giá.

Cú chốt này nhắm thẳng vào một cái lỗi ngu ngốc kinh điển của kiến trúc Magento: khăng khăng bắt ép cả giá lẫn tồn kho phải chui vào làm nô tỳ (attributes) cho một cái sản phẩm. Trong cái nền tảng composable này, chúng đều được giải phóng thành các thực thể độc lập thuộc về các vùng nghiệp vụ (business capabilities) riêng rẽ. Catalog Service chỉ được biết cái sản phẩm đó hình thù *ra sao* (what). Pricing Service mới biết nó *đáng giá bao nhiêu* (how much). Còn Warehouse Service là kẻ duy nhất đếm được *có bao nhiêu mạng đang tồn* (how many exist).

### ADR-022: Chuyển Đổi (Pivoting) SQL Động Cho EAV
Một cái chốt hạ đặt nền móng (foundational decision) cho Phần 5 của chuỗi bài viết: cấm tuyệt đối trò đóng đinh (hardcoded) mấy cái ID của attribute. Cái mưu hèn kế bẩn (pattern) lùng sục thông qua `eav_attribute.attribute_code` mới là đường lui an toàn nhất (safe migration approach). Bản ADR này được chắp bút mót vào tận ngày 02/03/2026 — ngay sau khi đợt cày cuốc EAV (EAV spike) vạch trần thói hư tật xấu: đám kịch bản bốc vác (extraction scripts) ban đầu của team toàn đâm đầu đi hardcode ID một cách trắng trợn.

### ADR-023: Chuẩn Hóa Lò Caching + Các Mô Hình Worker (Worker Patterns)
Cái ADR này chính là chiếc chìa khóa vạn năng (unlocked) sinh ra cái thư viện `common v1.9.5`: nhét chung cái khiên chắn sập cache (single-flight cache stampede protection), con cronjob xài thuật toán RedLock phân tán (RedLock distributed cron), và con processor lo khâu outbox (outbox processor) vào chung một rổ (common library) cho gọn lẹ. Nhớ lại trước cái ngày ký ADR này (tháng 03/2026), 10 thằng service thì đẻ ra 10 cái outbox tự xưng khác nhau (slight variations).

### ADR-024: Quyền Lực Dữ Liệu Tồn Kho (Inventory Data Ownership) (Dài 17KB — Trận Chiến Cãi Vã To Nhất)
Với 17KB vắt vẻo, ADR-024 dài hơn gấp 3 lần bất kỳ cái ADR tép riu nào khác. Việc thằng nào sẽ ôm trọn kho dữ liệu tồn kho (inventory data ownership) chính là ngọn lửa châm ngòi cuộc cãi vã khốc liệt (contested decision) nhất trong lịch sử thiết kế nền tảng này: Catalog Service sẽ nhét túi thông tin tồn kho (như cái cách mà Magento hay chơi, tống cái bảng `cataloginventory_stock_item` làm trư chư hầu cho catalog) hay là giao phó cho Warehouse Service cai quản?

Phán quyết: **Warehouse Service cai quản tồn kho (owns stock); Catalog Service chỉ được quyền trưng ra một cái bảng hiệu hiển thị (read-only stock indicator)** (vd: in_stock: true/false) được bơm đầy nhờ vào mớ event do Warehouse Service nhè ra.

Cái luồng phản biện bướng bỉnh (contested alternative) ban đầu đùn đẩy trách nhiệm là "Catalog phải vác xác đi réo Warehouse lấy số lượng tồn kho (stock level) bằng một cú gọi gRPC đồng bộ (synchronous) mỗi khi có đứa load trang sản phẩm (product page)." Ý tưởng này đã bị sỉ vả và gạt phăng (rejected) vì như thế khác gì treo cổ cả cái tốc độ load trang sản phẩm vào cái mạng sống lay lắt của Warehouse Service — lỡ thằng Warehouse lăn ra sập (single service failure) là sập luôn cả sạp hàng (product browsing) kéo theo không trượt phát nào. Bằng cách luộc chín (pre-computing) biến `in_stock` rồi nhét vào DB của Catalog (thông qua event), các trang Catalog giờ đã được buff (resilient) một khả năng sống dai dẳng mặc cho thằng Warehouse Service có xịt ngóm đi chăng nữa.

## 5 Lựa Chọn Ngược Đời Nhất Gây Há Hốc Mồm (The 5 Most Counter-Intuitive Decisions)

| Quyết định (Decision) | Kỹ sư bình thường (What most engineers would choose) | Thứ ta chốt hạ (What was chosen) | Cớ sự (Key reason) |
|---|---|---|---|
| Hắn tin sự kiện (Event messaging) | Cắm thẳng mặt vào Redis Streams | Dựng lớp màng Dapr abstraction | Dễ lật mặt (Broker portability) đổi nhà cung cấp |
| HTTP framework | Gin hoặc Echo | go-kratos v3 | Nhai ngon cả gRPC lẫn HTTP (Native dual transport) |
| K8s config | Helm | Kustomize | Gọn nhẹ, toàn YAML mộc (pure YAML) |
| Lịch sử Schema (Schema migrations) | golang-migrate | Goose | Được bọc transaction kỹ lưỡng |
| Cầm trịch tồn kho (Inventory ownership) | Nhét trong Catalog Service | Vứt sang Warehouse Service (chia tách) | Cứu vãn trang Catalog (Catalog page resilience) khỏi chết chùm |

## Đôi Lời Chốt Hạ (Final Word)

24 quyết định, tất cả đều được thông qua (accepted), không một vết xước đập đi (rejected), không một cái nào bị đạp đổ thay thế (superseded) — đó có thể là một dấu hiệu của bộ não quy hoạch thiên tài (excellent upfront design), hoặc cũng có thể là dấu hiệu cho thấy cả team này đã dối lòng (hasn't been honest) che giấu những lúc lén lút sửa sai sau lưng (retrospective rethinking). Cái lốc 3 cái ADR tháng 03/2026 (ADR-022, 023, 024) đã vạch trần một sự thật phũ phàng: những quyết định này mọc ra như nấm sau mưa để vá víu (document gaps) cho những cú trượt chân sấp mặt (found during implementation) lúc nhào vô code thực tế, chứ chả phải thần cơ diệu toán (upfront design) gì cho cam.

Cái quyết định mang tầm nhìn vĩ đại nhất vẫn thuộc về cái ADR-001 — được thai nghén 3 tháng trời trước khi có thứ gì khác. Tư tưởng **ưu tiên hướng sự kiện (Event-driven first)** đã gọt giũa và nặn nên hình thù của toàn bộ chiến dịch di dời (migration strategy): xài CDC bằng Debezium, ghi kép bằng event (dual-write), cái Transactional Outbox khét lẹt, cho tới điệu nhảy choreography saga uyển chuyển. Nếu không có màn tuyên thệ sắt đá bám rễ (founding commitment) này, cái kế hoạch thay máu rễ Strangler Fig (3-phase Strangler Fig migration) thần thánh được tung hô nhan nhản trong cái series này khéo đã tan thành mây khói (wouldn't have worked).

---

*Phần này chính thức đặt dấu chấm hết cho chuỗi bài viết Lộ trình Di dời Composable Commerce. Nếu bạn cũng đang nuôi ý định thay thế nền tảng Magento cũ mèm của mình, hãy lần mò theo cái [la bàn mục lục](/series/composable-commerce-migration/) được chỉ điểm sẵn — Các lão đại CTO thì nhảy vào cày từ Phần 0, dân cày Magento backend thì xắn tay áo mổ xẻ từ Phần 5, còn mấy dân tổ lái Golang (Golang engineers) thì cứ từ Phần 3 mà phang thẳng.*

*Cần người phím trước (architecture consulting) cho cú đâm lao sắp tới của bạn? → [Đặt gạch tâm sự 1:1 ngay và luôn](/hire/)*

---

### 🔗 Đọc thêm các chuyên đề liên quan:
- [Kiến trúc Microservices Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Triển khai Agentic AI Swarm trong Production với OpenClaw & LiteLLM](/posts/deploying-autonomous-ai-swarm-openclaw-litellm/)
- [Kiến trúc Microservices Golang gRPC: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/)

---

---

---

[← Chương trước: Phần 9: Transactional Outbox & Saga Pattern](/series/composable-commerce-migration/part-9-outbox-saga/) | [Mục lục Series](/series/composable-commerce-migration/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Dạo Quanh ADR — Giải Ngố 24 Quyết Định Kiến Trúc giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Tổng hợp 24 quyết định kiến trúc cốt lõi (ADR) khi xây dựng Composable Commerce: Dapr vs Kafka, Kustomize vs Helm, go-kratos vs Gin, Goose vs golang-migrate.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
