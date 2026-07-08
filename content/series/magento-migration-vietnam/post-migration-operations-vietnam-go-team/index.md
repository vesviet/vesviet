---
title: "Post-Magento Operations: Running a Vietnam Go Team in Production"
slug: "post-migration-operations-vietnam-go-team"
author: "Lê Tuấn Anh"
date: "2026-07-11T08:00:00+07:00"
lastmod: "2026-07-11T08:00:00+07:00"
draft: false
series: ["magento-migration-vietnam"]
tags: ["Operations", "Vietnam", "Golang", "SRE", "On-Call", "Observability", "Microservices", "Post-Migration"]
categories: ["Engineering Management", "Operations"]
description: "How a Vietnam Go team owns production after Magento migration — SLO design, on-call rotation, runbooks, and error budget tracking across timezones."
ShowToc: true
TocOpen: true
cover:
  image: "images/series/post-migration-operations-vietnam-cover.png"
  alt: "Post-migration operations with a Vietnam Go team: SLO, on-call, observability"
  relative: false
canonicalURL: "https://tanhdev.com/series/magento-migration-vietnam/post-migration-operations-vietnam-go-team/"
---

**Answer-first:** A Vietnam Go team can own full production operations for a post-Magento microservices platform — but only if SLOs, runbooks, and escalation paths are defined before cutover, not after. Teams that hand off operations without this infrastructure spend their first 90 days in reactive incident mode. Teams that build it before day one transition smoothly from migration team to engineering team.

> **Series context:** This is the final technical post in the [E-Commerce Re-Architecture in Vietnam](/series/magento-migration-vietnam/) series. For the migration execution playbook, see [Remote Team Playbook: Vietnam Engineers Through Migration](/series/magento-migration-vietnam/remote-team-vietnam-magento-migration/).

---

## The Ops Transition Problem

The moment Magento is decommissioned, the migration team becomes the operations team. The same Vietnam engineers who spent 12 months running Strangler Fig migrations are now responsible for:

- 10+ Go microservices in production
- Kafka event pipelines processing thousands of messages/minute
- Postgres databases per service (each with its own backup and failover story)
- A Kubernetes cluster running on AWS/GCP
- An on-call rotation that covers weekends and holidays

Most teams handle this poorly because the transition is treated as an event ("we decommissioned Magento on March 15!") rather than a capability transfer that must be built progressively throughout the migration.

This post covers how to build that capability before you need it.

---

## Phase 4 Must-Do: Operations Foundations Before Magento Decommission

Do not decommission Magento until these 6 items exist:

| # | Item | Why it can't wait |
|---|------|------------------|
| 1 | SLO definitions for all 10+ services | Can't measure operations health without a baseline |
| 2 | Error budget policy per service | Can't make release decisions without burn rate data |
| 3 | Runbook for top 5 failure scenarios per service | Vietnam on-call can't diagnose without documentation |
| 4 | On-call rotation roster with tested PagerDuty integration | P0 without on-call = hours of triage |
| 5 | Observability dashboards (Grafana) for all services | Can't diagnose what you can't see |
| 6 | Incident post-mortem template | First incident without a template wastes 3 hours |

If any of these are missing at cutover time, delay the decommission. The cost of running Magento hot standby for 2 more weeks ($1,000–$2,000) is trivially cheaper than operating blind in production.

---

## SLO Definition: What the Vietnam Team Owns

### The Right SLO Structure

Each Go service needs three SLO levels:

1. **Availability SLO:** What percentage of requests succeed in a given period?
2. **Latency SLO:** What percentage of requests complete within a defined time?
3. **Data freshness SLO** (for async services): How fresh is the data consumers receive?

**Example SLOs for the Order service:**

| SLO | Target | Measurement window |
|-----|--------|-------------------|
| Availability | 99.9% | 30 days rolling |
| P99 checkout latency | < 300ms | 30 days rolling |
| Order event processing lag | < 5 seconds | Real-time |

**99.9% availability = 43.8 minutes of allowable downtime per month.** This is your error budget.

### Who Sets SLOs?

SLOs are defined jointly by the Vietnam tech lead and the client-side CTO:
- **Tech lead provides:** what's technically achievable given the infrastructure and team capacity
- **CTO provides:** what's required to meet business commitments to customers

