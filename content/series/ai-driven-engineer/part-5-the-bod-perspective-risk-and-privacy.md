---
title: "Part 5 — The BOD Perspective: Expectations, Costs, Legal Risks & Internal AI"
date: 2026-05-10T15:40:00+07:00
lastmod: 2026-05-10T15:40:00+07:00
draft: false
description: "Analyzing AI through the lens of the Board of Directors (BOD). The balance between cost optimization, speed, and the legal/security landmines that could bring down a company."
ShowToc: true
TocOpen: true
weight: 6
categories: ["Series", "Software Engineering"]
tags: ["AI", "System Design", "Career"]
cover:
  image: "/images/posts/ai-native-frontend-cover.png"
  alt: "AI-Driven Engineer series: evolving from code typist to AI-native software architect"
  relative: false
---

So far, we have discussed AI extensively from the perspective of Programmers and Testers. But if you step into the boardroom of the Board of Directors (BOD) or Chief Technology Officers (CTO), you'll see a completely different lens.

Executives (BOD) don't care how fancy your AI is, or how long your prompts are. Their lens consists of 3 vital variables: **Cost, Time-to-Market, and Risk Management.**

The misalignment between BOD expectations and the working reality of Programmers is creating a zone of extreme pressure.

## 1. The Benefit Balance: Expectations and the Headcount Problem

When the BOD reads the news and sees "AI can code a whole app by itself," two questions immediately pop into their heads:

*   **The "Why not just let AI do it faster?" Syndrome:** Why is this shopping cart feature estimated at 3 weeks? Can't we just let AI run it in 1 day? The BOD often forgets that AI codes an isolated feature quickly, but to **integrate** it into the company's clunky Legacy system requires human architectural analysis.
*   **The Headcount Problem:** *If AI doubles productivity, why do I need to maintain a team of 10? Can I cut it down to 5 people plus an AI Premium account?*

**The Developer's Role Now:** You must be the one to bring the BOD back to earth. An excellent Developer will prove that: AI helps get **more done (Do more)** with the same headcount, improving quality and scaling larger systems, rather than being an excuse for reckless layoffs. You become an "ROI Investor" instead of a "Code Typist."

## 2. The Risk Balance: Legal and Security "Landmines"

The expectation of speed is quickly doused with cold water when the BOD faces **"Legal & Security Landmines"**. This is why large corporations ban employees from using public ChatGPT or Cursor.

