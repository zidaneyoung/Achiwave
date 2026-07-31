# Stage 4 authentication and account security

Stage 4 implements issues #65–#84. The backend remains authoritative for
identity, account state, device/session validity, and preference persistence;
the Android client stores only the credentials and presentation cache needed to
represent a previously confirmed server session.

## Passwords and identity

- Registration and login canonicalize email for lookup while retaining the
  display email returned to the owner.
- Passwords are bounded by validated settings and hashed with Argon2id. Plaintext
  passwords never enter persistence, logs, or response models.
- Login performs a dummy Argon2id verification for unknown users so unknown email
  and incorrect password share one `invalid_credentials` response. A successful
  login replaces an outdated Argon2id hash when the library parameters require it.
- Production startup requires an access-token signing key of at least 32
  characters. The key, database/Redis URLs, and other credentials are hidden from
  settings representations and logs.

## Access tokens

Access tokens are short-lived signed JWTs. Required claims are:

| Claim | Meaning |
|---|---|
| `sub` | authoritative user UUID |
| `sid` | device-session UUID |
| `iat` / `exp` | server issue and expiry instants |
| `jti` | unique token UUID |
| `iss` / `aud` | configured issuer and Achiwave mobile audience |

Verification fixes the configured algorithm (`HS256` in Stage 4), issuer, and
audience; it does not accept an algorithm proposed by the token. Protected
dependencies also load the user, registered device, and session and require all
three to be active, mutually owned, unexpired, and consistent with the claims.

## Refresh rotation, sessions, and devices

- Refresh tokens are cryptographically random opaque values. PostgreSQL stores
  only their SHA-256 credential digests, protected by a partial unique index.
- Each successful refresh replaces the current session and credential in one
  transaction. The old session points to its replacement and cannot refresh
  again. Reuse detection revokes the affected active sessions.
- A session belongs to one registered device and user. Installation identifiers
  are private device context, not identity proof and never progression authority.
- Session expiry is server-derived. Logout, user-directed session/device
  revocation, refresh reuse, device revocation, and account deactivation make
  future protected access fail closed.
- Device and session list responses omit installation identifiers and credential
  digests. Revocation only resolves targets owned by the authenticated user.

## Android protected storage and bootstrap

Expo SecureStore keys are namespaced by API environment:

- `achiwave.<environment>.authentication` contains the versioned access token,
  refresh token, server expirations, device/session IDs, and safe user snapshot.
- `achiwave.<environment>.installation` contains the stable installation UUID.
- `achiwave.<environment>.presentation-preferences` contains an owner-bound,
  versioned presentation cache.

Credentials are validated structurally on load. Corrupt envelopes are removed.
Logout writes a secret-free cleared envelope rather than relying on deletion;
the stable installation identifier and public application configuration remain.
Preference cache reads require the current authenticated owner ID, preventing an
account switch from exposing the prior owner’s cache.

At application bootstrap, the route guard resolves to loading, authenticated,
unauthenticated, offline limited, or controlled failure. An unexpired access
token receives a minimal `/api/v1/users/me` validation; expired access metadata
uses refresh. An authoritative rejection purges protected state. Network
unavailability preserves a structurally valid, previously confirmed session but
routes it only to the read-only offline screen. Reconnection revalidates before
online mutations are enabled.

## Logout, cleanup, and account deactivation

One extensible purge boundary currently registers only the stores that exist:
authentication credentials and the owner-bound presentation-preference cache.
It is idempotent and reports complete or partial cleanup. Authentication is
locked in memory before asynchronous work, and an epoch prevents an in-flight
login or refresh from restoring credentials after logout. A backend outage may
leave server revocation unconfirmed, but it cannot reopen protected routes.

`POST /api/v1/account/deactivate` requires an active session and password
confirmation. One transaction records the server deactivation instant, advances
the user version, revokes all active sessions and devices, and invalidates active
push-token associations. It preserves campaign, quest, completion, progression,
achievement, notification, delivery, and audit history. Permanent deletion and
reactivation are not implemented.

## Logging redaction

Backend JSON logging recursively sanitizes structured mappings, sequences,
message arguments, and exception text. Sensitive keys are matched
case-insensitively; bearer/JWT/opaque credentials and credential-bearing URLs are
also redacted. HTTP middleware records method, route template, status, duration,
and a validated correlation ID without reading query strings, headers, cookies,
or bodies. Authentication Pydantic, dataclass, SQLAlchemy, and settings
representations omit secret fields.

The mobile console wrapper applies the same recursive rules in development and
production-format calls, and converts `Error` objects to exception type only.
User-visible authentication errors remain generic. Sentinel tests cover normal,
exception, HTTP middleware, model representation, and mobile-console paths.

## Threat boundaries and deferred features

- Production transport and certificate enforcement belong to deployment and the
  platform; the mobile config requires an explicit HTTPS production API URL.
- SecureStore reduces ordinary local exposure but cannot make a rooted or
  physically compromised device trustworthy. Server session checks remain the
  authority.
- A stolen bearer token can be used until expiry or authoritative revocation;
  short access lifetimes and device/session checks limit that window.
- Deployment-level request throttling and abuse monitoring remain required. Stage
  4 does not add a distributed rate-limiting subsystem.
- Email verification, password reset, email change, social/OAuth login, passkeys,
  mandatory biometrics, roles, permanent deletion/reactivation, push-token
  registration/delivery, campaign or quest APIs, progression, offline mutation
  queues, synchronization, and Stage 5 navigation are deferred.

Issue-level commits and executed evidence are recorded in the
[Stage 4 acceptance audit](../testing/stage-4-acceptance.md).
