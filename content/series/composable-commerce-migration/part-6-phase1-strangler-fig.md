---
title: "Phần 6: Giai đoạn 1 — Strangler Fig: Di dời Chỉ-đọc (Read-Only)"
date: 2026-05-13T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Di dời Magento GĐ 1 (Strangler Fig): Go microservices chế độ read-only, Debezium CDC đồng bộ MySQL không cần Kafka, feature flags và fallback an toàn."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Strangler Fig", "Debezium", "CDC", "MySQL", "Read-Only Migration", "Feature Flags"]
series: ["composable-commerce-migration"]
weight: 7
slug: "part-6-phase1-strangler-fig"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-6-phase1-strangler-fig/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 6: Giai đoạn 1 — Strangler Fig: Di dời Chỉ-đọc (Read-Only)"
  relative: false
keywords: ["strangler fig phase 1", "debezium cdc magento", "read-only microservices", "zero downtime migration"]
---

[← Chương trước: Phần 5: Chuyển Đổi Schema EAV Magento](/series/composable-commerce-migration/part-5-eav-schema-migration/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 7: Giai Đoạn 2 — Dual-Write Dapr PubSub →](/series/composable-commerce-migration/part-7-phase2-dual-write/)

---

> **Answer-first:** Giai đoạn 1 của mô hình Strangler Fig chỉ di dời luồng truy vấn đọc (Catalog, Search) sang Go microservices, sử dụng Change Data Capture (Debezium CDC) để đồng bộ dữ liệu từ MySQL Magento theo thời gian thực mà không làm gián đoạn luồng ghi nghiệp vụ.

---

Giai đoạn 1 (Phase 1) là giai đoạn an toàn nhất trong toàn bộ cuộc di dời — đó là chủ ý thiết kế (by design). Sẽ không có bất kỳ thao tác ghi (write) dữ liệu nào chạm tới hệ thống microservice mới. Magento vẫn là nguồn sự thật duy nhất (source of truth) cho mọi sửa đổi dữ liệu. Việc duy nhất mà Giai đoạn 1 làm, đó là chứng minh rằng đống microservice của bạn có thể phục vụ các thao tác *đọc (read)* với tốc độ nhanh hơn và độ ổn định cao hơn Magento.

**Answer-first:** Strangler Fig pattern vẫn là tiêu chuẩn vàng của ngành công nghiệp trong việc giảm thiểu rủi ro khi migrate hệ thống nguyên khối trong năm 2026. Ở Giai đoạn 1, chúng ta sẽ triển khai các microservice Go ở chế độ chỉ-đọc (read-only), điều hướng các request dạng GET vào đó thông qua các cờ tính năng (feature flags) phân rã theo từng domain (lĩnh vực) nằm trên API Gateway (kèm theo cơ chế tự động xả ngược - fallback về Magento). Trái tim của giải pháp tách rời dữ liệu (data decomposition) là công cụ Change Data Capture (CDC) Debezium — chạy dưới dạng embedded engine để stream các thay đổi từ MySQL của Magento sang microservice thông qua Dapr PubSub (không cần Kafka cồng kềnh). Mọi thao tác ghi (write) vẫn tiếp tục đâm thẳng vào Magento, với các consumer được thiết kế bắt buộc theo cơ chế lũy đẳng (idempotent). Mục tiêu độ trễ dữ liệu: < 2 giây.

## 1. Kiến trúc Giai đoạn 1

```
Client App (browser/mobile)
         │
         ▼
┌─────────────────────────────────────┐
│         API Gateway :8000            │
│                                      │
│  GET /products/* ──► feature_flag   │
│                    [catalog_read]?   │
│           ┌─────────────────────┐    │
│           │ Bật cờ + Khỏe mạnh?  │    │
│           └─────────────────────┘    │
│               │           │          │
│               ▼           ▼          │
│      Catalog Service  Magento API   │
│          :8005        (fallback)    │
│                                      │
│  POST/PUT/DELETE /* ──► Magento API │  ← TOÀN BỘ request Ghi đều đẩy về Magento
└─────────────────────────────────────┘
         │                │
         ▼                ▼
  Microservices DB    Magento MySQL
  (read replica)     (source of truth)
         ▲
         │ Debezium CDC + Dapr PubSub
         │ (mỗi dòng bị thay đổi trong Magento → đẩy (publish) sang microservices)
         └──────────────────────────────
```

