# Audit `vesviet/content/radar` — 2026-07-28

**Phạm vi**: 22 file (17 bài radar + 5 trang index). **Vai trò**: `seo-analyst` + kiểm chứng factual.
**Phương pháp**: script audit riêng cho format radar (không dùng luật của `posts`), cộng verify claim bằng web search về nguồn công bố gốc, cộng build Hugo thật.

**Lưu ý về audit cũ**: `reports/content_radar_audit.md` tuyên bố **PASS 100% trên 21 file**. Về mặt *cấu trúc* kết luận đó đứng vững (khác với các audit posts trước đây bị phóng đại). Nhưng nó (a) bỏ sót file `2026-07/radar-2026-07-27.md` (thực tế 22 file), và (b) **không kiểm tra dẫn nguồn và độ chính xác thời điểm** — vốn là rủi ro chính của một sản phẩm tin tức.

---

## 1. Kết quả cấu trúc: SẠCH

| Hạng mục | Kết quả |
|---|---|
| Frontmatter bắt buộc | PASS (xem ghi chú false positive) |
| Filename date == frontmatter date | PASS 17/17 |
| Thư mục tháng == tháng trong date | PASS |
| Timezone +07:00 | PASS |
| Answer-First tồn tại | PASS |
| Answer-First ≤60 từ | PASS |
| FAQ section | PASS 17/17 |
| Buzzword / AI filler | PASS (0 phát hiện) |
| Code fence cân đối | PASS |
| mermaid flag khớp body | PASS |
| Thin content (<300 từ) | PASS |
| Build Hugo | PASS (exit 0, 965 pages) |

**Word count**: min 560, max 22.040, trung bình 3.883.

### Hai false positive mình đã loại (không sửa)

1. **"Duplicate Answer-First" ở 8 file** — Radar là newsletter **nhiều mục**: mỗi tin (`## 1.`, `## 2.`, …) có `**Answer-first:**` riêng, cộng một block cấp tài liệu. Đây là thiết kế **đúng** cho AEO/GEO (mỗi tin extract được độc lập), không phải lỗi lặp như ở `posts`. Luật "1 Answer-First/bài" của `content-brand.md` áp cho bài viết đơn chủ đề, không áp cho digest.
2. **Root `_index.md` thiếu `date`/`draft`/`tags`/`categories`** — đây là **section landing page** của Hugo, không cần các field đó; `ShowToc: false` đã set có chủ ý nên `TocOpen` vô nghĩa.

---

## 2. Phát hiện chính: 14/22 file KHÔNG có một link nguồn ngoài nào

Với format tin tức, đây là lỗ hổng E-E-A-T nghiêm trọng nhất: người đọc không thể truy về công bố gốc để kiểm chứng.

| Nhóm | External links | Nhận xét |
|---|---|---|
| `2026-05/_index.md` | 18 | Tốt |
| `2026-05/radar-2026-05-16.md` | 31 | Tốt |
| `2026-06/radar-2026-06-02.md` | 23 | Tốt |
| `2026-06/radar-2026-06-06.md` | 23 | Tốt |
| `2026-07/radar-2026-07-22.md` | 4 | Tạm |
| `2026-07/radar-2026-07-10.md` | 2 | Yếu |
| **Toàn bộ `2026-04/` (9 file)** | **0** | **Không dẫn nguồn** |
| `2026-05/radar-2026-05-01-*` (2 file) | **0** | **Không dẫn nguồn** |
| `2026-06/radar-2026-06-22.md` | **0** | **Không dẫn nguồn** |
| `2026-07/_index.md`, `2026-07/radar-2026-07-27.md` | **0** | **Không dẫn nguồn** |

**Pattern**: thói quen dẫn nguồn được hình thành từ khoảng tháng 5–6/2026 và làm tốt, nhưng **toàn bộ backlog tháng 4 chưa được bổ sung nguồn**. Nặng nhất: `2026-04/_index.md` — 20.685 từ, 13 claim số liệu, 0 nguồn.

