---
title: "Phần 5: Căn Chỉnh Hành Vi (Preference Alignment): DPO & GRPO"
date: 2026-05-20T21:05:00+07:00
lastmod: "2026-08-16T12:00:00+07:00"
author: "Lê Tuấn Anh"
description: "So sánh Direct Preference Optimization (DPO) với Group Relative Policy Optimization (GRPO) loại bỏ hoàn toàn Critic Model."
categories:
  - "Series"
  - "AI Engineering"
  - "Machine Learning"
tags:
  - "Preference Alignment"
  - "DPO"
  - "GRPO"
  - "RLHF"
  - "DeepSeek"
series:
  - "slm-playbook"
weight: 6
slug: "part-5-preference-alignment"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-5-preference-alignment/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 5: Căn Chỉnh Hành Vi (Preference Alignment): DPO & GRPO"
  relative: false
---

[← Chương trước: Phần 4: Knowledge Distillation: Chắt Lọc Tri Thức DeepSeek-R1](/series/slm-playbook/part-4-knowledge-distillation-r1/) | [Mục lục Series](/series/slm-playbook/) | [Chương tiếp theo: Phần 6: Enterprise Serving & Quantization Với vLLM →](/series/slm-playbook/part-6-vllm-deployment-evals/)

---

> **Answer-first:** Căn chỉnh hành vi mô hình bằng DPO loại bỏ hoàn toàn bước huấn luyện Reward Model, trong khi thuật toán GRPO (sử dụng trong DeepSeek-R1) tối ưu phần thưởng nhóm tương đối giúp giảm 50% bộ nhớ training so với PPO truyền thống.

Huấn luyện tinh chỉnh có giám sát (SFT) là bước đệm đưa tri thức vào mô hình, nhưng nó không dạy mô hình cách xử lý các tình huống phức tạp: Khi nào câu trả lời là an toàn hay độc hại, hoặc làm thế nào để tự nhận lỗi sai và sửa lại trong quá trình suy luận.

Để mô hình ngôn ngữ thực sự tương tác thông minh và hữu ích theo ý muốn của con người, chúng ta phải tiến hành bước **Căn chỉnh hành vi (Preference Alignment)**. 

Bài viết này sẽ đưa bạn đi sâu vào thế giới của học tăng cường căn chỉnh LLMs. Chúng ta sẽ cùng so sánh cơ chế toán học của **DPO**, **KTO** và đặc biệt là thuật toán **GRPO (Group Relative Policy Optimization)** — giải pháp đứng sau sự thành công của DeepSeek-R1 và các mô hình tiên tiến trong năm 2026 giúp giải phóng 50% dung lượng VRAM huấn luyện.

---

## 1. DPO vs KTO: Căn Chỉnh Không Cần Reward Model

Trong phương pháp học tăng cường truyền thống từ phản hồi của con người (RLHF), chúng ta bắt buộc phải huấn luyện một **Mô hình Phần thưởng (Reward Model)** riêng biệt để chấm điểm các câu trả lời của mô hình chính (Policy Model). Việc này nhân đôi gánh nặng phần cứng và cực kỳ bất ổn định trong quá trình tối ưu hóa.

```
┌──────────────────────────────────────────────────────────────┐
│            So Sánh Căn Chỉnh DPO vs KTO vs RLHF              │
├──────────────────────────────┬───────────────────────────────┤
│ RLHF (Truyền thống)          │ Cần 4 mô hình chạy đồng thời:  │
│                              │ Policy, Reference, Critic,    │
│                              │ và Reward Model. Cực kỳ tốn   │
│                              │ bộ nhớ GPU.                   │
├──────────────────────────────┼───────────────────────────────┤
│ DPO (Được ưa chuộng nhất)    │ Không cần Reward Model. Chỉ   │
│                              │ cần so sánh giữa cặp dữ liệu  │
│                              │ Chosen (Ưa thích) và Rejected │
│                              │ (Bị loại bỏ).                 │
├──────────────────────────────┼───────────────────────────────┤
│ KTO (Không cần dữ liệu cặp)  │ Phù hợp cho nhãn nhị phân     │
│                              │ Like/Dislike đơn lẻ, lấy cảm  │
│                              │ hứng từ tâm lý học hành vi.   │
└──────────────────────────────┴───────────────────────────────┘
```

