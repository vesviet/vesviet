---
title: "Phase 4: Technology Overview"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Technology overview: middle platform, payment flow, risk control, and SOFAStack components."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/phase-3-operations/) • [Next →](/series/alipay-double-11/phase-4-deep-dive/)
## 4.1 Middle Platform Architecture (中台架构)

### Lịch Sử Phát Triển (2015+)

```
2015: Alibaba công bố "Middle Platform Strategy"
  ↓
Large Middle Platform + Small Frontend (大中台, 小前台)
  ↓
2018: All systems migrated to cloud
  ↓
2020: Cloud-native data middle platform
```

### Core Concept: "大中台, 小前台"

```
┌──────────────────────────────────────────────────────────────┐
│                    Middle Platform Model                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                 FRONTEND (Small)                      │  │
│   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │  │
│   │  │Tmall│ │Taobao│ │Ele.me│ │Fliggy│ │...  │            │  │
│   │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘            │  │
│   └──────────────────────────────────────────────────────┘  │
│                            │                                  │
│                            ▼                                  │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              MIDDLE PLATFORM (Large)                  │  │
│   ├──────────────────┬──────────────────┬────────────────┤  │
│   │                  │                  │                │  │
│   │  Business        │  Data            │  Technology    │  │
│   │  Platform        │  Platform        │  Platform      │  │
│   │                  │                  │                │  │
│   │ • User Center    │ • MaxCompute     │ • Cloud infra  │  │
│   │ • Product Center │ • DataWorks      │ • DevOps       │  │
│   │ • Order Center   │ • Analytics      │ • Security     │  │
│   │ • Payment        │ • AI/ML          │ • Monitoring   │  │
│   │                  │                  │                │  │
│   └──────────────────┴──────────────────┴────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Data Middle Platform (统一数据平台)

#### Four Stages of Development

| Stage | Period | Characteristics |
|-------|--------|-----------------|
| **1. Diversified** | 2009-2012 | Phân tán, data islands |
| **2. Vertical Closed Loop** | 2012-2015 | Small vertical systems |
| **3. Middle Platform** | 2015-2018 | Unified methodology |
| **4. Cloud-Native** | 2018+ | On-cloud, Lake House |

#### Core Technologies

**MaxCompute**:
- **100,000+ servers** trong cluster
- **200,000+ employees** sử dụng hàng ngày
- Xử lý **12 PB tables**
- Query response: "Double 11 như một ngày bình thường"

**DataWorks**:
- All-in-one collaborative development
- Data governance platform
- Full-procedure data management

**Lake House**:
- Next-generation big data architecture
- Data warehouse + Data lake unified
- Cost barely increases khi business grows

#### Data Governance Challenges Solved

| Challenge | Solution |
|-----------|----------|
| Who owns data? | Clear ownership model |
| Core table 12 PB | Unified copy, shared access |
| Which half to delete? | Intelligent lifecycle management |
| 100+ departments | Standardized data models |

---

## 4.2 Security & Risk Control

### Ant Shield (蚁盾)

**Position**: Financial-grade security infrastructure

```
┌──────────────────────────────────────────────────────────────┐
│                    Ant Shield Architecture                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   User Action                                                │
│      │                                                       │
│      ▼                                                       │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              Risk Assessment Layer                    │  │
│   │  ┌───────────────────────────────────────────────┐   │  │
│   │  │           CTU Intelligent Brain               │   │  │
│   │  ├───────────┬───────────┬───────────┬───────────┤   │  │
│   │  │  Device   │  Account  │Transaction│ Behavior  │   │  │
│   │  │  Identity │  History  │  Pattern  │  Analysis │   │  │
│   │  └───────────┴───────────┴───────────┴───────────┘   │  │
│   │                                                         │  │
│   │  Real-time Score: 0-100 (Risk Level)                   │  │
│   │  Processing Time: < 0.1 second                         │  │
│   └──────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│   ┌──────────────────────────────────────────────────────┐  │
│   │              Decision & Action                          │  │
│   │                                                         │  │
│   │   Low Risk    │   Medium Risk   │   High Risk         │  │
│   │   ─────────►  │   Warning      │   Block/Review      │  │
│   │   Normal Pay  │   "Please      │   Account           │  │
│   │               │   confirm"     │   Restricted        │  │
│   └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### CTU Intelligent Risk Control Brain

**Eight Dimensions of Risk Assessment**:

| Dimension | What It Checks | Example |
|-----------|----------------|---------|
| **User Preferences** | Behavior patterns | Lần đầu transfer > 1000 CNY |
| **Account** | Account history | New account, no transactions |
| **Identity** | Verification level | Unverified device |
| **Transactions** | Amount, frequency | Spike in transfer amount |
| **Devices** | Device fingerprint | New device login |
| **Location** | Geographic | Login from unusual location |
| **Relationship** | Network analysis | No mutual friends |
| **Behavior** | Action patterns | Rushed, step-by-step诱导 |

**Real Case Study: Ms. Li Scam**:

```
Timeline:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

T+0: Ms. Li received call (fake Taobao CS)
     ↓
T+1: Sent to phishing website
     ↓
T+2: About to transfer ¥2,200
     ↓
     CTU Alert: "There may be a risk of fraud"
     Risk Score: Medium (relationship dimension)
     ↓
T+3: Ms. Li ignored warning, transferred ¥2,200
     ↓
T+4: Scammer induced ¥8,000 transfer
     ↓
     CTU BLOCK: "Beneficiary confirmed as scammer"
     Risk Score: High (behavior + relationship)
     Action: Account restricted
     ↓
T+5: Ms. Li demanded restriction lift (scammed)
     Total lost: ¥10,200
     Police intervened
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Relationship Analysis**:
- Empty account (no friends) → Suspicious
- No mutual transactions → Alert
- Bad credit record → Abnormal
- Connection to blacklisted account → Blocked

### Real-time Fraud Detection at Scale

**Performance**:
- **Processing time**: < 0.1 second
- **Throughput**: 544K+ TPS during Double 11
- **False positive rate**: < 0.1%
- **Coverage**: 100% transactions

**Architecture**:
```
Transaction Stream ──► Feature Extraction ──► ML Models
                              │                    │
                              ▼                    ▼
                    Real-time Graph Analysis   Risk Score
                              │                    │
                              └────────┬───────────┘
                                       ▼
                              Decision Engine
                                       │
                            ┌─────────┴─────────┐
                            ▼                   ▼
                         Approve             Block/Challenge
```

---

## 4.3 Payment Processing Flow

### Transaction Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│              Payment Transaction Lifecycle                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. INITIATION                                               │
│     User clicks "Pay"                                          │
│     │                                                         │
│     ▼                                                         │
│  2. RISK CHECK (CTU)                                          │
│     ┌─────────────────────────────────────────────┐          │
│     │ 8-dimension analysis < 0.1s                 │          │
│     └─────────────────────────────────────────────┘          │
│     │                                                         │
│     ▼                                                         │
│  3. AUTHENTICATION                                            │
│     • Password / Biometric                                    │
│     • Token validation                                        │
│     │                                                         │
│     ▼                                                         │
│  4. BALANCE CHECK                                             │
│     • Sufficient funds?                                       │
│     • Credit limit?                                           │
│     │                                                         │
│     ▼                                                         │
│  5. TRANSACTION PROCESSING                                  │
│     ┌─────────────────────────────────────────────┐          │
│     │  LDC Architecture:                          │          │
│     │  • Route to correct RZone                   │          │
│     │  • Local or Distributed 2PC                 │          │
│     │  • OceanBase: Paxos replication             │          │
│     └─────────────────────────────────────────────┘          │
│     │                                                         │
│     ▼                                                         │
│  6. SETTLEMENT                                                │
│     • Debit payer                                            │
│     • Credit payee                                           │
│     • Update balances (ACID)                                  │
│     │                                                         │
│     ▼                                                         │
│  7. NOTIFICATION                                              │
│     • Push notification                                       │
│     • SMS confirmation                                        │
│     • Receipt generation                                      │
│     │                                                         │
│     ▼                                                         │
│  8. COMPLETION                                                │
│     Response to user                                          │
│     < 1 second total                                          │
└──────────────────────────────────────────────────────────────┘
```

