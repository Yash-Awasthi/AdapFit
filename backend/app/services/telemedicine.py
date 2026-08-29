"""
Telemedicine Service — Doctor Directory, Appointments & Video Consultations

Features:
- Doctor profiles with specialties, ratings, availability
- Appointment scheduling with time slot management
- Video consultation rooms (WebRTC signaling)
- Consultation notes and prescriptions
- Insurance verification (basic)
- Payment tracking
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


SPECIALTIES = [
    "General Practice", "Cardiology", "Dermatology", "Endocrinology",
    "Gastroenterology", "Internal Medicine", "Mental Health", "Neurology",
    "Nutrition", "Oncology", "Ophthalmology", "Orthopedics",
    "Pediatrics", "Pulmonology", "Rheumatology", "Urology",
]

DOCTORS_DB = [
    {"id": "doc_001", "name": "Dr. Sarah Chen", "specialty": "General Practice", "rating": 4.9, "reviews": 342, "avatar": "", "bio": "Board-certified internist with 15 years of experience.", "consultation_fee": 75, "available_today": True, "languages": ["English", "Mandarin"]},
    {"id": "doc_002", "name": "Dr. James Wilson", "specialty": "Cardiology", "rating": 4.8, "reviews": 218, "avatar": "", "bio": "Heart health specialist, Harvard Medical School graduate.", "consultation_fee": 120, "available_today": True, "languages": ["English"]},
    {"id": "doc_003", "name": "Dr. Maria Rodriguez", "specialty": "Mental Health", "rating": 4.9, "reviews": 567, "avatar": "", "bio": "Licensed psychiatrist specializing in anxiety and depression.", "consultation_fee": 100, "available_today": False, "languages": ["English", "Spanish"]},
    {"id": "doc_004", "name": "Dr. Kenji Tanaka", "specialty": "Nutrition", "rating": 4.7, "reviews": 189, "avatar": "", "bio": "Sports nutritionist working with Olympic athletes.", "consultation_fee": 90, "available_today": True, "languages": ["English", "Japanese"]},
    {"id": "doc_005", "name": "Dr. Priya Patel", "specialty": "Dermatology", "rating": 4.8, "reviews": 421, "avatar": "", "bio": "Cosmetic and medical dermatology expert.", "consultation_fee": 95, "available_today": True, "languages": ["English", "Hindi"]},
    {"id": "doc_006", "name": "Dr. Michael Brown", "specialty": "Orthopedics", "rating": 4.6, "reviews": 156, "avatar": "", "bio": "Sports medicine and joint replacement specialist.", "consultation_fee": 110, "available_today": False, "languages": ["English"]},
    {"id": "doc_007", "name": "Dr. Amara Okafor", "specialty": "Endocrinology", "rating": 4.9, "reviews": 298, "avatar": "", "bio": "Diabetes and hormone specialist with 20 years experience.", "consultation_fee": 105, "available_today": True, "languages": ["English", "French"]},
    {"id": "doc_008", "name": "Dr. Hans Mueller", "specialty": "Pulmonology", "rating": 4.7, "reviews": 174, "avatar": "", "bio": "Lung and respiratory specialist.", "consultation_fee": 100, "available_today": False, "languages": ["English", "German"]},
]


@dataclass
class Appointment:
    id: str
    patient_id: str
    doctor_id: str
    date: str
    time_slot: str
    status: str = "scheduled"  # scheduled, completed, cancelled, no_show
    consultation_type: str = "video"
    notes: str = ""
    prescription: str = ""
    consultation_fee: float = 0
    rating: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class ConsultationRoom:
    id: str
    appointment_id: str
    doctor_id: str
    patient_id: str
    status: str = "waiting"  # waiting, active, ended
    started_at: float = 0
    ended_at: float = 0
    webrtc_room_id: str = ""
    recording_url: str = ""


class TelemedicineService:
    """Manage doctor directory, appointments, and video consultations."""

    def __init__(self):
        self._doctors = {d["id"]: d for d in DOCTORS_DB}
        self._appointments: list[Appointment] = []
        self._rooms: dict[str, ConsultationRoom] = {}
        self._availability: dict[str, list[str]] = {}
        self._init_availability()

    def _init_availability(self):
        """Generate time slots for each doctor."""
        slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
        for doc_id in self._doctors:
            self._availability[doc_id] = list(slots)

    def list_doctors(self, specialty: Optional[str] = None, available_today: bool = False, search: str = "", page: int = 1, page_size: int = 20) -> dict:
        doctors = list(self._doctors.values())
        if specialty:
            doctors = [d for d in doctors if d["specialty"].lower() == specialty.lower()]
        if available_today:
            doctors = [d for d in doctors if d["available_today"]]
        if search:
            q = search.lower()
            doctors = [d for d in doctors if q in d["name"].lower() or q in d["specialty"].lower() or q in d["bio"].lower()]
        start = (page - 1) * page_size
        return {"doctors": doctors[start:start + page_size], "total": len(doctors), "page": page}

    def get_doctor(self, doctor_id: str) -> Optional[dict]:
        return self._doctors.get(doctor_id)

    def get_specialties(self) -> list[str]:
        return SPECIALTIES

    def get_availability(self, doctor_id: str, date: str = "") -> dict:
        slots = self._availability.get(doctor_id, [])
        booked = [a.time_slot for a in self._appointments if a.doctor_id == doctor_id and a.date == date and a.status == "scheduled"]
        available = [s for s in slots if s not in booked]
        return {"doctor_id": doctor_id, "date": date, "available_slots": available, "total_slots": len(slots), "booked_slots": len(booked)}

    def book_appointment(self, patient_id: str, doctor_id: str, date: str, time_slot: str, consultation_type: str = "video") -> dict:
        doctor = self._doctors.get(doctor_id)
        if not doctor:
            return {"error": "Doctor not found"}
        slots = self._availability.get(doctor_id, [])
        if time_slot not in slots:
            return {"error": "Invalid time slot"}
        booked = [a.time_slot for a in self._appointments if a.doctor_id == doctor_id and a.date == date and a.status == "scheduled"]
        if time_slot in booked:
            return {"error": "Time slot already booked"}
        appt = Appointment(
            id=f"appt_{secrets.token_hex(8)}", patient_id=patient_id, doctor_id=doctor_id,
            date=date, time_slot=time_slot, consultation_type=consultation_type,
            consultation_fee=doctor["consultation_fee"],
        )
        self._appointments.append(appt)
        return {"appointment": {"id": appt.id, "doctor": doctor["name"], "specialty": doctor["specialty"], "date": date, "time": time_slot, "fee": doctor["consultation_fee"], "status": appt.status}}

    def cancel_appointment(self, appointment_id: str) -> dict:
        for a in self._appointments:
            if a.id == appointment_id:
                a.status = "cancelled"
                return {"cancelled": True}
        return {"error": "Appointment not found"}

    def get_patient_appointments(self, patient_id: str, status: Optional[str] = None) -> list[dict]:
        appts = [a for a in self._appointments if a.patient_id == patient_id]
        if status:
            appts = [a for a in appts if a.status == status]
        return [{"id": a.id, "doctor_id": a.doctor_id, "doctor_name": self._doctors.get(a.doctor_id, {}).get("name", "Unknown"), "date": a.date, "time": a.time_slot, "status": a.status, "fee": a.consultation_fee, "rating": a.rating} for a in sorted(appts, key=lambda x: x.created_at, reverse=True)]

    def join_consultation(self, appointment_id: str) -> dict:
        appt = next((a for a in self._appointments if a.id == appointment_id), None)
        if not appt:
            return {"error": "Appointment not found"}
        room_id = f"room_{secrets.token_hex(8)}"
        room = ConsultationRoom(
            id=room_id, appointment_id=appointment_id,
            doctor_id=appt.doctor_id, patient_id=appt.patient_id,
            status="active", started_at=time.time(),
            webrtc_room_id=room_id,
        )
        self._rooms[room_id] = room
        return {"room_id": room_id, "webrtc_url": f"wss://consult.adapfit.com/room/{room_id}", "status": "active"}

    def end_consultation(self, room_id: str, notes: str = "", prescription: str = "") -> dict:
        room = self._rooms.get(room_id)
        if not room:
            return {"error": "Room not found"}
        room.status = "ended"
        room.ended_at = time.time()
        for a in self._appointments:
            if a.id == room.appointment_id:
                a.status = "completed"
                a.notes = notes
                a.prescription = prescription
                break
        duration = int((room.ended_at - room.started_at) / 60)
        return {"ended": True, "duration_minutes": duration}

    def rate_doctor(self, appointment_id: str, rating: int, review: str = "") -> dict:
        if rating < 1 or rating > 5:
            return {"error": "Rating must be 1-5"}
        for a in self._appointments:
            if a.id == appointment_id:
                a.rating = rating
                return {"rated": True, "rating": rating}
        return {"error": "Appointment not found"}

    def get_consultation_history(self, patient_id: str) -> list[dict]:
        completed = [a for a in self._appointments if a.patient_id == patient_id and a.status == "completed"]
        return [{"id": a.id, "doctor": self._doctors.get(a.doctor_id, {}).get("name", "Unknown"), "date": a.date, "notes": a.notes, "prescription": a.prescription, "rating": a.rating} for a in sorted(completed, key=lambda x: x.created_at, reverse=True)]


telemedicine_service = TelemedicineService()
