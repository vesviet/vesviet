---
title: "Phần 3: Thực Chiến Fine-Tuning QLoRA: Axolotl & Unsloth"
date: 2026-05-20T21:05:00+07:00
lastmod: "2026-08-16T12:00:00+07:00"
author: "Lê Tuấn Anh"
description: "Cấu hình training 4-bit NF4, tối ưu hóa bộ nhớ GPU VRAM với Unsloth/Axolotl và huấn luyện mô hình 7B/14B trên một GPU duy nhất."
categories:
  - "Series"
  - "AI Engineering"
  - "Machine Learning"
tags:
  - "LoRA"
  - "QLoRA"
  - "Axolotl"
  - "Unsloth"
  - "Quantization"
series:
  - "slm-playbook"
weight: 4
slug: "part-3-lora-qlora-tuning"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-3-lora-qlora-tuning/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Phần 3: Thực Chiến Fine-Tuning QLoRA: Axolotl & Unsloth"
  relative: false
---

[← Chương trước: Phần 2: Kỹ Nghệ Dữ Liệu Cho SFT: NEFTune & SemDeDup](/series/slm-playbook/part-2-sft-data-engineering/) | [Mục lục Series](/series/slm-playbook/) | [Chương tiếp theo: Phần 4: Knowledge Distillation: Chắt Lọc Tri Thức DeepSeek-R1 →](/series/slm-playbook/part-4-knowledge-distillation-r1/)

---

> **Answer-first:** QLoRA lượng tử hóa trọng số gốc xuống định dạng 4-bit NormalFloat (NF4) kết hợp Double Quantization và Paged Optimizers. Kỹ thuật này giảm hơn 65% VRAM, cho phép fine-tune mô hình 8B-14B trên một GPU 24GB duy nhất (A10G/L4) mà vẫn bảo toàn 99% độ chính xác.

Huấn luyện tinh chỉnh toàn phần (Full Parameter Fine-Tuning) một mô hình ngôn ngữ lớn là một đặc quyền xa xỉ. Đối với một mô hình nhỏ như Llama 3.1 8B, việc cập nhật toàn bộ tham số ở định dạng 16-bit vẫn đòi hỏi cụm phần cứng khổng lồ vượt xa khả năng của các nhà phát triển hoặc startup vừa và nhỏ.

Để giải quyết bài toán tài nguyên, các kỹ thuật **PEFT (Parameter-Efficient Fine-Tuning)** ra đời, nổi bật nhất là **LoRA** và **QLoRA**. Chúng cho phép huấn luyện các mô hình hàng tỷ tham số trên duy nhất một chiếc GPU phổ thông (như RTX 3090, 4090 hoặc A10G) mà không làm suy giảm chất lượng đầu ra.

Bài viết này sẽ đi sâu giải mã toán học đằng sau kỹ thuật nén lượng tử, cách thiết lập cấu hình **Axolotl** thực chiến và cách tận dụng **Unsloth** để tăng tốc độ huấn luyện gấp nhiều lần.

---

## 1. LoRA: Cơ Chế Phân Rã Ma Trận Hạng Thấp (Low-Rank Adaptation)

Khi mô hình thực hiện các tác vụ chuyên biệt (ví dụ: Text-to-SQL hoặc chẩn đoán y khoa), các thay đổi trọng số trong quá trình tối ưu hóa thực chất có **"hạng nội tại" (intrinsic rank)** rất thấp. Thay vì cập nhật toàn bộ ma trận trọng số gốc `W_0 ∈ R^(d x k)`, LoRA đóng băng `W_0` và mô hình hóa lượng cập nhật trọng số `Delta W` dưới dạng tích của hai ma trận có hạng cực nhỏ `r` (`r << min(d, k)`):

`Delta W = B * A`

Trong đó:
*   `W_0` là ma trận trọng số gốc đã bị đóng băng (không cập nhật gradient).
*   `B ∈ R^(d x r)` và `A ∈ R^(r x k)` là hai ma trận adapter huấn luyện được.
*   `r` là tham số **Rank** (thường chọn `r ∈ [8, 64]`).

