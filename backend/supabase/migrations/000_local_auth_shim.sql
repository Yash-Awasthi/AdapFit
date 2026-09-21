-- ============================================================
-- AdapFit: auth.uid() for a plain Postgres server
--
-- The RLS policies in 002 are written for Supabase, where auth.uid() returns
-- the caller's UUID from the verified JWT. A vanilla Postgres has no such
-- function, so every policy in that file fails to parse and the whole schema
-- stops applying. This supplies the same function from a session setting.
--
-- On Supabase this file is a no-op: the auth schema already exists there and
-- its own auth.uid() is not replaced.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS auth;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'auth' AND p.proname = 'uid'
    ) THEN
        EXECUTE $fn$
            CREATE FUNCTION auth.uid() RETURNS uuid
            LANGUAGE sql STABLE
            -- Pinned search_path: a SECURITY-sensitive helper must not resolve
            -- names through whatever the caller has set.
            SET search_path = pg_catalog
            AS $body$
                SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid
            $body$;
        $fn$;
    END IF;
END
$$;
