---
type: service
id: vault-secrets-engine
title: Enterprise HashiCorp Vault Engine
version: "1.8.2"
status: production
updated_at: 2026-07-10T09:15:00Z
verified_by: secops@fincloud.internal
resource: service://fincloud/vault/v1
tags:
  - secrets
  - encryption
  - kms
  - pci-dss
relations:
  governed_by:
    - pci-dss-compliance
---

# Enterprise HashiCorp Vault Engine

## Role in Architecture
`vault-secrets-engine` is the centralized root-of-trust for FinCloud. It provides:
1. **Dynamic Database Credentials**: Generates on-the-fly ephemeral PostgreSQL credentials with 1-hour TTL.
2. **Transit Encryption as a Service**: Provides AES-256-GCM tokenization for `payment-gateway-v2`.
3. **Internal PKI Root**: Acts as the intermediate Certificate Authority issuing 24-hour mTLS certificates for SPIFFE identities.

## Key Rotation Policy
- **KMS Master Key**: Rotated automatically every 30 days via AWS KMS / GCP Cloud KMS HSM.
- **Data Encryption Keys (DEKs)**: Re-wrapped during key rollover without database downtime.
