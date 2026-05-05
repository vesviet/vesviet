---
title: "Part 2 — Handling the Surge: Event-Driven & Kafka"
date: 2026-05-05T21:00:00+07:00
draft: false
description: "How PayPay uses Kafka to buffer extreme traffic spikes during campaigns."
weight: 3
---

## The Danger of Synchronous Processing

During a massive campaign (like a sudden 50% cashback flash event), the TPS (Transactions Per Second) can jump 100x in a matter of seconds.

If the architecture is purely synchronous:
`User App -> API Gateway -> Payment Service -> Ledger Service -> Database`

A spike in traffic will instantly exhaust the database connections. The Ledger Service will time out, cascading failures back to the API Gateway, and the entire app will crash.

## The Event-Driven Buffer (Kafka)

To protect the core ledger and databases, PayPay heavily utilizes **Apache Kafka** to transition from synchronous to asynchronous processing.

### How it works:
1. **Fast Acknowledgment:** When a user initiates an action (e.g., claiming a coupon or initiating a P2P transfer), the edge service performs lightweight validation.
2. **Publish to Kafka:** The event is immediately published to a Kafka topic.
3. **Return to User:** The API returns a `202 Accepted` or `Processing` state to the user's app within milliseconds.
4. **Asynchronous Consumption:** Background workers (consumers) pull events from Kafka at a controlled rate—exactly what the downstream databases can safely handle.

### The "Shock Absorber" Effect
Kafka acts as a massive shock absorber. Even if 1 million users click "Pay" at the same second, the requests are safely queued in Kafka. The backend processes them sequentially without crashing. The user might see a loading spinner for an extra 2 seconds, but the transaction succeeds.

## Idempotency and Retries
In an event-driven system, a message might be delivered more than once (At-Least-Once delivery). PayPay must implement strict **Idempotency Keys** for every transaction. If the Payment Service consumes the same Kafka message twice, the database must recognize the Idempotency Key and ignore the duplicate request, preventing accidental double-charging.
