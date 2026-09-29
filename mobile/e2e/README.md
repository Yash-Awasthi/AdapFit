# End-to-end tests

`core-journey.yaml` walks sign-up, consent, onboarding, the morning check-in and one
workout on a real device, using [Maestro](https://maestro.mobile.dev). Maestro drives the
installed release build through adb, so it needs no changes to the app and no debug build.

Run it with the phone attached and the release APK built:

    e2e/run.sh [adb-serial]

The script reinstalls the APK for a clean start (some phones refuse to clear app data over
adb), then signs up a fresh account (`e2e<timestamp>@example.com`) on whichever API the
build points at, so run it against staging, not production. It stops short of the Health Connect, location and microphone
prompts, which need a person.

Install Maestro from https://github.com/mobile-dev-inc/maestro/releases (Java 17 or later).
