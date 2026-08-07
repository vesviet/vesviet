---
title: "Part 5: Declarative Prompting and Prompt Optimization with DSPy"
date: "2026-07-26T10:30:00+07:00"
lastmod: "2026-07-26T10:30:00+07:00"
draft: false
weight: 50
description: "Transition from manual string tweaking to declarative prompt compilation using DSPy 2.5+, abstract signatures, MIPROv2 teleprompters, and automated evaluation metrics."
categories: ["Engineering", "AI"]
tags: ["prompt", "standard", "context-engineering", "agent"]
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/prompt-engineering-benchmark-cover.png"
  alt: "Part 5 Declarative Prompting and DSPy Compilation Architecture"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/prompt-standard/part-5-declarative-prompting-dspy/"
mermaid: true
---

> **Prerequisite:** Familiarity with the concepts introduced in [Part 4 — Mcp And Hybrid Rag](/series/prompt-standard/part-4-mcp-and-hybrid-rag/). Review it first if the terminology in this part is unfamiliar.

**Answer-first:** Declarative prompting with DSPy replaces brittle manual prompt string tweaking with programmatic compiler pipelines. By defining input-output signatures and quantitative metrics, optimizers such as MIPROv2 search instruction variations and few-shot demonstrations to automatically generate high-performing, model-agnostic prompt artifacts.

---

## 1. Paradigm Shift: String Tweaking vs Declarative Compilation

Manual prompt engineering—spending hours editing adjectives, formatting bullet points, and pasting static few-shot examples—is an anti-pattern in modern software engineering. When underlying model versions update or providers change, hand-crafted prompts frequently break, requiring complete manual re-testing.

Declarative framework architectures like DSPy (Declarative Self-improving Python) separate prompt intent from implementation mechanics. Developers write structured input-output specifications, while compilation algorithms optimize the underlying instruction strings and demonstration selections automatically.

The structural diagram below contrasts traditional trial-and-error prompt editing with the automated DSPy compilation lifecycle.

```
+---------------------------------------+
|  Declarative DSPy Signature           | (Inputs -> Outputs Contract)
+---------------------------------------+
                   |
                   v
+---------------------------------------+
|  DSPy Optimizer / Teleprompter        | (MIPROv2 / BootstrapFewShot)
+---------------------------------------+
                   | (Evaluates against Golden Dataset & Quantitative Metric)
                   v
+---------------------------------------+
|  Compiled Production Prompt Pipeline  | (Saved JSON Config Artifact)
+---------------------------------------+
```

---

## 2. Core Building Blocks in DSPy 2.5+

DSPy abstracts prompt workflows using three fundamental primitives:

### 2.1 Signatures
A Signature defines *what* a language model step must do without specifying *how* to prompt it. Signatures use Python class syntax or shorthand strings to declare inputs and outputs:

```python
class CodeVulnerabilityReview(dspy.Signature):
    """Analyze code snippet for security bugs and return remediation patch."""
    code_snippet = dspy.InputField(desc="Source code string to evaluate")
    language = dspy.InputField(desc="Target programming language")
    
    vulnerability_found = dspy.OutputField(desc="Boolean flag indicating vulnerability presence")
    cwe_identifier = dspy.OutputField(desc="CWE ID string or 'None'")
    remediation_patch = dspy.OutputField(desc="Corrected code block")
```

### 2.2 Modules
Modules implement execution patterns over Signatures. Built-in modules include:
- `dspy.Predict`: Direct zero-shot model invocation.
- `dspy.ChainOfThought`: Automatically appends step-by-step reasoning steps (`Reasoning: ...`).
- `dspy.ReAct`: Interleaves thought generation with tool calls.

### 2.3 Teleprompters (Optimizers)
Teleprompters evaluate candidate prompt structures against training datasets using objective metric functions. The flagship optimizer in DSPy 2.5+, **MIPROv2** (Multi-prompt Instruction Proposal Optimizer v2), uses Bayesian optimization to search both instruction phrasing and exemplar combinations simultaneously.

---

## 3. Production DSPy Compilation Pipeline Implementation

To build an automated prompt compiler, developers define training samples, module pipelines, and objective metrics.

The Python implementation below constructs a complete vulnerability analysis pipeline compiled using DSPy 2.5+ and the MIPROv2 teleprompter optimizer.

