"""
Skin Health Tracking — Mole monitoring, AI skin analysis, dermatology

Features:
- Mole/lesion tracking with photos
- ABCDE analysis (Asymmetry, Border, Color, Diameter, Evolution)
- Skin type assessment (Fitzpatrick scale)
- UV exposure tracking
- Skin cancer risk assessment
- Dermatologist-ready reports
- Seasonal skin care recommendations
- Product recommendations by skin type
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


FITZPATRICK_SCALE = {
    1: {"type": "I", "description": "Very light, always burns, never tans", "risk": "very_high", "sunscreen": "SPF 50+", "color": "#FFF5EE"},
    2: {"type": "II", "description": "Light, usually burns, tans minimally", "risk": "high", "sunscreen": "SPF 50", "color": "#FFE4C4"},
    3: {"type": "III", "description": "Medium, sometimes burns, tans gradually", "risk": "moderate", "sunscreen": "SPF 30-50", "color": "#DEB887"},
    4: {"type": "IV", "description": "Olive, rarely burns, tans easily", "risk": "low_moderate", "sunscreen": "SPF 30", "color": "#D2B48C"},
    5: {"type": "V", "description": "Brown, very rarely burns, tans very easily", "risk": "low", "sunscreen": "SPF 15-30", "color": "#8B7355"},
    6: {"type": "VI", "description": "Dark brown/black, never burns", "risk": "low", "sunscreen": "SPF 15-30", "color": "#654321"},
}


class SkinHealthService:
    """Skin health monitoring and mole tracking."""

    def __init__(self):
        self._moles: dict[str, dict] = {}
        self._skin_type: Optional[dict] = None
        self._uv_log: list[dict] = []
        self._photos: list[dict] = []

    def assess_skin_type(self, Fitzpatrick_answers: dict) -> dict:
        score = Fitzpatrick_answers.get("skin_color", 3) + Fitzpatrick_answers.get("sun_reaction", 3) + Fitzpatrick_answers.get("tanning_ability", 3)
        skin_type = min(6, max(1, (score - 3) // 2 + 1))
        self._skin_type = {**FITZPATRICK_SCALE[skin_type], "level": skin_type}
        return {"skin_type": self._skin_type, "recommendations": self._get_care_recommendations(skin_type)}

    def _get_care_recommendations(self, skin_type: int) -> list[str]:
        recs = [f"Use {FITZPATRICK_SCALE[skin_type]['sunscreen']} daily"]
        if skin_type <= 2:
            recs.extend(["Seek shade during 10 AM - 4 PM", "Wear UV-protective clothing", "Monthly full-body skin checks", "Annual dermatologist visit"])
        elif skin_type <= 4:
            recs.extend(["Daily sunscreen even on cloudy days", "Check moles quarterly", "Be aware of changing spots"])
        else:
            recs.extend(["Protect against hyperpigmentation", "Moisturize regularly", "Check for acral moles (palms, soles)"])
        return recs

    def add_mole(self, name: str, body_location: str, size_mm: float, color: str = "brown", notes: str = "") -> dict:
        mole_id = f"mole_{secrets.token_hex(6)}"
        mole = {
            "id": mole_id, "name": name, "body_location": body_location,
            "size_mm": size_mm, "color": color, "notes": notes,
            "created_at": time.time(), "last_checked": time.time(),
            "photos": [], "abcde_score": self._calculate_abcde(size_mm, color),
            "status": "stable",
        }
        self._moles[mole_id] = mole
        return {"mole": mole, "message": f"Mole '{name}' added. Track it monthly for changes."}

    def _calculate_abcde(self, size_mm: float, color: str, features: Optional[dict] = None) -> dict:
        """
        Only criteria something measured. Asymmetry, border and colour come from
        a photo measurement; without one they are None, not guessed from size.
        """
        f = features or {}
        a = None if f.get("asymmetry_score") is None else int(f["asymmetry_score"] >= 0.5)
        b = None if f.get("border_irregularity") is None else int(f["border_irregularity"] >= 0.5)
        c = None if f.get("color_variation") is None else int(f["color_variation"] >= 0.4)
        d = int(size_mm > 6)
        met = sum(x for x in (a, b, c, d) if x)
        assessed = sum(x is not None for x in (a, b, c, d))
        return {"asymmetry": a, "border": b, "color_irregularity": c, "diameter": d, "evolution": 0,
                "total": met, "assessed": assessed,
                "risk_level": "low" if met == 0 else "moderate" if met == 1 else "high"}

    # A mole growing by more than this between checks is the change that
    # matters most — the "E" in ABCDE — and is worth acting on by itself.
    NOTABLE_GROWTH_MM = 2.0

    # A jump this large on the 0-1 photo scales between checks counts as change.
    NOTABLE_FEATURE_CHANGE = 0.2

    def record_measurement(
        self, mole_id: str, size_mm: Optional[float], color: str = "", notes: str = "",
        features: Optional[dict] = None,
    ) -> dict:
        """
        Record a fresh measurement of a mole and compare it with the last.

        This replaced an "analysis" that returned symmetry 85, border 80 and
        "overall risk: low" for every mole, whatever it looked like — a fixed
        reassuring result about skin cancer, for a photo nothing examined.
        What a phone can genuinely do is track change over time, which is what
        this does.
        """
        mole = self._moles.get(mole_id)
        if not mole:
            return {"error": "Mole not found"}
        if size_mm is None and features is None:
            return {"error": "A measured size in millimetres is required."}
        if size_mm is not None and (not isinstance(size_mm, (int, float)) or size_mm <= 0):
            return {"error": "A measured size in millimetres is required."}

        previous_size = mole["size_mm"]
        previous_color = mole.get("color", "")
        previous_features = mole.get("features") or {}
        growth = round(size_mm - previous_size, 1) if size_mm is not None else 0.0

        if size_mm is not None:
            mole["size_mm"] = float(size_mm)
        if color:
            mole["color"] = color
        if features:
            mole["features"] = features
        mole["abcde_score"] = self._calculate_abcde(mole["size_mm"], mole.get("color", ""), mole.get("features"))
        mole["last_checked"] = time.time()

        changes = []
        if growth >= self.NOTABLE_GROWTH_MM:
            changes.append(f"Grew {growth} mm since the last measurement")
        if color and previous_color and color.lower() != previous_color.lower():
            changes.append(f"Colour changed from {previous_color} to {color}")
        labels = {"asymmetry_score": "Shape became less even", "border_irregularity": "Edge became more irregular",
                  "color_variation": "Colour became more varied"}
        for key, label in labels.items():
            before, now = previous_features.get(key), (features or {}).get(key)
            if before is not None and now is not None and now - before >= self.NOTABLE_FEATURE_CHANGE:
                changes.append(label)
        if changes:
            mole["abcde_score"]["evolution"] = 1
            mole["abcde_score"]["total"] += 1

        entry = {
            "mole_id": mole_id,
            "size_mm": mole["size_mm"],
            "color": mole.get("color", ""),
            "growth_mm": growth,
            "changes": changes,
            "features": features,
            "notes": notes,
            "timestamp": time.time(),
        }
        self._photos.append(entry)

        return {
            "recorded": True,
            "size_mm": mole["size_mm"],
            "growth_mm": growth,
            "changes": changes,
            "abcde_assessment": mole["abcde_score"],
            "recommendation": (
                "This mole has changed. Have a clinician look at it."
                if changes else
                "No change recorded since the last measurement. Keep checking."
            ),
            "disclaimer": (
                "ABCDE is a prompt to get a mole looked at, from the size and colour you "
                "recorded. It does not diagnose or rule out skin cancer."
            ),
        }

    def get_mole_history(self, mole_id: str) -> list[dict]:
        """Every measurement recorded for one mole, oldest first."""
        return [entry for entry in self._photos if entry.get("mole_id") == mole_id]

    def log_uv_exposure(self, uv_index: int, duration_minutes: int, protection_used: str = "none") -> dict:
        entry = {"uv_index": uv_index, "duration_minutes": duration_minutes, "protection": protection_used, "timestamp": time.time()}
        self._uv_log.append(entry)
        risk = "low" if uv_index <= 2 else "moderate" if uv_index <= 5 else "high" if uv_index <= 7 else "very_high"
        return {"logged": True, "risk_level": risk, "recommendation": self._get_uv_recommendation(uv_index, duration_minutes, protection_used)}

    def _get_uv_recommendation(self, uv: int, minutes: int, protection: str) -> str:
        if uv >= 8:
            return "Very high UV! Avoid sun 10 AM-4 PM. Wear protective clothing and SPF 50+."
        elif uv >= 6:
            return "High UV. Limit outdoor time to 15-20 min without protection. Apply sunscreen."
        elif uv >= 3:
            return "Moderate UV. Seek shade during midday. Wear sunglasses."
        return "Low UV. Safe for outdoor activities with standard precautions."

    def get_uv_history(self, days: int = 7) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [u for u in self._uv_log if u["timestamp"] > cutoff]

    def get_all_moles(self) -> list[dict]:
        return list(self._moles.values())

    def get_mole(self, mole_id: str) -> Optional[dict]:
        return self._moles.get(mole_id)

    def get_skin_cancer_risk(self) -> dict:
        skin_type_risk = self._skin_type.get("risk", "unknown") if self._skin_type else "unknown"
        mole_count = len(self._moles)
        high_risk_moles = sum(1 for m in self._moles.values() if m["abcde_score"]["total"] >= 3)
        uv_exposure = len(self._uv_log)
        return {
            "overall_risk": "high" if skin_type_risk in ["very_high", "high"] or high_risk_moles > 0 else "moderate" if mole_count > 20 or skin_type_risk == "moderate" else "low",
            "skin_type_risk": skin_type_risk,
            "mole_count": mole_count,
            "high_risk_moles": high_risk_moles,
            "uv_exposure_sessions": uv_exposure,
            "recommendations": [
                "Monthly self-examination of all moles" if mole_count > 0 else "Start tracking any new or changing spots",
                "Yearly skin check by a dermatologist" if skin_type_risk in ["very_high", "high"] else "Show a dermatologist any spot that changes",
                "Daily sunscreen application",
                "Wear protective clothing and sunglasses",
            ],
            "disclaimer": "This assessment is for informational purposes. Consult a dermatologist for professional evaluation.",
        }

    def get_dermatology_report(self) -> dict:
        return {
            "report_date": time.strftime("%Y-%m-%d"),
            "skin_type": self._skin_type,
            "total_moles": len(self._moles),
            "moles_tracked": [{"name": m["name"], "location": m["body_location"], "size": m["size_mm"], "abcde": m["abcde_score"], "status": m["status"]} for m in self._moles.values()],
            "uv_exposure_summary": {"total_sessions": len(self._uv_log), "avg_uv_index": round(sum(u["uv_index"] for u in self._uv_log) / max(1, len(self._uv_log)), 1)},
            "risk_assessment": self.get_skin_cancer_risk(),
            "disclaimer": "Your own records and photo measurements, to share with a dermatologist. Not a diagnosis.",
        }


from app.core.per_user import per_user, register

skin_health_service = register("skin_health.skin_health_service", per_user(SkinHealthService))