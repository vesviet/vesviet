---
title: "Part 8: Inference Optimization & vLLM Deployment on Production"
slug: "part-8-inference-optimization-vllm"
date: "2026-05-17T12:00:00+07:00"
lastmod: "2026-05-17T12:00:00+07:00"
draft: false
weight: 80
tags: ["Inference", "vLLM", "PagedAttention", "Quantization", "FP8", "DevOps"]
description: "Overcoming VRAM limits and optimizing Server costs when deploying 70B LLMs with vLLM, PagedAttention, and FP8/AWQ Quantization."
categories: ["Data Engineering", "AI/ML", "Architecture", "DevOps"]
ShowToc: true
TocOpen: true
aliases:
  - "/series/ai-data-engineering-pipeline/part-8-inference-optimization-vllm/part-9-agentic-observability-monitoring"
  - "/series/ai-data-engineering-pipeline/part-7-agentic-memory-long-term/part-8-inference-optimization-vllm"
cover:
  image: "/images/posts/graphrag-vs-naive-rag-cover.png"
  alt: "Enterprise AI Data Pipeline and GraphRAG Architecture series: graph-based retrieval at scale"
  relative: false
---

## 1. The LLM Bottleneck: Why Are GPUs Still Idle?

After finishing designing the entire Agent architecture in the previous 7 parts, it is time to push your system to Production (live running). Every startup soon realizes a bitter truth: **The enemy of LLMs is not Compute Power, but Memory Bandwidth.**

To run the Llama-3 70B model (standard FP16), you need about 140GB of VRAM just to hold the model weights. But when 100 Users send prompts simultaneously, the system must generate a temporary memory space called the **KV Cache** to retain the context of those 100 conversations.
Instantly, the KV Cache bloats and drains all remaining VRAM. The system throws an `Out-Of-Memory (OOM)` error and crashes, even though the GPU's processing power was only 30% utilized. How do you "cram" more Users into the GPU without overflowing RAM?

---

## 2. The Miracle Named PagedAttention & vLLM

By 2026, **vLLM** has become the irreplaceable gold standard for Inference (HuggingFace's TGI has entered maintenance mode). The heart of vLLM is **PagedAttention** technology.

Previously, systems allocated KV Cache memory in long, contiguous blocks. Because it didn't know if a User would chat a long or short sentence, the system had to "reserve" a massive memory area upfront, causing waste and fragmentation up to 60%.
**PagedAttention** borrows an idea from Operating Systems (Virtual Memory): It divides the KV Cache into small, equal-sized "Pages". It only allocates a new page when a User generates a new Token.
*   **Result:** Memory fragmentation drops to near 0%. On the same GPU cluster, vLLM can handle a User Concurrency load **4 times** higher than the old architecture.

---

## 3. The Art of Stuffing the Conveyor Belt: Continuous Batching

If you use the old architecture (Static Batching), the Server gathers 10 users, waiting for all 10 to finish asking before letting the GPU answer. Whoever asks a short question has to wait for the person asking a long question. The GPU is forced to "wait", which is extremely wasteful.

vLLM utilizes **Continuous Batching (In-flight Batching)**. Everything is processed at the *Per-Token* level:
1. The GPU is busy processing for 10 Users.
2. User A just receives the final word of the answer. User A's position (Slot) is immediately vacated.
3. In less than 1 millisecond, the system grabs User B from the Queue and stuffs them right into that empty Slot.
The GPU doesn't get a single second of rest. Utilization is always >90%, maximizing every cent of your electricity bill.

---

## 4. Model Dieting (Quantization): FP8 and AWQ

No Enterprise is rich enough to run a 70B LLM in native FP16 format. You have to quantize (shrink) the model to fit it into cheaper GPUs.

*   **Enterprise Standard (NVIDIA H100 / Blackwell):** Use **FP8**. With newer GPU lines, FP8 is supported at the hardware level (Hardware Tensor Cores). Squishing down to 8-bit cuts RAM usage in half and boosts processing speed by 1.5x, while Reasoning quality remains almost **lossless**.
*   **Budget Saver (RTX 4090 / A100):** Use **AWQ (INT4)**. Compressing the model to 4-bit reduces VRAM capacity by 75%. You must accept sacrificing a bit of the model's logic, but in return, you can run a 70B model on a dirt-cheap GPU setup. Do not use GGUF on Servers; it is only for local running.

---

## 5. Dismembering the Model: Tensor vs. Pipeline Parallelism

If the quantized model is still too large to fit in 1 GPU, you are forced to use multiple GPUs.
*   **Tensor Parallelism (TP):** Slicing the model vertically. All 4 GPUs compute a Layer simultaneously. This enables extremely fast responses (Low Latency). However, it requires these 4 GPUs to be connected by ultra-fast cables (NVLink), otherwise transmission latency will kill the system.
*   **Pipeline Parallelism (PP):** Slicing the model horizontally. GPU 1 computes the first 20 Layers, then throws the results over to GPU 2 to compute the last 20 Layers. Suitable when stringing together cheap Servers over a LAN, helping increase load capacity (Throughput).

---

## 6. Hacking Speed with Speculative Decoding

The LLM word generation mechanism (Auto-regressive) is very slow because it has to type word by word.
In 2026, **Speculative Decoding** is a mandatory technique for acceleration. Instead of forcing the giant 70B model to type word by word, you hire an ultra-light "Draft" model (e.g., Llama-3 1B) to quickly guess the next 5 words.
Then, the 70B model just glances over those 5 words; if it finds them correct, it "nods" and approves all 5 words simultaneously.
*   **Benefit:** Word generation speed increases by 2 to 3 times, while maintaining 100% of the 70B model's accuracy.

---

## 7. Quick Start vLLM on Production

Below is a standard command (Code Snippet) to launch a vLLM Server compatible with the OpenAI API for a 70B model on a 4-GPU cluster, with FP8 quantization:

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Meta-Llama-3-70B-Instruct \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --quantization fp8
```

## 8. Conclusion

Bringing AI to Production is not throwing a Python file onto a Server. It is an architectural war, where you must use vLLM for memory management (PagedAttention), model quantization (FP8/AWQ), and generation speed hacking (Speculative Decoding).

When the system runs smoothly, the next question is: *"How do I know what my Agent is thinking? If it makes a mistake, at which step did it fail?"*
Let's move on to **[Part 9: Agentic Observability & Monitoring]({{< ref "part-9-agentic-observability-monitoring.md" >}})** to establish a surveillance camera system over the AI's thought process using LangSmith and Langfuse.


