"""
Apply supabase/migrations/*.sql to DATABASE_URL, in filename order.

The compose file feeds the same directory to Postgres' initdb, but initdb only
runs on an empty data volume. This applies them to a database that already
exists — a second developer's machine, or a new migration added later.

Every migration is written to be re-runnable (IF NOT EXISTS / DO blocks), and
the ones that have been applied are recorded in schema_migrations so a rerun is
cheap as well as safe.

    python -m scripts.apply_migrations            # apply what is pending
    python -m scripts.apply_migrations --list     # show status, change nothing
"""
import asyncio
import os
import sys
from pathlib import Path

import asyncpg

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "supabase" / "migrations"

LEDGER = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW()
)
"""


async def main(list_only: bool = False) -> int:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL is not set. Point it at the database to migrate.", file=sys.stderr)
        return 2

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"No migrations found in {MIGRATIONS_DIR}", file=sys.stderr)
        return 2

    conn = await asyncpg.connect(url)
    try:
        await conn.execute(LEDGER)
        applied = {r["filename"] for r in await conn.fetch("SELECT filename FROM schema_migrations")}

        for path in files:
            if path.name in applied:
                print(f"  ok      {path.name}")
                continue
            if list_only:
                print(f"  pending {path.name}")
                continue
            print(f"  apply   {path.name}")
            # One transaction per migration: a failure leaves the database on
            # the last complete migration rather than halfway through this one.
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute("INSERT INTO schema_migrations (filename) VALUES ($1)", path.name)
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(list_only="--list" in sys.argv)))
