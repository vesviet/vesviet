# Google Search Console Performance Audit & Twin SEO Review (2026-09-14)

> **Audit Period:** 2026-08-16 – 2026-09-12 (Last 28 days)  
> **Source Files Audited:**  
> - `tmp/tanhdev.com-Performance-on-Search-2026-09-14.zip`  
> - `tmp/learn.tanhdev.com-Performance-on-Search-2026-09-14.zip`  
> **Standard:** Technical Article Standard 2027 & Twin SEO Authority 2027 (`vesviet-team` pack)  
> **Lead Auditor:** SEO Analyst (`vesviet-team` / Antigravity A2A)

---

## 1. Executive Summary & Kiến Trúc Dữ Liệu GSC

### 1.1. Phát hiện cốt lõi về Kiến trúc GSC Property (Domain vs URL-Prefix)
Khi phân tích và đối soát chéo 2 file xuất GSC, chúng tôi phát hiện cấu trúc xuất dữ liệu như sau:
1. **`tanhdev.com-Performance-on-Search-2026-09-14.zip` là Domain Property (`sc-domain:tanhdev.com`)**:
   - Bao hàm toàn bộ lưu lượng của Apex domain `tanhdev.com` cùng tất cả subdomains: `learn.tanhdev.com`, `wiki.tanhdev.com`, và `dw.tanhdev.com`.
   - Chứa **424 URLs** trong `Pages.csv` và **564 queries** trong `Queries.csv`.
   - **Tách lọc theo Hostname:**
     - **Apex `tanhdev.com` (vesviet - Flagship / Citation Target):** 293 URLs | **48 clicks** | **10,869 impressions** | CTR 0.44%
     - **Subdomain `learn.tanhdev.com` (learn - Vietnamese Research Corpus):** 125 URLs | **6 clicks** | **394 impressions** | CTR 1.52%
     - **Subdomain `wiki.tanhdev.com`:** 5 URLs | 0 clicks | 30 impressions
     - **Subdomain `dw.tanhdev.com`:** 1 URL | 0 clicks | 3 impressions
2. **`learn.tanhdev.com-Performance-on-Search-2026-09-14.zip` là URL-Prefix Property (`https://learn.tanhdev.com/`)**:
   - Đo lường riêng biệt phân vùng nghiên cứu tiếng Việt: **6 clicks** | **383 impressions (Chart) / 394 impressions (Pages)** | **Avg Position: 19.9**.

### 1.2. Bảng Tổng Hợp Chỉ Số Vĩ Mô (Macro KPIs)

| Chỉ số (28 ngày qua) | Domain Property (tanhdev.com toàn diện) | Apex Flagship (tanhdev.com riêng) | Subdomain (learn.tanhdev.com riêng) | Đánh giá xu hướng |
| :--- | :--- | :--- | :--- | :--- |
| **Tổng Clicks (Chart/Pages)** | **54 clicks** | **48 clicks** | **6 clicks** | Clicks tập trung vào bài toán Routing & Banking |
| **Tổng Impressions** | **11,296** | **10,869** | **394** | Phủ sóng 119 quốc gia, US chiếm 46% |
| **CTR trung bình** | **0.47%** | **0.44%** | **1.52%** | CTR trên learn cao gấp 3.4x tanhdev |
| **Vị trí TB (Week 1 -> Week 4)** | **41.0 -> 23.0** | **41.0 -> 23.0** | **32.7 -> 7.1** | **Bứt phá:** Vị trí thăng hạng mạnh vào Page 1 & 2 |
| **Số URLs có hiển thị** | 424 URLs | 293 URLs | 125 URLs | Indexation diện rộng, độ phủ cao |
| **Số URLs có clicks (>0)** | 37 URLs | 31 URLs | 6 URLs | 8.7% URL tạo click (tiêu chuẩn blog kỹ thuật mới) |
| **Tỷ lệ Anonymized Queries** | 86.5% clicks | 87.5% clicks | 83.3% clicks | Traffic chủ yếu từ long-tail queries siêu chuyên sâu |

---

## 2. Phân Tích Chuyên Sâu: tanhdev.com (Vesviet - Flagship Citation Target)

