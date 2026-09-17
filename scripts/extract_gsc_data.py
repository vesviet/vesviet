#!/usr/bin/env python3
"""
extract_gsc_data.py — Automated Google Search Console (GSC) Coverage Data Extractor

Parses the 9 GSC export archives in `tmp/` (1.zip - 9.zip), performs forensic
reconciliation across 711 total rows, extracts historical crawl charts,
classifies the 500 non-learn URLs into the 6 GSC indexing groups, clusters
them by path pattern, maps 404 remediation destinations against Hugo aliases
and Cloudflare _redirects, and saves the structured dataset to JSON.

Usage:
    python extract_gsc_data.py [--input-dir DIR] [--output-file FILE] [--verify]
"""

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("gsc_extractor")

# Default Canonical Category Names & Keys
CATEGORY_SPECS = [
    {
        "key": "not_found_404",
        "display_name": "Not found (404)",
        "gsc_issue": "Not found (404)",
        "primary_zip": "2.zip",
        "severity": "High",
        "description": "Pages returning HTTP 404 status codes. Includes legacy flat radar URLs, renamed series chapters, and removed tags."
    },
    {
        "key": "crawled_not_indexed",
        "display_name": "Crawled - currently not indexed",
        "gsc_issue": "Crawled - currently not indexed",
        "primary_zip": "6.zip",
        "subset_zip": "8.zip",
        "severity": "Medium",
        "description": "Pages crawled by Googlebot but excluded from index due to low content density, thin taxonomy tags, or newly published queue."
    },
    {
        "key": "excluded_noindex",
        "display_name": "Excluded by 'noindex' tag",
        "gsc_issue": "Excluded by \u2018noindex\u2019 tag",
        "primary_zip": "1.zip",
        "subset_zip": "7.zip",
        "severity": "High",
        "description": "Pages excluded due to meta robots noindex tag. Predominantly intentional tag archives, plus accidental flags on production articles."
    },
    {
        "key": "page_with_redirect",
        "display_name": "Page with redirect",
        "gsc_issue": "Page with redirect",
        "primary_zip": "3.zip",
        "subset_zip": "9.zip",
        "severity": "Low",
        "description": "Pages that issue HTTP 301/302 redirects. Includes trailing slash normalizations, protocol/subdomain upgrades, and restructured slugs."
    },
    {
        "key": "blocked_robots",
        "display_name": "Blocked by robots.txt",
        "gsc_issue": "Blocked by robots.txt",
        "primary_zip": "5.zip",
        "severity": "Medium",
        "description": "Pages disallowed by robots.txt directives. Contains intentional XML feed and API blocks, plus historical tag crawl artifacts."
    },
    {
        "key": "canonical_alternate",
        "display_name": "Alternate page with proper canonical tag",
        "gsc_issue": "Alternate page with proper canonical tag",
        "primary_zip": "4.zip",
        "severity": "Low",
        "description": "Pages recognizing an alternate canonical URL. Covers www subdomain consolidation and external utility canonical pointers."
    }
]

