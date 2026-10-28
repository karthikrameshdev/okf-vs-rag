---
type: service
id: user-auth-service
title: User Authentication & Identity Service
version: "3.4.0"
status: production
updated_at: 2026-08-20T11:00:00Z
verified_by: identity-team@fincloud.internal
resource: service://fincloud/auth/v3
tags:
  - identity
  - oauth2
  - oidc
  - security
relations:
  depends_on:
    - vault-secrets-engine
  governed_by:
    - zero-trust-network
---

# User Authentication & Identity Service

## Overview
The User Authentication Service manages centralized authentication, OpenID Connect (OIDC) identity brokering, and multi-factor authentication (MFA) across the entire platform.

## Cryptographic Token Standards
- **Algorithm**: Asymmetric Ed25519 (Edwards-curve Digital Signature Algorithm).
- **Token Lifespan**: Access tokens expire in 900 seconds (15 minutes). Refresh tokens expire in 24 hours with sliding window refresh.
- **Key Rotation**: Asymmetric private signing keys are generated inside and leased from `vault-secrets-engine`.

## Rate Limiting & Threat Protection
- Enforces adaptive rate limiting of 50 auth requests per minute per IP using distributed Redis counters.
- Device fingerprinting and geo-velocity anomaly detection block credential stuffing attacks.
