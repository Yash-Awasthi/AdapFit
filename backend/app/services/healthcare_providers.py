"""
Healthcare Provider Directory — Doctors, Hospitals, Clinics, Pharmacies, Labs

Features:
- Search by specialty, location, rating, availability
- Provider profiles with qualifications, experience, accepted insurance
- Appointment booking slots
- Consultation history tracking
- Medical document storage references
"""
import time
import secrets
import math
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class HealthcareProvider:
    id: str
    name: str
    type: str  # doctor, hospital, clinic, pharmacy, lab
    specialty: str
    address: str
    city: str
    country: str
    latitude: float = 0
    longitude: float = 0
    phone: str = ""
    email: str = ""
    rating: float = 0
    review_count: int = 0
    accepted_insurance: list = field(default_factory=list)
    qualifications: list = field(default_factory=list)
    languages: list = field(default_factory=list)
    available: bool = True
    consultation_fee: float = 0
    online_consultation: bool = False


@dataclass
class Appointment:
    id: str
    provider_id: str
    user_id: str
    date: str
    time: str
    type: str  # in_person, video, phone
    reason: str
    status: str  # scheduled, completed, cancelled
    notes: str = ""
    created_at: float = 0


class HealthcareProviderService:
    """Healthcare provider directory and appointment management."""

    def __init__(self):
        self._providers: dict[str, HealthcareProvider] = {}
        self._appointments: dict[str, Appointment] = {}
        self._load_sample_providers()

    def _load_sample_providers(self):
        """Load sample provider directory."""
        providers = [
            HealthcareProvider(
                id="doc_001", name="Dr. Priya Sharma", type="doctor",
                specialty="General Practice", address="123 Health Street",
                city="Mumbai", country="IN", phone="+91-22-1234-5678",
                rating=4.8, review_count=245, languages=["English", "Hindi"],
                qualifications=["MBBS", "MD (General Medicine)"],
                consultation_fee=500, online_consultation=True,
            ),
            HealthcareProvider(
                id="doc_002", name="Dr. Rajesh Patel", type="doctor",
                specialty="Cardiology", address="456 Heart Lane",
                city="Mumbai", country="IN", phone="+91-22-9876-5432",
                rating=4.9, review_count=189, languages=["English", "Hindi", "Gujarati"],
                qualifications=["MBBS", "DM (Cardiology)"],
                consultation_fee=1500, online_consultation=True,
            ),
            HealthcareProvider(
                id="doc_003", name="Dr. Ananya Reddy", type="doctor",
                specialty="Endocrinology", address="789 Diabetes Road",
                city="Hyderabad", country="IN", phone="+91-40-5555-1234",
                rating=4.7, review_count=156, languages=["English", "Telugu"],
                qualifications=["MBBS", "MD (Endocrinology)"],
                consultation_fee=1200, online_consultation=True,
            ),
            HealthcareProvider(
                id="hosp_001", name="City General Hospital", type="hospital",
                specialty="Multi-Specialty", address="100 Hospital Avenue",
                city="Mumbai", country="IN", phone="+91-22-0000-1111",
                rating=4.5, review_count=1200, languages=["English", "Hindi"],
                accepted_insurance=["PM-JAY", "ESIC", "Star Health", "ICICI Lombard"],
                consultation_fee=0, online_consultation=False,
            ),
            HealthcareProvider(
                id="pharm_001", name="HealthFirst Pharmacy", type="pharmacy",
                specialty="Pharmacy", address="25 Medicine Lane",
                city="Mumbai", country="IN", phone="+91-22-3333-4444",
                rating=4.6, review_count=89, languages=["English", "Hindi"],
                consultation_fee=0,
            ),
        ]
        for p in providers:
            self._providers[p.id] = p

    def search_providers(
        self,
        specialty: Optional[str] = None,
        provider_type: Optional[str] = None,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 50,
        min_rating: float = 0,
        online_only: bool = False,
        limit: int = 20,
    ) -> list[dict]:
        """Search healthcare providers with optional filters."""
        results = list(self._providers.values())

        if specialty:
            results = [p for p in results if specialty.lower() in p.specialty.lower()]
        if provider_type:
            results = [p for p in results if p.type == provider_type]
        if city:
            results = [p for p in results if city.lower() in p.city.lower()]
        if min_rating > 0:
            results = [p for p in results if p.rating >= min_rating]
        if online_only:
            results = [p for p in results if p.online_consultation]

        # Geo-distance sorting
        if latitude is not None and longitude is not None:
            for p in results:
                p._distance = self._haversine(latitude, longitude, p.latitude, p.longitude)
            results = [p for p in results if getattr(p, '_distance', 999) <= radius_km]
            results.sort(key=lambda p: getattr(p, '_distance', 999))

        return [self._provider_to_dict(p) for p in results[:limit]]

    def get_provider(self, provider_id: str) -> Optional[dict]:
        """Get detailed provider information."""
        provider = self._providers.get(provider_id)
        return self._provider_to_dict(provider) if provider else None

    def get_specialties(self) -> list[dict]:
        """List available specialties."""
        specialties = {}
        for p in self._providers.values():
            if p.type == "doctor":
                spec = p.specialty
                specialties[spec] = specialties.get(spec, 0) + 1
        return [{"name": k, "count": v} for k, v in sorted(specialties.items())]

    def book_appointment(
        self,
        user_id: str,
        provider_id: str,
        date: str,
        time: str,
        appointment_type: str = "in_person",
        reason: str = "",
    ) -> dict:
        """Book an appointment with a provider."""
        provider = self._providers.get(provider_id)
        if not provider:
            return {"error": "Provider not found"}
        if not provider.available:
            return {"error": "Provider is not currently available"}

        appt_id = f"appt_{secrets.token_hex(6)}"
        appointment = Appointment(
            id=appt_id,
            provider_id=provider_id,
            user_id=user_id,
            date=date,
            time=time,
            type=appointment_type,
            reason=reason,
            status="scheduled",
            created_at=time.time() if isinstance(time, (int, float)) else time.time(),
        )
        self._appointments[appt_id] = appointment
        return {
            "booked": True,
            "appointment_id": appt_id,
            "provider": provider.name,
            "date": date,
            "time": time,
            "type": appointment_type,
            "fee": provider.consultation_fee,
        }

    def get_appointments(self, user_id: str, status: Optional[str] = None) -> list[dict]:
        """Get user's appointments."""
        appts = [a for a in self._appointments.values() if a.user_id == user_id]
        if status:
            appts = [a for a in appts if a.status == status]
        appts.sort(key=lambda a: a.created_at, reverse=True)
        return [
            {
                "id": a.id,
                "provider_id": a.provider_id,
                "date": a.date,
                "time": a.time,
                "type": a.type,
                "reason": a.reason,
                "status": a.status,
            }
            for a in appts
        ]

    def cancel_appointment(self, appointment_id: str, user_id: str) -> dict:
        """Cancel an appointment."""
        appt = self._appointments.get(appointment_id)
        if not appt or appt.user_id != user_id:
            return {"error": "Appointment not found"}
        appt.status = "cancelled"
        return {"cancelled": True, "appointment_id": appointment_id}

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _provider_to_dict(self, p: HealthcareProvider) -> dict:
        return {
            "id": p.id, "name": p.name, "type": p.type,
            "specialty": p.specialty, "address": p.address,
            "city": p.city, "country": p.country,
            "phone": p.phone, "email": p.email,
            "rating": p.rating, "review_count": p.review_count,
            "accepted_insurance": p.accepted_insurance,
            "qualifications": p.qualifications,
            "languages": p.languages,
            "available": p.available,
            "consultation_fee": p.consultation_fee,
            "online_consultation": p.online_consultation,
        }


healthcare_providers_service = HealthcareProviderService()
