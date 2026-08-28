"""Replace hardcoded API/WS base URLs with imports from src/services/config.

Run from repo root: python backend/scripts/fix_api_urls.py
"""
import re
from pathlib import Path

MOBILE = Path("mobile")

# (file relative to mobile/, import path from that file to src/services/config)
FILES = [
    ("app/workout-detail.tsx", "../src/services/config"),
    ("app/workout-complete.tsx", "../src/services/config"),
    ("app/checkin.tsx", "../src/services/config"),
    ("app/(tabs)/achievements.tsx", "../../src/services/config"),
    ("app/(tabs)/chat.tsx", "../../src/services/config"),
    ("app/(onboarding)/index.tsx", "../../src/services/config"),
    ("app/(tabs)/index.tsx", "../../src/services/config"),
    ("app/(tabs)/exercises.tsx", "../../src/services/config"),
    ("app/(tabs)/profile.tsx", "../../src/services/config"),
    ("app/(tabs)/wellness.tsx", "../../src/services/config"),
    ("app/(tabs)/periodization.tsx", "../../src/services/config"),
    ("app/(tabs)/diet.tsx", "../../src/services/config"),
    ("app/(tabs)/health.tsx", "../../src/services/config"),
    ("app/(tabs)/nutrition.tsx", "../../src/services/config"),
    ("app/(tabs)/sleep.tsx", "../../src/services/config"),
    ("app/(tabs)/social.tsx", "../../src/services/config"),
    ("app/(tabs)/settings.tsx", "../../src/services/config"),
    ("src/components/ActivityFeed.tsx", "../services/config"),
    ("src/components/PersonalBestsWall.tsx", "../services/config"),
    ("src/components/NotificationSetup.tsx", "../services/config"),
    ("src/components/MusicPlayer.tsx", "../services/config"),
    ("src/stores/recoveryStore.ts", "../services/config"),
]

API_LITERAL = "http://10.0.2.2:8000"
WS_LITERAL = "ws://10.0.2.2:8000"

for rel, import_path in FILES:
    p = MOBILE / rel
    if not p.exists():
        print(f"SKIP (missing): {rel}")
        continue
    src = p.read_text(encoding="utf-8")
    orig = src
    changed = False

    # Replace const API = 'http://10.0.2.2:8000';
    src = re.sub(
        r"const API = ['\"]http://10\.0\.2\.2:8000['\"];",
        "const API = API_BASE_URL;",
        src,
    )
    # Replace const WS_URL = 'ws://10.0.2.2:8000';
    src = re.sub(
        r"const WS_URL = ['\"]ws://10\.0\.2\.2:8000['\"];",
        "const WS_URL = WS_BASE_URL;",
        src,
    )
    # Replace inline fetch('http://10.0.2.2:8000/...')
    src = src.replace(f"'{API_LITERAL}/", "`${API_BASE_URL}/").replace(f'"{API_LITERAL}/', "`${API_BASE_URL}/")
    src = re.sub(r"`\$\{API_BASE_URL\}/([^`]*?)'", r"`${API_BASE_URL}/\1`", src)

    if src != orig:
        changed = True

    # Add import if we now reference API_BASE_URL/WS_BASE_URL but don't import it
    needs_import = ("API_BASE_URL" in src or "WS_BASE_URL" in src) and "from '" not in src.split("\n")[0] if False else (
        ("API_BASE_URL" in src or "WS_BASE_URL" in src)
        and f"from '{import_path}'" not in src
    )
    if needs_import:
        # Insert after the first import line
        lines = src.split("\n")
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        names = []
        if "API_BASE_URL" in src:
            names.append("API_BASE_URL")
        if "WS_BASE_URL" in src:
            names.append("WS_BASE_URL")
        lines.insert(insert_at, f"import {{ {', '.join(names)} }} from '{import_path}';")
        src = "\n".join(lines)
        changed = True

    if changed:
        p.write_text(src, encoding="utf-8")
        print(f"UPDATED: {rel}")
    else:
        print(f"no-op: {rel}")