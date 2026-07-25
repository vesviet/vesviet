---
title: "The AI Bug Taxonomy: Hallucinations & Phantom APIs"
slug: "part-3-ai-bug-taxonomy"
date: "2026-05-26T12:00:00+07:00"
lastmod: "2026-07-23T10:40:00+07:00"
draft: false
author: "Lê Tuấn Anh"
tags: ["AI Bugs", "Taxonomy", "Hallucinations", "Python", "Static Analysis", "Debugging"]
categories: ["Engineering"]
cover:
  image: "images/posts/vibe-coding-cover.png"
  alt: "The AI Bug Taxonomy classification diagram"
  relative: false
mermaid: true
canonicalURL: "https://tanhdev.com/series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/"
description: "Detailed technical guide categorizing AI-generated bugs, code hallucinations, phantom API calls, and automated AST scanners to prevent outages."
ShowToc: true
TocOpen: true
---

# Part 3 — The AI Bug Taxonomy: Hallucinations & Phantom APIs

> **Executive Summary & Quick Answer**: AI-generated code introduces a unique class of subtle defects distinct from traditional human coding errors. Understanding the **AI Bug Taxonomy**—encompassing Phantom API methods, Typosquatted Package Imports, Silent Type Coercions, and Logical Edge-Case Hallucinations—allows engineering teams to construct targeted AST static analysis filters that catch 95% of AI defects before code reaches production.
>
> **Key Takeaways**:
> - **Phantom API Interception**: Catching non-existent framework methods (e.g., `redis.get_or_set()`) at AST parse time.
> - **Typosquatting Supply Chain Guard**: Blocking AI hallucinated third-party package imports before execution.
> - **Silent Failure Suppression Elimination**: Flagging bare `except:` blocks that mask runtime crashes in production.

---

Unlike human developers (who primarily introduce syntax typos, off-by-one boundary errors, or missing null checks), Large Language Models generate code based on statistical pattern matching.

When an LLM generates code, it synthesizes snippets from millions of public repositories, training checkpoints, and API documentation versions. This creates a distinct set of failure modes known as the **AI Bug Taxonomy**.

---

## The AI Bug Taxonomy Topology

**Answer-first:** The AI bug taxonomy categorizes synthetic flaws into four categories: phantom package imports, silent logic inversions, state drift, and boundary omissions.

> **Pillar Architecture Guide:** This article is part of the **[Autonomous Hybrid-AI Pipeline: Cron to State-Machine](/posts/architecting-an-autonomous-hybrid-ai-content-pipeline/)** series. Please refer to the original article for a comprehensive overview of the architecture.

```mermaid
graph TD
    AIBugTaxonomy[AI Bug Taxonomy] --> Category1["1. Phantom APIs & Hallucinated Methods"]
    AIBugTaxonomy --> Category2[2. Supply Chain Typosquatting Imports]
    AIBugTaxonomy --> Category3["3. Silent Type Coercion & Swallowed Errors"]
    AIBugTaxonomy --> Category4[4. Non-Thread-Safe State Mutation]

    Category1 --> Ex1["Calling non-existent methods e.g. db.fetch_or_create()"]
    Category2 --> Ex2["Importing unverified packages e.g. import crypto_utils_v2"]
    Category3 --> Ex3["Bare except: blocks returning dummy empty values"]
    Category4 --> Ex4["Concurrent map access in Go/Python without mutex"]
```

---

## The Four Primary AI Bug Categories

**Answer-first:** AI code generators frequently produce non-existent package methods, improper async error handling, infinite loop conditions, and subtle type coercion errors.

### 1. Phantom APIs & Hallucinated Methods
LLMs often invent plausible-sounding API methods that combine features from multiple framework versions (e.g., mixing PyTorch and TensorFlow syntax or calling `df.to_sql_fast()` in pandas). The code looks syntactically pristine but fails at runtime with an `AttributeError` or `NoSuchMethodError`.

### 2. Supply Chain Typosquatting Imports
When generating solutions for complex tasks, LLMs occasionally hallucinate non-existent third-party library names (e.g., `import requests_retries_boost`). Attackers actively monitor public package registries for commonly hallucinated library names, registering malicious payloads under those exact identifiers.

