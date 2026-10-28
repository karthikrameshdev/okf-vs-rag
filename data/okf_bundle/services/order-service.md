---
type: service
id: order-service
title: Order Management & Saga Orchestrator
version: "4.0.1"
status: production
updated_at: 2026-09-01T16:00:00Z
verified_by: ecommerce-core@fincloud.internal
resource: service://fincloud/orders/v4
tags:
  - orders
  - checkout
  - saga
relations:
  depends_on:
    - payment-gateway-v2
    - user-auth-service
  triggers:
    - notification-service
  governed_by:
    - zero-trust-network
---

# Order Management & Saga Orchestrator

## Overview
Coordinates end-to-end shopping cart checkout, inventory reservation, and payment processing through a distributed Saga pattern.

## Payment Integration
- Connects directly to `payment-gateway-v2` via internal gRPC client.
- Passes tokenized payment references only; never touches raw cardholder data.
- Upon successful capture, dispatches `order.completed` event to Kafka topic `fincloud.events.orders` which triggers `notification-service`.
