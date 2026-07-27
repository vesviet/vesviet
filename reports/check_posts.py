import os
import glob
import re

POSTS_DIR = r"d:\myproject\vesviet\content\posts"

FORBIDDEN_TERMS = [
    "seamless",
    "landscape of",
    "comprehensive guide",
    "in conclusion",
    "dive into",
    "delve into",
    "testament to",
    "game-changer",
    "harnessing",
    "realm of",
    "unlocking"
]

def analyze_file(filepath):
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()

    issues = {
        "answer_first": None,
        "lead_ins": [],
        "thin_h2": [],
        "faq": None,
        "boilerplate": [],
        "integrity": []
    }

    # 1. Integrity check (Frontmatter, unclosed code blocks)
    if not content.startswith("---") and not content.startswith("+++"):
        issues["integrity"].append("Missing starting frontmatter delimiter")
    else:
        delim = lines[0].strip()
        close_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == delim:
                close_idx = i
                break
        if close_idx == -1:
            issues["integrity"].append("Unclosed frontmatter delimiter")

    code_block_count = content.count("```")
    if code_block_count % 2 != 0:
        issues["integrity"].append(f"Odd number of code block delimiters ({code_block_count})")

    # 2. Answer-First block check
    h1_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("# "):
            h1_idx = i
            break
    
    if h1_idx == -1:
        issues["answer_first"] = "FAIL: No H1 (# Title) found"
    else:
        af_found = False
        af_text = ""
        for i in range(h1_idx + 1, min(h1_idx + 10, len(lines))):
            line_str = lines[i].strip()
            if line_str.startswith(">") and "Answer-First" in line_str:
                af_found = True
                af_lines = []
                for j in range(i, len(lines)):
                    if lines[j].strip().startswith(">"):
                        af_lines.append(lines[j].strip("> ").strip())
                    else:
                        break
                af_text = " ".join(af_lines)
                break
            elif line_str and not line_str.startswith(">"):
                break
        
        if not af_found:
            issues["answer_first"] = "FAIL: Answer-First blockquote not found immediately after H1"
        else:
            match = re.search(r"\*\*Answer-First:?\*\*\s*(.*)", af_text, re.IGNORECASE)
            if match:
                af_main = match.group(1).split("Key Takeaways")[0].strip()
                words = af_main.split()
                if len(words) > 60:
                    issues["answer_first"] = f"FAIL: Word count {len(words)} > 60 words ({af_main[:30]}...)"
                else:
                    issues["answer_first"] = f"PASS ({len(words)} words)"
            else:
                words = af_text.split()
                if len(words) > 60:
                     issues["answer_first"] = f"FAIL: Blockquote text {len(words)} > 60 words"
                else:
                     issues["answer_first"] = f"PASS ({len(words)} words)"

    # 3. Content expansion (H2 word count >= 40)
    h2_positions = []
    for i, line in enumerate(lines):
        if line.startswith("## ") and not re.match(r"^##\s+(Frequently Asked Questions|FAQ|Related Reading)", line, re.IGNORECASE):
            h2_positions.append((i, line))
    
    for idx, (line_idx, h2_title) in enumerate(h2_positions):
        next_h_idx = len(lines)
        for k in range(line_idx + 1, len(lines)):
            if lines[k].startswith("#"):
                next_h_idx = k
                break
        
        sec_text = " ".join(lines[line_idx+1:next_h_idx])
        clean_sec = re.sub(r"```.*?```", "", sec_text, flags=re.DOTALL)
        clean_sec = re.sub(r"`.*?`", "", clean_sec)
        clean_sec = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean_sec)
        words = clean_sec.split()
        if len(words) < 40:
            issues["thin_h2"].append(f"{h2_title.strip()} ({len(words)} words)")

    # 4. Code blocks and diagrams lead-in check
    in_code = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                prev_line_idx = i - 1
                while prev_line_idx >= 0 and lines[prev_line_idx].strip() == "":
                    prev_line_idx -= 1
                
                if prev_line_idx < 0:
                    issues["lead_ins"].append(f"Line {i+1}: Code block at start of file without lead-in")
                else:
                    prev_str = lines[prev_line_idx].strip()
                    if (prev_str.startswith("#") or 
                        prev_str.startswith("---") or 
                        prev_str.startswith("+++") or 
                        prev_str.startswith("```") or 
                        prev_str.startswith("{{")):
                        issues["lead_ins"].append(f"Line {i+1}: Missing text lead-in before code block (prev line {prev_line_idx+1}: '{prev_str[:40]}')")
            else:
                in_code = False

    # 5. FAQ section check
    faq_idx = -1
    for i, line in enumerate(lines):
        if re.match(r"^##\s+(Frequently Asked Questions|FAQ)", line, re.IGNORECASE):
            faq_idx = i
            break
    
    if faq_idx == -1:
        issues["faq"] = "FAIL: Missing FAQ section (## Frequently Asked Questions)"
    else:
        qa_pairs = []
        curr_q = None
        curr_ans_lines = []
        for i in range(faq_idx + 1, len(lines)):
            line_str = lines[i]
            if line_str.startswith("## ") and not line_str.startswith("### "):
                if curr_q:
                    qa_pairs.append((curr_q, "\n".join(curr_ans_lines)))
                curr_q = None
                break
            elif line_str.startswith("### "):
                if curr_q:
                    qa_pairs.append((curr_q, "\n".join(curr_ans_lines)))
                curr_q = line_str.strip()
                curr_ans_lines = []
            else:
                if curr_q:
                    curr_ans_lines.append(line_str)
        if curr_q:
            qa_pairs.append((curr_q, "\n".join(curr_ans_lines)))

        if len(qa_pairs) < 3:
            issues["faq"] = f"FAIL: Found only {len(qa_pairs)} Q&A pairs (requires >= 3)"
        else:
            short_answers = []
            for q_title, ans_text in qa_pairs:
                clean_ans = re.sub(r"\{\{<.*?>\}\}", "", ans_text)
                clean_ans = re.sub(r"```.*?```", "", clean_ans, flags=re.DOTALL)
                clean_ans = clean_ans.strip()
                
                temp = re.sub(r"\b(e\.g\.|i\.e\.|vs\.|etc\.|fig\.|p99|p50|v1\.|v2\.)", "", clean_ans, flags=re.IGNORECASE)
                sentences = [s.strip() for s in re.split(r"[.!?]+(?:\s+|$)", temp) if len(s.strip()) > 3]
                if len(sentences) < 2:
                    short_answers.append(f"'{q_title}' ({len(sentences)} sentence(s))")
            
            if short_answers:
                issues["faq"] = f"FAIL: Answers with < 2 sentences: {'; '.join(short_answers)}"
            else:
                issues["faq"] = f"PASS ({len(qa_pairs)} pairs, all >= 2 sentences)"

    # 6. AI Boilerplate check
    content_lower = content.lower()
    for term in FORBIDDEN_TERMS:
        matches = [m.start() for m in re.finditer(r"\b" + re.escape(term) + r"\b", content_lower)]
        if matches:
            issues["boilerplate"].append(f"{term} ({len(matches)} match(es))")

    return filename, issues

