# ADR 0004: Reward and history reversal

- Status: Accepted
- Date: 2026-07-30

## Context

Users need correction without destroying evidence required to explain XP, levels,
streaks, achievements, and campaign state.

## Decision

Completion, XP awards, unlocks, and audit events are append-only while the account
exists. Reversal records a linked event and exact negative XP compensation, then
recalculates derived state. It never rewrites source timestamps or relocks an
achievement. Account/legal deletion is the explicit privacy exception.

## Consequences

Totals remain reconstructable, reversals may lower levels and streaks, and unlocked
achievements remain historical facts. Reversal stays available after archive.

Silent total mutation and destructive completion deletion were rejected because
they make state unauditable and produce cross-device divergence.
