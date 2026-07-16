---

title: "Part 6: Observability & Audit Trail"
date: "2026-05-15T14:00:00+07:00"
lastmod: "2026-05-15T14:00:00+07:00"
draft: false
weight: 7
categories: ["Operations"]
tags: ["Observability", "OpenTelemetry", "SIEM", "Auditing"]
description: "Eliminating operational 'blind spots' in AI systems. A guide to setting up OpenTelemetry, Distributed Tracing, and SIEM integration for MCP Servers."
aliases: ["/series/mcp-engineering-in-production/part-6-observability/"]
cover: {'image': 'images/posts/generative-ui-mcp-cover.png', 'alt': 'MCP Engineering in Production series: Go SDK to enterprise Model Context Protocol deployment', 'relative': False}
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/mcp-engineering-in-production/part-6-observability/"
mermaid: true
ShowToc: true
TocOpen: true
---

**Answer-first:** Monitoring MCP server performance requires tracking active SSE streams, tool execution latency, connection drops, and LLM input-output cardialities. Exposing Prometheus metrics from gateways and backend services helps identify slow tool handlers and troubleshoot socket exhaustion under heavy load.

> **Prerequisite:** Before reading this part, please ensure you have read the previous article in this series: [Part 5: Production Security & OWASP MCP Top 10]({{< ref "part-5-security.md" >}}).

### What You'll Learn That AI Won't Tell You
- **Socket Exhaustion Signals:** Why monitoring active TCP connections in the CLOSE_WAIT state is critical for gateways.
- **Prometheus Collector Setups:** Scraping metrics from ephemeral container nodes using consul discovery.
- **Grafana Dashboard Layouts:** Combining active client streams with database transaction latency charts.

As mentioned in [Part 5](/series/mcp-engineering-in-production/part-5-security/), the **MCP08 (Lack of Audit & Telemetry)** vulnerability is one of the biggest risks in Agentic systems. In the [AI Driven Playbook](/series/ai-driven-playbook/), we agreed that: When AI automates tasks on behalf of humans, the requirements for Observability and Auditing become stricter than ever, especially under the pressure of regulations like the EU AI Act.

When a human clicks a button and the system crashes, we have an error stack trace. When an Agent hallucinates, calls the wrong MCP tool, and drops a database table, we need more than a stack trace—we need the entire "Chain of Thought" leading to that disaster.

This article guides you through setting up an enterprise-grade Observability system for an MCP Server.

## 1. The Three Pillars of Telemetry for MCP

We don't use `fmt.Println()` to debug MCP (this will break the protocol if running over `stdio` as discussed in [Part 2](/series/mcp-engineering-in-production/part-2-build/)). Instead, all telemetry data must be structured and exported via **OpenTelemetry (OTel)**. This mindset should be very familiar if you have studied [The AI Driven Engineer](/series/ai-driven-engineer/).

### A. Structured Logging
Logs are not just text strings to be skimmed by the human eye. They must be machine-readable JSON containing rich metadata.
Every log line from an MCP Server must answer:
- Who is calling? (`agent_id`, `client_name`)
- What tool is being called? (`tool_name`)
- What is the request ID? (`mcp_request_id`)
- What is the status? (`status: success/failed/rate_limited`)

In Go, you should utilize `slog` (the structured logging package introduced in Go 1.21) hooked up to an OpenTelemetry exporter.

### B. Metrics
Metrics help you detect Behavioral Anomalies in the Agent over time, preventing runaway costs and security breaches.
Important metrics to track via Prometheus/Grafana:
- `mcp_tool_invocation_total`: The total number of times a tool is called, tagged by `tool_name` and `agent_id`. If the `delete_database` tool suddenly spikes from 0 to 100 in a minute, you have an active Prompt Injection happening.
- `mcp_request_duration_seconds`: Processing time. Vital for diagnosing slow third-party API dependencies.
- `mcp_payload_size_bytes`: Payload size. A bloated Context Window often originates from a Tool returning too much garbage data. Monitoring this prevents the "Context Window Exceeded" token crash.

