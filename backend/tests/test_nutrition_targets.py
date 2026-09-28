"""Nutrition targets come from the user's profile, or are absent."""
import asyncio

from fastapi.testclient import TestClient

from app.api.v1.endpoints.body_composition import measurements
from app.core.storage import storage
from app.main import app

c = TestClient(app)


def test_no_profile_means_no_targets():
    t = c.get("/api/v1/nutrition/targets?user_id=nt-empty").json()
    assert t["status"] == "insufficient_data" and "weight_kg" in t["missing"]
    d = c.get("/api/v1/nutrition/daily?user_id=nt-empty").json()
    assert d["calorie_target"] is None and d["remaining_calories"] is None


def test_targets_follow_the_profile():
    uid = "nt-full"
    asyncio.run(storage.create_user({"id": uid, "email": "nt@example.com", "age": 30, "gender": "male",
                                     "height_cm": 175, "primary_goal": "fat_loss", "preferred_days_per_week": 4}))
    measurements.setdefault(uid, []).append({"weight_kg": 80})
    t = c.get(f"/api/v1/nutrition/targets?user_id={uid}").json()
    # Mifflin-St Jeor male 80 kg / 175 cm / 30 y = 1749 kcal; x1.55 x0.85 = 2304
    assert t["basis"]["bmr"] == 1749 and abs(t["calories"] - 2304) <= 2
    assert t["protein_g"] > 100


def test_macro_mismatch_is_flagged():
    r = c.post("/api/v1/nutrition/meals?user_id=nt-meal", json={
        "name": "Dal rice", "calories": 900, "protein_g": 15, "carbs_g": 60, "fat_g": 10, "meal_type": "lunch"}).json()
    assert r["energy_check"] and "390" in r["energy_check"]
