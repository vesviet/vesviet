---
title: "Phase 3: Operations Playbook"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Operations and preparation: capacity planning, full-link stress testing, incident command, and checklists."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/phase-2-architecture/) • [Next →](/series/alipay-double-11/phase-4-technology/)
## 3.1 Capacity Planning

### Peak Prediction Models

**Vấn đề**: Double 11 có traffic peak gấp hàng chục lần bình thường, nhưng chỉ diễn ra trong thời gian ngắn.

**Giải pháp**: Hybrid Strategy

```
┌──────────────────────────────────────────────────────────────┐
│               Capacity Planning Strategy                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Daily Traffic                  Peak Traffic (Double 11)     │
│       │                              │                       │
│       ▼                              ▼                       │
│   ┌───────┐                    ┌───────────┐                │
│   │On-prem│ ──── Elastic ─────►│ On-prem   │                │
│   │(Base) │      Scaling       │ + Cloud   │                │
│   └───────┘                    └───────────┘                │
│       │                              │                       │
│       │                              │                       │
│   Normal Ops                     Peak Ops                    │
│   (Year-round)                   (1-2 months)                │
│                                                               │
│   Cost Optimization: Giữ resources 1 năm → Chỉ 1-2 tháng      │
└──────────────────────────────────────────────────────────────┘
```

**Resource Buffer Calculation**:
1. **Baseline**: Capacity cho daily traffic (80% utilization)
2. **Peak multiplier**: Tính toán peak / baseline ratio
3. **Buffer**: Thêm 20-30% cho unexpected spikes
4. **Elastic capacity**: Cloud burst cho phần vượt quá on-prem

### Hybrid Cloud Strategy

| Component | On-Premise | Public Cloud |
|-----------|------------|--------------|
| Core database | ✓ (sensitive) | ✗ |
| Application servers | ✓ (base) | ✓ (elastic) |
| Cache layer | ✓ | ✓ |
| CDN | ✗ | ✓ (Alibaba Cloud CDN) |
| Big data analytics | ✗ | ✓ (MaxCompute) |

### Cost Per Transaction Optimization

**Mục tiêu**: Giảm 50% cost per transaction qua các năm

**Các biện pháp**:
1. **Co-location**: Chia sẻ resources giữa online và batch
2. **Elastic scaling**: Scale up/down theo nhu cầu thực tế
3. **Containerization**: Tăng density, giảm waste
4. **Automation**: Giảm manual ops cost

---

## 3.2 Stress Testing System - Chi Tiết

### Evolution của Stress Testing

```
2010: Manual single-machine testing
  ↓
2013: First full-link stress test (200+ people, all-night)
  ↓
2014: Automated stress testing system (core systems)
  ↓
2017+: Intelligent stress testing (< 10 people, work hours)
```

### Full-Link Stress Testing Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                Full-Link Stress Testing                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Traffic Generation                                          │
│   ┌──────────────────────────────────────────────────────┐  │
│   │  Stress Testing Controller (Intelligent)              │  │
│   │  • Generate realistic traffic patterns                │  │
│   │  • Simulate 559M users, 55M warehouses                │  │
│   └──────────────────────┬───────────────────────────────┘  │
│                          │                                    │
│   ┌──────────────────────▼───────────────────────────────┐  │
│   │                    Full Link                          │  │
│   │  CDN ─► LB ─► App ─► Service ─► Cache ─► DB         │  │
│   │   │      │      │        │        │       │            │  │
│   │   └──────┴──────┴────────┴────────┴───────┘            │  │
│   │   All components participate in stress test             │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                               │
│   Data Isolation: Shadow Tables                               │
│   ┌─────────────┐    ┌─────────────┐                        │
│   │ Online Table│    │ Shadow Table│                        │
│   │ (Production)│    │ (Stress Test)│                        │
│   │   orders    │    │   orders_st  │                        │
│   └─────────────┘    └─────────────┘                        │
│   Same structure, isolated location                           │
└──────────────────────────────────────────────────────────────┘
```

### Stress Testing Process (7 năm evolution)

#### Phase 1: Process & Management

```
Timeline (Simulated Sequence):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

