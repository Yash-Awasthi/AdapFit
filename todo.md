# AdapFit — road to a commercial release

Each phase is one working session. Every phase starts with an investigation
step: measure the current state, write down what was found, then decide the
concrete work. The bullets below are starting questions, not a fixed task list.
`plan.md` holds the defect history; this file holds what is left to ship.
`docs/PRODUCT_SCOPE.md` holds the positioning every phase works inside: consumer
wellness, India first, every feature kept, nothing diagnoses.

---

## Phase 2 — Consolidation (in progress)

Every feature stays; duplicates of the same feature merge into the best one,
and features that exist in code but nothing calls get an API and a screen.
Decided with the user 2026-09-28.

Measured at start: 229 route modules, 281 services, 93 services unreachable
(65 with no importer, 28 used only by tests), 146 route modules no screen calls.

- [x] Sleep: one `/sleep` API and one screen (8d9aab5). Also removed the
      unused `app/api/v1/domains/` routers and the fake `/tasks` jobs.
- [x] HRV: one `/hrv` API over one analyzer with Lipponen artifact correction and
      biofeedback; HRV screen reads a Bluetooth chest strap (standard 0x180D).
- [x] Achievements: one `/achievements` derived from logged activity; the
      self-grant XP/badge routes and the `eval()` goal parser are gone.
- [x] Coach: `/ai-coach` briefing and weekly report built from the user's records
      (the old one picked canned "personal" insights at random); four duplicate
      chat surfaces removed, `/chat` is the one assistant. Briefing screen linked
      from home and menu. Fixed two dead home-screen routes.
- [ ] `ai-coach-v2` (workout plans, form check, demo videos that point at
      missing assets), `health-coaching` (sample coach marketplace), `habits`.
- [x] Community: `/challenges` (now with create and per-user progress) and
      `/community` feed; `/social`, `/community-v2`, `/activity-feed` and the
      social screen removed. Dashboard's medication, challenge and feed panels fixed.
- [x] New test `test_mobile_api_paths.py` fails on any mobile call to a path
      the server lacks. It found: the vital signs screen calling `/vital-signs/*`
      (server serves `/vitals/*`), health calendar calling `/calendar/cycle/*`,
      health hub posting fixed inputs to a missing `/stress/assess` and showing
      50 as the stress level, and a dead api-client module.
- [x] Removed seeded fake data: analytics dashboard (same generated 30 days
      for everyone), forum posts from invented members, and `/seed-demo` is
      closed in production.
- [ ] Dashboard screen needs a full wiring audit (it had three dead calls).
- [x] Recovery: one engine (personal baseline). The dashboard scored HRV against
      population cut-offs with a second engine; it now explains the check-in score
      via `/recovery-logs/today`. Five duplicate recovery engines removed.
- [x] Export: one `/export` over the real stores; `/export/all` includes every
      per-user service's state. `-v2` returned a sample export, `/data-export`
      was a second copy. Export screen saves real files.
- [x] Sixteen mobile files called the API without the auth token; one
      `authedFetch` helper now covers them.
- [x] Leftover duplicates: `/injury-risk-v2`, `/recommendations-v2`, `/recommend`.
- [x] Deleted 52 unreachable services that duplicated wired features, had no
      possible input (EEG staging, WHOOP frames), or were off-domain (a stock
      factor engine). Services: 281 at start, 201 now.
