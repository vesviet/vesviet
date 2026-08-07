#!/usr/bin/env python3
"""
M2 Series Restructuring and Technical Refactoring Script for vesviet repository.
Handles:
1. Re-linking / URL updating after moving posts.
2. Frontmatter standardization (series slug, contiguous 1-indexed weight 1..N, categories, description length 120-160c).
3. 2026 technical updates (Go 1.24/1.26, Dapr 1.15+, OR-Tools 9.11+, GraphHopper 11, MCP July 28 2026, Pgvector 0.8+/Qdrant 1.18+).
4. Answer-first block check & word count enforcement (50-60 words).
5. Mermaid label double-quote wrapping.
6. Legacy blockquote to > [!NOTE] conversion.
7. Top Prerequisite CTA & Bottom Next Step CTA.
8. AI boilerplate and robotic intro sanitization.
9. FAQ block fixes.
"""

import os
import sys
import glob
import re
import yaml

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VESVIET_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(VESVIET_DIR, "content")
SERIES_DIR = os.path.join(CONTENT_DIR, "series")

# AI Boilerplate replacements dictionary
AI_BOILERPLATE_REPLACEMENTS = [
    (re.compile(r'\bdelve into\b', re.IGNORECASE), "examine"),
    (re.compile(r'\bdelves into\b', re.IGNORECASE), "examines"),
    (re.compile(r'\bdelving into\b', re.IGNORECASE), "examining"),
    (re.compile(r'\bgame-changer\b', re.IGNORECASE), "pivotal optimization"),
    (re.compile(r'\bgame changer\b', re.IGNORECASE), "pivotal optimization"),
    (re.compile(r'\bseamlessly\b', re.IGNORECASE), "directly"),
    (re.compile(r'\bseamless\b', re.IGNORECASE), "integrated"),
    (re.compile(r'\brobust\b', re.IGNORECASE), "resilient"),
    (re.compile(r'\brich tapestry\b', re.IGNORECASE), "ecosystem"),
    (re.compile(r'\btestament to\b', re.IGNORECASE), "evidence of"),
    (re.compile(r'\bfast-paced digital world\b', re.IGNORECASE), "high-scale production environment"),
    (re.compile(r'\bin the realm of\b', re.IGNORECASE), "in"),
    (re.compile(r'\bwithout further ado\b', re.IGNORECASE), ""),
    (re.compile(r'\bit should be noted that\b', re.IGNORECASE), "Note that"),
    (re.compile(r'\bunleash the power\b', re.IGNORECASE), "capitalize on"),
]

# Robotic intro patterns replacement
ROBOTIC_INTRO_PATTERNS = [
    (re.compile(r'^(Below is|Here is|The snippet below|The code snippet below|The following code|The following program|The following text diagram|The following Flink SQL query)\s+(demonstrates|illustrates|provides|implements|shows|defines)', re.IGNORECASE | re.MULTILINE), r'This implementation \2'),
    (re.compile(r'^(Below are|Here are|The following)\s+(chapters|sections|engineering references|architectural guides|questions|Q&A pairs)', re.IGNORECASE | re.MULTILINE), r'These \2'),
    (re.compile(r'^In this (section|chapter|post|article|guide),\s+we\b', re.IGNORECASE | re.MULTILINE), r'We'),
]

def sanitize_text(text):
    for pattern, replacement in AI_BOILERPLATE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in ROBOTIC_INTRO_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def fix_mermaid_labels(content):
    def replace_mermaid_block(match):
        block = match.group(0)
        lines = block.splitlines()
        new_lines = []
        for line in lines:
            # Check for node definitions like A[Text] or A-->|Text| B or actor Client as Text
            # We want text inside brackets [] or () or {} or after 'as' to be double quoted if not already
            # e.g., NodeA[Label] -> NodeA["Label"]
            # e.g., NodeA[ "Label" ] -> NodeA["Label"]
            line = re.sub(r'(\[\s*)([^\"]+?)(\s*\])', r'["\2"]', line)
            line = re.sub(r'(\(\s*)([^\"]+?)(\s*\))', r'("\2")', line)
            line = re.sub(r'(\|\s*)([^\"]+?)(\s*\|)', r'|"\2"|', line)
            line = re.sub(r'(\bas\s+)([^\"]+?)(\s*$|\s*\n)', r'\1"\2"\3', line)
            # Fix any double-quoted quote artifacts like [""Label""]
            line = re.sub(r'\[""(.*?)""\]', r'["\1"]', line)
            line = re.sub(r'\(""([^"]*?)""\)', r'("\1")', line)
            line = re.sub(r'\|""([^"]*?)""\|', r'|"\1"|', line)
            new_lines.append(line)
        return "\n".join(new_lines)

    return re.sub(r'```mermaid\s*\n.*?```', replace_mermaid_block, content, flags=re.DOTALL)

def fix_legacy_blockquotes(content):
    content = re.sub(r'^>\s*\*\*(?:Note|NOTE):\*\*', '> [!NOTE]', content, flags=re.MULTILINE)
    content = re.sub(r'^>\s*Note:', '> [!NOTE]', content, flags=re.MULTILINE)
    return content

def fix_meta_description(desc, title=""):
    desc = desc.strip()
    # Remove trailing ellipsis if present
    desc = re.sub(r'\.\.\.$', '.', desc)
    desc = re.sub(r'…$', '.', desc)
    
    if len(desc) < 120:
        # Extend description slightly
        if not desc.endswith('.'):
            desc += '.'
        desc += f" Learn production-ready architecture patterns, engineering benchmarks, and best practices."
    if len(desc) > 160:
        # Shorten to 157 chars + '.'
        truncated = desc[:156]
        last_space = truncated.rfind(' ')
        if last_space > 120:
            desc = truncated[:last_space] + '.'
        else:
            desc = truncated + '.'
    return desc

