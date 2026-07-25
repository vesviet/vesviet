---
title: "Cornerstone Technologies: Kiến trúc & Production Guide"
date: 2026-07-25T09:00:00+07:00
draft: false
weight: 1
description: "Tổng hợp các bài viết chuyên sâu (Pillar Content) về các công nghệ cốt lõi trong Backend và Distributed Systems dành cho Senior Go Engineers."
series: ["Cornerstone Technologies"]
---

# Cornerstone Technologies: Kiến trúc & Production Guide

Chào mừng đến với **Cornerstone Technologies** – chuỗi bài viết chuyên sâu (Pillar Content) do team Kỹ thuật viên của Vesviet tổng hợp. Series này được thiết kế đặc biệt dành cho các **Senior Go Engineers**, Software Architects và những ai đang tìm kiếm các hướng dẫn thực chiến, từ kiến trúc hệ thống đến code Golang production-ready.

Khác với các tài liệu nhập môn (101 tutorials), series này tập trung vào:
- **Information Gain & E-E-A-T**: Kiến thức thực chiến, benchmark thực tế và các lỗi "đau thương" trên môi trường production.
- **Deep Architectural Dives**: Mổ xẻ chi tiết cách các công cụ hoạt động bên dưới (Event Sourcing, HNSW, V8 Isolates).
- **Golang First**: Toàn bộ ví dụ, best practices và SDK tuning đều xoay quanh hệ sinh thái Golang.

## Các Chủ Đề Cốt Lõi (Pillars)

1. **[NATS JetStream & Golang: Kiến trúc & Hướng dẫn Production](nats-jetstream-golang-production-guide/)**  
   Tìm hiểu cách NATS JetStream cung cấp Exactly-Once delivery và kiến trúc multi-tenant siêu nhẹ mà không cần ZooKeeper hay JVM, thay thế hoàn hảo cho Kafka trong nhiều use cases.
   
2. **[Temporal Workflow & Golang: Kiến trúc & Production Guide](temporal-workflow-go-architecture/)**  
   Khám phá mô hình Event Sourcing và Replay Engine của Temporal. Nắm vững các quy tắc Determinism sống còn khi viết Workflow bằng Go.
   
3. **[Zero-Trust Architecture cho Microservices: Toàn tập mTLS & Go](zero-trust-architecture-microservices/)**  
   Chấm dứt kỷ nguyên VPN nội bộ. Hướng dẫn thiết lập mTLS với SPIFFE/SPIRE và triển khai User Identity Propagation qua OAuth 2.1 & JWT.

4. **[Vector Database là gì? Kiến trúc HNSW & RAG Pipeline (Qdrant)](vector-database-rag-qdrant-milvus/)**  
   Trái tim của hệ thống AI Agents: Giải phẫu thuật toán Approximate Nearest Neighbor (HNSW), so sánh hiệu năng Qdrant (Rust) vs Milvus (Go), và memory profiling.

5. **[Cloudflare Workers & Edge Computing: Kiến trúc V8 Isolates](cloudflare-workers-edge-computing/)**  
   Đưa Compute ra sát người dùng nhất. Phân biệt V8 Isolates vs AWS Lambda, loại bỏ Cold Start (0ms) và chạy code Go/Rust tại Edge CDN qua WebAssembly (Wasm).

Hãy chọn một chủ đề phía dưới để bắt đầu hành trình nâng cấp kiến trúc hệ thống của bạn!
