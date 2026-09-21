"""Hospital & Urgent Care Finder Service.

Based on 2025 healthcare facility research:
- Emergency room wait times
- Urgent care center locator
- Hospital ratings and reviews
- Specialty availability
- Insurance acceptance
- Distance calculation
"""

import time
from typing import Dict, List, Any


class HospitalFinderService:
    """Find hospitals, ERs, and urgent care with real-time data."""

    def __init__(self):
        self.facilities = self._init_facilities()
        # Live waits, keyed by facility id, from whoever reports them.
        self._er_waits: Dict[str, Dict[str, Any]] = {}

    def record_er_wait(self, facility_id: str, wait_minutes: int) -> Dict[str, Any]:
        """Record a reported emergency department wait for one facility."""
        if not any(f["id"] == facility_id for f in self.facilities):
            return {"error": "Facility not found"}
        self._er_waits[facility_id] = {"wait_minutes": int(wait_minutes), "recorded_at": time.time()}
        return {"recorded": True, "facility_id": facility_id, "wait_minutes": int(wait_minutes)}

    def _wait_for(self, facility_id: str) -> Dict[str, Any]:
        """The reported wait, or an explicit absence. Never a guess."""
        reported = self._er_waits.get(facility_id)
        if reported is None:
            return {"wait_minutes": None, "wait_level": "unknown", "wait_reported_at": None}
        minutes = reported["wait_minutes"]
        return {
            "wait_minutes": minutes,
            "wait_level": "low" if minutes <= 30 else "moderate" if minutes <= 90 else "high",
            "wait_reported_at": reported["recorded_at"],
        }

    def _init_facilities(self) -> List[Dict]:
        return [
            {"id": "h1", "name": "Boston Medical Center", "type": "hospital", "address": "1 Boston Medical Center Pl, Boston, MA", "lat": 42.338, "lng": -71.072, "rating": 4.2, "specialties": ["emergency", "cardiology", "oncology", "neurology"], "phone": "617-638-8000", "insurance_accepted": ["blue_cross", "aetna", "united", "cigna"], "beds": 514, "has_er": True, "has_urgent_care": False},
            {"id": "h2", "name": "Mass General Hospital", "type": "hospital", "address": "55 Fruit St, Boston, MA", "lat": 42.363, "lng": -71.068, "rating": 4.7, "specialties": ["emergency", "cardiology", "transplant", "cancer"], "phone": "617-726-2000", "insurance_accepted": ["blue_cross", "aetna", "united", "cigna", "humana"], "beds": 1057, "has_er": True, "has_urgent_care": True},
            {"id": "uc1", "name": "CityHealth Urgent Care", "type": "urgent_care", "address": "100 Congress St, Boston, MA", "lat": 42.355, "lng": -71.051, "rating": 4.3, "specialties": ["urgent_care", "xray", "lab"], "phone": "617-555-0100", "insurance_accepted": ["blue_cross", "aetna", "united"], "has_er": False, "has_urgent_care": True, "hours": "8AM-8PM", "walk_in": True},
            {"id": "uc2", "name": "MinuteClinic", "type": "urgent_care", "address": "200 Boylston St, Boston, MA", "lat": 42.352, "lng": -71.070, "rating": 4.0, "specialties": ["urgent_care", "vaccinations"], "phone": "617-555-0200", "insurance_accepted": ["blue_cross", "aetna"], "has_er": False, "has_urgent_care": True, "hours": "9AM-7PM", "walk_in": True},
            {"id": "h3", "name": "Brigham and Women's Hospital", "type": "hospital", "address": "75 Francis St, Boston, MA", "lat": 42.336, "lng": -71.107, "rating": 4.6, "specialties": ["emergency", "cardiology", "orthopedics", "transplant"], "phone": "617-732-5500", "insurance_accepted": ["blue_cross", "aetna", "united", "cigna", "humana"], "beds": 793, "has_er": True, "has_urgent_care": False},
        ]

    def find_nearby(self, location: str = "Boston", facility_type: str = "all", max_wait_minutes: int = 0) -> Dict[str, Any]:
        """
        Facilities in the built-in directory, with any reported wait attached.

        The directory is a fixed list of Boston facilities, which is why the
        response says so: it is reference data, not a search of wherever the
        caller happens to be.
        """
        results = self.facilities
        if facility_type != "all":
            results = [f for f in results if f["type"] == facility_type]
        entries = [{**f, **self._wait_for(f["id"])} for f in results]
        if max_wait_minutes > 0:
            # A facility with no reported wait is kept rather than filtered
            # out: unknown is not the same as longer than the limit.
            entries = [
                e for e in entries
                if e["wait_minutes"] is None or e["wait_minutes"] <= max_wait_minutes
            ]
        return {
            "status": "ok",
            "directory": "built-in sample directory (Boston, MA)",
            "requested_location": location,
            "facilities": entries,
            "note": (
                "This directory is not a search of your area, and waits are only shown "
                "where one has been reported. In an emergency, call your local emergency "
                "number rather than comparing waits."
            ),
        }

    def get_er_wait_times(self) -> List[Dict]:
        """Reported emergency waits. `wait_minutes` is null where none was reported."""
        return [
            {"id": f["id"], "name": f["name"], "address": f["address"], **self._wait_for(f["id"])}
            for f in self.facilities if f.get("has_er")
        ]

    def get_urgent_care(self) -> List[Dict]:
        """Urgent care centres, with a reported wait where one exists."""
        return [
            {
                "id": f["id"], "name": f["name"], "hours": f.get("hours", "24/7"),
                "walk_in": f.get("walk_in", True), **self._wait_for(f["id"]),
            }
            for f in self.facilities if f.get("has_urgent_care")
        ]

    def get_hospital_details(self, facility_id: str) -> Dict[str, Any]:
        """Get detailed facility information."""
        for f in self.facilities:
            if f["id"] == facility_id:
                return f
        return {"error": "Facility not found"}

    def should_go_er_or_urgent_care(self, symptoms: List[str]) -> Dict[str, Any]:
        """Triage guidance for ER vs urgent care."""
        er_symptoms = ["chest_pain", "difficulty_breathing", "stroke_symptoms", "severe_bleeding", "loss_of_consciousness", "severe_allergic_reaction"]
        urgent_symptoms = ["fever", "sprain", "cut_needing_stitches", "mild_burn", "ut_infection", "ear_infection", "flu", "minor_allergy"]

        has_er = any(s in er_symptoms for s in symptoms)
        has_urgent = any(s in urgent_symptoms for s in symptoms)

        if has_er:
            return {"recommendation": "Go to Emergency Room", "urgency": "IMMEDIATE", "dial_911": True, "reason": "Symptoms require emergency care"}
        elif has_urgent:
            return {"recommendation": "Visit Urgent Care", "urgency": "Same day", "dial_911": False, "reason": "Symptoms can be treated at urgent care — shorter wait, lower cost"}
        else:
            return {"recommendation": "Schedule a primary care visit", "urgency": "Within 1-2 days", "dial_911": False, "reason": "Symptoms don't require emergency or urgent care"}


hospital_finder_service = HospitalFinderService()
