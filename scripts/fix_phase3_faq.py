#!/usr/bin/env python3
"""
Phase 3: Add FAQ sections to posts missing them.
Content-Writer role: "FAQ block at end of article when SERP/brief requires it:
format as ## FAQ with ### Question? subheadings for schema compatibility"

For each post, generate 3-5 relevant Q&A pairs based on:
- Post title/description
- Common PAA (People Also Ask) patterns for the topic
"""

import os
import re
import glob

POSTS_DIR = r"D:\myproject\vesviet\content\posts"

# Pre-defined FAQ sets for each post needing FAQ (based on topic analysis)
POST_FAQS = {
    "building-custom-golang-vector-database-engine-hnsw.md": [
        ("What is HNSW and why is it used in vector databases?",
         "HNSW (Hierarchical Navigable Small World) is a graph-based approximate nearest neighbor algorithm. It builds multi-layer proximity graphs achieving O(log n) search complexity. HNSW is preferred because it delivers <10ms p99 latency at 95%+ recall, outperforming brute-force cosine similarity by 100–1000x on datasets of 1M+ vectors."),
        ("How does SIMD acceleration improve vector search in Go?",
         "SIMD (Single Instruction, Multiple Data) allows CPU cores to compute dot products or cosine similarities on 8–16 float32 values simultaneously. In Go, using `unsafe` + AVX2 intrinsics via CGO cuts inner-product computation time by 4–8x compared to pure Go loops. This is critical for high-QPS embedding retrieval."),
        ("When should you build a custom vector DB instead of using Qdrant or Milvus?",
         "Build custom when: (1) you need embedding dimensions outside standard ranges, (2) your access patterns require non-standard indexing strategies, (3) you're embedding at the database layer with domain-specific distance metrics, or (4) operational complexity of a separate service exceeds the benefit. For most use cases, Qdrant or Milvus are faster to production."),
        ("What are the memory trade-offs of HNSW index construction?",
         "HNSW stores all vectors plus graph edges in RAM. A 1M vector dataset with 1024 dimensions at float32 consumes ~4GB for vectors alone. Graph overhead adds 20–40% depending on efConstruction and M parameters. Use HNSW on-disk variants (DiskANN, ScaNN) when RAM is constrained, accepting 3–5x higher latency."),
    ],

    "building-high-throughput-event-driven-microservices-go-nats-jetstream-cqrs.md": [
        ("What is the difference between NATS Core and NATS JetStream?",
         "NATS Core provides at-most-once fire-and-forget messaging with no persistence. NATS JetStream adds durable streams, consumer groups, exactly-once semantics, and replay from offset. For production microservices requiring guaranteed delivery, JetStream is required. Core NATS latency is <1ms; JetStream adds 1–3ms for persistence."),
        ("How does CQRS reduce database contention in high-throughput systems?",
         "CQRS separates read and write models into independent services. Write-side uses normalized storage for consistency; read-side uses denormalized projections optimized for queries. This removes contention on a single database, allowing write throughput to scale independently. At 50K+ events/sec, CQRS enables horizontal scaling without read locks."),
        ("What NATS JetStream consumer strategy is best for Go microservices?",
         "Use push consumers for low-latency event handlers (<5ms SLA). Use pull consumers for batch processors and worker pools where backpressure control is needed. In Go, pair pull consumers with `errgroup` for bounded concurrency. Set `MaxDeliver` and `AckWait` tuned to your service's p99 processing time to avoid double-delivery."),
        ("How do you handle message ordering in distributed NATS JetStream consumers?",
         "NATS JetStream guarantees per-stream ordering. For per-entity ordering (e.g., order events for OrderID=X), use subject-based partitioning: `events.orders.{orderID}`. Bind one consumer per partition to maintain sequence. For cross-entity ordering, use sequence numbers in payload headers and idempotent handlers in the consumer."),
    ],

    "osrm-vs-graphhopper-architecture-comparison.md": [
        ("What is the main architectural difference between OSRM and GraphHopper?",
         "OSRM uses pre-computed Contraction Hierarchies (CH): all routing is done at query time using pre-built shortcut graphs stored in shared memory. GraphHopper supports both CH and Multi-Level Dijkstra (MLD), offering flexible custom routing profiles. OSRM delivers <1ms routing latency; GraphHopper trades 5–20ms for runtime profile flexibility."),
        ("Which routing engine is better for custom vehicle profiles?",
         "GraphHopper wins for custom profiles. Its Weighting API allows runtime-configurable turn penalties, vehicle-specific restrictions, and conditional speed modifiers without rebuilding the full graph. OSRM requires a full CH pre-computation (30–60 min for Europe OSM) for every profile change. For dynamic routing needs, GraphHopper's MLD is the correct choice."),
        ("Can OSRM handle real-time traffic updates?",
         "Yes, via the `osrm-datastore` shared memory mechanism. New speed data (from HERE, TomTom, or OSM) can be hot-swapped into shared memory without restarting the routing server. This achieves zero-downtime traffic updates with sub-second switchover. However, OSRM traffic integration requires Edge-based profiles, which must be pre-configured before initial graph build."),
        ("What is the recommended infrastructure for self-hosting OSRM at production scale?",
         "For Western Europe or continental US: 64–128GB RAM (CH graph for Europe ~30GB), 8+ cores, NVMe SSD for graph loading. Use Kubernetes with a StatefulSet and POSIX shared memory volume. Pre-load graph in init container; expose via ClusterIP. Scale horizontally behind a LoadBalancer — OSRM is stateless per request after graph load."),
    ],

    "strangler-fig-shared-database-quick-win.md": [
        ("What is the Strangler Fig pattern and when should you use it?",
         "Strangler Fig is a migration pattern where new microservices are built alongside a legacy monolith, routing traffic incrementally until the old system can be retired. Use it when a full rewrite is too risky: it allows zero-downtime migration, A/B traffic splitting via API gateway, and rollback without data loss. Ideal for Magento-to-microservices migrations."),
        ("What is the difference between Shared DB, CDC, and Event Bus separation?",
         "Shared DB: both old and new services share one database — lowest migration risk but highest long-term coupling. CDC (Debezium): reads database WAL logs to replicate changes to new services in near real-time with no application changes. Event Bus: both services publish domain events to Kafka/NATS — highest decoupling but requires dual-write coordination during transition."),
        ("How do you prevent data inconsistency during a Strangler Fig migration?",
         "Use the Transactional Outbox Pattern: write business events and data changes in a single DB transaction, then have a relay (Debezium) publish from the outbox table. This guarantees at-least-once event delivery without 2PC. Combine with idempotent consumers in the new service to handle duplicate events safely."),
        ("When should you choose Debezium CDC over direct API calls between old and new services?",
         "Choose CDC when: (1) the legacy service cannot be modified to emit events, (2) you need real-time sync without polling, (3) you require replay capability (CDC can re-stream from any WAL offset). Use direct API calls when latency is critical (<10ms) and the source service can be updated to emit webhooks or events synchronously."),
    ],

    "temporal-saga-pattern-golang-distributed-transactions-guide.md": [
        ("What is the Temporal Saga pattern and how does it differ from 2PC?",
         "Temporal Sagas decompose distributed transactions into a sequence of local transactions with compensating actions for rollback. Unlike 2PC (Two-Phase Commit), Sagas don't hold distributed locks — each step commits independently, making them resilient to partial failures. Temporal durably persists workflow state in its event sourcing store, enabling automatic retry and compensation."),
        ("How does Temporal handle workflow failures and compensation?",
         "Temporal replays workflow history from the event log on failure. When a workflow activity fails beyond retry limits, Temporal executes registered compensation activities in reverse LIFO order. Compensation must be idempotent — use the workflow's RunID as an idempotency key. Temporal guarantees compensation runs exactly once using its durable execution engine."),
        ("What is the difference between Temporal Workflow and Activity in Go?",
         "A Workflow in Go is a deterministic orchestration function that cannot perform I/O directly. Activities are the I/O-capable units (DB writes, API calls, Kafka publishes) scheduled by the Workflow. The separation enables Temporal to replay Workflow history deterministically while Activities are retried independently with configurable timeouts and backoff."),
        ("How do you set up Temporal for high-availability in production?",
         "Deploy Temporal Server as a multi-replica StatefulSet with external PostgreSQL (for Persistence) and Elasticsearch (for visibility). Use Temporal's Frontend, History, Matching, and Worker services separately for independent scaling. In Go, configure the SDK Worker with `MaxConcurrentActivityExecutionSize` and `MaxConcurrentWorkflowTaskExecutionSize` tuned to your host's CPU/memory."),
        ("What are the cost trade-offs of using Temporal vs a simple job queue?",
         "Temporal adds 10–30ms overhead per activity vs direct queue dispatch, plus storage cost for event history (1–5KB per workflow event). A simple Redis job queue (Asynq, Sidekiq) is cheaper and faster for stateless tasks. Use Temporal when: workflows span >30 seconds, require compensation logic, need audit trails, or must survive server restarts mid-execution."),
    ],

    "temporal-saga-pattern-golang-distributed-transactions.md": [
        ("What is an Orchestrated Saga in Temporal Go SDK?",
         "An Orchestrated Saga uses a central Workflow function as the coordinator. It sequentially calls Activity functions for each business step and registers compensating Activities for each step. On failure, the Workflow executes compensations in reverse order. Temporal durably records every step in its event log, enabling automatic recovery without application-level checkpointing."),
        ("How do you implement a banking Saga with Temporal in Go?",
         "Define a Workflow struct with step functions (DebitAccount, CreditAccount, NotifyUser) and compensation functions (RefundDebit, ReverseCredit). Use `workflow.ExecuteActivity` for each step. Register compensations in a defer block with `workflow.Go` for parallel execution. Use workflow RunID as idempotency key in each Activity to prevent duplicate DB writes on retry."),
        ("What happens when a Temporal Activity times out mid-saga?",
         "Temporal retries the Activity per the configured RetryPolicy (exponential backoff, max attempts). If all retries fail, the Activity returns an `ApplicationError` to the Workflow. The Workflow's error handler then executes compensation Activities in reverse. During retry, Temporal guarantees the Activity is retried on a live Worker — the Workflow state is preserved in the event log."),
        ("How does Temporal prevent double-charging in payment sagas?",
         "Use idempotency keys passed as Activity parameters. In the payment service, use a unique key (WorkflowID + ActivityID) as the idempotency key for the payment API call. Store processed keys in Redis with a TTL matching your retry window. Temporal's at-least-once Activity delivery is safe when Activities are idempotent."),
    ],

    "zero-trust-service-mesh-security-spiffe-spire-istio-golang.md": [
        ("What is SPIFFE and how does it differ from traditional TLS certificates?",
         "SPIFFE (Secure Production Identity Framework for Everyone) provides workload identity via X.509 SVIDs (SPIFFE Verifiable Identity Documents) instead of hostname-based certificates. Each Go service receives a short-lived SPIFFE ID (e.g., `spiffe://example.org/ns/payments/sa/checkout`) issued by SPIRE. Unlike static TLS certs, SVIDs rotate automatically every hour, reducing exposure from credential theft."),
        ("How does Istio mTLS integrate with SPIRE for workload attestation?",
         "Istio uses its Pilot Agent as the SDS (Secret Discovery Service) client. When integrated with SPIRE, the SPIRE Agent replaces Pilot's Citadel CA for certificate issuance. Each Envoy sidecar requests its SVID from the local SPIRE Agent via Unix socket. Istio policy then enforces mTLS between all service pairs using these SVID certificates transparently to the Go application."),
        ("What is Zero Trust and why is it critical for microservices?",
         "Zero Trust assumes no network perimeter: every service-to-service call must be authenticated and authorized, even within the cluster. In microservices, East-West traffic (service-to-service) is often unencrypted on internal networks. Zero Trust + mTLS encrypts all East-West traffic and binds each connection to a cryptographic workload identity, eliminating lateral movement from compromised pods."),
        ("How do you enforce Zero Trust authorization policies in Istio with Go?",
         "Use Istio `AuthorizationPolicy` with `source.principal` matching SPIFFE IDs: `spiffe://cluster.local/ns/payments/sa/checkout-service`. In Go, add JWT validation middleware for user-facing APIs. Combine Istio RBAC (network layer) with Open Policy Agent (OPA) for fine-grained request-level authorization. Log all denied requests to audit trail via Envoy access logs."),
        ("What is the performance overhead of mTLS in a high-throughput Go service?",
         "mTLS adds 0.5–2ms handshake overhead per new connection. With connection pooling (HTTP/2 multiplexing, gRPC keep-alive), amortized overhead drops to <0.1ms per request. In benchmarks at 10K RPS, mTLS adds <5% CPU overhead with Envoy sidecar proxy. Short-lived SVID rotation (1hr) causes periodic handshake bursts — mitigate with connection warm-up in Go HTTP client pool."),
    ],

    "cloudflare-zero-devops-ecommerce.md": [
        ("What is Zero DevOps architecture and how does Cloudflare enable it?",
         "Zero DevOps means deploying and scaling production applications without managing servers, containers, or infrastructure. Cloudflare Workers run at the edge in 330+ PoPs globally, auto-scaling to zero when idle. Combined with D1 (SQLite at edge), KV, and R2 (S3-compatible storage), you can build full-stack e-commerce without Kubernetes, Docker, or cloud VMs."),
        ("How does Turborepo improve Cloudflare Workers development?",
         "Turborepo provides monorepo task caching and parallel builds for multi-package Cloudflare projects. For a Cloudflare Workers + Pages + D1 monorepo, Turborepo's remote cache stores build artifacts, cutting CI times by 60–80% when only one package changes. Use `turbo run deploy --filter=@app/storefront` to deploy only changed Workers without rebuilding unchanged packages."),
        ("What are the limitations of Cloudflare D1 for e-commerce databases?",
         "D1 (SQLite) current limitations: 10GB max database size, no multi-region write replication (single primary at edge), no full-text search without FTS5 extension, and no stored procedures. For e-commerce, D1 suits catalog and session storage. For high-write transactional data (orders, payments), pair D1 with Durable Objects or an external PostgreSQL via Cloudflare Hyperdrive."),
        ("How do you handle Cloudflare Workers CPU limits in e-commerce?",
         "Cloudflare Workers have a 50ms CPU time limit per request (Paid plan: 30s wall-clock, 50ms CPU). For CPU-intensive operations (image processing, PDF generation, complex queries), offload to Cloudflare AI Workers or Queues. Design Storefronts as thin API consumers — move business logic to Workers that run behind Queues with longer CPU budgets (15 min on Queues)."),
    ],

    "laravel-vs-golang-when-to-add-features.md": [
        ("When should you add a new feature in Laravel vs migrating to Go?",
         "Add the feature in Laravel when: the feature fits existing Eloquent models, the team's PHP expertise is high, and performance SLA is >100ms. Migrate to Go when: the feature requires <10ms response time, handles >1K concurrent requests, or involves CPU-bound processing (image, video, ML inference). Don't migrate prematurely — profile first with Laravel Telescope."),
        ("What is the Strangler Fig pattern for Laravel to Go migration?",
         "Route new endpoints to Go microservices via Nginx or Kong API Gateway while keeping existing Laravel routes intact. Use Debezium CDC to sync Laravel's MySQL data to Go services' PostgreSQL. Gradually move traffic using weighted routing: 10% → 50% → 100%. Laravel remains the fallback until the Go service has 30+ days of production stability."),
        ("What are the real performance differences between Laravel and Go for APIs?",
         "Benchmarks at equivalent workloads (CRUD + auth): Laravel averages 800–2,000 RPS with 30–80ms p99 latency. Go (Gin/Fiber) achieves 15,000–50,000 RPS with 1–5ms p99 latency. The 10–20x throughput difference matters when you're CPU-constrained or paying for compute per request. For most CRUD-heavy features, Laravel's developer velocity outweighs Go's throughput advantage."),
        ("How do you set up gRPC internal APIs between Laravel and Go services?",
         "Generate Protobuf stubs for both PHP (using protoc-gen-php) and Go. In Laravel, use the `grpc/grpc` PHP extension and a gRPC client in a Service class. In Go, implement the gRPC server with reflection for debugging. Use mTLS between services (SPIFFE SVIDs or static certs). For non-critical paths, REST with JSON is simpler and sufficient."),
    ],

    "mysql-horizontal-scaling.md": [
        ("What is the difference between Vitess and GORM Sharding for MySQL?",
         "Vitess is a database proxy layer (VTGate) that handles sharding transparently — applications connect to Vitess as if it's a single MySQL. GORM Sharding is an application-layer library that routes queries based on a sharding key using consistent hashing. Vitess handles cross-shard queries and schema migrations natively; GORM sharding requires manual handling of cross-shard joins."),
        ("When should you choose Vitess over application-level sharding?",
         "Choose Vitess when: your application has cross-shard query requirements, you need transparent schema migrations across shards, or you're already on PlanetScale. Choose application sharding when: all queries are single-shard (by user/tenant ID), you want to avoid infrastructure complexity, and your team controls all query patterns. Vitess adds ~2ms latency per query via VTGate proxy."),
        ("How does consistent hashing work for MySQL shard routing in Go?",
         "Consistent hashing maps a shard key (e.g., `userID`) to a position on a virtual ring. Each physical shard owns a range of ring positions. Adding a new shard only remaps ~1/N of existing keys. In Go, use `github.com/serialx/hashring` or GORM's Sharding middleware. The shard key must be included in every query — never run cross-shard aggregations without Vitess."),
        ("What is the ErrMissingShardingKey error in GORM Sharding?",
         "`ErrMissingShardingKey` occurs when a query doesn't include the sharding column (e.g., `user_id`) in the WHERE clause. This prevents GORM from routing to the correct shard. Fix: always include the sharding key in all queries. For admin queries that need cross-shard scans, use a separate non-sharded replica or Vitess's scatter query. Never suppress this error — it indicates an architectural issue."),
    ],
}

def has_faq(content):
    return bool(re.search(r'(?im)^#{2,3}\s+(Frequently Asked Questions|FAQ)\b', content))

def build_faq_block(faq_list):
    """Build a properly formatted FAQ section."""
    lines = ["\n\n## Frequently Asked Questions (FAQ)\n"]
    for i, (question, answer) in enumerate(faq_list, 1):
        lines.append(f"\n### {question}\n")
        lines.append(f"{answer}\n")
    return "".join(lines)

def main():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    print(f"[INFO] Processing {len(posts)} posts for FAQ sections...")
    
    fixed = 0
    skipped = 0
    
    for filepath in posts:
        filename = os.path.basename(filepath)
        
        if filename not in POST_FAQS:
            continue
        
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        if has_faq(content):
            print(f"[SKIP]  {filename}: already has FAQ")
            skipped += 1
            continue
        
        faq_block = build_faq_block(POST_FAQS[filename])
        new_content = content.rstrip() + faq_block + "\n"
        
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)
        
        fixed += 1
        print(f"[ADDED] {filename}: {len(POST_FAQS[filename])} Q&A pairs")
    
    print(f"\n[SUMMARY] FAQ added: {fixed} | Skipped: {skipped}")

if __name__ == "__main__":
    main()
