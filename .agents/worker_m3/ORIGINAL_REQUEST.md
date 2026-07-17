## 2026-07-16T08:49:45Z

You are the Worker for Milestone 3 (Content Quality & E-E-A-T Audit) of the tanhdev.com posts SEO audit.
Your working directory is /home/user/personalized/vesviet/.agents/worker_m3.

Your task is:
1. Write a Python script `audit_posts_content.py` to `/home/user/personalized/vesviet/_internal/audit_posts_content.py`.
2. The script must scan all 58 posts in `/home/user/personalized/vesviet/content/posts/` and perform:
   A. E-E-A-T Audit:
      - Count code blocks (using ```` `).
      - Count Mermaid diagrams (using ````mermaid`).
      - Count Case Study / Telemetry terms (e.g. "case study", "production failure", "symptom:", "root cause:", "impact:", "latency reduced", "RPS", "throughput", etc.).
      - Count Architectural depth terms (e.g. "microservices", "modular monolith", "bounded context", "saga pattern", "consistent hashing", "cqrs", "outbox pattern", etc.).
      - Count SME experience phrases (e.g. "in my experience", "in our production", "we built", "I designed", "I recommend", "my consulting", "my client").
      - Determine E-E-A-T rating:
        * HIGH DEPTH: >= 4 signals AND (code blocks > 0 OR mermaid diagrams > 0).
        * MEDIUM DEPTH: >= 2 signals.
        * LOW DEPTH: < 2 signals.
   B. Answer-First Block Audit:
      - Count occurrences of the tag (e.g. `**Answer-First:**` or `**Answer-first:**`).
      - Check if the Answer-First block is at the very beginning of the post body (first non-empty, non-header line).
      - Check if its content word count is <= 60 words.
      - Check if the Answer-First summary text is unique across all posts.
   C. Placeholder & Boilerplate Check:
      - Scan for phrases: "is a critical architectural pattern or system discussed in this guide", "Unlike legacy systems, **", "introduces modern microservices or event-driven paradigms that scale efficiently", "placeholder FAQ", "Lorem ipsum", "TODO:", "PLACEHOLDER".
   D. Date & Lastmod Formatting Check:
      - Check that `date` and `lastmod` are quoted and contain the "+07:00" timezone offset.
3. Write the detailed JSON output to `/home/user/personalized/vesviet/posts_quality_report.json`.
4. Execute `python3 /home/user/personalized/vesviet/_internal/audit_posts_content.py` from the workspace root.
5. Create your handoff report at `/home/user/personalized/vesviet/.agents/worker_m3/handoff.md` summarizing execution logs, key metrics found (total issues, E-E-A-T rating distribution, files with boilerplate or Answer-First violations, dates/lastmod formatting issues, etc.).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Report completion to parent when done.
