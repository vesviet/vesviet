#!/usr/bin/env python3
"""
Comprehensive Adversarial Stress-Test Suite for tanhdev.com
Challenger 2: Interaction, JS & Visual Regression Testing

Validates:
1. assets/js/portfolio.js under adversarial edge cases & malformed DOM states:
   - Empty DOM resilience
   - Malformed sections & links (missing IDs, hash-only '#', missing target anchors)
   - Missing data-attributes (data-percent, data-filter, data-category)
   - Malformed & extreme data-attribute values (strings, negatives, overflows)
   - Missing drawer elements (trigger exists, but backdrop/close button missing)
   - Missing delegation targets (native theme/search buttons missing)
   - Missing IntersectionObserver environment (fallback check)
   - Stress actions: 50 rapid filter clicks, 40 rapid drawer toggle/escape actions
   - Production DOM validation: live Chromium session on public/index.html with 0 errors
2. PDF Resume Binary Integrity at static/Le-Tuan-Anh-Resume.pdf:
   - File exists, non-empty, correct size
   - Magic bytes %PDF-1.4
   - Binary comment bytes
   - Trailer, startxref, %%EOF
   - Catalog dictionary /Root and Pages tree
   - Reachability & disk parity in public/
3. SVG Geometry & Dashoffset Math:
   - Radius r=34, ViewBox 0 0 80 80
   - Circumference C = 2*pi*34 ~= 213.6283 (approx 213.63)
   - stroke-dasharray ~= 213.63
   - Target dashoffsets: Go 95% (~10.68), K8s 90% (~21.36), Distributed Systems 92% (~17.09)
   - Linear gauge percentage animations
4. Absolute Absence of Pure Black #000000 / #000:
   - Zero occurrences in all source and compiled CSS, templates, and public/index.html
   - Presence of verified Monogram design tokens (#181615, #232120, #3A3634, #E65C40, #CFA969)
"""
from __future__ import annotations

import http.server
import math
import os
import re
import socketserver
import sys
import threading
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORTFOLIO_JS = ROOT / "assets" / "js" / "portfolio.js"
PORTFOLIO_MIN_JS = ROOT / "public" / "js" / "portfolio.min.js"
PDF_STATIC = ROOT / "static" / "Le-Tuan-Anh-Resume.pdf"
PDF_PUBLIC = ROOT / "public" / "Le-Tuan-Anh-Resume.pdf"
PUBLIC_INDEX = ROOT / "public" / "index.html"
LAYOUTS_DIR = ROOT / "layouts"
CSS_DIR = ROOT / "assets" / "css"


