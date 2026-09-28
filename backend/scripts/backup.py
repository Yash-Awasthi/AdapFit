"""
Postgres backup and restore that keeps erasures erased.

    python -m scripts.backup dump DIR            pg_dump into DIR, drop files older than 30 days
    python -m scripts.backup restore DUMP        pg_restore DUMP, then replay erasure events
                                                 logged after it was taken

Each dump gets an erasure ledger beside it (account ids and times, no health
data). A restore replays events newer than the dump from the live database
when it is reachable, and from the ledgers of every dump beside it, so an
account erased after the backup is erased again. pg_dump and pg_restore must
be on PATH (or PG_BIN) and DATABASE_URL must point at the database.
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import asyncpg

RETENTION_DAYS = 30
EVENTS = ("deletion_requested", "deletion_cancelled", "account_erased")
_LEDGER_SQL = ("SELECT extract(epoch FROM at) AS at, event, user_id FROM security_audit "
               "WHERE event = ANY($1::text[]) ORDER BY at")


def _bin(name: str) -> str:
    return str(Path(os.environ["PG_BIN"]) / name) if os.getenv("PG_BIN") else name


async def _ledger(url: str) -> list:
    conn = await asyncpg.connect(url)
    try:
        return [[float(r["at"]), r["event"], r["user_id"]] for r in await conn.fetch(_LEDGER_SQL, list(EVENTS))]
    finally:
        await conn.close()


def dump(directory: Path, url: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = directory / f"adapfit-{stamp}.dump"
    subprocess.run([_bin("pg_dump"), "--format=custom", "--no-owner", f"--file={target}", url], check=True)
    ledger = {"taken_at": time.time(), "events": asyncio.run(_ledger(url))}
    target.with_suffix(".ledger.json").write_text(json.dumps(ledger))
    cutoff = time.time() - RETENTION_DAYS * 86400
    for old in directory.glob("adapfit-*"):
        if old.stat().st_mtime < cutoff:
            old.unlink()
    return target


def pending_erasures(taken_at: float, event_lists: list) -> dict:
    """user id -> last erasure event after taken_at, across every source."""
    latest: dict = {}
    for at, event, uid in sorted(e for events in event_lists for e in events):
        if at > taken_at and uid:
            latest[uid] = event
    return {uid: event for uid, event in latest.items() if event != "deletion_cancelled"}


async def replay(todo: dict) -> None:
    import app.main  # noqa: F401  registers every feature holder, so erasure reaches all of them
    from app.core import durable, privacy
    from app.core.auth import user_manager

    await user_manager.load()
    await durable.load_all()
    for uid, event in todo.items():
        if event == "account_erased":
            await user_manager.delete_user(uid)
        else:
            privacy.request_deletion(uid, reason="user")  # full grace again: the original due time is not logged
    await durable.flush()


def restore(target: Path, url: str) -> dict:
    taken_at = json.loads(target.with_suffix(".ledger.json").read_text())["taken_at"]
    sources = [json.loads(p.read_text())["events"] for p in target.parent.glob("adapfit-*.ledger.json")]
    try:
        sources.append(asyncio.run(_ledger(url)))
    except Exception as exc:
        print(f"live database unreadable ({exc}); using ledgers in {target.parent} only", file=sys.stderr)
    todo = pending_erasures(taken_at, sources)
    subprocess.run([_bin("pg_restore"), "--clean", "--if-exists", "--no-owner", "--exit-on-error",
                    f"--dbname={url}", str(target)], check=True)
    asyncio.run(replay(todo))
    return todo


if __name__ == "__main__":
    url = os.environ["DATABASE_URL"]
    if sys.argv[1:2] == ["dump"] and len(sys.argv) == 3:
        print(dump(Path(sys.argv[2]), url))
    elif sys.argv[1:2] == ["restore"] and len(sys.argv) == 3:
        print("erasures replayed:", restore(Path(sys.argv[2]), url))
    else:
        raise SystemExit(__doc__)
