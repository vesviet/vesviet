---
title: "Part 10: ADR Walkthrough — 24 Architecture Decisions Decoded"
date: 2026-06-15T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Comprehensive review of 24 Architecture Decision Records (ADRs) powering the Composable Commerce migration: storage, messaging, telemetry, and auth."
categories: ["Series", "Software Engineering", "Architecture"]
tags: ["ADR", "Architecture Decision Record", "Microservices", "Golang", "System Design"]
series: ["composable-commerce-migration"]
weight: 11
slug: "part-10-adr-walkthrough"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-10-adr-walkthrough/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 10: ADR Walkthrough — 24 Architecture Decisions Decoded"
  relative: false
keywords: ["architecture decision records ecommerce", "adr walkthrough golang", "system design composable commerce", "microservices adr"]
---

[← Previous Chapter: Part 9: Transactional Outbox & Sagas](/series/composable-commerce-migration/part-9-outbox-saga/) | [Series Hub](/series/composable-commerce-migration/)

---

> **Answer-first:** Architecture Decision Records (ADRs) provide an immutable, version-controlled record of structural choices. This chapter documents all 24 production ADRs covering database selection (PostgreSQL + JSONB), messaging (Kafka), monorepo governance (Rush), framework (Kratos v2), and authentication (BFF + HttpOnly cookies).

---
## Summary of Key Production ADRs

| ADR # | Decision Title | Selected Option | Key Trade-Off Rationale |
|---|---|---|---|
| **ADR-001** | Primary Backend Language | **Golang 1.25+** | Sub-millisecond startup, low memory footprint, high concurrency goroutines. |
| **ADR-002** | Microservice Framework | **Kratos v2** | Native Protobuf annotations, Google Wire compile-time DI, Clean Architecture. |
| **ADR-003** | Monorepo Tooling | **Microsoft Rush + PNPM** | Strict symlink isolation, phantom dependency elimination, polyglot support. |
| **ADR-004** | Primary Database | **PostgreSQL (JSONB)** | ACID compliance, JSONB GIN indexing for dynamic E-Commerce attributes. |
| **ADR-005** | Event Streaming | **Apache Kafka** | High-throughput durable event log, replayability for new microservices. |
| **ADR-006** | Inter-Service Transport | **gRPC / Protobuf** | Binary payload efficiency, type-safe API contracts, auto-generated SDKs. |
| **ADR-007** | Client Gateway | **grpc-gateway** | Zero-maintenance REST/JSON exposure from existing Protobuf definitions. |
| **ADR-008** | Distributed Transactions | **Saga + Outbox** | Eliminates blocking 2-Phase Commit locks while ensuring eventual consistency. |
