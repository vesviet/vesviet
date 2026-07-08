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
