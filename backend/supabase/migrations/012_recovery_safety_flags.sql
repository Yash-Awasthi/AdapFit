-- ============================================================
-- AdapFit: keep the check-in fields the daily decision reads
--
-- Pain and illness force a rest day, and the resting heart rate delta raises
-- an illness caution. Without these columns Postgres dropped them on insert.
-- ============================================================

ALTER TABLE daily_recovery_logs ADD COLUMN IF NOT EXISTS pain_flagged BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE daily_recovery_logs ADD COLUMN IF NOT EXISTS illness_flagged BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE daily_recovery_logs ADD COLUMN IF NOT EXISTS resting_hr_delta NUMERIC(4,1);
