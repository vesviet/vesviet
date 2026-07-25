---
title: "The SLM Playbook: Fine-Tuning & Model Distillation"
date: "2026-05-20T21:05:00+07:00"
lastmod: "2026-05-20T21:05:00+07:00"
draft: false
weight: 35
description: "A practical guide to selecting, fine-tuning (PEFT), aligning (DPO/KTO/GRPO), and deploying Small Language Models (SLMs) on self-hosted vLLM infrastructure."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/slm-fine-tune-vs-prompt-engineering-cover.png"
  alt: "The SLM Playbook: fine-tuning and model distillation series for production AI engineers"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/slm-playbook/"
image: "images/posts/slm-fine-tune-vs-prompt-engineering-cover.png"
---

Welcome to **Phase 2.5** of our AI-Native architecture journey.

As Small Language Models (SLMs) like Llama 3 8B, Phi-4 14B, and Qwen 2.5 Coder 7B reach capabilities matching larger commercial models (Frontier LLMs) in specific domains, self-hosting and fine-tuning these models is the key to optimizing TCO, ensuring data privacy, and retaining full technology control.

This series is designed as a **Hands-On Technical Playbook**, taking you from quantization math and alignment algorithms to concrete Axolotl/vLLM code and configuration templates ready for enterprise scale.

## Series Contents

- [Executive Summary: The SLM Playbook](/series/slm-playbook/executive-summary/)
- [Part 1: Hybrid AI & Self-Hosted vLLM](/series/slm-playbook/part-1-slm-hybrid-architecture/)
- [Part 2: Data Engineering for SFT](/series/slm-playbook/part-2-sft-data-engineering/)
- [Part 3: Practical LoRA & QLoRA Fine-Tuning](/series/slm-playbook/part-3-lora-qlora-tuning/)
- [Part 4: Task & Knowledge Distillation](/series/slm-playbook/part-4-knowledge-distillation-r1/)
- [Part 5: Preference Alignment (DPO, KTO, GRPO)](/series/slm-playbook/part-5-preference-alignment/)
- [Part 6: Enterprise Serving & Quantization](/series/slm-playbook/part-6-vllm-deployment-evals/)

---

> **💡 Core Principle:** This playbook is not just about AI theory. We provide runnable YAML configs, core mathematical derivations, and Python code tested on production NVIDIA A10G/H100 GPUs.


## Technical Pillars & Engineering Scope

| Phase | Topic | Key Frameworks | Production Deliverables |
|---|---|---|---|
| **Part 1** | Hybrid AI & Self-Hosted vLLM | vLLM, LiteLLM, CUDA | Cost & latency routing gateway |
| **Part 2** | Data Engineering for SFT | SentenceTransformers, SemDeDup | Deduplicated JSONL SFT datasets |
| **Part 3** | LoRA & QLoRA Fine-Tuning | Unsloth, PEFT, BitsAndBytes | 4-bit quantized adapter training scripts |
| **Part 4** | Knowledge Distillation | Teacher-Student LLM Pipeline | Compressed SLMs matching frontier models |
| **Part 5** | Preference Alignment | DPO, KTO, GRPO | Aligned model checkpoints for reasoning |
| **Part 6** | Enterprise Serving & Quantization | AWQ, GPTQ, vLLM Engine | Sub-50ms P99 TTFT inference deployments |

## Target Audience & Technical Prerequisites

This playbook is tailored for **AI Engineers, Machine Learning Infrastructure Teams, and Software Architects** seeking to self-host and fine-tune open SLMs.

**Prerequisites:**
- Proficiency in Python, PyTorch, and HuggingFace Transformers ecosystem.
- Basic understanding of LLM quantization math (4-bit/8-bit precision) and GPU memory allocation.

## Key System Invariants

1. **Cost & Latency Optimization**: Dynamic hybrid model router sends high-complexity prompts to frontier LLMs while routing high-volume standard queries to self-hosted vLLM SLM instances.
2. **P99 Inference Performance**: Sub-50ms Time To First Token (TTFT) achieved using AWQ 4-bit tensor parallel quantization on self-hosted GPU clusters.
3. **Domain Alignment Quality**: Task-specific SFT and DPO alignment pipelines ensure 95%+ precision on domain code generation tasks.
