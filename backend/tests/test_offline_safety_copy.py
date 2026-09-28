"""The app's offline first-aid and red-flag copy matches the server's."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from export_offline_safety import OUT, build  # noqa: E402


def test_bundled_copy_is_current():
    assert OUT.read_text(encoding="utf-8") == build(), "run: python scripts/export_offline_safety.py"
