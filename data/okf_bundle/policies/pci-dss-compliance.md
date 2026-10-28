---
type: policy
id: pci-dss-compliance
title: PCI-DSS v4.0 Cardholder Security Policy
version: "4.0.0"
status: mandatory
updated_at: 2026-06-01T00:00:00Z
verified_by: compliance-auditor@fincloud.internal
tags:
  - compliance
  - security
  - pci-dss
  - audit
relations:
  applies_to:
    - payment-gateway-v2
    - vault-secrets-engine
---

# PCI-DSS v4.0 Cardholder Security Policy

## Strict Compliance Requirements
1. **Scope Restriction**: Only `payment-gateway-v2` and `vault-secrets-engine` are permitted inside the Cardholder Data Environment (CDE).
2. **Storage Prohibition**: Raw PAN (Primary Account Number) and CVV codes MUST NEVER be stored on disk, logs, or unencrypted memory.
3. **Encryption Standard**: All sensitive cardholder metadata must be encrypted using AES-256-GCM with keys managed exclusively by `vault-secrets-engine`.
4. **Audit Logging**: All cryptographic operations must generate signed audit events retained for 365 days.
