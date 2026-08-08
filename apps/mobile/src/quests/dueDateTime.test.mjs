import assert from "node:assert/strict";
import test from "node:test";

import {
  commitQuestDueDateTimeSelection,
  formatQuestDueDateTimeValue,
  isSupportedTimeZone,
  pickerValueForLocalDateTime,
} from "./dueDateTime.ts";

test("picker selection combines the chosen date and time in the saved IANA timezone", () => {
  const selectedDate = new Date("2027-03-14T15:00:00Z");
  const selectedTime = new Date("2027-03-15T00:45:00Z");

  assert.equal(
    commitQuestDueDateTimeSelection("", selectedDate, selectedTime, "America/Halifax"),
    "2027-03-14T21:45",
  );
});

test("picker cancellation preserves the previously committed value", () => {
  const currentValue = "2027-11-05T09:30";
  const selectedDate = new Date("2027-11-06T12:00:00Z");

  assert.equal(
    commitQuestDueDateTimeSelection(currentValue, selectedDate, null, "America/Halifax"),
    currentValue,
  );
  assert.equal(
    commitQuestDueDateTimeSelection(currentValue, null, new Date(), "America/Halifax"),
    currentValue,
  );
});

test("a committed local value round-trips into a picker instant in its saved timezone", () => {
  const fallback = new Date("2000-01-01T00:00:00Z");
  const pickerValue = pickerValueForLocalDateTime(
    "2027-11-05T09:30",
    "America/Halifax",
    fallback,
  );

  assert.notEqual(pickerValue, fallback);
  assert.equal(
    commitQuestDueDateTimeSelection("", pickerValue, pickerValue, "America/Halifax"),
    "2027-11-05T09:30",
  );
});

test("picker helpers reject unknown timezones and keep readable local intent", () => {
  const fallback = new Date("2000-01-01T00:00:00Z");

  assert.equal(isSupportedTimeZone("Not/A_Timezone"), false);
  assert.equal(pickerValueForLocalDateTime("2027-11-05T09:30", "Not/A_Timezone", fallback), fallback);
  assert.equal(
    formatQuestDueDateTimeValue("2027-11-05T09:30", "America/Halifax", "en-US"),
    "Nov 5, 2027, 9:30 AM (America/Halifax)",
  );
});