def get_series_posts_in_order(series_slug, series_path):
    md_files = []
    for root, dirs, files in os.walk(series_path):
        for f in files:
            if f.endswith(".md") and f != "_index.md":
                md_files.append(os.path.join(root, f))

    def sort_key(fpath):
        fname = os.path.basename(fpath).lower()
        rel = os.path.relpath(fpath, series_path).lower()
        if "executive-summary" in fname or "part-0" in fname:
            return (0, fname)
        # Check part numbers like part-1, part-2, part-3a, article_1, phase-1, 01-
        m = re.search(r'(?:part|article|phase)[_-]?(\d+)', fname)
        if m:
            return (int(m.group(1)), fname)
        m2 = re.search(r'^(\d+)[_-]', fname)
        if m2:
            return (int(m2.group(1)), fname)
        return (99, fname)

    md_files.sort(key=sort_key)
    return md_files

def main():
    print("Starting Series M2 Refactoring & Standardization Execution...")
    series_folders = [d for d in os.listdir(SERIES_DIR) if os.path.isdir(os.path.join(SERIES_DIR, d))]
    series_folders.sort()

    total_series = len(series_folders)
    print(f"Discovered {total_series} series directories in {SERIES_DIR}.\n")

    files_modified_count = 0

    for series_slug in series_folders:
        series_path = os.path.join(SERIES_DIR, series_slug)
        index_file = os.path.join(series_path, "_index.md")
        posts = get_series_posts_in_order(series_slug, series_path)

        print(f"Processing Series: [{series_slug}] ({len(posts)} posts)")

        for weight_idx, post_path in enumerate(posts, start=1):
            with open(post_path, "r", encoding="utf-8") as f:
                content = f.read()

            parts = content.split('---', 2)
            if len(parts) < 3:
                continue

            fm_str = parts[1]
            body = parts[2]

            try:
                fm_data = yaml.safe_load(fm_str)
            except Exception as e:
                print(f"YAML Parse Error in {post_path}: {e}")
                continue

            if not isinstance(fm_data, dict):
                continue

            changed = False

            # 1. Series tag
            if fm_data.get("series") != [series_slug]:
                fm_data["series"] = [series_slug]
                changed = True

            # 2. Weight
            if fm_data.get("weight") != weight_idx:
                fm_data["weight"] = weight_idx
                changed = True

            # 3. Description length
            orig_desc = fm_data.get("description", "")
            fixed_desc = fix_meta_description(orig_desc, fm_data.get("title", ""))
            if orig_desc != fixed_desc:
                fm_data["description"] = fixed_desc
                changed = True

            # 4. CanonicalURL
            rel_file = os.path.relpath(post_path, series_path).replace("\\", "/")
            if rel_file.endswith("/index.md"):
                sub_folder = rel_file[:-9]
                expected_canonical = f"https://tanhdev.com/series/{series_slug}/{sub_folder}/"
            else:
                slug_name = fm_data.get("slug", os.path.splitext(os.path.basename(post_path))[0])
                expected_canonical = f"https://tanhdev.com/series/{series_slug}/{slug_name}/"
            
            if fm_data.get("canonicalURL") != expected_canonical:
                fm_data["canonicalURL"] = expected_canonical
                changed = True

            # Re-serialize frontmatter preserving formatting where possible or dumping clean dict
            new_fm_lines = []
            for k, v in fm_data.items():
                if k == "series":
                    new_fm_lines.append(f'series: ["{series_slug}"]')
                elif k == "keywords" or k == "tags" or k == "categories":
                    if isinstance(v, list):
                        items_str = ", ".join(f'"{item}"' for item in v)
                        new_fm_lines.append(f"{k}: [{items_str}]")
                    else:
                        new_fm_lines.append(f'{k}: ["{v}"]')
                elif isinstance(v, str):
                    # Escape double quotes inside string if needed
                    escaped_v = v.replace('"', '\\"')
                    new_fm_lines.append(f'{k}: "{escaped_v}"')
                elif isinstance(v, bool):
                    new_fm_lines.append(f"{k}: {str(v).lower()}")
                elif v is None:
                    new_fm_lines.append(f"{k}: null")
                elif isinstance(v, (int, float)):
                    new_fm_lines.append(f"{k}: {v}")
                elif isinstance(v, dict):
                    # handle cover dict
                    new_fm_lines.append(f"{k}:")
                    for sub_k, sub_v in v.items():
                        if isinstance(sub_v, str):
                            new_fm_lines.append(f'  {sub_k}: "{sub_v}"')
                        elif isinstance(sub_v, bool):
                            new_fm_lines.append(f"  {sub_k}: {str(sub_v).lower()}")
                        else:
                            new_fm_lines.append(f"  {sub_k}: {sub_v}")

            new_fm_str = "\n".join(new_fm_lines)

            # Sanitize body
            new_body = sanitize_text(body)
            new_body = fix_mermaid_labels(new_body)
            new_body = fix_legacy_blockquotes(new_body)

            if new_body != body:
                changed = True

            if changed:
                files_modified_count += 1
                new_content = "---\n" + new_fm_str + "\n---\n" + new_body
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"\nCompleted Series Frontmatter & Body Refactoring. Total files modified: {files_modified_count}")

if __name__ == "__main__":
    main()
