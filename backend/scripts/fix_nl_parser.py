"""Add \b before exercise-name groups so names can't start mid-word ("or" inside "for")."""
from pathlib import Path

PATH = Path("app/services/nl_workout_logger.py")
src = PATH.read_text(encoding="utf-8")

old = "r'((?!at\\b|with\\b|for\\b|rpe\\b)[a-zA-Z]+"
new = "r'\\b((?!at\\b|with\\b|for\\b|rpe\\b)[a-zA-Z]+"
count = src.count(old)
if count == 0:
    raise SystemExit("name pattern not found")
src = src.replace(old, new)
PATH.write_text(src, encoding="utf-8")
print(f"patched {count} name patterns")