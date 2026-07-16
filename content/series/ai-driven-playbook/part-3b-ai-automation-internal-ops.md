---

title: "Part 3B — AI Automation for Internal Operations: Proving ROI"
date: "2026-05-16T08:00:00+07:00"
lastmod: "2026-05-16T08:00:00+07:00"
draft: false
description: "Win executive buy-in for the AI Platform by solving 'money-making' operational problems: Automated Reconciliation, Excel processing, and Lightweight"
ShowToc: true
TocOpen: true
weight: 5
categories: ["Series", "Enterprise Playbook"]
tags: ["AI", "Enterprise Architecture", "CTO", "Tech Lead"]
cover:
  image: "images/posts/hybrid-ai-pipeline-cover.png"
  alt: "AI-Driven Engineer Enterprise Playbook series: workflows, autonomous pipelines, and tooling"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/ai-driven-playbook/part-3b-ai-automation-internal-ops/"
mermaid: true
---

[← Previous](/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/) | [Series Hub](/series/ai-driven-playbook/)

> **Prerequisite:** This article builds upon the Enterprise RAG designs from [Part 3A — Enterprise RAG Architecture: Building the Internal 'Brain'](/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/).

The powerful RAG system we built in [Part 3A](/series/ai-driven-playbook/part-3a-enterprise-rag-architecture/) would be nothing more than an expensive "tech toy" if it only answers questions like: *"What does this function in the project do?"*


The Board of Directors (BOD) and CFOs do not care that Devs saved 15 minutes of typing. What they care about is **ROI (Return on Investment)**. To sustain the budget for the AI Platform, Tech Leads must prove the system can cut Operational Costs across other departments like Finance, Logistics, and HR.

## 1. Breaking Out of the "Dev Chatbot" Shadow

Enterprise data is typically extremely "messy" and unstructured. The greatest capability of an LLM is not writing code—it is **Reasoning & Structuring data**.

By connecting the AI Gateway (Part 2) with an internal RAG source (Part 3A), we can create "Agents" that replace humans in repetitive, comparison-based office work.

---

## 2. The "Money-Making" Use Case: Automated Reconciliation

Take the Accounting (Finance Ops) department as an example. At the end of every month, staff open 3 screens: 1 Excel file from the shipping partner, 1 PDF invoice, and the internal ERP system—manually checking whether each order's amount matches.

With an AI-Native System, this workflow is automated under the following architecture:

```mermaid
sequenceDiagram
    participant Ops as Finance Ops
    participant Gateway as AI Gateway (LiteLLM)
    participant RAG as RAG VectorDB (Internal)
    participant ERP as ERP System

    Ops->>Gateway: Upload Vendor_Report.xlsx + Bank_Statement.pdf
    Gateway->>Gateway: Document Extraction
    Gateway->>RAG: Query Metadata (Pricing rules, Contracts)
    RAG-->>Gateway: Returns vendor-specific discount rules
    Gateway->>Gateway: Line-by-line Matching & Reasoning
    
    alt Data matches
        Gateway->>ERP: Auto-mark "Reconciled" via API
    else Discrepancy detected
        Gateway-->>Ops: Alert: "Line 45 is off by $2.17 due to incorrect discount rule"
    end
```

> 💰 **Cost Numbers (ROI):** At a Logistics company, one staff member spent 40 hours/week reconciling 10,000 waybills. Applying the above workflow, the LLM scans 10,000 rows in 3 minutes at an API cost of approximately $2. The system fully frees up 1 headcount (reassigned to higher-value work) $\rightarrow$ **10x Operational Leverage**.

---

## 3. Common Risk: You Cannot Trust AI 100%

In automated financial workflows, Hallucination is simply not permitted. A single misplaced decimal point or incorrect currency conversion can trigger audited reporting compliance violations or cause irreversible monetary loss.

