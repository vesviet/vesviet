---
title: "Part 2: SFT Data Engineering — NEFTune & Synthetic Data Curation"
date: 2026-08-18T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Constructing high-signal Supervised Fine-Tuning (SFT) datasets: NEFTune embedding noise injection, semantic deduplication, and quality filtering."
categories: ["Series", "Machine Learning", "Data Engineering"]
tags: ["SFT", "Data Engineering", "NEFTune", "Synthetic Data", "Axolotl"]
series: ["slm-playbook"]
weight: 4
slug: "part-2-sft-data-engineering"
canonicalURL: "https://tanhdev.com/series/slm-playbook/part-2-sft-data-engineering/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 2: SFT Data Engineering — NEFTune & Synthetic Data Curation"
  relative: false
keywords: ["sft data curation", "neftune embedding noise", "synthetic data generation llm"]
---

[← Previous Chapter: Part 1: Hybrid AI Architecture](/series/slm-playbook/part-1-slm-hybrid-architecture/) | [Series Hub](/series/slm-playbook/) | [Next Chapter: Part 3: QLoRA & Axolotl Fine-Tuning →](/series/slm-playbook/part-3-lora-qlora-tuning/)

---

> **Answer-first:** Data quality completely dictates SLM performance. 5,000 meticulously verified, diverse instruction examples consistently outperform 100,000 noisy scraped samples. Adding NEFTune noise injection ($lpha = 5$) to embedding layers prevents overfitting and improves out-of-distribution reasoning.

---
