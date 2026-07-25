#!/usr/bin/env python3
"""
Phase 2: Add Answer-First blocks to all posts missing them.
Content-Writer role: "apply answer-first structure — place a direct, concise answer
(<=60 words) immediately after the frontmatter/intro, before elaboration."

Strategy: Use the post's description field (which is already concise and query-intent-focused)
as the basis for the Answer-First block, then insert it after frontmatter.
If description > 60 words, trim intelligently at sentence boundary.
"""

import os
import re
import glob

POSTS_DIR = r"D:\myproject\vesviet\content\posts"

def parse_frontmatter_and_body(content):
    """Split content into frontmatter dict, raw frontmatter str, and body."""
    if not content.startswith("---"):
        return {}, "", content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, "", content
    fm_raw = parts[1]
    body = parts[2]
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line and not line.strip().startswith("-"):
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm, fm_raw, body

def make_answer_first(description, title=""):
    """
    Create a clean Answer-First sentence from description.
    - Max 60 words
    - No fluff, no 'this article', no 'we will'
    - Factual, direct
    """
    if not description:
        return None
    
    # Clean up
    desc = description.strip().strip('"').strip("'")
    
    # Remove boilerplate suffixes injected by pipeline
    desc = re.sub(r'\s*Learn production engineer\w*.*$', '', desc, flags=re.IGNORECASE).strip()
    desc = re.sub(r'\s*Includes.*$', '', desc).strip()
    
    # Word count check
    words = desc.split()
    if len(words) <= 60:
        text = desc
    else:
        # Truncate at last sentence boundary within 60 words
        truncated = ' '.join(words[:60])
        last_period = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'))
        if last_period > 30:
            text = truncated[:last_period + 1]
        else:
            text = ' '.join(words[:55]) + '...'
    
    # Ensure ends with period
    if text and not text[-1] in '.!?':
        text += '.'
    
    return text

def has_answer_first(body):
    return bool(re.search(r'(?i)>\s*\*\*answer.?first', body))

def add_answer_first_to_body(body, answer_text):
    """
    Insert Answer-First block at the beginning of body content,
    after any leading whitespace/newlines.
    """
    # Strip leading whitespace from body
    stripped = body.lstrip('\n\r ')
    leading_ws = body[:len(body) - len(stripped)]
    
    answer_block = f"\n> **Answer-First:** {answer_text}\n"
    
    return leading_ws + answer_block + "\n" + stripped

def process_post(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    fm, fm_raw, body = parse_frontmatter_and_body(content)
    
    # Skip if already has Answer-First
    if has_answer_first(body):
        return False, "already has Answer-First"
    
    description = fm.get("description", "")
    title = fm.get("title", "")
    
    answer_text = make_answer_first(description, title)
    if not answer_text:
        return False, "no description available"
    
    new_body = add_answer_first_to_body(body, answer_text)
    new_content = "---" + fm_raw + "---" + new_body
    
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    
    return True, f"Added Answer-First: '{answer_text[:80]}...'"

def main():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    print(f"[INFO] Processing {len(posts)} posts for Answer-First blocks...")
    
    fixed = 0
    skipped = 0
    
    for filepath in posts:
        filename = os.path.basename(filepath)
        changed, msg = process_post(filepath)
        if changed:
            fixed += 1
            print(f"[ADDED] {filename}: {msg[:100]}")
        else:
            skipped += 1
            print(f"[SKIP]  {filename}: {msg}")
    
    print(f"\n[SUMMARY] Answer-First added: {fixed} | Skipped: {skipped}")

if __name__ == "__main__":
    main()
