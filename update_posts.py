import os
import re

d = "content/posts"
for f in os.listdir(d):
    if not f.endswith(".md"): continue
    p = os.path.join(d, f)
    with open(p, "r", encoding="utf-8") as file:
        content = file.read()
    
    parts = content.split("---", 2)
    if len(parts) >= 3:
        fm = parts[1]
        
        # Add ShowToc and TocOpen if not exist
        if "ShowToc:" not in fm:
            fm = fm.rstrip() + "\nShowToc: true\nTocOpen: true\n"
        
        # Fix missing tags and categories
        if "leaseinvietnam" in f:
            fm = re.sub(r'(?m)^categories:\s*$', 'categories:\n  - "AI/ML"\n  - "Product Development"', fm)
            fm = re.sub(r'(?m)^tags:\s*$', 'tags:\n  - "Automation"\n  - "LLM"\n  - "System Design"', fm)
        elif "hybrid-ai" in f:
            fm = re.sub(r'(?m)^categories:\s*$', 'categories:\n  - "AI/ML"\n  - "Engineering"', fm)
            fm = re.sub(r'(?m)^tags:\s*$', 'tags:\n  - "LLM"\n  - "Automation"\n  - "Architecture"', fm)
        elif "deploying-astro" in f:
            fm = re.sub(r'(?m)^categories:\s*$', 'categories:\n  - "Architecture"\n  - "Engineering"\n  - "Cloudflare"', fm)
            fm = re.sub(r'(?m)^tags:\s*$', 'tags:\n  - "Astro"\n  - "Cloudflare"\n  - "Edge Computing"\n  - "WordPress"', fm)
            
        content = parts[0] + "---" + fm + "---" + parts[2]
        
    # Append author-cta
    if "{{< author-cta >}}" not in content:
        content = content.rstrip() + "\n\n{{< author-cta >}}\n"
        
    with open(p, "w", encoding="utf-8") as file:
        file.write(content)

print("Updated all posts successfully.")
