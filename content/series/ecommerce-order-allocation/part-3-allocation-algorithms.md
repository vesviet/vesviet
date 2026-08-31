---
title: "Part 3: Allocation Algorithms — Greedy vs. Mixed-Integer Linear Programming"
date: 2026-08-19T10:00:00+07:00
lastmod: 2026-08-24T14:00:00+07:00
author: "Lê Tuấn Anh"
description: "Algorithmic showdown for order allocation: Greedy Nearest-Neighbor heuristics vs. Mixed-Integer Linear Programming (MILP) optimization solvers."
categories: ["Series", "Algorithms", "Optimization"]
tags: ["Algorithms", "MILP", "Linear Programming", "Heuristics", "Optimization"]
series: ["ecommerce-order-allocation"]
weight: 5
slug: "part-3-allocation-algorithms"
canonicalURL: "https://tanhdev.com/series/ecommerce-order-allocation/part-3-allocation-algorithms/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 3: Allocation Algorithms"
  relative: false
keywords: ["order allocation algorithms", "milp optimization ecommerce", "greedy order routing"]
---

[← Previous Chapter: Part 2: Real-Time Inventory](/series/ecommerce-order-allocation/part-2-inventory-realtime/) | [Series Hub](/series/ecommerce-order-allocation/) | [Next Chapter: Part 4: Anticipatory Shipping →](/series/ecommerce-order-allocation/part-4-amazon-condor-anticipatory/)

---

> **Answer-first:** Greedy algorithms run in $O(N)$ (<2ms) and work well for simple carts. For complex multi-item baskets across 20+ fulfillment centers, MILP solvers achieve **12–18% lower total shipping costs** within a 35ms compute budget.

---
