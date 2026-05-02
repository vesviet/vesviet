---
title: "Phase 1: Timeline and Scale Evolution"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "A timeline of Alipay Double 11 scaling evolution from 2009 to the cloud-native era: crises, architectural resets, and operational maturity."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/executive-summary/) • [Next →](/series/alipay-double-11/phase-2-architecture/)

## Overview

**Double 11 (Singles’ Day)** began in 2009 and grew into one of the largest online commerce peak events in the world. For Alipay, it became an annual forcing function: every year demanded new throughput, lower latency, and higher certainty under extreme load.

This phase captures the scaling journey as a sequence of constraints and responses: from early manual scaling, to an architecture reset (unitization/LDC), to deterministic operations (full-link stress testing), and finally to cloud-native efficiency.

## Timeline (Key Milestones)

### 2009: A modest start, a new kind of peak
- **Event**: First major promotion on Taobao Mall (later Tmall).
- **Scale**: Dozens of brands; revenue on the order of tens of millions CNY.
- **Engineering reality**: Traffic spiked several times above baseline; engineers relied heavily on manual interventions and vertical tuning.

### 2010: Peak preparedness becomes intentional
- Double 11 entered the routine stability agenda rather than being treated as a one-off surprise.
- Capacity planning was still heuristic (over-provisioning with large multipliers), but it began to formalize.
- Early stress testing was largely manual and incomplete.

### 2012: The scaling crisis (multiple hard limits at once)

Several ceilings collided:
- **Database bottlenecks** became existential (cost and scalability limits).
- **Connection limits / throughput ceilings** showed that the system could not be pushed much further by tuning.
- **Physical infrastructure constraints** (power/cooling) highlighted that “just add bigger machines” was not a reliable strategy.

Outcome: a clear conclusion that the next order of magnitude required an architectural shift, not incremental optimization.

### 2013: LDC (Logical Data Center) and unitization debut

Target: **20,000 payments per second** with a compressed delivery timeline.

Breakthrough: **unitization via LDC**:
- Split the system into independent **units** with service and data boundaries.
- Route traffic into the correct unit (cell) to isolate blast radius and scale horizontally.

Result: the first major step from centralized bottlenecks toward horizontally scalable capacity.

### 2014: From “uncertain” to “deterministic” via full-link stress testing

Problem: pre-event confidence was widely described as too low to be acceptable (the system “might survive” rather than “will survive”).

Solution: **automated, end-to-end stress testing** (full-link):
- Test the *real* production path under controlled isolation.
- Catch systemic issues (dependencies, bottlenecks, failure cascades) that component tests miss.

Result: confidence rose materially, and peak readiness became repeatable rather than heroic.

### 2019: Peak record milestones
- Reported peaks reached **hundreds of thousands TPS** for Alipay.
- The event was no longer just a performance story; it was an operational and reliability system built to prevent data loss and minimize incident impact.

### 2020+: Cloud-native era (elasticity and efficiency)
- Cloud-native adoption was positioned as the fastest path to improved elasticity and operational efficiency.
- The focus expanded from “survive the peak” to “survive the peak cheaply and repeatedly”: cost per transaction, time-to-prepare, and automation depth became first-class metrics.

## What Changed Across the Decade

The most important evolution is not a single technology choice; it is a shift in **operating model**:

- **From vertical scale to horizontal scale**: unitization/cell architecture.
- **From hope-based readiness to test-based confidence**: full-link stress testing.
- **From manual peak war rooms to automated peak pipelines**: repeatable procedures, checklists, and instrumentation.

## Next

Continue to [Phase 2: Core Architecture](/series/alipay-double-11/phase-2-architecture/) to see how **LDC/unitization**, **multi-active**, and the **database/messaging layers** work together to make peak scale possible.
