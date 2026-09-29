# AdapFit — road to a commercial release

Each phase is one working session. Every phase starts with an investigation
step: measure the current state, write down what was found, then decide the
concrete work. The bullets below are starting questions, not a fixed task list.
`plan.md` holds the defect history; this file holds what is left to ship.
`docs/PRODUCT_SCOPE.md` holds the positioning every phase works inside: consumer
wellness, India first, every feature kept, nothing diagnoses.

---

## Phase 6 — Monetisation (rest)

Decided 2026-09-29: every feature free at launch. Done in plan.md Part 20:
the per-account daily AI quota. Left for when paid tiers are wanted (owner's
decisions): tiers, INR prices, trial length, what stays free; a Play Console
and payments profile; then server-side entitlements, Google Play Billing,
restore purchases, refunds and receipts.

## Phase 7 — AI and data quality (rest)

Done in plan.md Part 18. Left:

- Photo measurement of skin spots (`lesion_measure.py`) is tested on synthetic
  images only; calibrate on real phone photos of moles with a coin (needs the
  owner's photos).
- `screen_reply` and the red-flag check now cover English, Hindi and Hinglish
  (plan.md Part 26); other languages have none, so do not offer them.
- Verify on a device: a Health Connect record deleted on the phone leaving the
  server after a sync (the server side works; the owner could not delete the
  phone's one steps record). Needs a record the owner can delete, from an app
  that writes to Health Connect.

## Phase 8 — Infrastructure and operations (rest)

Done in plan.md Part 17. Left:

- Staging is live (plan.md Part 26). AI on Render itself needs a key from a
  provider that accepts datacenter IPs (Groq or OpenRouter, free); until then
  the phone calls TokenHarbor directly. Rotate the tokens pasted in chat.
- Uptime monitor on `/health` (free UptimeRobot): needs the owner's account.
- Remote push (FCM): needs a Firebase project, and a server event worth
  pushing; every notification today is a local reminder.
- iOS project, build profile, HealthKit entitlement and sync (deferred).
- Expo past SDK 55 does not clear the remaining advisory (`docs/SECURITY.md`);
  take SDK 56 or 57 only for features, on a branch, with a full device walk.

## Phase 9 — User experience and quality (rest)

Done in plan.md Part 19. Left:

- Stroke rehab, chronic disease management, hospital at home and wound
  assessment are API-only; design each with a clinician before giving it a screen.
- Coach marketplace: rebuild only with verified, real practitioners.
- API-only features still without a screen: peer support, vaccination records
  (health passport), accessible workout alternatives, the accessibility API.
- With the owner, on their phone: camera heart rate, pose and sensors, and a
  BLE heart-rate strap; decide which wearables to keep for launch. Also a
  Health Connect record deleted on the phone disappearing after a sync.
- Sleep sounds stop listening if the screen turns off (JS timers pause); the
  screen stays on under a black overlay. Native metering would lift that.
- Localisation: no screen calls `t()`; the app is English only. Hindi first
  (India launch): extract the core journey's strings, translate, add a picker.
- Performance and app size.
- Layout: page content scrolls over the status bar; Record a route has a large
  empty area above Start; Filter by Muscle sits tight against Quick actions.
- Run `e2e/core-journey.yaml` (Maestro) on the phone and fix the selectors it
  cannot find; add flows for check-in edge cases and sign-out.

## Phase 10 — Launch readiness (rest)

Done in plan.md Part 21: prohibited-FDC check in the medicine lookup, store
listing and Health Connect declaration drafts, legal placeholders flagged.
Left:

- Owner: who reviews community reports (they land in the security audit log
  as `community_report`); choose the Play target audience (sign-up already
  refuses under-13s).
- Owner: company and legal entity, insurance, payment accounts; legal review
  of third-party data (Indian Medicine Dataset, NMC register search) and of
  `backend/app/legal/` with the `[...]` placeholders filled; appoint the
  Grievance Officer; SMTP; DigiLocker age verification for guardian consent;
  third-party penetration test; closed beta and feedback loop; support
  channel, incident response and breach notification procedure; store
  graphics, screenshots and the answers marked `[...]` in
  `docs/STORE_LISTING.md` and `docs/HEALTH_CONNECT_DECLARATION.md`.
- Re-run `python -m scripts.build_cdsco_fdc` when a new 26A notification is
  published; the 2024 list comes from Goa FDA's copy until CDSCO publishes a
  consolidated one.
