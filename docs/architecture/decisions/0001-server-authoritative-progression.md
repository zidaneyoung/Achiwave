# ADR 0001: Server-authoritative progression

- Status: Accepted
- Date: 2026-07-30

## Context

Editable, offline, and concurrent mobile state cannot safely decide ownership,
completion, XP, levels, streaks, achievements, recurrence, or history.

## Decision

Backend validates and persists all authoritative domain events and derives all
progression. Mobile submits intent, queues supported offline completion, and
presents pending or confirmed server state. Device clock and cache are never reward
authority. Database constraints supplement application validation.

## Consequences

Offline feedback must remain pending until accepted. APIs return reconciliation
state and stable event IDs. Backend/domain tests cover replay and concurrency.
Users cannot gain rewards solely by editing device data.

Client-authoritative progression and trust-then-reconcile totals were rejected
because they permit divergent and fabricated state.
