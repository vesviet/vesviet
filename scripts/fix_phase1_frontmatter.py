#!/usr/bin/env python3
"""
Phase 1 Batch Fix: tags + lastmod + slug fix for all 69 posts
Content-Writer role: enforce frontmatter completeness per role standard.

Tag taxonomy based on pillar mapping from content-manager audit:
- Go/Golang Engineering
- E-Commerce Architecture
- Database & Scaling
- Cloud Infrastructure
- Magento/Migration
- AI/LLM Engineering
- Routing/Geospatial
- Event-Driven/Saga
- System Design
"""

import os
import re
import glob
from datetime import datetime

POSTS_DIR = r"D:\myproject\vesviet\content\posts"
LASTMOD_DATE = "2026-07-25T15:31:00+07:00"
TODAY = "2026-07-25"

# Tag taxonomy — keyword → tags mapping
TAG_MAP = [
    # Go/Golang
    (["golang", "goroutine", "grpc", "pprof", "go-", "-go-", "go_", "errgroup", "gc-", "cgo", "gorm"], 
     ["Golang", "Go", "Backend Engineering"]),
    
    # Microservices
    (["microservice", "distributed", "saga", "event-driven", "cqrs", "nats", "dapr", "temporal"],
     ["Microservices", "System Design", "Backend Engineering"]),
    
    # E-Commerce
    (["ecommerce", "e-commerce", "shopee", "shopify", "magento", "flash-sale", "inventory", "cart", "checkout", "order"],
     ["E-Commerce", "System Design"]),
    
    # Database
    (["mysql", "tidb", "vitess", "database", "sharding", "redis", "postgresql"],
     ["Database", "Scaling", "Backend Engineering"]),
    
    # Cloud/Infra
    (["kubernetes", "k8s", "cloudflare", "aws", "eks", "ecs", "argocd", "gitops", "serverless", "edge"],
     ["Cloud Infrastructure", "DevOps", "Kubernetes"]),
    
    # AI/LLM
    (["ai", "llm", "mcp", "rag", "graphrag", "fine-tune", "prompt-engineer", "generative", "agentic", "swarm", "vibe-cod"],
     ["AI Engineering", "LLM", "Machine Learning"]),
    
    # Routing/Geo
    (["graphhopper", "osrm", "routing", "geo-distribut", "distance-matrix", "ride-hailing", "surge-pric"],
     ["Geospatial", "Architecture", "System Design"]),
    
    # Architecture/System Design
    (["architecture", "blueprint", "design", "monolith", "composable", "banking", "fintech", "payment"],
     ["Architecture", "System Design"]),
    
    # Security
    (["zero-trust", "spiffe", "spire", "istio", "service-mesh", "security", "oauth"],
     ["Security", "Cloud Infrastructure"]),
    
    # Performance
    (["profiling", "performance", "benchmark", "throughput", "scaling", "high-concurren"],
     ["Performance", "Backend Engineering"]),
    
    # Magento specific
    (["magento", "vietnam", "laravel"],
     ["Magento", "Vietnam", "E-Commerce"]),
]

def detect_tags(filename, title, description):
    """Detect appropriate tags based on file content."""
    combined = (filename + " " + title + " " + description).lower()
    all_tags = set()
    
    for keywords, tags in TAG_MAP:
        for kw in keywords:
            if kw in combined:
                all_tags.update(tags)
                break
    
    if not all_tags:
        all_tags = {"Architecture", "System Design", "Backend Engineering"}
    
    # Cap at 5 tags
    tag_list = sorted(all_tags)[:5]
    return tag_list

def format_tags_yaml(tags):
    """Format tags as Hugo-compatible YAML array."""
    return "tags: [" + ", ".join(f'"{t}"' for t in tags) + "]"

