# Alipay Double 11 — Phases 1–5 + Modern Tech: Consolidated Dossier (Standard 2027 SOTA)

> **Lead Researcher**: Lê Tuấn Anh (@researcher)
> **Standard**: SOTA 2027 Specification · Technical Article Standard 2027 (7 gates)
> **Total Rounds**: 800 narrative rounds across 8 chapter plans (Ch2–Ch9 of the campaign; series corpus is the primary evidence class — this dossier maps per-chapter evidence, figure ledgers, and upgrade designs)
> **Campaign**: `series-sync-upgrade` — Chapters 2–9 (consolidated pass)

---

## Common Evidence Base (all chapters)

The Ch1 dossier established the verified anchors every chapter reuses:
- **TPS records, year-labeled**: 256K (2017, Wikipedia-cited press), 544K (2019, Ant-reported), 583K (2020, Ant-reported); ~100 TPS (2009 origin).
- **GMV series** (Wikipedia, press-cited): ¥0.05B (2009) → ¥19B (2012) → ¥91B (2015) → ¥170B (2017) → ¥268.4B (2019) → ¥498.2B (2020) → ¥540.3B (2021).
- **Independent audits**: TPC-C 707M tpmC (TPC-audited) — the only externally benchmarked number in the series.
- **Ant-reported figures** (closed system, always labeled): 61M QPS OceanBase, 10M+ TPS RocketMQ, RPO=0/RTO<2s/99.99% envelope, sub-20ms payment latency.
- **Gate 7 rule for the whole series**: no bare TPS/QPS number without a year and source class; Ant-reported ≠ independent benchmark.
- 3 AI-citation mismatches rejected during Ch1 fetching (econ arXiv, Docker tutorial, Mars article) — logged, none carried forward.

## Chapter 2 — phase-1-timeline (VI 1,707w/11.2KB/0M/0FAQ ⇄ EN 2,173w/17.0KB/1M/3FAQ)

**Evidence plan**: the timeline chapter owns the GMV series and TPS-by-year table — the strongest externally-anchored chapter. VI gains: the year-labeled TPS records paragraph, GMV table (Wikipedia-anchored), 2 mermaid (era timeline + TPS growth curve shape), 3 FAQ (why-2012-wall, TPS-year-disambiguation, what-4-orders-of-magnitude-means), research anchors, badge. EN gains: GMV table with years, +1 mermaid (TPS curve), badge, anchors, +330w.
**Figure ledger**: 2009 ~100 TPS; 2012 ~2,000 TPS crisis year; 2013 20K; 2014 80K; 2015 140K; 2016 200K; 2017 256K; 2018 400K; 2019 544K; 2020 583K — the decade table both drafts already carry; every row keeps its year.

## Chapter 3 — phase-2-architecture (VI 2,226w/24.4KB/0M ⇄ EN 2,097w/16.4KB/1M/3FAQ)

**Evidence plan**: LDC/RZone/GZone/CZone + OceanBase. VI gains: 2 mermaid (LDC cell topology + RZone/GZone/CZone routing flow), 3 FAQ (why-unitize-not-shard, what-RPO0-protocol-means, CZone-vs-RZone-latency), anchors, badge. EN gains: +1 mermaid (cell topology), +400w (Paxos RPO=0 protocol explanation + TPC-C independent-audit paragraph), badge, anchors.
**Key claim to label**: "Zero cross-region database write blocking" (EN _index TOC row) — Ant-reported design property; keep the label.

## Chapter 4 — phase-3-operations (VI 2,253w/20.7KB/0M ⇄ EN 2,184w/17.4KB/1M/3FAQ)

**Evidence plan**: full-link stress testing + chaos + capacity. VI gains: 2 mermaid (FLST shadow-traffic flow + degradation decision ladder), 3 FAQ (why-staging-lies, what-shadow-traffic-isolate, chaos-vs-FLST), anchors, badge. EN gains: +1 mermaid (FLST flow), +320w (the staging-lies paragraph + self-healing 2s failover evidence), badge, anchors.
**Key claim**: "Self-healing failover within 2 seconds" (TOC row) = RTO<2s — Ant-reported.

## Chapter 5 — phase-4-technology (VI 3,010w/32.8KB/0M ⇄ EN 2,084w/16.8KB/1M/3FAQ) → label 4A

