# Zero-Trust Service Mesh Security: SPIFFE/SPIRE Cryptographic Workload Identities in Go

> **Domain:** Cloud Infrastructure | **Complexity:** Level 5/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `Cryptographic Workload Identity`, `X.509 SVID`, `Short-Lived Cert Rotation`

---

## 1. Problem Statement & Operational Context
Static API keys, database credentials, and IP allowlists are vulnerable to lateral movement during microservice cluster compromises. Production zero-trust architectures require automated cryptographic identity verification.

## 2. Core Architectural Invariants
1. **Identity Over Network Location:** Workload identity is bound to cryptographic certificates (X.509 SVIDs) rather than IP addresses or subnet namespaces.
2. **Automated Sub-Hour Certificate Rotation:** SVID certificates rotate automatically every 60 minutes, limiting exposure windows if compromised.
3. **Mutual TLS (mTLS) by Default:** All inter-service gRPC communication requires mutual cryptographic handshake verification.

## 3. Agent Retrieval Guidance
- **Apply When:** Designing PCI-DSS / SOC2 compliant architectures, implementing zero-trust service meshes, or hardening Go microservices.
- **Related Articles:** `/posts/zero-trust-service-mesh-security-spiffe-spire-istio-golang/`.
