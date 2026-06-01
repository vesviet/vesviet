---
title: "GenUI State Management: Astro vs Next.js RSC — Frontend (P2)"
date: 2026-05-16T12:05:00+07:00
lastmod: 2026-05-16T12:05:00+07:00
draft: false
description: "Comparing AIState and UIState. Framework-Agnostic architecture with Astro/Svelte. When to use SSE, and when WebSockets are mandatory in Generative UI."
ShowToc: true
TocOpen: true
weight: 2
categories: ["Series", "Generative UI", "Frontend Architecture"]
tags: ["Generative UI", "AI Frontend", "Astro", "State Management", "WebSockets", "SSE"]
---

In the previous part, we agreed on discarding Chatbots to move towards Generative UI. But for AI to "spawn" UI Components right on the user's screen, the Frontend and Backend cannot just communicate via standard stateless APIs. They need to share a common State.

The problem is: The AI's brain and the User's browser speak two entirely different languages.

## 2.1. Clear Demarcation: AIState vs UIState

When building an Agentic system with an Interface, the first vital rule is to strictly separate `AIState` and `UIState`.

### AIState (The Backend's Brain)
- **Nature:** An array containing the entire conversation history, tool calls, and Agent context.
- **Format:** Pure JSON (Serializable). This is what gets sent straight into the LLM's mouth (e.g., OpenAI API) and stored in the Database (PostgreSQL/Redis).
- **Example:** `[{"role": "user", "content": "Buy a ticket to Hanoi"}, {"role": "assistant", "tool_calls": [{"name": "book_flight", "arguments": "{"dest": "HAN"}"}]}]`

### UIState (The Frontend's Display)
- **Nature:** A list of React/Svelte/Vue Components currently being rendered on the screen.
- **Format:** Objects containing Functions, DOM Nodes, Event Listeners (Non-serializable). You **cannot** save UIState into a Database.
- **Example:** `[<UserMessage text="Buy a ticket to Hanoi" />, <FlightBookingWidget dest="HAN" onConfirm={handleConfirm} />]`

**The core challenge of Generative UI is how to map a JSON string (AIState) into a list of Components (UIState) safely and in real-time.**

## 2.2. Two Architectural Schools: Next.js (RSC) vs Framework-Agnostic (Astro)

Currently, the Frontend world is split into two halves in handling this mapping problem.

### School 1: Next.js and React Server Components (RSC)
This is the approach heavily promoted by Vercel (via Vercel AI SDK).
- **How it works:** The mapping from AIState to UIState happens *entirely on the Server*. The Server runs the LLM, receives JSON, and immediately renders a React Component. The server then "streams" that Component directly to the Client via an RSC payload.
- **Pros:** Excellent Developer Experience (DX). You code frontend and backend in one place.
- **Cons (The Enterprise Fatal Flaw):** Vendor lock-in to Next.js and React. If your core system is using Vue, Svelte, Angular, or runs on Astro, Java Spring Boot on the Backend, this model completely falls apart.

### School 2: Framework-Agnostic with A2UI Standard (The Enterprise Choice)
To keep the system Future-proof and easily integrable into Legacy projects, we must push the mapping logic down to the Client (or an intermediary Orchestrator like Astro).
- **How it works:**
  1. The Backend Agent (running Python/Golang/Node) calls the LLM and returns a standardized JSON structure (like the **A2UI - Agent to User Interface** standard).
  2. This JSON only contains: `Component_Name` (e.g., `flight_widget`) and `Props_Data`.
  3. The Frontend (Astro) acts as the *Orchestrator*. It receives this JSON, looks in its *Component Registry*, grabs the corresponding Svelte/Vue Component, injects the Data, and renders it on screen.
- **Pros:** Backend Agents can be written in any language. Frontend can use Astro to mix React, Vue, and Svelte on the same page (Islands Architecture). Absolute security because AI never touches HTML/JS code; it only returns Data.

## 2.3. Synchronization Protocol: SSE vs WebSockets

Once the Frontend knows how to render, the next question is: What communication channel should the Frontend use to receive signals from the Agent?

### Server-Sent Events (SSE) - Suitable for Token Streaming
If your UI only needs to display text typing out letter by letter (ChatGPT-style) or show simple statuses ("Searching..."), SSE is more than enough.
- **Pros:** Uses standard HTTP, passes through Load Balancers/Firewalls easily, browsers reconnect automatically.
- **Cons:** Unidirectional. The Server sends data down to the Client. If the Client wants to send data up, it must make another HTTP POST request.

### WebSockets - Mandatory for Interactive Agents
Complex Agentic systems require continuous Bi-directional interaction.
- **Scenario:** Agent A spawns a checkout form on the screen (Server $\rightarrow$ Client). The user modifies the amount and clicks "Confirm." This signal must immediately be sent back to Agent A so it can update its Context and proceed (Client $\rightarrow$ Server).
- In true Generative UI, UI state changes every millisecond when a user interacts with an AI-generated Component. Using HTTP POST for every interaction will cause unacceptable latency.
- **Recommendation:** Use **WebSockets** (or WebRTC Data Channels for heavy real-time apps) to manage `UIState` and `AIState`. 

> ⚠️ **Architectural Note (Operations & Recovery):** When using WebSockets, you will have to deal with 2 major infrastructure problems:
> 1. **Sticky Sessions:** The Load Balancer must route the Client's connection to the exact Pod/Container running that Agent in the Kubernetes cluster.
> 2. **State Recovery:** WebSockets drop connections very easily in real-world network environments (like 4G/Mobile). When the Frontend reconnects successfully, it must have a mechanism to automatically "pull" (sync) the current state from the Backend's `AIState` to recover the `UIState`, preventing Components from "freezing" due to a silent signal loss.

---
🔗 **Next Step:** In this part, we mentioned the "Component Registry" — the heart of the Framework-Agnostic architecture. How does the Backend Agent know what Components the Frontend has available to call? Find out in [Part 3 — Component Registry & Bridging MCP to Frontend](/series/generative-ui-architecture/part-3-component-registry/).