### 2.1. Diễn biến Xu Hướng theo Tuần (Weekly Trend)
- **Week 1 (16/08 - 22/08):** 15 clicks | 2,804 impr | CTR 0.53% | Vị trí TB: **41.0**
- **Week 2 (23/08 - 29/08):** 21 clicks | 3,024 impr | CTR 0.69% | Vị trí TB: **48.8**
- **Week 3 (30/08 - 05/09):** 10 clicks | 2,667 impr | CTR 0.37% | Vị trí TB: **35.3**
- **Week 4 (06/09 - 12/09):** 6 clicks | 2,483 impr | CTR 0.24% | Vị trí TB: **23.0** *(Nhảy vọt 18 bậc!)*
> **Nhận định:** Thứ hạng trung bình cải thiện vượt bậc (từ trang 4-5 nhảy lên trang 2). Tuy nhiên số click tạm thời chậm lại vì các từ khóa mới gia nhập top 20-30 có impression lớn nhưng chưa tối ưu Title/Meta để hút click.

### 2.2. Phân Bổ Địa Lý (Geographic Footprint)
- **United States:** **5,008 impressions (46.1%)**, 1 click, vị trí TB 26.62.
- **India:** 907 impressions, 2 clicks, vị trí TB 53.59.
- **Vietnam:** 709 impressions, **20 clicks (CTR 2.82%)**, vị trí TB 45.84. (Người dùng kỹ sư tại VN tìm kiếm tài liệu chuyên sâu bằng tiếng Anh click rất mạnh).
- **Philippines (522 impr), UK (469 impr), Indonesia (279 impr, 4 clicks), Mexico (232 impr), Switzerland (224 impr), Bangladesh (224 impr), Turkey (218 impr).**
> **Kết luận E-E-A-T:** Website đã đạt độ nhận diện toàn cầu (119 quốc gia). Thị trường trọng điểm Hoa Kỳ đang tiếp cận mạnh ở tầng nhận thức (Impressions).

### 2.3. Thiết Bị (Devices)
- **Desktop:** **9,644 impressions (88%)** | 40 clicks | CTR 0.41% | Vị trí TB 38.87.
- **Mobile:** **1,313 impressions (12%)** | 12 clicks | CTR 0.91% | Vị trí TB 21.05.
- **Tablet:** 21 impressions | 0 clicks.
> **Nhận định:** Độc giả của tanhdev.com là Software Architects, Tech Leads, Senior Engineers đọc tài liệu, diagram, code Golang/Kubernetes trên máy tính trong giờ làm việc.

### 2.4. Top 10 Bài Viết Hiệu Suất Cao Nhất (Top Clicked Pages)
1. `https://tanhdev.com/posts/osrm-vs-graphhopper-architecture-comparison/`  
   **7 clicks | 141 impr | CTR 4.96% | Pos 11.46**  
   *(Bài viết đứng đầu toàn domain; Google rank cả 2 anchor fragments H2 trực tiếp trên SERP)*.
2. `https://tanhdev.com/series/core-banking-developer/part-7-build-mini-core-banking/`  
   **3 clicks | 39 impr | CTR 7.69% | Pos 16.33**
3. `https://tanhdev.com/series/shopee-architecture/01-microservices-foundation/`  
   **3 clicks | 37 impr | CTR 8.11% | Pos 13.22**
4. `https://tanhdev.com/series/shopee-architecture/02-flash-sale-engine/`  
   **2 clicks | 129 impr | CTR 1.55% | Pos 8.56** *(Top 10 Google!)*
5. `https://tanhdev.com/posts/cloudflare-d1-durable-objects-realtime-cart/`  
   **2 clicks | 109 impr | CTR 1.83% | Pos 20.84**
6. `https://tanhdev.com/posts/go-pprof-kubernetes-remote-profiling/`  
   **2 clicks | 98 impr | CTR 2.04% | Pos 26.11**
7. `https://tanhdev.com/posts/osrm-shared-memory-kubernetes-live-traffic/`  
   **2 clicks | 54 impr | CTR 3.70% | Pos 17.09**
8. `https://tanhdev.com/posts/building-custom-golang-vector-database-engine-hnsw/`  
   **2 clicks | 46 impr | CTR 4.35% | Pos 23.28**
9. `https://tanhdev.com/series/alipay-double-11/executive-summary/`  
   **2 clicks | 44 impr | CTR 4.55% | Pos 9.27** *(Top 10 Google!)*
10. `https://tanhdev.com/posts/alipay-double-11-architecture-tps/`  
    **2 clicks | 22 impr | CTR 9.09% | Pos 10.68**

