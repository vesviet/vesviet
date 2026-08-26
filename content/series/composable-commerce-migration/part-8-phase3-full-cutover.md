---
title: "Phần 8: Giai đoạn 3 — Chuyển Đổi Hoàn Toàn (Full Cutover): Zero Downtime"
date: 2026-05-27T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Hoàn tất di dời Magento: chuyển traffic 25%→100% cho Order Service, giữ hot standby 30 ngày để dự phòng rollback, và áp dụng ArgoCD GitOps."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Full Cutover", "Zero Downtime", "GitOps", "ArgoCD", "Traffic Shifting", "Rollback Plan"]
series: ["composable-commerce-migration"]
weight: 9
slug: "part-8-phase3-full-cutover"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-8-phase3-full-cutover/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 8: Giai đoạn 3 — Chuyển Đổi Hoàn Toàn (Full Cutover): Zero Downtime"
  relative: false
keywords: ["full cutover phase 3", "traffic shifting 100%", "argocd gitops cutover", "magento hot standby rollback"]
---

[← Chương trước: Phần 7: Giai Đoạn 2 — Dual-Write Dapr PubSub](/series/composable-commerce-migration/part-7-phase2-dual-write/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 9: Transactional Outbox & Saga Pattern →](/series/composable-commerce-migration/part-9-outbox-saga/)

---

> **Answer-first:** Giai đoạn 3 hoàn tất quá trình chuyển dịch: điều hướng 100% traffic thanh toán và đơn hàng sang Go microservices, duy trì Magento ở chế độ hot-standby trong 30 ngày để dự phòng rollback tức thì và tự động hóa triển khai qua GitOps ArgoCD.

---

Giai đoạn 3 (Phase 3) là hồi kết: 100% traffic chuyển hẳn sang hệ thống microservice, Magento chính thức lùi về làm một kho lưu trữ thụ động (passive archive), và toàn bộ nền tảng vận hành hoàn toàn trên các microservice Go thông qua quy trình GitOps. Sẽ không còn bóng dáng của PHP trong những luồng request quan trọng nữa. Và cũng chấm dứt luôn chuỗi ngày phải chi trả chi phí gia hạn giấy phép (license) cho Magento.

**Answer-first:** Cắt luồng theo mô hình GitOps (GitOps-driven Cutover) với ArgoCD và Kustomize là best practice của năm 2026 để đảm bảo zero-downtime. Tránh xa cạm bẫy "Big Bang migration", Customer Service và Catalog Service sẽ được cắt luồng 100% trước tiên. Riêng Order Service sẽ được nâng dần theo từng bậc (shadow adoption/graduated ramp) 25%→50%→75%→100% trong vòng 10 ngày, với các chốt chặn theo dõi nghiêm ngặt. Magento vẫn được giữ ở chế độ chờ nóng (hot standby) trong 30 ngày, sử dụng `archive-service` đồng bộ một chiều. Toàn bộ thao tác deploy và quản lý cấu hình đều nằm trong Git repository (single source of truth); ArgoCD (kết hợp Sync Waves và Hooks) tự động cưỡng chế trạng thái kỳ vọng lên cluster, ngăn chặn hoàn toàn hiện tượng cấu hình trôi dạt (configuration drift).

## 1. Lịch Trình Chuyển Đổi 6 Tuần (Cutover Calendar)

```
Tuần 1–2: Customer Service → 100% đẩy vào microservices
Tuần 3–4: Catalog Service → 100% đẩy vào microservices
Tuần 5–6: Order Service → Rải từ từ 25% → 50% → 75% → 100%
Tuần 7+:  Magento chuyển sang hot standby (tắt event bus, chạy archive-service mỗi giờ)
Tuần 11:  Chính thức rút ống thở (decommission) Magento (Ngày thứ 30 của quá trình hot standby)
```

Đến Tuần thứ 5, Customer và Catalog đã được di dời trọn vẹn và đã có 3+ tuần chạy cọ xát trên môi trường production. Cái đường ống đồng bộ Debezium đã được tắt bỏ hoàn toàn cho hai domain này (hiện tại microservice đã lên nắm quyền làm nguồn sự thật duy nhất, không còn là kẻ bám đuôi nữa). Chỉ duy nhất Order Service là vẫn phải cẩn thận đi từng bước (graduated ramp) bởi vì đơn hàng là những giao dịch tài chính liên quan tới tiền bạc, sai một ly là đi một dặm.

