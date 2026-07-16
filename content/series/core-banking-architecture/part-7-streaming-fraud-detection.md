---
title: "Streaming Fraud Detection: Flink CEP, RocksDB & ML"
date: "2026-06-18T12:00:00+07:00"
lastmod: "2026-07-03T15:41:55+07:00"
draft: false
description: "Flink CEP fraud detection: 3 failed logins + high-value TX, RocksDB state, async ML inference 50-100ms SLA, 80% fewer false positives."
weight: 7
series: ["core-banking-architecture"]
keywords: ["flink fraud detection architecture", "flink rocksdb state size performance", "credit card fraud detection SLA", "streaming CEP patterns fintech"]
author: "Lê Tuấn Anh"
schema: ["Article", "TechArticle", "FAQPage"]
cover:
  image: "images/posts/banking-microservices-cover.png"
  alt: "Modern Core Banking Architecture series: Go, event sourcing, Saga pattern, and distributed ledger"
  relative: false
canonicalURL: "https://tanhdev.com/series/core-banking-architecture/part-7-streaming-fraud-detection/"
ShowToc: true
TocOpen: true
---

**Answer-first:** Real-time transaction fraud detection requires streaming processing engines (Flink/Spark) to run multi-variable rule scoring under 50ms. By maintaining stateful windows of customer activity, these systems identify anomalies and block fraudulent transfers before they settle.

> **Series (Part 7 of 8):** The final technical article before the QA handbook. We will build a real-time fraud detection pipeline with an SLA of <100ms per score — where your latency budget is shared between CEP pattern matching, state lookups, and ML model inference.

## What is a Flink Fraud Detection Architecture?

Real-time fraud detection systems rely on stream processing frameworks like Apache Flink and state backends like RocksDB to meet processing SLAs of 50-100ms. By combining Complex Event Processing (CEP) and async ML inference, these systems can reduce false positives by up to **80%** compared to legacy static rule engines, which often exhibit false positive rates of **85-99%**. When a fraud trigger blocks an account, it should integrate with the [Saga Pattern](/series/core-banking-architecture/part-4-saga-pattern/) to orchestrate the compensation flow and [FAPI 2.0 API Security](/series/core-banking-architecture/part-6-fapi-2-api-security/) to protect the fraud scoring API endpoint.

---

## Fraud Detection SLA Architecture

### Latency Budget Breakdown

Total end-to-end authorization latency for a credit card transaction: **100-300ms**

| Component | Allocated Budget | Typical Actual |
|-----------|-----------------|----------------|
| Network (client → gateway) | 10-20ms | 5-15ms |
| API Gateway routing | 5-10ms | 2-5ms |
| **Fraud scoring (Flink/ML)** | **50-100ms** | 30-80ms |
| Core Banking authorization | 10-20ms | 5-10ms |
| Network (gateway → client) | 10-20ms | 5-15ms |
| **Total** | **85-170ms** | **47-125ms** |

