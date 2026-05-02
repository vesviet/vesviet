---
title: "Modern Tech Comparison"
date: 2026-05-02T18:10:00+07:00
draft: false
description: "Comparison of Alipay’s stack versus modern cloud-native technologies: Kubernetes, Kafka/Pulsar, gRPC, service mesh, and distributed databases."
ShowToc: true
TocOpen: true
---
[← Series hub](/series/alipay-double-11/)
[← Prev](/series/alipay-double-11/phase-4-deep-dive/) • [Next →](/series/alipay-double-11/phase-5-synthesis/)
## Tổng Quan So Sánh

| Alipay Stack | Modern Equivalent | Key Difference |
|--------------|-------------------|----------------|
| **LDC + RZone** | Kubernetes + Multi-cluster | LDC: Business-driven sharding; K8s: Infrastructure abstraction |
| **OceanBase** | CockroachDB/TiDB/YugabyteDB | OceanBase: 10+ years prod, custom FPGA; Newer: Cloud-native first |
| **RocketMQ** | Apache Kafka/Apache Pulsar | RocketMQ: LSM-tree + rich msg types; Kafka: Log-centric; Pulsar: Tiered storage |
| **SOFARPC** | gRPC/Envoy Proxy | SOFARPC: Java-centric, financial features; gRPC: Cross-platform, protobuf |
| **SOFAMesh (MOSN)** | Istio/Linkerd | MOSN: Go-based, X-protocol; Istio: Envoy C++, standard mesh |
| **CTU** | Modern ML Platforms | CTU: Custom fraud-specific; Modern: General-purpose MLOps |
| **PouchContainer** | containerd/cri-o | Pouch: Alibaba-specific; containerd: CNCF standard |

---

## 1. LDC Architecture vs Kubernetes Multi-Cluster

### Kiến Trúc So Sánh

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LDC (Alipay) vs Kubernetes Multi-Cluster                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   LDC Architecture (Business-Driven)                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   RZone 1          RZone 2          RZone N                         │  │
│   │   ┌─────────┐      ┌─────────┐      ┌─────────┐                     │  │
│   │   │Users    │      │Users    │      │Users    │                     │  │
│   │   │1-1M     │      │1M-2M    │      │N-M      │                     │  │
│   │   ├─────────┤      ├─────────┤      ├─────────┤                     │  │
│   │   │Apps     │      │Apps     │      │Apps     │                     │  │
│   │   │DB       │      │DB       │      │DB       │                     │  │
│   │   │Cache    │      │Cache    │      │Cache    │                     │  │
│   │   └─────────┘      └─────────┘      └─────────┘                     │  │
│   │                                                                     │  │
│   │   • Sharding: User ID-based                                        │  │
│   │   • Self-contained units                                           │  │
│   │   • Cross-unit = Distributed txn                                   │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Kubernetes Multi-Cluster (Infrastructure-Driven)                          │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Cluster 1         Cluster 2         Cluster N                     │  │
│   │   ┌─────────┐       ┌─────────┐       ┌─────────┐                   │  │
│   │   │Region:  │       │Region:  │       │Region:  │                   │  │
│   │   │us-west  │       │eu-west  │       │ap-south │                   │  │
│   │   ├─────────┤       ├─────────┤       ├─────────┤                   │  │
│   │   │K8s Pods │       │K8s Pods │       │K8s Pods │                   │  │
│   │   │Services │       │Services │       │Services │                   │  │
│   │   └─────────┘       └─────────┘       └─────────┘                   │  │
│   │                                                                     │  │
│   │   • Sharding: Infrastructure/region-based                         │  │
│   │   • Shared global services                                           │  │
│   │   • Cross-cluster = Service mesh                                    │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Comparison

| Aspect | LDC (Alipay) | K8s Multi-Cluster | Recommendation |
|--------|--------------|---------------------|----------------|
| **Sharding Strategy** | User ID / Business key | Node/Region labels | LDC approach cho data-intensive apps |
| **Unit Boundary** | App + Data + Cache | Pods + Services | LDC: true isolation; K8s: shared storage |
| **Cross-Unit Traffic** | Explicit ( costly ) | Transparent via mesh | LDC: intentional design; K8s: hide complexity |
| **Failover** | Manual/Scripted (RZone switch) | Automatic (health checks) | K8s wins cho automation |
| **Scaling** | Add RZone (complex) | Add nodes (simple) | K8s wins cho ops simplicity |
| **Data Consistency** | Strong (Paxos in unit) | Eventual (cross-cluster) | LDC wins cho financial data |

