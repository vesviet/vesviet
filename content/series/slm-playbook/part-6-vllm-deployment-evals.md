---
title: "Optimizing vLLM Serving: AWQ, GPTQ, & GGUF | SLM Playbook"
date: 2026-05-26T08:00:00+07:00
lastmod: 2026-05-26T08:00:00+07:00
draft: false
description: "SLM production serving guide on vLLM. Compare AWQ, GPTQ, and GGUF quantization formats and set up memory-efficient Dynamic LoRA serving configurations."
ShowToc: true
TocOpen: true
weight: 7
categories: ["Series", "SLM Playbook"]
tags: ["AI Engineering", "vLLM", "Quantization", "Model Serving", "AWQ"]
aliases:
  - "/series/slm-playbook/part-2-vllm-serving/"
---
[â† Series hub](/series/slm-playbook/)
[â† Previous](/series/slm-playbook/part-5-preference-alignment/)

Successfully training and aligning a Small Language Model (SLM) is only half the battle. In enterprise environments, deploying a model to production serving requires solving three major challenges: **high request concurrency**, **low response latency**, and **minimized compute cost**.

To achieve this, we must master model compression (**Quantization**) and high-performance serving configurations using **vLLM**â€”the state-of-the-art serving engine for LLMs.

This final article in **The SLM Playbook** series compares the technical attributes of AWQ, GPTQ, and GGUF quantization formats, details how to set up **Dynamic LoRA serving** to conserve VRAM, and outlines a resilient enterprise-grade serving architecture.

---

## 1. Comparing Quantization Formats: AWQ vs. GPTQ vs. GGUF

Quantization is the process of compressing model weights from 16-bit floating-point (FP16/BF16) to lower-bit integer representations (such as INT8 or INT4). This drastically reduces VRAM requirements and accelerates hardware compute operations.

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                Quantization Format Comparison                â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Format           â”‚ Primary Target   â”‚ Technical Attributes   â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ AWQ (Recommended)â”‚ GPU Serving      â”‚ Preserves the top 1%   â”‚
â”‚                  â”‚                  â”‚ salient weights in     â”‚
â”‚                  â”‚                  â”‚ FP16. Retains accuracy.â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ GPTQ             â”‚ GPU Serving      â”‚ Calibration-based      â”‚
â”‚                  â”‚                  â”‚ linear quantization.   â”‚
â”‚                  â”‚                  â”‚ Minor accuracy loss.   â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ GGUF             â”‚ CPU / Edge       â”‚ Supports dynamic layer â”‚
â”‚                  â”‚                  â”‚ offloading to host CPU â”‚
â”‚                  â”‚                  â”‚ RAM (via llama.cpp).   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 1.1. AWQ (Activation-aware Weight Quantization)
Not all weights in a neural network contribute equally to its output representation. AWQ discovered that protecting just **1% of the most salient weight channels** from quantization preserves the majority of model capability.
*   *Mechanism:* AWQ identifies these salient weight channels, keeps them in their native 16-bit format, and quantizes the remaining 99% of non-salient channels to 4-bit.
*   *Verdict:* AWQ consistently yields lower perplexity (better accuracy) compared to GPTQ on reasoning tasks while executing fast on NVIDIA GPUs using optimized CUDA kernels.

### 1.2. GPTQ (Generalized Post-Training Quantization)
GPTQ utilizes a calibration dataset to compute second-order weight influences (the Hessian matrix), adjusting remaining weights to compensate for quantization errors.
*   *Verdict:* Widely supported across all serving engines. However, for smaller models (under 8B parameters), GPTQ can occasionally introduce noticeable degradation on complex math or programming tasks.

### 1.3. GGUF (GPT-Generated Unified Format)
Developed by the open-source community surrounding `llama.cpp`, GGUF is a single-file model format optimized for mixed CPU/GPU execution.
*   *Verdict:* The standard for running models on local developer machines (MacBooks, laptops) or edge deployments lacking dedicated datacenter GPUs. It is not recommended for high-throughput enterprise backend clusters.

---

## 2. Designing a Dynamic LoRA Architecture

In enterprise deployments, different teams require distinct fine-tuned behaviors (e.g., accounting needs JSON invoice classification, while engineering needs code debugging).

