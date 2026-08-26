---
title: "Phần 2: Kỹ Thuật Ngữ Cảnh Trong Lập Trình AI: AGENTS.md, Cursor Rules, và Codebase RAG"
date: 2026-05-31T17:00:00+07:00
lastmod: 2026-07-28T18:23:00+07:00
author: "Lê Tuấn Anh"
description: "Cách làm cho các tác nhân AI code đáng tin cậy trên các codebase thực tế: AGENTS.md, llms.txt, Cursor Rules, memory banks, RAG pipelines, ContextOps."
categories:
  - "AI Engineering"
  - "Context Engineering"
tags:
  - "AI Agents"
  - "Architecture"
  - "Engineering"
series:
  - "ai-code-review-vibe-coding"
weight: 3
slug: "part-2-context-engineering-codebase"
canonicalURL: "https://tanhdev.com/series/ai-code-review-vibe-coding/part-2-context-engineering-codebase/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 2: Kỹ Thuật Ngữ Cảnh Trong Lập Trình AI: AGENTS.md, Cursor Rules, và Codebase RAG"
  relative: false
---

[← Chương trước: Phần 1: Vibe Coding Cho CEO, PM, và BA](/series/ai-code-review-vibe-coding/part-1-vibe-coding-non-technical/) | [Mục lục Series](/series/ai-code-review-vibe-coding/) | [Chương tiếp theo: Phần 3: Hệ Thống Phân Loại Lỗi Code AI →](/series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/)

> **Answer-first:** Context Engineering chuẩn hóa ngữ cảnh cho AI thông qua AGENTS.md, llms.txt, Cursor Rules và Codebase RAG. Cung cấp đúng phạm vi ngữ cảnh theo từng Bounded Context giúp AI sinh code chuẩn xác, tuân thủ quy ước dự án và loại bỏ hoàn toàn các giả định sai lệch.

---

<!--more-->

> **Yêu cầu Bắt buộc (Prerequisite):** [Vibe Coding Cho CEO, PM, và BA: Công Cụ & Bức Tường Sản Xuất]({{< ref "part-1-vibe-coding-non-technical.md" >}})

Năm 2025, METR — một tổ chức nghiên cứu về năng lực và an toàn AI — đã tiến hành một thử nghiệm ngẫu nhiên có đối chứng (randomized controlled trial) vô cùng nghiêm ngặt. Mười sáu nhà phát triển mã nguồn mở giàu kinh nghiệm đã làm việc trên 246 nhiệm vụ thực tế, mỗi người được chỉ định ngẫu nhiên vào nhóm được tự do sử dụng các công cụ lập trình AI hoặc nhóm hoàn toàn không được sử dụng.

Kết quả thu được lại đi ngược lại trực giác: các developer sử dụng công cụ AI đã **chậm hơn 19%** đối với các tác vụ phức tạp.

Trước khi nghiên cứu diễn ra, chính những developer đó đã dự đoán rằng AI sẽ giúp họ **nhanh hơn 24%**. Sau khi hoàn thành thử nghiệm — họ vẫn tin rằng mình đã làm việc nhanh hơn — sự tự tin chủ quan của họ vẫn không hề bị lay chuyển.

Phát hiện này không lên trang nhất của các tờ báo vì cái lý do mà mọi người thường mặc định. Dòng tiêu đề không phải là "AI vô dụng." Tiêu đề thực sự là: **nút thắt cổ chai không nằm ở chất lượng của mô hình. Nó nằm ở chất lượng của ngữ cảnh (context quality).**

Những developer bị chậm lại đã phải dành một lượng thời gian đáng kể cho cái mà các nhà nghiên cứu gọi là "chi phí xác minh" (verification overhead) và "ma sát luồng công việc" (workflow friction) — tức là nỗ lực cần thiết để sửa chữa lại những đầu ra của AI vốn không hiểu rõ các ràng buộc về kiến trúc, các quy ước đặt tên (naming conventions), các hàm tiện ích (utility functions) có sẵn, và những khuôn mẫu đã được thiết lập của cái codebase mà họ đang làm việc. Đúng là con AI đang tạo ra code. Nhưng nó đang tạo ra code cho một hệ thống tưởng tượng.

Phần này của series sẽ nói về cách giải quyết vấn đề đó.