# Proposed 301 Redirect targets for the 15 unmitigated 404 URLs
PROPOSED_UNMITIGATED_TARGETS = {
    "/radar/radar-2026-04-29-creative-mcp/": {
        "target": "/radar/2026-04/radar-2026-04-29-creative-mcp/",
        "method": "alias_in_markdown",
        "file": "content/radar/2026-04/radar-2026-04-29-creative-mcp.md",
        "note": "Restructured monthly radar slug"
    },
    "/radar/radar-2026-04-27-claude-sonnet/": {
        "target": "/radar/2026-04/radar-2026-04-27-claude-sonnet/",
        "method": "alias_in_markdown",
        "file": "content/radar/2026-04/radar-2026-04-27-claude-sonnet.md",
        "note": "Restructured monthly radar slug"
    },
    "/tags/or-tools/": {
        "target": "/tags/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Retired taxonomy tag fallback"
    },
    "/radar/tech-radar-april-30-2026-the-first-24-hours-of-post-exclusivity-ai-multi-cloud-access-agent-runtime-control-and-mcp-expansion/": {
        "target": "/radar/2026-04/radar-2026-04-30/",
        "method": "alias_in_markdown",
        "file": "content/radar/2026-04/radar-2026-04-30.md",
        "note": "Verbose legacy radar headline to canonical daily slug"
    },
    "/posts/strangler-fig-shared-database-quick-win/": {
        "target": "/series/magento-migration-vietnam/moving-from-magento-to-microservices/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Consolidated into Magento migration microservices pillar"
    },
    "/radar/tech-radar-april-24-2026-google-cloud-next-26-bets-the-enterprise-on-agentic-ai-and-custom-silicon/": {
        "target": "/radar/2026-04/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Monthly archive fallback for pruned radar entry"
    },
    "/radar/tech-radar-aws-openai-bedrock-multi-cloud-expansion/": {
        "target": "/radar/2026-04/radar-2026-04-29/",
        "method": "alias_in_markdown",
        "file": "content/radar/2026-04/radar-2026-04-29.md",
        "note": "Legacy multi-cloud radar variant to daily issue"
    },
    "/radar/tech-radar-june-22-2026-dapr-workflow-kratos-clean-architecture/": {
        "target": "/radar/2026-06/tech-radar-june-22-2026-dapr-workflow-kratos-clean-architecture/",
        "method": "alias_in_markdown",
        "file": "content/radar/2026-06/radar-2026-06-22.md",
        "note": "Legacy radar title variant to canonical June issue"
    },
    "/series/ecommerce-order-allocation/order-splitting-graph-coloring-opa/": {
        "target": "/posts/order-fulfillment-algorithm-warehouse-last-mile/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Consolidated series chapter into order fulfillment pillar post"
    },
    "/research/high-throughput-local-llm-infrastructure-vllm-golang-gateway/": {
        "target": "/posts/high-throughput-local-llm-infrastructure-vllm-golang-gateway/",
        "method": "alias_in_markdown",
        "file": "content/posts/high-throughput-local-llm-infrastructure-vllm-golang-gateway.md",
        "note": "Migrated from legacy /research/ section to /posts/"
    },
    "/series/ecommerce-order-allocation/warehouse-picker-routing-optimization/": {
        "target": "/posts/order-fulfillment-algorithm-warehouse-last-mile/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Consolidated series chapter into order fulfillment pillar post"
    },
    "/tags/cutover/": {
        "target": "/tags/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Retired taxonomy tag fallback"
    },
    "/tags/supply-chain/": {
        "target": "/tags/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Retired taxonomy tag fallback"
    },
    "/tags/system-design/": {
        "target": "/categories/architecture/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Retired tag mapped to primary architecture category"
    },
    "/tags/awq/": {
        "target": "/tags/",
        "method": "rule_in_redirects",
        "file": "static/_redirects",
        "note": "Retired taxonomy tag fallback"
    }
}


