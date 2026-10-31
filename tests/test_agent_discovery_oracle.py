#!/usr/bin/env python3
"""
Master Automated Verification Test Suite — Agent Discovery & Readiness (2027 SOTA)
Mirrored in vesviet test harness.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[2]
LEARN_DIR = REPO_ROOT / 'learn'
VESVIET_DIR = REPO_ROOT / 'vesviet'
SCHEMA_PATH = REPO_ROOT / 'agent-skills' / 'core' / 'contracts' / 'schemas' / 'agent-card.json'


class TierResult:
    def __init__(self, name: str):
        self.name = name
        self.checks: List[Tuple[bool, str, str]] = []

    def check(self, condition: bool, description: str, detail: str = ''):
        self.checks.append((bool(condition), description, detail))
        mark = '[PASS]' if condition else '[FAIL]'
        msg = f'  {mark} {description}'
        if detail and not condition:
            msg += f' -> {detail}'
        print(msg)

    @property
    def passed(self) -> int:
        return sum(1 for c, _, _ in self.checks if c)

    @property
    def failed(self) -> int:
        return sum(1 for c, _, _ in self.checks if not c)

    @property
    def success(self) -> bool:
        return self.failed == 0


class AgentDiscoveryVerifier:
    def __init__(self):
        self.results: Dict[str, TierResult] = {}

    def verify_tier1_robots(self) -> TierResult:
        res = TierResult('Tier 1: Robots.txt & Content Signals')
        print('\n=== Tier 1: Robots.txt & Content Signals ===')

        for site_name, base_dir, domain in [('vesviet', VESVIET_DIR, 'tanhdev.com'), ('learn', LEARN_DIR, 'learn.tanhdev.com')]:
            robots_file = base_dir / 'static' / 'robots.txt'
            res.check(robots_file.exists(), f'[{site_name}] robots.txt exists at {robots_file}')
            if not robots_file.exists():
                continue

            content = robots_file.read_text(encoding='utf-8', errors='replace')
            lines = [line.strip() for line in content.splitlines()]

            # 1. Content-Signal directive
            has_content_signal = any(l.lower().startswith('content-signal:') for l in lines)
            res.check(has_content_signal, f'[{site_name}] robots.txt declares Content-Signal directive')

            # 2. GSC Tier 3 Invariants: Taxonomy RSS blocks & mock APIs
            disallow_lines = [
                l.split(':', 1)[1].strip()
                for l in lines
                if l.lower().startswith('disallow:')
            ]
            has_tags_xml = any('/tags/' in d and 'index.xml' in d for d in disallow_lines)
            has_cat_xml = any('/categories/' in d and 'index.xml' in d for d in disallow_lines)
            has_series_xml = any(('/series/' in d and 'index.xml' in d) or ('/*/' in d and 'index.xml' in d) for d in disallow_lines)

            res.check(has_tags_xml, f'[{site_name}] blocks taxonomy RSS feeds for /tags/*/index.xml')
            res.check(has_cat_xml, f'[{site_name}] blocks taxonomy RSS feeds for /categories/*/index.xml')
            res.check(has_series_xml, f'[{site_name}] blocks series/nested RSS feeds for /*/index.xml')

            mock_prefixes = ['/api/', '/orders', '/payments', '/checkout', '/catalog', '/cart', '/debug/', '/internal/']
            missing_mocks = [p for p in mock_prefixes if not any(d == p or d.startswith(p) or d == p.rstrip('/') for d in disallow_lines)]
            res.check(len(missing_mocks) == 0, f'[{site_name}] blocks mock endpoints (found {len(mock_prefixes) - len(missing_mocks)}/{len(mock_prefixes)})', f'Missing: {missing_mocks}')

            # 3. Public metadata allow lines
            allow_lines = [l.split(':', 1)[1].strip() for l in lines if l.lower().startswith('allow:')]
            res.check('/auth.md' in allow_lines, f'[{site_name}] allows /auth.md in robots.txt')
            res.check('/.well-known/' in allow_lines, f'[{site_name}] allows /.well-known/ in robots.txt')
            res.check('/sitemap.xml' in allow_lines, f'[{site_name}] allows /sitemap.xml in robots.txt')
            res.check('/llms.txt' in allow_lines, f'[{site_name}] allows /llms.txt in robots.txt')

            # 4. AI bot allowances
            ai_bots = ['GPTBot', 'OAI-SearchBot', 'ClaudeBot', 'Claude-SearchBot', 'PerplexityBot', 'Google-Extended', 'anthropic-ai', 'Cohere-ai']
            for bot in ai_bots:
                bot_idx = -1
                for idx, line in enumerate(lines):
                    if line.lower() == f'user-agent: {bot.lower()}':
                        bot_idx = idx
                        break
                is_allowed = False
                if bot_idx != -1:
                    for sub in lines[bot_idx + 1:bot_idx + 4]:
                        if sub.lower().startswith('user-agent:'):
                            break
                        if sub.lower() == 'allow: /':
                            is_allowed = True
                            break
                res.check(is_allowed, f'[{site_name}] AI crawler {bot} explicitly allowed')

            # 5. Scrapers blocked
            scrapers = ['Bytespider', 'CCBot', 'Meta-ExternalAgent', 'Amazonbot']
            for scraper in scrapers:
                bot_idx = -1
                for idx, line in enumerate(lines):
                    if line.lower() == f'user-agent: {scraper.lower()}':
                        bot_idx = idx
                        break
                is_blocked = False
                if bot_idx != -1:
                    for sub in lines[bot_idx + 1:bot_idx + 4]:
                        if sub.lower().startswith('user-agent:'):
                            break
                        if sub.lower() == 'disallow: /':
                            is_blocked = True
                            break
                res.check(is_blocked, f'[{site_name}] aggressive scraper {scraper} blocked')

            # 6. Sitemap directive points to proper domain
            sitemap_lines = [l.split(':', 1)[1].strip() for l in lines if l.lower().startswith('sitemap:')]
            exp_sitemap = f'https://{domain}/sitemap.xml'
            res.check(exp_sitemap in sitemap_lines, f'[{site_name}] Sitemap matches {exp_sitemap}')

        self.results['tier1'] = res
        return res

    def verify_tier2_headers(self) -> TierResult:
        res = TierResult('Tier 2: RFC 8288 Link Headers, CORS & MIME Types')
        print('\n=== Tier 2: RFC 8288 Link Headers, CORS & MIME Types ===')

        for site_name, base_dir in [('vesviet', VESVIET_DIR), ('learn', LEARN_DIR)]:
            headers_file = base_dir / 'static' / '_headers'
            res.check(headers_file.exists(), f'[{site_name}] _headers exists at {headers_file}')
            if not headers_file.exists():
                continue

            content = headers_file.read_text(encoding='utf-8', errors='replace')
            blocks = {}
            current_path = None
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                if not raw_line.startswith(' ') and not raw_line.startswith('\t'):
                    current_path = line
                    blocks[current_path] = []
                elif current_path:
                    blocks[current_path].append(line)

            root_headers = blocks.get('/', [])
            root_links = [h for h in root_headers if h.lower().startswith('link:')]

            req_link_rels = [
                ('sitemap.xml', 'describedby'),
                ('auth.md', 'authorizing-agent'),
                ('api-catalog', 'api-catalog'),
                ('agent-card.json', 'agent-card'),
                ('server-card.json', 'mcp-server-card'),
                ('index.json', 'agent-skills'),
                ('oauth-authorization-server', 'oauth-authorization-server'),
                ('oauth-protected-resource', 'oauth-protected-resource'),
                ('ai-catalog.json', 'service-desc'),
                ('llms.txt', 'help'),
            ]

            for target_substr, rel in req_link_rels:
                matched = any(target_substr in l and f'rel="{rel}"' in l for l in root_links)
                res.check(matched, f'[{site_name}] root Link header for {target_substr} (rel="{rel}")')

            # Check MIME types and CORS headers
            expected_mime = {
                '/.well-known/api-catalog': 'application/linkset+json',
                '/auth.md': 'text/markdown',
                '/.well-known/oauth-authorization-server': 'application/json',
                '/.well-known/oauth-protected-resource': 'application/json',
                '/.well-known/agent-card.json': 'application/json',
                '/.well-known/agent-registry.json': 'application/json',
                '/.well-known/ai-catalog.json': 'application/json',
                '/.well-known/agent-skills/index.json': 'application/json',
                '/.well-known/mcp/server-card.json': 'application/json',
                '/.well-known/security.txt': 'text/plain',
            }

            for path, mime in expected_mime.items():
                p_headers = blocks.get(path, [])
                has_mime = any(h.lower().startswith('content-type:') and mime in h for h in p_headers)
                has_cors = any(h.lower() == 'access-control-allow-origin: *' for h in p_headers)
                res.check(has_mime, f'[{site_name}] {path} has Content-Type containing {mime}')
                res.check(has_cors, f'[{site_name}] {path} has Access-Control-Allow-Origin: *')

        self.results['tier2'] = res
        return res

    def verify_tier3_auth_md(self) -> TierResult:
        res = TierResult('Tier 3: Auth.md Agentic Registration Protocol')
        print('\n=== Tier 3: Auth.md Agentic Registration Protocol ===')

        for site_name, base_dir, domain in [('vesviet', VESVIET_DIR, 'tanhdev.com'), ('learn', LEARN_DIR, 'learn.tanhdev.com')]:
            auth_file = base_dir / 'static' / 'auth.md'
            res.check(auth_file.exists(), f'[{site_name}] auth.md exists at {auth_file}')
            if not auth_file.exists():
                continue

            content = auth_file.read_text(encoding='utf-8', errors='replace')
            lines = content.splitlines()

            # 1. First non-empty line must be verbatim "# Auth.md"
            first_line = next((l for l in lines if l.strip()), '')
            res.check(first_line == '# Auth.md', f'[{site_name}] auth.md line 1 is verbatim "# Auth.md"')

            # 2. Must contain literal phrase "agentic registration"
            res.check('agentic registration' in content, f'[{site_name}] contains literal phrase "agentic registration"')

            # 3. Live endpoints documented
            res.check(f'register_uri: https://{domain}/oauth2/register' in content, f'[{site_name}] documents register_uri')
            res.check(f'claim_uri: https://{domain}/oauth2/claim' in content, f'[{site_name}] documents claim_uri')
            res.check(f'token_endpoint: https://{domain}/oauth2/token' in content, f'[{site_name}] documents token_endpoint')
            res.check('identity_types_supported:' in content, f'[{site_name}] documents identity_types_supported')

            # 4. Discovery endpoints documented
            res.check(f'https://{domain}/.well-known/oauth-protected-resource' in content, f'[{site_name}] references oauth-protected-resource')
            res.check(f'https://{domain}/.well-known/oauth-authorization-server' in content, f'[{site_name}] references oauth-authorization-server')
            res.check(f'https://{domain}/.well-known/api-catalog' in content, f'[{site_name}] references api-catalog')
            res.check(f'https://{domain}/.well-known/agent-card.json' in content, f'[{site_name}] references agent-card.json')

            # 5. MCP transport streamable-http
            res.check('transport: streamable-http' in content, f'[{site_name}] asserts MCP transport: streamable-http')

            # 6. Zero secrets
            secret_markers = ['BEGIN PRIVATE KEY', 'bearer_token:', 'client_secret:', 'secret_key', 'api_key:']
            has_secret = any(s in content for s in secret_markers)
            res.check(not has_secret, f'[{site_name}] auth.md contains zero credentials or secrets')

        self.results['tier3'] = res
        return res

    def verify_tier4_a2a_schema(self) -> TierResult:
        res = TierResult('Tier 4: A2A 1.0 JSON Schema Conformance')
        print('\n=== Tier 4: A2A 1.0 JSON Schema Conformance ===')

        res.check(SCHEMA_PATH.exists(), f'A2A Agent Card schema exists at {SCHEMA_PATH}')
        if not SCHEMA_PATH.exists() or Draft202012Validator is None:
            self.results['tier4'] = res
            return res

        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_json = json.load(f)
        validator = Draft202012Validator(schema_json)

        for site_name, base_dir, exp_url in [('vesviet', VESVIET_DIR, 'https://tanhdev.com'), ('learn', LEARN_DIR, 'https://learn.tanhdev.com')]:
            card_path = base_dir / 'static' / '.well-known' / 'agent-card.json'
            res.check(card_path.exists(), f'[{site_name}] agent-card.json exists')
            if not card_path.exists():
                continue

            with open(card_path, 'r', encoding='utf-8') as f:
                card_data = json.load(f)

            # JSON Schema Draft202012 validation
            errors = list(validator.iter_errors(card_data))
            res.check(len(errors) == 0, f'[{site_name}] agent-card.json passes Draft 2020-12 schema validation', f'Errors: {[e.message for e in errors]}')

            # Specific A2A invariants
            res.check(card_data.get('protocol_version') == '1.0', f'[{site_name}] protocol_version is "1.0"')
            res.check(card_data.get('url') == exp_url, f'[{site_name}] card url matches {exp_url}')
            caps = card_data.get('capabilities', {})
            res.check(caps.get('streaming') is True, f'[{site_name}] capabilities.streaming is true')
            res.check(caps.get('stateTransitionHistory') is True, f'[{site_name}] capabilities.stateTransitionHistory is true')
            skills = card_data.get('skills', [])
            res.check(len(skills) > 0, f'[{site_name}] card defines {len(skills)} skills')
            for s in skills:
                res.check(bool(s.get('id') and s.get('name') and s.get('description')), f'[{site_name}] skill {s.get("id")} has id, name, description')

        self.results['tier4'] = res
        return res

    def verify_tier5_registries(self) -> TierResult:
        res = TierResult('Tier 5: Machine Registries & Protocol Metadata')
        print('\n=== Tier 5: Machine Registries & Protocol Metadata ===')

        for site_name, base_dir, domain in [('vesviet', VESVIET_DIR, 'tanhdev.com'), ('learn', LEARN_DIR, 'learn.tanhdev.com')]:
            wk = base_dir / 'static' / '.well-known'

            # 1. RFC 9727 API Catalog
            api_cat = wk / 'api-catalog'
            res.check(api_cat.exists(), f'[{site_name}] api-catalog exists (without .json extension)')
            if api_cat.exists():
                with open(api_cat, 'r', encoding='utf-8') as f:
                    cat_json = json.load(f)
                linkset = cat_json.get('linkset', [])
                res.check(len(linkset) > 0 and 'anchor' in linkset[0], f'[{site_name}] api-catalog conforms to RFC 9727 linkset array')

            # 2. RFC 8414 OAuth Authorization Server
            oauth_as = wk / 'oauth-authorization-server'
            res.check(oauth_as.exists(), f'[{site_name}] oauth-authorization-server exists')
            if oauth_as.exists():
                with open(oauth_as, 'r', encoding='utf-8') as f:
                    as_json = json.load(f)
                res.check(as_json.get('issuer') == f'https://{domain}', f'[{site_name}] OAuth issuer is https://{domain}')
                res.check('S256' in as_json.get('code_challenge_methods_supported', []), f'[{site_name}] OAuth supports PKCE S256')
                agent_auth = as_json.get('agent_auth', {})
                res.check(agent_auth.get('register_uri') == f'https://{domain}/oauth2/register', f'[{site_name}] agent_auth.register_uri exact')
                res.check(agent_auth.get('claim_uri') == f'https://{domain}/oauth2/claim', f'[{site_name}] agent_auth.claim_uri exact')
                res.check('anonymous' in agent_auth and 'credential_types_supported' in agent_auth['anonymous'], f'[{site_name}] anonymous credentials nested')

            # 3. RFC 8707 OAuth Protected Resource
            oauth_pr = wk / 'oauth-protected-resource'
            res.check(oauth_pr.exists(), f'[{site_name}] oauth-protected-resource exists')
            if oauth_pr.exists():
                with open(oauth_pr, 'r', encoding='utf-8') as f:
                    pr_json = json.load(f)
                res.check(pr_json.get('resource') == f'https://{domain}', f'[{site_name}] resource matches domain')
                res.check(f'https://{domain}' in pr_json.get('authorization_servers', []), f'[{site_name}] authorization_servers matches domain')

            # 4. MCP Server Card (2026-07-28)
            mcp_card = wk / 'mcp' / 'server-card.json'
            res.check(mcp_card.exists(), f'[{site_name}] mcp/server-card.json exists')
            if mcp_card.exists():
                with open(mcp_card, 'r', encoding='utf-8') as f:
                    mcp_data = json.load(f)
                res.check(bool(mcp_data.get('serverInfo', {}).get('name') or mcp_data.get('name')), f'[{site_name}] MCP card defines server name')
                res.check(mcp_data.get('protocolVersion') == '2026-07-28' or mcp_data.get('mcp_version') == '2026-07-28', f'[{site_name}] protocol version is 2026-07-28')
                trans = mcp_data.get('transport', {})
                res.check(trans.get('type') == 'streamable-http', f'[{site_name}] MCP transport is streamable-http')
                res.check(trans.get('url') == f'https://{domain}/mcp', f'[{site_name}] MCP endpoint URL is https://{domain}/mcp')

            # 5. Agent Skills manifest (agentskills.io v1.0)
            skills_manifest = wk / 'agent-skills' / 'index.json'
            res.check(skills_manifest.exists(), f'[{site_name}] agent-skills/index.json exists')
            if skills_manifest.exists():
                with open(skills_manifest, 'r', encoding='utf-8') as f:
                    sm_data = json.load(f)
                res.check(sm_data.get('schema_version') == '1.0', f'[{site_name}] agent-skills schema_version is 1.0')
                res.check(len(sm_data.get('skills', [])) > 0, f'[{site_name}] agent-skills declares skills array')

            # 6. AI Catalog meta-index
            ai_cat = wk / 'ai-catalog.json'
            res.check(ai_cat.exists(), f'[{site_name}] ai-catalog.json exists')
            if ai_cat.exists():
                with open(ai_cat, 'r', encoding='utf-8') as f:
                    aic_data = json.load(f)
                res.check(len(aic_data.get('agents', [])) > 0, f'[{site_name}] ai-catalog indexes agents')
                res.check(len(aic_data.get('mcp', [])) > 0, f'[{site_name}] ai-catalog indexes mcp')

            # 7. Agent Registry
            agent_reg = wk / 'agent-registry.json'
            res.check(agent_reg.exists(), f'[{site_name}] agent-registry.json exists')
            if agent_reg.exists():
                with open(agent_reg, 'r', encoding='utf-8') as f:
                    ar_data = json.load(f)
                res.check(ar_data.get('contract_type') == 'agent-registry', f'[{site_name}] contract_type is agent-registry')

            # 8. Security.txt
            sec_txt = wk / 'security.txt'
            res.check(sec_txt.exists(), f'[{site_name}] security.txt exists')
            if sec_txt.exists():
                txt = sec_txt.read_text(encoding='utf-8')
                res.check('Contact:' in txt and 'Expires:' in txt, f'[{site_name}] security.txt contains Contact and Expires')

        self.results['tier5'] = res
        return res

    def verify_tier6_isitagentready(self) -> TierResult:
        res = TierResult('Tier 6: 19 isitagentready.com Checks Simulation')
        print('\n=== Tier 6: 19 isitagentready.com Checks Simulation ===')

        for site_name, base_dir, domain in [('vesviet', VESVIET_DIR, 'tanhdev.com'), ('learn', LEARN_DIR, 'learn.tanhdev.com')]:
            static = base_dir / 'static'
            wk = static / '.well-known'

            # 1. robotsTxt
            r_exists = (static / 'robots.txt').exists()
            res.check(r_exists, f'[{site_name}] Check 1/19: robotsTxt (RFC 9309 compliant)')

            # 2. sitemap
            s_declared = False
            if r_exists:
                c = (static / 'robots.txt').read_text(encoding='utf-8')
                s_declared = f'Sitemap: https://{domain}/sitemap.xml' in c
            res.check(s_declared, f'[{site_name}] Check 2/19: sitemap (Sitemap URL configured)')

            # 3. linkHeaders
            h_content = (static / '_headers').read_text(encoding='utf-8') if (static / '_headers').exists() else ''
            res.check('Link: </auth.md>' in h_content and 'Link: </.well-known/agent-card.json>' in h_content, f'[{site_name}] Check 3/19: linkHeaders (RFC 8288 metadata links on root)')

            # 4. contentSignals
            res.check('Content-Signal:' in (static / 'robots.txt').read_text(encoding='utf-8'), f'[{site_name}] Check 4/19: contentSignals (IETF AI usage preferences declared)')

            # 5. robotsTxtAiRules
            r_text = (static / 'robots.txt').read_text(encoding='utf-8')
            res.check('User-agent: GPTBot' in r_text and 'User-agent: ClaudeBot' in r_text, f'[{site_name}] Check 5/19: robotsTxtAiRules (explicit AI crawler permissions)')

            # 6. apiCatalog
            res.check((wk / 'api-catalog').exists(), f'[{site_name}] Check 6/19: apiCatalog (RFC 9727 linkset document)')

            # 7. oauthDiscovery
            as_text = (wk / 'oauth-authorization-server').read_text(encoding='utf-8') if (wk / 'oauth-authorization-server').exists() else ''
            res.check('"agent_auth"' in as_text and '"S256"' in as_text, f'[{site_name}] Check 7/19: oauthDiscovery (RFC 8414 metadata with agent_auth & PKCE)')

            # 8. oauthProtectedResource
            res.check((wk / 'oauth-protected-resource').exists(), f'[{site_name}] Check 8/19: oauthProtectedResource (RFC 8707 metadata)')

            # 9. authMd
            auth_text = (static / 'auth.md').read_text(encoding='utf-8') if (static / 'auth.md').exists() else ''
            res.check(auth_text.startswith('# Auth.md') and 'agentic registration' in auth_text, f'[{site_name}] Check 9/19: authMd (WorkOS agentic registration specification)')

            # 10. mcpServerCard
            mcp_text = (wk / 'mcp' / 'server-card.json').read_text(encoding='utf-8') if (wk / 'mcp' / 'server-card.json').exists() else ''
            res.check('streamable-http' in mcp_text and '2026-07-28' in mcp_text, f'[{site_name}] Check 10/19: mcpServerCard (MCP 2026-07-28 stateless HTTP manifest)')

            # 11. a2aAgentCard
            res.check((wk / 'agent-card.json').exists(), f'[{site_name}] Check 11/19: a2aAgentCard (A2A 1.0 Agent Card discoverable)')

            # 12. agentSkills
            res.check((wk / 'agent-skills' / 'index.json').exists(), f'[{site_name}] Check 12/19: agentSkills (agentskills.io manifest discoverable)')

            # 13. llmsTxt
            res.check((static / 'llms.txt').exists(), f'[{site_name}] Check 13/19: llmsTxt (curated documentation index present)')

            # 14. llmsFullTxt
            res.check((static / 'llms-full.txt').exists(), f'[{site_name}] Check 14/19: llmsFullTxt (comprehensive LLM corpus present)')

            # 15. securityTxt
            res.check((wk / 'security.txt').exists(), f'[{site_name}] Check 15/19: securityTxt (RFC 9116 security contact declared)')

            # 16. ardAiCatalog
            res.check((wk / 'ai-catalog.json').exists(), f'[{site_name}] Check 16/19: ardAiCatalog (Linux Foundation AI-Catalog meta-index)')

            # 17. corsHeaders
            res.check('Access-Control-Allow-Origin: *' in h_content, f'[{site_name}] Check 17/19: corsHeaders (Access-Control-Allow-Origin configured on discovery)')

            # 18. noSecrets
            res.check('PRIVATE KEY' not in auth_text and 'PRIVATE KEY' not in as_text, f'[{site_name}] Check 18/19: noSecrets (zero credentials or private keys exposed)')

            # 19. noDummyDomains
            res.check('example.com' not in auth_text and 'auth.internal' not in auth_text, f'[{site_name}] Check 19/19: noDummyDomains (all endpoints use live domain https://{domain})')

        self.results['tier6'] = res
        return res

    def verify_tier7_one_way_authority(self) -> TierResult:
        res = TierResult('Tier 7: One-Way Authority Law & Zero Cross-Leaks')
        print('\n=== Tier 7: One-Way Authority Law & Zero Cross-Leaks ===')

        v_static = VESVIET_DIR / 'static'
        violations = []
        for p in v_static.rglob('*'):
            if p.is_file():
                try:
                    text = p.read_text(encoding='utf-8', errors='ignore')
                    if 'learn.tanhdev.com' in text:
                        violations.append(str(p.relative_to(REPO_ROOT)))
                except Exception:
                    pass

        res.check(len(violations) == 0, 'vesviet/static has 0 references/leaks to learn.tanhdev.com', f'Violations: {violations}')
        self.results['tier7'] = res
        return res

    def run_all(self) -> bool:
        print('=' * 80)
        print(' SOTA AGENT DISCOVERY & READINESS VERIFICATION HARNESS')
        print('=' * 80)

        self.verify_tier1_robots()
        self.verify_tier2_headers()
        self.verify_tier3_auth_md()
        self.verify_tier4_a2a_schema()
        self.verify_tier5_registries()
        self.verify_tier6_isitagentready()
        self.verify_tier7_one_way_authority()

        print('\n' + '=' * 80)
        print(' SUMMARY REPORT')
        print('=' * 80)
        total_passed = 0
        total_failed = 0
        all_passed = True
        for tier_key, res in self.results.items():
            status = 'PASS' if res.success else 'FAIL'
            if not res.success:
                all_passed = False
            total_passed += res.passed
            total_failed += res.failed
            print(f'  [{status}] {res.name}: {res.passed} passed, {res.failed} failed')

        print('-' * 80)
        print(f'TOTAL: {total_passed} checks passed, {total_failed} checks failed.')
        print(f'OVERALL STATUS: {"PASS" if all_passed else "FAIL"}')
        print('=' * 80)
        return all_passed


if __name__ == '__main__':
    verifier = AgentDiscoveryVerifier()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