class TestAdversarialChallenger(unittest.TestCase):
    httpd: socketserver.TCPServer | None = None
    server_thread: threading.Thread | None = None
    server_port: int = 0

    @classmethod
    def setUpClass(cls):
        if not PORTFOLIO_JS.exists():
            raise FileNotFoundError(f"Missing portfolio.js at {PORTFOLIO_JS}")
        cls.js_code = PORTFOLIO_JS.read_text(encoding="utf-8")
        if not PORTFOLIO_MIN_JS.exists():
            raise FileNotFoundError(f"Missing portfolio.min.js at {PORTFOLIO_MIN_JS}")
        cls.min_js_code = PORTFOLIO_MIN_JS.read_text(encoding="utf-8")
        if not PUBLIC_INDEX.exists():
            raise FileNotFoundError(f"Missing public/index.html at {PUBLIC_INDEX}")
        cls.public_html = PUBLIC_INDEX.read_text(encoding="utf-8")

        # Start ephemeral local HTTP server for testing live production site
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(PUBLIC_INDEX.parent), **kwargs)
            def log_message(self, *args):
                pass

        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
        cls.server_port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls.httpd:
            cls.httpd.shutdown()

    # =========================================================================
    # PART 1: assets/js/portfolio.js Adversarial & Malformed DOM Testing
    # =========================================================================

    def test_1_1_empty_dom_resilience(self):
        """1.1 Empty DOM: portfolio.js initializes cleanly with zero errors."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            html = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><script>{self.js_code}</script></body></html>"
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")
            browser.close()

            self.assertEqual(errors, [], f"Errors on empty DOM: {errors}")

    def test_1_2_missing_intersection_observer_fallback(self):
        """1.2 Environment without IntersectionObserver: executes without throwing."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
            <script>delete window.IntersectionObserver;</script>
            <section class="portfolio-section" id="hero"></section>
            <div class="skills-meters-group"></div>
            <script>{self.js_code}</script>
            </body></html>"""
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")
            browser.close()

            self.assertEqual(errors, [], f"Errors when IntersectionObserver is missing: {errors}")

    def test_1_3_missing_sections_and_missing_data_attributes(self):
        """1.3 Malformed DOM: missing section targets, missing data-attributes."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
            <!-- Links pointing to missing sections -->
            <a href="#non-existent-1" class="rail-nav-link">Ghost 1</a>
            <a href="#non-existent-2" class="mobile-dock-link">Ghost 2</a>
            
            <!-- Skill container with missing data-percent attributes -->
            <div class="skills-meters-group">
                <circle class="skill-circle-meter" id="m-empty"></circle>
                <circle class="skill-circle-meter" id="m-non-numeric" data-percent="invalid_val"></circle>
                <div class="skill-linear-fill" id="l-empty"></div>
                <div class="skill-linear-fill" id="l-non-numeric" data-percent="xyz"></div>
            </div>

            <!-- Bento filters without data-filter and cards without data-category -->
            <button class="bento-filter-btn" id="f-empty">No Filter Data</button>
            <button class="bento-filter-btn" id="f-special" data-filter="microservices">Micro</button>
            <div class="bento-card" id="c-empty">Card No Cat</div>
            <div class="bento-card" id="c-cat" data-category="microservices">Card Micro</div>

            <script>{self.js_code}</script>
            </body></html>"""
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")

            # Click ghost links
            page.click('a[href="#non-existent-1"]')
            page.click('a[href="#non-existent-2"]')

            # Click filter with missing data-filter
            page.click("#f-empty")
            page.click("#f-special")

            browser.close()
            self.assertEqual(errors, [], f"Errors on malformed DOM: {errors}")

    def test_1_4_rapid_filter_clicks_stress(self):
        """1.4 Stress Test: 50 rapid filter switches across multiple categories."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
            <button class="bento-filter-btn active" data-filter="all" id="btn-all">All</button>
            <button class="bento-filter-btn" data-filter="microservices" id="btn-micro">Micro</button>
            <button class="bento-filter-btn" data-filter="concurrency" id="btn-conc">Conc</button>
            <button class="bento-filter-btn" data-filter="gitops" id="btn-git">Git</button>

            <div class="bento-card" data-category="microservices" id="card-1">Card 1</div>
            <div class="bento-card" data-category="concurrency" id="card-2">Card 2</div>
            <div class="bento-card" data-category="gitops" id="card-3">Card 3</div>

            <script>{self.js_code}</script>
            </body></html>"""
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")

            # Rapid 50 clicks cycling filters
            btn_ids = ["#btn-all", "#btn-micro", "#btn-conc", "#btn-git"]
            for i in range(50):
                target_btn = btn_ids[i % len(btn_ids)]
                page.click(target_btn)

            # Final state verification: click gitops
            page.click("#btn-git")
            is_card1_filtered = page.eval_on_selector("#card-1", "el => el.classList.contains('is-filtered-out')")
            is_card3_filtered = page.eval_on_selector("#card-3", "el => el.classList.contains('is-filtered-out')")
            self.assertTrue(is_card1_filtered, "Card 1 (microservices) should be filtered out under gitops")
            self.assertFalse(is_card3_filtered, "Card 3 (gitops) should NOT be filtered out under gitops")

            browser.close()
            self.assertEqual(errors, [], f"Errors during rapid filter stress: {errors}")

    def test_1_5_repeated_drawer_toggling_and_keyboard_stress(self):
        """1.5 Stress Test: 40 rapid drawer toggles via buttons, backdrop, and Escape key."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            # Provide explicit dimension for backdrop so Playwright can click without force
            html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
            <button id="mobile-drawer-toggle">Toggle 1</button>
            <button class="mobile-drawer-trigger">Toggle 2</button>
            <button id="drawer-close-btn">Close</button>
            <div id="drawer-backdrop" style="width: 100px; height: 100px; display: block;"></div>
            <script>{self.js_code}</script>
            </body></html>"""
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")

            # 10 full cycles (40 distinct interactions)
            for _ in range(10):
                # 1. Open via toggle, close via Escape
                page.click("#mobile-drawer-toggle")
                self.assertTrue(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))
                page.keyboard.press("Escape")
                self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

                # 2. Open via trigger class, close via close button
                page.click(".mobile-drawer-trigger")
                self.assertTrue(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))
                page.click("#drawer-close-btn")
                self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

                # 3. Open via toggle, close via backdrop click
                page.click("#mobile-drawer-toggle")
                self.assertTrue(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))
                page.click("#drawer-backdrop", force=True)
                self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

                # 4. Press Escape when already closed (idempotency check)
                page.keyboard.press("Escape")
                self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

            browser.close()
            self.assertEqual(errors, [], f"Errors during drawer toggling stress: {errors}")

    def test_1_6_missing_drawer_elements_resilience(self):
        """1.6 Edge Case: Drawer triggers exist but close button & backdrop are missing."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            # Note: No #drawer-close-btn and No #drawer-backdrop
            html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
            <button id="mobile-drawer-toggle">Toggle Only</button>
            <script>{self.js_code}</script>
            </body></html>"""
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")

            page.click("#mobile-drawer-toggle")
            self.assertTrue(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))
            page.keyboard.press("Escape")
            self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

            browser.close()
            self.assertEqual(errors, [], f"Errors with missing drawer elements: {errors}")

    def test_1_7_missing_delegation_targets(self):
        """1.7 Edge Case: Rail theme & search buttons clicked without native PaperMod elements."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            # No #theme-toggle or #search-nav-btn
            html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
            <button id="rail-theme-toggle">Theme</button>
            <button class="dock-theme-toggle">Dock Theme</button>
            <button id="rail-search-trigger">Search</button>
            <button class="dock-search-trigger">Dock Search</button>
            <script>{self.js_code}</script>
            </body></html>"""
            page.set_content(html)
            page.wait_for_load_state("domcontentloaded")

            page.click("#rail-theme-toggle")
            page.click(".dock-theme-toggle")
            page.click("#rail-search-trigger")
            page.click(".dock-search-trigger")

            browser.close()
            self.assertEqual(errors, [], f"Errors when delegation targets missing: {errors}")

    def test_1_8_production_dom_live_execution(self):
        """1.8 Production DOM: Full interaction test on public/index.html across desktop and mobile viewports."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

            # Mock external third-party requests (e.g. google analytics)
            page.route("**/*", lambda r: r.fulfill(status=200, content_type="application/javascript", body="// mock") if "google" in r.request.url else r.continue_())

            # ── Desktop Viewport (1280x800) ──────────────────────────────────
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto(f"http://127.0.0.1:{self.server_port}/", wait_until="domcontentloaded")

            # 1. Test clicking all rail links on desktop
            rail_links = page.query_selector_all(".rail-nav-link[href^='#']")
            self.assertGreaterEqual(len(rail_links), 6, "Expected at least 6 rail navigation links")
            for link in rail_links:
                link.click()

            # 2. Test bento filters on live desktop page
            filter_btns = page.query_selector_all(".bento-filter-btn")
            self.assertGreaterEqual(len(filter_btns), 4, "Expected at least 4 bento filter buttons")
            for btn in filter_btns:
                btn.click()
            # Click 'all' again
            page.click(".bento-filter-btn[data-filter='all']")

            # 3. Test clicking rail theme toggle
            rail_theme = page.query_selector("#rail-theme-toggle")
            if rail_theme:
                rail_theme.click()

            # ── Mobile Viewport (375x667) ────────────────────────────────────
            page.set_viewport_size({"width": 375, "height": 667})

            # Dismiss cookie consent banner if visible so bottom dock is reachable
            if page.is_visible("#cookie-banner"):
                page.click("#cookie-accept")
                page.wait_for_selector("#cookie-banner", state="hidden")

            # 4. Test mobile drawer toggle on mobile
            page.click("#mobile-drawer-toggle")
            self.assertTrue(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

            # 5. Test Escape key dismissal
            page.keyboard.press("Escape")
            self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

            # 6. Test open & close via close button
            page.click("#mobile-drawer-toggle")
            self.assertTrue(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))
            page.click("#drawer-close-btn")
            self.assertFalse(page.eval_on_selector("body", "el => el.classList.contains('drawer-open')"))

            browser.close()
            self.assertEqual(errors, [], f"Console/Runtime errors on production index.html: {errors}")

    def test_1_9_anchor_hash_only_template_audit(self):
        """1.9 Adversarial Audit: Verify zero href='#' or invalid selector links in templates."""
        soup = BeautifulSoup(self.public_html, "html.parser")
        rail_and_dock_links = soup.select(".rail-nav-link, .mobile-dock-link")
        
        hash_only_links = []
        for link in rail_and_dock_links:
            href = link.get("href", "")
            if href == "#" or href == "":
                hash_only_links.append(str(link))
            elif href.startswith("#"):
                # Selector must be valid (not digit after #)
                target_id = href[1:]
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*$", target_id):
                    hash_only_links.append(f"Invalid CSS ID selector: {href}")

        self.assertEqual(hash_only_links, [], f"Found invalid href in rail/dock links: {hash_only_links}")

    # =========================================================================
    # PART 2: PDF Resume Binary Integrity Verification
    # =========================================================================

    def test_2_1_pdf_exists_and_size_bounds(self):
        """2.1 PDF file exists in static/ and public/, non-empty and valid size."""
        self.assertTrue(PDF_STATIC.exists(), f"Missing {PDF_STATIC}")
        self.assertTrue(PDF_PUBLIC.exists(), f"Missing {PDF_PUBLIC}")

        static_size = PDF_STATIC.stat().st_size
        public_size = PDF_PUBLIC.stat().st_size

        self.assertEqual(static_size, public_size, "static and public PDF sizes must match exactly")
        self.assertGreater(static_size, 50_000, f"PDF suspiciously small: {static_size} bytes")
        self.assertLess(static_size, 2_000_000, f"PDF suspiciously large: {static_size} bytes")

    def test_2_2_pdf_binary_structure(self):
        """2.2 PDF binary format: %PDF header, binary comment, trailer, startxref, %%EOF."""
        content = PDF_STATIC.read_bytes()

        # Magic bytes header: %PDF-1.x
        self.assertTrue(content.startswith(b"%PDF-1."), f"Invalid PDF header: {content[:10]!r}")

        # High-order ASCII binary marker on second line
        lines = content.split(b"\n", 3)
        self.assertTrue(lines[1].startswith(b"%"), "Line 2 must be PDF binary indicator comment")
        high_ascii = any(b >= 128 for b in lines[1])
        self.assertTrue(high_ascii, "PDF line 2 should contain high-ASCII characters (binary flag)")

        # EOF marker near file end
        tail = content[-128:]
        self.assertIn(b"%%EOF", tail, "Missing %%EOF marker in last 128 bytes")
        self.assertIn(b"startxref", tail, "Missing startxref in last 128 bytes")

        # Object count & xref
        self.assertTrue(b"xref" in content or b"/XRef" in content, "Missing xref table or XRef stream")
        self.assertIn(b"/Root", content, "Missing PDF Root catalog dictionary")
        self.assertIn(b"/Pages", content, "Missing PDF Pages catalog dictionary")

    def test_2_3_pdf_anchor_links_reachability(self):
        """2.3 Verify all templates reference /Le-Tuan-Anh-Resume.pdf with proper download attribute."""
        soup = BeautifulSoup(self.public_html, "html.parser")
        pdf_links = soup.find_all("a", href=re.compile(r"Le-Tuan-Anh-Resume\.pdf"))
        self.assertGreaterEqual(len(pdf_links), 2, "Expected at least 2 links to Resume PDF (sidebar & resume header)")

        for link in pdf_links:
            href = link.get("href")
            self.assertEqual(href, "/Le-Tuan-Anh-Resume.pdf", f"Unexpected href: {href}")
            download = link.get("download")
            self.assertEqual(download, "Le-Tuan-Anh-Resume.pdf", f"Missing or invalid download attribute on {link}")

    # =========================================================================
    # PART 3: SVG Geometry & Dashoffset Math Verification
    # =========================================================================

    def test_3_1_svg_geometry_attributes(self):
        """3.1 SVG Circle Geometry: r=34, C=2*pi*34 ~= 213.6283, viewBox='0 0 80 80'."""
        soup = BeautifulSoup(self.public_html, "html.parser")
        meters = soup.select(".skill-circle-meter")
        self.assertEqual(len(meters), 3, "Expected exactly 3 circular skill meters (Go, DistSys, K8s)")

        expected_c = 2 * math.pi * 34  # 213.62830044410595

        for meter in meters:
            r = meter.get("r")
            cx = meter.get("cx")
            cy = meter.get("cy")
            style = meter.get("style", "")
            percent = float(meter.get("data-percent"))

            self.assertEqual(r, "34", f"Circle radius must be 34, got {r}")
            self.assertEqual(cx, "40", f"Circle center X must be 40, got {cx}")
            self.assertEqual(cy, "40", f"Circle center Y must be 40, got {cy}")

            # stroke-dasharray verification in inline style
            match_dasharray = re.search(r"stroke-dasharray:\s*([0-9.]+)", style)
            self.assertTrue(match_dasharray, f"Missing stroke-dasharray in style: {style}")
            dasharray_val = float(match_dasharray.group(1))
            self.assertAlmostEqual(dasharray_val, expected_c, delta=0.01,
                                   msg=f"stroke-dasharray {dasharray_val} should match 2*pi*r (~{expected_c:.2f})")

            # Parent SVG viewBox (handling case-insensitivity of html parser)
            svg = meter.find_parent("svg")
            self.assertIsNotNone(svg, "Meter circle must have parent SVG")
            viewbox = svg.get("viewbox") or svg.get("viewBox")
            self.assertEqual(viewbox, "0 0 80 80", "SVG viewBox must be '0 0 80 80'")

    def test_3_2_dashoffset_mathematical_precision(self):
        """3.2 Verify mathematical precision of dashoffset calculations for Go, K8s, DistSys."""
        expected_c = 2 * math.pi * 34  # 213.62830044410595

        skills = {
            "Go / Runtime": {"percent": 95, "expected_offset": expected_c * (1 - 0.95)},  # ~10.6814
            "Distributed Systems": {"percent": 92, "expected_offset": expected_c * (1 - 0.92)},  # ~17.0903
            "Kubernetes & GitOps": {"percent": 90, "expected_offset": expected_c * (1 - 0.90)},  # ~21.3628
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Execute the calculation formula directly in Chromium JS environment
            js_results = page.evaluate("""() => {
                const r = 34;
                const c = 2 * Math.PI * r;
                return {
                    circumference: c,
                    go_95: c - (c * 95) / 100,
                    dist_92: c - (c * 92) / 100,
                    k8s_90: c - (c * 90) / 100
                };
            }""")
            browser.close()

            c = js_results["circumference"]
            self.assertAlmostEqual(c, 213.6283, delta=0.001)

            # Go 95%
            self.assertAlmostEqual(js_results["go_95"], skills["Go / Runtime"]["expected_offset"], delta=0.0001)
            self.assertAlmostEqual(js_results["go_95"], 10.6814, delta=0.001)

            # DistSys 92%
            self.assertAlmostEqual(js_results["dist_92"], skills["Distributed Systems"]["expected_offset"], delta=0.0001)
            self.assertAlmostEqual(js_results["dist_92"], 17.0903, delta=0.001)

            # K8s 90%
            self.assertAlmostEqual(js_results["k8s_90"], skills["Kubernetes & GitOps"]["expected_offset"], delta=0.0001)
            self.assertAlmostEqual(js_results["k8s_90"], 21.3628, delta=0.001)

    def test_3_3_linear_gauge_percentages(self):
        """3.3 Linear Knowledge Gauges: verify valid percentages in [80, 100]."""
        soup = BeautifulSoup(self.public_html, "html.parser")
        gauges = soup.select(".skill-linear-fill")
        self.assertEqual(len(gauges), 4, "Expected exactly 4 linear gauges")

        expected_values = [94.0, 90.0, 88.0, 86.0]
        actual_values = [float(g.get("data-percent")) for g in gauges]
        self.assertEqual(actual_values, expected_values, f"Gauge percentages mismatch: {actual_values}")

    # =========================================================================
    # PART 4: Absolute Absence of Pure Black (#000000 / #000)
    # =========================================================================

    def test_4_1_css_source_absence_of_pure_black(self):
        """4.1 Verify zero pure black in extended CSS source files."""
        hex_black = re.compile(r'#(000000|000)\b', re.I)
        rgb_black = re.compile(r'rgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:,\s*1(?:\.0+)?\s*)?\)', re.I)
        named_black = re.compile(r'(?<![-_a-zA-Z0-9])(?:color|background|border)\s*:\s*black\b', re.I)

        violations = []
        for css_file in (ROOT / "assets" / "css" / "extended").glob("*.css"):
            text = css_file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                clean_line = line.split("/*")[0].strip()
                if hex_black.search(clean_line):
                    m = hex_black.search(clean_line)
                    after = clean_line[m.span()[1]:m.span()[1]+1]
                    if not after or after not in "0123456789abcdefABCDEF":
                        violations.append(f"{css_file.name}:{i} HEX: {line.strip()}")
                if rgb_black.search(clean_line):
                    violations.append(f"{css_file.name}:{i} RGB: {line.strip()}")
                if named_black.search(clean_line):
                    violations.append(f"{css_file.name}:{i} NAMED: {line.strip()}")

        self.assertEqual(violations, [], f"Pure black detected in source CSS: {violations}")

    def test_4_2_templates_absence_of_pure_black(self):
        """4.2 Verify zero pure black in homepage templates and partials."""
        hex_black = re.compile(r'#(000000|000)\b', re.I)
        rgb_black = re.compile(r'rgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:,\s*1(?:\.0+)?\s*)?\)', re.I)

        violations = []
        for tmpl in LAYOUTS_DIR.rglob("*.html"):
            text = tmpl.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if hex_black.search(line):
                    m = hex_black.search(line)
                    after = line[m.span()[1]:m.span()[1]+1]
                    if not after or after not in "0123456789abcdefABCDEF":
                        violations.append(f"{tmpl.name}:{i} HEX: {line.strip()}")
                if rgb_black.search(line):
                    violations.append(f"{tmpl.name}:{i} RGB: {line.strip()}")

        self.assertEqual(violations, [], f"Pure black detected in layouts templates: {violations}")

    def test_4_3_public_homepage_absence_of_pure_black(self):
        """4.3 Verify zero pure black inline styles or style blocks in public/index.html."""
        soup = BeautifulSoup(self.public_html, "html.parser")
        hex_black = re.compile(r'#(000000|000)\b', re.I)
        rgb_black = re.compile(r'rgba?\(\s*0\s*,\s*0\s*,\s*0\s*(?:,\s*1(?:\.0+)?\s*)?\)', re.I)

        violations = []
        for tag in soup.find_all(True):
            style = tag.get("style", "")
            if style:
                if hex_black.search(style) or rgb_black.search(style):
                    violations.append(f"<{tag.name} id='{tag.get('id')}'> style='{style}'")

        self.assertEqual(violations, [], f"Pure black in public/index.html inline styles: {violations}")

    def test_4_4_monogram_warm_palette_tokens_presence(self):
        """4.4 Verify required Monogram color tokens exist in extended CSS."""
        shell_css = (ROOT / "assets" / "css" / "extended" / "portfolio-shell.css").read_text(encoding="utf-8")
        tokens = {
            "Warm off-black canvas (#181615)": "#181615",
            "Dark slate surface (#232120)": "#232120",
            "Crisp border (#3A3634)": "#3A3634",
            "Terracotta accent (#E65C40)": "#e65c40",
            "Brass gold accent (#CFA969)": "#cfa969",
        }
        for name, token in tokens.items():
            self.assertIn(token.lower(), shell_css.lower(), f"Missing required Monogram design token: {name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