> **Ghi chú về phạm vi:** Bài viết này tập trung cụ thể vào kỹ thuật ngữ cảnh *ở cấp độ code-review* — những thực hành mà các cá nhân kỹ sư và team sử dụng để khiến cho các AI agent tạo ra những đoạn code đúng về mặt kiến trúc và có thể đánh giá được trên một codebase hiện có. Nếu bạn quan tâm đến hạ tầng ngữ cảnh *ở cấp độ nền tảng (platform-level)* — xây dựng một lớp Nền tảng AI cho tổ chức, các hệ thống RAG nội bộ ở quy mô lớn, hoặc quản lý tri thức doanh nghiệp — hãy xem bài [Kỹ Thuật Ngữ Cảnh: Domain-Driven Design Cho AI](/series/ai-driven-playbook/part-1-context-engineering-ddd/) trong series AI-Driven Playbook.

---

## Vấn Đề Cốt Lõi: AI Hoạt Động Trên Một Tờ Giấy Trắng

Mỗi khi bạn mở một phiên làm việc (session) mới với một công cụ code bằng AI, bạn lại bắt đầu từ con số không. Mô hình không biết gì về:

- Các quyết định kiến trúc của bạn và lý do tại sao bạn lại đưa ra chúng
- Những khuôn mẫu (patterns) nào bạn đã chuẩn hóa và những khuôn mẫu nào bạn đang chuyển đổi loại bỏ đi
- Nhóm của bạn gọi đâu là "service", đâu là "handler", và đâu là "controller"
- Những hàm tiện ích nào đã tồn tại sẵn trong thư viện dùng chung của bạn
- Một PR (Pull Request) "thành công" trong codebase của bạn trông như thế nào — điều gì sẽ vượt qua khâu review và điều gì sẽ bị từ chối

Nếu không có những thông tin này, AI sẽ hoạt động giống như một developer junior rất nhanh, rất tự tin, người chưa bao giờ nhìn thấy codebase của bạn trước đây và sẽ sao chép lại bất kỳ khuôn mẫu nào phổ biến nhất trong dữ liệu huấn luyện của nó — chứ không phải khuôn mẫu chính xác dành cho hệ thống của bạn.

**Kỹ thuật ngữ cảnh (Context engineering)** là kỷ luật cấu trúc hóa và truyền tải tri thức của tổ chức đến các AI agent dưới một định dạng mà chúng có thể sử dụng một cách đáng tin cậy. Nó được sự đồng thuận trong ngành mô tả như là "khoảnh khắc DevOps" dành cho AI — một lớp vận hành giúp phân định giữa việc sử dụng AI như một trải nghiệm hỗ trợ mang tính thử nghiệm với một sự hợp tác AI đạt tiêu chuẩn production, đáng tin cậy.

---

## Phân Cấp Ngữ Cảnh: Từ Các Tệp Quy Tắc (Rule Files) Đến Các Pipeline RAG

Các môi trường lập trình AI hiện đại hỗ trợ ngữ cảnh ở nhiều tầng (layers) khác nhau. Hiểu được hệ thống phân cấp này là nền tảng của bất kỳ chiến lược ngữ cảnh hiệu quả nào.

### Tầng 1: Các Tệp Quy Tắc (Luôn Bật, Không Tốn Chi Phí Khởi Động)

Tệp quy tắc (Rule files) là các file cấu hình văn bản thuần túy (plain-text) được tự động tiêm (injected) vào mọi tương tác với AI. Chúng là hình thức ngữ cảnh quan trọng nhất nhưng lại bị tận dụng kém nhất.

**AGENTS.md, CLAUDE.md, và llms.txt**

Những file này — được lưu trữ ở thư mục gốc của kho lưu trữ (repository) của bạn — sẽ được các AI agent đọc trước khi chúng bắt đầu bất kỳ nhiệm vụ nào. Trong năm 2026, tiêu chuẩn `llms.txt` đã trở thành chuẩn mực công nghiệp để bộc lộ tài liệu dự án trực tiếp cho các mô hình ngôn ngữ lớn (LLMs). Chúng hoạt động như những mệnh lệnh thường trực của agent: các ràng buộc kiến trúc, các tiêu chuẩn hành vi, và các điều cấm rõ ràng áp dụng cho mọi việc mà agent thực hiện.

Một file `AGENTS.md` có cấu trúc tốt sẽ bao gồm:

```markdown
# Kiến trúc Dự án (Project Architecture)
Đây là một microservice Kratos v2 sử dụng Clean Architecture.
Quy tắc phân lớp (Layer rules):
- api/ = chỉ chứa các hợp đồng (contracts) (proto + code được sinh tự động)
- internal/service/ = chỉ là lớp chuyển đổi (adapter layer), không chứa logic nghiệp vụ
- internal/biz/ = logic nghiệp vụ (business logic), KHÔNG gọi trực tiếp database
- internal/data/ = chỉ chịu trách nhiệm lưu trữ (persistence), sử dụng GORM + PostgreSQL

# Các Tiêu Chuẩn Bắt Buộc (Mandatory Standards)
- Mọi context phải được truyền qua các tham số của hàm (function parameters)
- Chỉ sử dụng errgroup cho các goroutine được quản lý
- Các câu truy vấn SQL phải sử dụng các đầu vào được tham số hóa (parameterized inputs) — KHÔNG BAO GIỜ được nối chuỗi (string concatenation)
- Các Secret phải đến từ biến môi trường (environment variables) hoặc Kratos Config — KHÔNG BAO GIỜ được hardcode

# Những Điều KHÔNG Được Làm (What NOT To Do)
- Không sử dụng global state (trạng thái toàn cục)
- Không phơi bày các lỗi raw của database ra phản hồi HTTP/gRPC
- Không tạo ra các pattern mới mà không kiểm tra thư mục internal/util trước
```

Tính cụ thể chính là điểm mấu chốt. Một chỉ dẫn chung chung như "hãy tuân theo clean architecture" sẽ tạo ra những kết quả thiếu nhất quán. Một chỉ dẫn cụ thể như "lớp biz không bao giờ được import `gorm.DB` trực tiếp" sẽ tạo ra kết quả mang tính xác định (deterministic).

**Cursor Rules (`.cursorrules`)**

Các tệp quy tắc của Cursor hoạt động tương tự như AGENTS.md nhưng là đặc trưng (native) của IDE Cursor. Chúng hỗ trợ các quy tắc có phạm vi (scoped rules) — bạn có thể xác định các hành vi khác nhau cho các mẫu file (file patterns) khác nhau, thực thi các tiêu chuẩn dành riêng cho từng ngôn ngữ, và chỉ định những file nào AI không bao giờ được phép sửa đổi.

```toml
[rules]
name = Tiêu Chuẩn Go Microservice
glob = **/*.go

[security]
never_hardcode_secrets = true
require_parameterized_queries = true
forbid_global_state = true

[architecture]
enforce_layer_boundaries = true
require_context_propagation = true
```

Tác dụng thực tế: trợ lý AI của bạn giờ đây hoạt động với các tiêu chuẩn của bạn đã được nhúng sẵn bên trong nó, chứ không phải như một thứ suy nghĩ đến muộn mà bạn phải chắp vá vào từng câu prompt.

### Các Tệp Quy Tắc Ngăn Chặn Sự Rò Rỉ Kiến Trúc Như Thế Nào (Một Ví Dụ Bằng Go / Kratos)

Hãy xem xét yêu cầu: *"Lấy thông tin hồ sơ người dùng bằng email trong lớp service (service layer)."*

*   **Khi không có Tệp Quy Tắc (`AGENTS.md`)**: AI sẽ viết một câu truy vấn GORM trực tiếp bên trong lớp service adapter, phá vỡ thiết kế Clean Architecture:
    ```go
    // File: internal/service/user.go
    func (s *UserService) GetProfileByEmail(ctx context.Context, req *pb.GetProfileReq) (*pb.GetProfileReply, error) {
        var user biz.User
        // VI PHẠM: Truy cập database trực tiếp bị rò rỉ vào lớp service
        if err := s.db.WithContext(ctx).Where("email = ?", req.Email).First(&user).Error; err != nil {
            return nil, err
        }
        return &pb.GetProfileReply{Name: user.Name, Email: user.Email}, nil
    }
    ```
