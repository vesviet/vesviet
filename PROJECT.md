# Project: tanhdev.com Technical SEO & Frontend Optimization Sprint

## Architecture
- Website URL: https://tanhdev.com/
- Static Site Generator: Hugo (with PaperMod theme)
- Deploy Target: Cloudflare Pages
- Code Layout:
  - `content/posts/`, `content/series/`, `content/radar/` — Blog posts and content
  - `content/reading-map.md` — Site cluster mapping
  - `layouts/` — Custom HTML layout templates
  - `assets/` — CSS/JS assets, images, styling
  - `static/` — Static assets (mapped to root during build)
  - `hugo.toml` — Hugo site configuration

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | M1: Canonical URLs & Author Metadata | Resolve duplicate canonicals, self-referential canonical script, author standardization (Tickets 1, 2, 9) | None | DONE |
| 2 | M2: Header Navigation, Accessibility & Dropdowns | Crawlable menu links, ARIA attributes, Escape key close handlers (Tickets 3, 15) | None | DONE |
| 3 | M3: Asset Pipeline, LCP & Responsive Images | Relocate static images to assets, Goldmark render hook, LCP preloading (Tickets 4, 12, 13) | None | DONE |
| 4 | M4: Mermaid Theme Sync & Dynamic Rendering | Add render configuration, dynamic theme switching scripts (Tickets 8, 14) | None | DONE |
| 5 | M5: CSS Hierarchy, Contrast & Typography | Class-based buttons styling, theme variables contrast, code wrapping (Tickets 11, 16, 17) | None | PLANNED |
| 6 | M6: Config, Caching, MCP Schemas & Content Quality | plain-text output formats, llms-full.txt layout, Cloudflare caching, MCP schema validation, Answer-First & FAQ placeholder validations (Tickets 5, 6, 7, 10, 18, 19, 20, 21, 22, 23) | M1, M2, M3, M4, M5 | PLANNED |

## Interface Contracts & Guidelines
- All modifications must follow `guidelines.md` in `/home/user/personalized/agent/vesviet/guidelines.md`.
- Ensure proper syntax and formatting for Hugo frontmatter.
- Static assets relocated from `/static/` to `/assets/` must have updated references in the content files.