T-60 days: Planning & preparation
    ├── Data preparation
    ├── Architecture reconstruction
    └── Team assignment

T-30 days: Pre-testing
    ├── Single-link debugging
    ├── Middleware transformation
    └── Business reconstruction

T-14 days: Full-link stress tests
    ├── Peak pulse simulation
    ├── Vertical jump test
    ├── Rate limiting verification
    └── Destructive testing

T-7 days: Issue fixing & re-test

T-1 day: Final preparation

T+0: Double 11 Event

T+7 days: Post-mortem
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Team Evolution**:
- 2013: **200+ people**, all-night testing
- 2020: **< 10 people**, work hours testing
- Equation: `Effective solution + Adequate preparation + Reliable platform = Successful test`

#### Phase 2: Environment Reconstruction

**Business Reconstruction**:
- Identify APIs affected by multiple stress tests
- Đánh giá dirty data impact
- Implement data isolation mechanisms

**Middleware Transformation**:
- Message queue: Separate stress test traffic
- Cache: Shadow cache keys
- Database: Shadow tables

#### Phase 3: Data Preparation

**Two Types of Data**:

1. **Business Model Data**:
   - User profiles
   - Product catalog
   - Inventory levels
   - Historical transactions

2. **Stress Testing Base Data**:
   - 559,440,000 emulated users (2019)
   - 55,944,000 warehouses
   - Realistic traffic patterns

#### Phase 4: Traffic Security Policy

**Data Isolation**:
```
Method: Shadow Table
- Same schema as production
- Writable stress testing data
- Isolated storage location
- Result: No data pollution
```

**Traffic Filtering**:
```
Method: Special identifier
- Mark stress test traffic
- Lift security policies slightly
- Prevent DDoS detection
- Result: Test runs successfully
```

**Third-party Integration**:
- 2013: Failed (không connect downstream)
- 2014+: Alipay và logistics connected
- External: Alipay cung cấp mock services

#### Phase 5: Test Implementation

**Pre-operations**:
1. **System Ramp-up**: 
   - Cache warm-up
   - Connection pool preparation
   - Pre-load critical data

2. **Logon Preparation**:
   - Flash sale scenarios
   - Persistent connection warmup
   - Simulate real user login patterns

**Formal Stress Testing Steps**:

| Test Type | Purpose | Method |
|-----------|---------|--------|
| **Peak Pulse** | Simulate exact 00:00 peak | Target traffic spike |
| **Vertical Jump** | Find system limits | Disable rate limiting, ramp up |
| **Rate Limiting Verification** | Verify protection works | Enable AHAS, check throttling |
| **Destructive Test** | Verify contingency plans | Simulate failures during peak |

**Peak Pulse Details**:
- Simulate chính xác target peak traffic
- Test promotion-state system performance
- Verify auto-scaling triggers

**Vertical Jump Test**:
- Disable rate limiting/degradation
- Increase traffic đến khi system gặp exception
- Tìm "breaking point" của hệ thống
- Chỉ chạy sau khi đã đạt target traffic

---

## 3.3 Incident Response & Monitoring

### "Guangming Peak" - Command Center

```
┌──────────────────────────────────────────────────────────────┐
│              Guangming Peak Command Center                    │
│              (光明顶 - Alibaba Xixi Campus)                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                Giant Screens                         │  │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐      │  │
│   │  │ Real-time  │  │ System     │  │ Business   │      │  │
│   │  │ Traffic    │  │ Health     │  │ Metrics    │      │  │
│   │  └────────────┘  └────────────┘  └────────────┘      │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                               │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │  Commander   │  │   Alipay     │  │   Taobao     │      │
│   │   in Chief   │  │   Rep (2013+)│  │   Team       │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│   Hundreds of engineers monitoring 24/7 during event          │
└──────────────────────────────────────────────────────────────┘
```

### Real-time Monitoring Dashboards

**Key Metrics**:
1. **Traffic Metrics**:
   - TPS (Transactions Per Second)
   - QPS (Queries Per Second)
   - RT (Response Time)
   - Error rate

2. **System Metrics**:
   - CPU utilization
   - Memory usage
   - Disk I/O
   - Network throughput

