-- ============================================================
-- AdapFit: mark when a profile was completed
--
-- Accounts live in the users table, so a row exists from sign-up with the
-- column defaults. The profile counts as present only once onboarding has
-- written it; until then GET /users/{id} answers 404 and the app onboards.
-- ============================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarded_at TIMESTAMPTZ;

-- Rows that already carry a name went through onboarding before this column existed.
UPDATE users SET onboarded_at = COALESCE(updated_at, created_at) WHERE onboarded_at IS NULL AND name IS NOT NULL;
