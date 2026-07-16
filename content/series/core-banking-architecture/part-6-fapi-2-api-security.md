---
title: "FAPI 2.0: DPoP, mTLS & Sender-Constrained Tokens"
date: "2026-06-18T11:50:00+07:00"
lastmod: "2026-07-03T15:41:55+07:00"
draft: false
description: "FAPI 2.0 DPoP: Node.js ES256 JWT generation, Go verification, mTLS Kubernetes 1-3ms vs <0.1ms pooled, PAR flow, and token replay protection."
weight: 6
series: ["core-banking-architecture"]
keywords: ["FAPI 2.0 DPoP implementation", "mTLS kubernetes latency overhead", "sender constrained tokens OAuth 2.1", "fintech API security"]
author: "Lê Tuấn Anh"
schema: ["Article", "TechArticle", "FAQPage"]
cover:
  image: "images/posts/banking-microservices-cover.png"
  alt: "Modern Core Banking Architecture series: Go, event sourcing, Saga pattern, and distributed ledger"
  relative: false
canonicalURL: "https://tanhdev.com/series/core-banking-architecture/part-6-fapi-2-api-security/"
ShowToc: true
TocOpen: true
---

**Answer-first:** Financial-grade API (FAPI) 2.0 enforces cryptographic API security using Mutual TLS (mTLS), pushed authorization requests (PAR), and signed request objects (JAR/JARM). This prevents credential hijacking, session sniffing, and token forgery in open banking networks.

> **Series (Part 6 of 8):** After mastering the payment data flow in [Part 5](/series/core-banking-architecture/part-5-iso-20022-payment-gateways/), this article focuses on the API security layer — where a single design flaw can lead to token theft and unauthorized fund transfers.

## What is FAPI 2.0 DPoP Implementation?

The Financial-grade API (FAPI) 2.0 standard mandates the use of sender-constrained tokens via DPoP or mTLS to prevent token theft. Deploying mTLS in Kubernetes adds **1-3ms** of latency for the initial handshake, but this drops to **<0.1ms** with connection pooling and HTTP Keep-Alive.

---

## Why Aren't OAuth 2.0 Bearer Tokens Enough for Fintech?

Bearer tokens have a fundamental vulnerability: anyone holding the token can use it — just like cash. If an attacker intercepts a bearer token:

1. **Replay attack**: They can use the token to call APIs at any time during its lifetime.
2. **Token theft**: Stealing from memory, logs, or network sniffing → usable until it expires.

**FAPI 2.0 solves this using Sender-Constrained Tokens:**

| Mechanism | Principle | Protects Against |
|-----------|-----------|-------------|
| **DPoP** (Demonstrating Proof-of-Possession) | The token is bound to a public key. The client must prove private key ownership on every request. | Token theft — a stolen token is useless without the private key. |
| **mTLS** (Mutual TLS) | The token is bound to the client certificate thumbprint. The server verifies the cert. | Man-in-the-middle, token theft. |
| **PAR** (Pushed Authorization Requests) | Authorization parameters are sent directly to the AS, not via the URL (preventing parameter injection). | Authorization code injection. |
| **JARM** (JWT Secured Authorization Response) | The response from the AS is signed → tamper-proof. | Parameter tampering. |

---

## DPoP: The Mathematical Mechanism

DPoP works by requiring the client to **sign a proof JWT** for every HTTP request, binding it to:
- The client's public key (in the JWT header).
- The specific HTTP method and URI.
- A timestamp (`iat`) and a unique `jti`.
- The access token hash (`ath`) — preventing token injection attacks.

### DPoP JWT Structure

```
Header (base64url):
{
  "alg": "ES256",       // Elliptic Curve P-256 — required by FAPI
  "typ": "dpop+jwt",    // DPoP-specific type
  "jwk": {              // Client's PUBLIC key (embedded in header)
    "kty": "EC",
    "crv": "P-256",
    "x": "...",
    "y": "..."
  }
}

Payload (base64url):
{
  "jti": "unique-uuid-prevents-replay",  // Must be unique per request
  "htm": "POST",                          // HTTP method
  "htu": "https://api.bank.vn/transfers", // URI (no query string)
  "iat": 1718689200,                      // Issued at (Unix timestamp)
  "ath": "base64url(SHA256(access_token))" // Access token hash
}

Signature: ES256(privateKey, base64(header) + "." + base64(payload))
```

### Node.js DPoP Implementation (ES256)

