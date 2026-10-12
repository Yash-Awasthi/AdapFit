# Better Stack: AdapFit

Upgrade plan built from the code itself (`backend/requirements.txt`, the root `Dockerfile`, the import graph of `backend/app` and `src/`, `backend/core_engine`, `mobile/package.json`, `mobile/app.json`, the mobile import graph and CI). Target versions were read from PyPI, npm, crates.io, Expo's `bundledNativeModules.json` and GitHub releases on 2026-10-12. "Newest" includes beta/RC builds; "Stable" is the newest final release.

## What the code actually uses

**Backend (`backend/app`, ~55k lines in 325 files, plus `src/` ~2.7k lines)**

- FastAPI (147 imports) + Pydantic (120) + Starlette middleware. Uvicorn, one worker.
- Postgres through **asyncpg** (5 modules) with pgvector; migrations are plain SQL under `backend/supabase/migrations`.
- `httpx` for LLM calls: Gemini REST (`core/gemini.py`, `gemini-3.6-flash`) and Groq's OpenAI-compatible endpoint (`core/config.py`).
- `slowapi` rate limiting, `cryptography` AES-GCM at rest, Sentry.
- Vision: MediaPipe pose (`form_check.py`), OpenCV + NumPy (`lesion_measure.py`), Pillow.
- Optional, lazily imported and **undeclared**: `sentence_transformers`, `transformers`, `faster_whisper`, `edge_tts`.
- `app/core/durable.py` keeps feature state in process memory, snapshots it with **pickle into SQLite**, and forces `--workers 1`.
- `backend/core_engine`: a 265-line PyO3 crate with four arithmetic functions (HRV z-score, sleep score, ACWR, subjective score) and a pure-Python fallback (`is_rust_available()`).

**Mobile (`mobile/`, ~34k lines)**

- Expo SDK 55, React Native 0.83, Expo Router with typed routes, plain `StyleSheet`.
- Icons from two libraries: `@expo/vector-icons` (66 imports) and `lucide-react-native` (22).
- Networking is `fetch` (9 files). Zustand for state (4 files). TanStack Query is imported once.
- Native: VisionCamera 5 (no frame processors), BLE (`react-native-ble-plx`), Health Connect, expo-sqlite.
- The generated `android/` project is committed.

## Dead weight to delete first

**Backend**

| Item | Evidence | Action |
|---|---|---|
| `supabase` | Zero imports; the DB layer is asyncpg | Remove |
| `structlog` | Zero imports; logging is stdlib `logging` | Remove |
| PyTorch CPU index in `Dockerfile` | `--extra-index-url https://download.pytorch.org/whl/cpu`, but nothing in `requirements.txt` pulls torch (`transformers` is commented out) | Remove the flag |
| `pytest`, `pytest-asyncio` in the runtime requirements | Ship inside the production image | Move to a dev group |
| `backend/core_engine` (Rust) | Four functions of scalar arithmetic. PyO3 call overhead is larger than the work, and the Python fallback already exists and is what the image runs (no Rust toolchain in the `Dockerfile`) | Delete the crate and keep the Python path. If it stays, upgrade `pyo3` 0.22 → 0.29.3 and `edition` 2021 → 2024 and build it with maturin in the image |

**Mobile**

| Item | Evidence | Action |
|---|---|---|
| `axios` | Zero imports; code uses `fetch` | Remove |
| `@gorhom/bottom-sheet` | Zero imports | Remove |
| `react-native-circular-progress` | Zero imports | Remove |
| `expo-blur` | Zero imports | Remove |
| `react-native-vision-camera-worklets` | No `useFrameProcessor` anywhere | Remove (keep `react-native-nitro-modules` and `react-native-nitro-image`, which VisionCamera 5 requires as peers) |
| `tailwind.config.js`, `nativewind-env.d.ts` | NativeWind is not installed and there are zero `className` props | Delete both files |
| `biome.json` | Biome is not a dependency, so nothing runs it | Add `@biomejs/biome` and a CI step, or delete the file |
| One of the two icon sets | `@expo/vector-icons` and `lucide-react-native` overlap | Standardise on one (lucide is tree-shaken per icon; `@expo/vector-icons` ships whole fonts) |
| `@tanstack/react-query` | One import | Either adopt it for all server data (it would replace the hand-rolled `useApi`/`useApis` hooks) or remove it |