```python
import dspy

# 1. Define Declarative Signature Contract
class VulnerabilityAnalysisSignature(dspy.Signature):
    """Analyze source code snippet for security vulnerabilities and output structured fix."""
    code_snippet = dspy.InputField(desc="Raw source code snippet")
    language = dspy.InputField(desc="Programming language: Go, Python, or TypeScript")
    
    vulnerability_detected = dspy.OutputField(desc="Boolean True or False")
    cwe_id = dspy.OutputField(desc="CWE Identifier such as CWE-89 or 'None'")
    remediation_patch = dspy.OutputField(desc="Minimal corrected code patch")

# 2. Define Execution Module Pipeline
class VulnerabilityAnalyzerModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(VulnerabilityAnalysisSignature)

    def forward(self, code_snippet: str, language: str):
        return self.analyze(code_snippet=code_snippet, language=language)

# 3. Define Quantitative Metric Function
def accuracy_and_format_metric(example, pred, trace=None):
    """Evaluate prediction correctness and structural format compliance."""
    detection_matches = (str(example.vulnerability_detected).lower() == str(pred.vulnerability_detected).lower())
    cwe_valid = pred.cwe_id is not None and len(pred.cwe_id.strip()) > 0
    patch_present = pred.remediation_patch is not None and len(pred.remediation_patch.strip()) > 0
    
    return detection_matches and cwe_valid and patch_present

# 4. Compilation Execution Pipeline
def run_mipro_compilation(train_dataset):
    # Configure LM backend
    lm = dspy.LM("openai/gpt-4o-mini")
    dspy.configure(lm=lm)

    # Initialize MIPROv2 Teleprompter
    teleprompter = dspy.MIPROv2(
        metric=accuracy_and_format_metric,
        auto="light",
        num_candidates=5
    )
    
    uncompiled_module = VulnerabilityAnalyzerModule()
    
    # Run optimization search across prompt candidate space
    compiled_program = teleprompter.compile(
        uncompiled_module,
        trainset=train_dataset,
        max_bootstrapped_demos=3,
        max_labeled_demos=3
    )
    
    # Save optimized prompt configuration artifact
    compiled_program.save("compiled_vulnerability_analyzer.json")
    return compiled_program
```

---

## 4. Managing Compiled Prompt Artifacts in CI/CD

Compiled DSPy programs export deterministic JSON artifacts containing optimal system instructions, field prefix labels, and curated few-shot examples.

The JSON configuration snippet below shows an exported DSPy compiled artifact ready for production deployment.

```json
{
  "analyze.predict": {
    "lm": null,
    "signature_description": "Analyze source code snippet for security vulnerabilities and output structured fix.",
    "instructions": "Given raw source code, perform deep AST analysis to check for CWE vulnerabilities. Output explicit boolean vulnerability_detected, exact cwe_id, and minimal remediation_patch.",
    "demos": [
      {
        "augmented": true,
        "code_snippet": "query := fmt.Sprintf(\"SELECT * FROM users WHERE id = '%s'\", input)",
        "language": "Go",
        "rationale": "The string concatenation in SQL query construction exposes direct SQL injection vulnerability (CWE-89).",
        "vulnerability_detected": "True",
        "cwe_id": "CWE-89",
        "remediation_patch": "db.Query(\"SELECT * FROM users WHERE id = $1\", input)"
      }
    ]
  }
}
```

By decoupling application source code from prompt artifacts, systems can re-compile prompts automatically whenever golden datasets expand or underlying models update, maintaining continuous quality without manual code changes.

---

## FAQ

{{< faq q="How does declarative prompting differ from traditional manual prompt engineering?" >}}
Declarative prompting replaces manual string manipulation with programmatic contracts called Signatures. Instead of manually editing text phrases, frameworks like DSPy compile signatures into optimal prompts and few-shot examples by running optimization algorithms against quantitative metrics.
{{< /faq >}}

{{< faq q="What role does the MIPROv2 teleprompter play in DSPy?" >}}
MIPROv2 (Multi-prompt Instruction Proposal Optimizer) is an advanced DSPy teleprompter that searches both system instruction variants and few-shot example combinations. It uses Bayesian optimization to discover prompt configurations that maximize performance against user-defined metric functions.
{{< /faq >}}

{{< faq q="Can compiled DSPy prompts be transferred across different LLM providers?" >}}
Yes, DSPy modules are model-agnostic. If a team transitions from OpenAI to Anthropic or open-weight models like Llama 3, they simply re-run the compilation script against the target model provider to generate optimized prompt artifacts tailored to that specific architecture.
{{< /faq >}}

{{< author-cta >}}

🔗 **Next Step:** Continue to [Part 6 — Promptops Evals And Security](/series/prompt-standard/part-6-promptops-evals-and-security/) for the following module in the series.
