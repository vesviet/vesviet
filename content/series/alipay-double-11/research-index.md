---
title: "Research Index"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Reading guide and index for the Alipay Double 11 Architecture research series."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
Tổng hợp nghiên cứu toàn diện về kiến trúc Alipay trong sự kiện Double 11, từ lịch sử 2009 đến công nghệ hiện đại 2024.

---

## Danh Sách Tài Liệu

### 📚 Core Documents

| File | Mô Tả | Độ Dài | Mục Tiêu |
|------|-------|--------|----------|
| **[vesviet](vesviet)** | Research Plan Overview | 194 dòng | Lộ trình nghiên cứu tổng quan |
| **[vesviet-phase1-timeline](vesviet-phase1-timeline.md)** | Timeline & Lịch Sử | 250 dòng | Hiểu bối cảnh: 2009 → 544K TPS |
| **[vesviet-phase2-architecture](vesviet-phase2-architecture.md)** | Kiến Trúc Kỹ Thuật | 400 dòng | LDC, OceanBase, Distributed Systems |
| **[vesviet-phase3-operations](vesviet-phase3-operations.md)** | Quy Trình Vận Hành | 300 dòng | Stress testing, Capacity planning |
| **[vesviet-phase4-technology](vesviet-phase4-technology.md)** | Công Nghệ Chi Tiết | 425 dòng | Middle Platform, CTU, Payment flow |
| **[vesviet-phase4-deep-dive](vesviet-phase4-deep-dive.md)** | Deep Dive Kỹ Thuật | 800 dòng | SOFAStack, RocketMQ, Storage Engine |
| **[vesviet-phase5-synthesis](vesviet-phase5-synthesis.md)** | Tổng Hợp & Bài Học | 350 dòng | Patterns, Metrics, Decision framework |
| **[vesviet-modern-tech-comparison](vesviet-modern-tech-comparison.md)** | So Sánh Công Nghệ Hiện Đại | 550 dòng | vs Kubernetes, Kafka, gRPC, v.v. |

**Tổng: ~3,300 dòng nghiên cứu**

---

## 🎯 Lộ Trình Đọc Theo Mục Tiêu

### 1. Executive Overview (30 phút)
👉 Đọc: **[Executive Summary](vesviet-executive-summary.md)** (file riêng)

Phù hợp cho:
- CTO, VP Engineering
- Product Managers
- Non-technical stakeholders
- Board presentations

### 2. Technical Deep Dive (4-8 giờ)
👉 Đọc theo thứ tự:
1. [Phase 1: Timeline](vesviet-phase1-timeline.md) - Bối cảnh lịch sử
2. [Phase 2: Architecture](vesviet-phase2-architecture.md) - LDC, OceanBase
3. [Phase 4 Deep Dive](vesviet-phase4-deep-dive.md) - SOFAStack, RocketMQ
4. [Modern Comparison](vesviet-modern-tech-comparison.md) - So sánh công nghệ

Phù hợp cho:
- System Architects
- Senior Engineers
- Tech Leads

### 3. Operations & Best Practices (2-4 giờ)
👉 Đọc:
1. [Phase 3: Operations](vesviet-phase3-operations.md) - Stress testing
2. [Phase 5: Synthesis](vesviet-phase5-synthesis.md) - Lessons learned

Phù hợp cho:
- DevOps Engineers
- SREs
- Engineering Managers

### 4. Full Comprehensive Study (1-2 tuần)
👉 Đọc tất cả các file theo thứ tự Phase 1 → 5 + Modern Comparison

Phù hợp cho:
- Research purposes
- Architecture design projects
- Technology migration planning

---

## 📊 Quick Reference

### Key Numbers