### C. Distributed Tracing
This is the hardest but most valuable part. A single "thought" from an LLM can lead to 5 consecutive MCP Tool calls, distributed across 3 different MCP Servers. As seen in hyper-scale microservices architectures (like [Alipay Double 11](/series/alipay-double-11/)), tracing the request lifecycle is paramount.

Without a Correlation ID, you will see disjointed logs and won't be able to tell if they belong to the same reasoning loop of an Agent. The Gateway must inject a `trace_id` (via standard W3C Trace Context headers) into every request sent down to the MCP Server over HTTP.

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant Gateway as MCP Gateway
    participant S1 as Server 1 (Jira)
    participant S2 as Server 2 (GitHub)

    Agent->>Gateway: 1. Request: "Review bug #123"
    Note over Gateway: Generate Trace_ID = XYZ-123
    Gateway->>S1: 2. Call Jira Tool [Trace_ID=XYZ-123]
    S1-->>Gateway: 3. Return Issue result
    Gateway->>S2: 4. Call GitHub Tool [Trace_ID=XYZ-123]
    S2-->>Gateway: 5. Return PR diff
    Note over Gateway,S2: All logs across the system are tagged with Trace_ID XYZ-123
```
<p align="center"><em>Figure 5: Gateway injecting Trace_ID for Distributed Tracing across multiple MCP Servers</em></p>

## 2. SIEM Integration and Audit Trail

For Enterprise organizations, pushing logs to Kibana or Grafana is not enough. Logs related to system-altering behaviors (like `provision_server` or `modify_user_role`) must be treated as **Security Events**.

They need to be exported directly into SIEM (Security Information and Event Management) systems like Splunk, Datadog Security, or Microsoft Sentinel for anomaly detection and compliance auditing.

### Standard Audit Log Structure:
```json
{
  "timestamp": "2026-05-15T14:30:00Z",
  "event_type": "mcp_tool_execution",
  "actor": {
    "identity_type": "spiffe",
    "agent_id": "spiffe://example.com/agent/finance-bot/uuid-abc123",
    "user_context": "john.doe@company.com"
  },
  "action": {
    "server_name": "billing-mcp-server",
    "tool_name": "refund_customer",
    "arguments_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "outcome": "success",
  "trace_id": "5b8aa5a2-c941-4775-b66f-3c6eb2d6a695"
}
```
*Crucial Note on Data Scrubbing:* Do not log sensitive parameters (PII, Passwords, API Secrets) in plain text. Always scrub or hash the arguments payload (`arguments_hash`) to avoid creating a new vulnerability (MCP01 Token Mismanagement via Log Leakage).

## 3. Semantic Validation at the Gateway

Observability is not just for "looking at the past". It can be used to block requests in Real-time.

Your Gateway can apply **Semantic Validation**:
Based on live metrics, if the Gateway notices an Agent continuously calling the `search_logs` tool with rapidly changing keywords but getting no results, it can recognize that the Agent is stuck in an Infinite reasoning loop. The Gateway can automatically cut the connection (Circuit Breaker) to save token costs and prevent the Agent from spiraling out of control.

## 4. Frequently Asked Questions (FAQ)

**Q: Do I need to implement OpenTelemetry manually in Go?**  
**A:** The Official Go SDK provides hooks and middleware for OpenTelemetry. You can easily wrap your `mcp.AddTool` handlers with OTel spans, automatically capturing the execution duration and status.

**Q: How do I store the Agent's original prompt along with the MCP logs?**  
**A:** The MCP Server does not see the Agent's prompt (it only sees the parsed JSON-RPC arguments). To correlate the prompt with the execution, the Agent Orchestrator (like LangChain) must attach the `trace_id` to its LLM prompt logs, and the Gateway must pass that same `trace_id` to the MCP Server. You join the data inside your SIEM using the `trace_id`.

## Conclusion

Observability turns the "black box" of AI into a transparent, verifiable system. By leveraging OpenTelemetry, Metrics, and Tracing, you ensure that every action taken by an autonomous Agent is auditable and justifiable to compliance boards. 

Once you have a solid Gateway, tight Security, and comprehensive Observability, the final step is to scale this system out for the entire enterprise to use.


## 4. Go Observability Correlation Middleware

Observability in MCP architectures is critical to detect agent hallucination and monitor Tool Execution times. The following middleware correlates logs using unique Trace IDs.

### Observability Log Snippet
```go
package main

import (
	"fmt"
	"net/http"
	"time"
)

func TraceLoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()
		traceID := r.Header.Get("X-Trace-ID")
		if traceID == "" {
			traceID = fmt.Sprintf("tr-%d", time.Now().UnixNano())
		}
		
		fmt.Printf("[MCP LOG] START | TraceID: %s | Path: %s\n", traceID, r.URL.Path)
		next.ServeHTTP(w, r)
		fmt.Printf("[MCP LOG] END   | TraceID: %s | Duration: %v\n", traceID, time.Since(startTime))
	})
}