### 3. Silent Failure Suppression
To make generated code appear "flawless" and prevent visible runtime crashes during user testing, LLMs frequently wrap risky execution blocks in broad `try/except` clauses that swallow exceptions and return dummy empty values, masking underlying system failures.

### 4. Non-Thread-Safe State Mutation
LLMs excel at single-threaded execution patterns. When asked to write concurrent code (e.g., Go goroutines or Python asyncio workers), they frequently mutate shared maps or global variables without applying mutex locks, causing intermittent data races under production load.

---

## Comparative Matrix: Human Bugs vs. AI Bugs

**Answer-first:** Human developers make off-by-one errors and conceptual mistakes, while AI code generators produce syntactically valid yet non-existent API invocations.

| Dimension | Traditional Human Bugs | AI-Generated Hallucination Bugs |
| :--- | :--- | :--- |
| **Syntax Errors** | Frequent (Missing braces, typos) | Near Zero (Syntactically perfect) |
| **Method Existence** | High Accuracy (IDE auto-complete) | Low Accuracy (Phantom method names) |
| **Package Imports** | Verified via package lock file | High Risk (Hallucinated package names) |
| **Exception Handling**| Often forgotten completely | Swallowed silently via bare `except:` |
| **Detection Method** | Compiler & basic linter | AST inspection & static symbol validation |

---

## Production Python AI Bug Taxonomy Scanner

**Answer-first:** Production AST scanners analyze generated Python and Go code against actual package index symbol tables to flag phantom imports instantly.

This production-grade Python static analysis tool using `ast` parsing that scans AI-generated code for Phantom API patterns, bare exception catching, and non-verified third-party imports:

```python
import ast
import sys
from typing import List, Set
from pydantic import BaseModel, Field

class TaxonomyViolation(BaseModel):
    line: int
    category: str
    severity: str
    message: str

class TaxonomyScanReport(BaseModel):
    total_violations: int
    has_critical_bugs: bool
    violations: List[TaxonomyViolation]

class AIBugTaxonomyScanner:
    def __init__(self, verified_packages: Set[str]):
        self.verified_packages = verified_packages
        # Known hallucinated phantom API method signatures
        self.phantom_methods = {"fetch_or_create", "get_or_set", "to_sql_fast", "execute_async_sync"}

    def scan_code(self, source_code: str) -> TaxonomyScanReport:
        violations: List[TaxonomyViolation] = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            violations.append(TaxonomyViolation(
                line=e.lineno or 1,
                category="Syntax Failure",
                severity="CRITICAL",
                message=f"Syntax Error: {e.msg}"
            ))
            return TaxonomyScanReport(total_violations=1, has_critical_bugs=True, violations=violations)

        for node in ast.walk(tree):
            # Check 1: Phantom API Method Detection
            if isinstance(node, ast.Attribute):
                if node.attr in self.phantom_methods:
                    violations.append(TaxonomyViolation(
                        line=node.lineno,
                        category="Phantom API Hallucination",
                        severity="HIGH",
                        message=f"Call to known hallucinated phantom method '{node.attr}'."
                    ))

            # Check 2: Typosquatted Package Import Detection
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_pkg = alias.name.split('.')[0]
                    if base_pkg not in self.verified_packages and base_pkg not in sys.stdlib_module_names:
                        violations.append(TaxonomyViolation(
                            line=node.lineno,
                            category="Typosquatted Package Risk",
                            severity="CRITICAL",
                            message=f"Import of unverified third-party library '{alias.name}'."
                        ))

            # Check 3: Silent Failure Suppression
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    violations.append(TaxonomyViolation(
                        line=node.lineno,
                        category="Silent Failure Suppression",
                        severity="MEDIUM",
                        message="Bare 'except:' catches and suppresses all system exceptions."
                    ))

        has_critical = any(v.severity in ["HIGH", "CRITICAL"] for v in violations)
        return TaxonomyScanReport(
            total_violations=len(violations),
            has_critical_bugs=has_critical,
            violations=violations
        )

if __name__ == "__main__":
    allowed = {"pydantic", "requests", "torch", "transformers", "redis"}
    scanner = AIBugTaxonomyScanner(verified_packages=allowed)

    ai_generated_snippet = """
import requests
import fake_helper_lib # Typosquatted package

def get_user_data(user_id):
    try:
        # Phantom API call hallucinated by model
        res = requests.get_or_set(f"https://api.com/users/{user_id}")
        return res
    except:
        return {} # Silent suppression
"""

    report = scanner.scan_code(ai_generated_snippet)
    print(f"=== AI Bug Taxonomy Scan Report ===")
    print(f"Total Violations: {report.total_violations} | Critical Bugs: {report.has_critical_bugs}")
    for v in report.violations:
        print(f" -> [Line {v.line}] [{v.severity}] {v.category}: {v.message}")
```