### 1.1. DPO: Tối Ưu Hóa Tỷ Lệ Trực Tiếp (Direct Preference Optimization)
DPO chứng minh bằng toán học rằng: Ta có thể biến đổi trực tiếp hàm mất mát RL thành một bài toán phân loại nhị phân trên chính mô hình Policy `pi_theta`, bỏ qua hoàn toàn bước huấn luyện Reward Model.
*   *Hàm mất mát DPO (DPO Loss):*
`L_DPO(theta; pi_ref) = - E_(x, y_w, y_l) [ log sigma ( beta * log(pi_theta(y_w|x)/pi_ref(y_w|x)) - beta * log(pi_theta(y_l|x)/pi_ref(y_l|x)) ) ]`

Trong đó:
*   `pi_ref` là mô hình tham chiếu gốc (frozen reference model) để tránh policy bị trôi quá xa (KL divergence guard).
*   `y_w` (chosen) là câu trả lời tốt, `y_l` (rejected) là câu trả lời kém.
*   `sigma` là hàm kích hoạt Sigmoid.
*   `beta` là hệ số kiểm soát độ phạt KL divergence (thường chọn `beta ∈ [0.1, 0.5]`).

### 1.2. KTO: Kahneman-Tversky Optimization
DPO đòi hỏi dữ liệu phải ở dạng bắt cặp hoàn hảo (Chosen - Rejected cho cùng một câu hỏi). KTO phá vỡ giới hạn này bằng cách sử dụng lý thuyết vi mô về hành vi con người (Prospect Theory từ nhà kinh tế học Daniel Kahneman). KTO cho phép huấn luyện trực tiếp trên các dữ liệu đơn lẻ được gán nhãn đúng/sai (Like/Dislike), mở rộng tối đa nguồn dữ liệu thu thập thực tế.

---

## 2. GRPO: Giải Pháp Tối Ưu Khả Năng Suy Luận Của DeepSeek

Đối với các tác vụ lập luận logic (Reasoning) như giải toán hoặc viết code, chúng ta có thể dễ dàng thiết lập các quy tắc kiểm tra tự động (Rule-Based Verifiers) thay cho con người (ví dụ: chạy thử code trong sandbox xem testcase có pass không, hoặc đối chiếu kết quả cuối cùng với đáp án toán học chính xác).

Tuy nhiên, nếu sử dụng thuật toán RLHF truyền thống (như PPO), ta cần duy trì một mô hình chấm điểm đánh giá **Critic Model** có kích thước tương đương với mô hình chính (Policy).

**GRPO (Group Relative Policy Optimization)** giải quyết triệt để bài toán này bằng cách loại bỏ hoàn toàn Critic Model ra khỏi kiến trúc huấn luyện RL.

```
   Quy trình GRPO (Group Relative Policy Optimization):

                 ┌────────────────┐
                 │  Prompt (x)    │
                 └───────┬────────┘
                         │
        [Sinh đồng thời G câu trả lời mẫu]
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Out 1       Out 2       Out G (e.g. G = 16)
             │           │           │
             └───────────┼───────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   Verifiers   │ (Rule-based scoring, e.g. Regex / Test cases)
                 └───────┬───────┘
                         │
                [Tính Reward R_i]
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  Normalize: (R_i - Mean) / Std   │ (Sử dụng trung bình nhóm làm baseline)
        └────────────────┬─────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────┐
        │   Cập nhật Trọng số Policy (θ)   │
        └──────────────────────────────────┘
```

### 2.1. Cơ Chế Hoạt Động Của GRPO
Với mỗi câu hỏi đầu vào `x`:
1.  **Lấy mẫu nhóm (Group Sampling):** Mô hình Policy `pi_theta` sinh ra một nhóm gồm `G` câu trả lời khác nhau `{y_1, y_2, ..., y_G}` (thường chọn `G ∈ [16, 64]`).
2.  **Đánh giá phần thưởng (Rewards Evaluation):** Dùng các bộ kiểm tra tự động (Verifiers) chấm điểm cho từng câu trả lời, trả về danh sách phần thưởng `{r_1, r_2, ..., r_G}`.
3.  **Chuẩn hóa tương đối (Relative Reward):** Trọng số của mỗi câu trả lời được tính toán dựa trên mức độ hiệu quả hơn của nó so với trung bình của nhóm:
`r_tilde_i = (r_i - mean(R)) / std(R)`
    Bằng cách này, giá trị trung bình của nhóm tự đóng vai trò làm **Baseline** (thay thế nhiệm vụ dự đoán của Critic Model).
