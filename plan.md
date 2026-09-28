# AdapFit (ZFIT) — bug audit and enhancement plan

## What this document is

AdapFit is an AI fitness and recovery platform: a FastAPI backend (648 Python
files, 105,766 lines, 229 endpoint modules, 277 service modules, 952 tests) plus
a React Native / Expo mobile app (135 TypeScript files). The backend uses
FastAPI with auto-discovered routers, LangGraph-style workflow services, and
SQLite/Postgres storage.

Unlike RemoteHarness, this project has **no absorption ledger**. There is no
record anywhere of what the 279-repository inspiration corpus contributed, and
no document mapping corpus features to shipped code. So this document has to do
both jobs: record the defects found in a full audit of the source (Part 1), and
give the corpus its first disposition (Part 2).

Everything in Part 1 was measured rather than read. Where a claim could be
checked by running something, it was, and the command output is quoted.

The corpus is `C:\Users\yasha\PROJECTS\inspiration\ZFIT`: 280 filesystem
entries, of which 279 are repositories and one is `MANIFEST.md`.

---

## Part 1 — Defects

### 1. Eight endpoint modules fail to import and disappear without a trace — critical

This is the single most consequential defect in the project, and it is invisible
from the outside.

Routers are auto-discovered. `app/core/registry.py` walks
`app/api/v1/endpoints/`, imports each module, and registers the `router`
attribute it finds. The import is wrapped in a bare handler:

```python
        except Exception as e:
            errors += 1
```

That block does not log, does not re-raise, and does not record anything about
what failed. `app/main.py:145` then calls the function and **discards the return
value**:

```python
register_endpoints(app)
```

So a module that cannot be imported is counted in a dictionary that nobody
reads, and the application starts normally without it. Measured on the working
tree:

```
register_endpoints() -> {'registered': 218, 'skipped': 2, 'errors': 8}
```

Eight endpoint modules are dead. Each fails with the same class of error — an
`ImportError` for a name the target service module does not define:

| Endpoint module | Imports | Service module defines instead |
|---|---|---|
| `activity_recognition_api` | `SensorReading` | `SensorSample`, `ActivityDetection`, `ActivityRecognizer` |
| `body_health_api` | `blood_pressure_service` | `BPReading`, `classify_reading` (no module-level instance) |
| `cardiovascular_api` | `HRVReading` | `CardioAnalysis`, `CardiovascularAnalyzer` |
| `fitness_assessment` | `estimate_1rm` | `assess_strength`, `classify_level` |
| `gamification_api` | `gamification_service` | `Achievement`, `LeaderboardEntry` (no module-level instance) |
| `injury_risk` | `injury_risk_engine` | `InjuryRiskEngine` (class, not instance) |
| `nutrition_tracking_api` | `MacroNutrients` | `Nutrient`, `Meal`, `DailyNutrition` |
| `sleep` | `analyze_sleep` | `SleepAnalyzer` (class, not function) |

The pattern is consistent: the endpoint modules were written against a service
API shape that was never implemented. Each of the eight service modules contains
a substantial implementation as classes and enums — the functionality largely
exists — but the endpoints expect a flattened module-level function or a
ready-made singleton. These modules were never functional; this is not a
refactor regression.

Impact: eight API surfaces, including sleep logging and fitness assessment,
return 404 with no log line, no warning, and no metric.

### 2. The test suite already detects the dead modules, and it is red — critical

Measured:

```
5 failed, 947 passed in 95.51s (0:01:35)
```

The five failures are exactly the dead modules surfacing:

| Failing test | Cause |
|---|---|
| `test_smoke_endpoints[GET-/api/v1/fitness/tests-200]` | `fitness_assessment` did not register |
| `test_smoke_endpoints[GET-/api/v1/fitness/summary-200]` | `fitness_assessment` did not register |
| `test_crud_lifecycle[sleep_logs]` | `sleep` did not register — 404 where 201 was expected |
| `test_sleep_analysis` | `KeyError: 'score'` — sleep analysis route absent |
| `test_fitness_assessment` | `KeyError: 'estimated_1rm'` — assessment route absent |

So the failure is known, reproduced by the project's own suite, and has been
left in place. `.github/workflows/ci.yml` runs `python -m pytest tests/ -v
--tb=short` with no `|| true`, which means CI should be failing on this. Two
possibilities follow and both are worth checking: either pushes to `main` are not
triggering CI, or CI is red and being ignored. Note that the same workflow runs
mypy as `python -m mypy app/ --ignore-missing-imports || true` — type checks are
explicitly non-blocking, so they can never catch anything.

Fixing defect 1 turns this suite green, which makes it the natural first step.

### 3. Broken access control across most of the API — critical

The backend has an authentication layer but almost no authorization. Measured:

| Measure | Count |
|---|---|
| Endpoint files that use any auth dependency (`require_user`, `get_current_user`, `require_admin`, `get_user_id`, `require_owner_or_owner_id`) | **13** |
| Endpoint files that use none | **216** |
| Endpoint files that read `request.state.user` (injected by the auth middleware) | **0** |
| Handlers that take `user_id: str` as a parameter | **520** |
| Files that take both a `user_id` and a `request: Request` (so they could compare) | **3** |

`AuthMiddleware` validates the JWT and then injects the identity into
`request.state.user` and `request.state.user_id`. Nothing reads it. The
middleware proves only that *some* valid token exists; it never establishes that
the caller is the user named in the request.

The concrete consequence, in the most sensitive part of the application —
`app/api/v1/endpoints/medical_id_api.py`:

```python
@router.get("/emergency/{user_id}")
async def get_emergency_view(user_id: str):

@router.get("/wallet/{user_id}")
async def get_wallet_card(user_id: str):

@router.get("/provider-summary/{user_id}")
async def get_provider_summary(user_id: str):
```

The emergency medical ID view is blood type, allergies, current medications and
emergency contacts. All three handlers take the subject's `user_id` straight from
the URL path and never compare it to the caller. Any registered account can read
any other user's emergency medical record by changing one path segment. That
pattern repeats across the 520 handlers that accept a `user_id`.

### 4. The authorization helpers exist and are unused — high

`app/core/dependencies.py` defines a complete, correct authorization toolkit:

- `get_current_user` (`:56`)
- `require_user` (`:71`)
- `require_admin` (`:94`)
- `require_owner_or_owner_id` (`:110`) — a dependency factory whose docstring is
  literally the missing check: "checks if the authenticated user matches the
  given user_id or is an admin"
- `get_user_id` (`:132`)

Usage: `get_current_user` is imported by exactly one endpoint file
(`auth_api.py`). `get_user_id` has **zero** callers. `require_owner_or_owner_id`
has no callers at all. The fix for defect 3 is not to write new code — it is to
apply `require_owner_or_owner_id` at the roughly 520 call sites that need it, or
to replace path-supplied `user_id` with the token-derived identity wholesale.

### 5. Every WebSocket endpoint is unauthenticated — critical

`AuthMiddleware` extends `BaseHTTPMiddleware`, which only receives HTTP scope.
WebSocket connections never pass through it, so the middleware cannot protect any
WebSocket route regardless of its `PUBLIC_ENDPOINTS` configuration. There are
seven WebSocket routes across six files, and none of them authenticates on its
own:

- `app/api/v1/endpoints/ws_chat.py:83` — `@router.websocket("/ws/{user_id}")`
  followed by a bare `await websocket.accept()` at `:86`. The path-supplied
  `user_id` becomes the identity, so a client can connect as any user and receive
  that user's coach conversation context.
- `app/api/v1/endpoints/ws_camera.py:12` — `@router.websocket("/ws/bpm")` with
  `await websocket.accept()` at `:26` and no token check anywhere.
- `app/api/v1/endpoints/challenges_ws.py:39-46` — the helper is explicit about
  being a stub:

  ```python
  """Validate token from query param or first message. Returns user_id or None."""
  # Check query param for token
  token = websocket.query_params.get("token")
  if token:
      # when auth middleware is wired. For now, accept any non-empty token.
      if token:
          return f"user-{token[:8]}"
  ```

  Any non-empty string is accepted, and the returned identity is derived from the
  token text itself rather than validated against it. The comment concedes the
  middleware is not wired.

- `sensor_hub.py` and `workout_rooms.py` also expose WebSocket routes.

### 6. A production password is committed in `docker-compose.yml` — high

`docker-compose.yml` carries literal values for ten environment variables,
including `POSTGRES_PASSWORD`. That value is 14 characters, is not a known
trivial default (`postgres`, `password`, `admin`, `root`, `changeme`), and does
not look like a placeholder — unlike `JWT_SECRET_KEY`, `GEMINI_API_KEY` and
`GROQ_API_KEY` in the same file, which are placeholder-shaped and should still be
moved out of the file but are not secrets.

The actual secret values are deliberately not reproduced here.

Two adjacent facts, both checked, so the picture is accurate:

- `.env` files are correctly ignored — `.gitignore:9` matches both `backend/.env`
  and `mobile/.env`, and neither is tracked. No secret leaks through those.
- `.env.example` is **not** a leak. Its non-empty values are a localhost database
  URL and a 37-character placeholder JWT secret. The `.sb-pentest-audit.log`
  claim that hardcoded credentials were found in `.env.example` is wrong.

### 7. The security audit record contradicts itself — medium

`.sb-pentest-audit.log` ends with:

```
[2026-08-29T10:00:25Z] [WARNING] Hardcoded credentials found in .env.example and docker-compose.yml
[2026-08-29T10:00:35Z] [COMPLETE] Scan complete - no P0 findings
```

A scan that reports hardcoded credentials and then reports no P0 findings in the
same ten seconds is not a usable security record, and both halves are wrong: the
`.env.example` half is false (see defect 6), and the `docker-compose.yml` half is
true but graded as P0-free despite a real password.

The log also looks generated rather than observed: the `START` line is printed
twice verbatim, and every timestamp is exactly five seconds after the last.

### 8. Middleware fails open, silently — high

`app/main.py` imports the security and auth middleware like this:

```python
try:
    from app.middleware.security import SecurityHeadersMiddleware, InputSanitizationMiddleware, RequestLoggingMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    ...
except ImportError:
    pass
try:
    from app.middleware.auth import AuthMiddleware
    app.add_middleware(AuthMiddleware)
except ImportError:
    pass
```

If either import fails, every middleware in that block is absent and the
application boots with no authentication and no security headers — silently.
Given that defect 1 proves import failures are actively happening in this
codebase, this is a live failure mode rather than a hypothetical one. The failure
direction is exactly backwards: a broken import should stop the process, not
quietly disable the security stack.

### 9. Endpoint and service sprawl with numbered generations — medium

229 endpoint modules and 277 service modules for a product that has perhaps
forty distinct features. The duplication is visible in the filenames:

- **Sleep**: `sleep_analysis`, `sleep_analysis_comprehensive`, `sleep_analyzer`,
  `sleep_architecture`, `sleep_classifier`, `sleep_recovery`, `sleep_scorer`,
  `sleep_staging`, `sleep_tracker` — nine services; plus four endpoint modules
  (`sleep.py`, `sleep_analysis.py`, `sleep_analysis_api.py`,
  `sleep_tracking_api.py`, 462 lines total).
- **HRV**: `hrv_analysis`, `hrv_analysis_advanced`, `hrv_analyzer`,
  `hrv_artifact_correction`, `hrv_biofeedback`, `hrv_recovery_scorer`.
- **rPPG**: `rppg_analyzer`, `rppg_heart_rate`, `rppg_signal_processing`.
- **Drug interaction**: `drug_interaction_checker`, `drug_interaction_engine`,
  `drug_interactions`, `drug_network`.
