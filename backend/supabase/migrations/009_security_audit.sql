-- Security audit log, kept 1 year (DPDP Rules; app/core/audit.py purges older rows).
-- user_id is not a foreign key: the record of an erasure must outlive the account.
CREATE TABLE IF NOT EXISTS security_audit (
    id        BIGSERIAL   PRIMARY KEY,
    at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    event     TEXT        NOT NULL,
    user_id   TEXT        NOT NULL DEFAULT '',
    actor_id  TEXT        NOT NULL DEFAULT '',
    ip        TEXT        NOT NULL DEFAULT '',
    details   TEXT        NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS security_audit_user_idx ON security_audit (user_id, at DESC);
CREATE INDEX IF NOT EXISTS security_audit_actor_idx ON security_audit (actor_id, at DESC);
CREATE INDEX IF NOT EXISTS security_audit_at_idx ON security_audit (at);

ALTER TABLE security_audit ENABLE ROW LEVEL SECURITY;
