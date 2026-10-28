---
type: policy
id: zero-trust-network
title: Enterprise Zero-Trust mTLS Standard
version: "2.2.0"
status: mandatory
updated_at: 2026-05-10T00:00:00Z
verified_by: netsec@fincloud.internal
tags:
  - zero-trust
  - mtls
  - spiffe
relations:
  applies_to:
    - payment-gateway-v2
    - user-auth-service
    - order-service
    - notification-service
---

# Enterprise Zero-Trust mTLS Standard

## Core Principles
1. **Never Trust, Always Verify**: Perimeter networks are considered hostile.
2. **Identity-Based Encryption**: Every service workload must present a valid X.509 SVID issued by SPIFFE/SPIRE intermediate CA.
3. **Cipher Suite Enforcements**: Only TLS 1.3 with ECDHE-ECDSA-AES256-GCM-SHA384 or ChaCha20-Poly1305.