```
        Forward Pass trong LoRA Layer:
        
             Input x 
             ┌───┴───┐
             │       │
             ▼       ▼
          ┌─────┐ ┌─────┐
          │     │ │  A  │ (Rank r, Khởi tạo Gaussian)
          │ W_0 │ └─────┘
          │     │    │ (Vector r-chiều)
          │(Frozen)  ▼
          │     │ ┌─────┐
          │     │ │  B  │ (Rank r, Khởi tạo bằng 0)
          └─────┘ └─────┘
             │       │
             ▼       ▼
            h_W     h_LoRA * (alpha / r)
             └───┬───┘
                 ▼
              Output y
```

### 1.1. Công thức Forward Pass của LoRA
Khi nhận đầu vào `x`, đầu ra ẩn `y` được tính bằng tổng tích lũy:
`y = W_0 * x + Delta W * x = W_0 * x + (alpha / r) * (B * A * x)`

Trong đó:
*   `alpha` là cờ tỷ lệ (scaling factor) cố định giúp điều tiết tầm ảnh hưởng của adapter lên trọng số gốc.
*   Tại thời điểm bắt đầu huấn luyện, ma trận `A` được khởi tạo ngẫu nhiên theo phân phối Gaussian, còn ma trận `B` được khởi tạo hoàn toàn bằng 0. Do đó, `Delta W = 0 * A = 0`, nghĩa là hành vi ban đầu của mô hình hoàn toàn không bị ảnh hưởng.

---

## 2. QLoRA: Đỉnh Cao Tiết Kiệm VRAM Nhờ Lượng Tử Hóa Kép

Được giới thiệu bởi Tim Dettmers vào năm 2023, **QLoRA (Quantized Low-Rank Adaptation)** đưa khả năng tiết kiệm VRAM lên một tầm cao mới bằng cách lượng tử hóa ma trận gốc `W_0` xuống định dạng **4-bit** siêu nén, trong khi vẫn duy trì độ chính xác của LoRA adapter ở định dạng 16-bit.

QLoRA dựa trên ba phát kiến toán học và hệ thống cốt lõi:

### 2.1. Kiểu dữ liệu NormalFloat 4-bit (NF4)
Trọng số của mạng Nơ-ron (Neural Network) thường tuân theo phân phối chuẩn (Normal Distribution) với giá trị trung bình bằng 0 và phương sai xác định. Các kiểu dữ liệu lượng tử hóa tuyến tính truyền thống (như INT4) phân bổ các vạch lượng tử đều nhau, dẫn đến lãng phí độ chính xác ở các vùng biên dữ liệu thưa thớt.

NF4 giải quyết vấn đề này bằng cách thiết lập các vạch lượng tử phi tuyến tính sao cho **mỗi vạch lượng tử chứa một lượng thông tin (xác suất) bằng nhau**:
`Tích phân từ q_i đến q_(i+1) của N(0, 1) dx = hằng số`

Nhờ đó, NF4 giữ lại được lượng thông tin tối đa của mô hình gốc, triệt tiêu gần như hoàn toàn sai số lượng tử hóa so với FP4.

### 2.2. Lượng tử hóa kép (Double Quantization - DQ)
Trong lượng tử hóa chuẩn, các khối trọng số được chia nhỏ và chuẩn hóa bằng một hệ số tỷ lệ 32-bit (Quantization Constant). Với kích thước khối là 64, lượng overhead bộ nhớ này chiếm khoảng `32 / 64 = 0.5` bits trên mỗi tham số.

Double Quantization tiến hành lượng tử hóa **chính các hệ số tỷ lệ này** từ 32-bit xuống FP8 với kích thước khối là 256.
*   *Lợi ích:* Giảm dung lượng overhead từ `0.5` bits/parameter xuống còn `0.127` bits/parameter. Tiết kiệm thêm khoảng **3 GB VRAM** cho mô hình 8B, mở ra cơ hội chạy trên các card đồ họa phổ thông.

### 2.3. Bộ tối ưu hóa phân trang (Paged Optimizers)
Khi huấn luyện chuỗi dài hoặc kích thước batch lớn, các đỉnh bộ nhớ (VRAM Spikes) đột ngột xảy ra khi tính toán gradient có thể gây lỗi treo máy sập hệ thống (OOM).

Paged Optimizers sử dụng tính năng CUDA Unified Memory để tự động hoán đổi (page) các trạng thái tối ưu hóa (Optimizer States) giữa VRAM của GPU và RAM hệ thống của Host CPU trong các bước xử lý tải cao. Nhờ cơ chế này, quá trình train sẽ chậm lại đôi chút thay vì bị crash giữa chừng.

---

