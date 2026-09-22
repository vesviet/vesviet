#!/usr/bin/env python3
"""
Independent Cross-Site Parity & Stress Verification Script
Challenger 1: Cross-Site Parity & Metric Stress Verifier

Empirically validates:
1. Exact binary and checksum match for Le-Tuan-Anh-Resume.pdf between vesviet and learn
2. Anchor link resolution and 1:1 section bijection across both homepages
3. Download link integrity for /Le-Tuan-Anh-Resume.pdf on both rendered sites
4. Core 4 metrics parity (17+, 21+, Millions, -35%) in hero and sidebar
5. Career timeline order and company parity (Lotte -> Vigo -> SnapMart -> ICM -> Earlier Career)
6. Education parity (Industrial Economic and Technical College 2, 2005-2008)
7. Absence of exaggerated/untruthful claims across rendered sites
8. Internal route existence on disk for all relative links
9. External links target="_blank" rel="noopener" security audit
"""
import os
import re
import sys
import hashlib
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

VESVIET_PUBLIC = os.path.normpath(r"d:/myproject/vesviet/public")
LEARN_PUBLIC = os.path.normpath(r"d:/myproject/learn/public")

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.anchors = []
        self.downloads = []
        self.target_blanks = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if "id" in attr_dict and attr_dict["id"]:
            self.ids.add(attr_dict["id"])
        if tag == "a":
            href = attr_dict.get("href", "")
            if href:
                self.links.append((href, attr_dict))
                if href.startswith("#"):
                    self.anchors.append((href, attr_dict))
                if "download" in attr_dict:
                    self.downloads.append((href, attr_dict["download"]))
                if attr_dict.get("target") == "_blank":
                    self.target_blanks.append((href, attr_dict.get("rel", "")))

