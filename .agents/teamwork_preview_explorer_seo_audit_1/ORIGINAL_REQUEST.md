## 2026-07-15T03:18:12Z

Objective:
Perform a comprehensive technical SEO, content quality, and keyword opportunity audit for the Hugo site 'tanhdev.com' (local directory '/home/user/personalized/vesviet').

Inputs:
- Content directories: 'content/posts/', 'content/series/', 'content/radar/'
- Site cluster map: 'content/reading-map.md'
- Configuration: 'hugo.toml'
- Prior SEO Audit: '/home/user/personalized/seo_audit_report.md'
- Prior Content Quality Report: '/home/user/personalized/vesviet/lowest_quality_posts_report.md'
- Guidelines: '/home/user/personalized/agent-skills/core/roles/seo-analyst.md' and '/home/user/personalized/agent-skills/core/roles/content-manager.md'

Tasks:
1. R1. Technical SEO & Architecture:
   - Analyze internal linking structure, and check for orphan pages.
   - Detect internal links that lack trailing slashes (e.g. '/posts/some-post') since Permalinks are configured as '/posts/:slug/' causing 301 redirects.
   - Check robots.txt and sitemap settings for AI crawler visibility (OAI-SearchBot, PerplexityBot, ClaudeBot, BingBot).
2. R2. Content Quality & E-E-A-T:
   - Evaluate compliance with the 1,400+ words baseline.
   - Audit Answer-First blocks: find articles missing them, having delayed placement, duplicate occurrences under subheadings, or copy-pasted frontmatter descriptions.
   - Audit placeholder FAQ sections: locate files with the generic 'What is [Topic]' templated FAQs.
   - Evaluate E-E-A-T signals (expert quotes, code blocks, configurations, author Person schema).
3. R3. Keyword Gap & Strategy:
   - Identify keyword gaps and strategy recommendations for B2B/Tech/Developer audiences, specifically focusing on System Design, AI Data Engineering, and Magento/E-commerce.
4. Deliverable:
   - Save your detailed analysis report as 'handoff.md' in your working directory: '/home/user/personalized/vesviet/.agents/teamwork_preview_explorer_seo_audit_1/handoff.md'.
   - The report must be highly detailed and cite specific file paths and findings.
   - Report back to the orchestrator (your parent) when finished.