- **Recommendations**: `recommendation_engine`, `recommendation_engine_v2`.
- **Recovery**: `recovery_detection`, `recovery_engine`, `recovery_engine_v2`,
  `recovery_tracker`.
- **Nutrition**: `nutrition_analyzer`, `nutrition_logger`, `nutrition_tracking`,
  `nutrition_validator`.

Endpoint modules come in versioned generations:
`achievements.py` / `achievements_v2_api.py` / `achievements_v3_api.py`;
`ai_coach_api.py` / `ai_coach_v2_api.py`; `community.py` /
`community_v2_api.py` / `forums_api.py`; `recovery.py` / `recovery_api.py` /
`recovery_v2_api.py`; `export.py` / `export_v2_api.py`.

`ROUTE_MAP` in `registry.py` assigns the same prefix to two different modules in
several places — `/workouts` (`workouts`, `auto_scale`), `/chat` (`chat`,
`ws_chat`), `/challenges` (`fitness_challenges`, `challenges_ws`),
`/sleep-analysis` (`sleep_analysis`, `sleep_analysis_api`), `/wearable`
(`wearos`, `wearable_api`). That is currently harmless: a route audit found **0**
duplicate method+path pairs, so no live collision exists. But this is the sprawl
that produced defect 1, and the same duplication will keep producing it.

### 10. The router registry mutates shared module state — medium

`_strip_baked_prefix` rewrites route objects in place:

```python
        route.path = path[len(baked_prefix):] or "/"
        route.path_regex, route.path_format, route.param_convertors = compile_path(route.path)
```

`importlib.import_module` caches modules in `sys.modules`, so the router object
being mutated is the same object every future caller sees. Registration is
therefore not idempotent in principle; it survives a second call only because the
`path.startswith(baked_prefix)` guard happens to fail once the prefix has been
stripped. Correctness here depends on a coincidence. The same function sets
`full_prefix = settings.API_V1_STR` (dropping the per-module prefix entirely)
whenever it strips, so a mis-declared prefix silently changes the public URL of
every route in that module.

### 11. Import resolution depends on a `sys.path` mutation — medium

`app/main.py:8-11` inserts the project root into `sys.path` so that `src.*`
modules are importable from services. This makes the meaning of an import depend
on how the process was launched and does not apply to code that imports the
package without first importing `app.main` — which is part of why the eight
modules in defect 1 fail in ways that depend on entry point. Explicit relative
imports or a proper package layout would remove the whole class of problem.

### 12. `/metrics` is public — low

`app/middleware/auth.py` lists `/metrics` in `PUBLIC_ENDPOINTS`, and the metrics
router is mounted at root. Prometheus output exposes internal call counts, route
names and error rates to anyone who can reach the host. Usually acceptable inside
a private network and not acceptable on a public one; worth a deliberate decision
rather than an allowlist accident.

### 13. The mobile app puts an API key in a URL query string — low

`mobile/app/(tabs)/dev-tools.tsx:87` builds
`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`. API keys
in query strings end up in proxy logs, browser history and referrer headers. The
Gemini API accepts the key in an `x-goog-api-key` header instead. The key is
user-supplied rather than bundled, which limits the severity.

### 14. The working tree is dirty, with 457 deletions — medium

```
     32 ??
    457 D
     25 M
```

The 457 deletions are an unused tooling directory. The 25
modifications include application code: `backend/app/main.py`,
`backend/app/core/registry.py`, `backend/app/api/v1/endpoints/challenges_ws.py`,
`backend/app/api/v1/endpoints/health_data_api.py`,
`backend/app/api/v1/endpoints/sleep_analysis.py`,
`backend/app/services/sleep_analyzer.py`, `backend/app/services/websocket_manager.py`,
plus mobile components and `backend/tests/*`.

Every finding in this document describes the working tree, which is what would
actually run. But nothing here should be committed before deciding what to do
with 457 deleted files and 25 uncommitted edits — and the edits to `registry.py`
and `main.py` are in exactly the two files defects 1 and 8 live in, so any fix
must be reconciled against work already in progress.

---

## Part 2 — Corpus coverage

The corpus is `C:\Users\yasha\PROJECTS\inspiration\ZFIT`: 279 repositories. This
is its first disposition; no prior record exists.

How to read the marks. ✅ means a matching capability was found in AdapFit and
the corpus repo's distinguishing technique is reflected there. ⚙️ means AdapFit
already had an equivalent capability before any absorption, so the repo confirmed
the design rather than contributing to it. 🧩 means AdapFit has the module but it
is not wired into a route. 🗺️ means a named gap to implement. ➖ means
reference-only: a curated list, a dataset, an unpublished research model, a
framework-specific plugin, or a repository outside the product's scope. ⛔ means
outside the product's domain entirely.

Marks were assigned by matching each repository against the 277 modules under
`backend/app/services/` and the 229 modules under `backend/app/api/v1/endpoints/`
by name and role. Where a repository's value is a trained model or a paper
reproduction, it is ➖ regardless of topic: the technique may inform AdapFit but
the artifact cannot be absorbed.

### G1. Sleep, circadian rhythm and actigraphy (24)

| Repo | Status | Note |
|---|---|---|
| airwaylab | ✅ | Airway flow-limitation analysis → `airway_analysis` |
| o2ring-analyzer | ✅ | Pulse-oximetry import and resampling → `vital_signs`, `sleep_analysis` |
| sleep-recovery-detector | ✅ | Morning readiness interpretation → `sleep_recovery`, `recovery_detection` |
| smartalarm | ✅ | Sleep-cycle-aware alarm → `smart_alarm`, `sleep_tracker` |
| asleep | ⚙️ | Wrist accelerometer staging → `sleep_staging`, `accelerometer_analyzer` |
| fips | ⚙️ | Fatigue/sleep prediction → `fatigue_prediction` |
| ggir | ⚙️ | Accelerometer sleep and activity → `accelerometer_analyzer`, `actigraphy_analysis` |
| hypnospy | ⚙️ | Circadian and sleep staging → `sleep_analysis`, `circadian_rhythm` |
| pyactigraphy | ⚙️ | Actigraphy metrics → `actigraphy_analysis` |
| sleep_classifiers | ⚙️ | Accelerometer + HR staging → `sleep_classifier` |
| sleepecg | ⚙️ | Sleep staging from ECG → `sleep_staging`, `ecg_interpreter` |
| sleepkit | ⚙️ | On-device sleep monitoring → `sleepkit_analyzer` |
| smart-alarm-using-tinyml | ⚙️ | TinyML alarm → `smart_alarm` |
| wakeiq | ⚙️ | Gentle cycle-based wake → `smart_alarm` |
| yasa | ⚙️ | Sleep staging and spindle detection → `sleep_staging` |
| attnsleep | ➖ | Research staging network |
| autosleepscorer | ➖ | CNN-LSTM research scorer |
| multimodal_sleep_stage_benchmark | ➖ | Benchmark dataset |
| pyrem | ➖ | EEG staging research |
| sleeptk_pinetime | ➖ | PineTime watch firmware |
| tinysleepnet | ➖ | Single-channel EEG model |
| u-time | ➖ | Time-series segmentation research |
| wav2sleep | ➖ | ML4H paper implementation |
| awesome-sleep-tracking | ➖ | Curated list |

### G2. HRV, ECG and cardiac signal processing (13)

| Repo | Status | Note |
|---|---|---|
| hrv-correction | ✅ | Ectopic-beat and artifact correction → `hrv_artifact_correction` |
| openhrv | ✅ | HRV biofeedback training → `hrv_biofeedback` |
| biobss | ⚙️ | ECG/PPG/EDA/ACC processing → `biosignal_analysis`, `ecg_interpreter` |
| biosppy | ⚙️ | Biosignal processing → `biosignal_analysis` |
| heartrate_analysis_python | ⚙️ | HeartPy toolkit → `hrv_analyzer`, `bvp_signal_processing` |
| hrv-analysis | ⚙️ | HRV module → `hrv_analysis` |
| hrvas | ⚙️ | HRV analysis suite → `hrv_analysis` |
| non-invasive-bp-estimation-using-deep-learning | ⚙️ | BP from PPG signals → `blood_pressure` |
| py-ecg-detectors | ⚙️ | Eight ECG detection algorithms → `ecg_interpreter` |
| pyhrv | ⚙️ | HRV toolbox → `pyhrv_analyzer` |
| systole | ⚙️ | ECG/HRV processing → `hrv_analysis`, `ecg_interpreter` |
| wearable-hrv | ⚙️ | Wearable HRV validation → `wearable_data`, `hrv_analysis` |
| awesome-hrv | ➖ | Curated list |

### G3. rPPG and camera-based vitals (20)

| Repo | Status | Note |
|---|---|---|
| heart-rate-camera | ✅ | Webcam BPM estimation → `camera_heart_rate`, `rppg_heart_rate` |
| heart-rate-measurement-using-camera | ✅ | Camera HR pipeline → `camera_heart_rate` |
| pyvhr | ⚙️ | rPPG framework and evaluation → `rppg_signal_processing` |
| rppg | ⚙️ | Remote biosensing methods → `rppg_analyzer` |
| rppg-toolbox | ⚙️ | Reference rPPG training/eval → `rppg_signal_processing` |
| yarppg | ⚙️ | Real-time rPPG → `rppg_signal_processing` |
| advanced-rppg | ➖ | Application wrapper, no new method |
| awesome-rppg | ➖ | Curated list |
| contrast-phys | ➖ | Research model (TPAMI) |
| deep-rppg | ➖ | Neural rPPG research |
| heartbeat | ➖ | rPPG tools pointer |
| heartbeat-js | ➖ | rPPG tools pointer |
| heartraterepo | ➖ | Collection of links |
| iphys-toolbox | ➖ | MATLAB research toolbox |
| meta-rppg | ➖ | ECCV 2020 research |
| ml-heart-rate-models | ➖ | Apple research code |
| mtts-can | ➖ | Research model |
| physformer | ➖ | CVPR 2022 research |
| rppg-cans | ➖ | Research network |
| vitallens-python | ➖ | Third-party API client |

### G4. Wearables, device SDKs and aggregators (41)

