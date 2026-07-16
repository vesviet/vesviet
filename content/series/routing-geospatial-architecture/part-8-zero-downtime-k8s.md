---
title: "Part 8: Zero-Downtime Map Updates & Multi-Region Kubernetes"
description: "The Grand Finale. How to deploy a Stateful Routing Engine to Kubernetes with Argo Rollouts, Geo DNS, and survive OOMKilled and 502 Bad Gateway errors."
date: "2026-06-15T19:30:00+07:00"
lastmod: "2026-06-15T19:30:00+07:00"
draft: false
tags: ["kubernetes", "devops", "sre", "graphhopper", "argo-rollouts", "system design"]
series: ["Routing & Geospatial Architecture"]
series_order: 8
cover:
  image: "images/posts/graphhopper-cover.png"
  alt: "Geospatial and Routing Engine Architecture series: Go and GraphHopper for production routing"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/routing-geospatial-architecture/part-8-zero-downtime-k8s/"
ShowToc: true
TocOpen: true
---

[← Series hub]({{< ref "/series/routing-geospatial-architecture/_index.md" >}})
[← Prev]({{< ref "/series/routing-geospatial-architecture/part-7-load-testing-production.md" >}})

> **Prerequisite:** This final part requires the optimizations from [Part 7: Load Testing and Performance Tuning for Production]({{< ref "part-7-load-testing-production.md" >}}) to successfully deploy to Kubernetes.

Writing a fast algorithm is only half the battle. The true test of a Principal Engineer is deploying a massive, stateful Routing Engine to the Cloud without causing a single second of downtime during map updates or infrastructure failures. 

**Answer-first:** You cannot treat Graphhopper like a stateless web server. Updating the OpenStreetMap data takes 30 minutes of heavy computation. You MUST decouple the map build process using Kubernetes Jobs, inject the pre-computed 50GB cache via `initContainers`, and switch traffic instantly using Blue-Green Deployments.

---

## 1. The Zero-Downtime Deployment Strategy

### Decoupling the Build from the Server
If you run the graph generation script inside your live serving Pods, you guarantee 30 minutes of downtime every time the map updates. 
**The Fix:** Use a Kubernetes Job (or CI pipeline) to download the new `.pbf` file and generate the `graph-cache` entirely offline. Upload the resulting 50GB cache folder to an AWS S3 bucket.

### InitContainers & Blue-Green Deployments
When deploying the new version, you cannot use standard Kubernetes Rolling Updates. A Rolling Update will cause a "Split-Brain" scenario where 50% of your pods route on the old map and 50% on the new map, completely destroying your Redis Semantic Cache Hit Rate.
**The Fix:** Use **Argo Rollouts** for a Blue-Green deployment. When the "Green" pods boot up, they use a Kubernetes `initContainer` running the AWS CLI to pull the 50GB cache from S3 into an `emptyDir` volume. The main Graphhopper container starts only when the data is fully downloaded. Once Readiness Probes confirm the graph is loaded into RAM, Argo Rollouts instantly flips 100% of the traffic to the Green pods.

## Kubernetes RollingUpdate vs Argo Rollouts Blue-Green

When updating map datasets in production, the strategy chosen determines whether your cache remains consistent:

- **Kubernetes `RollingUpdate` (Incremental):** Standard K8s deployments terminate old Pods and create new ones one-by-one. In a high-throughput routing environment, this creates a **"Split-Brain"** state where 50% of your gateway instances route traffic on the old graph, and the other 50% route on the new graph. Since these graphs have different node IDs and turn restrictions, this triggers a massive wave of cache misses and corrupts the Redis Semantic Cache.
- **Argo Rollouts Blue-Green (Atomic):** Instead of incremental updates, Argo Rollouts deploys a complete secondary set of pods (Green) alongside the running set (Blue). The Green pods load the new map data and run their readiness checks. Once 100% of the Green pods are healthy, Argo Rollouts executes a dynamic service endpoint swap, switching 100% of the user traffic to the new map instantly. This maintains perfect cache consistency.

## Go Implementation: Graceful Shutdown Handler

When scaling down pods during deployments, Kubernetes sends a `SIGTERM` signal. The Golang gateway must capture this signal and drain all active HTTP/gRPC requests before exiting:

```go
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// StartHTTPServerWithGracefulShutdown launches an HTTP server and listens for exit signals to exit cleanly
func StartHTTPServerWithGracefulShutdown(handler http.Handler, addr string) {
	server := &http.Server{
		Addr:    addr,
		Handler: handler,
	}

	// Create channel to listen for interrupt/termination signals
	stopChan := make(chan os.Signal, 1)
	signal.Notify(stopChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		log.Printf("Serving routing requests on %s...", addr)
		if err := server.ListenAndServe(); err != http.ErrServerClosed {
			log.Fatalf("HTTP server ListenAndServe failed: %v", err)
		}
	}()

	// Block until a signal is received
	sig := <-stopChan
	log.Printf("Received signal: %v. Initiating graceful shutdown...", sig)

	// Set a deadline context to drain active connections (e.g. 15 seconds)
	// During this period, the server stops accepting new connections
	// but finishes processing any active, in-flight routing requests
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown with active connections: %v", err)
	}

	log.Println("Server exited cleanly. All connections drained.")
}
```


---

## 2. Surviving Multi-Region Kubernetes & Global Latency

Code execution takes milliseconds, but the speed of light is unforgiving. A user in London hitting a Singapore cluster will suffer 200ms of TCP handshake latency before the API even receives the request.

### Geo DNS & Active Health Checks
To achieve global low latency, deploy your Kubernetes clusters to multiple regions (e.g., US-East, EU-West, AP-South). 
**The Fix:** Use a Geo DNS provider (like Route53 or Cloudflare). The authoritative DNS will inspect the user's location and resolve the domain to the IP of the closest cluster. **Crucially**, you must configure L7 Health Checks with a low TTL (30s). If the Singapore cluster loses power, the DNS provider will automatically withdraw the IP and route Asian users to Tokyo.

---

## FAQ: Senior SRE Nightmares

{{< faq q="During deployments, users randomly get '502 Bad Gateway' errors from the Golang API. Why?" >}}
When Kubernetes scales down a Pod, it sends a `SIGTERM` signal. If your Golang API exits immediately, inflight routing requests are brutally killed. Because `kube-proxy` needs a few seconds to update `iptables`, new traffic still hits the dead Pod. You MUST add a `preStop` hook (e.g., `sleep 10`) in your YAML and implement `http.Server.Shutdown()` in Go to drain connections gracefully.
{{< /faq >}}

{{< faq q="I set the Kubernetes Limit to 16GB and Java `-Xmx16G`, but it keeps crashing with OOMKilled (Exit Code 137). Why?" >}}
Welcome to the JVM Off-Heap trap. 16GB `-Xmx` only limits the Java Heap. The JVM also allocates "Off-Heap" memory for Thread Stacks, Metaspace, and NIO buffers. Total usage hits 16.5GB, and the Linux kernel's cgroup instantly kills the Pod without any Java logs. You MUST use `-XX:MaxRAMPercentage=75.0` to leave a 25% safety buffer for the OS.
{{< /faq >}}

{{< faq q="Under heavy load, my Golang Gateway randomly throws 503 errors when connecting to Redis, despite low CPU. Why?" >}}
This is **SNAT Port Exhaustion**. When your 50 Gateway Pods connect outbound, they use the physical Node's IP via Source NAT. When the Node exhausts its 65,000 ephemeral ports, it drops new connections. You MUST deploy a Managed NAT Gateway, use NodeLocal DNSCache, or heavily pool connections.
{{< /faq >}}

{{< faq q="Average latency is 50ms, but a 10x10 Distance Matrix always takes 2 seconds. Why?" >}}
This is the **Tail at Scale (P99) problem**. If you fan out 100 requests, and just 1 request hits a 2-second tail latency, the entire matrix waits 2 seconds. Averages lie. You MUST monitor Prometheus P99 metrics and implement **Hedging Requests**: if a request exceeds 100ms, the Gateway automatically fires a duplicate request to a different pod and takes the fastest result.
{{< /faq >}}

{{< faq q="My Golang API has high latency when calling external APIs from within Kubernetes. Why?" >}}
Check your `/etc/resolv.conf`. Kubernetes defaults to `ndots: 5`. This forces the DNS resolver to append 5 internal domain suffixes to every external request, creating a massive CoreDNS query storm. You MUST use FQDNs (add a trailing dot to the URL) or lower `ndots` to 2 in your Pod spec.
{{< /faq >}}

{{< faq q="I enabled OpenTelemetry tracing on my Routing API, but now my Cluster CPU is at 100%. Why?" >}}
Tracing 100% of 20,000 RPS will destroy your infrastructure bandwidth and CPU. You MUST implement **Tail-Based Sampling** at the OTel Collector level. The collector buffers traces in RAM and ONLY exports them to Jaeger if they contain an HTTP 5xx error or extremely high P99 latency. Normal requests are discarded.
{{< /faq >}}

Need help building high-scale routing engines or spatial indexing pipelines? [Contact me](/contact/) to discuss your project.

🔗 **Next Step:** You have completed the Routing & Geospatial Architecture masterclass! Feel free to review the [Executive Summary]({{< ref "executive-summary.md" >}}) or explore other series.