## 3. Thực Chiến: Cấu Hình Axolotl YAML Cho QLoRA

**Axolotl** là framework chuẩn Enterprise cho việc fine-tune LLM nhờ tính ổn định và khả năng tích hợp sẵn FlashAttention-2, Deepspeed và FSDP.

Dưới đây là file cấu hình `qlora_llama3_8b.yml` hoàn chỉnh tối ưu hóa cho card đồ họa NVIDIA A10G (24GB VRAM):

```yaml
# Cấu hình Mô hình & Kiểu huấn luyện
base_model: meta-llama/Llama-3.1-8B-Instruct
model_type: LlamaForCausalLM
tokenizer_type: PreTrainedTokenizerFast

# Bật QLoRA (Lượng tử hóa 4-bit NF4)
load_in_8bit: false
load_in_4bit: true
gptq: false

# Cấu hình chi tiết Lượng tử hóa 4-bit
bf16: true
fp16: false
tf32: true

# Target modules cho LoRA (Phải phủ toàn bộ các lớp tuyến tính của Llama)
adapter: qlora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj
  - gate_proj
  - up_proj
  - down_proj

# Dataset cấu hình
datasets:
  - path: ./temp_cleaned_dataset.jsonl
    type: alpaca
    shards: 10
dataset_prepared_path: ./last_run_prepared
val_set_size: 0.05
output_dir: ./lora-llama3-8b-output

# Tối ưu hóa bộ nhớ và tốc độ
sequence_len: 8192
sample_packing: true
pad_to_sequence_len: true
flash_attention: true

# Hyperparameters huấn luyện
gradient_accumulation_steps: 4
micro_batch_size: 2
num_epochs: 3
optimizer: paged_adamw_8bit
lr_scheduler: cosine
learning_rate: 0.0002
weight_decay: 0.01
max_grad_norm: 1.0

# Lưu trữ checkpoint
save_steps: 100
eval_steps: 100
logging_steps: 10
```

---

## 4. Tăng Tốc 3x Bằng Unsloth

Mặc dù Axolotl rất mạnh mẽ, nhưng việc triển khai các kernel tính toán ngược (backward pass) mặc định của PyTorch vẫn còn nhiều khoảng trống tối ưu. **Unsloth** đã tái cấu trúc lại các phép tính thủ công của lớp Attention và MLP bằng ngôn ngữ **OpenAI Triton**, giúp tăng tốc độ huấn luyện lên tới **3x** và giảm dung lượng VRAM tiêu hao thêm **60%**.

### Mã Nguồn Thực Thi Huấn Luyện QLoRA Bằng Unsloth:

```python
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

max_seq_length = 4096 # Rút ngắn để tối ưu hóa tốc độ trên GPU 24GB
dtype = None # Tự động phát hiện (Float16 hoặc Bfloat16)
load_in_4bit = True # Bật 4bit quantization

# 1. Khởi tạo Mô hình và Tokenizer thông qua Unsloth
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "meta-llama/Llama-3.1-8B-Instruct",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# 2. Thiết lập LoRA Adapter tích hợp sẵn cấu trúc tối ưu của Unsloth
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 32,
    lora_dropout = 0, # Unsloth tối ưu tuyệt đối khi dropout = 0
    bias = "none",
    use_gradient_checkpointing = "unsloth", # Tối ưu hóa bộ nhớ lưu trữ gradient
    random_state = 3407,
)

# 3. Chuẩn bị Format Dataset (Alpaca style)
alpaca_prompt = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{}

### Response:
{}"""

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    outputs      = examples["output"]
    texts = []
    for inst, out in zip(instructions, outputs):
        text = alpaca_prompt.format(inst, out) + tokenizer.eos_token
        texts.append(text)
    return { "text" : texts }

# Load tập dữ liệu đã qua lọc trùng lặp ở Phần 2
dataset = load_dataset("json", data_files="temp_cleaned_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched = True)

# 4. Cấu hình Trainer bằng SFTTrainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Có thể bật True nếu muốn nhóm các câu ngắn lại để train nhanh hơn
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10,
        max_steps = 120, # Số bước huấn luyện test
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

# Chạy huấn luyện
trainer_stats = trainer.train()

# 5. Lưu mô hình (LoRA Adapter duy nhất)
model.save_pretrained("lora_model_adapter")
tokenizer.save_pretrained("lora_model_adapter")
print("Training complete! Model saved.")
```