## 2. Customer + Catalog: Cắt Cái Rụp 100% (Immediate Cutover)

```bash
#!/bin/bash
# week-1-customer-cutover.sh

echo "Tuần 1: Cắt luồng hoàn toàn (Full Cutover) cho Customer Service"

# Tắt cờ đồng bộ ngược (reverse sync) của cơ chế ghi kép
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_magento_sync": "false"}}'

# Điều hướng 100% traffic của customer vào microservices
kubectl patch configmap feature-flags -n production \
  --patch '{"data": {"customer_write": "true", "customer_read": "true", "customer_cutover": "true"}}'

# Khởi động dịch vụ lưu trữ (archive) cho customer (Đồng bộ mỗi giờ một lần sang Magento trong vòng 30 ngày)
curl -X POST "http://archive-service:8080/api/v1/start-archive" \
  -d '{"domain": "customer", "interval_seconds": 3600}'

# Theo dõi sát sao trong 7 ngày
./scripts/monitor-cutover.sh --service=customer --duration=604800
echo "Quá trình cutover Customer Service đã hoàn tất. Đang bước vào 7 ngày theo dõi."
```

Cái archive service (lính mới xuất hiện ở Giai đoạn 3) làm nhiệm vụ vác dữ liệu từ microservice → ghi vào Magento theo lịch mỗi tiếng một lần. Đây là một cơ chế **đồng bộ một chiều, chỉ-đọc (one-way, read-only sync)** — Magento đã bị tước quyền ghi ngược lại. Nó đóng vai trò như một bản backup nóng và đáp ứng các yêu cầu kiểm toán/tuân thủ (regulatory requirements) buộc phải lưu trữ dữ liệu trên hệ thống cũ thêm một thời gian nhất định.

## 3. Order Service: Nâng Dần Traffic Theo Từng Bậc (Graduated Traffic Ramp)

Order Service được hưởng chế độ chăm sóc đặc biệt bởi vì đơn hàng là thứ dính líu trực tiếp tới tiền tươi thóc thật. Cái cờ tính năng `order_cutover` sẽ nhận thêm một tham số `percentage` (phần trăm) để kiểm soát xem bao nhiêu phần (fraction) số đơn hàng mới sẽ được ném sang cho microservice xử lý:

```go
// gateway-service/internal/router/order_router.go

func routeOrderRequest(c *gin.Context, clients *ServiceClients, flags *FlagStore) {
    flag := flags.Get("order_cutover")

    if !flag.Enabled || flag.Percentage == 0 {
        // Chế độ của Giai đoạn 2: toàn bộ đơn hàng đều vào Order Service và đồng bộ ngược về Magento
        handleOrderViaMicroservice(c, clients.Order, true /* syncToMagento */)
        return
    }

    // Nâng theo bậc: băm (hash) cái customer ID ra để quyết định xem rẽ hướng nào
    // (cùng một người mua thì lúc nào cũng phải chui vào cùng một hệ thống trong suốt thời gian chuyển đổi)
    customerID := c.GetHeader("X-Customer-ID")
    hash := fnv.New32a()
    hash.Write([]byte(customerID))
    bucket := hash.Sum32() % 100

    if bucket < uint32(flag.Percentage) {
        // Đơn hàng của khách hàng này sẽ được đẩy sang microservice (KHÔNG ĐỒNG BỘ về Magento nữa)
        handleOrderViaMicroservice(c, clients.Order, false /* cutover: no sync */)
    } else {
        // Vẫn điều hướng về Magento đối với khách hàng này
        proxyToMagento(c)
    }
}
```

Sử dụng cơ chế băm (hash) ID khách hàng (thay vì random ngẫu nhiên) sẽ đảm bảo rằng các đơn hàng của một người không bị xé lẻ ném đi hai nơi khác nhau — toàn bộ các đơn hàng xuất phát từ `customer_id=X` sẽ luôn luôn được gom về cùng một hệ thống duy nhất trong suốt quãng thời gian nâng bậc.

**Lịch trình nâng bậc cho Order Service (Tuần 5–6):**

