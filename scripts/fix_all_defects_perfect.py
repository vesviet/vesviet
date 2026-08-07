#!/usr/bin/env python3
"""
Comprehensive Precision Fixer for vesviet Content Quality Audit compliance.
Removes all remaining Category 2 (Robotic H2 intros) and Category 3 (FAQ issues) sitewide.
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

# Exact replacements for robotic lead-ins right under headings
ROBOTIC_REPLACEMENTS = [
    ("The table below outlines appropriate concurrency control strategies", "Appropriate concurrency control strategies depend on transaction conflict probability"),
    ("The following reference table outlines the technical implementation requirements specified under PCI-DSS v4.0", "PCI-DSS v4.0 specifies strict technical implementation requirements"),
    ("The following specification details standard transaction monitoring rules", "Standard transaction monitoring rules operate alongside"),
    ("This section references core pillar guides on protocol specs", "Core references include pillar guides on protocol specs"),
    ("The following execution comparison shows how microservice scaling", "Microservice execution metrics compare scaling performance"),
    ("The following TCO breakdown compares developer velocity", "TCO metrics compare developer velocity"),
    ("Here is a practical roadmap for navigating the 2.4.9 release cycle:", "Navigate the 2.4.9 release cycle using this roadmap:"),
    ("The following Go code snippet demonstrates initiating an in-memory OpenTelemetry trace span", "Initiate an in-memory OpenTelemetry trace span directly using Go `context.Context`"),
    ("The following Go code snippet provides a lightweight, zero-dependency in-memory span tracking pattern", "A lightweight, zero-dependency in-memory span tracking pattern enables internal domain packages"),
    ("The following index outlines the six core architectural pillars of a high-concurrency ride-hailing platform", "Six core architectural pillars define the high-concurrency ride-hailing platform"),
    ("The following Go program demonstrates an event streaming consumer that reads driver location updates", "This event streaming consumer reads driver location updates"),
    ("The following Go program implements a Kuhn-Munkres (Hungarian Algorithm) cost matrix solver", "This Kuhn-Munkres cost matrix solver computes"),
    ("The following Go program implements a production surge pricing calculator", "This production surge pricing calculator aggregates"),
    ("The following Redis CLI commands illustrate how calculated surge multipliers", "Calculated surge multipliers persist in Redis"),
    ("The following Go program implements a concurrent WebSocket/gRPC push gateway server", "This concurrent WebSocket/gRPC push gateway server tracks"),
    ("The following technical resources detail asynchronous event streaming", "Technical resources detail asynchronous event streaming"),
    ("The following five chapters break down Shopee's high-concurrency production stack", "Five core chapters break down Shopee's high-concurrency production stack"),
    ("The following frequently asked questions address key decision points", "Key decision points address self-hosted Small Language Models"),
    ("The following Q&A pairs clarify quantization math", "Quantization math, low-rank matrix parameters, and Triton kernel optimizations include:"),
]

def fix_faq_formatting(content):
    lines = content.splitlines()
    new_lines = []
    in_faq = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.search(r"^#{2,3}\s+(?:Frequently Asked Questions|FAQ)\b", stripped, re.IGNORECASE):
            in_faq = True
            new_lines.append(line)
            continue
        
        if in_faq and stripped.startswith("## "):
            in_faq = False

        if in_faq:
            # Change '* **Question?**' or '- **Question?**' to '### Question?'
            m = re.match(r"^(?:[\*\-]\s+)?\*\*(?:Q\d*:\s*)?([^*]+\?)\*\*(.*)", stripped)
            if m:
                q_text = m.group(1).strip()
                rest = m.group(2).strip()
                new_lines.append(f"### {q_text}")
                if rest:
                    new_lines.append(rest)
                continue

        new_lines.append(line)

    return "\n".join(new_lines)

def main():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "**", "*.md"), recursive=True))
    modified_count = 0

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content
        for search_str, replace_str in ROBOTIC_REPLACEMENTS:
            new_content = new_content.replace(search_str, replace_str)

        new_content = fix_faq_formatting(new_content)

        if new_content != content:
            modified_count += 1
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    print(f"Applied precision quality fixes to {modified_count} files.")

if __name__ == "__main__":
    main()
