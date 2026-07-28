#!/usr/bin/env python3
"""
Taxonomy Frontmatter Consolidation Script for vesviet (Milestone 3 & 4)
Consolidates deprecated taxonomy tags, categories, and series across all markdown content files according to project taxonomy rules.
"""

import os
import sys
import glob
import re
import yaml
import argparse

CONTENT_DIR = "/home/user/personalized/vesviet/content"

TAXONOMY_MAPPINGS = {
    # Rule 1: AI
    "AI/ML": "AI",
    "ai-ml": "AI",
    "AI Engineering": "AI",
    "ai-engineering": "AI",
    "AI Architecture": "AI",
    "ai-architecture": "AI",
    "Machine Learning": "AI",
    "machine-learning": "AI",
    
    # Rule 2: Architecture
    "System Architecture": "Architecture",
    "system-architecture": "Architecture",
    "System Design": "Architecture",
    "system-design": "Architecture",
    "system design": "Architecture",
    
    # Rule 3: Backend
    "Backend Architecture": "Backend",
    "backend-architecture": "Backend",
    "Backend Engineering": "Backend",
    "backend-engineering": "Backend",
    
    # Rule 4: Database
    "Databases": "Database",
    "databases": "Database",
    "Database Architecture": "Database",
    "database-architecture": "Database",
    "Database Design": "Database",
    "database-design": "Database",
    "Database Performance": "Database",
    "database-performance": "Database",
    "Database Systems": "Database",
    "database-systems": "Database",
    
    # Rule 5: Payments
    "Payment Gateways": "Payments",
    "payment-gateways": "Payments",
    "Payment Protocols": "Payments",
    "payment-protocols": "Payments",
    
    # Rule 6: Remove Series from categories
    "Series": None,
    "series": None
}

# Backward compatibility alias
CATEGORY_MAPPINGS = TAXONOMY_MAPPINGS

LOWER_MAPPINGS = {k.strip().lower(): v for k, v in TAXONOMY_MAPPINGS.items()}

def transform_val(val, is_categories=False):
    if val is None:
        return None
    val_str = str(val).strip()
    if is_categories and val_str.lower() == "series":
        return None
    if val_str in TAXONOMY_MAPPINGS:
        tgt = TAXONOMY_MAPPINGS[val_str]
        if tgt is None and val_str in ["Series", "series"]:
            return None
        return tgt
    if val_str.lower() in LOWER_MAPPINGS:
        return LOWER_MAPPINGS[val_str.lower()]
    return val_str

def transform_list(orig_list, is_categories=False):
    new_list = []
    for item in orig_list:
        tgt = transform_val(item, is_categories=is_categories)
        if tgt is not None and tgt not in new_list:
            new_list.append(tgt)
    return new_list

def transform_field(orig, is_categories=False):
    if isinstance(orig, list):
        return transform_list(orig, is_categories=is_categories)
    elif isinstance(orig, str):
        tgt = transform_val(orig, is_categories=is_categories)
        return tgt
    return orig

def update_field_in_fm_str(fm_str, key, new_val):
    # Match inline array: key: [...]
    inline_match = re.search(r"^(" + key + r"\s*:\s*\[)(.*?)(\])", fm_str, re.MULTILINE)
    if inline_match:
        if isinstance(new_val, list):
            items_str = ", ".join(f'"{item}"' for item in new_val)
            new_line = f"{key}: [{items_str}]"
        elif isinstance(new_val, str):
            new_line = f'{key}: ["{new_val}"]'
        else:
            new_line = f"{key}: []"
        start, end = inline_match.span()
        return fm_str[:start] + new_line + fm_str[end:]

    # Match block list or single line scalar: key: ...
    lines = fm_str.splitlines()
    key_idx = -1
    for idx, line in enumerate(lines):
        if re.match(r"^" + key + r"\s*:", line):
            key_idx = idx
            break
    if key_idx != -1:
        line_val = lines[key_idx].split(":", 1)[1].strip()
        if line_val and not line_val.startswith("#"):
            if isinstance(new_val, list):
                items_str = ", ".join(f'"{item}"' for item in new_val)
                new_line = f"{key}: [{items_str}]"
            elif isinstance(new_val, str):
                new_line = f'{key}: "{new_val}"'
            else:
                new_line = f"{key}: null"
            lines[key_idx] = new_line
            return "\n".join(lines)
        else:
            j = key_idx + 1
            while j < len(lines) and (lines[j].strip().startswith("-") or lines[j].strip().startswith("#")):
                j += 1
            indent = "  "
            if key_idx + 1 < j:
                indent_match = re.match(r"^(\s*)-", lines[key_idx + 1])
                if indent_match:
                    indent = indent_match.group(1)
            if isinstance(new_val, list):
                new_field_lines = [f"{key}:"] + [f'{indent}- "{item}"' for item in new_val]
            elif isinstance(new_val, str):
                new_field_lines = [f'{key}: "{new_val}"']
            else:
                new_field_lines = [f"{key}: []"]
            lines = lines[:key_idx] + new_field_lines + lines[j:]
            return "\n".join(lines)

    return fm_str

def process_file_content(content):
    m = re.match(r"^(---\s*\n)(.*?)\n(---\s*\n)", content, re.DOTALL)
    if not m:
        return False, content, "No YAML frontmatter"

    prefix, fm_str, suffix = m.groups()
    body = content[m.end():]

    orig_yaml = yaml.safe_load(fm_str)
    if not isinstance(orig_yaml, dict):
        return False, content, "Frontmatter is not a dict"

    new_fm_str = fm_str
    field_changes = []

    for key in ["categories", "tags", "series"]:
        if key in orig_yaml:
            orig_val = orig_yaml[key]
            new_val = transform_field(orig_val, is_categories=(key == "categories"))
            if orig_val != new_val:
                new_fm_str = update_field_in_fm_str(new_fm_str, key, new_val)
                field_changes.append(f"{key}: {orig_val} -> {new_val}")

    if not field_changes:
        return False, content, "No changes needed"

    # Validation assertions
    new_yaml = yaml.safe_load(new_fm_str)
    for k in orig_yaml:
        if k not in ["categories", "tags", "series"]:
            assert orig_yaml[k] == new_yaml[k], f"Field {k} altered in frontmatter!"
        else:
            expected = transform_field(orig_yaml[k], is_categories=(k == "categories"))
            assert new_yaml[k] == expected, f"Field {k} mismatch after serialization! Got {new_yaml[k]} vs {expected}"

    new_content = prefix + new_fm_str + "\n" + suffix + body
    assert new_content[len(prefix + new_fm_str + "\n" + suffix):] == body, "Body content altered!"

    return True, new_content, "; ".join(field_changes)

def main():
    parser = argparse.ArgumentParser(description="Taxonomy Frontmatter Consolidation")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without writing changes")
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True))
    updated_count = 0

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        changed, new_content, msg = process_file_content(content)
        if changed:
            updated_count += 1
            rel_path = os.path.relpath(file_path, CONTENT_DIR)
            print(f"[{'DRY-RUN' if args.dry_run else 'UPDATED'}] {rel_path}: {msg}")
            if not args.dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"\nTotal files {'would be ' if args.dry_run else ''}updated: {updated_count}")

if __name__ == "__main__":
    main()