Chỉ thị quan trọng nhất (The key constraint): **tuyệt đối không để bất kỳ đường ghi (write path) nào lọt tới các microservice trong Phase 1**. Thằng Gateway sẽ tống cổ mọi lệnh POST/PUT/DELETE về Magento, bất chấp cờ tính năng đang bật hay tắt.

## 2. Tại Sao Không Dùng Polling Theo Cột `updated_at` Cho Nhanh?

Bản năng đầu tiên của mọi người khi phải đồng bộ dữ liệu Magento là viết một vòng lặp quét (polling) cái cột `updated_at`:

```sql
-- ❌ Polling: mù tịt trước các lệnh DELETE, chết ngắc nếu server bị lệch giờ
SELECT entity_id FROM catalog_product_entity
WHERE updated_at > :last_check_time
ORDER BY updated_at ASC
LIMIT 1000;
```

Cách làm này sẽ sụp đổ theo ba cách:
1. **Các lệnh DELETE sẽ vô hình**: Một sản phẩm bị xóa sẽ không để lại dấu vết gì ở cột `updated_at` — nó đơn giản là bốc hơi khỏi cái bảng đó luôn.
2. **Lệch đồng hồ (Clock skew)**: Nếu con MySQL của Magento nằm ở một server khác có cái đồng hồ chạy lệch đi một tí tẹo, các bản ghi có thể bị rơi tõm vào khoảng trống giữa các lần quét.
3. **Tải đè lên database (High database load)**: Liên tục thực hiện quét toàn bảng (full-table scans) theo timestamp trên một con database e-commerce đang chạy production sẽ gây ra hiện tượng tắc nghẽn (contention).

Đây là giải pháp trích từ `sync-service-implementation.md`:

> *"Tại sao lại chọn Debezium thay vì dùng polling `updated_at`? Kỹ thuật polling vào cột `updated_at` sẽ bỏ lọt hoàn toàn các thao tác DELETE và cực kỳ dễ gãy khi đồng hồ bị lệch hoặc trùng timestamp. Debezium đọc thẳng vào binary logs của MySQL, bắt trọn từng thay đổi ở cấp độ dòng (row-level) cực kỳ cẩn mật với dữ liệu chuẩn xác trước/sau (before/after state)."*

## 3. Cài đặt Debezium CDC

Debezium đọc file binary log (binlog) của MySQL — chính là cái file log dạng chỉ-thêm-vào (append-only) mà cơ chế replication (nhân bản) của MySQL sử dụng. Mỗi một thao tác INSERT, UPDATE, và DELETE nã vào bất kỳ bảng nào đang được theo dõi cũng sẽ đẻ ra một sự kiện thay đổi (change event).

### Bước 1: Bật MySQL Binlog trên DB Magento

Thêm đoạn này vào file `/etc/mysql/conf.d/binlog.cnf` trên con server MySQL của Magento:

```ini
[mysqld]
log_bin           = mysql-bin
binlog_format     = ROW           # Bắt buộc phải là ROW — để bắt được chính xác giá trị before/after
binlog_row_image  = FULL          # Chụp lại toàn bộ dòng dữ liệu, không chỉ lấy mấy cột bị đổi
expire_logs_days  = 7
server_id         = 1             # Bắt buộc phải độc nhất vô nhị trong toàn cụm MySQL replica của bạn
```

Tạo một user chuyên dùng cho Debezium replication:

```sql
-- Chạy câu này trên MySQL của Magento
CREATE USER 'debezium'@'%' IDENTIFIED BY '${DEBEZIUM_PASSWORD}';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT
  ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;
```

Kiểm tra xem binlog đã lên chưa:

```sql
SHOW VARIABLES LIKE 'log_bin';
-- Kết quả kỳ vọng: log_bin = ON
SHOW VARIABLES LIKE 'binlog_format';
-- Kết quả kỳ vọng: binlog_format = ROW
```

### Bước 2: Cấu hình Connector cho Debezium

Nền tảng của chúng ta chạy Debezium ở **chế độ embedded engine** — không cần phải chăn dắt cả một cụm Kafka Connect độc lập. Cái connector này sẽ chạy ké dưới dạng một sidecar bám theo cái sync consumer service:

```yaml
# configs/debezium-connector.json — được cái sync consumer load lên lúc khởi động
{
  "connector.class": "io.debezium.connector.mysql.MySqlConnector",
  "database.hostname": "${MAGENTO_DB_HOST}",
  "database.port": "3306",
  "database.user": "debezium",
  "database.password": "${DEBEZIUM_PASSWORD}",
  "database.server.id": "184054",
  "database.server.name": "magento",
  "database.include.list": "${MAGENTO_DB_NAME}",

  "table.include.list": [
    "${MAGENTO_DB_NAME}.customer_entity",
    "${MAGENTO_DB_NAME}.customer_address_entity",
    "${MAGENTO_DB_NAME}.catalog_product_entity",
    "${MAGENTO_DB_NAME}.catalog_product_entity_varchar",
    "${MAGENTO_DB_NAME}.catalog_product_entity_decimal",
    "${MAGENTO_DB_NAME}.catalog_product_entity_int",
    "${MAGENTO_DB_NAME}.sales_order",
    "${MAGENTO_DB_NAME}.cataloginventory_stock_item"
  ],

  "snapshot.mode": "initial",           // Snapshot toàn bộ vào lần chạy đầu tiên, sau đó sẽ chuyển sang incremental (tăng dần)
  "include.schema.changes": "false",

  // Lưu trữ Offset: ghi nhớ vị trí binlog để có thể resume lại sau khi khởi động lại
  "offset.storage": "org.apache.kafka.connect.storage.FileOffsetBackingStore",
  "offset.storage.file.filename": "/var/debezium/offsets/offsets.dat",
  "offset.flush.interval.ms": "1000"
}
```

**Lưu ý sinh tử về `snapshot.mode: initial`**: Vào lần khởi động đầu tiên, Debezium sẽ chụp một bản snapshot (bản sao toàn bộ) của TẤT CẢ các dòng nằm trong các bảng được theo dõi trước khi nó chuyển sang chế độ stream binlog. Cú snapshot đầu đời này có thể ngốn từ 15–60 phút đối với một database Magento chứa hàng triệu sản phẩm. Hãy tính toán kế hoạch deploy Phase 1 cẩn thận dựa trên con số này.

## 4. Đường ống CDC → Dapr

Thay vì dùng cái đường ống cồng kềnh lấy Kafka làm trung tâm (Kafka-based) nhan nhản trong các bài tutorial trên mạng, nền tảng của chúng ta dùng:

```
Binlog của Magento MySQL
    ↓ Debezium embedded engine (Không cần cụm Kafka Connect)
Sync Consumer Service (viết bằng Go)
    ↓ Dịch số nguyên → UUID qua bảng magento_id_map
    ↓ Dát phẳng EAV (gom varchar + int + decimal → thành 1 bản ghi sản phẩm duy nhất)
Dapr PubSub Publisher
    ↓ Redis Streams (hạ tầng event có sẵn của nền tảng)
Microservice Consumers
```

Các topic sự kiện (event) phục vụ cho migration (đã được xác thực trong `sync-service-implementation.md`):

| Topic | Người Đẩy (Publisher) | Người Hứng (Consumer) |
|---|---|---|
| `migration.customer.changed` | Sync Service | Customer Service |
| `migration.product.changed` | Sync Service | Catalog Service |
| `migration.order.changed` | Sync Service | Order Service |
| `migration.stock.changed` | Sync Service | Warehouse Service |
| `migration.dlq` | Dapr (tự động) | Đội Ops qua DLQ handler |

Đoạn code của sync consumer gánh đường ống sản phẩm:

```go
// sync-service/internal/consumer/product_consumer.go

func (c *ProductConsumer) HandleChange(ctx context.Context, event debezium.ChangeEvent) error {
    if event.Table != "catalog_product_entity" {
        return nil
    }

    // Bước 1: Phiên dịch Magento integer ID → UUID
    magentoID := event.After["entity_id"].(int64)
    uuid, err := c.idMapper.GetOrCreate(ctx, "product", magentoID)
    if err != nil {
        return fmt.Errorf("id mapping failed for product %d: %w", magentoID, err)
    }

    // Bước 2: Bốc toàn bộ dữ liệu sản phẩm (chạy câu EAV pivot query)
    product, err := c.extractor.ExtractProduct(ctx, magentoID)
    if err != nil {
        return fmt.Errorf("EAV extraction failed for product %d: %w", magentoID, err)
    }
    product.ID = uuid

    // Bước 3: Publish vào Dapr PubSub
    payload, _ := json.Marshal(product)
    return c.daprClient.PublishEvent(ctx, "pubsub", "migration.product.changed", payload)
}
```

## 5. Điều hướng bằng Cờ Tính Năng (Feature Flag Routing)

