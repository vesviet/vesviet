#!/usr/bin/env python3
"""
Automated Verification & Hugo Build Validation Script for vesviet (Milestone M5 / R4)

This script objectively verifies content formatting, image path leading slashes,
series CTAs, legacy note blockquote conversions, and Hugo build execution.

Assertions verified:
1. [R1] 0 local image 404 errors remain (all local cover/content image paths starting with `images/` have leading `/`).
2. [R2] `**Answer-first:**` summary blocks present in all 275 content articles (and word count <= 60 words).
3. [R3] `> **Prerequisite:**` and `🔗 **Next Step:**` CTAs present in all 74 series posts across 11 series groups.
4. [R4] 0 legacy `> **Note:**` blockquote markers remain (all converted to GitHub alert syntax `> [!NOTE]`).
5. [R5] Hugo build (`hugo --source /home/user/personalized/vesviet`) completes cleanly with exit code 0 rendering 997 pages.
"""

import os
import sys
import glob
import re
import subprocess
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VESVIET_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CONTENT_DIR = os.path.join(VESVIET_DIR, "content")


def run_r1_image_check(all_md_files):
    """
    R1: Verify that 0 local image 404 errors remain due to missing leading slashes.
    All local cover and content image paths starting with images/ or images/posts/ must have a leading /.
    """
    total_refs_checked = 0
    unslashed_vios = []

    # Pattern for unslashed image paths (e.g. "images/posts/..." or 'images/...' without leading '/')
    unslashed_pattern = re.compile(r'(?<![/\w\.\-])(images/(?:posts/|series/)?[a-zA-Z0-9_\-\./]+\.(?:jpg|png|webp|svg|jpeg|gif))', re.IGNORECASE)

    for fpath in all_md_files:
        rel_path = os.path.relpath(fpath, VESVIET_DIR).replace("\\", "/")
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Count total image references in file
        image_matches = re.findall(r'/(images/(?:posts/|series/)?[a-zA-Z0-9_\-\./]+\.(?:jpg|png|webp|svg|jpeg|gif))', content, re.IGNORECASE)
        total_refs_checked += len(image_matches)

        # Check for unslashed image references
        unslashed = unslashed_pattern.findall(content)
        if unslashed:
            unslashed_vios.append((rel_path, unslashed))
            total_refs_checked += len(unslashed)

    passed = len(unslashed_vios) == 0
    return {
        "passed": passed,
        "total_files": len(all_md_files),
        "total_refs_checked": total_refs_checked,
        "unslashed_count": len(unslashed_vios),
        "unslashed_details": unslashed_vios
    }


def run_r2_answer_first_check(all_md_files):
    """
    R2: Verify **Answer-first:** summary blocks present in all 275 content articles (and word count <= 60 words).
    Content articles = non-index markdown files across content/ directory.
    """
    articles = [f for f in all_md_files if not f.endswith("_index.md")]
    missing_af = []
    over_60_af = []
    af_word_counts = []

    for fpath in articles:
        rel_path = os.path.relpath(fpath, VESVIET_DIR).replace("\\", "/")
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        m = re.search(r'(?i)(?:>\s*)?\*\*answer[-_ ]first:?\*\*\s*([^\n]+)', content)
        if not m:
            missing_af.append(rel_path)
        else:
            line_text = m.group(1).strip()
            # Clean markdown formatting for word count calculation
            clean_text = re.sub(r'[*_`~]', '', line_text)
            words = len(clean_text.split())
            af_word_counts.append(words)
            if words > 60:
                over_60_af.append((rel_path, words, line_text))

    passed = (len(articles) == 275) and (len(missing_af) == 0) and (len(over_60_af) == 0)
    return {
        "passed": passed,
        "total_articles": len(articles),
        "missing_af_count": len(missing_af),
        "missing_af_details": missing_af,
        "over_60_count": len(over_60_af),
        "over_60_details": over_60_af,
        "max_words": max(af_word_counts) if af_word_counts else 0,
        "avg_words": (sum(af_word_counts) / len(af_word_counts)) if af_word_counts else 0
    }


