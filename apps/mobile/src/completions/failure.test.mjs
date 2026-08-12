import assert from "node:assert/strict";
import test from "node:test";

import { CompletionRequestError } from "./errors.ts";
import { classifyCompletionFailure } from "./failure.ts";

test("classifies stale, archive, expiration, ownership, session, and malformed failures", () => {
  const cases = [
    [
      new CompletionRequestError("conflict", "stale", "stale_occurrence_version"),
      "stale_version",
    ],
    [
      new CompletionRequestError("conflict", "archived", "occurrence_not_eligible", {
        campaign: { status: "archived" }, occurrence: { status: "available" },
      }),
      "archived",
    ],
    [
      new CompletionRequestError("conflict", "expired", "occurrence_not_eligible", {
        campaign: { status: "active" }, occurrence: { status: "expired" },
      }),
      "expired",
    ],
    [new CompletionRequestError("not_found", "missing"), "target_unavailable"],
    [new CompletionRequestError("authentication", "session"), "authentication"],
    [new CompletionRequestError("validation", "bad"), "malformed_mutation"],
  ];
  for (const [error, reason] of cases) {
    const failure = classifyCompletionFailure(error);
    assert.equal(failure.reason, reason);
    assert.equal(failure.kind, "permanent_failure");
  }
});

test("network and server failures remain explicitly retryable", () => {
  for (const code of ["offline", "server", "invalid_response"]) {
    const failure = classifyCompletionFailure(new CompletionRequestError(code, code));
    assert.equal(failure.kind, "retryable_failure");
  }
});