---

## 3. Kiểm chứng factual: 1 lỗi thời điểm thật, 3 claim đúng

Mình verify các claim kiểm chứng được bằng nguồn công bố gốc:

| Claim | Kết quả | Nguồn |
|---|---|---|
| Mistral Small 4 = 119B total / 6B active per token | ✅ **ĐÚNG** | [Mistral](https://mistral.ai/news/mistral-small-4) |
| Gateway API v1.5 phát hành 14/03/2026, K8s blog 21/04/2026, ListenerSet lên Standard | ✅ **ĐÚNG cả 2 mốc** | [Kubernetes blog](https://kubernetes.io/blog/2026/04/21/gateway-api-v1-5/) |
| DeepSeek-V4 "released this week" (radar 26/04) | ✅ **ĐÚNG** — ra mắt 24/04/2026, cùng tuần | HuggingFace / DeepSeek |
| Claude Sonnet 4.5 + Agent SDK "shipped **this week**" (radar 27/04/2026) | ❌ **SAI ~7 tháng** | [Anthropic](https://www.anthropic.com/news/claude-sonnet-4-5) — công bố **29/09/2025** |

### Lỗi đã sửa

**`2026-04/radar-2026-04-27-claude-sonnet.md`** — bài đề ngày 27/04/2026 và viết "Anthropic shipped two things **this week**", nhưng Sonnet 4.5 và Agent SDK thực tế công bố **29/09/2025**. Ngoài ra Anthropic nay đã ra **Sonnet 5**, nên các claim xếp hạng "best coding model in the world" đã lỗi thời.
→ Đã thêm callout `[!NOTE]` đính chính ngày công bố thật + trạng thái hiện tại (Sonnet 5), đổi framing "this week" thành phân tích hồi cứu, kèm link nguồn Anthropic. **Không** đổi ngày archive của entry (không viết lại lịch sử).

**`2026-04/radar-2026-04-27-mistral-small.md`** — nói "released Small 4 **this week**" nhưng thực tế mid-March 2026 (~6 tuần trước).
→ Đổi thành "in mid-March 2026" + thêm 2 link nguồn Mistral cho spec 119B/6B.

**`2026-05/radar-2026-05-01-gateway-api-v1-5.md`** — fact đúng, chỉ thiếu nguồn.
→ Thêm link K8s blog chính thức.

---

## 4. Đợt 2 — bổ sung nguồn đã verify (hoàn tất)

Đã giảm số file không có nguồn từ **14 → 4**. Mỗi claim đều được verify bằng công bố gốc trước khi thêm link (không thêm link đoán):

| File | Claim đã verify | Nguồn thêm vào |
|---|---|---|
| `2026-04/radar-2026-04-14.md` | Go 1.26 `//go:fix inline` + source-level inliner | [Go blog](https://go.dev/blog/inliner) |
| `2026-04/radar-2026-04-26.md` | DeepSeek-V4 ra 24/04/2026, 1M context | [DeepSeek](https://api-docs.deepseek.com/news/news260424), [HF](https://huggingface.co/blog/deepseekv4) |
| `2026-04/radar-2026-04-28.md` | OpenAI–Microsoft sửa thoả thuận 27/04/2026 | [OpenAI](https://openai.com/index/next-phase-of-microsoft-partnership/), [Microsoft](https://blogs.microsoft.com/blog/2026/04/27/the-next-phase-of-the-microsoft-openai-partnership/) |
| `2026-04/radar-2026-04-29.md` | AWS mở rộng Bedrock cho OpenAI 28/04/2026 | [Amazon](https://www.aboutamazon.com/news/aws/bedrock-openai-models), [OpenAI](https://openai.com/index/openai-on-aws/) |
| `2026-04/radar-2026-04-29-creative-mcp.md` | Anthropic ra 9 connector creative 28/04/2026 | [9to5Mac](https://9to5mac.com/2026/04/28/anthropic-releases-9-new-claude-connectors-for-creative-tools-including-blender-and-adobe), [MacRumors](https://macrumors.com/2026/04/28/claude-creative-tool-connectors) |
| `2026-04/radar-2026-04-30.md` | Tổng hợp 2 sự kiện trên | Dẫn về nguồn gốc 27/04 + 28/04 |
| `2026-05/radar-2026-05-01-digitalocean-*.md` | DigitalOcean AI-Native Cloud tại Deploy 2026 | [DO blog](https://www.digitalocean.com/blog/introducing-digitalocean-ai-native-cloud), [DO investor PR](https://investors.digitalocean.com/news/news-details/2026/DigitalOcean-Unveils-AI-Native-Cloud-Built-for-the-Inference-Era/default.aspx) |
| `2026-06/radar-2026-06-22.md` | Dapr 1.18 ra 10/06/2026, là bản Workflows | [Dapr blog](https://blog.dapr.io/posts/2026/06/10/dapr-v1.18-is-now-available/) |
| `2026-07/radar-2026-07-27.md` | MCP transport model (stdio / Streamable HTTP + SSE) | [MCP spec](https://modelcontextprotocol.io/specification/latest) |
| `2026-04/_index.md` | — | Thêm mục điều hướng tới 8 bài daily (trước đó digest có **0** link nội bộ tới daily) |

**Kết quả kiểm chứng bổ sung**: tất cả claim kiểm tra được ở đợt 2 đều **ĐÚNG** về nội dung và mốc thời gian (DeepSeek-V4 24/04 vs radar 26/04; OpenAI–MS 27/04 vs radar 28/04; AWS 28/04 vs radar 29/04; Anthropic 28/04 vs radar 29/04; Dapr 10/06 vs radar 22/06; DigitalOcean 28/04 vs radar 01/05). Không phát hiện thêm lỗi thời điểm nào ngoài 2 lỗi ở đợt 1.

### 4 file còn lại không có link ngoài — đánh giá là chấp nhận được

- `radar/_index.md` (592 từ) — **section landing page**, không chứa claim tin tức → không cần nguồn.
- `2026-07/_index.md` (4.354 từ) và `2026-04/_index.md` (20.685 từ) — **digest tổng hợp** nội dung các bài daily. Với `2026-04` đã thêm điều hướng tới 8 bài daily (nơi có nguồn gốc). `2026-07/_index.md` nên làm tương tự khi có thời gian.

## 5. Còn tồn đọng (cần bạn quyết)

1. **`2026-04/_index.md` dòng ~1087**: "the Codex desktop app for macOS (**with Windows following in March**)" trong digest tháng 4 — mốc "March" nằm ở quá khứ so với ngữ cảnh, nghi lệch thời điểm. **Không tự sửa** vì không verify được chắc chắn timeline Codex cho Windows.
2. **Claim xếp hạng model dễ lỗi thời**: các bài tháng 4–5 gọi Sonnet 4.5 / GPT-5.2 / DeepSeek-V4 là "tốt nhất". Đã ràng buộc thời điểm cho bài Sonnet; các bài khác nên rà tương tự.
3. **`2026-07/_index.md`**: thêm mục điều hướng tới bài daily như đã làm cho tháng 4.

---

## 6. Khuyến nghị quy trình (để không tái diễn)

- **Bắt buộc dẫn nguồn công bố gốc** cho mọi claim tin tức trong radar — đây là điều phân biệt radar với blog ý kiến.
- **Ràng buộc thời điểm cho claim so sánh**: viết "tại thời điểm phát hành" thay vì "tốt nhất thế giới".
- **Kiểm tra mốc thời gian khi tái sử dụng nội dung cũ**: cả 2 lỗi tìm được đều do mô tả tin cũ bằng cụm "this week".
- Cân nhắc thêm bước CI kiểm: bài radar mới phải có ≥1 external link.

## Ghi chú
- Không đổi `draft:` của bất kỳ file nào. Build verify PASS sau mọi sửa đổi.
- Script audit tạm đã xoá, không lưu vào repo.
