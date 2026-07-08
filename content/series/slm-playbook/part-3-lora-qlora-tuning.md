---
title: "Practical QLoRA Fine-tuning: Axolotl & Unsloth | SLM Playbook"
date: "2026-05-23T08:00:00+07:00"
lastmod: "2026-07-02T00:00:00+07:00"
draft: false
description: "Fine-tune LoRA/QLoRA for SLMs. Understand Double Quantization, configure Axolotl YAML, and accelerate training 3x using Unsloth."
ShowToc: true
TocOpen: true
weight: 4
categories: ["Series", "SLM Playbook"]
tags: ["AI Engineering", "Fine-Tuning", "LoRA", "Axolotl", "Unsloth"]
cover:
  image: "images/posts/slm-fine-tune-vs-prompt-engineering-cover.png"
  alt: "SLM Playbook series: fine-tuning, LoRA, QLoRA, and production deployment of Small Language Models"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-3-lora-qlora-tuning/"
---
**QLoRA fine-tuning lets you adapt a multi-billion parameter model on a single consumer GPU — like an RTX 3090 or A10G — by combining LoRA adapter training with 4-bit NF4 quantization.** This article covers the math, a production Axolotl YAML config, and Unsloth integration for 3x training speedup.

[← Series hub](/series/slm-playbook/)
[← Previous](/series/slm-playbook/part-2-sft-data-engineering/) | [Next →](/series/slm-playbook/part-4-knowledge-distillation-r1/)

---

## 1. LoRA: Low-Rank Adaptation Matrix Decomposition

**LoRA reduces fine-tuning cost by freezing all original model weights and training only two small adapter matrices (A and B) of rank r — typically 8–64. This cuts trainable parameters by over 99% versus full fine-tuning with near-zero performance loss.**

During domain-specific fine-tuning (e.g., text-to-SQL or medical terminology), parameter weight updates do not occupy the full parameter space; they exhibit a very low **intrinsic rank**. Instead of updating the massive original weight matrix $W_0 \in \mathbb{R}^{d \times k}$, LoRA freezes $W_0$ and models the weight updates $\Delta W$ as the product of two extremely low-rank matrices $B$ and $A$ of rank $r$ ($r \ll \min(d, k)$):

$$\Delta W = B \cdot A$$

Where:
*   $W_0$ is the frozen pre-trained weight matrix (no gradient updates).
*   $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$ are the trainable adapter matrices.
*   $r$ is the **Rank** parameter (typically $r \in [8, 64]$).

```
        LoRA Layer Forward Pass:
        
             Input x 
             ┌───┴───┐
             │       │
             ▼       ▼
          ┌─────┐ ┌─────┐
          │     │ │  A  │ (Rank r, Gaussian initialized)
          │ W_0 │ └─────┘
          │     │    │ (r-dimensional vector)
          │(Frozen)  ▼
          │     │ ┌─────┐
          │     │ │  B  │ (Rank r, Zero initialized)
          └─────┘ └─────┘
             │       │
             ▼       ▼
            h_W     h_LoRA * (alpha / r)
             └───┬───┘
                 ▼
              Output y
```

### 1.1. LoRA Forward Pass Equation
For a given input $x$, the output activation $y$ is computed as:
$$y = W_0 x + \Delta W x = W_0 x + \frac{\alpha}{r} (B A x)$$

Where:
*   $\alpha$ is a constant scaling factor that controls the adapter's influence over the base model weights.
*   At the start of training, $A$ is randomly initialized via a Gaussian distribution, and $B$ is initialized to zero. Consequently, $\Delta W = 0 \times A = 0$, ensuring the model's baseline behavior is completely unchanged at step zero.

---

## 2. QLoRA: Maximizing VRAM Efficiency via Double Quantization

**QLoRA quantizes the frozen base model weights to 4-bit NF4 precision while keeping LoRA adapter weights in 16-bit — saving ~3 GB VRAM on an 8B model versus standard 4-bit quantization. It enables fine-tuning a 70B model on a single A100 80GB.**

Introduced by Tim Dettmers in 2023, **QLoRA (Quantized Low-Rank Adaptation)** takes memory efficiency a step further by quantizing the base model weights $W_0$ to a highly compressed **4-bit** representation, while keeping the active LoRA adapter weights in 16-bit precision.

QLoRA relies on three key mathematical and systems innovations:

### 2.1. NormalFloat 4 (NF4) Data Type
Neural network weights naturally follow a zero-centered normal distribution. Standard linear quantization schemes (like INT4) allocate quantization bins uniformly, wasting precision at the sparse tails of the distribution.

NF4 addresses this by establishing non-linear quantization intervals such that **each bin contains an equal number of expected parameters (equal information entropy)**:
$$\int_{q_i}^{q_{i+1}} \mathcal{N}(0, 1) dx = \text{const}$$

This preserves the maximum information of the original FP16 weights, matching FP4/INT4 precision while cutting model weight size to 4 bits per parameter.

### 2.2. Double Quantization (DQ)
In standard quantization, weight blocks are scaled using a 32-bit float constant. With a block size of 64, this scaling constant introduces an overhead of $32 / 64 = 0.5$ bits per parameter.

Double Quantization quantizes **these scaling constants themselves** from 32-bit floats to 8-bit floats with a block size of 256.
*   *Impact:* Reduces scaling overhead from $0.5$ bits/parameter to $0.127$ bits/parameter, saving approximately **3 GB VRAM** on an 8B model.

### 2.3. Paged Optimizers
During training with long sequence lengths or large batches, sudden gradient allocation spikes can exceed physical VRAM limits, triggering OOM crashes.

Paged Optimizers leverage CUDA Unified Memory to automatically swap (page) optimizer states between GPU VRAM and CPU RAM during peak memory phases, gracefully slowing down training rather than crashing.

