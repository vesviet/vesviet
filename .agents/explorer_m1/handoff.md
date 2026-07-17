# Milestone 1 Handoff Report: Discovery & Setup (vesviet posts SEO audit)

This handoff report summarizes the discovery phase of the `tanhdev.com` posts SEO audit. It documents the structure and metadata of all posts, identifies existing tooling and guidelines, defines the architecture for the programmatic verification script, and outlines the project configuration (`PROJECT.md`).

---

## 1. Observation

### A. Posts Directory Scan
Scanning `/home/user/personalized/vesviet/content/posts/` revealed exactly **58 Markdown files** (0 subdirectories). A direct scan of the files generated the following file name, size, and frontmatter configuration table:

| Post File | Size (Bytes) | Prose Word Count | ShowToc | TocOpen | Author | canonicalURL |
| --- | --- | --- | --- | --- | --- | --- |
| `agentic-ecommerce-search-golang-vector-databases.md` | 12,688 | 1,404 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `ai-native-frontend-architecture-predictions-2028.md` | 20,035 | 2,434 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `alipay-double-11-architecture-tps.md` | 20,363 | 2,703 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `architecting-21-service-ecommerce-golang-ddd.md` | 12,591 | 1,291 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `architecting-an-autonomous-hybrid-ai-content-pipeline.md` | 22,180 | 2,273 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `argo-cd-updates-2026.md` | 13,318 | 1,690 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `aws-eks-vs-ecs-comparison.md` | 30,570 | 4,141 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `banking-microservices-architecture.md` | 14,190 | 1,089 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `blueprint-ecommerce-microservices-architecture-diagram.md` | 14,961 | 1,497 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `cloudflare-d1-durable-objects-realtime-cart.md` | 24,679 | 1,382 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `cloudflare-zero-devops-ecommerce.md` | 13,245 | 955 | **Missing** | **Missing** | "Lê Tuấn Anh" | Present |
| `composable-banking-architecture.md` | 32,433 | 2,938 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `dapr-workflow-saga-orchestration-guide.md` | 27,132 | 1,798 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `deconstructing-ecommerce-service-details-domain.md` | 18,212 | 1,717 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `deconstructing-microfinance-core-banking-architecture.md` | 13,316 | 1,700 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `deploying-astro-on-cloudflare-full-stack-edge-architecture.md` | 24,331 | 3,267 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `deploying-autonomous-ai-swarm-openclaw-litellm.md` | 13,371 | 1,493 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `ecommerce-architecture-composable-migration.md` | 14,933 | 1,058 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `exporting-magento-2-data-flat-sql-nodejs.md` | 15,776 | 783 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `generative-ui-with-mcp-ai-native-frontend.md` | 26,841 | 1,734 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `gitops-at-scale-kubernetes-argocd-microservices.md` | 16,550 | 1,431 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `go-126-green-tea-gc-cgo-performance-guide.md` | 17,016 | 1,975 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `go-mcp-server-development-production-guide.md` | 31,615 | 2,858 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `go-microservices-distributed-tracing-architecture.md` | 8,158 | 712 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `go-microservices.md` | 36,370 | 4,061 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `go-pprof-kubernetes-remote-profiling.md` | 25,221 | 2,409 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `golang-goroutine-pool-errgroup-worker.md` | 22,849 | 1,722 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `golang-grpc-microservices-production-guide.md` | 28,820 | 1,323 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `golang-pprof-profiling-memory-cpu-tutorial.md` | 17,096 | 1,865 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `goroutine-leak-detection-production-golang.md` | 25,548 | 2,123 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `graphhopper-distance-matrix-production-guide.md` | 22,659 | 1,814 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `graphhopper-distance-matrix-routing.md` | 16,437 | 1,707 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `graphhopper-kubernetes-self-hosting-osm.md` | 18,808 | 1,645 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `graphrag-vs-naive-rag-enterprise-guide.md` | 20,810 | 1,944 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `kubernetes-in-place-pod-resizing-guide.md` | 18,057 | 1,583 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `leaseinvietnam-ai-powered-expat-rental-intelligence-system.md` | 20,684 | 2,538 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `magento-ai-integration-strategy-architecture.md` | 16,865 | 2,082 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `magento-developers-in-vietnam.md` | 15,163 | 2,151 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `magento-development-in-vietnam.md` | 18,156 | 2,548 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `magento-still-worth-investing-2026.md` | 14,687 | 2,040 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `magento-vietnam.md` | 25,923 | 3,642 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `mastering-event-driven-architecture-dapr.md` | 27,059 | 2,716 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `moving-from-magento-to-microservices.md` | 20,816 | 2,888 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `mysql-horizontal-scaling.md` | 10,805 | 1,381 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `mysql-scalability-guide.md` | 24,938 | 2,847 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `mysql-scaling-sharding-tidb-architecture.md` | 23,471 | 2,974 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `order-fulfillment-algorithm-warehouse-last-mile.md` | 18,916 | 2,289 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `paypay-architecture-scaling.md` | 19,960 | 2,528 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `production-ai-apis-oauth-versioning-meta-predictions.md` | 21,643 | 2,671 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `real-time-inventory-ecommerce-architecture.md` | 9,348 | 1,014 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `real-time-ride-hailing-architecture.md` | 19,883 | 2,598 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `serverless-ecommerce-cloudflare-d1.md` | 11,055 | 1,123 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `shopee-flash-sale-architecture.md` | 19,463 | 2,581 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `slm-fine-tune-vs-prompt-engineering.md` | 20,591 | 2,606 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `surge-pricing-optimization-architecture.md` | 11,850 | 1,560 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `the-future-of-laravel-development-in-ai-era.md` | 13,044 | 1,452 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `vibe-coding-and-ai-code-review-future.md` | 10,839 | 1,406 | `true` | `true` | "Lê Tuấn Anh" | Present |
| `why-migrate-magento-to-microservices.md` | 20,121 | 2,324 | `true` | `true` | "Lê Tuấn Anh" | Present |

