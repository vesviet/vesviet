# AWS RDS MySQL 8.0 EOL Migration Playbook: Blue/Green Deployments & ProxySQL Multiplexing

> **Domain:** Cloud Infrastructure | **Complexity:** Level 4/5 | **Status:** 2027 Production SOTA  
> **Key Anchors:** `AWS Blue/Green Deployment`, `ProxySQL Read/Write Split`, `MySQL 8.4 LTS`, `caching_sha2_password`

---

## 1. Problem Statement & Operational Context
AWS RDS MySQL 8.0 End of Standard Support triggers automatic $0.100–$0.200/vCPU-hr surcharges ($50,000+/year for 48 vCPUs) and violates PCI-DSS 4.0 Requirement 6.3.3. In-place database upgrades take hours of downtime.

## 2. Core Architectural Invariants
1. **Zero Downtime Cutover (< 45s):** AWS RDS Blue/Green deployment synchronizes changes via binary logs; cutover swaps CNAME DNS endpoints with zero data loss.
2. **Connection Multiplexing via ProxySQL:** Prevents PHP-FPM connection storms during failover; buffers in-flight queries and redirects read queries to replicas.
3. **Authentication Modernization:** Transition all database users from deprecated `mysql_native_password` to `caching_sha2_password` before initiation.

## 3. Agent Retrieval Guidance
- **Apply When:** Planning zero-downtime database upgrades, eliminating AWS Extended Support surcharges, or deploying ProxySQL.
- **Related Articles:** `/posts/aws-mysql-8-eol-magento-2-4-8-upgrade-architecture/`.
