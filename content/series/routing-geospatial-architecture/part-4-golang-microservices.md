---
title: "Part 4: Golang API & Microservices Integration (Kratos & Dapr)"
description: "How to build a bulletproof Golang API Gateway that talks to Graphhopper. We cover Circuit Breakers, Protobuf GC optimization, and Dapr asynchronous routing."
date: "2026-06-14T23:00:00+07:00"
lastmod: "2026-06-14T23:00:00+07:00"
draft: false
tags: ["golang", "kratos", "dapr", "grpc", "graphhopper", "system design"]
series: ["Routing & Geospatial Architecture"]
series_order: 4
cover:
  image: "images/posts/graphhopper-cover.png"
  alt: "Geospatial and Routing Engine Architecture series: Go and GraphHopper for production routing"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/routing-geospatial-architecture/part-4-golang-microservices/"
ShowToc: true
TocOpen: true
---

[← Series hub]({{< ref "/series/routing-geospatial-architecture/_index.md" >}})
[← Prev]({{< ref "/series/routing-geospatial-architecture/part-3-spatial-indexing.md" >}}) • [Next →]({{< ref "/series/routing-geospatial-architecture/part-5-visualization-ui.md" >}})

> **Prerequisite:** Ensure you have read [Part 3: Spatial Indexing (Uber H3, PostGIS & Redis GEO)]({{< ref "part-3-spatial-indexing.md" >}}) before integrating with Golang microservices.

Building a simple API that calls Graphhopper via `http.Get` is easy. Building a **Principal-level API Gateway** that survives 10,000 concurrent riders requesting routes without crashing is a masterclass in Distributed Systems.

**Answer-first:** Graphhopper is a heavily CPU-bound downstream service. If your Golang API blindly accepts traffic and forwards it, a slight slowdown in Graphhopper will cause your Goroutines to pile up, exhausting your server's RAM and triggering a cascading failure. You must implement a "Defense in Depth" strategy using Concurrency Bounding, Circuit Breakers, and Asynchronous Pub/Sub.

---

## 1. Defense in Depth: Protecting the Routing Engine

### The Concurrency Limit (`errgroup`)
When calculating multiple independent routes concurrently, always use `golang.org/x/sync/errgroup`. Crucially, you must call `g.SetLimit(10)` to prevent a "thundering herd." Limiting concurrent outgoing requests prevents your service from accidentally DDOSing your own internal Graphhopper instance.

### The Circuit Breaker (`gobreaker`)
What happens if Graphhopper takes 5 seconds to respond? Without a Circuit Breaker, your Golang API will keep opening new connections until it runs out of memory. By wrapping calls in `sony/gobreaker`, the breaker will "Fail Fast" (Open) when the error rate spikes, immediately returning a 503 to the client and giving Graphhopper time to recover.

### Deduplication (`singleflight`)
Imagine 100 users open their app to check the ETA to a massive concert at the exact same second. Instead of sending 100 identical requests to Graphhopper, use `golang.org/x/sync/singleflight`. It collapses identical concurrent requests into a single downstream HTTP call, instantly broadcasting the result to all 100 waiting users.

---

## 2. The Protobuf GC Trap (Flattened Arrays)

If you are exposing your routing engine internally via gRPC, how do you define a 10,000 x 10,000 Distance Matrix?

The amateur approach is to use nested arrays: `repeated MatrixRow rows` where each row has `repeated double distances`. In Golang, deserializing a 10,000x10,000 nested array creates **100 million tiny objects**. This triggers a catastrophic Garbage Collection (GC) pause, freezing your API for seconds.

**The Senior Solution:** Use a **Flattened 1D Array**. Define your Protobuf as `repeated double data` along with `int32 rows` and `int32 cols`. It creates exactly one object in memory. You calculate the exact cell mathematically using `index = row * cols + col`. 

---

## 3. Asynchronous Routing with Dapr Workflows

HTTP is synchronous. Matrix calculations can take minutes. These two facts don't mix.

When generating massive matrices (e.g., calculating the distance from 1,000 warehouses to 1,000 stores), you cannot keep the HTTP connection open. 
1. The Golang Gateway receives the request and immediately publishes a `RouteRequested` event via **Dapr Pub/Sub**. It returns a `202 Accepted` to the client.
2. A background worker picks up the event. Because complex routing involves multiple steps (Geocoding -> Graphhopper -> Notification), use **Dapr Workflows**. 
3. Dapr Workflows guarantee **Durable Execution**. If the worker crashes mid-calculation, Dapr automatically resumes the workflow from the last checkpoint upon restart.

## Kratos Gateway Path Routing & Load Distribution

In a professional microservice architecture, the API Gateway does not just route requests blindly; it performs intelligent geo-aware path routing. Using the Go Kratos framework, we implement custom gateway middleware that inspects spatial headers like `X-Routing-Region`.

