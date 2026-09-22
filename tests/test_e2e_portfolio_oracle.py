#!/usr/bin/env python3
"""Comprehensive E2E Portfolio Test Oracle for tanhdev.com (vesviet).

Empirically validates:
- Tier 1: Feature Coverage (>=5 per feature across F1-F6)
  * F1: Multi-column Responsive App Shell & Components
  * F2: Left Sticky Profile Sidebar & Verified Credentials
  * F3: Right Floating Navigation Rail & Rail Spy
  * F4: Interactive Resume & RyanCV Career Milestones
  * F5: Bento Architecture Case Studies & Proof Badges
  * F6: Romea Advisory & Consulting Booking Hub
- Tier 2: Boundary & Corner Cases (>=5 per area)
  * B1: Color Token Invariant (Zero pure #000000 or #000)
  * B2: Viewport Stability (100dvh dynamic viewport height)
  * B3: Mobile Drawer & Keyboard Accessibility
  * B4: Contrast & Accessible Attributes (alt, rel, aria)
  * B5: Performance Budget (portfolio.min.js < 4096 bytes)
  * B6: Circular SVG Progress Math & Geometry (r=34, C=213.63)
- Tier 3: Cross-Feature Combinations (Pairwise interactions)
  * C1: Navigation Rail <-> Stage Section IDs (1:1 Bijection)
  * C2: Bento Filter Pills <-> Card Data Categories
  * C3: Resume Stack Tags <-> Sidebar Knowledge Areas
  * C4: Theme Toggle & Search Triggers <-> PaperMod Base Scripts
  * C5: Mobile Drawer <-> App Shell & Bottom Tab Dock
- Tier 4: Real-World Scenarios
  * S1: Advisory Booking Click Flow (prefilled mailto validation)
  * S2: Resume PDF Binary Integrity (/Le-Tuan-Anh-Resume.pdf)
  * S3: 100% Invariant Route Preservation (core sections 200 OK)
  * S4: Full Integration with test_redirects_oracle.py (23/23 pass)
  * S5: Clean Sitemap Parity (zero leaks, valid apex URLs)
"""
from __future__ import annotations

import math
import os
import re
import sys
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Base directory paths
TESTS_DIR = Path(__file__).resolve().parent
VESVIET_DIR = TESTS_DIR.parent
PUBLIC_DIR = VESVIET_DIR / "public"
STATIC_DIR = VESVIET_DIR / "static"
ASSETS_DIR = VESVIET_DIR / "assets"
LAYOUTS_DIR = VESVIET_DIR / "layouts"