def fix_frontmatter(content, filename):
    """Add/fix tags and lastmod in frontmatter."""
    if not content.startswith("---"):
        return content, []
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content, []
    
    fm_raw = parts[1]
    body = parts[2]
    changes = []
    
    # Extract current values
    title_match = re.search(r'^title:\s*["\']?([^"\'\\n][^\n]*?)["\']?\s*$', fm_raw, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""
    
    desc_match = re.search(r'^description:\s*["\']?([^"\'\\n][^\n]*?)["\']?\s*$', fm_raw, re.MULTILINE)
    desc = desc_match.group(1).strip() if desc_match else ""
    
    # 1. Add tags if missing
    if not re.search(r'^tags:', fm_raw, re.MULTILINE):
        tags = detect_tags(filename, title, desc)
        tags_line = format_tags_yaml(tags)
        # Insert after 'date:' line
        if re.search(r'^date:', fm_raw, re.MULTILINE):
            fm_raw = re.sub(r'^(date:[^\n]+)', r'\1\n' + tags_line, fm_raw, flags=re.MULTILINE)
        else:
            fm_raw = fm_raw.rstrip() + "\n" + tags_line + "\n"
        changes.append(f"Added tags: {tags}")
    
    # 2. Add lastmod if missing
    if not re.search(r'^lastmod:', fm_raw, re.MULTILINE):
        lastmod_line = f'lastmod: "{LASTMOD_DATE}"'
        if re.search(r'^date:', fm_raw, re.MULTILINE):
            fm_raw = re.sub(r'^(date:[^\n]+)', r'\1\n' + lastmod_line, fm_raw, flags=re.MULTILINE)
        else:
            fm_raw = fm_raw.rstrip() + "\n" + lastmod_line + "\n"
        changes.append("Added lastmod")
    
    if changes:
        new_content = "---" + fm_raw + "---" + body
        return new_content, changes
    
    return content, []

def fix_slug_mismatch(filepath, content):
    """Fix specific slug mismatch for cloudflare-zero-devops-ecommerce.md"""
    basename = os.path.basename(filepath).replace(".md", "")
    changes = []
    
    # Check slug
    slug_match = re.search(r'^slug:\s*["\']?([^"\'\\n][^\n]*?)["\']?\s*$', content, re.MULTILINE)
    if slug_match:
        current_slug = slug_match.group(1).strip()
        if current_slug != basename:
            content = re.sub(
                r'^(slug:\s*["\']?)[^"\'\\n][^\n]*?(["\']?\s*)$',
                f'slug: "{basename}"',
                content,
                flags=re.MULTILINE
            )
            changes.append(f"Fixed slug: {current_slug} -> {basename}")
    
    return content, changes

def main():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    print(f"[INFO] Processing {len(posts)} posts...")
    
    total_changed = 0
    all_changes = []
    
    for filepath in posts:
        filename = os.path.basename(filepath)
        
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        original = content
        file_changes = []
        
        # Fix frontmatter (tags + lastmod)
        content, fm_changes = fix_frontmatter(content, filename)
        file_changes.extend(fm_changes)
        
        # Fix slug mismatch
        if "cloudflare-zero-devops-ecommerce" in filename:
            content, slug_changes = fix_slug_mismatch(filepath, content)
            file_changes.extend(slug_changes)
        
        if content != original:
            with open(filepath, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            total_changed += 1
            all_changes.append(f"[FIXED] {filename}: {'; '.join(file_changes)}")
            print(f"[FIXED] {filename}: {'; '.join(file_changes)}")
        else:
            print(f"[OK]    {filename}: no changes needed")
    
    print(f"\n[SUMMARY] {total_changed}/{len(posts)} files updated")
    
    # Write change log
    log_path = r"D:\myproject\vesviet\reports\batch_fix_phase1_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Batch Fix Phase 1 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Files updated: {total_changed}/{len(posts)}\n\n")
        f.write("\n".join(all_changes))
    print(f"[INFO] Log saved: {log_path}")

if __name__ == "__main__":
    main()
