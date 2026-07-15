import os
import yaml

count = 0
for root, _, files in os.walk('content'):
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8') as file:
                    txt = file.read()
            except Exception:
                continue
            has_mermaid = '```mermaid' in txt
            if has_mermaid:
                parts = txt.split('---', 2)
                fm = {}
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1]) or {}
                    except Exception:
                        pass
                fm_mermaid = fm.get('mermaid', False)
                print(f"File: {p} | has_mermaid: {has_mermaid} | fm_mermaid: {fm_mermaid}")
