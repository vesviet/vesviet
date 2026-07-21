#!/bin/bash
# Auto-generate llms-full.txt from content directory
echo "# tanhdev.com Full Text Content" > static/llms-full.txt
echo "" >> static/llms-full.txt
find content/ -name "*.md" | sort | while read f; do
  echo "# File: $f" >> static/llms-full.txt
  cat "$f" >> static/llms-full.txt
  echo "" >> static/llms-full.txt
  echo "---" >> static/llms-full.txt
done
