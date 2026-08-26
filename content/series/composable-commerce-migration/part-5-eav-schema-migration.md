---
title: "Phần 5: Chuyển đổi Schema EAV — Cái bẫy lớn nhất của Magento"
date: 2026-05-06T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Trích xuất schema EAV của Magento: ánh xạ định danh int sang UUID, không hardcode ID thuộc tính, dùng pivot SQL động và mẫu truy vấn SQL chạy thực tế."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Magento", "EAV", "Database Migration", "PostgreSQL", "SQL Pivot", "Schema Design"]
series: ["composable-commerce-migration"]
weight: 6
slug: "part-5-eav-schema-migration"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-5-eav-schema-migration/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 5: Chuyển đổi Schema EAV — Cái bẫy lớn nhất của Magento"
  relative: false
keywords: ["magento eav extraction", "eav to relational", "int to uuid migration", "dynamic sql pivot eav"]
---

[← Chương trước: Phần 4: gRPC Internal + REST Gateway](/series/composable-commerce-migration/part-4-grpc-rest-gateway/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 6: Giai Đoạn 1 — Strangler Fig Read-Only →](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)

---

> **Answer-first:** Thoát khỏi cấu trúc Entity-Attribute-Value (EAV) phức tạp của Magento đòi hỏi trích xuất dữ liệu qua các câu lệnh pivot SQL động, ánh xạ ID số nguyên sang UUID và tái cấu trúc sang schema quan hệ chuẩn hóa trong PostgreSQL nhằm tối ưu hiệu năng truy vấn.

---

Cấu trúc EAV schema chính là lý do khiến phần lớn các dự án chuyển đổi khỏi Magento chuốc lấy thất bại.

Nhìn từ bên ngoài, nó có vẻ dễ xơi: dữ liệu của sản phẩm bị băm ra rải rác ở `catalog_product_entity`, `catalog_product_entity_varchar`, `catalog_product_entity_int`, `catalog_product_entity_decimal`, `catalog_product_entity_datetime`, và `catalog_product_entity_text`. Sáu cái bảng, viết một cái job ETL đơn giản, làm một cuối tuần là xong.

Nhưng rồi bạn phát hiện ra rằng `attribute_id = 75` mang ý nghĩa "tên sản phẩm" (product name) trong cái database *của bạn*, nhưng nó lại mang nghĩa "màu sắc" (color) trong cái database trên môi trường staging. Mỗi một mã ID thuộc tính (attribute ID) được sinh ra tự động ngay tại thời điểm cài đặt (install time) và nó hoàn toàn khác biệt giữa các môi trường với nhau. Bất kỳ script ETL nào dám cả gan gán cứng (hardcode) các mã attribute ID này sẽ lập tức đẻ ra một đống dữ liệu rác bẹp dí (corrupted data) khi mang lên chạy ở production.

**Answer-first:** Chuyển đổi (migration) kiến trúc EAV phức tạp của Magento sang một database quan hệ phẳng (PostgreSQL) không thể sử dụng phương pháp 1-1 vì tính đến 2026, Magento vẫn không hỗ trợ native PostgreSQL. Để migrate EAV thành công sang hệ thống microservices, hãy làm theo các bước: (1) xây dựng một bảng `magento_id_map` để phiên dịch các ID số nguyên của Magento sang UUID, (2) dùng `eav_attribute.attribute_code` (chứ tuyệt đối không dùng `attribute_id`) làm khóa dò tìm (lookup key) bất di bất dịch, (3) áp dụng kỹ thuật SQL pivot động (dynamic SQL pivot) để chuyển đổi cấu trúc (flatten/normalize) thành dữ liệu JSONB hoặc cột phẳng ở thời gian chạy (runtime) thay vì gán cứng, và (4) chạy quá trình trích xuất dữ liệu qua ba giai đoạn: Tải toàn bộ lần đầu (initial full load) qua ETL pipeline → Đồng bộ độ lệch tăng dần (incremental delta) → Đánh giá trước khi chốt hạ (cutover validation). 

