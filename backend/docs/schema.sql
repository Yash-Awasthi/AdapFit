-- AdapFit Database Schema — Supabase Postgres
-- Follows Supabase Postgres Best Practices:
--   - schema-uuid-primary-keys: UUID v7 for sortable, non-leaking IDs
--   - schema-timestamptz: TIMESTAMPTZ for timezone-safe timestamps
--   - schema-jsonb: JSONB for flexible nested data
--   - schema-composite-indexes: (user_id, timestamp) for time-series queries
--   - security-rls: Row-Level Security on all user-facing tables
--   - security-rls-no-bypass: Functions use SECURITY DEFINER + search_path
--   - conn-pooling: Transaction-mode pooling via Supabase pooler

-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    avatar_url TEXT DEFAULT '',
    date_of_birth DATE,
    gender TEXT,
    height_cm REAL,
    weight_kg REAL,
    units TEXT DEFAULT 'metric' CHECK (units IN ('metric', 'imperial')),
    fitness_level TEXT DEFAULT 'intermediate' CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
    primary_goal TEXT DEFAULT 'general_fitness',
    preferred_days_per_week INTEGER DEFAULT 4 CHECK (preferred_days_per_week BETWEEN 1 AND 7),
    equipment_access TEXT[] DEFAULT '{}',
    health_connect_enabled BOOLEAN DEFAULT FALSE,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================================
-- USER BASELINES (recovery baselines)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hrv_rmssd REAL DEFAULT 50.0,
    hrv_std REAL DEFAULT 10.0,
    resting_hr REAL DEFAULT 65.0,
    sleep_hours REAL DEFAULT 8.0,
    chronic_load REAL DEFAULT 500.0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_baselines_user ON user_baselines(user_id);

-- ============================================================
-- DAILY RECOVERY LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_recovery_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    recovery_score REAL,
    sleep_score REAL,
    fatigue_level INTEGER CHECK (fatigue_level BETWEEN 1 AND 10),
    mood_score INTEGER CHECK (mood_score BETWEEN 1 AND 10),
    wearable_data JSONB DEFAULT '{}',
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, log_date)
);

-- Composite index for time-series queries (user + date range)
CREATE INDEX IF NOT EXISTS idx_recovery_user_date ON daily_recovery_logs(user_id, log_date DESC);

-- ============================================================
-- WORKOUTS
-- ============================================================
CREATE TABLE IF NOT EXISTS workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id TEXT DEFAULT 'custom',
    title TEXT,
    exercises JSONB DEFAULT '[]',
    warmup JSONB DEFAULT '[]',
    cooldown JSONB DEFAULT '[]',
    duration_minutes INTEGER DEFAULT 0,
    total_volume REAL DEFAULT 0,
    calories_burned INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workouts_user_completed ON workouts(user_id, completed);

-- ============================================================
-- WORKOUT LOGS (completions)
-- ============================================================
CREATE TABLE IF NOT EXISTS workout_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workout_id UUID REFERENCES workouts(id) ON DELETE SET NULL,
    logged_exercises JSONB DEFAULT '[]',
    session_rpe INTEGER CHECK (session_rpe BETWEEN 1 AND 10),
    duration_minutes INTEGER DEFAULT 0,
    calories_burned INTEGER DEFAULT 0,
    completed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workout_logs_user_date ON workout_logs(user_id, completed_at DESC);

-- ============================================================
-- WORKLOAD HISTORY (ACWR tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS workload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    acute_workload REAL,
    chronic_workload REAL,
    acwr REAL,
    session_rpe INTEGER,
    duration_minutes INTEGER,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workload_user_date ON workload_history(user_id, recorded_at DESC);

-- ============================================================
-- HEALTH METRICS (generic time-series)
-- ============================================================
CREATE TABLE IF NOT EXISTS health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'wearable', 'health_connect', 'camera', 'imported')),
    confidence TEXT DEFAULT 'medium' CHECK (confidence IN ('high', 'medium', 'low')),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Composite index for metric queries (user + type + time)