### Khi Nào Dùng Cái Nào?

**Use LDC-style khi**:
- [ ] Financial transactions (strong consistency needed)
- [ ] Data > 10TB per shard
- [ ] Compliance requirements (data residency)
- [ ] Predictable traffic patterns (can plan sharding)

**Use K8s Multi-cluster khi**:
- [ ] Microservices architecture
- [ ] Global deployment required
- [ ] Team autonomy priority
- [ ] Rapid scaling needs

---

## 2. OceanBase vs Modern Distributed Databases

### Landscape Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Distributed Database Landscape (2024)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   NEWSQL (SQL + Distributed)                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │
│   │   │  OceanBase  │  │CockroachDB  │  │    TiDB     │              │  │
│   │   │  (Alipay)   │  │  (Cockroach)│  │  (PingCAP)  │              │  │
│   │   ├─────────────┤  ├─────────────┤  ├─────────────┤              │  │
│   │   │ • 12+ years │  │ • 8+ years  │  │ • 8+ years  │              │  │
│   │   │ • 707M tpmC │  │ • Cloud-na  │  │ • HTAP      │              │  │
│   │   │ • Custom HW │  │ • PG compat │  │ • MySQL com │              │  │
│   │   │ • Paxos     │  │ • Multi-raft│  │ • Raft      │              │  │
│   │   │ • FPGA opt  │  │ • C++       │  │ • Go/Rust   │              │  │
│   │   └─────────────┘  └─────────────┘  └─────────────┘              │  │
│   │                                                                     │  │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │
│   │   │ YugabyteDB  │  │   FaunaDB   │  │  PlanetScale│              │  │
│   │   │ (Yugabyte)  │  │  (Fauna)    │  │  (Vitess)   │              │  │
│   │   ├─────────────┤  ├─────────────┤  ├─────────────┤              │  │
│   │   │ • Redis API │  │ • Calvin    │  │ • Git-based │              │  │
│   │   │ • Cassandra │  │ • Global    │  │ • Branching │              │  │
│   │   │ • K8s native│  │ • Serverless│  │ • Deploy prev│              │  │
│   │   └─────────────┘  └─────────────┘  └─────────────┘              │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Cloud-Native Databases                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  AWS Aurora │ Google Spanner │ Azure CosmosDB │ Alibaba POLARDB      │  │
│   │  (Log-based)│ (TrueTime)   │ (Multi-model)  │ (Multi-master)       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### OceanBase vs CockroachDB

| Feature | OceanBase | CockroachDB | Winner |
|---------|-----------|-------------|--------|
| **Production Maturity** | 12+ years, 544K TPS | 8+ years, widely adopted | Tie |
| **SQL Compatibility** | MySQL + Oracle | PostgreSQL | Depends on existing DB |
| **Storage Engine** | LSM-tree + FPGA | Pebble (RocksDB-like) | OceanBase (performance) |
| **Consensus** | Paxos | Multi-raft | Tie (both production-proven) |
| **Cloud-Native** | Kubernetes operator | Kubernetes native | CockroachDB |
| **Cost Model** | License + HW | Open source + support | CockroachDB |
| **Custom Hardware** | FPGA acceleration | None | OceanBase (if have budget) |
| **Documentation** | Chinese-focused | Excellent English | CockroachDB |

### OceanBase vs TiDB

| Feature | OceanBase | TiDB | Winner |
|---------|-----------|------|--------|
| **Architecture** | Monolithic distributed | Modular (TiDB/TiKV/PD) | TiDB (flexibility) |
| **HTAP** | Unified engine | TiFlash columnar | TiDB (more mature) |
| **Cloud** | Alibaba Cloud optimized | Multi-cloud | TiDB |
| **Storage** | LSM-tree + compression | TiKV (distributed) | OceanBase (storage efficiency) |
| **Deployment** | Heavyweight | Kubernetes-native | TiDB |
| **Best For** | Alibaba ecosystem | General multi-cloud | Depends on cloud |

### Migration Path