4.  **Tối ưu hóa chính sách (Policy Gradient Update):** Cập nhật trọng số của Policy bằng cách cực đại hóa phần thưởng tương đối của các câu trả lời tốt, kết hợp phạt khoảng cách KL để kiểm soát độ ổn định của mô hình.

### 2.2. Lợi Thế Tiết Kiệm VRAM Cực Hạn
Bằng cách cắt bỏ Critic Model và giảm thiểu overhead lưu trữ trạng thái tối ưu hóa của nó, GRPO giảm tải tiêu thụ bộ nhớ GPU đi **50%**. Điều này cho phép doanh nghiệp thực hiện huấn luyện Reinforcement Learning cho các mô hình 8B hoặc 14B trực tiếp trên các cụm máy chủ tầm trung mà không cần thuê hàng chục GPU H100 siêu đắt đỏ.

---

## 3. Mã Nguồn Thực Tế: Mô Phỏng Căn Chỉnh GRPO Bằng Python

Dưới đây là đoạn mã Python mô phỏng quy trình tính toán hàm mất mát (Loss) và cập nhật Policy theo thuật toán GRPO, giúp bạn hiểu rõ cơ chế vận hành của nó trong thực tế:

```python
import torch
import torch.nn.functional as F

def compute_grpo_loss(policy_logits, ref_logits, rewards, kl_coeff=0.01):
    """
    Mô phỏng tính toán loss GRPO cho một nhóm câu trả lời.
    
    Args:
        policy_logits: Tensor (G, sequence_len, vocab_size) - logit từ mô hình đang train
        ref_logits: Tensor (G, sequence_len, vocab_size) - logit từ mô hình tham chiếu
        rewards: List[float] - điểm phần thưởng thô từ Verifier cho từng câu trả lời trong nhóm
        kl_coeff: Hệ số phạt khoảng cách KL
    """
    G = len(rewards)
    
    # 1. Chuẩn hóa phần thưởng tương đối trong nhóm
    rewards_tensor = torch.tensor(rewards, dtype=torch.float32)
    mean_r = rewards_tensor.mean()
    std_r = rewards_tensor.std() + 1e-8
    normalized_advantages = (rewards_tensor - mean_r) / std_r
    
    # 2. Tính Log Probabilities của chuỗi token sinh ra
    # Giả lập token được chọn bằng cách lấy argmax
    selected_tokens = torch.argmax(policy_logits, dim=-1)
    
    policy_log_probs = F.log_softmax(policy_logits, dim=-1)
    ref_log_probs = F.log_softmax(ref_logits, dim=-1)
    
    # Trích xuất log_prob của các token đã sinh ra
    policy_action_log_probs = policy_log_probs.gather(2, selected_tokens.unsqueeze(-1)).squeeze(-1).sum(dim=-1)
    ref_action_log_probs = ref_log_probs.gather(2, selected_tokens.unsqueeze(-1)).squeeze(-1).sum(dim=-1)
    
    # 3. Tính tỷ lệ thay đổi Policy (Importance Sampling Ratio)
    ratio = torch.exp(policy_action_log_probs - ref_action_log_probs)
    
    # 4. Tính toán hàm mất mát Policy (PPO Clipped Objective tương đối)
    # Clipped surrogate loss giúp ngăn chính sách thay đổi quá đột ngột
    surr1 = ratio * normalized_advantages
    surr2 = torch.clamp(ratio, 0.8, 1.2) * normalized_advantages
    policy_loss = -torch.min(surr1, surr2).mean()
    
    # 5. Phạt khoảng cách KL Divergence trực tiếp
    # Dùng xấp xỉ KL: log(pi_theta) - log(pi_ref)
    kl_div = (policy_action_log_probs - ref_action_log_probs).mean()
    
    total_loss = policy_loss + kl_coeff * kl_div
    
    return total_loss, policy_loss.item(), kl_div.item()

if __name__ == "__main__":
    # Giả lập nhóm gồm G = 4 mẫu trả lời, độ dài chuỗi = 10, vocab_size = 1000
    G = 4
    seq_len = 10
    vocab_size = 1000
    
    # Logits ngẫu nhiên từ Policy và Reference Model
    torch.manual_seed(42)
    policy_logits = torch.randn(G, seq_len, vocab_size, requires_grad=True)
    ref_logits = torch.randn(G, seq_len, vocab_size)
    
    # Điểm thưởng thô giả lập từ bộ Verifier (Ví dụ: mẫu 1 và 4 giải đúng toán, mẫu 2 và 3 sai)
    raw_rewards = [1.0, 0.0, 0.0, 1.0]
    
    loss, p_loss, kl = compute_grpo_loss(policy_logits, ref_logits, raw_rewards)
    
    print(f"GRPO Simulation Results:")
    print(f"Total Loss: {loss.item():.4f}")
    print(f"Policy Loss Component: {p_loss:.4f}")
    print(f"KL Divergence Penalty Component: {kl:.4f}")
```