The negotiation is real. A P99 checkout latency of < 100ms may require 2× infrastructure spend. A < 300ms SLO may be achievable at current cost. The CTO decides based on customer experience requirements; the tech lead commits to feasibility.

**Do not let engineers define SLOs alone.** They will set conservative targets that are easy to meet. SLOs should be ambitious enough that 20–25% of months will require investigation.

---

## Error Budget Tracking

Error budget = the allowable failure time per SLO period. For 99.9% availability over 30 days: **43.8 minutes of downtime is your budget.**

### Weekly Error Budget Review

The Vietnam tech lead generates a weekly error budget report. It contains:
1. Current error budget remaining for each service (as % of monthly budget)
2. Burn rate (are we spending budget faster or slower than the 30-day average?)
3. Incidents that consumed budget this week
4. Forecast: "At current burn rate, we will exhaust this month's budget on [date]"

If burn rate is > 2× baseline: **freeze non-critical releases** until root cause is identified. If burn rate is > 5× baseline: **escalate to client-side CTO same day**.

### Error Budget Policy

Define this before cutover:

| Scenario | Action |
|----------|--------|
| Budget > 50% remaining | Normal operations, continue release cadence |
| Budget 20–50% remaining | Review planned releases; postpone low-priority changes |
| Budget < 20% remaining | Halt new feature releases; engineering focuses on reliability |
| Budget exhausted | No releases until next period; blameless post-mortem required |

This policy prevents the "we're almost out of error budget but we have a committed release for Friday" crisis.

---

## Observability Stack for Remote Operations

A Vietnam team operating services they cannot physically inspect needs exceptional observability. The three pillars of the post-migration observability stack:

### 1. Metrics (Prometheus + Grafana)

**Mandatory dashboards per service:**
- **RED dashboard:** Rate (requests/second), Errors (error %), Duration (P50/P95/P99 latency)
- **Service topology:** How much traffic is flowing between services? Where are the bottlenecks?
- **Infrastructure health:** CPU, memory, Kubernetes pod restarts, Kafka consumer lag

**Dashboard ownership:** Each Vietnam engineer owns the dashboards for the services they maintain. Dashboards are reviewed in the weekly architecture sync. If a dashboard has no alerts, it is not being used.

### 2. Distributed Tracing (OpenTelemetry + Tempo/Jaeger)

In a 10-service distributed system, a slow checkout may be caused by:
- The Order service responding slowly (its own database issue)
- The Order service waiting on the Inventory service (downstream issue)
- The Inventory service waiting on a Kafka consumer to process a reservation event

Without distributed tracing, diagnosing this takes hours. With OpenTelemetry instrumented in every Go service and traces centralized in Tempo or Jaeger, the answer is visible in 30 seconds: "The Order service is fast, but the Inventory reservation call has P99 at 2.8 seconds — spike began at 14:23 UTC, 3 minutes after the weekly batch import started."

**Implementation requirement:** Every Go service must emit `trace_id` in all log lines. Every service must propagate the trace context header (`traceparent`) in all outbound calls. This is non-optional infrastructure.

### 3. Structured Logging (JSON + Loki/CloudWatch)

Log format for every service:

```json
{
  "timestamp": "2026-07-11T14:23:01Z",
  "level": "error",
  "service": "order-service",
  "trace_id": "abc123",
  "span_id": "def456",
  "customer_id": "[REDACTED]",
  "order_id": "ord_uuid_here",
  "event": "payment.charge.failed",
  "error": "stripe_error: card_declined",
  "duration_ms": 234
}
```

**Never log PII (customer email, card details, phone numbers)** — this is a Vietnam PDPL compliance requirement as of January 1, 2026, as well as GDPR obligation for EU customers.

---

## Runbook Design: What Vietnam On-Call Engineers Need

A good runbook answers the question: "It's 2 AM in Ho Chi Minh City and the Order service is returning 500 errors. I am on call. What do I do?"

### Runbook Structure (per failure scenario)

