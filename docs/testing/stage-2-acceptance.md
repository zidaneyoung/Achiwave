# Stage 2 acceptance audit

This audit maps every Stage 2 issue to its implementation branch, commit, pull
request, relevant files, verification evidence, and final result. Commands were
run against the committed implementation described in each row. A result is not
marked Pass unless its listed non-device evidence actually passed.

Stage 1 product rules and the backend-authority boundary remain unchanged.
Stage 2 adds foundations only; it does not implement issue #37 or any later
domain model.

## Environment notes

- Windows host checks used Node.js 22, npm 10, and Python 3.12.
- Docker Desktop was installed but its engine did not become ready. The same
  Compose file was therefore verified with Docker Engine 29 and Compose 2.40
  inside WSL 2; all five services became healthy and the disposable verification
  project was removed afterward.
- The Android recheck used SDK Platform 36, Platform-Tools/ADB 37.0.1, and a
  Google APIs x86_64 API 36 emulator. On this Java 25 Windows host, native
  builds required `--enable-native-access=ALL-UNNAMED` and a short disposable
  worktree to avoid CMake path-length limits. Debug and release APKs built and
  installed, and issue #34's render failure/retry interaction passed.

## Issue evidence

| Issue | Branch | Commit | Pull request | Relevant files | Verification command and actual result | Final status |
| --- | --- | --- | --- | --- | --- | --- |
| [#18](https://github.com/zidaneyoung/Achiwave/issues/18) | `stage-2/mobile-foundation-18-22` | [`2128b63`](https://github.com/zidaneyoung/Achiwave/commit/2128b63) | [#367](https://github.com/zidaneyoung/Achiwave/pull/367) | `apps/mobile/package.json`, `apps/mobile/app.json` | `npm ci`; `npx expo-doctor`; Android export — install succeeded, Doctor reported 20/20 checks, export succeeded. | Pass |
| [#19](https://github.com/zidaneyoung/Achiwave/issues/19) | `stage-2/mobile-foundation-18-22` | [`ccb4dd2`](https://github.com/zidaneyoung/Achiwave/commit/ccb4dd2) | [#367](https://github.com/zidaneyoung/Achiwave/pull/367) | `apps/mobile/tsconfig.json`, `apps/mobile/package.json` | `npm run typecheck` — exited 0 with strict TypeScript configuration. | Pass |
| [#20](https://github.com/zidaneyoung/Achiwave/issues/20) | `stage-2/mobile-foundation-18-22` | [`94958b7`](https://github.com/zidaneyoung/Achiwave/commit/94958b7) | [#367](https://github.com/zidaneyoung/Achiwave/pull/367) | `apps/mobile/app/_layout.tsx`, `apps/mobile/app/index.tsx` | TypeScript and Android export — root Expo Router layout and route compiled and exported. | Pass |
| [#21](https://github.com/zidaneyoung/Achiwave/issues/21) | `stage-2/mobile-foundation-18-22` | [`1c4a48d`](https://github.com/zidaneyoung/Achiwave/commit/1c4a48d) | [#367](https://github.com/zidaneyoung/Achiwave/pull/367) | `apps/mobile/app.json`, `apps/mobile/README.md` | `npx expo config --type public` — Android package resolved to `com.zidaneyoung.achiwave.dev`. | Pass |
| [#22](https://github.com/zidaneyoung/Achiwave/issues/22) | `stage-2/mobile-foundation-18-22` | [`623fd1b`](https://github.com/zidaneyoung/Achiwave/commit/623fd1b) | [#367](https://github.com/zidaneyoung/Achiwave/pull/367) | `apps/mobile/eas.json`, `apps/mobile/package.json` | Expo config, Doctor, and Android export passed; `npx expo run:android` stopped because no Android SDK was installed. The build configuration itself passed. | Pass |
| [#23](https://github.com/zidaneyoung/Achiwave/issues/23) | `stage-2/backend-foundation-23-27` | [`619eb79`](https://github.com/zidaneyoung/Achiwave/commit/619eb79) | [#368](https://github.com/zidaneyoung/Achiwave/pull/368) | `apps/backend/src/achiwave_backend/main.py`, `apps/backend/pyproject.toml` | Pytest and a live Uvicorn request — app tests passed and the API served HTTP successfully. | Pass |
| [#24](https://github.com/zidaneyoung/Achiwave/issues/24) | `stage-2/backend-foundation-23-27` | [`07de464`](https://github.com/zidaneyoung/Achiwave/commit/07de464) | [#368](https://github.com/zidaneyoung/Achiwave/pull/368) | `apps/backend/src/achiwave_backend/config.py` | Pytest settings cases and a real PostgreSQL connection — valid URL accepted and live connection succeeded. | Pass |
| [#25](https://github.com/zidaneyoung/Achiwave/issues/25) | `stage-2/backend-foundation-23-27` | [`625469b`](https://github.com/zidaneyoung/Achiwave/commit/625469b) | [#368](https://github.com/zidaneyoung/Achiwave/pull/368) | `apps/backend/src/achiwave_backend/redis_client.py` | Pytest plus real Redis `PING` — client configuration passed and Redis returned `PONG`. | Pass |
| [#26](https://github.com/zidaneyoung/Achiwave/issues/26) | `stage-2/backend-foundation-23-27` | [`fb1aa5b`](https://github.com/zidaneyoung/Achiwave/commit/fb1aa5b) | [#368](https://github.com/zidaneyoung/Achiwave/pull/368) | `apps/backend/src/achiwave_backend/worker.py` | Real Celery worker and diagnostic task — worker became ready and returned the expected result. | Pass |
| [#27](https://github.com/zidaneyoung/Achiwave/issues/27) | `stage-2/backend-foundation-23-27` | [`6d409b8`](https://github.com/zidaneyoung/Achiwave/commit/6d409b8) | [#368](https://github.com/zidaneyoung/Achiwave/pull/368) | `apps/backend/src/achiwave_backend/worker.py`, `apps/backend/README.md` | Celery Beat startup — scheduler initialized with UTC settings and the intentionally empty Stage 2 schedule. | Pass |
| [#28](https://github.com/zidaneyoung/Achiwave/issues/28) | `stage-2/persistence-health-28-31` | [`18a7106`](https://github.com/zidaneyoung/Achiwave/commit/18a7106) | [#369](https://github.com/zidaneyoung/Achiwave/pull/369) | `apps/backend/src/achiwave_backend/database.py`, `apps/backend/tests/test_database.py` | Pytest plus real PostgreSQL `SELECT 1` — session lifecycle and connection passed without domain tables. | Pass |
| [#29](https://github.com/zidaneyoung/Achiwave/issues/29) | `stage-2/persistence-health-28-31` | [`d8d64d0`](https://github.com/zidaneyoung/Achiwave/commit/d8d64d0) | [#369](https://github.com/zidaneyoung/Achiwave/pull/369) | `apps/backend/alembic.ini`, `apps/backend/migrations/versions/20260731_0001_stage2_baseline.py` | `alembic upgrade head`, `downgrade base`, then `upgrade head` against PostgreSQL — all exited 0. | Pass |
| [#30](https://github.com/zidaneyoung/Achiwave/issues/30) | `stage-2/persistence-health-28-31` | [`ec2a724`](https://github.com/zidaneyoung/Achiwave/commit/ec2a724) | [#369](https://github.com/zidaneyoung/Achiwave/pull/369) | `apps/mobile/.env.example`, `apps/backend/.env.example`, `.gitignore` | Settings tests and tracked-file audit — examples load and real `.env` files remain ignored. | Pass |
| [#31](https://github.com/zidaneyoung/Achiwave/issues/31) | `stage-2/persistence-health-28-31` | [`6d7135c`](https://github.com/zidaneyoung/Achiwave/commit/6d7135c) | [#369](https://github.com/zidaneyoung/Achiwave/pull/369) | `apps/backend/src/achiwave_backend/health.py`, `apps/backend/tests/test_health.py` | Pytest plus live dependency transitions — liveness stayed 200; readiness returned 200 with both dependencies and 503 for each unavailable dependency without leaking URLs. | Pass |
| [#32](https://github.com/zidaneyoung/Achiwave/issues/32) | `stage-2/local-infrastructure-32-33` | [`170e2e1`](https://github.com/zidaneyoung/Achiwave/commit/170e2e1), [`94fcfe1`](https://github.com/zidaneyoung/Achiwave/commit/94fcfe1) | [#370](https://github.com/zidaneyoung/Achiwave/pull/370) | `infrastructure/compose.local.yaml`, `apps/backend/Dockerfile` | Compose config plus a full WSL Docker run — five services became healthy, migration/current passed, worker task completed, and PostgreSQL data survived stop/start. | Pass |
| [#33](https://github.com/zidaneyoung/Achiwave/issues/33) | `stage-2/local-infrastructure-32-33` | [`f3e6d2c`](https://github.com/zidaneyoung/Achiwave/commit/f3e6d2c), [`94fcfe1`](https://github.com/zidaneyoung/Achiwave/commit/94fcfe1) | [#370](https://github.com/zidaneyoung/Achiwave/pull/370) | `apps/backend/src/achiwave_backend/logging_config.py`, `apps/backend/tests/test_logging.py` | Pytest and live API/worker/scheduler logs — application records parsed as JSON, included service context, and redacted configured credentials and URLs. | Pass |
| [#34](https://github.com/zidaneyoung/Achiwave/issues/34) | `stage-2/android-runtime-config-34-36` | [`b3a3248`](https://github.com/zidaneyoung/Achiwave/commit/b3a3248) | [#371](https://github.com/zidaneyoung/Achiwave/pull/371) | `apps/mobile/app/_layout.tsx` | Android API 36 emulator build/install plus a deliberate release render failure — the accessible fixed-message fallback displayed without the injected internal error detail, and tapping `Try again` restored the normal screen. | Pass |
| [#35](https://github.com/zidaneyoung/Achiwave/issues/35) | `stage-2/android-runtime-config-34-36` | [`399a810`](https://github.com/zidaneyoung/Achiwave/commit/399a810), [`7ab5ca9`](https://github.com/zidaneyoung/Achiwave/commit/7ab5ca9) | [#371](https://github.com/zidaneyoung/Achiwave/pull/371) | `apps/mobile/app.config.ts`, `apps/mobile/src/config/environment.js`, `apps/mobile/src/api/client.ts` | Development emulator config and explicit production config resolved; missing/insecure production URLs failed clearly; mock liveness request, schema rejection, timeout, and sanitized failure checks passed. | Pass |
| [#36](https://github.com/zidaneyoung/Achiwave/issues/36) | `stage-2/android-runtime-config-34-36` | [`fe1924e`](https://github.com/zidaneyoung/Achiwave/commit/fe1924e), [`5447248`](https://github.com/zidaneyoung/Achiwave/commit/5447248) | [#371](https://github.com/zidaneyoung/Achiwave/pull/371), [#372](https://github.com/zidaneyoung/Achiwave/pull/372) (path correction) | `docs/local-development.md`, `docs/testing/stage-2-acceptance.md` | PowerShell local-link audit — all 23 Markdown files had no broken local links; all 19 issue rows reference existing committed files; documented mobile and backend checks produced the results below. | Pass |

## Final branch verification

- `.\.venv\Scripts\python.exe -m pytest -q` in `apps/backend`: Pass,
  31 tests passed. An initial invocation with the global Python failed
  collection because the editable package was not installed there; activating
  the documented package virtual environment resolved that setup error.
- `npx expo-doctor` with the documented development environment: Pass, 20/20
  checks. An invocation without `.env` failed at config evaluation as intended
  because required public API settings were absent.
- `npx expo export --platform android --output-dir .stage2-final-export` with
  development config: Pass, the Android bundle and assets exported. The
  generated output was removed afterward.
- strict TypeScript, development and production Expo config evaluation,
  invalid-production-config rejection, and API-client behavior checks: Pass.
- `npx expo run:android --device Achiwave_Issue34_API36_G --no-bundler` from a
  short disposable worktree at the audited commit: Pass, the debug APK built
  and installed on the API 36 emulator. A self-contained release APK with a
  temporary deliberate render failure also built and installed; UI Automator
  observed the safe accessible fallback, absence of the injected internal
  detail, and successful recovery after tapping `Try again`. The temporary
  source change, Git worktree, emulator, and AVD definitions were removed.
- PowerShell local Markdown link audit: Pass, 23 files checked with no broken
  local links.

## Runtime cleanup

The disposable Compose verification project contained exactly the expected five
containers, network, and PostgreSQL volume. It was removed with `down -v` after
the persistence check; that disposable database volume is not recoverable.
No verification containers or volumes remain.
