import os

d = "content/radar"
for f in os.listdir(d):
    if not f.endswith(".md") or f == "_index.md": continue
    p = os.path.join(d, f)
    with open(p, "r", encoding="utf-8") as file:
        content = file.read()
    
    parts = content.split("---", 2)
    if len(parts) >= 3:
        fm = parts[1]
        
        # Add ShowToc and TocOpen if not exist
        if "ShowToc:" not in fm:
            fm = fm.rstrip() + "\nShowToc: true\nTocOpen: true\n"
            
        content = parts[0] + "---" + fm + "---" + parts[2]
        
    # Append author-cta
    if "{{< author-cta >}}" not in content:
        content = content.rstrip() + "\n\n{{< author-cta >}}\n"
        
    with open(p, "w", encoding="utf-8") as file:
        file.write(content)

print("Updated all radar posts successfully.")
