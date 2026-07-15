import os
import re

content_dir = "/home/user/personalized/vesviet/content"
link_regex = re.compile(r'\[([^\]]+)\]\((/posts/[^\s)]+|/series/[^\s)]+|/radar/[^\s)]+)\)')

count = 0
for root, _, files in os.walk(content_dir):
    for f in files:
        if f.endswith('.md'):
            p = os.path.join(root, f)
            try:
                with open(p, encoding='utf-8') as file:
                    for i, l in enumerate(file, 1):
                        for a, u in link_regex.findall(l):
                            # Remove anchor or query params to check the main path
                            clean_u = u.split('#')[0].split('?')[0]
                            if not clean_u.endswith('/'):
                                count += 1
                                print(f"{p}:{i} -> {u}")
            except Exception:
                continue

print(f"Total internal links lacking trailing slashes: {count}")
