---
type: service
id: legacy-payment-v1
title: Legacy Payment Service (Decommissioned)
version: "1.0.0"
status: deprecated
decommissioned_at: 2025-12-31T23:59:59Z
verified_by: security-architecture@fincloud.internal
tags:
  - payments
  - legacy
  - deprecated
relations:
  replaced_by:
    - payment-gateway-v2
---

# Legacy Payment Service (Decommissioned)

> [!CAUTION]
> This service was completely decommissioned on December 31, 2025. It is NOT active in production.
> Any integration attempting to use this service will fail. Use `payment-gateway-v2` instead.

## Historical Characteristics (DEPRECATED)
- Used static developer API keys passed via `X-API-KEY` header.
- Handled raw credit card PAN strings directly in MySQL tables without tokenization.
- Lacked zero-trust network support (ran on legacy VPC).
