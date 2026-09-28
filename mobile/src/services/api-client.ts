/**
 * Typed API client with Zod runtime validation.
 * Replaces raw fetch calls with validated, type-safe requests.
 */
import { z } from 'zod';
import { API_V1 } from './config';
import { authedFetch } from './authToken';

// ===== Zod Schemas =====

export const StressResponseSchema = z.object({
  overall_score: z.number(),
  factors: z.record(z.string(), z.number()).optional(),
});

export const WellbeingReportSchema = z.object({
  step_count: z.number().optional(),
  mood_score: z.number().optional(),
  energy_level: z.number().optional(),
});

export const SleepLogResponseSchema = z.object({
  quality_score: z.number(),
  duration_minutes: z.number().optional(),
  stages: z.record(z.string(), z.number()).optional(),
});

export const HealthScoreSchema = z.object({
  score: z.number().min(0).max(100),
  breakdown: z.object({
    heart: z.number().optional(),
    sleep: z.number().optional(),
    activity: z.number().optional(),
  }).optional(),
});

// ===== API Client =====

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

async function request<T>(
  path: string,
  schema: z.ZodSchema<T>,
  options: RequestOptions = {},
): Promise<T | null> {
  try {
    const { body, ...fetchOptions } = options;
    const response = await authedFetch(`${API_V1}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...fetchOptions,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      console.warn(`[API] ${response.status}: ${path}`);
      return null;
    }

    const json = await response.json();
    const result = schema.safeParse(json);
    if (!result.success) {
      console.warn(`[API] Zod validation failed for ${path}:`, result.error.issues);
      return null;
    }
    return result.data;
  } catch (err) {
    console.error(`[API] Request failed for ${path}:`, err);
    return null;
  }
}

// ===== Typed API Functions =====

export async function assessStress(params: {
  mood_score: number;
  energy_level: number;
  sleep_quality: number;
}) {
  return request('/stress/assess', StressResponseSchema, {
    method: 'POST',
    body: params,
  });
}

export async function getWellbeingReport() {
  return request('/wellbeing/report', WellbeingReportSchema);
}

export async function logSleep(params: {
  bedtime: string;
  wake_time: string;
  quality_score: number;
}) {
  return request('/sleep/log', SleepLogResponseSchema, {
    method: 'POST',
    body: params,
  });
}

export async function getHealthScore(userId: string) {
  return request(`/health/score/${userId}`, HealthScoreSchema);
}
