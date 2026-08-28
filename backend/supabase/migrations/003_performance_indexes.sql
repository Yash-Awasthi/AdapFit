-- ============================================================
-- AdapFit: Performance Indexes
-- Following Supabase Postgres best practices
-- ============================================================

-- ============================================================
-- Composite indexes for common query patterns
-- ============================================================

-- Recovery logs: user's recent history (most common query)
CREATE INDEX IF NOT EXISTS idx_recovery_user_date_desc
    ON daily_recovery_logs(user_id, log_date DESC)
    INCLUDE (recovery_score, readiness_state, hrv_rmssd);

-- Workouts: user's workout history by date
CREATE INDEX IF NOT EXISTS idx_workouts_user_date_completed
    ON workouts(user_id, target_date DESC, completed);

-- Workout exercises: join lookup
CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout
    ON workout_exercises(workout_id)
    INCLUDE (exercise_id, sets, target_reps, completed);

-- Hydration: daily aggregation
CREATE INDEX IF NOT EXISTS idx_hydration_user_date_amt
    ON hydration_logs(user_id, log_date DESC)
    INCLUDE (amount_ml, drink_type);

-- Sleep logs: user history
CREATE INDEX IF NOT EXISTS idx_sleep_user_date
    ON sleep_logs(user_id, log_date DESC)
    INCLUDE (duration_hours, quality_score);

-- Body composition: trend queries
CREATE INDEX IF NOT EXISTS idx_body_user_date_weight
    ON body_composition_logs(user_id, log_date DESC)
    INCLUDE (weight_kg, body_fat_pct);

-- Training schedule: weekly calendar view
CREATE INDEX IF NOT EXISTS idx_schedule_user_date_status
    ON training_schedule(user_id, schedule_date, status)
    INCLUDE (workout_type, title);

-- Goals: active goals per user
CREATE INDEX IF NOT EXISTS idx_goals_user_status
    ON goals(user_id, status)
    WHERE status = 'active';

-- Chat messages: conversation history
CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages(session_id, created_at);

-- Community feed: public shares sorted by date
CREATE INDEX IF NOT EXISTS idx_shares_public_date
    ON workout_shares(visibility, shared_at DESC)
    WHERE visibility = 'public';

-- Challenge participants: leaderboard queries
CREATE INDEX IF NOT EXISTS idx_challenge_participants
    ON challenge_participants(challenge_id, progress DESC)
    INCLUDE (user_id, streak_current);

-- ============================================================
-- Partial indexes for filtered queries (smaller, faster)
-- ============================================================

-- Active challenges only
CREATE INDEX IF NOT EXISTS idx_challenges_active
    ON fitness_challenges(category)
    WHERE is_builtin = true;

-- User preferences: fast lookup by user
CREATE INDEX IF NOT EXISTS idx_user_preferences_user
    ON user_preferences(user_id, pref_key)
    INCLUDE (pref_value, confidence);

-- ============================================================
-- GIN indexes for array/JSONB columns
-- ============================================================

-- Exercise muscle groups search
CREATE INDEX IF NOT EXISTS idx_exercises_muscles_gin
    ON exercises USING GIN (primary_muscles);

-- User equipment access
CREATE INDEX IF NOT EXISTS idx_users_equipment_gin
    ON users USING GIN (equipment_access);

-- ============================================================
-- BRIN index for time-series data (very compact)
-- ============================================================

-- Daily recovery logs: time-range scans
CREATE INDEX IF NOT EXISTS idx_recovery_logs_brin_date
    ON daily_recovery_logs USING BRIN (log_date)
    WITH (pages_per_range = 32);