---

## 4. Tầm Quan Trọng Của Việc Căn Chỉnh Hành Vi Với Doanh Nghiệp

Triển khai Preference Alignment giúp doanh nghiệp chuyển đổi các mô hình AI từ dạng "thông thái nhưng bất kham" thành các Agent làm việc chuẩn mực:
*   **Định hình văn phong nhất quán:** Đảm bảo câu trả lời luôn ở định dạng ngắn gọn, tôn trọng khách hàng, không chứa từ ngữ lặp hoặc sáo rỗng.
*   **Bảo vệ an toàn dữ liệu:** Huấn luyện mô hình từ chối cung cấp thông tin nhạy cảm của hệ thống, chống lại các kỹ thuật tấn công prompt injection.
*   **Tối ưu hóa độ chính xác:** Định hướng mô hình suy nghĩ logic sâu trước khi đưa ra kết quả, thay vì đoán mò kết quả ngay lập tức.

---

## Kế Hoạch Cho Bài Viết Tiếp Theo

Sau khi đã hoàn thiện từ khâu chuẩn bị dữ liệu, huấn luyện tinh chỉnh LoRA, cho đến căn chỉnh hành vi mô hình bằng thuật toán GRPO, chúng ta đã sở hữu một SLM hoàn chỉnh ở mức tối ưu cao nhất. Bước cuối cùng để đưa mô hình này ra thực chiến là chuyển hóa nó thành một API phục vụ thương mại với hiệu năng tải cực khủng.

Trong [**Phần 6: Enterprise Serving & Quantization**](/series/slm-playbook/part-6-vllm-deployment-evals/), chúng ta sẽ học cách lượng tử hóa mô hình sang định dạng **AWQ**, **GPTQ** và **GGUF**, cấu hình phục vụ đa mô hình qua **Dynamic LoRA** và benchmark hiệu năng vLLM thực chiến.

---

### 🔗 Đọc thêm các chuyên đề liên quan:
- [Kiến trúc Microservices Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Triển khai Agentic AI Swarm trong Production với OpenClaw & LiteLLM](/posts/deploying-autonomous-ai-swarm-openclaw-litellm/)
- [Kiến trúc Microservices Golang gRPC: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/)

---

[← Chương trước: Phần 4: Knowledge Distillation: Chắt Lọc Tri Thức DeepSeek-R1](/series/slm-playbook/part-4-knowledge-distillation-r1/) | [Mục lục Series](/series/slm-playbook/) | [Chương tiếp theo: Phần 6: Enterprise Serving & Quantization Với vLLM →](/series/slm-playbook/part-6-vllm-deployment-evals/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Căn Chỉnh Hành Vi (Preference Alignment): DPO & GRPO giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
So sánh Direct Preference Optimization (DPO) với Group Relative Policy Optimization (GRPO) loại bỏ hoàn toàn Critic Model.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
