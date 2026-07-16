---
title: "Shopee Architecture: Scaling for Flash Sales"
date: "2026-05-05T08:00:00+07:00"
lastmod: "2026-05-05T08:00:00+07:00"
draft: false
weight: 140
description: "A structured series on how Shopee evolved its architecture to handle extreme high concurrency during 11.11 and Flash Sales."
ShowToc: true
TocOpen: true
cover:
  image: "images/posts/shopee-flash-sale-cover.png"
  alt: "Shopee Architecture series: scaling for flash sales — rate limiting, Redis, and distributed systems"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/shopee-architecture/"
---

This series explores the core architectural patterns and technologies Shopee uses to handle millions of concurrent users, specifically focusing on extreme traffic spikes during Flash Sales and mega-campaigns like 11.11.

## Series Contents

- [Chapter 1: Microservices Foundation]({{< ref "/series/shopee-architecture/01-microservices-foundation.md" >}})
- [Chapter 2: Flash Sale Engine]({{< ref "/series/shopee-architecture/02-flash-sale-engine.md" >}})
- [Chapter 3: Traffic Shield]({{< ref "/series/shopee-architecture/03-traffic-shield.md" >}})
- [Chapter 4: Database Scale]({{< ref "/series/shopee-architecture/04-database-scale.md" >}})
- [Chapter 5: Observability]({{< ref "/series/shopee-architecture/05-observability.md" >}})

---

*Looking for a practical guide to migrating a legacy e-commerce platform to a microservices architecture similar to Shopee's? See our **[Composable Commerce Migration Series]({{< ref "/series/composable-commerce-migration/_index.md" >}})** for a step-by-step production case study.*
