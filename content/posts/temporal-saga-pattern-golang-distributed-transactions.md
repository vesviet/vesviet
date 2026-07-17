---
title: "Orchestrated Saga Pattern with Temporal: Building Durable Distributed Transactions in Go"
slug: "temporal-saga-pattern-golang-distributed-transactions"
author: "Lê Tuấn Anh"
date: "2026-07-17T16:00:00+07:00"
lastmod: "2026-07-17T16:00:00+07:00"
draft: false
categories:
  - "Architecture"
  - "Fintech"
  - "Golang"
tags:
  - "Temporal"
  - "Saga Pattern"
  - "Distributed Transactions"
  - "Microservices"
description: "A Golang developer's guide to implementing the Orchestrated Saga Pattern using the Temporal Go SDK. Build durable banking transactions with automated, idempotent compensation."
ShowToc: true
TocOpen: true
---

## The Pain of Distributed Transactions in Core Banking

In a traditional monolithic architecture, ensuring the ACID (Atomicity, Consistency, Isolation, Durability) properties of a financial transaction is remarkably straightforward. You simply open a Database Transaction, execute multiple SQL statements (debit account A, credit account B, insert an audit log), and finally issue a `COMMIT`. If any step fails, you issue a `ROLLBACK`, and the database engine magically reverts everything to its pristine state.

However, the landscape changes drastically when the system is decoupled into a Microservices architecture. In a modern Core Banking system, where Ledger, CASA (Current Account Savings Account), and Payment Gateway are independent services with their own isolated databases, a single money transfer operation must traverse multiple network boundaries. 

Legacy solutions to this problem are notoriously flawed:
-   **Two-Phase Commit (2PC):** Introduces massive bottlenecks due to its synchronous locking mechanism. If the coordinator or any participating service hangs, the entire system locks up, making it highly prone to crashing under heavy load.
-   **Distributed Locks (Redis/ZooKeeper):** Extremely hard to manage correctly. Dealing with clock drifts, lock expirations, and deadlocks in a distributed environment usually leads to corrupted financial data.

This is where the **Saga Pattern** shines as the industry standard. A Saga breaks down a large distributed transaction into a series of local database transactions. If one local transaction fails, the Saga executes a series of compensating transactions to undo the changes made by the preceding successful steps. 

Compared to a Choreographed Saga (which relies on Event-Driven mechanisms like Kafka/RabbitMQ and is notoriously hard to trace or debug), an **Orchestrated Saga** (centralized coordination) is the perfect choice for banking. It provides a single point of truth for the transaction's state. [Read more about Banking Microservices Architecture](/posts/banking-microservices-architecture/).

## Temporal: Materializing the Concept of Durable Execution

Temporal is a revolutionary Durable Execution platform. It abstracts away the complexities of distributed system failures, allowing you to write your orchestration code as if the server executing it could never fail.

### The Event Sourcing Replay Mechanism

Unlike traditional orchestration engines, Temporal does not snapshot and store the internal state variables of your application in a database after every single line of code. Instead, it employs an Event Sourcing model, recording historical events (Workflow History Events) such as `ActivityTaskScheduled` or `ActivityTaskCompleted`.

When a Worker node executing your code crashes (perhaps due to an Out-Of-Memory kill, hardware failure, or network partition), the Temporal Server detects the failure and immediately re-assigns that Workflow to a new, healthy Worker. 

This new Worker downloads the event history and Replays the code from the very beginning. When the execution reaches an `ExecuteActivity` call that previously succeeded, the Temporal SDK intercepts the call. Instead of invoking the downstream service again, it immediately returns the result recorded in the history. This deterministic replay continues until the Worker's state perfectly matches the moment the previous Worker died, allowing it to resume execution seamlessly.

### The Strict Determinism Constraint

Because state recovery relies entirely on replaying code, Temporal strictly enforces that your Workflow code must be **deterministic**. This means that given the identical input history, the code branch must execute exactly the same way every single time. If it doesn't, the Temporal SDK will throw a `NonDeterministicWorkflowPolicy` error and freeze the workflow to prevent financial corruption.

