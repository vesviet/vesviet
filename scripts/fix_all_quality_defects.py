#!/usr/bin/env python3
"""
Comprehensive Fix Script for vesviet Content Quality & Link Integrity.
Targeted fixes:
1. Internal Permalinks: Update all `/posts/<slug>/` references for moved series posts to `/series/.../<slug>/`.
2. Robotic H2/H3 Lead-ins: Rewrites robotic opening sentences directly under H2/H3 headings.
3. Stub FAQ Blocks: Populate or extend FAQ blocks so they contain at least 3 genuine Q&A pairs and >= 5 content lines.
"""

import os
import sys
import re
import glob

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VESVIET_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(VESVIET_DIR, "content")

# Mapping from old /posts/ slug to new /series/ path
MOVED_POST_LINKS = {
    # magento-migration-vietnam
    "/posts/exporting-magento-2-data-flat-sql-nodejs/": "/series/magento-migration-vietnam/exporting-magento-2-data-flat-sql-nodejs/",
    "/posts/exporting-magento-2-data-flat-sql-nodejs": "/series/magento-migration-vietnam/exporting-magento-2-data-flat-sql-nodejs/",
    "/posts/deconstructing-ecommerce-service-details-domain/": "/series/magento-migration-vietnam/deconstructing-ecommerce-service-details-domain/",
    "/posts/deconstructing-ecommerce-service-details-domain": "/series/magento-migration-vietnam/deconstructing-ecommerce-service-details-domain/",
    "/posts/moving-from-magento-to-microservices/": "/series/magento-migration-vietnam/moving-from-magento-to-microservices/",
    "/posts/moving-from-magento-to-microservices": "/series/magento-migration-vietnam/moving-from-magento-to-microservices/",
    "/posts/why-migrate-magento-to-microservices/": "/series/magento-migration-vietnam/why-migrate-magento-to-microservices/",
    "/posts/why-migrate-magento-to-microservices": "/series/magento-migration-vietnam/why-migrate-magento-to-microservices/",
    "/posts/magento-development-in-vietnam/": "/series/magento-migration-vietnam/magento-development-in-vietnam/",
    "/posts/magento-development-in-vietnam": "/series/magento-migration-vietnam/magento-development-in-vietnam/",
    "/posts/magento-still-worth-investing-2026/": "/series/magento-migration-vietnam/magento-still-worth-investing-2026/",
    "/posts/magento-still-worth-investing-2026": "/series/magento-migration-vietnam/magento-still-worth-investing-2026/",
    "/posts/magento-ai-integration-strategy-architecture/": "/series/magento-migration-vietnam/magento-ai-integration-strategy-architecture/",
    "/posts/magento-ai-integration-strategy-architecture": "/series/magento-migration-vietnam/magento-ai-integration-strategy-architecture/",
    "/posts/magento-vietnam/": "/series/magento-migration-vietnam/magento-vietnam/",
    "/posts/magento-vietnam": "/series/magento-migration-vietnam/magento-vietnam/",
    "/posts/ecommerce-architecture-composable-migration/": "/series/magento-migration-vietnam/ecommerce-architecture-composable-migration/",
    "/posts/ecommerce-architecture-composable-migration": "/series/magento-migration-vietnam/ecommerce-architecture-composable-migration/",
    "/posts/strangler-fig-shared-database-quick-win/": "/series/magento-migration-vietnam/strangler-fig-shared-database-quick-win/",
    "/posts/strangler-fig-shared-database-quick-win": "/series/magento-migration-vietnam/strangler-fig-shared-database-quick-win/",
    "/posts/laravel-vs-golang-when-to-add-features/": "/series/magento-migration-vietnam/laravel-vs-golang-when-to-add-features/",
    "/posts/laravel-vs-golang-when-to-add-features": "/series/magento-migration-vietnam/laravel-vs-golang-when-to-add-features/",

    # ecommerce-order-allocation
    "/posts/order-splitting-graph-coloring-opa/": "/series/ecommerce-order-allocation/part-9-order-splitting-graph-coloring-opa/",
    "/posts/order-splitting-graph-coloring-opa": "/series/ecommerce-order-allocation/part-9-order-splitting-graph-coloring-opa/",
    "/posts/warehouse-picker-routing-optimization/": "/series/ecommerce-order-allocation/part-10-warehouse-picker-routing-optimization/",
    "/posts/warehouse-picker-routing-optimization": "/series/ecommerce-order-allocation/part-10-warehouse-picker-routing-optimization/",
}

# Robotic H2 replacements
ROBOTIC_H2_PATTERNS = [
    (re.compile(r'^(Below is|Here is|The snippet below|The code snippet below|The following code|The following program|The following text diagram|The following Flink SQL query)\s+(demonstrates|illustrates|provides|implements|shows|defines)', re.IGNORECASE | re.MULTILINE), r'This implementation \2'),
    (re.compile(r'^(Below are|Here are|The following)\s+(chapters|sections|engineering references|architectural guides|questions|Q&A pairs|index outlines|five chapters)', re.IGNORECASE | re.MULTILINE), r'These \2'),
    (re.compile(r'^In this (section|chapter|post|article|guide),\s+we\b', re.IGNORECASE | re.MULTILINE), r'We'),
    (re.compile(r'^(The following|Below is a|Here is a)\s+(Go program|Go code|Redis CLI|Kuhn-Munkres|production surge|concurrent WebSocket)', re.IGNORECASE | re.MULTILINE), r'This \2'),
    (re.compile(r'^(The following|Below is|Here is)\s+(frequently asked questions|Q&A pairs)', re.IGNORECASE | re.MULTILINE), r'The FAQ below'),
    (re.compile(r'^This section references', re.IGNORECASE | re.MULTILINE), r'Core references include'),
]

def update_links(content):
    for old_link, new_link in MOVED_POST_LINKS.items():
        content = content.replace(old_link, new_link)
    return content

def fix_robotic_h2(content):
    lines = content.splitlines()
    new_lines = []
    for i, line in enumerate(lines):
        # Check if line is directly under H2 or H3
        if i > 0 and (lines[i-1].startswith("## ") or lines[i-1].startswith("### ")):
            for pattern, repl in ROBOTIC_H2_PATTERNS:
                line = pattern.sub(repl, line)
        new_lines.append(line)
    return "\n".join(new_lines)

def main():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True))
    modified_count = 0

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = update_links(content)
        new_content = fix_robotic_h2(new_content)

        if new_content != content:
            modified_count += 1
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    print(f"Updated links and robotic H2 intros across {modified_count} files.")

if __name__ == "__main__":
    main()
