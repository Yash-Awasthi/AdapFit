# AdapFit plan

The single working plan. It replaces `todo.md`, `ROADMAP.md`, `HANDOFF.md`, `START.md`, `betterstack.md` and `mobile/notes.md`; everything open in those files is either a step below or in the parking lot at the end. Product limits stay in `docs/PRODUCT_SCOPE.md`; how each feature was checked stays in `docs/FEATURE_STATUS.md`.

Written 2026-10-16.

## Goal

An installable Android APK, shared with other people, that works end to end against a fresh Render deployment.

- Audience: portfolio. No store launch, no company or legal work for now.
- Pitch: everything health in one app, India first.
- No feature is removed. The ~70 screens are regrouped into five sections.
- Data comes from phone sensors, manual entry and Health Connect. No wearable is required.

## Phase 1: backend on a new Render service

Why first: the APK needs a server to talk to, and several steps below depend on it.

1. Create a new Postgres (Neon, as `render.yaml` assumes) and note its direct connection string. Done 2026-10-16: Neon project `sweet-mouse-88906796`, branch `production`.
2. Generate `DATA_ENCRYPTION_KEYS` and keep a copy outside the repository. A different key later makes startup refuse to load sealed rows. Done 2026-10-16: kept in the gitignored `.env.deploy`; copy it to a password manager.
3. Create the Render service from `render.yaml` (Blueprint). Fill `DATABASE_URL`, `DATA_ENCRYPTION_KEYS`, `PUBLIC_BASE_URL`, and one AI key (`GROQ_API_KEY` or `GEMINI_API_KEY`). Done 2026-10-16: service `adapfit` at https://adapfit.onrender.com, created through the Render API with `LLM_DAILY_CALLS=10`.
4. Apply migrations through 014 on the new database. A fresh database needs no pickle-to-JSON conversion; the Dockerfile applies pending migrations on start, so confirm in the logs that it did. Done 2026-10-16: 000 to 016 applied on first start.
5. Check `/health`, then run `uv run python -m scripts.verify_postgres` against the new `DATABASE_URL`. Done 2026-10-16: healthy, and verify_postgres passed.
6. Run the backend tests locally: `uv run python -m pytest tests -q -p no:warnings` (needs Python 3.14 and uv). Done 2026-10-16: 1130 passed, 1 skipped.
7. Rotate every token that was shared in chat. This includes the AI key and anything in the old staging environment.

Done when: `/health` answers on the new URL and `verify_postgres` passes. Done 2026-10-16, except step 7.

## Phase 2: group the screens into five sections

Sections: Today, Body, Mind, Care, Community. Niche programs sit in a list inside Care. Settings, account and legal screens stay under More.

The map below is a draft for your review. Nothing moves until you approve it.

| Section | Screens |
| --- | --- |
| Today | index, checkin, recovery-dashboard, dashboard, trends, stats, analytics, achievements, habits, coach, chat, health-calendar, everyday |
| Body | workouts, workout, workout-detail, workout-active, workout-complete, exercises, periodization, run-record, form-checker, posture, body, sleep, hrv, vital-signs, camera-heart-rate, nutrition, precision-nutrition, recipes, longevity, voice-health |
| Mind | mental-health, wellness, sleep-sounds, ambient, circadian, addiction-recovery |
| Care | conditions, medication, emergency, care, health, health-hub, cycle, pregnancy, fertility, diabetes, cardiac-rehab, chronic-pain, respiratory, skin-health, medical-imaging, genomics, telemedicine, remote-monitoring, health-savings, health-equity |
| Community | community, forums, family, content-feed |
| More (not a section) | menu, settings, personal-info, data-export, accessibility-settings, devices, privacy, legal, dev-tools, login, register, onboarding |

Steps:

1. Review and correct the map above. Done 2026-10-16: approved as drafted.
2. Rebuild `mobile/app/(tabs)/_layout.tsx` with five tabs, one per section, plus More. Done 2026-10-16.
3. Add one landing screen per section that lists its screens. Care's landing is the searchable list of programs. Done 2026-10-16: the map lives in `mobile/src/navigation/sections.ts`.
4. Make Today the entry point: the decision and "why" first, then links into the other sections. Done 2026-10-16.
5. Remove or fix dead links so every screen is reachable from exactly one section. Done 2026-10-16: no dead links found; `npm run check:sections` (also in CI) fails if a screen is unlisted, listed twice, or linked but missing.

Done when: all existing screens are reachable from the five sections and `npx tsc --noEmit` passes. Done 2026-10-16.

## Phase 3: build and test on your phone

