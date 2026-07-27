# Audit Báo cáo — `vesviet/content/posts` (68 bài viết)

**Vai trò**: `seo-analyst` (audit theo `agent-skills/core/roles/seo-analyst.md`, `agent-skills/overlays/vesviet-content/rules/content-brand.md`, và baseline SEO trong `AGENTS.md`)
**Ngày audit**: 2026-07-27
**Phương pháp**: Script Python đối chiếu frontmatter, cấu trúc heading, Answer-First, FAQ, internal links, boilerplate AI với từng file thực tế (đã kiểm tra chéo bằng tay để loại false positive). Không dùng lại số liệu từ các báo cáo cũ (`lowest_quality_posts_report.md`, `seo-audit-report.json`) vì phần lớn vấn đề trong đó đã được fix — báo cáo này phản ánh trạng thái hiện tại.

---

## 1. Tóm tắt điều hành

| Chỉ số | Kết quả |
|---|---|
| Tổng số bài viết | 68 |
| Bài có lỗi cứng (phải sửa) | 5 |
| Bài chỉ có cảnh báo (nên sửa) | 24 |
| Bài sạch hoàn toàn | 39 |
| Tổng lỗi cứng | 5 |
| Tổng cảnh báo | 42 |

**Điểm tích cực**: So với các audit trước (25-26/7), phần lớn vấn đề nghiêm trọng đã được khắc phục — placeholder FAQ template (10 bài), sai `author`, thiếu `canonicalURL`, title quá dài đều đã **PASS 100%** ở lượt audit này. Không phát hiện boilerplate AI (`delve into`, `game-changer`, v.v.) hoặc FAQ giả mạo dạng template ở bất kỳ bài nào.

**Vấn đề còn tồn đọng**: chủ yếu là (1) 2 bài có mermaid diagram nhưng thiếu cờ `mermaid: true`, (2) 2 bài thiếu field `categories`, (3) 14 bài có internal linking dưới baseline ≥3, (4) 8 bài có heading H2 liền kề không có nội dung prose ở giữa (heading trùng lặp/rác), (5) 5 bài dưới ngưỡng 1.400 từ.

---

## 2. Lỗi cứng (Issues — cần sửa ngay)

