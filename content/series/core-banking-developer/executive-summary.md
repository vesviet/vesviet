---
title: "The Landscape of Core Banking Developers"
date: 2026-05-06T18:00:00+07:00
draft: false
description: "A comprehensive overview of the Core Banking Developer role — what they do, what they need, and why they are among the highest-paid engineers in the financial sector."
weight: 1
---

## Who is a Core Banking Developer?

A **Core Banking Developer** is a software engineer responsible for building, operating, and extending the system that processes all of a bank's core financial operations — from managing accounts, processing money transfers, and calculating interest rates, to ensuring every single penny is recorded with absolute accuracy.

Unlike a typical developer, a mistake for a Core Banking Developer doesn't just mean a 404 error page — it means **customers' money being lost, duplicated, or the general ledger becoming unbalanced**. This intense pressure defines their entire approach to writing code and designing systems.

## Why is this field special?

### 1. Absolute Accuracy
In regular software development, "eventual consistency" is often acceptable. In Core Banking, **a transaction either completely succeeds or does not happen at all**. There is no in-between state. This is why ACID database transactions are an indispensable foundation.

### 2. Extremely High Concurrency
Millions of users can perform transactions simultaneously within the same second. The system must handle concurrency without allowing race conditions that could lead to incorrect deductions or double credits.

### 3. Compliance and Legal Requirements
Every action in a Core Banking system must have an audit trail. The State Bank, tax authorities, and international organizations reserve the right to review the entire transaction history at any given time.

## The Knowledge Map of a Core Banking Developer

```
┌─────────────────────────────────────────────────────────────────┐
│                   CORE BANKING DEVELOPER                        │
│                                                                 │
│  DOMAIN KNOWLEDGE          TECHNICAL SKILLS                     │
│  ─────────────────          ────────────────                    │
│  • Double-Entry (GL)       • Database (ACID, Locking)           │
│  • CASA (Deposits)         • Distributed Transactions           │
│  • Lending (Credit)        • Event-Driven Architecture          │
│  • Payments & Clearing     • API Design (REST/gRPC)             │
│  • Trade Finance           • Security & Encryption              │
│                                                                 │
│  STANDARDS & PROTOCOLS     ARCHITECTURE PATTERNS                │
│  ─────────────────────     ─────────────────────                │
│  • ISO 8583 (Card/ATM)     • Saga Pattern                       │
│  • ISO 20022 (SWIFT)       • Outbox Pattern                     │
│  • BIAN Framework          • CQRS & Event Sourcing              │
│  • PCI-DSS                 • Idempotency Keys                   │
└─────────────────────────────────────────────────────────────────┘
```

## The Market Landscape

### Popular Core Banking Systems in Vietnam
| System | Core Technology | Banks Using It |
|---|---|---|
| **Temenos T24** | Java, jBASE/BASIC | Techcombank, VPBank, MB Bank, Sacombank |
| **Oracle Flexcube** | Java EE, Oracle DB | VietinBank, BIDV |
| **Infosys Finacle** | Java | Agribank (Under deployment) |
| **In-house (Custom)** | Go, Java, Kotlin | MoMo, ZaloPay, VCB Digibank |

### Next-Generation Trends
Digital banks and fintechs are no longer purchasing off-the-shelf Core Banking systems — they are **building their own Core Banking systems using Microservices**. This represents a massive opportunity for full-stack developers with a mindset for distributed systems.

## Learning Roadmap in this Series

```
Step 1 → Double-Entry Bookkeeping Mindset (Mandatory, cannot be skipped)
Step 2 → Banking Domain: CASA & Lending
Step 3 → Database Engineering: ACID, Locking, Concurrency
Step 4 → Modern Core Banking Architecture
Step 5 → International Integration Standards (ISO 8583, ISO 20022)
Step 6 → Security, Audit, and Legal Compliance
Step 7 → Practice: Building a Mini Core Banking System
```

> *Let's start from [Part 1 — The Double-Entry Ledger Foundation](/series/core-banking-developer/part-1-double-entry-ledger/). This is the mental foundation that every Core Banking Developer must master before writing a single line of code.*
