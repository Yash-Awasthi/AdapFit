"""Replace hardcoded 'default' user ids with useUserStore userId in mobile screens.

Run from repo root: python backend/scripts/fix_user_ids.py
"""
import re
from pathlib import Path

MOBILE = Path("mobile")

# (file, import path to stores from that file)
FILES = [
    ("app/(tabs)/achievements.tsx", "../../src/stores"),
    ("app/(tabs)/chat.tsx", "../../src/stores"),
    ("app/(tabs)/cycle.tsx", "../../src/stores"),
    ("app/(tabs)/index.tsx", "../../src/stores"),
    ("app/(tabs)/nutrition.tsx", "../../src/stores"),
    ("app/(tabs)/periodization.tsx", "../../src/stores"),
    ("app/(tabs)/sleep.tsx", "../../src/stores"),
    ("app/(tabs)/social.tsx", "../../src/stores"),
    ("app/(tabs)/trends.tsx", "../../src/stores"),
    ("app/(tabs)/wellness.tsx", "../../src/stores"),
    ("app/(tabs)/workout.tsx", "../../src/stores"),
    ("app/checkin.tsx", "../src/stores"),
    ("app/workout-detail.tsx", "../src/stores"),
    ("src/components/ActivityFeed.tsx", "../stores"),
    ("src/components/MusicPlayer.tsx", "../stores"),
    ("src/components/NotificationSetup.tsx", "../stores"),
]

for rel, import_path in FILES:
    p = MOBILE / rel
    if not p.exists():
        print(f"SKIP (missing): {rel}")
        continue
    src = p.read_text(encoding="utf-8")
    orig = src
    changed = False

    # 1. Add import { useUserStore } if not present
    if "useUserStore" not in src:
        lines = src.split("\n")
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, f"import {{ useUserStore }} from '{import_path}';")
        src = "\n".join(lines)
        changed = True

    # 2. Add `const userId = useUserStore((s) => s.userId);` inside the component
    if "useUserStore((s) => s.userId)" not in src:
        m = re.search(r"(export default function \w+\([^)]*\) \{\n)", src)
        if m:
            src = src[: m.end()] + "  const userId = useUserStore((s) => s.userId);\n" + src[m.end():]
            changed = True

    # 3. Targeted replacements (never touch function default params)
    src = src.replace("user_id=default", "user_id=${userId}")
    src = src.replace("user_id: 'default'", "user_id: userId")
    src = src.replace("user_id: \"default\"", "user_id: userId")
    # api.xxx('default', ...) -> api.xxx(userId, ...)
    src = re.sub(r"(api\.\w+\()'default'", r"\1userId", src)
    # fetch(`...user_id=default...`) handled above; fetch('.../users', ...) not applicable
    # 'default' as first arg to api helpers in template strings
    src = re.sub(r"(\$\{API\}/api/v1/\w+[^`]*?user_id=)default", r"\1${userId}", src)

    if src != orig:
        changed = True

    if changed:
        p.write_text(src, encoding="utf-8")
        print(f"UPDATED: {rel}")
    else:
        print(f"no-op: {rel}")