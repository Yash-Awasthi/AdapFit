# Deployment

One image (`Dockerfile` at the repository root) runs the API. On start it
applies pending migrations when `DATABASE_URL` is set, re-encrypts any
`feature_state` row not under the first key in `DATA_ENCRYPTION_KEYS`, and
serves on `$PORT` (default 8000) with one worker: feature state lives in
process memory (`backend/app/core/durable.py`), so a second worker or replica
would hold its own copy. Before adding one, move feature state to per-request
loading and persist the used-refresh-token memory and the "sessions ended at"
cut-off (`backend/app/core/auth.py`), which also live in memory.

## Local stack

```bash
docker compose up --build        # API on http://localhost:8010, Postgres inside the network
```

Compose uses a development key it generates into its data volume. To reset
everything: `docker compose down -v`.

## Environment

| Variable | Required in production | Notes |
|---|---|---|
| `ENVIRONMENT` | `production` | Hides docs, schema and admin pages; enforces the checks below |
| `DATABASE_URL` | yes | Postgres 15+ with `pgcrypto`, `uuid-ossp` (and `vector` if available). Use a direct connection, not a transaction-mode pooler |
| `DATA_ENCRYPTION_KEYS` | yes | `k1:<base64 32 bytes>`; generate with `python -c "from app.core.crypto import new_key; print('k1:' + new_key())"` from `backend/` |
| `JWT_SECRET_KEY` | yes | 32+ random characters |
| `PUBLIC_BASE_URL` | yes, https | Used in password-reset and guardian links |
| `GROQ_API_KEY` or `GEMINI_API_KEY` | one of them | Both have free tiers |
| `SENTRY_DSN` | no | Error reports without request bodies, headers or query strings |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` | for reset and guardian mail | Without them the links are only logged |
| `METRICS_TOKEN` | no | Bearer token for `/metrics` |
| `ALLOWED_ORIGINS` | no | Only for a web client; the app does not need CORS |

## Free staging (Render + Neon)

1. Create a free Postgres at neon.tech (region Singapore) and copy the
   direct connection string (the one without `-pooler`).
2. On render.com: New > Blueprint > this repository. `render.yaml` defines the
   service. Paste `DATABASE_URL`, a generated `DATA_ENCRYPTION_KEYS`,
   `PUBLIC_BASE_URL` (the `https://...onrender.com` address Render shows) and
   an LLM key when asked.
3. Point the app at it: `EXPO_PUBLIC_API_URL=https://<service>.onrender.com`
   when building (see below).
4. Uptime: a free UptimeRobot monitor on `/health` every 5 minutes also keeps
   the free instance from sleeping during a test.

The free instance has 512 MB; the API idles at about 220 MB.

## Backups

```bash
cd backend
python -m scripts.backup dump ../backups          # nightly; files older than 30 days are deleted
python -m scripts.backup restore ../backups/adapfit-<stamp>.dump
```

Both need `DATABASE_URL`, and `pg_dump`/`pg_restore` on `PATH` (or `PG_BIN`).
A restore replays every erasure logged after the dump was taken (from the
live database when reachable, and from the ledger files kept beside newer
dumps), so an account deleted after the backup stays deleted. Restoring with
`pg_restore` directly skips that step.

Tested 2026-09-29 against Postgres 17: an account erased after the dump was
restored by `pg_restore` alone and erased again by the script, from the live
log and, with the live log overwritten, from a newer dump's ledger.

## Load test

```bash
RATE_LIMITING_ENABLED=false docker compose up -d
cd backend && python -m scripts.load_test http://127.0.0.1:8010 --users 20 --seconds 60
```

2026-09-29 on the compose stack (one worker, laptop): 20 users, 122
requests/s, no errors; p95 check-in 308 ms, decision 165 ms, generate 296 ms,
complete 289 ms.

## Android release

The release key is `mobile/android/app/adapfit-release.keystore`, described
by `mobile/android/keystore.properties`; neither is in git. Keep both, and
their passwords, in the company password manager: losing them means a new
Play listing. Without `keystore.properties` the release build is unsigned.

```bash
cd mobile
EXPO_PUBLIC_API_URL=https://<api host> npm run release:apk   # arm64 APK for a phone
EXPO_PUBLIC_API_URL=https://<api host> npm run release:aab   # bundle for Play
```

Bump `versionCode` in `mobile/android/app/build.gradle` for every upload.
The build writes several GB under `mobile/node_modules/*/android/build`;
delete those folders afterwards.
