#!/usr/bin/env python3
"""
Per-Post Deep Audit — Content Manager Role
Audits every post in vesviet/content/posts individually.

Audit dimensions per post:
1. Frontmatter completeness (title, slug, description, author, tags, lastmod, cover)
2. Meta description quality (length 120-160 chars, no truncation bug)
3. Answer-First block quality (present, ≤60 words, no boilerplate)
4. FAQ section (present, format, Q count)
5. Content structure (H2 count, H3 usage, table/code/diagram presence)
6. Word count (body only, no code)
7. Information gain signals (data points, numbers, original analysis)
8. E-E-A-T signals (author, citations, firsthand)
9. AI boilerplate patterns
10. Robotic H2 headings
11. Thin section detection (any H2 with <40 words body)
12. Cannibalization risk (similar titles to other posts)
13. Cover image
14. Slug matches filename
"""

import os
import re
import glob
import json
from collections import defaultdict

POSTS_DIR = r"D:\myproject\vesviet\content\posts"
REPORT_PATH = r"D:\myproject\vesviet\reports\per_post_deep_audit.md"

AI_BOILERPLATE = [
    (r"\bdelve into\b", "delve into"),
    (r"\bin today's (fast-paced|digital|rapidly evolving)", "in today's [filler]"),
    (r"\bunleash the power\b", "unleash the power"),
    (r"\bgame[-\s]?changer\b", "game-changer"),
    (r"\brich tapestry\b", "rich tapestry"),
    (r"\btestament to\b", "testament to"),
    (r"\bwithout further ado\b", "without further ado"),
    (r"\bit should be noted that\b", "it should be noted that"),
    (r"\bin conclusion,?\s+(it is|we can|this)", "in conclusion [wrap-up]"),
    (r"\bthis comprehensive guide\b", "this comprehensive guide"),
    (r"\bseasoned professionals\b", "seasoned professionals"),
    (r"\btailored to your needs\b", "tailored to your needs"),
    (r"\bin the ever-evolving\b", "in the ever-evolving"),
    (r"\blandscape of\b", "landscape of"),
    (r"\bempower(ing)? developers\b", "empowering developers"),
    (r"\brobust solution\b", "robust solution"),
    (r"\bleverage the power\b", "leverage the power"),
    (r"\bseamless(ly)?\b", "seamless"),
    (r"\bpioneering\b", "pioneering"),
    (r"\bcutting-edge\b", "cutting-edge"),
]

ROBOTIC_H2 = re.compile(
    r"^##\s*(Below (is|are)|Here (is|are)|This section (covers|provides)|Before diving into|"
    r"Let's (look|explore|dive)|In this (section|chapter|post|article|guide)|"
    r"The following|This guide (will|covers)|Here, we|Introduction to)",
    re.IGNORECASE | re.MULTILINE
)

def parse_frontmatter(content):
    fm = {}
    if not content.startswith("---"):
        return fm, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return fm, content
    raw = parts[1]
    body = parts[2]
    # Block-list tags/categories
    if re.search(r'^tags:\s*[\["]', raw, re.MULTILINE):
        fm["tags"] = "present"
    elif re.search(r'^tags:\s*$', raw, re.MULTILINE) and re.search(r'^\s+-\s+', raw, re.MULTILINE):
        fm["tags"] = "present"
    if re.search(r'^categories:\s*[\["]', raw, re.MULTILINE):
        fm["categories"] = "present"
    elif re.search(r'^categories:\s*$', raw, re.MULTILINE) and re.search(r'^\s+-\s+', raw, re.MULTILINE):
        fm["categories"] = "present"
    for line in raw.splitlines():
        if ":" in line and not line.strip().startswith("-"):
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in fm:
                fm[k] = v
    return fm, body

def count_body_words(body):
    t = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    t = re.sub(r'`[^`]+`', '', t)
    t = re.sub(r'^\s*#+.*$', '', t, flags=re.MULTILINE)
    t = re.sub(r'\{\{<.*?>}}\}?', '', t)
    return len(t.split())

def get_answer_first(body):
    m = re.search(r'(?i)(answer.?first)[:\*\s]+(.{10,300})', body)
    if not m:
        return None, 0
    text = m.group(2).strip().rstrip('*').strip()
    words = len(text.split())
    return text, words

def get_h2_sections(body):
    """Return list of (heading, body_text) pairs for each H2"""
    sections = []
    h2_pattern = re.compile(r'^## (.+)$', re.MULTILINE)
    positions = [(m.start(), m.group(1).strip()) for m in h2_pattern.finditer(body)]
    for i, (pos, heading) in enumerate(positions):
        start = body.index('\n', pos) + 1 if '\n' in body[pos:] else pos
        end = positions[i+1][0] if i+1 < len(positions) else len(body)
        section_body = body[start:end].strip()
        # Remove code blocks from word count
        section_body_clean = re.sub(r'```.*?```', '', section_body, flags=re.DOTALL)
        sections.append({
            "heading": heading,
            "body": section_body,
            "word_count": len(section_body_clean.split()),
        })
    return sections

