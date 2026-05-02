---
title: "Research Index"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Reading guide and index for the Alipay Double 11 Architecture research series: what each phase covers and how to consume it by time and role."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)

This index explains what each document covers and suggests reading paths depending on your time budget and role.

## Core Documents (Series Pages)

| Page | What it covers | Best for |
|------|-----------------|----------|
| [Executive Summary](/series/alipay-double-11/executive-summary/) | The story, the numbers, and the 3 pillars | Execs, CTO/VP Eng, PMs |
| [Phase 1: Timeline](/series/alipay-double-11/phase-1-timeline/) | Key milestones and why the architecture had to change | Everyone |
| [Phase 2: Architecture](/series/alipay-double-11/phase-2-architecture/) | LDC/unitization, multi-active, DB and MQ foundations | Architects, senior engineers |
| [Phase 3: Operations](/series/alipay-double-11/phase-3-operations/) | Capacity planning, full-link stress testing, incident command | Engineering leadership, SRE |
| [Phase 4: Technology Overview](/series/alipay-double-11/phase-4-technology/) | Middle platform, payment flow, risk control, SOFAStack | Architects, ICs |
| [Phase 4: Deep Dive](/series/alipay-double-11/phase-4-deep-dive/) | Internals: RPC, MQ, storage engine, transactions, ML risk control | Deep technical readers |
| [Modern Tech Comparison](/series/alipay-double-11/modern-tech-comparison/) | Mapping to Kubernetes, Kafka/Pulsar, gRPC, modern DBs, service mesh | Teams modernizing today |
| [Phase 5: Synthesis](/series/alipay-double-11/phase-5-synthesis/) | Patterns, anti-patterns, KPIs, decision framework | Leaders + architects |

## Reading Paths (By Time Budget)

### 10–15 minutes (Executive)
1. [Executive Summary](/series/alipay-double-11/executive-summary/)

### 60–90 minutes (Engineering leadership)
1. [Executive Summary](/series/alipay-double-11/executive-summary/)
2. [Phase 1: Timeline](/series/alipay-double-11/phase-1-timeline/)
3. [Phase 2: Architecture](/series/alipay-double-11/phase-2-architecture/)
4. [Phase 3: Operations](/series/alipay-double-11/phase-3-operations/)
5. [Phase 5: Synthesis](/series/alipay-double-11/phase-5-synthesis/)

### 6–10 hours (Full technical deep dive)
Read everything above, then:
1. [Phase 4: Technology Overview](/series/alipay-double-11/phase-4-technology/)
2. [Modern Tech Comparison](/series/alipay-double-11/modern-tech-comparison/)
3. [Phase 4: Deep Dive](/series/alipay-double-11/phase-4-deep-dive/)

## Quick Reference (What to Copy)

If you are building a high-throughput system:
- Copy the *ideas*: **unitization/cells**, **multi-active**, **deterministic readiness**, **downgrade strategies**, and **automation as a product**.
- Don’t blindly copy the *tooling*: the modern equivalents are often different (Kubernetes, modern DBs, Kafka/Pulsar, gRPC, service mesh).

## Notes

This series focuses on **repeatable peak reliability**, not just peak performance. Peak success is treated as an operational system: architecture + testing + monitoring + playbooks.