Hosting separate model instances on individual GPUs drives up infrastructure budgets exponentially. vLLM's **Dynamic LoRA Serving** resolves this issue.

```
                   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                   â”‚  User Request  â”‚
                   â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
             [Determine Target Adapter via Headers]
             [e.g., 'X-Lora-Adapter: accounting']
                           â”‚
                           â–¼
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚        vLLM Server Container         â”‚
         â”‚                                      â”‚
         â”‚        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”         â”‚
         â”‚        â”‚   Base Model 8B   â”‚         â”‚ (Shared in VRAM)
         â”‚        â”‚   (FP16 or AWQ)   â”‚         â”‚
         â”‚        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜         â”‚
         â”‚                  â”‚                   â”‚
         â”‚     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”‚
         â”‚     â–¼            â–¼            â–¼      â”‚ (Loaded dynamically
         â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”  â”‚  on-demand)
         â”‚ â”‚Lora A â”‚    â”‚Lora B â”‚    â”‚Lora C â”‚  â”‚
         â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”˜  â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 2.1. How Dynamic LoRA Operates
vLLM loads a single, shared base model (e.g., Llama 3 8B AWQ) into GPU VRAM. When a request specifies a target LoRA adapter, vLLM dynamically loads the adapter parameters from disk or system RAM and computes the delta weight adjustment ($\Delta W$) on-the-fly during the forward pass.
*   *Advantage:* Reduces memory overhead by up to 90%. Dozens of fine-tuned task-specific adapters can be served simultaneously on a single 24GB GPU.

### 2.2. vLLM Production Command for Dynamic LoRA
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --quantization awq \
    --enable-lora \
    --max-loras 8 \
    --max-lora-rank 16 \
    --lora-dtype auto
```

When invoking the API, clients simply specify their target adapter in the request payload:
```json
{
  "model": "accounting-lora-adapter",
  "messages": [
    {"role": "user", "content": "Analyze this invoice..."}
  ]
}
```

---

## 3. Production Serving Benchmarks

The following benchmarks demonstrate the memory and throughput gains achieved on a single NVIDIA A10G (24GB VRAM) running **Llama 3 8B**:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                     Serving Benchmark Results                â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Format           â”‚ Throughput (tps) â”‚ Peak VRAM Usage        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ FP16 (Baseline)  â”‚ 32 tokens/sec    â”‚ 16.2 GB (Low batch     â”‚
â”‚                  â”‚                  â”‚ limits, prone to OOM)  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ GPTQ 4-bit       â”‚ 74 tokens/sec    â”‚ 6.4 GB (Supports high  â”‚
â”‚                  â”‚                  â”‚ concurrency batches)   â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ AWQ 4-bit        â”‚ 78 tokens/sec    â”‚ 6.1 GB (15% faster     â”‚
â”‚                  â”‚                  â”‚ TTFT than GPTQ)        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

*   **Takeaway:** Compressing your model to **AWQ 4-bit** saves over **60% of GPU VRAM**, increasing sustained serving throughput by **2.4x** compared to FP16. This provides a resilient foundation for serving high-concurrency enterprise workloads.

---

## Summary of The SLM Playbook

Our 6-part playbook equips you with the complete workflow needed to customize and serve Small Language Models within your private enterprise infrastructure:

1.  **Architecture Design:** Balance cost and capability by deploying local SLMs alongside cloud frontier models via a Hybrid Router Gateway.
2.  **Data Engineering:** Mitigate memorization and clean instruction data using NEFTune noise injection and SemDeDup semantic pruning.
3.  **High-Performance Training:** Execute LoRA/QLoRA training loops using Axolotl and Unsloth to optimize GPU utilization.
4.  **Knowledge Distillation:** Distill structured reasoning paths (Chain of Thought) from deep models like DeepSeek-R1.
5.  **Preference Alignment:** Align outputs and safety parameters using sample-efficient DPO and GRPO reinforcement learning.
6.  **Enterprise Serving:** Quantize models to 4-bit AWQ and serve multiple tasks concurrently via Dynamic LoRA on vLLM.

By combining hardware optimization with targeted alignment, your team can deploy private, highly optimized models that guarantee data privacy at a fraction of the cost of public APIs.

*Access the complete source code and configs on the [**SLM Playbook Home Page**](/series/slm-playbook/).*

{{< author-cta />}}

