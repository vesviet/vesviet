---
title: "Production Agentic Search Optimization in Go"
date: 2026-05-22T22:45:00+07:00
draft: false
author: "Vesviet Team"
weight: 7
slug: "part-6-production-operations"
keywords: ["Agentic Search Production Optimization"]
tags: ["Golang", "Eino", "Semantic Caching", "Model Routing", "SSE Streaming", "OpenTelemetry"]
description: "Optimize Agentic Search in production with Semantic Caching (Redis), LLM routing, SSE Streaming, and OpenTelemetry monitoring via Eino."
categories: ["Engineering"]
ShowToc: true
TocOpen: true
---

In [Part 5: Critique Loop - Preventing LLM Hallucination](/series/agentic-ecommerce-search/part-5-critique-loop/), we successfully built an automated response auditing module to ensure logical accuracy. However, when deploying this Agentic Search system to a large-scale production environment serving millions of users, you will immediately face practical operational challenges:
1. **Unit Economics**: Every user search going through multiple LLM calls (from generating answers, calling tools, to self-critiquing) will skyrocket API bills.
2. **Latency**: Customers won't patiently wait 5-10 seconds to receive the complete final answer.
3. **Observability**: How do you trace which nodes a request went through, how many tokens it consumed, and where it encountered errors?

The final article in this series will guide you on thoroughly solving these problems by integrating **Semantic Caching (Redis)**, **Deterministic Model Routing**, **Server-Sent Events (SSE) Streaming**, and **OpenTelemetry Tracing** into the **Eino (CloudWeGo)** framework.

---

## 1. Semantic Caching With Redis

### Concept & Differences
Unlike traditional caches (Key-Value Cache that only matches exact characters), **Semantic Caching** stores question-answer pairs as vector embeddings. When a user submits a new question:
1. The system generates a vector embedding for the query.
2. Performs a K-Nearest Neighbors (KNN) Vector Search on Redis to find similar questions already existing in the cache.
3. If the Cosine Distance is smaller than a specified threshold (e.g., `Cosine Distance < 0.15` or `Similarity > 0.85`), the system immediately returns the cached answer, completely bypassing the LLM calls.

### Configuring go-redis/v9 Connection
To be compatible with vector search (`FT.SEARCH`) on Redis Stack, the `go-redis/v9` client needs to be configured using **Protocol 2** and enable the **UnstableResp3** flag.

Below is the source code initializing Eino's Retriever integrated with Redis:

```go
package cache

import (
	"context"
	"fmt"

	"github.com/redis/go-redis/v9"
	"github.com/cloudwego/eino-ext/components/retriever/redis"
)

// InitRedisRetriever establishes the connection and initializes the Eino Redis Retriever
func InitRedisRetriever(ctx context.Context) (*redis.Retriever, error) {
	// 1. Initialize go-redis client using Protocol 2 to be compatible with FT.SEARCH
	client := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: "", // Enter password if any
		DB:       0,
		Protocol: 2, 
	})

	// Enable UnstableResp3 to support parsing complex response formats from RediSearch
	client.Options().UnstableResp3 = true

	// Check connection to the Redis Server
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	// 2. Initialize Retriever configuring eino-ext vector search
	retriever, err := redis.NewRetriever(ctx, &redis.RetrieverConfig{
		Client:       client,
		Index:        "semantic_cache_idx", // Vector index name on Redis
		VectorField:  "query_vector",       // Field storing the embedding
		EmbeddingKey: "query_text",         // Field storing the raw query
		TopK:         1,                    // Only fetch the most similar result
	})
	if err != nil {
		return nil, fmt.Errorf("failed to initialize Eino Redis Retriever: %w", err)
	}

	return retriever, nil
}
```

---

## 2. Deterministic LLM Model Routing

Not every user question requires expensive and slow large language models.
* Simple questions: *"Hello"*, *"Where is your shop?"* -> Route to a cheap, high-speed model (e.g., `gpt-4o-mini`).
* Complex questions: *"Compare Asus ROG with MSI Cyborg and filter in-stock machines at District 1"* -> Route to an advanced model (e.g., `Gemini 1.5 Pro` or `gpt-4o`).

