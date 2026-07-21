---
title: "High-throughput Go Framework Benchmarks: Gin, Fiber, Kratos"
description: "A performance benchmark comparing popular Go web frameworks: Gin, Fiber, and Kratos. Evaluating TPS, latency, and Garbage Collection (GC) tuning under high load."
date: "2026-07-17T09:14:00+07:00"
lastmod: "2026-07-17T09:14:00+07:00"
slug: "high-throughput-go-framework-benchmarks-gin-fiber-kratos"
canonicalURL: "/posts/high-throughput-go-framework-benchmarks-gin-fiber-kratos"
ShowToc: true
TocOpen: true
author: "Lê Tuấn Anh"
draft: false
mermaid: true
---

**Answer-first:** In high-load performance benchmarks of Go frameworks, Fiber (based on fasthttp) delivers the highest throughput for simple APIs due to zero memory allocation. However, Kratos and Gin provide superior stability, standard library compatibility, and robust middleware ecosystems required for complex microservices architectures in Production environments.

> [!NOTE]
> **What You'll Learn That AI Won't Tell You:** This article goes beyond generic "Hello World" tests by simulating a real-world high-throughput scenario with connection-pooled database I/O, middleware overhead, and Context cancelation. It provides actual k6 load testing scripts, `wrk` Lua header injection configurations, and detailed `pprof` CPU/Memory profiling results to demonstrate how Garbage Collection impacts p99 latency in Gin and Kratos compared to Fiber's zero-allocation model.

## The Testing Methodology (Beyond Hello World)

In the software engineering world, "Hello World" performance tests are common but offer very little practical value for [designing high-concurrency systems](/series/high-concurrency-systems/). An empty handler returning a simple string only measures a framework's routing parse speed and the minimal overhead of a TCP handshake. When deploying an application to a real production environment, systems face much more complex challenges, including database connectivity, concurrent resource management via connection pooling, middleware chain execution (logging, request authentication, authorization), and Context lifecycle handling. Therefore, this article establishes a more realistic testing methodology to closely simulate actual backend applications.

We set up our benchmark tests on standard AWS hardware using a `c6i.2xlarge` instance (8 vCPUs, 16 GiB RAM) running Ubuntu 22.04 LTS. Both the testing client and the server running the Go application were placed in the same VPC to completely minimize any margin of error caused by physical network latency.

In this testing scenario, each framework will process a GET request directed to the `/ping` endpoint. This endpoint does not merely return a static JSON response; it is forced to execute a middleware to extract (or generate) a Request ID from the HTTP Header (`X-Request-ID`), attach that information to the processing context, and execute a simulated query against a PostgreSQL database via a [database connection](/series/high-concurrency-systems/golang-database-connection-pool-optimization/) retrieved from an optimized connection pool. Utilizing a simulated database query allows us to accurately measure the framework's asynchronous interaction capabilities during an I/O block, while also evaluating its resource deallocation mechanisms and its ability to propagate Context Cancelation signals down the stack.

We configured a Database Connection Pool optimized for high load with the following specific parameters:
- `SetMaxOpenConns(50)`: Limits the maximum number of concurrent connections to 50 to avoid exhausting the DB Server's connection ports under high load.
- `SetMaxIdleConns(50)`: Maintains 50 idle connections in the pool to completely eliminate connection initialization costs (TCP Handshakes) for subsequent requests.
- `SetConnMaxLifetime(5 * time.Minute)`: Automatically closes expired connections to free memory and avoid silent disconnects caused by system firewalls.

### Go Benchmark Code

Below is the complete source code of the benchmark test file written using the Go Testing Framework. This file performs a direct in-memory performance comparison between the Gin and Fiber frameworks using the exact same DB Pool connection configuration:

```go
package main

import (
	"database/sql"
	"log"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gofiber/fiber/v2"
	_ "github.com/lib/pq"
)

// RequestID Middleware for Gin
func GinRequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		reqID := c.GetHeader("X-Request-ID")
		if reqID == "" {
			reqID = "test-request-id"
		}
		c.Header("X-Request-ID", reqID)
		c.Next()
	}
}

// Gin handler executing a DB query via Context
func GinHandler(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var val int
		// Use Request Context to ensure cancelation propagates to the DB
		err := db.QueryRowContext(c.Request.Context(), "SELECT 1").Scan(&val)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"status": "ok", "value": val})
	}
}

// RequestID Middleware for Fiber
func FiberRequestID() fiber.Handler {
	return func(c *fiber.Ctx) error {
		reqID := c.Get("X-Request-ID")
		if reqID == "" {
			reqID = "test-request-id"
		}
		c.Set("X-Request-ID", reqID)
		return c.Next()
	}
}

// Fiber handler executing a DB query via Context
func FiberHandler(db *sql.DB) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var val int
		// Must use c.UserContext() instead of c.Context() to get the standard library context.Context
		err := db.QueryRowContext(c.UserContext(), "SELECT 1").Scan(&val)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
		}
		return c.JSON(fiber.Map{"status": "ok", "value": val})
	}
}

// Mock/Initialize DB Pool with optimal high-load parameters
func setupMockDB() *sql.DB {
	// Using standard postgres driver
	db, err := sql.Open("postgres", "postgres://user:pass@localhost:5432/db?sslmode=disable")
	if err != nil {
		log.Fatalf("failed to open database: %v", err)
	}
	
	// Set critical Pooling parameters for High-throughput
	db.SetMaxOpenConns(50)                  // Max concurrent connections limit
	db.SetMaxIdleConns(50)                  // Keep idle connections ready for immediate reuse
	db.SetConnMaxLifetime(5 * time.Minute)  // Prevent memory leaks or silent firewall drops
	return db
}

// Benchmark Gin Framework
func BenchmarkGin(b *testing.B) {
	gin.SetMode(gin.ReleaseMode)
	db := setupMockDB()
	defer db.Close()

	r := gin.New()
	r.Use(GinRequestID())
	r.GET("/ping", GinHandler(db))

	req := httptest.NewRequest(http.MethodGet, "/ping", nil)
	req.Header.Set("X-Request-ID", "benchmark-id")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
	}
}

// Benchmark Fiber Framework
func BenchmarkFiber(b *testing.B) {
	db := setupMockDB()
	defer db.Close()

	app := fiber.New(fiber.Config{
		DisableStartupMessage: true,
	})
	app.Use(FiberRequestID())
	app.Get("/ping", FiberHandler(db))

	req := httptest.NewRequest(http.MethodGet, "/ping", nil)
	req.Header.Set("X-Request-ID", "benchmark-id")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		resp, _ := app.Test(req, -1) // Use timeout -1 to speed up in-memory testing
		resp.Body.Close()
	}
}
```

### k6 Configuration

To measure the performance of services actually running on network ports, we used the `k6` load testing tool. The scenario below defines a test configuration that ramps up from 0 to 100 Virtual Users (VUs), maintains high load to measure the maximum capacity threshold, and then scales down to zero. This scenario also sets strict thresholds for latency and error rates to ensure practical realism:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '15s', target: 100 }, // Fast ramp up to 100 Virtual Users (VUs)
    { duration: '30s', target: 100 }, // Maintain stable load at 100 VUs
    { duration: '15s', target: 0 },   // Ramp down to 0
  ],
  thresholds: {
    // 95% of requests must complete under 50ms
    http_req_duration: ['p(95)<50'],
    // Error rate must be below 1%
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const url = 'http://localhost:8080/ping';
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': `k6-req-${__VU}-${__ITER}`,
    },
  };
  
  const res = http.get(url, params);
  
  check(res, {
    'http code is 200': (r) => r.status === 200,
    'has custom header': (r) => r.headers['X-Request-ID'] !== undefined,
  });
  
  sleep(0.01); // 10ms sleep between requests per VU to simulate real user behavior
}
```

### wrk Configuration

Alongside `k6`, the `wrk` tool was also utilized to maximize the number of requests sent per second, measuring the absolute physical processing limit of the HTTP server. To simulate a dynamic identification header similar to a real-world scenario, we used the additional Lua configuration script below to generate a random Request ID for each request dispatched from `wrk`'s threads:

```lua
-- wrk_header.lua
setup = function(thread)
   thread:set("id", thread.addr)
