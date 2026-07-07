---
title: "Chapter 3: Distributed Rate Limiting with Redis & GCRA Algorithm"
date: 2026-06-09T10:10:00+07:00
lastmod: 2026-06-09T10:10:00+07:00
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
  image: "/images/posts/realtime-inventory-cover.png"
  alt: "High Concurrency Systems Masterclass series: queues, caches, and distributed B2B commerce"
  relative: false
---
[← Previous](/series/high-concurrency-systems/caching-vulnerabilities-penetration-breakdown-avalanche/) | [Series hub](/series/high-concurrency-systems/) | [Next →](/series/high-concurrency-systems/transactional-outbox-pattern-dual-write/)

# Chapter 3: Securing APIs with Distributed Rate Limiting

If caching is the shield protecting your database, **Rate Limiting** is the armor guarding your API servers from DDoS attacks and resource exhaustion caused by abusive clients.

## Why Local Rate Limiting Fails in Microservices

**Answer-first:** Local RAM limiters fail because Load Balancers distribute traffic across multiple nodes. A user allowed 100 req/sec can exploit a 5-node cluster by sending 500 req/sec, bypassing the intended limit. Centralized state via Redis is required.

A common mistake is using in-memory token counters (Local Cache) for rate limiters. Suppose the rule is: "100 Requests/sec per User". Your system has 5 backend servers. When User A blasts 500 requests concurrently, the Load Balancer routes 100 requests to each server. Since each server counts in its own isolated memory, it determines "User A just sent 100 requests, this is valid" and allows them all! The result: User A successfully bypasses the limit.

To solve this, we need a **Centralized State** managed by Redis.

## Token Bucket vs Leaky Bucket

There are two legendary algorithms in the Rate Limiting domain:

1. **Token Bucket:**
   - **Mechanism:** Tokens are generated at a steady rate and placed in a bucket. Every request consumes 1 token. If the bucket is empty, the request is rejected (`HTTP 429`).
   - **Pros:** Allows burst traffic. If the bucket is full (100 tokens), a user can fire 100 requests in a single millisecond. Ideal for Public APIs (e.g., Stripe, Twitter).
   
2. **Leaky Bucket:**
   - **Mechanism:** All requests are poured into a bucket. The bucket leaks requests out of a hole at a strictly constant rate. If you pour water too fast, the bucket overflows (rejects).
   - **Pros:** Perfect Traffic Shaping. Regardless of input turbulence, the output rate is strictly constant. Extremely useful for protecting fragile legacy systems downstream.

## The Power of the GCRA Algorithm

**Answer-first:** GCRA (Generic Cell Rate Algorithm) tracks Time rather than Token count. It blends the best of Leaky Bucket into a single mathematical formula, requiring only 1 Redis Key per user, drastically optimizing memory.

Simulating buckets in Redis often requires calculating token balances and storing timestamps, leading to Race Conditions and memory bloat.

The most popular Go rate limiting library, `github.com/go-redis/redis_rate`, uses the **GCRA** algorithm. Fundamentally, GCRA does not track *Token counts*; it tracks *Time*. It calculates the "Theoretical Arrival Time" (TAT) — the earliest time the next request is allowed to pass. This requires just a single Key in Redis, minimizing storage overhead.

## Redis Lua Script: The Key to Atomicity

**Answer-first:** Checking and deducting limits in Redis must be atomic. By encapsulating GCRA logic inside a Redis Lua Script, we prevent race conditions since Redis executes Lua scripts sequentially on its single thread.

Under high-concurrency pressure, the Read (Check) and Write (Deduct) operations must be absolutely Atomic. If your Go code calls `GET limit` followed by `SET limit = limit - 1`, a Race Condition vulnerability opens.

Redis solves this via **Lua Scripting**. When you run an `EVAL` command with a Lua Script, Redis locks the entire engine, executing the script sequentially from start to finish. No other command can interrupt it. This is why `redis_rate` and production-grade limiters embed their core logic in Lua scripts.

By combining Golang Middleware, Redis Lua Scripts, and the GCRA algorithm, you establish an invincible checkpoint for your Microservices.
