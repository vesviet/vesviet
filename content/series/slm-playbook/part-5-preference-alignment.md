---
title: "Preference Alignment: DPO, KTO, & GRPO Algorithms | SLM Playbook"
date: 2026-05-25T08:00:00+07:00
lastmod: 2026-05-25T08:00:00+07:00
draft: false
description: "Understand reinforcement learning for aligning language models. Compare DPO, KTO, and dissect DeepSeek's GRPO to save 50% GPU VRAM by removing the Critic Model."
ShowToc: true
TocOpen: true
weight: 6
categories: ["Series", "SLM Playbook"]
tags: ["AI Engineering", "Preference Alignment", "DPO", "GRPO", "Reinforcement Learning"]
---
[← Series hub](/series/slm-playbook/)
[← Previous](/series/slm-playbook/part-4-knowledge-distillation-r1/) | [Next →](/series/slm-playbook/part-6-vllm-deployment-evals/)

Supervised Fine-Tuning (SFT) is the stepping stone that introduces domain knowledge and tone to a model, but it does not instruct the model on handling complex preference tradeoffs: identifying safe vs. toxic generation boundaries, formatting alignment, or self-correcting logic errors during reasoning cycles.

To ensure small models align with human intent, safety guidelines, and logical correctness, we execute a **Preference Alignment** phase.

This article details the mechanics of reinforcement learning for LLM alignment. We compare the mathematical objectives of **DPO** and **KTO**, and dissect **GRPO (Group Relative Policy Optimization)**—the breakthrough algorithm powering DeepSeek-R1 that frees up over 50% of training memory.

---

## 1. DPO vs. KTO: Reward-Model-Free Alignment

In traditional Reinforcement Learning from Human Feedback (RLHF), engineers must train a separate **Reward Model** to score completions from the main model (Policy). Managing multiple active models during training multiplies hardware overhead and makes RL optimization notoriously unstable.

```
┌──────────────────────────────────────────────────────────────┐
│             Comparing RLHF vs. DPO vs. KTO Alignment         │
├──────────────────────────────┬───────────────────────────────┤
│ RLHF (PPO)                   │ Requires 4 models concurrently:│
│                              │ Policy, Reference, Critic,    │
│                              │ and Reward. Highly memory    │
│                              │ intensive on GPUs.            │
├──────────────────────────────┼───────────────────────────────┤
│ DPO (De Facto Standard)      │ Bypasses the Reward Model.    │
│                              │ Computes loss directly on     │
│                              │ paired Chosen/Rejected inputs.│
├──────────────────────────────┼───────────────────────────────┤
│ KTO (Unpaired Optimizer)     │ Learns from binary (Like/     │
│                              │ Dislike) signals based on     │
│                              │ economic Prospect Theory.     │
└──────────────────────────────┴───────────────────────────────┘
```

### 1.1. DPO: Direct Preference Optimization
DPO mathematically proves that we can optimize policy parameters $\pi_\theta$ directly on preference pairs, avoiding intermediate reward modeling completely.
*   *DPO Loss Function:*
$$L_{\text{DPO}}(\theta; \pi_{\text{ref}}) = - \mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w | x)}{\pi_{\text{ref}}(y_w | x)} - \beta \log \frac{\pi_\theta(y_l | x)}{\pi_{\text{ref}}(y_l | x)} \right) \right]$$

Where:
*   $\pi_{\text{ref}}$ is the frozen pre-trained reference model protecting the policy from distribution collapse (KL divergence constraint).
*   $y_w$ (chosen) is the preferred completion, while $y_l$ (rejected) is the poor completion.
*   $\sigma$ is the Sigmoid activation function.
*   $\beta$ is a hyperparameter scaling the KL penalty strength (typically $\beta \in [0.1, 0.5]$).

