# ADR 0002: Timestamp and timezone authority

- Status: Accepted
- Date: 2026-07-30

## Context

Device clocks, travel, DST, offline delay, and concurrent processing can assign
different dates to the same action.

## Decision

Store instants in UTC and calendar context as validated IANA zones. Server receipt
and per-user event sequence order authoritative events. Device-observed time is
metadata. Recurring streak credit narrowly uses the backend-generated occurrence
local date; one-time credit uses server receipt in the saved zone. Timezone edits
are prospective and do not rebucket history.

## Consequences

Late recurring sync can preserve its occurrence day without trusting device time;
late one-time sync credits receipt day. Occurrences snapshot timezone resolution.
DST and concurrent events have deterministic rules.

Raw device dates and historical rebucketing were rejected because either can create
or erase progression through clock/timezone manipulation.