Thằng Gateway Service sẽ làm nhiệm vụ điều hướng traffic dựa vào các cờ tính năng (feature flags) gắn theo từng domain, được lôi ra đánh giá ở MỖI request:

```go
// gateway-service/internal/middleware/feature_flag.go

func FeatureFlagMiddleware(flagStore FlagStore) gin.HandlerFunc {
    return func(c *gin.Context) {
        // Lấy domain của request này
        domain := extractDomain(c.Request.URL.Path)

        flag, err := flagStore.Get(c, fmt.Sprintf("%s_read", domain))
        if err != nil || !flag.Enabled {
            // Không tìm thấy cờ hoặc cờ đang tắt → proxy vứt thẳng sang Magento
            proxyToMagento(c)
            return
        }

        // Kiểm tra xem microservice mục tiêu có đang thở không (healthy)
        if !isHealthy(domain) {
            // Service đang ngỏm → tự động fallback
            proxyToMagento(c)
            return
        }

        c.Next() // Cho đi tiếp vào microservice handler
    }
}
```

Tính năng Feature flags được lưu trữ trong Kubernetes ConfigMap và hỗ trợ hot-reload (cập nhật không cần khởi động lại):

```yaml
# configmap/feature-flags.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: feature-flags
  namespace: production
data:
  catalog_read: "true"     # Đẩy GET /products/* sang Catalog Service
  customer_read: "false"   # Vẫn đẩy về Magento (chưa hòm hòm)
  order_read: "false"      # Vẫn đẩy về Magento
```

Việc bật cờ cho một domain sẽ có tác dụng trong vòng 30 giây (khoảng thời gian refresh của ConfigMap) — tuyệt đối không cần tới một thao tác deployment nào.

## 6. Tự Động Fallback: Khả Năng Tự Phục Hồi Của Gateway

Thằng Gateway được cài một bộ đếm để tự xả kèo (fallback) sau 3 lần xịt:

```go
// gateway-service/internal/health/monitor.go

type HealthMonitor struct {
    failureCounts sync.Map  // domain → số lần xịt liên tiếp
    flagStore     FlagStore
}

func (m *HealthMonitor) RecordFailure(domain string) {
    count, _ := m.failureCounts.LoadOrStore(domain, int64(0))
    newCount := count.(int64) + 1
    m.failureCounts.Store(domain, newCount)

    if newCount >= 3 {
        // Xịt 3 phát liên tiếp → tự động tắt cờ tính năng
        m.flagStore.Disable(domain + "_read")
        log.Warnf("Đã tự động tắt cờ %s_read sau %d lần xịt liên tiếp", domain, newCount)
        // Bắn alert vào kênh Slack #migration-issues
        alert.Send(fmt.Sprintf("⚠️ %s_read đã bị tự động tắt — yêu cầu check sức khỏe của service", domain))
    }
}

func (m *HealthMonitor) RecordSuccess(domain string) {
    m.failureCounts.Store(domain, int64(0))
}
```

Một khi cờ đã bị tắt bởi hệ thống tự động, việc bật nó lên lại đòi hỏi phải có bàn tay can thiệp của con người (đọc log, xác minh service đã khỏe mạnh trở lại, sau đó sửa tay cái file ConfigMap). Cơ chế này chặn đứng tình trạng một con service đang chết ngắc ngoải (flapping) cứ tự động bật cờ lên rồi lại kéo nhau chết chùm.

## 7. Tiêu Chí Nghiệm Thu Giai Đoạn 1

Trước khi có thể hùng hồn tuyên bố Giai đoạn 1 đã xong và rục rịch sang Giai đoạn 2:

| Chỉ Số (Metric) | Mục Tiêu (Target) | Cách Đo |
|---|---|---|
| Độ trễ đồng bộ (Data sync latency) | < 2 giây | `check-data-consistency.sh catalog 100` |
| Thời gian Fallback | < 5 giây | Tắt mẹ cái service pod đi, đo xem mất bao lâu để nó tự nhảy về Magento |
| Tỷ lệ thành công (Success rate) của lệnh đọc | > 99.9% | Prometheus `http_request_duration_seconds` |
| Số lỗi liên quan tới ghi (Zero write errors) | 0 | Đảm bảo mọi lệnh POST đổ về Magento đều trả về 2xx |
| Theo dõi suốt 7 ngày | Không bị tự động tắt cờ lần nào | Lục lại lịch sử đổi cờ trong ConfigMap events |

Kịch bản (script) để thẩm định độ nhất quán dữ liệu (data consistency) (được cài chạy cronjob mỗi 15 phút một lần suốt Giai đoạn 1):