### 2.5. Bằng chứng Trích Xuất SERP Đoạn Trích (H2 Fragment Snippet Extraction)
Trong `Pages.csv`, Google đã index và hiển thị trực tiếp 2 section anchor link:
- `.../osrm-vs-graphhopper-architecture-comparison/#graphhopper-the-java-soul-with-infinite-runtime-flexibility`: **Pos 6.64 | CTR 9.09%**
- `.../osrm-vs-graphhopper-architecture-comparison/#osrm-the-c-titan-of-speed-and-memory-optimization`: **Pos 6.64 | CTR 9.09%**
> **Ý nghĩa chiến lược:** Cấu trúc Answer-First (BLUF) và H2 rõ ràng chuẩn 2027 đã được Google phân tách thành sitelink/fragment độc lập để trả lời trực tiếp ý định tìm kiếm của người dùng!

---

## 3. Phân Tích Cụm Chủ Đề (Topic Clusters) & Từ Khóa Tiềm Năng (Striking Distance)

### 3.1. Hiệu Suất Theo Cụm Chủ Đề Chiến Lược

| Cụm Chủ Đề | Số Queries | Impressions | Clicks | CTR | Phân Tích Cơ Hội |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Banking & Fintech Architecture** | 60 | 1,150 | 0 | 0.00% | **Mỏ vàng chưa khai thác:** `composable banking architecture` (186 impr, pos 28.5), `composable banking` (156 impr, pos 44.9), `core banking system architecture` (127 impr, pos 81.8). |
| **E-Commerce & High-Concurrency Sales** | 26 | 373 | 0 | 0.00% | `ecommerce microservices architecture diagram` (115 impr, pos 49.8), `e commerce microservice architecture` (81 impr, pos 73.9). |
| **Golang & Performance Profiling** | 85 | 368 | 0 | 0.00% | `agentic memory` (116 impr, pos 76.2), `go microservices` (66 impr, pos 52.2), `golang goroutine pool` (12 impr, pos 44.0). |
| **Geospatial & Routing (OSRM, GraphHopper)** | 23 | 240 | 6 | **2.50%** | **Cụm sinh lời cao nhất:** `graph hopper distance matrix` (58 impr, pos 11.8), `osrm vs graphhopper` (19 impr, 6 clicks, CTR 31.6%, pos 8.9). |
| **AI, Agents & Memory Architecture** | 30 | 168 | 0 | 0.00% | `vibe coding governance` (33 impr, pos 90.4), `+"ai ethics & policy"` (18 impr, pos 5.22). |
| **Microservices & Distributed Systems** | 33 | 146 | 1 | 0.68% | `mysql sharding alternative` (75 impr, pos 15.93), `replace mysql sharding` (5 impr, pos 7.0). |
| **Ride-Hailing & Realtime Dispatch** | 24 | 107 | 0 | 0.00% | `surge multiplier meaning` (24 impr, pos 8.5), `uber ramen` (11 impr, pos 9.55). |
| **Cloud Native, K8s & Edge (Cloudflare)** | 32 | 91 | 0 | 0.00% | `eks vs ecs` (15 impr, pos 46.1), `eks fargate pricing` (8 impr, pos 16.4). |

### 3.2. Danh Sách "Striking Distance" (Từ Khóa Vị Trí 4 - 20 Cần Đẩy Lên Top 3)
Đây là các từ khóa đã ở trang 1 hoặc đầu trang 2 Google, có lượng tìm kiếm tốt nhưng chưa có click. Chỉ cần tinh chỉnh H1/Title, Meta Description và thêm bảng tóm tắt BLUF là sẽ tạo ra traffic ngay:

1. **`mysql sharding alternative`** — **75 impressions | Pos 15.93 | 0 clicks**  
   *Target URL:* `/posts/mysql-scaling-sharding-tidb-architecture/` & `/posts/mysql-scalability-guide/`  
   *Hành động:* Sửa Title thành: `Top 5 MySQL Sharding Alternatives (TiDB, Vitess, Citus) Architecture Guide`.
2. **`graph hopper distance matrix`** — **58 impressions | Pos 11.83 | 0 clicks**  
   *Target URL:* `/posts/graphhopper-distance-matrix-production-guide/`  
   *Hành động:* Title hiện tại cần thêm keyword biến thể và hook: `GraphHopper Distance Matrix API: High-Throughput Routing at Scale`.
3. **`graph hopper maps distance matrix`** — **39 impressions | Pos 13.82 | 0 clicks**  
   *Target URL:* `/posts/graphhopper-distance-matrix-production-guide/`
4. **`graph hopper matrix`** — **33 impressions | Pos 15.88 | 0 clicks**
5. **`surge multiplier meaning`** — **24 impressions | Pos 8.50 (Trang 1!) | 0 clicks**  
   *Target URL:* `/series/ride-hailing-realtime-architecture/part-3-surge-pricing-algorithm/`  
   *Hành động:* Thêm định nghĩa BLUF ngắn gọn 25 từ ngay dưới H2 để bắt Snippet.
