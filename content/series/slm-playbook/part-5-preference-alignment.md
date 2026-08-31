---
title: "Part 5: Preference Alignment with DPO (Direct Preference Optimization)"
date: 2026-08-21T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Aligning Small Language Models with Direct Preference Optimization (DPO) to eliminate hallucinations, enforce JSON compliance, and prevent format violations."
categories: ["Series", "Machine Learning", "AI Alignment"]
tags: ["DPO", "Direct Preference Optimization", "Alignment", "RLHF", "JSON Schema"]
series: ["slm-playbook"]
weight: 7
slug: "part-5-preference-alignment"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-5-preference-alignment/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 5: Preference Alignment with DPO"
  relative: false
keywords: ["direct preference optimization dpo", "slm alignment dpo", "json format enforcement llm"]
---

[← Previous Chapter: Part 4: Knowledge Distillation](/series/slm-playbook/part-4-knowledge-distillation-r1/) | [Series Hub](/series/slm-playbook/) | [Next Chapter: Part 6: Enterprise vLLM Deployment →](/series/slm-playbook/part-6-vllm-deployment-evals/)

---

> **Answer-first:** DPO aligns model outputs directly on paired preference datasets (Chosen vs Rejected) using a closed-form loss function, completely bypassing the instability and memory overhead of training a separate PPO reward model.

---
