-- ============================================================
-- AdapFit: exercise embedding dimension fix + HNSW index
-- ============================================================
-- The embedding column was declared VECTOR(768) in 001_initial_schema.sql,
-- but the local embedding model (sentence-transformers all-MiniLM-L6-v2)
-- produces 384-dimensional vectors. The column was never written, so this
-- is a safe type change rather than a data migration.

ALTER TABLE exercises ALTER COLUMN embedding TYPE VECTOR(384);

CREATE INDEX IF NOT EXISTS idx_exercises_embedding ON exercises
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);
