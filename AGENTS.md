# Repository instructions

These instructions apply to all repository work.

## Product-rule authority

- Read [`docs/README.md`](docs/README.md) and the relevant product-rule document before changing domain, mobile, backend, worker, database, synchronization, notification, or testing behavior.
- Preserve backend authority for ownership, quest validation, completion acceptance, recurrence, authoritative timestamps, XP, levels, streaks, achievements, duplicate prevention, and persistent history.
- Treat mobile progression as cached, pending, or presented server state. A device must never award authoritative XP, levels, streaks, campaign completion, or achievements.
- Preserve stable client mutation identifiers across retries. Enforce one authoritative result per logical mutation and one active completion/reward per occurrence.
- Keep device-observed times as metadata. Use only the documented server-derived effective date for progression.
- Preserve append-only completion, reward, reversal, unlock, and audit records. Correct history with compensating events, not silent mutation.
- Apply the conflict rules in
  [`docs/product-rules/offline-and-synchronization.md`](docs/product-rules/offline-and-synchronization.md);
  never use generic last-write-wins for reward-bearing operations.
- Do not expose secret achievement definitions or private queued payloads.
- Treat archive, deletion, logout, account switching, and device revocation according
  to the documented privacy and history rules.

## Change discipline

- Inspect the relevant issue, dependencies, current behavior, and working tree first.
- Implement only the selected stage. Stage 1 documents rules; it does not authorize later-stage code.
- Update traceability and acceptance evidence when a product rule changes.
- Run the narrowest relevant checks and report `Pass`, `Fail`, or
  `Unable to Verify` from actual evidence.
- Preserve unrelated changes. Do not add dependencies for documentation checks.
