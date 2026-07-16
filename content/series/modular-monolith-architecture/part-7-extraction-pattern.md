---title: "Part 7: Extraction Pattern – When Should You Extract Microservices?"
lastmod: "2026-07-03T14:59:00+07:00"
description: "Not everything belongs in a Monolith. Learn how to determine when a module should be extracted into a Microservice through lessons from Sentry, GitLab, and"
slug: "extraction-pattern-when-to-extract-microservices"
tags: ["Microservices", "Extraction", "Sentry", "GitLab", "Modular Monolith", "Architecture"]
aliases:
  - "/series/modular-monolith-architecture/part-7-extraction-pattern/"
  - "/series/modular-monolith-architecture/migration-playbook-microservices-to-modular-monolith/part-7-extraction-pattern.md"
cover:
  image: "images/posts/golang-microservices-cover.png"
  alt: "Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/modular-monolith-architecture/extraction-pattern-when-to-extract-microservices/"
ShowToc: true
TocOpen: true
---

# Part 7: Extraction Pattern – When Should You Extract Microservices?

Advocating for a **Modular Monolith** architecture does not equate to a conservative "put absolutely everything in one place" mentality. In reality, even the greatest Monolith systems like Shopify, Sentry, or GitLab possess a few "satellites" (Microservices) orbiting their central core.

The core issue is: **We only extract a feature into a Microservice when it truly deserves it**, not out of preference. Expert Sam Newman – author of *Monolith to Microservices* – emphasizes that: If you cannot successfully separate the Database Schema inside a Monolith, you will undoubtedly create a disastrous Microservice.

Below are **4 signals** indicating a Module has "graduated" and is ready to be extracted from the Modular Monolith.

## Signal 1: Resource-Specific Independent Scaling Needs

Sometimes, your application has a task that consumes system resources entirely differently from the rest of the business logic (standard CRUD operations).