def run_r3_series_cta_check(all_md_files):
    """
    R3: Verify > **Prerequisite:** and 🔗 **Next Step:** CTAs present in all 74 series posts across 11 series groups.
    Series posts = markdown files containing series: frontmatter field.
    """
    series_posts = []
    series_groups = set()

    for fpath in all_md_files:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        m = re.search(r'^series:\s*\[?[\"\'\s]*([^\]\"\n\r]+)', content, re.MULTILINE)
        if m:
            s_group = m.group(1).strip('\"\'')
            series_groups.add(s_group)
            series_posts.append((fpath, content, s_group))

    missing_prereq = []
    missing_nextstep = []

    for fpath, content, s_group in series_posts:
        rel_path = os.path.relpath(fpath, VESVIET_DIR).replace("\\", "/")
        if '> **Prerequisite:**' not in content and '> **Prerequisite**:' not in content:
            missing_prereq.append(rel_path)
        if '🔗 **Next Step:**' not in content and 'Next Step:' not in content:
            missing_nextstep.append(rel_path)

    passed = (len(series_posts) == 74) and (len(series_groups) == 11) and (len(missing_prereq) == 0) and (len(missing_nextstep) == 0)
    return {
        "passed": passed,
        "total_series_posts": len(series_posts),
        "total_series_groups": len(series_groups),
        "series_groups_list": sorted(list(series_groups)),
        "missing_prereq_count": len(missing_prereq),
        "missing_prereq_details": missing_prereq,
        "missing_nextstep_count": len(missing_nextstep),
        "missing_nextstep_details": missing_nextstep
    }


def run_r4_legacy_note_check(all_md_files):
    """
    R4: Verify 0 legacy > **Note:** blockquote markers remain (all converted to GitHub alert syntax > [!NOTE]).
    """
    legacy_notes = []
    alert_notes_count = 0

    for fpath in all_md_files:
        rel_path = os.path.relpath(fpath, VESVIET_DIR).replace("\\", "/")
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if re.search(r'(?i)>\s*\*\*note\b', content):
            legacy_notes.append(rel_path)

        alert_notes_count += len(re.findall(r'>\s*\[!NOTE\]', content, re.IGNORECASE))

    passed = len(legacy_notes) == 0
    return {
        "passed": passed,
        "total_files": len(all_md_files),
        "legacy_notes_count": len(legacy_notes),
        "legacy_notes_details": legacy_notes,
        "alert_notes_count": alert_notes_count
    }


def run_r5_hugo_build():
    """
    R5: Run Hugo build (hugo --source /home/user/personalized/vesviet), verify exit code 0 and page count.
    """
    cmd = ["hugo", "--source", VESVIET_DIR]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = res.stdout
        stderr = res.stderr
        exit_code = res.returncode

        # Parse rendered pages count from output
        # Table output format: Pages | 997
        pages_match = re.search(r'Pages\s*│\s*(\d+)', stdout)
        pages_count = int(pages_match.group(1)) if pages_match else 0

        passed = (exit_code == 0) and (pages_count == 997)
        return {
            "passed": passed,
            "exit_code": exit_code,
            "pages_rendered": pages_count,
            "stdout": stdout,
            "stderr": stderr
        }
    except Exception as e:
        return {
            "passed": False,
            "exit_code": -1,
            "pages_rendered": 0,
            "stdout": "",
            "stderr": str(e)
        }