| Ngày | % Cắt Luồng | Hành động cần làm ở mỗi bậc |
|---|---|---|
| Ngày 1 (Thứ Hai) | 25% | Bật cờ, dán mắt theo dõi trong 3 ngày |
| Ngày 4 (Thứ Năm) | 50% | Validate tính nhất quán dữ liệu, check DLQ=0, nâng số |
| Ngày 7 (Chủ Nhật) | 75% | Validate, check đối soát thanh toán (payment reconciliation) |
| Ngày 10 (Thứ Tư) | 100% | Cắt luồng hoàn toàn (Final cutover), tắt luôn cổng điều hướng về Magento |

Ở mỗi bậc, bắt buộc phải thỏa mãn các điều kiện sau đây mới được phép nâng lên bậc tiếp theo:
1. Số lượng tin nhắn kẹt trong DLQ = 0 (không có cái event nào bị xịt)
2. Độ trễ ghi (write latency) p99 < 200ms (Đây là SLA của Phase 3, gắt hơn cái mức 500ms hồi Phase 2)
3. Đối soát thanh toán: tổng doanh thu (total revenue) trong database microservice phải khớp từng cắc với Magento
4. Không có bất kỳ khiếu nại (complaints) nào của khách hàng liên quan tới việc tạo đơn hàng

## 4. Archive Service (Dịch Vụ Lưu Trữ)

```yaml
# k8s/archive-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: archive-service
  namespace: production
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: archive-service
        image: archive-service:v1.0.0
        args: ["--final-sync", "--compress"]
        env:
        - name: MICRO_DB_HOST
          value: "platform-db.production.svc.cluster.local"
        - name: MAGENTO_DB_HOST
          value: "magento-db.production.svc.cluster.local"
        - name: ARCHIVE_INTERVAL
          value: "3600"   # 1 giờ
        - name: ARCHIVE_DOMAINS
          value: "customer,catalog,order,inventory"
```

Hành vi của Archive service:
- Chạy theo lịch trình mỗi giờ một lần
- Đọc dữ liệu từ PostgreSQL của microservice (nguồn nắm quyền)
- Ghi dữ liệu vào MySQL của Magento (chỉ nhằm mục đích lưu trữ archive, quyền tự ghi của Magento đã bị tước)
- Nén dữ liệu lại (từ JSON → gzip) để cất giữ dài hạn
- Tự động dừng hoạt động sau 30 ngày (Ngày thứ 30 = chính thức rút ống thở Magento)

## 5. ArgoCD GitOps: Mô Hình Triển Khai Hậu Di Dời

Khi bóng dáng Magento đã lùi vào dĩ vãng, toàn bộ các luồng triển khai (deployments) về sau này đều sẽ tuân theo mô hình GitOps của ArgoCD. Luồng chảy trọn vẹn của một dòng code thay đổi:

```
1. Developer: git push code lên nhánh feature
2. GitLab CI:
    a. Chạy đống unit tests + integration tests
    b. Build file Docker image → push lên registry
    c. Mở MR (Merge Request) → team vào review code
3. MR được merge vào nhánh main:
    a. CI chạy lại toàn bộ test suite một lần nữa
    b. Build image chốt hạ: order-service:v1.2.3
    c. Cập nhật vào repo GitOps:
       git commit -m "Update order-service to v1.2.3"
       # Nội dung file thay đổi: gitops/apps/order-service/overlays/production/kustomization.yaml
       # Từ: newTag: v1.2.2
       # Thành: newTag: v1.2.3
4. ArgoCD đánh hơi thấy có sự thay đổi trong repo GitOps:
    a. Chạy Kustomize build: trộn base + production overlay
    b. Chạy lệnh kubectl apply đập vào cluster production
    c. Cập nhật cuốn chiếu (Rolling update): cứ update xong 1 pod, đứng test sức khỏe ok rồi mới update pod tiếp theo
5. ArgoCD tự động rollback nếu thấy có biến (unhealthy):
    git revert HEAD  # Undo cái commit cập nhật image tag trong repo GitOps
    ArgoCD nhìn thấy có revert → tự động khôi phục deployment về bản cũ
```

Không còn cảnh SSH gõ phím cạch cạch trên server production. Không còn lệnh `kubectl apply` chạy bằng cơm. Khái niệm "ơ máy em chạy ngon mà" đã bị xóa sổ vĩnh viễn khỏi các pha deploy. **Mọi thay đổi trên production đều có thể truy vết ngược (traceable) chính xác tới từng dòng Git commit.**

## 6. Kustomize: Bức Tranh Base + Overlays

