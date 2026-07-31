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
