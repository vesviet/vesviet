---
title: "Phase 2: Core Architecture (LDC, Unitization, Multi-Active)"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Deep architecture study: LDC/unitization, OceanBase, messaging, and distributed systems patterns."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/phase-1-timeline/) • [Next →](/series/alipay-double-11/phase-3-operations/)
## 2.1 Logical Data Center (LDC) & Unitization Architecture

### Core Concept: "Unit"

**Định nghĩa**: Unit là một tập hợp **self-contained** có thể hoàn thành toàn bộ business operations. Đây là phiên bản thu nhỏ của toàn bộ hệ thống:
- **Có đầy đủ**: Tất cả services và applications
- **Không đầy đủ**: Chỉ chứa một phần dữ liệu (data sharding)

### Ba Loại Zone trong LDC

```
┌─────────────────────────────────────────────────────────────┐
│                    LDC Architecture                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│   │   RZone 1   │   │   RZone 2   │   │   RZone N   │       │
│   │  (Region)   │   │  (Region)   │   │  (Region)   │       │
│   ├─────────────┤   ├─────────────┤   ├─────────────┤       │
│   │ • App Layer │   │ • App Layer │   │ • App Layer │       │
│   │ • Data Shard│   │ • Data Shard│   │ • Data Shard│       │
│   │ • Full Svcs │   │ • Full Svcs │   │ • Full Svcs │       │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
│          │                 │                 │              │
│          └─────────────────┼─────────────────┘              │
│                            │                                │
│                   ┌──────────┴──────────┐                     │
│                   │                     │                     │
│            ┌──────┴──────┐      ┌──────┴──────┐              │
│            │   GZone     │      │   CZone     │              │
│            │  (Global)   │      │  (City)     │              │
│            ├─────────────┤      ├─────────────┤              │
│            │ • Config    │      │ • User Info │              │
│            │ • CIF       │      │ • Login     │              │
│            │ • Shared    │      │ • Frequent  │              │
│            └─────────────┘      └─────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

#### RZone (Region Zone)
- **Tự chủ hoàn toàn**: Có đủ data và services để xử lý business
- **Data sharding**: Mỗi RZone chỉ chứa một phần dữ liệu (ví dụ: user ID 1-1M ở RZone 1, 1M-2M ở RZone 2)
- **Horizontal scaling**: Thêm RZone = thêm capacity
- **Multi-active**: Nhiều RZone active đồng thời ở các region khác nhau

#### GZone (Global Zone)
- **Chỉ 1 instance toàn cục**
- Chứa dữ liệu **không thể chia nhỏ** (inseparable):
  - Config center
  - CIF (Customer Information File)
  - Shared global data
- **Read/Write**: Được tất cả RZones truy cập (tần suất thấp)

#### CZone (City Zone)
- **Giải quyết latency giữa các cities**
- Chứa dữ liệu/services được **RZone truy cập thường xuyên**
- Mỗi business access ít nhất một lần
- Khác GZone: CZone được truy cập **liên tục** bởi RZone

### Lợi Ích LDC Architecture

| Vấn đề | Giải pháp LDC |
|--------|---------------|
| Single point bottleneck | Chia thành nhiều units |
| Traffic allocation | Request routing đến đúng RZone |
| Data splitting | Sharding theo unit |
| Latency xuyên city | CZone cache frequent data |
| Remote disaster recovery | Multi-active RZones |

**Kết quả**:
- **99.99% availability** (financial-grade)
- **Theoretical unlimited capacity** (thêm RZone = scale out)
- **Hundreds of thousands TPS** trong promotion

---

## 2.2 Database Layer - OceanBase

### Lịch Sử Evolution

```
Oracle (commercial) → MySQL (open source) → OceanBase (distributed)
        ↓                     ↓                      ↓
    2010-2012             2012-2014               2014+
   Limits hit        Still bottlenecks       Auto-scaling
