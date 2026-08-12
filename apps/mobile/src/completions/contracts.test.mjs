import assert from "node:assert/strict";
import test from "node:test";

import { parseCompleteOccurrence, parseReverseCompletion } from "./contracts.ts";

const payload = {
  outcome: "completed",
  occurrence: {
    id: "d0000000-0000-4000-8000-000000000001",
    quest_id: "d0000000-0000-4000-8000-000000000002",
    campaign_id: "d0000000-0000-4000-8000-000000000003",
    status: "completed",
    record_version: 2,
    completed_at: "2026-08-12T12:00:00Z",
    reversed_at: null,
  },
  completion: {
    id: "d0000000-0000-4000-8000-000000000004",
    occurrence_id: "d0000000-0000-4000-8000-000000000001",
    device_id: "d0000000-0000-4000-8000-000000000007",
    server_received_at: "2026-08-12T12:00:00Z",
    server_processed_at: "2026-08-12T12:00:00Z",
    completion_effective_date: "2026-08-12",
    event_sequence: 1,
    reversed_at: null,
    device_observed_at: "2026-08-12T11:59:58Z",
    device_timezone_name: "America/Halifax",
    client_time_valid: true,
  },
  campaign: {
    id: "d0000000-0000-4000-8000-000000000003",
    status: "completed",
    record_version: 3,
    completed_at: "2026-08-12T12:00:00Z",
  },
  progress_events: [{
    id: "d0000000-0000-4000-8000-000000000006",
    event_type: "completion_accepted",
    event_sequence: 1,
    server_processed_at: "2026-08-12T12:00:00Z",
  }],
};

test("parses a canonical completion without Stage 8 reward data", () => {
  const result = parseCompleteOccurrence(payload);
  assert.equal(result?.outcome, "completed");
  assert.equal(result?.completion.eventSequence, 1);
  assert.equal(result?.progressEvents[0]?.eventType, "completion_accepted");
  assert.equal("xp" in (result ?? {}), false);
});

test("rejects mismatched occurrence ancestry", () => {
  assert.equal(parseCompleteOccurrence({
    ...payload,
    completion: { ...payload.completion, occurrence_id: "other" },
  }), null);
});

test("parses an append-oriented reversal", () => {
  const result = parseReverseCompletion({
    ...payload,
    outcome: "reversed",
    occurrence: {
      ...payload.occurrence,
      status: "reversed",
      record_version: 3,
      reversed_at: "2026-08-12T12:05:00Z",
    },
    completion: {
      ...payload.completion,
      reversed_at: "2026-08-12T12:05:00Z",
    },
    reversal: {
      id: "d0000000-0000-4000-8000-000000000005",
      completion_id: payload.completion.id,
      occurrence_id: payload.occurrence.id,
      device_id: payload.completion.device_id,
      reason: "user_correction",
      server_received_at: "2026-08-12T12:05:00Z",
      server_processed_at: "2026-08-12T12:05:00Z",
      event_sequence: 2,
    },
  });
  assert.equal(result?.outcome, "reversed");
  assert.equal(result?.reversal.eventSequence, 2);
});
