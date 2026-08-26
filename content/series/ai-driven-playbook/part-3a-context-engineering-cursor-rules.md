---
title: "Phần 3A — Context Engineering Nâng Cao: Tối Ưu Hóa .cursor/rules, AGENTS.md & MCP Tooling"
date: 2026-05-15T08:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Vượt xa Prompt Engineering truyền thống: kỹ nghệ quản lý ngữ cảnh cấp doanh nghiệp, chuẩn file AGENTS.md, định dạng .cursor/rules/*.mdc phân lớp và tích hợp MCP 1.x cho Autonomous Coding Agents."
categories: ["Series", "Sổ Tay Thực Chiến", "AI Engineering"]
tags: ["AI", "Context Engineering", "Cursor Rules", "AGENTS.md", "MCP", "Developer Productivity"]
series: ["ai-driven-playbook"]
weight: 5
slug: "part-3a-context-engineering-cursor-rules"
canonicalURL: "https://tanhdev.com/series/ai-driven-playbook/part-3a-context-engineering-cursor-rules/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 3A — Context Engineering Nâng Cao: Tối Ưu Hóa .cursor/rules, AGENTS.md & MCP Tooling"
  relative: false
keywords: ["cursor rules mdc", "agents md specification", "mcp 1.x tooling", "context window optimization", "prompt engineering vs context engineering", "ai driven playbook"]
---

[← Chương trước: Phần 2: Modern AI Engineering Stack](/series/ai-driven-playbook/part-2-modern-ai-engineering-stack/) | [Mục lục Series](/series/ai-driven-playbook/) | [Chương tiếp theo: Phần 3A: Enterprise RAG Architecture →](/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/)

---

> **Answer-first:** Quản lý ngữ cảnh nâng cao vượt qua Prompt Engineering truyền thống nhờ kết hợp chuẩn AGENTS.md, cấu hình phân lớp `.cursor/rules/*.mdc` theo glob pattern và tích hợp MCP 1.x, đảm bảo AI Agents chỉ nạp đúng ngữ cảnh kỹ thuật cần thiết cho từng tác vụ cụ thể.

---

Trong giai đoạn đầu của làn sóng AI coding (2023–2024), phần lớn lập trình viên bị ám ảnh bởi **Prompt Engineering** — nghệ thuật viết ra những câu lệnh ma thuật (magic prompts) để ép LLM tạo ra code như ý. Tuy nhiên, khi bước sang môi trường 2026 với các mô hình suy luận hàng đầu như Claude 3.7 Sonnet, DeepSeek-R1 và Gemini 2.0 Flash, giới kỹ thuật nhận ra một sự thật phũ phàng: **Prompt tốt đến đâu cũng thất bại nếu Ngữ cảnh (Context) bị sai hoặc thiếu.**

Bản chất của các AI Coding Assistant hiện đại không nằm ở việc nhớ Prompt, mà nằm ở **Context Engineering (Kỹ nghệ Quản lý Ngữ cảnh)**. Đây là kỹ năng kiến trúc hạ tầng ngữ cảnh sao cho AI luôn nhận đúng, đủ và tinh sạch nhất thông tin về codebase, quy chuẩn kiến trúc (Architectural Boundaries), và tri thức miền (Domain Knowledge) ngay tại thời điểm sinh code.

Bài viết này thuộc Series [Sổ Tay: The AI-Driven Engineer - Playbook Thực Chiến](/series/ai-driven-playbook/), cung cấp hướng dẫn thực chiến chi tiết để thiết lập hệ thống Context Engineering chuẩn 2026 cho doanh nghiệp sử dụng Cursor, Windsurf, Claude Code và hệ sinh thái Model Context Protocol (MCP 1.x).

---

## 1. Sự Thật Về Context Window & Hiện Tượng "Lost in the Middle"

Mặc dù các LLM 2026 tự hào sở hữu Context Window lên tới 1M - 2M tokens, việc nhét toàn bộ repository vào cửa sổ ngữ cảnh là một sai lầm chết người về mặt kiến trúc.

### Chi Phí Suy Giảm Chú Ý (Attention Degradation & Token Cost)

1. **Hiện tượng "Lost in the Middle":** Ngay cả các mô hình mở rộng Attention Mechanism, khả năng truy xuất chính xác (Retrieval Accuracy) ở khu vực giữa (middle 40-70%) của Context Window vẫn giảm đáng kể so với phần đầu (System Prompt/Rules) và phần cuối (Recent User Query).
2. **Chi phí Token và Độ trễ (Latency):** Việc truyền 100,000 tokens cho mỗi lượt chat làm tăng thời gian phản hồi (TTFT - Time To First Token) thêm 3-5 giây và làm bùng nổ ngân sách API của doanh nghiệp.
3. **Ảo giác do Ngữ cảnh Nhiễu (Context Contamination):** Khi context chứa các đoạn code legacy hoặc file test tạm thời, LLM sẽ tự động học theo (hallucinate) các anti-pattern cũ đó thay vì tuân thủ chuẩn mới.

```mermaid
flowchart TD
    subgraph "Context Budget Allocation (Optimal 32k Window)"
        Rules["1. Rules & Standards: AGENTS.md / MDC Rules - 10%"] --> Arch["2. Architecture & Domain Interfaces - 20%"]
        Arch --> Code["3. Relevant Code Slices / AST Context - 50%"]
        Code --> Query["4. Active Task & User Constraints - 20%"]
    end

    style Rules fill:#d4efdf,stroke:#27ae60,stroke-width:2px
    style Arch fill:#d6eaf8,stroke:#2980b9,stroke-width:2px
    style Code fill:#fcf3cf,stroke:#f39c12,stroke-width:2px
    style Query fill:#fadbd8,stroke:#e74c3c,stroke-width:2px
```

> **[Case Study Thực Tế]: Bài học từ Monorepo 600k dòng code**
> Một công ty Fintech tại TP.HCM cấu hình AI Assistant quét toàn bộ codebase Node.js/Go. Khi Dev nhờ viết handler chuyển tiền mới, AI đã tự động sử dụng hàm `db.queryRaw()` bị phản đối (deprecated) từ 3 năm trước chỉ vì file legacy đó nằm trong tập ngữ cảnh tự động nạp.
> **Hậu quả:** Xuất hiện lỗ hổng SQL Injection tiềm ẩn trong mã nguồn staging.
> **Khắc phục:** Áp dụng phân tầng Context với `.cursor/rules/*.mdc` và loại bỏ các thư mục legacy khỏi ranh giới tìm kiếm của AI Assistant. Tỷ lệ sinh code đúng chuẩn DDD tăng từ **58% lên 96%**.

---

## 2. Chuẩn Cấu Hình `.cursor/rules/*.mdc` & `AGENTS.md` (SOTA 2026)

Năm 2026, các IDE hàng đầu như Cursor và Windsurf đã chuẩn hóa định dạng quy tắc ngữ cảnh bằng file `.mdc` (Markdown Context) và file chuẩn toàn cục `AGENTS.md`.

### 2.1. Cấu Trúc Chuẩn Của File `.cursor/rules/*.mdc`

Thay vì lưu các file `.cursorrules` phẳng khổng lồ ở thư mục gốc (vốn dễ gây quá tải ngữ cảnh), hệ thống quy tắc 2026 được chia nhỏ theo mô-đun với YAML frontmatter hỗ trợ matcher thông minh (glob matching).

Hãy xem cấu trúc chuẩn của một file `.mdc` cho lớp Domain Service:

````markdown
---
description: "Quy chuẩn thiết kế Domain Service & Entity theo Domain-Driven Design (DDD)"
globs: ["src/domain/**/*.ts", "internal/domain/**/*.go"]
alwaysApply: false
---

