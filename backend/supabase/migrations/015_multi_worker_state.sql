-- Several API workers share feature state and sessions.
--
-- feature_state rows take a new sequence number on every write: a worker reads
-- the rows changed since the highest number it has seen, and writes a row only
-- if its number is still the one it read (otherwise it merges and retries).
-- An empty payload marks a deleted row, so other workers learn of the deletion.
CREATE SEQUENCE IF NOT EXISTS feature_state_seq;
ALTER TABLE feature_state ADD COLUMN IF NOT EXISTS seq BIGINT;
UPDATE feature_state SET seq = nextval('feature_state_seq') WHERE seq IS NULL;
ALTER TABLE feature_state ALTER COLUMN seq SET DEFAULT nextval('feature_state_seq');
ALTER TABLE feature_state ALTER COLUMN seq SET NOT NULL;
CREATE INDEX IF NOT EXISTS feature_state_seq_idx ON feature_state (seq);

-- Access tokens issued before this moment (epoch seconds) are void: sessions
-- ended by a password change, suspension or a reused refresh token.
ALTER TABLE users ADD COLUMN IF NOT EXISTS sessions_revoked_at DOUBLE PRECISION;

-- Refresh tokens already exchanged. Presenting one again means a copy leaked,
-- and every session of its owner is ended. Only the hash is stored.
CREATE TABLE IF NOT EXISTS rotated_refresh_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS rotated_refresh_tokens_expires_idx ON rotated_refresh_tokens (expires_at);