```

### Kiến Trúc OceanBase

```
┌──────────────────────────────────────────────────────────────┐
│                    OceanBase Cluster                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Zone 1          Zone 2          Zone 3         (Regions)   │
│   ┌────────┐     ┌────────┐     ┌────────┐                  │
│   │ OBS 1  │     │ OBS 2  │     │ OBS 3  │                  │
│   │ (Leader)│◄──►│(Follower)│◄──►│(Follower)│   Paxos Sync  │
│   └────────┘     └────────┘     └────────┘                  │
│      │               │               │                       │
│      └───────────────┼───────────────┘                       │
│                      │                                        │
│   ┌──────────────────┴──────────────────┐                    │
│   │         Table Partitions              │                    │
│   │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │                    │
│   │  │ P1  │ │ P2  │ │ P3  │ │ P4  │    │  Paxos per partition│
│   │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘    │                    │
│   │     └───────┴───────┴───────┘       │                    │
│   └─────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Paxos Protocol cho Consistency
- **RPO = 0** (Recovery Point Objective): Zero data loss
- **RTO < 8 seconds** (Recovery Time Objective)
- **Multi-replica strong synchronization**: Majority consensus
- **Automatic failover**: Server, rack, AZ, hoặc entire region failure

#### 2. Partitioning Strategy
- Tables được **partitioned explicitly** bởi user
- Partition = đơn vị cơ bản cho:
  - Data distribution
  - Load balancing
  - Paxos synchronization
- Thường **1 Paxos group per partition**

#### 3. Transaction Processing

**Local Transaction**:
```
SQL → Compile → Execution Plan → Local Execution
```

**Distributed Transaction (2PC + Paxos)**:
```
SQL → Compile → Distributed Plan → 2PC Coordinator
                                  ↓
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
                  Paxos 1       Paxos 2       Paxos N
                    │             │             │
                    └─────────────┴─────────────┘
                           Commit OK
```

**OceanBase 2PC vs Traditional 2PC**:
- Traditional: Coordinator single point of failure
- OceanBase: Paxos-based 2PC - coordinator replicated

#### 4. Storage Engine
- **LSM-tree** (Log-Structured Merge Tree) architecture
- **Compaction**: Offload đến FPGA (custom hardware) để xử lý nhanh hơn
- **Row caches + Block caches**: Multi-level caching
- **Replica types**:
  - Full replica (data + log)
  - Data replica (data only)
  - Log replica (log only)

### OceanBase Scale Numbers

| Metric | Value |
|--------|-------|
| tpmC (TPC-C benchmark) | **707 million** |
| Servers trong benchmark | 2,360 ECS servers |
| Users emulated | 559,440,000 |
| Warehouses | 55,944,000 |
| Deployment tại Alipay | **Tens of thousands servers** |
| Double 11 2019 TPS | **544,000 TPS** |
| Double 11 2019 QPS | **61 million QPS** |

### Lessons Learned từ OceanBase Paper

1. **Application layer**: Không dùng database như key-value store → dùng advanced features
2. **Stored procedures**: Vẫn có giá trị lớn cho OLTP
3. **Timeouts**: Mọi transaction và SQL phải có timeout (distributed systems có failure rate cao hơn)

---

## 2.3 Distributed Systems Patterns

### Remote Multi-Active Architecture (2013+)

