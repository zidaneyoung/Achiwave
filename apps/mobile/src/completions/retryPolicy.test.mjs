import assert from "node:assert/strict";
import test from "node:test";

import {
  COMPLETION_RETRY_MAX_AUTOMATIC_ATTEMPTS,
  nextCompletionRetryAt,
  parseRetryAfterMilliseconds,
} from "./retryPolicy.ts";

const clock = (random = 0) => ({
  now: () => new Date("2026-08-12T12:00:00.000Z"),
  random: () => random,
});

test("automatic retries begin at five seconds and double with bounded jitter", () => {
  assert.equal(nextCompletionRetryAt(1, null, clock()), "2026-08-12T12:00:05.000Z");
  assert.equal(nextCompletionRetryAt(2, null, clock()), "2026-08-12T12:00:10.000Z");
  assert.equal(nextCompletionRetryAt(3, null, clock(1)), "2026-08-12T12:00:24.000Z");
  assert.equal(nextCompletionRetryAt(20, null, clock()), null);
});

test("retry delay caps at fifteen minutes and stops after eight attempts", () => {
  assert.equal(
    nextCompletionRetryAt(7, null, clock(1)),
    "2026-08-12T12:06:24.000Z",
  );
  assert.equal(
    nextCompletionRetryAt(COMPLETION_RETRY_MAX_AUTOMATIC_ATTEMPTS, null, clock()),
    null,
  );
});

test("a longer valid Retry-After value wins", () => {
  assert.equal(
    nextCompletionRetryAt(1, 60_000, clock(1)),
    "2026-08-12T12:01:00.000Z",
  );
  assert.equal(parseRetryAfterMilliseconds("45"), 45_000);
  assert.equal(
    parseRetryAfterMilliseconds(
      "Wed, 12 Aug 2026 12:02:00 GMT",
      Date.parse("2026-08-12T12:00:00.000Z"),
    ),
    120_000,
  );
  assert.equal(parseRetryAfterMilliseconds("invalid"), null);
});