*Note: Prose Word Count represents the content length AFTER stripping Markdown code blocks and HTML elements. The total word count (including code blocks) is higher.*

### B. Frontmatter and Configuration Observations
- **TOC configuration**: In the frontmatter of all posts, the fields `ShowToc: true` and `TocOpen: true` are present, with the single exception of `cloudflare-zero-devops-ecommerce.md` which misses both keys entirely.
- **Author/E-E-A-T metadata**: All 58 files enforce `author: "Lê Tuấn Anh"` in their frontmatter.
- **Canonical URLs**: Every single post contains a `canonicalURL` field targeting its own absolute address on `tanhdev.com` (e.g. `canonicalURL: "https://tanhdev.com/posts/[slug]/"`), which is a self-referential canonical layout.
- **Reading maps**: `content/reading-map.md` maps exactly 57 posts to 6 content pillars (Commerce Modernization, Microservices, Event-driven Reliability, Platform Operations, AI Systems, Hiring & Capability) plus a Tech Radar.
- **LLM Discovery**: `static/llms.txt` maps all main posts to specific sections. `layouts/index.llms-full.txt` uses a Hugo range to dynamically output the metadata and raw content of posts inside `/posts/`.

### C. Existing Scripts & Guidelines
- **Guidelines**: `/home/user/personalized/agent/vesviet/guidelines.md` establishes editorial guidelines:
  - **Answer-First block**: Bold text, absolute start of markdown body, $\le$ 60 words, unique summary.
  - **Information Gain block**: Headed by `### What You'll Learn That AI Won't Tell You`.
  - **E-E-A-T metadata**: `author: "Lê Tuấn Anh"`, double-quoted date format (`"YYYY-MM-DDTHH:MM:SS+07:00"`).
- **Existing Scripts**: Located in `/home/user/personalized/vesviet/_internal/`:
  - `audit_content_quality.py`: Audits series formatting, ShowToc, canonical, FAQs, EEAT, and code blocks.
  - `audit_series.py`: Audits curriculum duplicates, orphans, Mojibake, next/prev links, and prereq CTAs.
  - `run_fix.py`: Automates injection of TOC configurations and updates prev/next links for the `content/series/` directory.

---

## 2. Logic Chain

1. **Word Count Context**: The target is a 1,400+ words SEO baseline. A programmatic script splitting text by whitespace on raw markdown may produce higher word counts because of code blocks. Therefore, the verification script must support two modes: raw word count (prose + code) and clean prose word count. Based on clean prose word counts, 11 posts are thin (< 1400 words), while on raw word count, only 6 posts are thin:
   - `architecting-21-service-ecommerce-golang-ddd.md` (1,291 prose words)
   - `banking-microservices-architecture.md` (1,089 prose words)
   - `cloudflare-zero-devops-ecommerce.md` (955 prose words)
   - `ecommerce-architecture-composable-migration.md` (1,058 prose words)
   - `exporting-magento-2-data-flat-sql-nodejs.md` (783 prose words)
   - `go-microservices-distributed-tracing-architecture.md` (712 prose words)
   - `golang-grpc-microservices-production-guide.md` (1,323 prose words)
   - `real-time-inventory-ecommerce-architecture.md` (1,014 prose words)
   - `serverless-ecommerce-cloudflare-d1.md` (1,123 prose words)
   - `cloudflare-d1-durable-objects-realtime-cart.md` (1,382 prose words)
   - `mysql-horizontal-scaling.md` (1,381 prose words)