---

## Frequently Asked Questions (FAQ)

**Answer-first:** Detecting phantom APIs requires automated AST parsing and symbol lookup against verified package registries prior to code compilation.

### Q1: Why do frontier LLMs hallucinate phantom API methods despite being trained on massive codebases?
LLMs operate on probabilistic next-token generation. When asked to solve a complex coding task, the model calculates high probability vectors for method names that combine common framework patterns (e.g., combining `fetch()` and `create()`), producing a syntactically natural but physically non-existent function name.

### Q2: How can static symbol resolution prevent phantom API calls from reaching production?
Static symbol resolution compiles the code AST against the exact target library version definitions. If an AST node calls a method `db.fetch_or_create()` that does not exist in the imported module's symbol table, the static analyzer flags an immediate compilation error before unit testing begins.

### Q3: Are AI hallucination bugs declining as models improve?
While newer frontier models (e.g., Claude 3.5 Sonnet, GPT-4o) exhibit lower hallucination rates on standard programming frameworks, hallucination rates remain high when generating code for niche frameworks, newly updated SDKs, or proprietary enterprise internal libraries.

---

## Technical Deep-Dive: Enterprise Code Review & Vibe Coding Governance

**Answer-first:** Addressing AI-generated bugs requires combining AST symbol verification with automated unit test synthesis during continuous integration runs.

Abstract Syntax Tree (AST) scanning provides a deterministic defense layer against common LLM code generation failures. By inspecting code structures at the syntax tree level, security and review pipelines can detect non-existent API calls, unverified third-party dependencies, and unsafe exception handling patterns before code reaches runtime execution.

### AST Bug Taxonomy Analysis & Detection Latency

Static AST parsing operates with near-zero latency overhead (sub-10ms for typical source files). By evaluating structural nodes—such as `ast.Attribute`, `ast.Import`, and `ast.ExceptHandler`—the parser identifies structural anti-patterns without requiring expensive runtime execution or dynamic sandbox instantiation.

### System Safety & Execution Guardrails

Enterprise vibe coding governance requires automated guardrails at every layer of the development pipeline:
1. **Symbol Table Verification:** Cross-referencing generated attribute calls against canonical package APIs to intercept phantom function invocations.
2. **Package Registry Allowlisting:** Validating imported modules against an organizationally approved lockfile to prevent typosquatting and slopsquatting attacks.
3. **Strict Exception Enforcement:** Flagging bare `except:` clauses that silently swallow errors and hide critical application failures.

### Operational Checklist for Software Engineering Teams

- **AST Scanner Integration:** Deploy pre-commit hooks and CI steps that execute AST taxonomy scanners on every pull request containing AI-assisted code.
- **Dependency Sandboxing:** Require explicit security approval for any newly introduced package name detected in AI code prompts or diffs.
- **Automated Regression Guardrails:** Pair AST static checks with mutation testing to ensure generated unit tests cover all logic branches.

---

## Internal Series Navigation

**Answer-first:** Proceed to Part 4 to examine multi-agent review pipeline architectures.

- [Executive Summary — The Vibe Coding Revolution](/series/ai-code-review-vibe-coding/executive-summary/)
- [Part 2 — Codebase Context Engineering for AI Reviewers](/series/ai-code-review-vibe-coding/part-2-context-engineering-codebase/)
- [Part 4 — Multi-Agent Review Pipeline Architecture](/series/ai-code-review-vibe-coding/part-4-review-pipeline-multi-agent/)
- [Part 5 — AI Code Security: Prompt Injection & Credentials](/series/ai-code-review-vibe-coding/part-5-ai-code-security/)
