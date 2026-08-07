import assert from "node:assert/strict";
import test from "node:test";

import {
  clearCachedCampaigns,
  getCachedCampaignDetail,
  getCachedCampaigns,
  setCachedCampaigns,
  setCachedCampaignDetail,
} from "./cache.ts";

test("campaign cache partitions accounts and purges protected data", async () => {
  const item = { id: "campaign-1" };
  setCachedCampaigns("owner-1", "active", [item]);
  setCachedCampaignDetail("owner-1", "campaign-1", false, item);
  assert.deepEqual(getCachedCampaigns("owner-1", "active"), [item]);
  assert.equal(getCachedCampaigns("owner-2", "active"), null);
  assert.equal(getCachedCampaignDetail("owner-2", "campaign-1", false), null);
  assert.equal(getCachedCampaignDetail("owner-1", "campaign-1", false), item);
  await clearCachedCampaigns();
  assert.equal(getCachedCampaigns("owner-1", "active"), null);
  assert.equal(getCachedCampaignDetail("owner-1", "campaign-1", false), null);
});
