import assert from "node:assert/strict";
import test from "node:test";

import { parseCompletionConflict } from "./conflicts.ts";

test("parses only scoped canonical conflict fields and stable event identity", () => {
  const conflict = parseCompletionConflict({
    occurrence: {
      id: "occurrence-1",
      quest_id: "quest-1",
      campaign_id: "campaign-1",
      status: "reversed",
      record_version: 3,
      private_evidence: "excluded",
    },
    campaign: { id: "campaign-1", status: "active", record_version: 3 },
    active_completion_id: null,
    event_sequence: 4,
    progress_events: [{ id: "event-4", event_type: "completion_reversed", event_sequence: 4 }],
    access_token: "excluded",
  });
  assert.deepEqual(conflict, {
    occurrence: {
      id: "occurrence-1",
      questId: "quest-1",
      campaignId: "campaign-1",
      status: "reversed",
      recordVersion: 3,
    },
    campaign: { id: "campaign-1", status: "active", recordVersion: 3 },
    activeCompletionId: null,
    eventSequence: 4,
    progressEvents: [{ id: "event-4", eventType: "completion_reversed", eventSequence: 4 }],
  });
});

test("rejects ancestry mismatches in conflict state", () => {
  assert.equal(parseCompletionConflict({
    occurrence: {
      id: "occurrence-1",
      quest_id: "quest-1",
      campaign_id: "campaign-1",
      status: "available",
      record_version: 2,
    },
    campaign: { id: "campaign-2", status: "active", record_version: 2 },
    active_completion_id: null,
    event_sequence: 0,
    progress_events: [],
  }), null);
});
