-- ============================================================
-- AdapFit: keep the whole generated workout
--
-- Warm-up, cool-down and each exercise's rest, image and notes had no
-- columns, so a workout read back from Postgres lost them.
-- ============================================================

ALTER TABLE workouts ADD COLUMN IF NOT EXISTS warmup JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE workouts ADD COLUMN IF NOT EXISTS cooldown JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE workout_exercises ADD COLUMN IF NOT EXISTS rest_seconds INT;
ALTER TABLE workout_exercises ADD COLUMN IF NOT EXISTS gif_url TEXT;
ALTER TABLE workout_exercises ADD COLUMN IF NOT EXISTS notes TEXT;
