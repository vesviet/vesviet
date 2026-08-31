---
title: "Part 6: Enterprise vLLM Deployment, Quantization & Automated Evals"
date: 2026-08-22T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Deploying production SLMs on vLLM with AWQ/FP8 quantization, continuous batching, and automated LLM-as-a-judge CI/CD evaluation pipelines."
categories: ["Series", "AI Infrastructure", "LLMOps"]
tags: ["vLLM", "Quantization", "AWQ", "FP8", "LLM Evals", "Kubernetes"]
series: ["slm-playbook"]
weight: 8
slug: "part-6-vllm-deployment-evals"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-6-vllm-deployment-evals/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 6: Enterprise vLLM Deployment, Quantization & Automated Evals"
  relative: false
keywords: ["vllm production deployment", "awq quantization vllm", "llm automated evaluation pipeline"]
---

[← Previous Chapter: Part 5: Preference Alignment](/series/slm-playbook/part-5-preference-alignment/) | [Series Hub](/series/slm-playbook/)

---

> **Answer-first:** Productionizing SLMs requires AWQ/FP8 quantization (cutting VRAM by 50% with zero perplexity loss), continuous batching via vLLM, and automated CI/CD evaluation pipelines using LLM-as-a-judge to catch regressions before deployment.

---
