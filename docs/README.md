# Achiwave documentation

## Development and acceptance

- [Stage 2 local development](local-development.md)
- [Stage 2 acceptance audit](testing/stage-2-acceptance.md)

This index is the normative entry point for Stage 1 product rules. If a later
implementation conflicts with these documents, the implementation is wrong until
an explicit replacement decision is accepted and all affected documents,
contracts, tests, and migrations are updated together.

## Product rules

- [Domain model, glossary, ownership, and recurrence](product-rules/domain-model.md)
  — issues #1–#3 and shared vocabulary.
- [Quest and campaign state transitions](product-rules/state-transitions.md)
  — issues #4–#6.
- [XP, levels, streaks, and achievements](product-rules/progression.md)
  — issues #7–#11 and progression invariants.
- [Time, timezone, and timestamp authority](product-rules/time-and-timezone.md)
  — issues #12 and #16.
- [Offline and multi-device synchronization](product-rules/offline-and-synchronization.md)
  — issues #13–#14.
- [History, archival, and deletion](product-rules/history-and-deletion.md)
  — issue #15.
- [MVP boundary](product-rules/mvp-boundary.md) — issue #17.
- [Stage 1 issue traceability](product-rules/stage-1-traceability.md) — exact
  #1–#17 mapping and verification result.

## Architecture decisions

- [ADR index](architecture/decisions/README.md)
- [Stage 1 acceptance audit](testing/stage-1-acceptance.md)

## Normative language and precedence

`Must`, `must not`, and `only` are requirements. `May` is an allowed choice.
Examples illustrate rules but do not override them.

Precedence is:

1. accepted architecture decision records;
2. product-rule documents;
3. acceptance audit and traceability;
4. examples and non-normative backlog scripts.

The live Stage 1 milestone and issues #1–#17 define scope. Issue #18 and later
issues are implementation work outside Stage 1.

## Non-negotiable authority boundary

Backend owns user isolation, validation, recurrence, accepted completions,
progression timestamps, XP, levels, streaks, achievement evaluation, duplicate
prevention, synchronization results, and durable history. Mobile owns input,
presentation, native feedback, permission handling, secure local data, and the
supported pending-operation queue. Device data can propose context; it cannot
create authoritative progression.
