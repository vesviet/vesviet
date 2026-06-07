# Auth.md

You are an agent. This service supports **agentic registration**: discover → register → (claim if needed) → exchange for an access_token → call API → handle revocation.

## Step 1 — Discover
Fetch the Protected Resource Metadata at `/.well-known/oauth-protected-resource`.
Fetch the Authorization Server metadata at `/.well-known/oauth-authorization-server`.

## Step 2 — Pick a method
Check the `agent_auth.identity_types_supported` in the AS metadata. We support `anonymous`.

## Step 3 — Register
Send your registration request to the endpoint listed in `agent_auth.register_uri`.

## Step 4 — Claim
If required, complete the claim ceremony at the `claim_uri`.

## Step 5 — Exchange
Exchange your identity assertion for an access_token at the `token_endpoint` using `urn:ietf:params:oauth:grant-type:jwt-bearer`.
