import assert from "node:assert/strict";
import test from "node:test";

import { createKeyedSingleFlight } from "./singleFlight.ts";

test("same-key requests share one in-flight promise", async () => {
  const requests = createKeyedSingleFlight();
  let calls = 0;
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  const first = requests.run("campaigns:active", async () => {
    calls += 1;
    await pending;
    return "canonical";
  });
  const second = requests.run("campaigns:active", async () => "duplicate");

  assert.equal(first.started, true);
  assert.equal(second.started, false);
  assert.equal(second.promise, first.promise);
  assert.equal(requests.has("campaigns:active"), true);
  release();
  assert.equal(await second.promise, "canonical");
  await Promise.resolve();
  assert.equal(calls, 1);
  assert.equal(requests.has("campaigns:active"), false);
});

test("different keys run independently and rejected requests are released", async () => {
  const requests = createKeyedSingleFlight();
  const active = requests.run("active", async () => "active");
  const archived = requests.run("archived", async () => {
    throw new Error("offline");
  });

  assert.equal(active.started, true);
  assert.equal(archived.started, true);
  assert.equal(await active.promise, "active");
  await assert.rejects(archived.promise, /offline/u);
  await Promise.resolve();
  assert.equal(requests.has("active"), false);
  assert.equal(requests.has("archived"), false);
  assert.equal(requests.run("archived", async () => "retry").started, true);
});
