# Original User Request

## Initial Request — 2026-07-15T03:16:57Z

Phân tích và nghiên cứu toàn diện chiến lược SEO, từ khóa và chất lượng nội dung cho website https://tanhdev.com/ (tập trung vào Tech/Developer và Khách hàng B2B).

Working directory: /home/user/personalized/vesviet
Integrity mode: benchmark

## Requirements

### R1. Phân tích Technical & Cấu trúc (Technical SEO & Architecture)
Quét và phân tích cấu trúc internal link, reading-map, và silo structure hiện tại trong mã nguồn để tìm ra các điểm đứt gãy hoặc chưa tối ưu luồng sức mạnh (link juice).

### R2. Đánh giá chất lượng nội dung (On-page SEO & E-E-A-T)
Đánh giá chất lượng của các bài viết và series chuyên sâu (độ dài, mật độ từ khóa, việc tuân thủ Answer-First block, và tính chuyên gia E-E-A-T).

### R3. Khám phá Cơ hội từ khóa (Keyword Gap & Strategy)
Phân tích hiện trạng để tìm ra các cơ hội từ khóa mới (keyword gap) phù hợp với ngách System Design, AI Data Engineering, và Magento/E-commerce.

## Acceptance Criteria

### Báo cáo Nghiệm thu (Deliverables)
- [ ] Phải tạo ra một Báo cáo phân tích (SEO Audit Report) hoàn chỉnh dưới định dạng Markdown, lưu tại `/home/user/personalized/vesviet/seo_audit_report.md`.
- [ ] Báo cáo phải có phần Action Plan chỉ ra chính xác các file/bài viết cần sửa hoặc các chủ đề mới cần viết thêm.

### Kiểm duyệt chéo (Agent-as-judge)
- [ ] Các tác nhân (SEO Analyst, Content Manager) phải tự động review và phê duyệt chéo Báo cáo Phân tích dựa trên tiêu chuẩn khắt khe về E-E-A-T trước khi nghiệm thu hoàn thành.

## Follow-up — 2026-07-16T08:38:14Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Kiểm tra và đánh giá chất lượng toàn diện (Technical & Content) đối với toàn bộ các bài viết trong danh mục `content/posts/` của website tanhdev.com, xuất ra báo cáo Read-Only Audit (không tự động sửa file).

Working directory: /home/user/personalized/vesviet
Integrity mode: benchmark

## Requirements

### R1. Technical SEO & Structure Audit
Quét toàn bộ thư mục `content/posts/` để phát hiện các lỗi kỹ thuật: rác ký tự (Mojibake), đứt gãy luồng Internal Link, và thiếu cấu hình Frontmatter (TOC).

### R2. Content Quality & E-E-A-T Audit
Đánh giá chất lượng nội dung: phát hiện các bài viết mỏng (Thin Content < 1.400 từ), kiểm tra sự tồn tại của cấu trúc Answer-first ở đầu bài, và mật độ chuyên môn (mã nguồn, sơ đồ kiến trúc) tối ưu cho Generative Engine Optimization (GEO).

### R3. Reporting & Action Plan
Tổng hợp kết quả vào một file báo cáo Markdown duy nhất (ví dụ: `posts_audit_report.md`), liệt kê số liệu định lượng, chi tiết các file bị lỗi, điểm số khả năng trích xuất AI (AI extractability), và đề xuất Action Plan.

## Acceptance Criteria

### Objective Verification
- [ ] Các lỗi kỹ thuật (đếm từ, đứt link, Mojibake) phải được quét tự động bằng script Python/Bash (programmatic verification), không được đoán mò bằng LLM.
- [ ] File báo cáo cuối cùng phải được xuất ra thư mục làm việc hiện tại, chứa bảng thống kê số lượng file lỗi cụ thể.
- [ ] Báo cáo phải vượt qua vòng duyệt chéo độc lập (Agent-as-judge) của SEO Reviewer để đảm bảo tính khách quan và tuân thủ chuẩn E-E-A-T trước khi nghiệm thu.

## Follow-up — 2026-07-17T02:04:56Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Viết và xuất bản 3 bài viết kỹ thuật System Design mới vào thư mục `content/posts/` của dự án, sử dụng Dàn bài SEO (`seo_briefs_system_design.md`), tài liệu Q&A (`research_qa_system_design.md`) và các tài nguyên code/sơ đồ đã thu thập trong `_internal/research/`.

Working directory: /home/user/personalized/vesviet
Integrity mode: benchmark

## Requirements

### R1. Soạn thảo 3 bài viết mới (Content Creation)
Tạo 3 file Markdown trong `content/posts/` với các slug tương ứng trong Dàn bài SEO. Mỗi bài bắt buộc phải mở đầu bằng cấu trúc Answer-first (khối text <= 60 từ) và Frontmatter phải chứa `ShowToc: true`, `TocOpen: true`, `date`, `lastmod` chuẩn `+07:00`.

### R2. Lắp ghép Tài nguyên Kỹ thuật (Asset Integration)
Trích xuất và nhúng nguyên bản các file cấu hình (YAML Dapr), mã nguồn (Go, Terraform) và sơ đồ kiến trúc (Mermaid) từ thư mục `_internal/research/` vào các bài viết tương ứng để tối ưu hóa E-E-A-T và độ sâu kỹ thuật (Fact-density).

### R3. Tích hợp Q&A (FAQ Section)
Sử dụng các câu trả lời kỹ thuật sâu sắc từ `research_qa_system_design.md` để xây dựng phần FAQ ở cuối mỗi bài viết.

### R4. Độ dài và Văn phong
Đảm bảo mỗi bài viết đều vượt ngưỡng 1.400 từ (prose words). Đội ngũ được phép sáng tạo thêm nội dung chuyên môn xoay quanh chủ đề nếu cần thiết để đảm bảo tính logic và độ sâu của bài viết.

## Acceptance Criteria

### Objective Verification
- [ ] Chạy lệnh quét tự động `python3 _internal/verify_posts.py` để chứng minh 3 file mới được tạo ra đều >= 1.400 từ, có chứa `ShowToc` và 0 lỗi Mojibake/Broken Link.
- [ ] Vòng kiểm duyệt độc lập (Agent-as-judge) bởi Content Manager xác nhận rằng cấu trúc Answer-first hợp lệ và toàn bộ code từ `_internal/research/` đã được nhúng thành công.

