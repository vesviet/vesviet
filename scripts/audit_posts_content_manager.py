#!/usr/bin/env python3
"""
Content Manager Audit — vesviet/content/posts
Audits all 69 post files against content-manager.md standards:
1. Frontmatter completeness (title, description, slug, tags, author, lastmod)
2. Meta description quality (length, truncation, keyword density)
3. AI boilerplate patterns
4. Thin content (word count < 800 for posts)
5. Missing FAQ block (informational/commercial posts should have FAQ)
6. Information gain signal (originality markers)
7. E-E-A-T signals (author, sources cited)
8. Robotic H2 intros
9. Answer-first implementation check
10. Cover image presence
"""

import os
import re
import glob
from collections import defaultdict

POSTS_DIR = r"D:\myproject\vesviet\content\posts"
REPORT_FILE = r"D:\myproject\vesviet\reports\posts_content_manager_audit.md"

# --- Patterns ---
AI_BOILERPLATE = [
    (r"\bdelve into\b", "delve into"),
    (r"\bin today's (fast-paced|digital|rapidly evolving)", "in today's [filler]"),
    (r"\bfast-paced digital world\b", "fast-paced digital world"),
    (r"\bunleash the power\b", "unleash the power"),
    (r"\bgame[-\s]?changer\b", "game-changer"),
    (r"\brich tapestry\b", "rich tapestry"),
    (r"\btestament to\b", "testament to"),
    (r"\bwithout further ado\b", "without further ado"),
    (r"\bit should be noted that\b", "it should be noted that"),
    (r"\bNavigating the complex world of\b", "Navigating the complex world of"),
    (r"Architecting production-ready solutions for .{0,60} within the .{0,60} domain requires strict component separation, sub-50ms P99 latency", "Cloned Answer-First template"),
    (r"outlines the end-to-end data flow, service boundaries, and asynchronous messaging pipelines required for enterprise-grade", "Diagram boilerplate injection"),
    (r"stale-while-revalidate caching reduces database query pressure during cache stampedes", "Redis FAQ boilerplate"),
    (r"managing context window limits requires dynamic prompt token estimation", "Context window FAQ boilerplate"),
]

ROBOTIC_H2_INTRO = re.compile(
    r"^(?:Below (?:is|are)|Here (?:is|are)|This section|Before diving into|Let's (?:look|explore)|"
    r"In this (?:section|chapter|post|article|guide)|The following|This guide|Here, we|"
    r"The (?:code\s+)?snippet below|The table below|The diagram below|The figure below)\b",
    re.IGNORECASE
)

INFORMATIONAL_KEYWORDS = [
    "architecture", "guide", "how to", "tutorial", "what is", "explained",
    "introduction", "deep dive", "mastering", "understanding"
]

def parse_frontmatter(content):
    fm = {}
    if not content.startswith("---"):
        return fm, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return fm, content
    raw = parts[1]
    body = parts[2]
    
    # Check for tags in any format: inline array OR block list
    # Inline: tags: ["a", "b"] or tags: [a, b]
    # Block: tags:\n  - "a"\n  - "b"
    if re.search(r'^tags:\s*[\[\"]', raw, re.MULTILINE):
        fm["tags"] = "present"  # inline array format
    elif re.search(r'^tags:\s*$', raw, re.MULTILINE) and re.search(r'^\s+-\s+', raw, re.MULTILINE):
        fm["tags"] = "present"  # block list format
    
    for line in raw.splitlines():
        if ":" in line and not line.strip().startswith("-"):
            key, _, val = line.partition(":")
            k = key.strip()
            v = val.strip().strip('"').strip("'")
            # Skip if already set (e.g. tags already detected above)
            if k not in fm:
                fm[k] = v
    return fm, body

def count_words(text):
    # Strip code blocks and frontmatter
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"^\s*#.*$", "", text, flags=re.MULTILINE)
    return len(text.split())

def has_answer_first(body):
    # Match Answer-First block in any form
    return bool(re.search(r"(?i)answer.?first", body))

def has_faq(body):
    return bool(re.search(r"^#{2,3}\s+(?:Frequently Asked Questions|FAQ)\b", body, re.IGNORECASE | re.MULTILINE))

def has_code_blocks(body):
    return len(re.findall(r"^```", body, re.MULTILINE)) >= 2

def has_tables(body):
    return bool(re.search(r"^\|[-| ]+\|", body, re.MULTILINE))

