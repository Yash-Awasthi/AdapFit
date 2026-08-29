-- ============================================================
-- AdapFit: diet_plans table + workouts.warmup/cooldown columns
-- ============================================================

CREATE TABLE IF NOT EXISTS diet_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

ALTER TABLE workouts ADD COLUMN IF NOT EXISTS warmup JSONB DEFAULT '[]'::jsonb;
ALTER TABLE workouts ADD COLUMN IF NOT EXISTS cooldown JSONB DEFAULT '[]'::jsonb;
