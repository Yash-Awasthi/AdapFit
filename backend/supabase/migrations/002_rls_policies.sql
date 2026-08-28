-- ============================================================
-- AdapFit: Row-Level Security Policies
-- Ensures users can only access their own data
-- ============================================================

-- Enable RLS on all user-scoped tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_baselines ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_recovery_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE hydration_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE sleep_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE body_composition_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_share_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_share_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE prediction_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_templates ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Helper: current user ID from JWT
-- ============================================================
-- In Supabase, auth.uid() returns the authenticated user's UUID
-- For the service role (backend), use a custom claim or bypass RLS

-- ============================================================
-- USERS: can read/update own profile
-- ============================================================
CREATE POLICY "users_select_own" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_update_own" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "users_insert_own" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- ============================================================
-- USER BASELINES: own data only
-- ============================================================
CREATE POLICY "baselines_select_own" ON user_baselines
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "baselines_insert_own" ON user_baselines
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "baselines_update_own" ON user_baselines
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================
-- DAILY RECOVERY LOGS: own data only
-- ============================================================
CREATE POLICY "recovery_select_own" ON daily_recovery_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "recovery_insert_own" ON daily_recovery_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "recovery_update_own" ON daily_recovery_logs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "recovery_delete_own" ON daily_recovery_logs
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- WORKOUTS: own data only
-- ============================================================
CREATE POLICY "workouts_select_own" ON workouts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "workouts_insert_own" ON workouts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "workouts_update_own" ON workouts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "workouts_delete_own" ON workouts
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- WORKOUT EXERCISES: via workout ownership
-- ============================================================
CREATE POLICY "workout_exercises_select_own" ON workout_exercises
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM workouts WHERE workouts.id = workout_exercises.workout_id AND auth.uid() = workouts.user_id)
    );

CREATE POLICY "workout_exercises_insert_own" ON workout_exercises
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM workouts WHERE workouts.id = workout_exercises.workout_id AND auth.uid() = workouts.user_id)
    );

-- ============================================================
-- HYDRATION LOGS: own data only
-- ============================================================
CREATE POLICY "hydration_select_own" ON hydration_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "hydration_insert_own" ON hydration_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "hydration_delete_own" ON hydration_logs
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- MEAL PLANS: own data only
-- ============================================================
CREATE POLICY "meals_select_own" ON meal_plans
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "meals_insert_own" ON meal_plans
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- SLEEP LOGS: own data only
-- ============================================================
CREATE POLICY "sleep_select_own" ON sleep_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "sleep_insert_own" ON sleep_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- BODY COMPOSITION: own data only
-- ============================================================
CREATE POLICY "body_select_own" ON body_composition_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "body_insert_own" ON body_composition_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- GOALS: own data only
-- ============================================================
CREATE POLICY "goals_select_own" ON goals
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "goals_insert_own" ON goals
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "goals_update_own" ON goals
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "goals_delete_own" ON goals
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- ACHIEVEMENTS: own data only
-- ============================================================
CREATE POLICY "achievements_select_own" ON achievements
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "achievements_insert_own" ON achievements
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- WORKOUT SHARES: public reads, own writes
-- ============================================================
CREATE POLICY "shares_select_public" ON workout_shares
    FOR SELECT USING (visibility = 'public' OR auth.uid() = user_id);

CREATE POLICY "shares_insert_own" ON workout_shares
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "shares_delete_own" ON workout_shares
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- SHARE LIKES: public reads, own writes
-- ============================================================
CREATE POLICY "likes_select_own" ON workout_share_likes
    FOR SELECT USING (true);

CREATE POLICY "likes_insert_own" ON workout_share_likes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "likes_delete_own" ON workout_share_likes
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================
-- SHARE COMMENTS: public reads, own writes
-- ============================================================
CREATE POLICY "comments_select_public" ON workout_share_comments
    FOR SELECT USING (true);

CREATE POLICY "comments_insert_own" ON workout_share_comments
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- CHALLENGES: public reads, own progress
-- ============================================================
CREATE POLICY "challenge_participants_select" ON challenge_participants
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "challenge_participants_insert" ON challenge_participants
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "challenge_logs_select_own" ON challenge_logs
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM challenge_participants WHERE challenge_participants.id = challenge_logs.participant_id AND auth.uid() = challenge_participants.user_id)
    );

CREATE POLICY "challenge_logs_insert_own" ON challenge_logs
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM challenge_participants WHERE challenge_participants.id = challenge_logs.participant_id AND auth.uid() = challenge_participants.user_id)
    );

-- ============================================================
-- CHAT: own sessions and messages
-- ============================================================
CREATE POLICY "chat_sessions_select_own" ON chat_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "chat_sessions_insert_own" ON chat_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "chat_messages_select_own" ON chat_messages
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "chat_messages_insert_own" ON chat_messages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- TRAINING SCHEDULE: own data only
-- ============================================================
CREATE POLICY "schedule_select_own" ON training_schedule
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "schedule_insert_own" ON training_schedule
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "schedule_update_own" ON training_schedule
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================
-- NOTIFICATION PREFS: own data only
-- ============================================================
CREATE POLICY "notif_select_own" ON notification_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "notif_insert_own" ON notification_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "notif_update_own" ON notification_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================
-- USER PREFERENCES: own data only
-- ============================================================
CREATE POLICY "prefs_select_own" ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "prefs_insert_own" ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "prefs_update_own" ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================
-- PREDICTION FEEDBACK: own data only
-- ============================================================
CREATE POLICY "feedback_select_own" ON prediction_feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "feedback_insert_own" ON prediction_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- WORKOUT TEMPLATES: own data + builtin for all
-- ============================================================
CREATE POLICY "templates_select" ON workout_templates
    FOR SELECT USING (is_builtin = true OR auth.uid() = user_id);

CREATE POLICY "templates_insert_own" ON workout_templates
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "templates_update_own" ON workout_templates
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "templates_delete_own" ON workout_templates
    FOR DELETE USING (auth.uid() = user_id AND is_builtin = false);

-- ============================================================
-- EXERCISES: public read-only catalog
-- ============================================================
-- Exercises table: read-only for all authenticated users, admin-only writes
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;
CREATE POLICY "exercises_select_all" ON exercises
    FOR SELECT USING (true);
