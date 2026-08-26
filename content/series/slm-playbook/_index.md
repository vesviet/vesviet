---
title: "Sổ Tay: The SLM Playbook - Fine-Tuning & Model Distillation"
slug: "slm-playbook"
description: "Series thực chiến giúp các kỹ sư và kiến trúc sư AI lựa chọn, huấn luyện (PEFT), căn chỉnh (DPO/KTO/GRPO) và vận hành tối ưu các mô hình ngôn ngữ nhỏ (SLMs) trên hạ tầng tự host (vLLM)."
date: 2026-05-20T21:05:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
draft: false
weight: 35
ShowToc: true
TocOpen: true
canonicalURL: "https://tanhdev.com/series/slm-playbook/"
cover:
  image: "/images/posts/default-post.png"
  alt: "Sổ Tay: The SLM Playbook - Fine-Tuning & Model Distillation"
  relative: false
categories: ['Series', 'AI Engineering', 'Machine Learning']
tags: ['SLM', 'Fine-Tuning', 'LoRA', 'QLoRA', 'vLLM', 'DeepSeek-R1', 'DPO', 'GRPO']
---

> **Answer-first:** Sổ Tay SLM Playbook cung cấp hướng dẫn thực chiến giúp doanh nghiệp làm chủ mô hình ngôn ngữ nhỏ (SLMs): kiến trúc Hybrid AI, kỹ nghệ dữ liệu SFT, fine-tuning QLoRA với Axolotl/Unsloth, chắt lọc tri thức DeepSeek-R1, căn chỉnh hành vi (DPO/GRPO) và tối ưu phục vụ mô hình trên vLLM.

Chào mừng bạn đến với **Phase 2.5** của lộ trình làm chủ kiến trúc AI-Native. 

Khi các mô hình ngôn ngữ nhỏ (Small Language Models - SLMs) như Llama 3.1 8B, Phi-4 14B hay Qwen 2.5 Coder 7B đạt tới ngưỡng năng lực tiệm cận các mô hình thương mại lớn (Frontier LLMs) trong các tác vụ chuyên biệt, việc tự huấn luyện và vận hành SLMs trở thành yếu tố cốt lõi để doanh nghiệp tối ưu hóa chi phí (TCO), bảo mật dữ liệu tuyệt đối và làm chủ hoàn toàn công nghệ.

Series này được thiết kế như một **Playbook Kỹ Thuật Thực Chiến**, đi thẳng từ lý thuyết lượng tử hóa, cơ chế toán học của alignment, cho đến cấu hình code mẫu cụ thể trên Axolotl/vLLM để bạn sẵn sàng áp dụng ngay lập tức vào hạ tầng Enterprise.

---

## 📚 Cấu Trúc Sổ Tay SLM Playbook (Chapter Roadmap)

Bộ tài liệu này được chia thành các phần thực hành chuyên sâu theo trình tự phát triển dự án thực tế:

- **[Executive Summary: Sổ Tay Tối Ưu Hóa SLM](/series/slm-playbook/executive-summary/)**  
  *Phân tích bài toán kinh tế (TCO), so sánh chi phí Cloud API vs Self-Hosted SLMs và chiến lược Hybrid AI định hình năm 2026.*

- **[Phần 1: Sự Trỗi Dậy Của SLMs & Kiến Trúc Hybrid AI: Tối Ưu Chi Phí & vLLM](/series/slm-playbook/part-1-slm-hybrid-architecture/)**  
  *Thiết kế kiến trúc Hybrid: định tuyến truy vấn đơn giản về SLM local (vLLM) và chỉ chuyển tiếp bài toán phức tạp lên Frontier LLM.*

- **[Phần 2: Kỹ Nghệ Dữ Liệu Cho SFT: Tiêm Nhiễu NEFTune & SemDeDup](/series/slm-playbook/part-2-sft-data-engineering/)**  
  *Xây dựng tập dữ liệu Supervised Fine-Tuning chất lượng cao: áp dụng NEFTune chống overfitting và lọc trùng ngữ nghĩa SemDeDup.*

- **[Phần 3: Thực Chiến Fine-Tuning LoRA & QLoRA: Axolotl, Unsloth & Double Quantization](/series/slm-playbook/part-3-lora-qlora-tuning/)**  
  *Cấu hình training 4-bit NF4, tối ưu hóa bộ nhớ GPU VRAM với Unsloth/Axolotl và huấn luyện mô hình 7B/14B trên một GPU duy nhất.*

