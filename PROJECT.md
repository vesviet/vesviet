# Project: tanhdev.com Posts SEO & Content Quality Audit Sprint

## Architecture & Content Layout
- **Website URL**: https://tanhdev.com/
- **SSG**: Hugo (with PaperMod theme)
- **Deployment Platform**: Cloudflare Pages
- **Content Hierarchy**:
  - `content/posts/` — Individual long-form posts (58 files). Enforces a 1,400+ words SEO baseline.
  - `content/series/` — Curriculum-based, multi-part tutorials grouped under directories (e.g. `agentic-ecommerce-search/`).
  - `content/radar/` — Tech updates and short architectural radars.
  - `content/reading-map.md` — Site index grouping 57 published essays into content pillars.
- **Config & Infrastructure**:
  - `hugo.toml` — Permalinks formatted with trailing slashes `/posts/:slug/`. Custom outputs configured for `llms.txt` and `llms-full.txt`.
  - `static/robots.txt` — Grants indexing access to AI bots (GPTBot, ClaudeBot, PerplexityBot) while blocking scraping search bots.
  - `static/_headers` — Exposes caching rules for static resources.

## Detailed Milestones

| Milestone | Name | Objective | Scope | Status |
| --- | --- | --- | --- | --- |
| **M1** | Discovery & Setup | Verify file directories, index canonicals/slugs, analyze guidelines and previous reports. | `/content/posts/`, `_internal/` | **COMPLETE** |
| **M2** | Technical Scan Execution | Implement and execute programmatic script checking for word counts, Mojibake patterns, broken internal links, and TOC status. | `verify_posts.py`, `/content/posts/` | PLANNED |
| **M3** | Content Quality & E-E-A-T | Scan Answer-First placement, verify placeholders (FAQs, boilerplate templates), audit schema integration and E-E-A-T signals. | `/content/posts/`, `layouts/` | PLANNED |
| **M4** | Report Consolidation | Consolidate technical and quality findings into single source of truth report markdown files. | `/posts_audit_report.md`, `/seo_audit_report.md` | PLANNED |
| **M5** | Independent Review | Run review passes to verify E-E-A-T compliance and test implementation solutions. | `/plan/baiviet/publish-log.md` | PLANNED |

## Interface Contracts & Schemas

### 1. `seo-audit-report.json`
Specifies metadata validation results for individual pages, ensuring Answer-First formatting, proper keyword clustering, and technical search visibility.
```json
{
  "document_path": "string",
  "audit_type": "string (post_draft_pre_publish | repository_wide)",
  "keywords": {
    "primary": "string",
    "secondary": ["string"]
  },
  "geo_aeo_execution": {
    "answer_first_structure": "string (Pass/Fail status)",
    "query_fan_out": "string",
    "fact_density": "string",
    "ai_extractability": "string"
  },
  "topical_authority": {
    "information_gain": "string",
    "cluster_position": "string (pillar | supporting)",
    "pillar_page": "string"
  },
  "issues": [
    {
      "severity": "string (Low | Medium | High)",
      "category": "string",
      "finding": "string",
      "recommendation": "string"
    }
  ],
  "technical_escalations": [
    {
      "owner": "string",
      "task": "string"
    }
  ],
  "next_steps": "string"
}
```

### 2. `internal-link-audit.json`
Ensures crawler link flow, identifying dead-ends, orphans, and broken links across the posts directory.
```json
{
  "stats": {
    "total_pages": "integer",
    "total_links": "integer",
    "avg_outbound": "float",
    "avg_inbound": "float"
  },
  "orphans": ["string (filenames/slugs)"],
  "dead_ends": ["string (filenames/slugs)"],
  "top_linked_pages": [["string", "integer"]],
  "top_linking_pages": [["string", "integer"]],
  "detailed_nodes": {
    "slug": {
      "type": "string (posts | series | radar)",
      "inbound_count": "integer",
      "outbound_count": "integer"
    }
  }
}
```
