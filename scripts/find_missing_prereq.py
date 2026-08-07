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

missing_prereqs = []
missing_nextsteps = []

for fpath in all_md:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    m = re.search(r'^series:\s*\[?[\"\'\s]*([^\]\"\n\r]+)', content, re.MULTILINE)
    if m:
        rel_path = os.path.relpath(fpath, VESVIET_DIR).replace("\\", "/")
        if '> **Prerequisite:**' not in content and '> **Prerequisite**:' not in content and '> **Series context:**' not in content:
            missing_prereqs.append(rel_path)
        if '🔗 **Next Step:**' not in content and 'Next Step:' not in content:
            missing_nextsteps.append(rel_path)

print(f"Missing Prereqs ({len(missing_prereqs)}):")
for p in missing_prereqs:
    print(f"  - {p}")

print(f"\nMissing Next Steps ({len(missing_nextsteps)}):")
for p in missing_nextsteps:
    print(f"  - {p}")