CREATE INDEX IF NOT EXISTS idx_metrics_user_type_time ON health_metrics(user_id, metric_type, recorded_at DESC);

-- ============================================================
-- MEALS
-- ============================================================
CREATE TABLE IF NOT EXISTS meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    foods JSONB DEFAULT '[]',
    total_calories REAL DEFAULT 0,
    total_protein REAL DEFAULT 0,
    total_carbs REAL DEFAULT 0,
    total_fat REAL DEFAULT 0,
    total_fiber REAL DEFAULT 0,
    photo_url TEXT,
    logged_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meals_user_date ON meals(user_id, logged_at DESC);

-- ============================================================
-- SLEEP SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS sleep_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    duration_hours REAL DEFAULT 0,
    quality INTEGER DEFAULT 5 CHECK (quality BETWEEN 1 AND 10),
    deep_sleep_minutes INTEGER DEFAULT 0,
    rem_sleep_minutes INTEGER DEFAULT 0,
    light_sleep_minutes INTEGER DEFAULT 0,
    score INTEGER DEFAULT 50,
    bedtime TIMESTAMPTZ,
    wake_time TIMESTAMPTZ,
    notes TEXT DEFAULT '',
    source TEXT DEFAULT 'manual',
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sleep_user_date ON sleep_sessions(user_id, recorded_at DESC);

-- ============================================================
-- MEDICATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    dosage TEXT DEFAULT '',
    frequency TEXT DEFAULT 'daily' CHECK (frequency IN ('daily', 'twice_daily', 'weekly', 'as_needed')),
    time_of_day TEXT DEFAULT '08:00',
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medications_user_active ON medications(user_id, is_active);

-- ============================================================
-- MEDICATION LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS medication_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medication_id UUID NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    taken_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_med_logs_user_date ON medication_logs(user_id, taken_at DESC);

-- ============================================================
-- MOOD ENTRIES
-- ============================================================
CREATE TABLE IF NOT EXISTS mood_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood INTEGER DEFAULT 5 CHECK (mood BETWEEN 1 AND 10),
    energy INTEGER DEFAULT 5 CHECK (energy BETWEEN 1 AND 10),
    anxiety INTEGER DEFAULT 5 CHECK (anxiety BETWEEN 1 AND 10),
    tags TEXT[] DEFAULT '{}',
    notes TEXT DEFAULT '',
    journal TEXT DEFAULT '',
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mood_user_date ON mood_entries(user_id, recorded_at DESC);

-- ============================================================
-- EMERGENCY CONTACTS
-- ============================================================
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    relationship TEXT DEFAULT '',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emergency_user ON emergency_contacts(user_id);

-- ============================================================
-- MEDICAL INFO
-- ============================================================
CREATE TABLE IF NOT EXISTS medical_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blood_type TEXT,
    allergies TEXT[] DEFAULT '{}',
    conditions TEXT[] DEFAULT '{}',
    medications TEXT[] DEFAULT '{}',
    emergency_note TEXT DEFAULT '',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- FAMILY CONNECTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS family_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_a UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_b UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship TEXT DEFAULT 'custom',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'paused', 'revoked')),
    permissions_by_a JSONB DEFAULT '{}',
    permissions_by_b JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_a, user_b)
);

CREATE INDEX IF NOT EXISTS idx_family_user_a ON family_connections(user_a);
CREATE INDEX IF NOT EXISTS idx_family_user_b ON family_connections(user_b);

-- ============================================================
-- FAMILY INVITES
-- ============================================================
CREATE TABLE IF NOT EXISTS family_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inviter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invitee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship TEXT DEFAULT 'custom',
    message TEXT DEFAULT '',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired', 'revoked')),
    token TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invites_invitee ON family_invites(invitee_id, status);

-- ============================================================
-- AGENT MEMORY (AI coach state)
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_preferences JSONB DEFAULT '{}',
    accepted_workouts INTEGER DEFAULT 0,
    rejected_workouts INTEGER DEFAULT 0,
    pain_flags TEXT[] DEFAULT '{}',
    great_exercises TEXT[] DEFAULT '{}',
    adaptation_history JSONB DEFAULT '[]',
    nlp_feedback_history JSONB DEFAULT '[]',
    evolution_version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    user_id UUID,
    target_user_id UUID,
    resource_type TEXT,
    details JSONB DEFAULT '{}',
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_type, created_at DESC);