func main() {
	mux := http.NewServeMux()
	mux.Handle("/mcp/v1/tools/call", TraceLoggingMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("success"))
	})))
	fmt.Println("Telemetry logging middleware bound to handler chain.")
}
```

### Monitoring Hallucinations and Loop Detection
By analyzing observability metrics:
- Track tool call failure ratios. A spike in errors indicates malformed inputs from the agent.
- Log agent responses alongside tool outputs. This matches execution contexts to find hallucinations.
- Implement loop detection: if the same tool is called with matching parameters more than 5 times in a minute, terminate the session.

### Technical Appendix: OpenTelemetry Spans for Agent Tool Execution
Tracing agent reasoning loops requires propagating contexts:
- Use OpenTelemetry SDK to create spans for the main reasoning loop.
- Nest tool execution calls as child spans under the active agent query trace.
- Annotate spans with custom attributes like `llm.model`, `llm.tokens.prompt`, `llm.tokens.completion`, and `mcp.tool.name`.
- Route trace telemetry to Jaeger or Datadog over gRPC to visualize latency bottlenecks in the tool chain.

## 5. Prometheus Metrics Scraping & Dashboard Configurations

To monitor the health of your MCP gateway and backend servers, you must set up automated scraping configurations. Below is the Prometheus scrape configuration block and the metrics dictionary to build your Grafana dashboards.

### Prometheus Configuration Snippet
Add this job definition to your `prometheus.yml` configuration:

```yaml
scrape_configs:
  - job_name: 'mcp-gateway'
    scrape_interval: 5s
    static_configs:
      - targets: ['mcp-gateway.production.internal:8080']
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'prod-gateway-01'

  - job_name: 'mcp-backend-servers'
    scrape_interval: 10s
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - action: keep
        source_labels: [__meta_kubernetes_pod_label_app]
        regex: mcp-server-.*
```

### Core Telemetry Metrics to Track
Configure your Grafana panels to alert on these metrics:
- `mcp_gateway_active_streams`: Track the number of active SSE connections. Sudden drops indicate proxy timeout issues.
- `mcp_tool_execution_duration_seconds`: Histogram of latency per tool call. Set thresholds at 1.5s for warnings.
- `mcp_tool_errors_total`: Counter of failed tool calls, segmented by `error_code` and `tool_name` labels.

---

## Navigation & Next Steps

[← Previous Part]({{< ref "part-5-security.md" >}})
[Next Part →]({{< ref "part-7-enterprise.md" >}})

🔗 **Next Step:** Continue to [Part 7: Enterprise Scaling & Governance]({{< ref "part-7-enterprise.md" >}})

Need help implementing this architecture in your organization? [Contact us](/contact/) or [hire our technical consulting team](/hire/) to review your system design and codebase.
