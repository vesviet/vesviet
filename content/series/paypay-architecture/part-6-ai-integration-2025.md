---
title: "Part 6 — PayPay Goes AI-Native: LLM Hub & RAG (2025)"
date: 2026-05-05T21:00:00+07:00
lastmod: 2026-05-05T21:00:00+07:00
draft: false
description: "How PayPay built its 2025 AI platform: multi-model LLM Hub, internal RAG pipeline, delinquency chatbot, and autonomous AI agents for payment operations."
weight: 7
cover:
  image: "/images/posts/paypay-scaling-cover.png"
  alt: "PayPay Architecture series: scaling for planet-scale mobile payment campaigns in Japan"
  relative: false
---

## Why a Payment Platform at Scale Needs an AI Architecture

In 2024, PayPay crossed 70 million registered users. At that scale, the support surface becomes enormous: millions of users with questions about payments, delinquent accounts, transaction disputes, and product features. The fraud detection surface grows with every new user and transaction pattern. The internal engineering organization — hundreds of engineers across multiple business units — generates thousands of decisions per week that benefit from knowledge retrieval and synthesis.

AI is not a feature addition for PayPay in 2025. It is an **operational necessity**.

Three forces converged to accelerate PayPay's AI investment:

1. **Scale pressure:** 7.8 billion transactions in FY2024 generates proportional support and operations volume that human teams alone cannot absorb cost-effectively.
2. **SoftBank-OpenAI partnership:** As a SoftBank Group company, PayPay has early access to OpenAI's enterprise capabilities — including "Cristal Intelligence," an enterprise AI platform designed to analyze and maintain legacy codebases. This partnership gave PayPay a technology advantage in AI adoption.
3. **Strategic shift:** PayPay's leadership recognized that transitioning from a payment platform to a **Financial OS** requires AI as invisible infrastructure — powering fraud detection, credit scoring, customer support, and product personalization simultaneously.

The result is a multi-layer AI architecture that spans developer tooling, internal knowledge management, and customer-facing AI products.

## Layer 1: The LLM API Hub — Multi-Model Gateway

PayPay's AI foundation is a central **LLM API Hub**: an internal gateway that routes AI requests to multiple large language models simultaneously, abstracting the specific model from the consuming application.

```
Internal Application / Agent
        ↓
LLM API Hub (internal gateway)
        ↓
┌───────┬───────────┬──────────┐
│ GPT-4o│  Gemini   │  Claude  │
│(OpenAI)│(Google)   │(Anthropic)│
└───────┴───────────┴──────────┘
```

**Why a multi-model hub?**

- **No vendor lock-in:** If OpenAI changes pricing or model behavior, PayPay can shift traffic to Gemini or Claude without modifying any consuming application.
- **Cost optimization:** GPT-4o-mini handles routine, lower-complexity tasks (document summarization, FAQ generation, code comments) at a fraction of the cost of larger models. GPT-4o or Claude 3 Opus handle complex reasoning tasks (fraud pattern analysis, multi-step agent workflows) where accuracy justifies the higher token cost.
- **Security and compliance layer:** All requests pass through the hub's sanitization layer before reaching external LLM APIs. Sensitive user PII, financial data, and internal system details are detected and filtered before transmission. Responses are validated against safety policies before returning to the consuming application.
- **Unified rate limiting and audit logging:** Every LLM API call is logged with the consuming service, model used, token count, latency, and cost. This audit trail is essential for both cost governance and regulatory compliance in a financial services context.

## Layer 2: The Internal RAG Pipeline

LLMs are powerful but have a fundamental limitation: their knowledge is frozen at training time. PayPay's internal knowledge — engineering runbooks, compliance policies, HR procedures, product specifications, and historical incident reports — is continuously updated and proprietary.

**Retrieval-Augmented Generation (RAG)** bridges this gap by giving the LLM access to a dynamic, searchable knowledge base at inference time.

### PayPay's RAG Architecture

```
Knowledge Sources:
  ├── Internal Confluence wikis
  ├── Engineering runbooks
  ├── Company regulations & compliance docs
  └── Historical incident reports

          ↓ (Ingestion Pipeline)

Preprocessing:
  - Documents chunked by heading and chapter
  - Each chunk maintains parent document context
  - Metadata tagged: document type, owner, last updated

          ↓

Vector Embedding → ChromaDB (vector store)

          ↓ (Query Pipeline)

User Query
  → Embedded into same vector space
  → Semantic similarity search in ChromaDB
  → Top-K relevant chunks retrieved
  → Chunks injected into LLM context window
  → LLM generates response grounded in retrieved documents
```

**Why chunk by heading/chapter?** Chunking by semantic units (sections, chapters) rather than arbitrary token windows ensures that retrieved context is coherent — the LLM receives a complete argument or procedure, not a fragment that starts mid-sentence. This dramatically reduces hallucination in the RAG response, which is critical for compliance documents where accuracy is non-negotiable.

### Production RAG Use Cases

| Use Case | Knowledge Source | Consumer |
|---|---|---|
| Engineering Q&A | Architecture docs, runbooks | Internal engineers |
| Compliance Q&A | Regulations, PCI DSS policies | Compliance and legal teams |
| Incident analysis | Historical post-mortems | SRE on-call engineers |
| Policy retrieval | HR, finance, product policies | All employees |

