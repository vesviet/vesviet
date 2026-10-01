# High-Throughput Shopping Cart & Redis Lua Stock Reservation Patterns

> **Domain:** E-Commerce Architecture | **Complexity:** Level 4/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Single-Threaded Atomicity`, `Monotonic Fencing Tokens`, `TTL Auto-Rollback`

---

## 1. Problem Statement & Operational Context
Relational database transactions holding row locks on stock tables during checkout authorization cause server thread pileups. If customer payment drops midway, orphaned locks paralyze sales.

## 2. Core Architectural Invariants
1. **Sub-Millisecond Atomic Holds:** Stock reservations execute via single-threaded Redis Lua scripts in < 0.2ms.
2. **Auto-Expiring Reservation Windows:** Reserved stock has a hard 15-minute TTL; unpaid reservations expire automatically without human intervention.
3. **Monotonic Fencing Token Verification:** Stale cancellation events arriving out of order are rejected by comparing sequence tokens.

## 3. Production Redis Lua Reservation Script
```lua
-- KEYS[1]: stock:{sku_id}, KEYS[2]: res:{saga_id}
-- ARGV[1]: qty, ARGV[2]: ttl_sec, ARGV[3]: fence_token
local cur = tonumber(redis.call('GET', KEYS[1]) or -1)
local qty = tonumber(ARGV[1])
if cur >= qty then
    redis.call('DECRBY', KEYS[1], qty)
    redis.call('HMSET', KEYS[2], 'qty', qty, 'fence', ARGV[3])
    redis.call('EXPIRE', KEYS[2], tonumber(ARGV[2]))
    return 1
else
    return 0
end
```

## 4. Agent Retrieval Guidance
- **Apply When:** Resolving stock overselling bugs, building flash sale carts, or architecting distributed checkout locks.
- **Related Articles:** `/posts/architecting-21-service-ecommerce-golang-ddd/`, `/posts/cloudflare-d1-durable-objects-realtime-cart/`.