| Severity | File | Category | Finding | Recommendation |
|---|---|---|---|---|
| Medium | `argo-cd-updates-2026.md` | Frontmatter/Rendering | Body có block ` ```mermaid ` (dòng ~213) nhưng frontmatter thiếu `mermaid: true` → diagram sẽ không render trên Hugo/PaperMod. | Thêm `mermaid: true` vào frontmatter. |
| Medium | `deconstructing-microfinance-core-banking-architecture.md` | Frontmatter/Rendering | Có mermaid diagram trong body nhưng thiếu `mermaid: true`. Đây là bài YMYL (tài chính) — lỗi hiển thị ảnh hưởng trực tiếp trải nghiệm người đọc. | Thêm `mermaid: true`. |
| Medium | `osrm-shared-memory-kubernetes-live-traffic.md` | Frontmatter/Rendering | Tương tự — mermaid diagram không có cờ kích hoạt. | Thêm `mermaid: true`. |
| Medium | `high-throughput-go-framework-benchmarks-gin-fiber-kratos.md` | Frontmatter/Taxonomy | Thiếu hoàn toàn field `categories` (chỉ có `tags`). Vi phạm yêu cầu frontmatter bắt buộc trong `content-brand.md`. | Thêm `categories: ["Engineering", "Backend"]` hoặc tương đương phù hợp taxonomy hiện có. |
| Medium | `multi-region-geo-distributed-api-routing.md` | Frontmatter/Taxonomy | Thiếu field `categories`. | Thêm `categories` phù hợp (ví dụ `["Architecture", "Engineering"]`). |

---

## 3. Cảnh báo theo nhóm (Warnings — nên sửa để tối ưu SEO/AEO)

### A. Internal Linking dưới baseline (≥3 theo `AGENTS.md`)

14 bài có **dưới 3 internal link** tới `/posts/`, `/series/`, hoặc `/radar/`. 8 bài trong số đó có **0 internal link hoàn toàn** — đây là vấn đề nghiêm trọng nhất về mặt cấu trúc site vì nó làm mất cơ hội truyền PageRank/topical authority nội bộ và vi phạm rõ ràng baseline "≥3 internal links" trong `AGENTS.md`.

| File | Internal Links | Ghi chú |
|---|---|---|
| `ai-native-frontend-architecture-predictions-2028.md` | 0 | |
| `alipay-double-11-architecture-tps.md` | 0 | Đồng thời dưới 1.400 từ (xem mục B) |
| `architecting-an-autonomous-hybrid-ai-content-pipeline.md` | 0 | Đồng thời dưới 1.400 từ |
| `building-custom-golang-vector-database-engine-hnsw.md` | 0 | Đồng thời thiếu FAQ |
| `generative-ui-with-mcp-ai-native-frontend.md` | 0 | Đồng thời dưới 1.400 từ |
| `order-fulfillment-algorithm-warehouse-last-mile.md` | 0 | Đồng thời dưới 1.400 từ |
| `shopee-flash-sale-architecture.md` | 0 | Đồng thời dưới 1.400 từ |
| `slm-fine-tune-vs-prompt-engineering.md` | 0 | Cạnh tranh cùng chủ đề với `slm-fine-tune-vs-prompt-engineering` — cần link chéo giữa các bài prompt/fine-tune |
| `temporal-saga-pattern-golang-distributed-transactions-guide.md` | 0 | Đồng thời thiếu FAQ |
| `zero-trust-service-mesh-security-spiffe-spire-istio-golang.md` | 0 | Đồng thời thiếu FAQ |
| `cloudflare-zero-devops-ecommerce.md` | 1 | |
| `deconstructing-ecommerce-service-details-domain.md` | 1 | |
| `ecommerce-architecture-composable-migration.md` | 1 | |
| `multi-region-geo-distributed-api-routing.md` | 2 | Đồng thời thiếu `categories` (xem mục 2) |

**Khuyến nghị**: Với các bài kiến trúc (ecommerce, banking, Go microservices), có sẵn hệ sinh thái pillar-cluster rất mạnh trong repo (`go-microservices.md`, `blueprint-ecommerce-microservices-architecture-diagram.md` là các pillar). Mỗi bài 0-link nên bổ sung ít nhất 3 link tới bài liên quan gần nhất trong cùng cluster — ví dụ `shopee-flash-sale-architecture.md` nên link tới `surge-pricing-optimization-architecture.md` và `real-time-inventory-ecommerce-architecture.md`.

### B. Nội dung dưới ngưỡng 1.400 từ (baseline `AGENTS.md`)

| File | Số từ (thân bài) |
|---|---|
| `alipay-double-11-architecture-tps.md` | 1.076 |
| `architecting-an-autonomous-hybrid-ai-content-pipeline.md` | 1.130 |
| `generative-ui-with-mcp-ai-native-frontend.md` | 1.047 |
| `order-fulfillment-algorithm-warehouse-last-mile.md` | 1.128 |
| `shopee-flash-sale-architecture.md` | 1.118 |

`AGENTS.md` cho phép ngoại lệ "content ngắn hơn chỉ khi phạm vi cập nhật hẹp" — 5 bài này đều là bài kiến trúc case-study đầy đủ, không phải update ngắn, nên nên mở rộng thêm phần benchmark số liệu, code snippet, hoặc so sánh kiến trúc để đạt baseline.

### C. Thiếu FAQ Section (khuyến nghị cho bài informational)

7 bài không có section FAQ (`## FAQ` hoặc `## Frequently Asked Questions`):
- `building-custom-golang-vector-database-engine-hnsw.md`
- `building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs.md`
- `cloudflare-zero-devops-ecommerce.md`
- `laravel-vs-golang-when-to-add-features.md`
- `strangler-fig-shared-database-quick-win.md`
- `temporal-saga-pattern-golang-distributed-transactions-guide.md`
- `zero-trust-service-mesh-security-spiffe-spire-istio-golang.md`

FAQ block hỗ trợ trực tiếp AEO (featured snippet) và FAQPage schema. Nên bổ sung 3-5 câu hỏi dùng shortcode `{{< faq q="..." >}}` như các bài khác đang làm chuẩn.

### D. Heading H2 liền kề không có prose (heading rác/trùng lặp)

8 bài có ít nhất 1 cặp heading H2 đứng sát nhau (không có câu văn ở giữa) — dấu hiệu của intro bị lặp hoặc generate thừa heading:

- `cloudflare-d1-durable-objects-realtime-cart.md` — dòng 71 & 73 (`## Architecture: Pairing Durable Objects...` ngay sau đó là `## Architecture Overview: D1 for Persistence...`)
- `deploying-astro-on-cloudflare-full-stack-edge-architecture.md`
- `go-pprof-kubernetes-remote-profiling.md`
- `golang-goroutine-pool-errgroup-worker.md`
- `graphhopper-distance-matrix-production-guide.md`
- `moving-from-magento-to-microservices.md`
- `mysql-scaling-sharding-tidb-architecture.md`
- `temporal-saga-pattern-golang-distributed-transactions-guide.md`