The RAG pipeline has a secondary benefit: it forces documentation discipline. Teams that want their knowledge to be retrievable must keep their Confluence pages updated, structured, and properly tagged — turning AI adoption into an organizational documentation improvement program.

## Layer 3: Production AI Application — The Delinquency Chatbot

PayPay launched its first production-facing generative AI application in **March 2025**: a **Generative AI-Enabled Payment Delinquency Chatbot**.

**The problem:** PayPay's financial services (PayPay Atobarai credit, PayPay Card) generate delinquency cases — users who have missed payment due dates. Handling delinquency inquiries manually is expensive, time-sensitive, and emotionally sensitive — users experiencing financial difficulty often avoid engaging with human support agents due to shame or anxiety.

**The AI solution:**

```
User initiates delinquency inquiry (app or web)
        ↓
Chatbot retrieves from RAG:
  - User's specific payment history (personalized)
  - Current overdue amounts and due dates
  - Available repayment options and deadlines
  - Company policy on late fees and grace periods
        ↓
LLM generates empathetic, accurate, personalized response
        ↓
User can confirm repayment plan directly in chat
        ↓
If human escalation needed → seamless handoff to human agent with full context
```

**Design principles:**
- **Lowering the psychological barrier:** The chatbot's tone is deliberately non-judgmental and solution-focused, reducing the anxiety that prevents users from engaging with delinquency issues.
- **Accuracy over speed:** Given the financial and regulatory stakes, the RAG retrieval is optimized for precision — it is better to retrieve fewer, more accurate documents than many loosely relevant ones.
- **Graceful escalation:** The chatbot has explicit handoff protocols — when a situation exceeds its scope (complex disputes, legal threats), it summarizes the conversation and routes to a human agent with full context, avoiding the frustrating "start over" experience of chatbot escalations.

## Layer 4: From Tools to Autonomous Agents

PayPay's AI strategy for 2025 and beyond is explicit: **move from AI as a tool to AI as an autonomous agent**.

**2024 — AI tools phase:**
- GitHub Copilot for code completion
- Internal Slackbots for Q&A and document search
- GPT-4 for one-off tasks (code explanation, PR summaries)

**2025 — Agentic phase:**
PayPay is building agents that can reason, plan, and execute multi-step tasks autonomously — not just respond to prompts.

Example: **Code Review Agent**
```
Trigger: PR opened in GitHub
Agent actions:
  1. Read PR diff and identify changed services
  2. Retrieve relevant architecture docs from RAG
  3. Check test coverage against coverage policies
  4. Analyze potential breaking changes in gRPC contracts
  5. Post structured review comments:
     - Security: "This endpoint lacks rate limiting — see runbook X"
     - Architecture: "This violates the Wallet domain boundary — see ADR-42"
     - Testing: "Coverage for payment edge cases is below 80%"
  6. Flag for human reviewer if risk score exceeds threshold
```

The agent does not replace the human reviewer — it amplifies their effectiveness by completing the mechanical parts of code review before the human reads a single line.

## LLMOps: How PayPay Governs AI in Production

Operating AI in a regulated financial services context requires governance that most AI deployments skip. PayPay's LLMOps practices:

**DesignDocs for AI components:** Every new AI feature follows the same DesignDoc process as any microservice — articulating the "why" behind model selection, chunking strategy, prompt design, and fallback behavior before implementation begins. This ensures that AI architectural decisions are as well-reasoned and documented as infrastructure decisions.

**Multi-tier metrics framework:**
- **System health:** LLM API latency, RAG retrieval time, embedding computation cost, error rates
- **Response quality:** Retrieval precision (are the right chunks being retrieved?), response groundedness (is the answer based on retrieved documents, not hallucinated?)
- **Business value:** For the delinquency chatbot — resolution rate (user agrees to repayment plan without human escalation), user satisfaction score, reduction in delinquency duration

**Patent portfolio:** PayPay has obtained multiple patents on specific components of its internal RAG pipeline — particularly around how training data from internal systems is processed, chunked, and indexed. This intellectual property protects against competitors replicating their knowledge retrieval approach.

**Bottom-up AI adoption:** PayPay's AI Utilization Office does not mandate specific tools or use cases. Engineers propose AI integrations, demonstrate value in a controlled experiment, and gain organization-wide adoption if the results justify it. This culture has produced a wider and more creative portfolio of AI applications than a top-down mandate would have generated.

## What This Means for Financial Infrastructure

PayPay's AI architecture in 2025 represents a broader shift happening across fintech: AI is becoming **infrastructure**, not a feature. The LLM API Hub is as fundamental to PayPay's operations as Kafka or TiDB — a layer that every other system depends on, that must be highly available, observable, and governable.

The transition from the 2018 platform (a QR payment app that crashed under its first campaign) to the 2025 platform (a 70-million-user Financial OS with autonomous AI agents) did not happen through a single architectural decision. It happened through continuous iteration — each campaign, each incident, each new capability driving the next architectural improvement.

For teams building agentic AI systems into their own platforms, the [Agentic System Architecture](/series/agentic-system-architecture/) series covers the multi-agent orchestration patterns that underpin systems like PayPay's code review agent and delinquency chatbot in technical depth.