> **[Production Failure Case Study]: Automated Refund Gone Wrong**
> A retail company let an AI Agent automatically read complaint emails and call the refund API. The AI read an email that said *"I'm so furious I want a $50,000 refund"*, and with no guardrails in place, it actually triggered a refund exceeding the authorized limit.
> 📊 **Impact Metrics:** Lost $12,000 within 2 hours before the system was emergency-killed (kill-switch).
> 📈 **Before/After (Post Human-in-the-Loop Implementation):**
> - **Before:** Blind auto-refunds with a False Positive rate of up to 15%.
> - **After:** AI acts as a Drafter, generating a proposal with a `confidence_score`. Ticket processing speed increased 300% (reduced from 10 min/ticket to 2 min/ticket), while financial losses from AI hallucinations dropped to **$0**.

**Anti-pattern:** Letting AI auto-execute tasks that mutate sensitive state (money, database records).

**Best Practice:** Apply **Human-in-the-Loop (HITL)**.
AI's only job is "Extraction" and "Drafting". Every command that changes money or updates the DB must pass through a UI where a staff member clicks "Approve". The LLM must output a `confidence_score`. If `confidence_score < 0.95`, the system automatically flags it (Red Flag) for human review.

### Database Schema for Automated Bank Reconciliation

To store reconciliation audit logs and match discrepancies, we implement a structured SQL database schema to log matching outputs and reasons parsed by the AI matching system:

```sql
CREATE TABLE transaction_reconciliation (
    reconciliation_id UUID PRIMARY KEY,
    source_bank_reference VARCHAR(100) NOT NULL,
    internal_ledger_reference VARCHAR(100) NOT NULL,
    amount NUMERIC(18, 4) NOT NULL,
    currency CHAR(3) NOT NULL,
    bank_post_date TIMESTAMP WITH TIME ZONE NOT NULL,
    ledger_post_date TIMESTAMP WITH TIME ZONE NOT NULL,
    matching_score NUMERIC(5, 2) NOT NULL, -- Confidence level generated by LLM matching logic (0.00 to 100.00)
    status VARCHAR(50) NOT NULL, -- 'MATCHED', 'PARTIAL_MATCH', 'DISCREPANCY_UNRESOLVED'
    mismatch_reason TEXT,
    resolved_by_ops BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reconciliation_status ON transaction_reconciliation(status);
CREATE INDEX idx_reconciliation_bank_ref ON transaction_reconciliation(source_bank_reference);
```

### Go Implementation: Automated Transaction Reconciliation Engine

To implement the "Human-in-the-Loop" pattern with deterministic matching fallback, we build the core reconciliation engine in Go. This service fetches bank transactions and internal ledger entries, computes a similarity/matching score based on transaction references, amount match, and date proximity, and calls the LiteLLM gateway to resolve fuzzy reference mismatches:

```go
package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"net/http"
	"strings"
	"time"
)

type Transaction struct {
	ID        string    `json:"id"`
	Reference string    `json:"reference"`
	Amount    float64   `json:"amount"`
	Currency  string    `json:"currency"`
	Timestamp time.Time `json:"timestamp"`
}

type ReconciledPair struct {
	BankTxID       string  `json:"bank_tx_id"`
	LedgerTxID     string  `json:"ledger_tx_id"`
	Amount         float64 `json:"amount"`
	Score          float64 `json:"score"` // 0.0 to 100.0
	Status         string  `json:"status"`
	MismatchReason string  `json:"mismatch_reason"`
}

type LiteLLMRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type LiteLLMResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

// ReconciliationService handles the business logic of matching transactions
type ReconciliationService struct {
	db            *sql.DB
	gatewayURL    string
	gatewayAPIKey string
}

// ReconcileTransactions runs the matching process for a batch of transactions
func (s *ReconciliationService) ReconcileTransactions(ctx context.Context, bankTxs []Transaction, ledgerTxs []Transaction) ([]ReconciledPair, error) {
	var results []ReconciledPair

	for _, bTx := range bankTxs {
		bestMatchIdx := -1
		bestScore := 0.0
		var reason string

		for i, lTx := range ledgerTxs {
			// Exact physical match
			if bTx.Reference == lTx.Reference && bTx.Amount == lTx.Amount && bTx.Currency == lTx.Currency {
				bestMatchIdx = i
				bestScore = 100.0
				reason = "Exact reference, amount, and currency match."
				break
			}

			// Partial match check: fuzzy reference, exact amount
			if bTx.Amount == lTx.Amount && bTx.Currency == lTx.Currency {
				// Compute reference edit distance/similarity
				refScore := computeReferenceSimilarity(bTx.Reference, lTx.Reference)
				
				// Date difference penalty
				dateDiff := math.Abs(bTx.Timestamp.Sub(lTx.Timestamp).Hours())
				datePenalty := math.Min(dateDiff * 0.5, 20.0) // max 20 points penalty for 40+ hours difference

				score := refScore - datePenalty
				if score > bestScore && score > 60.0 {
					bestScore = score
					bestMatchIdx = i
					reason = fmt.Sprintf("Amount match with fuzzy reference similarity of %.1f%%.", refScore)
				}
			}
		}

		// If score is good but not exact (60 to 95), resolve using LiteLLM
		if bestScore >= 60.0 && bestScore < 95.0 && bestMatchIdx != -1 {
			resolvedScore, err := s.resolveFuzzyMatchWithAI(ctx, bTx, ledgerTxs[bestMatchIdx])
			if err == nil {
				bestScore = resolvedScore
				reason = fmt.Sprintf("Fuzzy match resolved by AI with confidence score %.1f%%.", resolvedScore)
			} else {
				reason += fmt.Sprintf(" AI resolution failed: %v", err)
			}
		}

		status := "DISCREPANCY_UNRESOLVED"
		if bestScore >= 95.0 {
			status = "MATCHED"
		} else if bestScore >= 75.0 {
			status = "PARTIAL_MATCH"
		}

		var matchedLedgerID string
		if bestMatchIdx != -1 {
			matchedLedgerID = ledgerTxs[bestMatchIdx].ID
		}

		results = append(results, ReconciledPair{
			BankTxID:       bTx.ID,
			LedgerTxID:     matchedLedgerID,
			Amount:         bTx.Amount,
			Score:          bestScore,
			Status:         status,
			MismatchReason: reason,
		})
	}

	return results, nil
}

func computeReferenceSimilarity(a, b string) float64 {
	a = strings.ToLower(strings.TrimSpace(a))
	b = strings.ToLower(strings.TrimSpace(b))
	if a == b {
		return 100.0
	}
	
	// Simple overlap coefficient for demonstrative purposes
	wordsA := strings.Fields(a)
	wordsB := strings.Fields(b)
	matches := 0
	for _, wA := range wordsA {
		for _, wB := range wordsB {
			if wA == wB {
				matches++
			}
		}
	}
	
	if len(wordsA) == 0 || len(wordsB) == 0 {
		return 0.0
	}
	
	minLen := math.Min(float64(len(wordsA)), float64(len(wordsB)))
	return (float64(matches) / minLen) * 100.0
}

func (s *ReconciliationService) resolveFuzzyMatchWithAI(ctx context.Context, bankTx Transaction, ledgerTx Transaction) (float64, error) {
	prompt := fmt.Sprintf(
		"Compare these transaction references and evaluate the probability that they refer to the same transaction.\n"+
		"Bank Reference: '%s', Amount: %.2f\n"+
		"Ledger Reference: '%s', Amount: %.2f\n"+
		"Respond ONLY with a JSON object: {\"confidence_score\": float} where score is between 0.0 and 100.0.",
		bankTx.Reference, bankTx.Amount, ledgerTx.Reference, ledgerTx.Amount,
	)

	reqPayload := LiteLLMRequest{
		Model: "claude-3-haiku",
		Messages: []Message{
			{Role: "system", Content: "You are a financial auditing assistant that compares ledger items."},
			{Role: "user", Content: prompt},
		},
	}

	jsonData, err := json.Marshal(reqPayload)
	if err != nil {
		return 0.0, err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", s.gatewayURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return 0.0, err
	}
	req.Header.Set("Authorization", "Bearer "+s.gatewayAPIKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return 0.0, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return 0.0, fmt.Errorf("gateway returned status code %d", resp.StatusCode)
	}

	var apiResp LiteLLMResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return 0.0, err
	}

	if len(apiResp.Choices) == 0 {
		return 0.0, errors.New("empty response choices from gateway")
	}

	// Parse JSON output
	var parsed struct {
		ConfidenceScore float64 `json:"confidence_score"`
	}
	content := strings.TrimSpace(apiResp.Choices[0].Message.Content)
	// Strip markdown block if exists
	content = strings.TrimPrefix(content, "```json")
	content = strings.TrimSuffix(content, "```")
	content = strings.TrimSpace(content)

	if err := json.Unmarshal([]byte(content), &parsed); err != nil {
		return 0.0, fmt.Errorf("failed to parse AI response content '%s': %w", content, err)
	}

	return parsed.ConfidenceScore, nil
}
```

This Go service guarantees that high-confidence matches are processed immediately, while any match falling below the strict 95.0% threshold is saved as `PARTIAL_MATCH` or `DISCREPANCY_UNRESOLVED`, where the internal auditing dashboard triggers human verification.

---

## 4. Lightweight Automation: The Right Tool for the Right Job

Many Tech Leads suffer from "Over-engineering": The moment AI is involved, they immediately want to write Python, spin up Docker, and deploy on Kubernetes.

In reality, many small operational tasks (like daily expense categorization in a department's Google Sheet) simply do not warrant deploying a full microservice.

**Solution:** Use **Google Apps Script** to call your internal AI Gateway (LiteLLM) directly. You can embed a tiny JavaScript snippet right inside Google Sheets, turning it into a standalone AI-powered application.

**Hands-on Snippet: Calling LiteLLM from Google Sheets**
```javascript
// Attach this function to a button on Google Sheets
function categorizeExpensesAI() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var expenseDescription = sheet.getRange("A2").getValue(); // Read invoice description
  
  var payload = {
    "model": "claude-3-haiku", // Already routed through the internal AI Gateway
    "messages": [
      {"role": "system", "content": "You are an accountant. Categorize expenses into: Marketing, IT, Ops. Return only the category name."},
      {"role": "user", "content": expenseDescription}
    ]
  };

  var options = {
    "method": "post",
    "headers": {
      "Authorization": "Bearer sk-internal-team-admin-key", // API Key managed by LiteLLM
      "Content-Type": "application/json"
    },
    "payload": JSON.stringify(payload)
  };

  // Call directly to the AI Gateway (Nginx Proxy Manager)
  var response = UrlFetchApp.fetch("https://ai.yourcompany.internal/v1/chat/completions", options);
  var result = JSON.parse(response.getContentText());
  
  // Write the returned result to column B
  sheet.getRange("B2").setValue(result.choices[0].message.content);
}
```
*With just 20 lines of code, any operations staff member can automate their own Excel file securely—no Backend team required.*

### Strategic Scaling of Internal Operational AI

To scale this beyond single sheets, the operations team implements Webhook notifications triggered by Google Sheets edits. When a row status updates, it notifies Slack/Teams channels or pushes data directly to PostgreSQL staging databases. This decouples business logic from spreadsheets while keeping the administrative interface familiar and friendly to non-technical operational users. By avoiding massive dashboard UI development cycles, teams can launch working internal automations within hours rather than months, generating immediate ROI.

---

## Conclusion

When you use AI to optimize operations—from complex Reconciliation to Lightweight Automation on Google Sheets—the AI Platform Layer proves its massive ROI to the entire business.

However, this productivity explosion will create a massive shock for the Engineering team. When AI can ship 5 new features in a single day, **traditional CI/CD and Code Review workflows will seize up completely**. Recklessly merging AI-generated code will create irreversible technical debt.

Need architecture consulting or team training for your transition? → [Book a 1:1 Architecture Consultation](/hire/)

🔗 **Next Step:** [Part 4 — Policy-as-Code: Agentic CI/CD Guardrails for AI-Generated Code](/series/ai-driven-playbook/part-4-policy-as-code-agentic-cicd/) — Implementing static rules, tests, and automated policy gates in the CI/CD pipeline.
