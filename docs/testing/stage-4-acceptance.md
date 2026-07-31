# Stage 4 acceptance audit

Stage 4 covers mobile authentication, account security, and user preferences in
issues #65–#84. Evidence was collected on 2026-07-31 against the isolated
`achiwave_stage4_gate` Docker project, PostgreSQL 18.4, Redis 8.2.8, and an
Android Expo export. Issue #85 and later stages remain outside this work.

## Publication evidence

| Key | Branch | Pull request | Result |
|---|---|---|---|
| B1 | `stage-4/authentication-core-65-69` | [#380](https://github.com/zidaneyoung/Achiwave/pull/380) | Merged as `1805c4c32c84f2980707541df4e7f9f60431adf8` |
| B2 | `stage-4/android-device-security-70-74` | [#381](https://github.com/zidaneyoung/Achiwave/pull/381) | Merged as `cf496d2710afff48dc613bc11aa1afdb4f26e70e` |
| B3 | `stage-4/profile-preferences-75-80` | [#382](https://github.com/zidaneyoung/Achiwave/pull/382) | Merged as `7961806b3f8ec8d9ed6b9ee53aa5c9b993e617a8` |
| B4 | `stage-4/account-lifecycle-security-81-84` | [#383](https://github.com/zidaneyoung/Achiwave/pull/383) | Open during evidence commit; merge recorded by the linked PR |

## Issue traceability

File entries identify the primary implementation and test surfaces; they are not
intended to duplicate every file in each Git commit. `None` means the issue uses
the existing Stage 3/4 schema and did not require a migration.

| Issue | Branch | Commit | Primary files | Migration | Verification / actual result | Status |
|---|---|---|---|---|---|---|
| #65 | B1 | `f0b32d8` | `api/auth.py`; `auth/passwords.py`; `services/registration.py`; `tests/auth/test_registration.py` | `20260731_0065` | PostgreSQL auth and full B1 suite (`69 passed`) | Pass |
| #66 | B1 | `b3de316` | `services/login.py`; `api/auth.py`; `tests/auth/test_login.py` | None | success/failure/rehash and generic-response tests passed | Pass |
| #67 | B1 | `856bf4f` | `auth/tokens.py`; `services/refresh.py`; `tests/auth/test_refresh.py` | `20260731_0067` | rotation, reuse, transaction, and migration tests passed | Pass |
| #68 | B1 | `1c063c2` | `services/logout.py`; `api/auth.py`; `tests/auth/test_logout.py` | None | access/refresh logout paths and repeat safety passed | Pass |
| #69 | B1 | `3f67e52` | `api/dependencies.py`; `api/users.py`; `tests/auth/test_protected_endpoints.py` | None | ownership/session/device protected-endpoint tests passed | Pass |
| #70 | B2 | `347f930` | mobile route layouts; `auth/AuthContext.tsx`; `auth/bootstrap.ts` | None | TypeScript, Expo Doctor, Android export passed | Pass |
| #71 | B2 | `a0ca5e1` | `auth/secureCredentials.ts`; Expo SecureStore config | None | secure-envelope audit, TypeScript, Android export passed | Pass |
| #72 | B2 | `a7b79fd` | `auth/service.ts`; `AuthenticationForm.tsx`; auth state | None | backend rejection/refresh tests plus mobile checks passed | Pass |
| #73 | B2 | `3ee6305` | `api/devices.py`; `services/devices.py`; `tests/devices/test_devices.py` | None | device target suite and live current-device registration passed | Pass |
| #74 | B2 | `f5cb849` | device/session APIs; mobile `security.tsx`; `devices/api.ts` | None | B2 target (`39 passed`), full (`78 passed`), live revocations passed | Pass |
| #75 | B3 | `0a7d086` | `services/profile.py`; `api/users.py`; `tests/profile/test_profile.py` | `20260731_0075` | profile tests and live profile update passed | Pass |
| #76 | B3 | `d842d61` | `services/preferences.py`; `api/preferences.py`; `test_timezone.py` | None | IANA/timezone version tests passed | Pass |
| #77 | B3 | `618c805` | date-format backend/mobile preference files and tests | `20260731_0077` | preference tests, migration, TypeScript/export passed | Pass |
| #78 | B3 | `6251d6e` | feedback preference backend/mobile files and tests | `20260731_0078` | independent sound/haptic tests passed | Pass |
| #79 | B3 | `8072606` | reduced-motion backend/mobile files and tests | `20260731_0079` | reduced-motion tests and accessibility-oriented UI checks passed | Pass |
| #80 | B3 | `f831d39` | notification preference backend/mobile files and tests | None | B3 target (`34 passed`), full (`112 passed`), mobile checks passed | Pass |
| #81 | B4 | `3ad167c` | `services/account.py`; `api/account.py`; `tests/account/test_deactivation.py` | None | transaction/idempotence tests and live later-login/refresh rejection passed | Pass |
| #82 | B4 | `f1fc017` | `privacy/localDataPurge.ts`; auth/pref stores; account/logout UI | None | TypeScript and Android export passed; physical cleanup inspection unavailable | Pass |
| #83 | B4 | `db381c4` | `auth/service.ts`; `AuthContext.tsx`; protected/offline routes | None | state-machine review, TypeScript, Android export passed; physical offline launch unavailable | Pass |
| #84 | B4 | `f6339cb` | `logging_config.py`; safe model reprs; `safeLogging.ts`; sentinel tests | None | backend security/logging (`10 passed`), mobile sentinel and live 18-value scan passed | Pass |

## Executed verification

### Backend and migrations

Commands ran from `apps/backend` with `ACHIWAVE_TEST_DATABASE_URL` pointing only
to the disposable `achiwave_stage4_gate_test` database.

```powershell
python -m pytest tests/auth tests/devices tests/preferences tests/security -q
python -m pytest -q
python -m alembic heads
python -m alembic current
python -m alembic upgrade head
python -m alembic check
```

Actual result: target suite `69 passed`; full suite `121 passed`; one head and
current revision `20260731_0079`; upgrade succeeded; `No new upgrade operations
detected.` The initial full-suite command inherited a signing key and therefore
could not exercise the missing-production-key test (`1 failed, 120 passed`);
removing that contaminating environment variable produced the authoritative
`121 passed` result.

Earlier sequential branch results were B1 full `69 passed`, B2 target `39 passed`
and full `78 passed`, and B3 profile/preference target `34 passed` and full `112
passed`. The migration chain remained reversible and drift-free with one head.

### Mobile

```powershell
npm ci
npm run typecheck
npm run test:security
$env:EXPO_PUBLIC_API_ENV = 'development'
$env:EXPO_PUBLIC_API_BASE_URL = 'http://10.0.2.2:58000'
npx expo-doctor
npx expo export --platform android
```

Actual result: clean install succeeded (596 packages); TypeScript and the mobile
secret sentinel passed; Expo Doctor passed 20/20; Android bundled 1,252 modules
and exported successfully. `npm ci` reports 10 moderate transitive advisories in
Expo’s Apple build tooling and no high/critical gate failure; the available
all-advisory forced fix proposes a breaking Expo dependency change and was not
applied. Expo correctly failed closed before the two required public development
variables were supplied.

### Live Docker and runtime workflow

The backend image was rebuilt, migrations applied, and only the backend, worker,
and scheduler in Compose project `achiwave_stage4_gate` were recreated. Its fixed
host ports are backend `58000`, PostgreSQL `55432`, and Redis `56379`.

Actual result: backend/PostgreSQL/Redis reported healthy; worker and scheduler
remained running. Liveness returned `ok` and readiness returned `ready`. A live
workflow passed registration, login, refresh, protected access, current-device
registration, session listing, other-session revocation, current-device
revocation, a fresh login, profile/preferences updates, logout, account
deactivation, and rejection of later login and refresh. The workflow observed
three sessions and found none of 18 actual password/token/header/query/device
sentinels in backend logs.

The separate Uptime Arc Compose project `api-monitoring-platform` was not
recreated or stopped. Its main backend and frontend returned HTTP 200 on host
ports `8000` and `3000`, and its primary containers remained healthy/running.

## Unable to Verify

`adb` is not installed in this environment, so TalkBack interaction, emulator or
physical-device logout cleanup, process-death restoration, network-toggle offline
launch, touch-target behavior, and OS-level SecureStore inspection are `Unable to
Verify`. This does not convert those checks into a pass: the available evidence is
TypeScript, Expo Doctor, Android export, backend/runtime tests, and source-level
state/cleanup review. No Expo cloud build or store submission was in Stage 4.

## Scope and remaining limitations

No Stage 5 navigation, domain progression, offline mutation queue, notification
permission/delivery, push-token registration, permanent deletion, or account
reactivation was implemented. Backend authority, append-only history, device
context boundaries, and environment-scoped mobile storage remain intact.