Mỗi một service đều có những file ghi đè (overlays) dành riêng cho từng môi trường:

```
gitops/apps/order-service/
├── base/
│   ├── deployment.yaml          ← Những thứ xài chung: định nghĩa service, cổng (port), mấy cục thăm dò sức khỏe (probes)
│   ├── service.yaml
│   ├── configmap.yaml           ← Các config không chứa thông tin nhạy cảm
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml  ← Chỉ chạy 1 replicas, cấu hình resources siêu nhỏ nhắn
    └── production/
        ├── kustomization.yaml
        └── patch-replicas.yaml  ← Chạy 3 replicas, cấu hình resources hầm hố chuẩn production
```

```yaml
# gitops/apps/order-service/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - path: patch-replicas.yaml
images:
  - name: order-service
    newTag: v1.2.3                 ← CI sẽ tự động cập nhật cục này mỗi khi có bản release mới
```

```yaml
# gitops/apps/order-service/base/deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: order-service
        image: order-service           # Phần Tag đã được cái file overlay ở trên lo liệu
        ports:
        - containerPort: 8001          # HTTP
        - containerPort: 9001          # gRPC
        livenessProbe:
          grpc:
            port: 9001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 7. Sync Waves: Khởi Động Theo Thứ Tự

ArgoCD Sync Waves là thứ đứng ra bảo kê đảm bảo rằng các cụm cơ sở hạ tầng (infrastructure components) phải được khởi động trước tiên rồi mới tới lượt các service nhảy vào:

```yaml
# gitops/apps/order-service/base/deployment.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"   # Làn sóng (Wave) 2: các service sẽ khởi động sau khi wave 1 xong
---
# gitops/infrastructure/databases/postgresql.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # Làn sóng 0: Database phải dậy đầu tiên
---
# gitops/infrastructure/dapr-components.yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"   # Làn sóng 1: Dapr phải sống trước đám services
```

Thứ tự khởi động (Sync wave order): `Database (0) → Các cục Dapr (1) → Services (2) → Gateway (3)`

## 8. Nghiệm Thu Hiệu Năng: Bài Test Ép Tải X10 (10× Load Test)

Tiêu chí để qua ải Giai đoạn 3: *"Phải gánh được khối lượng tải gấp 10 lần production hiện tại (Handle 10× current production load)."* Đoạn kịch bản ép tải K6 này sẽ được thả xích vào giờ thấp điểm (off-peak hours) trước khi hùng hồn tuyên bố Giai đoạn 3 kết thúc:

```javascript
// tests/load/phase3-validation.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    stages: [
        { duration: '5m', target: 100 },   // Lấy đà (Ramp up)
        { duration: '10m', target: 1000 }, // Đập tải gấp 10 lần bình thường (10× normal load)
        { duration: '5m', target: 0 },     // Thả trôi (Ramp down)
    ],
    thresholds: {
        'http_req_duration': ['p99<200'],  // SLA yêu cầu p99 phải < 200ms
        'http_req_failed': ['rate<0.001'], // Tỷ lệ lỗi (error rate) phải < 0.1%
    },
};

export default function() {
    // Ép tải khâu tạo Đơn hàng (Cái endpoint nguy hiểm và mong manh nhất)
    const res = http.post('https://api.platform.com/api/v1/orders', JSON.stringify({
        customer_id: randomCustomerID(),
        items: [{ product_id: randomProductID(), quantity: 1 }],
        shipping_address: testAddress(),
        request_id: crypto.randomUUID(),
    }));

    check(res, { 'order created': (r) => r.status === 201 });
}
```

## 9. Rút Ống Thở Magento (Magento Decommission): Ngày 30

Sau 30 ngày kiên trì chạy hot standby mà không hề phải xài tới con bài rollback (quay xe) nào:

```bash
#!/bin/bash
# day-30-decommission.sh

echo "Ngày 30: Đang tiến hành rút ống thở cụ Magento hot standby"

# Bước 1: Dừng cái archive service lại
kubectl delete deployment archive-service -n production

# Bước 2: Tắt luôn connector Debezium (nếu vẫn còn đang chạy lay lắt cho domain nào đó)
kubectl delete deployment sync-service -n migration

# Bước 3: Đóng gói (Export) bản backup database Magento cuối cùng của cuộc đời nó
mysqldump --all-databases > /backup/magento-final-$(date +%Y%m%d).sql.gz