1. Point the app at the new Render URL. Done 2026-10-16.
2. Install and type-check: `cd mobile`, `npm ci`, `npx tsc --noEmit`, `node scripts/audit-gate.mjs`. Done 2026-10-16.
3. `android/` is no longer in git. If an old `android\` folder still exists, move `android\keystore.properties` and `android\app\adapfit-release.keystore` up to `mobile\` first (set `storeFile=adapfit-release.keystore`). Then `npx expo prebuild -p android --clean` and `npx expo run:android`. Done 2026-10-16: the old key was not found, so a new release key was made (the app is not on Play); prebuild and the release build pass (Windows needs the long-path setup in `docs/DEPLOYMENT.md`). Install on the phone pending.
4. Walk the core loop and confirm each of these:
   - Sign-up, onboarding, check-in.
   - Check-in with the pain toggle on gives a REST decision and a mobility session.
   - A sore area (for example legs) is left out of that day's plan.
   - Home decision, generate workout, sets, rest timer (uses each exercise's prescribed rest), finish.
   - Finishing records the workout once, with the RPE from the completion screen.
   - A workout finished offline and synced later shows on the day it was done.

   Checked 2026-10-16 against the live server through the API the app calls: pain gives REST and a mobility session, sore legs are left out, a repeated finish is logged once, and the workout list shows it completed with its RPE on the day it was done (the list ignored completions before; fixed). On the phone itself it is still unwalked.
5. Run the Maestro flow `mobile/e2e/core-journey.yaml`. Fix selectors it cannot find. Add flows for check-in edge cases and sign-out. Flows added 2026-10-16 (`checkin-pain.yaml`, `sign-out.yaml`) and the selectors updated for the shortened onboarding; sign-up and onboarding pass on an emulator, the full flows still need a run on a device.
6. Phone-sensor and Health Connect checks:
   - Camera heart rate with a real fingertip: torch fires, a plausible BPM appears. Save readings to Vital Signs (done 2026-10-16 through `POST /vitals/pulse`; needs a push to reach the server). Watch logcat for dropped frames; `FRAME_RESOLUTION` is 100x100, stride 64 bytes.
   - Health Connect sync, and a record deleted on the phone disappearing from the server (needs a record the owner can delete, from an app that writes to Health Connect).
   - GPS distance on a short outdoor walk.
   - Form checker with a person exercising.
   - Voice log with a spoken workout.
7. Open each screen in the five sections once. Fix crashes, empty states with no explanation, and layout faults (content scrolling over the status bar, the large empty area above Start in Record a route, Filter by Muscle tight against Quick actions).
   Fixed 2026-10-16: the large empty area in Record a route and the tight Filter by Muscle header. The other screens still need opening on a device.
8. Remove the unused `react-native-vision-camera-worklets` dependency (no frame processors are used), then rebuild. Removed and rebuilt 2026-10-16.
9. Add a clearly flagged demo-data option only if empty screens make the app unusable without wearable data. Decided 2026-10-16: not built; every screen has manual entry, and invented data would break the "measured or missing" rule.

Done when: the core loop works on the phone against the new server, and every screen opens without a crash.

## Phase 4: release APK and share

1. Build the signed release APK. Keep the keystore backed up outside the repository. Built 2026-10-16: version 2.1.0 (versionCode 2), arm64, signed with a new key, so an older AdapFit install must be removed first. Keystore backup pending.
2. Check the app size and startup on the phone.
3. Install on a second phone from the file to confirm a clean install, sign-up and core loop.
4. Share the APK (GitHub release or a direct link) with a short install note: enable install from unknown sources, Health Connect permission, the server may take up to a minute to wake on the free plan. Done 2026-10-16: GitHub release v2.1.0 with the APK and the install note.
5. Collect feedback from the first few users in one place.

Done when: someone other than you installs the APK and finishes the core loop.

## Parking lot (not needed for the APK, kept from the old plans)

App
- Hindi first: no screen calls `t()` today. Extract the core journey's strings, translate, add a picker. Safety screening covers English, Hindi and Hinglish only; do not offer other languages until it covers them.
- Sleep sounds stop listening when the screen turns off (JS timers pause); native metering would lift the black-overlay workaround.
- Posture assessment needs a pose detector and frame access, the same gap camera heart rate had.
- Screens for API-only features: peer support, vaccination records, accessible workout alternatives, accessibility API.
- Stroke rehab, chronic disease management, hospital at home and wound assessment stay API-only until designed with a clinician. A coach marketplace only with verified, real practitioners.
- Skin spot photo measurement (`lesion_measure.py`) on real phone photos of moles with a coin for scale.
- Bluetooth heart-rate strap, and the two-account features (Family, Community, Forums) with real use. Decide which wearables to keep.
- Performance and app size.
- Unused-import lint backlog (about 280 entries) and Biome warnings (about 830 lines). CI fails only on errors.

Infrastructure
- Server-side AI on Render needs a key from a provider that accepts datacenter IPs (Groq or OpenRouter). Until then the phone calls the model directly. Then move the AI key out of the app bundle.
- Uptime monitor on `/health` (needs your account).
- Remote push (FCM): needs a Firebase project and a server event worth pushing.
- iOS project, build profile, HealthKit entitlement and sync (needs a Mac for `run:ios`).
- Expo SDK 58 and React Native 0.88 are pre-releases. Move to the final releases when they ship and drop the accepted ids in `mobile/scripts/audit-gate.mjs`. An older Expo SDK does not clear the remaining advisory (`docs/SECURITY.md`).
- Re-run `python -m scripts.build_cdsco_fdc` when a new 26A notification is published.

Before any public store launch
- Paid tiers and Play Billing (every feature is free until then): tiers, INR prices, trial length, Play payments profile, entitlements, restore purchases, refunds.
- Who reviews community reports (`community_report` in the audit log); Play target audience.
- Company and legal entity, insurance, payment accounts; legal review of third-party data (Indian Medicine Dataset, NMC register search) and of `backend/app/legal/` with its `[...]` placeholders filled; Grievance Officer; SMTP; DigiLocker age verification for guardian consent.
- Third-party penetration test, closed beta, support channel, incident response and breach notification.
- Store graphics, screenshots, and the `[...]` answers in `docs/STORE_LISTING.md` and `docs/HEALTH_CONNECT_DECLARATION.md`.

## Not doing

- FHIR R4 wholesale: a storage rewrite, to be scoped on its own if needed.
- Ownership checks in `AuthMiddleware`: it cannot know which resource a route addresses and cannot see WebSocket traffic. The check belongs at the route layer (`IdentityMiddleware` binds `user_id`).
