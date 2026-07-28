# Audit `vesviet/content/categories` — 2026-07-28

**Phạm vi**: 15 landing page trong `content/categories/` + toàn bộ taxonomy `categories` sinh ra từ 307 file content.
**Phương pháp**: đối chiếu category khai trong frontmatter với landing page thực có, build Hugo thật rồi kiểm `<meta name="robots">` và `sitemap.xml` của output.

> **Kết luận ngắn**: 15 landing page tự thân **không có lỗi** (description đều unique, không trùng). Vấn đề thật nằm ở **tầng taxonomy**: 83 category slug được sinh ra, tất cả đều `index, follow` nhưng bị loại khỏi sitemap — hai tín hiệu ngược nhau; và 36 slug chỉ có 1 bài.

---

## 1. Trạng thái 15 landing page — SẠCH

| Hạng mục | Kết quả |
|---|---|
| Description trùng nhau | **0** (15/15 unique) |
| Description vượt 160 ký tự | 0 |
| Thiếu description | 0 |
| Orphan (page không category nào dùng) | **0** |

Ghi chú nhỏ: 12/15 description hơi ngắn (91–119 ký tự, dưới ngưỡng ~120 thường khuyến nghị). Không phải lỗi, chỉ là chưa tối ưu độ dài snippet.

**3 page curated nhưng volume thấp** — cân nhắc có nên là hub riêng:
- `cloudflare` (2 bài), `kubernetes` (2 bài), `payments` (2 bài)

Đối chiếu: `engineering` 118 bài, `architecture` 50 bài, `tech-radar` 21, `fintech` 20 — đây mới là hub thực sự.

---

## 2. Phát hiện chính: tín hiệu index không nhất quán

Kiểm tra trên **output build thật**:

| Loại trang | `<meta name="robots">` | Có trong `sitemap.xml`? |
|---|---|---|
| `/tags/*` | `noindex, follow` | Không |
| `/categories/*` (cả 83) | **`index, follow`** | **Không** |
| Bài viết (`/posts/*`…) | `index, follow` | Có |

Nguyên nhân gốc, xác định trong template:

- `layouts/sitemap.xml` dòng 4 **cố ý loại** taxonomy: `(not (in (slice "taxonomy" "term") .Kind))`
- `layouts/partials/head.html` dòng 4 chỉ loại `tags` khỏi index: `and (ne .Section "tags")` — **không có `categories`**

Nghĩa là chủ site đã cố ý (a) không quảng bá taxonomy trong sitemap và (b) noindex `tags`, nhưng `categories` bị bỏ sót khỏi quy tắc (b). Kết quả: 83 URL mời Google index nhưng không được khai báo trong sitemap.

**Vì sao đáng quan tâm**: Google vẫn phát hiện các URL này qua internal link (mỗi bài đều link tới category của nó), nên chúng vào index bất chấp việc vắng trong sitemap. Trong đó **36 slug chỉ có 1 bài** → thin taxonomy page.

---

## 3. Taxonomy sprawl

| Chỉ số | Giá trị |
|---|---|
| Tổng category slug | **83** |
| Có landing page curated | 15 |
| Chỉ 1 bài | **36** |
| ≤2 bài | **45** |
| ≥5 bài | 25 |

83 category cho 307 file là quá phân mảnh. Nặng hơn, có các cụm gần trùng nghĩa gây cannibalization giữa chính các trang taxonomy:

| Cụm | Số slug | Chi tiết |
|---|---|---|
| AI | 5 | `ai`(14), `ai-ml`(14), `ai-engineering`(3), `ai-architecture`(1), `machine-learning`(1) |
| Architecture / System | 3 | `architecture`(50), `system-architecture`(15), `system-design`(16) |
| Backend | 3 | `backend`(3), `backend-architecture`(11), `backend-engineering`(15) |
| Fintech / Payments | 6 | `fintech`(20), `payments`(2), `core-banking`(3), `fintech-architecture`(1), `payment-gateways`(1), `payment-protocols`(1) |
| Database | 6 | `database`(5), `databases`(2), + 4 slug 1 bài (`database-architecture/-design/-performance/-systems`) |

Đáng chú ý: `ai` và `ai-ml` mỗi cụm 14 bài — gần như chắc chắn là **cùng một chủ đề bị tách đôi**. Tương tự `databases` vs `database` chỉ khác số nhiều.

Ngoài ra `series` đang là một category (20 bài) — đây là phân loại **cấu trúc**, không phải chủ đề, nên thường không thuộc taxonomy nội dung.

---

## 4. Khuyến nghị — CẦN BẠN QUYẾT trước khi mình sửa

Mình **không tự ý sửa** phần này vì nó là quyết định chiến lược index ảnh hưởng 83 URL, và thuộc phạm vi cần chủ sở hữu đồng ý (không phải bug rõ ràng như link gãy).

**Phương án A — Taxonomy không dùng cho search (đơn giản, nhất quán nhất)**
Thêm `categories` vào quy tắc noindex trong `head.html`, cùng nhóm với `tags`.
- Ưu: nhất quán tuyệt đối với sitemap; loại 36 thin page khỏi index ngay; 1 dòng template.
- Nhược: 15 description đã soạn công phu trở thành vô dụng (meta description chỉ có ý nghĩa khi được index).

**Phương án B — 15 category curated là hub thực sự (khuyến nghị)**
- noindex 68 category không có landing page curated
- giữ index 15 page curated **và bổ sung chúng vào sitemap** để hai tín hiệu khớp nhau
- Ưu: khớp với ý định đã thể hiện (có người chủ động viết 15 description unique); hub thật được index, page mỏng bị loại.
- Nhược: cần logic template phức tạp hơn một chút; nên cân nhắc bỏ `cloudflare`/`kubernetes`/`payments` khỏi nhóm curated vì chỉ 2 bài.

**Việc nên làm song song (độc lập với A/B) — gộp category trùng nghĩa**
Đây là việc sửa trong frontmatter content, không phải template:
1. `ai-ml` → gộp vào `ai` (hoặc ngược lại) — 2 slug × 14 bài đang chia đôi cùng chủ đề
2. `databases` → `database`; 4 slug database 1-bài → gộp vào `database`
3. `backend-architecture` + `backend-engineering` → thống nhất 1 slug
4. `system-architecture` + `system-design` → cân nhắc gộp vào `architecture`
5. Bỏ `series` khỏi `categories` (dùng `series` taxonomy/section riêng)

Lưu ý: gộp category **đổi URL taxonomy**, nên nếu các URL đó đã được index thì cần redirect. Vì hiện tại chúng không có trong sitemap, rủi ro thấp hơn — nhưng vẫn nên kiểm Search Console xem có URL nào đang có traffic trước khi gộp.

---

## Ghi chú phương pháp
- Không sửa file nào trong đợt audit này — chỉ đo và báo cáo, vì các thay đổi đề xuất đều ảnh hưởng chính sách index/URL.
- Số liệu lấy từ output build thật (`hugo` → kiểm `robots` meta + `sitemap.xml`), không suy đoán từ markdown.