## 1. Mô hình Dữ liệu EAV

Một sản phẩm Magento có SKU là `MSH-BLK-L` (Áo sơ mi nam đen, size L) được lưu trữ như thế này:

**`catalog_product_entity`** (bảng chứa thực thể gốc):
```
entity_id | sku           | entity_type_id | attribute_set_id
2841      | MSH-BLK-L     | 4              | 9
```

**`catalog_product_entity_varchar`** (chứa các thuộc tính kiểu chuỗi):
```
entity_id | attribute_id | store_id | value
2841      | 75           | 0        | Men's Black Shirt
2841      | 76           | 0        | MSH-BLK-L
2841      | 97           | 0        | Men's Shirts
```

**`catalog_product_entity_int`** (chứa các thuộc tính kiểu số nguyên):
```
entity_id | attribute_id | store_id | value
2841      | 80           | 0        | 8                ← status (trạng thái): 1=Enabled, 2=Disabled
2841      | 81           | 0        | 4                ← visibility (hiển thị)
2841      | 134          | 0        | 2                ← tax_class_id (nhóm thuế)
```

**`catalog_product_entity_decimal`** (chứa các thuộc tính kiểu số thập phân):
```
entity_id | attribute_id | store_id | value
2841      | 77           | 0        | 299000.0000     ← price (giá)
2841      | 78           | 0        | 0.0000          ← special_price (giá khuyến mãi)
```

Vấn đề nằm ở đây: `attribute_id = 75` mang nghĩa "name" (tên) trong cái database này. Nhưng ở database trên môi trường staging của bạn (vốn được dựng từ một bản cài đặt Magento mới tinh), `attribute_id = 75` hoàn toàn có thể mang nghĩa là "color" (màu sắc). **Các Attribute ID mang tính đặc thù cho từng bản cài đặt (instance-specific), chúng được sinh ra thông qua cơ chế `AUTO_INCREMENT` trong suốt quá trình cài đặt Magento**.

## 2. Cái Bẫy: Gán cứng (Hardcoded) Attribute IDs

Đây là cách tiếp cận ngây ngô nhất, được copy từ vô số câu trả lời trên Stack Overflow:

```sql
-- ❌ SAI BÉT: Gán cứng attribute ID sẽ làm nổ tung production
SELECT
    e.entity_id,
    e.sku,
    v_name.value AS name,
    d_price.value AS price
FROM catalog_product_entity e
LEFT JOIN catalog_product_entity_varchar v_name
    ON v_name.entity_id = e.entity_id AND v_name.attribute_id = 75  -- gán cứng "name"!
LEFT JOIN catalog_product_entity_decimal d_price
    ON d_price.entity_id = e.entity_id AND d_price.attribute_id = 77  -- gán cứng "price"!
WHERE v_name.store_id = 0
```

Câu query này sẽ chạy ra kết quả đúng mười mươi ở môi trường phát triển (dev) của bạn, có khả năng chạy ra kết quả sai lệch ở staging, và sẽ âm thầm trả ra dữ liệu sai bét nhè khi lên production nếu trước đó có ai lỡ chạy lại lệnh re-index của Magento hoặc thêm mới các thuộc tính theo một thứ tự khác.

## 3. Lời Giải: Dò tìm bằng Mã Thuộc tính (Attribute Code)

```sql
-- ✅ CHUẨN XÁC: Dò tìm linh động các attribute ID thông qua bảng eav_attribute
SELECT attr.attribute_id
FROM eav_attribute attr
JOIN eav_entity_type et ON et.entity_type_id = attr.entity_type_id
WHERE et.entity_type_code = 'catalog_product'
  AND attr.attribute_code = 'name';      -- 'name' thì không bao giờ đổi, còn 'attribute_id' thì có
```