---

## 5. Hướng Dẫn Merge Weights Trọng Số

Sau khi huấn luyện LoRA/QLoRA hoàn tất, bạn sẽ nhận được một thư mục chứa các file adapter cực nhẹ (chỉ khoảng vài chục MB đến vài trăm MB). Để đưa mô hình vào chạy suy luận thực tế (Inference serving) với tốc độ tối đa trên vLLM, bạn cần gộp (merge) các trọng số LoRA adapter này vào lại mô hình gốc 16-bit.

### Mã Nguồn Gộp Trọng Số & Xuất Định Dạng 16-bit:

```python
from unsloth import FastLanguageModel

# Khởi tạo lại mô hình gốc và load adapter đã train
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "meta-llama/Llama-3.1-8B-Instruct",
    max_seq_length = 4096,
    dtype = None,
    load_in_4bit = False, # Bắt buộc phải là False để xuất ra định dạng FP16/BF16 nguyên bản
)
model.load_adapter("lora_model_adapter")

# Thực hiện merge và lưu trực tiếp lên đĩa cứng
print("Merging weights and saving to disk...")
model.save_pretrained_merged("merged_model_fp16", tokenizer, save_method = "merged_16bit")
print("Merge complete! Ready for vLLM serving.")
```

Mô hình lưu tại thư mục `merged_model_fp16` giờ đây là một mô hình 16-bit độc lập, sẵn sàng để khởi chạy bằng lệnh `vllm serve` mà không cần thêm bất kỳ cấu hình adapter phức tạp nào khác.

---

## Kế Hoạch Cho Bài Viết Tiếp Theo

Việc tinh chỉnh mô hình bằng SFT giúp mô hình định dạng được cấu trúc câu trả lời và ghi nhớ phong cách giao tiếp của doanh nghiệp. Tuy nhiên, đối với các tác vụ đòi hỏi khả năng suy luận logic chuyên sâu (Reasoning) như giải toán lập trình phức tạp, phương pháp SFT đơn thuần là chưa đủ.

Trong [**Phần 4: Task & Knowledge Distillation**](/series/slm-playbook/part-4-knowledge-distillation-r1/), chúng ta sẽ khám phá cách "chắt lọc tri thức" từ các siêu mô hình (như **DeepSeek-R1**) sang SLM thông qua cơ chế chưng cất Chain of Thought (CoT), biến mô hình thành "nhà lập luận" thực thụ.

---

### 🔗 Đọc thêm các chuyên đề liên quan:
- [Kiến trúc Microservices Golang & DDD](/posts/architecting-21-service-ecommerce-golang-ddd/)
- [Triển khai Agentic AI Swarm trong Production với OpenClaw & LiteLLM](/posts/deploying-autonomous-ai-swarm-openclaw-litellm/)
- [Kiến trúc Microservices Golang gRPC: Protobuf, TLS & Middleware](/posts/golang-grpc-microservices-production-guide/)

---

[← Chương trước: Phần 2: Kỹ Nghệ Dữ Liệu Cho SFT: NEFTune & SemDeDup](/series/slm-playbook/part-2-sft-data-engineering/) | [Mục lục Series](/series/slm-playbook/) | [Chương tiếp theo: Phần 4: Knowledge Distillation: Chắt Lọc Tri Thức DeepSeek-R1 →](/series/slm-playbook/part-4-knowledge-distillation-r1/)


---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Thực Chiến Fine-Tuning QLoRA: Axolotl & Unsloth giải quyết vấn đề cốt lõi nào trong kiến trúc hệ thống?
Cấu hình training 4-bit NF4, tối ưu hóa bộ nhớ GPU VRAM với Unsloth/Axolotl và huấn luyện mô hình 7B/14B trên một GPU duy nhất.

### Q2: Những lưu ý quan trọng nhất khi triển khai thực tế là gì?
Cần chú trọng phân tầng ranh giới trách nhiệm (bounded context), thiết lập cơ chế fallback dự phòng, và giám sát chặt chẽ qua metrics OpenTelemetry để phát hiện sớm các điểm nghẽn.

### Q3: Làm sao để kiểm thử và đánh giá hiệu quả sau khi áp dụng?
Áp dụng kiểm thử tải (load test), benchmark độ trễ P95/P99 trước và sau triển khai, kết hợp tracing phân tán để xác minh tính ổn định dưới tải cao.
