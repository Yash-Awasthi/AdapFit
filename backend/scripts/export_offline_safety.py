"""
Writes mobile/src/data/offlineSafety.json: first-aid protocols and the fixed
red-flag replies, so the app can show them with no connection.

    python scripts/export_offline_safety.py

tests/test_offline_safety_copy.py fails when the bundled copy drifts.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OUT = Path(__file__).resolve().parents[2] / "mobile" / "src" / "data" / "offlineSafety.json"


def build() -> str:
    from app.services import safety_policy as sp
    from app.services.first_aid import first_aid_service

    data = {
        "protocols": first_aid_service.emergency_protocols,
        "medical": {"patterns": sp._MEDICAL_RED_FLAGS, "reply": sp.triage("chest pain")["reply"]},
        "self_harm": {"patterns": sp._SELF_HARM, "reply": sp.triage("suicide")["reply"]},
    }
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