*   **Khi có Tệp Quy Tắc (`AGENTS.md`)**: AI bắt buộc phải tuân theo sự cô lập giữa các lớp, điều hướng quyền truy cập GORM đi qua riêng rẽ miền lưu trữ (repository) và use case của nghiệp vụ:
    ```go
    // File: internal/service/user.go
    func (s *UserService) GetProfileByEmail(ctx context.Context, req *pb.GetProfileReq) (*pb.GetProfileReply, error) {
        // CHÍNH XÁC: Service gọi bộ điều phối (orchestrator) của lớp biz (UseCase)
        user, err := s.userUseCase.FindByEmail(ctx, req.Email)
        if err != nil {
            return nil, err
        }
        return &pb.GetProfileReply{Name: user.Name, Email: user.Email}, nil
    }
    ```

---

### Tầng 2: Quản Lý Phiên Làm Việc (Kiểm Soát Ngữ Cảnh Tích Cực)

Ngay cả khi các tệp quy tắc đã được thiết lập, những phiên làm việc kéo dài vẫn sẽ bị suy giảm chất lượng. Đây là hiện tượng "ngữ cảnh mục nát" (context rot): khi một session tích lũy quá nhiều các nỗ lực thất bại, các lỗi đã được sửa, và các ghi chú kế hoạch bị hủy bỏ, tỷ lệ tín hiệu trên nhiễu (signal-to-noise ratio) trong cửa sổ ngữ cảnh (context window) sẽ sụt giảm. Mô hình có thể ưu tiên những "nhiễu loạn" gần đây hơn là các ràng buộc mang tính nền tảng.

**Chiến Lược Phiên Làm Việc Mới (The Fresh Session Strategy)**

Các team kỹ thuật có hiệu suất cao coi các session AI như các hàm không trạng thái (stateless functions): một tác vụ riêng biệt cho mỗi session. Khi bạn hoàn thành việc sửa một con bug, hãy đóng session đó lại. Khi bạn bắt đầu một tính năng mới, hãy mở một session mới. Quy tắc vận hành: ranh giới tác vụ chính là ranh giới session.

**Bàn Giao Có Cấu Trúc (Structured Handovers)**

Khi một session kéo dài quá lâu trước khi tác vụ được hoàn thành, hãy thực hiện một cuộc bàn giao có cấu trúc:

1. Yêu cầu AI tóm tắt: "Chúng ta đã đưa ra những quyết định nào? Trạng thái hiện tại là gì? Còn những việc gì cần làm?"
2. Chụp lại output đó vào một file `PLAN.md` hoặc `HANDOVER.md` trong thư mục dự án của bạn
3. Mở một session mới và tải bản tóm tắt đó lên cùng với các tệp quy tắc cốt lõi của bạn

Việc này sẽ loại bỏ "ngữ cảnh mục nát" trong khi vẫn bảo tồn được toàn bộ những tiến trình có ý nghĩa.

**Các Lệnh Nén Ngữ Cảnh (Compaction Commands)**

Các agent lập trình hiện đại (như Claude Code, Cursor) đều bao gồm các lệnh `/compact` hoặc `/summarize`. Hãy chủ động sử dụng chúng khi một session chạy dài — trước khi mô hình chạm đến giới hạn ngữ cảnh (context limit) của nó và trước khi hiệu suất bị suy giảm. Một bản tóm tắt đã được nén lại (compacted summary) là một đầu vào có chất lượng cao hơn rất nhiều so với một dòng chảy tích lũy các đoạn hội thoại thô (raw conversation).

---

### Tầng 3: Lập Chỉ Mục Kho Lưu Trữ (Tiêm Ngữ Cảnh Có Chọn Lọc)

Các tệp quy tắc dùng để thiết lập các tiêu chuẩn. Việc quản lý session dùng để kiểm soát nhiễu. Lập chỉ mục kho lưu trữ (Repository indexing) giải quyết một bài toán khác: cung cấp cho AI kiến thức chính xác về những gì đã có sẵn trong codebase của bạn.

**Bài Toán Khám Phá N+1 (The N+1 Discovery Problem)**

Nếu không có ngữ cảnh của kho lưu trữ, các AI agent sẽ thực hiện lại các hàm (functions) đã tồn tại một cách như một thói quen. Chúng tạo ra các bảng database mới trùng lặp với các bảng đã có. Chúng định nghĩa các loại lỗi (error types) xung đột với các pattern đã được thiết lập. Chúng import các package vi phạm biểu đồ dependency của bạn. Không phải vì chúng không có khả năng làm tốt hơn — mà vì chúng không biết những gì đã tồn tại.