**Ví dụ cụ thể** (`cloudflare-d1-durable-objects-realtime-cart.md`, dòng 71-73):
```
## Architecture: Pairing Durable Objects (State) with D1 (Persistence)

## Architecture Overview: D1 for Persistence, Durable Objects for Real-Time State
```
Hai heading gần như nói cùng một điều — nên gộp thành 1 heading duy nhất và giữ lại phần mô tả + mermaid diagram phía dưới.

### E. Internal self-link

`magento-development-in-vietnam.md` có 1 link nội bộ trỏ về chính nó (`/posts/magento-development-in-vietnam/`) ở phần "Related Articles" cuối bài — nên xoá hoặc thay bằng link khác trong cluster Magento.

---

## 4. Những gì đã PASS (không cần hành động)

- **Answer-First block**: 100% (68/68) bài có đúng 1 block `**Answer-First:**` ở đầu intro, không lặp lại, không copy verbatim từ `description`.
- **Frontmatter bắt buộc khác** (`title`, `slug`, `date`, `lastmod`, `draft`, `description`, `tags`, `ShowToc`, `TocOpen`): đầy đủ ở tất cả bài trừ 2 bài thiếu `categories` đã nêu ở mục 2.
- **canonicalURL**: có ở 100% bài (đã fix so với audit trước — trước đây chỉ 4/68).
- **Author persona**: 100% dùng đúng `"Lê Tuấn Anh"`.
- **Date/lastmod timezone**: 100% dùng `+07:00`, và đã được quote đúng chuẩn string.
- **Title tag length** (≤60 ký tự): 100% PASS, không bài nào vượt ngưỡng.
- **Meta description**: không bài nào vượt 160 ký tự.
- **AI boilerplate/filler** (`delve into`, `game-changer`, `rich tapestry`, v.v.): 0 phát hiện trên toàn bộ 68 bài.
- **Placeholder FAQ template** (`is a critical architectural pattern...`, `modern microservices or event-driven paradigms...`): 0 phát hiện — đã fix hoàn toàn so với 10 bài bị flag trước đây.
- **H1 trùng lặp trong body**: không phát hiện heading `# ` (H1) thừa ngoài code block ở bất kỳ bài nào (audit trước có false positive do không loại trừ code comment `#`).

---

## 5. Đề xuất hành động ưu tiên

1. **Ưu tiên cao**: Thêm `mermaid: true` cho 3 bài có diagram không render (`argo-cd-updates-2026.md`, `deconstructing-microfinance-core-banking-architecture.md`, `osrm-shared-memory-kubernetes-live-traffic.md`) — ảnh hưởng trực tiếp UX, dễ sửa (1 dòng frontmatter/bài).
2. **Ưu tiên cao**: Bổ sung `categories` cho 2 bài thiếu field bắt buộc.
3. **Ưu tiên trung bình**: Bổ sung internal link (target ≥3) cho 14 bài đang dưới baseline, ưu tiên 8 bài có 0 link tuyệt đối trước — dùng pillar-cluster mapping sẵn có trong repo.
4. **Ưu tiên trung bình**: Gộp/sửa 8 cặp heading H2 rác không có prose ở giữa.
5. **Ưu tiên thấp**: Bổ sung FAQ cho 7 bài đang thiếu (hỗ trợ AEO/featured snippet).
6. **Ưu tiên thấp**: Mở rộng 5 bài dưới 1.400 từ nếu có ý định cạnh tranh từ khóa cao (nếu là bài case-study cố định, có thể giữ nguyên và ghi rõ lý do ngoại lệ).
7. Xoá self-link trong `magento-development-in-vietnam.md`.

---

## Ghi chú phương pháp

- Không phát sinh, publish, hoặc chỉnh `draft:` — theo đúng ranh giới vai trò `seo-analyst` (không thực thi content writing/production, chỉ audit và đề xuất).
- Không đưa ra cam kết về ranking/traffic — các phát hiện trên là structural/technical, không phải dự đoán hiệu suất.
- Script audit tạm dùng để kiểm tra (`scripts/_tmp_audit_posts.py`) đã bị xoá sau khi hoàn tất, không lưu vào repo như một script chính thức.
