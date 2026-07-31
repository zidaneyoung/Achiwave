# Achiwave mobile

This package contains the native Expo application for Android and future iOS
support. Run all mobile commands from this directory.

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
