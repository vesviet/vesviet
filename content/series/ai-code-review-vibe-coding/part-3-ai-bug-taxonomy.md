---
title: "AI Code Bug Taxonomy: Silent Failures to Slopsquatting (2025)"
date: 2026-05-31T17:30:00+07:00
lastmod: 2026-05-31T17:30:00+07:00
draft: false
weight: 4
categories:
  - AI Engineering
  - Code Review
tags:
  - AI bugs
  - slopsquatting
  - AI code vulnerabilities
  - tautological tests
  - logic failure
  - security review
  - bug taxonomy
  - mutation testing
  - AI code review
  - supply chain attack
description: "The 5 AI code bug categories: logic failures, security gaps, N+1 queries, IaC misconfigs, tautological tests — plus the Slopsquatting supply chain attack."
aliases:
  - /series/ai-code-review-vibe-coding/part-3-ai-bug-taxonomy/
---

> **Series Orientation:** This article is Part 3 of the **AI Code Review & Vibe Coding** series, examining the unique failure modes of AI-generated code. For the broader business context, see the [Series Executive Summary](/series/ai-code-review-vibe-coding/executive-summary/).

When engineers first review AI-generated code, they often encounter a counterintuitive phenomenon: the code looks right. It passes compilation. The tests are green. The function signatures are clean. The variable names are descriptive. And somewhere inside, there is a logic error that will silently corrupt your data, or a missing authorization check that will expose every user record to the first person who thinks to try a simple query manipulation.

AI-generated code fails in ways that are systematically different from human-generated code. The failures are less random and more predictable — shaped by the statistical patterns of the training data, the limitations of the model's context window, and the fundamental mismatch between "code that looks correct" and "code that is correct under all conditions."

This part of the series provides the taxonomy engineers need to audit AI-generated code effectively. Understanding *what categories of failure to expect* changes how you review — and where you allocate your most careful attention.

---

## The Five Categories of AI-Generated Bug

### Category 1: Silent Logic Failures (The Most Dangerous)

Silent logic failures are bugs where the code executes without error, produces output, and yet produces *incorrect* output. According to security audit telemetry from exceeds.ai, silent logic failures constitute over **60% of all AI-generated code defects**. They are the most dangerous category because they evade all automated detection and can persist undetected in production for extended periods.

**Off-by-one errors and boundary conditions**

AI models generate loop logic by statistical association with training patterns, not by careful reasoning about boundary conditions. Off-by-one errors — `<` versus `<=`, `0` versus `1` as loop starting points, inclusive versus exclusive range endpoints — appear consistently in AI-generated code at higher rates than in carefully reviewed human-generated code.

The review pattern: any loop bound, any range calculation, and any index operation in AI-generated code should be tested explicitly against its boundary conditions. Do not rely on the code "looking right."

**Business rule misapplication**

AI generates code that implements *a* business rule — often the most common variant of what was described in the prompt. It does not verify that the rule it implemented is the *correct* one for all edge cases, or that it handles the interactions between multiple rules correctly.

Example: A discount calculation that correctly applies a percentage discount, but silently fails to enforce the rule that loyalty discounts and promotional discounts cannot stack — because the prompt described each discount in isolation, and the AI had no context for the interaction constraint.

**Context blindness**

Context blindness is the category of errors arising from the AI's lack of knowledge of the broader codebase. The AI sees the task; it does not see the system.

Common manifestations:
- Reimplementing utility functions that already exist, often with subtly different behavior
- Creating new enum types that partially overlap with existing ones
- Writing validation logic that contradicts the validation already present in upstream layers
- Using different constants for the same conceptual value (timeout values, pagination limits, error codes)

Context engineering (Part 2) is the primary mitigation for context blindness. A well-constructed `AGENTS.md` with memory banks of key utilities can substantially reduce this category. But for any domain where the existing codebase is complex, the reviewer must verify: does this implementation conflict with anything that already exists?

---

### Category 2: Security Vulnerabilities (High Frequency, High Impact)

Research from security firms (such as Snyk and Veracode) consistently finds that AI-generated code exhibits **2.7× higher vulnerability density** than carefully reviewed human-written code. The exact figure varies by study, but the direction is consistent: AI code has more security vulnerabilities per unit of code, concentrated in predictable categories.

**Injection vulnerabilities**

SQL injection remains the most frequently generated security vulnerability in AI code. The pattern appears in two forms:

1. **String concatenation**: `query := "SELECT * FROM users WHERE id = " + userID` — the classic pattern AI reproduces because it appears extensively in tutorial-quality training data.
2. **Implicit string formatting**: `fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", username)` — less obviously wrong to the eye, equally exploitable.

The correct pattern — parameterized queries using `?` or named parameters — must be specified explicitly in context and verified in every code review. Automated SAST tools catch the first form reliably; the second requires human or semantic analysis.

Command injection and template injection follow similar patterns: AI generates functional code without sanitizing untrusted input before passing it to shell execution or template rendering.

**Authorization gaps**

Authorization gaps are perhaps the most consequential vulnerability category in AI-generated code because they are systematically produced by how AI constructs features in sequence.

When an AI implements a new API endpoint, it typically:
1. Creates the handler function
2. Implements the business logic
3. Returns a response

What it frequently omits: the middleware check that verifies the requesting user has permission to access the resource being returned. The Moltbook breach from Part 1 was an authorization gap — not at the route level, but at the database level (RLS disabled).

Authorization gaps require active verification against every new endpoint and every new data access path. They do not appear as static analysis warnings because the code is syntactically correct — it simply does not include the check.

**Cryptographic failures**

AI generates cryptographic code by pattern-matching against its training data, which includes extensive libraries of tutorial and example code using deprecated algorithms and insecure configurations:

| Pattern | What AI generates | What is correct |
|---|---|---|
| Password hashing | MD5, SHA1 | bcrypt, Argon2id |
| Random token generation | `math/rand` | `crypto/rand` |
| Symmetric encryption | DES, AES-CBC without authentication | AES-GCM |
| Secrets handling | Inline string literals | Environment variables |

The review principle: never accept AI-generated cryptographic code without explicit verification of the algorithm choice, key length, and configuration. Even when the AI uses the right library, it may use it incorrectly — generating static initialization vectors for AES, using weak parameters for bcrypt, or failing to validate MAC tags before decryption.

**Hardcoded credentials**

AI generates working code. In training data, "working code" frequently includes database credentials, API keys, and connection strings as inline strings. The AI reproduces this pattern because it is statistically the most common way it has seen credentials referenced in code.

Every AI-generated code review must include a credential scan — both automated (using tools like `gitleaks` or `trufflehog`) and manual (for patterns that automated tools miss, like numeric API keys that lack the characteristic formatting that triggers automated detection).

---

### Category 3: Performance and Reliability Issues

Performance bugs in AI-generated code rarely appear in isolated unit tests. They surface under production workloads, at scale, or in edge case conditions that test environments do not replicate.

**N+1 query generation**

This is the single most common performance anti-pattern in AI-generated data access code. AI generates the most readable, conceptually simple implementation of a data retrieval task — which, for any entity with relationships, is almost always a loop that queries child records for each parent.

```go
// AI-generated: readable but catastrophic under load
for _, order := range orders {
    order.Items, _ = repo.GetItemsByOrderID(ctx, order.ID)
}
```

At 10 orders in a test environment, this executes 11 queries and returns in milliseconds. At 10,000 orders in production, it executes 10,001 queries and may time out or trigger database connection exhaustion.

The correct implementation uses `Preload` (GORM) or an explicit JOIN with a single query. Identifying N+1 patterns requires understanding the data model and the relationship between the entities being accessed — not just reading the code.

**Unbounded resource consumption**

AI-generated code for operations that process large datasets frequently lacks pagination, streaming, or batching:

```go
// AI-generated: works in tests, OOM in production
func ExportAllOrders() ([]Order, error) {
    return db.Find(&orders).Error  // fetches everything into memory
}
```

Any operation that retrieves potentially large result sets must be reviewed for pagination and streaming behavior. If the test dataset is small, this bug will never appear in automated testing.

**Missing resilience patterns**

AI generates calls to external services as direct function calls. It does not automatically add the resilience patterns that production systems require:

- Timeouts: requests without timeouts will block indefinitely when upstream services hang
- Retry logic: transient failures require exponential backoff with jitter
- Circuit breakers: cascading failure prevention when a dependency is degraded
- Fallback behavior: what the system does when a non-critical external call fails

These patterns must be specified in context engineering (rule files that mandate them) and verified in code review (explicit checklist items for every external call).

---

### Category 4: Infrastructure and Configuration Errors

This category is specific to AI-generated Infrastructure as Code (IaC), cloud configuration, and deployment manifests.

**Hallucinated APIs and resource attributes**