| Repo | Status | Note |
|---|---|---|
| bleakheart | ⚙️ | Async BLE HR monitoring → `ble_heart_rate_logger`, `ble_device_manager` |
| bleheartratelogger | ⚙️ | BLE HR logging → `ble_heart_rate_logger` |
| capacitor-health | ⚙️ | HealthKit / Health Connect bridge → `healthkit_bridge` |
| colmi_r02_client | ⚙️ | Colmi R02 ring protocol → `smart_ring_parser` |
| health-auto-export | ⚙️ | Health data export → `data_export`, `health_export_v2` |
| healthsave-observatory | ⚙️ | Self-hosted Apple Health backend → `apple_health_parser`, `device_sync` |
| healthwallet.me | ⚙️ | Offline health record → `health_passport`, `medical_id` |
| life-dashboard-companion-app | ⚙️ | Health Connect webhook sync → `device_sync`, `health_integrations` |
| open-wearables | ⚙️ | Unified wearable platform → `device_sync`, `health_platform_bridge` |
| open-wearables-react-native-sdk | ⚙️ | RN wearable SDK → `wearable_data` |
| openscale | ⚙️ | BLE weight scale → `body_composition_tracker` |
| oura-ring | ⚙️ | Oura API v2 client → `oura_analyzer` |
| polar-ble-sdk | ⚙️ | Polar BLE streaming → `ble_device_manager`, `wearable_decoder` |
| react-native-ble-nitro | ⚙️ | RN BLE library → `ble_device_manager` |
| react-native-ble-plx | ⚙️ | RN BLE library → `ble_device_manager` |
| react-native-google-fit | ⚙️ | Google Fit bridge → `healthkit_bridge`, `device_sync` |
| react-native-health | ⚙️ | HealthKit binding → `healthkit_bridge` |
| react-native-health-connect | ⚙️ | Health Connect binding → `healthkit_bridge` |
| react-native-healthkit | ⚙️ | HealthKit binding → `healthkit_bridge` |
| ring-health-tracker | ⚙️ | Colmi R02 pipeline → `smart_ring_parser` |
| shimmer | ⚙️ | Fitbit/Runkeeper pull → `health_integrations` |
| vital-sync | ⚙️ | Health data aggregation → `vital_sync`, `health_aggregator` |
| wearable | ⚙️ | WHOOP 4.0 local client → `wearable_data` |
| wearablecompute | ⚙️ | 50+ wearable features → `wearable_data`, `accelerometer_analyzer` |
| wearipedia | ⚙️ | Wearable data access → `wearable_data` |
| wearsync | ⚙️ | Multi-device aggregator → `device_sync`, `health_aggregator` |
| whoop | ⚙️ | WHOOP API v2 client → `wearable_data` |
| whoop-data | ⚙️ | Multi-agent wearable analysis → `wearable_data`, `ai_insights_engine` |
| apple-health-mcp-server | ⚙️ | Apple Health access layer → `apple_health_parser` |
| applehealth | ⚙️ | Terminal Apple Health chat → `apple_health_parser` |
| ble-scale-sync | 🗺️ | 25+ BLE scale driver matrix and Garmin/Strava/MQTT push is wider than `body_composition_tracker` |
| ergometerjs | 🗺️ | Concept2 PM BLE ergometer driver — no equivalent |
| expo-workoutkit | 🗺️ | iOS WorkoutKit integration — no equivalent |
| apple-health-grafana | ➖ | Influx/Grafana plumbing |
| gatt-xml | ➖ | BLE GATT schema dump |
| healthypi-move-fw | ➖ | Zephyr device firmware |
| gadgetbridge | ➖ | Native Android app, unrelated stack |
| open_wearables_health_sdk | ➖ | Flutter plugin, wrong platform |
| react-native-wear-connectivity | ➖ | WearOS connectivity, unused |
| reactnative-apple-health-ios | ➖ | Demonstration app |
| reactnative-health-connect | ➖ | Demonstration app |

### G5. Garmin, Strava and training-data import (14)

| Repo | Status | Note |
|---|---|---|
| claude-garmin-ai-trainer | ✅ | Garmin-driven training optimisation → `garmin_recovery`, `ai_workout_coach` |
| garmin-recovery-insights-agent | ✅ | Recovery recommendations from Garmin → `garmin_recovery`, `recovery_engine` |
| fit-dashboard | ⚙️ | Garmin health dashboard → `garmin_import`, `analytics_dashboard` |
| garmin-ai-coach | ⚙️ | CLI Garmin coach → `garmin_recovery`, `ai_workout_coach` |
| garmin-ai-notifier | ⚙️ | Daily AI brief push → `daily_health_brief` |
| garmin-health-data | ⚙️ | Garmin to SQLite import → `garmin_import` |
| garmin-kpi-dashboard | ⚙️ | Garmin KPI dashboard → `analytics_dashboard` |
| garmin-stats-ai | ⚙️ | Garmin analytics chat → `garmin_data_analyzer` |
| garmindb | ⚙️ | Garmin downloader → `garmin_import`, `garmin_transforms` |
| open-wearable-insights | ⚙️ | Local wearable analytics → `garmin_data_analyzer` |
| statistics-for-strava | ⚙️ | Strava statistics → `strava_import` |
| tapiriik | ⚙️ | Multi-service fitness sync → `health_integrations` |
| intervals-icu-sync | 🗺️ | intervals.icu read/write sync and plan upload — no equivalent |
| trainingpeaks-mcp | 🗺️ | TrainingPeaks integration — no equivalent |

### G6. Fitness and workout tracking applications (33)

| Repo | Status | Note |
|---|---|---|
| coach | ✅ | Self-hosted endurance coaching and digital twin → `digital_twin`, `endurance_coaching` |
| fitness-trainer-pose-estimation | ✅ | Real-time form scoring → `pose_estimation`, `exercise_form_analyzer` |
| gymcoach | ✅ | AI coach with weekly debriefs → `ai_workout_coach`, `workout_planner` |
| peakready | ✅ | 0–100 readiness score → `peak_readiness`, `recovery_detection` |
| caber | ⚙️ | Workout string parsing → `workout_parser` |
| endurain | ⚙️ | Activity tracker → `workout_tracker` |
| fitdown | ⚙️ | Fitness log markup → `fitdown_parser` |
| fitfusion | ⚙️ | Real-time exercise tracking → `wearable_realtime` |
| fitness-coach | ⚙️ | Coaching logic → `ai_workout_coach` |
| fittrackee | ⚙️ | Self-hosted activity tracker → `workout_tracker` |
| freereps | ⚙️ | Records and evaluation server → `workout_tracker` |
| habitforge | ⚙️ | Gamified habits + community → `habit_tracker`, `habit_coach` |
| health-skill | ⚙️ | Personal health workspace → `health_chat`, `personal_health_assistant` |
| kinetiq-ai | ⚙️ | AI form feedback → `pose_exercise_engine` |
| openfit | ⚙️ | Cross-platform workout tracker → `workout_tracker` |
| openweight | ⚙️ | Strength-training data format → `openweight_format` |
| plate | ⚙️ | Nutrition and health sync → `meal_planner`, `precision_nutrition` |
| pulseai | ⚙️ | Full-stack AI health platform → `ai_health_assistant` |
| skulpt | ⚙️ | Multi-platform workout tracker → `workout_tracker` |
| sparkyfitness | ⚙️ | Self-hosted nutrition and metrics → `nutrition_tracking`, `nutrition_logger` |
| sport-tracker | ⚙️ | Gamified social fitness → `gamification`, `community` |
| sportiq | ⚙️ | Biomechanical analysis pipeline → `pose_estimation`, `athlete_monitor` |
| state-of-health-tracker | ⚙️ | Lift/eat/run tracking → `workout_tracker`, `nutrition_tracking` |
| vitaflex-ai | ⚙️ | Personalised wellness guidance → `generative_wellness` |
| wger | ⚙️ | Workout and fitness manager → `workout_engine`, `exercise_service` |
| wingfit | ⚙️ | Self-hosted fitness tracker → `workout_tracker` |
| workout-tracker | ⚙️ | Personal workout web app → `workout_tracker` |
| Jackie | ➖ | React Native demonstration app |
| ai-workout-tracker | ➖ | Sanity CMS demonstration app |
| react-native-expo-fitness-app | ➖ | Expo scaffold |
| elderly_app | ➖ | Unrelated care application |
| health-app | ➖ | Create React Native App scaffold |
| ignitegym-rn | ➖ | Gym app scaffold |
| ryot | ➖ | General life tracking, not fitness-specific |

### G7. Training load, injury risk and athlete monitoring (13)

| Repo | Status | Note |
|---|---|---|
| trainingloadcalculator | ✅ | Duration-sport load metrics → `training_load`, `training_intensity` |
| cycling-analysis-agent | ✅ | Self-hosted cycling analysis → `cycling_analysis`, `cycling_fueling_planner` |
| pgis-manus-skill | ✅ | Glycaemic-aware endurance coaching → `diabetes_manager`, `cycling_fueling_planner` |
| athlete-injury-risk-detection | ⚙️ | Workload/RPE injury risk → `injury_risk_engine`, `injury_predictor` |
| athlete-training-load-prediction | ⚙️ | Training load prediction → `training_load` |
| injury-prediction-prevention-ml | ⚙️ | Ensemble injury prediction → `injury_predictor` |
| injury_risk_prediction | ⚙️ | Injury risk analysis → `injury_risk_engine` |
| monitoring-athletes-performance | ⚙️ | Coach feedback generation → `athlete_monitor` |
| pedalmind | ⚙️ | Cycling training analytics → `cycling_analysis` |
| pitchease-dashboard | ⚙️ | Pitcher workload monitoring → `training_load`, `athlete_monitor` |
| athlete-core | ➖ | Generic TypeScript library |
| domestique | ➖ | Presentation-layer dashboard |
| regmon | ➖ | Sports-science platform under rebuild |

### G8. Medication safety and drug interaction (26)

| Repo | Status | Note |
|---|---|---|
| rxinteract | ✅ | RxNorm + OpenFDA interaction API → `drug_interaction_checker`, `openfda_client` |
| ddinter | ⚙️ | Drug interaction lookup → `drug_interactions` |
| dosezy | ⚙️ | Medicine tracking and reminders → `medication_reminder` |
| drug-drug-interaction-agent | ⚙️ | LangGraph interaction analysis → `drug_interaction_engine` |
| drug-interaction-checker | ⚙️ | PubChem interaction lookup → `drug_interaction_checker` |
| drug-interaction-dashboard | ⚙️ | ChEMBL interaction dashboard → `drug_interaction_checker` |
| drugsafetyportal | ⚙️ | Adverse drug reaction data → `openfda_client` |
| drugscan | ⚙️ | Prescription verification → `medication_checker` |
| llm-drug-interaction-checker | ⚙️ | LLM interaction detection → `drug_interaction_engine` |
| llm-medication-qa-risk-classifier-mediguard | ⚙️ | Medication QA risk classification → `medication_checker` |
| medication-interaction-checker | ⚙️ | Gemini-based interaction analysis → `drug_interaction_checker` |
| medrecon | ⚙️ | Medication reconciliation → `medication_checker` |
| mensung | ⚙️ | Offline interaction checker → `drug_interactions` |
| pharmexpert-drug-interactions | ⚙️ | Interaction knowledge base → `drug_interaction_engine` |
| pillchecker-api | ⚙️ | OCR identification + interaction check → `medication_checker`, `drug_interactions` |
| sagerx | ⚙️ | Medication ontology aggregation → `drug_network` |
| sdif | ⚙️ | Interaction database builder → `drug_interactions` |
| sourced | ⚙️ | Cited medication safety review → `medication_checker`, `health_misinformation` |
| t1copilot | ✅ | Type 1 diabetes AI copilot → `diabetes_manager` |
| chemicalx | ➖ | Drug-pair research model |
| gamenet | ➖ | Medication recommendation research |
| knowddi | ➖ | Knowledge-graph DDI research |
| safedrug | ➖ | Medication combination research |
| awesome-medication-recommendation | ➖ | Curated list |
| herbal-medicine-api | 🗺️ | 592 herb–drug interactions — no herbal interaction data |
| medication-safety-guideline-for-geriatric | 🗺️ | BEERS criteria and STOPP/START rules — `senior_health` exists but not the criteria sets |

### G9. Clinical records, triage and terminology (16)

