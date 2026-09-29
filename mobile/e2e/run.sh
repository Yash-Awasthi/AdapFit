#!/bin/sh
# Reinstall the release APK for a clean slate, then run the core journey on the attached phone.
# usage: e2e/run.sh [adb-serial]   (needs adb and maestro on PATH)
set -e
APK="$(dirname "$0")/../android/app/build/outputs/apk/release/app-release.apk"
DEVICE="${1:-$(adb devices | awk 'NR==2 {print $1}')}"
adb -s "$DEVICE" uninstall com.adapfit.app >/dev/null 2>&1 || true
adb -s "$DEVICE" install "$APK"
maestro --device "$DEVICE" test "$(dirname "$0")/core-journey.yaml"