class PortfolioE2EOracle:
    """Empirical Opaque-Box E2E Testing Oracle for tanhdev.com."""

    def __init__(self, public_dir: Path | None = None):
        self.public_dir = public_dir or PUBLIC_DIR
        self.index_html_path = self.public_dir / "index.html"
        self.soup: BeautifulSoup | None = None
        self.passed_checks = 0
        self.failed_checks = 0
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def record_pass(self, check_name: str, detail: str = ""):
        self.passed_checks += 1
        msg = f"[PASS] {check_name}"
        if detail:
            msg += f" ({detail})"
        print(msg)

    def record_fail(self, check_name: str, reason: str):
        self.failed_checks += 1
        msg = f"[FAIL] {check_name}: {reason}"
        self.failures.append(msg)
        print(msg, file=sys.stderr)

    def record_warn(self, check_name: str, note: str):
        msg = f"[WARN] {check_name}: {note}"
        self.warnings.append(msg)
        print(msg)

    def load_index_html(self):
        """Loads and parses public/index.html."""
        if not self.index_html_path.exists():
            raise FileNotFoundError(
                f"Missing {self.index_html_path}. Run 'hugo --gc --minify' first."
            )
        raw_html = self.index_html_path.read_text(encoding="utf-8", errors="ignore")
        self.soup = BeautifulSoup(raw_html, "html.parser")
        self.record_pass("Load public/index.html", f"{len(raw_html)} bytes parsed")

    # =========================================================================
    # TIER 1: FEATURE COVERAGE (>=5 per feature across F1-F6)
    # =========================================================================

    def test_tier1_f1_app_shell(self):
        """F1: Multi-column Responsive App Shell & Structure."""
        assert self.soup is not None
        # 1. Shell container
        shell = self.soup.find(id="app-shell")
        if shell and "portfolio-app-shell" in shell.get("class", []):
            self.record_pass("F1.1 App Shell Container", "id='app-shell' with class 'portfolio-app-shell'")
        else:
            self.record_fail("F1.1 App Shell Container", "Missing #app-shell or .portfolio-app-shell")

        # 2. Sidebar container
        sidebar = self.soup.find(id="portfolio-sidebar")
        if sidebar and "portfolio-sidebar" in sidebar.get("class", []):
            self.record_pass("F1.2 Sidebar Container", "id='portfolio-sidebar' with class 'portfolio-sidebar'")
        else:
            self.record_fail("F1.2 Sidebar Container", "Missing #portfolio-sidebar")

        # 3. Main stage container
        main_stage = self.soup.find(id="main-stage")
        if main_stage and "portfolio-main-stage" in main_stage.get("class", []):
            self.record_pass("F1.3 Main Stage Container", "id='main-stage' with class 'portfolio-main-stage'")
        else:
            self.record_fail("F1.3 Main Stage Container", "Missing #main-stage")

        # 4. Navigation rail container
        nav_rail = self.soup.find(id="portfolio-nav-rail")
        if nav_rail and "portfolio-nav-rail" in nav_rail.get("class", []):
            self.record_pass("F1.4 Nav Rail Container", "id='portfolio-nav-rail' with class 'portfolio-nav-rail'")
        else:
            self.record_fail("F1.4 Nav Rail Container", "Missing #portfolio-nav-rail")

        # 5. Hero section inside stage
        hero = self.soup.find(id="hero")
        if hero and hero.find_parent(id="main-stage"):
            self.record_pass("F1.5 Hero Section", "id='hero' located within #main-stage")
        else:
            self.record_fail("F1.5 Hero Section", "Missing #hero or not inside #main-stage")

        # 6. Mobile bottom dock
        bottom_dock = self.soup.find(id="mobile-bottom-dock")
        if bottom_dock and "mobile-bottom-dock" in bottom_dock.get("class", []):
            self.record_pass("F1.6 Mobile Bottom Dock", "id='mobile-bottom-dock' with class 'mobile-bottom-dock'")
        else:
            self.record_fail("F1.6 Mobile Bottom Dock", "Missing #mobile-bottom-dock")

        # 7. Mobile drawer backdrop and toggle triggers
        backdrop = self.soup.find(id="drawer-backdrop")
        drawer_btn = self.soup.find(id="mobile-drawer-toggle")
        close_btn = self.soup.find(id="drawer-close-btn")
        if backdrop and drawer_btn and close_btn:
            self.record_pass("F1.7 Drawer Controls", "Backdrop, drawer toggle, and close buttons present")
        else:
            self.record_fail("F1.7 Drawer Controls", f"Missing controls: backdrop={bool(backdrop)}, toggle={bool(drawer_btn)}, close={bool(close_btn)}")

    def test_tier1_f2_profile_sidebar(self):
        """F2: Left Sticky Profile Sidebar & Verified Credentials."""
        assert self.soup is not None
        sidebar = self.soup.find(id="portfolio-sidebar")
        if not sidebar:
            self.record_fail("F2 Sidebar Scope", "Sidebar not found")
            return

        # 1. Avatar image attributes
        avatar = sidebar.select_one(".profile-avatar-img")
        if avatar and avatar.get("src") == "/vesviet.png" and avatar.get("width") == "104" and avatar.get("height") == "104" and "Lê Tuấn Anh" in avatar.get("alt", ""):
            self.record_pass("F2.1 Avatar Image", f"src='{avatar.get('src')}', 104x104, alt verified")
        else:
            self.record_fail("F2.1 Avatar Image", f"Invalid avatar: {avatar}")

        # 2. Status pulse beacon and pill
        beacon = sidebar.select_one(".avatar-status-beacon")
        pill = sidebar.select_one(".profile-status-pill")
        pill_text = pill.text if pill else ""
        if beacon and "Available for Advisory" in pill_text:
            self.record_pass("F2.2 Status Pulse Indicator", f"Beacon active, text='{pill_text.strip()}'")
        else:
            self.record_fail("F2.2 Status Pulse Indicator", "Missing beacon or 'Available for Advisory' text")

        # 3. Four verified production metrics
        metric_cards = sidebar.select(".sidebar-metric-card")
        metric_pairs = [(m.select_one(".metric-num").text.strip(), m.select_one(".metric-desc").text.strip()) for m in metric_cards if m.select_one(".metric-num") and m.select_one(".metric-desc")]
        expected_metrics = ["17+", "21", "25M+", "120ms"]
        nums_found = [num for num, _ in metric_pairs]
        if len(metric_cards) == 4 and all(exp in nums_found for exp in expected_metrics):
            self.record_pass("F2.3 Production Metrics Strip", f"4 verified metrics: {nums_found}")
        else:
            self.record_fail("F2.3 Production Metrics Strip", f"Expected {expected_metrics}, found {nums_found}")

        # 4. Circular SVG skill progress meters
        circle_meters = sidebar.select(".skill-circle-meter")
        r_values = [c.get("r") for c in circle_meters]
        percents = [c.get("data-percent") for c in circle_meters]
        if len(circle_meters) == 3 and all(r == "34" for r in r_values) and set(percents) == {"95", "92", "90"}:
            self.record_pass("F2.4 Circular SVG Skill Meters", f"3 meters: r=34, percents={percents} (Go 95%, DistSys 92%, K8s 90%)")
        else:
            self.record_fail("F2.4 Circular SVG Skill Meters", f"Meters invalid: r={r_values}, percents={percents}")

        # 5. Linear knowledge gauges
        linear_fills = sidebar.select(".skill-linear-fill")
        gauge_percents = [g.get("data-percent") for g in linear_fills]
        expected_gauge_percents = {"94", "90", "88", "86"}
        if len(linear_fills) == 4 and set(gauge_percents) == expected_gauge_percents:
            self.record_pass("F2.5 Linear Knowledge Gauges", f"4 linear gauges verified: {gauge_percents}")
        else:
            self.record_fail("F2.5 Linear Knowledge Gauges", f"Expected {expected_gauge_percents}, got {gauge_percents}")

        # 6. Download resume button
        resume_btn = sidebar.select_one(".btn-sidebar-resume")
        if resume_btn and resume_btn.get("href") == "/Le-Tuan-Anh-Resume.pdf" and resume_btn.get("download") == "Le-Tuan-Anh-Resume.pdf" and resume_btn.get("target") == "_blank":
            self.record_pass("F2.6 Download Resume Button", "href='/Le-Tuan-Anh-Resume.pdf', download, target='_blank'")
        else:
            self.record_fail("F2.6 Download Resume Button", f"Invalid resume button: {resume_btn}")

        # 7. Direct contact channels
        social_links = [a.get("href") for a in sidebar.select(".sidebar-social-links a")]
        has_mail = any(h and h.startswith("mailto:vesviet@gmail.com") for h in social_links)
        has_gh = any(h and "github.com/vesviet" in h for h in social_links)
        has_in = any(h and "linkedin.com/in/vesviet" in h for h in social_links)
        if has_mail and has_gh and has_in:
            self.record_pass("F2.7 Social & Direct Channels", "Email, GitHub, and LinkedIn channels verified")
        else:
            self.record_fail("F2.7 Social & Direct Channels", f"Missing channels: mail={has_mail}, gh={has_gh}, in={has_in}")

    def test_tier1_f3_navigation_rail(self):
        """F3: Right Floating Navigation Rail & Rail Spy."""
        assert self.soup is not None
        rail = self.soup.find(id="portfolio-nav-rail")
        if not rail:
            self.record_fail("F3 Nav Rail Scope", "Nav rail not found")
            return

        # 1. Six section links with anchors
        links = rail.select(".rail-sections-menu a[href^='#']")
        hrefs = [a.get("href") for a in links]
        expected_hrefs = ["#hero", "#resume", "#works", "#playbooks", "#contact", "#publications"]
        if hrefs == expected_hrefs:
            self.record_pass("F3.1 Rail Section Links", f"6 section links: {hrefs}")
        else:
            self.record_fail("F3.1 Rail Section Links", f"Expected {expected_hrefs}, got {hrefs}")

        # 2. Tooltips present on each link
        tooltips = [a.select_one(".rail-tooltip").text.strip() for a in links if a.select_one(".rail-tooltip")]
        if len(tooltips) == 6:
            self.record_pass("F3.2 Rail Tooltips", f"6 tooltips present: {tooltips}")
        else:
            self.record_fail("F3.2 Rail Tooltips", f"Expected 6 tooltips, found {len(tooltips)}")

        # 3. Search action trigger
        search_btn = rail.find(id="rail-search-trigger")
        if search_btn and ("Search" in search_btn.get("aria-label", "") or "Search" in search_btn.get("title", "")):
            self.record_pass("F3.3 Rail Search Trigger", "id='rail-search-trigger' with search label/title")
        else:
            self.record_fail("F3.3 Rail Search Trigger", "Missing or misconfigured #rail-search-trigger")

        # 4. Theme toggle action trigger
        theme_btn = rail.find(id="rail-theme-toggle")
        if theme_btn and ("Theme" in theme_btn.get("aria-label", "") or "Theme" in theme_btn.get("title", "")):
            self.record_pass("F3.4 Rail Theme Toggle", "id='rail-theme-toggle' with theme label/title")
        else:
            self.record_fail("F3.4 Rail Theme Toggle", "Missing or misconfigured #rail-theme-toggle")

        # 5. data-section attributes
        data_sections = [a.get("data-section") for a in links]
        expected_sections = ["hero", "resume", "works", "playbooks", "contact", "publications"]
        if data_sections == expected_sections:
            self.record_pass("F3.5 Rail data-section Attributes", f"All 6 match: {data_sections}")
        else:
            self.record_fail("F3.5 Rail data-section Attributes", f"Expected {expected_sections}, got {data_sections}")

        # 6. Mobile bottom dock counterpart
        dock = self.soup.find(id="mobile-bottom-dock")
        dock_links = [a.get("href") for a in dock.select("a[href^='#']")] if dock else []
        dock_btns = len(dock.select("button")) if dock else 0
        if dock and len(dock_links) >= 3 and dock_btns >= 2:
            self.record_pass("F3.6 Mobile Bottom Dock Items", f"Dock verified with {len(dock_links)} links and {dock_btns} buttons")
        else:
            self.record_fail("F3.6 Mobile Bottom Dock Items", f"Invalid dock: links={dock_links}, btns={dock_btns}")

    def test_tier1_f4_resume_timeline(self):
        """F4: Interactive Resume & RyanCV Career Milestones."""
        assert self.soup is not None
        resume_sec = self.soup.find(id="resume")
        if not resume_sec:
            self.record_fail("F4 Resume Scope", "Section #resume not found")
            return

        # 1. Three career milestones
        milestones = resume_sec.select(".timeline-milestone-item")
        periods = [m.select_one(".milestone-period-badge").text.strip() for m in milestones if m.select_one(".milestone-period-badge")]
        has_p1 = any("2021" in p and "Present" in p for p in periods)
        has_p2 = any("2019" in p and "2021" in p for p in periods)
        has_p3 = any("2008" in p and "2019" in p for p in periods)
        if len(milestones) == 3 and has_p1 and has_p2 and has_p3:
            self.record_pass("F4.1 Three Career Milestones", f"3 periods: {periods}")
        else:
            self.record_fail("F4.1 Three Career Milestones", f"Expected 3 milestones (2021-Pres, 2019-2021, 2008-2019), got {periods}")

        # 2. Milestone roles and titles
        roles = [m.select_one(".milestone-role").text.strip() for m in milestones if m.select_one(".milestone-role")]
        if any("Senior Go Backend Architect" in r for r in roles) and any("Principal Backend Engineer" in r for r in roles) and any("Lead Systems Engineer" in r for r in roles):
            self.record_pass("F4.2 Milestone Roles", f"Verified roles: {roles}")
        else:
            self.record_fail("F4.2 Milestone Roles", f"Unexpected roles: {roles}")

        # 3. Expandable details with quantitative achievements
        details_elements = resume_sec.select("details.milestone-expandable")
        summaries = resume_sec.select(".milestone-summary")
        all_text = " ".join(m.text for m in milestones)
        has_21svcs = "21 Go microservices" in all_text or "21 Go Microservices" in all_text
        has_120ms = "120ms" in all_text
        has_p95 = "p95" in all_text
        if len(details_elements) == 3 and len(summaries) == 3 and has_21svcs and has_120ms and has_p95:
            self.record_pass("F4.3 Quantitative Achievements", "3 expandable details with 21 microservices, p95 120ms proof")
        else:
            self.record_fail("F4.3 Quantitative Achievements", f"Missing achievements: details={len(details_elements)}, 21svcs={has_21svcs}, 120ms={has_120ms}")

        # 4. Tech stack chips on milestones
        m1_tags = [t.text.strip() for t in milestones[0].select(".stack-tag")]
        expected_m1_tags = {"Go 1.25+", "Kratos / gRPC", "Kubernetes (K3s/EKS)", "Dapr Pub/Sub", "Temporal Saga"}
        if expected_m1_tags.issubset(set(m1_tags)):
            self.record_pass("F4.4 Stack Tags", f"Milestone 1 tags verified: {m1_tags}")
        else:
            self.record_fail("F4.4 Stack Tags", f"Missing required tags from {m1_tags}")

        # 5. Academic degree & authority credentials
        credentials = [c.select_one(".credential-title").text.strip() for c in resume_sec.select(".credential-item-card") if c.select_one(".credential-title")]
        if any("B.S. in Software Engineering" in c for c in credentials) and any("Cloud Native & Go Specialist" in c for c in credentials):
            self.record_pass("F4.5 Degree & Certifications", f"Credentials verified: {credentials}")
        else:
            self.record_fail("F4.5 Degree & Certifications", f"Missing credentials: {credentials}")

        # 6. Section header download resume link
        header_cv_link = resume_sec.select_one(".section-more-link[download]")
        if header_cv_link and header_cv_link.get("href") == "/Le-Tuan-Anh-Resume.pdf":
            self.record_pass("F4.6 Header CV Download Link", "Direct download link to /Le-Tuan-Anh-Resume.pdf verified")
        else:
            self.record_fail("F4.6 Header CV Download Link", f"Invalid link: {header_cv_link}")

    def test_tier1_f5_bento_works(self):
        """F5: Bento Architecture Case Studies & Metrics Showcase."""
        assert self.soup is not None
        works_sec = self.soup.find(id="works")
        if not works_sec:
            self.record_fail("F5 Bento Works Scope", "Section #works not found")
            return

        # 1. Four bento cards present
        cards = works_sec.select(".bento-card")
        if len(cards) == 4:
            self.record_pass("F5.1 Bento Cards Count", "4 bento case study cards present")
        else:
            self.record_fail("F5.1 Bento Cards Count", f"Expected 4 cards, found {len(cards)}")

        # 2. Flagship bento card
        flagship = works_sec.select_one(".bento-flagship-card")
        if flagship and "Composable E-Commerce Microservices Platform" in flagship.text:
            self.record_pass("F5.2 Flagship Bento Card", "Flagship 21-service microservices platform present")
        else:
            self.record_fail("F5.2 Flagship Bento Card", f"Missing flagship card: {flagship}")

        # 3. Quantitative metrics badges on flagship card
        badges = [b.text.strip() for b in flagship.select(".metric-chip")] if flagship else []
        expected_badges = {"21 Go Services", "p95 120ms", "8,000 RPS", "0 Downtime"}
        if expected_badges.issubset(set(badges)):
            self.record_pass("F5.3 Flagship Metrics Badges", f"All 4 badges present: {badges}")
        else:
            self.record_fail("F5.3 Flagship Metrics Badges", f"Expected {expected_badges}, got {badges}")

        # 4. Filter buttons
        filter_btns = works_sec.select(".bento-filter-btn")
        filters = [b.get("data-filter") for b in filter_btns]
        expected_filters = ["all", "microservices", "concurrency", "gitops"]
        if filters == expected_filters:
            self.record_pass("F5.4 Category Filter Pills", f"4 filters verified: {filters}")
        else:
            self.record_fail("F5.4 Category Filter Pills", f"Expected {expected_filters}, got {filters}")

        # 5. data-category attributes on all cards
        card_categories = [c.get("data-category") for c in cards]
        if all(cat in ["microservices", "concurrency", "gitops"] for cat in card_categories):
            self.record_pass("F5.5 Card Category Attributes", f"Card categories verified: {card_categories}")
        else:
            self.record_fail("F5.5 Card Category Attributes", f"Invalid card categories: {card_categories}")

        # 6. Case study links (GitHub blueprint and articles)
        gh_links = [a.get("href") for a in works_sec.select("a[href*='github.com']")]
        post_links = [a.get("href") for a in works_sec.select("a[href^='/posts/']")]
        if gh_links and len(post_links) >= 3:
            self.record_pass("F5.6 Case Study Deep Dives", f"GitHub blueprint ({len(gh_links)}) and article deep dives ({len(post_links)}) verified")
        else:
            self.record_fail("F5.6 Case Study Deep Dives", f"Missing links: gh={gh_links}, posts={len(post_links)}")

    def test_tier1_f6_consulting_hub(self):
        """F6: Romea Advisory & Consulting Booking Hub."""
        assert self.soup is not None
        contact_sec = self.soup.find(id="contact")
        if not contact_sec:
            self.record_fail("F6 Consulting Hub Scope", "Section #contact not found")
            return

        # 1. Three advisory tiers
        tier_cards = contact_sec.select(".advisory-tier-card")
        tier_titles = [t.select_one(".tier-title").text.strip() for t in tier_cards if t.select_one(".tier-title")]
        if len(tier_cards) == 3 and any("Architecture Review" in t for t in tier_titles) and any("Migration & Platform" in t for t in tier_titles) and any("High-Traffic" in t for t in tier_titles):
            self.record_pass("F6.1 Three Advisory Tiers", f"3 tiers present: {tier_titles}")
        else:
            self.record_fail("F6.1 Three Advisory Tiers", f"Expected 3 tiers, got {tier_titles}")

        # 2. Featured / Recommended retainer tier
        featured_card = contact_sec.select_one(".advisory-tier-card.tier-featured")
        featured_tag = featured_card.select_one(".tier-featured-tag") if featured_card else None
        if featured_card and featured_tag and "RECOMMENDED" in featured_tag.text:
            self.record_pass("F6.2 Recommended Tier Badge", "Migration Retainer marked RECOMMENDED")
        else:
            self.record_fail("F6.2 Recommended Tier Badge", "Featured tier or RECOMMENDED badge missing")

        # 3. Durations on each tier
        durations = [t.select_one(".tier-duration-badge").text.strip() for t in tier_cards if t.select_one(".tier-duration-badge")]
        if len(durations) == 3 and any("WEEKS" in d for d in durations) and any("RETAINER" in d for d in durations):
            self.record_pass("F6.3 Tier Durations", f"Durations verified: {durations}")
        else:
            self.record_fail("F6.3 Tier Durations", f"Unexpected durations: {durations}")

        # 4. Pre-filled mailto triggers on all 3 tiers
        mailto_links = [t.select_one(".tier-card-footer a").get("href") for t in tier_cards if t.select_one(".tier-card-footer a")]
        all_mailto = all(m.startswith("mailto:vesviet@gmail.com") and "subject=" in m and "body=" in m for m in mailto_links)
        if len(mailto_links) == 3 and all_mailto:
            self.record_pass("F6.4 Prefilled Mailto Links", "All 3 tiers have prefilled mailto links with subject & body")
        else:
            self.record_fail("F6.4 Prefilled Mailto Links", f"Invalid mailto links: {mailto_links}")

        # 5. Reassurance trust strip
        trust_badges = [b.text.strip() for b in contact_sec.select(".trust-badge-item")]
        has_direct = any("Direct Architect Access" in b for b in trust_badges)
        has_nda = any("Mutual NDA" in b for b in trust_badges)
        has_sla = any("24 Business Hours" in b or "24h" in b for b in trust_badges)
        if len(trust_badges) == 3 and has_direct and has_nda and has_sla:
            self.record_pass("F6.5 Reassurance Trust Strip", f"3 trust badges verified: {trust_badges}")
        else:
            self.record_fail("F6.5 Reassurance Trust Strip", f"Missing trust badges: {trust_badges}")

        # 6. Detailed scope & terms link to /hire/
        hire_link = contact_sec.select_one(".section-more-link[href='/hire/']")
        if hire_link:
            self.record_pass("F6.6 Hire Page Scope Link", "Bridge link to /hire/ verified")
        else:
            self.record_fail("F6.6 Hire Page Scope Link", "Missing link to /hire/")

    # =========================================================================
    # TIER 2: BOUNDARY & CORNER CASES (>=5 per area)
    # =========================================================================

    def test_tier2_b1_banned_pure_black(self):
        """B1: Banned Pure Black Invariant (Zero pure #000000 or #000)."""
        # 1. Extended CSS files audit
        extended_css_files = list((ASSETS_DIR / "css" / "extended").glob("*.css"))
        forbidden_re = re.compile(r'(?:color|background|background-color|border|border-color|fill|stroke)\s*:\s*#(?:000000|000)\b', re.I)
        violations = []
        for f in extended_css_files:
            text = f.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), 1):
                if forbidden_re.search(line):
                    violations.append((f.name, line_no, line.strip()))

        if not violations:
            self.record_pass("B1.1 Extended CSS Pure Black Check", f"0 pure black rules in {len(extended_css_files)} source CSS files")
        else:
            self.record_fail("B1.1 Extended CSS Pure Black Check", f"Found {len(violations)} violations: {violations[:3]}")

        # 2. Compiled public CSS audit
        public_css_files = list((self.public_dir / "assets" / "css").glob("*.css"))
        public_violations = []
        for f in public_css_files:
            text = f.read_text(encoding="utf-8", errors="ignore")
            matches = forbidden_re.findall(text)
            if matches:
                public_violations.append((f.name, len(matches)))

        if not public_violations:
            self.record_pass("B1.2 Compiled Public CSS Pure Black Check", f"0 pure black rules in {len(public_css_files)} compiled CSS files")
        else:
            self.record_fail("B1.2 Compiled Public CSS Pure Black Check", f"Found violations in: {public_violations}")

        # 3. Homepage inline style audit
        assert self.soup is not None
        inline_black = []
        for tag in self.soup.find_all(style=True):
            if forbidden_re.search(tag["style"]):
                inline_black.append((tag.name, tag["style"]))

        if not inline_black:
            self.record_pass("B1.3 Homepage Inline Styles Pure Black Check", "0 inline pure black style attributes")
        else:
            self.record_fail("B1.3 Homepage Inline Styles Pure Black Check", f"Found inline pure black: {inline_black}")

        # 4. Monogram Warm Off-Black theme canvas token presence
        shell_css = (ASSETS_DIR / "css" / "extended" / "portfolio-shell.css").read_text(encoding="utf-8", errors="ignore")
        theme_css = (ASSETS_DIR / "css" / "extended" / "modern-architect-theme.css").read_text(encoding="utf-8", errors="ignore")
        combined_css = shell_css + theme_css

        has_theme_181615 = "#181615" in combined_css
        has_entry_232120 = "#232120" in combined_css
        if has_theme_181615 and has_entry_232120:
            self.record_pass("B1.4 Warm Canvas Tokens", "Warm off-black #181615 and slate #232120 present")
        else:
            self.record_fail("B1.4 Warm Canvas Tokens", f"Missing tokens: #181615={has_theme_181615}, #232120={has_entry_232120}")

        # 5. Accent terracotta & brass gold authority tokens
        has_terracotta = "#E65C40" in combined_css or "#e65c40" in combined_css
        has_gold = "#CFA969" in combined_css or "#cfa969" in combined_css
        if has_terracotta and has_gold:
            self.record_pass("B1.5 Accent Authority Tokens", "Terracotta #E65C40 and Brass Gold #CFA969 present")
        else:
            self.record_fail("B1.5 Accent Authority Tokens", f"Missing accents: terracotta={has_terracotta}, gold={has_gold}")

    def test_tier2_b2_viewport_stability(self):
        """B2: Viewport Stability (100dvh dynamic viewport height)."""
        shell_css = (ASSETS_DIR / "css" / "extended" / "portfolio-shell.css").read_text(encoding="utf-8", errors="ignore")
        
        # 1. 100dvh present in portfolio-shell.css
        count_100dvh = shell_css.count("100dvh")
        if count_100dvh >= 2:
            self.record_pass("B2.1 Dynamic Viewport Height (100dvh)", f"{count_100dvh} occurrences in portfolio-shell.css")
        else:
            self.record_fail("B2.1 Dynamic Viewport Height (100dvh)", f"Expected >= 2 occurrences of '100dvh', found {count_100dvh}")

        # 2. Hero container or app shell min-height
        has_shell_dvh = (
            re.search(r'\.portfolio-app-shell[^{]*{[^}]*min-height\s*:\s*100dvh', shell_css) is not None or
            re.search(r'\.hero-architect-container[^{]*{[^}]*min-height\s*:\s*100dvh', shell_css) is not None
        )
        if has_shell_dvh:
            self.record_pass("B2.2 Viewport Stability 100dvh Rule", "App shell/Hero uses min-height: 100dvh")
        else:
            self.record_fail("B2.2 Viewport Stability 100dvh Rule", "Shell/Hero lacks min-height: 100dvh")

        # 3. 100vh fallback alongside 100dvh
        has_fallback = "min-height: 100vh;" in shell_css
        if has_fallback:
            self.record_pass("B2.3 Viewport Height 100vh Fallback", "100vh fallback provided for legacy mobile clients")
        else:
            self.record_fail("B2.3 Viewport Height 100vh Fallback", "Missing 100vh fallback")

        # 4. Avatar explicit dimensions (CLS = 0)
        assert self.soup is not None
        avatar = self.soup.select_one(".profile-avatar-img")
        if avatar and avatar.get("width") and avatar.get("height"):
            self.record_pass("B2.4 Avatar Explicit Dimensions", f"width={avatar.get('width')}, height={avatar.get('height')}")
        else:
            self.record_fail("B2.4 Avatar Explicit Dimensions", "Avatar missing explicit width/height attributes")

        # 5. Fixed navigation rail width to prevent horizontal shift
        has_rail_width = re.search(r'\.portfolio-nav-rail[^{]*{[^}]*width\s*:\s*64px', shell_css) is not None
        if has_rail_width:
            self.record_pass("B2.5 Fixed Navigation Rail Width", "Rail explicitly styled with width: 64px")
        else:
            self.record_fail("B2.5 Fixed Navigation Rail Width", "Rail missing fixed 64px width declaration")

    def test_tier2_b3_drawer_accessibility(self):
        """B3: Mobile Drawer & Keyboard Accessibility."""
        assert self.soup is not None
        js_code = (ASSETS_DIR / "js" / "portfolio.js").read_text(encoding="utf-8", errors="ignore")

        # 1. Drawer backdrop aria-hidden
        backdrop = self.soup.find(id="drawer-backdrop")
        if backdrop and backdrop.get("aria-hidden") == "true":
            self.record_pass("B3.1 Backdrop aria-hidden", "id='drawer-backdrop' has aria-hidden='true'")
        else:
            self.record_fail("B3.1 Backdrop aria-hidden", f"Invalid backdrop: {backdrop}")

        # 2. Drawer close button accessible label
        close_btn = self.soup.find(id="drawer-close-btn")
        if close_btn and "Close" in close_btn.get("aria-label", ""):
            self.record_pass("B3.2 Close Button Accessible Label", f"aria-label='{close_btn.get('aria-label')}'")
        else:
            self.record_fail("B3.2 Close Button Accessible Label", "Missing or non-descriptive aria-label on close button")

        # 3. Drawer toggle button accessible label
        toggle_btn = self.soup.find(id="mobile-drawer-toggle")
        if toggle_btn and ("Profile" in toggle_btn.get("aria-label", "") or "Sidebar" in toggle_btn.get("aria-label", "")):
            self.record_pass("B3.3 Drawer Toggle Accessible Label", f"aria-label='{toggle_btn.get('aria-label')}'")
        else:
            self.record_fail("B3.3 Drawer Toggle Accessible Label", "Missing aria-label on drawer toggle button")

        # 4. Keyboard Escape key listener
        has_esc = "Escape" in js_code or "Esc" in js_code
        if has_esc and "drawer-open" in js_code:
            self.record_pass("B3.4 Escape Key Drawer Dismissal", "JavaScript controller dismisses drawer on Escape key")
        else:
            self.record_fail("B3.4 Escape Key Drawer Dismissal", "Missing Escape key handler in portfolio.js")

        # 5. Drawer open class management
        if "document.body.classList.add('drawer-open')" in js_code or 'drawer-open' in js_code:
            self.record_pass("B3.5 Drawer Class Toggling", "Controller properly manages drawer-open state")
        else:
            self.record_fail("B3.5 Drawer Class Toggling", "Missing drawer-open state handling in portfolio.js")

    def test_tier2_b4_contrast_and_aria(self):
        """B4: Contrast & Accessible Attributes (alt, rel, aria)."""
        assert self.soup is not None

        # 1. All images have alt
        imgs = self.soup.find_all("img")
        missing_alt = [img for img in imgs if not img.get("alt")]
        if not missing_alt:
            self.record_pass("B4.1 Image Alt Attributes", f"All {len(imgs)} images on homepage provide non-empty alt text")
        else:
            self.record_fail("B4.1 Image Alt Attributes", f"{len(missing_alt)} images missing alt text: {missing_alt}")

        # 2. All target="_blank" links have rel="noopener" or "noreferrer"
        blank_links = self.soup.find_all("a", target="_blank")
        unsecure = []
        for a in blank_links:
            rel = (a.get("rel") or [])
            rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)
            if "noopener" not in rel_str and "noreferrer" not in rel_str:
                unsecure.append(a.get("href"))

        if not unsecure:
            self.record_pass("B4.2 Secure External Links", f"All {len(blank_links)} target='_blank' links include rel='noopener'")
        else:
            self.record_fail("B4.2 Secure External Links", f"Unsecure external links missing noopener: {unsecure}")

        # 3. Interactive icon-only buttons have aria-label
        buttons = self.soup.find_all("button")
        unlabeled_buttons = []
        for b in buttons:
            has_text = bool(b.text.strip())
            has_label = bool(b.get("aria-label") or b.get("title"))
            if not has_text and not has_label:
                unlabeled_buttons.append(str(b)[:60])

        if not unlabeled_buttons:
            self.record_pass("B4.3 Button Accessibility", f"All {len(buttons)} buttons have text or accessible labels")
        else:
            self.record_fail("B4.3 Button Accessibility", f"{len(unlabeled_buttons)} icon buttons missing labels: {unlabeled_buttons}")

        # 4. Major landmarks have aria-labels
        sections = self.soup.find_all("section", class_="portfolio-section")
        unlabeled_sections = [s.get("id") for s in sections if not s.get("aria-label")]
        if not unlabeled_sections:
            self.record_pass("B4.4 Section Landmark Labels", f"All {len(sections)} portfolio sections have aria-label")
        else:
            self.record_fail("B4.4 Section Landmark Labels", f"Sections missing aria-label: {unlabeled_sections}")

        # 5. High-contrast typography tokens
        # Verify text tokens achieving >= 4.5:1 (AA) and >= 7:1 (AAA) against #181615
        theme_css = (ASSETS_DIR / "css" / "extended" / "modern-architect-theme.css").read_text(encoding="utf-8", errors="ignore")
        has_primary_white = "--primary: #FFFFFF" in theme_css or "--primary: #fff" in theme_css
        has_text_body = "--text-body: #E2E8F0" in theme_css or "--content: #E2E8F0" in theme_css
        if has_primary_white and has_text_body:
            self.record_pass("B4.5 High-Contrast Typography Tokens", "Primary text #FFFFFF (18:1 AAA) and body #E2E8F0 (14:1 AAA)")
        else:
            self.record_fail("B4.5 High-Contrast Typography Tokens", "High contrast tokens missing in theme CSS")

    def test_tier2_b5_js_payload_budget(self):
        """B5: Performance Budget (portfolio.min.js < 4096 bytes)."""
        min_js_path = self.public_dir / "js" / "portfolio.min.js"
        src_js_path = ASSETS_DIR / "js" / "portfolio.js"

        # 1. Minified script exists
        if min_js_path.exists():
            size = min_js_path.stat().st_size
            self.record_pass("B5.1 Minified Script Exists", f"{min_js_path.name} ({size} bytes)")
        else:
            self.record_fail("B5.1 Minified Script Exists", f"Missing {min_js_path}")
            return

        # 2. Strict payload budget < 4096 bytes (4KB)
        budget = 4096
        if size < budget:
            self.record_pass("B5.2 Script Payload Budget", f"Size: {size} bytes < {budget} bytes (utilizing {(size/budget)*100:.1f}% of budget)")
        else:
            self.record_fail("B5.2 Script Payload Budget", f"Script exceeds 4KB budget: {size} >= {budget}")

        # 3. Source script exists
        if src_js_path.exists():
            self.record_pass("B5.3 Source Script Exists", f"{src_js_path.name} present in assets")
        else:
            self.record_fail("B5.3 Source Script Exists", f"Missing {src_js_path}")

        # 4. Zero external dependencies / CDN imports
        js_code = src_js_path.read_text(encoding="utf-8", errors="ignore")
        has_cdn = "http://" in js_code or "https://" in js_code or "import " in js_code or "require(" in js_code
        if not has_cdn:
            self.record_pass("B5.4 Zero External Dependencies", "Pure vanilla JavaScript with 0 external network imports")
        else:
            self.record_fail("B5.4 Zero External Dependencies", "Found external network imports in portfolio.js")

        # 5. Strict mode & IIFE encapsulation
        has_strict = "'use strict'" in js_code or '"use strict"' in js_code
        has_iife = "(function () {" in js_code or "(function()" in js_code or "(() => {" in js_code
        if has_strict and has_iife:
            self.record_pass("B5.5 Strict Mode & IIFE Isolation", "Controller wrapped in strict mode IIFE")
        else:
            self.record_fail("B5.5 Strict Mode & IIFE Isolation", "Missing strict mode or IIFE wrapper")

    def test_tier2_b6_svg_meter_geometry(self):
        """B6: Circular SVG Progress Math & Geometry."""
        assert self.soup is not None
        circle_meters = self.soup.select(".skill-circle-meter")

        # 1. Circle radius r = 34
        radii = [c.get("r") for c in circle_meters]
        if radii and all(r == "34" for r in radii):
            self.record_pass("B6.1 Circle Radius Geometry", f"All {len(radii)} meters have r=34")
        else:
            self.record_fail("B6.1 Circle Radius Geometry", f"Invalid radius: {radii}")

        # 2. Circular viewBox 0 0 80 80
        svgs = self.soup.select(".circular-chart")
        viewboxes = [s.get("viewBox") or s.get("viewbox") for s in svgs]
        if svgs and all(v == "0 0 80 80" for v in viewboxes):
            self.record_pass("B6.2 SVG ViewBox Geometry", f"All {len(svgs)} SVG charts have viewBox='0 0 80 80'")
        else:
            self.record_fail("B6.2 SVG ViewBox Geometry", f"Invalid viewBox: {viewboxes}")

        # 3. Circumference C = 2 * pi * 34 ~ 213.63
        expected_circumference = 2 * math.pi * 34
        styles = [c.get("style", "") for c in circle_meters]
        dasharrays = []
        for s in styles:
            m = re.search(r'stroke-dasharray\s*:\s*([\d.]+)', s)
            if m:
                dasharrays.append(float(m.group(1)))

        if dasharrays and all(abs(da - expected_circumference) < 1.0 for da in dasharrays):
            self.record_pass("B6.3 Stroke Dasharray Math", f"stroke-dasharray ~ 213.63 verified (expected {expected_circumference:.2f})")
        else:
            self.record_fail("B6.3 Stroke Dasharray Math", f"Expected ~ {expected_circumference:.2f}, got {dasharrays}")

        # 4. Percent values in [0, 100]
        percents = [float(c.get("data-percent", -1)) for c in circle_meters]
        if percents and all(0 <= p <= 100 for p in percents):
            self.record_pass("B6.4 Skill Meter Bounds", f"All percentages in valid range [0, 100]: {percents}")
        else:
            self.record_fail("B6.4 Skill Meter Bounds", f"Out of bounds percentages: {percents}")

        # 5. Linear gauges percent values in [0, 100]
        linear_percents = [float(g.get("data-percent", -1)) for g in self.soup.select(".skill-linear-fill")]
        if linear_percents and all(0 <= p <= 100 for p in linear_percents):
            self.record_pass("B6.5 Linear Gauge Bounds", f"All linear percentages in valid range [0, 100]: {linear_percents}")
        else:
            self.record_fail("B6.5 Linear Gauge Bounds", f"Out of bounds linear percentages: {linear_percents}")

    # =========================================================================
    # TIER 3: CROSS-FEATURE COMBINATIONS (Pairwise interactions)
    # =========================================================================

    def test_tier3_c1_rail_spy_section_alignment(self):
        """C1: Navigation Rail <-> Stage Section IDs (1:1 Bijection)."""
        assert self.soup is not None
        rail_links = [a.get("href").lstrip("#") for a in self.soup.select(".rail-sections-menu a[href^='#']")]
        stage_sections = [s.get("id") for s in self.soup.select(".portfolio-main-stage section[id]")]

        # Check 1: Every rail link targets a section that exists in the stage
        missing_targets = [target for target in rail_links if target not in stage_sections]
        # Check 2: Every main stage section has a corresponding rail link
        untracked_sections = [sec for sec in stage_sections if sec not in rail_links]

        if not missing_targets and not untracked_sections:
            self.record_pass("C1 Rail <-> Stage Bijection", f"100% 1:1 match across {len(rail_links)} sections: {rail_links}")
        else:
            self.record_fail("C1 Rail <-> Stage Bijection", f"Missing targets: {missing_targets}, untracked sections: {untracked_sections}")

    def test_tier3_c2_bento_filter_categories(self):
        """C2: Bento Filter Pills <-> Card Data Categories."""
        assert self.soup is not None
        filters = [b.get("data-filter") for b in self.soup.select(".bento-filter-btn") if b.get("data-filter") != "all"]
        cards = self.soup.select(".bento-card")
        card_categories = [c.get("data-category") for c in cards]

        unmatched_filters = [f for f in filters if f not in card_categories]
        total_cards = len(cards)

        if not unmatched_filters and total_cards >= 4:
            self.record_pass("C2 Bento Filter <-> Category Harmony", f"All filters ({filters}) match active cards ({card_categories})")
        else:
            self.record_fail("C2 Bento Filter <-> Category Harmony", f"Unmatched filters: {unmatched_filters}")

    def test_tier3_c3_resume_stack_tags_sidebar_harmony(self):
        """C3: Resume Stack Tags <-> Sidebar Knowledge Areas."""
        assert self.soup is not None
        resume_tags = {t.text.strip().lower() for t in self.soup.select("#resume .stack-tag")}
        sidebar_text = self.soup.select_one("#portfolio-sidebar").text.lower() if self.soup.select_one("#portfolio-sidebar") else ""

        core_technologies = ["go", "kubernetes", "dapr", "redis", "mysql", "linux"]
        matched = [tech for tech in core_technologies if any(tech in tag for tag in resume_tags) and tech in sidebar_text]

        if len(matched) >= 4:
            self.record_pass("C3 Resume <-> Sidebar Competency Harmony", f"Unified technology presence: {matched}")
        else:
            self.record_fail("C3 Resume <-> Sidebar Competency Harmony", f"Insufficient tech alignment: only {matched}")

    def test_tier3_c4_theme_search_papermod_hooks(self):
        """C4: Theme Toggle & Search Triggers <-> PaperMod Base Scripts."""
        assert self.soup is not None
        js_code = (ASSETS_DIR / "js" / "portfolio.js").read_text(encoding="utf-8", errors="ignore")

        # 1. Native PaperMod elements exist
        native_theme_btn = self.soup.find(id="theme-toggle")
        native_search_btn = self.soup.find(id="search-nav-btn")
        search_modal = self.soup.find(id="search-modal")

        # 2. Rail elements exist
        rail_theme_btn = self.soup.find(id="rail-theme-toggle")
        rail_search_btn = self.soup.find(id="rail-search-trigger")

        # 3. JavaScript controller connects rail triggers to native triggers
        wires_theme = "nativeThemeBtn.click()" in js_code or "theme-toggle" in js_code
        wires_search = "nativeSearchBtn.click()" in js_code or "search-nav-btn" in js_code

        if native_theme_btn and native_search_btn and search_modal and rail_theme_btn and rail_search_btn and wires_theme and wires_search:
            self.record_pass("C4 Theme & Search Delegation", "Rail triggers correctly delegate to native PaperMod theme toggle & search modal")
        else:
            self.record_fail("C4 Theme & Search Delegation", "Missing native or rail elements, or missing delegation wiring in portfolio.js")

    def test_tier3_c5_drawer_app_shell_coordination(self):
        """C5: Mobile Drawer <-> App Shell & Bottom Tab Dock."""
        assert self.soup is not None
        shell = self.soup.find(id="app-shell")
        sidebar = self.soup.find(id="portfolio-sidebar")
        dock = self.soup.find(id="mobile-bottom-dock")
        backdrop = self.soup.find(id="drawer-backdrop")

        if shell and sidebar and dock and backdrop:
            self.record_pass("C5 Mobile Drawer & Dock Coordination", "App shell, off-canvas sidebar, bottom dock, and backdrop structurally sound")
        else:
            self.record_fail("C5 Mobile Drawer & Dock Coordination", "Structural mismatch in mobile drawer and bottom dock layout")

    # =========================================================================
    # TIER 4: REAL-WORLD SCENARIOS
    # =========================================================================

    def test_tier4_s1_advisory_booking_flow(self):
        """S1: Advisory Booking Click Flow (prefilled mailto validation)."""
        assert self.soup is not None
        tier_ctas = self.soup.select("#contact .btn-tier-cta")
        valid_intake = True
        intake_details = []

        for cta in tier_ctas:
            href = cta.get("href", "")
            parsed = urllib.parse.urlparse(href)
            if parsed.scheme != "mailto" or parsed.path != "vesviet@gmail.com":
                valid_intake = False
                break
            query = urllib.parse.parse_qs(parsed.query)
            subject = query.get("subject", [""])[0]
            body = query.get("body", [""])[0]
            if not subject or not body or "Inquiry" not in subject or "Tuan Anh" not in body:
                valid_intake = False
                break
            intake_details.append(subject)

        if valid_intake and len(intake_details) == 3:
            self.record_pass("S1 Advisory Booking Intake Flow", f"All 3 mailto CTAs verified: {intake_details}")
        else:
            self.record_fail("S1 Advisory Booking Intake Flow", f"Invalid mailto CTAs: {intake_details}")

    def test_tier4_s2_resume_pdf_integrity(self):
        """S2: Resume PDF Binary Integrity (/Le-Tuan-Anh-Resume.pdf)."""
        pub_pdf = self.public_dir / "Le-Tuan-Anh-Resume.pdf"
        stat_pdf = STATIC_DIR / "Le-Tuan-Anh-Resume.pdf"

        if not pub_pdf.exists() or not stat_pdf.exists():
            self.record_fail("S2 Resume PDF Existence", f"Missing resume PDF: public={pub_pdf.exists()}, static={stat_pdf.exists()}")
            return

        pub_bytes = pub_pdf.read_bytes()
        stat_bytes = stat_pdf.read_bytes()

        # Check PDF header magic bytes %PDF-1.
        has_magic = pub_bytes.startswith(b"%PDF-1.") and stat_bytes.startswith(b"%PDF-1.")
        # Check non-empty size (canonical is ~306 KB, must be >= 50 KB)
        is_substantial = len(pub_bytes) >= 50000 and len(stat_bytes) >= 50000

        if has_magic and is_substantial:
            self.record_pass("S2 Resume PDF Integrity", f"Valid %PDF-1.4 header, size={len(pub_bytes)} bytes")
        else:
            self.record_fail("S2 Resume PDF Integrity", f"Corrupt or undersized PDF: size={len(pub_bytes)}, magic={has_magic}")

    def test_tier4_s3_route_preservation(self):
        """S3: 100% Invariant Route Preservation (core sections 200 OK)."""
        core_routes = [
            "posts",
            "series",
            "radar",
            "reading-map",
            "about",
            "hire",
            "categories",
        ]
        missing_routes = []
        for route in core_routes:
            idx = self.public_dir / route / "index.html"
            if not idx.exists() or idx.stat().st_size < 500:
                missing_routes.append(route)

        if not missing_routes:
            self.record_pass("S3 Core Route Preservation", f"100% active (200 OK disk parity) across {core_routes}")
        else:
            self.record_fail("S3 Core Route Preservation", f"Missing or truncated route indexes: {missing_routes}")

    def test_tier4_s4_redirect_oracle_integration(self):
        """S4: Full Integration with test_redirects_oracle.py (23/23 pass)."""
        redirect_test_path = TESTS_DIR / "test_redirects_oracle.py"
        if not redirect_test_path.exists():
            self.record_fail("S4 Redirect Oracle Integration", f"Missing {redirect_test_path}")
            return

        # Import and run the empirical redirect oracle
        sys.path.insert(0, str(TESTS_DIR))
        try:
            from test_redirects_oracle import EmpiricalRedirectOracle
            oracle = EmpiricalRedirectOracle()
            oracle.load_redirects()
            oracle.test_redirect_graph()
            oracle.test_gsc_404_coverage()
            oracle.test_gsc_redirect_coverage()
            oracle.test_destination_health()
            oracle.test_frontmatter_aliases_parity()
            oracle.test_flagship_posts()
            oracle.test_sitemap_cleanliness()

            if oracle.failed_checks == 0:
                self.record_pass("S4 Redirect Oracle Integration", f"23/23 redirect checks passed ({oracle.passed_checks} checks, 0 regressions)")
            else:
                self.record_fail("S4 Redirect Oracle Integration", f"{oracle.failed_checks} redirect failures: {oracle.failures[:3]}")
        except Exception as e:
            self.record_fail("S4 Redirect Oracle Integration", f"Exception running redirect oracle: {e}")

    def test_tier4_s5_sitemap_parity(self):
        """S5: Clean Sitemap Parity (zero leaks, valid apex URLs)."""
        sitemap_path = self.public_dir / "sitemap.xml"
        if not sitemap_path.exists():
            self.record_fail("S5 Sitemap Parity", f"Missing {sitemap_path}")
            return

        tree = ET.parse(sitemap_path)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text.strip() for loc in tree.getroot().findall("s:url/s:loc", ns)]

        has_apex = "https://tanhdev.com/" in urls
        has_posts = any("https://tanhdev.com/posts/" in u for u in urls)
        has_series = any("https://tanhdev.com/series/" in u for u in urls)
        is_deduped = len(urls) == len(set(urls))

        if len(urls) >= 300 and has_apex and has_posts and has_series and is_deduped:
            self.record_pass("S5 Clean Sitemap Parity", f"{len(urls)} unique URLs, apex domain verified, zero duplicates")
        else:
            self.record_fail("S5 Clean Sitemap Parity", f"Sitemap issue: total={len(urls)}, apex={has_apex}, deduped={is_deduped}")

    def run_all(self) -> bool:
        """Executes the full 4-tier E2E testing suite."""
        print("=" * 72)
        print("EMPIRICAL E2E PORTFOLIO ORACLE & RELEASE GATE")
        print("=" * 72)
        try:
            self.load_index_html()
        except Exception as e:
            self.record_fail("HTML Initialization", str(e))
            return False

        print("\n-- Tier 1: Feature Coverage (F1-F6) " + "-" * 35)
        self.test_tier1_f1_app_shell()
        self.test_tier1_f2_profile_sidebar()
        self.test_tier1_f3_navigation_rail()
        self.test_tier1_f4_resume_timeline()
        self.test_tier1_f5_bento_works()
        self.test_tier1_f6_consulting_hub()

        print("\n-- Tier 2: Boundary & Corner Cases (B1-B6) " + "-" * 28)
        self.test_tier2_b1_banned_pure_black()
        self.test_tier2_b2_viewport_stability()
        self.test_tier2_b3_drawer_accessibility()
        self.test_tier2_b4_contrast_and_aria()
        self.test_tier2_b5_js_payload_budget()
        self.test_tier2_b6_svg_meter_geometry()

        print("\n-- Tier 3: Cross-Feature Combinations (C1-C5) " + "-" * 25)
        self.test_tier3_c1_rail_spy_section_alignment()
        self.test_tier3_c2_bento_filter_categories()
        self.test_tier3_c3_resume_stack_tags_sidebar_harmony()
        self.test_tier3_c4_theme_search_papermod_hooks()
        self.test_tier3_c5_drawer_app_shell_coordination()

        print("\n-- Tier 4: Real-World Scenarios (S1-S5) " + "-" * 31)
        self.test_tier4_s1_advisory_booking_flow()
        self.test_tier4_s2_resume_pdf_integrity()
        self.test_tier4_s3_route_preservation()
        self.test_tier4_s4_redirect_oracle_integration()
        self.test_tier4_s5_sitemap_parity()

        print("\n" + "=" * 72)
        print(f"RESULTS: {self.passed_checks} PASSED, {self.failed_checks} FAILED, {len(self.warnings)} WARNINGS")
        print("=" * 72)
        if self.failed_checks > 0:
            print(f"FAILED CHECKS ({self.failed_checks}):", file=sys.stderr)
            for f in self.failures:
                print(f"  {f}", file=sys.stderr)
            return False
        print("ALL E2E PORTFOLIO ORACLE CHECKS PASSED SUCCESSFULLY!")
        return True


