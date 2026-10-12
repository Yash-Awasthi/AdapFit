# AdapFit — open work

The one working list: what is left, nothing that is finished. Product limits
live in `docs/PRODUCT_SCOPE.md` (consumer wellness, India first, nothing
diagnoses); how each feature was checked lives in `docs/FEATURE_STATUS.md`.

## What the product optimises for

1. Little or no manual logging.
2. Turn data into a decision: what to do today, and why.
3. Adapt daily rather than prescribe a static plan.
4. Reliable, explainable recommendations: rules pick the decision, a model may
   only phrase it.
5. Trust: privacy, no dark subscriptions, the user owns their data.

The proprietary core is the recovery model, training-load model, personal
baseline, safety rules and recommendation policy; everything around it should
be borrowed infrastructure.

## On a phone

- Walk the core loop: sign-up, onboarding, check-in (pain toggle, sore areas),
  Home decision, generate workout, sets and rest timer, finish, completion.
- Run `mobile/e2e/core-journey.yaml` (Maestro); fix selectors it cannot find and
  add flows for check-in edge cases and sign-out.
- Camera heart rate with a real fingertip, the form checker with a person
  exercising, a BLE heart-rate strap; decide which wearables to keep for launch.
- Voice log, GPS distance, and the two-account features (Family, Community,
  Forums) with real use.
- A Health Connect record deleted on the phone disappearing from the server
  (needs a record the owner can delete, from an app that writes to Health
  Connect).
- Skin spot photo measurement (`lesion_measure.py`) on real phone photos of
  moles with a coin for scale.

## App

- Localisation: no screen calls `t()`; the app is English only. Hindi first:
  extract the core journey's strings, translate, add a picker.
- Safety screening covers English, Hindi and Hinglish only; do not offer other
  languages until it covers them.
- Layout: page content scrolls over the status bar; Record a route has a large
  empty area above Start; Filter by Muscle sits tight against Quick actions.
- Sleep sounds stop listening when the screen turns off (JS timers pause);
  native metering would lift the black-overlay workaround.
- Screens for API-only features: peer support, vaccination records (health
  passport), accessible workout alternatives, the accessibility API.
- Stroke rehab, chronic disease management, hospital at home and wound
  assessment are API-only; design each with a clinician before giving it a
  screen. A coach marketplace only with verified, real practitioners.
- Performance and app size.
- Unused-import lint backlog (about 280 entries); CI checks only syntax and
  undefined names.

## Infrastructure

- Server-side AI on Render needs a key from a provider that accepts datacenter
  IPs (Groq or OpenRouter); until then the phone calls the model directly.
  Move the AI key out of the app bundle once that works.
- Rotate every token that was shared in chat.
- Uptime monitor on `/health` (needs the owner's account).
- Remote push (FCM): needs a Firebase project and a server event worth pushing.
- iOS project, build profile, HealthKit entitlement and sync.
- Rotated-token memory and the "sessions ended at" cut-off live in process
  memory; persist them before running more than one worker.
- Expo upgrade only for features, on a branch, with a full device walk; SDK 56
  does not clear the remaining advisories (`docs/SECURITY.md`). Drop the
  accepted ids in `mobile/scripts/audit-gate.mjs` when fixes ship.
- Re-run `python -m scripts.build_cdsco_fdc` when a new 26A notification is
  published.

## Owner decisions before launch

- Paid tiers when wanted: tiers, INR prices, trial length, what stays free; a
  Play Console payments profile; then server-side entitlements, Play Billing,
  restore purchases, refunds and receipts. Every feature is free until then.
- Who reviews community reports (they land in the audit log as
  `community_report`); the Play target audience.
- Company and legal entity, insurance, payment accounts; legal review of
  third-party data (Indian Medicine Dataset, NMC register search) and of
  `backend/app/legal/` with its `[...]` placeholders filled; Grievance Officer;
  SMTP; DigiLocker age verification for guardian consent.
- Third-party penetration test, closed beta and feedback loop, support channel,
  incident response and breach notification procedure.
- Store graphics, screenshots and the `[...]` answers in
  `docs/STORE_LISTING.md` and `docs/HEALTH_CONNECT_DECLARATION.md`.

## Not doing

- FHIR R4 wholesale: a storage rewrite, to be scoped on its own if needed.
- Ownership checks in `AuthMiddleware`: it cannot know which resource a route
  addresses and cannot see WebSocket traffic; the check belongs at the route
  layer (`IdentityMiddleware` binds `user_id`).
