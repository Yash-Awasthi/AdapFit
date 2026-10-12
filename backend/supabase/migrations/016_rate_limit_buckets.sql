-- Request rate limits shared by every API worker: one token bucket per caller
-- and route class, read and written under a row lock. Times are epoch seconds.
CREATE TABLE IF NOT EXISTS rate_limit_buckets (
    key        TEXT PRIMARY KEY,
    tokens     DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS rate_limit_buckets_updated_idx ON rate_limit_buckets (updated_at);
