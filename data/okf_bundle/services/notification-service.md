---
type: service
id: notification-service
title: Multi-channel Event Notification Service
version: "2.0.0"
status: production
updated_at: 2026-08-14T10:00:00Z
verified_by: comms-eng@fincloud.internal
resource: service://fincloud/notifications/v2
tags:
  - notifications
  - messaging
  - email
  - sms
relations:
  consumed_from:
    - order-service
  governed_by:
    - zero-trust-network
---

# Multi-channel Event Notification Service

## Description
Consumes business events and delivers notifications across SMS (Twilio), Email (SendGrid), and Webhooks.
Consumes asynchronous events published by `order-service` to send order confirmations and receipt invoices.
Protected by internal zero-trust mTLS.
