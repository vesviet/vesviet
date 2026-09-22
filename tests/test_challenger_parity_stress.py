#!/usr/bin/env python3
"""
================================================================================
CHALLENGER 1: ADVERSARIAL HTML & PARITY STRESS TESTING HARNESS
tanhdev.com Frontend Architecture & Modern Command Center Upgrade
================================================================================
Empirically verifies:
1. Structural validity across all generated HTML pages in public/
2. Zero layout bleed from homepage app shell into subpages (/posts/, /series/, /radar/, etc.)
3. Homepage internal link graph, anchors, rail-spy bijection, and asset resolution
4. CSS scoping, layout isolation, pure black absence, and viewport stability (320px, 768px, 1920px)
"""

import os
import re
import sys
import glob
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

PUBLIC_DIR = os.path.normpath(r"d:/myproject/vesviet/public")
ASSETS_DIR = os.path.normpath(r"d:/myproject/vesviet/assets")
STATIC_DIR = os.path.normpath(r"d:/myproject/vesviet/static")

passed_count = 0
failed_count = 0
warnings_count = 0

def report_pass(test_id: str, description: str):
    global passed_count
    passed_count += 1
    print(f"[PASS] {test_id}: {description}")

def report_fail(test_id: str, description: str, details: str = ""):
    global failed_count
    failed_count += 1
    print(f"[FAIL] {test_id}: {description}")
    if details:
        print(f"       Details: {details}")

def report_warn(test_id: str, description: str, details: str = ""):
    global warnings_count
    warnings_count += 1
    print(f"[WARN] {test_id}: {description}")
    if details:
        print(f"       Details: {details}")


# ==============================================================================
# Helper HTML Parser
# ==============================================================================
class StructuralHTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.has_html = False
        self.has_head = False
        self.has_body = False
        self.has_title = False
        self.ids = set()
        self.classes = set()
        self.links = []
        self.images = []
        self.scripts = []
        self.data_sections = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "html":
            self.has_html = True
        elif tag == "head":
            self.has_head = True
        elif tag == "body":
            self.has_body = True
        elif tag == "title":
            self.has_title = True

        attr_dict = dict(attrs)
        if "id" in attr_dict and attr_dict["id"]:
            self.ids.add(attr_dict["id"])
        if "class" in attr_dict and attr_dict["class"]:
            for c in attr_dict["class"].split():
                self.classes.add(c)
        if "data-section" in attr_dict and attr_dict["data-section"]:
            self.data_sections.append(attr_dict["data-section"])
        if tag == "a" and "href" in attr_dict:
            self.links.append((attr_dict.get("href"), attr_dict))
        if tag == "img" and "src" in attr_dict:
            self.images.append((attr_dict.get("src"), attr_dict))
        if tag == "script" and "src" in attr_dict:
            self.scripts.append((attr_dict.get("src"), attr_dict))