We use `compose.NewGraphBranch` combined with `compose.ProcessState` to inspect the complexity of the query based on keywords and character length, subsequently deciding the graph branching:

```go
package routing

import (
	"context"
	"strings"

	"github.com/cloudwego/eino/compose"
	"github.com/cloudwego/eino/schema"
)

// QueryState stores query information for routing decisions
type QueryState struct {
	Query     string
	IsComplex bool
}

// ModelRouterBranch executes dynamic routing based on the question state
var ModelRouterBranch = compose.NewGraphBranch(func(ctx context.Context, input *schema.Message) (string, error) {
	var nextNode string
	
	err := compose.ProcessState[*QueryState](ctx, func(ctx context.Context, state *QueryState) error {
		queryLower := strings.ToLower(state.Query)
		
		// Routing constraint: If the query is long (> 80 characters) or contains complex comparison/analysis keywords
		if len(state.Query) > 80 || 
			strings.Contains(queryLower, "compare") || 
			strings.Contains(queryLower, "analyze") || 
			strings.Contains(queryLower, "why") {
			
			state.IsComplex = true
			nextNode = "advanced_llm_node"
		} else {
			state.IsComplex = false
			nextNode = "cheap_llm_node"
		}
		return nil
	})
	
	return nextNode, err
}, map[string]bool{
	"cheap_llm_node":    true, // gpt-4o-mini node
	"advanced_llm_node": true, // Gemini 1.5 Pro node
})
```

---

## 3. Server-Sent Events (SSE) Streaming HTTP Handler

Time-to-First-Token (TTFT) latency is crucial in AI chat experiences. By using **Server-Sent Events (SSE)**, the backend can push each token generated by the LLM back to the browser immediately via standard HTTP protocols.

The Go snippet below sets up a standard SSE handler that receives the Stream from Eino and ensures resource deallocation by calling `defer streamReader.Close()` to prevent Goroutine leaks:

```go
package sse

import (
	"context"
	"fmt"
	"net/http"

	"github.com/cloudwego/eino/compose"
	"github.com/cloudwego/eino/schema"
)

// StreamSSEHandler processes the HTTP request and pushes data as Server-Sent Events
func StreamSSEHandler(w http.ResponseWriter, r *http.Request, runnable compose.Runnable[[]*schema.Message, *schema.StreamReader[*schema.Message]]) {
	// 1. Set required HTTP Headers for SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Transfer-Encoding", "chunked")

	// Ensure the Web Server supports Streaming (Flusher)
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Browser or Server does not support Response Streaming", http.StatusInternalServerError)
		return
	}

	query := r.URL.Query().Get("q")
	if query == "" {
		http.Error(w, "Query parameter 'q' cannot be empty", http.StatusBadRequest)
		return
	}

	input := []*schema.Message{schema.UserMessage(query)}

	// 2. Activate Eino Stream to read data sequentially
	streamReader, err := runnable.Stream(r.Context(), input)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to initialize Stream: %v", err), http.StatusInternalServerError)
		return
	}
	// CRITICAL: Always Close streamReader to free the background Eino goroutines
	defer streamReader.Close() 

	// 3. Loop to receive data and push to Client
	for {
		msg, err := streamReader.Recv()
		if err != nil {
			// Receive EOF signal when the stream naturally concludes
			break
		}
		
		// Write data in standard SSE format (data: <content>\n\n)
		_, _ = fmt.Fprintf(w, "data: %s\n\n", msg.Content)
		flusher.Flush() // Push data out over the network immediately
	}

	// Send stream termination event for the Frontend to close the connection
	_, _ = fmt.Fprint(w, "event: done\ndata: [DONE]\n\n")
	flusher.Flush()
}
```

---

## 4. Monitoring With OpenTelemetry (OTel Telemetry Callbacks)

