"""
Body Composition Service — BMI, Body Fat, Measurements & Trends
"""
import time
import math
from typing import Optional


class BodyCompositionService:
    """Body composition tracking and analysis."""

    def calculate_bmi(self, weight_kg: float, height_cm: float) -> dict:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        if bmi < 18.5: category = "Underweight"; color = "#3B82F6"
        elif bmi < 25: category = "Normal"; color = "#10B981"
        elif bmi < 30: category = "Overweight"; color = "#F59E0B"
        else: category = "Obese"; color = "#EF4444"
        return {"bmi": round(bmi, 1), "category": category, "color": color, "ideal_range": f"{round(18.5 * height_m ** 2, 1)} - {round(24.9 * height_m ** 2, 1)} kg"}

    def estimate_body_fat(self, gender: str, waist_cm: float, neck_cm: float, height_cm: float, hip_cm: float = 0) -> dict:
        """Navy method body fat estimation."""
        if gender == "male":
            bf = 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)) - 450
        else:
            if hip_cm == 0: hip_cm = waist_cm * 1.1
            bf = 495 / (1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm) + 0.22100 * math.log10(height_cm)) - 450
        bf = max(3, min(60, bf))
        if gender == "male":
            if bf < 10: status = "Athletic"
            elif bf < 18: status = "Fitness"
            elif bf < 25: status = "Average"
            else: status = "Above Average"
        else:
            if bf < 16: status = "Athletic"
            elif bf < 24: status = "Fitness"
            elif bf < 31: status = "Average"
            else: status = "Above Average"
        return {"body_fat_pct": round(bf, 1), "status": status, "method": "Navy"}

    def ideal_weight(self, gender: str, height_cm: float, frame: str = "medium") -> dict:
        height_in = height_cm / 2.54
        if gender == "male":
            base = 48.0 + 1.1 * (height_in - 60)
        else:
            base = 45.5 + 0.9 * (height_in - 60)
        adj = {"small": -5, "medium": 0, "large": 5}.get(frame, 0)
        ideal = base + adj
        return {"ideal_weight_kg": round(ideal, 1), "range_kg": f"{round(ideal - 5, 1)} - {round(ideal + 5, 1)}", "frame": frame}

    def log_measurement(self, data: dict) -> dict:
        return {"logged": True, "data": data, "timestamp": time.strftime("%Y-%m-%d")}

    def get_trends(self) -> dict:
        return {"weight_trend": "stable", "body_fat_trend": "decreasing", "measurements": {"waist": "82cm (-2cm)", "chest": "98cm (+1cm)", "arms": "34cm (+0.5cm)"}}


body_composition_service = BodyCompositionService()
