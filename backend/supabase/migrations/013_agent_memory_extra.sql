-- ============================================================
-- AdapFit: agent memory keys without their own column
--
-- Mood logs, thought records and questionnaire history live in agent memory.
-- Postgres had no column for them, so they were dropped on save.
-- ============================================================

ALTER TABLE agent_memory ADD COLUMN IF NOT EXISTS extra JSONB NOT NULL DEFAULT '{}'::jsonb;
