---
title: "Part 6 — Security, Compliance & Audit (Security, Compliance & Audit)"
date: 2026-05-06T18:00:00+07:00
draft: false
description: "Core Banking is the ultimate target for hackers. Understand mandatory security standards (PCI-DSS, AML), how to design tamper-proof audit trails, and process sensitive data."
weight: 7
---

## Why is Core Banking Security Different?

In a typical application, a security vulnerability might lead to a data breach. In Core Banking, a vulnerability leads directly to **lost money** — the money of millions of customers. This is why the banking sector has the strictest security standards in the world.

---

## PCI-DSS — Payment Card Industry Data Security Standard

**PCI-DSS** is a mandatory set of standards for any organization that stores, processes, or transmits payment card data (Visa, Mastercard, JCB...). Violating PCI-DSS can result in millions of dollars in fines and being banned from processing card payments.

### The 12 Core Requirements of PCI-DSS v4.0

| # | Requirement | Technical Implication |
|---|---|---|
| 1 | Firewall & Network Control | Network segmentation, never expose Core Banking to the public internet |
| 2 | No Vendor Defaults | Change all default passwords, disable unnecessary services |
| 3 | Protect Stored Card Data | Never store CVV/CVV2. Encrypt PAN (card number) with AES-256 |
| 4 | Encrypt Transmission | TLS 1.2+ mandatory for all card data transmissions |
| 5 | Anti-Virus | Protect all systems against malware |
| 6 | Secure Development | SAST, DAST, strict code reviews, OWASP Top 10 |
| 7 | Restrict Access | Principle of Least Privilege — access strictly on a need-to-know basis |
| 8 | Identity & Auth | MFA is mandatory for admins, no shared accounts |
| 9 | Physical Access | Control physical access to datacenters |
| 10 | Monitor & Log | Log all access to cardholder data, retain for 12 months |
| 11 | Pentest | Regular penetration testing at least annually |
| 12 | Security Policy | Maintain an information security policy, train staff |

### Handling Card Data Correctly

```
Card Data Classification:

╔══════════════════════════════════════════════════════════╗
║  NEVER STORE UNDER ANY CIRCUMSTANCES                    ║
║  • CVV/CVV2/CVC (3-4 digits on the back)                ║
║  • PIN block                                            ║
║  • Track 1/Track 2 data (magnetic stripe data)          ║
╠══════════════════════════════════════════════════════════╣
║  STORED ONLY IF STRONGLY ENCRYPTED                      ║
║  • PAN (Primary Account Number = the 16 digits)         ║
║    → Requires Tokenization or AES-256 encryption        ║
║  • Expiration Date                                      ║
║  • Cardholder Name                                      ║
╚══════════════════════════════════════════════════════════╝
```

### Tokenization

Instead of storing the real card number, the system generates a meaningless **token**. This token cannot be used to execute transactions if stolen.

```
Real Card Number: 4111 1111 1111 1111
Token:            8293 4721 9834 5612  (random, no mathematical relationship)

Mapping (inside an HSM or Secure Token Vault):
  8293 4721 9834 5612 → 4111 1111 1111 1111
```

---

## AML & CFT — Anti-Money Laundering

**AML (Anti-Money Laundering)** and **CFT (Countering the Financing of Terrorism)** are legal obligations. Core Banking Developers must build automated detection mechanisms.

### Detection Techniques

**1. Transaction Monitoring Rules:**
```
Example Rules:
- Cash transaction > $10,000 → Generate an STR (Suspicious Transaction Report)
- Single account receives > 10 transactions < $10,000 in 24h (Structuring/Smurfing)
- Transfers to FATF High-Risk countries
```

**2. Customer Risk Scoring:**
```go
type CustomerRiskScore struct {
    CIFNumber     string
    Score         int     // 0-100
    RiskLevel     string  // "LOW", "MEDIUM", "HIGH"
    Factors       []string
    // ["PEP", "HIGH_RISK_COUNTRY", "CASH_INTENSIVE_BUSINESS"]
    LastUpdated   time.Time
}
```

**3. Sanctions Screening:**
Check all transactions and customers against international watchlists:
- OFAC (US Treasury)
- UN Security Council
- EU Consolidated List

---

## Designing the Audit Trail

Every action in Core Banking must have an immutable audit trail. This is a strict legal requirement.

### The Audit Log Table

```sql
CREATE TABLE audit_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(50) NOT NULL,   -- 'ACCOUNT', 'CUSTOMER', 'TRANSACTION'
    entity_id       VARCHAR(50) NOT NULL,   -- ID of the modified entity
    action          VARCHAR(50) NOT NULL,   -- 'CREATE', 'UPDATE', 'DELETE', 'VIEW'
    actor_id        VARCHAR(50) NOT NULL,   -- ID of user/system performing action
    actor_type      VARCHAR(20) NOT NULL,   -- 'STAFF', 'CUSTOMER', 'SYSTEM', 'API'
    ip_address      INET,
    before_state    JSONB,                  -- State prior to change
    after_state     JSONB,                  -- State after change
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    
    -- No updated_at column — audit logs are immutable
    -- NEVER UPDATE or DELETE from this table
);

-- Guarantee immutability via PostgreSQL Row Security
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_insert_only ON audit_logs FOR INSERT WITH CHECK (true);
-- INSERT only, no SELECT without rights, absolutely no UPDATE/DELETE
```

### Append-Only Pattern for the Ledger

```sql
-- Trigger to prevent UPDATE/DELETE on the ledger
CREATE OR REPLACE FUNCTION prevent_ledger_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Ledger entries are immutable. Use reversal entries to correct errors.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ledger_immutability_guard
    BEFORE UPDATE OR DELETE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION prevent_ledger_modification();
```

---

## Hardware Security Modules (HSM)

An HSM is a dedicated physical hardware device that performs the most sensitive cryptographic operations (PIN encryption, card key generation, digital signatures). Cryptographic keys never leave the HSM in plaintext.

```
PIN Processing Flow (ATM Withdrawal):
1. ATM: Encrypts PIN with a PIN Encryption Key (PEK) → generates a PIN Block
2. Core Banking → forwards the PIN Block to the HSM
3. HSM: decrypts the PIN Block → verifies PIN against stored offset → returns "VALID"/"INVALID"
4. The plaintext PIN NEVER appears in the application code memory
```

> *This concludes the theoretical portion. It's time to apply everything we've learned. Continue reading [Part 7 — Practice: Build a Mini Core Banking System from Scratch](/series/core-banking-developer/part-7-build-mini-core-banking/) to start coding.*
