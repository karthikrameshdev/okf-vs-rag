---
type: service
id: payment-gateway-v2
title: Payment Gateway V2 Architecture
version: "2.1.0"
status: production
updated_at: 2026-09-15T14:30:00Z
verified_by: security-architecture@fincloud.internal
resource: service://fincloud/payments/v2
tags:
  - payments
  - pci-dss
  - microservices
  - zero-trust
relations:
  depends_on:
    - vault-secrets-engine
    - user-auth-service
  deprecates:
    - legacy-payment-v1
  governed_by:
    - pci-dss-compliance
    - zero-trust-network
---

# Payment Gateway V2 Architecture

## Executive Summary
Payment Gateway V2 is FinCloud's active high-throughput transaction processing engine.
It replaces the decommissioned `legacy-payment-v1` service and adheres to PCI-DSS v4.0.

## Authentication & Security Protocols
- **Inter-service Communication**: Requires SPIFFE/SPIRE mutual TLS (mTLS) with TLS 1.3 only.
- **Cardholder Data Tokenization**: Primary Account Numbers (PAN) are NEVER stored in plaintext. PANs are ingested through an ephemeral enclave and exchanged with `vault-secrets-engine` for irreversible surrogate tokens (AES-256-GCM).
- **Client Authentication**: Requests must bear signed Ed25519 JWT bearer tokens issued by `user-auth-service`.
- **API Keys**: Static API keys are strictly forbidden (previously used in v1).

## Architecture & Dependencies
1. **Inbound Orders**: Received from `order-service` via gRPC port 9443.
2. **Secrets Leasing**: Pulls rotating tokenization keys from `vault-secrets-engine` on a 15-minute lease window.
3. **Session Verification**: Validates caller cryptographic identities against `user-auth-service`.

## Compliance Checklist
- [x] PCI-DSS v4.0 Requirement 3: Cardholder data encrypted at rest and in transit.
- [x] Zero-Trust network segmentation (namespace `fincloud-cde`).
- [x] Full audit telemetry streamed to immutable ledger.