- **[Phần 4: Task & Knowledge Distillation: Chắt Lọc Tri Thức DeepSeek-R1 Sang Qwen Coder](/series/slm-playbook/part-4-knowledge-distillation-r1/)**  
  *Phương pháp chắt lọc chuỗi suy luận (Chain-of-Thought) từ DeepSeek-R1 sang các SLM nhẹ hơn mà không làm suy giảm độ chính xác logic.*

- **[Phần 5: Căn Chỉnh Hành Vi (Preference Alignment): DPO, IPO, KTO & Thuật Toán GRPO](/series/slm-playbook/part-5-preference-alignment/)**  
  *So sánh Direct Preference Optimization (DPO) với Group Relative Policy Optimization (GRPO) loại bỏ hoàn toàn Critic Model.*

- **[Phần 6: Enterprise Serving & Quantization: Dynamic LoRA, Prefix Caching & vLLM](/series/slm-playbook/part-6-vllm-deployment-evals/)**  
  *Triển khai vLLM trên Production: tối ưu Chunked Prefill, PagedAttention, Dynamic LoRA Adapters và benchmark AWQ/GPTQ/GGUF.*

---

## ❓ Câu Hỏi Thường Gặp (FAQ)

{{< faq q="Khi nào doanh nghiệp nên tự host SLM thay vì dùng API của OpenAI/Anthropic?" >}}
Doanh nghiệp nên tự host SLM khi: (1) Khối lượng truy vấn lớn (> 5-10 triệu tokens/ngày) khiến chi phí API vượt quá chi phí thuê GPU, (2) Yêu cầu tuân thủ dữ liệu nghiêm ngặt (Data Privacy, GDPR, PCI-DSS) không được phép gửi dữ liệu ra ngoài, hoặc (3) Cần độ trễ cực thấp (Time-to-First-Token < 50ms) trong mạng nội bộ.
{{< /faq >}}

{{< faq q="QLoRA khác biệt gì so với LoRA thông thường và có làm giảm chất lượng mô hình không?" >}}
LoRA đóng băng trọng số gốc ở định dạng FP16 và huấn luyện các ma trận adapter hạng thấp (low-rank). QLoRA lượng tử hóa các trọng số gốc xuống 4-bit NormalFloat (NF4) kết hợp Double Quantization, giúp giảm hơn 65% dung lượng VRAM (huấn luyện model 7B chỉ cần GPU 12-16GB VRAM) trong khi vẫn duy trì 99% hiệu năng học so với LoRA 16-bit đầy đủ.
{{< /faq >}}

{{< faq q="Thuật toán GRPO (Group Relative Policy Optimization) mang lại bước đột phá gì trong căn chỉnh mô hình?" >}}
GRPO (thuật toán được sử dụng trong DeepSeek-Math và DeepSeek-R1) loại bỏ hoàn toàn sự cần thiết của Critic Model (Reward Model riêng biệt) vốn chiếm tới 50% tài nguyên GPU trong PPO truyền thống. Bằng cách lấy mẫu một nhóm (group) câu trả lời cho cùng một prompt và tính toán phần thưởng tương đối trong nhóm, GRPO cắt giảm một nửa dung lượng bộ nhớ training.
{{< /faq >}}

---

## 🔗 Series Liên Quan & Masterclass Đề Xuất

- **[Enterprise AI Data Pipeline & GraphRAG Architecture](/series/ai-data-engineering-pipeline/)** — Xây dựng pipeline dữ liệu và hạ tầng RAG cho doanh nghiệp.
- **[Sổ Tay: The AI-Driven Playbook](/series/ai-driven-playbook/)** — Cẩm nang thực chiến triển khai AI Gateway và Private AI Platform.
- **[Series: Agentic System Architecture](/series/agentic-system-architecture/)** — Thiết kế hệ thống Multi-Agent phân tán, Memory State và Guardrails.
- **[Chuyên Đề Cornerstone Technologies](/series/cornerstone-technologies/)** — Nền tảng hạ tầng phân tán, Qdrant Vector DB, Temporal Workflows và Zero-Trust.

