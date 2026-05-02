---
title: "Phase 3: Operations Playbook"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Operational readiness for Double 11: capacity planning, full-link stress testing, incident command, dashboards, downgrade strategies, and checklists."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/phase-2-architecture/) • [Next →](/series/alipay-double-11/phase-4-technology/)

This phase is about how peak performance becomes **repeatable**. The core claim: peaks are won in operations, not heroics.

## 3.1 Capacity Planning

Capacity planning for peak events is fundamentally a prediction problem under uncertainty.

Common patterns in mature peak readiness:
- **Peak forecasting** using historical curves + product plans + marketing inputs.
- **Safety margins** based on known unknowns (dependencies, tail latencies, cache miss storms).
- **Bottleneck-first reviews**: DB, network, MQ, hot keys, and “global” dependencies.
- **Explicit downgrade plans**: define what can be turned off to protect the payment core.

Good capacity planning is not a spreadsheet; it is a living process with drill-down ownership.

## 3.2 Full-Link Stress Testing (Making confidence deterministic)

Component tests do not predict peak behavior. Full-link testing validates the *real* production path:
- The same service graph.
- The same dependency surfaces.
- Production-like concurrency and hotspots.

What full-link testing usually requires:
- Traffic replay or high-fidelity traffic generation.
- Strict data isolation (shadow tables / isolated accounts / isolation layers).
- End-to-end observability to detect where time and failures go.

The operational payoff:
- Catch systemic issues early (cascades, timeouts, retries, “thundering herds”).
- Turn pre-event readiness from “hope” into measurable confidence.

## 3.3 Incident Command and Monitoring

At peak scale, the goal is not “no incidents.” The goal is:
- **Detect fast**
- **Classify correctly**
- **Mitigate safely**
- **Recover predictably**

A strong incident setup typically includes:
- A command center operating model (roles, comms, escalation paths).
- Golden-signal dashboards (latency, traffic, errors, saturation) + business KPIs.
- Runbooks for known failure classes (DB pressure, MQ lag, cache failure, hot partitions).
- Post-incident reviews that produce permanent fixes (not blame).

## 3.4 Downgrade and Degrade Strategies

During extreme load, protecting the payment core often means turning optional paths into best-effort:
- Disable non-critical features (recommendations, long-tail queries, expensive joins).
- Switch to cached or approximated results.
- Shed traffic by tiers (rate-limits, queueing, admission control).

The key is that degrade plans must be:
- Pre-defined,
- Tested in drills,
- Observable in dashboards,
- Reversible.

## 3.5 Operational Checklist (Template)

### Pre-event (T-30 days)
- Confirm peak forecast + assumptions.
- Run full-link tests and record bottleneck owners.
- Freeze risky changes; define release gates and rollback rules.
- Validate degrade plans and toggles.

### Pre-event (T-7 days)
- Re-run full-link tests with the final traffic model.
- Drill incident command and escalation.
- Validate DB/MQ capacity and failover.
- Validate dashboards, alerts, and on-call coverage.

### During event (T-0)
- Monitor golden signals + business KPIs continuously.
- Apply throttles/degrades early (don’t wait for collapse).
- Track anomalies and mitigation actions in a shared log.

### Post-event (T+1 day)
- Postmortems with action items and owners.
- Compare forecast vs actual; update models.
- Backlog the hard fixes (hot keys, global dependencies, unsafe retries).

## Key Takeaways

1. **Automation is a force multiplier**: it reduces peak readiness headcount while improving reliability.
2. **Full-link testing is the confidence engine**: it converts uncertainty into engineering work.
3. **Peak operations is a product**: dashboards, checklists, drills, and runbooks are first-class artifacts.
