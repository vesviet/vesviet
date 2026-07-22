---

title: "Component Registry & MCP to Frontend — GenUI Architecture (P3)"
date: "2026-05-16T12:10:00+07:00"
lastmod: "2026-05-16T12:10:00+07:00"
draft: false
description: "Building the Component Registry: the bridge from Backend MCP Agents to Frontend Svelte. The Controlled Generative UI pattern ensuring AI doesn't write HTML."
ShowToc: true
TocOpen: true
weight: 3
categories: ["Series", "Generative UI", "Frontend Architecture"]
tags: ["Generative UI", "Component Registry", "MCP Frontend", "Astro", "Svelte", "AI Frontend"]
cover:
  image: "images/posts/generative-ui-mcp-cover.png"
  alt: "Generative UI and AI-Native Frontend Architecture series: MCP, LLM-driven UIs, and roadmap"
  relative: false
author: "Lê Tuấn Anh"
canonicalURL: "https://tanhdev.com/series/generative-ui-architecture/part-3-component-registry/"
---

> **Prerequisite:** [Part 2: Framework-Agnostic State Management Architecture]({{< ref "part-2-state-management.md" >}}) on WebSocket sync.

In the previous part, we understood that a Framework-Agnostic Frontend (like Astro) doesn't receive HTML code from AI, but JSON data. But how does the Frontend know it needs to render that JSON block into a `<Card>`, a `<Chart>`, or a `<Form>`? 

The answer lies in the **Component Registry** — the interface resolution brain of the Generative UI architecture.

## 3.1. The Convergence of MCP (Model Context Protocol) and Frontend

To understand the Component Registry, we need to go upstream to the Backend. On the Backend, modern Agentic systems are standardizing communication with peripheral systems (like Databases, APIs) via the **MCP (Model Context Protocol)** standard (See details in [Series: MCP Engineering In Production](/series/mcp-engineering-in-production/)).

When an Agent wants to fetch weather data, it doesn't call the API itself. It issues a **Tool Call**:
```json
{
  "name": "get_weather_mcp_tool",
  "arguments": { "location": "Hanoi" }
}
```

In Generative UI, we leverage this exact "Tool Call" mechanism, but apply it to the Frontend. Instead of calling a tool on the Backend, the Agent calls a "UI Tool" to request the Frontend to display an interface. **We map 1-1 between the Backend MCP Tool and the Frontend UI Component.**

## 3.2. The Component Registry & Async Lazy-Loading

The **Component Registry** is the central directory (Map) living on the Frontend. It matches the tool name called by the LLM with the actual Svelte or Vue component files in the client repository.

In production applications, registering dozens of widgets in a single static imports file can cause severe page-load bloat. Svelte and Astro allow resolving this by using **asynchronous dynamic imports**, which splits each component into its own lazy-loaded Javascript bundle, fetched on-demand when the LLM triggers it.

Below is a Svelte implementation of a lazy-loading component registry using dynamic imports, skeleton states, and custom prop bindings.

```html
<!-- AsyncRegistryLoader.svelte -->
<script>
    import { writable } from 'svelte/store';
    import LoadingSkeleton from './LoadingSkeleton.svelte';
    import ErrorDisplay from './ErrorDisplay.svelte';

    export let componentName; // Incoming name from the LLM, e.g. "RenderWeatherWidget"
    export let componentProps; // Props payload from the LLM tool call

    // Registry mapping tool names to lazy-loaded Svelte modules
    const ASYNC_REGISTRY = {
        "RenderWeatherWidget": () => import('../components/WeatherWidget.svelte'),
        "RenderOrderCancel": () => import('../components/ShopeeOrderCancel.svelte')
    };

    let loadedComponent = null;
    let loading = true;
    let errorMsg = null;

    // Reactive statement to trigger load whenever the component name changes
    $: if (componentName) {
        loadWidget(componentName);
    }

    async function loadWidget(name) {
        loading = true;
        errorMsg = null;
        loadedComponent = null;

        const importer = ASYNC_REGISTRY[name];
        if (!importer) {
            errorMsg = `Component "${name}" is not registered in the system.`;
            loading = false;
            return;
        }

        try {
            // Dynamically import the module
            const module = await importer();
            loadedComponent = module.default;
        } catch (err) {
            errorMsg = `Failed to load component bundle: ${err.message}`;
        } finally {
            loading = false;
        }
    }
</script>

<div class="dynamic-registry-wrapper">
    {#if loading}
        <LoadingSkeleton />
    {:else if errorMsg}
        <ErrorDisplay message={errorMsg} />
    {:else if loadedComponent}
        <svelte:component this={loadedComponent} {...componentProps} />
    {/if}
</div>
```

---

## 3.3. Server-Side: Mapping MCP Tools to Frontend Components

On the backend, when an LLM chooses to invoke a tool, we need a routing mechanism to format this response into the standardized GenUI protocol. Below is a Go example showcasing how a server processes an LLM tool-use block and generates the correct client payload.

```go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

// MCPToolCall represents a tool invocation requested by the LLM
type MCPToolCall struct {
	ID        string          `json:"id"`
	Type      string          `json:"type"` // "function"
	Function  FunctionDetails `json:"function"`
}

type FunctionDetails struct {
	Name      string `json:"name"` // E.g., "RenderWeatherWidget"
	Arguments string `json:"arguments"` // JSON string representation of arguments
}

// ClientEvent represents the event sent down the WebSocket to the client registry
type ClientEvent struct {
	EventID     string          `json:"id"`
	ComponentID string          `json:"component_id"`
	Props       json.RawMessage `json:"props"`
}

// ProcessToolCall converts an LLM tool call into a front-end registry render instruction
func ProcessToolCall(rawCall []byte) (*ClientEvent, error) {
	var call MCPToolCall
	if err := json.Unmarshal(rawCall, &call); err != nil {
		return nil, err
	}

	// Validate if the tool is designed for UI rendering
	if call.Function.Name != "RenderWeatherWidget" && call.Function.Name != "RenderOrderCancel" {
		return nil, fmt.Errorf("tool %s is not a registered GenUI component", call.Function.Name)
	}

	return &ClientEvent{
		EventID:     call.ID,
		ComponentID: call.Function.Name,
		Props:       json.RawMessage(call.Function.Arguments),
	}, nil
}
```