AI generates Terraform, Kubernetes manifests, and cloud configuration from its training data, which has a knowledge cutoff and includes examples from multiple provider versions. The result: AI regularly generates configuration using resource attributes that do not exist in the current provider version, or using patterns that were valid in a previous API version.

```hcl
# AI-generated: attribute 'enable_dns_support' has been renamed
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true  # This attribute is correct
  enable_dns_hostnames = true
  enable_classiclink = false  # This attribute was deprecated
}
```

IaC reviews must verify that every resource attribute is valid in the current provider version. Running `terraform validate` catches some of these; others only surface on `terraform plan`.

**Overprivileged IAM roles**

AI generates IAM policies and Kubernetes RBAC configurations that work — meaning the system functions as expected — but grant significantly more permission than necessary. The principle of least privilege requires explicit scoping; AI defaults to broad permissions because they are more likely to produce working code on the first generation.

```hcl
# AI-generated: wildcard permissions for development convenience
resource "aws_iam_role_policy" "app_policy" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*"]        # Should be scoped to specific actions
      Resource = ["*"]           # Should be scoped to specific buckets
    }]
  })
}
```

Every AI-generated IAM policy and RBAC configuration requires explicit review against the principle of least privilege.

**Security misconfiguration by default**

The Moltbook breach is the canonical example: database-level Row Level Security disabled by default, AI leaving it that way. The same pattern appears across many configuration contexts:

- Public S3 buckets (the default before AWS introduced account-level blocking)
- Database security groups with `0.0.0.0/0` CIDR blocks (the example in most tutorials)
- TLS termination without certificate validation
- Debug endpoints enabled in production configurations

Any AI-generated infrastructure configuration must be reviewed against a security baseline, not just against "does it work?"

---

### Category 5: Testing Anti-Patterns (The Illusion of Coverage)

This category is distinct from the others because the bugs are in the tests themselves — and they are dangerous precisely because they allow all the bugs in categories 1–4 to persist undetected.

**Tautological (implementation-mirroring) tests**

When AI generates code and is asked to write tests for it, it routinely generates tests that verify the implementation's behavior rather than the specification's requirements. If the implementation is wrong, the test is wrong in exactly the same way.

```go
// Implementation:
func CalculateDiscount(price float64, loyaltyTier string) float64 {
    if loyaltyTier == "gold" {
        return price * 0.15  // Bug: should be 0.20 for gold tier
    }
    return price * 0.10
}

// AI-generated test (tautological):
func TestCalculateDiscount(t *testing.T) {
    result := CalculateDiscount(100, "gold")
    assert.Equal(t, 15.0, result)  // Tests the bug, not the requirement
}
```

The test passes. The coverage report shows 100%. The discount is wrong.

The correct approach: tests should be written from requirements, not from code. Test inputs and expected outputs should come from the specification or acceptance criteria — explicitly stated in the test file, not inferred from the implementation.

**Assertion Roulette**

AI-generated test suites frequently produce tests with multiple assertions where a test failure provides insufficient information to diagnose which assertion failed:

```go
func TestOrderProcessing(t *testing.T) {
    order := processOrder(testCart)
    assert.Equal(t, "confirmed", order.Status)
    assert.Equal(t, 99.99, order.Total)
    assert.Equal(t, 3, len(order.Items))
    assert.NotNil(t, order.ConfirmationID)
    assert.True(t, order.PaymentVerified)
}
```

When this test fails in CI, the failure message tells you "order processing test failed" — not which of the five assertions failed or why. Meaningful test failures require scoped assertions with descriptive failure messages.

**Happy-path bias**

AI generates tests for the paths most commonly present in training data: the successful case, the expected input. It systematically under-tests:

- Null/nil inputs
- Empty collections
- Boundary values (zero, negative, maximum valid, one past maximum)
- Error conditions and rejection paths
- Concurrent access (race conditions)

A test suite with 90% coverage that covers only happy paths may be nearly useless for detecting production failures, which disproportionately occur at boundaries and under error conditions. Indeed, mutation testing research shows that AI-generated tests with 90%+ line coverage still fail to catch over **60% of injected defects** (as documented in studies compiled by exceeds.ai).

**Mutation testing as the remedy**

The solution to the coverage illusion is **mutation testing** — injecting controlled faults into the source code to verify that the test suite catches them. Tools like Stryker (JavaScript/TypeScript), PITest (Java), and Gremlins (Go) automate this process.

