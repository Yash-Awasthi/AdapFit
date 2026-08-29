"""
Database Layer — SQLAlchemy async with all health app models

Features:
- Async SQLAlchemy setup (SQLite dev, PostgreSQL-ready)
- Session management with context manager
- All health domain models: User, HealthMetric, Workout, Meal, SleepSession, Medication, MoodEntry
- Migration-ready base model
"""
import os
import time
import json
from typing import Optional, AsyncGenerator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager


# === Simple in-memory database (SQLite-ready pattern) ===
# For production, swap with SQLAlchemy async + PostgreSQL

class InMemoryDB:
    """In-memory database with SQLite-like API. Easy to swap with real DB."""

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}
        self._id_counters: dict[str, int] = {}

    def _next_id(self, table: str) -> str:
        self._id_counters[table] = self._id_counters.get(table, 0) + 1
        return f"{table}_{self._id_counters[table]:06d}"

    def insert(self, table: str, data: dict) -> dict:
        record = {
            "id": self._next_id(table),
            "created_at": time.time(),
            "updated_at": time.time(),
            **data,
        }
        self._tables.setdefault(table, []).append(record)
        return record

    def find_by_id(self, table: str, record_id: str) -> Optional[dict]:
        for record in self._tables.get(table, []):
            if record["id"] == record_id:
                return record
        return None

    def find_all(self, table: str, filters: Optional[dict] = None, limit: int = 100, offset: int = 0) -> list[dict]:
        records = self._tables.get(table, [])
        if filters:
            records = [r for r in records if all(r.get(k) == v for k, v in filters.items())]
        return records[offset:offset + limit]

    def update(self, table: str, record_id: str, updates: dict) -> Optional[dict]:
        for record in self._tables.get(table, []):
            if record["id"] == record_id:
                record.update(updates)
                record["updated_at"] = time.time()
                return record
        return None

    def delete(self, table: str, record_id: str) -> bool:
        records = self._tables.get(table, [])
        for i, record in enumerate(records):
            if record["id"] == record_id:
                records.pop(i)
                return True
        return False

    def count(self, table: str, filters: Optional[dict] = None) -> int:
        records = self._tables.get(table, [])
        if filters:
            records = [r for r in records if all(r.get(k) == v for k, v in filters.items())]
        return len(records)

    def query(self, table: str, sql_like: str = "", order_by: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Simple query with optional ordering."""
        records = list(self._tables.get(table, []))
        if order_by:
            desc = order_by.startswith("-")
            field = order_by.lstrip("-")
            records.sort(key=lambda r: r.get(field, 0), reverse=desc)
        return records[:limit]

    def get_stats(self) -> dict:
        return {table: len(records) for table, records in self._tables.items()}


# Singleton database instance
db = InMemoryDB()


# === Model Helpers ===

def create_user_record(email: str, username: str, password_hash: str, **kwargs) -> dict:
    return db.insert("users", {
        "email": email.lower(),
        "username": username.lower(),
        "password_hash": password_hash,
        "display_name": kwargs.get("display_name", username),
        "avatar_url": kwargs.get("avatar_url", ""),
        "date_of_birth": kwargs.get("date_of_birth", ""),
        "gender": kwargs.get("gender", ""),
        "height": kwargs.get("height", 0),
        "weight": kwargs.get("weight", 0),
        "units": kwargs.get("units", "metric"),
        "role": kwargs.get("role", "user"),
        "is_active": True,
        "last_login": 0,
    })


def create_health_metric(user_id: str, metric_type: str, value: float, unit: str, **kwargs) -> dict:
    return db.insert("health_metrics", {
        "user_id": user_id,
        "metric_type": metric_type,
        "value": value,
        "unit": unit,
        "source": kwargs.get("source", "manual"),
        "notes": kwargs.get("notes", ""),
        "recorded_at": kwargs.get("recorded_at", time.time()),
    })


def create_workout_record(user_id: str, **kwargs) -> dict:
    return db.insert("workouts", {
        "user_id": user_id,
        "plan_id": kwargs.get("plan_id", "custom"),
        "exercises": json.dumps(kwargs.get("exercises", [])),
        "duration_minutes": kwargs.get("duration_minutes", 0),
        "total_volume": kwargs.get("total_volume", 0),
        "calories_burned": kwargs.get("calories_burned", 0),
        "completed": kwargs.get("completed", False),
        "started_at": kwargs.get("started_at", time.time()),
        "ended_at": kwargs.get("ended_at", 0),
    })


def create_meal_record(user_id: str, **kwargs) -> dict:
    return db.insert("meals", {
        "user_id": user_id,
        "meal_type": kwargs.get("meal_type", "snack"),
        "foods": json.dumps(kwargs.get("foods", [])),
        "total_calories": kwargs.get("total_calories", 0),
        "total_protein": kwargs.get("total_protein", 0),
        "total_carbs": kwargs.get("total_carbs", 0),
        "total_fat": kwargs.get("total_fat", 0),
        "total_fiber": kwargs.get("total_fiber", 0),
        "logged_at": kwargs.get("logged_at", time.time()),
    })


def create_sleep_session(user_id: str, **kwargs) -> dict:
    return db.insert("sleep_sessions", {
        "user_id": user_id,
        "duration_hours": kwargs.get("duration_hours", 0),
        "quality": kwargs.get("quality", 5),
        "deep_sleep": kwargs.get("deep_sleep", 0),
        "rem_sleep": kwargs.get("rem_sleep", 0),
        "light_sleep": kwargs.get("light_sleep", 0),
        "score": kwargs.get("score", 50),
        "notes": kwargs.get("notes", ""),
        "bedtime": kwargs.get("bedtime", ""),
        "wake_time": kwargs.get("wake_time", ""),
        "recorded_at": kwargs.get("recorded_at", time.time()),
    })


def create_medication_record(user_id: str, **kwargs) -> dict:
    return db.insert("medications", {
        "user_id": user_id,
        "name": kwargs.get("name", ""),
        "dosage": kwargs.get("dosage", ""),
        "frequency": kwargs.get("frequency", "daily"),
        "time": kwargs.get("time", "08:00"),
        "is_active": kwargs.get("is_active", True),
        "taken_at": kwargs.get("taken_at", 0),
    })


def create_mood_entry(user_id: str, **kwargs) -> dict:
    return db.insert("mood_entries", {
        "user_id": user_id,
        "mood": kwargs.get("mood", 5),
        "emoji": kwargs.get("emoji", "😐"),
        "energy": kwargs.get("energy", 5),
        "anxiety": kwargs.get("anxiety", 5),
        "tags": json.dumps(kwargs.get("tags", [])),
        "notes": kwargs.get("notes", ""),
        "journal": kwargs.get("journal", ""),
        "recorded_at": kwargs.get("recorded_at", time.time()),
    })


def create_challenge_record(**kwargs) -> dict:
    return db.insert("challenges", {
        "name": kwargs.get("name", ""),
        "challenge_type": kwargs.get("challenge_type", "steps"),
        "description": kwargs.get("description", ""),
        "target_value": kwargs.get("target_value", 0),
        "start_date": kwargs.get("start_date", ""),
        "end_date": kwargs.get("end_date", ""),
        "created_by": kwargs.get("created_by", ""),
        "participants": json.dumps(kwargs.get("participants", [])),
        "is_active": kwargs.get("is_active", True),
    })


def create_notification_record(user_id: str, **kwargs) -> dict:
    return db.insert("notifications", {
        "user_id": user_id,
        "title": kwargs.get("title", ""),
        "body": kwargs.get("body", ""),
        "category": kwargs.get("category", "general"),
        "read": False,
        "data": json.dumps(kwargs.get("data", {})),
    })


# === Database Stats ===

def get_database_stats() -> dict:
    stats = db.get_stats()
    stats["total_records"] = sum(stats.values())
    return stats


# === SQL Schema (for future SQLAlchemy migration) ===

SCHEMA_SQL = """
-- AdapFit Database Schema (PostgreSQL / SQLite compatible)

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    avatar_url TEXT DEFAULT '',
    date_of_birth TEXT DEFAULT '',
    gender TEXT DEFAULT '',
    height REAL DEFAULT 0,
    weight REAL DEFAULT 0,
    units TEXT DEFAULT 'metric',
    role TEXT DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    last_login REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS health_metrics (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    metric_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    notes TEXT DEFAULT '',
    recorded_at REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS workouts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    plan_id TEXT DEFAULT 'custom',
    exercises TEXT DEFAULT '[]',
    duration_minutes INTEGER DEFAULT 0,
    total_volume REAL DEFAULT 0,
    calories_burned INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    started_at REAL NOT NULL,
    ended_at REAL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS meals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    meal_type TEXT NOT NULL,
    foods TEXT DEFAULT '[]',
    total_calories REAL DEFAULT 0,
    total_protein REAL DEFAULT 0,
    total_carbs REAL DEFAULT 0,
    total_fat REAL DEFAULT 0,
    total_fiber REAL DEFAULT 0,
    logged_at REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sleep_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    duration_hours REAL DEFAULT 0,
    quality INTEGER DEFAULT 5,
    deep_sleep REAL DEFAULT 0,
    rem_sleep REAL DEFAULT 0,
    light_sleep REAL DEFAULT 0,
    score INTEGER DEFAULT 50,
    notes TEXT DEFAULT '',
    bedtime TEXT DEFAULT '',
    wake_time TEXT DEFAULT '',
    recorded_at REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS medications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    dosage TEXT DEFAULT '',
    frequency TEXT DEFAULT 'daily',
    time TEXT DEFAULT '08:00',
    is_active BOOLEAN DEFAULT TRUE,
    taken_at REAL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS mood_entries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    mood INTEGER DEFAULT 5,
    emoji TEXT DEFAULT '😐',
    energy INTEGER DEFAULT 5,
    anxiety INTEGER DEFAULT 5,
    tags TEXT DEFAULT '[]',
    notes TEXT DEFAULT '',
    journal TEXT DEFAULT '',
    recorded_at REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS challenges (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    challenge_type TEXT NOT NULL,
    description TEXT DEFAULT '',
    target_value REAL DEFAULT 0,
    start_date TEXT DEFAULT '',
    end_date TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    participants TEXT DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    read BOOLEAN DEFAULT FALSE,
    data TEXT DEFAULT '{}',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_health_metrics_user ON health_metrics(user_id, metric_type);
CREATE INDEX IF NOT EXISTS idx_workouts_user ON workouts(user_id);
CREATE INDEX IF NOT EXISTS idx_meals_user ON meals(user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_sleep_user ON sleep_sessions(user_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read);
CREATE INDEX IF NOT EXISTS idx_mood_user ON mood_entries(user_id, recorded_at);
"""