Common determinism violations in Go include:
-   Using the native `time.Now()`. When replayed tomorrow, it yields a different time. You must use `workflow.Now(ctx)`.
-   Using the standard `math/rand` library. You must use the SDK's internal Random functions.
-   Making HTTP API calls, reading from disk, or querying a Database directly within the Workflow function. All side-effects must be strictly encapsulated inside `Activities`.
-   Iterating over a Go `map` (`for k, v := range myMap`), because Go randomizes map iteration order. You must convert maps to slices and sort them before iterating.

## Implementing the Saga Pattern with the Temporal Go SDK

### Building the Compensation Stack (LIFO)

In a Saga, the order of compensation is critical. If Step 2 fails, you must invoke the compensation function of Step 1 to revert the system to its initial state. If Step 3 fails, you must compensate Step 2, and then Step 1. The most optimal and idiomatic pattern in Go is to use a slice of compensation functions acting as a stack (Last-In-First-Out - LIFO).

Every time an Activity executes successfully, you `append` its corresponding rollback (compensation) function to the stack. If a global error occurs during the Saga execution, you iterate backward through the stack from end to start to Undo the operations in reverse order.

### The Crucial Use of `workflow.NewDisconnectedContext`

This is a **classic, catastrophic pitfall** for many engineers learning Temporal. When a Workflow times out or is cancelled externally by a user, the root Context (`ctx`) transitions to a Cancelled state (`ctx.Err() != nil`). 

If you blindly pass this cancelled context into your compensation Activities, the Temporal SDK will immediately block the Activity execution. It assumes that since the parent context is dead, it shouldn't execute new network calls. The result? Your compensation activities never run, leaving your financial data un-rollbacked and permanently inconsistent.

The solution is to create a Disconnected Context. This context inherits all the necessary metadata and tracing information from the parent context, but it explicitly strips away the cancellation state:

```go
// CRITICAL FIX: Create a disconnected context to execute compensations safely
disconnectedCtx, _ := workflow.NewDisconnectedContext(ctx)
```

Below is a highly robust Proof-of-Concept (PoC) demonstrating an Interbank Transfer Saga in Go:

```go
func InterbankTransferWorkflow(ctx workflow.Context, input TransferInput) (err error) {
	logger := workflow.GetLogger(ctx)
	acts := &AccountActivity{}
	var compensations []func(workflow.Context) error

	// The defer block guarantees LIFO compensation execution upon any failure
	defer func() {
		if err != nil {
			logger.Warn("Saga failed. Executing compensations...", "tx_id", input.TransactionID)
			
			// 1. Create the disconnected context to bypass cancellation
			disconnectedCtx, _ := workflow.NewDisconnectedContext(ctx)
			
			// 2. Configure dedicated Retry and Timeout policies for rollbacks
			// Compensations must be highly resilient and retry aggressively
			disconnectedCtx = workflow.WithActivityOptions(disconnectedCtx, compensationActivityOptions)
			
			// 3. Iterate backwards through the compensation stack (LIFO)
			for i := len(compensations) - 1; i >= 0; i-- {
				compErr := compensations[i](disconnectedCtx)
				if compErr != nil {
					logger.Error("Catastrophic compensation failure! Requires manual intervention", "error", compErr)
				}
			}
		}
	}()

	// Step 1: Debit source account
	ctx1 := workflow.WithActivityOptions(ctx, standardActivityOptions)
	err = workflow.ExecuteActivity(ctx1, acts.DebitSourceAccount, input).Get(ctx1, nil)
	if err != nil { return fmt.Errorf("debit failed: %w", err) }
	
	// Register compensation for Step 1
	compensations = append(compensations, func(cCtx workflow.Context) error {
		return workflow.ExecuteActivity(cCtx, acts.CompensateDebit, input).Get(cCtx, nil)
	})

	// Step 2: Call external Payment Gateway (e.g., SWIFT or NAPAS)
	// Simulating a network failure here will trigger the Step 1 rollback
	ctx2 := workflow.WithActivityOptions(ctx, standardActivityOptions)
	err = workflow.ExecuteActivity(ctx2, acts.ExecuteGatewayTransfer, input).Get(ctx2, nil)
	if err != nil { return fmt.Errorf("gateway failed: %w", err) }

	// Register compensation for Step 2
	compensations = append(compensations, func(cCtx workflow.Context) error {
		return workflow.ExecuteActivity(cCtx, acts.CompensateGatewayTransfer, input).Get(cCtx, nil)
	})

	// Step 3: Credit target account
	ctx3 := workflow.WithActivityOptions(ctx, standardActivityOptions)
	err = workflow.ExecuteActivity(ctx3, acts.CreditTargetAccount, input).Get(ctx3, nil)
	if err != nil { return fmt.Errorf("credit failed: %w", err) }

	logger.Info("Interbank Money Transfer Saga completed successfully")
	return nil
}
```

