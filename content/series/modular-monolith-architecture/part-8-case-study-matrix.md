---

title: "Part 8: Case Study Matrix – The Monuments of the Modular Monolith"
lastmod: "2026-07-03T14:59:00+07:00"
description: "A compilation of the greatest Modular Monolith case studies from Shopify, Stack Overflow, Notion, WhatsApp, Target, and Basecamp."
slug: "case-study-matrix-modular-monolith-success-stories"
tags: ["Case Study", "Modular Monolith", "Shopify", "Stack Overflow", "Notion", "WhatsApp"]
aliases: ["/series/modular-monolith-architecture/part-8-case-study-matrix/", "/series/modular-monolith-architecture/extraction-pattern-when-to-extract-microservices/part-8-case-study-matrix.md"]
cover: {'image': 'images/posts/golang-microservices-cover.png', 'alt': 'Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal', 'relative': False}
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/modular-monolith-architecture/case-study-matrix-modular-monolith-success-stories/"
ShowToc: true
TocOpen: true
---

**Answer-first:** The Modular Monolith case study matrix analyzes how Notion, Stack Overflow, Target, and Lyft optimize resources by balancing monolithic vertical scaling with selective service extraction. These real-world architectures prove that keeping core domains co-located in a single binary reduces cloud costs, code duplication, and tooling friction.

> **Prerequisite:** Before reading this part, please ensure you have read the previous article in this series: [Part 7: Extraction Pattern – When Should You Extract Microservices?]({{< ref "part-7-extraction-pattern.md" >}}).

### What You'll Learn That AI Won't Tell You
- **Notion Database Consolidation:** How Notion runs shard migrations inside monolithic logic.
- **Lyft Microservice Consolidations:** Why Lyft merged several microservices back into their core monorepo.
- **Target Peak Scale Handling:** How Target manages Black Friday traffic peaks using vertical monolith replicas.

> **Prerequisite:** Before reading this part, please ensure you have read the previous article in this series: [Part 8: Part 7: Extraction Pattern – When Should You Extract Microservices?]({{< ref "part-7-extraction-pattern.md" >}}).

# Part 8: Case Study Matrix – The Monuments of the Modular Monolith

Numerous debates about architectural design often lead to dead ends due to a lack of quantitative, real-world numbers. There is a common misconception that: "Only Microservices can withstand web-scale loads."

To conclude this Playbook series, we will look at the **Case Study Matrix** – a compilation of the greatest Modular Monolith systems, ranging from massive e-commerce platforms to billion-user chat applications.

## 1. Shopify: 284 Million Requests/Minute with Ruby On Rails

When discussing the Monolith, one cannot ignore **Shopify**. This e-commerce system faces brutally massive traffic spikes during every Black Friday.

- **The Numbers:** Handled over **173 billion requests** during Black Friday/Cyber Monday, peaking at **284 million requests/minute**.
- **Architecture:** The entire core of Shopify remains a massive Ruby on Rails Modular Monolith application (over 3 million lines of code, contributed to by thousands of developers).
- **How they Scale:**
  - They did not fracture the application. Instead, they protected code boundaries using the **Packwerk** library.
  - To solve the performance equation, Shopify invested heavily in **YJIT** (a Just-In-Time compiler for Ruby) helping the application run 15% faster.
  - The database is heavily sharded to distribute write loads.

## 2. Notion: Sharding Postgres (200 Billion Blocks) on a Node.js Monolith

**Notion** is clear proof that "The bottleneck is always in the Database, not the Application Logic."
- **The Numbers:** Stores over **200 billion data blocks**, equivalent to tens of Terabytes.
- **Architecture:** Node.js Monolith.
- **How they Scale:** When Postgres became overloaded, Notion did not shatter the Node.js system into Microservices. They focused entirely on **Database Sharding**. They scaled from 32 to 96 physical Postgres servers using a simple routing algorithm `workspace_id % 480`. The Node.js application remained intact as a Monolith handling centralized logic.

