---
title: "Part 2: Rush Monorepo — Managing 21 Go & 2 Next.js Apps"
date: 2026-04-10T10:00:00+07:00
lastmod: "2026-11-02T09:00:00+07:00"
author: "Lê Tuấn Anh"
description: "Why Rush beats Nx and Turborepo for a Go + Next.js monorepo: strict dependency governance, incremental builds, and auto-generated TypeScript SDKs."
categories: ["Series", "Software Engineering", "Backend Architecture"]
tags: ["Golang", "Next.js", "Protobuf"]
series: ["composable-commerce-migration"]
weight: 3
slug: "part-2-rush-monorepo"
canonicalURL: "https://tanhdev.com/series/composable-commerce-migration/part-2-rush-monorepo/"
ShowToc: true
TocOpen: true
draft: false
cover:
  image: "/images/posts/default-post.png"
  alt: "Part 2: Rush Monorepo — Managing 21 Go & 2 Next.js Microservices"
  relative: false
keywords: ["rush monorepo golang", "polyglot monorepo pnpm", "buf protobuf monorepo", "composable commerce rush"]
mermaid: true
---

[← Previous Chapter: Part 1: Decomposing Magento into 21 Services with DDD](/series/composable-commerce-migration/part-1-ddd-bounded-contexts/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 3: Go + Kratos v2 Framework Deep Dive →](/series/composable-commerce-migration/part-3-golang-kratos/)

---

> **Answer-first:** Governing a polyglot monorepo (21 Go microservices and 2 Next.js frontends) with Microsoft Rush delivers strict dependency control, incremental builds, and automatic generation of TypeScript SDKs from proto files — all without version conflicts.

---

When you own 21 Go microservices and 2 frontend applications, the first infrastructure question is not Kubernetes or CI/CD — it is **how do you manage the source code itself?**

The two obvious options fail immediately: polyrepo (more than 21 separate Git repositories — impossible to keep versions consistent) and a naive monorepo (dump everything into one folder, with phantom dependencies everywhere). You need a real monorepo management tool.

> **A note on scope:** Rush manages the frontend layer (Next.js, TypeScript packages). The Go microservices are managed independently via `go.mod` and Go workspaces. The structure below reflects the platform's recommended approach — verify the `rush.json` configuration details against your own team's repository reality before copying it wholesale.

**Answer-first:** Microsoft Rush is the right choice for a platform that demands strict dependency governance, mixes Go services with TypeScript frontends, and needs to publish internal packages (such as the `api-client` TypeScript SDK generated from your Go protobuf definitions). This article documents the setup, the folder structure, and the key integration point between Go protos and frontend types.

## 1. Why Rush Instead of Nx or Turborepo?

A quick comparison:

| Feature | Rush | Nx | Turborepo |
|---|---|---|---|
| **Dependency governance** | ✅ `common-versions.json` — enforced | ⚠️ Per-project | ⚠️ Per-project |
| **Phantom dependency prevention** | ✅ Strict PNPM isolation | ⚠️ Configurable | ✅ Strict |
| **Polyglot (Go + TS)** | ✅ Custom bulk commands | ✅ Plugins | ⚠️ JS-only (native) |
| **Package publishing** | ✅ First-class `rush publish` command | ⚠️ Requires a plugin | ⚠️ Manual |
| **Learning curve** | 🔴 Steeper | 🟡 Moderate | 🟢 Low |
| **Backing company** | Microsoft (Rush Stack) | Nrwl (acquired by VSHN) | Vercel |

The deciding factor for the Composable Commerce platform: **`common-versions.json`**. When a storefront and an admin dashboard both consume an `api-client` package, you cannot allow one to run `react@19.0.0` while the other runs `react@19.1.0`. Rush enforces identical dependency versions across the entire repository — whereas Nx and Turborepo require you to configure this per project.

The second factor: Magento's PHP ecosystem taught us the true cost of **phantom dependencies** — where a package works fine locally because it happens to be installed somewhere in `node_modules`, but breaks in production because it was never a declared dependency. Rush's strict isolation with PNPM eliminates this entire class of bugs.

## 2. Repository Structure

```
composable-commerce/               ← Root folder of the monorepo
├── rush.json                      ← Rush configuration: pnpm version, project list
├── .npmrc                         ← PNPM configuration
├── common/                        ← Managed by Rush (NEVER edit by hand)
│   ├── config/
│   │   ├── rush/
│   │   │   └── common-versions.json   ← Pins versions for all shared dependencies
│   │   └── .npmrc
│   └── temp/                      ← Rush's working folder (gitignored)
│
├── apps/
│   ├── storefront/                ← Next.js storefront (SSR)
│   │   └── package.json
│   └── admin-dashboard/           ← React admin dashboard
│       └── package.json
│
├── packages/
│   ├── ui-components/             ← Shared design system (Radix + Tailwind)
│   │   └── package.json
│   ├── api-client/                ← TypeScript SDK generated from Go protos
│   │   ├── package.json
│   │   └── generated/             ← Generated code, never edit by hand
│   └── utils/                     ← Shared validation and formatting helpers
│       └── package.json
│
└── services/                      ← Go microservices (Rush orchestrates the builds)
    ├── order-service/
    │   ├── go.mod
    │   └── ...
    ├── catalog-service/
    │   ├── go.mod
    │   └── ...
    └── ... (21 services in total)
```

