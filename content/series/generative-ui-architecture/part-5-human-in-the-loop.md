---
title: "GenUI Human-In-The-Loop: Optimistic UI & Fallback (Part 5)"
date: "2026-05-16T12:20:00+07:00"
lastmod: "2026-05-16T12:20:00+07:00"
draft: false
description: "Handling LLM latency with Skeleton Streaming & Optimistic UI. Designing Approve/Reject mechanisms for AI Agents. Graceful Degradation during network loss."
ShowToc: true
TocOpen: true
weight: 5
categories: ["Series", "Generative UI", "Frontend Architecture"]
tags: ["Generative UI", "Human-in-the-loop", "Optimistic UI", "AI Frontend", "Latency", "Fallback UI"]
cover:
  image: "images/posts/generative-ui-mcp-cover.png"
  alt: "Generative UI and AI-Native Frontend Architecture series: MCP, LLM-driven UIs, and roadmap"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/generative-ui-architecture/part-5-human-in-the-loop/"
---

Unlike traditional software (where feedback happens in tens of milliseconds), AI systems always come with a haunting ghost: **Latency**. 

Furthermore, because AI is non-deterministic (probabilistic), there is always a risk it executes contrary to the user's intent. If you let an AI automatically execute a dangerous command (like Deleting a Database or Transferring Money) without human moderation, it's a recipe for disaster.

Part 5 will address these two core issues through UX design: **Hiding latency** and **Empowering control (Human-in-the-loop)**.

## 5.1. Hiding Latency with Skeleton Streaming and Optimistic UI

When an Agent receives a command, it takes anywhere from 1 to 5 seconds to think, generate a JSON string, and send it down to the Frontend. The experience of staring at a blank screen or a loading Spinner for 5 seconds is terrible.

### Skeleton Streaming
Don't wait for the LLM to finish generating the entire JSON payload before rendering. As soon as the Backend WebSocket emits an Event announcing: `"Agent is preparing Component X"`, the Frontend must immediately paint a **Skeleton Loading** state of that Component.

```svelte
<!-- When aiState.status === 'generating' -->
<div class="skeleton-card">
  <div class="skeleton-title animate-pulse"></div>
  <div class="skeleton-body animate-pulse"></div>
</div>
```
Users will feel the system responds *instantly*. They see the "shape" of the result before the actual data is even injected.

### Optimistic UI
When a user clicks "Confirm" on a GenUI Component, don't wait for the Backend to return a result before updating the screen. **Optimistically assume** the operation will succeed and update the UI immediately.
- *Example:* Clicking "Delete Order". The "Order" component instantly disappears from the screen, showing a "Deleted" toast. In the background, the system then sends the Delete request to the Backend. If the Backend reports an error, the UI rolls back to the previous state and displays a red alert. 

## 5.2. Human-In-The-Loop: Blocking AI from Dangerous Tasks

"Human-in-the-loop" (HITL) means placing a human directly inside the AI's automation workflow. 

In the Generative UI architecture, **HITL is not a feature, but a security principle.** When the AI decides to execute an action that affects data (Mutation), it is not allowed to call the Backend API directly. Instead, it must **generate a Component that allows the user to Approve, Reject, or Modify**.

### Example: Human Resources (HR) System
- **Scenario:** A manager commands: *"Increase employee A's salary to $2000"*.
- **The WRONG way (Fully automated):** The Agent automatically calls the `POST /api/salary` API and updates the Database. If the AI misheard "A" as "B" or "2000" as "20000", the consequences are dire.
- **The RIGHT way (Generative UI HITL):** 
  1. The Agent generates a JSON requesting to call the tool: `RenderSalaryAdjustmentForm`.
  2. The Frontend renders the Form Component containing: Employee Name (A), Old Salary ($1500), Proposed New Salary ($2000).
  3. This Form has 2 buttons: **[Confirm]** and **[Cancel]**. The inputs can be freely *Modified*.
  4. The manager sees the Form, corrects $2000 to $1800, and manually clicks **[Confirm]**.
  5. Only then does the Form on the Frontend actually call the API (or send a confirmation signal back via WebSocket to the Agent).

## 5.3. Fallback UI: Graceful Degradation

Generative UI relies heavily on LLMs and WebSockets. If OpenAI/Anthropic goes down, or the user enters a dead zone (spotty 3G/4G), how will your system react?

The design principle of **Graceful Degradation** requires the system to fall back to a safe mode, rather than crashing entirely.

1. **Fallback to Traditional GUI:** If the LLM returns malformed JSON more than 3 times (exceeding Zod's Auto-Correction limit), the Frontend automatically displays a standard static Form for the user to manually fill out.
2. **Offline Mode:** If the WebSocket disconnects for a prolonged period, disable the "Chat / Generative AI" area entirely, show a "Lost connection to Smart Assistant" warning, but **still allow** the user to use the app's basic features via standard REST APIs.

By designing these Fallback paths, you ensure that AI remains an "Enhancement" layer, rather than the Achilles heel of your system.

---
🔗 **Next Step:** A GenUI system with countless ever-changing Components is a nightmare for Quality Assurance (QA) teams. How do you automate testing for an interface when you don't know what it will look like beforehand? Read on in [Part 6 — E2E Testing & Performance Optimization at the Edge](/series/generative-ui-architecture/part-6-e2e-testing-edge/).
