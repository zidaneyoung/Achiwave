import assert from "node:assert/strict";
import test from "node:test";

import { parseQuest, parseQuestAuthoringOptions, parseQuestList, parseQuestOrder } from "./contracts.ts";

test("quest order parser requires unique contiguous canonical items", () => {
  assert.deepEqual(
    parseQuestOrder({
      campaign_id: "campaign",
      campaign_record_version: 5,
      items: [
        { id: "b", display_order: 0, record_version: 2 },
        { id: "a", display_order: 1, record_version: 2 },
      ],
    }),
    {
      campaignId: "campaign",
      campaignRecordVersion: 5,
      items: [
        { id: "b", displayOrder: 0, recordVersion: 2 },
        { id: "a", displayOrder: 1, recordVersion: 2 },
      ],
    },
  );
  assert.equal(
    parseQuestOrder({
      campaign_id: "campaign",
      campaign_record_version: 5,
      items: [{ id: "a", display_order: 1, record_version: 2 }],
    }),
    null,
  );
});

test("authoring options parser accepts only canonical category values", () => {
  assert.deepEqual(
    parseQuestAuthoringOptions({
      categories: [
        { value: "personal", label: "Personal" },
        { value: "finance", label: "Finance" },
      ],
      difficulties: [
        { value: "easy", label: "Easy" },
        { value: "medium", label: "Medium" },
        { value: "hard", label: "Hard" },
      ],
      reward_xp_values: [0, 10, 20],
    }),
    {
      categories: [
        { value: "personal", label: "Personal" },
        { value: "finance", label: "Finance" },
      ],
      difficulties: [
        { value: "easy", label: "Easy" },
        { value: "medium", label: "Medium" },
        { value: "hard", label: "Hard" },
      ],
      rewardXpValues: [0, 10, 20],
    },
  );
  assert.equal(
    parseQuestAuthoringOptions({
      categories: [{ value: "Finance", label: "Finance" }],
      difficulties: [{ value: "medium", label: "Medium" }],
      reward_xp_values: [0, 10, 20],
    }),
    null,
  );
});

test("quest parser accepts canonical one-time occurrence snapshot", () => {
  const quest = parseQuest({
    id: "quest", campaign_id: "campaign", campaign_record_version: 2, campaign_status: "active",
    quest_type: "one_time", definition_state: "active", title: "Write brief",
    description: null, category: "work", category_label: "Work", difficulty: "hard", difficulty_label: "Hard", reward_xp: 20, display_order: 0, available_from: null,
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
  assert.equal(quest?.difficultyLabel, "Hard");
});

test("quest parser rejects invalid occurrence snapshots", () => {
  assert.equal(parseQuest({ id: "quest" }), null);
});

test("quest list parser preserves authoritative status and campaign context", () => {
  const item = {
    id: "quest", campaign_id: "campaign", campaign_title: "Launch", campaign_record_version: 2,
    campaign_status: "active", quest_type: "one_time", definition_state: "active",
    status: "available", title: "Write brief", description: null, category: "work",
    category_label: "Work", difficulty: "hard", difficulty_label: "Hard", reward_xp: 20,
    display_order: 0, available_from: null, due_at: "2026-08-12T13:00:00Z",
    timezone_name: "America/Halifax", due_status: "upcoming", record_version: 1,
    archived_at: null, restored_at: null, created_at: "2026-08-07T00:00:00Z",
    updated_at: "2026-08-07T00:00:00Z",
    occurrence: {
      id: "occurrence", status: "available", occurrence_local_date: "2026-08-07",
      timezone_name: "America/Halifax", available_at: "2026-08-07T00:00:00Z",
      eligibility_expires_at: "2026-08-12T13:00:00Z", reward_xp: 20, record_version: 1,
    },
  };
  const page = parseQuestList({ items: [item], total: 1, limit: 50, offset: 0 });
  assert.equal(page?.items[0].campaignTitle, "Launch");
  assert.equal(page?.items[0].status, "available");
  assert.equal(page?.items[0].dueStatus, "upcoming");

  assert.equal(
    parseQuestList({ items: [{ ...item, status: "overdue" }], total: 1, limit: 50, offset: 0 }),
    null,
  );
  assert.equal(
    parseQuestList({ items: [{ ...item, campaign_title: "" }], total: 1, limit: 50, offset: 0 }),
    null,
  );
  assert.equal(
    parseQuestList({ items: [item, item], total: 2, limit: 50, offset: 0 }),
    null,
  );
});