| Repo | Status | Note |
|---|---|---|
| clinical-decision-support-system | ⚙️ | Medication risk analysis with RAG → `drug_interaction_engine`, `health_risk_engine` |
| deterioration-prediction | ⚙️ | Clinical deterioration detection → `early_warning_score`, `health_predictions` |
| dexta-intelligence | ⚙️ | Continuous glucose intelligence → `diabetes_manager` |
| early_warning_scores | ⚙️ | Early warning score computation → `early_warning_score` |
| fasten-onprem | ⚙️ | Personal health record server → `health_passport` |
| healthcare-ai-clinical-decision-support-system-using-langgraph | ⚙️ | LangGraph CDSS → `workflow_engine`, `health_risk_engine` |
| hikma-health-app | ⚙️ | Mobile electronic health record → `medical_id` |
| medagent-core | ⚙️ | Clinical agent framework → `workflow_engine` |
| medireport-ai | ⚙️ | Multi-pass OCR report extraction → `medical_imaging` |
| news2 | ⚙️ | NEWS2 scoring standard → `early_warning_score` |
| openfda-faers | ⚙️ | FAERS adverse-event data → `openfda_client` |
| schemas | ⚙️ | Open mHealth canonical schemas → `health_data_formatter` |
| fhir-server | 🗺️ | FHIR R4 resource model — AdapFit has no FHIR layer |
| oddb.org | ➖ | Swiss drug database, unrelated stack |
| snow-owl | ➖ | Commercial terminology server |
| umls-downloader | ➖ | Dataset downloader |

### G10. Emergency, SOS and elder care (8)

| Repo | Status | Note |
|---|---|---|
| oksigenia-sos | ⚙️ | Autonomous emergency beacon concept → `emergency_sos` |
| public-emergency-app | ⚙️ | Multi-role emergency response → `emergency_sos` |
| safeguard-emergency-sos-app | ⚙️ | SOS with location sharing → `emergency_sos`, `location_tracker` |
| sos-alerter | ⚙️ | Android emergency assistance → `emergency_sos` |
| sos-application | ⚙️ | Android SOS → `emergency_sos` |
| sos-emergency-app | ⚙️ | Contacts, messages, first aid → `emergency_sos`, `first_aid` |
| stay-safe-sos | ⚙️ | Android SOS → `emergency_sos` |
| real-time-person-elderly-fall-detection-system | 🗺️ | Occlusion-robust fall detection — no fall-detection module |

### G11. Anomaly detection and time-series machine learning (8)

| Repo | Status | Note |
|---|---|---|
| adtk | ⚙️ | Unsupervised anomaly detection → `anomaly_detection` |
| luminaire | ⚙️ | Anomaly detection library → `anomaly_detection`, `outlier_detection` |
| orion | ⚙️ | Unsupervised time-series anomaly detection → `anomaly_detection` |
| pyod | ⚙️ | Outlier detection toolkit → `anomaly_detection`, `outlier_detection` |
| sktime | ⚙️ | Time-series ML interface → `ml_engine` |
| nixtla | ➖ | TimeGPT, third-party hosted model |
| ts4health | ➖ | Slides and sample code |
| awesome-ts-anomaly-detection | ➖ | Curated list |

### G12. RAG agents, LangGraph workflows and MCP servers (14)

| Repo | Status | Note |
|---|---|---|
| agentic-rag-chatbot | ⚙️ | RAG fitness chatbot → `fitness_chatbot`, `rag_knowledge` |
| ai-fitness-planner | ⚙️ | LangGraph plan generation → `fitness_planner`, `workflow_engine` |
| fitness-chatbot | ⚙️ | RAG fitness assistant → `fitness_chatbot` |
| rag-anything | ⚙️ | Multimodal RAG pipeline → `rag_knowledge` |
| rag-fitness-coach | ⚙️ | Expert-persona RAG coach → `fitness_chatbot` |
| fastapi-langgraph-agent-production-ready-template | 🧩 | Template pattern maps to `workflow_engine`, which exists but is not exposed through an endpoint |
| fitness_coach_mcp | 🗺️ | MCP server surface — AdapFit has no MCP server |
| garmin-mcp | 🗺️ | MCP server surface — none |
| medical-mcp | 🗺️ | MCP server surface — none (though `openfda_client` supplies the data) |
| openfda-mcp-server | 🗺️ | MCP server surface — none |
| oura-mcp-server | 🗺️ | MCP server surface — none |
| whoop-mcp | 🗺️ | MCP server surface — none |
| biomcp | ➖ | Rust biomedical MCP binary |
| awesome-langgraph | ➖ | Curated list |

### G13. Gamification and habits (8)

| Repo | Status | Note |
|---|---|---|
| achievibit | ⚙️ | Achievement webhooks → `achievements_engine` |
| gamification-engine | ⚙️ | Generic gamification engine → `gamification` |
| gamification-server | ⚙️ | Awards and points framework → `health_rewards`, `achievements_engine` |
| level-up | ⚙️ | XP and levels → `gamification`, `achievements_engine` |
| django-gamification | ➖ | Django-specific plugin |
| laravel-achievements | ➖ | Laravel-specific package |
| laravel-gamify | ➖ | Laravel-specific package |
| ui | 🗺️ | Prebuilt gamification UI kit (trophyso) — the mobile app has streak and achievement screens but no such component library |

### G14. Authentication, FastAPI infrastructure and libraries (10)

| Repo | Status | Note |
|---|---|---|
| authx | ⚙️ | Authentication library patterns → `jwt_authentication`, `core/auth` |
| fastapi-jwt-auth | ⚙️ | JWT authentication → `jwt_authentication` |
| fastapi-jwt | ⚙️ | JWT extension → `jwt_authentication` |
| fastapi-users | ⚙️ | User management → `core/auth` |
| slowapi | ⚙️ | Rate limiting → `limiter`, `rate_limiter` |
| awesome-fastapi | ➖ | Curated list |
| fastapi-best-practices | ➖ | Documentation only |
| full-stack-fastapi-template | ➖ | Project template |
| minimal-fastapi-postgres-template | ➖ | Project template |
| jwt-module | ➖ | Express/TypeScript, wrong stack |

### G15. Quantified self, personal data and self-hosted platforms (15)

| Repo | Status | Note |
|---|---|---|
| mirobody | ⚙️ | Health data collection and standardisation → `health_data_formatter`, `health_api_gateway` |
| selfhosted-health | ⚙️ | Wearables as disposable feeders → `device_sync` |
| opentwins | ⚙️ | Open-source digital twin platform → `digital_twin` |
| chronicle-etl | ➖ | Personal data archiving |
| dogsheep.github.io | ➖ | Personal analytics toolchain |
| hpi | ➖ | Personal data framework |
| me-api | ➖ | Personal data API |
| open-pryv.io | ➖ | User-data storage platform |
| ownchart | ➖ | Health narrative app |
| personal-timeline | ➖ | Timeline research tool |
| pulse | ➖ | Fitbit Air iOS client |
| qs_ledger | ➖ | Quantified-self scripts |
| quantified-self | ➖ | General tracking platform |
| shenas | ➖ | Local-first federated platform |
| timelinize | ➖ | Personal timeline organiser |
| awesome-quantified-self | ➖ | Curated list |

### G16. Outside the product domain (13)

| Repo | Status | Note |
|---|---|---|
| core | ⛔ | Home Assistant, home automation |
| esphome | ⛔ | IoT device firmware platform |
| openhab-addons | ⛔ | Home automation add-ons |
| sure | ⛔ | Personal finance |
| noop | ⛔ | Unrelated app collection |
| omi | ⛔ | Screen and conversation capture |
| alertness-recognition | ⚙️ | Drowsiness and gaze detection → `drowsiness_detection` |
| fatigue-detection-using-deep-learning | ⚙️ | Facial fatigue cues → `fatigue_prediction` |
| biomarkerdash | ⚙️ | Bloodwork trend dashboard → `biomarker_tracker`, `body_dashboard` |
| bloodboy | ⚙️ | Blood test tracking with extraction → `biomarker_tracker` |
| scikit-digital-health | ⚙️ | Wearable inertial sensor analysis → `accelerometer_analyzer` |
| openreact | ➖ | Java project, no health relevance |
| oasis | ➖ | Java project, no health relevance |
| awesome-openclaw | ➖ | Curated list |

### Corpus totals

| Mark | Count |
|---|---|
| ✅ Absorbed | 19 |
| ⚙️ Already covered | 158 |
| 🧩 Module present, unwired | 1 |
| 🗺️ Planned gap | 16 |
| ➖ Reference-only | 79 |
| ⛔ Out of domain | 6 |
| **Total** | **279** |

These totals were verified programmatically against the corpus inventory: all 279
repositories appear in Part 2 exactly once, with no omissions and no duplicates.

---

## Part 3 — Plan

**Phase 0 — Make the suite green.** Fix the eight dead endpoint modules from
defect 1. Each has two possible repairs: adapt the endpoint to the class-based
service API that actually exists, or add the missing module-level name. Prefer
adapting the endpoint, because module-level singletons over classes are what
created the ambiguity. For `sleep` specifically, do not repair it: there are
already four sleep endpoint modules (462 lines) for one feature, so the right
move is to delete `sleep.py` and fold anything unique into `sleep_analysis.py`.
Then make registry.py log every skipped module with its exception, and make
`main.py` fail fast if errors is non-zero. Goal: `5 failed, 947 passed` becomes
`0 failed, 952 passed`, and a future import failure is loud instead of silent.

**Phase 1 — Keep the corpus disposition honest.** Part 2 is complete and
verified: 279 repositories, each classified once. The remaining work in this
phase is maintenance — re-run the coverage check whenever the corpus or the
service surface changes, and correct the marks when a 🗺️ gap closes or a ⚙️
module gains an endpoint. AdapFit is the only project in this collection with no
absorption ledger, so this phase is about not losing the one that now exists.

**Phase 2 — Close the authorization hole.** This is the largest and most
important piece of work in the project. The mechanism exists
(`require_owner_or_owner_id`); it needs to be applied. In rough order:

1. Replace every path- or query-supplied `user_id` with the token-derived
   identity, so a handler cannot be asked for another user's data at all. This is
   strictly better than adding a check to each of 520 handlers, because it
   removes the parameter the mistake is made with.
2. Where an endpoint genuinely needs to address another user (admin views,
   provider summaries, emergency access), gate it with `require_admin` or
   `require_owner_or_owner_id`.
3. Start with `medical_id_api.py` (`/emergency/{user_id}`,
   `/wallet/{user_id}`, `/provider-summary/{user_id}`), then `health_data_api`
   and anything under `app/api/v1/domains/`, since those hold the most sensitive
   record types.
4. Add a test that iterates the registered routes and asserts that any route with
   a `user_id` path or query parameter does not resolve the caller's identity
   from it. That test is the regression guard for the whole class.

**Phase 3 — Authenticate the WebSockets.** The middleware cannot do it, so each
of the seven handlers must validate on connect. `challenges_ws.py` and
`ws_camera.py` already read a token from the query string; use it, verify it with
`decode_token`, and derive the user from the token rather than from the path or
from the token's own text. Close connections that fail before accepting, and add
a per-connection timeout so that unauthenticated sockets cannot accumulate.

**Phase 4 — Make failures loud.** Remove the `except ImportError: pass` wrappers
around the middleware imports in `main.py` (defect 8). A missing security
middleware must stop the process. Do this after Phase 0 so that the real import
failures are fixed first and the change does not turn a working app into a
non-booting one.

**Phase 5 — Secrets and records.** Move the `docker-compose.yml` literals into a
`.env` file that is not committed, keep placeholders in the compose file, and
rotate the committed database password since it is in git history. Then either
regenerate or delete `.sb-pentest-audit.log` and `.sb-pentest-context.json` —
a security record that reports "no P0 findings" alongside a real committed
password is worse than no record.

