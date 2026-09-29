# AdapFit roadmap

AdapFit is a consumer wellness app for India: it tracks, explains and suggests safe next steps, and never diagnoses. This file is the plain summary; `todo.md` holds the working list, `plan.md` the history and `docs/FEATURE_STATUS.md` how each feature was checked.

Status: **MVP.** It runs end to end on a real phone against a free staging server. It is not production-ready.

## What works today

- Sign-up with per-purpose consent, sign-in, sign-out, account deletion and data export.
- Onboarding (goals, about you, devices, activity and sleep target), morning check-in and a recovery score.
- Adaptive workouts: generate, run with sets and a rest timer, finish, feedback.
- AI coach chat through free models, with safety screening in English, Hindi and Hinglish.
- Route recording, sleep sounds, Health Connect sync (including deletions reaching the server).
- Around 30 more screens (nutrition, sleep, mind, cycle, medication, calendar, emergency and others). Their server calls answer correctly on staging; most screens were opened but not used in depth.
- Staging on free Render, Neon and Sentry; a signed Android release build.

## Next: finish the MVP

- Walk the new onboarding on the phone, then run the Maestro flow (`mobile/e2e`) end to end.
- Try the camera heart rate with a real fingertip and the form checker with a person exercising; save heart-rate readings to Vital Signs.
- Check voice log, GPS distance, the Bluetooth strap and the two-account features (Family, Community, Forums) with real use.
- Check on the phone that a Health Connect record deleted there disappears from the server.

## Then: make it usable in India

- Hindi first: translate the core journey and add a language picker (the app is English only today).
- Layout polish pass on every screen.
- Firebase push for reminders and server events (needs a Firebase project).
- Server-side AI on Render (needs a key from a provider that accepts datacenter IPs); today the phone calls the model directly.
- Uptime monitor on `/health`.

## Before a public launch

- Legal: company details, Grievance Officer, filled-in terms and privacy policy, legal review of the third-party data sources.
- Who reviews community reports; Play target audience; store listing and Health Connect declaration answers (`docs/STORE_LISTING.md`, `docs/HEALTH_CONNECT_DECLARATION.md`).
- Rotate every token that was shared in chat; move the AI key out of the app.
- Third-party penetration test, closed beta, support channel, incident and breach procedure.
- Real screens for stroke rehab, chronic disease, hospital at home and wound assessment, designed with a clinician; a coach marketplace only with verified practitioners.
- iOS build with HealthKit.

## Deliberately not done

- Paid tiers and Play Billing: every feature is free for now.
- An Expo upgrade: SDK 56 does not clear the remaining advisory and needs React Native 0.85 (`docs/SECURITY.md`).
