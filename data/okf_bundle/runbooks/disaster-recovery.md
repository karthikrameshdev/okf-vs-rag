---
type: runbook
id: disaster-recovery
title: Production Multi-Region Failover Runbook
version: "3.1.0"
status: active
target_rto: 15 minutes
target_rpo: 0 minutes
updated_at: 2026-10-01T08:00:00Z
verified_by: site-reliability-eng@fincloud.internal
tags:
  - runbook
  - sre
  - disaster-recovery
  - failover
relations:
  governs_services:
    - payment-gateway-v2
    - order-service
    - user-auth-service
---

# Production Multi-Region Failover Runbook

## Objective & SLA
Execute an emergency region failover from Primary Region (us-east-1) to Standby Region (eu-west-1).
Target Recovery Time Objective (RTO) is 15 minutes; Recovery Point Objective (RPO) is 0 data loss.

## Step-by-Step Execution Sequence

### Phase 1: DNS & Ingress Redirection
1. Navigate to Cloudflare Global Traffic Manager or run:
   ```bash
   fincloud-cli traffic reroute --from us-east-1 --to eu-west-1 --drain-seconds 60
   ```
2. Monitor HTTP 5xx spikes on Edge Envoy Gateways.

### Phase 2: Database Cluster State Promotion
CRITICAL WARNING: NEVER run Step 4 before validating Step 3 replica sync state!
3. Check CockroachDB replication lag:
   ```bash
   cockroach node status --host=eu-west-1.db.internal --assert-lag-max=0ms
   ```
4. If replication lag is confirmed zero, execute the node promotion command:
   ```bash
   cockroach cluster promote-standby --region=eu-west-1 --confirm-cluster-split-brain-prevention
   ```

### Phase 3: Vault Dynamic Key Authority Switch
5. Issue the regional HSM takeover command:
   ```bash
   vault operator step-down -address=https://us-east-1.vault.internal
   vault operator step-up -address=https://eu-west-1.vault.internal
   ```

### Phase 4: Service Health Verification
6. Run automated end-to-end synthetic probe:
   ```bash
   probe-runner --target=eu-west-1.fincloud.internal/health --assert-all-passing
   ```
