# AdapFit — road to a commercial release

Each phase is one working session. Every phase starts with an investigation
step: measure the current state, write down what was found, then decide the
concrete work. The bullets below are starting questions, not a fixed task list.
`plan.md` holds the defect history; this file holds what is left to ship.
`docs/PRODUCT_SCOPE.md` holds the positioning every phase works inside: consumer
wellness, India first, every feature kept, nothing diagnoses.

---

## Phase 6 — Monetisation

- Subscription model and pricing tiers.
- In-app purchase integration for both stores.
- Server-side entitlements and feature gating.
- Trials, restore purchases, refunds, receipts.
- LLM cost per user and quotas that keep tiers profitable.

## Phase 7 — AI and data quality

- `session_load` silently assumes 45 minutes and RPE 5 when a workout omits them;
  the training routes exclude such sessions but ACWR and the recovery engine do not.
- Audit for constant "sample" readings returned as user data. The random-number
  guard cannot see these (device sync and the analytics dashboard were two).

- Every LLM call: purpose, prompt, safety filter, fallback, cost.
- Health-advice guardrails and escalation wording.
- Score and algorithm validation against references (recovery, HRV, sleep,
  readiness).
- Remaining places where values are defaulted or estimated without input.
- The home recovery ring shows 0 when there is no check-in, and the "Train, but
  reduce intensity" advice appears with no data behind it.
- Photo measurement of skin spots (`lesion_measure.py`) is tested on synthetic
  images only; calibrate on real phone photos of moles with a coin.
- Health Connect sync adds and updates records but never learns of deletions;
  use the changes API so a record deleted on the phone leaves the server too.

## Phase 8 — Infrastructure and operations (rest)

Done in plan.md Part 17. Left:

- Staging on the free Render + Neon setup in `docs/DEPLOYMENT.md`: needs the
  owner's accounts there, a Groq or Gemini key, and a Sentry DSN (all free).
- Uptime monitor on `/health` (free UptimeRobot) once staging exists.
- Remote push (FCM): needs a Firebase project, and a server event worth
  pushing; every notification today is a local reminder.
- iOS project, build profile, HealthKit entitlement and sync (deferred).
- Expo past SDK 55 for the moderate advisories in `docs/SECURITY.md`.

## Phase 9 — User experience and quality

- Stroke rehab, chronic disease management, hospital at home and wound
  assessment are API-only; design each with a clinician before giving it a screen.
- Coach marketplace: rebuild only with verified, real practitioners.
- `mobile/e2e` has no runner installed (no detox or jest) and is excluded from
  the typecheck; install one or delete it.

- API-only features still without a screen: peer support, vaccination records
  (health passport), accessible workout alternatives, the accessibility API.
- `test_mobile_api_paths.py` misses calls whose generic type contains nested
  `<...>` (for example `getJson<{ data: Record<string, any> }>(...)`); widen it.
- 12 new hub and feature screens this phase have only been typechecked, never
  run on a device.

- With the user present, on their phone: camera heart rate, pose and sensors,
  and a BLE heart-rate strap. Decide which wearables are worth keeping for launch.
- Reminders are inexact alarms: Android gave a daily reminder a one-hour window.
  Medication times may need exact alarms (`SCHEDULE_EXACT_ALARM`, user-granted).
- Run recording hits expo/expo#50364: if the app is relaunched while a run's
  location task is registered, fixes stop reaching JS (Finish now times out
  instead of hanging). Patch expo-task-manager or move to a native service.
- Sleep sounds stop listening if the screen turns off (JS timers pause); the
  screen stays on under a black overlay. Native metering would lift that.
- Change-password screen (the API returns a fresh token pair; reset by email works).
- Onboarding flow and first-run experience.
- Navigation and information architecture for the reduced feature set.
- Empty, loading and error states.
- Accessibility (screen reader, contrast, text scaling).
- Localisation completeness.
- Performance and app size.
- End-to-end tests for the core journeys.

## Phase 10 — Launch readiness

- Legal review of third-party data: the Indian Medicine Dataset (MIT, but
  scraped retail listings) and use of the NMC register search.
- Add the CDSCO list of banned fixed-dose combinations to the medicine check.

- Third-party penetration test.
- Store listings, screenshots, descriptions, age ratings, review notes.
- Health data declarations for Google Play and Apple.
- Closed beta, feedback loop, analytics with consent.
- Support channel, incident response, breach notification procedure (Board
  and users without delay, full report within 72 hours; see `docs/PRIVACY.md`).
- Fill the placeholders in `backend/app/legal/`, legal review, appoint the
  Grievance Officer, configure SMTP, and add DigiLocker age verification for
  guardian consent.
- Company, legal entity, insurance and payment accounts.
