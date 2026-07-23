#!/usr/bin/env python3
"""Validate high-impact content publishing invariants without rewriting content."""
from __future__ import annotations

import re
import sys
from pathlib import Path

CONTENT = Path("content")
FRONT_MATTER = re.compile(r"\A---[ \t]*\n(?P<front>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)
MERMAID_BLOCK = re.compile(r"(?m)^```mermaid\s*$")
MERMAID_FLAG = re.compile(r"(?mi)^mermaid:\s*true\s*$")
NOINDEX_FLAG = re.compile(r"(?mi)^noindex:\s*true\s*$")
ANSWER_FIRST = re.compile(r"^\s*(?:# [^\n]+\n+)?\*\*Answer-[Ff]irst:\*\*")
REQUIRED_POST_METADATA = ("title", "date", "lastmod", "description", "slug", "canonicalURL", "ShowToc", "TocOpen")
INTERNAL_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(/(?!/)[^)]+\)")
WORDS = re.compile(r"\b[\w'-]+\b")

errors: list[str] = []
warnings: list[str] = []

for path in sorted(CONTENT.rglob("*.md")):
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(raw)
    if not match:
        errors.append(f"{path}: missing or malformed YAML front matter")
        continue

    front = match.group("front")
    body = match.group("body")
    has_mermaid = bool(MERMAID_BLOCK.search(body))
    enabled_mermaid = bool(MERMAID_FLAG.search(front))
    if has_mermaid != enabled_mermaid:
        expected = "mermaid: true" if has_mermaid else "no mermaid: true flag"
        errors.append(f"{path}: Mermaid configuration must be {expected}")

    section = path.relative_to(CONTENT).parts[0]
    words = len(WORDS.findall(body))
    noindex = bool(NOINDEX_FLAG.search(front))
    if section == "radar" and path.name != "_index.md" and words < 800 and not noindex:
        errors.append(f"{path}: Radar entry below 800 words must set noindex: true or be expanded")
    if section == "series" and path.name not in {"_index.md"} and words < 600 and not noindex:
        errors.append(f"{path}: Series page below 600 words must set noindex: true or be expanded")

    if section in {"posts", "series"} and not noindex and path.name != "_index.md" and not INTERNAL_LINK.search(body):
        warnings.append(f"{path}: no root-relative internal Markdown link found")

    if section == "posts" and not noindex:
        if not ANSWER_FIRST.search(body):
            warnings.append(f"{path}: indexable post does not begin with an Answer-first summary")
        for field in REQUIRED_POST_METADATA:
            if not re.search(rf"(?mi)^{re.escape(field)}:\s*.+$", front):
                warnings.append(f"{path}: missing recommended post metadata field: {field}")

if warnings:
    print("Content quality warnings:")
    print("\n".join(f"WARNING: {message}" for message in warnings))
if errors:
    print("Content validation failed:", file=sys.stderr)
    print("\n".join(f"ERROR: {message}" for message in errors), file=sys.stderr)
    sys.exit(1)

print("Content validation passed.")

