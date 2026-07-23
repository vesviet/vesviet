#!/bin/bash
# Generate machine-readable content indexes from Hugo source files.
set -euo pipefail

site_url="https://tanhdev.com"
content_root="content"

title_for() {
  awk '
    /^---$/ { delimiters++; next }
    delimiters == 1 && /^title:[[:space:]]*/ {
      value = $0
      sub(/^title:[[:space:]]*/, "", value)
      gsub(/^"|"$/, "", value)
      print value
      exit
    }
  ' "$1"
}

slug_for() {
  awk '
    /^---$/ { delimiters++; next }
    delimiters == 1 && /^slug:[[:space:]]*/ {
      value = $0
      sub(/^slug:[[:space:]]*/, "", value)
      gsub(/^"|"$/, "", value)
      print value
      exit
    }
  ' "$1"
}

route_for() {
  file="$1"
  relative="${file#${content_root}/}"
  section="${relative%%/*}"
  filename="${relative##*/}"
  stem="${filename%.md}"
  slug="$(slug_for "$file")"

  case "$section" in
    posts)
      printf '/posts/%s/' "${slug:-$stem}"
      ;;
    radar)
      printf '/radar/%s/' "${slug:-$stem}"
      ;;
    series)
      path="${relative#series/}"
      if [ "$filename" = "_index.md" ]; then
        path="${path%/_index.md}"
      elif [ "$filename" = "index.md" ]; then
        path="${path%/index.md}"
      else
        path="${path%.md}"
      fi
      printf '/series/%s/' "$path"
      ;;
  esac
}

{
  printf '# tanhdev.com\n\n'
  printf '> Technical writing by Le Tuan Anh on Go, distributed systems, e-commerce architecture, and AI systems.\n\n'
  printf '## Navigation\n\n'
  printf -- '- [Blog](%s/posts/)\n' "$site_url"
  printf -- '- [Series](%s/series/)\n' "$site_url"
  printf -- '- [Tech Radar](%s/radar/)\n' "$site_url"
  printf -- '- [Reading Map](%s/reading-map/)\n\n' "$site_url"

  for section in posts series radar; do
    case "$section" in
      posts) heading='Posts' ;;
      series) heading='Series' ;;
      radar) heading='Tech Radar' ;;
    esac
    printf '## %s\n\n' "$heading"
    find "$content_root/$section" -type f -name '*.md' -print | sort | while IFS= read -r file; do
      if [ "$section" != "series" ] && [ "${file##*/}" = "_index.md" ]; then
        continue
      fi
      title="$(title_for "$file")"
      [ -n "$title" ] || continue
      route="$(route_for "$file")"
      printf -- '- [%s](%s%s)\n' "$title" "$site_url" "$route"
    done
    printf '\n'
  done
} | sed -e '${/^$/d;}' > static/llms.txt

{
  printf '# tanhdev.com Full Text Content\n\n'
  find "$content_root" -type f -name '*.md' -print | sort | while IFS= read -r file; do
    printf '# File: %s\n' "$file"
    cat "$file"
    printf '\n---\n'
  done
} > static/llms-full.txt