Source: [Redis Fraud Detection Brief](https://redis.io/solutions/fraud-detection/), Feedzai AI Report.

---

## Apache Flink: Complex Event Processing (CEP)

[Apache Flink](https://nightlies.apache.org/flink/flink-docs-stable/) provides a CEP library to detect complex event sequences in real-time streams.

### CEP Pattern: 3 Failed Logins + High-Value Transaction

Detect when a user has ≥3 failed logins within 5 minutes, **immediately followed** by a transaction >1,000,000 VND:

```java
import org.apache.flink.cep.CEP;
import org.apache.flink.cep.PatternStream;
import org.apache.flink.cep.pattern.Pattern;
import org.apache.flink.cep.pattern.conditions.SimpleCondition;
import org.apache.flink.streaming.api.windowing.time.Time;

// Event types
record Event(String userId, String type, double amount, long timestamp) {}
record AlertEvent(String userId, String reason, List<Event> matchedEvents) {}

// === CEP Pattern Definition ===
Pattern<Event, ?> fraudPattern = Pattern.<Event>begin("failed_login")
    .where(new SimpleCondition<Event>() {
        @Override
        public boolean filter(Event value) {
            return "login_failed".equals(value.type());
        }
    })
    .timesOrMore(3)        // ≥3 failed logins
    .consecutive()         // Consecutive events (no other event type in between)
    .followedByAny("high_value_transaction")  // Followed by ANY transaction
    .where(new SimpleCondition<Event>() {
        @Override
        public boolean filter(Event value) {
            return "transaction".equals(value.type())
                && value.amount() > 1_000_000.0;  // >1M VND
        }
    })
    .within(Time.minutes(5));  // Entire sequence must occur within 5 minutes

// === Apply Pattern to Stream ===
DataStream<Event> eventStream = ...; // Kafka source

PatternStream<Event> patternStream = CEP.pattern(
    eventStream.keyBy(Event::userId),  // Partition by user
    fraudPattern
);

// === Process Matches ===
DataStream<AlertEvent> alerts = patternStream.process(
    new PatternProcessFunction<Event, AlertEvent>() {
        @Override
        public void processMatch(
            Map<String, List<Event>> match,
            Context ctx,
            Collector<AlertEvent> out
        ) throws Exception {
            List<Event> failedLogins = match.get("failed_login");
            List<Event> highValueTxs = match.get("high_value_transaction");
            
            out.collect(new AlertEvent(
                failedLogins.get(0).userId(),
                "3+ failed logins followed by high-value transaction",
                Stream.concat(failedLogins.stream(), highValueTxs.stream())
                      .collect(Collectors.toList())
            ));
        }
    }
);
```

### Sliding Window: Velocity Checks

Check the number of transactions in the last hour per user:

```java
// Velocity check: >10 transactions in 1 hour for the same user
DataStream<Alert> velocityAlerts = eventStream
    .filter(e -> "transaction".equals(e.type()))
    .keyBy(Event::userId)
    .window(SlidingEventTimeWindows.of(Time.hours(1), Time.minutes(5)))
    .aggregate(new CountAggregator(), new VelocityAlertFunction())
    .filter(count -> count > 10);

// Geographic velocity: transactions from 2 locations >500km apart in <1 hour
Pattern<Event, ?> geoVelocityPattern = Pattern.<Event>begin("tx1")
    .where(e -> "transaction".equals(e.type()))
    .followedBy("tx2")
    .where(new IterativeCondition<Event>() {
        @Override
        public boolean filter(Event value, Context<Event> ctx) {
            Iterator<Event> tx1Events = ctx.getEventsForPattern("tx1").iterator();
            if (tx1Events.hasNext()) {
                Event tx1 = tx1Events.next();
                double distance = haversineDistance(tx1.location(), value.location());
                return distance > 500_000; // 500km in meters
            }
            return false;
        }
    })
    .within(Time.hours(1));
```

---

## Async ML Inference: Maintaining the 50ms SLA

Traditional synchronous ML inference calls block the processing thread and destroy throughput. Flink's `AsyncDataStream` solves this:

```java
// Async ML inference — does not block the main stream
DataStream<ScoredTransaction> scoredStream = AsyncDataStream.unorderedWait(
    txStream,
    new AsyncMLInferenceFunction(),
    100,              // Timeout: 100ms — SLA hard limit
    TimeUnit.MILLISECONDS,
    1000              // Max 1000 concurrent async requests
);

// ML Inference Function
class AsyncMLInferenceFunction
    extends RichAsyncFunction<Event, ScoredTransaction> {
    
    private OkHttpClient httpClient;  // Non-blocking HTTP client
    
    @Override
    public void open(Configuration parameters) {
        httpClient = new OkHttpClient.Builder()
            .connectTimeout(20, TimeUnit.MILLISECONDS)
            .readTimeout(80, TimeUnit.MILLISECONDS)
            .build();
    }
    
    @Override
    public void asyncInvoke(Event input, ResultFuture<ScoredTransaction> resultFuture) {
        // Fire async HTTP request to TensorFlow Serving
        Request request = new Request.Builder()
            .url("http://ml-serving:8501/v1/models/fraud_model:predict")
            .post(buildFeatureVector(input))
            .build();
        
        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                // Timeout or ML service down → default score (do not block transaction)
                resultFuture.complete(Collections.singletonList(
                    new ScoredTransaction(input, 0.5, "ml_timeout")
                ));
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                double score = parseFraudScore(response.body().string());
                resultFuture.complete(Collections.singletonList(
                    new ScoredTransaction(input, score, "ml_success")
                ));
            }
        });
    }
}
```

**Scoring decision logic:**

```java
// Combine CEP rule alerts + ML score → final decision
DataStream<FraudDecision> finalDecision = scoredStream
    .connect(alerts.broadcast(rulesDescriptor))
    .process(new RuleAndMLCombiner());

class RuleAndMLCombiner extends BroadcastProcessFunction<ScoredTransaction, Alert, FraudDecision> {
    @Override
    public void processElement(ScoredTransaction tx, ReadOnlyContext ctx, Collector<FraudDecision> out) {
        FraudDecision decision;
        
        if (tx.mlScore() > 0.95) {
            // High confidence fraud → auto-block
            decision = FraudDecision.block(tx, "ml_high_confidence");
        } else if (tx.mlScore() > 0.75) {
            // Medium confidence → step-up authentication (OTP required)
            decision = FraudDecision.stepUp(tx, "ml_medium_confidence");
        } else {
            // Low risk → approve
            decision = FraudDecision.approve(tx);
        }
        
        out.collect(decision);
    }
}
```

---

## RocksDB State Backend: Production Configuration

[Apache Flink Docs](https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/state_backends/) — RocksDB allows state to exceed RAM (spill to SSD):

```yaml
# flink-conf.yaml — Production RocksDB configuration

# === State Backend ===
state.backend: rocksdb
state.backend.rocksdb.localdir: /mnt/nvme-ssd/flink-state  # NVMe local SSD
state.backend.incremental: true                              # Incremental checkpoints

# === Memory Tuning ===
# Block cache: 2GB — keep hot user profiles in memory
state.backend.rocksdb.block.cache-size: 2147483648  # 2 GB

# Block size: 64KB — optimize for sequential fraud profile reads
state.backend.rocksdb.block.blocksize: 65536        # 64 KB
```

---

## Flink State: User Profile Schema

```java
// User fraud profile stored in Flink RocksDB state
public class UserFraudProfile implements Serializable {
    public String userId;
    
    // Velocity counters
    public int txLast1h;          // Transactions in last hour
    public int txLast24h;         // Transactions in last 24 hours
    public double totalAmountLast1h;
    
    // Failed auth tracking
    public int failedLoginLast5m; // Failed logins in last 5 minutes
    public long lastFailedLoginTs;
    
    // Geographic data
    public String lastLocation;   // "10.8231,106.6297" (lat,lng)
    public long lastTxTimestamp;
    
    // Device fingerprint
    public String lastDeviceHash;
    public int newDeviceCountLast7d;
    
    // Risk scores history
    public double avgRiskScore30d;
    public boolean isHighRiskUser;
}
```

---

## ML vs Rules Engine: False Positive Analysis

Source: [Feedzai AI Report](https://feedzai.com/resource/ai-and-ml-in-fraud-prevention/)

| Approach | False Positive Rate | False Negative Rate | Latency |
|----------|--------------------|--------------------|---------|
| **Static Rules Engine** | **85-99%** | 15-30% | <5ms |
| **Hybrid (Rules + ML)** | **20-45%** | 5-15% | 30-80ms |
| **Pure ML** | **10-25%** | 3-8% | 50-100ms |

**Business Impact of False Positives:**
- Every false positive = blocked legitimate transaction = revenue loss + customer friction
- For a bank with 1M transactions/day, a 1% false positive rate = **10,000 blocked good transactions/day**
- ML reduces false positives by 80% → dropping from 10,000 to **2,000 blocked good transactions/day**

---

## Feature Engineering for Fraud ML Model

```python
# Feature extraction for training data
def extract_features(transaction: Transaction, user_history: UserHistory) -> dict:
    return {
        # Amount features
        "amount_usd": transaction.amount / 23000,  # Normalize to USD
        "amount_zscore": (transaction.amount - user_history.avg_amount) / user_history.std_amount,
        
        # Velocity features
        "tx_count_1h": user_history.tx_count_1h,
        "tx_count_24h": user_history.tx_count_24h,
        "amount_sum_1h": user_history.amount_sum_1h,
        
        # Behavioral features
        "hour_of_day": transaction.timestamp.hour,
        "is_weekend": transaction.timestamp.weekday() >= 5,
        "days_since_account_open": user_history.account_age_days,
        
        # Geographic features
        "distance_from_last_tx_km": haversine_distance(
            transaction.location, user_history.last_tx_location
        ),
        "is_new_country": transaction.country != user_history.home_country,
        
        # Device features
        "is_new_device": transaction.device_hash not in user_history.known_devices,
        "new_device_count_7d": user_history.new_device_count_7d,
        
        # Auth features
        "failed_auth_count_5m": user_history.failed_auth_5m,
    }
```

---

## QA & SDET Testing Strategy

### Test 1: Flink Operator State Testing (TestHarness)

```java
import org.apache.flink.streaming.util.KeyedOneInputStreamOperatorTestHarness;

@Test
public void testFraudDetectorOperator() throws Exception {
    // Setup test harness — no real Kafka/Flink cluster needed
    KeyedOneInputStreamOperatorTestHarness<String, Event, AlertEvent> testHarness =
        new KeyedOneInputStreamOperatorTestHarness<>(
            new FraudDetectorOperator(),
            Event::userId,
            Types.STRING
        );
    
    testHarness.open();
    
    long baseTime = System.currentTimeMillis();
    
    // Inject 3 failed logins
    for (int i = 0; i < 3; i++) {
        testHarness.processElement(
            new Event("user-001", "login_failed", 0.0, baseTime + i * 1000),
            baseTime + i * 1000
        );
    }
    
    // Inject high-value transaction WITHIN 5 minutes
    testHarness.processElement(
        new Event("user-001", "transaction", 5_000_000.0, baseTime + 120_000),
        baseTime + 120_000
    );
    
    // Advance watermark to trigger timer
    testHarness.processWatermark(baseTime + 300_001);
    
    // Verify alert was generated
    List<StreamRecord<AlertEvent>> output = testHarness.extractOutputStreamRecords();
    assertEquals(1, output.size(), "Must generate 1 fraud alert");
    assertEquals("user-001", output.get(0).getValue().userId());
    
    testHarness.close();
}
```

### Test 2: MiniCluster Integration Test

```java
@Test
public void testFraudPipelineEndToEnd() throws Exception {
    // Embedded Flink cluster — no external dependencies
    MiniClusterWithClientResource flinkCluster = new MiniClusterWithClientResource(
        new MiniClusterResourceConfiguration.Builder()
            .setNumberSlotsPerTaskManager(4)
            .setNumberTaskManagers(1)
            .build()
    );
    flinkCluster.before();
    
    // Run full pipeline with test data
    StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
    env.enableCheckpointing(1000); // 1 second checkpoints
    
    List<Event> testEvents = generateFraudScenario("user-001");
    DataStream<Event> source = env.fromCollection(testEvents);
    
    // Connect full pipeline
    DataStream<FraudDecision> results = buildFraudPipeline(source);
    
    // Collect and verify
    List<FraudDecision> collected = results.executeAndCollect();
    
    assertTrue(collected.stream().anyMatch(d -> d.action() == BLOCK),
        "Fraud scenario must trigger a BLOCK decision");
    
    flinkCluster.after();
}
```

### Test 3: Latency SLA Validation

```go
func TestFraudScoringLatencySLA(t *testing.T) {
    const (
        targetP50  = 50 * time.Millisecond
        targetP99  = 100 * time.Millisecond
        sampleSize = 10000
    )
    
    var latencies []time.Duration
    
    for i := 0; i < sampleSize; i++ {
        start := time.Now()
        _ = fraudScoringService.Score(generateTestTransaction())
        latencies = append(latencies, time.Since(start))
    }
    
    sort.Slice(latencies, func(i, j int) bool {
        return latencies[i] < latencies[j]
    })
    
    p50 := latencies[len(latencies)*50/100]
    p99 := latencies[len(latencies)*99/100]
    
    assert.LessOrEqual(t, p50, targetP50, "P50 must be < 50ms")
    assert.LessOrEqual(t, p99, targetP99, "P99 must be < 100ms")
}
```

---

### State Size Tuning and Checkpoint Latency Optimization in Flink for RocksDB State Backend

In a real-time streaming fraud detection system, Apache Flink maintains stateful profiles for millions of bank accounts (e.g., historical transaction counts, login locations, and average spending amounts). Storing these massive states in-memory is impractical. The system utilizes the RocksDB state backend, which stores state on local SSDs and caches hot records in memory.

However, RocksDB can introduce latency spikes during checkpoint operations and state updates. To maintain a P99 latency under 100ms, the following tuning parameters are applied:
1. **Incremental Checkpointing:** Flink is configured to use incremental checkpoints (state.backend.incremental: true). Instead of writing the entire state to remote storage (e.g., S3), Flink only uploads the diff files generated by RocksDB, reducing checkpoint I/O overhead.
2. **RocksDB Block Cache Size Tuning:** The RocksDB block cache size (state.backend.rocksdb.block.cache-size) is increased to allocate 40% of the container's memory to the cache. This ensures that fraud-profile lookups for active users are served from RAM, avoiding disk read latencies.
3. **Write Buffer Configuration:** The write buffer size is optimized to prevent write stalls. RocksDB writes data to in-memory memtables first. Tuning state.backend.rocksdb.write-buffer-size and increasing the number of write buffers prevents RocksDB from blocking active event processing during high-volume transaction spikes.

### State TTL and Historical Data Retention Policies

Unchecked state growth in RocksDB leads to disk space exhaustion and degrades recovery times during failovers. To prevent this, Flink state definitions enforce strict State Time-To-Live (TTL) configurations:
- **Query-Based TTL Renewal:** Flink's StateTtlConfig is configured to expire state after 30 days of inactivity. This automatically cleans up stale profiles of inactive users.
- **Background Cleanup:** Flink cleans up expired state in the background using RocksDB compaction filters. When compaction runs, expired state records are permanently deleted from disk, keeping database file sizes optimized.

### JVM Heap and Off-Heap Memory Distribution

Because RocksDB runs as an off-heap process, allocating Flink memory requires balancing JVM heap and off-heap memory. If too much memory is allocated to the JVM heap, RocksDB will experience out-of-memory (OOM) kills by the container manager. If too little is allocated to the heap, Flink will trigger frequent garbage collection pauses, blocking the stream processing loops.
- **Heap Allocation:** Allocate 40% of container RAM to the JVM heap. This is used for Flink operators, serialization buffers, and general execution logic.
- **Managed Memory (Off-Heap):** Allocate 45% of container RAM to Flink's managed memory pool, which RocksDB uses for block caches, write buffers, and index blocks.
- **Overhead and Metaspace:** Reserve 15% for system overhead and JVM Metaspace.

### Flink Backpressure and Flow Control Optimizations

Under high volume spikes (such as during Black Friday shopping events), downstream fraud verification databases can become overwhelmed, leading to backpressure. Flink handles backpressure using credit-based flow control at the network layer. If a TaskManager's input buffers become full, it stops sending credits to the upstream TaskManager, pausing the upstream sender. This prevents memory overflow and ensures that fraud events are not lost, keeping transaction pipelines reliable under extreme loads.

## FAQ

{{< faq q="RocksDB vs HashMapStateBackend — when to use which?" >}}
- **HashMapStateBackend**: State is in the JVM heap. Faster (~2-5x), but limited by JVM heap size. Suitable when state size is <10GB.
- **RocksDB**: State is on local SSD. Slower but scales to **terabytes**. Suitable for fraud profiles of millions of users.
{{< /faq >}}

{{< faq q="Are Exactly-Once semantics important for fraud detection?" >}}
Yes. With a Kafka → Flink → Kafka pipeline and `EXACTLY_ONCE` mode, each fraud alert is emitted exactly once, even in the event of checkpoint failures and task restarts. Lacking exactly-once semantics can lead to duplicate alerts → duplicate account freezes → customer complaints.
{{< /faq >}}

{{< faq q="How do I tune Flink to achieve <100ms P99?" >}}
1. Increase `state.backend.rocksdb.block.cache-size` to keep hot data in memory.
2. Use **unordered** async I/O (`unorderedWait`) — do not wait for ML responses sequentially.
3. Place Flink TaskManagers network-close to the ML serving nodes.
4. Enable `state.backend.rocksdb.use-direct-io-for-flush-and-compaction: true`.
5. Reduce checkpoint interval if not strictly necessary (every checkpoint has an I/O overhead).
{{< /faq >}}

## Stateful Streaming Windows and gRPC ML Server Latency Optimizations

Real-time fraud detection requires processing streaming transactions instantly. Streaming engines deploy stateful event processing to evaluate risk models under 50ms.

### Stateful Stream Processing in Flink

Flink streams transactions into partitioned memory blocks, tracking customer behavior over time windows:
- **Sliding Event-Time Windows:** The engine evaluates activity over sliding windows (e.g., counting transactions in the last 10 minutes).
- **Watermarking:** Watermarks handle late-arriving events, ensuring the engine processes out-of-order telemetry before finalizing window calculations.
- **Managed Memory State:** Flink stores session states in distributed key-value backends (like RocksDB), enabling fast read/write updates during stream execution.

### gRPC Machine Learning Server Optimizations

To evaluate risk models without delaying transactions, systems run machine learning models on dedicated gRPC servers:
- **gRPC Protocols:** Communication leverages HTTP/2-based gRPC, reducing connection handshaking latency.
- **Concurrent Batching:** The ML server groups incoming transactions into batches, running GPU evaluations concurrently to optimize throughput.
- **Local Rules Engine Fallback:** If the ML server latency exceeds 30ms, the system falls back to a local rules engine (e.g., verifying limits and IP checks) to prevent transaction delays.
---

*Up Next: [Part 8 — QA & SDET Handbook](/series/core-banking-architecture/part-8-qa-sdet-handbook/) — A comprehensive testing strategy for distributed financial systems: split-brain, clock skew, double-submit, and chaos engineering.*

{{< author-cta >}}
