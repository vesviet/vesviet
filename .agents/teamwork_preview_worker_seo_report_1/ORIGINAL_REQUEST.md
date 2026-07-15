## 2026-07-15T03:23:09Z

You are a teamwork_preview_worker running as 'Senior SEO Analyst'.
Your working directory (for agent metadata) is '/home/user/personalized/vesviet/.agents/teamwork_preview_worker_seo_report_1/'.
The user's project workspace directory is '/home/user/personalized/vesviet'.

Objective:
Draft the final, comprehensive SEO Audit Report for 'tanhdev.com' based on the findings gathered by the Explorer subagent.

Inputs:
- Explorer's findings: '/home/user/personalized/vesviet/.agents/teamwork_preview_explorer_seo_audit_1/handoff.md'
- Prior SEO Audit: '/home/user/personalized/seo_audit_report.md'
- Prior Quality Report: '/home/user/personalized/vesviet/lowest_quality_posts_report.md'
- Rules & Guidelines: '/home/user/personalized/agent-skills/core/roles/seo-analyst.md' and '/home/user/personalized/agent-skills/core/roles/content-manager.md'

Tasks:
1. Write a comprehensive, master-level SEO Audit Report in Vietnamese.
2. Save the report to the exact target path: '/home/user/personalized/vesviet/seo_audit_report.md'.
3. The report must contain:
   - Context, executive summary, and project details (Hugo static site, PaperMod theme, deploy to Cloudflare Pages).
   - Technical SEO & Architecture: Detailed explanation of the 72 trailing slash redirect issues (provide specific files and lines as examples), 76 orphan and 52 dead-end pages, Robots.txt AI bot crawler allowed/blocked rules, and dropdown resources menu crawlability fallback.
   - On-page SEO & E-E-A-T: Word count compliance analysis (specifying the 3 thin posts that fail the 1,400+ words target), 100% Answer-First compliance across posts, placeholder FAQ cleanup (citing examples of the updated FAQs), Mermaid configuration mismatches (citing the 47 files with body diagrams but missing frontmatter flag), and structured data/schema setup (Article JSON-LD linked to Person Lê Tuấn Anh).
   - Keyword Gap & Strategy: Core opportunities in System Design, AI Data Engineering, and Magento/E-commerce.
   - Detailed Action Plan: A structured table/list outlining the exact files to modify (trailing slashes, Mermaid flags, thin post expansions) and the new topics to write.
4. Verify the file exists and is correctly formatted.
5. Report completion back to your parent orchestrator.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
