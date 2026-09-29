# Feature status

What works and how it was checked, as of 2026-09-29. Three kinds of evidence, strongest first:

1. **Phone**: used by hand on a Realme RMX5061 (Android 16) with the signed release build against the staging server.
2. **Server sweep**: every read endpoint the API exposes (437) was called on the live staging server with a signed-in account. 410 answered normally. The rest are expected refusals (admin routes for a normal user, the metrics token) or need a real record id. Two real faults turned up and were fixed (see the end).
3. **Backend tests**: 1,088 automated tests cover the write paths (logging, saving, consent, deletion, safety screening).

A feature marked "server only" has a working server side and tests, but its screen has not been opened on the phone yet.

## Checked on the phone

| Feature | How it was checked | Result |
| --- | --- | --- |
| Sign-up, consent, onboarding | Created an account, chose consent switches, went through onboarding | Works. Onboarding was then shortened (each question asked once); the new version is installed but not walked yet |
| Sign-out, sign-in | Fresh installs and relaunches | Works |
| Home | Recovery score, today's plan card, metric tiles | Works. Score bands now match the workout's readiness wording |
| Morning check-in | Submitted sleep, soreness, energy, stress | Works; the score and plan update at once |
| Workouts | Generated a workout, started it, logged a set, rest timer, finished, submitted feedback | Works, including Start workout from Home |
| Coach (AI) | Asked for a short dumbbell session | Works: the phone calls the free model and the server screens the reply |
| Record a route | Started and finished a recording indoors | Works. Real distance needs a walk outdoors; a route under 50 m is not saved |
| Sleep sounds | Listened for 30 seconds, stopped, read the summary | Works. Android pauses listening if the screen locks, so the screen stays on |
| Health Connect | Granted access, synced | Works: 1 steps record (6 steps) reached the server |
| Privacy and consent | Turned AI on in Privacy and saved | Works; the server shows the change |
| Settings, More menu, Devices | Opened and scrolled | Works |

## Server only (screens not yet opened on the phone)

Dashboard, Trends, Stats, Exercises, Periodization, Achievements, Habits, Recovery, Mind (mood, questionnaires), Wellness (breathing), Everyday wellbeing, Sleep logging, Health (conditions, medications), Cycle, Pregnancy, Nutrition and Hydration, Recipes, Body measurements and goals, Vital signs, HRV, Medication, Calendar, Emergency contacts and medical ID, Conditions and Recovery, Care and Safety, Accessibility, Export data.

Every read call these screens make returned normally on staging. Their writes are covered by the backend tests.

## Needs hardware or another person

| Feature | Why it is unchecked |
| --- | --- |
| Camera heart rate and fatigue (Health Hub) | Needs a person in front of the camera with the flash |
| Form checker | Needs a camera and someone exercising |
| Bluetooth heart-rate strap | Needs a strap |
| Voice log | Needs the microphone and a spoken workout |
| GPS distance | Needs an outdoor walk or run |
| Family, Community, Forums | Need a second account; reporting and blocking are covered by tests |
| Deleting a Health Connect record | The server side works (import two records, delete one, one left). Detecting a deletion on the phone needs a record the owner can delete |

## Not built as screens

Stroke rehab, chronic disease management, hospital at home, wound assessment, peer support, vaccination records and the accessible-workout API exist only on the server. The app is English only: the translation files hold English, Spanish and French but no screen uses them yet.

## Faults the sweep found (fixed)

- `/modules-health/health` answered 500 because its declared return type rejected its own response.
- `/voice/prompts` was a GET that expected a request body, which a phone cannot send; it is now a POST. A test now fails if any GET route expects a body.

## MVP notes

This is an MVP, not a production release. Known gaps the owner chose to leave:

- The form checker and camera heart rate have been opened on the phone but not used properly. The form checker now uses the front camera by default with a switch, and a 5-second countdown before each capture. The heart-rate screen explains why it uses the camera, and no longer calls an uncovered lens a good signal. Neither has been checked against a person exercising or a real fingertip, and heart-rate readings are not saved to Vital Signs.
- The app is English only.
- Health Connect deletion on the phone, Bluetooth strap, voice log, GPS distance and the two-account features (Family, Community, Forums) were not exercised.
- Firebase push, legal placeholders and the uptime monitor wait on the owner (see todo.md).
