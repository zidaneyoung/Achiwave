import assert from "node:assert/strict";
import test from "node:test";

import { parseQuest, parseQuestAuthoringOptions } from "./contracts.ts";

test("authoring options parser accepts only canonical category values", () => {
  assert.deepEqual(
    parseQuestAuthoringOptions({
      categories: [
        { value: "personal", label: "Personal" },
        { value: "finance", label: "Finance" },
      ],
    }),
    {
      categories: [
        { value: "personal", label: "Personal" },
        { value: "finance", label: "Finance" },
      ],
    },
  );
  assert.equal(
    parseQuestAuthoringOptions({
      categories: [{ value: "Finance", label: "Finance" }],
    }),
    null,
  );
});

test("quest parser accepts canonical one-time occurrence snapshot", () => {
  const quest = parseQuest({
    id: "quest", campaign_id: "campaign", campaign_record_version: 2, campaign_status: "active",
    quest_type: "one_time", definition_state: "active", title: "Write brief",
    description: null, category: "work", category_label: "Work", reward_xp: 20, display_order: 0, available_from: null,
    due_at: null, timezone_name: null, due_status: "none", record_version: 1, archived_at: null,
    restored_at: null, created_at: "2026-08-07T00:00:00Z", updated_at: "2026-08-07T00:00:00Z",
    occurrence: {
      id: "occurrence", status: "available", occurrence_local_date: "2026-08-07",
      timezone_name: "UTC", available_at: "2026-08-07T00:00:00Z",
      eligibility_expires_at: null, reward_xp: 20, record_version: 1,
    },
  });
  assert.equal(quest?.occurrence?.rewardXp, 20);
  assert.equal(quest?.campaignRecordVersion, 2);
  assert.equal(quest?.categoryLabel, "Work");
});

test("quest parser rejects invalid occurrence snapshots", () => {
  assert.equal(parseQuest({ id: "quest" }), null);
});