**Lựa Chọn Thủ Công so với Quét Toàn Bộ Repo (Manual Selection vs. Full-Repo Scanning)**

Hầu hết các công cụ lập trình AI đều cung cấp khả năng tự động quét toàn bộ kho lưu trữ (repository). Nghe có vẻ rất giá trị nhưng thực tế lại thường phản tác dụng. Việc đẩy sỉ toàn bộ một codebase lớn vào context sẽ bổ sung một lượng nhiễu đáng kể — các file không liên quan, các pattern lỗi thời, các module đã bị loại bỏ (deprecated). Nguyên tắc là: hãy chọn thủ công (manually select) chỉ những file có liên quan trực tiếp đến tác vụ.

Đối với một tác vụ sửa đổi tính năng xác thực (authentication) người dùng, ngữ cảnh liên quan sẽ là:
- Interface của service authentication
- Khối triển khai (implementation) user repository hiện tại
- Middleware quản lý session
- Các định nghĩa error type có liên quan

Chứ không phải là toàn bộ codebase.

**Ngân Hàng Bộ Nhớ Ngữ Nghĩa (Semantic Memory Banks)**

Các team sành sỏi hơn sẽ duy trì các tệp "ngân hàng bộ nhớ" (memory bank) được tuyển chọn cẩn thận — đó là các tài liệu markdown có cấu trúc mô tả kiến trúc của codebase, các pattern chính, và các quyết định quan trọng dưới một định dạng được tối ưu hóa cho AI hấp thụ:

```markdown
# Ngân Hàng Bộ Nhớ (Memory Bank): Authentication Domain

## Kiến Trúc
- Auth service xử lý việc phát hành và xác thực JWT
- Danh tính người dùng được lưu trữ trong PostgreSQL thông qua GORM, bảng users
- Các Session sử dụng Redis với TTL là 24h (xem internal/data/session_repo.go)
- MFA được triển khai thông qua TOTP (internal/service/mfa_service.go)

## Các Khuôn Mẫu Chính (Key Patterns)
- Mọi lỗi auth đều trả về domain errors, không bao giờ trả về lỗi raw DB
- Tính năng giới hạn tốc độ (Rate limiting) được đặt ở cấp độ middleware (internal/middleware/rate_limiter.go)
- Refresh token được băm (hash) trước khi lưu trữ (xem HashToken trong internal/util/crypto.go)

## Các Lỗi Phổ Biến Cần Tránh
- KHÔNG kiểm tra password trực tiếp — luôn sử dụng bcrypt.CompareHashAndPassword
- KHÔNG log ra giá trị của token — chỉ log token IDs
- KHÔNG triển khai crypto mới — chỉ sử dụng duy nhất internal/util/crypto.go
```

Những ngân hàng bộ nhớ này được cập nhật bất cứ khi nào có những quyết định kiến trúc quan trọng được đưa ra và được commit vào repository cùng với code.

---

### Tầng 4: Pipeline RAG (Ngữ Cảnh Cấp Độ Doanh Nghiệp)

Đối với các tổ chức kỹ thuật lớn — những nơi có hàng trăm service, tài liệu khổng lồ, và các tiêu chuẩn kiến trúc phức tạp — các tệp quy tắc tĩnh (static rule files) là không đủ. Ngữ cảnh liên quan cho bất kỳ nhiệm vụ nào cũng thay đổi quá nhanh và tồn tại ở quá nhiều nơi để có thể quản lý thủ công.

**Phương pháp Retrieval-Augmented Generation (RAG)** cho code context hoạt động bằng cách:

1. Lập chỉ mục (indexing) codebase, các Hồ sơ Quyết định Kiến trúc (ADRs), runbooks, và các tài liệu nội bộ của bạn vào một vector database
2. Khi một AI agent bắt đầu một nhiệm vụ, nó sẽ tự động truy vấn chỉ mục đó để lấy ra những ngữ cảnh có sự liên quan về mặt ngữ nghĩa (semantically relevant) nhất
3. Tiêm (Inject) những ngữ cảnh đã truy xuất đó vào trong session cùng với bản mô tả công việc

Kết quả vận hành: một AI agent làm việc trên một tính năng thanh toán (payments feature) sẽ tự động truy xuất các interface của payment service có liên quan, bản ADR giải thích lý do tại sao bạn lại chọn mô hình giao dịch hiện tại, và cuốn runbook về việc tích hợp nhà cung cấp dịch vụ thanh toán — mà không cần người kỹ sư phải tự tay đi tổng hợp các ngữ cảnh đó.

