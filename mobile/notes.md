# Camera heart rate — handoff

Done: `app/camera-heart-rate.tsx` now uses react-native-vision-camera (Nitro)
instead of expo-camera. Back camera + torch, frame processor averages RGB,
posts to POST /api/v1/rppg/estimate-hr-chrom, uses server's bpm/confidence.

Not done: never run on real hardware. No Android SDK / device / iOS folder
in this dev environment (Windows, android/ only, no ios/).

Before shipping:
- `npx expo run:android` on a real phone, check torch fires, finger-over-lens
  gives a plausible BPM in Analyzing state.
- `npx expo prebuild` for iOS (no ios/ dir exists yet), then `run:ios`.
- Watch for frame drops / dropped-frame warnings in logcat — FRAME_RESOLUTION
  is 100x100, stride 64 bytes; tune if CPU-bound.
- Check permission dialog wording on Android (CAMERA already in app.json).

Next open item from the original punch list: posture assessment has the same
gap (needs pose detector, no frame access) — same problem, different screen.
