-- Feature data that the app keeps in memory and writes through after each change.
-- One row per (feature, user) for per-user services, one per feature for shared
-- services, and one per key for module-level stores. Payloads are pickled
-- snapshots restored with an allowlisting unpickler (app/core/durable.py).
CREATE TABLE IF NOT EXISTS feature_state (
    namespace   TEXT        NOT NULL,
    key         TEXT        NOT NULL,
    payload     BYTEA       NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (namespace, key)
);

CREATE INDEX IF NOT EXISTS feature_state_key_idx ON feature_state (key);

ALTER TABLE feature_state ENABLE ROW LEVEL SECURITY;