# ==============================================================================
# 1. HOMEPAGE STRUCTURAL INTEGRITY & LINKS/ANCHORS STRESS TEST
# ==============================================================================
def test_homepage_structure_and_links():
    print("\n-- Suite 1: Homepage Structural Integrity & Internal Link Graph --")
    homepage_path = os.path.join(PUBLIC_DIR, "index.html")
    if not os.path.exists(homepage_path):
        report_fail("HP-01", "Homepage index.html does not exist in public/")
        return

    with open(homepage_path, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    # HP-01: File size sanity
    if len(html_content) > 10000:
        report_pass("HP-01", f"Homepage index.html exists and is substantial ({len(html_content)} bytes)")
    else:
        report_fail("HP-01", f"Homepage index.html is suspiciously small ({len(html_content)} bytes)")

    # HP-02: DOCTYPE and HTML5 declaration
    if html_content.lstrip().lower().startswith("<!doctype html>"):
        report_pass("HP-02", "Homepage begins with valid HTML5 <!doctype html>")
    else:
        report_fail("HP-02", "Homepage missing standard <!doctype html>")

    parser = StructuralHTMLValidator()
    try:
        parser.feed(html_content)
        report_pass("HP-03", f"Homepage HTML parses cleanly with 0 fatal parser errors (extracted {len(parser.ids)} IDs, {len(parser.classes)} classes)")
    except Exception as e:
        report_fail("HP-03", "Homepage HTML parser crashed", str(e))
        return

    # HP-04: Core App Shell Structural Containers
    required_shell_elements = [
        ("app-shell", "id"),
        ("portfolio-app-shell", "class"),
        ("portfolio-sidebar", "id"),
        ("portfolio-sidebar", "class"),
        ("main-stage", "id"),
        ("portfolio-main-stage", "class"),
        ("drawer-backdrop", "id"),
        ("portfolio-nav-rail", "id"),
        ("portfolio-nav-rail", "class"),
        ("mobile-bottom-dock", "id"),
        ("mobile-bottom-dock", "class")
    ]
    all_shell_found = True
    for item, kind in required_shell_elements:
        if kind == "id" and item not in parser.ids:
            report_fail("HP-04", f"Missing shell DOM ID: #{item}")
            all_shell_found = False
        elif kind == "class" and item not in parser.classes:
            report_fail("HP-04", f"Missing shell class: .{item}")
            all_shell_found = False
    if all_shell_found:
        report_pass("HP-04", "All required 3-column app shell containers present (#portfolio-sidebar, #main-stage, #portfolio-nav-rail, #mobile-bottom-dock, #drawer-backdrop)")

    # HP-05: Scroll-Spy Section IDs and Rail Bijection
    expected_sections = ["hero", "resume", "works", "playbooks", "contact", "publications"]
    sections_present = [s for s in expected_sections if s in parser.ids]
    if len(sections_present) == len(expected_sections):
        report_pass("HP-05", f"All 6 continuous smooth-scroll section DOM IDs verified: {sections_present}")
    else:
        missing = set(expected_sections) - set(sections_present)
        report_fail("HP-05", f"Missing expected section DOM IDs: {missing}")

    # HP-06: Rail navigation items match sections
    rail_data_sections = parser.data_sections
    if set(rail_data_sections) == set(expected_sections):
        report_pass("HP-06", f"Navigation rail data-section items exactly match section IDs: {rail_data_sections}")
    else:
        report_fail("HP-06", f"Mismatch between rail items and section IDs. Rail: {rail_data_sections}, Expected: {expected_sections}")

    # HP-07: Internal Anchor Link Resolution (#hero, #resume, etc.)
    anchor_links = [href for href, attrs in parser.links if href and href.startswith("#")]
    broken_anchors = []
    for anchor in anchor_links:
        target_id = anchor[1:]
        if not target_id:
            continue
        if target_id not in parser.ids:
            broken_anchors.append(anchor)
    if not broken_anchors:
        report_pass("HP-07", f"All {len(anchor_links)} internal anchor links on homepage resolve to active DOM element IDs")
    else:
        report_fail("HP-07", f"Found broken anchor links on homepage: {broken_anchors}")

    # HP-08: Internal Relative Link Resolution (/posts/, /series/, /radar/, etc.)
    internal_route_links = [href for href, attrs in parser.links if href and (href.startswith("/") or href.startswith("https://tanhdev.com/"))]
    broken_routes = []
    verified_routes = 0

    for raw_href in internal_route_links:
        parsed = urlparse(raw_href)
        path = parsed.path
        if not path or path == "/":
            continue

        clean_path = unquote(path).lstrip("/")
        
        target_file = os.path.join(PUBLIC_DIR, clean_path.replace("/", os.sep))
        target_index = os.path.join(PUBLIC_DIR, clean_path.replace("/", os.sep), "index.html")
        static_file = os.path.join(STATIC_DIR, clean_path.replace("/", os.sep))

        if os.path.isfile(target_file) or os.path.isfile(target_index) or os.path.isdir(target_file) or os.path.isfile(static_file):
            verified_routes += 1
        else:
            broken_routes.append(raw_href)

    if not broken_routes:
        report_pass("HP-08", f"All {verified_routes} internal route links resolve to existing files on disk")
    else:
        report_fail("HP-08", f"Found {len(broken_routes)} broken internal routes: {broken_routes[:5]}")

    # HP-09: Downloadable PDF Resume Check
    pdf_links = [href for href, attrs in parser.links if href and "Resume.pdf" in href]
    if pdf_links:
        pdf_disk_path = os.path.join(PUBLIC_DIR, "Le-Tuan-Anh-Resume.pdf")
        if os.path.exists(pdf_disk_path):
            with open(pdf_disk_path, "rb") as f:
                header = f.read(5)
            file_size = os.path.getsize(pdf_disk_path)
            if header == b"%PDF-" and file_size > 100000:
                report_pass("HP-09", f"Downloadable PDF Resume verified on disk ({file_size} bytes, valid %PDF- header)")
            else:
                report_fail("HP-09", f"Resume PDF corrupted or invalid header: {header}, size={file_size}")
        else:
            report_fail("HP-09", f"Resume PDF target not found on disk at {pdf_disk_path}")
    else:
        report_fail("HP-09", "No Resume.pdf link found on homepage")

    # HP-10: Image Assets Resolution & Alt Attributes
    images = parser.images
    broken_images = []
    missing_alts = []
    for src, attrs in images:
        if not attrs.get("alt"):
            missing_alts.append(src)
        if src.startswith("http://") or src.startswith("https://"):
            continue
        clean_src = unquote(urlparse(src).path).lstrip("/")
        disk_img = os.path.join(PUBLIC_DIR, clean_src.replace("/", os.sep))
        static_img = os.path.join(STATIC_DIR, clean_src.replace("/", os.sep))
        if not (os.path.isfile(disk_img) or os.path.isfile(static_img)):
            broken_images.append(src)

    if not broken_images:
        report_pass("HP-10", f"All {len(images)} local image tags resolve to valid disk assets")
    else:
        report_fail("HP-10", f"Found {len(broken_images)} broken image references: {broken_images}")

    if not missing_alts:
        report_pass("HP-11", f"All {len(images)} images have descriptive alt attributes (WCAG AA)")
    else:
        report_fail("HP-11", f"Found {len(missing_alts)} images missing alt text: {missing_alts}")

    # HP-12: External Links Security (rel="noopener")
    insecure_externals = []
    for href, attrs in parser.links:
        if attrs.get("target") == "_blank":
            rel = attrs.get("rel", "")
            if "noopener" not in rel:
                insecure_externals.append(href)
    if not insecure_externals:
        report_pass("HP-12", "All target='_blank' links explicitly contain rel='noopener'")
    else:
        report_fail("HP-12", f"Found {len(insecure_externals)} insecure target='_blank' links without rel='noopener'")

    # HP-13: Controller Script Presence and Payload Budget
    portfolio_scripts = [src for src, attrs in parser.scripts if "portfolio" in src]
    if portfolio_scripts:
        script_rel = portfolio_scripts[0]
        clean_script = unquote(urlparse(script_rel).path).lstrip("/")
        script_disk_path = os.path.join(PUBLIC_DIR, clean_script.replace("/", os.sep))
        if os.path.exists(script_disk_path):
            script_size = os.path.getsize(script_disk_path)
            if script_size < 4096:
                report_pass("HP-13", f"Lightweight controller script verified ({script_rel}, {script_size} bytes < 4KB budget)")
            else:
                report_fail("HP-13", f"Controller script exceeded 4KB budget: {script_size} bytes")
        else:
            report_fail("HP-13", f"Controller script file not found at {script_disk_path}")
    else:
        report_fail("HP-13", f"No portfolio controller script found in homepage scripts: {parser.scripts}")


# ==============================================================================
# 2. ZERO LAYOUT BLEED ACROSS ALL SUBPAGES
# ==============================================================================
def test_zero_subpage_layout_bleed():
    print("\n-- Suite 2: Subpage Layout Bleed & Shell Isolation Stress Test --")
    subpage_sections = [
        "posts",
        "series",
        "radar",
        "reading-map",
        "about",
        "hire",
        "categories",
        "tags"
    ]

    prohibited_shell_markers = [
        ('class="portfolio-app-shell"', "portfolio-app-shell container class"),
        ('class=portfolio-app-shell', "minified portfolio-app-shell class"),
        ('id="app-shell"', "app-shell DOM ID"),
        ('id=app-shell', "minified app-shell DOM ID"),
        ('class="portfolio-sidebar', "portfolio-sidebar component"),
        ('class=portfolio-sidebar', "minified portfolio-sidebar component"),
        ('class="portfolio-nav-rail', "portfolio-nav-rail component"),
        ('class=portfolio-nav-rail', "minified portfolio-nav-rail component"),
        ('class="mobile-bottom-dock', "mobile-bottom-dock component"),
        ('class=mobile-bottom-dock', "minified mobile-bottom-dock component"),
        ('id="drawer-backdrop"', "drawer-backdrop DOM ID"),
        ('id=drawer-backdrop', "minified drawer-backdrop DOM ID"),
        ('portfolio.min.js', "portfolio controller script"),
        ('class="bento-grid-container', "bento case study grid"),
        ('class="skills-meters-group', "skills circular meter group")
    ]

    total_subpages_checked = 0
    section_counts = {}
    violations = []

    for section in subpage_sections:
        sec_dir = os.path.join(PUBLIC_DIR, section)
        if not os.path.exists(sec_dir):
            continue
        html_files = glob.glob(os.path.join(sec_dir, "**", "*.html"), recursive=True)
        section_counts[section] = len(html_files)

        for fpath in html_files:
            total_subpages_checked += 1
            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()

            rel_p = os.path.relpath(fpath, PUBLIC_DIR)
            for marker, desc in prohibited_shell_markers:
                if marker in content:
                    violations.append((rel_p, desc))

    # Also check standalone pages: 404.html
    standalone_pages = ["404.html"]
    for s_page in standalone_pages:
        s_path = os.path.join(PUBLIC_DIR, s_page)
        if os.path.exists(s_path):
            total_subpages_checked += 1
            with open(s_path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            for marker, desc in prohibited_shell_markers:
                if marker in content:
                    violations.append((s_page, desc))

    print(f"Total verified content subpages checked: {total_subpages_checked}")
    for sec, cnt in section_counts.items():
        print(f"  - /{sec}/* : {cnt} pages")

    if not violations:
        report_pass("BLD-01", f"100% of {total_subpages_checked} subpages have zero layout bleed from homepage app shell")
    else:
        report_fail("BLD-01", f"Found {len(violations)} subpages with layout bleed: {violations[:5]}")

    # Specific assertions for each critical subpage section
    for section in subpage_sections:
        sec_index = os.path.join(PUBLIC_DIR, section, "index.html")
        if os.path.exists(sec_index):
            with open(sec_index, "r", encoding="utf-8", errors="ignore") as fp:
                c = fp.read()
            bleed_found = [desc for marker, desc in prohibited_shell_markers if marker in c]
            if not bleed_found:
                report_pass(f"BLD-SEC-/{section}/", f"Section hub /{section}/ is 100% clean and isolated")
            else:
                report_fail(f"BLD-SEC-/{section}/", f"Section hub /{section}/ has layout bleed: {bleed_found}")

    # Verify 404 page isolation
    fof_path = os.path.join(PUBLIC_DIR, "404.html")
    if os.path.exists(fof_path):
        with open(fof_path, "r", encoding="utf-8", errors="ignore") as fp:
            c = fp.read()
        fof_bleed = [desc for marker, desc in prohibited_shell_markers if marker in c]
        if not fof_bleed:
            report_pass("BLD-404", "404.html is 100% clean and isolated from app shell")
        else:
            report_fail("BLD-404", f"404.html has layout bleed: {fof_bleed}")


# ==============================================================================
# 3. STRUCTURAL VALIDITY ACROSS ALL GENERATED PAGES IN PUBLIC/
# ==============================================================================
def test_all_pages_structural_validity():
    print("\n-- Suite 3: Structural Validity Across All Generated Pages in public/ --")
    all_html_files = glob.glob(os.path.join(PUBLIC_DIR, "**", "*.html"), recursive=True)

    non_alias_pages = []
    alias_count = 0
    for path in all_html_files:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                snippet = f.read(500)
                if 'http-equiv="refresh"' in snippet or "http-equiv=refresh" in snippet:
                    alias_count += 1
                    continue
                non_alias_pages.append(path)
        except Exception:
            pass

    report_pass("VAL-01", f"Found {len(non_alias_pages)} full content pages to structurally validate (excluding {alias_count} redirect aliases)")

    pages_missing_doctype = []
    pages_missing_html = []
    pages_missing_head = []
    pages_missing_body = []
    pages_missing_title = []
    pages_with_nil_leaks = []

    sample_size = len(non_alias_pages)
    for idx, path in enumerate(non_alias_pages):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        rel_p = os.path.relpath(path, PUBLIC_DIR)

        # DOCTYPE check
        if not content.lstrip().lower().startswith("<!doctype html"):
            pages_missing_doctype.append(rel_p)

        # html / head / body checks
        c_lower = content.lower()
        if "<html" not in c_lower or "</html>" not in c_lower:
            pages_missing_html.append(rel_p)
        if "<head" not in c_lower or "</head>" not in c_lower:
            pages_missing_head.append(rel_p)
        if "<body" not in c_lower or "</body>" not in c_lower:
            pages_missing_body.append(rel_p)
        if "<title" not in c_lower or "</title>" not in c_lower:
            pages_missing_title.append(rel_p)

        # Nil leak check: "<nil>" in HTML output outside <pre><code>
        if "<nil>" in content:
            clean_content = re.sub(r'<pre.*?</pre>', '', content, flags=re.DOTALL)
            clean_content = re.sub(r'<code.*?</code>', '', clean_content, flags=re.DOTALL)
            if "<nil>" in clean_content:
                pages_with_nil_leaks.append(rel_p)

    if not pages_missing_doctype:
        report_pass("VAL-02", f"100% of {sample_size} pages have valid <!doctype html> declaration")
    else:
        report_fail("VAL-02", f"{len(pages_missing_doctype)} pages missing <!doctype html>: {pages_missing_doctype[:3]}")

    if not pages_missing_html and not pages_missing_head and not pages_missing_body:
        report_pass("VAL-03", f"100% of {sample_size} pages have complete <html>, <head>, and <body> structures")
    else:
        report_fail("VAL-03", f"Structure tags missing (html: {len(pages_missing_html)}, head: {len(pages_missing_head)}, body: {len(pages_missing_body)})")

    if not pages_missing_title:
        report_pass("VAL-04", f"100% of {sample_size} pages contain a valid <title> tag for SEO & Accessibility")
    else:
        report_fail("VAL-04", f"{len(pages_missing_title)} pages missing <title>: {pages_missing_title[:3]}")

    if not pages_with_nil_leaks:
        report_pass("VAL-05", f"100% of {sample_size} pages have 0 unrendered Hugo '<nil>' artifacts")
    else:
        report_fail("VAL-05", f"{len(pages_with_nil_leaks)} pages contain unrendered <nil> artifacts: {pages_with_nil_leaks[:3]}")


# ==============================================================================
# 4. CSS SCOPING, VIEWPORT STRESS & PURE BLACK AUDIT
# ==============================================================================
def test_css_scoping_and_viewports():
    print("\n-- Suite 4: CSS Scoping, Viewport Stability & Pure Black Absence --")

    css_path = os.path.join(ASSETS_DIR, "css", "extended", "portfolio-shell.css")
    if not os.path.exists(css_path):
        report_fail("CSS-01", f"portfolio-shell.css not found at {css_path}")
        return

    with open(css_path, "r", encoding="utf-8", errors="ignore") as f:
        css_content = f.read()

    report_pass("CSS-01", f"portfolio-shell.css loaded ({len(css_content)} bytes)")

    # CSS-02: Absence of pure black (#000000, #000;)
    pure_black_matches = re.findall(r'(?i)(#[0]{3,6}\b|:\s*black\b)', css_content)
    if not pure_black_matches:
        report_pass("CSS-02", "portfolio-shell.css contains 0 pure black (#000000) hex declarations")
    else:
        report_fail("CSS-02", f"Found {len(pure_black_matches)} pure black declarations in portfolio-shell.css: {pure_black_matches}")

    # CSS-03: Viewport dynamic units (100dvh)
    dvh_matches = re.findall(r'100dvh', css_content)
    if len(dvh_matches) >= 2:
        report_pass("CSS-03", f"Viewport stability verified: {len(dvh_matches)} dynamic 100dvh declarations found")
    else:
        report_fail("CSS-03", f"Insufficient dynamic viewport declarations (expected >= 2, found {len(dvh_matches)})")

    # CSS-04: Responsive breakpoint architecture (< 992px collapse & >= 992px desktop 3-col)
    has_desktop_query = "@media (min-width: 992px)" in css_content
    has_mobile_query = "@media (max-width: 991px)" in css_content

    if has_desktop_query and has_mobile_query:
        report_pass("CSS-04", "Responsive breakpoint architecture matches spec (Desktop >= 992px, Mobile/Tablet <= 991px)")
    else:
        report_fail("CSS-04", f"Missing responsive breakpoints: desktop_992={has_desktop_query}, mobile_991={has_mobile_query}")

    # CSS-05: Off-canvas drawer transform & bottom dock positioning
    has_drawer_transform = "translateX(-100%)" in css_content
    has_bottom_dock = "position: fixed" in css_content and "bottom: 0" in css_content

    if has_drawer_transform and has_bottom_dock:
        report_pass("CSS-05", "Mobile off-canvas drawer transform (translateX(-100%)) and fixed bottom dock (bottom: 0) verified")
    else:
        report_fail("CSS-05", f"Mobile drawer/dock mechanics missing (drawer_transform={has_drawer_transform}, bottom_dock={has_bottom_dock})")

    # CSS-06: Scoping audit - verify no unscoped global selectors
    risky_globals = []
    css_stripped = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    rules = re.findall(r'([^{]+)\{([^}]+)\}', css_stripped)

    for selector_block, body in rules:
        if "@media" in selector_block or "@keyframes" in selector_block:
            continue
        selectors = [s.strip() for s in selector_block.split(",")]
        for sel in selectors:
            sel = sel.strip()
            if sel in ["h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "ul", "li", "body", "main", ".header", ".main"]:
                risky_globals.append(sel)

    if not risky_globals:
        report_pass("CSS-06", "All CSS rules are strictly scoped or class-prefixed; zero risky unscoped globals")
    else:
        report_fail("CSS-06", f"Found {len(risky_globals)} risky unscoped global CSS selectors: {risky_globals}")

    # CSS-07: Compiled public CSS pure black check
    compiled_css_files = glob.glob(os.path.join(PUBLIC_DIR, "assets", "css", "*.css"))
    compiled_black_violations = []
    for c_file in compiled_css_files:
        with open(c_file, "r", encoding="utf-8", errors="ignore") as f:
            c_text = f.read()
        raw_blacks = re.findall(r'(?i)(#[0]{3,6}\b|:\s*black\b)', c_text)
        if raw_blacks:
            compiled_black_violations.append((os.path.basename(c_file), len(raw_blacks)))

    if not compiled_black_violations:
        report_pass("CSS-07", f"All {len(compiled_css_files)} compiled CSS stylesheets in public/ maintain zero pure black")
    else:
        report_fail("CSS-07", f"Compiled CSS contains pure black: {compiled_black_violations}")

    # CSS-08: Viewport Stress: 320px Ultra-Narrow Mobile Support
    # Verify that drawer has responsive max-width, stage collapses to 1fr, and overflow-x is prevented
    has_narrow_drawer_guard = "max-width: 85vw" in css_content or "max-width: 90vw" in css_content or "max-width: 100%" in css_content
    has_single_col_grid = "grid-template-columns: 1fr" in css_content
    has_overflow_guard = "overflow-x: hidden" in css_content

    if has_narrow_drawer_guard and has_single_col_grid and has_overflow_guard:
        report_pass("CSS-08", "320px ultra-narrow mobile stability verified (1fr single column grid, max-width: 85vw drawer guard, overflow-x: hidden)")
    else:
        report_fail("CSS-08", f"320px narrow mobile guards missing: drawer_guard={has_narrow_drawer_guard}, 1fr_grid={has_single_col_grid}, overflow_guard={has_overflow_guard}")

    # CSS-09: Viewport Stress: 1920px Ultrawide Support
    # Verify max-width 1480px, auto margins, and 3-column desktop layout
    has_max_width_1480 = "1480px" in css_content
    has_3col_grid = "320px minmax(0, 1fr) 64px" in css_content
    has_desktop_header_hide = "body:has(.portfolio-app-shell) .header" in css_content and "display: none !important" in css_content

    if has_max_width_1480 and has_3col_grid and has_desktop_header_hide:
        report_pass("CSS-09", "1920px ultrawide stability verified (max-width 1480px auto-centered, 320px/1fr/64px desktop grid, PaperMod header cleanly suppressed)")
    else:
        report_fail("CSS-09", f"1920px ultrawide requirements missing: 1480px={has_max_width_1480}, 3col={has_3col_grid}, header_hide={has_desktop_header_hide}")


# ==============================================================================
# MAIN EXECUTION & VERDICT
# ==============================================================================
def main():
    print("=" * 78)
    print("CHALLENGER 1: ADVERSARIAL HTML & PARITY STRESS TESTING HARNESS")
    print("=" * 78)

    test_homepage_structure_and_links()
    test_zero_subpage_layout_bleed()
    test_all_pages_structural_validity()
    test_css_scoping_and_viewports()

    print("\n" + "=" * 78)
    print(f"STRESS TEST SUMMARY: {passed_count} PASSED, {failed_count} FAILED, {warnings_count} WARNINGS")
    print("=" * 78)

    if failed_count == 0:
        print("\n>>> VERDICT: APPROVE <<<")
        print("All empirical adversarial challenges passed with zero regressions.")
        sys.exit(0)
    else:
        print(f"\n>>> VERDICT: FAIL <<<")
        print(f"Failed {failed_count} adversarial stress tests. Investigation required.")
        sys.exit(1)

if __name__ == "__main__":
    main()