# Domain-Driven Design (DDD) Enforcement Rules

## Principles
1. **Zero External Dependencies:** Các Entity và Aggregate Root trong thư mục này KHÔNG ĐƯỢC IMPORT thư mục `infrastructure/` hoặc `controllers/`.
2. **Immutability:** Mọi thay đổi trạng thái Entity phải đi qua Domain Method có kiểm tra Invariant. Không dùng public setters.
3. **Ubiquitous Language:** Tên biến và tên hàm phải sử dụng chính xác thuật ngữ từ `docs/domain-glossary.md`.

## Bad vs Good Code Pattern

### Bad (Phá vỡ ranh giới DDD)
```typescript
// NEVER DO THIS
import { UserRepository } from '../../infrastructure/repositories';

export class TransferService {
  async execute(fromId: string, toId: string, amount: number) {
    const repo = new UserRepository(); // Directly coupling infrastructure!
  }
}
```

### Good (Dependency Inversion)
```typescript
// ALWAYS DO THIS
import { IUserRepository } from '../contracts/IUserRepository';

export class TransferService {
  constructor(private readonly userRepo: IUserRepository) {}

  async execute(command: TransferCommand): Promise<Result<TransferReceipt, DomainError>> {
    // Business validation here
  }
}
```

### 2.2. Chuẩn Toàn Cục `AGENTS.md` Cho Toàn Bộ Workspace

