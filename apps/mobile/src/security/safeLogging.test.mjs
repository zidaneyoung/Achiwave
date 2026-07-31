import assert from "node:assert/strict";
import test from "node:test";

import { createSafeConsole } from "./safeLogging.ts";

const sentinels = {
  accessToken: "access-token-sentinel-mobile-84",
  authorization: "authorization-sentinel-mobile-84",
  cookie: "cookie-sentinel-mobile-84",
  credentialDigest: "credential-digest-sentinel-mobile-84",
  databasePassword: "database-password-sentinel-mobile-84",
  installationId: "84000000-0000-4000-8000-000000000084",
  password: "password-sentinel-mobile-84",
  redisPassword: "redis-password-sentinel-mobile-84",
  refreshToken: "refresh-token-sentinel-mobile-84",
  secureStoreValue: "secure-store-sentinel-mobile-84",
  signingKey: "signing-key-sentinel-mobile-84",
};

test("mobile console wrapper recursively redacts authentication secrets", () => {
  const calls = [];
  const collect = (...data) => calls.push(data);
  const logger = createSafeConsole({
    debug: collect,
    error: collect,
    info: collect,
    warn: collect,
  });

  logger.error("authentication_failure", {
    correlationId: "stage4-mobile-84",
    errorCode: "invalid_credentials",
    PaSsWoRd: sentinels.password,
    Authorization: `Bearer ${sentinels.authorization}`,
    Cookie: sentinels.cookie,
    nested: [
      {
        access_token: sentinels.accessToken,
        refresh_token: sentinels.refreshToken,
        credential_digest: sentinels.credentialDigest,
        SecureStoreValue: sentinels.secureStoreValue,
        installation_id: sentinels.installationId,
        database_url: `postgresql://user:${sentinels.databasePassword}@database/app`,
        redis_url: `redis://user:${sentinels.redisPassword}@redis/0`,
        signing_key: sentinels.signingKey,
      },
    ],
  });
  logger.error(
    "authentication_exception",
    new Error(`refresh_token=${sentinels.refreshToken}`),
  );

  const output = JSON.stringify(calls);
  assert.match(output, /authentication_failure/);
  assert.match(output, /stage4-mobile-84/);
  assert.match(output, /invalid_credentials/);
  assert.match(output, /\[REDACTED\]/);
  for (const sentinel of Object.values(sentinels)) {
    assert.doesNotMatch(output, new RegExp(sentinel));
  }
});