2. **Mojibake Status**: The search for characters `â†→`, `â†’`, `â† `, `â€”`, `â€“`, `â”`, `Ã©`, `Ã`, `Â`, `å` returned zero matches inside `content/posts/` (though some were historically present and corrected in `content/series/`).
3. **Internal Link Redirects**: A trailing slash configuration is set in `hugo.toml` (`posts = "/posts/:slug/"`). Any post URL lacking a trailing slash (e.g. `/posts/some-slug`) triggers a 301 redirect. Thus, the verification script must enforce trailing slashes for all internal links pointing to posts.
4. **TOC Validation**: `cloudflare-zero-devops-ecommerce.md` has missing frontmatter keys, requiring verification of both `ShowToc` and `TocOpen` presence.

---

## 3. Caveats

- We assumed that all posts are located inside `content/posts/` and that other content directories (like `content/series/` or `content/radar/`) are out-of-scope for the posts audit except for incoming/outgoing links.
- We analyzed the main branch/workspace directly. Any uncommitted changes on other branches or deployment environments were not analyzed.

---

## 4. Conclusion

The directory contains 58 posts, with 11 failing the 1,400 prose words baseline and 1 missing TOC configuration. No Mojibake was found in the posts folder. The programmatic verifier script structure must be class-based, parsing YAML frontmatter and scanning body markdown contents to evaluate word count (prose vs raw), trailing slashes on internal links, encoding patterns, and frontmatter integrity.

---

## 5. Verification Method

To verify the findings and the execution of the verification script:
1. View the frontmatter of `cloudflare-zero-devops-ecommerce.md` to confirm the absence of `ShowToc` and `TocOpen`.
2. Inspect the proposed `verify_posts.py` script structure designed in Section 6.
3. Validate the `PROJECT.md` milestones against the project blueprint.

---

## 6. Verification Script Design (`verify_posts.py`)

Below is the designed architecture for the Python script that will be implemented in Milestone 2.