The important constraint: `services/` holds Go modules. Rush does not manage `go.mod` — it only orchestrates builds through custom commands in `rush.json` (by shelling out to `go build`). Go dependency management (`go mod tidy`, `go.sum`) is an entirely separate concern.

## 3. rush.json Configuration

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/rush/v5/rush.schema.json",
  "rushVersion": "5.150.0",
  "pnpmVersion": "11.0.0",
  "nodeSupportedVersionRange": ">=20.0.0 <23.0.0",

  "projects": [
    { "packageName": "@composable/storefront",       "projectFolder": "apps/storefront" },
    { "packageName": "@composable/admin-dashboard",  "projectFolder": "apps/admin-dashboard" },
    { "packageName": "@composable/ui-components",    "projectFolder": "packages/ui-components" },
    { "packageName": "@composable/api-client",       "projectFolder": "packages/api-client" },
    { "packageName": "@composable/utils",            "projectFolder": "packages/utils" }
  ]
}
```

The Go services are added as custom bulk commands rather than as Rush projects — because they have no `package.json`:

```json
{
  "commands": [
    {
      "commandKind": "bulk",
      "name": "build:go",
      "description": "Build all Go microservices",
      "enableParallelism": true,
      "allowWarningsInSuccessfulBuild": false,
      "shellCommand": "go build ./..."
    },
    {
      "commandKind": "bulk",
      "name": "test:go",
      "description": "Run Go unit tests",
      "shellCommand": "go test ./... -race -count=1"
    }
  ]
}
```

## 4. Dependency Version Governance

The `common/config/rush/common-versions.json` file pins the shared dependencies:

```json
{
  "preferredVersions": {
    "typescript":          "~5.5.0",
    "react":               "^19.0.0",
    "react-dom":           "^19.0.0",
    "next":                "^15.0.0",
    "@tanstack/react-query": "^5.50.0",
    "zod":                 "^3.24.0",
    "tailwindcss":         "^3.4.0",
    "@radix-ui/react-dialog": "^1.1.0"
  },
  "allowedAlternativeVersions": {}
}
```

When a developer runs `rush add -p react@18.2.0` in any project, Rush rejects it if the preferred version is `^19.0.0`. This is exactly the enterprise-grade governance feature that justifies Rush's steep learning curve.

## 5. The api-client Bridge: From Go Proto → TypeScript

This is the single most valuable structural decision in the entire monorepo setup: **your TypeScript types are automatically generated from your Go proto definitions**.

The flow:

```
services/order-service/api/order/v1/order.proto
    ↓ buf generate (buf.gen.yaml)
packages/api-client/generated/
    ├── order/v1/order_pb.ts          ← Proto message types
    ├── order/v1/order_connect.ts     ← ConnectRPC client (or grpc-gateway)
    └── index.ts                      ← Re-exports
    ↓ rush build --to @composable/api-client
apps/storefront/                      ← import @composable/api-client
apps/admin-dashboard/                 ← import @composable/api-client
```

The `buf.gen.yaml` file at the repository root:

```yaml
version: v2
plugins:
  - plugin: es
    out: packages/api-client/generated
    opt: target=ts
  - plugin: connect-es
    out: packages/api-client/generated
    opt: target=ts
inputs:
  - directory: services
    paths:
      - "*/api/**/*.proto"
```

Running `buf generate` from the repository root regenerates all the TypeScript clients whenever any proto file changes. This task is configured as a CI check: if the generated files differ from the committed ones, the build fails. **Protobuf is the contract; the TypeScript types are derived from it.**

The result, inside the storefront:

```typescript
import { OrderServiceClient } from "@composable/api-client/order/v1";
import { CreateOrderRequest } from "@composable/api-client/order/v1";

// Types mirror your Go proto exactly — no hand-typing (duplication)
const req: CreateOrderRequest = {
  customerId: session.userId,
  items: cart.items.map(item => ({
    productId: item.id,
    quantity: item.qty,
    unitPrice: item.price, // Money type: { currencyCode, units, nanos }
  })),
  shippingAddress: shippingAddr,
  requestId: crypto.randomUUID(), // Idempotency key
};
```

When the Go backend team adds a field to `CreateOrderRequest`, the TypeScript type is automatically updated on the next `buf generate` run — accompanied by compile-time errors in the frontend code if it has not yet been updated to handle the new field.

## 6. Selective Builds in CI

CI is where the monorepo investment pays off:

```bash
# Build everything (used on the main branch, or after any change)
rush build

# Incremental: build only what is affected by this PR's changes
rush build --from packages/api-client  # Rebuild api-client and everything that depends on it
rush build --to apps/storefront         # Build only the storefront and its dependencies