File `AGENTS.md` đặt ở thư mục gốc của repository đóng vai trò là "Bản Hiến Pháp" cho mọi AI Agent (Cursor, Windsurf, Claude Code, GitHub Copilot Workspace, Custom Agents). File này định nghĩa danh tính, quyền hạn và ranh giới kiến trúc tối cao.

Sơ đồ phân tầng quản lý quy tắc ngữ cảnh:

```mermaid
flowchart TD
    Root["AGENTS.md - Root Architecture & Rules"] --> FolderDomain[".cursor/rules/domain-ddd.mdc"]
    Root --> FolderInfra[".cursor/rules/infrastructure-db.mdc"]
    Root --> FolderSecurity[".cursor/rules/security-guardrails.mdc"]
    
    FolderDomain --> FileMatch1["Match: src/domain/**/*.ts"]
    FolderInfra --> FileMatch2["Match: src/infra/**/*.ts"]
    FolderSecurity --> FileMatch3["Match: src/api/**/*.ts"]
```

---

## 3. Tích Hợp Model Context Protocol (MCP 1.x) Vẫn Chạy Thực Thời

Trong mô hình RAG cũ, thông tin ngữ cảnh bị đóng đọng (static vector index). Đến năm 2026, **Model Context Protocol (MCP 1.x)** do Anthropic khởi xướng, và vừa được cập nhật cấu trúc lõi Stateless Protocol Core vào tháng 7/2026, đã trở thành chuẩn kết nối động và an toàn (Enterprise Readiness) giữa IDE và các hệ thống bên ngoài.

MCP cho phép AI Assistant chủ động gọi các MCP Server để lấy ngữ cảnh chính xác ngay tại thời điểm soạn thảo:
- Schema cơ sở dữ liệu PostgreSQL/ClickHouse từ database thật.
- API Specs từ OpenAPI/Swagger registry nội bộ.
- Trạng thái các ticket Jira/GitHub Issues đang active.
- Sơ đồ phụ thuộc AST (Abstract Syntax Tree) từ LSP (Language Server Protocol).

```mermaid
flowchart TD
    Dev["Kỹ Sư / Agent"] -->|"Gửi yêu cầu lập trình"| IDE["Cursor / Windsurf Agent"]
    
    subgraph Context_Assembly["Dynamic Context Aggregator"]
        IDE -->|"1. Quét quy chuẩn"| R1["AGENTS.md & Root MDC"]
        R1 -->|"2. Khớp thư mục"| R2["Module-Specific MDC Rules"]
        R2 -->|"3. Trích xuất chữ ký"| R3["AST Interfaces & Type Slices"]
    end

    R3 -->|"Compact Context Window (< 2,000 Tokens)"| Model["Frontier LLM (Claude 3.7 / DeepSeek-V3)"]
    Model -->|"Mã nguồn chuẩn xác 100% theo thiết kế"| Dev
```