```python
#!/usr/bin/env python3
"""
verify_posts.py
Programmatic technical validator for tanhdev.com blog posts.
Checks for word count constraints, Mojibake encoding corruption, broken links,
and frontmatter TOC configuration.
"""

import os
import re
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

class PostsVerifier:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.posts_dir = workspace_root / "content/posts"
        self.slug_to_file = {}
        self.aliases_to_file = {}
        
        # Mojibake corruption characters to search for
        self.mojibake_chars = ["â†→", "â†’", "â† ", "â€”", "â€“", "â”", "Ã©", "Ã", "Â", "å"]
        self.mojibake_re = re.compile("|".join(re.escape(x) for x in self.mojibake_chars))
        
        # Results container matching contracts/schemas/internal-link-audit.json
        self.report = {
            "stats": {
                "total_pages": 0,
                "thin_pages_count": 0,
                "mojibake_pages_count": 0,
                "missing_toc_count": 0,
                "broken_links_count": 0
            },
            "thin_pages": [],
            "mojibake_pages": [],
            "missing_toc_pages": [],
            "broken_links_pages": []
        }

    def index_workspace(self):
        """Index all post slugs and aliases to resolve internal links."""
        if not self.posts_dir.exists():
            raise FileNotFoundError(f"Posts directory not found: {self.posts_dir}")
            
        for f in self.posts_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            slug = f.stem
            aliases = []
            if fm_match:
                try:
                    fm = yaml.safe_load(fm_match.group(1)) or {}
                    slug = fm.get("slug", f.stem)
                    val = fm.get("aliases", [])
                    aliases = val if isinstance(val, list) else [val]
                except Exception:
                    pass
            self.slug_to_file[slug] = f.name
            for alias in aliases:
                self.aliases_to_file[alias.strip("/")] = f.name
        self.report["stats"]["total_pages"] = len(self.slug_to_file)

    def clean_prose(self, body: str) -> str:
        """Strip code blocks and HTML templates to isolate prose text."""
        no_code = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        no_html = re.sub(r"<[^>]+>", "", no_code)
        return no_html

    def verify_file(self, filepath: Path) -> Dict[str, Any]:
        """Perform checks on a single file."""
        content = filepath.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        
        fm = {}
        body = content
        if fm_match:
            fm_text = fm_match.group(1)
            body = fm_match.group(2)
            try:
                fm = yaml.safe_load(fm_text) or {}
            except Exception as e:
                fm = {"error": f"YAML Parse error: {e}"}

        # 1. Word Count Check
        raw_words = len(body.split())
        prose_words = len(self.clean_prose(body).split())
        
        # 2. Mojibake Check
        mojibake = []
        for i, line in enumerate(content.splitlines(), 1):
            matches = self.mojibake_re.findall(line)
            if matches:
                mojibake.append({"line": i, "patterns": list(set(matches)), "snippet": line.strip()})

        # 3. Frontmatter TOC Presence
        show_toc = fm.get("ShowToc")
        toc_open = fm.get("TocOpen")
        
        # 4. Link & Trailing Slash Verification
        broken_links = []
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body)
        for text, url in md_links:
            # Handle internal posts relative URLs
            if url.startswith("/") or url.startswith("https://tanhdev.com/"):
                clean_url = url.replace("https://tanhdev.com", "").strip("/")
                
                # Filter for post link structure
                is_post_link = clean_url.startswith("posts/") or (
                    not clean_url.startswith("series/") and 
                    not clean_url.startswith("radar/") and 
                    not clean_url.startswith("about/") and 
                    not clean_url.startswith("hire/") and 
                    "/" not in clean_url
                )
                
                if is_post_link and clean_url and clean_url != "posts":
                    parts = clean_url.split("/")
                    post_slug = parts[-1] if parts else ""
                    
                    resolved = (post_slug in self.slug_to_file) or (clean_url in self.aliases_to_file)
                    
                    # Redirect check (must have trailing slash)
                    has_trailing_slash = url.split("#")[0].split("?")[0].endswith("/")
                    
                    if not resolved:
                        broken_links.append({"text": text, "url": url, "reason": "Slug or alias not found"})
                    elif not has_trailing_slash:
                        broken_links.append({"text": text, "url": url, "reason": "Missing trailing slash (triggers 301)"})

        return {
            "name": filepath.name,
            "raw_word_count": raw_words,
            "prose_word_count": prose_words,
            "mojibake": mojibake,
            "ShowToc": show_toc,
            "TocOpen": toc_open,
            "broken_links": broken_links
        }

    def run(self) -> Dict[str, Any]:
        self.index_workspace()
        
        for f in sorted(list(self.posts_dir.glob("*.md"))):
            res = self.verify_file(f)
            
            # Populate report based on thresholds
            if res["prose_word_count"] < 1400:
                self.report["thin_pages"].append({
                    "file": res["name"],
                    "prose_words": res["prose_word_count"],
                    "raw_words": res["raw_word_count"]
                })
            
            if res["mojibake"]:
                self.report["mojibake_pages"].append({
                    "file": res["name"],
                    "occurrences": res["mojibake"]
                })
                
            if res["ShowToc"] is not True or res["TocOpen"] is not True:
                self.report["missing_toc_pages"].append({
                    "file": res["name"],
                    "ShowToc": res["ShowToc"],
                    "TocOpen": res["TocOpen"]
                })
                
            if res["broken_links"]:
                self.report["broken_links_pages"].append({
                    "file": res["name"],
                    "issues": res["broken_links"]
                })

        # Calculate final stats
        self.report["stats"]["thin_pages_count"] = len(self.report["thin_pages"])
        self.report["stats"]["mojibake_pages_count"] = len(self.report["mojibake_pages"])
        self.report["stats"]["missing_toc_count"] = len(self.report["missing_toc_pages"])
        self.report["stats"]["broken_links_count"] = sum(len(p["issues"]) for p in self.report["broken_links_pages"])
        
        return self.report

if __name__ == "__main__":
    verifier = PostsVerifier(Path("/home/user/personalized/vesviet"))
    report = verifier.run()
    
    # Write report json
    with open("posts_audit_report.json", "w", encoding="utf-8") as rf:
        json.dump(report, rf, indent=2)
        
    print(f"Audit completed: {report['stats']['total_pages']} posts scanned.")
    print(f"- Thin: {report['stats']['thin_pages_count']}")
    print(f"- Mojibake: {report['stats']['mojibake_pages_count']}")
    print(f"- Missing TOC: {report['stats']['missing_toc_count']}")
    print(f"- Link issues: {report['stats']['broken_links_count']}")
    sys.exit(0 if report['stats']['broken_links_count'] == 0 else 1)
```