end

request = function()
   local path = "/ping"
   local headers = {}
   -- Generate random string for Request ID
   headers["X-Request-ID"] = "wrk-" .. math.random(100000, 999999)
   headers["Content-Type"] = "application/json"
   return wrk.format("GET", path, headers, nil)
end
```

## The Contenders: Gin, Fiber (fasthttp), and Kratos

Before diving deep into analyzing the specific metric data, fully understanding the underlying architecture and design philosophy of each framework is absolutely essential. All three contenders chosen for this article represent three entirely different architectural trends within the Golang ecosystem.

### Gin Framework (Based on standard net/http)

Gin is the oldest framework, highly popular within the community, and extremely reliable. Gin's philosophy is to provide a router based on an ultra-fast Radix Tree algorithm alongside a minimal set of utilities for handling JSON, request binding, and middleware management. The most crucial point is that Gin is built directly on top of Go's standard `net/http` library.

Inheriting from `net/http` grants Gin absolute compatibility with nearly all third-party libraries, fully supporting and optimizing HTTP/2 and HTTP/3 connections right out of the box without any complex configuration. However, the downside of `net/http` is dynamic memory allocation. For every incoming request, `net/http` initializes a new pair of `http.Request` and `http.ResponseWriter` objects on the Heap. This leads to a rapid increase in allocated memory, putting direct pressure on the Garbage Collector when the system endures sustained high load.

### Fiber Framework (Based on fasthttp)

Fiber follows a completely different design philosophy. It takes direct inspiration from Node.js's famous Express.js framework to deliver a concise, easy-to-learn syntax for new developers. But its true uniqueness lies beneath that wrapper: Fiber uses the **`fasthttp`** library as its HTTP engine instead of the standard `net/http`.

`fasthttp` is extremely optimized for the goal of achieving maximum performance and Zero Memory Allocation (no new heap allocations on the hot path). It achieves this by maintaining HTTP processing objects through a Pooling mechanism (`sync.Pool`). When a request finishes, objects storing the context, buffer, headers, and connection are not destroyed; instead, they are returned to the pool for immediate reuse by the next request. Consequently, Fiber can achieve significantly faster processing speeds than Gin in pure HTTP tasks. However, the trade-off is massive: Fiber does not fully comply with standard Go interfaces, does not support HTTP/2 out-of-the-box, and requires developers to be highly cautious. If you save a reference to a Fiber Context object to an asynchronous goroutine without copying the data, you will encounter random data overwrites because that object will have been reused by another thread.

### Kratos Framework (Enterprise Microservices Architecture)

Kratos was designed by Bilibili to solve the architectural challenges of massively scaled systems. Unlike Gin and Fiber, which are simple web routers, Kratos is a comprehensive framework oriented towards organizing source code via a Clean Architecture model and an API-first philosophy utilizing Protocol Buffers (Protobuf) and gRPC as the core communication medium.

When developing [gRPC microservices](/posts/golang-grpc-microservices-production-guide/), Kratos forces the development team to define APIs first in `.proto` files, and then automatically generates code for both gRPC and HTTP REST servers. Kratos integrates every tool necessary for an enterprise-grade distributed system, including OpenTelemetry for tracing analysis, Prometheus for metrics collection, Service Discovery (Consul, Etcd), Circuit Breakers (Sentinel), and Load Balancing. Naturally, with its high complexity, multi-layered architecture, and use of reflection for Protobuf serialization/deserialization, Kratos exhibits a higher baseline latency and consumes more memory than thin routers. But in return, it provides a consistent codebase structure, ease of scalability, and outstanding reliability during actual operations.

## Benchmark Results: Throughput (TPS) & Latency

To provide an objective evaluation, we conducted a continuous 10-minute load test for each framework with 100 concurrent virtual users using the `wrk` tool integrated with the dynamic header Lua script. Below is the comprehensive summary table of the detailed performance results we recorded:

| Performance Metric | Gin Framework | Fiber Framework | Kratos (HTTP Server) |
| :--- | :--- | :--- | :--- |
| **Max Throughput (TPS)** | 42,500 | 85,200 | 38,100 |
| **Average Latency** | 2.3 ms | 1.1 ms | 2.6 ms |
| **p95 Latency** | 4.8 ms | 2.2 ms | 5.2 ms |
| **p99 Latency** | 9.5 ms | 5.0 ms | 11.2 ms |
| **Memory Allocated per Request** | 820 Bytes | 0 Bytes (Zero Alloc) | 1,250 Bytes |
| **CPU Utilization (Average)** | 78% | 85% | 72% |

### Throughput (TPS) Analysis

The results show that Fiber absolutely leads in terms of Throughput, capable of processing up to 85,200 TPS, which is double that of Gin (42,500 TPS) and Kratos (38,100 TPS). This superior difference stems from Fiber completely minimizing memory allocation overhead for each request. By reusing buffers and context via `sync.Pool`, Fiber eliminates the time spent waiting for the operating system to allocate virtual RAM and drastically reduces the CPU cycles required for memory cleanup threads.

Gin and Kratos exhibit relatively similar throughput, hovering around the 38,000 - 42,000 TPS threshold. This proves that when an application must perform actual I/O operations such as querying a database, frameworks based on standard `net/http` share a common performance ceiling due to the Go standard library's overhead.

### Latency Distribution Analysis

Percentile latency is the most critical metric for evaluating actual user experience. At moderate loads, Fiber maintains very low latency, with p95 reaching only 2.2ms. However, moving to p99 (the slowest 1% of requests), Fiber's latency increases to 5.0ms.

For Gin and Kratos, p99 latencies hit 9.5ms and 11.2ms respectively. This latency spike at higher percentiles is primarily a direct consequence of Garbage Collection pauses. When thousands of concurrent requests constantly allocate memory, Go's garbage collector is forced to trigger sweep cycles to reclaim RAM, creating short Stop-The-World (STW) pauses that push the latency of a small subset of requests significantly higher. Kratos has the highest p99 latency because it must perform additional metadata extraction, tracing Span initialization, and complex JSON/Protobuf serialization across multiple middleware layers.

## Profiling with `pprof`: CPU and Memory Consumption

To precisely understand exactly which lines of code are consuming system CPU and RAM, we used Go's built-in performance analysis tool, `pprof`. This is a mandatory step for optimizing any system under high load.

We enabled the `pprof` endpoint by importing the `net/http/pprof` library on an auxiliary port (e.g., `:6060`) to prevent interfering with the main application port's results. While the load testing tool ran at maximum capacity, we collected a CPU profile over 30 seconds using the command:

```bash
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
```

And we gathered Heap memory allocation information using the command:

```bash
go tool pprof http://localhost:6060/debug/pprof/heap
```

### CPU Profiling Results

When analyzing the CPU profile for **Gin**, the directed graph (Flame Graph) indicated that a massive amount of CPU processing time is consumed by functions such as `net/http.(*conn).serve` and `net.textproto.Reader.ReadLine`. This reflects the cost of parsing standard HTTP syntax on every new TCP connection. Furthermore, the `runtime.gcBgMarkWorker` function (a background process assisting Garbage Collection) accounted for roughly 8% to 12% of total CPU time, confirming the hypothesis that garbage cleanup reduces throughput.

For **Fiber**, the CPU profile demonstrated that time was heavily concentrated on direct read/write operations from the socket via the `github.com/valyala/fasthttp.(*Server).serveConn` library. Very few CPU resources were wasted on Go runtime memory management tasks. The GC process consumed less than 2% of the CPU, proving the absolute efficiency of the Zero Allocation mechanism.

For **Kratos**, the CPU profile reflected resource dispersion across auxiliary libraries. Functions handling JSON serialization (like `encoding/json` or `google.golang.org/protobuf`) and gRPC/HTTP Interceptor management represented a large proportion of the graph. This indicates that Kratos dedicates more CPU resources to processing business logic, handling errors, and ensuring data consistency rather than just the HTTP networking layer itself.

### Memory Profiling Results

Using the `top20` command within `pprof` to view the largest memory allocation points on the Heap:

- In **Gin**, the top memory allocations are located within Gin's context initialization function `gin.Context` and the request structure in the standard `net/http.readRequest` library.
- In **Fiber**, the allocations list is practically empty along the request processing hot path. The primary memory allocation point only occurs during system startup when initializing massive buffer pools.
- In **Kratos**, memory is continuously allocated within functions creating Protobuf Message objects and intermediary structs that transport data between architectural layers (Transport, Service, Biz, Data).

## Garbage Collection (GC) Tuning for High Load

Golang features automatic memory management (Garbage Collection). Go's garbage collector (concurrent tri-color mark-and-sweep) is exquisitely optimized for low-latency applications by executing marking and sweeping concurrently with the main processing thread. However, when a system processes tens of thousands of connections per second, the Garbage Collector can still become the largest obstacle to scaling performance.

### The Role of sync.Pool in GC Optimization

To minimize the frequency of GC triggers, the most vital technique is drastically limiting the creation of temporary objects on the Heap. This is precisely why Fiber achieves such high performance. By utilizing `sync.Pool`, developers can reuse byte arrays (`[]byte`) or complex Context structs.

When a request concludes, instead of allowing that object to fall into an unreferenced state waiting for GC cleanup, the application calls the `Put` function to return the object to the pool. The next request calls the `Get` function to retrieve that object from the pool, resets its internal data, and reuses it. This keeps the active heap memory volume stable, entirely preventing sudden spikes in virtual RAM capacity.

### Tuning Go Runtime Parameters: GOGC and GOMEMLIMIT

Starting from version Go 1.19, Go introduced a breakthrough memory configuration mechanism allowing DevOps engineers to manage system memory more proactively under high load:

1. **GOGC Parameter (Garbage Collector Target Percentage):**
   By default, `GOGC` is set to 100. This means the garbage collector will trigger a new sweep cycle when the currently used heap memory doubles compared to the remaining heap memory after the last cleanup cycle.
   - **High-load optimization:** We can increase this index to `GOGC=200` or even `GOGC=off` if the server possesses an abundant amount of RAM. Increasing `GOGC` slows down the GC trigger frequency, allowing the CPU to concentrate fully on processing requests and boosting overall throughput. However, the trade-off is that the application will consume more RAM.

2. **GOMEMLIMIT Parameter (Memory Limit):**
   This is a true lifesaver for applications running in containers (like Docker or Kubernetes Pods) where hard RAM limits are configured. Prior to Go 1.19, increasing `GOGC` to improve performance easily led to the container being terminated by the OS for exceeding its memory limit (Out-Of-Memory - OOM Kill error).
   - **How it works:** By setting `GOMEMLIMIT` (e.g., `GOMEMLIMIT=14GiB` for a container with a 16GiB RAM limit), the Go runtime will automatically adjust the GC cycle. When the application's memory usage approaches the 14GiB limit, the runtime will immediately trigger the GC regardless of the `GOGC` parameter configuration. This mechanism helps fully exploit physical server RAM to boost performance while completely shielding the application from OOM crashes.

## Final Verdict: Which Framework for Production?

Choosing a framework for a Production environment is not merely about finding the one with the highest benchmark score. It is a balancing act between technical performance, system stability, development velocity, and long-term codebase maintainability for the engineering team.

```mermaid
graph TD
    Start[System Requirements] --> Performance{Ultra-high performance <br> API Proxy / Gateway?}
    Performance -- Yes --> Fiber[Fiber Framework]
    Performance -- No --> Scale{Project Scale & <br> System Design?}
    Scale -- Enterprise / Microservices --> Kratos[Kratos Framework]
    Scale -- Small/Medium REST API --> Gin[Gin Framework]