## 3. WhatsApp: 2 Million Concurrent Connections on ONE Server

In 2014, WhatsApp served hundreds of millions of daily active users with only about... 50 engineers.
- **The Numbers:** 2 million concurrent TCP connections on a single physical server.
- **Architecture:** Erlang Monolith.
- **How they Scale:** The WhatsApp team pursued physical system optimization to an extreme degree (Vertical Scaling). They tuned everything from the FreeBSD kernel to Erlang's BEAM runtime to achieve massive connection capacity on each network node. The simplicity of the Monolith design helped the system operate smoothly and with far less risk than a distributed approach.

## 4. 37signals (HEY/Basecamp): Saving $1.5 Million USD by Dropping the Cloud

The company belonging to the creator of the Ruby on Rails framework (DHH) holds strong views on the Majestic Monolith.
- **The Event:** The "Cloud Exit" campaign (abandoning the AWS cloud) to bring their Monolith applications (HEY, Basecamp) to run on physical bare-metal servers purchased by the company.
- **How they executed:** They utilized the open-source tool **Kamal** to simplify deploying Docker containers directly onto Bare-metal servers with Zero-downtime deployment capabilities. They didn't need to employ the complexity of Kubernetes.
- **The Result:** Saved **$1.5 million USD** in cloud server rental costs in just the first year.

## 5. Target: Consolidating Micro-APIs to Accelerate Mobile Experience

The retail giant Target once applied Microservices extensively for its mobile backend.
- **The Problem:** To load a checkout screen, the Mobile App had to call back and forth across dozens of Micro-APIs. The latency generated from HTTP handshakes severely degraded the user experience.
- **How they executed:** Target decided to **Consolidate** these Micro-APIs back into a larger Monolithic API Backend.
- **The Result:** Completely eradicated internal network hops, reducing the average latency of requests by over **120ms** – a critical timeframe for E-commerce conversion rates.

## 6. Stack Overflow: The Art of In-Memory Caching

As mentioned throughout this Series, **Stack Overflow** serves billions of page views every month with only 9 primary Web servers.
- **Architecture:** C# .NET Monolith.
- **The Secret:** They store the entire Tag Engine in the RAM of each Web Server. Instead of querying a caching Microservice or a database, retrieving a list of articles by Tag only takes a **few nanoseconds** reading from internal memory. This speed is unrivaled.

## Conclusion of the Entire Series

The resurgence of the **Modular Monolith** in the years 2024-2026 is not a technological step backward. It is a "Correction" or maturation. The software industry has finally realized that: **Separating systems over a TCP/IP network is the most expensive, most complex, and most failure-prone solution to solve problems related to people (Organization).**

By rigorously designing hard Domain boundaries using tools (Packwerk, ArchUnit), consolidating databases to avoid fragmentation, and fully leveraging the power of modern hardware through internal Caching, the Modular Monolith helps us save FinOps costs, simplify CI/CD, and return the inherent Developer Velocity back to engineers.

> "Start with a Monolith. If the boundaries are good enough, you can always split it into Microservices someday... but 90% of projects will never need that day."


## 4. In-Process Tag-Engine Caching Mechanics

To achieve the lightning-fast performance of Shopify and Basecamp inside a Modular Monolith, aggressive local caching is necessary. The primary challenge is cache invalidation. A tag-based caching engine allows invalidating multiple related cache blocks simultaneously.

