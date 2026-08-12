# Achiwave mobile

This package contains the native Expo application for Android and future iOS
support. Run all mobile commands from this directory.

## Environment

Create local public configuration before running Expo:

```powershell
Copy-Item .env.example .env
```

`EXPO_PUBLIC_API_ENV` selects the API environment and
`EXPO_PUBLIC_API_BASE_URL` points to the backend. Android emulators reach a
backend running on the host through `http://10.0.2.2:8000`; physical devices
need a reachable local-network URL instead. Every `EXPO_PUBLIC_*` value is
embedded in the application bundle and must never contain a secret.

Production configuration must set `EXPO_PUBLIC_API_ENV=production` and supply
`EXPO_PUBLIC_API_BASE_URL` explicitly as an HTTPS URL. Expo config evaluation
fails when that production URL is missing, malformed, credential-bearing, or
non-HTTPS. Production URLs and credentials are never committed to this
repository.

## Stage 4 authentication lifecycle

Android credentials and the stable installation ID use environment-scoped Expo
SecureStore keys. Protected routes are enabled only after the backend validates
or refreshes a structurally valid saved session. Network loss with a previously
confirmed session enters a minimal read-only offline screen; it does not create a
server session or enable offline mutations.

Logout and account deactivation lock in-memory authentication immediately and
run the centralized protected-data purge for the current authentication envelope
and owner-bound presentation-preference cache. The public environment config and
stable installation ID remain. See the
[Stage 4 authentication design](../../docs/security/stage-4-authentication.md)
and [acceptance audit](../../docs/testing/stage-4-acceptance.md).

## Stage 5 design foundations

The app follows the system light/dark appearance through centralized semantic
colour tokens. Typography, 4-point spacing, radii, elevation, viewport, and
touch-target values are shared rather than restated per screen. See the
[Stage 5 visual direction](../../docs/design/stage-5-visual-direction.md) and
[mobile design system](../../docs/design/stage-5-design-system.md). Verification
evidence is recorded in the
[Stage 5 acceptance audit](../../docs/testing/stage-5-acceptance.md).

## Stage 6 campaign and quest management

Authenticated Android users can create, inspect, edit, archive, restore,
filter, reorder, and refresh campaigns and one-time quests while the backend
retains ownership, lifecycle, record-version, scheduling, and reward authority.
See the [Stage 6 feature contract](../../docs/features/stage-6-campaigns-and-quests.md)
and [acceptance audit](../../docs/testing/stage-6-acceptance.md).

## Stage 7 completion and synchronization

Android presents server-confirmed completion/reversal state, safe pending
feedback, and the controlled durable offline completion queue. It does not award
progression. See the
[Stage 7 feature contract](../../docs/features/stage-7-completion-and-synchronization.md)
and [acceptance audit](../../docs/testing/stage-7-acceptance.md).

## Android identity

Stage 2 development builds use `com.zidaneyoung.achiwave.dev` and the `achiwave`
application scheme. Final production application-identifier and Google Play
configuration remain deferred to issue #333.

## Android development builds

Use `npx expo run:android` for a local development build after installing a JDK,
Android Studio, and the Android SDK/platform tools.

The `development` profile in `eas.json` creates an internally distributed Android
APK with the Expo development client. Running
`npx eas-cli build --platform android --profile development` requires an
authenticated Expo account and project linking. Stage 2 intentionally does not
invent or commit an EAS project identifier or credentials.

Run local acceptance checks with a configured non-secret development API URL:

```powershell
npm ci
npm run typecheck
npm run test:security
npm run test:theme
npx expo-doctor
npx expo export --platform android
```
