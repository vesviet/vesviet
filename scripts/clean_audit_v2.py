import os
import re

base_dir = r"d:\myproject\vesviet\content"

cat1_pattern = re.compile(r"> \*\*Answer-First:\*\* Architecting production-ready solutions for .*? within the .*? domain requires strict component separation, sub-50ms P99 latency guarantees, explicit error handling, and comprehensive telemetry instrumentation\.", re.IGNORECASE)
cat2_pattern = re.compile(r"The .*? outlines the end-to-end data flow, service boundaries, and asynchronous messaging pipelines required for enterprise-grade high-concurrency systems\.", re.IGNORECASE)
cat3_pattern = re.compile(r"To scale .*? effectively, engineering teams implement Redis Cluster cache-aside patterns with\s*randomized TTL jitter\. Stale-while-revalidate caching reduces database query pressure during cache\s*stampedes\.(To scale .*? effectively\.\.\.)?", re.IGNORECASE)
cat3_dup_pattern = re.compile(r"To scale .*? effectively\.\.\.", re.IGNORECASE)

cleaned_count = 0
for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".md"):
            full_path = os.path.join(root, file)
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            orig_content = content
            
            content = cat1_pattern.sub("", content)
            content = cat2_pattern.sub("", content)
            content = cat3_pattern.sub("", content)
            content = cat3_dup_pattern.sub("", content)
            
            # Clean up empty lines that might have been left behind
            content = re.sub(r'\n[ \t]*\n[ \t]*\n', '\n\n', content)
            
            if orig_content != content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                cleaned_count += 1
                print(f"Cleaned {full_path}")

print(f"\nTotal files cleaned: {cleaned_count}")