```markdown
## Scenario: Order Service High Error Rate (> 5% 5xx)

**Trigger:** PagerDuty alert fires when order_service_error_rate_5m > 0.05

**Diagnosis steps:**
1. Open Grafana → Order Service RED dashboard
2. Check if errors began at a deployment (compare error onset time to last deploy)
3. Check if errors correlate with Inventory service lag (Grafana → Service Topology)
4. Open Tempo → search for trace_id from a failed order, examine span breakdown
5. Check Postgres connection pool saturation (Grafana → order_service_db_pool)

**Resolution paths:**
- If deployment-correlated: rollback via ArgoCD (see: ArgoCD rollback runbook)
- If Inventory service lag: pause Order service Kafka consumer (see: consumer pause runbook)
- If DB connection exhaustion: restart order-service pods (kubectl rollout restart deployment/order-service)

**Escalation:**
- 30 min without resolution → wake tech lead
- 60 min without resolution → trigger rollback decision call
```

**Runbook quality bar:** A junior engineer who has been on the team for 2 weeks should be able to follow the runbook and either resolve the issue or accurately describe the situation to the tech lead during escalation.

### The 5 Runbooks Every Service Needs

1. High error rate (> 5% 5xx)
2. High latency (P99 > 3× SLO baseline)
3. Kafka consumer lag growing (> 10 minutes behind)
4. Database connection pool saturated
5. Pod crash loop (CrashLoopBackOff in Kubernetes)

For the Order service specifically, add:
6. Order event not appearing in downstream systems (inventory not reserved)
7. Saga compensation not triggering (payment failed but stock not released)

---

## On-Call Rotation Design

### The Vietnam On-Call Stack

A 6-engineer Vietnam team (standard migration team size) supports a rotating on-call schedule:

**Weekly rotation (recommended for steady state):**
- 1 primary on-call engineer per week (rotates across team)
- 1 secondary (escalation target) per week
- Tech lead is always the tertiary escalation

**During hot standby (first 30 days post-cutover):**
- Primary on-call: Vietnam engineer
- Secondary escalation: Vietnam tech lead (available within 30 minutes)
- Tertiary: Client-side architect (available within 60 minutes for rollback approval)

**Compensation:** On-call duty requires compensation above base salary. Budget 15–20% monthly premium for the on-call engineer's weeks. Build this into the contract from day one.

### On-Call Readiness Checklist (per engineer, before rotation)

- [ ] PagerDuty profile configured and tested (mobile alert received)
- [ ] All service runbooks reviewed (can navigate without searching)
- [ ] Kubernetes `kubectl` access confirmed (can list pods, view logs, restart deployments)
- [ ] Grafana dashboard bookmarks current
- [ ] ArgoCD rollback procedure tested in staging
- [ ] Contact numbers for tech lead and client-side escalation saved

---

## Knowledge Transfer: PHP to Go, Magento to Services

One underestimated challenge: your Vietnam team spent 12 months building the new system. They know it deeply. But the client-side team and any new engineers they hire post-migration may only know Magento.

**The PHP → Go mental model shift:**

| Magento PHP concept | Go microservice equivalent |
|--------------------|--------------------------|
| Magento observer events | Kafka events (domain events) |
| Magento API endpoint | Go gRPC/REST service endpoint |
| Magento admin panel | Internal tools + service dashboards |
| Magento extension | Dedicated Go microservice |
| Database JOIN across tables | Service-to-service API call |
| Magento cron job | Go worker service with scheduled jobs |
| Magento cache (Redis Varnish) | Service-level read caching + CDN |

**Knowledge transfer plan:**
1. **Month 1 post-cutover:** Each Vietnam engineer records a 15-minute Loom walkthrough of each service they own (architecture, common operations, known failure modes)
2. **Month 1–2:** Pair each client-side engineer with a Vietnam engineer for a 2-week "shadow" period on their service
3. **Month 3:** Client-side engineers take primary on-call for non-critical services; Vietnam engineers provide escalation backup
4. **Month 6:** Full on-call rotation includes client-side engineers; Vietnam team focuses on feature development

---

## When to Keep Magento On-Call vs. Full Go Team Cutover

The most common mistake in operations transition is premature Magento decommission.

**Keep Magento hot standby running until:**
- Zero P0 incidents for 30 consecutive days on Go services
- All 5 most-likely failure scenarios have occurred at least once and been resolved (the team has "earned" their runbooks through practice)
- Error budget for all critical services remains > 70% at day 30

