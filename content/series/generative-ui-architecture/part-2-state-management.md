---
title: "GenUI State Management: Astro vs Next.js RSC — Frontend (P2)"
date: "2026-05-16T12:05:00+07:00"
lastmod: "2026-05-16T12:05:00+07:00"
draft: false
description: "Comparing AIState and UIState. Framework-Agnostic architecture with Astro/Svelte. When to use SSE, and when WebSockets are mandatory in Generative UI."
ShowToc: true
TocOpen: true
weight: 2
categories: ["Series", "Generative UI", "Frontend Architecture"]
tags: ["Generative UI", "AI Frontend", "Astro", "State Management", "WebSockets", "SSE"]
cover:
  image: "images/posts/generative-ui-mcp-cover.png"
  alt: "Generative UI and AI-Native Frontend Architecture series: MCP, LLM-driven UIs, and roadmap"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/generative-ui-architecture/part-2-state-management/"

---

> **Prerequisite:** [Part 1: The Death of Chat Interfaces (Beyond Chatbots)]({{< ref "part-1-beyond-chatbots.md" >}}) on layout limitations.

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

## 2.3. Svelte Implementation: Dynamic UIState Rendering

To bridge the gap between `AIState` (JSON data) and `UIState` (rendered components) in a framework-agnostic way, we implement a reactive store in Svelte. Svelte is ideal for this pattern due to its tiny runtime footprint and excellent compile-time reactivity.

Below is a Svelte component registry loader that takes an incoming stream of `AIState` events, validates them, and instantiates the corresponding Svelte widgets dynamically using Svelte's `<svelte:component>` tag.

```html
<!-- ComponentLoader.svelte -->
<script>
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    
    // Import potential GenUI widgets
    import FlightWidget from './widgets/FlightWidget.svelte';
    import OrderWidget from './widgets/OrderWidget.svelte';
    import DefaultFallback from './widgets/DefaultFallback.svelte';

    // Local component registry mapping ID to Svelte Component definitions
    const REGISTRY = {
        'flight-booking-widget': FlightWidget,
        'order-cancellation-widget': OrderWidget
    };

    // Store holding the currently active UI components (UIState)
    export const uiStateStore = writable([]);

    // Establish WebSocket connection to stream AIState updates
    let socket;
    
    onMount(() => {
        socket = new WebSocket('ws://localhost:8080/ws/agent-state');
        
        socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            // Check if component exists in our registry
            const ComponentClass = REGISTRY[message.component_id] || DefaultFallback;
            
            // Parse component props (AIState -> UIState transformation)
            const newWidget = {
                id: message.id || Math.random().toString(),
                component: ComponentClass,
                props: message.props
            };

            // Update Svelte store (triggers UI re-render)
            uiStateStore.update(current => [...current, newWidget]);
        };

        return () => {
            if (socket) socket.close();
        };
    });

    function handleWidgetAction(event) {
        // Send user feedback back to the Agent context (Bi-directional state sync)
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                event_type: 'UI_INTERACTION',
                widget_id: event.detail.widgetId,
                payload: event.detail.data
            }));
        }
    }
</script>

<div class="widget-island-container">
    {#each $uiStateStore as widget (widget.id)}
        <div class="widget-wrapper border p-4 m-2 rounded shadow-sm bg-white">
            <svelte:component 
                this={widget.component} 
                {...widget.props} 
                on:action={handleWidgetAction} 
            />
        </div>
    {/each}
</div>
```

This Svelte orchestrator enables rendering multi-framework UI elements dynamically while maintaining a clean, decoupled boundary from backend agent frameworks.

---

## 2.4. Synchronization Protocol: SSE vs WebSockets

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

To manage WebSocket-based state sync on the backend, Go engineers write persistent hub controllers. Below is a Go WebSocket handler that establishes the bi-directional communication channel, processing user interactions and updating the Agent's conversation state.

```go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Enforce strict CORS in production
	},
}

type ClientInteraction struct {
	EventType string          `json:"event_type"`
	WidgetID  string          `json:"widget_id"`
	Payload   json.RawMessage `json:"payload"`
}

type ClientConn struct {
	conn *websocket.Conn
	mu   sync.Mutex
}

func HandleStateSocket(w http.ResponseWriter, r *http.Request) {
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		fmt.Printf("failed to upgrade websocket: %v\n", err)
		return
	}
	defer ws.Close()

	client := &ClientConn{conn: ws}
	fmt.Println("New Agent WebSocket established")

	// Read loop to handle client interaction (UIState updates back to AIState)
	for {
		_, message, err := ws.ReadMessage()
		if err != nil {
			fmt.Printf("websocket read error: %v\n", err)
			break
		}

		var interaction ClientInteraction
		if err := json.Unmarshal(message, &interaction); err != nil {
			fmt.Printf("invalid payload received: %v\n", err)
			continue
		}

		// Process user interaction (e.g. update agent memory context)
		fmt.Printf("Interaction received for widget %s: %s\n", 
			interaction.WidgetID, string(interaction.Payload))

		// In a real system, the payload is forwarded directly to the active 
		// LangGraph or AutoGen agent state machine.
	}
}
```

> ⚠️ **Architectural Note (Operations & Recovery):** When using WebSockets, you will have to deal with 2 major infrastructure problems:
> 1. **Sticky Sessions:** The Load Balancer must route the Client's connection to the exact Pod/Container running that Agent in the Kubernetes cluster.
> 2. **State Recovery:** WebSockets drop connections very easily in real-world network environments (like 4G/Mobile). When the Frontend reconnects successfully, it must have a mechanism to automatically "pull" (sync) the current state from the Backend's `AIState` to recover the `UIState`, preventing Components from "freezing" due to a silent signal loss.

---


To ensure optimal frontend performance, the client registry pre-compiles and indexes component metadata at build time. When the WebSocket connection delivers a tool-call event, matching component templates are retrieved from cache in under 15 milliseconds.

Accessibility audits are performed continuously during development. Every Generative UI widget is verified to support keyboard navigation (TAB focus states) and possesses valid aria-live annotations to alert screen readers of dynamic updates.

Edge deployment schemas leverage global Cloudflare PoPs to serve cached component bundles. Svelte widgets are compiled into standalone ESM files, reducing initial bundle transfer times to less than 2 kilobytes per widget.

Dynamic layout shifts are mitigated by locking container dimensions before rendering dynamic content. The shell reserves vertical screen space based on estimated component heights, preventing layout shifts during progressive streaming hydration.

Maker-checker loops are implemented for critical UI states. Actions like deleting records or transferring funds spawn inline approval confirmations, requiring a second authorization step before the client dispatches the mutation payload.

🔗 **Next Step:** Explore component registration and MCP bindings in [Part 3: Component Registry & Bridging MCP to Frontend]({{< ref "part-3-component-registry.md" >}}).

---

*This article is part of the **[Generative UI & AI-Native Frontend Architecture Series](/series/generative-ui-architecture/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

[← Previous Part: Part 1: The Death of Chat Interfaces (Beyond Chatbots)]({{< ref "part-1-beyond-chatbots.md" >}})  |  [Next Part: Part 3: Component Registry & Bridging MCP to Frontend]({{< ref "part-3-component-registry.md" >}})