### Go Thread-Safe Tagged Cache
```go
package main

import (
	"fmt"
	"sync"
)

type TaggedCache struct {
	mu    sync.RWMutex
	items map[string]interface{}
	tags  map[string]map[string]bool
}

func NewTaggedCache() *TaggedCache {
	return &TaggedCache{
		items: make(map[string]interface{}),
		tags:  make(map[string]map[string]bool),
	}
}

func (c *TaggedCache) Set(key string, val interface{}, tags []string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.items[key] = val
	for _, t := range tags {
		if c.tags[t] == nil {
			c.tags[t] = make(map[string]bool)
		}
		c.tags[t][key] = true
	}
}

func (c *TaggedCache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, exists := c.items[key]
	return val, exists
}

func (c *TaggedCache) InvalidateTag(tag string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if keys, found := c.tags[tag]; found {
		for key := range keys {
			delete(c.items, key)
		}
		delete(c.tags, tag)
	}
}

func main() {
	cache := NewTaggedCache()
	cache.Set("user_123_profile", "John Doe", []string{"users", "user_123"})
	cache.Set("user_123_settings", "Dark Mode", []string{"users", "user_123"})

	cache.InvalidateTag("user_123") // Invalidates both keys
	
	_, ok := cache.Get("user_123_profile")
	fmt.Println("Profile exists after invalidation:", ok)
}
```

### Invalidation Strategies in High-Concurrency Systems
When implementing tagged caching:
- **Lock Contention Mitigation:** Use partitioned mutex locks to prevent threads from blocking on unrelated keys.
- **Memory Pressure Handling:** Implement an LRU eviction policy to drop older tags when heap allocation approaches 80% limit.
- **Cache Penetration Prevention:** Use single-flight groups to coordinate database fetches when a high-traffic key is invalidated.
- **Event-Driven Eviction:** Connect the tagged cache invalidator directly to the in-memory event bus to flush entries automatically on record updates.

### Technical Appendix: Memory Profiling and Heap Allocation Tuning
Using in-memory caches requires monitoring to avoid Out-Of-Memory (OOM) crashes:
- Run Go's pprof tool (`go tool pprof`) periodically to analyze active heap objects.
- Use `sync.Pool` to reuse byte buffers and struct instances, reducing garbage collection sweep CPU cycles.
- Set a hard memory limit in Go using the `debug.SetMemoryLimit` API. This prevents container OOM termination by triggering aggressive garbage collection when the heap approaches the container's memory ceiling.




Thank you for joining the **Modular Monolith Architecture Playbook**. Apply this framework to your organization's next system design to gain the maximum advantage in speed and cost!

## 5. Architectural Breakdown Matrix of Bounded Context Case Studies

The table below summarizes the core architectural parameters and deployment strategies of prominent tech companies that leverage Modular Monoliths or consolidate microservices back into a single codebase.

| Company | Core Technology Stack | Peak Request Throughput | Primary Reason for Monolithic Strategy | Key Optimization Mechanism |
|---------|-----------------------|--------------------------|-----------------------------------------|----------------------------|
| **Stack Overflow** | IIS Web Servers, MS SQL, C# / .NET | 1.3 Billion page views/month | Extreme query speed and low latency limits | Extensive in-memory caching of tag indices, vertical hardware scaling |
| **Notion** | Node.js / Go, PostgreSQL | 100M+ active users | Database consistency and transaction speed | Custom application-level Postgres sharding, local cache caching |
| **Lyft** | Python, Go, Envoy Proxy | Tens of thousands of rides/sec | Organizational friction and debugging overhead | Consolidation of microservices into coarse-grained 'Macroservices' |
| **Segment** | Go, Docker, AWS ECS | Millions of events/second | Infrastructure cost overhead and container drift | Merging 140 destination workers into a single monolithic binary |

### Core Takeaways from Enterprise Restructuring Case Studies
Analyzing these architectures reveals that distributed system overhead is a physical bottleneck. When organizations transition from microservices to modular monoliths, they witness an immediate reduction in log ingestion volume, an elimination of cross-service connection overheads, and a return to simpler deployment validation cycles.

---

## Navigation & Next Steps

[← Previous Part]({{< ref "part-7-extraction-pattern.md" >}})

🔗 **Next Step:** This concludes the series. Review the full table of contents and curriculum mapping on the [Series Index Page]({{< ref "_index.md" >}})

Need help implementing this architecture in your organization? [Contact us](/contact/) or [hire our technical consulting team](/hire/) to review your system design and codebase.