1. **Copyright Infringement Landmine:** AIs like GitHub Copilot are trained on billions of lines of open-source code. Sometimes, AI engages in "Regurgitation" and spits out an exact code snippet from a project with a strict license (like `GPL` or `Copyleft`). If a Dev blindly accepts that code into the company's closed-source project, **the entire project could be forced to become open-source** by law. This is a business disaster.
2. **Data Leakage:** Copying Database schema structures or pasting API Keys into Public LLMs is considered leaking company assets.
   > **[Case Study] [Samsung Source Code Leak](https://www.bloomberg.com/news/articles/2023-05-02/samsung-bans-chatgpt-and-other-generative-ai-use-by-staff-after-leak):** In April 2023, within just 20 days of allowing engineers to use ChatGPT, Samsung recorded 3 instances of highly classified semiconductor source code leaked to OpenAI's servers. The company immediately issued a global ban on public AI use.

3. **Supply Chain Attacks Landmine:** AI sometimes "hallucinates" an npm or PyPI library that doesn't exist at all. Hackers know this and proactively create malicious packages bearing that exact fake name. Devs trust the AI, type the install command, and the system is compromised.
   > **[Hard Evidence] ["AI Package Hallucination" Attack](https://vulcan.io/blog/ai-hallucinations-package-risk):** Research by Vulcan Cyber shows hackers can bait AI into generating fake library names (like `huggingface-cli-login`). When a junior dev copies this exact install script and runs it on a server, Ransomware is instantly activated.

## 3. The Enterprise Solution: Internal AI (Local LLMs)

To solve the dilemma: *Banning AI loses productivity, but using public AI carries legal risks*, Enterprises are rushing to build **Private AI Infrastructure**.

Instead of buying Cloud OPEX (monthly subscriptions), companies spend massive CAPEX to buy expensive GPU server clusters (NVIDIA H100). Then, they run **Local LLMs** (open-source coding models like DeepSeek Coder, Qwen-Coder, Llama 3) directly on the company's internal network (VPC).

### Architecture Diagram: Private AI Infrastructure

Here is how a business protects its source code using On-Premise AI architecture:

```mermaid
graph TD
    Dev[Developer Laptop] -->|Code Completion & Chat| LocalAPI[Local AI Gateway]
    LocalAPI -->|Route| VectorDB[(Internal Vector DB / RAG)]
    LocalAPI -->|Route| GPU[On-Premise GPU Cluster]
    
    subgraph "Internal Network (VPC - No Internet)"
        GPU --> Model[Llama 3 / DeepSeek-Coder]
        VectorDB -.->|Context (Gitlab/Jira)| Model
    end
    
    style Dev fill:#d5f5e3,stroke:#2ecc71
    style GPU fill:#f9e79f,stroke:#f1c40f
```

### Technical Example: AI Operating Model Template

To deploy this model, Dev/DevOps teams often use Docker and Ollama to run local language models without sending data externally:

```yaml
# docker-compose.yml for Private AI
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
              
  # Internal WebUI for employees
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    ports:
      - "3000:8080"
```
*Thanks to this configuration, hundreds of devs in the company can call the `localhost:11434` API to generate code while data absolutely never leaves the internal servers.*

*   **100% Secure:** Devs use their IDE (VS Code) with plugins (like Continue.dev) pointing to the internal AI server. Not a single line of code leaves the LAN.
*   **Internal RAG Superpower:** ChatGPT only knows code on public Github. But a Local LLM is connected to the company's Gitlab via RAG technology. This AI will "memorize" 10 years of the company's coding history. It generates code that perfectly matches internal Conventions, using internal libraries that no outsider knows about.

## [Bonus] AI Risk Assessment Checklist for Enterprises

Below is a highly practical checklist that Tech Leads and QA can immediately integrate into their Code Review / CI-CD processes to protect the company from the "3 landmines" mentioned above:

- [ ] **PII (Personal Identifiable Information) Filtering:** Has the source code fed to public AI (ChatGPT/Claude) been WIPED clean of real emails, phone numbers, and credit cards of Users?
- [ ] **Secrets/Tokens Filtering:** Are there any API Keys, AWS Secrets, or Database Passwords hardcoded in the prompt sent to AI?
- [ ] **License Check:** Has the AI-generated code been scanned through a licensing tool (like Black Duck or Snyk) to ensure no `GPL/Copyleft` violations?
- [ ] **Dependency Hallucination Check:** Does the `npm` or `pip` library the AI suggests installing ACTUALLY EXIST on the official registry? Is it verified by the community?
- [ ] **Local LLM Mandate:** Does this module contain the company's proprietary "Core Business Logic"? If YES, you **MUST** use the on-premise Local LLM to generate code instead of a Public LLM.

## The Climax: Where Do Developers Stand In The Crossfire?

Artificial intelligence is no longer a personal "magic trick". In the eyes of the BOD, it has become **Enterprise Infrastructure**.

The BOD has bought servers, installed Local LLMs, and issued a directive: *"From now on, everyone uses internal AI to double their work speed, and not a single line of code is allowed to leak outside."*

The pressure shifts back to the Programmer's shoulders. You have no retreat. You cannot reject AI. You are forced to learn how to "Ride the Beast". But how do you transition from a pure Coder to a true AI Orchestrator, knowing how to "inject context" so the computer works for you? The secret will be revealed in **[Part 6: Role Shift: From Coder to AI Orchestrator](/series/ai-driven-engineer/part-6-from-coder-to-orchestrator/)**.

---
### 🛠 Practical Exercise: Audit an AI Prompt
1. **Challenge:** You are a Security Auditor.
2. **Action:** Take a piece of real code containing database connection logic from your current project. Paste it into ChatGPT.
3. **Analysis:** Review that code. Did you accidentally leak a secret key, password, or sensitive table structure in the prompt? Learn from this and make it a habit to sanitize sensitive data before using Public AI.

### 📚 External Resources & Related Links
- **Private AI Tools:** [Ollama](https://ollama.com/) (Run AI locally), [LM Studio](https://lmstudio.ai/).
- **Further Reading:** [OWASP Top 10 for LLMs](https://owasp.org/www-project-top-10-for-large-language-model-applications/) - Mandatory reading on AI security.
- **Related in series:** Detailed architectural solutions to avoid being locked into a single AI provider are presented in [Part 9: Building AI-Native Architecture](/series/ai-driven-engineer/part-9-building-ai-native-architecture/).

---
💬 **Discussion Corner:** From a business perspective, what is your boss's (CTO/BOD) biggest fear regarding AI right now? High account costs, source code leak risks, or employee resistance?

<div style="display: flex; justify-content: space-between; margin-top: 2rem;">
  <div><a href="/series/ai-driven-engineer/part-4-blurring-sdlc-lines-and-qc-revolution/">← Previous: Part 4</a></div>
  <div><a href="/series/ai-driven-engineer/part-6-from-coder-to-orchestrator/">Next Article: Part 6 →</a></div>
</div>
