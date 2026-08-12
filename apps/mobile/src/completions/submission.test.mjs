import assert from "node:assert/strict";
import test from "node:test";

import { CompletionSubmissionRegistry } from "./submission.ts";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, reject, resolve };
}

test("rapid taps and rerenders share one in-flight operation", async () => {
  const registry = new CompletionSubmissionRegistry();
  const request = deferred();
  let calls = 0;
  let identities = 0;
  const createInput = () => ({ mutationId: `mutation-${++identities}` });
  const execute = () => {
    calls += 1;
    return request.promise;
  };

  const first = registry.run("owner:occurrence", createInput, execute);
  const second = registry.run("owner:occurrence", createInput, execute);

  assert.equal(calls, 1);
  assert.equal(identities, 1);
  assert.equal(second.reused, true);
  assert.equal(first.promise, second.promise);
  assert.equal(first.input.mutationId, second.input.mutationId);
  request.resolve({ outcome: "completed" });
  await first.promise;
  await Promise.resolve();
  assert.equal(registry.getInput("owner:occurrence"), null);
});

test("timeout retry replays the same mutation identity", async () => {
  const registry = new CompletionSubmissionRegistry();
  const attempts = [];
  const first = registry.run(
    "owner:occurrence",
    () => ({ mutationId: "stable-mutation" }),
    async (input) => {
      attempts.push(input.mutationId);
      throw new Error("timeout after commit");
    },
  );
  await assert.rejects(first.promise);
  await Promise.resolve();

  const retry = registry.run(
    "owner:occurrence",
    () => ({ mutationId: "must-not-be-used" }),
    async (input) => {
      attempts.push(input.mutationId);
      return { outcome: "completed" };
    },
  );
  assert.equal(retry.input.mutationId, "stable-mutation");
  assert.equal(retry.reused, true);
  assert.deepEqual(attempts, ["stable-mutation", "stable-mutation"]);
  await retry.promise;
});

test("independent occurrences do not block each other", () => {
  const registry = new CompletionSubmissionRegistry();
  const first = deferred();
  const second = deferred();
  registry.run("owner:first", () => ({ id: "first" }), () => first.promise);
  registry.run("owner:second", () => ({ id: "second" }), () => second.promise);
  assert.equal(registry.isInFlight("owner:first"), true);
  assert.equal(registry.isInFlight("owner:second"), true);
  first.resolve(null);
  second.resolve(null);
});
