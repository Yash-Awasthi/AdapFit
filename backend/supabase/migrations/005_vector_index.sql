-- ============================================================
-- AdapFit: exercise embedding dimension fix + HNSW index
-- ============================================================
-- The embedding column was declared VECTOR(768) in 001_initial_schema.sql,
-- but the local embedding model (sentence-transformers all-MiniLM-L6-v2)
-- produces 384-dimensional vectors. The column was never written, so this
-- is a safe type change rather than a data migration.
--
-- Wrapped because a stock Postgres has no pgvector, in which case the column
-- was never created either and there is nothing here to do.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'exercises' AND column_name = 'embedding'
    ) THEN
        ALTER TABLE exercises ALTER COLUMN embedding TYPE vector(384);
        CREATE INDEX IF NOT EXISTS idx_exercises_embedding ON exercises
            USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);
    ELSE
        RAISE NOTICE 'exercises.embedding does not exist (no pgvector); skipping index.';
    END IF;
END
$$;
