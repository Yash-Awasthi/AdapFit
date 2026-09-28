/**
 * Consent, account deletion and legal documents (DPDP Act). The server is the
 * record of consent; this module only reads and changes it.
 */
import { API_V1 } from './config';
import { authHeader } from './authToken';
import { getJson } from './http';

export type PurposeId = 'health_data' | 'ai' | 'sharing' | 'analytics';

export interface Purpose {
  title: string;
  detail: string;
  required: boolean;
  granted?: boolean;
  at?: string | null;
}

export interface ConsentState {
  policy_version: string;
  purposes: Record<PurposeId, Purpose>;
  needs_consent: boolean;
  minor: boolean;
  guardian_pending: boolean;
  guardian: { name: string; relationship: string; confirmed_at: string } | null;
  deletion_due_at: number | null;
}

export const DOCUMENTS = [
  { id: 'privacy-policy', title: 'Privacy Policy' },
  { id: 'terms', title: 'Terms of Service' },
  { id: 'medical-disclaimer', title: 'Health Disclaimer' },
] as const;

export function isBlocked(state: ConsentState | null): boolean {
  return !!state && (state.needs_consent || state.guardian_pending || !!state.deletion_due_at);
}

export const getConsent = () => getJson<ConsentState>('/privacy/consent');

export const getPurposes = () =>
  getJson<{ policy_version: string; adult_age: number; purposes: Record<PurposeId, Purpose> }>('/privacy/consent/purposes');

/** Resolves to the new state, or throws with the server's reason. */
async function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_V1}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Server returned ${res.status}`);
  return data as T;
}

export const setConsent = (choices: Partial<Record<PurposeId, boolean>>) =>
  send<ConsentState>('/privacy/consent', 'PUT', { choices });

export const resendGuardianEmail = () => send<{ sent: boolean }>('/privacy/guardian/resend', 'POST');

export const requestDeletion = (password: string) =>
  send<{ deletion_due_at: number; grace_minutes: number }>('/auth/delete-account', 'POST', { password });

export const cancelDeletion = () => send<{ cancelled: boolean }>('/auth/delete-account/cancel', 'POST');

export async function getDocument(id: string): Promise<string | null> {
  try {
    const res = await fetch(`${API_V1}/privacy/documents/${id}`);
    return res.ok ? await res.text() : null;
  } catch {
    return null;
  }
}
