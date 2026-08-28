-- ============================================================
-- AdapFit: Supabase PostgreSQL Initial Schema Migration
-- 36 domain modules, UUID PKs, pgvector embeddings
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- pgvector: CREATE EXTENSION IF NOT EXISTS vector;  -- run after enabling in Supabase dashboard

-- ============================================================
-- 1. USERS & BASELINES
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    name TEXT,
    age INT CHECK (age > 0 AND age < 150),
    weight_kg NUMERIC(5,1) CHECK (weight_kg > 0),
    height_cm NUMERIC(5,1) CHECK (height_cm > 0),
    sex TEXT CHECK (sex IN ('male', 'female', 'other')),
    fitness_level TEXT CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')) DEFAULT 'intermediate',
    primary_goal TEXT CHECK (primary_goal IN ('strength', 'hypertrophy', 'endurance', 'fat_loss', 'general')) DEFAULT 'general',
    equipment_access TEXT[] DEFAULT ARRAY['bodyweight', 'dumbbells', 'barbell'],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_baselines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    baseline_hrv_rmssd NUMERIC(6,2),
    baseline_rhr NUMERIC(4,1),
    baseline_sleep_score NUMERIC(4,1),
    chronic_load_28d NUMERIC(8,2) DEFAULT 500,
    chronic_load_7d NUMERIC(8,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- 2. RECOVERY & BIOMETRICS
-- ============================================================

CREATE TABLE IF NOT EXISTS daily_recovery_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    hrv_rmssd NUMERIC(6,2),
    resting_heart_rate NUMERIC(4,1),
    sleep_score NUMERIC(4,1),
    sleep_duration_hours NUMERIC(4,2),
    soreness_score INT CHECK (soreness_score >= 1 AND soreness_score <= 5),
    fatigue_score INT CHECK (fatigue_score >= 1 AND fatigue_score <= 5),
    stress_score INT CHECK (stress_score >= 1 AND stress_score <= 5),
    sore_muscle_groups TEXT[],
    readiness_state TEXT CHECK (readiness_state IN ('OPTIMAL', 'MODERATE', 'REDUCED', 'DEPLETED')),
    recovery_score NUMERIC(5,1) CHECK (recovery_score >= 0 AND recovery_score <= 100),
    steps INT CHECK (steps >= 0),
    active_calories NUMERIC(7,1) CHECK (active_calories >= 0),
    water_intake_ml INT CHECK (water_intake_ml >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, log_date)
);

CREATE INDEX IF NOT EXISTS idx_recovery_user_date ON daily_recovery_logs(user_id, log_date DESC);

-- ============================================================
-- 3. WORKOUTS & EXERCISES
-- ============================================================

CREATE TABLE IF NOT EXISTS workouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    target_date DATE,
    readiness_state TEXT,
    recovery_score NUMERIC(5,1),
    adaptation_rationale TEXT,
    target_duration_minutes INT DEFAULT 45,
    actual_duration_minutes INT,
    session_rpe NUMERIC(3,1),
    acwr_before NUMERIC(4,2),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, target_date DESC);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL,
    exercise_name TEXT,
    target_muscle TEXT,
    sets INT DEFAULT 3,
    target_reps TEXT,
    target_rpe NUMERIC(3,1),
    actual_weight NUMERIC(6,1),
    actual_reps INT,
    actual_rpe NUMERIC(3,1),
    axial_loading_rating INT CHECK (axial_loading_rating >= 1 AND axial_loading_rating <= 5),
    order_index INT DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS exercises (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT CHECK (category IN ('strength', 'stretching', 'cardio')),
    primary_muscles TEXT[] DEFAULT '{}',
    secondary_muscles TEXT[] DEFAULT '{}',
    equipment TEXT,
    mechanics TEXT CHECK (mechanics IN ('isolation', 'compound')),
    axial_loading_rating INT CHECK (axial_loading_rating >= 1 AND axial_loading_rating <= 5),
    gif_url TEXT,
    instructions TEXT[],
    embedding VECTOR(768),  -- pgvector for semantic search
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (run after pgvector is enabled)
-- CREATE INDEX IF NOT EXISTS idx_exercises_embedding ON exercises
--     USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);

-- ============================================================
-- 4. HYDRATION & NUTRITION
-- ============================================================

CREATE TABLE IF NOT EXISTS hydration_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount_ml INT NOT NULL CHECK (amount_ml > 0),
    drink_type TEXT CHECK (drink_type IN ('water', 'tea', 'coffee', 'sports_drink', 'juice', 'milk', 'other')),
    logged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hydration_user_date ON hydration_logs(user_id, log_date DESC);

CREATE TABLE IF NOT EXISTS meal_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_date DATE NOT NULL,
    goal TEXT,
    total_calories NUMERIC(7,1),
    protein_g NUMERIC(6,1),
    carbs_g NUMERIC(6,1),
    fat_g NUMERIC(6,1),
    meals JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. SLEEP
-- ============================================================

