# Product scope

Decided 2026-09-28. Every later phase in `todo.md` works inside these limits.

## Positioning

AdapFit is a consumer wellness app sold by subscription, launching in India
first. Every feature ships. None of them diagnoses.

The app measures, tracks and explains the user's own data against their own
baseline, and suggests safe next steps. When something needs a professional,
it says which kind and how soon, and does not guess at a cause. That line keeps
the product outside medical device regulation (CDSCO Medical Device Rules 2017
in India, FDA SaMD and EU MDR if it later expands) while leaving every feature
in place.

Personalisation is the product: advice refers to the user's name, goal,
history and baseline, never to an average user.

## Rules every feature follows

1. **No diagnosis.** Never state or imply that the user has a condition, and
   never attach a probability to a disease.
2. **No medication changes.** Never tell a user to start, stop or change a
   dose. Interaction checks say what to ask the prescriber.
3. **Measured or missing.** A value is either measured, entered by the user,
   or reported as missing. Nothing is defaulted or invented.
4. **Safe next step.** Every alert ends with something the user can do now,
   and names the kind of professional and the timeframe when one is needed.
5. **Emergencies are not generated.** Red-flag messages (chest pain, stroke
   signs, severe bleeding, self-harm) get a fixed, reviewed reply with Indian
   emergency numbers before any model is called.

Rules 1, 2 and 5 are enforced in `backend/app/services/safety_policy.py`,
which every chat path uses. Rule 3 is guarded by
`tests/test_no_random_measurements.py`.

## Regulatory frame for India

| Area | Rule | What it means here |
|---|---|---|
| Medical devices | Medical Device Rules 2017 (software included since 2022) | Stay wellness: no diagnostic or treatment claims in app, store listing or marketing |
| Personal data | Digital Personal Data Protection Act 2023 and Rules 2025 | Explicit consent per purpose, consent withdrawal, erasure, grievance officer, breach notice to the Data Protection Board |
| Telemedicine | Telemedicine Practice Guidelines 2020 | Consultations only with registered practitioners; the app can link out, not practise |
| Health records | ABDM / ABHA (voluntary) | Optional later: link an ABHA ID to import and share records |
| Payments | Play Billing and App Store rules, RBI e-mandate rules for recurring UPI and cards | Subscriptions through store billing; any web checkout needs e-mandate compliance |

## Feature inventory

**Core wellness.** Home, dashboard, workout, workouts, exercises, periodization,
sleep, sleep tracker, circadian, nutrition, recipes, achievements, gamification,
stats, trends, analytics, coach, chat, community, forums, social, content
feed, wellness, longevity, respiratory (breathing training), posture, ambient,
family, devices, health calendar, health hub, data export, settings, personal
info, accessibility settings.

**Health tracking.** Logs and charts what the user measures, compared with
their own baseline, with safe next steps: vital signs, cycle, fertility,
pregnancy, diabetes, medication, chronic pain, addiction recovery, mental
health, voice health, remote monitoring, health savings, health equity,
precision nutrition, emergency (medical ID).

**Clinical-adjacent.** Real implementations that screen and refer, never
diagnose: cardiac rehab, skin health, medical imaging (ABCDE), genomics,
telemedicine (connects to registered practitioners). These carry the most
risk and get the strictest review in the phase that rebuilds them.