---

## 7. Drafted `PROJECT.md`

Below is the drafted `PROJECT.md` for the technical and SEO audit sprint:

```markdown
# Project: tanhdev.com Posts SEO & Content Quality Audit Sprint

## Architecture & Content Layout
- **Website URL**: https://tanhdev.com/
- **SSG**: Hugo (with PaperMod theme)
- **Deployment Platform**: Cloudflare Pages
- **Content Hierarchy**:
  - `content/posts/` — Individual long-form posts (58 files). Enforces a 1,400+ words SEO baseline.
  - `content/series/` — Curriculum-based, multi-part tutorials grouped under directories (e.g. `agentic-ecommerce-search/`).
  - `content/radar/` — Tech updates and short architectural radars.
  - `content/reading-map.md` — Site index grouping 57 published essays into content pillars.
- **Config & Infrastructure**:
  - `hugo.toml` — Permalinks formatted with trailing slashes `/posts/:slug/`. Custom outputs configured for `llms.txt` and `llms-full.txt`.
  - `static/robots.txt` — Grants indexing access to AI bots (GPTBot, ClaudeBot, PerplexityBot) while blocking scraping search bots.
  - `static/_headers` — Exposes caching rules for static resources.

## Detailed Milestones

| Milestone | Name | Objective | Scope | Status |
| --- | --- | --- | --- | --- |
| **M1** | Discovery & Setup | Verify file directories, index canonicals/slugs, analyze guidelines and previous reports. | `/content/posts/`, `_internal/` | **COMPLETE** |
| **M2** | Technical Scan Execution | Implement and execute programmatic script checking for word counts, Mojibake patterns, broken internal links, and TOC status. | `verify_posts.py`, `/content/posts/` | PLANNED |
| **M3** | Content Quality & E-E-A-T | Scan Answer-First placement, verify placeholders (FAQs, boilerplate templates), audit schema integration and E-E-A-T signals. | `/content/posts/`, `layouts/` | PLANNED |
| **M4** | Report Consolidation | Consolidate technical and quality findings into single source of truth report markdown files. | `/posts_audit_report.md`, `/seo_audit_report.md` | PLANNED |
| **M5** | Independent Review | Run review passes to verify E-E-A-T compliance and test implementation solutions. | `/plan/baiviet/publish-log.md` | PLANNED |

## Interface Contracts & Schemas

### 1. `seo-audit-report.json`
Specifies metadata validation results for individual pages, ensuring Answer-First formatting, proper keyword clustering, and technical search visibility.
```json
{
  "document_path": "string",
  "audit_type": "string (post_draft_pre_publish | repository_wide)",
  "keywords": {
    "primary": "string",
    "secondary": ["string"]
  },
  "geo_aeo_execution": {
    "answer_first_structure": "string (Pass/Fail status)",
    "query_fan_out": "string",
    "fact_density": "string",
    "ai_extractability": "string"
  },
  "topical_authority": {
    "information_gain": "string",
    "cluster_position": "string (pillar | supporting)",
    "pillar_page": "string"
  },
  "issues": [
    {
      "severity": "string (Low | Medium | High)",
      "category": "string",
      "finding": "string",
      "recommendation": "string"
    }
  ],
  "technical_escalations": [
    {
      "owner": "string",
      "task": "string"
    }
  ],
  "next_steps": "string"
}
```

### 2. `internal-link-audit.json`
Ensures crawler link flow, identifying dead-ends, orphans, and broken links across the posts directory.
```json
{
  "stats": {
    "total_pages": "integer",
    "total_links": "integer",
    "avg_outbound": "float",
    "avg_inbound": "float"
  },
  "orphans": ["string (filenames/slugs)"],
  "dead_ends": ["string (filenames/slugs)"],
  "top_linked_pages": [["string", "integer"]],
  "top_linking_pages": [["string", "integer"]],
  "detailed_nodes": {
    "slug": {
      "type": "string (posts | series | radar)",
      "inbound_count": "integer",
      "outbound_count": "integer"
    }
  }
}
```
```
