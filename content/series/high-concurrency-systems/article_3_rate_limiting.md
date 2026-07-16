---
title: "Chapter 3: Distributed Rate Limiting with Redis & GCRA Algorithm"
date: "2026-06-09T10:10:00+07:00"
lastmod: "2026-06-09T10:10:00+07:00"
draft: false
series: ["Mastering High-Concurrency Systems in Production"]
series_order: 3
tags: ["golang", "rate limiting", "redis", "gcra"]
mermaid: true
slug: "distributed-rate-limiting-redis-gcra"
description: "Discover why local rate limiters fail in Microservices and how Redis Lua scripts powering the GCRA algorithm solve distributed throttling."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/realtime-inventory-cover.png"
  alt: "High Concurrency Systems Masterclass series: queues, caches, and distributed B2B commerce"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/high-concurrency-systems/distributed-rate-limiting-redis-gcra/"
---

> **Prerequisite:** Before reading this chapter, please ensure you have read the previous article in this series: [Chapter 2: The 3 Caching Vulnerabilities (Penetration, Breakdown, Avalanche) & Go Singleflight]({{< ref "article_2_caching.md" >}}).

If caching is the shield protecting your database, **Rate Limiting** is the armor guarding your API servers from DDoS attacks and resource exhaustion caused by abusive clients.

---

## 1. Why Local Rate Limiting Fails in Microservices

Local RAM limiters fail because Load Balancers distribute traffic across multiple nodes. A user allowed 100 req/sec can exploit a 5-node cluster by sending 500 req/sec, bypassing the intended limit. Centralized state via Redis is required.

A common mistake is using in-memory token counters (Local Cache) for rate limiters. Suppose the rule is: "100 Requests/sec per User". Your system has 5 backend servers. When User A blasts 500 requests concurrently, the Load Balancer routes 100 requests to each server. Since each server counts in its own isolated memory, it determines "User A just sent 100 requests, this is valid" and allows them all! The result: User A successfully bypasses the limit.

To solve this, we need a **Centralized State** managed by Redis.

---

## 2. Token Bucket vs Leaky Bucket (Mathematical Models)

There are two legendary algorithms in the Rate Limiting domain:

### Token Bucket (Traffic Policing)
The Token Bucket algorithm models a bucket of capacity $B$ that accumulates tokens at a constant rate $r$ tokens per second. When a request arrives, the system attempts to draw 1 token (or $c$ tokens) from the bucket. If the bucket has sufficient tokens, the request is allowed; otherwise, it is dropped or queued.

The mathematical update function for token count $T(t)$ at arrival time $t$ is:
$$T(t) = \min\left(B, T_{\text{prev}} + r \cdot (t - t_{\text{prev}})\right)$$

Where $t_{\text{prev}}$ is the arrival time of the last allowed request and $T_{\text{prev}}$ is the remaining token count.
- **Pros:** Supports bursts up to $B$ requests instantaneously, which fits modern REST APIs where pages load multiple assets in parallel.

### Leaky Bucket (Traffic Shaping)
The Leaky Bucket algorithm queues incoming requests in a bounded FIFO queue of capacity $Q$. The queue "leaks" requests at a strictly constant rate $L$ per second to the downstream services. If a request arrives and the queue is full, the request is immediately rejected.
- **Pros:** Perfect traffic shaping. Regardless of the spike's size, the rate at which requests enter the backend is locked at $L$, eliminating downstream buffer overload.
- **Cons:** Introduces queueing delay (latency penalty) for all requests buffered during a burst.

---

## 3. The Power of the GCRA Algorithm

GCRA (Generic Cell Rate Algorithm) tracks Time rather than Token count. It blends the best of Leaky Bucket into a single mathematical formula, requiring only 1 Redis Key per user, drastically optimizing memory.

Simulating buckets in Redis often requires calculating token balances and storing timestamps, leading to Race Conditions and memory bloat.

The most popular Go rate limiting library, `github.com/go-redis/redis_rate`, uses the **GCRA** algorithm. Fundamentally, GCRA does not track *Token counts*; it tracks *Time*. It calculates the "Theoretical Arrival Time" (TAT) — the earliest time the next request is allowed to pass.

### GCRA Algorithm Flowchart

The following Mermaid diagram outlines the logic executed for every incoming request:

```mermaid
flowchart TD
    Start([Incoming Request at Time t]) --> GetTAT[Retrieve TAT from Redis]
    GetTAT --> CheckNull{TAT exists?}
    CheckNull -- No --> InitTAT[Set TAT = t]
    CheckNull -- Yes --> CalculateNewTAT[Calculate NewTAT = max(t, TAT) + EmissionInterval]
    InitTAT --> Allow[Allow Request & Set Redis Key = TAT + EmissionInterval]
    CalculateNewTAT --> CheckLimit{NewTAT - t > BurstTolerance}
    CheckLimit -- Yes --> Reject[Reject Request - 429 Too Many Requests]
    CheckLimit -- No --> UpdateRedis[Update Redis Key = NewTAT]
    UpdateRedis --> Allow
```

In GCRA:
- **Emission Interval ($T$):** The reciprocal of the rate ($1 / \text{rate}$). E.g., for 100 req/sec, $T = 10\text{ms}$.
- **Burst Tolerance ($\tau$):** The maximum burst size times the Emission Interval. E.g., for a burst of 5 requests, $\tau = 5 \cdot T = 50\text{ms}$.
- When a request arrives at time $t$, if the difference between the theoretical arrival time ($TAT$) and $t$ exceeds $\tau$, the request violates the rate limit:
  $$\text{If } TAT - t > \tau \implies \text{Reject}$$
  $$\text{Otherwise, } TAT_{\text{new}} = \max(t, TAT) + T \implies \text{Allow & Store } TAT_{\text{new}}$$

