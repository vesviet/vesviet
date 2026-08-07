---
title: "The SLM Playbook: Fine-Tuning & Model Distillation"
slug: "slm-playbook"
date: "2026-05-20T21:05:00+07:00"
lastmod: "2026-07-26T15:42:00+07:00"
draft: false
weight: 35
categories: ["SLM Playbook"]
tags: ["SLM", "Fine-Tuning", "vLLM", "AI Infrastructure"]
description: "A practical guide to selecting, fine-tuning (PEFT), aligning (DPO/KTO/GRPO), and serving Small Language Models (SLMs) on self-hosted vLLM and edge infrastructure."
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/slm-fine-tune-vs-prompt-engineering-cover.png"
  alt: "The SLM Playbook: fine-tuning and model distillation series for production AI engineers"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/slm-playbook/"
mermaid: false
image: "/images/posts/slm-fine-tune-vs-prompt-engineering-cover.png"
---

> **Answer-first:** The SLM Playbook is a six-part engineering blueprint for fine-tuning, aligning, distilling, and serving Small Language Models (SLMs) in production. It covers data deduplication (SemDeDup), QLoRA training (Axolotl/Unsloth), knowledge distillation, preference alignment (DPO/GRPO), high-throughput vLLM serving, AWQ quantization, and WasmEdge edge deployment on enterprise GPU and ARM64 infrastructure.

Welcome to our production AI architecture series for self-hosting and scaling Small Language Models (SLMs).

As open-weights SLMs like Llama 3 8B, Phi-4 14B, and Qwen 2.5 Coder 7B reach parity with commercial frontier models on domain-specific tasks, fine-tuning and self-hosting these models provides optimal Total Cost of Ownership (TCO), strict data privacy, and full architectural control.

This playbook provides runnable Python scripts, mathematical derivations, and production configuration templates tested on NVIDIA GPU clusters and ARM64 edge devices.

## Series Contents

- [Executive Summary: The SLM Playbook](/series/slm-playbook/executive-summary/)
- [Part 1: Hybrid AI & Self-Hosted vLLM](/posts/slm-fine-tune-vs-prompt-engineering/)
- [Part 2: Data Engineering for SFT: NEFTune & SemDeDup](/series/slm-playbook/part-2-sft-data-engineering/)
- [Part 3: Practical LoRA & QLoRA Fine-Tuning](/series/slm-playbook/part-3-lora-qlora-tuning/)
- [Part 4: Task & Knowledge Distillation](/posts/slm-fine-tune-vs-prompt-engineering/)
- [Part 5: Preference Alignment (DPO, KTO, GRPO)](/posts/slm-fine-tune-vs-prompt-engineering/)
- [Part 6: Enterprise Serving & Quantization](/posts/slm-fine-tune-vs-prompt-engineering/)

---

> **💡 Core Principle:** Every guide in this series prioritizes reproducible engineering patterns over theory. We include executable Axolotl/Unsloth training configs, AWQ quantization parameters, and async load testing scripts.

## Technical Pillars & Engineering Scope

The matrix below details the six core technical pillars of the SLM Playbook, mapping each phase to its frameworks and production deliverables.

| Phase | Topic | Key Frameworks | Production Deliverables |
|---|---|---|---|
| **Part 1** | Executive Summary & Hybrid AI Architecture | vLLM, LiteLLM, CUDA | Cost & latency routing gateway architecture |
| **Part 2** | Data Engineering for SFT: NEFTune & SemDeDup | SentenceTransformers, SemDeDup, NEFTune | Deduplicated JSONL SFT datasets & noise injection |
| **Part 3** | Practical LoRA & QLoRA Fine-Tuning | Unsloth, PEFT, BitsAndBytes | 4-bit quantized adapter training scripts |
| **Part 4** | Task & Knowledge Distillation | PyTorch, Teacher-Student Pipeline | Compressed SLMs matching frontier LLM accuracy |
| **Part 5** | Preference Alignment (DPO, KTO, GRPO) | TRL, DeepSpeed, GRPO Trainer | Reasoner aligned model checkpoints |
| **Part 6** | Enterprise vLLM Serving & Edge Deployment | vLLM, AWQ, WasmEdge, ONNX | Sub-50ms P99 TTFT multi-LoRA & edge deployments |

## Target Audience & Technical Prerequisites

This playbook is authored for **AI Engineers, Machine Learning Infrastructure Teams, and Software Architects** building self-hosted language model infrastructure.

**Prerequisite:**
- Proficiency in Python, PyTorch, and HuggingFace Transformers.
- Fundamental knowledge of model quantization math (4-bit/8-bit precision) and CUDA VRAM allocation.

## Key System Invariants

1. **Cost & Latency Optimization**: Dynamic hybrid routing directs complex multi-step reasoning to frontier LLMs while serving high-volume domain queries on self-hosted vLLM instances.
2. **P99 Inference Performance**: Sub-50ms Time To First Token (TTFT) achieved using AWQ 4-bit weight quantization and PagedAttention on self-hosted GPU clusters.
3. **Domain Alignment Quality**: Task-specific SFT and preference alignment (DPO/GRPO) ensure over 95% precision on specialized enterprise code generation and structured extraction tasks.

---

## Frequently Asked Questions

Designing and deploying production Small Language Models requires balancing fine-tuning efficiency, memory constraints, and serving latency. The answers below summarize core architectural considerations across the full 6-part playbook lifecycle.

### Why choose Small Language Models (SLMs) over commercial frontier LLMs for enterprise workloads?

Self-hosted SLMs drastically reduce Total Cost of Ownership (TCO) for domain-specific, high-volume inference tasks while guaranteeing strict data privacy and microsecond control over weights and latency. When combined with targeted SFT and preference alignment, 7B to 14B parameter models routinely equal or exceed frontier LLM performance on specialized business benchmarks.

### How does dynamic multi-LoRA routing scale multiple fine-tuned models on single GPU servers?

vLLM loads base model weights into VRAM once and allocates modular memory slots for low-rank adapter matrices. Because adapters represent under 1% of total model parameters, vLLM dynamically swaps adapter weights in real-time per request without incurring engine restart overhead or duplicating base memory footprint.

### When should an enterprise deploy SLMs via vLLM versus edge runtimes like WasmEdge?

High-throughput cloud API services and batch processing pipelines benefit from vLLM's PagedAttention, tensor parallelism, and continuous batching on NVIDIA A10G/H100 GPUs. Conversely, offline environments, mobile applications, and resource-constrained edge gateways achieve optimal performance using GGUF 4-bit quantized models compiled for WasmEdge or Apple Silicon Metal runtimes.
