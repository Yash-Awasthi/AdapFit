# AdapFit — road to a commercial release

Each phase is one working session. Every phase starts with an investigation
step: measure the current state, write down what was found, then decide the
concrete work. The bullets below are starting questions, not a fixed task list.
`plan.md` holds the defect history; this file holds what is left to ship.
`docs/PRODUCT_SCOPE.md` holds the positioning every phase works inside: consumer
wellness, India first, every feature kept, nothing diagnoses.

---

## Phase 2 — Consolidation

Every feature stays; duplicates of the same feature do not.

- Collapse duplicate generations (sleep, HRV, achievements, coach, community,
  recovery, export) to one module each.
- Resolve shared route prefixes, make registration idempotent.
- Replace sample data that still ships in screens (the mental health screen
  has a hard-coded journal and a wellbeing score fixed at 72).
- Measure endpoint, service, screen and test counts before and after.

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
