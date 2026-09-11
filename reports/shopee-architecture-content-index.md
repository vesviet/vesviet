# Comprehensive Content Index & Audit Report: Shopee Architecture Series
**Generated Date**: 2026-09-11T21:40:00+07:00  
**Standards Adhered**: 2027 SOTA Hyper-Scale E-Commerce, Southeast Asian Distributed Infrastructure, Flash Sale Zero-Overselling, Redis Lua Atomic Engines, Distributed SQL (TiDB), Kafka Peak Shaving, and ClickHouse Observability.

---

## 1. Series Architecture & Curriculum Overview
The `shopee-architecture` series provides production-grade architectural blueprints, concurrency controls, database migration roadmaps, and SRE resilience strategies designed to withstand extreme Southeast Asian Mega Sale traffic peaks (9.9, 11.11, 12.12).

### Master Quality Standards (2027 SOTA):
- **Total Chapters**: 6 files per repository (**12 files total** across `vesviet` and `learn`).
- **Interactive Diagrams**: Exactly 2 valid Mermaid diagrams per file (**24 diagrams total**), 100% AST syntax validated with quoted labels and safe styling.
- **Interactive FAQs**: Exactly 3 Hugo `{{< faq >}}` components per file (**36 interactive FAQs total**).
- **Weight Normalization**: `_index.md` normalized to Weight 100; Chapters sequentially assigned Weights 1 to 5.
- **Reciprocal Linking**: Fully bidirectional between `tanhdev.com` and `learn.tanhdev.com`.
- **Zero Hallucination / Copypasta**: Real production metrics, benchmarks, formulas, and exact code implementations.

---

## 2. Chapter Inventory & Content Metrics Matrix

| File Name (Vesviet / Learn) | Weight | Vesviet (English) | Learn (Vietnamese) | Reciprocal Links |
| :--- | :---: | :--- | :--- | :--- |
| `_index.md` / `_index.md` | 100 | Shopee Architecture Masterclass<br>M: 2, FAQ: 3 | Tổng Quan Kiến Trúc Shopee<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/shopee-architecture/) / [Tiếng Việt](https://learn.tanhdev.com/series/shopee-architecture/) |
| `01-microservices-foundation.md` / `01-microservices-foundation.md` | 1 | Shopee Microservices: Go, gRPC & Gateway<br>M: 2, FAQ: 3 | Bài 1: Nền Tảng Microservices — Go, gRPC & API Gateway<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/shopee-architecture/01-microservices-foundation/) / [Tiếng Việt](https://learn.tanhdev.com/series/shopee-architecture/01-microservices-foundation/) |
| `02-flash-sale-engine.md` / `02-flash-sale-engine.md` | 2 | Shopee Flash Sale Engine: Redis Lua & Zero Overselling<br>M: 2, FAQ: 3 | Bài 2: Động Cơ Flash Sale — Redis Lua & Chống Bán Quá Kho<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/shopee-architecture/02-flash-sale-engine/) / [Tiếng Việt](https://learn.tanhdev.com/series/shopee-architecture/02-flash-sale-engine/) |
| `03-traffic-shield.md` / `03-traffic-shield.md` | 3 | Shopee Traffic Shield: Kafka Peak Shaving & Circuit Breaking<br>M: 2, FAQ: 3 | Bài 3: Tấm Khiên Bảo Vệ — Kafka Peak Shaving & Cắt Tải<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/shopee-architecture/03-traffic-shield/) / [Tiếng Việt](https://learn.tanhdev.com/series/shopee-architecture/03-traffic-shield/) |
| `04-database-scale.md` / `04-database-scale.md` | 4 | Shopee DB: MySQL Sharding to TiDB NewSQL Migration<br>M: 2, FAQ: 3 | Bài 4: Tầng Dữ Liệu — Từ MySQL Sharding Đến TiDB NewSQL<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/shopee-architecture/04-database-scale/) / [Tiếng Việt](https://learn.tanhdev.com/series/shopee-architecture/04-database-scale/) |
| `05-observability.md` / `05-observability.md` | 5 | Shopee Observability: ClickHouse & Distributed Tracing<br>M: 2, FAQ: 3 | Bài 5: Tai Mắt Hệ Thống — Distributed Tracing Với ClickHouse<br>M: 2, FAQ: 3 | [English](https://tanhdev.com/series/shopee-architecture/05-observability/) / [Tiếng Việt](https://learn.tanhdev.com/series/shopee-architecture/05-observability/) |

---

## 3. Technology & Architecture Stack (2027 SOTA Standard)

| Domain Area | Technical Specification & Implementation Standard |
| :--- | :--- |
| **Microservices RPC** | Golang 1.25+, ByteDance Kitex / gRPC, Protobuf v3 with zero-copy serializers, Consul partitioned discovery, Envoy/Ambient service mesh. |
| **Flash Sale Core** | Redis 7.4 Cluster, single-variable atomic Lua scripts, sub-key SKU inventory sharding, in-memory FreeCache short-circuiting. |
| **Traffic Shaping** | Multi-partition Kafka peak shaving, Alibaba Sentinel adaptive shedding, Cloudflare Workers virtual waiting rooms, DLQ poison-pill routing. |
| **Database Scalability** | MySQL InnoDB limits, TiDB 8.0 Distributed SQL, TiKV Multi-Raft consensus, Placement Driver (PD) region auto-split, TiFlash HTAP analytics. |
| **Telemetry & SRE** | Datadog Vector SIMD pipelines, ClickHouse columnar log storage, OpenTelemetry W3C distributed tracing, continuous Pyroscope profiling. |
| **Live Commerce** | WebRTC interactive low-latency video, WebSocket gateway connection pools, Redis Streams real-time voucher broadcast. |
| **Multi-Region Topology** | Regional sovereign clusters (SG, ID, VN, TH, PH, MY), Anycast BGP ingress, bi-directional CDC replication, CRDT shopping carts. |
| **Search & AI** | Hybrid lexical (BM25) + dense vector search (Qdrant HNSW), Feast real-time feature store, NVIDIA Triton INT8 GPU inference. |
| **Anti-Fraud & Security** | Device fingerprinting, TLS JA4 hashing, eBPF XDP crawler throttling, graph database (Nebula Graph) syndicate fraud ring detection. |
| **Disaster Recovery** | Chaos Mesh fault injection, GoReplay production socket traffic replay at 3x scale, 60-minute Mega Sale triage runbooks. |

---

## 4. Verification & Quality Assurance Checklist
- [x] 100-Round Deep Research completed and persisted in JSON and Markdown formats.
- [x] Exact Chapter Symmetry: 6 chapters in `vesviet`, 6 chapters in `learn` (12 files total).
- [x] Slugs perfectly matched between repositories.
- [x] Exactly 2 valid Mermaid diagrams per file (24 diagrams total, zero syntax/AST errors).
- [x] Exactly 3 interactive Hugo FAQ shortcodes per file (36 FAQs total).
- [x] Reciprocal cross-links established on all files.
- [x] Hugo build verified with zero errors (`hugo --minify`).
