"""
Location Tracker Service — GPS Walk Tracking, Distance Counter & Route Analysis

Features:
- Real-time GPS walk/run tracking with distance calculation
- Pace and speed analysis
- Elevation tracking
- Route mapping with waypoints
- Activity auto-detection (walking, running, cycling)
- Calorie burn estimation based on GPS data
- Floor climbing detection
- Historical route storage and replay

Inspired by: Google Fit GPS tracking, Samsung Health workout tracking, Strava
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ActivityType(Enum):
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    HIKING = "hiking"
    STATIONARY = "stationary"
    UNKNOWN = "unknown"


class TrackingStatus(Enum):
    INACTIVE = "inactive"
    TRACKING = "tracking"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class GeoPoint:
    latitude: float
    longitude: float
    altitude: float = 0.0
    accuracy: float = 10.0
    speed: float = 0.0
    timestamp: float = field(default_factory=time.time)
    heart_rate: Optional[int] = None


@dataclass
class RouteSegment:
    start_point: GeoPoint
    end_point: GeoPoint
    distance_meters: float
    duration_seconds: float
    avg_speed: float
    avg_pace: Optional[float]  # min/km
    elevation_change: float
    activity_type: ActivityType


@dataclass
class WalkSession:
    session_id: str
    start_time: float
    end_time: Optional[float]
    status: TrackingStatus
    route_points: list[GeoPoint]
    total_distance_meters: float
    total_duration_seconds: float
    avg_speed: float
    avg_pace: float  # min/km
    max_speed: float
    calories_burned: float
    steps_estimated: int
    floors_climbed: int
    elevation_gain: float
    elevation_loss: float
    activity_type: ActivityType
    segments: list[RouteSegment]


@dataclass
class DailyWalkSummary:
    date: str
    total_steps: int
    total_distance_km: float
    total_active_minutes: int
    total_calories: float
    floors_climbed: int
    longest_walk_km: float
    avg_pace: float
    active_minutes_by_hour: dict[str, int]


class LocationTrackerService:
    """
    GPS-based walk tracking and distance measurement system.
    
    Uses device GPS sensor for:
    - Real-time distance calculation using Haversine formula
    - Pace and speed tracking
    - Route recording with waypoints
    - Activity type auto-detection
    - Calorie estimation from distance + pace
    """

    # Calorie burn rates (cal/kg/km)
    CALORIE_RATES = {
        ActivityType.WALKING: 0.53,
        ActivityType.RUNNING: 0.75,
        ActivityType.CYCLING: 0.28,
        ActivityType.HIKING: 0.60,
        ActivityType.STATIONARY: 0.0,
        ActivityType.UNKNOWN: 0.45,
    }

    # Average stride length (meters) by height bracket
    STRIDE_LENGTHS = {
        "short": 0.63,   # < 160cm
        "medium": 0.72,  # 160-175cm
        "tall": 0.82,    # > 175cm
    }

    # Activity detection thresholds (m/s)
    SPEED_THRESHOLDS = {
        "stationary": 0.3,
        "walking": 0.5,
        "running": 2.0,
        "cycling": 4.0,
    }

    def __init__(self):
        self._sessions: list[WalkSession] = []
        self._current_session: Optional[WalkSession] = None
        self._daily_summaries: list[DailyWalkSummary] = []
        self._user_weight_kg: float = 70.0
        self._user_height_cm: float = 170.0

    def set_user_profile(self, weight_kg: float, height_cm: float):
        """Set user physical profile for accurate calculations."""
        self._user_weight_kg = weight_kg
        self._user_height_cm = height_cm

    def start_tracking(self, activity_type: str = "auto") -> dict:
        """Start a new GPS tracking session."""
        if self._current_session and self._current_session.status == TrackingStatus.TRACKING:
            return {"error": "A tracking session is already active. Stop it first."}
        
        try:
            act = ActivityType(activity_type)
        except ValueError:
            act = ActivityType.UNKNOWN
        
        session = WalkSession(
            session_id=f"session_{int(time.time())}",
            start_time=time.time(),
            end_time=None,
            status=TrackingStatus.TRACKING,
            route_points=[],
            total_distance_meters=0,
            total_duration_seconds=0,
            avg_speed=0,
            avg_pace=0,
            max_speed=0,
            calories_burned=0,
            steps_estimated=0,
            floors_climbed=0,
            elevation_gain=0,
            elevation_loss=0,
            activity_type=act,
            segments=[],
        )
        self._current_session = session
        
        return {
            "session_id": session.session_id,
            "status": "tracking",
            "activity_type": session.activity_type.value,
            "message": "GPS tracking started. Walk or run to track your activity.",
        }

    def add_location_point(self, latitude: float, longitude: float, altitude: float = 0.0,
                          accuracy: float = 10.0, heart_rate: Optional[int] = None) -> dict:
        """Add a new GPS location point during active tracking."""
        if not self._current_session or self._current_session.status != TrackingStatus.TRACKING:
            return {"error": "No active tracking session"}
        
        point = GeoPoint(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            accuracy=accuracy,
            timestamp=time.time(),
            heart_rate=heart_rate,
        )
        
        # Calculate distance from last point
        if self._current_session.route_points:
            last = self._current_session.route_points[-1]
            distance = self._haversine_distance(last.latitude, last.longitude, latitude, longitude)
            
            # Skip points with poor accuracy or unrealistic jumps
            if accuracy > 50 or distance > 1000:  # > 1km jump = GPS glitch
                return {"skipped": True, "reason": "Poor accuracy" if accuracy > 50 else "GPS glitch"}
            
            # Calculate speed
            time_diff = point.timestamp - last.timestamp
            if time_diff > 0:
                speed = distance / time_diff
                point.speed = speed
                
                # Auto-detect activity type
                if self._current_session.activity_type == ActivityType.UNKNOWN:
                    self._current_session.activity_type = self._detect_activity(speed)
            
            # Update session stats
            self._current_session.total_distance_meters += distance
            
            # Elevation tracking
            alt_diff = altitude - last.altitude
            if alt_diff > 0.5:
                self._current_session.elevation_gain += alt_diff
            elif alt_diff < -0.5:
                self._current_session.elevation_loss += abs(alt_diff)
            
            # Floor estimation (1 floor ≈ 3 meters)
            if alt_diff > 3:
                self._current_session.floors_climbed += int(alt_diff / 3)
            
            self._current_session.max_speed = max(self._current_session.max_speed, speed)
        
        self._current_session.route_points.append(point)
        
        # Update derived stats
        self._update_session_stats()
        
        return {
            "point_added": True,
            "total_distance_km": round(self._current_session.total_distance_meters / 1000, 3),
            "current_speed_kmh": round(point.speed * 3.6, 1) if point.speed else 0,
            "points_collected": len(self._current_session.route_points),
        }

    def pause_tracking(self) -> dict:
        """Pause the current tracking session."""
        if not self._current_session:
            return {"error": "No active session"}
        self._current_session.status = TrackingStatus.PAUSED
        return {"status": "paused", "session_id": self._current_session.session_id}

    def resume_tracking(self) -> dict:
        """Resume a paused tracking session."""
        if not self._current_session or self._current_session.status != TrackingStatus.PAUSED:
            return {"error": "No paused session to resume"}
        self._current_session.status = TrackingStatus.TRACKING
        return {"status": "tracking", "session_id": self._current_session.session_id}

    def stop_tracking(self) -> dict:
        """Stop and save the current tracking session."""
        if not self._current_session:
            return {"error": "No active session"}
        
        self._current_session.end_time = time.time()
        self._current_session.status = TrackingStatus.COMPLETED
        self._update_session_stats()
        
        session = self._current_session
        self._sessions.append(session)
        self._current_session = None
        
        return self._format_session_summary(session)

    def get_current_status(self) -> dict:
        """Get current tracking status and live stats."""
        if not self._current_session:
            return {"status": "inactive", "message": "No active tracking session"}
        
        s = self._current_session
        elapsed = time.time() - s.start_time
        
        return {
            "status": s.status.value,
            "session_id": s.session_id,
            "activity_type": s.activity_type.value,
            "elapsed_seconds": round(elapsed),
            "elapsed_formatted": self._format_duration(elapsed),
            "distance_km": round(s.total_distance_meters / 1000, 3),
            "distance_miles": round(s.total_distance_meters / 1609.34, 3),
            "current_pace": f"{s.avg_pace:.1f} min/km" if s.avg_pace > 0 else "N/A",
            "avg_speed_kmh": round(s.avg_speed * 3.6, 1),
            "max_speed_kmh": round(s.max_speed * 3.6, 1),
            "calories": round(s.calories_burned),
            "steps": s.steps_estimated,
            "elevation_gain_m": round(s.elevation_gain),
            "floors_climbed": s.floors_climbed,
            "points_collected": len(s.route_points),
        }

    def get_daily_summary(self, date: str = "today") -> DailyWalkSummary:
        """Get daily walking summary."""
        today_sessions = [s for s in self._sessions if s.status == TrackingStatus.COMPLETED]
        
        total_steps = sum(s.steps_estimated for s in today_sessions)
        total_distance = sum(s.total_distance_meters for s in today_sessions)
        total_active = sum(s.total_duration_seconds for s in today_sessions) / 60
        total_calories = sum(s.calories_burned for s in today_sessions)
        floors = sum(s.floors_climbed for s in today_sessions)
        longest = max((s.total_distance_meters for s in today_sessions), default=0) / 1000
        
        return DailyWalkSummary(
            date=date,
            total_steps=total_steps,
            total_distance_km=round(total_distance / 1000, 2),
            total_active_minutes=round(total_active),
            total_calories=round(total_calories),
            floors_climbed=floors,
            longest_walk_km=round(longest, 2),
            avg_pace=self._calculate_overall_pace(today_sessions),
            active_minutes_by_hour={},
        )

    def get_route_history(self, limit: int = 10) -> list[dict]:
        """Get recent tracked routes."""
        routes = []
        for session in reversed(self._sessions[-limit:]):
            routes.append({
                "session_id": session.session_id,
                "date": time.strftime("%Y-%m-%d", time.localtime(session.start_time)),
                "activity": session.activity_type.value,
                "distance_km": round(session.total_distance_meters / 1000, 2),
                "duration": self._format_duration(session.total_duration_seconds),
                "calories": round(session.calories_burned),
                "pace": f"{session.avg_pace:.1f} min/km" if session.avg_pace > 0 else "N/A",
                "points": len(session.route_points),
                "elevation_gain": round(session.elevation_gain),
            })
        return routes

    # === Private helpers ===

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    def _detect_activity(self, speed_ms: float) -> ActivityType:
        """Auto-detect activity from speed."""
        if speed_ms < self.SPEED_THRESHOLDS["stationary"]:
            return ActivityType.STATIONARY
        elif speed_ms < self.SPEED_THRESHOLDS["walking"]:
            return ActivityType.WALKING
        elif speed_ms < self.SPEED_THRESHOLDS["running"]:
            return ActivityType.WALKING  # fast walk
        elif speed_ms < self.SPEED_THRESHOLDS["cycling"]:
            return ActivityType.RUNNING
        else:
            return ActivityType.CYCLING

    def _update_session_stats(self):
        """Update derived statistics for current session."""
        s = self._current_session
        if not s or not s.route_points:
            return
        
        # Duration
        s.total_duration_seconds = time.time() - s.start_time
        
        # Average speed
        if s.total_duration_seconds > 0:
            s.avg_speed = s.total_distance_meters / s.total_duration_seconds
        
        # Pace (min/km)
        if s.avg_speed > 0:
            s.avg_pace = 1000 / (s.avg_speed * 60)  # min/km
        
        # Steps estimation
        stride = self._get_stride_length()
        s.steps_estimated = int(s.total_distance_meters / stride)
        
        # Calories
        rate = self.CALORIE_RATES.get(s.activity_type, 0.45)
        s.calories_burned = s.total_distance_meters / 1000 * rate * self._user_weight_kg

    def _get_stride_length(self) -> float:
        """Get stride length based on user height."""
        if self._user_height_cm < 160:
            return self.STRIDE_LENGTHS["short"]
        elif self._user_height_cm <= 175:
            return self.STRIDE_LENGTHS["medium"]
        else:
            return self.STRIDE_LENGTHS["tall"]

    def _calculate_overall_pace(self, sessions: list) -> float:
        total_dist = sum(s.total_distance_meters for s in sessions)
        total_dur = sum(s.total_duration_seconds for s in sessions)
        if total_dist > 0 and total_dur > 0:
            avg_speed = total_dist / total_dur
            return round(1000 / (avg_speed * 60), 1)
        return 0.0

    def _format_session_summary(self, session: WalkSession) -> dict:
        return {
            "session_id": session.session_id,
            "activity": session.activity_type.value,
            "distance_km": round(session.total_distance_meters / 1000, 3),
            "distance_miles": round(session.total_distance_meters / 1609.34, 3),
            "duration": self._format_duration(session.total_duration_seconds),
            "avg_pace": f"{session.avg_pace:.1f} min/km" if session.avg_pace > 0 else "N/A",
            "avg_speed_kmh": round(session.avg_speed * 3.6, 1),
            "max_speed_kmh": round(session.max_speed * 3.6, 1),
            "calories": round(session.calories_burned),
            "steps": session.steps_estimated,
            "elevation_gain_m": round(session.elevation_gain),
            "elevation_loss_m": round(session.elevation_loss),
            "floors_climbed": session.floors_climbed,
            "route_points": len(session.route_points),
        }

    def _format_duration(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        return f"{m}m {s}s"


# Singleton
location_tracker_service = LocationTrackerService()
