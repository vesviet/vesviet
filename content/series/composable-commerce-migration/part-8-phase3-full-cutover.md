---
title: "Part 8: Phase 3 — Full Cutover & Decommissioning the Monolith"
date: 2026-05-28T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Executing the final checkout cutover, DNS switchover, fallback rollback runbooks, and decommissioning the legacy Magento monolith."
categories: ["Series", "Software Engineering", "DevOps"]
tags: ["Cutover", "DevOps", "DNS Migration", "Zero Downtime", "Decommissioning", "Microservices"]
series: ["composable-commerce-migration"]
weight: 9
slug: "part-8-phase3-full-cutover"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-8-phase3-full-cutover/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 8: Phase 3 — Full Cutover & Decommissioning the Monolith"
  relative: false
keywords: ["monolith decommissioning", "cutover runbook ecommerce", "zero downtime cutover", "magento sunset"]
---

[← Previous Chapter: Part 7: Phase 2 — Dual-Write](/series/composable-commerce-migration/part-7-phase2-dual-write/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 9: Transactional Outbox & Sagas →](/series/composable-commerce-migration/part-9-outbox-saga/)

---

> **Answer-first:** Phase 3 transfers write authority for Orders and Payments to the Go microservices. Once historical orders are reconciled and payment webhooks are repointed, the Magento PHP monolith is placed in read-only maintenance mode and subsequently decommissioned.

---
## The Cutover Runbook Checklist:
1. **T-24h:** Run full data reconciliation audit between MySQL and PostgreSQL.
2. **T-2h:** Lower DNS TTL to 60 seconds on all retail domains.
3. **T-0:** Flip Cloudflare routing rule for `/checkout` to Go `order-service`.
4. **T+1h:** Verify zero failed payments in Stripe / PayPal webhooks.
5. **T+48h:** Terminate legacy Magento EC2 instances.
