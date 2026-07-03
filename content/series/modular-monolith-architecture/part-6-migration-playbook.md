---
title: "Part 6: Migration Playbook â€“ Consolidating Microservices"
lastmod: "2026-07-03T14:59:00+07:00"
description: "A practical guide to safely transitioning from Microservices back to a Modular Monolith using the Reverse Strangler Fig pattern, Dual-write databases, and Conway's Law."
slug: "migration-playbook-microservices-to-modular-monolith"
tags: ["Migration", "Strangler Fig", "Modular Monolith", "Database", "Conway's Law"]
aliases:
  - "/series/modular-monolith-architecture/part-6-migration-playbook/"
  - "/series/modular-monolith-architecture/observability-in-process-modular-monolith-opentelemetry/part-6-migration-playbook.md"
---

# Part 6: Migration Playbook â€“ Consolidating Microservices into a Monolith

Breaking a Monolith into multiple Microservices is often referred to as the **Strangler Fig Pattern**. The process of consolidating distributed Microservices back into a central Monolith system follows the opposite direction: the **Reverse Strangler Fig Pattern**.

Although merging application code might seem simple, the highest risks of this process lie in the **Database** and the **Organization**. Below is a step-by-step practical Playbook to consolidate architecture safely (zero-downtime).

## 1. Conway's Law: Organizational Preparation

In 1968, Melvin Conway stated a classic law (Conway's Law):
> "Any organization that designs a system (defined broadly) will produce a design whose structure is a copy of the organization's communication structure."

You cannot successfully transition from Microservices to a Modular Monolith if your organization still maintains dozens of small teams operating in silos (independently, without communication).
**Action:**
- You must group small Engineering Teams into larger **Domain Teams** (Macro-teams).
- Establish clear Code Contribution rules on a shared repository (Monorepo codebase) before writing the first line of merged code.

## 2. Reverse Strangler Fig Pattern: Merging Code with Zero Downtime

The goal of this model is to bring features from an external Microservice into the core Monolith without the end-user ever noticing.

**Step 1: Create a New Module Inside the Monolith**
Instead of writing completely from scratch, create a new package/module (e.g., `PaymentModule`) right inside the Modular Monolith, strictly applying Bounded Context boundaries (see Part 3). Import the logic from the old Microservice into this Module.

**Step 2: Build an Anti-Corruption Layer (Optional)**
If the data structure of the old Microservice is too different, build a translation layer (Anti-corruption layer) so the new Module can communicate cleanly with other Modules in the Monolith.

**Step 3: Routing at the API Gateway (Canary Routing)**
Use an API Gateway or Load Balancer (like NGINX, AWS ALB) to route traffic. Initially, push 95% of traffic to the old Microservice (Legacy) and 5% to the corresponding API on the Modular Monolith system (New). Test thoroughly for errors and gradually increase the ratio to 100%.

## 4. The Biggest Nightmare: Database Consolidation

Moving code won't kill a system, but making a mistake when moving data will destroy a business. The process of moving data from the Microservice's Database to a shared Schema in the Monolith's Database must use a **Dual-Write** strategy to guarantee absolute safety.

**Phase 1: Dual-Write**
- When the application receives a `CREATE` or `UPDATE` command, it will write data to both places: The old Microservice's Database and the corresponding Schema on the Monolith's Database.
- *Note:* Reading remains completely pointed at the old Microservice's Database.

**Phase 2: Historical Data Sync (Backfill)**
- Write asynchronous jobs to copy historical data from the Microservice DB to the Monolith DB without causing bottlenecks on the live system.
- Verify to ensure the total number of records matches perfectly on both sides.

**Phase 3: Switch Read Source**
- When both Databases are 100% synchronized, you change the system logic to begin Reading from the Monolith's Database.
- Maintain the Dual-write for a few weeks as a safety net (Fallback/Rollback gate). If there is an error in the new read logic, you can immediately switch back to reading from the old DB.

**Phase 4: Decommission the Microservice**
- Turn off the Dual-write feature. Operations are now exclusively on the Monolith DB.
- Shut down the old Microservice's server, archive its code repository, and complete the consolidation process.

> [!WARNING]
> **Data Risk:** Never perform a Database migration by "Stopping the system, Exporting a SQL file, Importing into the new DB, then Turning it back on." Downtime can last for hours if the import encounters an issue. The Dual-write model is mandatory for Production systems.

## Playbook Summary

Consolidating Microservices into a Modular Monolith is a project requiring meticulous care. It reduces long-term costs (FinOps) but will require short-term effort from the engineering team.

So, is there ever a time when we **SHOULD NOT** merge a service into a Monolith, or even have to **EXTRACT** it from the Monolith? Absolutely. Blindly pursuing a Monolith is equally dangerous. Let's explore the correct separation philosophy in **[Part 7: Extraction Pattern]({{< ref "part-7-extraction-pattern.md" >}})**.