```
From Legacy to Modern:

Oracle ─────────────────────────────────────────────────────────►
    │                                                              │
    ├─► OceanBase (easiest, Oracle compat) ──► Cloud version    │
    │                                                              │
    └─► CockroachDB (rewrite queries) ──► Distributed scaling     │

MySQL ───────────────────────────────────────────────────────────►
    │                                                              │
    ├─► OceanBase (easiest, MySQL compat)                         │
    │                                                              │
    ├─► TiDB (HTAP benefits)                                      │
    │                                                              │
    └─► Vitess (if want keep MySQL, just shard)                   │
```

---

## 3. RocketMQ vs Kafka vs Pulsar

### Architecture Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Message Queue Architectures                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   RocketMQ (Alipay)                                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  ┌──────────┐       ┌──────────┐       ┌──────────┐                │  │
│   │  │ NameSrv  │◄─────►│  Broker  │◄─────►│  Store   │                │  │
│   │  │ (Route)  │       │ (M/S)    │       │(CommitLog│                │  │
│   │  └──────────┘       └──────────┘       │ + Queue) │                │  │
│   │                                         └──────────┘                │  │
│   │  • LSM-tree based                                                   │  │
│   │  • Rich message types (order, scheduled, tx)                       │  │
│   │  • 10M+ TPS proven                                                   │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Apache Kafka                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  ┌──────────┐       ┌──────────┐                                  │  │
│   │  │  ZK/KRaft│◄─────►│  Broker  │◄─────► Segment files           │  │
│   │  │ (Coord)  │       │(Partition│       │(Log + Index)            │  │
│   │  └──────────┘       └──────────┘                                  │  │
│   │                                                                      │  │
│   │  • Log-centric architecture                                         │  │
│   │  • Stream processing (Kafka Streams)                                │  │
│   │  • Ecosystem maturity                                                │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Apache Pulsar                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  ┌──────────┐       ┌──────────┐       ┌──────────┐                │  │
│   │  │  ZK/etcd │◄─────►│  Broker  │◄─────►│ BookKeeper│                │  │
│   │  │ (Metadata)│      │(Stateless)│      │(Storage)  │                │  │
│   │  └──────────┘       └──────────┘       └──────────┘                │  │
│   │                                                                      │  │
│   │  • Tiered storage (offload to S3)                                   │  │
│   │  • Multi-tenancy built-in                                            │  │
│   │  • Geo-replication                                                    │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Feature Matrix

| Feature | RocketMQ | Kafka | Pulsar | Best For |
|---------|----------|-------|--------|----------|
| **Message Types** | Rich (order, scheduled, tx) | Basic + compaction | Rich + functions | RocketMQ cho complex biz |
| **Throughput** | 10M+ TPS | 1M+ TPS | 1M+ TPS | RocketMQ (proven at scale) |
| **Latency** | < 10ms | < 10ms | < 10ms | Tie |
| **Storage** | LSM-tree | Log segments | BookKeeper + Tiered | Pulsar cho long retention |
| **Geo-replication** | Yes | MirrorMaker | Native | Pulsar |
| **Multi-tenancy** | Basic | No | Built-in | Pulsar cho SaaS |
| **Ecosystem** | China-centric | Global mature | Growing | Kafka cho tooling |
| **K8s Native** | Operator | Operator | Native | Pulsar |

### When to Choose

**Choose RocketMQ if**:
- Building e-commerce/financial system (transactional msg)
- Need scheduled/delayed messages
- Operating in Alibaba Cloud
- Need proven 10M+ TPS

**Choose Kafka if**:
- Event streaming architecture
- Need Kafka Streams/Connect ecosystem
- Global team (English docs/tools)
- Log aggregation use case

**Choose Pulsar if**:
- Multi-tenant SaaS product
- Need infinite retention (tiered storage)
- Geo-replication required
- K8s-native deployment priority

---

## 4. SOFARPC vs gRPC vs Modern RPC

### Performance Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              RPC Framework Performance (requests/sec)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   250K ┤                                                    SOFARPC        │
│        │                                                ████████████         │
│   200K ┤                                            gRPC (HTTP/2)           │
│        │                                        ████████████                 │
│   150K ┤                                    Thrift                          │
│        │                                ██████████                           │
│   100K ┤                            Dubbo                                    │
│        │                        ████████                                     │
│    50K ┤                    REST (HTTP/1.1)                                  │
│        │                ████                                                 │
│     0K ┼────────────────────────────────────────────────────────────────    │
│                                                                               │
│   Note: Numbers approximate, vary by payload size and network               │
│   SOFARPC optimized for Java/financial services                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technical Comparison

| Feature | SOFARPC | gRPC | Apache Dubbo | Best For |
|---------|---------|------|--------------|----------|
| **Protocol** | Bolt (binary) | HTTP/2 + ProtoBuf | Triple (HTTP/2) | gRPC cho cross-platform |
| **Serialization** | Hessian2, Protobuf | Protobuf | Hessian2, Protobuf | gRPC (efficient) |
| **Language** | Java-focused | Multi-language | Java, Go, Node.js | gRPC cho polyglot |
| **Service Mesh** | SOFAMesh (MOSN) | Envoy (standard) | Dubbo Mesh | gRPC (standard) |
| **Load Balancing** | Rich (consistent hash) | Basic (round robin) | Rich | SOFARPC/Dubbo cho features |
| **Fault Tolerance** | Failover, broadcast, forking | Basic retry | Similar to SOFARPC | SOFARPC cho options |
| **Integration** | Spring/SOFABoot | Any framework | Spring Boot | Dubbo cho Spring |
| **Production Use** | Alipay 10+ years | Google, everywhere | Alibaba, many | gRPC (widest adoption) |

### Modern Alternative: Connect RPC

```
New Generation: Connect RPC (2023+)
┌─────────────────────────────────────────────────────────────────┐
│                    Connect RPC (buf.build)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Features:                                                     │
│   • gRPC + REST-like simplicity                                 │
│   • Streaming support                                           │
│   • Multiple protocols (Connect, gRPC, gRPC-Web)                │
│   • Generated code (TypeScript, Go, Kotlin, Swift)              │
│   • Small binary size                                           │
│                                                                 │
│   Compare to SOFARPC:                                           │
│   ┌─────────────────┬─────────────────┬─────────────────────┐  │
│   │     Aspect      │    SOFARPC      │    Connect RPC      │  │
│   ├─────────────────┼─────────────────┼─────────────────────┤  │
│   │ Protocol        │ Bolt (binary)   │ Connect (HTTP/2)    │  │
│   │ Browser support │ ❌              │ ✅ (gRPC-Web)      │  │
│   │ Code generation │ Java-focused    │ Multi-language      │  │
│   │ Ecosystem       │ Alipay-specific │ Modern, growing     │  │
│   │ Learning curve  │ Steep           │ Gentle              │  │
│   └─────────────────┴─────────────────┴─────────────────────┘  │
│                                                                 │
│   Recommendation: Consider Connect for new greenfield projects  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. SOFAMesh (MOSN) vs Istio/Linkerd

### Service Mesh Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Service Mesh Architectures                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   SOFAMesh (MOSN-based)                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Control Plane: SOFAMesh Controller                               │  │
│   │   ├── XDS API (Envoy compatible)                                    │  │
│   │   ├── Routing rules (Alibaba-specific)                              │  │
│   │   └── mTLS certificates                                             │  │
│   │                                                                     │  │
│   │   Data Plane: MOSN (Go-based)                                       │  │
│   │   ├── X-protocol (multi-protocol support)                           │  │
│   │   ├── Hot upgrade (zero downtime)                                   │  │
│   │   ├── Financial-grade stability                                     │  │
│   │   └── Bolt/SOFARPC optimized                                        │  │
│   │                                                                     │  │
│   │   Unique: Protocol extension dễ dàng (Go vs C++)                    │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Istio (Envoy-based)                                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Control Plane: Istiod                                             │  │
│   │   ├── Istio APIs (Gateway, VirtualService, etc.)                    │  │
│   │   ├── Universal (works with any service)                            │  │
│   │   └── Rich ecosystem (Kiali, Jaeger, Grafana)                        │  │
│   │                                                                     │  │
│   │   Data Plane: Envoy (C++)                                         │  │
│   │   ├── Industry standard                                             │  │
│   │   ├── WASM extensions                                               │  │
│   │   ├── High performance (C++)                                        │  │
│   │   └── Complex configuration                                         │  │
│   │                                                                     │  │
│   │   Unique: Mature ecosystem, wide adoption                         │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Linkerd (Rust-based)                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │   Control + Data: Linkerd-proxy (Rust)                            │  │
│   │   ├── Lightweight (~10MB memory)                                    │  │
│   │   ├── Simple configuration                                          │  │
│   │   ├── Slower feature velocity                                       │  │
│   │   └── Opinionated defaults                                          │  │
│   │                                                                     │  │
│   │   Unique: Simplicity, security-focused                              │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Feature Matrix

| Feature | SOFAMesh | Istio | Linkerd | Best For |
|---------|----------|-------|---------|----------|
| **Language** | Go (MOSN) | C++ (Envoy) | Rust | MOSN cho Go teams |
| **Memory** | Medium (~50MB) | High (~100MB) | Low (~10MB) | Linkerd cho resource constrained |
| **Protocol** | X-protocol (extensible) | HTTP/gRPC first | HTTP/gRPC | MOSN cho custom protocols |
| **Hot Upgrade** | ✅ Yes | ❌ No | ❌ No | MOSN cho zero downtime |
| **Ecosystem** | Alibaba | Universal | CNCF | Istio cho standardization |
| **mTLS** | ✅ | ✅ | ✅ | Tie |
| **Learning Curve** | Steep | Very steep | Gentle | Linkerd cho simplicity |
| **Customization** | Easy (Go) | Hard (C++) | Medium | MOSN cho rapid iteration |

### Migration Path

```
Legacy to Modern Service Mesh:

Traditional RPC ──────────────────────────────────────────────────►
    │                                                              │
    ├─► SOFAMesh (if using SOFARPC, Bolt protocol)                 │
    │                                                              │
    ├─► Istio (if using standard gRPC/HTTP, want ecosystem)         │
    │                                                              │
    └─► Linkerd (if want simplicity, security-first)              │
```

---

## 6. CTU Risk Control vs Modern ML Platforms

### Comparison

| Feature | CTU (Alipay) | Modern MLOps (Seldon/KFServing) | Custom Fraud Platform |
|---------|--------------|----------------------------------|----------------------|
| **Domain** | Fraud-specific | General-purpose | Varies |
| **Latency** | < 100ms optimized | Configurable | Depends |
| **Features** | 8-dimension built-in | Bring your own | Pre-built templates |
| **Graph Analysis** | Built-in GNN | Add Neo4j/etc | Optional |
| **Real-time** | Native | Configurable | Varies |
| **Explainability** | Rule-based fallback | SHAP/LIME | Varies |
| **A/B Testing** | Built-in | Experimentation platform | Varies |
| **Cost** | Internal development | Cloud service fees | License + infra |

### Modern Alternatives

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Modern Fraud Detection Stack (2024)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   Feature Engineering                                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Feast / Tecton (Feature Store)                                      │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│   │  │ Real-time   │  │ Batch       │  │ Streaming   │                  │  │
│   │  │ features    │  │ features    │  │ features    │                  │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘                  │  │
│   │                                                                      │  │
│   │  Alternative to CTU feature computation:                            │  │
│   │  • Tecton: Enterprise feature platform                              │  │
│   │  • Feast: Open source feature store                                 │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Model Serving                                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Seldon Core / KServe / BentoML                                    │  │
│   │                                                                      │  │
│   │  ┌─────────────────────────────────────────────────────────────┐   │  │
│   │  │  Ensemble Serving (similar to CTU multi-model)               │   │  │
│   │  │  • XGBoost + PyTorch + Rules                                 │   │  │
│   │  │  • A/B testing built-in                                      │   │  │
│   │  │  • Canary deployments                                        │   │  │
│   │  │  • Drift detection                                           │   │  │
│   │  └─────────────────────────────────────────────────────────────┘   │  │
│   │                                                                      │  │
│   │  Alternative to CTU inference engine:                               │  │
│   │  • Seldon: Kubernetes-native, rich features                         │  │
│   │  • KServe: Standardized, serverless scaling                         │  │
│   │  • BentoML: Developer-friendly, framework agnostic                │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│   Graph Analysis                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Neo4j / TigerGraph / Dgraph                                       │  │
│   │                                                                      │  │
│   │  Alternative to CTU GNN:                                            │  │
│   │  • Neo4j GDS: Graph Data Science library                            │  │
│   │  • TigerGraph: Native parallel graph                               │  │
│   │  • PyTorch Geometric: Custom GNN models                             │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Recommendation

**Build vs Buy Decision**:

| Scale | Recommendation | Stack |
|-------|----------------|-------|
| Startup (< 1M users) | Buy | Stripe Radar / Sift Science |
| Growth (1M-10M) | Hybrid | Custom rules + purchased ML |
| Enterprise (> 10M) | Build | Feast + Seldon + Custom GNN |
| Financial (Alipay scale) | Build (like CTU) | Custom end-to-end |

---

## 7. Tổng Hợp: Build vs Use Modern

### Decision Framework

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              Decision Tree: Alipay Stack vs Modern Tech                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   Bạn đang ở đâu?                                                             │
│                                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │  [Bắt đầu mới] ─────┐                                              │  │
│   │                     ▼                                              │  │
│   │              ┌──────────────┐                                      │  │
│   │              │ Cloud Native │                                      │  │
│   │              │   Stack      │                                      │  │
│   │              │ • Kubernetes │                                      │  │
│   │              │ • CockroachDB│                                      │  │
│   │              │ • Kafka      │                                      │  │
│   │              │ • gRPC       │                                      │  │
│   │              │ • Istio      │                                      │  │
│   │              └──────────────┘                                      │  │
│   │                                                                     │  │
│   │  [Đang dùng Java/Alibaba Cloud] ─┐                                │  │
│   │                                   ▼                                │  │
│   │              ┌──────────────┐                                    │  │
│   │              │ SOFAStack    │                                    │  │
│   │              │   Hybrid     │                                    │  │
│   │              │ • SOFABoot   │                                    │  │
│   │              │ • OceanBase  │                                    │  │
│   │              │ • RocketMQ   │                                    │  │
│   │              │ • SOFAMesh   │                                    │  │
│   │              └──────────────┘                                    │  │
│   │                                                                     │  │
│   │  [Đang dùng Legacy Java] ─────┐                                   │  │
│   │                                ▼                                  │  │
│   │              ┌──────────────┐                                   │  │
│   │              │ Gradual      │                                   │  │
│   │              │ Migration    │                                   │  │
│   │              │ • SOFAStack  │                                   │  │
│   │              │ • CockroachDB│                                   │  │
│   │              │ • Kafka      │                                   │  │
│   │              └──────────────┘                                   │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Final Recommendations by Component

| Component | Modern Choice | When to Use Alipay Stack |
|-----------|---------------|---------------------------|
| **Orchestration** | Kubernetes | Only if locked to Alibaba Cloud |
| **Database** | CockroachDB/TiDB | Need 544K+ TPS, custom HW |
| **Message Queue** | Kafka/Pulsar | Need 10M+ TPS, scheduled msgs |
| **RPC** | gRPC/Connect | Only if heavy Java/Spring |
| **Service Mesh** | Istio/Linkerd | Using Bolt protocol |
| **Risk Control** | Buy (Sift/Stripe) | Scale > 10M users, custom needs |
| **Cache** | Redis Cluster | Tair cho Alibaba Cloud |

---

## 8. Code Migration Examples

### From SOFARPC to gRPC

```java
// SOFARPC
@SofaService(bindings = {@SofaBinding(bindingType = "bolt")})
public class PaymentServiceImpl implements PaymentService {
    @Override
    public PaymentResult pay(PaymentRequest request) { ... }
}

// gRPC equivalent
@GrpcService
public class PaymentServiceGrpc extends PaymentServiceGrpcImplBase {
    @Override
    public void pay(PaymentRequest request, StreamObserver<PaymentResult> response) {
        // Implementation
        response.onNext(result);
        response.onCompleted();
    }
}
```

### From RocketMQ to Kafka

```java
// RocketMQ
Message msg = new Message("topic", "tag", "body".getBytes());
producer.send(msg);

// Kafka equivalent
ProducerRecord<String, String> record = 
    new ProducerRecord<>("topic", "key", "body");
producer.send(record);
```

---

**End of Modern Tech Comparison**

*Recommendation: For new projects, prefer modern cloud-native stack. For Alibaba Cloud environments or need Alipay-scale performance, SOFAStack is proven.*

