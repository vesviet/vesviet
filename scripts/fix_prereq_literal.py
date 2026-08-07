#!/usr/bin/env python3
import os
import sys
import glob
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VESVIET_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(VESVIET_DIR, "content")

all_md = sorted(glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True))

fixed_count = 0

for fpath in all_md:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    m = re.search(r'^series:\s*\[?[\"\'\s]*([^\]\"\n\r]+)', content, re.MULTILINE)
    if m:
        # Check if literal '> **Prerequisite:**' is missing
        if '> **Prerequisite:**' not in content and '> **Prerequisite**:' not in content:
            rel_path = os.path.relpath(fpath, VESVIET_DIR).replace("\\", "/")
            print(f"Fixing missing literal Prerequisite CTA in: {rel_path}")
            
            # If it has > **Series context:**, convert it to > **Prerequisite:**
            if '> **Series context:**' in content:
                content = content.replace('> **Series context:**', '> **Prerequisite:**')
            else:
                # Insert > **Prerequisite:** after H1
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    fm_text = parts[1]
                    body_text = parts[2]
                    series_match = re.search(r'series:\s*\["(.*?)"\]', fm_text)
                    s_name = series_match.group(1) if series_match else "series"
                    prereq_line = f"\n\n> **Prerequisite:** Review the previous module in the [{s_name}](/series/{s_name}/) series before proceeding.\n\n"
                    h1_match = re.search(r'^(#\s+[^\n]+)', body_text, re.MULTILINE)
                    if h1_match:
                        h1_end = h1_match.end()
                        body_text = body_text[:h1_end] + prereq_line + body_text[h1_end:]
                    else:
                        body_text = prereq_line + body_text
                    content = "---" + fm_text + "---" + body_text

            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fixed_count += 1

print(f"Fixed literal Prerequisite CTAs in {fixed_count} files.")