Cái cột `attribute_code` là thứ duy nhất bất di bất dịch xuyên suốt mọi instance. `name`, `price`, `sku`, `status`, `visibility` — những cái mã này đã được định nghĩa cứng trong lõi (core) của Magento và không bao giờ thay đổi giữa các bản cài đặt. **Luôn luôn dò tìm các attribute ID từ bảng `eav_attribute` ở thời điểm chạy (runtime). Tuyệt đối không bao giờ được gán cứng chúng.**

## 4. Bảng magento_id_map: Ánh xạ từ Số nguyên → UUID

Mỗi một bản ghi trong Magento đều sử dụng các khóa chính (primary keys) dạng số nguyên sinh tự động `AUTO_INCREMENT` của MySQL. Mọi bản ghi trong nền tảng microservice mới đều sử dụng UUID. Quá trình chuyển đổi (migration) phải bắt đầu bằng việc tạo ra một bảng đối chiếu chéo (cross-reference table) làm bước đi đầu tiên:

```sql
-- Bước Migration 1: Tạo bản đồ định danh (identity map)
CREATE TABLE magento_id_map (
    id              BIGSERIAL PRIMARY KEY,
    entity_type     VARCHAR(64) NOT NULL,    -- 'product', 'customer', 'order'
    magento_id      BIGINT NOT NULL,         -- ID gốc dạng AUTO_INCREMENT của Magento
    platform_uuid   UUID NOT NULL DEFAULT gen_random_uuid(),
    migrated_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_type, magento_id)
);

-- Bơm dữ liệu cho toàn bộ sản phẩm
INSERT INTO magento_id_map (entity_type, magento_id)
SELECT 'product', entity_id
FROM catalog_product_entity
ON CONFLICT (entity_type, magento_id) DO NOTHING;

-- Nghiệm thu: đảm bảo mọi sản phẩm đều đã được cấp UUID
SELECT COUNT(*) AS total_products,
       COUNT(platform_uuid) AS mapped_products
FROM magento_id_map
WHERE entity_type = 'product';
-- Kết quả kỳ vọng: total_products = mapped_products
```

Sau khi hoàn tất bước này, dịch vụ đồng bộ Debezium CDC (sẽ được mô tả ở [Phần 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)) sẽ dùng cái bảng `magento_id_map` này để phiên dịch mọi cái `entity_id` xuất hiện trong các event CDC thành UUID tương ứng của nó trước khi tiến hành đẩy (publish) vào Dapr PubSub.

## 5. SQL Pivot Động: Đọc dữ liệu ở Runtime

Khi các attribute ID đã được dò tìm một cách linh động (dynamically), câu query trích xuất (extraction) sẽ biến thành một trục xoay (pivot) có khả năng chạy mượt mà trên bất kỳ instance Magento nào:

```sql
-- Trích xuất EAV bằng cơ chế dò tìm attribute ID linh động
WITH attr_ids AS (
    -- Dò tìm toàn bộ attribute code ra attribute ID tương ứng của instance Magento NÀY
    SELECT
        attribute_id,
        attribute_code,
        backend_type                -- 'varchar', 'int', 'decimal', 'datetime', 'text'
    FROM eav_attribute
    WHERE entity_type_id = (
        SELECT entity_type_id FROM eav_entity_type
        WHERE entity_type_code = 'catalog_product'
    )
    AND attribute_code IN ('name', 'price', 'special_price', 'status',
                           'visibility', 'description', 'short_description',
                           'tax_class_id', 'weight', 'manufacturer')
)
SELECT
    e.entity_id                                             AS magento_id,
    idmap.platform_uuid                                     AS id,
    e.sku,
    e.attribute_set_id,
    MAX(CASE WHEN a.attribute_code = 'name'
        THEN v.value END)                                   AS name,
    MAX(CASE WHEN a.attribute_code = 'description'
        THEN t.value END)                                   AS description,
    MAX(CASE WHEN a.attribute_code = 'status'
        THEN i.value END)                                   AS status,
    MAX(CASE WHEN a.attribute_code = 'price'
        THEN d.value END)                                   AS price,
    MAX(CASE WHEN a.attribute_code = 'special_price'
        THEN d2.value END)                                  AS special_price,
    MAX(CASE WHEN a.attribute_code = 'weight'
        THEN d3.value END)                                  AS weight,
    e.created_at,
    e.updated_at

FROM catalog_product_entity e
JOIN magento_id_map idmap
    ON idmap.entity_type = 'product' AND idmap.magento_id = e.entity_id

-- Các thuộc tính Varchar (name, manufacturer, v.v.)
LEFT JOIN catalog_product_entity_varchar v
    ON v.entity_id = e.entity_id AND v.store_id = 0
    AND v.attribute_id IN (SELECT attribute_id FROM attr_ids WHERE backend_type = 'varchar')
LEFT JOIN attr_ids a_v ON a_v.attribute_id = v.attribute_id

-- Các thuộc tính Text (description, short_description)
LEFT JOIN catalog_product_entity_text t
    ON t.entity_id = e.entity_id AND t.store_id = 0
    AND t.attribute_id IN (SELECT attribute_id FROM attr_ids WHERE backend_type = 'text')
LEFT JOIN attr_ids a_t ON a_t.attribute_id = t.attribute_id AND a_t = a_v

-- Các thuộc tính số nguyên (status, visibility, tax_class_id)
LEFT JOIN catalog_product_entity_int i
    ON i.entity_id = e.entity_id AND i.store_id = 0
    AND i.attribute_id IN (SELECT attribute_id FROM attr_ids WHERE backend_type = 'int')

-- Các thuộc tính số thập phân (price, special_price, weight)
LEFT JOIN catalog_product_entity_decimal d
    ON d.entity_id = e.entity_id AND d.store_id = 0
    AND d.attribute_id = (SELECT attribute_id FROM attr_ids WHERE attribute_code = 'price')
LEFT JOIN catalog_product_entity_decimal d2
    ON d2.entity_id = e.entity_id AND d2.store_id = 0
    AND d2.attribute_id = (SELECT attribute_id FROM attr_ids WHERE attribute_code = 'special_price')
LEFT JOIN catalog_product_entity_decimal d3
    ON d3.entity_id = e.entity_id AND d3.store_id = 0
    AND d3.attribute_id = (SELECT attribute_id FROM attr_ids WHERE attribute_code = 'weight')

GROUP BY e.entity_id, e.sku, e.attribute_set_id, idmap.platform_uuid, e.created_at, e.updated_at
ORDER BY e.entity_id;
```

Đây là phiên bản query an toàn, đủ tiêu chuẩn chạy production. Phân đoạn CTE `WITH attr_ids AS (...)` chỉ chạy đúng một lần lúc bắt đầu truy vấn để giải mã toàn bộ attribute ID từ trạng thái hiện tại của database — tuyệt đối không có sự gán cứng nào, cũng không có hằng số (constants) nào mang tính đặc thù cho từng môi trường cả.

## 6. Lớp Chuyển đổi Dữ liệu bằng Go (Transformation Layer)

Sau khi được trích xuất bằng SQL, dữ liệu cần phải trải qua khâu biến đổi (transformation) trước khi được nhét vào PostgreSQL của Catalog Service:

```go
// migration/transformer/product_transformer.go

type MagentoProduct struct {
    MagentoID   int64
    UUID        string
    SKU         string
    Name        string
    Description string
    Status      int   // 1=Enabled, 2=Disabled
    Price       float64
    SpecialPrice *float64
    Weight      float64
    CreatedAt   time.Time
    UpdatedAt   time.Time
}

func TransformProduct(mp *MagentoProduct) *catalog.Product {
    p := &catalog.Product{
        ID:          mp.UUID,
        SKU:         mp.SKU,
        Name:        mp.Name,
        Description: mp.Description,
        Status:      transformStatus(mp.Status),
        // Chuyển đổi giá trị price dạng float64 sang kiểu Money (tuyệt đối không cho float lọt qua tầng API)
        Price: money.FromFloat("VND", mp.Price),
        Weight: mp.Weight,
        CreatedAt: mp.CreatedAt,
        UpdatedAt: mp.UpdatedAt,
    }

    if mp.SpecialPrice != nil {
        p.SpecialPrice = money.FromFloat("VND", *mp.SpecialPrice)
    }

    return p
}

func transformStatus(magentoStatus int) catalog.ProductStatus {
    switch magentoStatus {
    case 1: return catalog.ProductStatus_ENABLED
    case 2: return catalog.ProductStatus_DISABLED
    default: return catalog.ProductStatus_UNSPECIFIED
    }
}
```

## 7. Customer EAV: Bổn Cũ Soạn Lại

Dữ liệu Customer trong Magento cũng xài EAV (bảng `customer_entity` + các bảng hậu tố theo kiểu dữ liệu). Quá trình trích xuất cũng tuân theo y xì đúc mô hình trên:

```sql
-- Trích xuất Customer kèm tính năng dò tìm thuộc tính linh động
WITH customer_attrs AS (
    SELECT attribute_id, attribute_code, backend_type
    FROM eav_attribute
    WHERE entity_type_id = (
        SELECT entity_type_id FROM eav_entity_type
        WHERE entity_type_code = 'customer'
    )
    AND attribute_code IN ('firstname', 'lastname', 'dob', 'gender', 'taxvat')
)
SELECT
    ce.entity_id                    AS magento_id,
    idmap.platform_uuid             AS id,
    ce.email,
    ce.group_id                     AS customer_group,
    ce.is_active,
    ce.created_at,
    MAX(CASE WHEN ca.attribute_code = 'firstname'
        THEN v.value END)           AS first_name,
    MAX(CASE WHEN ca.attribute_code = 'lastname'
        THEN v.value END)           AS last_name
FROM customer_entity ce
JOIN magento_id_map idmap
    ON idmap.entity_type = 'customer' AND idmap.magento_id = ce.entity_id
LEFT JOIN customer_entity_varchar v
    ON v.entity_id = ce.entity_id
    AND v.attribute_id IN (SELECT attribute_id FROM customer_attrs WHERE backend_type = 'varchar')
JOIN customer_attrs ca ON ca.attribute_id = v.attribute_id
GROUP BY ce.entity_id, ce.email, ce.group_id, ce.is_active, ce.created_at, idmap.platform_uuid;
```

## 8. Đồng bộ Độ lệch Tăng dần (Incremental Delta Sync)

Sau lần tải cày toàn bộ (initial full load) lúc ban đầu, đường ống CDC (Debezium, được mô tả ở [Phần 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)) sẽ đứng ra hứng chịu nhiệm vụ đồng bộ các thay đổi tăng dần. Tuy nhiên, trong khoảng thời gian chờ Debezium được deploy, một tiến trình đồng bộ dạng quét polling (polling-based delta sync) sẽ đứng ra trám chỗ:

```sql
-- Delta sync: lấy ra những sản phẩm đã bị thay đổi kể từ lần trích xuất gần nhất
SELECT e.entity_id
FROM catalog_product_entity e
WHERE e.updated_at > :last_sync_timestamp
ORDER BY e.updated_at ASC
LIMIT 1000;
```

Đây chỉ thuần túy là một phương án **chữa cháy (fallback)** — nó sẽ bị mù hoàn toàn trước các thao tác xóa (DELETEs) và rất dễ vỡ mồm nếu đồng hồ giữa các server bị lệch (clock skew). Ngay khi Debezium được khởi chạy (cột mốc Phase 1), cái cục đồng bộ dạng polling này sẽ bị tắt bỏ ngay lập tức.