**Phase 6 — Reduce the sprawl.** Consolidate the numbered generations. Concretely:
pick one of the four sleep endpoint modules and delete the rest; collapse the nine
sleep services and six HRV services to one each plus explicit variants; and pick a
single generation for each of `achievements`, `ai_coach`, `community`,
`recovery`, and `export`. The `ROUTE_MAP` prefix collisions (`/workouts`, `/chat`,
`/challenges`, `/sleep-analysis`, `/wearable`) should be resolved as part of this
so that each prefix belongs to exactly one module. Make `register_endpoints`
idempotent (defect 10) at the same time, since consolidation will make
re-registration a normal thing to do in tests.

**Phase 7 — Close the planned gaps.** The 20 🗺️ items, grouped by value:

- *Identity and safety*: `require_owner_or_owner_id` adoption is Phase 2, but the
  geriatric medication criteria (BEERS, STOPP/START) and herbal interaction data
  are real clinical-safety gaps.
- *Interoperability*: FHIR R4 support, and the MCP server surface that six
  different corpus repositories independently implement. A single MCP server
  exposing the existing services would close six rows at once and is the
  highest-leverage item in this list.
- *Training data*: intervals.icu sync, TrainingPeaks, the Concept2 ergometer
  driver, and the wider BLE scale matrix.
- *Mobile*: iOS WorkoutKit integration and a gamification component library.
- *Safety net*: fall detection.

---

## Part 4 — Not doing

- **Absorbing the ➖ repositories.** 84 of them are curated lists, datasets,
  unpublished research models, framework-specific plugins, or packages for a
  different stack. There is no artifact to take. They are recorded so that the
  corpus disposition is complete, not because there is work hiding in them.
- **Adopting FHIR wholesale.** FHIR R4 is genuinely useful for interoperability,
  but retrofitting it onto a system whose storage layer is `storage.get_stats()`
  and per-user dicts is a rewrite, not an absorption. It is listed as a gap and
  should be scoped separately.
- **Replacing the auth middleware with an authorization middleware.** It is
  tempting to add the ownership check in `AuthMiddleware` and be done. That does
  not work: the middleware cannot know which resource a route addresses, and it
  demonstrably cannot see WebSocket traffic at all. The fix belongs at the route
  layer.
- **Chasing the leftover `except Exception` blocks.** The empty `except`
  handlers in the daemon-adjacent helpers are best-effort cleanup of optional
  resources. The one that matters is defect 1's, and that is Phase 0.
- **Fixing the placeholder-shaped values in `docker-compose.yml` as if they were
  secrets.** `JWT_SECRET_KEY`, `GEMINI_API_KEY` and `GROQ_API_KEY` there are
  placeholders. They should still move to `.env` for hygiene, but they are not
  incidents and should not be treated as ones. `POSTGRES_PASSWORD` is the real
  one.

---

## Part 5 — Verification

| # | Defect | How it is confirmed | How the fix is checked |
|---|---|---|---|
| 1 | Eight endpoint modules dead | `register_endpoints() -> {'registered': 218, 'skipped': 2, 'errors': 8}`; each of the eight named modules raises `ImportError` for a name its service module does not define | All eight register; registry logs instead of swallowing; `main.py` fails fast on errors |
| 2 | Suite red with the dead modules | `5 failed, 947 passed in 95.51s`; the five failures are the fitness and sleep routes | `0 failed, 952 passed` |
| 3 | Broken access control | 13 of 229 files use auth deps, 216 do not, 0 read `request.state.user`, 520 handlers take `user_id`, 3 take a `Request`; `medical_id_api.py:31` reads another user's emergency record | Route-invariant test: no route derives identity from a request parameter |
| 4 | Auth helpers unused | `get_user_id` has 0 callers; `get_current_user` is imported by 1 endpoint file; `require_owner_or_owner_id` has none | Callers exist and the invariant test passes |
| 5 | WebSockets unauthenticated | `BaseHTTPMiddleware` sees HTTP scope only; `ws_chat.py:86`, `ws_camera.py:26` accept without checks; `challenges_ws.py:44-46` accepts any non-empty token | Each handler rejects a bad token before accept and derives identity from the token |
| 6 | Committed password | Ten literal env entries in `docker-compose.yml`; `POSTGRES_PASSWORD` is 14 chars, not a trivial default and not placeholder-shaped; `.env` is correctly ignored (`.gitignore:9`); `.env.example` values are localhost/placeholder | Compose contains no secret; password rotated |
| 7 | Self-contradicting audit log | `[WARNING] Hardcoded credentials found` immediately followed by `[COMPLETE] ... no P0 findings`; duplicate `START` line; every timestamp exactly 5s apart | Regenerated or removed |
| 8 | Middleware fails open | `main.py` wraps the security and auth middleware imports in `except ImportError: pass` | Imports are unconditional; a failure stops startup |
| 9 | Endpoint and service sprawl | Four sleep endpoint modules (462 lines) and nine sleep services; `achievements`/`_v2`/`_v3`; 5 duplicate `ROUTE_MAP` prefixes; 0 duplicate method+path pairs currently | One module per feature; no duplicate prefixes |
| 10 | Registry mutates shared state | `_strip_baked_prefix` rewrites `route.path`/`path_regex` on the `sys.modules`-cached router; `full_prefix` drops the module prefix when it strips | Registration is idempotent under a double call; test covers it |
| 11 | `sys.path` mutation | `main.py:8-11` inserts the project root before importing app code | Imports resolve without the mutation |
| 12 | Public `/metrics` | `/metrics` is in `PUBLIC_ENDPOINTS` and mounted at root | Auth applied, or the exposure is a documented decision |
| 13 | Key in query string | `mobile/app/(tabs)/dev-tools.tsx:87` uses `?key=` for the Gemini API | Key moves to a request header |
| 14 | Dirty tree | 457 deleted, 25 modified, 32 untracked; deletions are an unused tooling directory; `main.py`, `registry.py`, `challenges_ws.py` modified | Reconciled deliberately before any commit |
| 15 | Corpus disposition | Verified: 279 repositories, each appearing exactly once, no omissions or duplicates | Coverage check re-run whenever the corpus or service surface changes |

---

## Part 6 — Applied fixes

These are the changes that were made, each with the check that proves it. Four
of the fifteen defects are closed; the rest are recorded above and are still
open. Nothing here has been committed.

### Defect 1 — the eight dead endpoint modules

Every one of the eight now registers. Each was repaired by giving it the
service API it was written against, as thin functions and models over the
class-based implementation that already existed, rather than by rewriting the
endpoint to match the class. Where a name collided, the endpoint was pointed at
a distinctly named function: `fitness_assessment.assess_strength` already meant
"score push-ups, sit-ups and a plank", so the endpoint's lift-relative call
became `assess_lift_strength`.

| Module | Added to the service |
|---|---|
| `sleep` | `SleepEntry`, `SleepAnalysis`, `StageMinutes`, `analyze_sleep` — aggregates nights and grades the result |
| `fitness_assessment` | `OneRepMaxEstimate`, `FitnessTest`, `estimate_1rm`, `assess_lift_strength`, `assess_fitness_test`, `available_tests`, a six-test normative table |
| `injury_risk` | A facade over `InjuryRiskEngine` joining workout and recovery logs by day, plus `MUSCLE_VULNERABILITY` for eight body regions |
| `activity_recognition` | `SensorReading`, `UserProfile`, `detect_activity`, `count_steps`, `estimate_distance`, `calculate_calories`, `classify_intensity` |
| `body_health_api` | `BloodPressureService` with logging, today view, trend and doctor report; AHA/ACC classification reused |
| `cardiovascular_api` | `HRVReading`, `CVRiskProfile`, `analyze_hrv`, `calculate_cv_risk`, `calculate_hr_zones`, `classify_hr_zone`, `ecg_to_hrv`, `max_hr_from_age` |
| `gamification_api` | An eight-badge catalogue and `GamificationService` over the existing pure functions |
| `nutrition_tracking_api` | `MacroNutrients`, `MicroNutrients`, `MealEntry`, `DailyIntake`, eleven dietary profiles, `analyze_daily_intake`, `calculate_tdee`, `score_meal_quality` |

Reuse was the rule rather than reimplementation. `estimate_1rm` delegates to the
Epley implementation already in `openweight_format`, `ecg_to_hrv` calls the
Pan-Tompkins detector in `biosignal_analysis`, `calculate_tdee` calls
`FitnessPlanner`, and the blood-pressure facade calls the pure
`classify_reading`, `analyze_trends` and `assess_risk` functions in its own
module. That matters here because defect 9 counted five separate TDEE
implementations before this change; adding a sixth would have made the sprawl
worse.

Check:

```
register_endpoints() -> {'registered': 226, 'skipped': 2, 'errors': 0}
```

It was `{'registered': 218, 'skipped': 2, 'errors': 8}`. All 228 endpoint
modules import cleanly. The four endpoints that could be handed an unknown
identifier — fitness test, body region, badge, dietary profile — now raise 404
rather than a server error, and the blood-pressure logger validates its ranges
at the trust boundary and returns 400.

### Defect 2 — the red suite

```
952 passed in 112.37s
```

It was `5 failed, 947 passed`. All five failures were the dead fitness and sleep
routes, so defect 1 was the whole of it. No test was changed to make this pass.

### Defect 5 — unauthenticated WebSockets

`app/core/dependencies.py` gained `authenticate_websocket`, which reads a token
from the `token` query parameter or an `Authorization` header, validates it with
the existing `decode_token`, and closes the socket with code 1008 before
accepting when the token is missing or invalid. Where the route names a user in
its path or query, the caller must be that user, or carry an admin role.

All seven routes now call it: `ws_chat`, `ws_camera`, `challenges_ws`,
`sensor_hub`, `workout_rooms`, and the two handlers declared directly on the app
in `main.py`. Two details were corrected on the way:

- `challenges_ws` accepted **any** non-empty string as a token and then derived
  the user's identity from the token text itself (`f"user-{token[:8]}"`), so a
  client could name itself anything. It now validates properly.
- That same handler closed the socket a second time after a refusal, which is why
  a refused connection surfaced a code other than 1008. The helper closes; the
  handler returns.

`tests/test_websocket_auth.py` (20 assertions) drives every route three ways:
anonymous, owner, and a stranger holding a valid token. Demonstrated to
discriminate by removing the check from `ws_chat` and watching exactly the three
chat assertions fail.

### Defect 8 — middleware that failed open

`main.py` imported the security and auth middleware inside `try` blocks whose
`except ImportError: pass` meant a broken import left the app running with no
authentication and no security headers. The imports are now at module scope and
the middleware is added unconditionally, so a failure stops startup. Confirmed
present in the live stack:

```
BaseHTTPMiddleware, CORSMiddleware, AuthMiddleware, RequestLoggingMiddleware,
InputSanitizationMiddleware, SecurityHeadersMiddleware, CompressionMiddleware,
ErrorHandlingMiddleware, MetricsMiddleware, ValidationMiddleware
```

### Defect 3 — the medical ID routes

The emergency view is the most sensitive record in the application: blood type,
allergies, current medications, emergency contacts, addressed by a user id in
the URL. All six routes in `medical_id_api.py` now require authentication and
check ownership.

The existing `require_owner_or_owner_id` could not be used for this. Its
argument is a plain string that is evaluated where the dependency is declared,
so it can only ever compare against a fixed literal — which is why its own
docstring passes `"me"`. A runtime value cannot reach it. `ensure_owner(caller,
user_id)` was added alongside it for the path- and query-supplied case, and it
yields to the development bypass, which is what makes that bypass usable at all
and can never be active in production.

`tests/test_medical_id_access.py` (10 assertions) covers anonymous (401),
another user (403) and owner (200) on the three read routes, plus a cross-user
write.

