# Báo Cáo SEO Audit: Series Cornerstone Technologies

**Ngày thực hiện:** 2026-07-25
**Người thực hiện:** `@seo-analyst`
**Mục tiêu Audit:** Đánh giá chất lượng SEO (Traditional & AEO/GEO), mức độ tuân thủ Information Gain và AI Extractability của 5 bài viết mới trong series `cornerstone-technologies`.
**Tình trạng:** Pre-publish Audit (Bản Draft).

---

## 1. NATS JetStream & Golang: Kiến trúc & Hướng dẫn Production

* **URL dự kiến:** `series/cornerstone-technologies/nats-jetstream-golang-production-guide`
* **Traditional SEO:**
  * Keyword Optimization: Tối ưu tốt cho từ khóa "nats jetstream golang" (Primary) và "nats vs kafka" (Secondary).
  * Internal Links: Có 3 internal links trích xuất về `core-banking-developer`, `alipay-double-11`, và trang `_index.md`.
  * Heading Structure: Cấu trúc H2/H3 phân cấp chuẩn.
  * **Đánh giá chung:** `Pass`
* **AEO / GEO & AI Extractability:**
  * Answer-First: Mỗi thẻ H2 đều có đoạn text tóm tắt (< 60 từ) giải thích trực diện.
  * Fact Density: Có chứa số liệu benchmark rõ ràng (115k RPS, <2ms latency, ~30MB idle RAM).
  * Lỗi / Thiếu sót: Không có.
  * **Đánh giá chung:** `Pass` (AI Extractability Score: 100/100)
* **E-E-A-T:** Có "firsthand account" giải quyết vấn đề slow consumer.

---

## 2. Temporal Workflow & Golang: Kiến trúc & Production Guide

* **URL dự kiến:** `series/cornerstone-technologies/temporal-workflow-go-architecture`
* **Traditional SEO:**
  * Keyword Optimization: Tối ưu tốt cho "temporal workflow golang".
  * Internal Links: Đầy đủ 3 links.
  * **Đánh giá chung:** `Pass`
* **AEO / GEO & AI Extractability:**
  * Answer-First: Tuân thủ quy tắc 60 từ.
  * Fact Density: Có so sánh cụ thể về Timeouts và scale workers.
  * **Đánh giá chung:** `Pass` (AI Extractability Score: 95/100)
* **E-E-A-T:** Tác giả chia sẻ kinh nghiệm xử lý lỗi "Non-Deterministic Error" kinh điển trong Go.

---

## 3. Zero-Trust Architecture cho Microservices: Toàn tập mTLS & Go

* **URL dự kiến:** `series/cornerstone-technologies/zero-trust-architecture-microservices`
* **Traditional SEO:**
  * Keyword Optimization: Tốt. Focus vào "zero trust architecture microservices".
  * YMYL Flag: Kích hoạt (Security). Bài viết có độ chính xác kỹ thuật cao, link đến chuẩn NIST.
  * **Đánh giá chung:** `Pass`
* **AEO / GEO & AI Extractability:**
  * Answer-First: Áp dụng đầy đủ, trả lời trực diện cấu trúc mTLS, JWT.
  * Fact Density: Benchmark latency mTLS overhead <2ms.
  * **Đánh giá chung:** `Pass` (AI Extractability Score: 100/100)
* **E-E-A-T:** Trích dẫn các kinh nghiệm setup SPIFFE/SPIRE không gây downtime.

---

## 4. Vector Database là gì? Kiến trúc HNSW & RAG Pipeline (Qdrant)

* **URL dự kiến:** `series/cornerstone-technologies/vector-database-rag-qdrant-milvus`
* **Traditional SEO:**
  * Keyword Optimization: Tối ưu tốt cho "vector database là gì" và "thuật toán hnsw".
  * **Đánh giá chung:** `Pass`
* **AEO / GEO & AI Extractability:**
  * Answer-First: Giới thiệu HNSW và khái niệm semantic search ngay sau H2.
  * Fact Density: Rất cao. Có công thức tính RAM OOM chi tiết cho 5 triệu vectors 1536-dims.
  * **Đánh giá chung:** `Pass` (AI Extractability Score: 100/100)
* **E-E-A-T:** Có chia sẻ kinh nghiệm tránh lỗi OOM trên server 32GB RAM.

---

## 5. Cloudflare Workers & Edge Computing: Kiến trúc V8 Isolates

* **URL dự kiến:** `series/cornerstone-technologies/cloudflare-workers-edge-computing`
* **Traditional SEO:**
  * Keyword Optimization: Focus vào "cloudflare workers edge computing" và "v8 isolates".
  * **Đánh giá chung:** `Pass`
* **AEO / GEO & AI Extractability:**
  * Answer-First: Khái quát sự khác biệt giữa V8 Isolates và Docker Containers.
  * Fact Density: Đo lường Cold Start 0ms của Cloudflare vs 200ms của AWS Lambda.
  * **Đánh giá chung:** `Pass` (AI Extractability Score: 98/100)
* **E-E-A-T:** Giải quyết thách thức giới hạn 10ms/50ms CPU time.

---

## Tổng Kết (Overall Handoff)

* **Topical Authority:** Cả 5 bài viết đều link về trang trụ cột (`_index.md`), thỏa mãn kiến trúc Pillar-Cluster.
* **Cannibalization Check:** `Clear`. Không ghi nhận xung đột từ khóa với các bài cũ.
* **Technical SEO Escalations:** Frontend Developer cần lưu ý chèn đúng schema JSON-LD (`Article`, `FAQPage`, `Person`) cho các bài viết này khi deploy.
* **Trạng Thái:** **`approved_to_publish`** (Cả 5 bài viết đều thỏa mãn tiêu chuẩn SEO & E-E-A-T khắt khe nhất, sẵn sàng để xuất bản).
