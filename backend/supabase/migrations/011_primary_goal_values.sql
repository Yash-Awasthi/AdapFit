-- ============================================================
-- AdapFit: primary_goal values match the API
--
-- The API (and onboarding) send 'general_fitness'; the column only allowed
-- 'general', so every profile save with that goal failed on Postgres.
-- ============================================================

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_primary_goal_check;
UPDATE users SET primary_goal = 'general_fitness' WHERE primary_goal = 'general';
ALTER TABLE users ALTER COLUMN primary_goal SET DEFAULT 'general_fitness';
ALTER TABLE users ADD CONSTRAINT users_primary_goal_check
    CHECK (primary_goal IN ('strength', 'hypertrophy', 'endurance', 'fat_loss', 'general_fitness'));
