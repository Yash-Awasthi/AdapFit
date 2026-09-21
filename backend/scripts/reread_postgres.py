"""Re-read a user's data in a fresh process, proving it is in the database."""
import asyncio
import os
import pathlib
import sys

for line in pathlib.Path(".env").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()
sys.path.insert(0, ".")

from app.core.auth import UserManager  # noqa: E402
from app.core.storage import storage  # noqa: E402


async def main(user_id: str, email: str) -> int:
    account = await UserManager().get_user(user_id)
    assert account is not None, "account did not survive the restart"
    assert account["email"] == email, account["email"]

    logs = await storage.get_recovery_logs(user_id, 28)
    assert len(logs) == 7, f"expected 7 recovery logs, found {len(logs)}"

    baseline = await storage.get_baseline(user_id)
    assert baseline is not None, "baseline was not persisted"

    print(f"re-read in a new process: {account['email']}, {len(logs)} recovery logs, "
          f"baseline HRV {baseline['hrv_mean_rmssd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1], sys.argv[2])))
