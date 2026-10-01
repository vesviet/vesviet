# Primary Key Showdown: UUIDv7 vs. Twitter Snowflake vs. BigInt Auto-Increment

> **Domain:** Distributed Systems | **Complexity:** Level 4/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Monotonic B-Tree Sorting`, `Distributed Generation`, `Index Page Splitting`, `Clock Skew`

---

## 1. Problem Statement & Operational Context
Using random UUIDv4 as primary keys in high-write transactional databases causes catastrophic B-Tree index fragmentation and random I/O writes. Sequential keys are mandatory for enterprise databases.

## 2. Comparison Matrix

| Identifier Scheme | Length / Storage | Sorting Property | Generation Overhead | B-Tree Fragmentation |
| :--- | :--- | :--- | :--- | :--- |
| **BigInt Auto-Increment** | 8 Bytes | Strict Sequential | Centralized DB Lock | **Zero** |
| **Twitter Snowflake** | 8 Bytes (Int64) | Time-Ordered | Requires Worker ID Cluster | **Near-Zero** |
| **UUIDv7 (RFC 9562)** | **16 Bytes** | **Unix Epoch MS Ordered** | **Decentralized (No coordination)** | **Near-Zero (< 1.5%)** |
| **UUIDv4 (Legacy)** | 16 Bytes | Completely Random | Decentralized | Severe (> 85% Page Splits) |

## 3. Agent Retrieval Guidance
- **Apply When:** Designing database schemas for distributed systems, multi-region databases, or sharded tables.
- **Related Articles:** `/series/architectural-tradeoffs-showdowns/03-primary-key-showdown-uuidv7-vs-snowflake-vs-bigint/`.
