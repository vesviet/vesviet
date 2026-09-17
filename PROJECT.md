# Project: GSC Coverage Audit and Technical Remediation (vesviet / tanhdev.com)

## Architecture
- **Platform**: Hugo (Extended v0.164.0) static site generator with PaperMod theme, hosted on Cloudflare Pages.
- **Domain Scope**: Primary domain `tanhdev.com`, secondary alias `www.tanhdev.com`. Excluded subdomains: `learn.tanhdev.com` (211 URLs), `it-tools.tanhdev.com` (23 URLs), `dw.tanhdev.com` (2 URLs), `donthan.tanhdev.com` (1 URL).
- **Routing Rules**:
  - `baseURL = "https://tanhdev.com/"`
  - `posts = "/posts/:slug/"`
  - `radar = "/radar/:sections[1]/:slug/"` (Canonical format `/radar/YYYY-MM/:slug/`)
  - `series = "/series/<series-slug>/<file-slug>/"`
- **Redirect Layer**:
  - Layer 1 (Static Cloudflare Pages): `vesviet/static/_redirects` (HTTP 301 rules for edge redirection).
  - Layer 2 (Hugo Native Fallback): Frontmatter `aliases: [...]` producing client refresh fallbacks via `layouts/alias.html`.
  - Parity requirement: 100% agreement between frontmatter aliases and `_redirects`.

## Feature Inventory
| # | Feature | Description | Milestone | Source | Status |
|---|---------|-------------|-----------|--------|--------|
| 1 | Archive Extraction & Schema Parsing | Extract 9 ZIP files from `tmp/`, parse CSV schemas (`Chart.csv`, `Table.csv`, `Metadata.csv`), reconcile 711 total rows / 500 non-learn URLs / 458 unique `tanhdev.com` URLs | M1 | ORIGINAL_REQUEST §R1 | DONE |
| 2 | 6 GSC Indexing Groups Classification | Classify URLs into 404 (101), Crawled Not Indexed (106), Excluded by Noindex (162), Redirects (69), Robots.txt (18), Canonical (2) | M1 | ORIGINAL_REQUEST §R1 | DONE |
| 3 | URL Pattern Clustering | Cluster URLs by `/radar/...`, `/series/...`, `/posts/...`, `/categories/...`, `/tags/...`, and legacy endpoints | M1 | ORIGINAL_REQUEST §R1 | DONE |
| 4 | 404 URL Ground-Truth Audit | Audit 101 404 URLs: 35 in both alias/redirect, 51 in redirect only, 15 unmitigated active 404s | M2 | ORIGINAL_REQUEST §R2 | DONE |
| 5 | Noindex & Robots.txt Root Cause Analysis | Analyze 163 noindex URLs (152 tags in head.html, 1 accidental noindex in `radar-2026-07-27.md`, 22 deprecated series parts) and 18 robots.txt blocks (15 historic tag crawls, 1 API, 2 RSS feeds) | M2 | ORIGINAL_REQUEST §R2 | DONE |
| 6 | Comprehensive Audit Report Generation | Publish complete report `vesviet/reports/GSC_INDEXING_AUDIT_2026_09_17.md` with Executive Summary, Matrix, 301 Mapping Table, Crawl Budget Strategy, Robots/Sitemap Recommendations | M3 | ORIGINAL_REQUEST §R3 | DONE |
| 7 | Hugo Aliases Frontmatter Patching | Patch frontmatter `aliases:` in content markdown files for 15 unmitigated 404s and backfill frontmatter aliases for 51 redirect-only URLs | M4 | ORIGINAL_REQUEST §R4 | DONE |
| 8 | Cloudflare `_redirects` Synchronization | Update `vesviet/static/_redirects` to ensure 100% parity with Hugo aliases and cover deleted/deprecated endpoints (328 clean rules) | M4 | ORIGINAL_REQUEST §R4 | DONE |
| 9 | Accidental Noindex Flag Removal | Remove `noindex: true` from `vesviet/content/radar/2026-07/radar-2026-07-27.md` | M4 | ORIGINAL_REQUEST §R4 | DONE |
| 10 | Redirect Oracle Test Portability Fix | Update `vesviet/tests/test_redirects_oracle.py` to use dynamic repo pathing instead of hardcoded `/home/user/personalized` | M4 | QA Exploration | DONE |
| 11 | Hugo Build Verification (`hugo --gc`) | Execute `hugo --gc` on `vesviet`, verifying exit code 0, no circular alias loops, and valid page generation (1316 pages, 1194 aliases) | M5 | Acceptance Criteria | DONE |
| 12 | Redirect Oracle Verification | Run `test_redirects_oracle.py` verifying 100% 404 coverage, alias parity, 0 loops, 0 chains, clean sitemap (23/23 PASSED) | M5 | Acceptance Criteria | DONE |
| 13 | Adversarial Cross-Domain Audit | Run `node tests/adversarial-audit.mjs` ensuring zero regressions | M5 | Acceptance Criteria | DONE |
| 14 | Forensic Audit Integrity Gate | Independent audit verifying authentic implementation without cheating, hardcoding, or facades (Verdict: CLEAN) | M5 | Acceptance Criteria | DONE |

