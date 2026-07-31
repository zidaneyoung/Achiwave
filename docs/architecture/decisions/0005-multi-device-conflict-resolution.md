# ADR 0005: Multi-device conflict resolution

- Status: Accepted
- Date: 2026-07-30

## Context

Multiple devices may edit, complete, archive, reverse, change timezone, and present
events from stale snapshots.

## Decision

Backend versions mutable resources, assigns per-user event sequence, and returns
canonical state on conflict. Reward-bearing operations use first valid commit,
idempotency, source relationships, and uniqueness. Ordinary edits use optimistic
concurrency; stale edits reject rather than merge. Presentation events are claimed
atomically and remain separate from progression.

## Consequences

Every conflict maps to a valid serial order. Stale devices refresh and may preserve
non-authoritative drafts, but never overwrite rewards or timestamps. Archive first
blocks a later completion; completion first remains in history after archive.

Generic last-write-wins was rejected because it can resurrect archived data,
duplicate rewards, and lose audit history.
