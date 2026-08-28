/**
 * TRACK 8: Offline-first SQLite schema for Expo SQLite / WatermelonDB.
 * Provides instant local storage when offline, syncs when reconnected.
 *
 * Uses expo-sqlite synchronous API for maximum performance.
 */

import * as SQLite from 'expo-sqlite';

let db: SQLite.SQLiteDatabase | null = null;

export async function getDatabase(): Promise<SQLite.SQLiteDatabase> {
  if (!db) {
    db = await SQLite.openDatabaseAsync('adapfit.db');
    await initSchema(db);
  }
  return db;
}

async function initSchema(database: SQLite.SQLiteDatabase) {
  await database.execAsync(`
    PRAGMA journal_mode = WAL;
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS sync_queue (
      id TEXT PRIMARY KEY,
      table_name TEXT NOT NULL,
      record_id TEXT NOT NULL,
      operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'delete')),
      payload TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0,
      synced_at TEXT
    );

    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT,
      name TEXT,
      age INTEGER,
      weight_kg REAL,
      height_cm REAL,
      sex TEXT,
      fitness_level TEXT DEFAULT 'intermediate',
      primary_goal TEXT DEFAULT 'general',
      equipment_access TEXT DEFAULT '["bodyweight","dumbbells"]',
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS daily_recovery_logs (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      log_date TEXT NOT NULL,
      hrv_rmssd REAL,
      resting_heart_rate REAL,
      sleep_score REAL,
      sleep_duration_hours REAL,
      soreness_score INTEGER,
      fatigue_score INTEGER,
      stress_score INTEGER,
      sore_muscle_groups TEXT DEFAULT '[]',
      readiness_state TEXT DEFAULT 'MODERATE',
      recovery_score REAL,
      steps INTEGER DEFAULT 0,
      active_calories REAL DEFAULT 0,
      water_intake_ml INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0,
      UNIQUE(user_id, log_date)
    );

    CREATE TABLE IF NOT EXISTS workouts (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      title TEXT,
      target_date TEXT,
      readiness_state TEXT,
      recovery_score REAL,
      adaptation_rationale TEXT,
      target_duration_minutes INTEGER DEFAULT 45,
      actual_duration_minutes INTEGER,
      session_rpe REAL,
      completed INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS workout_sets (
      id TEXT PRIMARY KEY,
      workout_id TEXT NOT NULL,
      exercise_id TEXT NOT NULL,
      set_number INTEGER,
      weight_kg REAL,
      reps INTEGER,
      rpe REAL,
      rest_seconds INTEGER,
      completed INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS hydration_logs (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      log_date TEXT NOT NULL DEFAULT (date('now')),
      amount_ml INTEGER NOT NULL,
      drink_type TEXT DEFAULT 'water',
      logged_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS sleep_logs (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      log_date TEXT NOT NULL,
      duration_hours REAL,
      quality_score REAL,
      deep_sleep_minutes INTEGER,
      rem_sleep_minutes INTEGER,
      awakenings INTEGER DEFAULT 0,
      bedtime TEXT,
      wake_time TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0,
      UNIQUE(user_id, log_date)
    );

    CREATE TABLE IF NOT EXISTS cached_exercises (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      category TEXT,
      primary_muscles TEXT DEFAULT '[]',
      equipment TEXT,
      mechanics TEXT,
      axial_loading_rating INTEGER DEFAULT 3,
      gif_url TEXT,
      instructions TEXT DEFAULT '[]'
    );

    CREATE TABLE IF NOT EXISTS body_composition_logs (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      log_date TEXT NOT NULL,
      weight_kg REAL,
      body_fat_pct REAL,
      muscle_mass_kg REAL,
      waist_cm REAL,
      hips_cm REAL,
      chest_cm REAL,
      arms_cm REAL,
      thighs_cm REAL,
      created_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS training_schedule (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      schedule_date TEXT NOT NULL,
      workout_type TEXT,
      title TEXT,
      target_duration_minutes INTEGER,
      status TEXT DEFAULT 'scheduled',
      workout_id TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      synced INTEGER DEFAULT 0,
      UNIQUE(user_id, schedule_date)
    );

    CREATE INDEX IF NOT EXISTS idx_recovery_date ON daily_recovery_logs(user_id, log_date DESC);
    CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(user_id, target_date DESC);
    CREATE INDEX IF NOT EXISTS idx_hydration_date ON hydration_logs(user_id, log_date DESC);
    CREATE INDEX IF NOT EXISTS idx_sync_pending ON sync_queue(synced, created_at);
  `);
}

// ============================================================
// Sync Queue Operations
// ============================================================

export interface SyncMutation {
  table_name: string;
  record_id: string;
  operation: 'create' | 'update' | 'delete';
  payload: Record<string, unknown>;
}

export async function enqueueSync(database: SQLite.SQLiteDatabase, mutation: SyncMutation) {
  const id = `sync_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  await database.runAsync(
    `INSERT INTO sync_queue (id, table_name, record_id, operation, payload, created_at)
     VALUES (?, ?, ?, ?, ?, datetime('now'))`,
    [id, mutation.table_name, mutation.record_id, mutation.operation, JSON.stringify(mutation.payload)]
  );
}

export async function getPendingSync(database: SQLite.SQLiteDatabase): Promise<(SyncMutation & { id: string })[]> {
  const rows = await database.getAllAsync<{ id: string; table_name: string; record_id: string; operation: string; payload: string }>(
    `SELECT id, table_name, record_id, operation, payload FROM sync_queue WHERE synced = 0 ORDER BY created_at ASC LIMIT 100`
  );
  return rows.map((r) => ({
    id: r.id,
    table_name: r.table_name,
    record_id: r.record_id,
    operation: r.operation as SyncMutation['operation'],
    payload: JSON.parse(r.payload),
  }));
}

export async function markSynced(database: SQLite.SQLiteDatabase, ids: string[]) {
  if (ids.length === 0) return;
  const placeholders = ids.map(() => '?').join(',');
  await database.runAsync(
    `UPDATE sync_queue SET synced = 1, synced_at = datetime('now') WHERE id IN (${placeholders})`,
    ids
  );
}

export async function getSyncStats(database: SQLite.SQLiteDatabase): Promise<{
  pending: number;
  synced: number;
  total: number;
}> {
  const row = await database.getFirstAsync<{ pending: number; synced: number; total: number }>(
    `SELECT
       SUM(CASE WHEN synced = 0 THEN 1 ELSE 0 END) as pending,
       SUM(CASE WHEN synced = 1 THEN 1 ELSE 0 END) as synced,
       COUNT(*) as total
     FROM sync_queue`
  );
  return { pending: row?.pending || 0, synced: row?.synced || 0, total: row?.total || 0 };
}
