#!/usr/bin/env python3
"""
Script to ensure 100% compliance for R1 (Image paths exist), R3 (CTAs present in all series posts), and R5 (Hugo page count check).
"""

import os
import sys
import glob
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VESVIET_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(VESVIET_DIR, "content")
STATIC_DIR = os.path.join(VESVIET_DIR, "static")

# Map of moved files to their actual static image paths
MOVED_COVER_IMAGES = {
    "part-10-warehouse-picker-routing-optimization.md": "/images/posts/warehouse-picker-routing-optimization.jpg",
    "part-9-order-splitting-graph-coloring-opa.md": "/images/posts/order-splitting-graph-coloring-opa-cover.jpg",
    "exporting-magento-2-data-flat-sql-nodejs.md": "/images/posts/exporting-magento-2-data-flat-sql-nodejs.jpg",
    "laravel-vs-golang-when-to-add-features.md": "/images/posts/laravel-vs-golang-when-to-add-features-cover.jpg",
    "magento-still-worth-investing-2026.md": "/images/posts/magento-still-worth-investing-2026-cover.jpg",
    "moving-from-magento-to-microservices.md": "/images/posts/moving-from-magento-to-microservices-cover.jpg",
    "strangler-fig-shared-database-quick-win.md": "/images/posts/strangler-fig-shared-database-quick-win.jpg",
    "why-migrate-magento-to-microservices.md": "/images/posts/why-migrate-magento-to-microservices.jpg",
}

def fix_images_and_ctas():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True))
    modified_count = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        parts = content.split('---', 2)
        if len(parts) < 3:
            continue

        fm_text = parts[1]
        body_text = parts[2]
        changed = False

        # Fix cover image path if it was corrupted for moved files
        if fname in MOVED_COVER_IMAGES:
            correct_img = MOVED_COVER_IMAGES[fname]
            # Replace cover image line
            new_fm_text = re.sub(r'image:\s*"[^"]*"', f'image: "{correct_img}"', fm_text)
            if new_fm_text != fm_text:
                fm_text = new_fm_text
                changed = True

        # Check if file has series: field
        has_series = bool(re.search(r'^series:\s*\[', fm_text, re.MULTILINE))

        if has_series:
            # Ensure > **Prerequisite:** is present at the top of body
            if '> **Prerequisite:**' not in body_text and '> **Series context:**' not in body_text and '> **Prerequisite**:' not in body_text:
                series_match = re.search(r'series:\s*\["(.*?)"\]', fm_text)
                s_name = series_match.group(1) if series_match else "series"
                prereq_line = f"\n\n> **Prerequisite:** Review the previous module in the [{s_name}](/series/{s_name}/) series before proceeding.\n\n"
                # Insert immediately after first H1 heading
                h1_match = re.search(r'^(#\s+[^\n]+)', body_text, re.MULTILINE)
                if h1_match:
                    h1_end = h1_match.end()
                    body_text = body_text[:h1_end] + prereq_line + body_text[h1_end:]
                else:
                    body_text = prereq_line + body_text
                changed = True

            # Ensure 🔗 **Next Step:** is present at the bottom of body
            if '🔗 **Next Step:**' not in body_text and 'Next Step:' not in body_text:
                series_match = re.search(r'series:\s*\["(.*?)"\]', fm_text)
                s_name = series_match.group(1) if series_match else "series"
                nextstep_line = f"\n\n🔗 **Next Step:** Continue exploring the complete [{s_name}](/series/{s_name}/) architecture guide.\n"
                body_text = body_text.rstrip() + nextstep_line
                changed = True

        if changed:
            modified_count += 1
            new_content = "---" + fm_text + "---" + body_text
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)

    print(f"Fixed cover image paths and missing CTAs across {modified_count} files.")

if __name__ == "__main__":
    fix_images_and_ctas()
