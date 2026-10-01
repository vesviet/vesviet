# Shopee Flash Sale Engine: Multi-Tier Traffic Shield & High-Concurrency Inventory Gates

> **Domain:** E-Commerce Architecture | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Traffic Shield`, `Redis Lua Fencing`, `Token Bucket Rate Limiting`, `Eventual Order Sinking`

---

## 1. Problem Statement & Operational Context
Flash sales introduce extreme traffic asymmetry: 99.8% of incoming requests during midnight flash sales will fail to secure stock. Passing raw flash-sale traffic directly to order creation pipelines collapses message brokers and relational databases.

## 2. Core Architectural Invariants
1. **Zero Overselling Invariant:** Total committed inventory across successful orders must equal initial allocation exactly; stock count must never drop below zero.
2. **Traffic Shedding at the Edge:** Filter and discard at least 95% of invalid, bot, or exhausted-stock traffic before reaching internal microservices.
3. **Asynchronous Order Materialization:** Storefront responds with "Order Queued" within 30ms; downstream order creation processes via buffered event streams.

## 3. Technology Trade-off Matrix

| Architecture Tier | Shopee Multi-Tier Shield | Naive Direct Checkout | Database Row Locking |
| :--- | :--- | :--- | :--- |
| **Ingress Filtering** | Cloudflare WAF + OpenResty Lua Gate | API Gateway Passthrough | Direct DB Connection |
| **Stock Check Speed** | **< 0.5 ms (Redis RAM Lua)** | 15–40 ms (SQL Query) | 200–2,000 ms (Lock Contention) |
| **Max Absorbable QPS** | **50,000+ QPS per Redis Node** | 1,500 QPS (DB Bottleneck) | 300 QPS (Deadlock Convoy) |
| **System Resiliency** | Degrades to wait-room queue | Hard HTTP 500 Outages | Database Connection Pool Starvation |

## 4. Architectural Anchors & Code Implementation

### Atomic Token Bucket Rate Limiter (Redis Lua)
```lua
-- KEYS[1]: rate_limit:{user_id}
-- ARGV[1]: max_tokens, ARGV[2]: refill_rate_per_sec, ARGV[3]: now_unix_timestamp
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local data = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(data[1]) or max_tokens
local last_updated = tonumber(data[2]) or now

-- Calculate refilled tokens based on elapsed time
local delta = math.max(0, now - last_updated)
tokens = math.min(max_tokens, tokens + delta * refill_rate)

if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', now)
    redis.call('EXPIRE', key, 60)
    return 1 -- Allowed
else
    return 0 -- Throttled
end
```

## 5. Agent Retrieval Guidance
- **Apply When:** Engineering high-traffic flash sale engines, ticketing portals, or sneaker drop campaigns.
- **Related Articles:** `/series/shopee-architecture/`, `/posts/architecting-21-service-ecommerce-golang-ddd/`.