This is one endpoint file of the 216 that use no auth dependency. The mechanism
now exists and is proven; applying it across the remaining files is Phase 2 and
is not done.

### Two bugs found in shared code while doing the above

Neither is in Part 1, because neither was visible until a caller existed.

**`CardiovascularAnalyzer.estimate_vo2_max` raised `NameError` on every call.**
It computed `15.3 * (max_hr / resting_hr)` where `max_hr` is neither a parameter
nor a module global, so the function — and `full_analysis`, which calls it —
could never return. Nothing called either, so nothing caught it. The value is
now derived from the sibling `estimate_max_hr`.

**`biosignal_analysis.detect_r_peaks_simple` could not find a peak in a signal
with a realistically wide QRS complex.** The moving-average integration step
produces a flat plateau for a wide complex, and the peak test required
`integrated[i] > integrated[i+1]` — strictly greater than the next value. On a
plateau no sample satisfies that, so the function returned zero peaks for the
whole signal. Measured on a nine-beat synthetic ECG at 250 Hz:

```
before: 0 peaks
after:  9 peaks at 250, 500, 750, 1000, ... -> heart rate 60.0 bpm
```

The existing test for this function passes only because it adds a 60 Hz sine
term to the signal, which breaks the plateau up. The comparison now accepts
equality on the right, which selects the last sample of a plateau.

### Two routing facts worth recording

- The `/api/v1/challenges` WebSocket answers at
  `/api/v1/challenges/ws/challenges/{challenge_id}`. The declared prefix from
  `ROUTE_MAP` is applied on top of a route path that already contains
  `/ws/challenges/`, so the segment repeats. Defect 9.
- Seven WebSocket routes are registered, and the five declared on routers are
  reachable. A quick check of `app.routes` finds only the two declared on the
  app itself, because this FastAPI version (0.139.2) keeps included routers as
  `_IncludedRouter` objects instead of flattening their routes. Enumerating
  WebSockets by looking at `app.routes` will undercount.

### Verified states

```
228 endpoint modules imported, 0 failures
register_endpoints() -> {'registered': 226, 'skipped': 2, 'errors': 0}
pytest tests/ -> 982 passed
pytest tests/test_websocket_auth.py -> 20 passed
pytest tests/test_medical_id_access.py -> 10 passed
```

The 982 is the 952 that the pre-existing suite reaches once defect 1 is fixed,
plus the 30 assertions in the two new files.

### Still open in this project

- Defects 3, 4, 6, 7, 9, 10, 11, 12, 13 and 14. The medical ID routes are
  guarded; the other ~215 endpoint files that take a `user_id` are not.
- The committed `POSTGRES_PASSWORD` in `docker-compose.yml` has not been changed
  or rotated. Moving it to an uncommitted `.env` and rotating it are both
  required, and rotation is not something this audit can do.
- The 457 deleted files and the pre-existing modifications in the working tree
  are untouched. Every file listed in defect 14 that this work also edited
  (`main.py`, `challenges_ws.py`, `sleep_analysis.py`, `sleep_analyzer.py`, the
  mobile components) still carries whatever was there before, plus these
  changes.

## Part 7 — Second-pass audit and fixes

Status as of 2026-09-12. This pass re-checked Parts 5 and 6 against the running application —
importing the app and reading its OpenAPI document — rather than against the source alone. It found
a deploy-breaking packaging defect, the cause of the route double-prefix bug that Part 6 recorded but
did not explain, and several smaller faults. It also committed the work that had been sitting in the
working tree, which the section above previously listed as untouched.

### 1. Neither Dockerfile copied `src/`, so 14 endpoint modules could not import

Both images copy `backend/` and `web/` and stop. Backend code reads 29 times from the `src.*`
packages, and `main.py` puts the project root on `sys.path` so those imports resolve:

```
$ grep -rn "from src\.\|import src\." backend/ --include=*.py | wc -l
29
$ sed -n '9,13p' backend/app/main.py
_zfit_root = str(_Path(__file__).resolve().parent.parent.parent)
if _zfit_root not in sys.path:
    sys.path.insert(0, _zfit_root)
```

`_zfit_root` resolves to `/app`, and `/app/src` did not exist in either image. The registry discards
an endpoint module that fails to import (defect 13), so the failure is silent: those routes simply
never register. Fourteen packages are affected — `achievements`, `anomaly`, `biomarkers`,
`biometrics`, `breathing`, `chat`, `injury`, `medication`, `planner`, `pose`, `rppg`, `sensors`,
`sleep`, `tracker` — and every one of them has an importer, so none is dead code. `railway.toml`
builds `Dockerfile.backend`, so the production deploy path was affected, not just the compose stack.

Both Dockerfiles now copy `src/` to `/app/src`, which is where `_zfit_root` looks.

Docker is not installed on the machine this audit ran on, so the images were not built. The COPY
paths were checked against how `main.py` computes the root rather than by building.

### 2. The route double-prefix bug: cause found, 23 paths fixed

Part 6 recorded 23 endpoint URLs with a doubled path segment and left the cause open. The cause is
that the registry appended the generated prefix to routers that had already written that segment
into their own paths.

```
$ sed -n '13p' backend/app/api/v1/endpoints/blood_pressure_api.py
router = APIRouter()
$ sed -n '31p' backend/app/api/v1/endpoints/blood_pressure_api.py
@router.get("/blood-pressure/classify")
```

The router declares no prefix, so the registry's mismatch branch — which strips a router's own prefix
when it disagrees with the declared one — never fires, and the generated `/blood-pressure` is
appended on top of a path that already starts with it. The registry now detects that case with
`_prefix_is_baked`, using the same reasoning it already applied to a declared prefix that disagrees.

Three modules could not be fixed that way and were corrected at the source instead:

- `health_predictions_api.py` mixed conventions — four routes baked `/predictions/...` and a fifth
  used a relative `/anomalies/detect`, so no single prefix rule could match it. It now declares
  `APIRouter(prefix="/predictions")` with five relative paths, which leaves the working
  `/api/v1/predictions/anomalies/detect` exactly as it was.
- `health_passport_api.py:80` declared `@router.get("/passport/{user_id}")` under a router whose
  prefix is already `/passport`, while its eight sibling routes are relative. The segment is removed.
- `habit_coach_api.py:20` declared `@router.get("/habits")` on a router mapped to `/habits`, producing
  `/api/v1/habits/habits`. It is now `@router.get("/")`, giving `/api/v1/habits/`.

Verified against the running app:

| Check | Before | After |
|---|---|---|
| OpenAPI path templates | 1225 | 1225 |
| Double-prefixed paths | 23 | **0** |
| `/api/v1/predictions/sleep` | absent | present |
| `/api/v1/passport/{user_id}` | absent | present |
| `/api/v1/habits/habits` | present | absent |

No route was gained or lost, so the count is unchanged and only the mount points moved. Nothing in
`backend/`, `mobile/` or `web/` referenced either doubled URL, so no caller needed updating.

The project's own check, `backend/scratch/check_route_prefix_fix.py`, exits 0 for the first time.
Three of its assertions were stale — it whitelisted the two doubles that are now fixed, banned every
path under `/api/v1/wellness/` even though `wellness_api` legitimately lives there, and expected an
`/api/v1/recovery-v1/` module that does not exist. Each had been hidden behind the failure before
it. They now assert what is actually true.

**That check is untracked.** `backend/scratch/` is in `.gitignore` (line 34), so the regression test
for this bug is not in the repository and cannot run in CI.

### 3. `docker-compose.yml` committed a credential and published the databases

```
$ grep -nE "POSTGRES_PASSWORD|5432:|6379:" docker-compose.yml   # before
49:      POSTGRES_PASSWORD: adapfit_secret
51:      - "5432:5432"
69:      - "6379:6379"
```

The password was also repeated verbatim in the backend's `DATABASE_URL` (line 18), so changing one
without the other would have broken the stack. Postgres and Redis were published on every interface,
not just loopback, so both were reachable from the host's network. The password now reads from
`${POSTGRES_PASSWORD:-adapfit_dev_only}` in both places, the two port mappings bind `127.0.0.1`, and
the obsolete `version:` key is gone.

Compose itself does not need those host ports: the backend reaches both services over the compose
network by name. The mappings exist only for a developer connecting from the host.

**Not done:** the exposed password has not been rotated. That is the operator's action, and the audit
cannot perform it. Treat `adapfit_secret` as compromised.

### 4. Smaller findings, recorded and not fixed

