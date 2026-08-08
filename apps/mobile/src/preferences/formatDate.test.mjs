import assert from "node:assert/strict";
import test from "node:test";

import { formatPreferenceDateTime } from "./formatDate.ts";

test("due-date formatter applies the saved date order in the quest timezone", () => {
  const instant = new Date("2100-01-01T03:00:00Z");
  assert.match(
    formatPreferenceDateTime(instant, "year_month_day", "America/Halifax"),
    /^2099-12-31 /u,
  );
  assert.match(
    formatPreferenceDateTime(instant, "day_month_year", "America/Halifax"),
    /^31\/12\/2099 /u,
  );
});
