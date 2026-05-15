---
title: "Part 6: Observability & Audit Trail"
date: 2026-05-15T14:00:00+07:00
draft: false
weight: 7
categories:
  - Operations
tags:
  - Observability
  - OpenTelemetry
  - SIEM
  - Auditing
description: "Eliminating operational 'blind spots' in AI systems. A guide to setting up OpenTelemetry, Distributed Tracing, and SIEM integration for MCP Servers."
aliases:
  - /series/mcp-engineering-in-production/part-6-observability/
---

As mentioned in [Part 5](/series/mcp-engineering-in-production/part-5-security/), the **MCP08 (Lack of Audit & Telemetry)** vulnerability is one of the biggest risks in Agentic systems. In the [AI Driven Playbook](/series/ai-driven-playbook/), we agreed that: When AI automates tasks on behalf of humans, the requirements for Observability and Auditing become stricter than ever, especially under the pressure of regulations like the EU AI Act.

This article guides you through setting up a standard Observability system for an MCP Server.

## 1. The Three Pillars of Telemetry for MCP

We don't use `fmt.Println()` to debug MCP (this will break the protocol if running over `stdio` as discussed in [Part 2](/series/mcp-engineering-in-production/part-2-build/)). Instead, all telemetry data must be structured and exported via **OpenTelemetry (OTel)**. This mindset should be very familiar if you have studied [The AI Driven Engineer](/series/ai-driven-engineer/).

### A. Structured Logging
Logs are not just text strings. They must be JSON containing metadata.
Every log line from an MCP Server must answer:
- Who is calling? (`agent_id`, `client_name`)
- What tool is being called? (`tool_name`)
- What is the request ID? (`mcp_request_id`)
- What is the status? (`status: success/failed/rate_limited`)

### B. Metrics
Metrics help you detect Behavioral Anomalies in the Agent.
Important metrics to track:
- `mcp_tool_invocation_total`: The total number of times a tool is called. If the `delete_database` tool suddenly spikes, you have an active Prompt Injection happening.
- `mcp_request_duration_seconds`: Processing time.
- `mcp_payload_size_bytes`: Payload size. A bloated Context Window often originates from a Tool returning too much garbage data.

### C. Distributed Tracing
This is the hardest but most valuable part. A single "thought" from an LLM can lead to 5 consecutive MCP Tool calls, distributed across 3 different MCP Servers.
Without a Correlation ID, you will see disjointed logs and won't be able to tell if they belong to the same reasoning loop of an Agent. The Gateway must inject a `trace_id` into the header of every request sent down to the MCP Server.

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

## 2. SIEM Integration and Audit Trail

For Enterprise organizations, pushing logs to Kibana or Grafana is not enough. Logs related to system-altering behaviors (like `provision_server` or `modify_user_role`) must be treated as **Security Events**.

They need to be exported directly into SIEM (Security Information and Event Management) systems like Splunk, Datadog Security, or Microsoft Sentinel.

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
*Note:* Do not log sensitive parameters (PII/Secrets) in plain text; use an `arguments_hash`.

## 3. Semantic Validation at the Gateway

Observability is not just for "looking at the past". It can be used to block requests in Real-time.

Your Gateway can apply **Semantic Validation**:
Based on metrics, if the Gateway notices an Agent continuously calling the `search_logs` tool with rapidly changing keywords but getting no results, it can recognize that the Agent is stuck in an Infinite reasoning loop and automatically cut the connection (Circuit Breaker) to save token costs.

## Conclusion

Observability turns the "black box" of AI into a transparent, verifiable system. Once you have a solid Gateway, tight Security, and comprehensive Observability, the final step is to scale this system out for the entire enterprise to use.

---
*Next up: [Part 7: Enterprise Scaling & Governance](/series/mcp-engineering-in-production/part-7-enterprise/)*
