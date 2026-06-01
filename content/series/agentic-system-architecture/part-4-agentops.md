---
title: "Part 4 — AgentOps & Production Observability"
date: 2026-05-22T08:00:00+07:00
lastmod: 2026-05-22T08:00:00+07:00
draft: false
description: "Why is Observability for AI Agents different? Building Tracing systems, monitoring costs, and safely testing in production with Signadot."
ShowToc: true
TocOpen: true
weight: 5
categories: ["Series", "Agent Architecture"]
tags: ["AI", "Multi-Agent", "AgentOps", "Observability", "Signadot"]
---

> **Prerequisite:** Before discussing Monitoring, you must thoroughly understand the operational architecture of AI in the Enterprise. Please review [Comprehensive AI-Native System Architecture](/series/ai-driven-playbook/part-8-ai-native-system-architecture/).

We've come a long way: Designing the Topology ([Part 1](/series/agentic-system-architecture/part-1-topology/)), building Memory ([Part 2](/series/agentic-system-architecture/part-2-memory/)), and erecting Guardrails ([Part 3](/series/agentic-system-architecture/part-3-tool-calling/)).

Now, your Agent is ready for Production. But this is when the real nightmare begins: How do you debug a system where **the output is different every single time** (Non-deterministic)?

## 4.1. Why is Observability for AI Agents different from normal microservices?

With a traditional REST API, you care about **RED metrics**: Rate (Requests/sec), Errors (5xx), and Duration (Latency).

But with an AI Agent, RED metrics are insufficient. A request might return an HTTP 200 OK, but if the content is a "hallucination," the request is still a failure. AgentOps requires you to monitor more:

- **Cost:** How many USD does the Agent burn per Session? (Token usage).
- **Tool Success Rate:** What is the percentage of Agent Tool calls failing due to incorrectly parsed JSON parameters?
- **Step/Turn Count:** How many steps does the Agent need to solve a problem? (If loops > 5, the Agent might be stuck).

## 4.2. Tracing LLM Calls: Latency, Token usage, Cost per-session

When an Agent calls an LLM, we need to record the entire Trace (Input Prompt, Output Tokens, and Latency). Below is Golang code using OpenTelemetry (OTel) to wrap an LLM Call.

```go
// Module: Agent Tracer (Golang)
// Uses OpenTelemetry to record Token Usage and Latency of the LLM.
package agentops

import (
	"context"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
)

// Cost calculation function (USD)
// Reference: https://openai.com/pricing
func calculateCost(promptTokens, completionTokens int, model string) float64 {
	pricing := map[string]struct{ prompt, completion float64 }{
		"gpt-4-turbo":   {0.01, 0.03}, // $/1K tokens
		"gpt-4":         {0.03, 0.06},
		"gpt-3.5-turbo": {0.001, 0.002},
	}
	p := pricing[model]
	return (float64(promptTokens) * p.prompt / 1000) + 
	       (float64(completionTokens) * p.completion / 1000)
}

// Simulated OpenAI API call (Mock function)
func mockOpenAICall(prompt string) (string, int, int, error) {
	// Returns: Response, PromptTokens, CompletionTokens, Error
	return "This is a mocked response from the Agent.", 150, 50, nil
}

func CallLLMWithTracing(ctx context.Context, prompt string) (string, error) {
	tracer := otel.Tracer("agent-orchestrator")
	ctx, span := tracer.Start(ctx, "LLM_Generate_Response")
	defer span.End()

	span.SetAttributes(attribute.String("llm.prompt", prompt))
	span.SetAttributes(attribute.String("llm.model", "gpt-4-turbo"))

	// Simulate calling OpenAI API
	response, promptTokens, completionTokens, err := mockOpenAICall(prompt)
	if err != nil {
		span.RecordError(err)
		return "", err
	}

	// Calculate cost (USD) based on Tokens
	totalCost := calculateCost(promptTokens, completionTokens, "gpt-4-turbo")
	
	// Attach metrics to Span
	span.SetAttributes(
		attribute.Int("llm.usage.prompt_tokens", promptTokens),
		attribute.Int("llm.usage.completion_tokens", completionTokens),
		attribute.Float64("llm.usage.cost_usd", totalCost),
	)

	return response, nil
}
```

