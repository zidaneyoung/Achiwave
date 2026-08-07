import assert from "node:assert/strict";
import test from "node:test";

import {
  clearCachedCampaigns,
  getCachedCampaigns,
  setCachedCampaigns,
} from "./cache.ts";

test("campaign cache partitions accounts and purges protected data", async () => {
  const item = { id: "campaign-1" };
  setCachedCampaigns("owner-1", "active", [item]);
  assert.deepEqual(getCachedCampaigns("owner-1", "active"), [item]);
  assert.equal(getCachedCampaigns("owner-2", "active"), null);
  await clearCachedCampaigns();
  assert.equal(getCachedCampaigns("owner-1", "active"), null);
});