```javascript
const crypto = require('crypto');

/**
 * generateDPoPProof — Generates a DPoP proof JWT for every HTTP request
 * @param {string} privateKeyPem - EC private key PEM
 * @param {Object} publicKeyJwk  - Public key JWK (embedded in header)
 * @param {string} httpMethod    - 'GET', 'POST', etc.
 * @param {string} httpUri       - Full URI (no query params)
 * @param {string|null} accessToken - Access token to generate the ath claim
 * @returns {string} DPoP proof JWT
 */
function generateDPoPProof(privateKeyPem, publicKeyJwk, httpMethod, httpUri, accessToken = null) {
    const header = {
        alg: 'ES256',
        typ: 'dpop+jwt',
        jwk: publicKeyJwk  // Embedded public key
    };

    const payload = {
        jti: crypto.randomUUID(),           // Unique per request — prevents replay
        htm: httpMethod.toUpperCase(),
        htu: httpUri.split('?')[0],         // Strip query params
        iat: Math.floor(Date.now() / 1000)  // Current Unix timestamp
    };

    // Bind DPoP proof with access token (if available)
    if (accessToken) {
        const hash = crypto.createHash('sha256')
            .update(accessToken, 'ascii')
            .digest();
        payload.ath = hash.toString('base64url');
    }

    // Encode header and payload
    const base64Header  = Buffer.from(JSON.stringify(header)).toString('base64url');
    const base64Payload = Buffer.from(JSON.stringify(payload)).toString('base64url');
    const signingInput  = `${base64Header}.${base64Payload}`;

    // Sign with EC private key
    const sign = crypto.createSign('SHA256');
    sign.update(signingInput);
    const signature = sign.sign(privateKeyPem, 'base64url');

    return `${signingInput}.${signature}`;
}

// Usage:
const { privateKey, publicKey } = crypto.generateKeyPairSync('ec', {
    namedCurve: 'P-256',
    publicKeyEncoding: { type: 'spki', format: 'pem' },
    privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
});

// Convert public key to JWK
const publicKeyJwk = crypto.createPublicKey(publicKey).export({ format: 'jwk' });

// Generate proof for each request
const accessToken = 'eyJhbGci...';  // Token from authorization server
const dpopProof = generateDPoPProof(
    privateKey,
    publicKeyJwk,
    'POST',
    'https://api.bank.vn/v1/transfers',
    accessToken
);

// HTTP Request headers:
// DPoP: <dpopProof>
// Authorization: DPoP <accessToken>
```

### Go DPoP Verification (Server-side)

```go
package dpop

import (
    "crypto/sha256"
    "encoding/base64"
    "errors"
    "time"
    
    "github.com/lestrrat-go/jwx/v2/jwa"
    "github.com/lestrrat-go/jwx/v2/jwk"
    "github.com/lestrrat-go/jwx/v2/jwt"
)

type DPoPVerifier struct {
    // Track used JTIs to prevent replay attacks
    usedJTIs *RecentJTICache // sliding window cache, e.g. 5 minutes
}

func (v *DPoPVerifier) VerifyDPoP(
    dpopHeader string,
    method string,
    uri string,
    accessToken string,
) error {
    // 1. Parse JWT and extract JWK from header
    token, err := jwt.ParseString(dpopHeader,
        jwt.WithValidate(false), // Manual validation below
    )
    if err != nil {
        return errors.New("invalid dpop jwt")
    }

    // 2. Verify alg is ES256 or RS256 (FAPI forbids weak algs)
    rawAlg, _ := token.Get("alg")
    if alg, ok := rawAlg.(string); !ok || (alg != "ES256" && alg != "RS256") {
        return errors.New("unsupported algorithm")
    }

    // 3. Verify typ = "dpop+jwt"
    if token.JwtID() == "" {
        return errors.New("missing jti")
    }

    // 4. Check replay: jti must not have been used
    if v.usedJTIs.Contains(token.JwtID()) {
        return errors.New("dpop replay detected: jti already used")
    }

    // 5. Verify iat is not older than 30 seconds (prevent delayed replay)
    issuedAt, _ := token.Get(jwt.IssuedAtKey)
    if t, ok := issuedAt.(time.Time); ok {
        if time.Since(t) > 30*time.Second {
            return errors.New("dpop token expired")
        }
    }

    // 6. Verify htm and htu match the actual request
    if htm, _ := token.Get("htm"); htm != method {
        return errors.New("dpop htm mismatch")
    }
    if htu, _ := token.Get("htu"); htu != uri {
        return errors.New("dpop htu mismatch")
    }

    // 7. Verify ath = SHA256(access_token)
    hash := sha256.Sum256([]byte(accessToken))
    expectedAth := base64.URLEncoding.WithPadding(base64.NoPadding).EncodeToString(hash[:])
    if ath, _ := token.Get("ath"); ath != expectedAth {
        return errors.New("dpop ath mismatch: token binding invalid")
    }

    // 8. Verify signature with JWK embedded in header
    // (extracted via jwt.ParseString with key extraction)
    
    // 9. Mark JTI as used
    v.usedJTIs.Add(token.JwtID(), 30*time.Second)

    return nil
}
```

