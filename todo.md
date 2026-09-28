# AdapFit — road to a commercial release

Each phase is one working session. Every phase starts with an investigation
step: measure the current state, write down what was found, then decide the
concrete work. The bullets below are starting questions, not a fixed task list.
`plan.md` holds the defect history; this file holds what is left to ship.
`docs/PRODUCT_SCOPE.md` holds the positioning every phase works inside: consumer
wellness, India first, every feature kept, nothing diagnoses.

---

## Phase 4 — Security hardening

- Token storage on device, session lifetime, refresh rotation review.
- Encryption at rest and field-level encryption for the most sensitive records.
- Access audit trail for health records.
- Rate limiting and abuse protection on auth and expensive routes.
- Secrets management and credential rotation.
- Public surfaces (`/metrics`, docs, admin pages, WebSockets).
- `health_security` keeps encryption keys in process memory, and the auth audit
  log is an in-memory list; both are lost on restart and neither belongs in the
  feature store.
- Dependency and container scanning; third-party penetration test before launch.
- The privacy policy promises 1-year retention of security logs; the auth
  audit log is in memory, so move it to durable storage with that retention.
- `POST /api/v1/users` is public and creates profile rows with no account or
  consent; the mobile user store falls back to the seeded `default` identity
  when nothing is stored.

## Phase 5 — Platform coverage and device data

- Photo measurement of skin spots (`lesion_measure.py`) is tested on synthetic
  images only; calibrate on real phone photos of moles with a coin.

- iOS project, build profile and HealthKit entitlement.
- Health Connect and HealthKit sync actually wired and installed.
- Wearable and BLE integrations worth keeping for launch.
- `actigraphy_analysis` (rest-activity rhythm) once hourly activity syncs.
- Live GPS run recording (`gps_tracking`) and night sleep-audio (`sleep_audio`)
  have APIs but need on-device capture.
- `realtime_pipeline` is only exercised by tests; decide with live streaming.
- Health Connect sync can supply blood glucose to the CGM summary
  (`/diabetes/glucose/import` already takes bulk readings).
- Real-device testing of camera heart rate, pose and sensors.
- Offline behaviour and sync conflicts.
- Push notifications end to end.

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

## Phase 8 — Infrastructure and operations

- Build and deploy images; staging and production environments.
- The server must run one worker until feature state moves to per-request
  loading (all three Dockerfiles now say so). Three Dockerfiles is two too many.
- Verify `feature_state` on real Postgres: local login for `adapfit` failed with
  the password in `backend/.env` on 2026-09-28, so only SQLite was exercised.
- Postgres backups with a tested restore. Keep backups at most 30 days (the
  privacy policy says so) and re-run erasures requested after the backup.
- Error tracking and crash reporting on backend and mobile.
- Metrics, logs, uptime alerts, on-call basics.
- CI that blocks on types, lint and mobile checks; release pipeline for EAS.
- Load test the core loop.

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

- Store listings, screenshots, descriptions, age ratings, review notes.
- Health data declarations for Google Play and Apple.
- Closed beta, feedback loop, analytics with consent.
- Support channel, incident response, breach notification procedure (Board
  and users without delay, full report within 72 hours; see `docs/PRIVACY.md`).
- Fill the placeholders in `backend/app/legal/`, legal review, appoint the
  Grievance Officer, configure SMTP, and add DigiLocker age verification for
  guardian consent.
- Company, legal entity, insurance and payment accounts.
