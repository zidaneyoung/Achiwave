import assert from "node:assert/strict";
import test from "node:test";

import {
  activeQueueRecord,
  canAutomaticallyRetry,
  canonicalCompletionPayload,
  isLeaseExpired,
  retainedTerminalCutoff,
} from "./queuePolicy.ts";

const input = {
  occurrenceId: "occurrence-1",
  expectedOccurrenceVersion: 4,
  clientMutationId: "mutation-1",
  deviceObservedAt: "2026-08-12T12:00:00.000Z",
  deviceTimezoneName: "America/Halifax",
};

test("canonical queue payload excludes tokens and unrelated private data", () => {
  assert.equal(
    canonicalCompletionPayload(input),
    '{"device_observed_at":"2026-08-12T12:00:00.000Z","device_timezone_name":"America/Halifax","expected_occurrence_version":4,"occurrence_id":"occurrence-1"}',
  );
  assert.equal(canonicalCompletionPayload(input).includes("mutation-1"), false);
});

test("duplicate taps resolve to one account-scoped active operation", () => {
  const record = {
    accountId: "account-a",
    occurrenceId: "occurrence-1",
    state: "pending",
  };
  assert.equal(
    activeQueueRecord([record], "account-a", "occurrence-1"),
    record,
  );
  assert.equal(activeQueueRecord([record], "account-b", "occurrence-1"), null);
});

test("only an expired in-flight lease is recoverable after restart", () => {
  const now = new Date("2026-08-12T12:01:00.000Z");
  assert.equal(
    isLeaseExpired(
      { state: "in_flight", leaseExpiresAt: "2026-08-12T12:00:59.000Z" },
      now,
    ),
    true,
  );
  assert.equal(
    isLeaseExpired(
      { state: "in_flight", leaseExpiresAt: "2026-08-12T12:01:01.000Z" },
      now,
    ),
    false,
  );
  assert.equal(
    isLeaseExpired(
      { state: "retryable_failure", leaseExpiresAt: "2026-08-12T12:00:59.000Z" },
      now,
    ),
    false,
  );
});

test("terminal queue evidence uses a bounded seven-day retention cutoff", () => {
  assert.equal(
    retainedTerminalCutoff(new Date("2026-08-12T12:00:00.000Z")),
    "2026-08-05T12:00:00.000Z",
  );
});

test("permanent, succeeded, and cancelled operations never retry", () => {
  assert.equal(canAutomaticallyRetry("pending", 0), true);
  assert.equal(canAutomaticallyRetry("retryable_failure", 7), true);
  assert.equal(canAutomaticallyRetry("retryable_failure", 8), false);
  assert.equal(canAutomaticallyRetry("permanent_failure", 0), false);
  assert.equal(canAutomaticallyRetry("succeeded", 0), false);
  assert.equal(canAutomaticallyRetry("cancelled", 0), false);
});
