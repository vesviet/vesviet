# Auth.md

Technical portfolio and distributed systems engineering platform by Lê Tuấn Anh (Senior Software Engineer).
This service supports **agentic registration** for autonomous AI agents, orchestrators, and tool runners: discover → register → (claim if needed) → exchange for an access_token → call API → handle revocation.

## Registration & Identity
- register_uri: https://tanhdev.com/oauth2/register
- claim_uri: https://tanhdev.com/oauth2/claim
- token_endpoint: https://tanhdev.com/oauth2/token
- identity_types_supported:
  - anonymous
  - identity_assertion (JWT Bearer)

## Discovery Endpoints
- Protected Resource: https://tanhdev.com/.well-known/oauth-protected-resource
- Authorization Server: https://tanhdev.com/.well-known/oauth-authorization-server
- API Catalog: https://tanhdev.com/.well-known/api-catalog
- Agent Card: https://tanhdev.com/.well-known/agent-card.json
- Agent Skills: https://tanhdev.com/.well-known/agent-skills/index.json
- AI Catalog: https://tanhdev.com/.well-known/ai-catalog.json

## MCP Servers
- name: tanhdev-mcp
  transport: streamable-http
  endpoint: https://tanhdev.com/mcp
  card: https://tanhdev.com/.well-known/mcp/server-card.json

## Autonomy Governance
- tier: Tier 1 Supervised
- protocol_version: 1.0