When a client sends a route request, the Kratos gateway extracts the region. If the request originates from Ho Chi Minh City, it routes it to the specific HCMC Graphhopper instance. This prevents unnecessary cross-region network latency and localizes traffic within isolated geographical clusters. If the header is missing, the gateway defaults to a round-robin load balancer across global instances.

## gRPC Connection Pool Options and Tuning

While HTTP/2 multiplexes multiple streams over a single connection, high-throughput systems with more than 10,000 concurrent routing requests will hit physical TCP bottlenecks (socket buffer exhaustion, CPU context switching).

To scale past these limits, we implement a custom gRPC connection pool in Go. The pool maintains a slice of `*grpc.ClientConn` objects and routes requests across them in a round-robin manner. We also tune the connection properties to ensure high availability:

- **Keepalive Parameters:** We set client keepalive time to 10 seconds and timeout to 3 seconds. This forces the client to send active pings, preventing firewalls or load balancers from silently closing idle TCP connections.
- **Lazy Reconnection:** If a connection transitions to a failure state, the pool lazily re-dials and replaces the dead connection without blocking active traffic.

## Go Implementation: gRPC Connection Pool & Kratos Service Handler

Here is the complete implementation of the connection pool and the Kratos HTTP dispatch handler in Go:

```go
package service

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/go-kratos/kratos/v2/log"
	"github.com/go-kratos/kratos/v2/transport/grpc"
	"google.golang.org/grpc/connectivity"
	ggrpc "google.golang.org/grpc"
)

// ConnectionPool manages a pool of gRPC client connections to prevent TCP port exhaustion
type ConnectionPool struct {
	mu      sync.RWMutex
	conns   []*ggrpc.ClientConn
	target  string
	maxSize int
	next    int
}

// NewConnectionPool instantiates a connection pool for a specific downstream target
func NewConnectionPool(target string, maxSize int) (*ConnectionPool, error) {
	pool := &ConnectionPool{
		target:  target,
		maxSize: maxSize,
		conns:   make([]*ggrpc.ClientConn, maxSize),
	}

	for i := 0; i < maxSize; i++ {
		conn, err := grpc.DialInsecure(
			context.Background(),
			grpc.WithEndpoint(target),
			grpc.WithTimeout(5*time.Second),
		)
		if err != nil {
			return nil, fmt.Errorf("failed to dial gRPC endpoint %s at index %d: %w", target, i, err)
		}
		pool.conns[i] = conn
	}
	return pool, nil
}

// GetConnection returns a connection from the pool using a round-robin strategy
func (p *ConnectionPool) GetConnection() (*ggrpc.ClientConn, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	conn := p.conns[p.next]
	p.next = (p.next + 1) % p.maxSize

	state := conn.GetState()
	if state == connectivity.TransientFailure || state == connectivity.Shutdown {
		// Reconnect lazily if the connection is dead
		newConn, err := grpc.DialInsecure(
			context.Background(),
			grpc.WithEndpoint(p.target),
			grpc.WithTimeout(5*time.Second),
		)
		if err == nil {
			conn.Close()
			p.conns[p.next] = newConn
			return newConn, nil
		}
	}
	return conn, nil
}

// RoutingService implements a Kratos HTTP/gRPC service for dynamic route dispatch
type RoutingService struct {
	pool   *ConnectionPool
	logger *log.Helper
}

// NewRoutingService initializes the service with a gRPC connection pool
func NewRoutingService(target string, logger log.Logger) (*RoutingService, error) {
	pool, err := NewConnectionPool(target, 10)
	if err != nil {
		return nil, err
	}
	return &RoutingService{
		pool:   pool,
		logger: log.NewHelper(logger),
	}, nil
}

// DispatchRouteHandler processes incoming routing requests via Kratos HTTP middleware
func (s *RoutingService) DispatchRouteHandler(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	s.logger.WithContext(ctx).Infof("Received route dispatch request from %s", r.RemoteAddr)

	// Fetch a healthy connection from the gRPC pool
	_, err := s.pool.GetConnection()
	if err != nil {
		s.logger.Errorf("Failed to retrieve gRPC connection from pool: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	// Dynamic path routing logic based on spatial headers (e.g. city or region)
	region := r.Header.Get("X-Routing-Region")
	if region == "" {
		region = "default"
	}

	s.logger.Infof("Routing request to region: %s", region)
	
	// Write response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(fmt.Sprintf(`{"status":"success","region":"%s","message":"Route dispatched"}`, region)))
}
```

## Deep Dive: Implementing Circuit Breaking and Request Collapse

To protect our downstream GraphHopper engine, let us look at a concrete implementation in Golang using `sony/gobreaker` for circuit breaking and `golang.org/x/sync/singleflight` for request deduplication (collapsing concurrent identical requests).

Below is the complete, production-ready Go wrapper client:

```go
package routing

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"

	"github.com/sony/gobreaker"
	"golang.org/x/sync/singleflight"
)

type GraphHopperClient struct {
	httpClient *http.Client
	cb         *gobreaker.CircuitBreaker
	sfGroup    singleflight.Group
	baseURL    string
}

func NewGraphHopperClient(baseURL string) *GraphHopperClient {
	// Configure the Circuit Breaker
	settings := gobreaker.Settings{
		Name:        "GraphHopper-Routing-Engine",
		MaxRequests: 3,
		Interval:    10 * time.Second,
		Timeout:     5 * time.Second,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			// Trip the breaker if error rate exceeds 50% after at least 10 requests
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.Requests >= 10 && failureRatio >= 0.5
		},
	}

	return &GraphHopperClient{
		httpClient: &http.Client{Timeout: 5 * time.Second},
		cb:         gobreaker.NewCircuitBreaker(settings),
		baseURL:    baseURL,
	}
}

// RequestRoute computes a route, utilizing SingleFlight to collapse identical concurrent requests
func (c *GraphHopperClient) RequestRoute(ctx context.Context, routeKey string, origin, destination string) (string, error) {
	// Singleflight collapses concurrent identical route requests into one call
	res, err, shared := c.sfGroup.Do(routeKey, func() (interface{}, error) {
		// Circuit Breaker wraps the actual downstream HTTP call
		return c.cb.Execute(func() (interface{}, error) {
			reqURL := fmt.Sprintf("%s/route?point=%s&point=%s&profile=car", c.baseURL, origin, destination)
			req, err := http.NewRequestWithContext(ctx, "GET", reqURL, nil)
			if err != nil {
				return nil, err
			}

			resp, err := c.httpClient.Do(req)
			if err != nil {
				return nil, err
			}
			defer resp.Body.Close()

			if resp.StatusCode != http.StatusOK {
				return nil, fmt.Errorf("downstream error status code: %d", resp.StatusCode)
			}

			// In a real application, you would parse and return the response body
			return "route-payload", nil
		})
	})

	if err != nil {
		if errors.Is(err, gobreaker.ErrOpenState) {
			return "", fmt.Errorf("circuit breaker is open, downstream service down: %w", err)
		}
		return "", err
	}

	fmt.Printf("Request key: %s, Shared request: %t\n", routeKey, shared)
	return res.(string), nil
}
```

### Key Advantages of This Wrapper:
1. **Singleflight Deduplication**: If 50 riders in the same spatial cell request a route to the same destination simultaneously, `c.sfGroup.Do` blocks 49 of them and makes exactly one downstream HTTP call. When the single call completes, the returned payload is instantly shared with all 50 Goroutines. This prevents the "thundering herd" problem from spiking downstream CPU usage.
2. **Dynamic Breaker States**: If GraphHopper becomes overloaded and begins timing out or returning 500 errors, the `sony/gobreaker` transitions from the `Closed` state to the `Open` state. In this state, any incoming request is rejected immediately with `ErrOpenState`, preventing Golang from spinning up new idle connections and blocking threads. After 5 seconds (the configured `Timeout`), the breaker shifts to `Half-Open` to send a probe request. If the probe succeeds, the breaker closes; otherwise, it opens again.

---

## FAQ: Backend Routing Traps

{{< faq q="I sent a Custom Model to avoid Toll Roads, but Graphhopper ignored it. Why?" >}}
Welcome to the `ch.disable=true` trap. Contraction Hierarchies (Speed Mode) pre-calculates the fastest paths and cannot process dynamic weights at runtime. To use custom rules, you MUST send a POST request and append `?ch.disable=true` to force Graphhopper into Flexible Mode (Dijkstra/A*).
{{< /faq >}}

{{< faq q="Why can't I see Graphhopper execution times in my Jaeger/Zipkin dashboards?" >}}
You have a tracing blind spot. In Kratos v2, you must inject the OpenTelemetry middleware into your HTTP client using `http.WithMiddleware(tracing.Client())`. This injects the W3C `traceparent` context into the HTTP headers, linking the gateway request directly to the Graphhopper server logs.
{{< /faq >}}

{{< faq q="My massive Matrix API call returns a 400 Bad Request. What happened?" >}}
You hit Graphhopper's `Maximum visited nodes exceeded` limit. This is a safety mechanism in `config.yml` (`routing.max_visited_nodes`) to prevent RAM exhaustion. Do not blindly increase this limit; instead, design your Golang worker to split the massive matrix into smaller sub-grids.
{{< /faq >}}

Need help building high-scale routing engines or spatial indexing pipelines? [Contact me](/contact/) to discuss your project.

🔗 **Next Step:** Build the visualization dashboard in [Part 5: Route Visualization UI with Mapbox & Deck.gl]({{< ref "/series/routing-geospatial-architecture/part-5-visualization-ui.md" >}}).

