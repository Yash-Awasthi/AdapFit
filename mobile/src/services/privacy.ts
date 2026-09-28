/**
 * Consent, account deletion and legal documents (DPDP Act). The server is the
 * record of consent; this module only reads and changes it.
 */
import { API_V1 } from './config';
import { authedFetch } from './authToken';
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

export type SecurityEvent = { at: number; event: string; ip: string; actor_id: string; user_id: string };

/** Plain words for the events a user can see in their own security log. */
export const SECURITY_EVENT_LABELS: Record<string, string> = {
  register: 'Account created',
  login_success: 'Signed in',
  login_failed_bad_password: 'Wrong password entered',
  account_locked: 'Sign-in locked after failed attempts',
  login_locked: 'Sign-in tried while locked',
  password_changed: 'Password changed',
  password_reset_requested: 'Password reset email sent',
  password_reset: 'Password reset',
  sessions_revoked: 'Signed out on all devices',
  refresh_token_reuse: 'Old session reused; all devices signed out',
  export_all: 'Everything exported',
  consent_changed: 'Consent choices changed',
  deletion_requested: 'Account deletion requested',
  admin_access: 'Support staff opened your records',
  vault_shared: 'Vault record shared',
  vault_share_read: 'Shared vault record opened',
  vault_share_revoked: 'Vault share revoked',
};

export const getSecurityActivity = (limit = 20) =>
  getJson<{ entries: SecurityEvent[] }>(`/auth/activity?limit=${limit}`);

export const getPurposes = () =>
  getJson<{ policy_version: string; adult_age: number; purposes: Record<PurposeId, Purpose> }>('/privacy/consent/purposes');

/** Resolves to the new state, or throws with the server's reason. */
async function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  const res = await authedFetch(`${API_V1}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
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