if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")))
    print(f"Auditing {len(files)} files in {POSTS_DIR}...\n")
    pass_count = 0
    fail_count = 0
    for f in files:
        fname, issues = analyze_file(f)
        c1_pass = issues["answer_first"] and issues["answer_first"].startswith("PASS")
        c2_pass = (len(issues["thin_h2"]) == 0) and (len(issues["lead_ins"]) == 0)
        c3_pass = issues["faq"] and issues["faq"].startswith("PASS")
        c4_pass = len(issues["boilerplate"]) == 0
        c5_pass = len(issues["integrity"]) == 0

        overall_pass = c1_pass and c2_pass and c3_pass and c4_pass and c5_pass
        if overall_pass:
            pass_count += 1
            status = "PASS"
        else:
            fail_count += 1
            status = "FAIL"
        
        print(f"[{status}] {fname} | C1: {'PASS' if c1_pass else 'FAIL'}, C2: {'PASS' if c2_pass else 'FAIL'}, C3: {'PASS' if c3_pass else 'FAIL'}, C4: {'PASS' if c4_pass else 'FAIL'}, C5: {'PASS' if c5_pass else 'FAIL'}")
        if not overall_pass:
            if not c1_pass:
                print(f"  - C1 Answer-First: {issues['answer_first']}")
            if len(issues['thin_h2']) > 0:
                print(f"  - C2 Thin H2 (<40w): {', '.join(issues['thin_h2'])}")
            if len(issues['lead_ins']) > 0:
                print(f"  - C2 Lead-ins: {'; '.join(issues['lead_ins'])}")
            if not c3_pass:
                print(f"  - C3 FAQ: {issues['faq']}")
            if not c4_pass:
                print(f"  - C4 AI Boilerplate: {', '.join(issues['boilerplate'])}")
            if not c5_pass:
                print(f"  - C5 Integrity: {', '.join(issues['integrity'])}")

    print(f"\n==========================================")
    print(f"AUDIT SUMMARY: Total: {len(files)} | PASS: {pass_count} | FAIL: {fail_count} | Pass Rate: {pass_count/len(files)*100:.1f}%")
    print(f"==========================================")

