---
title: "Part 2: Build a Production Server with Go"
date: "2026-05-15T14:00:00+07:00"
lastmod: "2026-05-15T14:00:00+07:00"
draft: false
weight: 3
categories: ["Implementation"]
tags: ["Golang", "MCP SDK", "Best Practices", "Error Handling"]
description: "A practical guide to building a Model Context Protocol Server with the Go SDK."
aliases: ["/series/mcp-engineering-in-production/part-2-build/"]
cover: {'image': 'images/posts/generative-ui-mcp-cover.png', 'alt': 'MCP Engineering in Production series: Go SDK to enterprise Model Context Protocol deployment', 'relative': False}
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/mcp-engineering-in-production/part-2-build/"
ShowToc: true
TocOpen: true
---

> **Prerequisite:** Before reading this part, please ensure you have read the previous article in this series: [Part 2: Part 1: Protocol Fundamentals & Transport Evolution]({{< ref "part-1-protocol.md" >}}).

Writing a simple Python script that runs over `stdio` to demo the Model Context Protocol (MCP) on your local machine is easy. But deploying an MCP Server into a Kubernetes cluster to handle thousands of AI Agent requests per minute without crashing requires a powerful compiled language, a small memory footprint, and excellent concurrency support. That's why **Go (Golang)** has become the top choice for Infrastructure and Platform teams.

In this article, we will dive deep into using the Go SDK to build a Production MCP Server, while avoiding the pitfalls that engineers new to Agentic AI often fall into. We will also explore advanced concepts like `context.Context` cancellation handling and Context Window optimization.

## 1. Three Enterprise Design Principles

Before typing the first line of code, Tech Leads must agree on 3 vital principles when designing MCP Tools within the organization:

1. **Bounded Context:** Do not cram every tool in your entire system into a single "Super Server". Design servers following Domain-Driven Design (DDD) philosophy. For example, `mcp-billing-server` should only handle payment operations, while `mcp-k8s-server` only interacts with cluster infrastructure. This separation limits the blast radius of security risks and adheres to principles discussed in the [AI Driven Playbook](/series/ai-driven-playbook/).
2. **Outcome-Oriented:** An Agent is not like a standard frontend interface. Do not expose low-level CRUD APIs like `create_user_record`, `assign_user_role`, `send_welcome_email`. Expose APIs based on complete workflows: `onboard_employee(email, department)`. Forcing an LLM to call too many granular tools sequentially will bloat its Context Window, burn tokens, and significantly increase the hallucination rate.
3. **Stateless and Scalable:** An MCP Server must absolutely not hold local state in memory. Any session state, transaction locks, or caching must be pushed to external storage systems like Redis or PostgreSQL. Only then can the system safely handle Horizontal Pod Autoscaling (HPA) when cloning the server into dozens of instances. For an extreme example of stateless scaling, refer to the [Alipay Double 11 Architecture](/series/alipay-double-11/) series.

## 2. Choosing an SDK: Official vs Community

In the Go ecosystem for MCP, historical development has created a notable split. Engineers need to clearly distinguish between the two main libraries:

- **Community SDK (`github.com/mark3labs/mcp-go`):** Before the official project released its own SDK, this was the most popular community library. It is extremely flexible and pioneered support for various Transport Layers (including HTTP and SSE). However, in the long term, it relies on community maintenance efforts.
- **Official SDK ([`github.com/modelcontextprotocol/go-sdk`](https://github.com/modelcontextprotocol/go-sdk)):** Starting in 2025-2026, the MCP project, in collaboration with Google, released the official SDK. It strictly adheres to every change in the Protocol Specification, perfectly optimizes automatic JSON Schema generation from Go struct tags, and offers enterprise-grade stability.

In a Production Enterprise environment, **we strongly recommend/require using the Official SDK** to ensure long-term compatibility and receive the fastest security patches.

### Initializing the Project and `go.mod`

Let's start by initializing a Go module and downloading the dependencies. Open your terminal and run:

```bash
mkdir cloud-ops-mcp
cd cloud-ops-mcp
go mod init my-mcp-server
go get github.com/modelcontextprotocol/go-sdk/mcp
```

Your `go.mod` file should look something like this:

```go
module my-mcp-server

go 1.23.0 // Or the latest Go version

require (
	github.com/modelcontextprotocol/go-sdk v1.x.x
)
```

## 3. Code Structure and Schema Validation

LLMs are highly sensitive to parameter names and descriptions. The looser your schema, the easier it is for the LLM to hallucinate non-existent parameters or pass incorrect formats. In Go, we will fully leverage the power of `struct tags` combined with `jsonschema` so the official SDK can automatically generate the perfect schema for the LLM.

Let's look at an example defining a tool to provision cloud resources (`provision_cloud_resource`):

```go
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Declare a strict Schema using jsonschema tags
type ProvisionRequest struct {
	ResourceType string `json:"resource_type" jsonschema:"required,enum=ec2,enum=s3,description=The type of resource to provision (only 'ec2' or 's3' accepted)"`
	Region       string `json:"region" jsonschema:"required,description=AWS Region (e.g., 'us-west-2')"`
	RequestID    string `json:"request_id" jsonschema:"required,description=UUID generated by the client to ensure Idempotency. This is mandatory."`
}

func main() {
	// Initialize Server
	server := mcp.NewServer("cloud-ops-mcp", "1.0.0")

	// Register the Tool with the system
	mcp.AddTool(server, mcp.Tool{
		Name:        "provision_cloud_resource",
		Description: "A tool to create a new cloud resource. The Agent must call this before deploying source code to the environment.",
	}, handleProvision)

	// Start the Server. 
	// (In real Production, we would use Streamable HTTP transport. Here we use Stdio to illustrate the basic flow)
	log.SetOutput(os.Stderr)
	log.Println("Starting Model Context Protocol Server...")

	if err := server.ServeStdio(); err != nil {
		log.Fatalf("Server crash: %v", err)
	}
}
```

### Why do we need `RequestID` (Idempotency)?

Network environments and Agentic Workflows are never perfect. Networks can experience packet loss, and LLM APIs can time out. When this happens, Agent orchestrators (like LangGraph or AutoGen) are often designed to **automatically retry** function calls.

If you don't design your tool with **Idempotency** (meaning whether called 1 or 100 times sequentially with the same parameters, the system state does not change), a retry might cause the Agent to accidentally spin up 5 EC2 instances instead of 1. The cloud bill at the end of the month would be a disaster.

Always require the Agent to generate a `request_id` (or idempotency_key). Your Go server will cache this key (e.g., in Redis) to de-duplicate incoming requests.

## 4. Handling Logic, Cancellations, and Context Windows

When an Agent calls a tool, the returned result must be a message (text or structured JSON) that the LLM can **read, parse, and understand easily**. 

### Managing the Context Window
If your tool queries a database and finds 10,000 rows, returning all 10,000 rows in the `mcp.CallToolResult` will instantly overflow the LLM's Context Window (causing a Token Limit Error). A robust Go server must truncate results and provide pagination hints to the Agent.

```go
func handleProvision(ctx context.Context, req mcp.CallToolRequest) (mcp.CallToolResult, error) {
	// 1. Check for Context Cancellation
	// Agents can cancel requests if they realize they made a mistake or timeout
	select {
	case <-ctx.Done():
		return mcp.NewToolResultError("Request was cancelled by the Agent"), ctx.Err()
	default:
		// Continue processing
	}

	// 2. Parse arguments
	args := req.Arguments
	reqID, _ := args["request_id"].(string)
	resourceType, _ := args["resource_type"].(string)
	region, _ := args["region"].(string)

	if reqID == "" {
		// Differentiate between Tool Execution Error and Protocol Error
		// Return the error as text to the LLM so it can learn and correct its mistake
		return mcp.NewToolResultError("Validation Failed: request_id is missing. Please retry with a valid UUID."), nil
	}

	// 3. Execute business logic
	log.Printf("[req: %s] Starting provisioning of %s in %s", reqID, resourceType, region)

	// 4. Return concise, markdown-formatted text
	msg := fmt.Sprintf("✅ **Task completed**.\n- Resource: `%s`\n- Region: `%s`\n- ARN: `arn:aws:%s:12345:res-01`", 
		resourceType, region, resourceType)

	return mcp.NewToolResultText(msg), nil
}
```

### Error Semantics in Go vs MCP
Notice that when validation fails, we return `mcp.NewToolResultError(text), nil`. We do **not** return `nil, err`. 
In MCP, if you return a native Go `error`, the protocol interprets this as a fatal server crash, breaking the connection. If you return an `mcp.CallToolResult` with the `isError` flag set to true, the Agent receives the error message smoothly, understands it made a mistake, and will attempt to fix its parameters and retry. This concept of graceful degradation is critical in [Agentic System Architecture](/series/agentic-system-architecture/).

## 5. The Fatal Trap: Logging to STDOUT

This is a fundamental yet the most common mistake development teams make when transitioning from writing REST backends to writing MCP Servers over `stdio`: **Using `fmt.Println()` to print debug logs.**

The MCP protocol (when running transport over `stdio`) transmits standard JSON-RPC packets via the `stdout` stream. Any character, any extra log line that is not valid JSON-RPC printed to `stdout` will immediately crash the Client (like Claude Desktop or the Agent Gateway) due to a JSON parsing error.

**The Golden Rule:** In MCP Server code, all internal logs, warnings, and errors must be routed to `stderr` (like the `log.SetOutput(os.Stderr)` line above) or sent out through a dedicated telemetry system (like OpenTelemetry).

## 6. Frequently Asked Questions (FAQ)

**Q: Can my Go Server return binary data like Images or PDFs to the Agent?**  
**A:** Yes! The `CallToolResult` supports returning `ImageContent`. You must Base64 encode the binary file and specify the `mimeType` (e.g., `image/png`). Multimodal LLMs like GPT-4o or Claude 3.5 Sonnet can natively read these images from the MCP result.

**Q: How do we handle long-running operations? If provisioning takes 5 minutes, the Agent will timeout.**  
**A:** Do not block the MCP request for 5 minutes. Implement an asynchronous pattern: the `provision` tool should immediately return a `Job_ID` and a status of "Pending". Then, provide a second tool called `check_job_status(Job_ID)` so the Agent can poll for the result, or use the `Resources` primitive to allow the Agent to subscribe to status updates.

## Conclusion

You have just walked through the foundational structure of a Production MCP Server written in Golang. To stand strong in an Enterprise environment, it requires strict Schema definitions, Idempotency by design, Context Window protection, and strict Logging discipline to prevent breaking the protocol.

But how do we protect this server? What prevents a malicious (or hacked) AI Agent from arbitrarily calling `provision_cloud_resource` and spinning up thousands of massive VMs, burning through the company's bank account? We will need to fundamentally solve the problem of identity and authorization.

---

## Navigation & Next Steps

[← Previous Part]({{< ref "part-1-protocol.md" >}})
[Next Part →]({{< ref "part-3-identity.md" >}})

🔗 **Next Step:** Continue to [Part 3: Part 3: Identity & AuthN For Agentic Workflows]({{< ref "part-3-identity.md" >}})

Need help implementing this architecture in your organization? [Contact us](/contact/) or [hire our technical consulting team](/hire/) to review your system design and codebase.