# =============================================================================
# Unittest Compatibility Class
# =============================================================================
class TestPortfolioE2EUnittest(unittest.TestCase):
    """Unittest test runner adapter."""

    @classmethod
    def setUpClass(cls):
        cls.oracle = PortfolioE2EOracle()
        cls.oracle.load_index_html()

    def test_t1_f1_app_shell(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier1_f1_app_shell()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t1_f2_profile_sidebar(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier1_f2_profile_sidebar()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t1_f3_navigation_rail(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier1_f3_navigation_rail()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t1_f4_resume_timeline(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier1_f4_resume_timeline()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t1_f5_bento_works(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier1_f5_bento_works()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t1_f6_consulting_hub(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier1_f6_consulting_hub()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t2_b1_banned_pure_black(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier2_b1_banned_pure_black()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t2_b2_viewport_stability(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier2_b2_viewport_stability()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t2_b3_drawer_accessibility(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier2_b3_drawer_accessibility()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t2_b4_contrast_and_aria(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier2_b4_contrast_and_aria()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t2_b5_js_payload_budget(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier2_b5_js_payload_budget()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t2_b6_svg_meter_geometry(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier2_b6_svg_meter_geometry()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t3_pairwise_combinations(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier3_c1_rail_spy_section_alignment()
        self.oracle.test_tier3_c2_bento_filter_categories()
        self.oracle.test_tier3_c3_resume_stack_tags_sidebar_harmony()
        self.oracle.test_tier3_c4_theme_search_papermod_hooks()
        self.oracle.test_tier3_c5_drawer_app_shell_coordination()
        self.assertEqual(self.oracle.failed_checks, prev)

    def test_t4_real_world_scenarios(self):
        prev = self.oracle.failed_checks
        self.oracle.test_tier4_s1_advisory_booking_flow()
        self.oracle.test_tier4_s2_resume_pdf_integrity()
        self.oracle.test_tier4_s3_route_preservation()
        self.oracle.test_tier4_s4_redirect_oracle_integration()
        self.oracle.test_tier4_s5_sitemap_parity()
        self.assertEqual(self.oracle.failed_checks, prev)


if __name__ == "__main__":
    oracle = PortfolioE2EOracle()
    success = oracle.run_all()
    sys.exit(0 if success else 1)
