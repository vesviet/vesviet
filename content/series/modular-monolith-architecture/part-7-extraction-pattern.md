---
title: "Part 7: Extraction Pattern â€“ When Should You Extract Microservices?"
lastmod: "2026-07-03T14:59:00+07:00"
description: "Not everything belongs in a Monolith. Learn how to determine when a module should be extracted into a Microservice through lessons from Sentry, GitLab, and Shopify."
slug: "extraction-pattern-when-to-extract-microservices"
tags: ["Microservices", "Extraction", "Sentry", "GitLab", "Modular Monolith", "Architecture"]
aliases:
  - "/series/modular-monolith-architecture/part-7-extraction-pattern/"
  - "/series/modular-monolith-architecture/migration-playbook-microservices-to-modular-monolith/part-7-extraction-pattern.md"
cover:
  image: "/images/posts/golang-microservices-cover.png"
  alt: "Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal"
  relative: false
---

# Part 7: Extraction Pattern â€“ When Should You Extract Microservices?

Advocating for a **Modular Monolith** architecture does not equate to a conservative "put absolutely everything in one place" mentality. In reality, even the greatest Monolith systems like Shopify, Sentry, or GitLab possess a few "satellites" (Microservices) orbiting their central core.

The core issue is: **We only extract a feature into a Microservice when it truly deserves it**, not out of preference. Expert Sam Newman â€“ author of *Monolith to Microservices* â€“ emphasizes that: If you cannot successfully separate the Database Schema inside a Monolith, you will undoubtedly create a disastrous Microservice.

Below are **4 signals** indicating a Module has "graduated" and is ready to be extracted from the Modular Monolith.

## Signal 1: Resource-Specific Independent Scaling Needs

Sometimes, your application has a task that consumes system resources entirely differently from the rest of the business logic (standard CRUD operations).

**Case Study: Sentry and the Snuba/Relay services**
Sentry (the world's most popular error tracking platform) was built at its core as a massive Monolith running on Python (Django). However, they faced a problem: The rate at which clients sent error events (Events Ingestion) was thousands of times higher than the action of viewing reports on the web.
- Instead of forcing the web system (Django) to bear this massive traffic, Sentry extracted the event reception layer into an independent Microservice named **Relay** (rewritten entirely in **Rust** to optimize CPU and RAM).
- Simultaneously, the high-cardinality data storage and search phase was extracted into a separate service named **Snuba** (running on ClickHouse DB).
The rest of the business logic, from billing and account management to error analysis logic, continues to reside safely and neatly within the Python Monolith block.

## Signal 2: Specialized Environment & Language Requirements (Polyglot)

Sometimes, the programming language of the Monolith does not provide the best libraries or performance for a specific feature.

**Case Study: GitLab and Gitaly**
GitLab is an enormous Ruby on Rails Monolith project. But reading/writing directly to the Git repo's FileSystem using Ruby was extremely slow and created severe I/O Bottlenecks when scaling.
- GitLab decided to create a single specialized service to communicate with Git files on the hard drive, called **Gitaly**.
- Gitaly was written in **Go (Golang)** to handle concurrency and low-level I/O access far better than Ruby.
- However, GitLab is extremely disciplined: Gitaly *only* processes Git files. All authorization, organization management, and merge request features remain embedded in the Rails core. This is a perfect testament to "Extract the tool, Keep the business logic."

## Signal 3: Disparate Deployment Cadence

If your entire Monolith is typically released every 2 days, but one single module (e.g., an AI product recommendation algorithm module) needs configuration updates every 15 minutes from Data Scientists.

This disparity in risk cadence is a valid reason to extract the AI Module into an independent Microservice. This prevents AI configuration changes from disrupting the stable CI/CD lifecycle of the entire core system.

## Signal 4: Compliance Requirements and Organizational Boundaries

In large organizations, handling credit card information (PCI-DSS) or health/medical data (HIPAA) often must comply with strict security audit regulations.

If the entire Monolith contains credit card processing code, you must push millions of lines of code through expensive periodic audit processes. Extracting the Billing module into a small, compact system operated by a Dedicated Security Team is a wise strategic Organizational Boundary decision to save on legal and compliance costs.

## The Rule of "Tearing Down" the Database

Before you actually create a new repository and write a Microservice:
1. You must ensure that the Module within the Monolith already has a standard Bounded Context.
2. The Tables of that module must absolutely not be intertwined (JOINed) with the tables of another module.

Extract the Database Schema before you extract the Code. If the DB cannot be decoupled, the Code will never be able to run independently.

---

Thus, we have gone through all the theory and design processes. In **[Part 8: Case Study Matrix]({{< ref "part-8-case-study-matrix.md" >}})** (the final article of this Playbook series), we will validate all our reasoning with a comprehensive table of speaking numbers from Shopify, Stack Overflow, Target, Zulip, Notion, and Basecamp.


