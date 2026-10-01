# Master Agent Knowledge Index — 2027 SOTA Architecture & Engineering Standards

> **Epoch:** 2026-10-01T19:45:00+07:00  
> **Authoring Swarm:** `@vesviet-team` (`@architect`, `@content-manager`, `@technical-writer`, `@qa-engineer`)  
> **Purpose:** Ultra-compact, high-density architectural cheat-sheets and decision matrices designed for instant LLM/Agent retrieval without context window bloat.  
> **Total Knowledge Cards:** 26 High-Signal Cards across 6 Core Domains.  

---

## Quick Domain Jump Matrix
- [1. E-Commerce Architecture](#1-e-commerce-architecture) (5 Cards)
- [2. Banking & FinTech Architecture](#2-banking--fintech-architecture) (3 Cards)
- [3. AI, SLM & Agentic Systems](#3-ai-slm--agentic-systems) (5 Cards)
- [4. Distributed Systems & Architectural Showdowns](#4-distributed-systems--architectural-showdowns) (6 Cards)
- [5. Ride-Hailing & Geospatial Architecture](#5-ride-hailing--geospatial-architecture) (4 Cards)
- [6. Cloud Infrastructure & Resilience](#6-cloud-infrastructure--resilience) (3 Cards)

---

## 1. E-Commerce Architecture

| Card Slug | Title & Key Themes | Tags | File Path |
| :--- | :--- | :--- | :--- |
| [`alipay-double-11-architecture`](knowledge/ecommerce/alipay-double-11-architecture.md) | **Alipay Double 11 Peak Architecture: OceanBase Multi-Paxos & Zero-Loss Financial Transactions** | `#alipay`, `#oceanbase`, `#paxos` | [`knowledge/ecommerce/alipay-double-11-architecture.md`](knowledge/ecommerce/alipay-double-11-architecture.md) |
| [`shopee-flash-sale-architecture`](knowledge/ecommerce/shopee-flash-sale-architecture.md) | **Shopee Flash Sale Engine: Multi-Tier Traffic Shield & High-Concurrency Inventory Gates** | `#shopee`, `#flash-sale`, `#redis-sentinel` | [`knowledge/ecommerce/shopee-flash-sale-architecture.md`](knowledge/ecommerce/shopee-flash-sale-architecture.md) |
| [`composable-ecommerce-microservices`](knowledge/ecommerce/composable-ecommerce-microservices.md) | **Composable E-Commerce: 21-Service Decomposition with Golang, DDD & Dapr Event Mesh** | `#golang`, `#microservices`, `#ddd` | [`knowledge/ecommerce/composable-ecommerce-microservices.md`](knowledge/ecommerce/composable-ecommerce-microservices.md) |
| [`order-allocation-fulfillment`](knowledge/ecommerce/order-allocation-fulfillment.md) | **Real-Time Multi-Warehouse Order Allocation & Dynamic Inventory Routing** | `#fulfillment`, `#wms`, `#inventory-allocation` | [`knowledge/ecommerce/order-allocation-fulfillment.md`](knowledge/ecommerce/order-allocation-fulfillment.md) |
| [`cart-checkout-redis-lua`](knowledge/ecommerce/cart-checkout-redis-lua.md) | **High-Throughput Shopping Cart & Redis Lua Stock Reservation Patterns** | `#cart`, `#checkout`, `#redis-lua` | [`knowledge/ecommerce/cart-checkout-redis-lua.md`](knowledge/ecommerce/cart-checkout-redis-lua.md) |

## 2. Banking & FinTech Architecture

| Card Slug | Title & Key Themes | Tags | File Path |
| :--- | :--- | :--- | :--- |
| [`core-banking-double-entry-ledger`](knowledge/banking-fintech/core-banking-double-entry-ledger.md) | **Core Banking Architecture: Double-Entry Immutable Ledgers & ACID Financial Invariants** | `#core-banking`, `#double-entry`, `#immutable-ledger` | [`knowledge/banking-fintech/core-banking-double-entry-ledger.md`](knowledge/banking-fintech/core-banking-double-entry-ledger.md) |
| [`microfinance-event-sourcing`](knowledge/banking-fintech/microfinance-event-sourcing.md) | **Microfinance & Lending Platforms: Event Sourcing & CQRS Audit Traces** | `#microfinance`, `#event-sourcing`, `#cqrs` | [`knowledge/banking-fintech/microfinance-event-sourcing.md`](knowledge/banking-fintech/microfinance-event-sourcing.md) |
| [`distributed-saga-reconciliation`](knowledge/banking-fintech/distributed-saga-reconciliation.md) | **Distributed Financial Sagas & Asynchronous Reconciliation Workflows** | `#saga`, `#reconciliation`, `#temporal` | [`knowledge/banking-fintech/distributed-saga-reconciliation.md`](knowledge/banking-fintech/distributed-saga-reconciliation.md) |

## 3. AI, SLM & Agentic Systems

| Card Slug | Title & Key Themes | Tags | File Path |
| :--- | :--- | :--- | :--- |
| [`vllm-v1-kv-cache-optimization`](knowledge/ai-slm-agentic/vllm-v1-kv-cache-optimization.md) | **vLLM v1 Deep Dive: PagedAttention, Chunked Prefill & Disaggregated KV Cache** | `#vllm`, `#kv-cache`, `#paged-attention` | [`knowledge/ai-slm-agentic/vllm-v1-kv-cache-optimization.md`](knowledge/ai-slm-agentic/vllm-v1-kv-cache-optimization.md) |
| [`slm-hybrid-distillation-deepseek-r1`](knowledge/ai-slm-agentic/slm-hybrid-distillation-deepseek-r1.md) | **Small Language Models (SLMs): Knowledge Distillation from DeepSeek-R1 to Edge Devices** | `#slm`, `#deepseek-r1`, `#distillation` | [`knowledge/ai-slm-agentic/slm-hybrid-distillation-deepseek-r1.md`](knowledge/ai-slm-agentic/slm-hybrid-distillation-deepseek-r1.md) |
| [`generative-ui-edge-architecture`](knowledge/ai-slm-agentic/generative-ui-edge-architecture.md) | **Generative UI Architecture: Streaming Dynamic React Server Components from the Edge** | `#generative-ui`, `#cloudflare-workers`, `#rsc` | [`knowledge/ai-slm-agentic/generative-ui-edge-architecture.md`](knowledge/ai-slm-agentic/generative-ui-edge-architecture.md) |
| [`autonomous-agent-swarms-litellm`](knowledge/ai-slm-agentic/autonomous-agent-swarms-litellm.md) | **Autonomous AI Agent Swarms: A2A Protocols & LiteLLM Gateway Orchestration** | `#agent-swarms`, `#litellm`, `#a2a-protocol` | [`knowledge/ai-slm-agentic/autonomous-agent-swarms-litellm.md`](knowledge/ai-slm-agentic/autonomous-agent-swarms-litellm.md) |
| [`vector-database-hnsw-search`](knowledge/ai-slm-agentic/vector-database-hnsw-search.md) | **Custom Golang Vector Database Engine: HNSW Graphs & Hybrid Lexical-Semantic Search** | `#vector-search`, `#hnsw`, `#golang` | [`knowledge/ai-slm-agentic/vector-database-hnsw-search.md`](knowledge/ai-slm-agentic/vector-database-hnsw-search.md) |

## 4. Distributed Systems & Architectural Showdowns

| Card Slug | Title & Key Themes | Tags | File Path |
| :--- | :--- | :--- | :--- |
| [`grpc-protobuf-vs-http-rest`](knowledge/distributed-systems/grpc-protobuf-vs-http-rest.md) | **Protocol Showdown: gRPC / Protobuf v3 vs. HTTP/REST JSON in High-Throughput Services** | `#grpc`, `#protobuf`, `#http-rest` | [`knowledge/distributed-systems/grpc-protobuf-vs-http-rest.md`](knowledge/distributed-systems/grpc-protobuf-vs-http-rest.md) |
| [`kafka-vs-nats-jetstream-event-mesh`](knowledge/distributed-systems/kafka-vs-nats-jetstream-event-mesh.md) | **Message Broker Showdown: Apache Kafka vs. NATS JetStream for Event-Driven Microservices** | `#kafka`, `#nats-jetstream`, `#event-mesh` | [`knowledge/distributed-systems/kafka-vs-nats-jetstream-event-mesh.md`](knowledge/distributed-systems/kafka-vs-nats-jetstream-event-mesh.md) |
| [`mysql-sharding-vs-tidb-newsql`](knowledge/distributed-systems/mysql-sharding-vs-tidb-newsql.md) | **Database Scaling Showdown: Sharded MySQL (Vitess) vs. Distributed TiDB NewSQL** | `#mysql`, `#vitess`, `#sharding` | [`knowledge/distributed-systems/mysql-sharding-vs-tidb-newsql.md`](knowledge/distributed-systems/mysql-sharding-vs-tidb-newsql.md) |
| [`redis-state-vs-dapr-virtual-actors`](knowledge/distributed-systems/redis-state-vs-dapr-virtual-actors.md) | **State Management Showdown: Redis Distributed State vs. Dapr Virtual Actors** | `#redis`, `#dapr`, `#virtual-actors` | [`knowledge/distributed-systems/redis-state-vs-dapr-virtual-actors.md`](knowledge/distributed-systems/redis-state-vs-dapr-virtual-actors.md) |
| [`modular-monolith-vs-microservices`](knowledge/distributed-systems/modular-monolith-vs-microservices.md) | **Architecture Paradigm Showdown: Go Modular Monolith vs. Microservices vs. SpinKube Wasm** | `#modular-monolith`, `#microservices`, `#spinkube` | [`knowledge/distributed-systems/modular-monolith-vs-microservices.md`](knowledge/distributed-systems/modular-monolith-vs-microservices.md) |
| [`primary-key-uuidv7-snowflake-bigint`](knowledge/distributed-systems/primary-key-uuidv7-snowflake-bigint.md) | **Primary Key Showdown: UUIDv7 vs. Twitter Snowflake vs. BigInt Auto-Increment** | `#primary-key`, `#uuidv7`, `#snowflake` | [`knowledge/distributed-systems/primary-key-uuidv7-snowflake-bigint.md`](knowledge/distributed-systems/primary-key-uuidv7-snowflake-bigint.md) |

## 5. Ride-Hailing & Geospatial Architecture

| Card Slug | Title & Key Themes | Tags | File Path |
| :--- | :--- | :--- | :--- |
| [`h3-geospatial-indexing-uber-grab`](knowledge/ride-hailing-geospatial/h3-geospatial-indexing-uber-grab.md) | **Geospatial Indexing: Uber H3 Hexagonal Hierarchies vs. Google S2 vs. PostGIS Geohash** | `#h3`, `#geospatial`, `#uber` | [`knowledge/ride-hailing-geospatial/h3-geospatial-indexing-uber-grab.md`](knowledge/ride-hailing-geospatial/h3-geospatial-indexing-uber-grab.md) |
| [`dispatch-matching-surge-pricing`](knowledge/ride-hailing-geospatial/dispatch-matching-surge-pricing.md) | **Real-Time Dispatch Matching & Dynamic Surge Pricing Architecture** | `#dispatch`, `#surge-pricing`, `#bipartite-matching` | [`knowledge/ride-hailing-geospatial/dispatch-matching-surge-pricing.md`](knowledge/ride-hailing-geospatial/dispatch-matching-surge-pricing.md) |
| [`urban-canyon-gps-kalman-filtering`](knowledge/ride-hailing-geospatial/urban-canyon-gps-kalman-filtering.md) | **Urban Canyon GPS Multipath Mitigation: Extended Kalman Filtering & Map Matching** | `#gps`, `#urban-canyon`, `#kalman-filter` | [`knowledge/ride-hailing-geospatial/urban-canyon-gps-kalman-filtering.md`](knowledge/ride-hailing-geospatial/urban-canyon-gps-kalman-filtering.md) |
| [`realtime-push-ramen-architecture`](knowledge/ride-hailing-geospatial/realtime-push-ramen-architecture.md) | **Real-Time Driver Location Streaming: Uber Ramen WebSocket Gateway Architecture** | `#websocket`, `#realtime-push`, `#ramen` | [`knowledge/ride-hailing-geospatial/realtime-push-ramen-architecture.md`](knowledge/ride-hailing-geospatial/realtime-push-ramen-architecture.md) |

## 6. Cloud Infrastructure & Resilience

| Card Slug | Title & Key Themes | Tags | File Path |
| :--- | :--- | :--- | :--- |
| [`aws-mysql-8-eol-magento-upgrade`](knowledge/cloud-infrastructure/aws-mysql-8-eol-magento-upgrade.md) | **AWS RDS MySQL 8.0 EOL Migration Playbook: Blue/Green Deployments & ProxySQL Multiplexing** | `#aws-rds`, `#mysql-84`, `#proxysql` | [`knowledge/cloud-infrastructure/aws-mysql-8-eol-magento-upgrade.md`](knowledge/cloud-infrastructure/aws-mysql-8-eol-magento-upgrade.md) |
| [`aws-eks-vs-ecs-architectural-decision`](knowledge/cloud-infrastructure/aws-eks-vs-ecs-architectural-decision.md) | **Container Orchestration Showdown: AWS EKS (Kubernetes) vs. AWS ECS (Fargate)** | `#aws-eks`, `#aws-ecs`, `#kubernetes` | [`knowledge/cloud-infrastructure/aws-eks-vs-ecs-architectural-decision.md`](knowledge/cloud-infrastructure/aws-eks-vs-ecs-architectural-decision.md) |
| [`envoy-gateway-vs-cilium-ebpf-service-mesh`](knowledge/cloud-infrastructure/envoy-gateway-vs-cilium-ebpf-service-mesh.md) | **Service Mesh Showdown: Envoy Proxy Sidecar vs. Cilium eBPF Kernel Routing** | `#envoy`, `#cilium`, `#ebpf` | [`knowledge/cloud-infrastructure/envoy-gateway-vs-cilium-ebpf-service-mesh.md`](knowledge/cloud-infrastructure/envoy-gateway-vs-cilium-ebpf-service-mesh.md) |
| [`zero-trust-spiffe-spire-istio-golang`](knowledge/cloud-infrastructure/zero-trust-spiffe-spire-istio-golang.md) | **Zero-Trust Service Mesh Security: SPIFFE/SPIRE Cryptographic Workload Identities in Go** | `#zero-trust`, `#spiffe`, `#spire` | [`knowledge/cloud-infrastructure/zero-trust-spiffe-spire-istio-golang.md`](knowledge/cloud-infrastructure/zero-trust-spiffe-spire-istio-golang.md) |

---

## Architecture Governance & Usage Standard for Coding Agents
1. **Context Window Efficiency:** Always read targeted cards in `knowledge/<domain>/<topic>.md` rather than searching loose historical dossiers.
2. **Production Realism:** All code snippets, configurations, and benchmarks reflect verified production standards in Go 1.25, Redis 7.4, MySQL 8.4 LTS, and Kubernetes 1.30+.
3. **Zero Leaks:** Internal authority follows the One-Way Authority Rule (`learn` references `tanhdev.com`, 0 outbound leaks from `vesviet`).
