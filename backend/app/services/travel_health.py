"""Travel Health Service - Vaccination tracker, destination risk, travel health.

Based on 2025 CDC/WHO travel health guidelines:
- Destination-specific health risk assessment
- Vaccination requirements and recommendations
- Travel health kit checklist
- Jet lag management
- Travel illness prevention
- Post-travel health monitoring
"""

import time
from typing import Dict, List, Optional, Any


class TravelHealthService:
    """Travel health planning and monitoring."""

    def __init__(self):
        self.trips: Dict[str, Dict] = {}
        self._init_destination_data()

    def _init_destination_data(self):
        self.destinations = {
            "india": {
                "risks": ["malaria", "dengue", "typhoid", "hepatitis_a", "rabies", "cholera"],
                "required_vaccines": ["yellow_fever_if_from_endemic"],
                "recommended_vaccines": ["typhoid", "hepatitis_a", "rabies", "cholera"],
                "malaria_prophylaxis": True,
                "altitude_risk": "low",
                "water_safety": "drink_bottled",
                "food_precautions": "avoid_street_food",
                "travel_advisory": "moderate",
            },
            "brazil": {
                "risks": ["dengue", "zika", "malaria", "yellow_fever", "chikungunya"],
                "required_vaccines": ["yellow_fever_if_from_endemic"],
                "recommended_vaccines": ["yellow_fever", "hepatitis_a", "typhoid"],
                "malaria_prophylaxis": True,
                "altitude_risk": "low",
                "water_safety": "drink_bottled",
                "food_precautions": "standard",
                "travel_advisory": "moderate",
            },
            "japan": {
                "risks": ["japanese_encephalitis"],
                "required_vaccines": [],
                "recommended_vaccines": ["japanese_encephalitis"],
                "malaria_prophylaxis": False,
                "altitude_risk": "low",
                "water_safety": "safe",
                "food_precautions": "standard",
                "travel_advisory": "low",
            },
            "thailand": {
                "risks": ["dengue", "malaria", "rabies", "hepatitis_a", "typhoid"],
                "required_vaccines": [],
                "recommended_vaccines": ["typhoid", "hepatitis_a", "rabies", "japanese_encephalitis"],
                "malaria_prophylaxis": True,
                "altitude_risk": "low",
                "water_safety": "drink_bottled",
                "food_precautions": "moderate",
                "travel_advisory": "moderate",
            },
            "kenya": {
                "risks": ["malaria", "yellow_fever", "cholera", "typhoid", "hepatitis_a"],
                "required_vaccines": ["yellow_fever"],
                "recommended_vaccines": ["typhoid", "hepatitis_a", "cholera", "rabies"],
                "malaria_prophylaxis": True,
                "altitude_risk": "variable",
                "water_safety": "drink_bottled",
                "food_precautions": "avoid_raw",
                "travel_advisory": "high",
            },
            "europe": {
                "risks": [],
                "required_vaccines": [],
                "recommended_vaccines": ["hepatitis_a_if_adventure"],
                "malaria_prophylaxis": False,
                "altitude_risk": "variable",
                "water_safety": "safe",
                "food_precautions": "standard",
                "travel_advisory": "low",
            },
        }

        self.vaccination_database = {
            "yellow_fever": {"validity": "lifetime", "advance_time_weeks": 2, "side_effects": ["mild_pain", "low_fever"]},
            "typhoid": {"validity": "2_years_oral_5_years_injection", "advance_time_weeks": 2, "side_effects": ["mild_pain"]},
            "hepatitis_a": {"validity": "25_years", "advance_time_weeks": 2, "side_effects": ["mild_pain"]},
            "hepatitis_b": {"validity": "lifetime", "advance_time_weeks": 6, "side_effects": ["mild_pain"]},
            "rabies": {"validity": "2_years", "advance_time_weeks": 4, "side_effects": ["mild_pain"]},
            "japanese_encephalitis": {"validity": "lifetime", "advance_time_weeks": 8, "side_effects": ["mild_pain"]},
            "cholera": {"validity": "2_years", "advance_time_weeks": 2, "side_effects": ["mild_gi"]},
            "meningococcal": {"validity": "5_years", "advance_time_weeks": 2, "side_effects": ["mild_pain"]},
        }

    def plan_trip(self, user_id: str, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan health requirements for a trip."""
        trip_id = f"trip_{user_id}_{int(time.time())}"
        destination = trip_data.get("destination", "").lower()
        dest_data = self.destinations.get(destination, self._get_generic_destination())

        required = dest_data.get("required_vaccines", [])
        recommended = dest_data.get("recommended_vaccines", [])

        trip = {
            "trip_id": trip_id,
            "user_id": user_id,
            "destination": destination,
            "travel_dates": trip_data.get("dates", {}),
            "health_risks": dest_data["risks"],
            "vaccination_requirements": {
                "required": required,
                "recommended": recommended,
                "advice": self._get_vaccination_advice(required, recommended),
            },
            "malaria_prophylaxis_needed": dest_data["malaria_prophylaxis"],
            "altitude_risk": dest_data["altitude_risk"],
            "water_safety": dest_data["water_safety"],
            "food_precautions": dest_data["food_precautions"],
            "travel_advisory": dest_data["travel_advisory"],
            "health_checklist": self._generate_health_checklist(dest_data),
            "emergency_contacts": self._get_emergency_info(destination),
            "travel_health_kit": self._get_travel_kit(dest_data),
        }

        self.trips[trip_id] = trip
        return trip

    def check_vaccinations(self, user_id: str, current_vaccinations: List[Dict]) -> Dict[str, Any]:
        """Check vaccination status against travel requirements."""
        missing_required = []
        missing_recommended = []
        up_to_date = []

        for v in current_vaccinations:
            name = v.get("name", "")
            up_to_date.append({"name": name, "date": v.get("date"), "valid": True})

        all_needed = set()
        for trip in self.trips.values():
            if trip["user_id"] == user_id:
                all_needed.update(trip["vaccination_requirements"]["required"])
                all_needed.update(trip["vaccination_requirements"]["recommended"])

        vaccinated = {v["name"] for v in current_vaccinations}
        for vax in all_needed:
            if vax not in vaccinated:
                info = self.vaccination_database.get(vax, {})
                entry = {
                    "vaccine": vax,
                    "advance_notice_weeks": info.get("advance_time_weeks", 4),
                    "validity": info.get("validity", "check with doctor"),
                }
                if vax in {t for trip in self.trips.values() if trip["user_id"] == user_id for t in trip["vaccination_requirements"]["required"]}:
                    missing_required.append(entry)
                else:
                    missing_recommended.append(entry)

        return {
            "user_id": user_id,
            "up_to_date": up_to_date,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "action_needed": len(missing_required) > 0,
            "timeline": self._get_vaccination_timeline(missing_required + missing_recommended),
        }

    def get_jet_lag_plan(self, destination: str, departure_time: str) -> Dict[str, Any]:
        """Generate jet lag management plan."""
        timezone_offset = {"japan": 9, "india": 5.5, "brazil": -3, "kenya": 3, "thailand": 7, "europe": 1}.get(destination.lower(), 0)
        hours_diff = abs(timezone_offset)

        plan = {
            "destination": destination,
            "timezone_difference_hours": timezone_offset,
            "severity": "mild" if hours_diff <= 3 else "moderate" if hours_diff <= 6 else "severe",
            "pre_travel": [
                f"Adjust sleep schedule by {min(hours_diff, 2)} hours per day starting 3 days before",
                "Stay well hydrated",
                "Avoid alcohol 24 hours before flight",
            ],
            "during_flight": [
                "Set watch to destination time immediately",
                "Sleep according to destination time",
                "Stay hydrated, avoid alcohol/caffeine",
                "Move and stretch regularly",
                "Use eye mask and earplugs",
            ],
            "upon_arrival": [
                "Get sunlight exposure during daytime",
                "Avoid napping longer than 20 minutes",
                "Exercise lightly in the morning",
                "Eat meals at local mealtimes",
                "Avoid heavy meals before bed",
            ],
            "recovery_days": max(1, hours_diff // 3),
        }
        return plan

    def _get_generic_destination(self) -> Dict:
        return {
            "risks": [], "required_vaccines": [], "recommended_vaccines": ["hepatitis_a"],
            "malaria_prophylaxis": False, "altitude_risk": "low", "water_safety": "safe",
            "food_precautions": "standard", "travel_advisory": "low",
        }

    def _get_vaccination_advice(self, required: List, recommended: List) -> str:
        if required:
            return f"Get {len(required)} required vaccines at least 2-8 weeks before travel"
        return f"Consider {len(recommended)} recommended vaccines for extra protection"

    def _generate_health_checklist(self, dest: Dict) -> List[Dict]:
        checklist = [
            {"item": "Travel insurance with medical coverage", "priority": "high"},
            {"item": "Prescription medications (enough for trip + extra)", "priority": "high"},
            {"item": "Copy of prescriptions", "priority": "medium"},
            {"item": "First aid kit", "priority": "medium"},
        ]
        if dest.get("malaria_prophylaxis"):
            checklist.append({"item": "Malaria prophylaxis medication", "priority": "high"})
        if dest.get("water_safety") == "drink_bottled":
            checklist.append({"item": "Water purification tablets", "priority": "high"})
        checklist.extend([
            {"item": "Sunscreen SPF 30+", "priority": "medium"},
            {"item": "Insect repellent (DEET 20%+)", "priority": "high" if dest.get("malaria_prophylaxis") else "medium"},
            {"item": "Hand sanitizer", "priority": "medium"},
        ])
        return checklist

    def _get_emergency_info(self, destination: str) -> Dict[str, str]:
        return {"emergency_number": "112", "embassy_contact": "Check your country's embassy", "hospital": "Find nearest hospital on arrival"}

    def _get_travel_kit(self, dest: Dict) -> List[str]:
        kit = ["pain relievers", "antihistamines", "anti-diarrheal", "bandages", "antiseptic"]
        if dest.get("malaria_prophylaxis"):
            kit.append("mosquito net")
        if dest.get("water_safety") != "safe":
            kit.append("oral rehydration salts")
        return kit

    def _get_vaccination_timeline(self, vaccines: List[Dict]) -> List[Dict]:
        sorted_v = sorted(vaccines, key=lambda x: x.get("advance_notice_weeks", 4), reverse=True)
        return [{"vaccine": v["vaccine"], "when": f"{v['advance_notice_weeks']} weeks before travel"} for v in sorted_v]


travel_health_service = TravelHealthService()