**Decommission Magento when:**
- The team has institutional knowledge of production failure patterns (not just theoretical runbooks)
- The client-side CTO is comfortable with no rollback path
- A full data export of Magento's database is archived and stored (for audit and historical lookup)

Rushing Magento decommission to "close the chapter" is a project management reflex, not an engineering decision. Hot standby costs $500–$1,500/month in infrastructure. That is cheap optionality.

---

## The Long-Term Operating Model

After 12–18 months of stable operations, the post-migration operating model looks like this:

**Steady-state Vietnam team (not migration team):**
- 1 Go tech lead / squad lead
- 2 senior Go engineers (service owners)
- 1 DevOps/platform engineer
- 0.5 QA engineer (automated test maintenance)

**Client-side role:**
- 1 product manager (roadmap ownership)
- 0.5 technical architect (architecture review, ADR approval)

**Development cadence:**
- 2-week sprints with demo at sprint end
- Monthly architecture review (60 min)
- Quarterly performance review and SLO target adjustment

**At this point, the cost model looks like:**
- Vietnam team: $150,000–$180,000/year
- Client-side overhead: 0.5 FTE equivalent
- Infrastructure: $24,000–$36,000/year
- **Total: $174,000–$216,000/year**

Compared to:
- Magento annual TCO (platform, maintenance, security): $80,000–$400,000/year
- Unrealized feature velocity: difficult to quantify but typically 3–5× improvement in features shipped per quarter

---

## FAQ

### How do we handle production support for B2B customers who call directly?

B2B customers often escalate technical issues through account management, not standard support. Build an "account manager escalation" runbook that account managers can follow: specific Slack channel, specific SLA (1-hour response during business hours), and a designated Vietnam engineer as the account-facing technical contact.

### What if the Vietnam team loses a key engineer post-migration?

Mitigation built into the system:
- No single engineer is the sole owner of production knowledge (pair programming + documentation enforced)
- All runbooks are reviewed quarterly for accuracy
- On-call rotation ensures all engineers have practical debugging experience, not just the expert

Budget 4–6 weeks of knowledge transfer for any departure. The documentation-first culture makes this significantly less painful than the same departure in a Magento-era shop where knowledge lived in one PHP developer's head.

### How do we know the Vietnam team is performing at steady state?

Metrics that matter in steady state:
- **Deployment frequency:** Are they shipping multiple times per week? (Target: 2–3 deploys/week per service)
- **Change failure rate:** What percentage of deployments require a rollback? (Target: < 5%)
- **MTTR:** When incidents occur, how long to resolve? (Target: < 30 minutes for P1)
- **Error budget utilization:** Are services staying within their error budgets? (Target: < 50% utilization most months)

Monthly review of these 4 metrics provides a clear picture of operations health without requiring line-level management.

### Should we move to a single Vietnam-based team owning everything vs. maintaining client-side engineers?

The right answer depends on your risk tolerance and product velocity requirements. Full Vietnam ownership works well for platform stability and cost efficiency. Hybrid (Vietnam execution + client-side product/architecture) works better for teams that need to ship product features quickly and require close business alignment.

For most B2B SaaS companies: hybrid model is the stable long-term state. Full Vietnam ownership is appropriate only after 12+ months of demonstrated operational maturity.

---

## Closing: The Migration Is Not the Destination

Magento migration is not a project with an end date. It is the beginning of a different operating model — one where your Vietnam Go team is a product engineering team, not a maintenance team.

The measure of a successful migration is not "Magento is gone" or "the new services are running." It is:

- Your engineers ship product features in days, not weeks
- Your platform scales during flash sales without 502 errors
- Your B2B customers see configuration changes instantly, not after the next deployment window
- Your engineering team's retention improves because they're building, not firefighting

That outcome is achievable with a properly staffed, properly supported Vietnam team. This series documents exactly how to get there.

---

*End of series: [E-Commerce Re-Architecture in Vietnam](/series/magento-migration-vietnam/)*

*Previous: [Managing Vietnam Engineers Through a Magento Migration →](/series/magento-migration-vietnam/remote-team-vietnam-magento-migration/)*

*For the technical foundation this team operates: [Composable Commerce Migration: Full Series →](/series/composable-commerce-migration/)*

*Ready to plan your migration? [Book a Migration Architecture Review →](/hire/)*