## 9. Nghiệm thu: Cửa Ải Cuối Cùng Trước Khi Hoàn Tất Trích Xuất

```bash
#!/bin/bash
# validate-product-extraction.sh

MAGENTO_COUNT=$(mysql -h $MAGENTO_DB -e "
    SELECT COUNT(*) FROM catalog_product_entity
    WHERE status = 1  -- Chỉ đếm hàng đang Enabled (được mở bán)
" | tail -1)

PLATFORM_COUNT=$(psql $PLATFORM_DB -t -c "
    SELECT COUNT(*) FROM products WHERE status = 'ENABLED'
")

echo "Số lượng sản phẩm Enabled trên Magento: $MAGENTO_COUNT"
echo "Số lượng sản phẩm trên Nền tảng mới: $PLATFORM_COUNT"

# Hai con số này phải khớp nhau chằn chặn thì mới được phép đi tiếp sang Phase 1
if [ "$MAGENTO_COUNT" -ne "$PLATFORM_COUNT" ]; then
    echo "❌ Lệch số — quá trình trích xuất chưa hoàn thiện"
    exit 1
fi

# Chạy test lấy mẫu: bốc đại (spot-check) 100 sản phẩm
psql $PLATFORM_DB -c "
    SELECT p.sku, p.name, p.price
    FROM products p
    ORDER BY RANDOM()
    LIMIT 100
" > /tmp/platform_sample.csv

echo "✅ Số lượng đã khớp. Vui lòng kiểm tra file lấy mẫu ở /tmp/platform_sample.csv"
```

## Bài Học Xương Máu (Key Takeaways)

1. **Không bao giờ được gán cứng `attribute_id`** — phải luôn dò tìm thông qua `eav_attribute.attribute_code`
2. **Dựng bảng `magento_id_map` đầu tiên** — mọi bước migration sau này đều sẽ phụ thuộc vào cái bảng tham chiếu chéo UUID này
3. **Dùng kỹ thuật SQL pivot động** — cách dùng CTE sẽ đảm bảo truy vấn chạy ngon trên mọi instance Magento bất chấp thứ tự lúc cài đặt
4. **Nghiệm thu (Validate) số lượng đếm trước khi vào Phase 1** — chỉ cần hai con số đếm (count) bị lệch nhau cũng đủ để kết luận quá trình trích xuất của bạn bị thủng lỗ chỗ
5. **Giá (Price) nằm trong MySQL là decimal, nhưng vào proto thì phải là Money** — hãy chuyển đổi tường minh (explicitly), tuyệt đối không để lọt kiểu float qua được tầng API

Trích xuất EAV là công đoạn tốn sức người (labor-intensive) nhất trong toàn bộ chuỗi migration. Nhưng một khi bảng `magento_id_map` đã được bơm đầy và câu lệnh dynamic pivot báo về kết quả count chuẩn xác, bạn đã chính thức sẵn sàng để dấn thân vào các giai đoạn (phase) migration thực sự. [Phần 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) sẽ cho bạn thấy cách Debezium biến công việc đồng bộ tăng dần thành một dòng chảy liên tục và siêu cẩn mật (reliable) như thế nào — bằng việc đá văng cái cục polling-based delta đi để thế chỗ bằng kỹ thuật CDC chọc thẳng vào tầng binlog.

## Câu Hỏi Thường Gặp (FAQ)

### Tại sao tôi không thể dùng luôn cái tính năng import/export CSV có sẵn của Magento thay vì đi hì hục cào SQL trực tiếp?