## Milestones
| # | Name | Scope | Dependencies | Status | Key Outputs |
|---|------|-------|-------------|--------|-------------|
| M1 | Data Extraction & Classification (R1) | Build parsing script, extract 9 zips from `tmp/`, filter domains, classify 500 URLs into 6 groups, output structured JSON dataset | Survey | DONE | `vesviet/scripts/extract_gsc_data.py`, `vesviet/data/gsc_audit_dataset_2026_09_17.json` |
| M2 | Ground-Truth Cross-Referencing (R2) | Map 101 404s against `content/`, verify 163 noindex URLs, verify 18 robots.txt blocks, produce complete 301 redirection & remediation spec | M1 | DONE | Documented in Section 2 of audit report and explorer handoffs |
| M3 | Comprehensive Audit Report Publication (R3) | Author `vesviet/reports/GSC_INDEXING_AUDIT_2026_09_17.md` with executive summary, 6-group matrix, 301 mapping table, crawl budget & content strategy, robots/sitemap recommendations | M2 | DONE | `vesviet/reports/GSC_INDEXING_AUDIT_2026_09_17.md` (48.8 KB, 425 lines) |
| M4 | Technical Remediation (R4) | Patch frontmatter aliases, sync `static/_redirects`, remove accidental `noindex: true`, fix `test_redirects_oracle.py` portability | M2 | DONE | 18 content markdown files patched, `static/_redirects` (328 rules), `tests/test_redirects_oracle.py` |
| M5 | E2E Verification & Adversarial Audit | Execute `hugo --gc`, run `test_redirects_oracle.py`, run `challenger_redirect_oracle.py`, independent Review, Challenge, and Forensic Audit | M3, M4 | DONE | Gate Result: PASS; Auditor: CLEAN; Reviewers: APPROVE; Challengers: APPROVE |

## Code Layout
- `vesviet/content/radar/`: Tech radar issues organized by `YYYY-MM/`
- `vesviet/content/posts/`: Technical deep dive articles
- `vesviet/content/series/`: Multi-part engineering series
- `vesviet/static/_redirects`: Cloudflare Pages 301 redirect map (328 active rules, 0 loops, 0 chains)
- `vesviet/static/robots.txt`: Production robots.txt (verified safe and intentional)
- `vesviet/layouts/partials/head.html`: Robots meta tag generation logic
- `vesviet/layouts/sitemap.xml`: XML sitemap template (verified clean, 0 redirect leaks, 0 noindex leaks)
- `vesviet/reports/GSC_INDEXING_AUDIT_2026_09_17.md`: Official audit report deliverable
- `vesviet/scripts/extract_gsc_data.py`: GSC ZIP extraction and dataset parsing tool
- `vesviet/data/gsc_audit_dataset_2026_09_17.json`: Extracted structured GSC dataset
- `vesviet/tests/test_redirects_oracle.py`: Empirical redirect and GSC coverage test harness
- `tests/adversarial-audit.mjs`: Workspace-level adversarial cross-domain test harness
- `tests/challenger_redirect_oracle.py`: Independent adversarial redirect graph stress-test harness
