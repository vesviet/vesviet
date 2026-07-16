---

title: "Part 6: Migration Playbook – Consolidating Microservices"
lastmod: "2026-07-03T14:59:00+07:00"
description: "A practical guide to safely transitioning from Microservices back to a Modular Monolith using the Reverse Strangler Fig pattern, Dual-write databases, and"
slug: "migration-playbook-microservices-to-modular-monolith"
tags: ["Migration", "Strangler Fig", "Modular Monolith", "Database", "Conway's Law"]
aliases: ["/series/modular-monolith-architecture/part-6-migration-playbook/", "/series/modular-monolith-architecture/observability-in-process-modular-monolith-opentelemetry/part-6-migration-playbook.md"]
cover: {'image': 'images/posts/golang-microservices-cover.png', 'alt': 'Modular Monolith Architecture Masterclass: Go, DDD, bounded contexts, and microservices reversal', 'relative': False}
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/modular-monolith-architecture/migration-playbook-microservices-to-modular-monolith/"
ShowToc: true
TocOpen: true
---

**Answer-first:** Decommissioning microservices and returning to a Modular Monolith requires a structured Reverse Strangler Fig migration playbook. By consolidating database tables into separate schemas within a single Postgres instance, executing dual-writes through transactional outbox patterns, and routing traffic dynamically via feature flags, teams can merge systems with zero downtime.

> **Prerequisite:** Before reading this part, please ensure you have read the previous article in this series: [Part 5: Observability in Memory – When Everything Shares a Single Call Stack]({{< ref "part-5-observability.md" >}}).

### What You'll Learn That AI Won't Tell You
- **Database Consolidation Math:** How to merge connection pools to optimize database RAM utilization.
- **Transactional Outbox Implementations:** The SQL schema design for safe event auditing during migrations.
- **Canary Merging Safety:** Running dual-writes for 14 days to audit state reconciliation before switching readers.

# Part 6: Migration Playbook – 
## 4. Transactional Outbox Pattern in Monolith Migration

During the migration from isolated Microservices to a Modular Monolith, database tables are consolidated. To guarantee eventual consistency between modular databases without using distributed two-phase commits, we use the Transactional Outbox pattern.

### Go Outbox Polling Worker
The following background worker polls an outbox table and dispatches messages to the event bus in a reliable, transactional fashion.

```go
package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

type OutboxEvent struct {
	ID        int64
	Topic     string
	Payload   string
	Status    string
}

type OutboxWorker struct {
	db *sql.DB
}

func (w *OutboxWorker) Run(ctx context.Context) {
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			w.processPendingEvents()
		}
	}
}

func (w *OutboxWorker) processPendingEvents() {
	// Query pending events
	events := []OutboxEvent{
		{ID: 1, Topic: "PaymentCaptured", Payload: "{\"amount\": 100}", Status: "PENDING"},
	}
	
	for _, event := range events {
		// Publish event to local bus
		fmt.Printf("Outbox dispatching event %d: %s\n", event.ID, event.Payload)
		// Mark event as processed in the database
	}
}

func main() {
	worker := &OutboxWorker{db: nil}
	ctx, cancel := context.WithTimeout(context.Background(), 500 * time.Millisecond)
	defer cancel()
	
	go worker.Run(ctx)
	time.Sleep(300 * time.Millisecond)
}
```

### Relational Schema Merging Strategy
When consolidating database tables, developers must apply a disciplined approach:
1. **Schema Separation:** Ensure each module uses its own schema namespaces (e.g. `billing.invoice`, `inventory.stock`).
2. **Remove Foreign Keys:** Do not create physical foreign keys across module schemas. Use logical validation in code instead.
3. **Outbox Synchronization:** Keep the outbox table inside the same transaction as the database updates to prevent data loss.
4. **Gradual Deprecation:** Keep both database connections open during the migration window, routing traffic dynamically using adapters.

### Technical Appendix: Blue-Green Database Merges and Data Reconciliation
Merging live databases from separate microservices back into a shared monolithic database clusters requires zero downtime:
- **Deploy Monolithic Database Instance:** Set up a database instance with separate schemas configured for each module.
- **Enable Replication:** Use replication tools (like AWS DMS or Debezium) to sync tables from old microservice databases to the monolithic schemas in real-time.
- **Double Writes:** Configure the service adapter layer to write new data to both the old and new instances.
- **Run Reconciliation Scripts:** Run daily checksum scripts to verify column values are identical on both databases.
- **Cut Over Reads:** Divert read queries to the new database, keeping the double-write layer active to preserve the rollback path.
- **Disable Old Instances:** Shut down the old microservice databases once data parity is verified for a continuous 7-day cycle.




Consolidating Microservices into a Monolith

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

## 5. SQL Database Schema Merge & Outbox Table Structure

Before merging application code, database tables must be migrated under a single Postgres instance. Below is the SQL script to co-locate schemas and define a transactional outbox table to queue synchronization events during the transition phase.

```sql
-- Create distinct schemas inside the consolidated database
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS inventory;

-- Define billing payments table
CREATE TABLE billing.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(50) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Define transaction outbox table for audit logging
CREATE TABLE billing.outbox (
    id BIGSERIAL PRIMARY KEY,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for processing optimization
CREATE INDEX idx_outbox_unprocessed ON billing.outbox (id) WHERE processed = FALSE;

-- Trigger to log outbox events on new payments
CREATE OR REPLACE FUNCTION billing.queue_payment_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO billing.outbox (aggregate_type, aggregate_id, event_type, payload)
    VALUES ('Payment', NEW.id::text, 'PaymentProcessed', json_build_object(
        'order_id', NEW.order_id,
        'amount', NEW.amount,
        'status', NEW.status
    ));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_payment_processed
    AFTER INSERT ON billing.payments
    FOR EACH ROW
    EXECUTE FUNCTION billing.queue_payment_event();
```

So, is there ever a time when we **SHOULD NOT** merge a service into a Monolith, or even have to **EXTRACT** it from the Monolith? Absolutely. Blindly pursuing a Monolith is equally dangerous. Let's explore the correct separation philosophy in **[Part 7: Extraction Pattern]({{< ref "part-7-extraction-pattern.md" >}})**.

---

## Navigation & Next Steps

[← Previous Part]({{< ref "part-5-observability.md" >}})
[Next Part →]({{< ref "part-7-extraction-pattern.md" >}})

🔗 **Next Step:** Continue to [Part 7: Extraction Pattern – When Should You Extract Microservices?]({{< ref "part-7-extraction-pattern.md" >}})

Need help implementing this architecture in your organization? [Contact us](/contact/) or [hire our technical consulting team](/hire/) to review your system design and codebase.
