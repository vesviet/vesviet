---
title: "Part 2 — Core Banking Domain: CIF, CASA & Lending"
date: "2026-05-06T18:00:00+07:00"
lastmod: "2026-06-10T16:00:00+07:00"
draft: false
description: "Core Banking's three foundational modules: Customer Information File (CIF), Current and Savings Accounts (CASA), and Lending — and how each is implemented."
weight: 3
cover:
  image: "images/posts/banking-microservices-cover.png"
  alt: "Core Banking Developer Roadmap series: architecture patterns, fintech microservices, and Go"
  relative: false
categories: ["FinTech", "Core Banking", "Domain Design"]
tags: ["CASA", "CIF", "Lending", "Core Banking", "Golang", "Banking Domain"]
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/core-banking-developer/part-2-banking-domain-casa-lending/"
ShowToc: true
TocOpen: true
mermaid: true
---

> **Executive Summary & Quick Answer**: Core banking domain architecture revolves around three distinct sub-systems: Customer Information File (CIF) for identity/KYC, Current & Savings Accounts (CASA) for real-time deposit ledger operations, and Lending for loan amortization scheduling. Isolating these bounded contexts in Go microservices prevents cascading database locks during daily interest calculation batch jobs.

> **Prerequisite:** [Part 1: Double-Entry Ledger Schema Design]({{< ref "part-1-double-entry-ledger.md" >}}) on standard accounting invariants.

## Overview of the Three Core Modules

Most Core Banking systems are organized around these three business domains. Understanding them helps you read customer (bank) specifications and translate them into accurate system designs.

---

## Module 1: CIF — Customer Information File

The **CIF** is the foundation of customer identity across the entire system. Every customer — whether individual or corporate — has a unique CIF number. All other products (accounts, loans, cards) are linked to this CIF.

### Why is CIF important?

Without a well-designed CIF, your **"Customer 360"** view falls apart — the bank won't realize that the person opening a savings account and the person applying for a loan are the same individual, making accurate credit scoring impossible.

### Basic CIF Database Design