| Metric | Value | Context |
|--------|-------|---------|
| **544K TPS** | Peak transactions | Alipay Double 11 2019 |
| **61M QPS** | Queries per second | OceanBase peak |
| **707M tpmC** | TPC-C benchmark | World record |
| **10M+ TPS** | Message queue | RocketMQ peak |
| **200K+ TPS** | Per node | SOFARPC performance |
| **< 100ms** | Latency P99 | CTU risk scoring |
| **< 0.1%** | False positive | Fraud detection |
| **50%** | Cost reduction | Elastic architecture |
| **60% → 95%** | Confidence | System stability |

### Timeline Milestones

```
2009 ──┬── 50M CNY, 27 brands (Event đầu tiên)
       │
2012 ──┼── Khủng hoảng scale (Oracle limits, power crisis)
       │
2013 ──┼── LDC Architecture debut (20K TPS target)
       │
2014 ──┼── Automated stress testing (60% → 95% confidence)
       │
2015 ──┼── Middle Platform Strategy (大中台, 小前台)
       │
2016 ──┼── Elastic architecture (50% cost reduction)
       │
2019 ──┼── 544K TPS peak record
       │
2020 ──┴── Cloud-native full deployment
```

### Technology Stack Summary

```
Frontend:     Mobile Apps, Web, Mini Programs
              ↓
Gateway:      Traffic routing, Rate limiting, Auth
              ↓
Services:     SOFAStack (SOFABoot, SOFARPC, SOFAMesh)
              ↓
Middleware:   RocketMQ, Tair (Cache)
              ↓
Data:         OceanBase, POLARDB, OSS
              ↓
Infrastructure: PouchContainer, Kubernetes, Alibaba Cloud
              ↓
Security:     Ant Shield, CTU Risk Control
```

---

## 🔍 Search Guide

### Theo Chủ Đề

| Chủ Đề | File | Section |
|--------|------|---------|
| **LDC Architecture** | Phase 2 | 2.1 Logical Data Center |
| **RZone/GZone/CZone** | Phase 2 | 2.1 |
| **OceanBase** | Phase 2 | 2.2; Phase 4 Deep Dive | 4.4 |
| **Paxos Protocol** | Phase 2 | 2.2 |
| **SOFARPC** | Phase 4 | 4.4; Phase 4 Deep Dive | 4.2 |
| **RocketMQ** | Phase 4 Deep Dive | 4.3 |
| **Stress Testing** | Phase 3 | 3.2 |
| **CTU Risk Control** | Phase 4 | 4.2; Phase 4 Deep Dive | 4.5 |
| **Payment Flow** | Phase 4 | 4.3 |
| **Modern Tech Compare** | Modern Comparison | All |

### Theo Use Case

| Use Case | File | Mục Tiêu |
|----------|------|----------|
| Design distributed system | Phase 2 | LDC patterns |
| Choose message queue | Modern Comparison | Kafka vs RocketMQ vs Pulsar |
| Database migration | Modern Comparison | OceanBase vs CockroachDB vs TiDB |
| Implement stress testing | Phase 3 | Full-link testing guide |
| Build fraud detection | Phase 4 Deep Dive | CTU architecture |
| Service mesh decision | Modern Comparison | Istio vs Linkerd vs MOSN |

---

## 💡 Key Takeaways by File

### Phase 1: Timeline
- **"Impossible" 20K TPS** → Trở thành reality
- **2012 Crisis**: Oracle limits + power supply = forced innovation
- **Cultural insight**: "Worship Guan Gong" tradition

### Phase 2: Architecture
- **LDC**: Unitization = scalability
- **OceanBase**: Paxos + FPGA = 707M tpmC
- **Multi-active**: Geographic redundancy

### Phase 3: Operations
- **Confidence 60% → 95%**: Via automated testing
- **Full-link stress test**: Production-like simulation
- **200 people → 10 people**: Efficiency gain

### Phase 4: Technology
- **Middle Platform**: "大中台, 小前台" strategy
- **CTU**: 8-dimension risk analysis in 0.1s
- **SOFAStack**: Financial-grade infrastructure

