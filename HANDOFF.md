# Handoff: core logic fixes (branch `fix/core-logic`)

## What changed

The check-in to decision to workout loop was giving wrong answers and parts of
it did not persist on Postgres. All of the following are fixed and covered by
`backend/tests/test_core_logic.py`.

**Decision and recovery**
- Soreness and energy were read backwards: the app sends 10 for fresh and
  energized, the decision treated 10 as "high soreness". A fresh user got
  RECOVER and a wrecked one got REDUCE.
- Signals already inside the recovery score (HRV, sleep, ratings, load) were
  applied again as downgrades. A red flag now only stops a full TRAIN day.
- Readiness state and the decision used different bands (85/65/45 vs 75/55/30).
  `RecoveryEngine.readiness_for` now uses the decision bands.
- Sleep target never drops below 7h, so a habitual short sleeper is not scored
  against their own deficit.
- HRV domain on `/recovery-logs/today` uses the engine's mapping
  (`RecoveryEngine.hrv_score_from_z`).
- ACWR exponential averages are bias-corrected; steady training reads about 1.0
  from day 28 instead of about 1.16.
- A second check-in on the same day replaces the first in the memory store, as
  Postgres already did.

**Workouts**
- `POST /workouts` sizes the session from today's decision, so pain, illness and
  low recovery give a mobility session. A REST day is titled "Rest day".
- The rule-based plan rotated nothing: every plan was three chest exercises and
  a row. It now rotates legs, push, pull and core, one exercise per muscle,
  changes per date and scales the exercise count with the requested duration.
- Sore body areas ("legs", "arms", "back", ...) exclude their muscles.
- Completing the same workout twice no longer logs its load twice. The app was
  doing exactly that (active screen and completion screen both sent it).
- `target_date` is stored with each workout.
- `suggest_progression` follows its documented rules and respects limitations;
  adaptive selection spreads muscle groups.

**API-wide**
- `IdentityMiddleware` rewrote literal routes such as `POST /passport/create`
  into `/passport/<user id>`, giving 405. Literal routes now win.
- `min(max(x), 10)` crashed chronic symptom logging and vision strain logging.
- Vision health score read `strain_level` from the wrong log list.

**Postgres**
- `012_recovery_safety_flags.sql`: `pain_flagged`, `illness_flagged`,
  `resting_hr_delta` on `daily_recovery_logs` (they were silently dropped, so
  the pain override never fired).
- `013_agent_memory_extra.sql`: `extra` JSONB on `agent_memory`. Mood logs,
  thought records and questionnaires returned 500 and were lost.
- `014_workout_details.sql`: warm-up, cool-down, rest, image and notes for
  workouts.
- `_upsert` no longer emits an empty `DO UPDATE SET` when only the key is sent.
- `001` and `006` use built-in `gen_random_uuid()` instead of `uuid-ossp`, so a
  stock Postgres needs no contrib extensions. Databases that already applied
  them are unaffected (the runner tracks file names).
- `verify_postgres.py` and `reread_postgres.py` no longer crash without `.env`
  and do not override variables already set.

**Mobile**
- Check-in: sore-area chips plus pain and illness toggles.
- Workout finish sends the session once, from the completion screen, with RPE
  defaulting to the average of the logged sets.
- Rest timer uses the prescribed `rest_seconds`.

## What to do on Windows

1. Get the branch:
   ```powershell
   git fetch origin
   git checkout fix/core-logic
   ```
2. Apply the three new migrations to the local database. `backend/.env` must
   hold `DATABASE_URL`, and the same `DATA_ENCRYPTION_KEYS` the database was
   written with (a different key makes startup refuse to load sealed rows).
   ```powershell
   cd backend
   python -m scripts.apply_migrations --list
   python -m scripts.apply_migrations
   python -m scripts.verify_postgres
   ```
3. Run the backend tests:
   ```powershell
   python -m pytest tests -q -p no:warnings
   ```
4. Run the app on a device or emulator and walk the loop: check-in (try the
   pain toggle and a sore area), home decision, generate workout, finish it,
   complete screen. This has not been run on a device yet.
   ```powershell
   cd ..\mobile
   npm ci
   npx tsc --noEmit
   npx expo start
   ```

## Verified so far (Linux)

- 1105 backend tests pass (`test_lesion_measure.py` skipped there only because
  libGL was missing on that machine).
- Every route hit as a signed-in user on both the memory store and Postgres 16:
  no 5xx left except the optional pose-estimation and text-to-speech engines
  (503 until their packages are installed).
- `verify_postgres` passes; a 30-day check-in and workout loop on Postgres gave
  30 distinct plans, a REST plus mobility day on pain, sore legs left out of the
  next plan, and no duplicate load on repeat completion.
- Mobile `tsc` and the `.check.ts` scripts pass.

## Still open

- Completed sessions are dated when the server receives them. A workout queued
  offline and synced days later lands on the sync day in the load history.
- When an LLM key is set, the generated plan is not checked against the
  requested duration.
- Not run on a phone or emulator.
- The unused-import lint backlog (about 280 entries) is untouched; CI only
  checks syntax and undefined names.