def classify_path_cluster(path: str) -> Dict[str, str]:
    """
    Classifies a URL path into coarse and granular pattern clusters.
    """
    clean_path = path.strip()
    if not clean_path or clean_path == "/":
        return {"section": "root", "pattern": "/", "cluster": "Homepage"}

    parts = [p for p in clean_path.split("/") if p]
    if not parts:
        return {"section": "root", "pattern": "/", "cluster": "Homepage"}

    root_section = parts[0]

    if root_section == "radar":
        if len(parts) >= 2 and re.match(r"^\d{4}-\d{2}$", parts[1]):
            month = parts[1]
            slug = parts[2] if len(parts) > 2 else ""
            return {
                "section": "radar",
                "pattern": f"/radar/{month}/",
                "cluster": f"Tech Radar Monthly ({month})"
            }
        else:
            return {
                "section": "radar",
                "pattern": "/radar/legacy-flat/",
                "cluster": "Tech Radar Legacy Flat Slug"
            }

    elif root_section == "series":
        series_name = parts[1] if len(parts) > 1 else "root"
        return {
            "section": "series",
            "pattern": f"/series/{series_name}/",
            "cluster": f"Series: {series_name}"
        }

    elif root_section == "posts":
        return {
            "section": "posts",
            "pattern": "/posts/",
            "cluster": "Technical Posts / Articles"
        }

    elif root_section == "tags":
        return {
            "section": "tags",
            "pattern": "/tags/",
            "cluster": "Taxonomy Tags"
        }

    elif root_section in ("categories", "category"):
        cat_name = parts[1] if len(parts) > 1 else "root"
        return {
            "section": "categories",
            "pattern": "/categories/",
            "cluster": f"Category: {cat_name}"
        }

    elif root_section == "api":
        return {
            "section": "api",
            "pattern": "/api/",
            "cluster": "API Endpoints"
        }

    elif root_section in ("portfolio", "our-portfolio"):
        return {
            "section": "portfolio",
            "pattern": "/portfolio/",
            "cluster": "Portfolio Pages"
        }

    elif clean_path.endswith(".xml"):
        return {
            "section": "feed_xml",
            "pattern": "/*.xml",
            "cluster": "RSS / Sitemap XML Feed"
        }

    elif clean_path.endswith(".ico") or clean_path.endswith(".pdf"):
        return {
            "section": "static_asset",
            "pattern": "/*.asset",
            "cluster": "Static Assets & Documents"
        }

    else:
        return {
            "section": "legacy_single_page",
            "pattern": f"/{root_section}",
            "cluster": f"Single Page: /{root_section}"
        }


