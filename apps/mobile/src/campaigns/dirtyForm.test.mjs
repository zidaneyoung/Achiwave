import assert from "node:assert/strict";
import test from "node:test";

import {
  campaignFormSnapshotsEqual,
  createCampaignFormSnapshot,
} from "../forms/snapshots.ts";

test("campaign create defaults and trimmed semantic values remain clean", () => {
  const initial = createCampaignFormSnapshot("", null);

  assert.equal(
    campaignFormSnapshotsEqual(initial, createCampaignFormSnapshot("  ", "   ")),
    true,
  );
});

test("campaign edit snapshots preserve canonical values and invalid nonblank input is dirty", () => {
  const initial = createCampaignFormSnapshot("  Campaign  ", " Notes ");

  assert.deepEqual(initial, { title: "Campaign", description: "Notes" });
  assert.equal(
    campaignFormSnapshotsEqual(initial, createCampaignFormSnapshot("Campaign", "Notes")),
    true,
  );
  assert.equal(
    campaignFormSnapshotsEqual(initial, createCampaignFormSnapshot("Invalid\u0000", "Notes")),
    false,
  );
});