## Backend upgrades

| Item | Current | Stable | Newest | Pick |
|---|---|---|---|---|
| Python (Dockerfile, CI) | 3.12 | 3.14.8 | 3.15.0rc3 | **3.14** now, 3.15 when final |
| Packaging | `pip install -r requirements.txt` | uv 0.13.0 | | **`pyproject.toml` + `uv.lock`**, `uv sync --frozen` in the image (fin-scrape already does this) |
| fastapi | >=0.115.0 | 0.143.0 | 0.143.0 | **0.143.0** |
| uvicorn[standard] | >=0.30.0 | 0.54.0 | 0.54.0 | **0.54.0**, or Granian 2.8.4 |
| pydantic / pydantic-settings | >=2.8 / >=2.0 | 2.14.1 / 2.15.0 | | **2.14.1 / 2.15.0** |
| python-multipart | >=0.0.9 | 0.0.32 | | **0.0.32** (several upload-parsing CVEs fixed since 0.0.9) |
| httpx | >=0.27.0 | 0.28.1 | 1.0.dev6 | **0.28.1** |
| slowapi | >=0.1.9 | 0.1.10 | | **0.1.10** |
| cryptography | >=44.0.0 | 50.0.2 | | **50.0.2** |
| asyncpg | >=0.30.0 | 0.32.0 | | **0.32.0** |
| pgvector (py) | >=0.3.0 | 0.5.1 | | **0.5.1** |
| numpy | `<2.0.0` | 2.5.4 | | **2.5.4** |
| opencv-contrib-python | `<4.10` | 5.0.0.93 | | **5.0.0.93** |
| mediapipe | ==1.0.1 | 1.1.0 | | **1.1.0** |
| Pillow | >=10.0.0 | 12.3.0 | | **12.3.0** |
| sentry-sdk[fastapi] | >=2.0.0 | 2.72.0 | 3.0.0a7 | **2.72.0** (3.0 is alpha with breaking API changes) |
| yt-dlp | >=2026.8.19 | 2026.8.19 | | keep |
| defusedxml | ==0.7.1 | 0.7.1 | | keep |
| pytest / pytest-asyncio | >=8.0 / >=0.21 | 9.1.1 / 1.4.0 | | **9.1.1 / 1.4.0** (pytest-asyncio 1.x removed the `event_loop` fixture; check the 93 test files) |
| Lint | `ruff` (unpinned, 5 rules) | 0.17.0 | | **ruff 0.17.0 pinned**, then widen the rule set gradually |

The `numpy<2` and `opencv<4.10` pins exist together for a reason: current OpenCV wheels require `numpy>=2`, and MediaPipe depends on OpenCV. Lift all three together (numpy 2.5.4, OpenCV 5.0, MediaPipe 1.1.0) and run `form_check` and `lesion_measure` against saved fixtures before shipping.

Declare the optional ML stack as an extra instead of relying on whatever happens to be installed:

```toml
[project.optional-dependencies]
ml = ["sentence-transformers", "transformers", "faster-whisper", "edge-tts"]
```

### Architecture: retire the pickle snapshot

`durable.py` loads all users' feature state into memory at startup, writes pickled snapshots to SQLite and pins the server to one worker. The module's own comment names the next step: per-request hydration keyed by user.

- Store each holder's state as a Postgres `jsonb` row keyed by `(user_id, holder)`, serialised with Pydantic or msgspec instead of pickle. Unpickling data from storage is code execution if that storage is ever tampered with; JSON is not.
- Load rows lazily per request and write back on change, which the snapshot-diff logic already does.
- Then `--workers` can go above 1 (or Granian with several workers), and the container no longer needs a local SQLite file.

## Mobile upgrades