## Designing Idempotency for Compensation Activities

In a distributed, cloud-native system, network partitions and micro-outages are guaranteed. A compensation Activity (`CompensateDebit`) might successfully refund the money in the database, but the HTTP response might be dropped by a load balancer before reaching the Temporal Worker.

The Temporal Worker, assuming the Activity failed, will retry it according to its RetryPolicy. Without strict **Idempotency** guarantees, the customer's account could be erroneously refunded 2 or 3 times for a single failed transaction. 

### Transaction-level Idempotency Keys

To solve this, you must generate a unique Idempotency Key. While you can pass a UUID from the client, a highly reliable approach is to extract `workflow.GetInfo(ctx).WorkflowExecution.ID` as the Idempotency Key, passing it down to the Microservice's Database layer.

In the downstream Microservice's relational Database (like PostgreSQL), you must create a `transaction_events` or `idempotency_logs` table with the `idempotency_key` column constrained as strictly `UNIQUE`.

### Using Unique Constraints and the Outbox Pattern

When the downstream service receives a debit, credit, or compensation request, it must execute the following protocol:

1.  **Open a Database Transaction**.
2.  `INSERT` the idempotency key into the `transaction_events` table.
3.  Catch any `Duplicate Key` exceptions. If the key already exists, it means this request was already processed. The service should immediately return an idempotent success response (HTTP 200 OK) without modifying the account balance again.
4.  If the insertion is successful, proceed to `UPDATE` the actual account balance.
5.  **COMMIT** the database transaction.

If your microservice also needs to emit events (e.g., to Kafka) after a successful transaction, never execute the Kafka publish call directly inside the database transaction (which causes dual-write anomalies). Instead, use the **Transactional Outbox Pattern**, writing the event to an `outbox` table in the same transaction, and using a tool like Debezium to stream it to Kafka.

## Testing and Versioning Workflows

### Writing Unit Tests with TestWorkflowEnvironment
One of the greatest advantages of the Temporal Go SDK is its built-in testing framework. You do not need to spin up a real Temporal Server to test your orchestrations. The `testsuite.TestWorkflowEnvironment` allows you to mock Activities and simulate time passing instantaneously.

For example, if you have an Activity that is supposed to sleep for 30 days before charging a subscription fee, using the test environment will execute the 30-day sleep in a few milliseconds during your CI pipeline, ensuring your business logic is robust without delaying your builds.

### Handling Versioning Safely
Because of the Determinism constraint, you cannot simply deploy a new version of your code if it changes the execution sequence of currently running Workflows. If you add a new Activity call into the middle of a Workflow, older executions that are replaying will crash with a `NonDeterministicWorkflowPolicy` error.

To safely roll out changes, you must use the Temporal Versioning API (e.g., `workflow.GetVersion(ctx, "Add Fraud Check", workflow.DefaultVersion, 1)`). This instructs the replayer to execute the old code path for historical workflows, and only execute the new "Fraud Check" path for newly initiated workflows. Once all old workflows have finished executing, you can safely remove the versioning branching logic in the next code deployment.

[Explore more about money transfer flows in Composable Banking Architectures](/posts/composable-banking-architecture/) and how [Temporal compares to the Dapr Workflow SDK for Saga Orchestration](/posts/dapr-workflow-saga-orchestration-guide/).