**ADRs Như Những Bản Đánh Giá Có Thể Đọc Được Bằng Máy (Machine-Readable Judgment)**

Các Bản Ghi Quyết Định Kiến Trúc (Architecture Decision Records - ADRs) xứng đáng được chú ý đặc biệt. Khi được commit dưới một định dạng có cấu trúc và được lập chỉ mục vào một pipeline RAG, các ADR sẽ biến đổi từ một bản tài liệu tĩnh thành các ràng buộc chủ động (active constraints):

```markdown
# ADR-047: Event-Sourcing Cho Các Chuyển Đổi Trạng Thái Đơn Hàng

## Trạng thái: Được chấp nhận (2025-03)
- **Tác giả:** Architecture Review Board (ARB) & Core Engineering Team
- **Phạm vi tác động:** Toàn bộ hệ thống Order Processing, Inventory Management, và Billing Services
- **Hiệu lực:** Phê duyệt ngày 15/03/2025 (Cập nhật tiêu chuẩn định kỳ 2026), bắt buộc tuân thủ đối với cả kỹ sư con người và AI Coding Agents.

## Ngữ Cảnh
Việc thay đổi (mutation) trạng thái trực tiếp của các bản ghi đơn hàng tạo ra các lỗ hổng trong việc truy vết kiểm toán (audit trail) và khiến cho các kịch bản rollback (hoàn tác) trở nên phức tạp.
## Quyết Định
Mọi sự chuyển đổi trạng thái của đơn hàng đều được triển khai dưới dạng các sự kiện (events), nối thêm vào bảng events.
Trạng thái hiện tại được suy ra bằng cách phát lại (replaying) các events, chứ không phải bằng cách cập nhật cột (column) trực tiếp.
## Hậu Quả
- Logic trạng thái đơn hàng mới BẮT BUỘC phải thêm các event type mới, KHÔNG được sửa đổi những event đã có
- Các truy vấn đơn hàng (Order queries) yêu cầu logic trình chiếu (projection logic) (xem internal/projection/order_projector.go)
- KHÔNG ghi trực tiếp vào orders.status — luôn luôn phải publish một event OrderStateTransitioned
```

Một AI agent khi có quyền truy cập vào bản ADR này sẽ không tạo ra các câu lệnh truy vấn `UPDATE orders SET status = ?` trực tiếp để thay đổi trạng thái đơn hàng. Nếu không có nó, nó gần như chắc chắn sẽ làm như vậy.

**Giao thức Ngữ Cảnh Mô Hình (Model Context Protocol - MCP)**

Giao thức Ngữ Cảnh Mô Hình (Model Context Protocol - MCP), được phát hành bởi Anthropic và nay đã được áp dụng rộng rãi trên toàn ngành, cung cấp một interface tiêu chuẩn hóa để phục vụ context cho các tác nhân AI. Thay vì phải xây dựng các cấu hình tích hợp (integrations) riêng biệt cho từng công cụ AI, các tổ chức có thể xây dựng các máy chủ MCP (MCP servers) — những dịch vụ gọn nhẹ giúp bộc lộ tri thức cụ thể của tổ chức (tài liệu, mẫu code, thông tin ticket) thông qua một giao thức tiêu chuẩn.

Sự chuyển dịch mà điều này mang lại: cơ sở hạ tầng ngữ cảnh trở thành một tài sản được chia sẻ của cả tổ chức thay vì là vấn đề cấu hình của từng kỹ sư đơn lẻ.

---

## Kỷ Luật ContextOps

Ngành công nghiệp hiện đã có một cái tên dành cho việc vận hành cơ sở hạ tầng ngữ cảnh ở quy mô tổ chức: **ContextOps**. Đến năm 2026, ContextOps đã thay thế "prompt engineering" (kỹ thuật viết prompt) để trở thành kỹ năng đòn bẩy cao nhất, đặc biệt trong việc quản lý "ranh giới ngữ cảnh" (context boundaries) nơi các tác nhân AI giao tiếp với nhau trong một quy trình làm việc multi-agent.

Vòng lặp vận hành (operational loop) là: **Tiếp nhận (Ingest) → Xác nhận (Validate) → Cấu trúc (Structure) → Phục vụ (Serve) → Kiểm toán (Audit) → Tinh chỉnh (Refine)**.

