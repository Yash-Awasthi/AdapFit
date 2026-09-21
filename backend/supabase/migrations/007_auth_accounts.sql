-- ============================================================
-- AdapFit: credentials on the users table
--
-- Accounts previously lived only in the API process, so every restart
-- dropped every registration. The auth columns join the profile row rather
-- than forming a second table, so one user_id addresses both the login and
-- the fitness profile it personalizes.
-- ============================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS weight_kg NUMERIC(5,1);
ALTER TABLE users ADD COLUMN IF NOT EXISTS units TEXT DEFAULT 'metric';
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

-- Case-insensitive uniqueness: "Alice" and "alice" are one account.
CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_key ON users (LOWER(username));
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_key ON users (LOWER(email));

-- Login reads by email on every request that is not already token-bearing.
CREATE INDEX IF NOT EXISTS users_active_idx ON users (is_active) WHERE is_active;

-- Refresh tokens survive a restart, so a deploy does not sign everyone out.
-- Only the hash is stored: the table is useless to anyone who reads it.
CREATE TABLE IF NOT EXISTS user_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS user_sessions_expires_idx ON user_sessions (expires_at);
CREATE INDEX IF NOT EXISTS user_sessions_user_idx ON user_sessions (user_id);
