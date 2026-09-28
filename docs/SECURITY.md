# Security

How AdapFit protects accounts and health records, and the runbooks for keys.
`docs/PRIVACY.md` covers consent, retention and erasure.

## Sessions

- Access tokens (JWT, HS256) last 15 minutes. Refresh tokens last 30 days, are
  stored only as SHA-256 hashes (`user_sessions`), and work once: each refresh
  returns a new pair.
- Presenting a refresh token that was already used ends every session of that
  account (a copy was stolen). Changing or resetting the password, suspension
  and erasure end every session too. A token of a suspended or erased account
  is refused at once, not after it expires.
- A refresh token is never accepted as an API credential.
- The app keeps both tokens in the Android Keystore / iOS Keychain
  (`expo-secure-store`) and refreshes once on a 401. The web build keeps them
  in memory only.
- Password reset: `POST /auth/forgot-password` emails a single-use link valid
  for 30 minutes; the answer is the same whether or not the email has an
  account. The link opens a server page (`/auth/reset-password/{token}`).
- Per-email lockout after 5 wrong passwords in 15 minutes.

## Rate limits

`app/core/rate_limiter.py`, a token bucket per caller (account when signed in,
otherwise address) and route class:

| Routes | Burst | Sustained |
|---|---|---|
| Sign-in, sign-up, password reset, guardian page (per address) | 30 | 6 per minute |
| Password change, account deletion | 10 | 2 per minute |
| AI routes (chat, coach, meal photos, voice) | 20 | 4 per minute |
| Export, key rotation | 5 | 1 per 2 minutes |
| Everything else under `/api/v1` | 180 | 3 per second |

Behind a proxy the client address comes from `X-Forwarded-For`, which uvicorn
only trusts when `FORWARDED_ALLOW_IPS` allows the proxy (the Dockerfiles set
`*` because the container is reachable only through the platform proxy).

## Encryption

- In transit: TLS at the platform proxy. `PUBLIC_BASE_URL` must be https in
  production (startup refuses otherwise).
- At rest: every `feature_state` row (all per-user and shared feature data:
  cycle, pregnancy, mental health, medications, substance use...) is sealed
  with AES-256-GCM (`app/core/crypto.py`), bound to its namespace and key so a
  row cannot be moved to another user. Core tables (`users`, workouts,
  recovery logs) rely on the database host's disk encryption.
- Vault (`/encryption/*`): records a user can lock with a passphrase the
  server never stores (PBKDF2-SHA256, 600,000 iterations), and share with
  another account for a limited time and number of reads.

### Rotating the at-rest key

1. As an admin, `POST /api/v1/encryption/master-key/generate` (or
   `python -c "from app.core.crypto import new_key; print('k2:' + new_key())"`).
2. Put the new key first in `DATA_ENCRYPTION_KEYS`, keep the old one after it,
   and restart.
3. As an admin, `POST /api/v1/encryption/key/rotate`: every row not under the
   new key is re-encrypted.
4. Remove the old key and restart.

Losing every key loses the data; keep `DATA_ENCRYPTION_KEYS` in the
platform's secret store and a copy in the company password manager.

### Rotating the JWT key

Set `JWT_SECRET_KEY_PREVIOUS` to the current key and `JWT_SECRET_KEY` to a new
one, restart. Old tokens keep working until they expire; remove the previous
key after 30 days (or at once to sign everyone out).

## Audit log

`security_audit` (Postgres; SQLite beside the feature store in development),
kept 1 year and purged by the erasure sweep. It records sign-in results,
lockouts, session revocations, password changes and resets, exports, consent
changes, guardian consent, deletion requests and erasure, vault sharing, key
generation and rotation, admin reads of the log, and any admin request that
names another user. Entries hold account ids and addresses, never health
records; an email that matches no account is kept as a keyed hash.
Users read their own entries at `GET /auth/activity` (Privacy screen); admins
read all at `GET /auth/audit-log`.

## Public surfaces

In production: no `/docs`, `/redoc`, OpenAPI schema, `/admin` static pages,
`/static` or `/dashboard`; `/metrics` needs `Authorization: Bearer
$METRICS_TOKEN` (404 when unset); `/health` reports status only; CORS allows
only `ALLOWED_ORIGINS`. WebSockets authenticate each connection
(`authenticate_websocket`) with the access token in the `token` query
parameter; that value can appear in proxy logs, so keep proxy access logs
short-lived.

## Dependency scan (2026-09-29)

- `pip-audit -r backend/requirements.txt`: protobuf 4.25.9 (PYSEC-2026-1805),
  held below 5 by `mediapipe==0.10.21`. The app does not parse untrusted
  protobuf; upgrade with mediapipe.
- `npm audit --omit=dev` (mobile): 14 moderate, all from two packages:
  `uuid@7` inside the build-time `xcode` tool (bug only with a caller-supplied
  buffer) and `decode-uri-component@0.2.2` under `expo-router`'s
  `query-string` (a crafted deep link can stall the app's own URL parsing).
  Both come with Expo 55; take the fix with the next Expo upgrade.

## Not done yet

- Container image scanning and a third-party penetration test (Phase 8 and 10).
- Rotated-token memory and the "sessions ended at" cut-off are in process
  memory; a restart forgets them, bounded by the 15-minute access token.
  Persist them before running more than one worker.