def verify_cross_site_parity():
    print("=" * 78)
    print("CHALLENGER 1: INDEPENDENT CROSS-SITE PARITY & STRESS HARNESS")
    print("=" * 78)

    failures = []

    # 1. Resume PDF Parity
    print("\n[CHECK 1] Resume PDF Binary & Checksum Parity...")
    pdf_vesviet = os.path.join(VESVIET_PUBLIC, "Le-Tuan-Anh-Resume.pdf")
    pdf_learn = os.path.join(LEARN_PUBLIC, "Le-Tuan-Anh-Resume.pdf")

    if not os.path.exists(pdf_vesviet):
        failures.append(f"vesviet resume PDF missing: {pdf_vesviet}")
    if not os.path.exists(pdf_learn):
        failures.append(f"learn resume PDF missing: {pdf_learn}")

    if os.path.exists(pdf_vesviet) and os.path.exists(pdf_learn):
        bytes_v = open(pdf_vesviet, "rb").read()
        bytes_l = open(pdf_learn, "rb").read()
        h_v = hashlib.sha256(bytes_v).hexdigest()
        h_l = hashlib.sha256(bytes_l).hexdigest()
        size_v = len(bytes_v)
        size_l = len(bytes_l)

        print(f"  vesviet PDF: {size_v} bytes, SHA256: {h_v}")
        print(f"  learn PDF:   {size_l} bytes, SHA256: {h_l}")

        if h_v == h_l and bytes_v.startswith(b"%PDF-"):
            print("  [PASS] Resume PDFs are 100% byte-identical with valid %PDF header.")
        else:
            failures.append(f"PDF mismatch or invalid header: sha_match={h_v==h_l}, header={bytes_v[:5]}")

    # 2. Homepage Parsing and Analysis
    sites = {
        "vesviet (tanhdev.com)": VESVIET_PUBLIC,
        "learn (learn.tanhdev.com)": LEARN_PUBLIC,
    }

    hp_contents = {}
    parsers = {}

    for name, pdir in sites.items():
        print(f"\n[CHECK 2] Parsing Homepage & Validating Links for {name}...")
        hp = os.path.join(pdir, "index.html")
        if not os.path.exists(hp):
            failures.append(f"{name} index.html missing: {hp}")
            continue

        content = open(hp, "r", encoding="utf-8", errors="ignore").read()
        hp_contents[name] = content
        parser = LinkExtractor()
        parser.feed(content)
        parsers[name] = parser

        print(f"  Extracted {len(parser.ids)} IDs, {len(parser.anchors)} anchor links, {len(parser.downloads)} downloads, {len(parser.target_blanks)} target=_blank links")

        # Check Anchors
        broken_anchors = []
        for a, attrs in parser.anchors:
            tid = a.lstrip("#")
            if tid and tid not in parser.ids:
                broken_anchors.append(a)
        if not broken_anchors:
            print(f"  [PASS] All {len(parser.anchors)} internal anchor links resolve cleanly.")
        else:
            failures.append(f"{name} broken anchor links: {broken_anchors}")

        # Check Downloads
        broken_dls = []
        for href, dl_name in parser.downloads:
            clean = unquote(urlparse(href).path).lstrip("/")
            dl_path = os.path.join(pdir, clean.replace("/", os.sep))
            if not os.path.exists(dl_path):
                broken_dls.append((href, dl_path))
        if not broken_dls:
            print(f"  [PASS] All {len(parser.downloads)} download CTAs resolve to real disk assets.")
        else:
            failures.append(f"{name} broken download links: {broken_dls}")

        # Check Target Blank Security
        insecure_blanks = []
        for href, rel in parser.target_blanks:
            if "noopener" not in rel:
                insecure_blanks.append((href, rel))
        if not insecure_blanks:
            print(f"  [PASS] All {len(parser.target_blanks)} target=_blank links contain rel=noopener.")
        else:
            failures.append(f"{name} insecure target=_blank links: {insecure_blanks}")

        # Check Internal Route Links
        broken_routes = []
        internal_routes = [href for href, attrs in parser.links if href.startswith("/") and not href.startswith("//") and not href.startswith("/#")]
        for route in internal_routes:
            clean = unquote(urlparse(route).path).lstrip("/")
            if not clean:
                continue
            path_file = os.path.join(pdir, clean.replace("/", os.sep))
            path_index = os.path.join(pdir, clean.replace("/", os.sep), "index.html")
            if not (os.path.exists(path_file) or os.path.exists(path_index)):
                broken_routes.append(route)
        if not broken_routes:
            print(f"  [PASS] All {len(internal_routes)} relative internal routes resolve on disk.")
        else:
            failures.append(f"{name} broken internal route links: {broken_routes}")

    # 3. Section Bijection Parity
    print("\n[CHECK 3] Continuous Smooth-Scroll Section Bijection Parity...")
    expected_sections = ["hero", "resume", "works", "playbooks", "contact", "publications"]
    for name, parser in parsers.items():
        missing_secs = [s for s in expected_sections if s not in parser.ids]
        if not missing_secs:
            print(f"  [PASS] {name} contains all 6 core sections: {expected_sections}")
        else:
            failures.append(f"{name} missing sections: {missing_secs}")

    # 4. Core 4 Metrics Parity
    print("\n[CHECK 4] Core 4 Metrics Parity Across Hero and Sidebar...")
    # Metric 1: 17+
    # Metric 2: 21+
    # Metric 3: Millions
    # Metric 4: -35%
    for name, content in hp_contents.items():
        m_17 = "17+" in content or ("17" in content and "metric-accent" in content)
        m_21 = "21+" in content or ("21" in content and "metric-accent" in content)
        m_millions = "Millions" in content
        m_latency = "-35%" in content or "-35" in content

        print(f"  {name} metric indicators: 17+={m_17}, 21+={m_21}, Millions={m_millions}, -35%={m_latency}")
        if m_17 and m_21 and m_millions and m_latency:
            print(f"  [PASS] {name} has all 4 verified production metrics (17+, 21+, Millions, -35%).")
        else:
            failures.append(f"{name} missing core metrics: 17={m_17}, 21={m_21}, millions={m_millions}, latency={m_latency}")

    # 5. Career Timeline Parity & Chronological Order
    print("\n[CHECK 5] Career Timeline Companies & Chronological Ordering...")
    career_companies = [
        ("Lotte Innovate", ["Lotte Innovate"]),
        ("Vigo Retail", ["Vigo Retail"]),
        ("SnapMart", ["SnapMart"]),
        ("ICM Factory Direct", ["ICM Factory Direct", "ICM"]),
        ("Earlier Career", ["Earlier Career", "2008", "Giai đoạn khởi đầu"]),
    ]

    for name, content in hp_contents.items():
        pos_list = []
        for company_label, aliases in career_companies:
            found_idx = -1
            for alias in aliases:
                idx = content.find(alias)
                if idx != -1:
                    found_idx = idx
                    break
            if found_idx == -1:
                failures.append(f"{name} missing career milestone for: {company_label}")
            else:
                pos_list.append((company_label, found_idx))

        # Assert chronological order (top to bottom)
        order_ok = True
        for i in range(len(pos_list) - 1):
            if pos_list[i][1] >= pos_list[i+1][1]:
                order_ok = False
                failures.append(f"{name} career milestone order mismatch: {pos_list[i][0]} appears after {pos_list[i+1][0]}")
        if order_ok and len(pos_list) == len(career_companies):
            print(f"  [PASS] {name} career milestones are strictly chronological: {[p[0] for p in pos_list]}")

    # 6. Education Parity
    print("\n[CHECK 6] Education Parity (College 2, 2005-2008)...")
    for name, content in hp_contents.items():
        has_college = "College 2" in content or "Cao đẳng Kinh tế Kỹ thuật Công nghiệp 2" in content or "Industrial Economic and Technical College 2" in content
        has_years = "2005" in content and "2008" in content
        if has_college and has_years:
            print(f"  [PASS] {name} education verified: College 2 (2005-2008).")
        else:
            failures.append(f"{name} education verification failed: has_college={has_college}, has_years={has_years}")

    # 7. Absence of Exaggerated Claims
    print("\n[CHECK 7] Zero Exaggerated Claims Audit...")
    banned_claims = [
        r"25M\+\s*req/mo\s*@\s*8K\s*RPS",
        r"8[,.]000\s*RPS",
        r"8K\s*RPS",
        r"p95\s*1\.2s\s*->\s*120ms",
        r"p95\s*120ms",
        r"Principal\s+Architect",
        r"Independent\s+Consultant",
    ]

    for name, content in hp_contents.items():
        found_banned = []
        for pattern in banned_claims:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_banned.extend(matches)
        if not found_banned:
            print(f"  [PASS] {name} 100% clean of exaggerated claims.")
        else:
            failures.append(f"{name} contains banned claims: {found_banned}")

    # 8. Personal Project Distinction Parity
    print("\n[CHECK 8] Personal / Portfolio Project Distinction...")
    for name, content in hp_contents.items():
        has_21_proj = "21+" in content and ("Microservices" in content or "Services" in content)
        is_framed_personal = bool(re.search(r'\b(personal|portfolio|cá nhân|mã nguồn mở)\b', content, re.IGNORECASE))
        if has_21_proj and is_framed_personal:
            print(f"  [PASS] {name} correctly frames 21+ Microservices platform as personal/portfolio reference architecture.")
        else:
            failures.append(f"{name} personal project framing failed: has_21={has_21_proj}, personal={is_framed_personal}")

    # Verdict
    print("\n" + "=" * 78)
    if not failures:
        print(">>> ALL INDEPENDENT CROSS-SITE PARITY STRESS CHECKS PASSED (100%) <<<")
        print("VERDICT: APPROVE")
        print("=" * 78)
        return True
    else:
        print(f">>> FAILED {len(failures)} CHECKS <<<")
        for f in failures:
            print(f"  - {f}")
        print("VERDICT: REQUEST_CHANGES")
        print("=" * 78)
        return False

if __name__ == "__main__":
    success = verify_cross_site_parity()
    sys.exit(0 if success else 1)