```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Active Deployment                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Hangzhou          Shanghai         Beijing               │
│   ┌────────┐        ┌────────┐       ┌────────┐            │
│   │Unit A  │◄──────►│Unit B  │◄─────►│Unit C  │            │
│   │(Active)│        │(Active)│       │(Active)│            │
│   └────────┘        └────────┘       └────────┘            │
│      │                  │                │                   │
│      └──────────────────┼────────────────┘                   │
│                         │                                   │
│                    ┌────┴────┐                              │
│                    │  GZone  │                              │
│                    │ (Shared)│                              │
│                    └─────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

**Đặc điểm**:
- Mỗi city có **complete transaction unit**
- Regional scaling: Thêm city = thêm capacity
- Disaster recovery: Một city down → traffic chuyển sang city khác

### Service Mesh & Inter-Service Communication

### Message Queue (RocketMQ)
- **Async processing** cho non-critical path
- **Peak shaving**: Buffer traffic bursts
- **Decoupling** giữa các services

### Circuit Breaker, Throttling, Degrade

#### Throttling (Rate Limiting)
- **AHAS** (Application High Availability Service)
- Giới hạn request rate để bảo vệ downstream services

#### Degrade
- **Graceful degradation**: Tắt non-essential features khi quá tải
- **Prioritization**: Quan trọng nhất được bảo vệ đầu tiên

#### Circuit Breaker
- **Fail fast**: Không đợi timeout
- **Auto-recovery**: Tự động thử lại sau cooldown

---

## 2.4 Cloud-Native Evolution (2020+)

### Containerization với PouchContainer

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud-Native Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Application Layer                                          │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│   │  App 1  │ │  App 2  │ │  App 3  │ │ App N   │         │
│   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘         │
│        │           │           │           │              │
│   ┌────┴───────────┴───────────┴───────────┴────┐         │
│   │           Kubernetes (ACK)                   │         │
│   │    Scheduling, Auto-scaling, Recovery      │         │
│   └────────────────┬──────────────────────────────┘         │
│                    │                                        │
│   ┌────────────────┴──────────────────────┐                │
│   │      PouchContainer Runtime            │                │
│   │  • OCI compatible                      │                │
│   │  • Kubernetes CRI                      │                │
│   │  • Enterprise features                 │                │
│   └────────────────────────────────────────┘                │
│                                                              │
│   ┌──────────────────────────────────────────┐               │
│   │        Alibaba Cloud Infrastructure      │               │
│   │  • ECS, Bare Metal, GPU, FPGA           │               │
│   └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### PouchContainer
- **OCI compatible**: Tuân thủ Open Container Initiative
- **Kubernetes CRI**: Native Kubernetes integration
- **Enterprise features**: Bảo mật, isolation cao

### Elastic Architecture

```
Normal State                     Peak State (Double 11)
┌──────────────┐                ┌──────────────┬──────────────┐
│  RZone 1     │                │  RZone 1     │ Elastic Unit │
│  (Daily)     │                │  (Daily)     │  (Cloud)     │
├──────────────┤      ─────►    ├──────────────┼──────────────┤
│  RZone 2     │                │  RZone 2     │ Elastic Unit │
│  (Daily)     │                │  (Daily)     │  (Cloud)     │
└──────────────┘                └──────────────┴──────────────┘
```

**Elastic Units**:
- Một số RZones biến thành **elastic units**
- Peak period: **Pop up lên cloud** để scale nhanh
- Post-peak: **Bounce back** về daily data center
- **Insensible elasticity**: Business layer không biết đang chạy ở đâu

### Co-location: Online + Big Data

```
┌─────────────────────────────────────────────────────────────┐
│                    Co-location Cluster                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                 Shared Resources                    │  │
│   │  ┌─────────────┐              ┌─────────────────┐   │  │
│   │  │ Online Svc  │   Idle time  │  Big Data Task  │   │  │
│   │  │ (Real-time) │◄────────────►│  (Batch)        │   │  │
│   │  └─────────────┘              └─────────────────┘   │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
│   Resource Pool: Online peak sử dụng, idle dùng cho Big Data │
│   Cost saving: ~50% giảm chi phí                             │
└─────────────────────────────────────────────────────────────┘
```

**Sigma + Fuxi Scheduling**:
- **Sigma**: Online service scheduling
- **Fuxi**: Big data task scheduling
- **Unified**: Một cluster cho cả hai loại workload

### Cost Efficiency 2020

| Metric | Improvement |
|--------|-------------|
| Cost per transaction | Giảm **>50%** |
| IT costs (STO Express) | Giảm **30%** |
| Elastic resource cost | Giảm **>40%** |
| R&D efficiency | Tăng **>30%** |

---

## Key Architectural Insights

### 1. Evolution Path
```
2008: Distributed architecture (break monolithic)
  ↓
2013: LDC + Multi-active (horizontal scale)
  ↓
2014: Automated testing (predictable reliability)
  ↓
2016: Elastic architecture (cloud integration)
  ↓
2020: Cloud-native (efficiency & cost)
```

### 2. Design Principles
- **Unitization**: Chia nhỏ để scale
- **Self-containment**: Mỗi unit độc lập
- **Automation**: Không manual intervention
- **Testing**: Verify trước production

### 3. Trade-offs
- **Consistency**: Paxos = strong consistency nhưng latency
- **Sharding**: Scale tốt nhưng cross-shard query phức tạp
- **Elasticity**: Cost tốt nhưng architecture phức tạp

---

*Next: Phase 3 - Quy Trình Vận Hành & Stress Testing*