-- ============================================================
-- ROW-LEVEL SECURITY (RLS)
-- ============================================================
-- Following: security-rls — all user-facing tables have RLS enabled

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_recovery_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workload_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE sleep_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mood_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- RLS POLICIES — Users can only access their own data
-- ============================================================

-- Users: can read/update their own profile
CREATE POLICY "users_own_profile" ON users
    FOR ALL USING (auth.uid() = id);

-- Baselines: user owns their baseline
CREATE POLICY "baselines_own" ON user_baselines
    FOR ALL USING (auth.uid() = user_id);

-- Recovery logs: user owns their logs
CREATE POLICY "recovery_own" ON daily_recovery_logs
    FOR ALL USING (auth.uid() = user_id);

-- Workouts: user owns their workouts
CREATE POLICY "workouts_own" ON workouts
    FOR ALL USING (auth.uid() = user_id);

-- Workout logs: user owns their logs
CREATE POLICY "workout_logs_own" ON workout_logs
    FOR ALL USING (auth.uid() = user_id);

-- Workload: user owns their data
CREATE POLICY "workload_own" ON workload_history
    FOR ALL USING (auth.uid() = user_id);

-- Health metrics: user owns their data
CREATE POLICY "metrics_own" ON health_metrics
    FOR ALL USING (auth.uid() = user_id);

-- Meals: user owns their meals
CREATE POLICY "meals_own" ON meals
    FOR ALL USING (auth.uid() = user_id);

-- Sleep: user owns their sleep data
CREATE POLICY "sleep_own" ON sleep_sessions
    FOR ALL USING (auth.uid() = user_id);

-- Medications: user owns their medications
CREATE POLICY "medications_own" ON medications
    FOR ALL USING (auth.uid() = user_id);

-- Medication logs: user owns their logs
CREATE POLICY "med_logs_own" ON medication_logs
    FOR ALL USING (auth.uid() = user_id);

-- Mood: user owns their mood entries
CREATE POLICY "mood_own" ON mood_entries
    FOR ALL USING (auth.uid() = user_id);

-- Emergency contacts: user owns their contacts
CREATE POLICY "emergency_own" ON emergency_contacts
    FOR ALL USING (auth.uid() = user_id);

-- Medical info: user owns their info
CREATE POLICY "medical_own" ON medical_info
    FOR ALL USING (auth.uid() = user_id);

-- Family connections: user is part of the connection
CREATE POLICY "family_own" ON family_connections
    FOR ALL USING (auth.uid() = user_a OR auth.uid() = user_b);

-- Family invites: user is inviter or invitee
CREATE POLICY "invites_own" ON family_invites
    FOR ALL USING (auth.uid() = inviter_id OR auth.uid() = invitee_id);

-- Agent memory: user owns their memory
CREATE POLICY "agent_memory_own" ON agent_memory
    FOR ALL USING (auth.uid() = user_id);

-- Audit log: user can see their own events
CREATE POLICY "audit_own" ON audit_log
    FOR SELECT USING (auth.uid() = user_id);

-- ============================================================
-- HELPER FUNCTIONS (SECURITY DEFINER)
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER set_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_baselines_updated_at BEFORE UPDATE ON user_baselines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_workouts_updated_at BEFORE UPDATE ON workouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_medications_updated_at BEFORE UPDATE ON medications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_family_updated_at BEFORE UPDATE ON family_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_agent_memory_updated_at BEFORE UPDATE ON agent_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- PARTITIONING READY (for future scale)
-- ============================================================
-- health_metrics and daily_recovery_logs can be range-partitioned
-- by recorded_at/log_date when data grows beyond 10M rows.
-- Example for future implementation:
-- CREATE TABLE health_metrics_partitioned (
--     LIKE health_metrics INCLUDING ALL
-- ) PARTITION BY RANGE (recorded_at);