---

## 4. Redis Lua Script: The Key to Atomicity

Checking and deducting limits in Redis must be atomic. By encapsulating GCRA logic inside a Redis Lua Script, we prevent race conditions since Redis executes Lua scripts sequentially on its single thread.

Under high-concurrency pressure, the Read (Check) and Write (Deduct) operations must be absolutely Atomic. If your Go code calls `GET limit` followed by `SET limit = limit - 1`, a Race Condition vulnerability opens.

Redis solves this via **Lua Scripting**. When you run an `EVAL` command with a Lua Script, Redis locks the entire engine, executing the script sequentially from start to finish. No other command can interrupt it.

---

## Go Implementation: Atomic GCRA Rate Limiter

The following Go code implements a distributed rate limiter wrapping an atomic Redis Lua script that implements the GCRA algorithm.

```go
package main

import (
	"context"
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
)

// GCRALimiter manages atomic rate limiting execution in Redis.
type GCRALimiter struct {
	rdb     *redis.Client
	luaSHA  string
	luaCode string
}

// GCRA Lua Script to execute atomically in Redis.
const gcraScript = `
local key = KEYS[1]
local rate = tonumber(ARGV[1])         -- allowed rate (requests per second)
local burst = tonumber(ARGV[2])        -- allowed burst capacity
local now = tonumber(ARGV[3])         -- current Unix timestamp in microseconds

local emission_interval = 1000000 / rate
local burst_tolerance = burst * emission_interval

local tat = redis.call("GET", key)

if not tat then
    tat = now
else
    tat = tonumber(tat)
end

local new_tat = math.max(now, tat) + emission_interval

if (new_tat - now) > burst_tolerance then
    return {0, math.ceil((new_tat - now - burst_tolerance) / 1000000)}
else
    redis.call("SET", key, new_tat, "PX", math.ceil((new_tat - now + burst_tolerance) / 1000))
    return {1, 0}
end
`

// NewGCRALimiter initializes and compiles the Lua script in Redis.
func NewGCRALimiter(ctx context.Context, rdb *redis.Client) (*GCRALimiter, error) {
	// Pre-load Lua script to save network bandwidth on subsequent requests
	hasher := sha1.New()
	hasher.Write([]byte(gcraScript))
	sha := hex.EncodeToString(hasher.Sum(nil))

	err := rdb.ScriptLoad(ctx, gcraScript).Err()
	if err != nil {
		return nil, fmt.Errorf("failed to load lua script: %w", err)
	}

	return &GCRALimiter{
		rdb:     rdb,
		luaSHA:  sha,
		luaCode: gcraScript,
	}, nil
}

// Allow checks if the request is allowed under the rate limit.
func (l *GCRALimiter) Allow(ctx context.Context, key string, rate int, burst int) (bool, time.Duration, error) {
	nowMicro := time.Now().UnixNano() / 1000
	
	// Execute evalsha to leverage pre-cached script
	res, err := l.rdb.EvalSha(ctx, l.luaSHA, []string{key}, rate, burst, nowMicro).Result()
	if err != nil {
		// Fallback to loading and executing script if it was flushed from Redis memory
		res, err = l.rdb.Eval(ctx, l.luaCode, []string{key}, rate, burst, nowMicro).Result()
		if err != nil {
			return false, 0, err
		}
	}

	slice, ok := res.([]interface{})
	if !ok || len(slice) < 2 {
		return false, 0, fmt.Errorf("unexpected Redis response shape")
	}

	allowed := slice[0].(int64) == 1
	retryAfterSec := slice[1].(int64)

	var retryAfter time.Duration
	if retryAfterSec > 0 {
		retryAfter = time.Duration(retryAfterSec) * time.Second
	}

	return allowed, retryAfter, nil
}

func main() {
	// Connect to local Redis instance
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	ctx := context.Background()

	limiter, err := NewGCRALimiter(ctx, rdb)
	if err != nil {
		fmt.Printf("Initialization Error: %v\n", err)
		return
	}

	userKey := "user_limit:userId_99"

	// Simulate 10 immediate requests (Rate: 2 per sec, Burst: 5)
	for i := 1; i <= 10; i++ {
		allowed, retryAfter, err := limiter.Allow(ctx, userKey, 2, 5)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			continue
		}
		if allowed {
			fmt.Printf("Request %d: ALLOWED\n", i)
		} else {
			fmt.Printf("Request %d: BLOCKED (Retry after %v)\n", i, retryAfter)
		}
		time.Sleep(50 * time.Millisecond) // Short delay
	}
}
```

This implementation allows Go microservices to enforce strict, atomic limits across distributed nodes in O(1) time complexity, shielding backend nodes from abusive request surges.

---

## 🎯 Architecture Review & Consulting (Hire Me)

If your enterprise e-commerce or B2B platform is struggling with slow database queries, checkout timeouts, or scaling bottlenecks, don't let it jeopardize your business revenue.

👉 **[Book a 1:1 Architecture Consultation this week](/hire/)** with Lê Tuấn Anh (Vesviet) to identify bottlenecks and implement proven scaling strategies.

---

[← Previous]({{< ref "article_2_caching.md" >}}) | [Series hub]({{< ref "_index.md" >}}) | [Next →]({{< ref "article_4_outbox_pattern.md" >}})