By doing this, on dashboards like Datadog or Jaeger, you can easily query: *"How much money did Agent B burn today?"*

## 4.3. Testing Agents in a production-like environment with Signadot

How do you test an Agent that has permission to delete from a Database (Tool Calling) without corrupting actual Production data? Testing in Staging often means the data is too old, and the LLM won't deduce the correct real-world context.

The solution is the **Signadot Sandbox**.

**How it works:**

1. Create a Sandbox: `signadot create sandbox --name test-agent-v2`
2. Route traffic with a header: `x-signadot-sandbox: test-agent-v2`
3. The Database is cloned at a logical level (PostgreSQL logical clone).
4. Verify Guardrails: Let the Agent run on Auto-pilot and check if unauthorized `delete_*` calls are intercepted.

**Config example:**
```yaml
# signadot.yaml
sandboxes:
  - name: agent-test-v2
    spec:
      clusters:
        - name: production
      datastores:
        - name: postgres-main
          logical_clone: true
```

*(Note: This technique is a profound continuation from our [Tech Radar May 13, 2026](https://tanhdev.com/radar/radar-2026-05-13/)).*

## 4.4. Alerting on Agent drift or infinite loops

### Infinite Loop Detection
Besides Agent Drift, you must monitor the **Turn Count** (the number of steps an Agent takes):

- Alert Setup: If `turn_count > max_turns` (usually 5-10) in 1 session.
- Mechanism: When the Agent calls Tools > N times without a Final Output → auto-escalate to Human.
- Golang code snippet:
```go
// Pseudo-code for Alerting system
if len(trace.Steps) > 10 {
    span.SetAttributes(attribute.Bool("agent.loop_detected", true))
    alert.PagerDuty("Agent stuck in loop", trace.SessionID)
}
```

### Model Drift Detection
LLM Models are constantly updated stealthily by Providers (OpenAI, Anthropic). Even if you don't change your code, the Agent's behavior can suddenly shift. This phenomenon is called **Model Drift** (or Agent Drift).

> 🔥 **[Production Failure]: Agent Drift silently destroying revenue**
> **Symptom:** The closing rate of a Sales Agent dropped from 15% to 2% within a week, with absolutely no error alerts (Error = 0).
> **Root Cause:** The Provider (OpenAI) released a minor update for the model (silently updated). This update caused the Agent to automatically append "Would you like to think more about it?" at the end of every sales pitch, inadvertently causing customers to hesitate.
> 📊 **Impact:** A plunge of $300,000 in revenue in 48 hours before the team noticed the issue, due to a lack of tracking metrics.
> 📈 **Resolution:** Build an automated Evals (Evaluation) system. Configure Alerting: Trigger a red alert if `Avg_Turns_Per_Sale` spikes or `Conversion_Rate` drops > 10% within 2 hours. *(Source: Synthesized from AgentOps reports on Hacker News).*

---

## 🎯 Series Wrap-up

Congratulations! Across the 4 parts of the **Agentic System Architecture** series, you've grasped the entire lifecycle of a real-world Multi-Agent system:
- Knowing how to design Topologies to distribute power (Part 1).
- Knowing how to optimize Vector Memory and prevent Context overflows (Part 2).
- Knowing how to block Prompt Injections using robust Sandbox infrastructure (Part 3).
- And finally, the ability to illuminate every dark corner of the system with Observability (Part 4).

You now possess a solid foundational knowledge to design, protect, and operate a Multi-Agent system at an Enterprise scale. Start building your first Orchestrator today!
