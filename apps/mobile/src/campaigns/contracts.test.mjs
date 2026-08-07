import assert from "node:assert/strict";
import test from "node:test";

import { parseCampaignList } from "./contracts.ts";

const campaign = {
  id: "10000000-0000-4000-8000-000000000001",
  title: "Launch",
  description: null,
  display_order: 0,
  status: "active",
  record_version: 1,
  completed_at: null,
  archived_at: null,
  restored_at: null,
  created_at: "2026-08-07T12:00:00Z",
  updated_at: "2026-08-07T12:00:00Z",
  quest_summary: { active: 1, archived: 2, total: 3 },
};

test("campaign list parser accepts canonical owner-safe summaries", () => {
  const parsed = parseCampaignList({ items: [campaign], total: 1, limit: 50, offset: 0 });
  assert.equal(parsed?.items[0].title, "Launch");
  assert.deepEqual(parsed?.items[0].questSummary, { active: 1, archived: 2, total: 3 });
});

test("campaign list parser rejects contradictory summaries", () => {
  assert.equal(
    parseCampaignList({
      items: [{ ...campaign, quest_summary: { active: 1, archived: 2, total: 99 } }],
      total: 1,
      limit: 50,
      offset: 0,
    }),
    null,
  );
});
