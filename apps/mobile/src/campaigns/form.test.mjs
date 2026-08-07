import assert from "node:assert/strict";
import test from "node:test";

import {
  CAMPAIGN_DESCRIPTION_MAX_LENGTH,
  CAMPAIGN_TITLE_MAX_LENGTH,
  validateCampaignForm,
} from "./form.ts";

test("campaign form trims canonical content and preserves absent description", () => {
  assert.deepEqual(validateCampaignForm("  Train for 10K  ", "   "), {
    title: "Train for 10K",
    description: null,
    titleError: null,
    descriptionError: null,
  });
});

test("campaign form rejects blank, oversized, and unsafe values", () => {
  assert.equal(validateCampaignForm("   ", "").titleError, "Enter a campaign title.");
  assert.match(
    validateCampaignForm("x".repeat(CAMPAIGN_TITLE_MAX_LENGTH + 1), "").titleError,
    /characters or fewer/u,
  );
  assert.match(
    validateCampaignForm("Valid", "x".repeat(CAMPAIGN_DESCRIPTION_MAX_LENGTH + 1))
      .descriptionError,
    /characters or fewer/u,
  );
  assert.match(validateCampaignForm("Bad\u0000title", "").titleError, /control/u);
});