- **Tiếp nhận (Ingest)**: Kéo (Pull) dữ liệu từ Confluence, Notion, các file ADR, runbooks, và các cuộc thảo luận về kiến trúc trên Slack
- **Xác nhận (Validate)**: Xác nhận rằng nội dung là chính xác, cập nhật, và không có gì mâu thuẫn
- **Cấu trúc (Structure)**: Định dạng (Format) lại cho AI dễ hấp thụ — các tiêu đề rõ ràng, các phần "nên làm/không nên làm" rõ ràng, các ví dụ về code có cấu trúc
- **Phục vụ (Serve)**: Thông qua các máy chủ MCP, tệp quy tắc, hoặc RAG retrieval
- **Kiểm toán (Audit)**: Giám sát xem các đầu ra của AI có đang tuân thủ theo context hay không (nếu agent cứ liên tục mắc phải những lỗi mà context đã nghiêm cấm, thì có nghĩa là context đó bị sai hoặc không rõ ràng)
- **Tinh chỉnh (Refine)**: Cập nhật context dựa trên những gì quá trình audit phát hiện được

Những tổ chức coi ngữ cảnh (context) giống như các cấu hình dùng một lần — chỉ được cập nhật ngẫu hứng, định dạng không nhất quán, lưu trữ trong các file markdown không được lập chỉ mục — sẽ phải hứng chịu kết quả giống như của METR: AI làm đội ngũ chậm lại. Còn những tổ chức đối xử với context như một cơ sở hạ tầng thực thụ — được quản lý phiên bản (versioned), được xác thực (validated), được giám sát (monitored) — sẽ trải nghiệm những kết quả khác biệt có ý nghĩa.

---

## Triển Khai Thực Tế: Bắt Đầu Từ Số Không

Nếu đội ngũ của bạn hiện không có bất kỳ cơ sở hạ tầng ngữ cảnh nào, thì điểm khởi đầu thiết thực nhất là một chuỗi gồm ba bước:

**Bước 1: Viết một file AGENTS.md (mất một buổi chiều)**

Hãy tập trung vào những nội dung có giá trị cao nhất trước:
- Cấu trúc phân lớp của bạn và các quy tắc chính cho mỗi lớp
- Top 5 mẫu "không bao giờ được làm điều này" (những lỗi mà những người review code của bạn thường bắt gặp nhất)
- Top 5 mẫu "luôn luôn sử dụng cái này thay thế" (các utility dùng chung và các quy ước đã được thiết lập)
- Các nguyên tắc bảo mật không thể thương lượng của bạn (không hardcode secret, phải tham số hóa các query, v.v.)

**Bước 2: Thiết lập kỷ luật cho session (cần một buổi thảo luận team)**

Thống nhất các ranh giới session theo từng tác vụ. Bổ sung một bước nén (compaction step) vào các chuẩn mực (norms) của team: trước khi bất kỳ session nào vượt quá 20 lần trao đổi thực chất, hãy nén nó lại và tiếp tục trong một session mới.

**Bước 3: Xây dựng ngân hàng bộ nhớ (memory bank) đầu tiên (mất một sprint)**

Chọn miền (domain) cốt lõi nhất của bạn — authentication, payments, hay bất cứ domain nào mang rủi ro cao nhất. Ghi chép lại nó theo định dạng memory bank. Thêm một quy tắc vào danh sách kiểm tra khi code review của bạn: "File memory bank có liên quan đã được cập nhật thành một phần của cái PR này chưa?"

Sự cải thiện biên (marginal improvement) từ ngay cả những cơ sở hạ tầng ngữ cảnh cơ bản nhất cũng đã rất đáng kể. Các nhóm hoàn thành được ba bước này đều báo cáo rằng họ đã giảm thiểu đáng kể số lượng các PR do AI tạo ra vi phạm tiêu chuẩn kiến trúc, đòi hỏi phải làm lại (rework) nhiều, hoặc mang theo những vấn đề bảo mật mà memory bank đã cấm rõ ràng.

---

## Một Hệ Thống Ngữ Cảnh Kỹ Thuật (Context Engineering) Tốt Trông Sẽ Ra Sao Trong Thực Tế