---

## FAPI 2.0 Mandatory Parameters

Source: [OpenID FAPI 2.0 Profile](https://openid.net/specs/fapi-2_0-profile.html)

### Entropy Requirements

- **nonce**: Minimum **128 bits** of entropy (≥16 random characters from a secure PRNG).
- **state**: Minimum **128 bits** of entropy — must be verified when receiving the authorization response.

### PKCE Requirements

- `code_challenge_method` must be `S256`. **Never use `plain`**.
- `code_verifier` must be 43-128 characters from `[A-Z a-z 0-9 -._~]`.

### Client Authentication (Token Endpoint)

| Method | Mechanism | Security Level |
|--------|--------|---------------|
| `private_key_jwt` | Client signs a JWT assertion with a private key | ✅ FAPI compliant |
| `tls_client_auth` | mTLS with a client certificate | ✅ FAPI compliant |
| `client_secret_basic` | HTTP Basic Auth | ❌ Not allowed in FAPI |
| `client_secret_post` | Secret in POST body | ❌ Not allowed in FAPI |

---

## mTLS Latency: Kubernetes Benchmark

Source: [Linkerd Performance Benchmarks](https://linkerd.io/2021/05/27/linkerd-performance-benchmarks/).

| Scenario | Latency Overhead | Notes |
|----------|----------------|-------|
| **Initial mTLS handshake** | **1-3ms** | Certificate exchange + key negotiation |
| **Subsequent requests** (Keep-Alive) | **<0.1ms** | Session reuse, no re-handshake |
| **Expired session** (reconnect) | **1-3ms** | Full handshake again |
| **OCSP stapling** | +0.5-1ms | Real-time certificate revocation check |

**Kubernetes mTLS with Linkerd sidecar:**

```yaml
# Linkerd annotation to automatically enable mTLS
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
  annotations:
    linkerd.io/inject: enabled  # Linkerd sidecar injection
spec:
  template:
    metadata:
      annotations:
        linkerd.io/inject: enabled
        config.linkerd.io/proxy-cpu-request: "100m"
        config.linkerd.io/proxy-memory-request: "20Mi"
    # All traffic between pods will be automatically mTLS encrypted
    # No changes required in the application code
```

**With connection pooling (production recommendation):**

```go
// Go HTTP client with mTLS and connection pool
tlsConfig := &tls.Config{
    Certificates: []tls.Certificate{clientCert},
    RootCAs:      caPool,
    MinVersion:   tls.VersionTLS13,
}

transport := &http.Transport{
    TLSClientConfig: tlsConfig,
    MaxIdleConns:       100,  // Pool 100 idle connections
    MaxIdleConnsPerHost: 10,  // 10 per host
    IdleConnTimeout:    90 * time.Second,
    // Keep-Alive: subsequent requests do not need to re-handshake → <0.1ms overhead
}

client := &http.Client{
    Transport: transport,
    Timeout:   5 * time.Second,
}
```

---

## PAR (Pushed Authorization Requests)

In traditional OAuth 2.0, authorization parameters are sent via URL redirect:

```
❌ Insecure:
https://auth.bank.vn/authorize?
  response_type=code&
  client_id=xxx&
  redirect_uri=https://app.example.com/callback&
  scope=transfer:write&
  ...
  
→ The URL can be logged, shared, or tampered with via referrer headers
```

PAR pushes parameters directly to the Authorization Server endpoint:

```
✅ PAR Flow:

Step 1: Client POSTs parameters to the AS /par endpoint (authenticated)
POST /par
Authorization: DPoP <client_assertion>
DPoP: <proof>
Body: response_type=code&scope=transfer:write&...

Response: { "request_uri": "urn:ietf:params:oauth:request_uri:random", "expires_in": 60 }

Step 2: Client redirects the user with ONLY the request_uri
https://auth.bank.vn/authorize?
  client_id=xxx&
  request_uri=urn:ietf:params:oauth:request_uri:random
  
→ No sensitive parameters exposed in the URL
```

---

## QA & SDET Testing Strategy

### Test 1: DPoP Token Replay Attack Simulation

```go
func TestDPoPTokenReplayAttack(t *testing.T) {
    // Get valid access token and DPoP proof
    accessToken, dpopProof := getValidTokenAndProof("POST", "/v1/transfers")
    
    // Request 1: Valid → Success
    resp1 := makeRequest(accessToken, dpopProof, "POST", "/v1/transfers")
    assert.Equal(t, 200, resp1.StatusCode)
    
    // Request 2: Use SAME dpopProof (replay attack)
    resp2 := makeRequest(accessToken, dpopProof, "POST", "/v1/transfers")
    
    // Must be rejected: jti has already been used
    assert.Equal(t, 401, resp2.StatusCode)
    assert.Contains(t, resp2.Body, "dpop_replay_detected")
}
```

### Test 2: Key Thumbprint Mismatch (Stolen Token)

```go
func TestStolenTokenWithWrongKey(t *testing.T) {
    // Get valid token (bound to key pair A)
    accessToken := getAccessToken(keyPairA)
    
    // Attacker possesses the access token but does not have private key A
    // Generate DPoP proof with key pair B (attacker's key)
    attackerProof := generateDPoPProof(keyPairB.Private, keyPairB.Public,
        "POST", "/v1/transfers", accessToken)
    
    // Request with stolen token + wrong key
    resp := makeRequest(accessToken, attackerProof, "POST", "/v1/transfers")
    
    // Must be rejected: thumbprint mismatch
    assert.Equal(t, 401, resp.StatusCode)
    assert.Contains(t, resp.Body, "dpop_key_mismatch")
}
```

### Test 3: mTLS Certificate Expiry

```bash
# Generate expired certificate for testing
openssl req -x509 -nodes -days -1 -newkey rsa:2048 \
  -keyout expired.key -out expired.crt \
  -subj "/CN=test-client"

# Test with expired cert
curl --cert expired.crt --key expired.key \
  https://api.bank.vn/v1/transfers

# Expectation: TLS handshake failure, connection rejected
# Server response: 400 Bad Request or TLS alert
```

---

## FAPI 2.0 Security Checklist

```markdown
## Pre-deployment Security Gate

### Authorization Server
- [ ] PAR endpoint enabled and enforced
- [ ] JARM (signed response) enabled
- [ ] nonce and state entropy ≥ 128 bits
- [ ] PKCE: S256 only, plain forbidden

### Client Authentication
- [ ] private_key_jwt or tls_client_auth only
- [ ] client_secret_* not allowed

### DPoP Verification (Resource Server)
- [ ] Verify alg ∈ {ES256, RS256, PS256}
- [ ] Verify typ = "dpop+jwt"
- [ ] Verify jti is not reused (replay prevention)
- [ ] Verify iat is within 30 seconds
- [ ] Verify htm = actual HTTP method
- [ ] Verify htu = actual URI
- [ ] Verify ath = SHA256(access_token)
- [ ] Verify signature with embedded JWK

### mTLS (if used)
- [ ] TLS 1.3 minimum
- [ ] Certificate pinning for known clients
- [ ] OCSP stapling enabled
- [ ] Connection pool for latency optimization
```

---

> 💡 **Read more:** [Streaming Fraud Detection](/series/core-banking-architecture/part-7-streaming-fraud-detection/) — Fraud detection using a FAPI-secured event stream.

### mTLS Certificate Pinning and Client Credentials Lifecycle Management in FAPI 2.0

Financial-Grade API (FAPI) 2.0 security relies on Mutual TLS (mTLS) for secure client authentication. This requires the client application to present a valid X.509 certificate during the TLS handshake. The resource server validates the certificate chain against a trusted root certificate authority (CA) and extracts the certificate thumbprint to bind it to the issued access token.

Operationalizing FAPI 2.0 introduces certificate lifecycle challenges:
- **Certificate Rotation:** Client certificates expire and must be rotated without interrupting API services. The authorization server supports dual-certificate registration, allowing clients to register a new certificate before the old one expires. During the rotation window, the gateway accepts either certificate.
- **Certificate Pinning:** To prevent man-in-the-middle (MitM) attacks caused by compromised external certificate authorities, clients use certificate pinning, hardcoding the expected server certificate thumbprint in the client application.
- **Cryptographic Token Binding Verification:** When the client calls a resource API (e.g., retrieving bank account balances), the gateway validates the access token signature and extracts the cnf (confirmation) claim containing the certificate thumbprint. It then compares this thumbprint against the client certificate presented in the active mTLS session. If they do not match, the gateway rejects the request with a 401 Unauthorized error.

### DPoP (Demonstrating Proof-of-Possession) token security

To complement mTLS, FAPI 2.0 architectures deploy DPoP (Demonstrating Proof-of-Possession) at the application layer. DPoP binds access tokens to a client-generated private key. When calling a protected API, the client signs a token request with its private key, producing a DPoP proof JWT. The resource server verifies this JWT before granting access. This ensures that even if an access token is leaked or intercepted, it cannot be used by an attacker without the corresponding private key.

### Kubernetes Network Isolation for Security Enclaves

At the network layer, FAPI 2.0 workloads run in isolated Kubernetes namespaces with strict network policies. All incoming traffic to the banking core must pass through a specialized API Gateway pod. Direct pod-to-pod communication between external APIs and internal database nodes is explicitly blocked, ensuring that a compromised API gateway cannot directly access ledger databases.

### Client Secret Rotation and Token Revocation Mechanisms

Authorization servers implement dynamic client registration (DCR) and automated client secret rotation. If a client application detects a potential credential leak, it initiates an API call to revoke active tokens and rotate keys. The revocation event is streamed instantly to API gateways, which immediately invalidate the associated access tokens.

### Cryptographic Auditing and Signature Logs

To meet regulatory requirements for financial auditing, the gateway logs the signature verification results and cryptographic thumbprints of all incoming transactions. These security logs are stored in an immutable, write-once-read-many (WORM) storage system, providing a secure audit trail for forensic investigators.

## FAQ

{{< faq q="DPoP or mTLS — which should I choose?" >}}
It depends on the client type:
- **DPoP**: Better for browser-based clients and mobile apps — no certificate management required.
- **mTLS**: Better for server-to-server (B2B APIs) and payment gateways — cert rotation can be automated.

FAPI 2.0 allows both. Many implementations support both to let clients choose.
{{< /faq >}}

{{< faq q="Does mTLS affect Kubernetes auto-scaling?" >}}
Yes, but a service mesh like Linkerd or Istio handles cert rotation automatically. When a new pod spins up, the sidecar automatically negotiates an mTLS cert from the control plane — this is completely transparent to the application code.
{{< /faq >}}

{{< faq q="Where should the DPoP private key be stored in a mobile app?" >}}
iOS: Secure Enclave (hardware-backed key storage). Android: StrongBox or Android Keystore (hardware-backed when supported by the device). The private key must never be exported out of the secure enclave.
{{< /faq >}}

## mTLS Client Certificates, Signed Request Objects, and PAR Flow Mechanics

Financial-grade API (FAPI) 2.0 provides advanced security controls for banking API networks, protecting transactions from credential hijacking and message alteration.

### mTLS Client Certificate Validation

FAPI 2.0 requires Mutual TLS (mTLS) for authentication and token binding:
- **Token Binding:** The authorization server binds the issued access token to the client's mTLS certificate thumbprint (`x5t#S256`).
- **Resource Server Validation:** When the client calls a banking API, the resource server extracts the certificate thumbprint and verifies it matches the bound token. Even if an attacker steals the token, it is unusable without the matching private key.

### Signed Request Objects (JAR/JARM)

JWT Secured Authorization Requests (JAR) enforce cryptographic integrity:
- **Signed Requests:** Clients sign authorization parameters in a JWT using RSA/ECDSA keys before submitting them, preventing tampering in transit.
- **Signed Responses (JARM):** The authorization server returns signed response parameters, preventing authorization code injection attacks.

### Pushed Authorization Requests (PAR) Flow Mechanics

PAR prevents authorization parameters from leaking through browser histories:

```
1. Client sends authorization parameters in a secure POST to the /par endpoint.
2. Authorization Server validates parameters, generates a reference URI, and returns it.
3. Client redirects the browser to the /authorize endpoint using only the reference URI.
```

This prevents interception of sensitive query parameters and ensures strict parameter validation before browser interaction begins.
---

*Up Next: [Part 7 — Streaming Fraud Detection](/series/core-banking-architecture/part-7-streaming-fraud-detection/) — Apache Flink CEP patterns, RocksDB memory tuning, async ML inference, and achieving <100ms fraud scoring SLAs.*

{{< author-cta >}}