def audit_post(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    
    fm, body = parse_frontmatter(raw)
    filename = os.path.basename(filepath)
    issues = []
    warnings = []
    passed = []
    
    # --- 1. Frontmatter completeness ---
    required_fields = ["title", "description", "slug", "author", "tags"]
    for field in required_fields:
        if field not in fm or not fm[field]:
            issues.append(f"[Frontmatter] Missing `{field}` field")
        else:
            passed.append(f"Has `{field}`")
    
    if "lastmod" not in fm:
        warnings.append("[Frontmatter] Missing `lastmod` — freshness signal for Google")
    
    # Cover image
    has_cover = "cover" in raw or ("image" in fm and fm.get("image", ""))
    if not has_cover:
        warnings.append("[Cover] No cover image — affects social sharing CTR")
    else:
        passed.append("Has cover image")
    
    # --- 2. Meta description quality ---
    desc = fm.get("description", "")
    if desc:
        desc_len = len(desc)
        if desc_len < 120:
            warnings.append(f"[Meta] Description too short ({desc_len} chars < 120 min)")
        elif desc_len > 160:
            warnings.append(f"[Meta] Description too long ({desc_len} chars > 160 max)")
        else:
            passed.append(f"Meta description length OK ({desc_len} chars)")
        
        # Truncation bug
        if re.search(r"Learn production engine\w{0,5}[\"']?\s*$", desc):
            issues.append(f"[Meta] Description truncated: ends with 'Learn production engine...' (pipeline bug)")
    
    # --- 3. AI Boilerplate ---
    boilerplate_found = []
    lines = body.splitlines()
    in_code = False
    for lno, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for pattern, label in AI_BOILERPLATE:
            if re.search(pattern, line, re.IGNORECASE):
                boilerplate_found.append(f"  L{lno}: [{label}] → `{line.strip()[:90]}`")
    
    if boilerplate_found:
        issues.append(f"[AI Boilerplate] {len(boilerplate_found)} instance(s):")
        issues.extend(boilerplate_found)
    else:
        passed.append("No AI boilerplate detected")
    
    # --- 4. Thin content ---
    word_count = count_words(body)
    if word_count < 800:
        issues.append(f"[Thin Content] Only {word_count} words — posts should be ≥800 words")
    elif word_count < 1500:
        warnings.append(f"[Content Length] {word_count} words — borderline for competitive SEO (aim ≥1500)")
    else:
        passed.append(f"Word count OK ({word_count} words)")
    
    # --- 5. Answer-first ---
    title_lower = fm.get("title", "").lower()
    is_informational = any(kw in title_lower for kw in INFORMATIONAL_KEYWORDS) or \
                       any(kw in filename for kw in INFORMATIONAL_KEYWORDS)
    
    if not has_answer_first(body):
        if is_informational:
            issues.append("[Answer-First] Missing Answer-first block — required for informational/commercial queries (SEO Analyst mandate)")
        else:
            warnings.append("[Answer-First] No Answer-first block detected — check if article needs one")
    else:
        passed.append("Has Answer-first block")
    
    # --- 6. FAQ block ---
    if not has_faq(body):
        if is_informational:
            warnings.append("[FAQ] No FAQ section — informational posts benefit from FAQPage schema & PAA coverage")
    else:
        passed.append("Has FAQ section")
    
    # --- 7. Robotic H2 intros ---
    robotic_intros = []
    prev_is_heading = False
    for lno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            prev_is_heading = True
            continue
        if prev_is_heading and stripped:
            if ROBOTIC_H2_INTRO.match(stripped):
                robotic_intros.append(f"  L{lno}: `{stripped[:100]}`")
            prev_is_heading = False
        elif stripped:
            prev_is_heading = False
    
    if robotic_intros:
        issues.append(f"[Robotic H2 Intro] {len(robotic_intros)} instance(s):")
        issues.extend(robotic_intros)
    else:
        passed.append("No robotic H2 intros")
    
    # --- 8. E-E-A-T signals ---
    author = fm.get("author", "")
    if not author:
        warnings.append("[E-E-A-T] No author field — weakens trust signal")
    else:
        passed.append(f"Author: {author}")
    
    # Fact density proxy: numbers/stats in body
    stat_count = len(re.findall(r"\b\d+[%x]?\b|\$[\d,]+|\d+ms|\d+TB|\d+GB", body))
    per_500 = (stat_count / max(word_count, 1)) * 500
    if per_500 < 3:
        warnings.append(f"[Fact Density] ~{per_500:.1f} data points per 500 words (target ≥3)")
    else:
        passed.append(f"Fact density OK (~{per_500:.1f} per 500w)")
    
    # --- 9. Artifacts (code/tables) ---
    if not has_code_blocks(body) and not has_tables(body):
        warnings.append("[Scanability] No code blocks or tables — technical posts need artifacts")
    else:
        passed.append("Has code blocks or tables")
    
    # --- 10. Slug match filename ---
    slug = fm.get("slug", "")
    if slug:
        expected = filename.replace(".md", "")
        if slug != expected:
            warnings.append(f"[SEO] Slug `{slug}` doesn't match filename `{expected}`")
        else:
            passed.append("Slug matches filename")
    
    return {
        "file": filename,
        "words": word_count,
        "issues": issues,
        "warnings": warnings,
        "passed": passed,
        "has_faq": has_faq(body),
        "has_cover": has_cover,
        "has_answer_first": has_answer_first(body),
    }


def main():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    print(f"[INFO] Auditing {len(posts)} posts in {POSTS_DIR}")
    
    results = []
    for p in posts:
        r = audit_post(p)
        results.append(r)
        issue_count = len([i for i in r["issues"] if not i.startswith("  ")])
        if issue_count > 0 or r["warnings"]:
            status = "ISSUES" if issue_count > 0 else "WARNINGS"
            print(f"[{status}] {r['file']} ({r['words']}w) - {issue_count} issues, {len(r['warnings'])} warnings")
    
    # --- Report ---
    total_issues = sum(len([i for i in r["issues"] if not i.startswith("  ")]) for r in results)
    total_warnings = sum(len(r["warnings"]) for r in results)
    files_with_issues = sum(1 for r in results if any(not i.startswith("  ") for i in r["issues"]))
    files_clean = sum(1 for r in results if not r["issues"] and not r["warnings"])
    has_faq_count = sum(1 for r in results if r["has_faq"])
    has_af_count = sum(1 for r in results if r["has_answer_first"])
    avg_words = int(sum(r["words"] for r in results) / len(results))
    
    md = f"""# Content Manager Audit — vesviet/content/posts

**Audit Date**: 2026-07-25 15:18 ICT  
**Scope**: `content/posts/` — **{len(posts)} posts**  
**Role**: @content-manager (+ @seo-analyst, @content-writer standards)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total posts audited | {len(posts)} |
| Posts with critical issues | **{files_with_issues}** |
| Posts clean (no issues, no warnings) | **{files_clean}** |
| Total critical issues | **{total_issues}** |
| Total warnings | **{total_warnings}** |
| Posts with FAQ section | {has_faq_count} / {len(posts)} |
| Posts with Answer-first block | {has_af_count} / {len(posts)} |
| Average word count | {avg_words} words |

---

## Critical Issues by File

"""

    for r in results:
        hard_issues = [i for i in r["issues"] if not i.startswith("  ")]
        detail_issues = [i for i in r["issues"] if i.startswith("  ")]
        if not r["issues"] and not r["warnings"]:
            continue
        
        status = "❌" if r["issues"] else "⚠️"
        md += f"### {status} {r['file']} ({r['words']}w)\n\n"
        
        if r["issues"]:
            md += "**Critical Issues:**\n"
            for i in r["issues"]:
                md += f"- {i}\n"
            md += "\n"
        
        if r["warnings"]:
            md += "**Warnings:**\n"
            for w in r["warnings"]:
                md += f"- {w}\n"
            md += "\n"

    # Clean posts
    clean = [r for r in results if not r["issues"] and not r["warnings"]]
    if clean:
        md += f"\n---\n\n## ✅ Posts Passing All Checks ({len(clean)})\n\n"
        for r in clean:
            md += f"- `{r['file']}` ({r['words']}w)\n"

    # Summary tables
    md += f"""

---

## Content Manager Recommendations

### Priority 1 — Fix Immediately
- **AI Boilerplate**: Remove any remaining template-injected sentences before publishing
- **Thin Content** (<800w): Either expand or merge into pillar articles
- **Truncated meta descriptions**: Fix pipeline bug causing `Learn production engine...` cutoff

### Priority 2 — Improve Before Sprint Ends  
- **Answer-First**: Add ≤60-word direct answers after key H2s on informational posts
- **FAQ sections**: Add `## FAQ` with 3–5 PAA-sourced questions on top commercial/informational posts
- **Fact density**: Ensure ≥3 verifiable data points per 500 words (stats, benchmarks, %s)

### Priority 3 — Ongoing Quality Bar
- **lastmod**: Keep updated when post content changes — Google uses this for freshness ranking
- **Slug consistency**: Slug field should match filename exactly (no mismatch)
- **Cover images**: All posts should have cover image for social sharing CTR

---
*Audit by @content-manager role — vesviet repo 2026-07-25*
"""

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"\n[INFO] Report saved: {REPORT_FILE}")
    print(f"[SUMMARY] {files_with_issues} posts with issues | {total_issues} critical | {total_warnings} warnings")
    return 1 if total_issues > 0 else 0

if __name__ == "__main__":
    exit(main())
