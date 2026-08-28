import { cache } from './cache';
import { API_BASE_URL } from './config';

const API = API_BASE_URL;
const CACHE_TTL = 60_000; // 1 minute
const LONG_CACHE_TTL = 300_000; // 5 minutes

async function request<T>(path: string, options?: RequestInit, ttl: number = CACHE_TTL): Promise<T> {
  // Only cache GET requests
  const method = options?.method || 'GET';
  if (method === 'GET') {
    const cached = cache.get<T>(path);
    if (cached) return cached;
  }

  try {
    const res = await fetch(`${API}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status}`);
    }
    const data = await res.json();

    // Cache GET responses
    if (method === 'GET') {
      cache.set(path, data, ttl);
    }

    return data;
  } catch (err) {
    // Offline or server unreachable — serve the last known value for GETs
    // rather than a blank screen. Writes still fail loudly (caller queues/retries).
    if (method === 'GET') {
      const stale = await cache.getPersisted<T>(path);
      if (stale !== null) return stale;
    }
    throw err;
  }
}

export const api = {
  // Users
  createUser: (data: { email: string; name?: string }) =>
    request<{ id: string; email: string; name: string | null }>(
      '/api/v1/users',
      { method: 'POST', body: JSON.stringify(data) }
    ),

  getUser: (id: string) =>
    request<{
      id: string; email: string; name: string | null; fitness_level: string;
      primary_goal: string; preferred_days_per_week: number;
      age?: number | null; gender?: string | null; height_cm?: number | null;
      work_start?: string | null; work_end?: string | null;
    }>(`/api/v1/users/${id}`),

  updateUser: async (id: string, data: Record<string, any>) => {
    const result = await request<any>(`/api/v1/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
    cache.invalidate(`/api/v1/users/${id}`);
    return result;
  },

  // Recovery
  getRecoveryLogs: (userId: string, days = 28) =>
    request<{ items: any[]; count: number }>(
      `/api/v1/recovery-logs?user_id=${userId}&days=${days}`
    ),

  createRecoveryLog: (data: any) =>
    request<any>('/api/v1/recovery-logs', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Workouts
  getWorkouts: (userId: string, days = 14) =>
    request<{ items: any[]; count: number }>(
      `/api/v1/workouts?user_id=${userId}&days=${days}`
    ),

  generateWorkout: (data: any) =>
    request<any>('/api/v1/workouts', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  completeWorkout: (workoutId: string, data: any) =>
    request<any>(`/api/v1/workouts/${workoutId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Exercises (longer cache - catalog rarely changes)
  getExercises: (params?: { category?: string; equipment?: string; page?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set('category', params.category);
    if (params?.equipment) searchParams.set('equipment', params.equipment);
    if (params?.page) searchParams.set('page', String(params.page));
    return request<{ items: any[]; total: number; pages: number }>(
      `/api/v1/exercises?${searchParams}`,
      undefined,
      LONG_CACHE_TTL
    );
  },

  // Chat & AI Coach
  chat: (
    userId: string,
    message: string,
    history: { role: string; content: string }[] = [],
    llmOverride?: { provider: string; api_key: string; model?: string; base_url?: string }
  ) =>
    request<{ reply: string; intent: string | null; follow_up_suggestions?: string[] }>(
      '/api/v1/chat',
      { method: 'POST', body: JSON.stringify({ user_id: userId, message, history, llm_override: llmOverride }) }
    ),

  getMemoryContext: (userId: string) =>
    request<{ user_id: string; context: string; token_estimate: number }>(
      `/api/v1/memory/context/${userId}`
    ),

  // Mental Health
  logMood: (data: any) =>
    request<any>('/api/v1/mental-health', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMoodTrend: (userId: string, days = 7) =>
    request<{ avg_mood: number; avg_energy: number; avg_anxiety: number; mood_trend: string; count: number }>(
      `/api/v1/mental-health?user_id=${userId}&days=${days}`
    ),

  getBreathingExercises: () =>
    request<{ id: string; name: string; inhale_sec: number; hold_sec: number; exhale_sec: number }[]>(
      '/api/v1/mental-health/breathing-exercises',
      undefined,
      LONG_CACHE_TTL // 5 min - breathing exercises never change
    ),

  // Meditation
  getMeditationSessions: () =>
    request<{
      sessions: {
        id: string; name: string; category: string; duration_minutes: number;
        difficulty: string; benefits: string[]; best_time: string; tags: string[];
        steps_count: number;
      }[];
    }>('/api/v1/meditation', undefined, LONG_CACHE_TTL),

  getMeditationSession: (sessionId: string) =>
    request<{
      id: string; name: string; category: string; duration_minutes: number;
      difficulty: string;
      steps: { step: number; instruction: string; duration_seconds: number }[];
      benefits: string[]; best_time: string; tags: string[];
    }>(`/api/v1/meditation/${sessionId}`, undefined, LONG_CACHE_TTL),

  // Trends & Injury Risk
  getAcwr: (userId: string) =>
    request<{ acwr: number; acwr_status: string; acute_workload_7d: number; chronic_workload_28d: number }>(
      `/api/v1/trends/acwr?user_id=${userId}`
    ),

  getHrvTrend: (userId: string, days = 28) =>
    request<{ hrv_history: number[]; forecast: any; anomalies: any }>(
      `/api/v1/trends/hrv?user_id=${userId}&days=${days}`
    ),

  getMlInsights: (userId: string) =>
    request<{ readiness_prediction: any; hrv_forecast: any; model_status: any }>(
      `/api/v1/trends/ml-insights?user_id=${userId}`
    ),

  getInjuryRisk: (userId: string, injuryHistory?: any[]) =>
    request<{
      user_id: string;
      overall_risk_score: number;
      risk_level: string;
      vulnerable_regions: string[];
      top_factors: string[];
      recommendations: { priority?: string; action: string; reason?: string }[];
    }>(
      '/api/v1/injury-risk/analyze',
      { method: 'POST', body: JSON.stringify({ user_id: userId, injury_history: injuryHistory }) }
    ),

  getInjuryRiskTrend: (userId: string, weeks = 4) =>
    request<{ user_id: string; weekly_trends: any[]; trend_direction: string }>(
      `/api/v1/injury-risk/trend/${userId}?weeks=${weeks}`
    ),

  // AI Meal Planning
  generateMealPlan: (data: {
    weight_kg: number;
    goal?: string;
    body_fat_pct?: number;
    activity_level?: string;
    dietary_restrictions?: string[];
    training_day?: boolean;
    recovery_score?: number;
  }, userId: string = 'default') =>
    request<any>(`/api/v1/meal-plan/generate?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getCurrentMealPlan: (userId: string) =>
    request<any>(`/api/v1/meal-plan/current?user_id=${userId}`),

  getMealPlanTargets: (data: {
    weight_kg: number;
    goal?: string;
    body_fat_pct?: number;
    activity_level?: string;
  }) =>
    request<any>('/api/v1/meal-plan/targets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Hydration Tracking
  getHydrationToday: (userId: string) =>
    request<{
      date: string;
      total_ml: number;
      daily_goal_ml: number;
      progress_pct: number;
      goal_met: boolean;
      log_count: number;
      drink_breakdown: Record<string, number>;
    }>(`/api/v1/hydration/today?user_id=${userId}`),

  logHydration: (userId: string, amount_ml: number, drink_type = 'water', note?: string) =>
    request<any>(`/api/v1/hydration/log?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ amount_ml, drink_type, note }),
    }),

  getHydrationStats: (userId: string, days = 14) =>
    request<any>(`/api/v1/hydration/stats?user_id=${userId}&days=${days}`),

  // Warmup & Cooldown Routines
  getWarmupRoutine: (muscles: string[] = ['chest', 'back', 'quadriceps']) =>
    request<any>(`/api/v1/routine/warmup?target_muscles=${encodeURIComponent(muscles.join(','))}`),

  getCooldownRoutine: (muscles: string[] = ['chest', 'back', 'quadriceps']) =>
    request<any>(`/api/v1/routine/cooldown?target_muscles=${encodeURIComponent(muscles.join(','))}`),

  getFullRoutine: (muscles: string[] = ['chest', 'back', 'quadriceps']) =>
    request<any>(`/api/v1/routine/full?target_muscles=${encodeURIComponent(muscles.join(','))}`),

  // Photo-based meal logging
  photoLogMeal: (imageBase64: string, mealType = 'snack', userId = 'default') =>
    request<{
      logged: boolean;
      record: any;
      foods: { name: string; portion_grams: number; calories: number }[];
      confidence: number;
      suggestions: string[];
    }>(`/api/v1/diet/photo-log?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ image_base64: imageBase64, meal_type: mealType }),
    }),

  // Voice & Natural Language Workout Logging
  parseVoiceWorkout: (text: string) =>
    request<{
      raw_text: string;
      normalized_text: string;
      parsed_set: {
        exercise_name: string | null;
        weight_kg: number | null;
        reps: number | null;
        rpe: number | null;
      };
      confidence: number;
      voice_feedback: string;
    }>('/api/v1/voice/parse', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  parseNlWorkout: (text: string, userId = 'default') =>
    request<any>('/api/v1/nl-workout', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, text, auto_log: true }),
    }),

  // Cycle Tracking
  logCycle: (userId: string, data: {
    start_date: string; length_days?: number; period_length_days?: number;
    symptoms?: string[]; mood?: number; energy?: number; cramping?: boolean; notes?: string;
  }) =>
    request<any>(`/api/v1/cycle/log?user_id=${userId}`, { method: 'POST', body: JSON.stringify(data) }),

  getCurrentCyclePhase: (userId: string) =>
    request<any>(`/api/v1/cycle/current?user_id=${userId}`),

  getCycleCalendar: (userId: string, months = 3) =>
    request<{ calendar: { date: string; phase: string; day_in_cycle: number }[] }>(
      `/api/v1/cycle/calendar?user_id=${userId}&months=${months}`
    ),

  // Form Check (pose estimation)
  getFormCheckExercises: () =>
    request<{ exercise_ids: string[]; model_available: boolean }>('/api/v1/form-check/exercises'),

  analyzeForm: (exerciseId: string, imageBase64: string) =>
    request<{
      detected: boolean; exercise_id: string; angle?: number; grade?: string;
      penalties: string[]; suggestions: string[]; rep_quality_pct?: number; message?: string;
    }>('/api/v1/form-check/analyze', {
      method: 'POST',
      body: JSON.stringify({ exercise_id: exerciseId, image_base64: imageBase64 }),
    }),

  analyzeFormBatch: (exerciseId: string, frames: string[]) =>
    request<{
      exercise_id: string; total_reps: number;
      frames: { frame_index: number; detected: boolean; angle?: number; grade?: string;
        rep_count: number; rep_completed: boolean; rep_state: string; message?: string }[];
      average_grade?: string; grade_distribution: Record<string, number>; suggestions: string[];
    }>('/api/v1/form-check/analyze-batch', {
      method: 'POST',
      body: JSON.stringify({ exercise_id: exerciseId, frames, reset_counter: true }),
    }),

  // Voice Engine (STT + TTS)
  transcribeAudio: async (audioBase64: string, userId: string) => {
    // Multipart upload — must NOT set Content-Type (boundary is auto-generated)
    const res = await fetch(`${API}/api/v1/voice-engine/transcribe-base64`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audio_base64: audioBase64, filename: 'recording.m4a', user_id: userId }),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json() as Promise<{ text: string; language: string; confidence: number; available: boolean }>;
  },

  synthesizeSpeech: (text: string, voice = 'coach_female') =>
    request<{ ok: boolean; audio_base64: string; format: string; duration: number }>(
      '/api/v1/voice-engine/speak',
      { method: 'POST', body: JSON.stringify({ text, voice }) }
    ),

  // Sleep
  getSleepAnalysis: (userId: string, days = 7) =>
    request<{
      score: number; grade: string; consistency_score: number;
      avg_duration_hours: number; avg_efficiency: number;
      deep_sleep_pct: number; rem_sleep_pct: number;
      consistency_trend: string; recommendations: string[];
      stage_breakdown: { name: string; minutes: number; percentage: number }[];
    }>(`/api/v1/sleep/analysis?user_id=${userId}&days=${days}`),

  // Health Status
  health: () =>
    request<{ status: string; version: string; services: any }>('/health'),

  // Generic POST, used by the offline sync daemon for batch endpoints
  post: (path: string, body: any) =>
    request<any>(path, { method: 'POST', body: JSON.stringify(body) }),
};
