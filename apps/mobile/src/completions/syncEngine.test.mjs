import assert from "node:assert/strict";
import test from "node:test";

import { createSynchronizationEngine } from "./syncEngine.ts";

test("canonical result is persisted before synchronized presentation", async () => {
  const order = [];
  const engine = createSynchronizationEngine({
    validateSession: async () => order.push("validated"),
    leaseDue: async () => [{ queueId: "queue-1" }],
    submit: async () => ({ completionId: "completion-1" }),
    persistSuccess: async () => order.push("persisted"),
    afterPersistedSuccess: async () => order.push("presented"),
    classifyFailure: () => ({ kind: "retryable", safeClass: "network", safeMessage: "Reconnect.", retryAfterMilliseconds: null }),
    persistRetryableFailure: async () => undefined,
    persistPermanentFailure: async () => undefined,
    releaseLeases: async () => undefined,
  });
  const summary = await engine.run("account-1");
  assert.deepEqual(order, ["validated", "persisted", "presented"]);
  assert.equal(summary.succeeded, 1);
});

test("overlapping synchronization calls share one run", async () => {
  let release;
  let validations = 0;
  const gate = new Promise((resolve) => { release = resolve; });
  const engine = createSynchronizationEngine({
    validateSession: async () => { validations += 1; await gate; },
    leaseDue: async () => [],
    submit: async () => ({}),
    persistSuccess: async () => undefined,
    afterPersistedSuccess: async () => undefined,
    classifyFailure: () => ({ kind: "retryable", safeClass: "network", safeMessage: "Reconnect.", retryAfterMilliseconds: null }),
    persistRetryableFailure: async () => undefined,
    persistPermanentFailure: async () => undefined,
    releaseLeases: async () => undefined,
  });
  const first = engine.run("account-1");
  const second = engine.run("account-1");
  assert.equal(first, second);
  release();
  await first;
  assert.equal(validations, 1);
});

test("different account partitions never share a synchronization run", async () => {
  const validated = [];
  const engine = createSynchronizationEngine({
    validateSession: async (accountId) => { validated.push(accountId); },
    leaseDue: async () => [],
    submit: async () => ({}),
    persistSuccess: async () => undefined,
    afterPersistedSuccess: async () => undefined,
    classifyFailure: () => ({ kind: "retryable", safeClass: "network", safeMessage: "Reconnect.", retryAfterMilliseconds: null }),
    persistRetryableFailure: async () => undefined,
    persistPermanentFailure: async () => undefined,
    releaseLeases: async () => undefined,
  });
  await Promise.all([engine.run("account-1"), engine.run("account-2")]);
  assert.deepEqual(validated.sort(), ["account-1", "account-2"]);
});

test("presentation callback failure cannot downgrade persisted success", async () => {
  let retryableWrites = 0;
  const engine = createSynchronizationEngine({
    validateSession: async () => undefined,
    leaseDue: async () => [{ queueId: "queue-1" }],
    submit: async () => ({}),
    persistSuccess: async () => undefined,
    afterPersistedSuccess: async () => { throw new Error("listener failed"); },
    classifyFailure: () => ({ kind: "retryable", safeClass: "server", safeMessage: "Retry.", retryAfterMilliseconds: null }),
    persistRetryableFailure: async () => { retryableWrites += 1; },
    persistPermanentFailure: async () => undefined,
    releaseLeases: async () => undefined,
  });
  const summary = await engine.run("account-1");
  assert.equal(summary.succeeded, 1);
  assert.equal(retryableWrites, 0);
});

test("authentication failure pauses and releases unsubmitted leases", async () => {
  const released = [];
  const operations = [{ queueId: "queue-1" }, { queueId: "queue-2" }];
  const engine = createSynchronizationEngine({
    validateSession: async () => undefined,
    leaseDue: async () => operations,
    submit: async () => { throw Object.assign(new Error("session"), { authentication: true }); },
    persistSuccess: async () => undefined,
    afterPersistedSuccess: async () => undefined,
    classifyFailure: (error) => error.authentication
      ? { kind: "authentication" }
      : { kind: "retryable", safeClass: "network", safeMessage: "Reconnect.", retryAfterMilliseconds: null },
    persistRetryableFailure: async () => undefined,
    persistPermanentFailure: async () => undefined,
    releaseLeases: async (_accountId, pending) => released.push(...pending),
  });
  const summary = await engine.run("account-1");
  assert.equal(summary.authenticationPaused, true);
  assert.deepEqual(released, operations);
});

test("permanent conflict is persisted and never submitted again in the run", async () => {
  let persisted = 0;
  const engine = createSynchronizationEngine({
    validateSession: async () => undefined,
    leaseDue: async () => [{ queueId: "queue-1" }],
    submit: async () => { throw new Error("conflict"); },
    persistSuccess: async () => undefined,
    afterPersistedSuccess: async () => undefined,
    classifyFailure: () => ({
      kind: "permanent",
      safeClass: "stale_version",
      safeMessage: "The occurrence changed.",
      canonicalResultJson: "{}",
    }),
    persistRetryableFailure: async () => undefined,
    persistPermanentFailure: async () => { persisted += 1; },
    releaseLeases: async () => undefined,
  });
  const summary = await engine.run("account-1");
  assert.equal(persisted, 1);
  assert.equal(summary.permanentFailures, 1);
});