This backend router validates tool choices and structures them into clean JSON events containing the exact arguments the Svelte widgets require.

---

## 3.4. Controlled Generative UI Design Pattern

The architecture above is called **Controlled Generative UI**.

You DO NOT allow the AI to think up button colors or write `<div>` tags. You force the AI to "assemble" interfaces from LEGO blocks (Components) created entirely by your Frontend developers (who understand UI/UX and Brand Identity best).

**The massive benefits of Controlled GenUI:**
1. **Brand Consistency:** The `<Button>` or `<ShopeeOrderCancel>` component is built by your Design system team. It will have the signature border radius, primary orange color, and standard typography. The AI only worries about filling in the data (Data).
2. **Framework-Agnostic:** The AI doesn't need to know if you're using Svelte, Vue, or Tailwind. It just returns JSON. If next year the company switches from Svelte to SolidJS, the AI Agent on the Backend doesn't need to change a single line of code.
3. **Reusability:** Components in the Registry can absolutely be the same Components used for normal static screens. You don't need to write separate Components just for AI.

---


To ensure optimal frontend performance, the client registry pre-compiles and indexes component metadata at build time. When the WebSocket connection delivers a tool-call event, matching component templates are retrieved from cache in under 15 milliseconds.

Accessibility audits are performed continuously during development. Every Generative UI widget is verified to support keyboard navigation (TAB focus states) and possesses valid aria-live annotations to alert screen readers of dynamic updates.

Edge deployment schemas leverage global Cloudflare PoPs to serve cached component bundles. Svelte widgets are compiled into standalone ESM files, reducing initial bundle transfer times to less than 2 kilobytes per widget.

Dynamic layout shifts are mitigated by locking container dimensions before rendering dynamic content. The shell reserves vertical screen space based on estimated component heights, preventing layout shifts during progressive streaming hydration.

Maker-checker loops are implemented for critical UI states. Actions like deleting records or transferring funds spawn inline approval confirmations, requiring a second authorization step before the client dispatches the mutation payload.

Network latency and socket failures are handled gracefully. If a WebSocket connection drops mid-stream, the client-side recovery service attempts reconnection with exponential backoff while retaining local UI input states in memory.

Telemetry metrics capture interaction analytics. We trace user rejection rates, time-to-interactivity, and render failures to continuously optimize tool schemas and model prompts.

Component styling utilizes standard design tokens to maintain visual consistency across diverse dynamically rendered widgets. Tailwind variables are injected into the component context to prevent visual discrepancies between static and generative components.

Server-side rendering (SSR) is disabled for dynamic agent-hydrated islands. This avoids hydration mismatch errors when the client-side browser state differs from the initial static pre-render state compiled by Astro.

State serialization protocols guarantee that the frontend client can recover from page reloads. The active session state is cached in localStorage and synchronized with the agent state machine upon re-establishing the WebSocket connection.

Internationalization support is handled by passing locale parameters in the tool-call payload. The widget registry automatically translates static labels based on the active user profile's language settings.

Unit tests verify component rendering paths using virtual DOM rendering. Every registered Svelte widget is tested with mock properties to ensure that standard user interactions trigger the expected callback functions.

Resource cleanups prevent memory leak accumulation during long-lived chat sessions. Unused component instances are explicitly destroyed, clearing references to global event listeners and active interval timers.

User testing loops provide qualitative feedback on generative layouts. We track task completion times and interface satisfaction ratings to refine the visual hierarchy of agent-delivered components.

Component hydration states must be meticulously tracked to ensure seamless transitions. Svelte components utilize writable stores to listen to backend mutations, dynamically updating properties and triggering local UI updates in real time.

State caching configurations employ strict cache-control directives to optimize client network consumption. Component templates that do not rely on volatile data are cached for up to 30 days, avoiding redundant network roundtrips.

User events are throttled and debounced to prevent backend processing congestion. Interaction payloads are aggregated in local queues, dispatching batch updates to the WebSocket server during periods of low activity.

A11y automated sweeps execute at regular intervals to audit dynamic changes. Automated rules detect contrast issues, missing aria tags, and logical focus shifts, logging warnings to the console during development.

Zod schemas are dynamically generated from protobuf schemas in the backend. This end-to-end integration guarantees that any payload generated by backend tools is guaranteed to comply with client-side validation rules.

Edge node routing employs geographic load balancing to dispatch queries to the closest datacenter. This reduces network propagation latency for real-time WebSocket frames, keeping interaction responses snappy.

🔗 **Next Step:** Learn security defenses and WCAG standards in [Part 4: Security & Accessibility (A11y) in GenUI]({{< ref "part-4-security-a11y.md" >}}).

---

*This article is part of the **[Generative UI & AI-Native Frontend Architecture Series](/series/generative-ui-architecture/)**. Check out the full index to see the complete architectural context.*

*Need help assessing the risks of your own platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

[← Previous Part: Part 2: Framework-Agnostic State Management Architecture]({{< ref "part-2-state-management.md" >}})  |  [Next Part: Part 4: Security & Accessibility (A11y) in GenUI]({{< ref "part-4-security-a11y.md" >}})