CREATE TABLE IF NOT EXISTS sleep_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    duration_hours NUMERIC(4,2),
    quality_score NUMERIC(4,1),
    deep_sleep_minutes INT,
    rem_sleep_minutes INT,
    light_sleep_minutes INT,
    awakenings INT DEFAULT 0,
    bedtime TEXT,
    wake_time TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, log_date)
);

-- ============================================================
-- 6. BODY COMPOSITION & MEASUREMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS body_composition_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    weight_kg NUMERIC(5,1),
    body_fat_pct NUMERIC(4,1),
    muscle_mass_kg NUMERIC(5,1),
    waist_cm NUMERIC(5,1),
    hips_cm NUMERIC(5,1),
    chest_cm NUMERIC(5,1),
    arms_cm NUMERIC(5,1),
    thighs_cm NUMERIC(5,1),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_body_user_date ON body_composition_logs(user_id, log_date DESC);

-- ============================================================
-- 7. GOALS & ACHIEVEMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    goal_type TEXT CHECK (goal_type IN ('strength', 'body_composition', 'consistency', 'habit', 'custom')),
    title TEXT NOT NULL,
    description TEXT,
    target_value NUMERIC(10,2),
    current_value NUMERIC(10,2) DEFAULT 0,
    unit TEXT,
    start_date DATE DEFAULT CURRENT_DATE,
    deadline DATE,
    status TEXT CHECK (status IN ('active', 'achieved', 'expired', 'abandoned')) DEFAULT 'active',
    milestones_achieved INT DEFAULT 0,
    streak_current INT DEFAULT 0,
    streak_best INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    badge_type TEXT NOT NULL,
    badge_name TEXT NOT NULL,
    description TEXT,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, badge_type)
);

-- ============================================================
-- 8. COMMUNITY & SOCIAL
-- ============================================================

CREATE TABLE IF NOT EXISTS workout_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workout_id UUID REFERENCES workouts(id) ON DELETE SET NULL,
    title TEXT,
    summary TEXT,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    visibility TEXT CHECK (visibility IN ('public', 'friends', 'private')) DEFAULT 'public',
    shared_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workout_share_likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    share_id UUID REFERENCES workout_shares(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    liked_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(share_id, user_id)
);

CREATE TABLE IF NOT EXISTS workout_share_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    share_id UUID REFERENCES workout_shares(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 9. FITNESS CHALLENGES
-- ============================================================

CREATE TABLE IF NOT EXISTS fitness_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    challenge_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    target_value NUMERIC(10,2),
    target_unit TEXT,
    duration_days INT,
    category TEXT CHECK (category IN ('strength', 'endurance', 'flexibility', 'consistency')),
    is_builtin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS challenge_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    challenge_id UUID REFERENCES fitness_challenges(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    progress NUMERIC(10,2) DEFAULT 0,
    streak_current INT DEFAULT 0,
    streak_best INT DEFAULT 0,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(challenge_id, user_id)
);

CREATE TABLE IF NOT EXISTS challenge_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    participant_id UUID REFERENCES challenge_participants(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    notes TEXT,
    logged_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(participant_id, log_date)
);

-- ============================================================
-- 10. CONVERSATIONAL MEMORY
-- ============================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    summary TEXT,
    topics TEXT[],
    message_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    intent TEXT,
    entities JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id, created_at DESC);

-- ============================================================
-- 11. TRAINING CALENDAR
-- ============================================================

CREATE TABLE IF NOT EXISTS training_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    schedule_date DATE NOT NULL,
    workout_type TEXT,
    title TEXT,
    target_duration_minutes INT,
    status TEXT CHECK (status IN ('scheduled', 'completed', 'missed', 'skipped')) DEFAULT 'scheduled',
    workout_id UUID REFERENCES workouts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, schedule_date)
);

-- ============================================================
-- 12. NOTIFICATIONS & PREFERENCES
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workout_reminders BOOLEAN DEFAULT TRUE,
    recovery_checkins BOOLEAN DEFAULT TRUE,
    sleep_reminders BOOLEAN DEFAULT TRUE,
    quiet_hours_start TEXT DEFAULT '22:00',
    quiet_hours_end TEXT DEFAULT '07:00',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- 13. USER PREFERENCES (from conversational memory)
-- ============================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    pref_key TEXT NOT NULL,
    pref_value TEXT NOT NULL,
    confidence NUMERIC(3,2) DEFAULT 0.5,
    source TEXT DEFAULT 'inferred',
    confirmed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, pref_key)
);

-- ============================================================
-- 14. PREDICTION FEEDBACK (continuous learning)
-- ============================================================

CREATE TABLE IF NOT EXISTS prediction_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prediction_type TEXT NOT NULL,
    predicted_value NUMERIC(10,2),
    actual_value NUMERIC(10,2),
    rating TEXT CHECK (rating IN ('accurate', 'too_high', 'too_low', 'way_off')),
    feedback_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 15. WORKOUT TEMPLATES
-- ============================================================

CREATE TABLE IF NOT EXISTS workout_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    category TEXT CHECK (category IN ('push', 'pull', 'legs', 'upper', 'lower', 'full_body', 'custom')),
    exercises JSONB DEFAULT '[]',
    is_builtin BOOLEAN DEFAULT FALSE,
    use_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