6. **`cache stampede vs cache avalanche`** — **18 impressions | Pos 9.78 (Trang 1!) | 0 clicks**  
   *Target URL:* `/series/high-concurrency-systems/caching-vulnerabilities-penetration-breakdown-avalanche/`  
   *Hành động:* Bài viết này vừa được nâng cấp trong đợt pull hôm nay! Cần submit index lại trên GSC.
7. **`uber ramen`** — **11 impressions | Pos 9.55 (Trang 1!) | 0 clicks**  
   *Target URL:* `/series/ride-hailing-realtime-architecture/part-6-realtime-push-ramen/`

### 3.3. Các Trang Có Impressions Cực Lớn Nhưng 0 Clicks (Cần Cải Thiện Vị Trí)
- `https://tanhdev.com/posts/composable-banking-architecture/`: **741 impressions | Pos 37.5**  
  *Vấn đề:* Thứ hạng đang ở trang 4. Nhu cầu tìm kiếm về kiến trúc ngân hàng khả biến cực kỳ lớn. Cần liên kết nội bộ từ các bài viết trong series Core Banking sang bài viết này và bổ sung sơ đồ Mermaid.
- `https://tanhdev.com/series/architectural-tradeoffs-showdowns/01-http-rest-json-vs-grpc-protobuf/`: **424 impressions | Pos 44.7**
- `https://tanhdev.com/series/core-banking-developer/executive-summary/`: **370 impressions | Pos 75.3**
- `https://tanhdev.com/posts/blueprint-ecommerce-microservices-architecture-diagram/`: **359 impressions | Pos 64.0**

---

## 4. Phân Tích Chuyên Sâu: learn.tanhdev.com (Vietnamese Research Corpus)

### 4.1. Bước Nhảy Vọt Về Thứ Hạng (Rank Surge)
- Vị trí trung bình trong 28 ngày là **19.9**.
- Tuy nhiên xét theo từng tuần:
  - Week 1: Vị trí **32.7**
  - Week 2: Vị trí **27.3**
  - Week 3: Vị trí **13.7**
  - **Week 4 (06/09 - 12/09): Vị trí 7.1 (CHẠM TOP 10 TOÀN TRANG!)**
> **Ý nghĩa:** Kho nghiên cứu tiếng Việt đang được Google đánh giá độ uy tín (Authority) tăng vọt. Thuật toán xếp hạng đã đưa hàng loạt bài viết kỹ thuật vào Trang 1 Google tại Việt Nam và cả người dùng tiếng Việt tại Hoa Kỳ.

### 4.2. Top Bài Viết Trên learn.tanhdev.com
- **Đã có click:**
  1. `/radar/cloud-native-ai-envoy-gateway-kubernetes-dapr-agents-2026/`: 1 click | 5 impr | CTR 20.0% | Pos 10.2
  2. `/posts/zero-trust-service-mesh-security-spiffe-spire-istio-golang/`: 1 click | 4 impr | CTR 25.0% | Pos 7.0
  3. `/posts/gitops-at-scale-kubernetes-argocd-microservices/`: 1 click | 3 impr | CTR 33.3% | Pos 6.67
  4. `/series/composable-commerce-migration/part-8-phase3-full-cutover/`: 1 click | 2 impr | CTR 50.0% | Pos 17.5
  5. `/series/core-banking-developer/`: 1 click | 2 impr | CTR 50.0% | Pos 34.5
  6. `/posts/golang-pprof-profiling-memory-cpu-tutorial/`: 1 click | 2 impr | CTR 50.0% | Pos 39.0
- **Đang ở Top 10 Google nhưng 0 click (Cơ hội chuyển đổi ngay):**
  - `/series/core-banking-architecture/part-2-distributed-sql-acid-latency/`: **Pos 7.22 | 23 impr | 0 clicks**
  - `/series/ecommerce-order-allocation/part-7-distance-matrix-routing/`: **Pos 7.74 | 19 impr | 0 clicks**
  - `/radar/2026-04/`: **Pos 9.67 | 18 impr | 0 clicks**
  - `/posts/building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs/`: **Pos 4.92 (Top 5!) | 13 impr | 0 clicks**
  - `/series/ai-driven-playbook/part-3b-ai-code-review-quality-gates/`: **Pos 7.20 | 10 impr | 0 clicks**
  - `/series/composable-commerce-migration/part-3-golang-kratos/`: **Pos 5.38 (Top 5!) | 8 impr | 0 clicks**

---