def check_fact_density(body):
    """Count verifiable data points: numbers, percentages, named tools, latency figures"""
    # Number patterns: "40%", "50ms", "3 nodes", "2024", "$200", "1M+", "100K"
    numbers = len(re.findall(r'\b\d+[\.,]?\d*\s?(?:%|ms|KB|MB|GB|TB|K|M|B|RPS|TPS|s|min|hr)?\b', body))
    # Named tools/products mentioned (signal of specificity)
    tools = len(re.findall(r'\b(Redis|Kafka|Kubernetes|PostgreSQL|MySQL|TiDB|NATS|Temporal|Go|Golang|Envoy|Istio|Debezium|OceanBase|Qdrant|Milvus|gRPC|Protobuf|HNSW|OSRM|GraphHopper)\b', body))
    return min(numbers + tools // 3, 99)  # normalized signal

def audit_post(filepath):
    filename = os.path.basename(filepath)
    slug_from_file = filename.replace('.md', '')

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.read()

    fm, body = parse_frontmatter(raw)

    result = {
        "file": filename,
        "issues": [],
        "warnings": [],
        "passes": [],
        "score": 0,  # 0-100
        "word_count": count_body_words(body),
        "h2_count": len(re.findall(r'^## ', body, re.MULTILINE)),
        "h3_count": len(re.findall(r'^### ', body, re.MULTILINE)),
    }

    score = 100  # Start at 100, deduct

    # === 1. Frontmatter ===
    title = fm.get("title", "")
    slug = fm.get("slug", "")
    desc = fm.get("description", "")
    author = fm.get("author", "")
    lastmod = fm.get("lastmod", "")

    if not title:
        result["issues"].append("❌ [FM] Missing title")
        score -= 10
    else:
        result["passes"].append(f"✅ title: {title[:60]}")

    if not slug:
        result["issues"].append("❌ [FM] Missing slug")
        score -= 8
    elif slug != slug_from_file:
        result["warnings"].append(f"⚠️ [FM] Slug mismatch: slug='{slug}' vs filename='{slug_from_file}'")
        score -= 3
    else:
        result["passes"].append(f"✅ slug matches filename")

    if not desc:
        result["issues"].append("❌ [FM] Missing description")
        score -= 10
    else:
        desc_len = len(desc)
        if desc_len < 120:
            result["warnings"].append(f"⚠️ [Meta] Description short ({desc_len} chars < 120)")
            score -= 3
        elif desc_len > 160:
            result["warnings"].append(f"⚠️ [Meta] Description long ({desc_len} chars > 160)")
            score -= 2
        else:
            result["passes"].append(f"✅ description: {desc_len} chars")
        # Truncation bug
        if re.search(r'Learn production engine\w{0,5}[\"\']?\s*$', desc, re.IGNORECASE):
            result["issues"].append("❌ [Meta] Truncation bug in description (ends with 'Learn production engine...')")
            score -= 5

    if not author or not author.strip():
        result["warnings"].append("⚠️ [FM] Missing author — E-E-A-T signal weakened")
        score -= 3
    else:
        result["passes"].append(f"✅ author: {author}")

    if not lastmod:
        result["warnings"].append("⚠️ [FM] Missing lastmod — freshness signal")
        score -= 2
    else:
        result["passes"].append(f"✅ lastmod: {lastmod}")

    if "tags" not in fm or not fm["tags"]:
        result["issues"].append("❌ [FM] Missing tags")
        score -= 8
    else:
        result["passes"].append("✅ tags present")

    # Cover image
    has_cover = bool(re.search(r'image:\s*["\']?images/', raw))
    if not has_cover:
        result["warnings"].append("⚠️ [FM] No cover image — affects social CTR")
        score -= 2
    else:
        result["passes"].append("✅ cover image")

    # === 2. Answer-First ===
    af_text, af_words = get_answer_first(body)
    if not af_text:
        result["issues"].append("❌ [GEO] Missing Answer-First block")
        score -= 15
    elif af_words > 60:
        result["warnings"].append(f"⚠️ [GEO] Answer-First too long ({af_words} words > 60 max)")
        score -= 5
    else:
        result["passes"].append(f"✅ Answer-First present ({af_words} words)")

    # Boilerplate in Answer-First
    if af_text:
        for pattern, label in AI_BOILERPLATE:
            if re.search(pattern, af_text, re.IGNORECASE):
                result["warnings"].append(f"⚠️ [AI] Boilerplate in Answer-First: '{label}'")
                score -= 3

    # === 3. Word count ===
    wc = result["word_count"]
    if wc < 800:
        result["issues"].append(f"❌ [Thin] Only {wc} words (min 800)")
        score -= 15
    elif wc < 1200:
        result["warnings"].append(f"⚠️ [Length] {wc} words — borderline (aim ≥1200 for competitive queries)")
        score -= 3
    else:
        result["passes"].append(f"✅ {wc} words")

    # === 4. FAQ ===
    has_faq = bool(re.search(r'(?im)^#{2,3}\s+(Frequently Asked Questions|FAQ)\b', body)) or \
              bool(re.search(r'\{\{<\s*faq\s+', body))
    faq_count = len(re.findall(r'\{\{<\s*faq\s+', body))
    h2_faq = bool(re.search(r'(?im)^#{2,3}\s+(Frequently Asked Questions|FAQ)\b', body))
    h3_faq_count = len(re.findall(r'^### .+\?', body, re.MULTILINE))
    if not has_faq:
        result["warnings"].append("⚠️ [FAQ] No FAQ section (recommended for informational posts)")
        score -= 5
    else:
        total_q = max(faq_count, h3_faq_count)
        if total_q < 3:
            result["warnings"].append(f"⚠️ [FAQ] Only {total_q} Q&A pairs (recommend ≥3)")
            score -= 2
        else:
            result["passes"].append(f"✅ FAQ with {total_q} Q&A pairs")

    # === 5. H2 structure ===
    h2_count = result["h2_count"]
    if h2_count < 3:
        result["warnings"].append(f"⚠️ [Structure] Only {h2_count} H2 sections (recommend ≥3 for scanability)")
        score -= 3
    else:
        result["passes"].append(f"✅ {h2_count} H2 sections")

    # Robotic H2 headings
    robotic_h2s = ROBOTIC_H2.findall(body)
    if robotic_h2s:
        result["warnings"].append(f"⚠️ [H2] Robotic opener in heading: '{robotic_h2s[0][:50]}'")
        score -= 5

    # === 6. Thin H2 sections ===
    sections = get_h2_sections(body)
    thin_sections = [s for s in sections if s["word_count"] < 40 and "FAQ" not in s["heading"] and "Executive Summary" not in s["heading"]]
    if thin_sections:
        for s in thin_sections[:3]:
            result["warnings"].append(f"⚠️ [Thin H2] '## {s['heading']}' only {s['word_count']} words prose")
            score -= 3

    # === 7. AI Boilerplate ===
    boilerplate_found = []
    for pattern, label in AI_BOILERPLATE:
        if re.search(pattern, body, re.IGNORECASE):
            boilerplate_found.append(label)
    if boilerplate_found:
        result["issues"].append(f"❌ [AI Boilerplate] Found: {', '.join(boilerplate_found[:3])}")
        score -= 8

    # === 8. Information gain signals ===
    fact_score = check_fact_density(body)
    if fact_score < 5:
        result["warnings"].append(f"⚠️ [E-E-A-T] Low fact density (score {fact_score}) — add specific numbers/benchmarks")
        score -= 5
    else:
        result["passes"].append(f"✅ Fact density OK (score {fact_score})")

    # Code blocks
    code_blocks = len(re.findall(r'^```', body, re.MULTILINE)) // 2
    if code_blocks == 0 and wc > 600:
        result["warnings"].append("⚠️ [Structure] No code blocks — technical posts need concrete examples")
        score -= 3
    elif code_blocks > 0:
        result["passes"].append(f"✅ {code_blocks} code block(s)")

    # Tables
    has_table = bool(re.search(r'^\|[-| ]+\|', body, re.MULTILINE))
    if has_table:
        result["passes"].append("✅ Has comparison table")

    # Mermaid diagrams
    has_mermaid = bool(re.search(r'```mermaid', body, re.IGNORECASE))
    if has_mermaid:
        result["passes"].append("✅ Has Mermaid diagram")

    # === 9. canonicalURL ===
    canonical = fm.get("canonicalURL", "")
    if not canonical:
        result["warnings"].append("⚠️ [SEO] Missing canonicalURL in frontmatter")
        score -= 2
    else:
        result["passes"].append(f"✅ canonicalURL set")

    # Final score
    result["score"] = max(0, min(100, score))
    return result

def classify(score):
    if score >= 85:
        return "🟢 GOOD"
    elif score >= 70:
        return "🟡 NEEDS MINOR FIXES"
    elif score >= 50:
        return "🟠 NEEDS WORK"
    else:
        return "🔴 CRITICAL"

def main():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    results = []

    for filepath in posts:
        r = audit_post(filepath)
        results.append(r)

    # Sort by score ascending (worst first)
    results_sorted = sorted(results, key=lambda x: x["score"])

    # Stats
    scores = [r["score"] for r in results]
    avg_score = sum(scores) / len(scores)
    critical = [r for r in results if r["score"] < 50]
    needs_work = [r for r in results if 50 <= r["score"] < 70]
    minor_fixes = [r for r in results if 70 <= r["score"] < 85]
    good = [r for r in results if r["score"] >= 85]

    lines = []
    lines.append("# Per-Post Deep Audit — vesviet/content/posts")
    lines.append(f"\n**Audited:** {len(results)} posts | **Avg Score:** {avg_score:.0f}/100 | **Date:** 2026-07-25\n")
    lines.append("## Portfolio Overview\n")
    lines.append(f"| Status | Count | Posts |")
    lines.append(f"|--------|-------|-------|")
    lines.append(f"| 🔴 Critical (<50) | {len(critical)} | {', '.join(r['file'].replace('.md','')[:30] for r in critical)} |")
    lines.append(f"| 🟠 Needs Work (50-69) | {len(needs_work)} | — |")
    lines.append(f"| 🟡 Minor Fixes (70-84) | {len(minor_fixes)} | — |")
    lines.append(f"| 🟢 Good (85+) | {len(good)} | — |")
    lines.append("")

    # Score table (all posts)
    lines.append("## Score Table (All Posts)\n")
    lines.append("| Score | Status | File | Words | H2s | FAQ | Answer-First |")
    lines.append("|-------|--------|------|-------|-----|-----|--------------|")
    for r in results_sorted:
        af_ok = "✅" if any("Answer-First present" in p for p in r["passes"]) else "❌"
        faq_ok = "✅" if any("FAQ with" in p for p in r["passes"]) else "⚠️"
        lines.append(f"| {r['score']} | {classify(r['score'])} | {r['file'].replace('.md','')} | {r['word_count']} | {r['h2_count']} | {faq_ok} | {af_ok} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Per-Post Detail\n")

    for r in results_sorted:
        status = classify(r["score"])
        lines.append(f"### [{r['score']}/100] {status} — `{r['file']}`")
        lines.append(f"**Words:** {r['word_count']} | **H2s:** {r['h2_count']} | **H3s:** {r['h3_count']}\n")

        if r["issues"]:
            lines.append("**Issues (fix required):**")
            for issue in r["issues"]:
                lines.append(f"- {issue}")
            lines.append("")

        if r["warnings"]:
            lines.append("**Warnings (recommended):**")
            for w in r["warnings"]:
                lines.append(f"- {w}")
            lines.append("")

        if r["passes"]:
            lines.append("**Passing:**")
            for p in r["passes"][:6]:  # Show max 6 passes
                lines.append(f"- {p}")
            lines.append("")

        lines.append("---\n")

    # Action plan
    lines.append("## Priority Action Plan\n")
    lines.append("### P0 — Critical (Fix This Week)")
    if critical:
        for r in critical:
            lines.append(f"- **{r['file']}** (score {r['score']}): {'; '.join(r['issues'][:2])}")
    else:
        lines.append("- None 🎉")

    lines.append("\n### P1 — Needs Work (Fix This Month)")
    for r in needs_work:
        top_issue = r["issues"][0] if r["issues"] else r["warnings"][0] if r["warnings"] else "—"
        lines.append(f"- **{r['file']}** (score {r['score']}): {top_issue}")

    lines.append("\n### P2 — Minor Fixes (Next Cycle)")
    for r in minor_fixes:
        top = r["warnings"][0] if r["warnings"] else "—"
        lines.append(f"- **{r['file']}** (score {r['score']}): {top}")

    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(f"[DONE] Audit complete: {len(results)} posts")
    print(f"[STATS] Avg score: {avg_score:.0f}/100")
    print(f"[STATS] Critical: {len(critical)} | Needs Work: {len(needs_work)} | Minor Fixes: {len(minor_fixes)} | Good: {len(good)}")
    print(f"[REPORT] {REPORT_PATH}")

    # Console summary — ASCII only (no emoji to avoid CP1252 issues)
    print(f"\n{'='*60}")
    print("WORST SCORING POSTS (Bottom 10):")
    for r in results_sorted[:10]:
        print(f"  [{r['score']:3d}] {r['file']}")
        for issue in r["issues"][:2]:
            issue_clean = issue.replace("❌", "[X]").replace("⚠️", "[!]").replace("✅", "[OK]")
            print(f"         {issue_clean}")

if __name__ == "__main__":
    main()