The workflow:
1. AI generates code and tests
2. Mutation testing runs against the generated suite
3. "Surviving mutants" — faults the test suite did not catch — are reviewed by engineers
4. Engineers write targeted tests to kill the surviving mutants

A mutation score (the percentage of injected faults caught by the test suite) provides a far more accurate signal of test quality than line coverage. High-performing teams target mutation scores of 70–80% for business-critical logic.

---

## What Is Slopsquatting? The Supply Chain Attack That Targets AI Hallucinations

**Slopsquatting** is a supply chain attack where adversaries register malicious packages under names that AI coding tools commonly hallucinate — names that sound plausible but do not exist on real package registries like PyPI or npm. When a developer installs an AI-suggested package without verifying it exists, they may unknowingly install attacker-controlled code that executes during installation.

No taxonomy of AI-generated bugs would be complete without addressing this vulnerability class, unique to AI coding:

The term — coined by security researchers in 2024 — describes an attack pattern that exploits a specific AI behavior: hallucinating plausible-sounding package names that do not exist.

**How it works:**

AI models, asked to implement functionality, sometimes reference packages that seem plausible but are not real libraries. These hallucinated package names are often syntactically coherent, follow the naming conventions of the relevant ecosystem, and sound like exactly the kind of utility library that should exist.

```python
# AI-generated code referencing a plausible but fictitious package
from data_utils.preprocessing import normalize_schema
# 'data_utils.preprocessing' does not exist on PyPI
```

**The attack mechanism:**

1. Researchers documented that AI models hallucinate specific package names with measurable frequency
2. Attackers monitor AI coding tools and identify which fictitious packages are commonly hallucinated
3. Attackers register those package names on PyPI, npm, or other registries and publish malicious code
4. Developers who run AI-generated `pip install` or `npm install` commands unknowingly install attacker-controlled packages
5. The malicious package executes during installation — credential theft, backdoor installation, cryptocurrency mining

**The scale of the threat:**

Research shows that AI models hallucinate package names in a significant percentage of generated code involving third-party dependencies. Once a fictitious package name is confirmed to appear consistently in AI output, a malicious package registered under that name has a stable, recurring supply of victims.

**Mitigation:**

- Treat every AI-generated `import` statement and `require`/`use` directive as a candidate for verification
- Verify package existence on official registries before installation
- Check package publication date and download history — newly registered packages with no history are high risk
- Pin dependencies to specific versions and commit hash-verified lockfiles
- Run automated SCA (Software Composition Analysis) on every AI-generated `requirements.txt`, `package.json`, or `go.mod`
- For high-security environments, maintain an internal package mirror and only allow installation from it

Slopsquatting is not a theoretical attack. It is active in 2026. Supply chain incidents attributable to hallucinated package names are documented, and the attacker toolchain for monitoring AI output at scale is well-established.

---

## The Review Framework: What to Actually Do

Given this taxonomy, the practical review framework for AI-generated code is a tiered approach:

| Tier | Trigger | Key Focus | Owner / Mechanisms |
|---|---|---|---|
| **Tier 1: Automated** | Every PR (no exceptions) | • SAST scan for injection patterns<br>• Secret scanning<br>• SCA scan for hallucinated packages<br>• Mutation testing check | CI/CD Runner (Semgrep, GitLeaks, Snyk, Gremlins) |
| **Tier 2: Systematic Manual** | Every PR | • Authorization boundaries & data access<br>• Cryptographic patterns<br>• N+1 query patterns<br>• Resilience patterns (timeouts/retries)<br>• Boundary condition & error paths | Human Reviewer (Developer / Tech Lead) |
| **Tier 3: Deep Architecture** | Significant changes, high-risk domains | • Context blindness (code duplication)<br>• IaC security baseline<br>• Business rule correctness vs spec<br>• Load & concurrency behavior analysis | Principal Architect / Security Lead |

The allocation of human review effort follows the risk curve: most PRs need solid Tier 1 and Tier 2 coverage. The PRs that touch authentication, payments, core data model, and security-critical configuration need all three tiers.

---

Part 4 covers the infrastructure for running this review at scale — the multi-agent pipeline, zero-trust code posture, and the specific workflow designs that make rigorous review sustainable under the velocity pressure that AI coding tools create.

---

*Next: [Part 4 — Building the Review Pipeline: Zero-Trust Mindset, Multi-Agent, and Mutation Testing](/series/ai-code-review-vibe-coding/part-4-review-pipeline-multi-agent/)*