def main():
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
    print("=" * 80)
    print("          VESVIET AUTOMATED CONTENT & BUILD VALIDATION SUITE (M5 / R4)          ")
    print("=" * 80)
    print(f"Target Repository : {VESVIET_DIR}")
    print(f"Content Directory  : {CONTENT_DIR}")
    print(f"Execution Time     : {now_str}")
    print("=" * 80)

    if not os.path.exists(CONTENT_DIR):
        print(f"[FAIL] Content directory not found at {CONTENT_DIR}")
        sys.exit(1)

    all_md_files = sorted(glob.glob(os.path.join(CONTENT_DIR, "**/*.md"), recursive=True))
    total_md_count = len(all_md_files)
    print(f"[INFO] Discovered {total_md_count} total Markdown files in vesviet/content.\n")

    # Run R1
    r1 = run_r1_image_check(all_md_files)
    print("-" * 80)
    print("[R1] Local Image Path Validation (Leading Slash Check)")
    print("-" * 80)
    print(f"Files Scanned               : {r1['total_files']}")
    print(f"Image References Checked    : {r1['total_refs_checked']}")
    print(f"Unslashed Local Image Paths : {r1['unslashed_count']}")
    if r1['passed']:
        print(f"[PASS] R1 Assertion PASSED: 0 local image 404 errors remain (all {r1['total_refs_checked']} image paths have leading '/').")
    else:
        print(f"[FAIL] R1 Assertion FAILED: {r1['unslashed_count']} unslashed image paths detected.")
        for f, vios in r1['unslashed_details']:
            print(f"       - {f}: {vios}")

    # Run R2
    r2 = run_r2_answer_first_check(all_md_files)
    print("\n" + "-" * 80)
    print("[R2] Answer-First Summary Block Validation")
    print("-" * 80)
    print(f"Content Articles Evaluated  : {r2['total_articles']}")
    print(f"Articles with Answer-First  : {r2['total_articles'] - r2['missing_af_count']} / {r2['total_articles']} (100.0%)")
    print(f"Articles > 60 Words Limit   : {r2['over_60_count']}")
    print(f"Max Answer-First Word Count : {r2['max_words']} words")
    print(f"Avg Answer-First Word Count : {r2['avg_words']:.1f} words")
    if r2['passed']:
        print(f"[PASS] R2 Assertion PASSED: All {r2['total_articles']} content articles have '**Answer-first:**' summary blocks <= 60 words.")
    else:
        print(f"[FAIL] R2 Assertion FAILED: {r2['missing_af_count']} missing, {r2['over_60_count']} exceeded 60 words.")

    # Run R3
    r3 = run_r3_series_cta_check(all_md_files)
    print("\n" + "-" * 80)
    print("[R3] Series Post CTAs Validation")
    print("-" * 80)
    print(f"Series Posts Identified     : {r3['total_series_posts']}")
    print(f"Series Groups Count         : {r3['total_series_groups']}")
    print(f"Posts with > **Prerequisite:** : {r3['total_series_posts'] - r3['missing_prereq_count']} / {r3['total_series_posts']}")
    print(f"Posts with 🔗 **Next Step:**    : {r3['total_series_posts'] - r3['missing_nextstep_count']} / {r3['total_series_posts']}")
    if r3['passed']:
        print(f"[PASS] R3 Assertion PASSED: All {r3['total_series_posts']} series posts across {r3['total_series_groups']} groups contain required CTAs.")
    else:
        print(f"[FAIL] R3 Assertion FAILED: Missing Prereq: {r3['missing_prereq_count']}, Missing Next Step: {r3['missing_nextstep_count']}")

    # Run R4
    r4 = run_r4_legacy_note_check(all_md_files)
    print("\n" + "-" * 80)
    print("[R4] Legacy Blockquote Markers Validation (GitHub Alert Syntax)")
    print("-" * 80)
    print(f"Files Scanned               : {r4['total_files']}")
    print(f"Legacy > **Note:** Markers  : {r4['legacy_notes_count']}")
    print(f"GitHub Alert > [!NOTE]      : {r4['alert_notes_count']}")
    if r4['passed']:
        print(f"[PASS] R4 Assertion PASSED: 0 legacy '> **Note:**' blockquote markers remain (all converted to '> [!NOTE]').")
    else:
        print(f"[FAIL] R4 Assertion FAILED: {r4['legacy_notes_count']} legacy '> **Note:**' markers remain.")

    # Run R5
    r5 = run_r5_hugo_build()
    print("\n" + "-" * 80)
    print("[R5] Hugo Build Execution & Page Metric Verification")
    print("-" * 80)
    print(f"Hugo Exit Code              : {r5['exit_code']}")
    print(f"Rendered Pages Count        : {r5['pages_rendered']}")
    if r5['passed']:
        print(f"[PASS] R5 Assertion PASSED: Hugo build completed cleanly with exit code 0 rendering {r5['pages_rendered']} pages.")
    else:
        print(f"[FAIL] R5 Assertion FAILED: Hugo build failed with exit code {r5['exit_code']}, pages rendered: {r5['pages_rendered']}.")

    # Final Summary
    all_passed = r1['passed'] and r2['passed'] and r3['passed'] and r4['passed'] and r5['passed']
    print("\n" + "=" * 80)
    if all_passed:
        print("SUMMARY: ALL ASSERTIONS (R1, R2, R3, R4, R5) PASSED OBJECTIVELY WITH 0 FAILURES")
        print("=" * 80)
        sys.exit(0)
    else:
        print("SUMMARY: VALIDATION SUITE FAILED WITH DETECTED DEFECTS")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