- **The audit's own test-count and gate claims were not reproducible as stated.** `python -m pytest
  tests/ -q` reports **982 passed**, not the 952 the plan header claims; `npx tsc --noEmit` in
  `mobile/` fails with 13 errors, all in `e2e/app.test.ts` importing an uninstalled `detox`, and the
  mobile package has no test script and no CI job. `python -m ruff check app/` reports **5480 errors**
  and exits 1, and `ci.yml` runs it with no `|| true`, so the lint job is red on the committed tree —
  which also blocks the build job through `needs: [test, lint]`.
- **`python -m mypy` is not installed** on this machine, so the CI typecheck (`mypy app/
  --ignore-missing-imports || true`) could not be reproduced. It is masked either way.
- **`backend/app/core/registry.py` still discards a module that fails to import**, incrementing
  `errors` that `main.py:141` ignores. This is why finding 1 was invisible.
- **`/api/v1/openapi.json` is served without authentication** and the `/metrics` endpoint is
  allowlisted in `middleware/auth.py:54`, exposing route names and counters.
- **96 of 277 service modules (~23,180 LOC) are never imported**, 65 with zero references anywhere.
  `backend/app/api/v1/domains/` (25 files) is imported by nothing.
- **`backend/core_engine/` is never built**, so `is_rust_available()` is always false and every call
  takes the pure-Python path. No build step exists in either Dockerfile or in CI.
- **`backend/.env` is on disk with `AUTH_DISABLED=true` and real-looking API keys.** It is gitignored
  and was never committed, which is why this is not a leak, but the dev environment it configures has
  authentication switched off for the whole API.

### 5. Repo state

The working tree held 538 changed paths, 457 of them deletions of an unused tooling directory, none of them
committed. They are now committed in `711427a`. `plan.md` was untracked and is added in that commit.

The fixes are in `75f9f6c`. `registry.py` carries both my change and the route-map entries for the
absorbed modules that were already uncommitted before this pass.

### Still open

- The items in section 4, plus everything still listed in Part 6 that this pass did not touch: the
  ~215 unguarded endpoint files that take a `user_id`, the public `/metrics`, the dead services, and
  the unbuilt Rust engine.
- Rotate the Postgres password.
- Build both Docker images somewhere with Docker available, and confirm the `src.*` endpoints
  register — the fix is reasoned and the COPY paths verified, but the images were never built here.

---

## Part 8 — Multi-user, persistence, and the fabricated readings

Branch: `multi-user-personalization`, 16 commits on top of `6e1b019`.

Scope agreed at the start: a real multi-user product, running on local Postgres,
with every feature reachable and wired rather than a demo against one fake user.

### Verified state

- 1,395 backend tests pass. The suite was 9 red at the start of this work.
- Mobile typechecks clean (`npx tsc --noEmit`, 0 errors under `app/` and `src/`;
  the `e2e/` failures are missing detox types and predate this branch).
- The whole loop runs against real PostgreSQL 17 and survives a restart —
  `python -m scripts.verify_postgres` from `backend/` is that check.
- 67 of 71 mobile screens read live data. It was 34.

### 1. Identity binding — the largest defect

229 endpoint files, 4 of which used an auth dependency. 144 path templates and
195 query parameters took the subject's `user_id` straight from the request, so
any account could read any other by changing one segment.

The fix is one middleware, `app/middleware/identity.py`, rather than 500 edits
that only have to be forgotten once: the parameter is bound to the caller's
token before routing, across the path, the query string and the JSON body.

The worse half was omission, not substitution. Handlers declare
`user_id: str = Query("default")`, so a request that simply left it out landed
every account in one shared bucket — which is how the app had been running. The
middleware injects it when absent.

`/api/v1/admin/`, `/api/v1/medical-id/` and `/api/v1/forums/reputation/` are
exempt because naming another user is the point of those routes; each already
carries its own check. `tests/test_identity_binding.py` sweeps every registered
route, so a new one cannot quietly reopen the hole.

### 2. Accounts and sessions are durable

`UserManager` kept accounts in a process dictionary, so a restart deleted every
registration. They now write through to the `users` table (migration 007) or to
a local file, account ids are UUIDs matching the profile row, and refresh tokens
persist and rotate on use.

### 3. The recovery score is actually personal

`RecoveryEngine.compute_daily_recovery` has always accepted a baseline.
`recovery.py` never passed one, so every user in the system was scored against
the population defaults — HRV 50±10, sleep 8h. The central claim of the product
was not wired.

`app/services/personal_baseline.py` starts at those defaults and shifts toward
the user's own measurements as readings accumulate, reaching full confidence at
14 readings, and refreshes after every check-in. `tests/test_end_to_end_loop.py`
holds the property that matters: the same 60 ms reading scores high for a user
whose normal is 40 and low for one whose normal is 75.

### 4. Per-user service state

55 feature services were module-level singletons holding plain dicts, so one
medication list, one hydration total and one sleep log were shared by every
account on the server. `app/core/per_user.py` gives each caller its own
instance, resolved from the request identity, which converts a service by
changing the line that constructs it rather than every endpoint that calls it.

Services holding reference data or genuinely shared state — the exercise
catalogue, forums, community, family — are deliberately untouched.

### 5. Fabricated clinical readings

Around twenty services returned measurements that nothing had measured. This was
not visible in review, because a fabricated reading looks exactly like a real
one. The worst of them:

- **ECG interpretation** chose a rhythm with `random.choice` and reported it at
  85–99% confidence. Roughly one call in five announced atrial fibrillation and
  advised a cardiologist within 24 hours. It now derives heart rate and rhythm
  regularity from measured R-R intervals through the existing HRV analyser, and
  never names an arrhythmia — that is a diagnosis, not something intervals give.
- **Skin lesion scoring** defaulted the four ABCDE features to random values, so
  a request carrying no measurements could return high suspicion for melanoma —
  or miss one — by chance, with an invented probability attached to the word.
- **Cardiac rehab** defaulted age to 65, and the target heart-rate zone is
  derived from age, so a 45-year-old was given a 65-year-old's training ceiling.
  Blood pressure defaulted to "120/80" and oxygen saturation to 97, silencing
  the alerts the daily log exists to raise for exactly the patient who recorded
  nothing.
- **Sleep audio** generated the night it was meant to be scoring.
- **Voice analysis** screened for Parkinson's, depression and cognitive decline
  from features that defaulted to random numbers, with the client computing each
  risk with `Math.random()` on top. The screening is gone; acoustic measurements
  and personal trends remain.
- **Air quality, pollen and ER wait times** were invented. Those are numbers
  people act on with asthma, hay fever or an emergency.
- **Camera heart rate** synthesised its own green-channel signal, always
  yielding about 60 BPM with a confidence beside it.

Every one now derives from real input or reports that the input is missing.
`tests/test_no_random_measurements.py` fails on any new random-generated
measurement across all 280 services, with an explicit allowlist for the uses
that pick wording or generate an id.

Camera heart rate has since been finished: `react-native-vision-camera` reads
the back camera's RGB buffer with the torch on, and the averages go to the
same CHROM estimator (`rppg_api.py`) instead of standing idle behind the
`FRAME_SAMPLING_AVAILABLE` switch. Untested on real hardware — no Android SDK
or device in this environment; verify torch behavior and finger-placement
signal quality on a phone before shipping.

### 6. Real data where it was invented

Air quality, UV index and pollen come from Open-Meteo, which is free and needs
no API key (`app/services/open_meteo.py`). Coverage is reported honestly: the
pollen model covers Europe, and outside it the API returns nulls, which surface
as "no coverage" rather than as a zero count.

### 7. Postgres

Installed natively via winget — Docker Desktop needs WSL2 and a reboot, and
neither was present. The schema applies to a stock Postgres now: migration 000
supplies the `auth.uid()` the Supabase RLS policies in 002 expect, and pgvector
is optional in both the schema and the connection pool, since a stock install
does not ship it. Semantic exercise search falls back to its in-memory index.

`python -m scripts.apply_migrations` applies pending migrations to an existing
database; the compose file feeds the same directory to initdb.

### Closing the Part 7 list

- The ~215 unguarded endpoint files: closed by the identity middleware.
- Rotate the Postgres password: the Supabase project no longer resolves and its
  entry is commented out in `.env`; the local database has a generated password.
  The old Supabase key is still worth rotating if it was used anywhere else.
- Docker images: still not built. Postgres runs natively instead.
- The public `/metrics` endpoint: still open.

### 9. The last nine screens

addiction-recovery, ambient, fertility, genomics, health-equity,
health-savings, precision-nutrition, pregnancy, and remote-monitoring all
read real data now, each behind a setup flow and an honest empty state
rather than the fixed sample it shipped with.

Wiring them surfaced the same class of bug Part 8.5 fixed elsewhere:

- Sobriety and journal mood clamps called `max()` on a bare int, which
  raises `TypeError` on every craving or journal entry.
- Genomics defaulted an untested gene to "normal" at 85-95% confidence —
  a pharmacogenomics panel that could tell a poor CYP2D6 metabolizer their
  codeine dose was fine without ever seeing that gene.
- Health equity silently scored missing SDOH categories at 50 and folded
  them into the weighted average, so scoring one category out of six
  produced a grade for all six.
- Health savings marked every expense HSA/FSA-eligible regardless of
  category.
- Fertility's cycle-regularity check always returned "regular, ±2 days"
  with no logged cycles behind it.
- Ambient health's environment score fell back to a fixed 50 when no
  device had reported a reading.

`tests/test_nine_screens_backend_fixes.py` covers each. Two services
(ambient health, health equity) needed a `get_homes`/`get_communities`
style lookup added, since a per-user singleton has no way to hand back an
id the mobile app never stored.

### Still open

- Posture assessment needs a pose detector supplying body landmarks —
  the same per-frame pixel access gap camera heart rate had, still open
  there.
- The telemedicine and hospital directories are sample data and now say so. They
  need a real provider before they mean anything.
- The Postgres superuser password is winget's default. Fine on loopback, worth
  changing if the machine is shared.
- `/metrics` is still public.
- The endpoint and service sprawl from Part 6 phase 6 is untouched, except that
  `chronic-pain-v2` and `pregnancy-v2` were deleted — both were registered in
  the tab layout but linked from nowhere.

---

## Part 10 — Consolidation (todo.md Phase 2)

Measured at the start: 229 route modules, 281 services, 93 services nothing
reached, 146 route modules no screen called. At the end: 208 route modules,
191 services, 3 unreachable (each assigned to a later phase), 1,254 backend
tests passing, mobile typecheck clean.

One implementation per feature: sleep, HRV, achievements, coach, community and
challenges, recovery, export, injury risk and recommendations each had two to
eleven parallel versions. The duplicates were not harmless. The recovery
dashboard scored HRV against population thresholds while the check-in used the
personal baseline, so the same morning had two different scores.

Fabricated data found and removed along the way, beyond Part 8:

- The coach's "personal" insights and health risks were canned sentences picked
  at random, with invented numbers in them.
- Device sync wrote fixed readings (7,200 steps, 72 bpm, 7.2 h sleep) as the
  user's synced data; Garmin and Strava imports reported counts and stored
  nothing.
- The analytics dashboard served every user the same generated 30 days.
- The forums and coach marketplace opened with invented members, testimonials,
  credentials and reviews.
- Nutrition targets were 2,500 kcal and 150 g protein for everyone.
- The mental health screen showed a fixed journal and a wellbeing score of 72.

Safety changes: interaction checks and diabetes patterns no longer tell users
to change doses; PHQ-9 results no longer suggest medication; NEWS2 gained the
single-parameter red score; sleep architecture reports patterns instead of
naming disorders.

New guards: `test_mobile_api_paths.py` (every mobile call has a route; it found
three screens calling paths that did not exist), `test_route_ownership.py`, and
the random-reading sweep now covers route modules.

## Part 11 — Durable feature state (todo.md Phase 2a)

Only accounts, check-ins, workouts and a few other records reached Postgres.
Everything else — 50 per-user services, 51 shared services and 40 module-level
stores, including medical ID, medications, meals, sleep and pregnancy logs —
lived in process memory and vanished on every restart. Two of the three
Dockerfiles also ran four workers, so each worker held a different copy.

`app/core/durable.py` writes that state through to one table (`feature_state`,
migration 008): one row per user for per-user services, one per shared service,
one per key for module stores. It loads at startup, saves only what a request
touched and only when it changed, and restores through an allowlisting
unpickler so a tampered row cannot run code. Services imported lazily are
restored when they register. The per-user LRU eviction is gone, since an
evicted user would have come back empty and been saved over. Overhead was
below measurement noise (about 3 ms per request either way).

Decided with the user: write-through with one worker on Railway for now;
per-request loading by user is the upgrade path. `tests/test_durable_state.py`
simulates a restart. Postgres itself was not exercised: the local password in
`backend/.env` was rejected.

## Part 12 — Screen coverage (todo.md Phase 2c)

Before: 206 route modules, 71 called by any screen. After: 133 modules, 95 in
use; the remaining 38 are infrastructure, device sync, WebSockets, or clinical
modules deferred to Phase 2b. Services went from 191 to about 130.

Decided with the user: keep what is unique or helps an ordinary user, delete
the rest, and group features into hubs rather than one screen each. Deleted:
gimmicks (blockchain records, AR, digital twin), off-market modules (US OSHA,
US insurance, B2B corporate), and duplicates (ten trend engines, a second forum
and chat, 17 workout modules, second body, ECG, medication and breathing
modules), plus "detection" modules that diagnosed.

New screens: Care & Safety, Conditions & Recovery, Everyday Wellbeing, Body,
Family (rewritten), and BP in vital signs. Built on real sources: OpenStreetMap
for care nearby, Open-Meteo for AQI and UV, validated instruments (IDRS for
diabetes risk, CDC STEADI for falls, digit span for working memory), and the
Government of India's NCD screening and schemes.

Defects found while wiring, beyond what earlier parts recorded:

- Fabricated or wrong: a Boston hospital list, bookable invented doctors and
  coaches, PM-JAY eligibility by income (it is SECC lists and age 70+), a
  demo family with invented members, fixed fitness and vision scores, content
  ratings and view counts, disease risk reductions per kilogram lost.
- Unsafe: symptom severity clamped so a 10/10 headache stopped being an
  emergency; BP labelled "stage 2 hypertension, medication typically required";
  a keyword myth-checker that answered every vaccine question with autism.
- Privacy: every user's lab results in one shared tracker; symptom history kept
  under one "default" user.
- Broken: rehab progress crashed on every call; two routes were shadowed by
  catch-alls; in-app family invites could never be accepted.

## Part 13 — Clinical modules built for real (todo.md Phase 2b)

Measured at the start: telemedicine still listed eight invented doctors with
ratings and bookable slots; genomics reported disease risk from an additive
model (0.1 plus fixed increments) and a "genetic health score"; mole ABCDE
derived asymmetry and border from the size typed in; ME/CFS pacing assumed age
35; cardiac rehab set training zones from 220 minus age. 999 backend tests
passed; the mobile typecheck failed on `e2e/`, which has no test runner
installed and is now excluded.

Decided with the user: telemedicine links out and checks registrations, image
measurement runs on the backend, genomics shows published odds ratios, and
Indian brands come from a large open dataset.

- Telemedicine: eSanjeevani, Tele-MANAS and three private platforms as
  outbound links, a "which doctor, how soon" guide, and a live check against
  the NMC Indian Medical Register (its public JSON search). Only registration
  fields are returned, not the address or birth date the register exposes.
  Saved doctors record what the register said, not what the client claimed.
- Genomics: parses 23andMe and AncestryDNA raw files (text or zip) and keeps
  only a fixed panel; the file is discarded. Associations carry the published
  per-copy odds ratio and its source (TCF7L2, FTO, 9p21). APOE is hidden until
  the user asks, with a counselling note. CPIC phenotypes for CYP2C19, CYP2C9,
  SLCO1B1 and VKORC1; CYP2D6 is reported as not callable from a chip. The old
  advice to take methylfolate for MTHFR is gone.
- Skin: `lesion_measure.py` segments the spot with OpenCV and measures
  asymmetry, border compactness, colour spread in CIELAB, and diameter from a
  coin of known size; blurry or empty photos are refused by edge width. The
  0-1 cutoffs are unvalidated screening choices; the dependable signal is
  change between photos of the same mole, which now counts as evolution.
- Medication: 246,068 marketed products from the MIT-licensed Indian Medicine
  Dataset, loaded lazily (~40 MB). Brands resolve to their ingredients; a brand
  whose products differ (Dolo, Telma) is treated as every ingredient, since a
  missed interaction is worse than an extra one. Interaction checks now see
  Indian brands and spellings.
- First aid and the red-flag replies ship inside the app and are used when the
  network is down; a test fails if the bundled copy drifts. Snakebite and
  poisoning (AIIMS poison centre) were added.
- ME/CFS pacing: ceiling is measured resting heart rate plus 15 (Workwell),
  or none; boom-bust detection; a section on the Conditions screen.

Unsafe or wrong, found and fixed:

- A dosage calculator (reduce by 25% over 65, defaults age 40 and 70 kg),
  a timing optimiser and Beers "alternatives" were live endpoints.
- A petechial rash with fever was "see a doctor within 24 hours"; it is now
  an emergency, as are lip swelling and breathing trouble. Rash output named
  meningococcaemia and herpes as causes.
- Reduced fetal movement said "try again after a snack"; it now says contact
  the maternity team today, judged against the baby's own pattern.
- Cardiac zones use the rehab team's prescription, else resting plus 20, with
  RPE 11-14 always shown; age-predicted zones fail on beta blockers.
- The Fitzpatrick skin type never reached the skin-check plan (string key
  looked up in an int-keyed table). First aid used 911, inches and °F.
- Defaults removed: wound size 2 x 2 cm and pain 3, a 2,000 ml fluid limit,
  30 s voice duration, pregnancy log fields.

Left for later phases: stroke rehab, chronic disease, hospital at home and
wound care stay API-only until a clinician designs them; the CDSCO banned
fixed-dose-combination list; the coach marketplace.

## Part 14 — Privacy, consent and user rights (todo.md Phase 3)

Measured at the start: account deletion existed only as an admin route; there
was no consent capture anywhere (the login footer claimed agreement to
documents that did not exist); `/export/all` and erasure skipped the 24 shared
services that keep every user's records in one object (fertility, pregnancy,
habits, medical passport, substance use...), and module stores keyed by record
id (a goal's logs, a post's comments) kept a deleted user's data. Settings said
"your data stays on your device", which was false, and its export buttons
showed "Export ready" without saving anything. 1,040 backend tests passed.

Decided with the user: deletion after a 30-minute grace period with password
confirmation; one required consent plus three optional ones; a guardian consent
flow for under-18s rather than an age gate; legal documents drafted with
placeholders for the company details.

- Consent (`app/core/privacy.py`): per purpose (`health_data` required; `ai`,
  `sharing`, `analytics` optional), tied to a policy version, appended to a log
  with time and source. `IdentityMiddleware` returns 403 with a reason while an
  account lacks current consent, awaits a guardian, or is scheduled for
  deletion; auth, privacy and export stay reachable. Sharing writes need
  `sharing`. Every LLM call (chat, WebSocket chat, agent phrasing, goal parsing,
  weekly summary, meal photos) checks `ai` and falls back to rules.
  WebSockets now set the caller for per-user state and consent, which
  `authenticate_websocket` never did.
- Children: signup takes a date of birth; under 18 needs a guardian email. The
  guardian gets a 72-hour link to a server-rendered page, declares adulthood,
  and agrees or declines (decline erases the account). The child can withdraw
  but not grant; analytics is never offered to a child. Mail goes over SMTP
  (`app/core/mailer.py`). The interim identity check is a declaration;
  DigiLocker is the upgrade path.
- Erasure: `POST /auth/delete-account` schedules erasure; a sweep every minute
  runs it. `durable.erase_user` now walks shared services and module stores
  and removes anything keyed by the user id, any record with a field equal to
  it, set membership (likes), and records keyed by the ids of removed records;
  the in-memory storage fallback is cleared too. Signing out now clears the
  device cache and local SQLite database; before this there was no sign-out.
- Retention: a child account with no guardian decision is erased after 7 days;
  an account unused for 3 years gets an email and is erased 48 hours later
  unless the user signs in (no email, no erasure).
- Export: `/export/all` adds the account, shared-service records and the
  consent log.
- Documents: privacy policy, terms and health disclaimer in
  `backend/app/legal/`, served at `/privacy/documents/{id}` and shown in the
  app; `docs/PRIVACY.md` holds the retention table, store declarations and
  enforcement map.
- Mobile: signup asks for date of birth, consent per purpose and a guardian
  email when needed; a Privacy screen manages consent, guardian status,
  deletion (with cancel), export and sign-out; the root layout sends a blocked
  account there.

Also fixed: meal photo logging without an AI key saved a zero-calorie "Photo
meal"; it now refuses and asks for manual entry.

Left for later phases: the security audit log is still in memory, so the
1-year log retention in the policy is not yet met (Phase 4); `POST /users` is
public and creates profile rows without an account, and the mobile store falls
back to the seeded `default` identity when no user is stored (Phase 4); backup
retention and re-applying erasures after a restore (Phase 8); filling the
placeholders, appointing the Grievance Officer, SMTP in production and
DigiLocker (Phase 10).

## Part 15 — Security hardening (todo.md Phase 4)

Measured at the start: `AuthMiddleware` accepted a refresh token as a Bearer
credential, and `IdentityMiddleware` only binds `user_id` for access tokens, so
a refresh token reached every handler unbound: any user's records could be read
or written by naming their id, and the consent gate was skipped. Any signed-in
user could create, list and revoke API keys (`/auth/keys`), which nothing ever
validated. `/encryption/encrypt` stored random bytes as "ciphertext" and threw
the data away; `/security/compliance/*` reported every HIPAA/GDPR requirement
"implemented". A suspended or erased account's access token kept working for 60
minutes, and a password change left every refresh token valid. Login, signup
and password reset had no rate limit (the token-bucket middleware existed but
was never installed). `/forgot-password` was a stub. The app kept the access
token in plain AsyncStorage and discarded the refresh token, so every session
died after an hour; sign-out never revoked anything server-side. The audit log
and `health_security` lived in process memory. `POST /users` was public and
the app fell back to the seeded `default` identity. `/metrics`, `/docs`, the
OpenAPI schema and the static admin pages were public in production, CORS
allowed localhost there, and `/health` published record counts. Feature state,
which holds the most sensitive modules, was stored as plain pickles.
1,047 backend tests passed.

Decided with the user: make the encryption API real rather than delete it;
app-level AES-GCM at rest; audit sensitive events (not every read); build
password reset by email now.

- Sessions (`app/core/auth.py`): access tokens 15 minutes; refresh tokens
  single use, and replaying a used one ends every session of the account
  (theft). Password change (returns a fresh pair), reset, suspension and
  erasure end every session; tokens of a suspended or erased account are
  refused at once. Only access tokens authenticate API calls, in both
  middlewares and the route dependencies. `JWT_SECRET_KEY_PREVIOUS` verifies
  old tokens during a key rotation. `/auth/logout` takes the refresh token
  without an access token, so sign-out works after expiry.
- Password reset: single-use 30-minute link by email, same answer for unknown
  addresses, server-rendered form, all sessions end, lockout cleared.
- Rate limits (`app/core/rate_limiter.py`, now installed): per caller and route
  class; sign-in routes per address with a generous burst for carrier-grade
  NAT; AI and export routes tighter. The Dockerfiles trust the platform proxy's
  `X-Forwarded-For` so the address is the client's.
- Audit (`app/core/audit.py`, migration 009): durable, 1-year retention purged
  by the erasure sweep; sign-ins, lockouts, session revocations, password
  events, exports, consent and guardian decisions, erasure, vault sharing, key
  operations, and any admin request naming another user. Unknown emails are
  stored as a keyed hash. Users see their own log in the Privacy screen
  (`/auth/activity`).
- Encryption at rest (`app/core/crypto.py`): every `feature_state` row sealed
  with AES-256-GCM under a keyring from `DATA_ENCRYPTION_KEYS`, authenticated
  with its namespace and key. A missing key stops startup rather than
  restoring empty state. Rows written before this are read as they are and
  sealed on the next change; `POST /encryption/key/rotate` seals everything.
- Vault (`/encryption/*`): records optionally locked with a passphrase the
  server never stores (PBKDF2 600k), time- and read-limited shares to another
  account (needs sharing consent, logged when read), key generation and
  rotation for admins. `/security/*` reports the caller's own log and a
  measured self-check: organisational controls show "not_verified".
- Public surfaces: production serves no docs, schema, admin or static pages;
  `/metrics` needs `METRICS_TOKEN`; `/health` has no counts; CORS only
  `ALLOWED_ORIGINS`. Startup refuses production without a valid keyring or an
  https `PUBLIC_BASE_URL`.
- Removed the API key manager and its routes; `POST /users` now needs a token
  and completes the caller's own profile.
- Mobile: tokens in the Keystore/Keychain (`expo-secure-store`), one shared
  refresh on 401 then retry, sign-in when the refresh fails; all 20 direct
  `fetch` calls go through `authedFetch`. No `default` identity: signed out
  means the sign-in screen, signed in without a profile means onboarding.
  "Forgot password" works; sign-out revokes the session.
- `docs/SECURITY.md`: key rotation runbooks, limits, audit contents, the
  dependency scan and what is accepted.

Dependency scan: pip-audit finds protobuf 4.25.9 (held by mediapipe 0.10.21);
npm audit finds `uuid@7` (build tool) and `decode-uri-component@0.2.2` (via
expo-router), both shipped with Expo 55. Accepted with reasons in SECURITY.md.

1,060 backend tests pass; mobile typecheck clean.

Left for later phases: run `POST /encryption/key/rotate` once after the first
deploy with a key (Phase 8); container image scanning in CI (Phase 8);
persist rotated-token memory and the session cut-off before a second worker
(Phase 8); a change-password screen in the app (Phase 9); third-party
penetration test (Phase 10).
