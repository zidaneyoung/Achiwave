import assert from "node:assert/strict";
import test from "node:test";

import {
  activeQueueRecord,
  canonicalCompletionPayload,
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