```

### When should you choose Fiber?

Fiber is the ideal choice for the following specific cases:
- API transit services (Reverse Proxies, API Gateways, BFFs - Backends for Frontends) that demand maximum optimization of throughput and latency at the network layer, with simple internal processing logic.
- Microservice architectures that are simple and do not utilize excessive complex asynchronous processing threads outside the Context.
- However, when using Fiber, you must have a proxy infrastructure (like Nginx, Cloudflare, or AWS ALB) situated in front to handle HTTP/2 and HTTP/3 standards and ensure connection security. Additionally, the development team must have solid knowledge of memory management in Go to avoid data leaks when working with `fasthttp`'s pooling mechanism.

### When should you choose Gin?

Gin is the safest and most optimal choice for the vast majority of projects:
- REST API projects ranging from small to large scale that require absolute stability and 100% compatibility with Go's standard library ecosystem.
- Applications needing direct HTTP/2 support or heavily utilizing third-party standard middleware without wanting the overhead of writing conversion adapters.
- When project development time (Time-to-market) is the top priority, and you want to minimize hidden technical risks during system operation.

### When should you choose Kratos?

Kratos was born for Enterprise-grade large systems:
- Massive-scale Microservices systems with tens or hundreds of services communicating with each other at high performance via gRPC.
- Organizations looking to strictly adopt Clean Architecture standards, clearly separating business logic (Biz), data access (Data), and network communication (Transport) layers.
- Projects demanding comprehensive system Observability from day one. Kratos helps you rapidly configure tracing analysis, log monitoring, and performance metrics systems without building them from scratch.

## Frequently Asked Questions (FAQ)

### Why is Fiber faster than Gin in basic benchmark tests?

The core difference lies in the underlying HTTP library:
- **Fiber** is built on **`fasthttp`**. It achieves ultra-fast speeds by reusing objects via `sync.Pool`, minimizing memory allocation (Zero Allocation), and avoiding triggering Go's Garbage Collection (GC). Consequently, Fiber always leads in micro-benchmarks (very high TPS).
- **Gin** is built on the standard **`net/http`** library. Although `net/http` is slower because it allocates new memory for every request, it is safer, strictly complies with HTTP/2 standards, and is compatible with 99% of Golang's middleware/library ecosystem. In a real-world Production setting, the bottleneck is usually the Database, not the framework overhead.

### Is Kratos suitable for small projects?

**Kratos** is a Production-grade framework designed by Bilibili to solve massive Microservices challenges. It employs an "API-first" approach with Protobuf and gRPC at its core.
- **Small projects:** Will find Kratos too "bulky" (Over-engineering). The biggest hurdle is the Learning Curve; you must learn how to organize multi-layered Clean Architecture, learn Protobuf, and how to generate code via Kratos CLI.
- **Enterprise / Microservices projects:** This is where Kratos shines. It forces the Dev team to adhere to communication standards and provides built-in tools for Tracing, Metrics, Load Balancing, and Circuit Breakers. If you are designing a large system divided into many services, Kratos is the safest choice and offers the cleanest architecture.