| Item | Current | Stable (SDK 57) | Newest (SDK 58 beta) | Pick |
|---|---|---|---|---|
| `expo` | ~55.0.0 | 57.0.28 | 58.0.7 (`next`) | **SDK 58 beta**, fallback SDK 57 |
| `react-native` | 0.83.10 | 0.86.3 | 0.88.0-rc.2 | follows the SDK |
| `react` | 19.2.0 | 19.2.3 | 19.3.0 | follows the SDK |
| `react-native-reanimated` / `worklets` | 4.2.1 / 0.7.1 | 4.5.1 / 0.10.1 | 4.7.0 / 0.13.0 | follows the SDK |
| `react-native-gesture-handler` | ~2.30.0 | ~2.32.0 | ~3.2.1 | follows the SDK (3.x is a new gesture API; review the 3 call sites) |
| `react-native-screens` | ~4.23.0 | ~4.26.0 | ~4.28.0 | follows the SDK |
| all `expo-*` modules | 55.x | 57.x | 58.x | `npx expo install --fix` |
| `typescript` | ~5.8.0 | 7.0.2 | | **7.0.2** for `tsc --noEmit` |
| `@types/react` | ~19.0.0 | 19.3.0 | | match React |
| `zod` | ^4.5.4 | 4.6.7 | | **4.6.7** |
| `zustand` | ^5.0.0 | 5.0.15 | | **5.0.15** |
| `lucide-react-native` | ^0.468.0 | 1.55.0 | | **1.55.0** (1.x renamed some icons; check the 22 imports) |
| `react-native-vision-camera` | ^5.2.3 | 5.2.3 | | keep |
| `react-native-nitro-modules` | ^0.37.1 | 0.37.1 | | keep |

Notes tied to this app:

- Run upgrades with `npx expo install expo@next --fix` (or `expo@^57`) so every native module lands on the SDK-matched version, then `npx expo-doctor`.
- `patches/expo-modules-core+55.0.25.patch` pins a fix to SDK 55. Check whether upstream already contains it; if so, delete the patch, otherwise regenerate it for the new version.
- **Continuous Native Generation.** `mobile/android/` is committed, but `MainActivity.kt` and `MainApplication.kt` are the stock templates. Git-ignore `android/` and let `expo prebuild` generate it, with native settings in `app.json` plugins (`expo-build-properties` is already a dependency). This removes the main source of pain in every SDK upgrade.
- Turn on the **React Compiler** (`"experiments": { "reactCompiler": true }` in `app.json`). With 109 React imports and screens built from hooks, it removes most manual `useMemo`/`useCallback` work.
- `web/` is a 281-line static dashboard. Expo Router already targets web (`expo start --web`), so it can be folded into the app or left as is; it carries no dependencies.

## CI (`.github/workflows/ci.yml`)

| Action | Current | Latest |
|---|---|---|
| `actions/checkout` | v4 | v7.0.1 |
| `actions/setup-python` | v5, Python 3.12 | replace with `astral-sh/setup-uv@v10.3.0`, Python 3.14 |
| `actions/setup-node` | v4, Node 24 | v7.1.0, Node 24 or 26 |
| `aquasecurity/trivy-action` | `@master` | pin `@v0.36.0`; an unpinned third-party action runs whatever is on its default branch |

## Order of work

1. Delete dead backend and mobile dependencies and files; run `pytest` and `tsc`.
2. Backend to `pyproject.toml` + `uv.lock`; image built with `uv sync --frozen`; dev deps split out.
3. Python 3.14; library bumps; lift numpy/OpenCV/MediaPipe together with the vision fixtures.
4. Decide on the Rust crate (delete, or PyO3 0.29 + maturin build in the image).
5. Mobile: SDK 57 with `expo install --fix`, the patch check and `expo-doctor`; then CNG.
6. SDK 58 beta (RN 0.88 RC) and the React Compiler.
7. `durable.py` → Postgres `jsonb` per user, then raise the worker count.
8. CI action bumps and the Trivy pin.

Each step should leave the backend tests, `tsc --noEmit`, the `*.check.ts` scripts and the Docker build green.
