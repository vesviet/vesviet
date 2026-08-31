---
title: "Part 6: Phase 1 — Strangler Fig: Offloading the Product Catalog"
date: 2026-05-12T10:00:00+07:00
lastmod: 2026-08-16T12:00:00+07:00
author: "Lê Tuấn Anh"
description: "Phase 1 of the Strangler Fig pattern: Offloading 80% of read traffic from Magento to Go Catalog & Search microservices behind Cloudflare Edge."
categories: ["Series", "Software Engineering", "Architecture"]
tags: ["Strangler Fig", "Cloudflare", "Edge Computing", "Redis", "Golang", "Microservices"]
series: ["composable-commerce-migration"]
weight: 7
slug: "part-6-phase1-strangler-fig"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-6-phase1-strangler-fig/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 6: Phase 1 — Strangler Fig: Offloading the Product Catalog"
  relative: false
keywords: ["strangler fig pattern ecommerce", "cloudflare edge routing microservices", "catalog offloading magento", "zero downtime migration"]
---

[← Previous Chapter: Part 5: Migrating Magento EAV Schema](/series/composable-commerce-migration/part-5-eav-schema-migration/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 7: Phase 2 — Dual-Write CDC →](/series/composable-commerce-migration/part-7-phase2-dual-write/)

---

> **Answer-first:** Phase 1 of the Strangler Fig migration routes catalog read traffic (`/products/*`, `/catalog/*`, `/search/*`) to high-speed Go microservices via Cloudflare Edge Workers while keeping Magento active for checkout. This offloads **82% of server compute load** from the legacy monolith with zero downtime.

---
```mermaid
flowchart TD
    Client["Client Browser / Mobile App"] --> Edge["Cloudflare Edge Worker (Traffic Router)"]
    Edge -->|"/products/* & /search/* (82% Traffic)"| GoCatalog["Go Catalog & Search Service (K8s)"]
    Edge -->|"/checkout/* & /customer/* (18% Traffic)"| Magento["Legacy Magento Monolith (PHP/MySQL)"]
```

---

## 1. Cloudflare Edge Routing Implementation

```typescript
// cloudflare-edge-router.ts
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Route Catalog & Search to new Go Microservices
    if (url.pathname.startsWith('/api/v1/products') || url.pathname.startsWith('/api/v1/search')) {
      return fetch(`https://catalog-api.example.com${url.pathname}${url.search}`, request);
    }

    // Fallback all other requests (Checkout, Admin) to legacy Magento
    return fetch(`https://legacy-magento.example.com${url.pathname}${url.search}`, request);
  }
};
```