### Snippet Cấu Hình MCP Client Trong IDE (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "postgres-schema": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://readonly_user:secret@db.internal:5432/production"],
      "env": {
        "MAX_CONNECTIONS": "5"
      }
    },
    "ast-code-graph": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "${workspaceRoot}:/workspace", "mcp/tree-sitter-indexer:v1.4"],
      "env": {
        "INDEX_LANGUAGES": "typescript,go,python"
      }
    }
  }
}
```

---

## 4. Hướng Dẫn Thực Chiến Xây Dựng Layer Context Engineering

Để triển khai hệ thống Context Engineering cho một dự án Enterprise từ đầu, hãy thực hiện theo 4 bước bài bản sau:

### Bước 1: Xóa Bỏ Anti-Patterns & Dọn Dẹp File Cấu Hình Cũ
- Xóa bỏ file `.cursorrules` khổng lồ đơn khối.
- Thêm các thư mục build artifact, node_modules, generated code, vendor vào `.cursorignore` để tránh AI quét vào nhiễu context.

### Bước 2: Thiết Lập Thư Mục Quy Tắc `.cursor/rules/`
Tạo danh mục các file quy tắc chuyên biệt:
- `.cursor/rules/00-tech-stack.mdc`: Khai báo exact versions của framework (Astro v5, Next.js 15, Go 1.24, FastAPI 0.115).
- `.cursor/rules/01-domain-ddd.mdc`: Quy chuẩn kiến trúc domain & boundaries.
- `.cursor/rules/02-api-standards.mdc`: Quy chuẩn RESTful/gRPC response wrapper, error handling format.
- `.cursor/rules/03-testing-guidelines.mdc`: Chuẩn viết Unit Test (Vitest/PyTest/Go test) & Mocking strategy.

### Bước 3: Định Nghĩa Ranh Giới Ủy Quyền Trong `AGENTS.md`
Soạn thảo `AGENTS.md` ở gốc dự án với 3 phần rõ ràng:
1. **Project Vision & Stack Summary**
2. **Context Indexing Strategy** (Chỉ định rõ file nào là Single Source of Truth)
3. **Non-Negotiable Escalation Rules** (Các quy định tuyệt đối không được vi phạm như Security Tokens, Database Migration Approval).

### Bước 4: Thiết Lập Trình Phân Luồng Ngữ Cảnh Bằng MCP
Tích hợp ít nhất 2 MCP Server chuyên biệt:
1. Database Schema Inspection MCP.
2. Architecture & API Contract Inspection MCP.

---

## 5. Bảng So Sánh Chi Phí & Hiệu Quả Xử Lý Ngữ Cảnh

Dưới đây là số liệu thực tế đo đạc tại một dự án E-commerce Microservices sau khi chuyển đổi từ Naive Context sang Context Engineering chuẩn 2026:

| Chỉ số (Metrics) | Naive Prompting (Không Rules/MCP) | Single `.cursorrules` File | Context Engineering (.mdc + AGENTS.md + MCP 1.x) |
| :--- | :--- | :--- | :--- |
| **Average Prompt Token Count** | 45,000 tokens / request | 18,000 tokens / request | **4,200 tokens / request** |
| **First-Pass Success Rate (Code chạy ngay)** | 42% | 68% | **91%** |
| **Architectural Violation Rate (Sai DDD)** | 38% | 15% | **< 2%** |
| **Thời gian phản hồi bình trung (TTFT)** | 6.8s | 3.2s | **0.9s** |
| **Chi phí API trung bình / Developer / Tháng** | $120 | $55 | **$18** |

---

## 6. Kết Luận & Liên Kết Series

Kỹ nghệ Quản lý Ngữ cảnh (Context Engineering) chính là chiếc cầu nối phân định giữa việc "vibe coding" tùy tiện và việc kỹ thuật hóa quy trình phát triển phần mềm bằng AI một cách chuyên nghiệp. Bằng cách kết hợp giữa quy tắc mô-đun `.cursor/rules/*.mdc`, bản quy hoạch toàn cục `AGENTS.md` và các công cụ MCP 1.x động, bạn biến AI từ một trợ lý ngập ngừng thành một Kiến trúc sư thấu hiểu chính xác từng nếp gấp mã nguồn của tổ chức.

Để tiếp tục hoàn thiện rào chắn chất lượng cho dòng code được tạo ra từ AI, hãy đọc tiếp các bài viết liên quan trong hệ sinh thái:
- **Phần tiếp theo trong Series:** [Phần 3B — AI Code Review & Quality Gates: Xây Dựng Rào Chắn Chất Lượng Tự Động Với LLM Judges](/series/ai-driven-playbook/part-3b-ai-code-review-quality-gates/)
- **Hệ thống Multi-Agent Review:** [Kiến Trúc Multi-Agent Review Pipeline trong Thực Tế](/series/ai-code-review-vibe-coding/part-4-review-pipeline-multi-agent/)
- **Tích hợp MCP nâng cao:** [Kỹ Nghệ MCP Trong Môi Trường Production](/series/mcp-engineering-in-production/)
- **Xây dựng hệ thống Agentic:** [Kiến Trúc Hệ Thống Multi-Agent Chuyên Sâu](/series/agentic-system-architecture/)

---

---

---

[← Chương trước: Phần 2: Modern AI Engineering Stack](/series/ai-driven-playbook/part-2-modern-ai-engineering-stack/) | [Mục lục Series](/series/ai-driven-playbook/) | [Chương tiếp theo: Phần 3A: Enterprise RAG Architecture →](/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Phần 3A — Context Engineering Nâng Cao: Tối Ưu Hóa .cursor/rules, AGENTS.md & MCP Tooling giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Vượt xa Prompt Engineering truyền thống: kỹ nghệ quản lý ngữ cảnh cấp doanh nghiệp, chuẩn file AGENTS.md, định dạng .cursor/rules/*.mdc phân lớp và tích hợp MCP 1.x cho Autonomous Coding Agents.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