- [ ] Wire the 18 unique ones, API and screen, grouped by where they surface:
      - [x] Medication: openFDA lookup (brand or generic, Indian names mapped)
        and an interaction check on the screen; interaction results now give a
        next step instead of prescriber dose advice. `medication_safety`
        duplicated the existing Beers check and was removed.
      - [x] Diabetes: CGM analyzer drives the summary (episodes, CV, GMI,
        consensus targets) with a bulk import route; insulin and medication
        advice removed from pattern messages.
      - [x] Devices: Garmin/Strava "import" parsed files and stored nothing, and its
        log was shared across users; imports now save workouts and nights per
        user, deduplicated. GPX import added (defusedxml). The device "sync" button
        wrote fixed sample readings (7200 steps, 72 bpm) as the user's data;
        removed. Devices screen rebuilt around strap + file import.
      - [x] Training analytics: `/training/form` (fitness/fatigue/form from
        session-RPE load, sessions without RPE excluded), `/training/intensity`,
        `/training/ride-fueling` (planner had never run: a field-name bug). On Stats.
      - [x] `cycling_analysis`: climbs detected on GPX import.
      - [ ] `core_training` (pull-up progression) still unwired.
      - [x] Circadian: personal alertness curve (two-process model timed by the
        sleep journal's mid-sleep) on the circadian screen; the old fatigue model
        used arbitrary constants. Chronotype cards relabelled as general guidance.
      - [ ] `actigraphy_analysis` needs hourly activity from device sync (Phase 5).
      - [x] Nutrition: targets from profile and weight (Mifflin-St Jeor + protein
        recommender) replace a fixed 2500 kcal/150 g for everyone; meal entries
        whose calories disagree with their macros are flagged.
      - [x] Insights: personal patterns (sleep vs next-day mood and recovery,
        10+ paired days, only clear differences) in the briefing. `quantified_self`
        turned out to be another logger with no correlation code; removed.
      - [x] Vital signs: NEWS2 home check (`/vitals/check`) with the single-parameter
        red-score rule it was missing and plain next steps.
      - Conditions: `chronic_fatigue` (ME/CFS energy envelope and pacing).
- [x] Mind screen: mood check-ins, journal, WHO-5/PHQ-9/GAD-7 with safe next
      steps (no medication advice), CBT thought records API, tap-to-call crisis
      lines. The old screen was fake and its mood button posted to a missing route.
- [ ] CBT thought records have an API but no screen yet.
- [x] `test_no_random_measurements.py` now sweeps route modules too; the
      simulator is closed in production.
- [x] Route ownership test: one module per prefix except named companions, no
      duplicate method+path, registration repeatable.

## Phase 2b — Clinical modules built for real

Cardiac rehab, skin health, medical imaging, genomics, telemedicine, diabetes,
pregnancy, medication, remote monitoring, voice health. Each gets a real
implementation that screens and refers without diagnosing.

- Genomics disease risk is an invented additive model (0.1 baseline plus fixed
  increments) reported as a probability; replace with published effect sizes
  or report variants without a risk figure.
- Skin and imaging: real image measurement (on-device segmentation) instead
  of self-assessed ABCDE numbers.
- Telemedicine: a real registered-practitioner provider, per the 2020 guidelines.
- Medication: Indian brand names and the CDSCO drug list alongside OpenFDA.
- Offline copies of the red-flag and first-aid content.

## Phase 3 — Privacy, consent and user rights

Target the DPDP Act 2023 and DPDP Rules 2025 first.

- Account deletion that wipes every store (Postgres, per-user service state,
  files, caches, backups policy).
- Full data export in a portable format.
- Consent capture at onboarding, versioned and timestamped.
- Data retention rules per record type.
- Privacy policy, terms of service, medical disclaimer, store privacy labels.

## Phase 4 — Security hardening

- Token storage on device, session lifetime, refresh rotation review.
- Encryption at rest and field-level encryption for the most sensitive records.
- Access audit trail for health records.
- Rate limiting and abuse protection on auth and expensive routes.
- Secrets management and credential rotation.
- Public surfaces (`/metrics`, docs, admin pages, WebSockets).
- Dependency and container scanning; third-party penetration test before launch.

## Phase 5 — Platform coverage and device data

- iOS project, build profile and HealthKit entitlement.
- Health Connect and HealthKit sync actually wired and installed.
- Wearable and BLE integrations worth keeping for launch.
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

- Every LLM call: purpose, prompt, safety filter, fallback, cost.
- Health-advice guardrails and escalation wording.
- Score and algorithm validation against references (recovery, HRV, sleep,
  readiness).
- Remaining places where values are defaulted or estimated without input.

## Phase 8 — Infrastructure and operations

- Build and deploy images; staging and production environments.
- Postgres backups with a tested restore.
- Error tracking and crash reporting on backend and mobile.
- Metrics, logs, uptime alerts, on-call basics.
- CI that blocks on types, lint and mobile checks; release pipeline for EAS.
- Load test the core loop.

## Phase 9 — User experience and quality

- Onboarding flow and first-run experience.
- Navigation and information architecture for the reduced feature set.
- Empty, loading and error states.
- Accessibility (screen reader, contrast, text scaling).
- Localisation completeness.
- Performance and app size.
- End-to-end tests for the core journeys.

## Phase 10 — Launch readiness

- Store listings, screenshots, descriptions, age ratings, review notes.
- Health data declarations for Google Play and Apple.
- Closed beta, feedback loop, analytics with consent.
- Support channel, incident response, breach notification procedure.
- Company, legal entity, insurance and payment accounts.
