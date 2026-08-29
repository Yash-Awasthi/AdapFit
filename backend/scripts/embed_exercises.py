"""Populate the Postgres `exercises` table with the exercise catalog and its embeddings.

This is the pgvector index build step: it runs once (or whenever
app/data/exercises.json changes), not on every server boot. Requires
DATABASE_URL and sentence-transformers to be installed.

Run from backend/:  python scripts/embed_exercises.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.db import close_pool, get_pool
from app.services.exercise_service import exercise_service
from app.services.vector_store import embed, exercise_text

UPSERT_SQL = """
    INSERT INTO exercises (id, name, category, primary_muscles, secondary_muscles,
        equipment, mechanics, axial_loading_rating, gif_url, instructions, embedding)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        category = EXCLUDED.category,
        primary_muscles = EXCLUDED.primary_muscles,
        secondary_muscles = EXCLUDED.secondary_muscles,
        equipment = EXCLUDED.equipment,
        mechanics = EXCLUDED.mechanics,
        axial_loading_rating = EXCLUDED.axial_loading_rating,
        gif_url = EXCLUDED.gif_url,
        instructions = EXCLUDED.instructions,
        embedding = EXCLUDED.embedding
"""


async def main() -> None:
    if not settings.DATABASE_URL:
        raise SystemExit("DATABASE_URL is not set; nothing to embed into.")

    pool = await get_pool()
    exercises = exercise_service.get_all()
    print(f"Embedding {len(exercises)} exercises into Postgres...")

    async with pool.acquire() as conn:
        for ex in exercises:
            vector = embed(exercise_text(ex.model_dump()))
            await conn.execute(
                UPSERT_SQL,
                ex.id, ex.name, ex.category, ex.primary_muscles, ex.secondary_muscles,
                ex.equipment, ex.mechanic, ex.axial_loading_rating, ex.gif_url,
                ex.instructions, vector,
            )

    await close_pool()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