def load_redirects_rules(redirects_path: Path) -> Dict[str, str]:
    """
    Parses Cloudflare static/_redirects file.
    """
    rules = {}
    if not redirects_path.exists():
        logger.warning("Redirects file not found: %s", redirects_path)
        return rules

    with open(redirects_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                parts = stripped.split()
                if len(parts) >= 2:
                    rules[parts[0]] = parts[1]
    return rules


def load_frontmatter_aliases(content_dir: Path) -> Dict[str, str]:
    """
    Recursively scans Hugo markdown content files for aliases frontmatter.
    """
    aliases_map = {}
    if not content_dir.exists():
        logger.warning("Content directory not found: %s", content_dir)
        return aliases_map

    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith(".md"):
                fp = Path(root) / file
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        match = re.search(r"aliases:\s*\n((?:\s*-\s*[^\n]+\n)+)", text)
                        if match:
                            for raw_line in match.group(1).splitlines():
                                alias = raw_line.strip().lstrip("-").strip(" \"'")
                                if alias:
                                    aliases_map[alias] = str(fp)
                except Exception as e:
                    logger.debug("Error reading %s: %s", fp, e)
    return aliases_map


class GscDataExtractor:
    """
    Core engine to parse, reconcile, and cluster Google Search Console data.
    """

    def __init__(
        self,
        tmp_dir: Path,
        vesviet_dir: Path,
        output_path: Path
    ):
        self.tmp_dir = tmp_dir
        self.vesviet_dir = vesviet_dir
        self.output_path = output_path
        self.redirects_file = vesviet_dir / "static" / "_redirects"
        self.content_dir = vesviet_dir / "content"

        self.redirects_rules = load_redirects_rules(self.redirects_file)
        self.frontmatter_aliases = load_frontmatter_aliases(self.content_dir)

    def extract_raw_archives(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses all 9 zip archives in tmp/. Returns (archive_metadata_list, raw_rows).
        """
        archives_meta = []
        raw_rows = []

        for i in range(1, 10):
            zip_file = self.tmp_dir / f"{i}.zip"
            if not zip_file.exists():
                raise FileNotFoundError(f"Missing required GSC archive: {zip_file}")

            with zipfile.ZipFile(zip_file, "r") as z:
                # 1. Parse Metadata.csv
                meta_raw = z.read("Metadata.csv").decode("utf-8-sig", errors="replace").strip()
                issue = "Unknown"
                sitemap = "Unknown"
                for line in meta_raw.splitlines():
                    if line.startswith("Issue,"):
                        issue = line.split(",", 1)[1].strip('"')
                    elif line.startswith("Sitemap,"):
                        sitemap = line.split(",", 1)[1].strip('"')

                # 2. Parse Chart.csv
                chart_reader = csv.reader(io.StringIO(z.read("Chart.csv").decode("utf-8-sig", errors="replace")))
                chart_header = next(chart_reader, None)
                chart_points = []
                for row in chart_reader:
                    if len(row) >= 2 and row[0] and row[1]:
                        try:
                            chart_points.append({"date": row[0].strip(), "affected_pages": int(row[1].strip())})
                        except ValueError:
                            pass

                # 3. Parse Table.csv
                table_reader = csv.reader(io.StringIO(z.read("Table.csv").decode("utf-8-sig", errors="replace")))
                table_header = next(table_reader, None)
                table_entries = []
                for row in table_reader:
                    if row and row[0]:
                        url = row[0].strip()
                        crawled = row[1].strip() if len(row) > 1 else ""
                        table_entries.append((url, crawled))
                        raw_rows.append({
                            "archive_index": i,
                            "archive_name": f"{i}.zip",
                            "issue": issue,
                            "url": url,
                            "last_crawled": crawled
                        })

                archives_meta.append({
                    "archive_index": i,
                    "archive_name": f"{i}.zip",
                    "file_size_bytes": zip_file.stat().st_size,
                    "issue": issue,
                    "sitemap": sitemap,
                    "chart_data_points": len(chart_points),
                    "chart_start": chart_points[0] if chart_points else None,
                    "chart_end": chart_points[-1] if chart_points else None,
                    "chart_history": chart_points,
                    "total_table_rows": len(table_entries),
                    "table_entries": table_entries
                })

        return archives_meta, raw_rows

    def build_dataset(self) -> Dict[str, Any]:
        """
        Executes full pipeline: extraction, reconciliation, classification, and clustering.
        """
        archives_meta, raw_rows = self.extract_raw_archives()

        total_raw_rows = len(raw_rows)
        assert total_raw_rows == 711, f"Expected 711 raw rows across 9 archives, got {total_raw_rows}"

        # Group rows by domain
        domain_counts = Counter(urlparse(r["url"]).netloc.lower() for r in raw_rows)
        learn_rows = [r for r in raw_rows if urlparse(r["url"]).netloc.lower() == "learn.tanhdev.com"]
        non_learn_rows = [r for r in raw_rows if urlparse(r["url"]).netloc.lower() != "learn.tanhdev.com"]

        assert len(learn_rows) == 211, f"Expected 211 learn rows, got {len(learn_rows)}"
        assert len(non_learn_rows) == 500, f"Expected exactly 500 non-learn rows, got {len(non_learn_rows)}"

        # Scoped core vesviet (tanhdev.com + www.tanhdev.com)
        vesviet_rows = [r for r in non_learn_rows if urlparse(r["url"]).netloc.lower() in ("tanhdev.com", "www.tanhdev.com")]
        assert len(vesviet_rows) == 474, f"Expected 474 vesviet rows, got {len(vesviet_rows)}"

        # Outlier subdomains in non-learn
        outlier_rows = [r for r in non_learn_rows if urlparse(r["url"]).netloc.lower() not in ("tanhdev.com", "www.tanhdev.com")]
        assert len(outlier_rows) == 26, f"Expected 26 outlier rows, got {len(outlier_rows)}"

        # Deduplication check for vesviet URLs
        seen_urls: Set[str] = set()
        dedup_records: List[Dict[str, Any]] = []
        vesviet_unique_rows: List[Dict[str, Any]] = []

        for r in vesviet_rows:
            u = r["url"]
            if u in seen_urls:
                dedup_records.append(r)
            else:
                seen_urls.add(u)
                vesviet_unique_rows.append(r)

        assert len(dedup_records) == 16, f"Expected 16 duplicate records (from 7.zip, 8.zip, 9.zip), got {len(dedup_records)}"
        assert len(vesviet_unique_rows) == 458, f"Expected 458 unique vesviet URLs, got {len(vesviet_unique_rows)}"

        # Group into the 6 GSC Indexing Groups
        groups_data = {}
        for spec in CATEGORY_SPECS:
            key = spec["key"]
            gsc_issue = spec["gsc_issue"]

            # Filter non-learn rows for this issue
            issue_non_learn = [r for r in non_learn_rows if r["issue"] == gsc_issue]
            # Filter core vesviet rows
            issue_vesviet = [r for r in vesviet_rows if r["issue"] == gsc_issue]

            # Unique vesviet URLs in this issue
            unique_issue_urls: Dict[str, Dict[str, Any]] = {}
            for r in issue_vesviet:
                u = r["url"]
                if u not in unique_issue_urls:
                    parsed = urlparse(u)
                    path = parsed.path
                    cluster_info = classify_path_cluster(path)

                    url_record: Dict[str, Any] = {
                        "url": u,
                        "domain": parsed.netloc.lower(),
                        "path": path,
                        "last_crawled": r["last_crawled"],
                        "archive": r["archive_name"],
                        "section": cluster_info["section"],
                        "pattern": cluster_info["pattern"],
                        "cluster": cluster_info["cluster"]
                    }

                    # If 404 group, enrich with 301 redirection status
                    if key == "not_found_404":
                        p_slash = path if path.endswith("/") else path + "/"
                        p_noslash = path.rstrip("/")

                        target_red = self.redirects_rules.get(path) or self.redirects_rules.get(p_slash) or self.redirects_rules.get(p_noslash)
                        alias_file = self.frontmatter_aliases.get(path) or self.frontmatter_aliases.get(p_slash) or self.frontmatter_aliases.get(p_noslash)

                        if target_red and alias_file:
                            url_record["mitigation_status"] = "both"
                            url_record["destination_url"] = target_red
                            url_record["alias_file"] = alias_file
                            url_record["remediation_needed"] = False
                        elif target_red:
                            url_record["mitigation_status"] = "redirects_only"
                            url_record["destination_url"] = target_red
                            url_record["alias_file"] = None
                            url_record["remediation_needed"] = True
                            url_record["remediation_action"] = "backfill_frontmatter_alias"
                        elif alias_file:
                            url_record["mitigation_status"] = "aliases_only"
                            url_record["destination_url"] = None
                            url_record["alias_file"] = alias_file
                            url_record["remediation_needed"] = True
                            url_record["remediation_action"] = "add_rule_to_redirects"
                        else:
                            # Check proposed unmitigated mapping
                            prop = PROPOSED_UNMITIGATED_TARGETS.get(path) or PROPOSED_UNMITIGATED_TARGETS.get(p_slash)
                            url_record["mitigation_status"] = "unmitigated_active_404"
                            url_record["destination_url"] = prop["target"] if prop else None
                            url_record["remediation_action"] = prop["method"] if prop else "investigate_or_confirm_410"
                            url_record["remediation_file"] = prop["file"] if prop else None
                            url_record["remediation_needed"] = True
                            url_record["note"] = prop["note"] if prop else "Unknown 404 endpoint"

                    unique_issue_urls[u] = url_record

            # Cluster counts
            pattern_counter = Counter(rec["pattern"] for rec in unique_issue_urls.values())
            cluster_counter = Counter(rec["cluster"] for rec in unique_issue_urls.values())
            section_counter = Counter(rec["section"] for rec in unique_issue_urls.values())

            # Find primary archive chart
            primary_arch = next((a for a in archives_meta if a["archive_name"] == spec["primary_zip"]), None)

            groups_data[key] = {
                "key": key,
                "display_name": spec["display_name"],
                "gsc_issue": gsc_issue,
                "severity": spec["severity"],
                "description": spec["description"],
                "primary_archive": spec["primary_zip"],
                "subset_archive": spec.get("subset_zip"),
                "non_learn_rows_count": len(issue_non_learn),
                "vesviet_raw_rows_count": len(issue_vesviet),
                "vesviet_unique_urls_count": len(unique_issue_urls),
                "pattern_breakdown": dict(pattern_counter.most_common()),
                "cluster_breakdown": dict(cluster_counter.most_common()),
                "section_breakdown": dict(section_counter.most_common()),
                "chart_trend": {
                    "start": primary_arch["chart_start"] if primary_arch else None,
                    "end": primary_arch["chart_end"] if primary_arch else None,
                    "total_data_points": len(primary_arch["chart_history"]) if primary_arch else 0,
                    "daily_history": primary_arch["chart_history"] if primary_arch else []
                },
                "urls": list(unique_issue_urls.values())
            }

        # Validate canonical counts for the 6 groups
        assert groups_data["not_found_404"]["non_learn_rows_count"] == 101, "404 non-learn count mismatch"
        assert groups_data["not_found_404"]["vesviet_unique_urls_count"] == 101, "404 vesviet count mismatch"

        assert groups_data["crawled_not_indexed"]["non_learn_rows_count"] == 116, "Crawled non-learn count mismatch"
        assert groups_data["crawled_not_indexed"]["vesviet_unique_urls_count"] == 106, "Crawled vesviet count mismatch"

        assert groups_data["excluded_noindex"]["non_learn_rows_count"] == 164, "Noindex non-learn count mismatch"
        assert groups_data["excluded_noindex"]["vesviet_unique_urls_count"] == 162, "Noindex vesviet count mismatch"

        assert groups_data["page_with_redirect"]["non_learn_rows_count"] == 79, "Redirect non-learn count mismatch"
        assert groups_data["page_with_redirect"]["vesviet_unique_urls_count"] == 69, "Redirect vesviet count mismatch"

        assert groups_data["blocked_robots"]["non_learn_rows_count"] == 18, "Robots non-learn count mismatch"
        assert groups_data["blocked_robots"]["vesviet_unique_urls_count"] == 18, "Robots vesviet count mismatch"

        assert groups_data["canonical_alternate"]["non_learn_rows_count"] == 22, "Canonical non-learn count mismatch"
        assert groups_data["canonical_alternate"]["vesviet_unique_urls_count"] == 2, "Canonical vesviet count mismatch"

        # 404 status breakdown (dynamically reflects mitigation progress)
        url_404s = groups_data["not_found_404"]["urls"]
        status_404 = Counter(u["mitigation_status"] for u in url_404s)
        assert sum(status_404.values()) == 101, f"Expected exactly 101 total 404 URLs, got {sum(status_404.values())}"

        # Global pattern summary across all 458 vesviet unique URLs
        all_vesviet_patterns = Counter()
        all_vesviet_sections = Counter()
        for g in groups_data.values():
            for u in g["urls"]:
                all_vesviet_patterns[u["pattern"]] += 1
                all_vesviet_sections[u["section"]] += 1

        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "audit_date": "2026-09-17",
                "source_directory": str(self.tmp_dir),
                "total_raw_rows": total_raw_rows,
                "learn_rows": len(learn_rows),
                "non_learn_rows": len(non_learn_rows),
                "vesviet_records": len(vesviet_rows),
                "vesviet_unique_urls": len(vesviet_unique_rows),
                "duplicate_subset_records": len(dedup_records),
                "domain_distribution": dict(domain_counts),
                "outlier_subdomains": {
                    "it-tools.tanhdev.com": domain_counts.get("it-tools.tanhdev.com", 0),
                    "dw.tanhdev.com": domain_counts.get("dw.tanhdev.com", 0),
                    "donthan.tanhdev.com": domain_counts.get("donthan.tanhdev.com", 0)
                },
                "status_breakdown_404": dict(status_404)
            },
            "archive_manifest": [
                {
                    "archive_index": a["archive_index"],
                    "archive_name": a["archive_name"],
                    "file_size_bytes": a["file_size_bytes"],
                    "issue": a["issue"],
                    "sitemap": a["sitemap"],
                    "total_table_rows": a["total_table_rows"],
                    "chart_start": a["chart_start"],
                    "chart_end": a["chart_end"]
                }
                for a in archives_meta
            ],
            "pattern_distribution_vesviet": {
                "sections": dict(all_vesviet_sections.most_common()),
                "patterns": dict(all_vesviet_patterns.most_common(25))
            },
            "groups": groups_data
        }

        return dataset

    def run(self) -> Dict[str, Any]:
        """
        Executes extraction and writes dataset to JSON file.
        """
        logger.info("Extracting GSC archives from: %s", self.tmp_dir)
        dataset = self.build_dataset()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Writing structured audit dataset to: %s", self.output_path)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info("Dataset successfully generated with %d groups.", len(dataset["groups"]))
        return dataset


def print_summary_table(dataset: Dict[str, Any]):
    """
    Prints human-readable terminal verification tables.
    """
    meta = dataset["metadata"]
    print("\n" + "=" * 80)
    print(" GSC COVERAGE AUDIT EXTRACTION & RECONCILIATION SUMMARY ")
    print("=" * 80)
    print(f"Audit Date             : {meta['audit_date']}")
    print(f"Total Raw Rows (1-9)   : {meta['total_raw_rows']} rows")
    print(f"Excluded (learn sub)   : {meta['learn_rows']} rows (learn.tanhdev.com)")
    print(f"Non-Learn Target Set   : {meta['non_learn_rows']} rows (Exact 500 URLs match)")
    print(f"Core vesviet Rows      : {meta['vesviet_records']} rows (470 apex + 4 www)")
    print(f"Unique vesviet URLs    : {meta['vesviet_unique_urls']} URLs (16 subset duplicates deduplicated)")
    print(f"Other Subdomains       : {meta['outlier_subdomains']}")
    print("-" * 80)

    print("\n--- 6 GSC INDEXING GROUPS RECONCILIATION MATRIX ---")
    header = f"{'#':<3} {'GSC Indexing Group':<40} {'Non-Learn':<11} {'Vesviet':<10} {'Unique':<8} {'Severity':<8}"
    print(header)
    print("-" * len(header))
    for idx, (k, g) in enumerate(dataset["groups"].items(), 1):
        print(f"{idx:<3} {g['display_name']:<40} {g['non_learn_rows_count']:<11} {g['vesviet_raw_rows_count']:<10} {g['vesviet_unique_urls_count']:<8} {g['severity']:<8}")

    print("\n--- 404 NOT FOUND REMEDIATION MITIGATION STATUS ---")
    st404 = meta["status_breakdown_404"]
    print(f"1. In both Hugo aliases & static/_redirects : {st404.get('both', 0)} URLs (Fully Mitigated)")
    print(f"2. In static/_redirects only               : {st404.get('redirects_only', 0)} URLs (Needs Frontmatter Alias Backfill)")
    print(f"3. Unmitigated Active 404s                 : {st404.get('unmitigated_active_404', 0)} URLs (Requires Frontmatter/Redirect Patch)")
    print(f"Total 404 URLs Audited                     : {sum(st404.values())} URLs")
    print("=" * 80 + "\n")


def main():
    script_dir = Path(__file__).resolve().parent
    default_vesviet = script_dir.parent
    default_workspace = default_vesviet.parent
    default_tmp = default_workspace / "tmp"
    default_out = default_vesviet / "data" / "gsc_audit_dataset_2026_09_17.json"

    parser = argparse.ArgumentParser(description="Extract and reconcile GSC Page Indexing Coverage data.")
    parser.add_argument("--input-dir", type=Path, default=default_tmp, help="Path to directory containing 1.zip - 9.zip")
    parser.add_argument("--vesviet-dir", type=Path, default=default_vesviet, help="Path to vesviet Hugo repository")
    parser.add_argument("--output-file", type=Path, default=default_out, help="Destination JSON path")
    parser.add_argument("--verify", action="store_true", help="Run assertion tests on extracted data")
    parser.add_argument("--quiet", action="store_true", help="Suppress informational table output")

    args = parser.parse_args()

    extractor = GscDataExtractor(
        tmp_dir=args.input_dir,
        vesviet_dir=args.vesviet_dir,
        output_path=args.output_file
    )

    dataset = extractor.run()

    if not args.quiet:
        print_summary_table(dataset)

    if args.verify:
        logger.info("Verification mode: all assertions passed during extraction.")


if __name__ == "__main__":
    main()