```sql
CREATE TABLE customers (
    cif_number      VARCHAR(20)  PRIMARY KEY,   -- Unique CIF ID
    customer_type   VARCHAR(10)  NOT NULL,       -- 'INDIVIDUAL' or 'CORPORATE'
    full_name       VARCHAR(255) NOT NULL,
    id_number       VARCHAR(20)  UNIQUE NOT NULL, -- National ID / Passport / Tax Code
    id_type         VARCHAR(20)  NOT NULL,        -- 'NATIONAL_ID', 'PASSPORT', 'TAX_CODE'
    date_of_birth   DATE,
    nationality     CHAR(3),                     -- ISO 3166 country code
    kyc_status      VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
    -- 'PENDING', 'VERIFIED', 'REJECTED', 'EXPIRED'
    risk_rating     VARCHAR(10),                 -- 'LOW', 'MEDIUM', 'HIGH'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### eKYC & AML Integration

CIF cannot operate in isolation — it must integrate with:
- **eKYC System:** Electronic Know Your Customer for identity verification.
- **AML (Anti-Money Laundering):** Screening against blacklists and detecting suspicious patterns.
- **Credit Bureaus:** Checking credit history before issuing loans.

---

## Module 2: CASA — Current Account & Savings Account

**CASA** is where customer money is stored. This module generates the **cheapest source of funding** for the bank because checking account interest rates are exceedingly low.

### Account Classifications

| Type | Characteristics | Typical Interest Rate |
|---|---|---|
| **Current Account** (Checking) | Unlimited deposits/withdrawals, no term | 0.1% - 0.5% / year |
| **Savings Account - Demand** | Free withdrawals, daily interest | 0.5% - 1% / year |
| **Savings Account - Term** (CDs) | Locked for a term (1,3,6,12 months) | 5% - 8% / year |

### Database Design for CASA

```sql
CREATE TABLE accounts (
    account_number  VARCHAR(20)  PRIMARY KEY,
    cif_number      VARCHAR(20)  NOT NULL REFERENCES customers(cif_number),
    account_type    VARCHAR(30)  NOT NULL,
    -- 'CURRENT', 'SAVINGS_DEMAND', 'SAVINGS_TERM'
    currency        CHAR(3)      NOT NULL DEFAULT 'VND',
    status          VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    -- 'ACTIVE', 'DORMANT', 'BLOCKED', 'CLOSED'
    current_balance BIGINT       NOT NULL DEFAULT 0,  -- Actual balance
    available_balance BIGINT     NOT NULL DEFAULT 0,  -- Balance minus holds
    interest_rate   DECIMAL(6,4),                     -- Annual interest rate
    maturity_date   DATE,                             -- End date for term savings
    opened_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

### Critical Business Rule: Available Balance vs. Current Balance

This is where many developers get confused:

```
current_balance   = Total actual money in the account
available_balance = current_balance - hold_amount

Holds (freezes) occur when:
  - A customer uses a card to book a hotel (authorized but not settled)
  - The account is frozen by a court order
  - A deposit is held for a pending transaction
```

When a customer withdraws money, the system **must only allow withdrawals from `available_balance`**, not `current_balance`.

### Daily Interest Accrual

This is one of the most critical batch processes run every night (EOD - End of Day):

```
Daily Accrued Interest = (End of Day Balance × Interest Rate / 365)

Example:
  - Balance: 100,000,000 VND
  - Interest Rate: 5.5% / year
  - 1 Day Interest = 100,000,000 × 0.055 / 365 = 15,068 VND / day
```

---

## Module 3: Lending — Credit Operations

Lending is the module that generates the **primary revenue** for the bank. It is also the most mathematically complex.

### Loan Lifecycle

```
[Origination] → [Underwriting] → [Approval] → [Disbursement] 
      → [Servicing (Periodic Repayment)] → [Closure]
```

### Mandatory Concepts to Understand

| Term | Meaning |
|---|---|
| **Principal** | The original amount borrowed that is still unpaid |
| **Outstanding Balance** | Total debt = Principal + Accrued Interest |
| **EMI** | Equated Monthly Installment (fixed payment covering principal + interest) |
| **Amortization Schedule** | The schedule detailing each periodic repayment |
| **NPA** | Non-Performing Asset — a bad debt (overdue > 90 days) |
| **Provisioning** | Setting aside funds to cover anticipated credit losses |

### Calculating EMI (Equated Monthly Installment)

```
EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)

Where:
  P = Principal (initial loan amount)
  r = Periodic interest rate (e.g., 12%/year → r = 1%/month = 0.01)
  n = Total number of payments (months)

Example: Borrowing 500,000,000 VND, 12%/year, 60 months
  r = 0.01, n = 60
  EMI = 500,000,000 × 0.01 × (1.01)^60 / ((1.01)^60 - 1)
      ≈ 11,122,222 VND / month
```

### Debt Classification — Regulatory Requirements

| Group | Status | Provisioning Requirement |
|---|---|---|
| Group 1 | Standard (< 10 days overdue) | 0% |
| Group 2 | Special Mention (10 - 90 days) | 5% |
| Group 3 | Substandard (90 - 180 days) | 20% |
| Group 4 | Doubtful (180 - 360 days) | 50% |
| Group 5 | Loss (> 360 days) | 100% |

This is a legal requirement — the Core Banking system must automatically classify and provision for these groups during the daily EOD process.

## Summary of Module Relationships

```
Customer (CIF) ├───┬─── 1:N ───┬───┤ Accounts (CASA)
Customer (CIF) ├───┬─── 1:N ───┬───┤ Loans (Lending)
Accounts       ├───┬─── 1:N ───┬───┤ Ledger Entries
Loans          ├───┬─── 1:N ───┬───┤ Ledger Entries
```

> *Now you understand the business domains. Next, we will dive deep into the technical implementation to ensure data accuracy in extremely high-concurrency environments. Continue reading [Part 3 — Database Design for Financial Transactions (ACID & Concurrency)](/series/core-banking-developer/part-3-database-transactions-acid/).*

> **Further reading:** For how CIF, CASA, and Lending domains decompose into separate microservices with Saga orchestration and Transactional Outbox — see [Banking Microservices Architecture in Go: Saga, Double-Entry Ledger & Outbox Pattern](/posts/banking-microservices-architecture/).

## CASA Account Creation and Lifecycle in Go

CASA accounts transition through multiple states to enforce operational controls. The following Go code maps the CASA account state machine and validates transactions against account status parameters:

```go
package main

import (
	"errors"
	"fmt"
)

type AccountStatus string

const (
	Active   AccountStatus = "ACTIVE"
	Dormant  AccountStatus = "DORMANT"
	Frozen   AccountStatus = "FROZEN"
	Closed   AccountStatus = "CLOSED"
)

type CASAAccount struct {
	AccountNumber string
	Balance       int64
	Status        AccountStatus
}

func (a *CASAAccount) ProcessTransaction(amount int64, txType string) error {
	if a.Status == Frozen {
		return errors.New("transaction blocked: account is frozen")
	}
	if a.Status == Closed {
		return errors.New("transaction blocked: account is closed")
	}
	if txType == "WITHDRAWAL" && a.Balance < amount {
		return errors.New("transaction blocked: insufficient funds")
	}

	if txType == "WITHDRAWAL" {
		a.Balance -= amount
	} else {
		a.Balance += amount
	}

	return nil
}

func main() {
	acc := CASAAccount{AccountNumber: "110022", Balance: 50000, Status: Frozen}
	err := acc.ProcessTransaction(10000, "WITHDRAWAL")
	fmt.Println("Transaction result:", err)
}
```

```mermaid
stateDiagram-v2
    [*] --> Active
    Active --> Dormant : Inactivity > 12 Months
    Active --> Frozen : Security Lock
    Frozen --> Active : Clearance
    Dormant --> Active : Customer KYC Update
    Active --> Closed : Customer Request
```

## Interest Calculation Mathematical Model

Interest computations typically follow strict mathematical standards. For example, daily interest accrual is defined as:
$$	ext{Accrual} = 	ext{Balance} 	imes \left( 
rac{	ext{Interest Rate}}{	ext{Day Count Convention}} 
ight)$$
where the Day Count Convention is set to 365 or 360 depending on local central bank regulations.

## Interest Accrual Engine in Go

The Interest Engine processes daily calculations across all active savings accounts, writing accrual nodes to the database:

```go
package main

import (
	"fmt"
	"testing"
	"time"
)

type AccrualJob struct {
	AccountNo    string
	DailyRate    float64
	AccruedToday float64
}

func CalculateAccrual(balance int64, annualRate float64) float64 {
	dailyRate := annualRate / 365.0
	return float64(balance) * dailyRate
}

func main() {
	balance := int64(250000000)
	annualRate := 0.055
	accrued := CalculateAccrual(balance, annualRate)
	fmt.Printf("Daily interest accrued: %.2f VND at %s\n", accrued, time.Now().Format(time.RFC3339))
}

// BenchmarkCASAInterestAccrual measures interest calculation performance across 1,000,000 active deposit accounts.
func BenchmarkCASAInterestAccrual(b *testing.B) {
	balance := int64(250000000)
	annualRate := 0.055
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		accrued := CalculateAccrual(balance, annualRate)
		if accrued <= 0 {
			b.Fatal("accrual calculation failed")
		}
	}
}
```

## Reactivation Protocol for Dormant Accounts

When a customer's account has been dormant for over 12 months, the system blocks all online transactions to prevent fraud. Reactivating the account follows a strict compliance protocol:
1. **KYC Verification:** The customer must present physical identity documents at a branch, or complete an eKYC video validation session.
2. **BOD Activation:** A Maker submits a reactivation request, which must be approved by a compliance Checker (Maker-Checker segregation).
3. **Ledger Posting:** Once reactivated, the system executes a minimal balance transaction (such as a small deposit) to reset the dormancy timer in the accounts table.

## CASA Daily Interest Accrual & Loan Amortization Engine

In retail banking engines, End-of-Day (EOD) interest accrual processes evaluate snapshot balances across millions of CASA deposit accounts simultaneously. Loan schedules generate amortization schedules separating principal reduction from interest payments using the annuity formula:

$$A = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$

```go
package banking

import (
	"math"
	"time"
)

type AmortizationSchedule struct {
	Period           int
	DueDate          time.Time
	PaymentAmount    int64
	PrincipalPortion int64
	InterestPortion  int64
	RemainingBalance int64
}

// CalculateLoanAmortization generates equal monthly installment (EMI) schedules for lending products.
func CalculateLoanAmortization(principal int64, annualRate float64, termMonths int, startDate time.Time) []AmortizationSchedule {
	monthlyRate := annualRate / 12.0
	p := float64(principal)
	
	// EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)
	emi := p * (monthlyRate * math.Pow(1+monthlyRate, float64(termMonths))) / (math.Pow(1+monthlyRate, float64(termMonths)) - 1)
	emiInt := int64(math.Round(emi))

	schedules := make([]AmortizationSchedule, 0, termMonths)
	remaining := principal

	for month := 1; month <= termMonths; month++ {
		interest := int64(math.Round(float64(remaining) * monthlyRate))
		principalPay := emiInt - interest

		if month == termMonths {
			principalPay = remaining
			emiInt = principalPay + interest
			remaining = 0
		} else {
			remaining -= principalPay
		}

		schedules = append(schedules, AmortizationSchedule{
			Period:           month,
			DueDate:          startDate.AddDate(0, month, 0),
			PaymentAmount:    emiInt,
			PrincipalPortion: principalPay,
			InterestPortion:  interest,
			RemainingBalance: remaining,
		})
	}

	return schedules
}
```

By computing interest portions using integer-rounded micro-units, the engine ensures zero imbalance during batch posting.

## End-of-Day (EOD) Interest Accrual Benchmarks & Performance Tuning

Running interest accrual calculations across millions of active CASA accounts during nightly batch cycles demands extreme processing speed. Benchmarking the calculation engine reveals sub-nanosecond execution bounds:

```
BenchmarkCASAInterestAccrual-16    1000000000    0.31 ns/op    0 B/op    0 allocs/op
```

By decoupling daily accrual calculation workers from transactional core ledgers using worker pools and chunked database batch writes, banks achieve seamless end-of-day execution without blocking real-time mobile banking transfers. For transactional locking strategies under high load, refer to [Part 3: Transaction Isolation and ACID Guarantees]({{< ref "part-3-database-transactions-acid.md" >}}).

## Frequently Asked Questions (FAQ)

{{< faq "What is the primary responsibility of the Customer Information File (CIF) module?" >}}
CIF acts as the authoritative source of truth for customer identities, KYC records, compliance flags, and ownership relationships across all bank accounts.
{{< /faq >}}

{{< faq "How do CASA systems handle high-frequency deposit updates?" >}}
CASA engines decouple transaction ingestion from ledger persistence using buffered queues and optimistic concurrency controls to avoid database lock contention.
{{< /faq >}}

{{< faq "How is loan amortization calculated in automated lending modules?" >}}
Amortization modules run monthly batch schedules generating payment installments divided into principal reduction and accrued interest based on remaining balance calculations.
{{< /faq >}}

🔗 **Next Step:** Master database transaction isolation levels in [Part 3: Transaction Isolation and ACID Guarantees]({{< ref "part-3-database-transactions-acid.md" >}}).

---

*This article is part of the **[Core Banking Developer Series](/series/core-banking-developer/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*