### Settlement Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 Settlement System                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│   │   Payer     │   │   Alipay    │   │   Payee     │        │
│   │   Account   │◄──┤   Escrow    │◄──┤   Account   │        │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘        │
│          │                 │                 │                │
│          │    ┌────────────┴────────────┐     │                │
│          │    │    Settlement Core     │     │                │
│          │    ├────────────────────────┤     │                │
│          │    │ • Netting              │     │                │
│          │    │ • Clearing             │     │                │
│          │    │ • Reconciliation       │     │                │
│          │    │ • Batch processing     │     │                │
│          │    └────────────────────────┘     │                │
│          │                 │                 │                │
│          └─────────────────┴─────────────────┘                │
│                                                               │
│   Daily Settlement: T+0 (real-time) hoặc T+1 (batch)        │
└──────────────────────────────────────────────────────────────┘
```

### ACID Guarantees at Scale

**Challenge**: Đảm bảo ACID với 544K TPS distributed transactions

**Solutions**:

| Property | Implementation |
|----------|----------------|
| **Atomicity** | 2PC + Paxos (coordinator không single point) |
| **Consistency** | Paxos consensus, majority replication |
| **Isolation** | MVCC (Multi-Version Concurrency Control) |
| **Durability** | Write-ahead log + Paxos persistence |

**Paxos-based 2PC**:
```
Traditional 2PC:          OceanBase 2PC:
┌─────────┐               ┌─────────┐
│  coord  │               │  Paxos  │  ← Coordinator is replicated!
│ (SPOF)  │               │ group   │
└────┬────┘               └────┬────┘
     │                         │
 ┌───┴───┐                 ┌───┴───┐
 │       │                 │       │
 ▼       ▼                 ▼       ▼
R1      R2                R1      R2

SPOF = Single Point of Failure (traditional)
Paxos = Distributed consensus (OceanBase)
```

**MVCC Concurrency Control**:
- Multi-version để đọc không block ghi
- Read committed snapshot
- Serializable transactions khi cần

### Throughput Numbers

| Component | Double 11 2019 | Double 11 2020 |
|-----------|----------------|----------------|
| **Alipay TPS** | 544,000 | 583,000 |
| **Alipay QPS** | 61 million | Higher |
| **POLARDB TPS** | 87 million | Higher |
| **Settlement batch** | Billions | Billions |

---

## 4.4 SOFAStack - Financial-Grade Distributed Architecture

### Core Components

```
┌──────────────────────────────────────────────────────────────┐
│                    SOFAStack Platform                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Service Layer                                               │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  • SOFABoot (Spring Boot enhanced)                  │  │
│   │  • SOFARPC (High-performance RPC)                  │  │
│   │  • SOFAMesh (Service mesh)                          │  │
│   │  • SOFAArk (Modular isolation)                      │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                               │
│   Middleware Layer                                            │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  • SOFAMQ (Message queue)                           │  │
│   │  • SOFATracer (Distributed tracing)                │  │
│   │  • SOFALookout (Monitoring)                        │  │
│   │  • SOFARegistry (Service discovery)                  │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                               │
│   Data Layer                                                  │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  • OceanBase (Distributed database)                │  │
│   │  • SOFADashboard (Ops platform)                   │  │
│   └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Benefit |
|---------|---------|
| **SOFABoot** | Rapid development, enterprise-ready |
| **SOFARPC** | 200K+ TPS per node, multiple protocols |
| **SOFAMesh** | Service-to-service communication, mTLS |
| **SOFAMQ** | Exactly-once delivery, 10M+ TPS |

---

## Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────┐
│              Alipay Double 11 Technology Stack               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend                                                    │
│  ├── Mobile Apps (iOS/Android)                              │
│  ├── Web (React/Vue)                                        │
│  └── Mini Programs (支付宝小程序)                            │
│                                                              │
│  API Gateway                                                 │
│  ├── Traffic routing (LDC-aware)                            │
│  ├── Rate limiting                                          │
│  └── Authentication                                         │
│                                                              │
│  Service Layer (SOFAStack)                                   │
│  ├── SOFABoot + SOFARPC                                     │
│  ├── SOFAMesh (Service mesh)                                │
│  └── Business logic (Java/Go)                               │
│                                                              │
│  Middleware                                                  │
│  ├── RocketMQ (Message queue)                               │
│  ├── Tair (Distributed cache)                               │
│  └── SOFAMQ                                                 │
│                                                              │
│  Data Layer                                                  │
│  ├── OceanBase (Distributed SQL)                            │
│  ├── POLARDB (Cloud-native DB)                              │
│  └── OSS (Object storage)                                   │
│                                                              │
│  Infrastructure                                              │
│  ├── PouchContainer (Container runtime)                   │
│  ├── Kubernetes (ACK)                                       │
│  ├── Alibaba Cloud                                          │
│  └── LDC Architecture (RZone/GZone/CZone)                  │
│                                                              │
│  Security & Risk                                             │
│  ├── Ant Shield                                             │
│  ├── CTU Risk Control                                       │
│  └── Real-time fraud detection                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*Next: Phase 5 - Synthesis & Lessons Learned*

