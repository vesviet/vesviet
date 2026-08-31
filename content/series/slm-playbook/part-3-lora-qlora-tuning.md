---
title: "Part 3: QLoRA & Axolotl Fine-Tuning on Commodity GPUs"
date: 2026-08-19T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Practical guide to fine-tuning 3B–8B parameter models on a single 24GB GPU using 4-bit NormalFloat QLoRA and the Axolotl training framework."
categories: ["Series", "Machine Learning", "AI Infrastructure"]
tags: ["QLoRA", "Axolotl", "Fine-Tuning", "PyTorch", "HuggingFace"]
series: ["slm-playbook"]
weight: 5
slug: "part-3-lora-qlora-tuning"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-3-lora-qlora-tuning/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 3: QLoRA & Axolotl Fine-Tuning on Commodity GPUs"
  relative: false
keywords: ["qlora fine tuning axolotl", "train slm 24gb gpu", "lora rank alpha target modules"]
---

[← Previous Chapter: Part 2: SFT Data Engineering](/series/slm-playbook/part-2-sft-data-engineering/) | [Series Hub](/series/slm-playbook/) | [Next Chapter: Part 4: Knowledge Distillation →](/series/slm-playbook/part-4-knowledge-distillation-r1/)

---

> **Answer-first:** QLoRA compresses base model weights into 4-bit NormalFloat (NF4) while training 16-bit LoRA adapter matrices on attention and MLP projections. A 7B parameter model trains smoothly on a single $1.20/hr cloud GPU (NVIDIA A10G / RTX 4090).

---
