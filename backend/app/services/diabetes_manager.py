"""
Diabetes Management — Blood glucose tracking, insulin logging, carb counting

Features:
- Blood glucose logging with context (fasting, pre/post meal, bedtime)
- Insulin dose tracking (type, units, injection site)
- Carb counting with food database
- Time-in-range (TIR) analysis
- HbA1c estimation from glucose data
- Hypoglycemia/hyperglycemia alerts
- Pattern analysis (dawn phenomenon, post-meal spikes)
- CGM integration ready
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field


FOOD_CARB_DATABASE = [
    {"name": "White Bread", "carbs_per_serving": 15, "serving": "1 slice"},
    {"name": "Brown Rice", "carbs_per_serving": 45, "serving": "1 cup cooked"},
    {"name": "Pasta", "carbs_per_serving": 43, "serving": "1 cup cooked"},
    {"name": "Apple", "carbs_per_serving": 25, "serving": "1 medium"},
    {"name": "Banana", "carbs_per_serving": 27, "serving": "1 medium"},
    {"name": "Orange", "carbs_per_serving": 12, "serving": "1 medium"},
    {"name": "Oatmeal", "carbs_per_serving": 27, "serving": "1 cup cooked"},
    {"name": "Milk", "carbs_per_serving": 12, "serving": "1 cup"},
    {"name": "Yogurt", "carbs_per_serving": 17, "serving": "1 cup"},
    {"name": "Potato", "carbs_per_serving": 37, "serving": "1 medium"},
    {"name": "Sweet Potato", "carbs_per_serving": 27, "serving": "1 medium"},
    {"name": "Corn", "carbs_per_serving": 19, "serving": "1 ear"},
    {"name": "Beans (cooked)", "carbs_per_serving": 45, "serving": "1 cup"},
    {"name": "Lentils", "carbs_per_serving": 40, "serving": "1 cup cooked"},
    {"name": "Quinoa", "carbs_per_serving": 39, "serving": "1 cup cooked"},
    {"name": "Cereal", "carbs_per_serving": 30, "serving": "1 cup"},
    {"name": "Grapes", "carbs_per_serving": 27, "serving": "1 cup"},
    {"name": "Watermelon", "carbs_per_serving": 11, "serving": "1 cup"},
    {"name": "Pizza", "carbs_per_serving": 35, "serving": "2 slices"},
    {"name": "Burger Bun", "carbs_per_serving": 24, "serving": "1 bun"},
    {"name": "Tortilla", "carbs_per_serving": 22, "serving": "1 medium"},
    {"name": "Honey", "carbs_per_serving": 17, "serving": "1 tbsp"},
    {"name": "Jam", "carbs_per_serving": 13, "serving": "1 tbsp"},
    {"name": "Coke", "carbs_per_serving": 39, "serving": "1 can"},
    {"name": "Orange Juice", "carbs_per_serving": 26, "serving": "1 cup"},
]

INSULIN_TYPES = [
    {"type": "Rapid-acting", "brands": ["Humalog", "NovoLog", "Apidra"], "onset": "15 min", "peak": "1-2 hours", "duration": "3-5 hours"},
    {"type": "Short-acting", "brands": ["Regular insulin"], "onset": "30 min", "peak": "2-4 hours", "duration": "6-8 hours"},
    {"type": "Intermediate-acting", "brands": ["NPH"], "onset": "2-4 hours", "peak": "4-10 hours", "duration": "10-16 hours"},
    {"type": "Long-acting", "brands": ["Lantus", "Levemir", "Tresiba"], "onset": "1-2 hours", "peak": "Minimal peak", "duration": "20-42 hours"},
    {"type": "Mixed", "brands": ["Humalog Mix", "NovoMix"], "onset": "15-30 min", "Dual peak": "1-12 hours", "duration": "12-18 hours"},
]


class DiabetesManagerService:
    """Comprehensive diabetes management."""

    def __init__(self):
        self._glucose_readings: list[dict] = []
        self._insulin_logs: list[dict] = []
        self._carb_logs: list[dict] = []
        self._meals: list[dict] = []

    def log_glucose(self, value_mgdl: int, context: str = "fasting", notes: str = "") -> dict:
        if value_mgdl < 54:
            level = "severe_hypo"
            alert = "SEVERE HYPOGLYCEMIA! Consume 15g fast-acting carbs immediately."
        elif value_mgdl < 70:
            level = "hypo"
            alert = "Low blood sugar. Eat 15g carbs and recheck in 15 minutes."
        elif value_mgdl <= 180:
            level = "in_range"
            alert = "Blood glucose is in target range."
        elif value_mgdl <= 250:
            level = "high"
            alert = "Blood glucose is elevated. Check for ketones if Type 1."
        else:
            level = "severe_high"
            alert = "Very high blood glucose. Seek medical attention."

        reading = {"value": value_mgdl, "context": context, "notes": notes, "level": level, "alert": alert, "timestamp": time.time()}
        self._glucose_readings.append(reading)
        return {"logged": True, "value": value_mgdl, "level": level, "alert": alert, "context": context}

    def get_glucose_readings(self, hours: int = 24) -> list[dict]:
        cutoff = time.time() - hours * 3600
        return [r for r in self._glucose_readings if r["timestamp"] > cutoff]

    def get_glucose_summary(self) -> dict:
        if not self._glucose_readings:
            return {"message": "No glucose data yet"}
        values = [r["value"] for r in self._glucose_readings[-50:]]
        avg = sum(values) / len(values)
        in_range = sum(1 for v in values if 70 <= v <= 180) / len(values) * 100
        hypo = sum(1 for v in values if v < 70)
        hyper = sum(1 for v in values if v > 180)
        estimated_a1c = round((avg + 46.7) / 28.7, 1)
        return {
            "average_glucose": round(avg),
            "time_in_range": round(in_range, 1),
            "hypo_episodes": hypo,
            "hyper_episodes": hyper,
            "estimated_hba1c": estimated_a1c,
            "readings_count": len(self._glucose_readings),
            "target_range": "70-180 mg/dL",
            "in_range_target": "70%+",
        }

    def log_insulin(self, insulin_type: str, units: float, site: str = "abdomen", notes: str = "") -> dict:
        entry = {"type": insulin_type, "units": units, "site": site, "notes": notes, "timestamp": time.time()}
        self._insulin_logs.append(entry)
        return {"logged": True, "insulin": insulin_type, "units": units, "site": site}

    def get_insulin_history(self, days: int = 7) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [i for i in self._insulin_logs if i["timestamp"] > cutoff]

    def get_insulin_types(self) -> list[dict]:
        return INSULIN_TYPES

    def log_carbs(self, food_name: str, carbs: float, meal_type: str = "snack") -> dict:
        entry = {"food": food_name, "carbs": carbs, "meal_type": meal_type, "timestamp": time.time()}
        self._carb_logs.append(entry)
        return {"logged": True, "carbs": carbs, "food": food_name}

    def search_food_carbs(self, query: str) -> list[dict]:
        q = query.lower()
        return [f for f in FOOD_CARB_DATABASE if q in f["name"].lower()]

    def get_carb_summary(self) -> dict:
        if not self._carb_logs:
            return {"total_carbs": 0, "meals": 0}
        total = sum(c["carbs"] for c in self._carb_logs)
        return {"total_carbs": round(total), "meals_logged": len(self._carb_logs), "avg_per_meal": round(total / max(1, len(self._carb_logs)))}

    def get_patterns(self) -> list[dict]:
        patterns = []
        readings = self._glucose_readings[-20:]
        if len(readings) >= 5:
            fasting = [r for r in readings if r["context"] == "fasting"]
            if fasting:
                avg_fasting = sum(r["value"] for r in fasting) / len(fasting)
                if avg_fasting > 130:
                    patterns.append({"pattern": "Elevated Fasting Glucose", "value": round(avg_fasting), "message": "Fasting glucose consistently above 130 mg/dL. Discuss medication adjustment with your doctor."})
            post_meal = [r for r in readings if r["context"] == "post_meal"]
            if post_meal:
                avg_post = sum(r["value"] for r in post_meal) / len(post_meal)
                if avg_post > 200:
                    patterns.append({"pattern": "Post-Meal Spikes", "value": round(avg_post), "message": "Post-meal glucose frequently above 200 mg/dL. Consider reducing carb intake or adjusting insulin."})
            all_values = [r["value"] for r in readings]
            if max(all_values) - min(all_values) > 100:
                patterns.append({"pattern": "High Variability", "message": "Large glucose swings detected. Consider more consistent meal timing and carb counting."})
        return patterns if patterns else [{"pattern": "No patterns detected", "message": "Keep logging to identify patterns over time."}]

    def get_carb_database(self) -> list[dict]:
        return FOOD_CARB_DATABASE


diabetes_manager_service = DiabetesManagerService()