### 1.2. KTO: Kahneman-Tversky Optimization
While DPO requires paired Chosen/Rejected responses for every prompt, KTO bypasses this dependency. Rooted in behavioral economics (Daniel Kahneman's *Prospect Theory*), KTO optimizes directly on unpaired binary flags (Like/Dislike labels). This dramatically simplifies production data logging pipelines since positive and negative logs can be ingested independently.

---

## 2. GRPO: The Key to Distilling Reasoning Capabilities

For logic-bound reasoning workloads like math and code generation, we can deploy automated, rule-based verification scripts (Verifiers) instead of relying on human graders (e.g., executing code in sandboxes to check unit tests or checking final outputs against math answers).

However, traditional RL algorithms (like PPO) still require maintaining an active **Critic Model** matching the parameter size of the Policy to evaluate reward baselines.

**GRPO (Group Relative Policy Optimization)** resolves this by removing the Critic Model from the RL training loop.

```
    GRPO (Group Relative Policy Optimization) Pipeline:

                  ┌────────────────┐
                  │   Prompt (x)   │
                  └───────┬────────┘
                          │
         [Sample G completions concurrently]
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Out 1       Out 2       Out G (e.g., G = 16)
              │           │           │
              └───────────┼───────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │   Verifiers   │ (Rule-based scoring, e.g., Regex / Sandboxes)
                  └───────┬───────┘
                          │
                [Evaluate Rewards R_i]
                          │
                          ▼
         ┌─────────────────────────────────┐
         │ Normalize: (R_i - Mean) / Std   │ (Use group mean as the baseline)
         └────────────────┬────────────────┘
                          │
                          ▼
         ┌─────────────────────────────────┐
         │     Update Policy Weights (θ)   │
         └─────────────────────────────────┘
```

### 2.1. How GRPO Operates
For a given input prompt $x$:
1.  **Group Sampling:** The policy model $\pi_\theta$ generates a group of $G$ alternative completions $\{y_1, y_2, \dots, y_G\}$ (typically $G \in [16, 64]$).
2.  **Rewards Evaluation:** Automated rule-based verifiers score each completion, returning raw reward values $\{r_1, r_2, \dots, r_G\}$.
3.  **Relative Normalization:** The advantage of each completion is computed by comparing its reward relative to the group mean:
$$\tilde{r}_i = \frac{r_i - \text{mean}(R)}{\text{std}(R)}$$
    Consequently, the collective performance of the group acts as a dynamic **Baseline**, rendering a separate Critic Model obsolete.
4.  **Policy Gradient Update:** Updates policy parameters $\pi_\theta$ by maximizing the relative advantages of high-scoring completions while enforcing a KL divergence penalty to maintain stability.

### 2.2. VRAM Reductions
Removing the Critic Model and its optimizer overhead reduces GPU VRAM consumption by **50%**. This enables startups and enterprises to train RL pipelines on 8B or 14B models on mid-tier GPU servers, bypassing the need for ultra-premium H100 clusters.

---

## 3. Python Simulation: Modeling GRPO Loss

Here is a Python script illustrating the advantage normalization, probability ratio calculations, and policy gradient loss computation defined in GRPO:

```python
import torch
import torch.nn.functional as F

def compute_grpo_loss(policy_logits, ref_logits, rewards, kl_coeff=0.01):
    """
    Simulates GRPO loss computation for a group of completions.
    
    Args:
        policy_logits: Tensor (G, sequence_len, vocab_size) - Logits from the active policy model
        ref_logits: Tensor (G, sequence_len, vocab_size) - Logits from the frozen reference model
        rewards: List[float] - Raw rewards returned by the Verifier for each completion
        kl_coeff: KL divergence scaling penalty
    """
    G = len(rewards)
    
    # 1. Normalize group rewards to compute relative advantages
    rewards_tensor = torch.tensor(rewards, dtype=torch.float32)
    mean_r = rewards_tensor.mean()
    std_r = rewards_tensor.std() + 1e-8
    normalized_advantages = (rewards_tensor - mean_r) / std_r
    
    # 2. Extract Log Probabilities of chosen tokens
    selected_tokens = torch.argmax(policy_logits, dim=-1)
    
    policy_log_probs = F.log_softmax(policy_logits, dim=-1)
    ref_log_probs = F.log_softmax(ref_logits, dim=-1)
    
    # Gather selected token probabilities
    policy_action_log_probs = policy_log_probs.gather(2, selected_tokens.unsqueeze(-1)).squeeze(-1).sum(dim=-1)
    ref_action_log_probs = ref_log_probs.gather(2, selected_tokens.unsqueeze(-1)).squeeze(-1).sum(dim=-1)
    
    # 3. Calculate Policy Ratio (Importance Sampling Ratio)
    ratio = torch.exp(policy_action_log_probs - ref_action_log_probs)
    
    # 4. Compute Clipped Surrogate Loss
    surr1 = ratio * normalized_advantages
    surr2 = torch.clamp(ratio, 0.8, 1.2) * normalized_advantages
    policy_loss = -torch.min(surr1, surr2).mean()
    
    # 5. Add Direct KL Divergence Penalty
    kl_div = (policy_action_log_probs - ref_action_log_probs).mean()
    
    total_loss = policy_loss + kl_coeff * kl_div
    
    return total_loss, policy_loss.item(), kl_div.item()

if __name__ == "__main__":
    # Simulate a group size of G = 4, sequence length of 10, and vocabulary size of 1000
    G = 4
    seq_len = 10
    vocab_size = 1000
    
    torch.manual_seed(42)
    policy_logits = torch.randn(G, seq_len, vocab_size, requires_grad=True)
    ref_logits = torch.randn(G, seq_len, vocab_size)
    
    # Mock rewards: Completions 1 & 4 solved the task, while 2 & 3 failed
    raw_rewards = [1.0, 0.0, 0.0, 1.0]
    
    loss, p_loss, kl = compute_grpo_loss(policy_logits, ref_logits, raw_rewards)
    
    print(f"GRPO Simulation Results:")
    print(f"Total Loss: {loss.item():.4f}")
    print(f"Policy Loss Component: {p_loss:.4f}")
    print(f"KL Penalty Component: {kl:.4f}")
```

---

## Next Chapter

Now that our data is curated, adapters are trained, and alignment is optimized, we possess a production-ready model. The final step is serving it to users at scale.

In [**Part 6: Enterprise Serving & Quantization**](/series/slm-playbook/part-6-vllm-deployment-evals/), we study quantization formats (**AWQ**, **GPTQ**, and **GGUF**), configure high-concurrency **Dynamic LoRA** architectures, and benchmark throughput on vLLM.

{{< author-cta />}}
