"""Gym Integration & Fitness Facility Service.

Based on 2025 ClassPass/gym app research:
- Gym check-in tracking
- ClassPass credit management
- Workout class booking
- Facility finder with amenities
- Personal training session booking
- Group fitness scheduling
"""

import time
import random
from typing import Dict, List, Any


class GymIntegrationService:
    """Gym and fitness facility integration."""

    def __init__(self):
        self.gyms = self._init_gyms()
        self.bookings: Dict[str, List] = {}
        self._init_classes()

    def _init_gyms(self) -> List[Dict]:
        return [
            {"id": "g1", "name": "Equinox", "type": "luxury", "rating": 4.7, "monthly_price": 260, "amenities": ["pool", "spa", "classes", "personal_training", "sauna", "towel_service"], "locations": 100, "classpass_credits": 8},
            {"id": "g2", "name": "Planet Fitness", "type": "budget", "rating": 4.1, "monthly_price": 15, "amenities": ["cardio", "weights", "machines", "tanning"], "locations": 2400, "classpass_credits": 0},
            {"id": "g3", "name": "Orangetheory", "type": "boutique", "rating": 4.5, "monthly_price": 169, "amenities": ["heart_rate_monitoring", "group_classes", "treadmills", "rowers", "weights"], "locations": 1500, "classpass_credits": 10},
            {"id": "g4", "name": "CorePower Yoga", "type": "boutique", "rating": 4.4, "monthly_price": 139, "amenities": ["yoga", "hot_yoga", "sculpt", "meditation"], "locations": 200, "classpass_credits": 8},
            {"id": "g5", "name": "CrossFit Box", "type": "functional", "rating": 4.6, "monthly_price": 199, "amenities": ["crossfit", "open_gym", "personal_training"], "locations": 50, "classpass_credits": 12},
            {"id": "g6", "name": "LA Fitness", "type": "standard", "rating": 3.9, "monthly_price": 35, "amenities": ["pool", "classes", "cardio", "weights", "basketball"], "locations": 700, "classpass_credits": 0},
        ]

    def _init_classes(self):
        self.classes = [
            {"id": "c1", "name": "HIIT Blast", "gym": "Orangetheory", "instructor": "Sarah M.", "time": "6:00 AM", "duration_min": 60, "spots_total": 36, "spots_available": random.randint(0, 10), "type": "cardio", "intensity": "high", "classpass_credits": 8},
            {"id": "c2", "name": "Vinyasa Flow", "gym": "CorePower Yoga", "instructor": "Mike R.", "time": "7:30 AM", "duration_min": 60, "spots_total": 30, "spots_available": random.randint(2, 15), "type": "yoga", "intensity": "moderate", "classpass_credits": 8},
            {"id": "c3", "name": "Spin Class", "gym": "Equinox", "instructor": "Lisa K.", "time": "12:00 PM", "duration_min": 45, "spots_total": 25, "spots_available": random.randint(0, 8), "type": "cardio", "intensity": "high", "classpass_credits": 10},
            {"id": "c4", "name": "CrossFit WOD", "gym": "CrossFit Box", "instructor": "Coach Dan", "time": "5:30 PM", "duration_min": 60, "spots_total": 20, "spots_available": random.randint(0, 5), "type": "functional", "intensity": "high", "classpass_credits": 12},
            {"id": "c5", "name": "Pilates Core", "gym": "Equinox", "instructor": "Emma S.", "time": "9:00 AM", "duration_min": 50, "spots_total": 20, "spots_available": random.randint(3, 12), "type": "pilates", "intensity": "moderate", "classpass_credits": 8},
            {"id": "c6", "name": "Power Lifting", "gym": "CrossFit Box", "instructor": "Coach Mike", "time": "6:00 PM", "duration_min": 75, "spots_total": 15, "spots_available": random.randint(0, 6), "type": "strength", "intensity": "high", "classpass_credits": 12},
        ]

    def search_gyms(self, gym_type: str = "", max_price: int = 0, amenity: str = "") -> List[Dict]:
        """Search for gyms by criteria."""
        results = self.gyms
        if gym_type:
            results = [g for g in results if g["type"] == gym_type]
        if max_price > 0:
            results = [g for g in results if g["monthly_price"] <= max_price]
        if amenity:
            results = [g for g in results if amenity in g["amenities"]]
        return results

    def get_classes(self, gym: str = "", class_type: str = "", available_only: bool = True) -> List[Dict]:
        """Get available fitness classes."""
        results = self.classes
        if gym:
            results = [c for c in results if gym.lower() in c["gym"].lower()]
        if class_type:
            results = [c for c in results if c["type"] == class_type]
        if available_only:
            results = [c for c in results if c["spots_available"] > 0]
        return results

    def book_class(self, user_id: str, class_id: str) -> Dict[str, Any]:
        """Book a fitness class."""
        for cls in self.classes:
            if cls["id"] == class_id:
                if cls["spots_available"] <= 0:
                    return {"error": "Class is full"}
                cls["spots_available"] -= 1
                if user_id not in self.bookings:
                    self.bookings[user_id] = []
                booking = {
                    "class_id": class_id,
                    "class_name": cls["name"],
                    "gym": cls["gym"],
                    "instructor": cls["instructor"],
                    "time": cls["time"],
                    "credits_used": cls["classpass_credits"],
                    "booked_at": time.time(),
                }
                self.bookings[user_id].append(booking)
                return {"booked": True, "booking": booking, "message": f"Booked {cls['name']} at {cls['gym']}"}
        return {"error": "Class not found"}

    def check_in(self, user_id: str, gym_id: str) -> Dict[str, Any]:
        """Check in at a gym."""
        return {"checked_in": True, "gym": gym_id, "timestamp": time.time(), "message": "Have a great workout!"}

    def get_classpass_credits(self, user_id: str) -> Dict[str, Any]:
        """Get ClassPass credit balance."""
        return {"credits_remaining": random.randint(15, 45), "credits_used_this_month": random.randint(5, 30), "next_reset": "1st of next month"}

    def get_my_bookings(self, user_id: str) -> List[Dict]:
        """Get user's upcoming bookings."""
        return self.bookings.get(user_id, [])


gym_integration_service = GymIntegrationService()
