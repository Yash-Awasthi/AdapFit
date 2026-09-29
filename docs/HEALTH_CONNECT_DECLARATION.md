# Health Connect declaration (Google Play)

Draft answers for the Play Console "Health apps" declaration and the Health
Connect permissions form. Items in [brackets] are the owner's to complete.

## App and access

- App: AdapFit, package `com.adapfit.app`. Category: Health & Fitness.
- Access is **read only**; AdapFit writes nothing to Health Connect.
- Reading starts only when the user taps "Connect Health Connect" in Devices
  and grants types in the system sheet. It then reads the last 30 days once,
  and afterwards what changed since the last sync (at most hourly, when the
  app is opened). Background reads are not requested.
- Records deleted in Health Connect are deleted on our server at the next
  sync (changes API).
- Privacy policy: [PUBLIC URL of backend/app/legal/privacy-policy.md]. It
  names Health Connect, the purposes below, retention and erasure.

## Purpose of each type

Every type is used only to show the user their own data and to personalise
their own plan. None is sold, used for advertising, or shared with anyone the
user has not chosen. None is used to diagnose.

Every synced type appears in the user's daily summary on the Devices screen
("Last 7 days from Health Connect"). Some are used further:

| Permission | Shown and used |
|---|---|
| READ_STEPS | Daily steps; hourly profile for the rest-activity rhythm after 3 days; morning check-in |
| READ_SLEEP | Sleep hours; pre-fills the morning check-in's sleep |
| READ_HEART_RATE | Daily average heart rate |
| READ_RESTING_HEART_RATE | Morning check-in: resting heart rate against the user's own baseline in the recovery score |
| READ_HEART_RATE_VARIABILITY | Morning check-in: HRV against the user's own baseline in the recovery score |
| READ_WEIGHT | Daily weight |
| READ_BODY_FAT | Daily body fat |
| READ_BLOOD_GLUCOSE | Daily average; readings go into the diabetes log and its time-in-range summary |
| READ_EXERCISE | Daily exercise minutes |
| READ_ACTIVE_CALORIES_BURNED | Daily active calories; morning check-in |
| READ_DISTANCE | Daily distance |
| READ_OXYGEN_SATURATION | Daily SpO2 |
| READ_BLOOD_PRESSURE | Latest reading of the day |
| READ_BODY_TEMPERATURE | Latest temperature of the day |
| READ_NUTRITION | Daily calories from food apps |
| READ_MENSTRUATION | Period days |

## Data handling (Play Data safety form)

- Collected: health and fitness data above; name, email and date of birth
  for the account; app interactions only with analytics consent (off by
  default, never for under-18s).
- Encrypted in transit (HTTPS) and at rest (AES-256-GCM for feature data).
- Users can export everything (Settings, Export my data) and delete the
  account (Privacy, Delete account); erasure also reaches backups (restore
  replays erasures).
- Shared with third parties: AI features send the user's message and the
  records it needs to an AI provider (Google Gemini, Groq or TokenHarbor), only with the user's AI consent.
  Crash reports (if enabled) exclude request bodies, headers and query strings.

## Reviewer notes

- Test account: [EMAIL] / [PASSWORD] on the review build's server.
- To see Health Connect: open Devices, tap "Connect" on the Health Connect card, allow
  any types; Health Connect test data can be added with the Health Connect
  Toolbox.
