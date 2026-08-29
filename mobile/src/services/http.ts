/**
 * Fetch helper for screens that talk to the API directly.
 *
 * Carries the Authorization header and, critically, never hands an error body
 * back to a caller: a 401 responds with {"detail": "..."}, which is truthy and
 * renders as data right up until the first missing field throws.
 */
import { API_V1 } from './config';
import { authHeader } from './authToken';

/** GET that returns null instead of throwing or handing back an error body. */
export async function getJson<T>(path: string): Promise<T | null> {
  return sendJson<T>(path, 'GET');
}

export async function postJson<T>(path: string, body?: unknown): Promise<T | null> {
  return sendJson<T>(path, 'POST', body);
}

async function sendJson<T>(path: string, method: string, body?: unknown): Promise<T | null> {
  try {
    const res = await fetch(path.startsWith('http') ? path : `${API_V1}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Coerce a value that should be an array into one.
 *
 * Guards the render path against an endpoint returning null, an error object,
 * or a renamed field, which is what turns a bad response into a white screen.
 */
export function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

/** Coerce a value that should be a finite number, falling back to `fallback`. */
export function asNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}