### Phase 4 Deep Dive
- **SOFARPC**: 200K+ TPS per node
- **RocketMQ**: 10M+ TPS peak
- **OceanBase Storage**: LSM-tree + FPGA compaction
- **CTU ML**: GNN for fraud detection

### Phase 5: Synthesis
- **Patterns**: Modularization, Automation, Testing
- **Anti-patterns**: Vertical scaling, Manual processes
- **Metrics**: 5,440x growth in 10 years

### Modern Comparison
- **OceanBase vs**: CockroachDB, TiDB
- **RocketMQ vs**: Kafka, Pulsar
- **SOFARPC vs**: gRPC, Connect
- **Decision framework**: When to use which

---

## 🛠️ Tools & Resources

### Open Source Projects

| Project | Link | Description |
|---------|------|-------------|
| **OceanBase** | github.com/oceanbase/oceanbase | Distributed database |
| **SOFAStack** | github.com/sofastack | RPC, Mesh, Boot |
| **RocketMQ** | github.com/apache/rocketmq | Message queue |
| **Seata** | github.com/seata | Distributed transactions |
| **PouchContainer** | github.com/AliyunContainerService/pouch | Container runtime |

### External Resources

| Resource | URL | Type |
|----------|-----|------|
| Alibaba Cloud Blog | alibabacloud.com/blog | Articles |
| OceanBase Blog | en.oceanbase.com/blog | Technical |
| SOFAStack Docs | www.sofastack.tech | Documentation |
| Alipay Papers | VLDB, SIGMOD | Academic |

### Academic Papers

1. "OceanBase: A 707 Million tpmC Distributed Relational Database System" (VLDB 2022)
2. "Paxos Made Simple" (Lamport)
3. "The Dataflow Model" (Google)

---

## 📈 Next Steps

### Immediate Actions
- [ ] Read [Executive Summary](vesviet-executive-summary.md) for overview
- [ ] Identify relevant phases cho use case của bạn
- [ ] Bookmark [Modern Comparison](vesviet-modern-tech-comparison.md) cho tech decisions

### Short Term (1-2 tuần)
- [ ] Đọc Phase 1-5 theo lộ trình đề xuất
- [ ] Take notes on patterns applicable to your system
- [ ] Draw architecture diagrams cho understanding

### Long Term (1-2 tháng)
- [ ] Implement stress testing framework
- [ ] Evaluate database options (Modern Comparison)
- [ ] Design distributed system với LDC principles
- [ ] Present findings to team/leadership

---

## 📝 Changelog

| Date | File | Changes |
|------|------|---------|
| 2026-05-02 | All files | Initial creation |
| | vesviet | Research plan overview |
| | Phase 1 | Timeline & history |
| | Phase 2 | Architecture deep dive |
| | Phase 3 | Operations & testing |
| | Phase 4 | Technology overview |
| | Phase 4 Deep Dive | Technical details |
| | Phase 5 | Synthesis & lessons |
| | Modern Comparison | Tech stack comparison |
| | This index | Navigation & organization |

---

## 🤝 How to Use This Research

### For Individual Learning
1. Bắt đầu với Executive Summary
2. Đọc Phase 1 để hiểu context
3. Chọn Phase phù hợp với role của bạn
4. Refer back khi cần specific details

### For Team Sharing
1. Share Executive Summary cho leadership
2. Share relevant Phase với engineers
3. Use Modern Comparison cho tech decisions
4. Reference patterns từ Phase 5

### For Implementation
1. Use stress testing guide từ Phase 3
2. Follow architecture patterns từ Phase 2
3. Apply code examples từ Phase 4 Deep Dive
4. Evaluate alternatives từ Modern Comparison

---

**Research Status**: ✅ Complete
**Last Updated**: 2026-05-02
**Total Lines**: ~3,300
**Estimated Reading Time**: 8-16 hours (full)

---

*"Nothing is impossible" - Alipay Engineering*