**Case Study: Sentry and the Snuba/Relay services**
Sentry (the world's most popular error tracking platform) was built at its core as a massive Monolith running on Python (Django). However, they faced a problem: The rate at which clients sent error events (Events Ingestion) was thousands of times higher than the action of viewing reports on the web.
- Instead of forcing the web system (Django) to bear this massive traffic, Sentry extracted the event reception layer into an independent Microservice named **Relay** (rewritten entirely in **Rust** to optimize CPU and RAM).
- Simultaneously, the high-cardinality data storage and search phase was extracted into a separate service named **Snuba** (running on ClickHouse DB).
The rest of the business logic, from billing and account management to error analysis logic, continues to reside safely and neatly within the Python Monolith block.

## Signal 2: Specialized Environment & Language Requirements (Polyglot)

Sometimes, the programming language of the Monolith does not provide the best libraries or performance for a specific feature.

**Case Study: GitLab and Gitaly**
GitLab is an enormous Ruby on Rails Monolith project. But reading/writing directly to the Git repo's FileSystem using Ruby was extremely slow and created severe I/O Bottlenecks when scaling.
- GitLab decided to create a single specialized service to communicate with Git files on the hard drive, called **Gitaly**.
- Gitaly was written in **Go (Golang)** to handle concurrency and low-level I/O access far better than Ruby.
- However, GitLab is extremely disciplined: Gitaly *only* processes Git files. All authorization, organization management, and merge request features remain embedded in the Rails core. This is a perfect testament to "Extract the tool, Keep the business logic."

## Signal 3: Disparate Deployment Cadence

If your entire Monolith is typically released every 2 days, but one single module (e.g., an AI product recommendation algorithm module) needs configuration updates every 15 minutes from Data Scientists.

This disparity in risk cadence is a valid reason to extract the AI Module into an independent Microservice. This prevents AI configuration changes from disrupting the stable CI/CD lifecycle of the entire core system.

## Signal 4: Compliance Requirements and Organizational Boundaries

In large organizations, handling credit card information (PCI-DSS) or health/medical data (HIPAA) often must comply with strict security audit regulations.

If the entire Monolith contains credit card processing code, you must push millions of lines of code through expensive periodic audit processes. Extracting the Billing module into a small, compact system operated by a Dedicated Security Team is a wise strategic Organizational Boundary decision to save on legal and compliance costs.

## The Rule of "Tearing Down" the Database

Before you actually create a new repository and write a Microservice:
1. You must ensure that the Module within the Monolith already has a standard Bounded Context.
2. The Tables of that module must absolutely not be intertwined (JOINed) with the tables of another module.

Extract the Database Schema before you extract the Code. If the DB cannot be decoupled, the Code will never be able to run independently.

---


## 4. ConnectRPC Service Adapter for Interface Migration

When a module within a Modular Monolith grows too large and meets the criteria for extraction, it must be separated into a distinct microservice. To do this without rewriting client code inside the monolith, we use the Adapter pattern via ConnectRPC.

### Go ConnectRPC Adapter
The adapter implements the internal Go interface but forwards requests over the network via a high-performance HTTP/2 gRPC client.

```go
package main

import (
	"context"
	"fmt"
	"net/http"
)

type OrderRequest struct{ ID string }
type OrderResponse struct{ Status string }

// Internal interface used by the monolith
type OrderService interface {
	GetOrder(ctx context.Context, req *OrderRequest) (*OrderResponse, error)
}

// RemoteAdapter implements OrderService interface but routes over gRPC
type RemoteAdapter struct {
	RemoteURL string
}

func (a *RemoteAdapter) GetOrder(ctx context.Context, req *OrderRequest) (*OrderResponse, error) {
	// In a real environment, we would use a ConnectRPC client
	fmt.Printf("Adapter routing request for Order %s to remote microservice: %s\n", req.ID, a.RemoteURL)
	return &OrderResponse{Status: "Shipped"}, nil
}

func main() {
	var svc OrderService = &RemoteAdapter{RemoteURL: "http://orders-microservice.local"}
	res, _ := svc.GetOrder(context.Background(), &OrderRequest{ID: "ord-998"})
	fmt.Printf("Result status: %s\n", res.Status)
}
```

### Steps to Safely Extract a Module
The physical extraction process should follow these steps:
- **Step 1: Check AST Imports:** Run the AST validator to guarantee there are no illegal direct package imports coupling the target module.
- **Step 2: Split Schema:** Move the module schema to a separate database instance, ensuring all links use logical keys rather than joins.
- **Step 3: Deploy Service:** Package the module in a Docker image and deploy it on ECS or Kubernetes.
- **Step 4: Register Adapter:** Replace the local module implementation with the ConnectRPC adapter in the dependency injection container.
- **Step 5: Cut Over Traffic:** Enable the adapter dynamically via feature flags to monitor latency and error metrics.

### Technical Appendix: HTTP/2 Multiplexing & Client-Side Load Balancing
ConnectRPC relies on HTTP/2, which offers features over HTTP/1.1:
- **Multiplexing:** Send multiple RPC queries over a single TCP connection, eliminating the TCP handshake overhead for each request.
- **Header Compression:** Use HPACK compression to reduce request payload size.
- **Server Push:** Push data to clients before they ask, optimizing real-time monitoring streams.
To prevent load balancers from becoming a bottleneck, configure the client adapter to use client-side round-robin load balancing. The client polls the Kubernetes DNS API or Consul to fetch a list of healthy pod IPs, maintaining persistent HTTP/2 connection pools to each target pod directly.


Thus, we have gone through all the theory and design processes. In **[Part 8: Case Study Matrix]({{< ref "part-8-case-study-matrix.md" >}})** (the final article of this Playbook series), we will validate all our reasoning with a comprehensive table of speaking numbers from Shopify, Stack Overflow, Target, Zulip, Notion, and Basecamp.