3. **Business Metrics**:
   - GMV (Gross Merchandise Volume)
   - Order count
   - Payment success rate
   - Active users

### Contingency Plans & Downgrade Strategies

**Three Levels of Protection**:

```
Level 1: Rate Limiting (AHAS)
├── Throttle non-critical requests
├── Priority queue for core transactions
└── Auto-trigger khi latency tăng

Level 2: Degradation
├── Tắt non-essential features
├── Giảm image quality
├── Disable recommendations
└── Static page fallback

Level 3: Emergency Mode
├── Cash-only payments
├── Disable coupons/discounts
├── Offline payment redirect
└── Manual override available
```

**Downgrade Priority**:
1. Core payment flow (không bao giờ downgrade)
2. User authentication
3. Inventory check
4. Logistics tracking
5. Recommendations (đầu tiên bị downgrade)

### Post-Mortem Process

**Timeline**:
- **T+1 day**: Initial incident summary
- **T+1 week**: Detailed post-mortem
- **T+1 month**: Action items implementation review

**Template**:
1. Incident summary (what happened)
2. Timeline (minute-by-minute)
3. Impact assessment (users affected)
4. Root cause analysis (5 Whys)
5. Action items (who, what, when)
6. Lessons learned

---

## 3.4 Cultural Aspects

### "Worshiping Guan Gong" Tradition

**History**:
- Bắt nguồn từ khi Alipay mới thành lập
- 2013: Zheng Yangfei mang painting vào phòng chuẩn bị
- "Prince of Stress Testing" - Zheng Yangfei

**Evolution**:
```
2013: Painting of Guan Yu
2014: Guan Gong shadow puppet (từ Xi'an campus recruitment)
2015: Wooden Guan Gong statue (Cheng Li mua)
2016+: Bronze Guan Gong statue (Hu Xi mua)
```

**Practice**:
- Mỗi release quan trọng: Forward Guan Gong emojis trong Wangwang
- Cầu nguyện: "No bugs"
- Ý nghĩa: Respect và sự kính sợ đối với unpredictable

### Temple Traditions

**"Lingyin Temple Faction" vs "Faxi Temple faction"**:
- Hai phe đi chùa cầu may trước Double 11
- Lingyin Temple (灵隐寺) - gần West Lake
- Faxi Temple (法喜寺) - nơi lãnh đạo đi

**Post-Double 11 Ritual**:
1. Cheng Li và Hu Xi dẫn team đi chùa Faxi
2. Đi bộ từ Alipay Building đến chùa
3. "Redeem vow" - trả lời hứa với thần
4. Nhặt rác trên đường về

### Team Collaboration

**Key Principles**:
1. **"You are never fighting alone"** - Li Junkui
2. **Trust your teammates**: "First, don't panic. Say 'Got it. Let me take a look.' Then convey to backend team."
3. **Monthly release cycles**: 2013 LDC project - release hầu như mỗi tháng (gấp nhiều lần bình thường)

**Stress Relief Methods**:
| Person | Method |
|--------|--------|
| Chen Liang | Chạy bộ, chơi bóng |
| Others | Kiểm tra code đi kiểm tra lại |
| Foodies | Ăn lẩu Haidilao trước Double 11 |

---

## Operations Checklist

### Pre-Event (T-30 days)
- [ ] Full-link stress test completed
- [ ] All critical issues fixed
- [ ] Contingency plans reviewed
- [ ] Monitoring dashboards verified
- [ ] Team assignments confirmed
- [ ] Guangming Peak setup complete

### Pre-Event (T-7 days)
- [ ] Final stress test passed
- [ ] Rate limiting tested
- [ ] Degradation paths verified
- [ ] Cache warmed up
- [ ] Database optimized
- [ ] Team on-call schedule confirmed

### During Event (T-0)
- [ ] Command center active
- [ ] All teams in position
- [ ] Real-time monitoring
- [ ] Incident response ready
- [ ] Communication channels open

### Post-Event (T+1 day)
- [ ] Initial summary
- [ ] Thank team
- [ ] Temple visit scheduled 😄

---

*Next: Phase 4 - Công Nghệ Chi Tiết (Middle Platform, Risk Control, Payment Flow)*

