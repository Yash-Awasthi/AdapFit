# Privacy operations

How the app meets the DPDP Act 2023 and Rules 2025, where each rule lives in the
code, and what the store listings must declare. The user-facing documents are
in `backend/app/legal/` and are served at `/api/v1/privacy/documents/{id}`.

## Consent

- Purposes, policy version and every rule below: `backend/app/core/privacy.py`.
- Signup requires a date of birth. Adults must grant `health_data`; `ai`,
  `sharing` and `analytics` are optional. Every change is appended to the
  user's log with version, time and source (`signup`, `user`, `guardian`).
- Bumping `POLICY_VERSION` invalidates every grant, so each user sees the
  consent screen again. Do it only when a purpose or recipient changes.
- Enforcement:
  - `IdentityMiddleware` refuses API calls with 403 and a reason
    (`consent_required`, `guardian_pending`, `deletion_pending`) until the
    account is in order; `/auth`, `/privacy` and `/export` stay open.
  - POST/PUT/PATCH to community, family invites, peer support and challenges
    need `sharing` (`sharing_consent_required`).
  - Every LLM call checks `privacy.allowed("ai")` and falls back to rules.
  - WebSockets apply the same check in `authenticate_websocket`.
- Nothing collects product analytics yet. When something does, it must check
  `allowed("analytics")`; the purpose is never granted to a child.

## Children

Under 18 the account is locked until a guardian opens the emailed link
(`/api/v1/privacy/guardian/{token}`, valid 72 hours), gives name and
relationship, declares they are an adult guardian, and agrees. Declining
deletes the account. The child can withdraw consent but not grant it.

Known gap: Rule 10 expects the guardian's age and identity to be verifiable,
for example through a DigiLocker token. An emailed link with a declaration is
the interim method; add DigiLocker before marketing to families.

Mail needs `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`
and `PUBLIC_BASE_URL`. Without `SMTP_HOST` the link is only logged, and in
production nothing is sent.

## Erasure and export

- `POST /auth/delete-account` (password required) schedules erasure 30 minutes
  out; the account is blocked meanwhile and `POST /auth/delete-account/cancel`
  undoes it. A sweep in `main.py` runs every minute.
- `UserManager.delete_user` removes the account row (Postgres cascades every
  table keyed to it), the in-memory store fallback, every per-user service's
  state, and, through `durable.erase_user`, the user's records inside shared
  services and module stores: anything keyed by the user id, any record with a
  field equal to it, and records keyed by the ids of removed records (a goal's
  logs, a post's comments). Other users' posts keep existing without the
  deleted user's comments and likes.
- `GET /export/all` returns the account, stored records, per-user and shared
  feature data, and the consent log as one JSON file.

## Retention

| Record | Rule | Enforced by |
|---|---|---|
| Account and health records | Erased 30 min after a deletion request | `run_due_deletions` |
| Account unused 3 years | Email warning, erased 48 h later unless the user signs in | `schedule_retention` |
| Child account without guardian decision | Erased after 7 days | `schedule_retention` |
| Guardian link | 72 hours | `guardian_link` |
| Refresh sessions | 30 days, rotated on use | `auth.py` |
| Raw DNA file | Never stored | `genomics_insights.py` |
| Security audit log | 1 year (Rule 6) | Not yet: the log is in memory. Phase 4 |
| Database backups | At most 30 days | Phase 8. A restore must re-run erasures requested after the backup was taken |

## Breach response

The Board and every affected user are told without delay; the Board gets the
full report within 72 hours (Rule 7): what happened, when, the data and users
affected, the likely consequences, what was done, and a contact. The
runbook belongs to Phase 10 (incident response).

## Store declarations

Google Play Data safety and the App Store privacy label must match this table.

| Data type | Collected | Shared with third parties | Purpose | Optional |
|---|---|---|---|---|
| Email, name, user id | Yes | No | Account management | No |
| Date of birth | Yes | No | Age check for guardian consent | No |
| Health info (symptoms, conditions, medications, cycle, pregnancy) | Yes | With AI processors only when `ai` is on | App functionality, personalisation | No |
| Fitness info (workouts, steps, heart rate, sleep) | Yes | Same as above | App functionality, personalisation | No |
| Photos (meal, skin, progress) | Yes | Meal photos to Gemini only when `ai` is on | App functionality | Yes |
| Approximate and precise location | Only when the user asks for care nearby, AQI or a route | Coordinates to OpenStreetMap and Open-Meteo | App functionality | Yes |
| Messages to the coach | Yes | To Gemini or Groq when `ai` is on | App functionality | Yes |
| Genetic data | Read once, not stored | No | App functionality | Yes |
| App activity / analytics | No | No | - | - |

Declare: data encrypted in transit; users can request deletion (in app and by
email to the Grievance Officer); not used for advertising; not sold. Google
Play also requires a web page for account deletion requests: point it at the
privacy policy's erasure section once the site exists.

## Before launch

- Fill the placeholders in `backend/app/legal/` and have a lawyer review them.
- Appoint the Grievance Officer and publish their contact.
- Configure SMTP in production.
- DigiLocker guardian verification (see Children).
