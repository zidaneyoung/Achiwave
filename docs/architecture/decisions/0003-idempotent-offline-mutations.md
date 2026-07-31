# ADR 0003: Idempotent offline mutations

- Status: Accepted
- Date: 2026-07-30

## Context

Mobile requests can be tapped twice, replayed after timeout, reordered, or retried
after the backend committed but before the device received a response.

## Decision

Each logical offline completion receives one stable UUID client mutation ID and
canonical payload hash, unique per user. Exact replay returns its stored result;
identifier reuse with another payload is rejected. Independent unique constraints
protect active completion and reward sources. Queue states and failure classes are
explicit and durable.

## Consequences

Retries are safe across restart and reconnection. Mobile persists result before
confirmed UI and stops permanent failures. Logout cancels and clears private queued
payloads.

Request-time random IDs and application-only duplicate checks were rejected because
they fail after timeout, restart, or concurrent requests.
