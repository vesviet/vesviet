---
title: "Chapter 2: The 3 Caching Vulnerabilities (Penetration, Breakdown, Avalanche) & Go Singleflight"
date: 2026-06-09T10:05:00+07:00
lastmod: 2026-06-09T10:05:00+07:00
draft: false
series: ["Mastering High-Concurrency Systems in Production"]
series_order: 2
tags: ["golang", "caching", "redis", "singleflight"]
mermaid: true
slug: "caching-vulnerabilities-penetration-breakdown-avalanche"
description: "Learn how to defend against Cache Penetration, Avalanche, and Breakdown using Bloom Filters, TTL jittering, and Golang singleflight."
ShowToc: true
TocOpen: true
cover:
  image: "/images/posts/realtime-inventory-cover.png"
  alt: "High Concurrency Systems Masterclass series: queues, caches, and distributed B2B commerce"
  relative: false
---
[← Previous](/series/high-concurrency-systems/how-systems-handle-c10m/) | [Series hub](/series/high-concurrency-systems/) | [Next →](/series/high-concurrency-systems/distributed-rate-limiting-redis-gcra/)

# Chapter 2: The 3 Deadliest Cache Vulnerabilities

Caching is the ultimate shield for databases in distributed systems. However, poorly implemented caches can become the exact reason your system crashes. In this chapter, we dissect three classic caching phenomenons and how to defend against them using Golang.

## 1. Cache Penetration

**Answer-first:** Cache penetration occurs when attackers query non-existent IDs, bypassing the cache entirely. Defend against it by caching `NULL` values or utilizing Bloom Filters at the memory level.

**The Mechanism:** An attacker or a logic bug continuously sends requests for IDs that do not exist (e.g., `ID = -1` or random UUIDs). Since the data does not exist in the Database, it is NEVER written to the Cache. Consequently, every malicious request "penetrates" the cache and hits the DB directly. At 10,000 RPS, the Database will exhaust its connection pool and crash.

**The Solution:**
- **Cache Null Values:** If the DB query returns empty, force Redis to store a `NULL` or `Not_Found` value with a short TTL (e.g., 60 seconds). Subsequent requests will be blocked at Redis.
- **Bloom Filters:** Use a Bloom Filter to verify if an ID "probably exists" with near-zero memory overhead. If the Bloom Filter says NO, block the request instantly without touching the network.

## 2. Cache Avalanche

**Answer-first:** Cache Avalanche happens when massive amounts of keys expire simultaneously, sending a surge of queries to the DB. Prevent it by adding a random jitter offset to your TTLs.

**The Mechanism:** This phenomenon occurs when a massive batch of Cache Keys expires **at the exact same time**. For example, if you reset loyalty points at midnight and set a 1-hour TTL for 1 million users, exactly at 1:00 AM, 1 million keys will vanish. Every request hitting the system at 1:00:01 AM will bypass the empty cache and form an "avalanche" that crushes the database.

**The Solution:**
- **TTL Jittering:** Never hardcode an exact TTL. Always add a random time offset (Jitter). Instead of exactly 60 minutes, assign a random TTL between `55` and `65` minutes.

## 3. Cache Breakdown (Thundering Herd)

**Answer-first:** Cache Breakdown occurs when a single highly-accessed "Hot Key" expires, causing thousands of concurrent requests to query the DB simultaneously. Go's `singleflight` groups these identical requests into a single DB query.

**The Mechanism:** While an Avalanche involves 1 million normal keys expiring together, Breakdown involves **1 super Hot Key** (e.g., a Flash Sale product) suddenly expiring. At the very millisecond the TTL hits zero, 100,000 users are refreshing the page. Experiencing a Cache Miss, all 100,000 requests stampede toward the database to repopulate the cache. The DB bursts into flames instantly.

**The Solution: Golang `singleflight`**

This is the ultimate weapon for Go Developers. The `golang.org/x/sync/singleflight` package allows you to collapse tens of thousands of duplicate requests into a single execution.

When 100,000 requests query "Product A", `singleflight` will:
1. Assign the DB query task to the first Goroutine.
2. Block the remaining 99,999 Goroutines, forcing them to wait.
3. When the first Goroutine fetches the data, it shares the result with the 99,999 waiters directly in RAM.

Only **1 actual DB query** is executed instead of 100,000!

```go
import "golang.org/x/sync/singleflight"

var requestGroup singleflight.Group

func GetProductInfo(id string) (*Product, error) {
    if prod := getFromCache(id); prod != nil {
        return prod, nil
    }

    // Use singleflight to prevent Thundering Herd
    v, err, _ := requestGroup.Do(id, func() (interface{}, error) {
        product, dbErr := fetchFromDB(id)
        if dbErr == nil {
            setToCache(id, product, 60*time.Minute)
        }
        return product, dbErr
    })

    if err != nil {
        return nil, err
    }
    return v.(*Product), nil
}
```

By combining `singleflight` (node-level protection) and Redis Distributed Locks (cluster-level protection), you create an impenetrable fortress around your database.
