import os
import re
import yaml

workspace_dir = "/home/user/personalized/vesviet"
mermaid_pattern = re.compile(r'```\s*mermaid', re.IGNORECASE)

mismatch_files = []

for root, dirs, files in os.walk(workspace_dir):
    dirs[:] = [d for d in dirs if d not in ['.git', '.agents']]
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            try:
                txt = open(p, encoding='utf-8').read()
            except Exception:
                continue
            
            if mermaid_pattern.search(txt):
                parts = txt.split('---', 2)
                fm_mermaid = False
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1]) or {}
                        fm_mermaid = fm.get('mermaid', False)
                    except Exception:
                        pass
                
                if not fm_mermaid:
                    mismatch_files.append(p)

for path in mismatch_files:
    print(path)