Hãy xem xét một tác vụ: "Implement một endpoint mới để xuất (export) lịch sử giao dịch của người dùng dưới dạng một file CSV."

**Nếu không có context engineering**, một AI agent sẽ:
- Tạo một câu truy vấn DB mới join trực tiếp giữa `users` và `transactions` bên trong lớp service
- Generate tất cả transaction cùng một lúc thay vì dùng luồng (streaming) (nguy cơ bị lỗi tràn bộ nhớ - OOM risk ở quy mô lớn)
- Viết inline logic xử lý CSV thay vì tận dụng thư viện `internal/util/csv_writer.go` đã có sẵn của bạn
- Bỏ qua cái middleware rate limiting mà kiến trúc của bạn yêu cầu cho tất cả các endpoint dùng để xuất dữ liệu

**Với context engineering hiệu quả**, cùng con AI agent đó sẽ:
- Biết rằng việc truy cập dữ liệu bắt buộc phải đi qua lớp repository, thay vì truy vấn DB trực tiếp ở tầng service
- Gọi ra được thư viện `csv_writer.go` có sẵn và sử dụng nó thay vì phải tự viết lại từ đầu
- Tìm thấy cái khuôn mẫu phân trang bằng luồng (streaming pagination pattern) đang được dùng bởi `internal/service/report_service.go` và áp dụng nó
- Tự áp dụng rate limit cho cái export endpoint thông qua `internal/middleware/` đúng như những gì đã được ghi rõ trong file AGENTS.md của bạn

Đây không phải là một mô hình AI khác. Đây là cùng một mô hình nhưng có context chuẩn xác. Sự khác biệt về đầu ra (output) là rất đáng kể.

---

## Kết Nối Đến Quy Trình Review (Review Pipeline)

Context engineering không phải là sự thay thế cho công việc code review. Nó là một cỗ máy nhân hiệu năng (force multiplier) cho quá trình code review. Khi các AI agent hoạt động với một lượng ngữ cảnh chính xác, toàn diện, những kết quả chúng tạo ra sẽ:

- Chứa ít các lỗi vi phạm về kiến trúc hơn (bởi context đã ngăn cấm chúng một cách rõ ràng)
- Tái sử dụng các utility có sẵn một cách nhất quán hơn (bởi context đã chỉ rõ chúng ra cho AI)
- Mắc lỗi bảo mật ít hơn (bởi context đã quy định rõ các yêu cầu về bảo mật)

Kết quả là: các human reviewer dành ít thời gian hơn cho những việc soi lỗi vi phạm pattern hay đi sửa lại kiến trúc, và có nhiều thời gian hơn cho các nhiệm vụ review có giá trị thực sự cao — ví dụ như tính đúng đắn của logic, xử lý các trường hợp biên (edge case), và những hành vi bảo mật đòi hỏi đến sự đánh giá phán đoán chứ không chỉ đơn thuần là việc áp dụng một quy tắc cứng nhắc nào đó.

Phần 3 sẽ đề cập đến các tác vụ review có giá trị cao đó là gì: một hệ thống phân loại toàn diện về các lỗi code do AI tạo ra (AI-generated bugs), từ những con bug mà các công cụ kiểm tra tự động có thể bắt được cho đến những con bug chỉ có thể tìm thấy thông qua một đợt human review cẩn trọng.

---

Bạn muốn thiết lập các quy tắc tùy chỉnh Cursor Rules và AGENTS.md cho codebase của mình? [Hire me](/hire/) để nâng cao tốc độ phát triển một cách an toàn.

🔗 **Next Step:** [Hệ Thống Phân Loại Lỗi Code AI]({{< ref "part-3-ai-bug-taxonomy.md" >}})

---

[← Chương trước: Phần 1: Vibe Coding Cho CEO, PM, và BA](/series/ai-code-review-vibe-coding/part-1-vibe-coding-non-technical/) | [Mục lục Series](/series/ai-code-review-vibe-coding/) | [Chương tiếp theo: Phần 3: Hệ Thống Phân Loại Lỗi Code AI →](/series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Kỹ Thuật Ngữ Cảnh Trong Lập Trình AI: AGENTS.md, Cursor Rules, và Codebase RAG giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Cách làm cho các tác nhân AI code đáng tin cậy trên các codebase thực tế: AGENTS.md, llms.txt, Cursor Rules, memory banks, RAG pipelines, ContextOps.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