Cái tính năng CSV import/export của Magento không hề chịu xuất ra các mối quan hệ của thuộc tính, và cũng chẳng chịu đẻ ra cái bảng đối chiếu `magento_id_map` mà bạn đang rất cần. Xuất ra CSV sẽ chỉ trả về cho bạn các dòng dữ liệu dạng bẹt (flat row) cho từng sản phẩm — tức là ném sạch đi toàn bộ cấu trúc EAV — chưa kể một con Magento nguyên thủy (vanilla) không cắm extension sẽ bị kẹt trần giới hạn xuất đúng 5,000 sản phẩm là ngỏm. Với hơn 10,000 SKU, cào SQL trực tiếp vào MySQL là con đường duy nhất có thể kham nổi khối lượng này mà không cần phải can thiệp (modification) vào code.

*Lưu ý kiến trúc 2026 (E-E-A-T Context): Magento/Adobe Commerce hoàn toàn không tương thích native với PostgreSQL. Đừng cố gắng chạy Magento core trên PostgreSQL bằng các gói proof-of-concept của cộng đồng. Thay vào đó, hãy duy trì MySQL/MariaDB cho Magento và dùng các kịch bản SQL extraction/ETL này để đồng bộ và chuyển đổi (normalize) schema EAV "dài và gầy" thành một PostgreSQL schema hiệu năng cao cho hệ thống microservices đích.*

### Tôi có phải giữ cái bảng magento_id_map này sống vĩnh viễn không?

Có — cho đến khi nào quá trình chốt hạ (cutover) ở Phase 3 hoàn tất. Cái đường ống đồng bộ CDC (Phần 6), bộ chuyển tiếp ghi dữ liệu kép (dual-write adapter - Phần 7), và bộ phân xử xung đột (conflict resolver - Phần 7) đều sống phụ thuộc vào bảng `magento_id_map` để phiên dịch các ID dạng số nguyên của Magento sang UUID mỗi khi chúng xử lý sự kiện (event). Chừng nào Phase 3 xong xuôi và Magento chính thức bị rút ống thở (decommissioned), cái bảng này mới được phép đưa vào kho lưu trữ (archive) (không được xóa sạch — phải giữ lại làm đường mòn kiểm toán - audit trail).

### Điều gì sẽ xảy ra nếu có hai bản cài đặt Magento cùng xài chung một cái `attribute_code` nhưng lại mang ý nghĩa (semantics) hoàn toàn khác nhau?

Trường hợp này sẽ xảy ra khi các thuộc tính tự chế (custom attributes) được tạo ra bởi các extension bên thứ ba lười biếng hay xài mấy cái tên mã kiểu vô thưởng vô phạt như `custom_attribute_1`. Trong tình cảnh đó, hãy kiểm tra thêm các cột `eav_attribute.frontend_label` và `eav_attribute.source_model` để gỡ rối (disambiguate). Hãy đảm bảo bạn đã ghi chép lại toàn bộ các thuộc tính mang ý nghĩa nhập nhằng này vào một trường comment bên trong bảng `magento_id_map` của bạn trước khi bấm nút trích xuất — việc phải đi dọn dẹp đống rác này sau khi đã trích xuất xong xuôi đắt đỏ hơn gấp tỷ lần.

---

*Bài viết này nằm trong **[Series Chuyển đổi sang Composable Commerce](/series/composable-commerce-migration/)**. Hãy xem toàn bộ mục lục để nắm bắt ngữ cảnh kiến trúc đầy đủ nhất.*

*Bạn cần hỗ trợ đánh giá rủi ro cho đợt chuyển đổi nền tảng sắp tới? â†’ [Đặt lịch Tư vấn Kiến trúc 1:1](/hire/)*

---

---

---

[← Chương trước: Phần 4: gRPC Internal + REST Gateway](/series/composable-commerce-migration/part-4-grpc-rest-gateway/) | [Mục lục Series](/series/composable-commerce-migration/) | [Chương tiếp theo: Phần 6: Giai Đoạn 1 — Strangler Fig Read-Only →](/series/composable-commerce-migration/part-6-phase1-strangler-fig/)