# Bước 4: Khai tử (Shut down) luôn dàn server application của Magento
kubectl delete namespace magento

# Bước 5: Tháo tung mấy cái cờ tính năng tàn dư của Magento khỏi Gateway
kubectl patch configmap feature-flags -n production \
  --type=json \
  -p='[{"op": "remove", "path": "/data/catalog_read"},
       {"op": "remove", "path": "/data/customer_read"},
       {"op": "remove", "path": "/data/order_read"}]'

echo "✅ Đã rút ống thở Magento thành công. Nền tảng lúc này đang chạy 100% bằng hệ thống microservices."
echo "💰 Chi phí license tiết kiệm được: sẽ bắt đầu phát huy tác dụng từ kỳ gia hạn tiếp theo"
```

## Danh Sách Kiểm Tra Hoàn Tất Giai Đoạn 3

**Tuần 5 (Kết thúc quá trình cutover của Order Service):**
- [ ] Chạy êm ru 10 ngày liên tiếp ở mức 100% không dính auto-rollback lần nào
- [ ] Đối soát thanh toán: con số ghi trong sổ cái (ledger) của microservice và Magento phải khớp nhau 100%, không lệch một đồng
- [ ] Số tin nhắn trong DLQ: = 0 trong suốt cả Tuần 5

**Tuần 7 (Sát giờ rút ống thở):**
- [ ] Archive service miệt mài chạy đủ 30 ngày không ném ra một cái lỗi nào
- [ ] Chốt hạ bài ép tải (load test): gấp 10 lần tải production, p99 < 200ms, tỷ lệ lỗi < 0.1%
- [ ] Toàn bộ các team phụ trách domain hân hoan ký tên xác nhận migration đã hoàn tất

**Ngày 30 (Rút ống thở - Decommission):**
- [ ] Bản sao lưu (backup) DB Magento cuối cùng đã được bọc kỹ tống vào kho lạnh (long-term storage)
- [ ] Sập cầu dao toàn bộ hạ tầng (infrastructure) của Magento
- [ ] Quét dọn mớ cấu hình cờ tính năng trên Gateway cho gọn gàng
- [ ] Nhấc máy lên gọi điện hủy luôn cái thông báo gia hạn bản quyền (license renewal) của platform cũ

## Thành Quả Bạn Vừa Xây Dựng

Hậu Giai đoạn 3, hệ thống của bạn trông sẽ thế này:
- **21 con microservice viết bằng Go** tung hoành trên Kubernetes, được deploy rần rần qua ArgoCD GitOps
- **Zero PHP** trong các luồng request quan trọng
- **Zero tiền mua license Magento** kể từ kỳ gia hạn tiếp theo
- **Khả năng phình to độc lập (Independent scaling)**: Order Service có thể tự bành trướng quy mô riêng rẽ mỗi khi có săn sale (flash sales)
- Độ trễ phản hồi **< 200ms p99** cho toàn bộ các endpoint quan trọng nhất
- **Có sẵn cơ chế rollback xoay tua 30 ngày** → nhưng quan trọng là: ta đã chứng minh được chả bao giờ thèm xài tới nó

[Phần 9](/series/composable-commerce-migration/part-9-outbox-saga/) sẽ đi sâu mổ xẻ cái cơ chế đảm bảo độ tin cậy của sự kiện (event reliability mechanism) — thứ vũ khí bí mật đã chắp cánh cho cuộc di dời này thành công mỹ mãn mà không làm rớt mất một mẩu dữ liệu nào: Transactional Outbox + Saga pattern, con bài mang lại lời thề vàng ngọc (guarantees) rằng mọi sự kiện đơn hàng đều sẽ được giao đi "không thừa không thiếu một lần" (exactly once), và mọi giao dịch xịt đều sẽ được cấp cho một liều thuốc giải độc tương xứng (compensating action).

---

*Nếu bạn đang hứng thú khám phá những mảng miếng (patterns) thiết kế hệ thống phân tán (distributed systems) tương tự, hãy nghía qua [Series Kiến Trúc Shopee](/series/shopee-architecture/) — nơi ghi lại cách một siêu ứng dụng (super-app) cấp độ khu vực gồng gánh 10 triệu người dùng đồng thời (10M+ concurrent users) bằng một mô hình chẻ nhỏ microservice (microservices decomposition) có nhiều nét tương đồng — một nguồn tham khảo cực kỳ đáng giá cho các quyết định về định cỡ hệ thống (sizing) và thiết lập chỉ tiêu SLO (SLO decisions).*

## Câu Hỏi Thường Gặp (FAQ)

### Tại sao lại xài ArgoCD GitOps thay vì phang thẳng lệnh kubectl hay xài Helm cho lẹ?

Phang thẳng `kubectl apply` bằng cơm là trò chơi mạo hiểm, vi phạm nghiêm trọng nguyên tắc phân quyền (separation of concerns) trong tiêu chuẩn bảo mật 2026. Helm thì tuyệt trong việc tạo ra khuôn mẫu (templating), nhưng nó không tự động cưỡng chế trạng thái kỳ vọng (target state). Ngược lại, ArgoCD hoạt động như một gã cảnh sát mẫn cán, luôn duy trì luật **trạng thái kỳ vọng = trạng thái thực tế (desired state = actual state)** ở mỗi chu kỳ rà soát (thường là 3 phút). Đặc biệt, trong môi trường Cloud Native 2026, ArgoCD kết hợp với Sealed Secrets / External Secrets Operator xử lý bài toán tiêm mã bí mật (secret injection) an toàn. Nếu một pod bị ai đó tiêm image tag lạ (hotfix tay), ArgoCD sẽ ngửi thấy mùi sai lệch (drift) và tự động ghi đè khôi phục (self-heal). Sự bảo kê này là ranh giới mong manh giữa một ca quay xe có kiểm soát (reproducible rollback) và một thảm họa hệ thống lúc cutover.

### Cái khái niệm "chuyển đổi không thời gian chết" (zero-downtime cutover) rút cục là nó hứa hẹn (guarantee) cái gì?

Zero-downtime mang ý nghĩa: **tuyệt đối không để văng ra lỗi HTTP 5xx trong lúc đang đảo luồng (traffic shift), tuyệt đối không giam lỏng (queued) hay đánh rơi (dropped) bất kỳ request nào của người dùng, và tuyệt đối không trưng ra cái trang bảo trì (maintenance page) ngứa mắt**. Nhưng hãy nhớ kỹ, nó KHÔNG ĐỒNG NGHĨA với "không bị giật lag" (no latency increase) — những cú request mở bát ngay sau lúc đảo luồng thường sẽ dính độ trễ (latency) p99 cao hơn khoảng 10–20% do đám pod mới đang lạch cạch tự làm nóng (warm up) đống connection pool của chúng. Cái khoảng thời gian làm nóng (warm-up period) ất ơ này chính là lý do tại sao hệ thống nền tảng bắt buộc phải có bước mồi (pre-warms) trước 5 phút cho mỗi nhịp tăng traffic. Lết qua được vài phút mồi máy đó (thường là 2-5 phút), latency sẽ lập tức vút về lại ngưỡng lý tưởng.

### Magento nên được giữ lại bao lâu dưới dạng hot standby (chờ nóng) sau khi đã cutover xong?

Con số an toàn tối thiểu là **30 ngày** ở trạng thái chỉ-đọc (read-only archive mode). Quãng thời gian này sinh ra để bao biện cho ba chuyện: (1) Chu kỳ chốt sổ thanh toán (billing cycles) thường xuyên réo tên mấy cái mã order ID cũ kỹ của Magento, (2) Đám chăm sóc khách hàng (customer service) hay có trò đào mồ sống dậy kêu ca mấy cái đơn hàng từ thời đồ đá, (3) Đó là khung thời gian vàng để bắt quả tang (detect) mấy dữ liệu oái oăm lọt lưới (edge-case data missing) của quá trình migration. Vượt qua cửa ải 30 ngày, cứ tự tin mà giật sập dàn máy chủ ứng dụng (application tier) của Magento, nhưng chớ có dại mà xóa luôn; hãy bê nguyên cái snapshot của database nhét vào kho lạnh (cold storage) thêm 90 ngày nữa rồi hẵng phi tang vĩnh viễn (permanent deletion).

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 7: Giai Đoạn 2 — Dual-Write Dapr PubSub](/series/composable-commerce-migration/part-7-phase2-dual-write/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 9: Transactional Outbox & Saga Pattern →](/series/composable-commerce-migration/part-9-outbox-saga/)