The Eino framework possesses an Aspect-Oriented architecture allowing intervention into the execution lifecycle of components via a Callback mechanism. Although an official OpenTelemetry integration package is under discussion (See Eino Issue #1028), we can entirely implement a custom `callbacks.Handler` to record execution traces (Spans) and measure token consumption.

The code below utilizes the OpenTelemetry Go SDK to trace the runtime of each Node and attach token information based on the **Semantic Conventions** specification:

```go
package telemetry

import (
	"context"

	"github.com/cloudwego/eino/callbacks"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

var tracer = otel.Tracer("eino-search-agent")

type spanCtxKey struct{}

// NewOTelCallbackHandler creates a custom event handler for monitoring
func NewOTelCallbackHandler() callbacks.Handler {
	return callbacks.NewHandlerBuilder().
		// Triggered when starting a Node in the graph
		OnStartFn(func(ctx context.Context, info *callbacks.RunInfo, input callbacks.CallbackInput) context.Context {
			// Start a new Span based on the respective Node's name
			ctx, span := tracer.Start(ctx, info.ComponentName, trace.WithSpanKind(trace.SpanKindInternal))
			span.SetAttributes(
				attribute.String("eino.component.type", string(info.ComponentType)),
				attribute.String("eino.component.name", info.ComponentName),
			)
			
			// Save Span to context so the next Node or the ending callback can access it
			return context.WithValue(ctx, spanCtxKey{}, span)
		}).
		// Triggered when the Node successfully completes processing
		OnEndFn(func(ctx context.Context, info *callbacks.RunInfo, output callbacks.CallbackOutput) context.Context {
			if span, ok := ctx.Value(spanCtxKey{}).(trace.Span); ok {
				// Record token consumption according to OpenTelemetry Semantic Conventions
				if usage, ok := output.Config["token_usage"].(map[string]int); ok {
					span.SetAttributes(
						attribute.Int("gen_ai.usage.input_tokens", usage["input"]),
						attribute.Int("gen_ai.usage.output_tokens", usage["output"]),
					)
				}
				span.End() // Close Span
			}
			return ctx
		}).
		// Triggered when the Node encounters an error during execution
		OnErrorFn(func(ctx context.Context, info *callbacks.RunInfo, err error) context.Context {
			if span, ok := ctx.Value(spanCtxKey{}).(trace.Span); ok {
				span.RecordError(err) // Mark error in Span
				span.End()
			}
			return ctx
		}).
		Build()
}
```

---

## Series Conclusion: The Agentic Search Engine Journey

Over the course of **6 deep-dive parts**, we have traversed from foundational architectural concepts to practical operational optimization solutions for an AI assistant search system:

* **[Executive Summary](/series/agentic-ecommerce-search/executive-summary/)**: The big picture of why E-commerce needs Agentic Search.
1. **[Part 1: The Paradigm Shift](/series/agentic-ecommerce-search/part-1-golang-orchestration/)**: Understanding why the AI Agent architecture on the **Golang** platform delivers vastly superior performance over Python thanks to Concurrency mechanisms and compile-time safety.
2. **[Part 2: Data Ingestion & Chunking](/series/agentic-ecommerce-search/part-2-ingestion-chunking/)**: Designing the processing pipeline for raw product data, intelligently chunking to preserve hierarchical structure and semantic relationships.
3. **[Part 3: Mastering Qdrant Hybrid Search](/series/agentic-ecommerce-search/part-3-qdrant-hybrid-search/)**: Combining the power of Vector Search (Dense) with hard attribute filters to solve the problem of real-time accurate product filtering.
4. **[Part 4: Active RAG & Strict Tool Calling](/series/agentic-ecommerce-search/part-4-active-rag-tool-calling/)**: Transforming a static LLM into a dynamic agent capable of calling APIs to check actual warehouse status and promotional campaigns.
5. **[Part 5: Self-Reflection Critique Loop](/series/agentic-ecommerce-search/part-5-critique-loop/)**: Establishing an iterative self-evaluation and error-correction loop to control output quality and eradicate hallucination.
6. **[Part 6: Production Operations](/series/agentic-ecommerce-search/part-6-production-operations/)**: Finalizing the cost, latency, and observability challenges with Semantic Cache, Model Routing, SSE, and OpenTelemetry.

This is the complete **Architecture Blueprint** helping you confidently build and operate a next-generation AI Search system in Go. Best of luck applying this to your practical projects!