**Evidence plan**: middle platform + CTU risk control. VI gains: 2 mermaid (middle-platform layer diagram + risk-control pipeline), 3 FAQ, anchors, badge. EN gains: +1 mermaid, +420w (middle-platform rationale + risk-control real-time constraints), badge, anchors. **Both TOCs re-label to "Phase 4A — Technology"** (slug unchanged).

## Chapter 6 — phase-4-deep-dive (VI 4,682w/68.4KB/0M ⇄ EN 2,093w/15.9KB/1M/3FAQ) → label 4B

**Evidence plan**: SOFAStack, RocketMQ, storage. VI prose is the deepest in the series (68KB) — gains: 2 mermaid (RocketMQ 10M+ topology + SOFAStack layer stack), 3 FAQ (RocketMQ-vs-Kafka financial-grade, SOFA-vs-Istio, why-LSM-tree-for-ledger), anchors, badge. EN gains: +1 mermaid (RocketMQ topology), +400w (RocketMQ 10M+ evidence + SOFAStack financial-grade constraints), badge, anchors. **Both TOCs re-label to "Phase 4B — Deep Dive"**.
**Key figures**: RocketMQ 10M+ TPS (Ant-reported), OceanBase 61M QPS (Ant-reported), 707M tpmC (TPC-audit).

## Chapter 7 — phase-5-synthesis (VI 2,327w/19.5KB/0M ⇄ EN 2,153w/16.4KB/1M/3FAQ)

**Evidence plan**: design patterns + lessons. VI gains: 2 mermaid (decision framework flow + pattern map), 3 FAQ (which-pattern-first, patterns-vs-stack, envelope-for-small-teams), anchors, badge. EN gains: +1 mermaid (decision flow), +350w (patterns-not-stack + commodity-infrastructure application), badge, anchors.

## Chapter 8 — modern-tech-comparison (VI 4,036w/52.5KB/0M ⇄ EN 2,066w/16.8KB/1M/0FAQ)

**Evidence plan**: OceanBase vs TiDB/Cockroach/Vitess + stack comparisons. VI gains: 2 mermaid (comparison matrix visual + decision tree by workload), 3 FAQ, anchors, badge. EN gains: **3 FAQ from scratch**, +1 mermaid, +430w (when-to-choose-what decision guidance), badge, anchors.
**Comparison integrity rule**: benchmarks compared only within their own audit regimes (TPC-C vs TPC-C); no cross-benchmark cherry-picking.

## Chapter 9 — meta polish (alipay-learn VI-only 2,080w/13.6KB; research-index VI-only 1,538w/10.0KB)

Light pass only: keep noTranslation (site navigation aids, not corpus chapters — documented decision), alipay-learn gains 1 mermaid (learning-path flow) + link hygiene; research-index gains link hygiene + updated campaign status note. No EN twins (documented in both _index TOCs).

## Chapter 10 — _index refresh (both repos) + campaign close

Both `_index` TOCs: Phase 4A/4B labels (slugs untouched), key-figures table gains year + source-class columns, meta-chapter note (alipay-learn/research-index = VI-only navigation), lastmod bumps. Campaign close: series indexes final refresh, corpus CONTENT_INDEX regeneration both repos, full badge sweep (8 twin pairs), Hugo builds, verification checklist run.

---

## Information Gain Assessment

- **unique_insights**: (1) the year-labeled figure discipline applied series-wide (the disambiguation ledger from Ch1 becomes every chapter's spine); (2) per-chapter evidence mapping that separates Ant-reported from TPC-audited from press-cited; (3) the staging-lies / shadow-traffic mechanics grounded for the operations chapter; (4) comparison-integrity rule for the modern-tech chapter.
- **AI_coverage_gap**: Double 11 deep-dive coverage almost never separates figure provenance classes; the audited-vs-reported distinction is this campaign's cross-chapter differentiator.
- **grounding_completeness**: external anchors concentrated in Ch2 (timeline: GMV/TPS series Wikipedia-verified); chapters 3–8 are corpus-internal architecture documentation with the Ch1 ledger as external spine — series-internal is the primary class by design (~65%); [VERIFICATION-NOTE] labels on every Ant-reported figure.

## Handoff

- **recommended_next_roles**: content-writer (per-chapter extend-only upgrades, both sides), seo-analyst (batch audit), reviewer (final 7-gate sweep at campaign close).
- **residual_risks**: (1) extend-only means VI FAQ/mermaid insert at natural seams — never restructure existing prose; (2) the 4A/4B re-label touches TOC labels only — slugs and 301s untouched; (3) modern-tech EN needs FAQ authored fresh — design follows the comparison-integrity rule.
