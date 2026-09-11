# Comprehensive Content Index & Audit Report: Prompt Standard Series
**Generated Date**: 2026-09-11
**Standards Adhered**: Technical Article Standard 2027 (8 gates), PromptOps 2026 (Context engineering, 8 core blocks, Layered stacks, MCP + Hybrid RAG, DSPy compilation, PromptOps CI/CD, OWASP Top 10 for LLMs / ASI).
**Sync Campaign**: `series-sync-upgrade` workflow — 100 deep-research rounds per part (10 dossiers = 1,000 rounds), synchronized across `vesviet` (English, tanhdev.com) and `learn` (Vietnamese, learn.tanhdev.com) with 1:1 symmetric twin parity.

---

## 1. Series Architecture & Twin Parity Overview

The `prompt-standard` series is structured with **1:1 Symmetric Twin Parity** across both repositories:

- **vesviet (English, tanhdev.com)**: Hub `_index.md` + 10 chapters (`executive-summary.md` + `part-1` through `part-9`).
- **learn (Vietnamese, learn.tanhdev.com)**: Hub `_index.md` + 10 chapters (`executive-summary.md` + `part-1` through `part-9`).
- **One-Way Authority Rule**: ZERO links from `vesviet` to `learn.tanhdev.com` (no reverse links or Vietnamese badges). All `learn` chapters link up to canonical `tanhdev.com` chapters via the `Bản tiếng Anh` navigation badge.

---

## 2. vesviet Content Metrics & Gate Compliance (English)

Words = body word count · M = fenced Mermaid diagrams · FAQ = `{{< faq >}}` components · AF = Answer-first words.

| File (slug) | Wt | Size (KB) | Words | M | FAQ | AF Words | Prereq | VI Twin Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_index.md` | 100 | 7.23 | 832 | 1 | 3 | 55 | N/A | 1:1 Hub Parity |
| `executive-summary.md` | 1 | 22.88 | 3,190 | 2 | 5 | 55 | PASS | 1:1 Twin Parity |
| `part-1-what-is-prompt-standard.md` | 2 | 23.06 | 3,242 | 2 | 5 | 54 | PASS | 1:1 Twin Parity |
| `part-2-core-blocks.md` | 3 | 23.69 | 3,189 | 2 | 4 | 50 | PASS | 1:1 Twin Parity |
| `part-3-layered-prompt-design.md` | 4 | 21.75 | 2,928 | 2 | 5 | 52 | PASS | 1:1 Twin Parity |
| `part-4-versioning-and-evals.md` | 5 | 21.74 | 2,825 | 2 | 5 | 53 | PASS | 1:1 Twin Parity |
| `part-5-team-template.md` | 6 | 21.98 | 3,092 | 2 | 4 | 51 | PASS | 1:1 Twin Parity |
| `part-6-context-engineering.md` | 7 | 22.15 | 2,846 | 3 | 5 | 51 | PASS | 1:1 Twin Parity |
| `part-7-declarative-prompting-dspy.md` | 8 | 21.33 | 2,761 | 2 | 5 | 55 | PASS | 1:1 Twin Parity |
| `part-8-production-promptops.md` | 9 | 20.53 | 2,522 | 2 | 4 | 52 | PASS | 1:1 Twin Parity |
| `part-9-mcp-and-hybrid-rag.md` | 10 | 21.39 | 2,803 | 2 | 5 | 58 | PASS | 1:1 Twin Parity |

**Audit Result**: 10/10 chapters pass 100% of the 8 gates (>20 KB, ≥2,500 words, Answer-first 50–60 words single line, Prerequisite block, ≥2 Mermaid diagrams, ≥3 FAQs, production code, zero links to `learn.tanhdev.com`).

---

## 3. Deep Research Dossiers (100 Rounds per Part = 1,000 Rounds)

Mirrored in `vesviet/reports/` and `learn/reports/`. All 10 JSON dossiers validated with `jsonschema.Draft202012Validator` against `agent-skills/core/contracts/schemas/research-report.json` with 0 schema violations.

1. `research-prompt-standard-executive-summary-100-rounds.json` & `.md`
2. `research-prompt-standard-part-1-what-is-prompt-standard-100-rounds.json` & `.md`
3. `research-prompt-standard-part-2-core-blocks-100-rounds.json` & `.md`
4. `research-prompt-standard-part-3-layered-prompt-design-100-rounds.json` & `.md`
5. `research-prompt-standard-part-4-versioning-and-evals-100-rounds.json` & `.md`
6. `research-prompt-standard-part-5-team-template-100-rounds.json` & `.md`
7. `research-prompt-standard-part-6-context-engineering-100-rounds.json` & `.md`
8. `research-prompt-standard-part-7-declarative-prompting-dspy-100-rounds.json` & `.md`
9. `research-prompt-standard-part-8-production-promptops-100-rounds.json` & `.md`
10. `research-prompt-standard-part-9-mcp-and-hybrid-rag-100-rounds.json` & `.md`

---

## 4. Edge Redirects & Oracle Test Status

- **Rules in `vesviet/static/_redirects`**: All legacy and non-canonical slugs redirected via 301 rules.
- **Oracle Test**: `python3 vesviet/tests/test_redirects_oracle.py` executes with **23 PASSED, 0 FAILED, 0 WARNINGS**.
- **No Self-Loops & No Redirect Chains**: 100% 1-hop redirects verified.
- **Destination Verification**: 100% of internal redirect targets exist on disk.

---

## 5. Campaign Verification Checklist

- [x] All 10 chapters ≥2,500 words, >20 KB, ≥2 AST-valid Mermaid, ≥3 FAQ, Answer-first single line (50–60 words), Prerequisite block
- [x] Weights sequential 1–10, 1:1 twin slug parity with Vietnamese repo
- [x] Zero links from `vesviet` to `learn.tanhdev.com` (no reverse badges or cross-linking)
- [x] Canonical URLs anchored strictly on `tanhdev.com`
- [x] Hugo build `--minify -s vesviet`: 0 errors (1,278 pages built)
- [x] Redirects oracle test: 23/23 tests passed
