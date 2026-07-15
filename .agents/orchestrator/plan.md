# Execution Plan: Technical SEO, Content Quality, and Keyword Gap Audit for tanhdev.com

This plan details the steps required to execute the comprehensive SEO analysis and content audit for https://tanhdev.com/ using the vesviet workspace.

## Objectives
1. Analyze Technical SEO & Architecture (internal links, silo structure, reading-map).
2. Evaluate Content Quality (EEAT, Answer-First compliance, keyword density, word length).
3. Discover Keyword Opportunities (System Design, AI Data Engineering, Magento/E-commerce).
4. Produce a complete SEO Audit Report at `/home/user/personalized/vesviet/seo_audit_report.md` with a detailed Action Plan.
5. Obtain cross-agent review and approvals from SEO Analyst and Content Manager roles.

## Phased Approach

### Phase 1: Exploration
- **Spawn Agent**: `teamwork_preview_explorer` (Role: "SEO Analyst Explorer")
- **Task**:
  - Crawl/inspect content files in `content/posts/`, `content/series/`, `content/radar/` and `content/reading-map.md`.
  - Analyze internal links structure, find orphan pages, broken links, missing trailing slashes.
  - Assess content quality, specifically Answer-First block alignment, E-E-A-T signals, word counts, and placeholder FAQ sections.
  - Investigate keyword alignment and spot cannibalization risks.
  - Formulate keyword gaps in System Design, AI Data Engineering, and Magento/E-commerce.
  - Write detailed findings and structured data outputs in its directory.

### Phase 2: Report Drafting
- **Spawn Agent**: `teamwork_preview_worker` (Role: "Senior SEO Analyst")
- **Task**:
  - Consume Explorer findings.
  - Synthesize findings into the final `/home/user/personalized/vesviet/seo_audit_report.md` report.
  - The report must comply with the SEO Analyst role standard and provide a clear, actionable plan pointing to specific files/articles to fix/write.

### Phase 3: Cross-Agent Review & Approval
- **Spawn Agent 1**: `teamwork_preview_reviewer` (Role: "Content Manager Reviewer")
  - **Task**: Review `/home/user/personalized/vesviet/seo_audit_report.md` against E-E-A-T guidelines, brand rules, and content quality.
- **Spawn Agent 2**: `teamwork_preview_reviewer` (Role: "SEO Analyst Peer Reviewer")
  - **Task**: Review the report's technical SEO correctness, keyword strategy, and linking issues.
- **Goal**: Reconcile reviews, verify pass gates, and produce a clean report.

### Phase 4: Final Sign-off
- Synthesize all review verdicts.
- Report completion to parent/sentinel.