---

## 3. Hands-On: Configuring Axolotl for QLoRA

**Axolotl uses a single YAML file to define the entire fine-tuning pipeline — base model, dataset, LoRA config, and hardware settings. Set `load_in_4bit: true` and `adapter: qlora` to activate QLoRA mode. The config below is production-tested on a single NVIDIA A10G (24 GB VRAM).**

**Axolotl** is a robust framework for LLM fine-tuning, offering native integration with FlashAttention-2, DeepSpeed, and PyTorch FSDP.

Here is a complete production-ready `qlora_llama3_8b.yml` configuration optimized for a single NVIDIA A10G (24GB VRAM):

```yaml
# Model & Training Mode Config
base_model: meta-llama/Meta-Llama-3-8B-Instruct
model_type: LlamaForCausalLM
tokenizer_type: PreTrainedTokenizerFast

# Enable QLoRA (4-bit NF4 Quantization)
load_in_8bit: false
load_in_4bit: true
gptq: false

# Precision settings
bf16: true
fp16: false
tf32: true

# LoRA Adapter Configuration
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

# Dataset Configurations
datasets:
  - path: ./temp_cleaned_dataset.jsonl
    type: alpaca
    shards: 10
dataset_prepared_path: ./last_run_prepared
val_set_size: 0.05
output_dir: ./lora-llama3-8b-output

# Memory & Speed Optimizations
sequence_len: 8192
sample_packing: true
pad_to_sequence_len: true
flash_attention: true

# Hyperparameters
gradient_accumulation_steps: 4
micro_batch_size: 2
num_epochs: 3
optimizer: paged_adamw_8bit
lr_scheduler: cosine
learning_rate: 0.0002
weight_decay: 0.01
max_grad_norm: 1.0

# Checkpointing & Logs
save_steps: 100
eval_steps: 100
logging_steps: 10
```

---

## 4. Accelerating Loops: 3x Speedup with Unsloth

**Unsloth replaces PyTorch's standard attention and MLP backward kernels with hand-written OpenAI Triton kernels, delivering a 3x training speedup and 60% memory reduction on the same GPU — with no accuracy loss. It works out-of-the-box as a drop-in replacement for Hugging Face model loading.**

While Axolotl is highly configurable, standard PyTorch backward passes for attention layers leave performance on the table. **Unsloth** rewrites the attention and MLP backward steps in raw **OpenAI Triton**, achieving a **3x speedup** while reducing memory consumption by **60%**.

### Complete Python script to execute QLoRA using Unsloth:

```python
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

max_seq_length = 4096 # Limit context length to optimize speed on 24GB GPUs
dtype = None # Auto-detect (Float16 or Bfloat16)
load_in_4bit = True # Enable 4-bit quantization

# 1. Initialize model and tokenizer via Unsloth
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "meta-llama/Meta-Llama-3-8B-Instruct",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# 2. Add optimized LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 32,
    lora_dropout = 0, # Unsloth is optimized for dropout = 0
    bias = "none",
    use_gradient_checkpointing = "unsloth", # Memory-optimized gradient checkpointing
    random_state = 3407,
)

# 3. Format SFT Prompts (Alpaca style)
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

# Load semantic deduplicated dataset from Part 2
dataset = load_dataset("json", data_files="temp_cleaned_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched = True)

# 4. Setup SFT Trainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Set to True to pack short sequences and speed up training
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10,
        max_steps = 120, # Number of training steps for test run
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

# Execute training run
trainer_stats = trainer.train()

# 5. Save model adapter weights
model.save_pretrained("lora_model_adapter")
tokenizer.save_pretrained("lora_model_adapter")
print("Training complete! Model saved.")
```

---

## 5. Merging LoRA Weights for Serving

**After training, merge your LoRA adapter weights (typically 50–500 MB) back into the base model at fp16 to create a self-contained checkpoint. This removes the adapter dependency and enables direct loading by vLLM, TGI, or any inference engine without LoRA support.**

Fine-tuning via LoRA outputs a directory of adapter weights (typically 50MB - 500MB). To run high-performance inference serving with engines like vLLM, you should merge these adapter matrices back into the 16-bit base model weights.

### Python Script to Merge Weights:

```python
from unsloth import FastLanguageModel

# Load the base model and model adapter in native 16-bit
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "meta-llama/Meta-Llama-3-8B-Instruct",
    max_seq_length = 4096,
    dtype = None,
    load_in_4bit = False, # Must be False to export back to native 16-bit float
)
model.load_adapter("lora_model_adapter")

# Execute weights merge and save to disk
print("Merging weights and saving to disk...")
model.save_pretrained_merged("merged_model_fp16", tokenizer, save_method = "merged_16bit")
print("Merge complete! Ready for vLLM serving.")
```

The output in `merged_model_fp16` is a standalone 16-bit Hugging Face model directory ready to be loaded by `vllm serve`.

---

## Next Chapter

Supervised Fine-Tuning instructs your model on formatting styles and conversational behavior. However, complex, multi-step logical operations (Reasoning) benefit from structured channelling of reasoning steps.

In [**Part 4: Task & Knowledge Distillation**](/series/slm-playbook/part-4-knowledge-distillation-r1/), we explore how to extract reasoning traces (Chain of Thought - CoT) from larger teacher models like **DeepSeek-R1** into small student models.

> **Not sure if fine-tuning is the right approach?** Before investing in LoRA/QLoRA training, see the decision framework: [Prompt Engineering vs Fine-Tuning: When to Use Each (GPT-5 Era)](/posts/slm-fine-tune-vs-prompt-engineering/) — covers the full tradeoff matrix including RAG and MCP tool-use as alternatives for the 2026 AI stack.

{{< author-cta >}}
