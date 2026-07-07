---
title: "Part 3: Domain-Driven Design (DDD) Boundaries in a Modular Monolith"
lastmod: "2026-07-03T14:59:00+07:00"
description: "How to keep a Monolith from becoming a 'Big Ball of Mud'? A guide to establishing Module boundaries using Bounded Contexts, Spring Modulith, and Packwerk."
slug: "ddd-module-boundaries-modular-monolith"
tags: ["Domain-Driven Design", "DDD", "Modular Monolith", "Spring Modulith", "Packwerk", "Architecture"]
aliases:
  - "/series/modular-monolith-architecture/part-3-ddd-module-boundaries/"
  - "/series/modular-monolith-architecture/finops-cost-reality-microservices-tax/part-3-ddd-module-boundaries.md"
cover:
  image: "/images/posts/golang-microservices-cover.png"
  alt: "Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal"
  relative: false
---

# Part 3: Domain-Driven Design (DDD) Boundaries in a Modular Monolith

The biggest reason engineering teams fear the Monolith architecture is due to terrible past experiences with "Spaghetti Monoliths" or the "Big Ball of Mud" â€” where the code for the Billing function calls directly into the database of the Cart function, creating an inextricable web of cross-dependencies.

To leverage the performance advantages of a Monolith while still achieving independent development velocity like Microservices, we must build a **Modular Monolith**. The key to this architecture is strictly applying **Domain-Driven Design (DDD)** principles and establishing hard "borders" right within the code.

## 1. Core Principle: Bounded Contexts and Internal APIs

In Microservices, if Service A wants to retrieve data from Service B, it is forced to call an HTTP API or gRPC; it cannot poke directly into B's Database. This is a physical barrier.

In a Modular Monolith, because all code resides in the same memory space, it's very easy to violate this rule. To prevent that, we create **Bounded Contexts** through architectural conventions:
- Each Domain/Module (e.g., `Billing`, `Inventory`, `User`) is isolated into its own folder/package.
- Each Module only exposes a set of Interfaces or Public Classes as an **Internal API**.
- **Golden Rule:** Other Modules must absolutely never call implementation classes (private/internal) or directly access the Database Tables of another Module. They must communicate via the Internal API.

## 2. Database Boundaries: Defending Against Cross-Schema JOINs

The most dangerous level of coupling in a Monolith isn't in the code, but in the Database. Executing a `JOIN` query between the `orders` table of the *Order* module and the `users` table of the *Identity* module completely destroys the ability to decouple modules.

**Standard design model (Database-per-module pattern):**
- Still share a single Database Server (to save hardware costs).
- Segregate data into separate Schemas (e.g., PostgreSQL schemas: `schema_orders`, `schema_identity`).
- If the Order module needs User information, the system will execute a method call within the application (e.g., `UserService.getUserById(id)`), retrieve the result into RAM, and process it in code (Application-level join) instead of using a direct SQL JOIN.
- If large-scale data synchronization is needed, use an **Internal Event Bus** (in-memory event-driven architecture) instead of sharing a common transaction.

## 3. Enforcing Boundaries with Automated Tools

Paper conventions are often broken when deadline pressure mounts. The solution adopted by leading tech companies is turning these conventions into Static Analysis tools that run directly during compilation or in the CI/CD pipeline.

### A. Spring Modulith (For Java / Spring Boot)
The **Spring Modulith** project provides tools to automatically detect and verify package structures. By integrating the **ArchUnit** library into the Unit Test suite, Spring Modulith ensures that:
- Internal classes within one Module's package are not accessed by another Module.
- Application Events are published and listened to correctly.
If an engineer intentionally violates a boundary, the Unit Test will fail right on their local machine, preventing garbage code from being merged into the main branch.

### B. Packwerk: Lessons from Shopify and Gusto (For Ruby on Rails)
Both **Shopify** and HR software company **Gusto** operate on massive Ruby on Rails Monolith architectures. To avoid chaos, they apply **Packwerk** (an open-source library developed by Shopify):
- The codebase is divided into **"Packs"** (virtual domains).
- Whenever the source code of Pack A calls into an internal class (private method) or directly queries the database of Pack B, Packwerk will print a Compile-time warning.
- Gusto shared that by applying Packwerk, they eliminated circular dependencies and **reduced Onboarding time by 50%** for new engineers, because the code structure became as clear as a microservices system.

## 4. DHH's "Citadel" Model (Basecamp)

David Heinemeier Hansson (DHH) - the creator of the Ruby on Rails framework, proposed the **"Majestic Monolith & Citadel"** model.
Accordingly, 99% of business logic will reside in the central "Citadel" (Monolith). However, if there is a specific function that requires distinct technology (like processing AI with Python, or handling massive WebSocket streams with Elixir), only then is it extracted into independent "Outposts."

This proves that the Modular Monolith is not a conservative "all-in-one" mindset, but an optimization mindset: Only distribute what truly needs to be distributed.

> [!FAQ]
> **Question: Does prohibiting SQL JOINs degrade the Monolith's performance?**
> **Answer:** For complex display tasks (Dashboards), calling multiple Internal APIs instead of 1 JOIN query might create a small overhead. To handle this, Modular Monolith systems often apply the **CQRS** (Command Query Responsibility Segregation) model â€“ separating the write database (containing strict module boundaries) and creating specialized materialized views (aggregated display tables) for reading (automatically updated via events).

Maintaining strict code borders helps you turn a Monolith into a collection of independent modules. But how do you ensure the Build and Test process for a massive CodeBase doesn't become overloaded? See Shopify's solution in **[Part 4: CI/CD Simplified]({{< ref "part-4-cicd-simplified.md" >}})**.


