"""Convert the yuhonas/free-exercise-db (873 exercises, public domain) into
AdapFit's schema and merge with the existing catalog (keeping stable ids).

Run from backend/:  python scripts/build_exercise_db.py
"""
import json
import re
import unicodedata
from pathlib import Path

SRC = Path("scripts/free_exercises.json")
OLD = Path("app/data/exercises.json")
OUT = Path("app/data/exercises.json")

# Muscle mapping (free-exercise-db -> AdapFit canonical)
MUSCLE_MAP = {
    "abdominals": "core",
    "abductors": "glutes",
    "adductors": "inner_thighs",
    "biceps": "biceps",
    "calves": "calves",
    "chest": "chest",
    "forearms": "forearms",
    "glutes": "glutes",
    "hamstrings": "hamstrings",
    "lats": "back",
    "lower_back": "lower_back",
    "middle_back": "back",
    "neck": "neck",
    "quadriceps": "quadriceps",
    "traps": "traps",
    "triceps": "triceps",
    "shoulders": "shoulders",
    "cardio": "cardio",
    "full_body": "full_body",
}

# Category mapping
CATEGORY_MAP = {
    "strength": "strength",
    "stretching": "stretching",
    "cardio": "cardio",
    "plyometrics": "cardio",
    "powerlifting": "strength",
    "strongman": "strength",
    "olympic_weightlifting": "strength",
}

# Equipment mapping
EQUIPMENT_MAP = {
    "body_only": "bodyweight",
    "dumbbell": "dumbbells",
    "barbell": "barbell",
    "kettlebells": "kettlebells",
    "cable": "cables",
    "machine": "machine",
    "bands": "bands",
    "medicine_ball": "medicine_ball",
    "exercise_ball": "stability_ball",
    "foam_roll": "foam_roll",
    "e-z_curl_bar": "ez_bar",
    "other": "other",
    "none": "bodyweight",
}

# Axial loading heuristic by muscle/mechanic
HIGH_AXIAL = {"lower_back", "traps", "quadriceps", "hamstrings", "glutes"}


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def axial_rating(primary_muscles: list[str], mechanic: str) -> int:
    if mechanic == "isolation":
        return 1
    if any(m in HIGH_AXIAL for m in primary_muscles):
        return 4 if mechanic != "isolation" else 2
    return 2 if mechanic != "isolation" else 1


def main():
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    print(f"Source exercises: {len(raw)}")

    old = json.loads(OLD.read_text(encoding="utf-8"))
    old_map = {e["id"]: e for e in old}
    print(f"Existing exercises: {len(old)}")

    converted = []
    seen_ids = set()
    for ex in raw:
        name = ex.get("name", "").strip()
        if not name:
            continue
        ex_id = ex.get("id") or slugify(name)
        if ex_id in seen_ids:
            ex_id = f"{ex_id}-{len(seen_ids)}"
        seen_ids.add(ex_id)

        primary = [MUSCLE_MAP.get(m, m.replace("_", " ")) for m in (ex.get("primaryMuscles") or ["full_body"])]
        secondary = [MUSCLE_MAP.get(m, m.replace("_", " ")) for m in (ex.get("secondaryMuscles") or [])]

        images = ex.get("images", []) or []
        gif_url = None
        if images:
            img = images[0]
            if img.startswith("http"):
                gif_url = img
            else:
                gif_url = f"https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{img}"

        category = CATEGORY_MAP.get(ex.get("category", ""), "strength")
        equipment = EQUIPMENT_MAP.get(ex.get("equipment", ""), "bodyweight")
        mechanic = ex.get("mechanic") or ("compound" if category == "strength" else "isolation")

        converted.append({
            "id": ex_id,
            "name": name,
            "category": category,
            "primary_muscles": primary,
            "secondary_muscles": secondary,
            "equipment": equipment,
            "mechanic": mechanic,
            "instructions": ex.get("instructions") or [],
            "gif_url": gif_url,
            "axial_loading_rating": axial_rating(primary, mechanic),
        })

    # Merge: existing entries first (stable ids), then new ones not duplicated by id
    merged = []
    merged_ids = set()
    for e in old:
        merged.append(e)
        merged_ids.add(e["id"])

    added = 0
    for e in converted:
        if e["id"] not in merged_ids:
            merged.append(e)
            merged_ids.add(e["id"])
            added += 1

    # Fix relative gif urls in old entries (free-exercise-db images are relative)
    for e in merged:
        url = e.get("gif_url")
        if url and not url.startswith("http"):
            e["gif_url"] = f"https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{url}"

    OUT.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(merged)} exercises to {OUT} (+{added} new from free-exercise-db)")


if __name__ == "__main__":
    main()