# Example: a developer edits packages/utils/src/formatters.ts
# CI automatically detects that this change affects:
# - @composable/utils (the edited package)
# - @composable/api-client (imports utils for validation)
# - @composable/storefront (imports api-client)
# - @composable/admin-dashboard (imports api-client)
# Rush rebuilds and re-tests exactly these 4 packages and skips the rest
```

This matters enormously at scale: a change in `packages/ui-components/Button.tsx` must never trigger a rebuild of `packages/api-client` or `services/order-service`. Rush's dependency graph guarantees that it does not.

## 7. Strangler Fig for the Frontend

The Rush monorepo also implements the Strangler Fig pattern at the **frontend layer** — mirroring the backend migration phases from [Part 6](/series/composable-commerce-migration/part-6-phase1-strangler-fig/) through [Part 8](/series/composable-commerce-migration/part-8-phase3-full-cutover/).

During Phase 1 (the read-only cutover), the CDN configuration routes:

```
GET /products/*  → the new Next.js storefront (reads from the Catalog Service)
GET /checkout/*  → the Magento frontend (writes still flow into Magento)
POST /*          → the Magento frontend (all write traffic)
```

The Next.js storefront in `apps/storefront/` only serves the pages that have been migrated. Unmigrated routes fall through to a Magento reverse proxy. As the migration progresses through Phase 2 and Phase 3, more and more routes are directed to the new storefront — with no frontend rebuild or deployment required.

```typescript
// apps/storefront/next.config.ts
const nextConfig = {
  async rewrites() {
    return {
      fallback: [
        {
          source: "/:path*",
          destination: `${process.env.MAGENTO_URL}/:path*`, // Fallback route to Magento
        },
      ],
    };
  },
};
```

## 8. The Essential Rush Commands

```bash
# First-time setup
npm install -g @microsoft/rush
rush install         # Install all dependencies (pnpm)

# Development
rush build           # Build all packages in dependency order
rush test            # Test all packages
rush rebuild         # Force a full rebuild (bypasses the cache)
rush watch           # Watch mode for development

# Adding dependencies
rush add -p react --make-consistent          # Add to the current project + pin it globally
rush add -p @composable/utils --caret        # Add a dependency on an internal package

# Publishing
rush publish --apply --target-branch main   # Bump versions and publish

# Go services
rush build:go        # Build all 21 Go microservices
rush test:go         # Test all 21 Go microservices

# CI
rush build --to apps/storefront              # Build only what the storefront needs
rush build --from packages/api-client       # Build everything that consumes api-client
```

## 9. An Important Caveat

The Rush monorepo in this series describes the **recommended structure** for managing the frontend layer of the Composable Commerce platform. The backend Go architecture documents (`Composable-Commerce-Service-Architecture`) are extremely thorough — 24 ADRs, comprehensive API guidelines, and a migration playbook. The frontend monorepo configuration details, however, were inferred from the platform's overall design goals.

If you are implementing this model for your own migration, validate the `buf.gen.yaml` setup against your specific proto folder structure and the ConnectRPC version your team prefers. The structure is proven; the specific toolchain versions keep evolving.

## Next Steps

With the repository structure in place, we can dive into what an individual Go microservice looks like. [Part 3: Kratos v2 Internals](/series/composable-commerce-migration/part-3-golang-kratos/) dissects it all — from the 5-layer folder structure and Wire dependency injection to the shared `common` library that eliminates 4,150 lines of boilerplate across the 21 services.

## Frequently Asked Questions (FAQ)

### When is Rush a better choice than plain pnpm workspaces?

Use plain pnpm workspaces if you have 4 or fewer packages and no strict version governance requirements. Rush starts paying off from 5 packages upward, when you need `common-versions.json` enforcement (preventing one package from upgrading to the latest React while another stays stuck on an old version), the `rush publish` lifecycle, and project-level build caching. For this platform — 2 apps, 3 shared packages, 21 Go services — Rush's governance features are well worth it.

### Are the Go services part of Rush's project graph?

No. Rush only manages packages that have a `package.json`. The Go services live in the `services/` folder and are orchestrated via custom bulk commands in `rush.json` (shelling out to `go build ./...`). Rush tracks the Go build artifacts in its cache but does not parse `go.mod` or `go.sum` files. Go dependency management remains entirely the standard Go toolchain's responsibility.

### What happens if you skip `buf generate` after a proto file is modified?

The TypeScript SDK in `packages/api-client/generated/` goes stale. CI enforces freshness: if the generated files differ from the committed ones, the pipeline fails via `buf lint` + `buf generate --check`. This prevents the frontend from shipping with TypeScript types that no longer match the backend proto contract.

---

*This article is part of the **[Composable Commerce Migration Series](/series/composable-commerce-migration/)**. Check out the full table of contents for the complete architectural context.*

*Need help assessing the risks of an upcoming platform migration? → [Book a 1:1 Architecture Consultation](/hire/)*

---

---

---

[← Previous Chapter: Part 1: Decomposing Magento into 21 Services with DDD](/series/composable-commerce-migration/part-1-ddd-bounded-contexts/) | [Series Hub](/series/composable-commerce-migration/) | [Next Chapter: Part 3: Go + Kratos v2 Framework Deep Dive →](/series/composable-commerce-migration/part-3-golang-kratos/)