## 5. Đánh Giá Tuân Thủ Mô Hình Song Sinh (Twin SEO Authority Audit)

Theo quy định tại `overlays/vesviet-content/rules/seo-authority.md`:
1. **Phân định vai trò (Authority Split):**
   - `tanhdev.com` (`en`) đóng vai trò Citation Target cho các AI Engine (AI Overviews, Perplexity, SearchGPT) và độc giả quốc tế (119 quốc gia).
   - `learn.tanhdev.com` (`vi`) đóng vai trò Research Corpus phục vụ thị trường kỹ sư Việt Nam.
2. **Kiểm tra tự ăn thịt từ khóa (Cannibalization Check):**
   - 12 query trùng lặp xuất hiện trong cả 2 file nén thực chất là do `tanhdev.com` export ở cấp độ Domain Property nên bao hàm cả subdomain `learn.tanhdev.com`.
   - Đối soát query thực tế: Các query tiếng Việt (`e2e testing là gì`, `debezium là gì`, `phát triển phần mềm hướng dịch vụ`) chỉ trả về URL của `learn.tanhdev.com`. Các query tiếng Anh trả về `tanhdev.com`.
   - **Kết quả:** **KHÔNG CÓ TÌNH TRẠNG CANNIBALIZATION.**
3. **Quy tắc Dòng chảy Thẩm quyền Một chiều (One-Way Authority Flow):**
   - Các bài viết trên `learn` liên kết thẩm quyền lên flagship `tanhdev.com`.
   - Không có liên kết ngược phá vỡ cấu trúc.
   - Mỗi host giữ canonical riêng của mình (`canonicalURL` độc lập), hoàn toàn đúng chuẩn chống spam 2026-2027.

---

## 6. Kế Hoạch Hành Động Ưu Tiên (Actionable Plan)

### Giai đoạn 1: Quick-Wins tối ưu CTR cho Từ khóa Striking Distance (1-3 ngày)
- [ ] **Tối ưu Meta Description & Title cho 5 bài viết Top Striking:**
  1. `tanhdev/posts/mysql-scaling-sharding-tidb-architecture.md`: Thêm từ khóa `MySQL Sharding Alternatives (TiDB vs Vitess vs Citus)` vào H1 và Title.
  2. `tanhdev/posts/graphhopper-distance-matrix-production-guide.md`: Đưa cụm `GraphHopper Distance Matrix API` vào vị trí đầu của Title (≤60 chars).
  3. `tanhdev/posts/composable-banking-architecture.md`: Bổ sung bảng so sánh Core Banking Monolith vs Composable Banking ngay đầu bài để lấy Featured Snippet.
  4. `learn/posts/building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs.md`: Đổi meta description tiếng Việt hấp dẫn hơn với các số liệu benchmark throughput (ví dụ: `Xử lý 1.2M msg/sec với Go và NATS JetStream`).
  5. `learn/series/core-banking-architecture/part-2-distributed-sql-acid-latency.md`: Tối ưu meta cho vị trí 7.22 để chuyển đổi 23 lượt hiển thị thành click.

### Giai đoạn 2: Củng cố Internal Linking Hub-and-Spoke (Tuần tới)
- [ ] Bổ sung liên kết 2 chiều giữa Pillar Post `composable-banking-architecture` (741 impr) với Series `core-banking-developer` (8 phần).
- [ ] Liên kết từ các bài viết routing (`osrm-vs-graphhopper`, `graphhopper-distance-matrix`) sang Series `ride-hailing-realtime-architecture`.

### Giai đoạn 3: Tận dụng các bài viết vừa nâng cấp trong đợt Git Pull hôm nay (14/09)
- [ ] Đợt pull vừa qua vừa bổ sung các bài viết chuyên sâu:
  - `high-concurrency-systems/caching-vulnerabilities-penetration-breakdown-avalanche.md` -> Khớp với query `cache stampede vs cache avalanche` (Pos 9.78).
  - `high-concurrency-systems/database-sharding-read-write-splitting.md` -> Khớp với query `mysql sharding alternative` (Pos 15.93).
  - Series `ai-code-review-vibe-coding` (700 rounds research) -> Đón đầu các query `vibe coding governance` và `ai code review`.
- [ ] Khuyến nghị submit URL Inspection trên Google Search Console cho các URL vừa nâng cấp để Google re-crawl và cập nhật thuật toán xếp hạng sớm nhất.

---
*Báo cáo được khởi tạo tự động bởi SEO Analyst (`vesviet-team` pack).*  
*Dữ liệu gốc được lưu trữ tại: `reports/gsc_performance_audit_2026_09_14.json`*