```bash
#!/bin/bash
# scripts/check-data-consistency.sh

SERVICE=$1       # ví dụ: "catalog"
SAMPLE_SIZE=$2   # ví dụ: 100

echo "Đang kiểm tra độ nhất quán dữ liệu của $SERVICE ($SAMPLE_SIZE mẫu)..."

# Lấy ID của các bản ghi mẫu từ Magento
MAGENTO_IDS=$(mysql -h $MAGENTO_DB -e "
    SELECT entity_id FROM catalog_product_entity
    ORDER BY RAND() LIMIT $SAMPLE_SIZE
" | tail -n +2)

MISMATCH_COUNT=0

while IFS= read -r magento_id; do
    # Bốc UUID từ magento_id_map
    UUID=$(psql $PLATFORM_DB -t -c "
        SELECT platform_uuid FROM magento_id_map
        WHERE entity_type = '${SERVICE}' AND magento_id = $magento_id
    ")

    # Đem hai cái updated_at timestamp ra đọ (phải lệch nhau dưới 2 giây)
    MAGENTO_TS=$(mysql -h $MAGENTO_DB -e "
        SELECT UNIX_TIMESTAMP(updated_at) FROM catalog_product_entity
        WHERE entity_id = $magento_id
    " | tail -1)

    PLATFORM_TS=$(psql $PLATFORM_DB -t -c "
        SELECT EXTRACT(EPOCH FROM updated_at) FROM products WHERE id = '${UUID}'
    ")

    LAG=$(echo "$PLATFORM_TS - $MAGENTO_TS" | bc | tr -d '-')

    if (( $(echo "$LAG > 2" | bc -l) )); then
        echo "⚠️  Sản phẩm $magento_id bị trễ mất: ${LAG}s"
        ((MISMATCH_COUNT++))
    fi
done <<< "$MAGENTO_IDS"

echo "Đã kiểm tra xong. Số mẫu bị lỗi: $MISMATCH_COUNT / $SAMPLE_SIZE"
[ $MISMATCH_COUNT -eq 0 ] && echo "✅ Toàn bộ mẫu đều đạt chuẩn SLA < 2s"
```

## 8. Danh Sách Kiểm Tra Khi Triển Khai (Deployment Checklist)

**Trước khi deploy (1–2 tuần trước lúc go-live Phase 1):**
- [ ] Bật MySQL binlog cho Magento (`log_bin = ON`, `binlog_format = ROW`)
- [ ] Tạo user cho Debezium replication, cấp đủ quyền (grants)
- [ ] Bơm đầy `magento_id_map` (kiểm tra lại số đếm có khớp với entity count bên Magento không)
- [ ] Chạy trích xuất (extraction) toàn bộ EAV và nghiệm thu thành công (count match)
- [ ] Deploy Sync Consumer Service, chạy snapshot cày dữ liệu lần đầu
- [ ] Check lại toàn bộ Dapr topic dành cho việc migration xem đã nhận được sự kiện chưa
- [ ] Tạo PersistentVolumeClaim trên Kubernetes để chứa cái offset file của Debezium

**Go-live Phase 1:**
- [ ] Feature flags: Mặc định tắt hết `"false"` (chạy mượt qua Magento)
- [ ] Bật `catalog_read: "true"` cho 10% quân số trong team test thử
- [ ] Chăm chú theo dõi trong 24h: cờ không bị tự động tắt, latency < 2s
- [ ] Bật cờ hứng 100% traffic
- [ ] Lên bảng dashboard monitoring hứng số liệu cho Phase 1

**Kết thúc Phase 1 (Đạt đủ tiêu chuẩn nhảy sang Phase 2):**
- [ ] Tất cả các domain đã được bật: chạy thông đồng 7 ngày liền không bị tự động tắt cờ
- [ ] Thẩm định độ nhất quán dữ liệu: quét ngẫu nhiên 1000 mẫu trả về 0 lỗi
- [ ] Hiệu năng: p99 latency < 200ms cho toàn bộ các endpoint đọc

## Bước Tiếp Theo

