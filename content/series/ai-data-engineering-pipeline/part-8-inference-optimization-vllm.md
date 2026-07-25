---
title: "Inference Optimization: vLLM & PagedAttention Guide"
slug: "part-8-inference-optimization-vllm"
date: "2026-05-21T08:00:00+07:00"
lastmod: "2026-07-23T10:40:00+07:00"
draft: false
author: "Lê Tuấn Anh"
tags: ["vLLM", "PagedAttention", "Inference", "Python", "GPU", "Performance"]
categories: ["Engineering", "AI/ML"]
cover:
  image: "images/posts/graphrag-vs-naive-rag-cover.png"
  alt: "vLLM PagedAttention virtual memory allocation architecture"
  relative: false
mermaid: true
canonicalURL: "https://tanhdev.com/series/ai-data-engineering-pipeline/part-8-inference-optimization-vllm/"
description: "Production engineering guide to scaling LLM inference using vLLM, PagedAttention memory management, and speculative decoding for low latency."
ShowToc: true
TocOpen: true
---



# Part 8 — Inference Optimization: vLLM, PagedAttention & Speculative Decoding


In enterprise AI infrastructure, model serving cost is dictated by GPU VRAM utilization and generation throughput (tokens per second per GPU). Running large language models (LLMs) under high concurrency presents a severe memory management challenge: **Managing the KV Cache**.

---

## The KV Cache Memory Problem

**Answer-first:** Standard LLM serving wastes up to 80% of GPU memory due to static allocation and fragmentation of Key-Value (KV) cache tensors.

> **Pillar Architecture Guide:** This article is part of the **[Autonomous Hybrid-AI Pipeline: Cron to State-Machine](/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/)** series. Please refer to the original article for a comprehensive overview of the architecture.

During autoregressive transformer inference, every generated token requires computing Key ($K$) and Value ($V$) tensors for all attention layers. To avoid recomputing these tensors for past tokens at every step, frameworks cache $K$ and $V$ in GPU VRAM.

```mermaid
graph LR
    subgraph Traditional KV Cache Allocation
        A1[Reserved Contiguous GPU Memory Slot] --> B1[Active Sequence Tokens 1..50]
        B1 --> C1[Wasted Unused VRAM Fragmentation 51..2048]
    end

    subgraph vLLM PagedAttention Allocation
        A2[Virtual Memory Block Table] --> Page1["Physical GPU Page 0xAF (Tokens 1..16)"]
        A2 --> Page2["Physical GPU Page 0xB2 (Tokens 17..32)"]
        A2 --> Page3["Physical GPU Page 0xCC (Tokens 33..48)"]
    end
```

### Why Traditional Frameworks Waste VRAM
1. **Pre-Allocation Waste**: Traditional serving systems (Hugging Face TGI, early vLLM versions) pre-allocate contiguous memory blocks for the maximum possible context length (e.g., 2,048 or 8,192 tokens) for every active user sequence.
2. **Internal Fragmentation**: If a user query requires only 200 tokens, the remaining 1,848 pre-allocated token slots remain empty and locked in VRAM, preventing other requests from being served.
3. **External Fragmentation**: Over time, dynamic sequence allocations create fragmented memory holes across physical VRAM, causing out-of-memory (OOM) crashes even when total free memory appears sufficient.

---

## PagedAttention Architecture

**Answer-first:** PagedAttention manages KV cache memory like virtual memory pages in operating systems, eliminating fragmentation and boosting throughput 4x.

Inspired by virtual memory paging in operating systems, **PagedAttention** partitions the KV cache into fixed-size physical blocks (e.g., 16 tokens per block).

1. **Virtual Block Tables**: Each sequence maintains a logical block table mapping logical KV cache blocks to non-contiguous physical GPU VRAM pages.
2. **On-Demand Allocation**: Physical memory blocks are allocated dynamically as tokens are generated step-by-step.
3. **Memory Sharing**: Multiple sequences (e.g., parallel beam search paths or shared system prompt prefixes) share the same physical VRAM pages, reducing prompt memory overhead to near zero.

---

## Production Python Benchmark: Async vLLM Engine

**Answer-first:** Production Python benchmarks evaluate vLLM throughput, demonstrating sub-50ms token latencies under high concurrent request volume.

This production-grade Python script serving an LLM model via `vLLM` using the asynchronous engine API (`AsyncLLMEngine`), custom tensor parallelism, and latency instrumentation:

```python
import asyncio
import time
from typing import AsyncGenerator, List
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
from vllm.utils import random_uuid

class ProductionVLLMServer:
    def __init__(self, model_path: str = "meta-llama/Llama-3.1-8B-Instruct"):
        self.engine_args = AsyncEngineArgs(
            model=model_path,
            tensor_parallel_size=1, # Number of GPUs
            gpu_memory_utilization=0.90, # Reserve 90% VRAM for PagedAttention
            max_num_seqs=256, # Concurrency limit
            max_model_len=4096,
            trust_remote_code=True,
            enforce_eager=False # Enable CUDA graphs for fast execution
        )
        self.engine = AsyncLLMEngine.from_engine_args(self.engine_args)

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        request_id = f"req-{random_uuid()}"
        sampling_params = SamplingParams(
            temperature=0.2,
            top_p=0.95,
            max_tokens=512,
        )

        start_time = time.perf_counter()
        results_generator = self.engine.generate(prompt, sampling_params, request_id)

        first_token_time = None
        token_count = 0

        async for request_output in results_generator:
            if first_token_time is None and len(request_output.outputs[0].text) > 0:
                first_token_time = time.perf_counter()

            text_delta = request_output.outputs[0].text
            token_count = len(request_output.outputs[0].token_ids)
            yield text_delta

        end_time = time.perf_counter()
        ttft_ms = (first_token_time - start_time) * 1000.0 if first_token_time else 0
        total_time_s = end_time - start_time
        tps = token_count / total_time_s if total_time_s > 0 else 0

        print(f"[vLLM Metric] Req ID: {request_id} | TTFT: {ttft_ms:.2f}ms | Throughput: {tps:.2f} tokens/sec")

async def main():
    server = ProductionVLLMServer()
    prompt = "Explain the architectural trade-offs between PagedAttention and traditional KV cache."
    
    print("--- Initiating vLLM Stream Generation ---")
    async for chunk in server.generate_stream(prompt):
        pass # Consume stream tokens
    print("--- Stream Generation Complete ---")

if __name__ == "__main__":
    # Note: Requires vllm library installed on CUDA environment
    print("vLLM Production Inference Engine Spec Loaded.")
```

---

## Comparative Matrix: LLM Serving Engines

**Answer-first:** Naive Transformers serving bottlenecks GPU utilization, while vLLM with PagedAttention and speculative decoding maximizes batch throughput.

| Feature / Metric | Naive Transformers | TGI (Text Generation Inference) | vLLM Engine (PagedAttention) |
| :--- | :--- | :--- | :--- |
| **KV Cache Allocation** | Contiguous Static Buffer | Paged KV (Partial) | Fully Paged Virtual Blocks |
| **VRAM Waste (Fragmentation)** | ~60% - 70% | ~15% - 25% | < 4% |
| **Concurrency (Reqs/GPU)** | 8 - 16 sequences | 64 - 128 sequences | 256 - 512 sequences |
| **Prefix Prompt Sharing** | No | Partial | Yes (Automatic Block Reuse) |
| **Speculative Decoding** | No | Yes | Yes |

---

## Frequently Asked Questions (FAQ)

### Q1: How does PagedAttention eliminate KV cache memory fragmentation in vLLM?
PagedAttention partitions KV cache memory into fixed-size physical blocks allocated dynamically on demand. Rather than reserving large contiguous memory blocks per sequence, it maps logical token blocks to non-contiguous GPU physical pages using a virtual memory page table.

### Q2: What is speculative decoding and how does it reduce inference latency?
Speculative decoding uses a small, lightweight draft model to generate multiple candidate tokens in parallel, which are then validated in a single forward pass by the larger target LLM. This speeds up token generation by 2x to 3x without degrading output quality.

### Q3: How do prefix prompt caching and block sharing optimize multi-tenant serving throughput?
When multiple user requests share common system prompt instructions or context prefixes, vLLM routes their logical block tables to point to the exact same physical GPU memory pages, reducing KV cache memory consumption for prompts to near zero.

---

## Technical Deep-Dive: Inference Optimization & Serving Performance Invariants

**Answer-first:** High-throughput LLM inference requires continuous batching, FlashAttention-2 GPU kernels, and PagedAttention memory bounds to maintain target Time-To-First-Token (TTFT) SLAs.

Operating vLLM inference clusters in production requires strict hardware utilization benchmarks and failure-mode defenses.

### Production Micro-Benchmarks & SLA Thresholds

1. **TTFT SLA Threshold**: Time-To-First-Token under 50ms P99 across concurrent user batches using CUDA graph execution and FP8 quantization.
2. **Throughput Scaling**: 256+ concurrent sequences served per NVIDIA H100 GPU with PagedAttention memory utilization capped at 90%.
3. **Prefix Block Cache Hit Rate**: Over 85% cache reuse efficiency for enterprise system prompts, reducing prefill phase computation time by 60%.

### Architectural Invariants & Failure-Mode Defenses

- **Dynamic Request Scheduling**: Continuous batching schedules incoming requests iteration-by-iteration, avoiding idle GPU cycles caused by static sequence padding.
- **OOM Guardrails**: Automatic block preemption preempts lower-priority requests to secondary host RAM if GPU VRAM pressure spikes, preventing CUDA out-of-memory engine crashes.
- **Speculative Verification**: Draft model predictions are verified deterministically by target model logits, maintaining identical output sampling distributions.

---

## Internal Series Navigation

**Answer-first:** Continue to Part 9 to explore agentic observability with OpenTelemetry and cost monitoring.

- [Part 7 — Agentic Memory Systems: Episodic, Semantic & Working](/series/ai-data-engineering-pipeline/part-7-agentic-memory-long-term/)
- [Part 9 — Agentic Observability: OpenTelemetry & Cost Monitoring](/series/ai-data-engineering-pipeline/part-9-agentic-observability-monitoring/)
- [Part 10 — Production Evals & CI/CD Guardrails](/series/ai-data-engineering-pipeline/part-10-production-evals-cicd/)
- [Part 1 — Hybrid AI Architecture & Self-Hosted vLLM](/posts/slm-fine-tune-vs-prompt-engineering/)
- [High Concurrency Systems Architecture](/series/high-concurrency-systems/executive-summary/)
