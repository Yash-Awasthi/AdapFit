#!/bin/sh
# Reinstall the release APK before each flow for a clean slate, then run every flow on the attached phone.
# usage: e2e/run.sh [adb-serial] [flow.yaml ...]   (needs adb and maestro on PATH)
set -e
DIR="$(dirname "$0")"
APK="$DIR/../android/app/build/outputs/apk/release/app-release.apk"
DEVICE="${1:-$(adb devices | awk 'NR==2 {print $1}')}"
[ $# -gt 0 ] && shift
FLOWS="${*:-$DIR/core-journey.yaml $DIR/checkin-pain.yaml $DIR/sign-out.yaml}"
for flow in $FLOWS; do
  adb -s "$DEVICE" uninstall com.adapfit.app >/dev/null 2>&1 || true
  adb -s "$DEVICE" install "$APK"
  maestro --device "$DEVICE" test "$flow"
done