Giai đoạn 1 đang chạy rầm rập. Microservice đã gánh được phần đọc (read). Magento vẫn nắm quyền sinh sát phần ghi (write). Sang tới [Phần 7: Giai đoạn 2 — Ghi Kép (Dual-Write)](/series/composable-commerce-migration/part-7-phase2-dual-write/), chúng ta sẽ bắt đầu bật tính năng ghi dữ liệu trên các microservice — mở hàng với Customer Service (rủi ro thấp nhất) và khép lại bằng Order Service (rủi ro ngập mặt). Thách thức đắt giá: cả Magento lẫn microservice giờ đây sẽ lao vào sửa cùng một khối dữ liệu cùng một lúc (concurrently). Chúng ta sẽ mổ xẻ cái chiến thuật phân xử xung đột (conflict resolution strategy) để xử lý mớ bòng bong này mà không làm mất một bit dữ liệu nào.

## Câu Hỏi Thường Gặp (FAQ)

### Debezium khác quái gì so với Kafka Connect?

Debezium là một **thư viện CDC connector** — nó bới móc mớ log thay đổi của database (MySQL binlog, PostgreSQL WAL, v.v.) và sản sinh ra các sự kiện thay đổi theo cơ chế log-based CDC. Còn Kafka Connect là một **framework dùng để chạy mấy cái connector đó**, thường được xài để rải Debezium ở quy mô lớn với đầy đủ món ăn chơi như tự động khắc phục sự cố, dải worker phân tán, và REST API. 

*Góc nhìn vận hành 2026 (E-E-A-T Context): CDC hiện nay được coi là một kỷ luật hạ tầng doanh nghiệp chứ không chỉ là công cụ copy dữ liệu. Nền tảng của chúng ta chọn chạy Debezium ở **chế độ embedded engine** — cái connector này chạy cắm rễ bên trong cái process Go của con sync-consumer, đá văng nhu cầu vận hành cụm Kafka Connect. Sự đánh đổi là fault tolerance thấp hơn (do chạy 1 process), nhưng bù lại dễ vận hành hơn cả tỷ lần. Lưu ý rằng do việc đồng bộ CDC mang tính chất "at-least-once" (ít nhất một lần), mọi hàm xử lý (consumer) tại các microservice mục tiêu bắt buộc phải được thiết kế dạng lũy đẳng (idempotency) kết hợp với các vòng lặp đối chiếu (reconciliation loops) để đảm bảo dữ liệu không bị hỏng hóc hoặc lặp lại.*

### Pattern Strangler Fig (Cây siết cổ) giúp né downtime khi migration kiểu gì?

Strangler Fig vận hành bằng cách luân chuyển dòng chảy traffic ngay tại tầng proxy/gateway — chứ không phải bằng cách tắt hệ thống này bật hệ thống kia lên. Suốt quá trình Phase 1, cùng một cái tên miền đó sẽ đứng ra hứng toàn bộ traffic. CDN hoặc API Gateway sẽ phân tích từng request một: nếu thấy cờ tính năng bật và cái service mục tiêu còn đang thở (healthy), nó sẽ ném request qua cho microservice; còn không, nó sẽ buông tay xả cho rớt xuống Magento. Hoàn toàn không có chuyện trỏ lại DNS (DNS switch), không có bảo trì hệ thống định kỳ (maintenance window), và không có lấy một khoảnh khắc gián đoạn nào mà người dùng có thể thấy được. Cuộc di dời này âm thầm diễn ra phía sau lớp routing suốt nhiều tuần liền, chứ không phải diễn ra chớp nhoáng trong vài tiếng đồng hồ.

### Làm thế nào để giải quyết vụ Debezium chạy snapshot lần đầu mà không block (khóa) luôn con MySQL đang chạy production?

Cái lệnh `snapshot.mode: initial` của Debezium sẽ đọc toàn bộ dữ liệu bằng một bản snapshot đồng nhất (consistent snapshot) — nó xài cái cấp độ cô lập (isolation level) `REPEATABLE READ` của MySQL, nghĩa là nó **không** lock (khóa) cái bảng đó lại. Tuy nhiên, nó lại ngốn cực kỳ nhiều băng thông I/O suốt quãng thời gian snapshot (do nó phải tuần tự nhai hết hàng triệu dòng). Best practice ở đây là: hãy chạy cái initial snapshot này vào giờ thấp điểm (off-peak hours), dán mắt vào các chỉ số MySQL I/O metrics, và vặn cái cấu hình `max.batch.size` của Debezium để hãm bớt tốc độ đọc lại nếu thấy cần.

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 5: Chuyển Đổi Schema EAV Magento](/series/composable-commerce-migration/part-5-eav-schema-migration/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 7: Giai Đoạn 2 — Dual-Write Dapr PubSub →](/series/composable-commerce-migration/part-7-phase2-dual-write/)
