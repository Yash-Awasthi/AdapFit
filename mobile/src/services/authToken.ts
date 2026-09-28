import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { API_V1 } from './config';

const ACCESS_KEY = 'adapfit.access_token';
const REFRESH_KEY = 'adapfit.refresh_token';
// Where the access token lived before it moved to the keystore; removed on first start.
const LEGACY_KEY = '@adapfit/access_token';

export type TokenPair = { access_token?: string | null; refresh_token?: string | null };

/**
 * Tokens live in the Android Keystore / iOS Keychain, cached in memory so the
 * request path stays synchronous. The web build has no keystore and keeps them
 * in memory only, so a reload signs out there.
 */
let accessToken: string | null = null;
let refreshToken: string | null = null;
let refreshing: Promise<boolean> | null = null;
let onSignedOut: (() => void) | null = null;

const secure = Platform.OS !== 'web';

async function read(key: string): Promise<string | null> {
  return secure ? SecureStore.getItemAsync(key) : null;
}

async function write(key: string, value: string | null): Promise<void> {
  if (!secure) return;
  if (value) await SecureStore.setItemAsync(key, value, { keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK });
  else await SecureStore.deleteItemAsync(key);
}

export async function restoreToken(): Promise<void> {
  try {
    accessToken = await read(ACCESS_KEY);
    refreshToken = await read(REFRESH_KEY);
    await AsyncStorage.removeItem(LEGACY_KEY);
  } catch {
    accessToken = null;
    refreshToken = null;
  }
}

export async function setTokens(tokens: TokenPair | null): Promise<void> {
  accessToken = tokens?.access_token ?? null;
  refreshToken = tokens?.refresh_token ?? null;
  try {
    await write(ACCESS_KEY, accessToken);
    await write(REFRESH_KEY, refreshToken);
  } catch {
    /* in-memory tokens still apply for this session */
  }
}

export function getToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  return refreshToken;
}

/** Called once when a refresh fails for good, so the app can return to sign-in. */
export function setSignedOutHandler(handler: (() => void) | null): void {
  onSignedOut = handler;
}

/** Authorization header for a request, or an empty object when signed out. */
export function authHeader(): Record<string, string> {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

/** Swap the refresh token for a new pair. Concurrent callers share one request: a token works only once. */
export function refreshSession(): Promise<boolean> {
  if (!refreshToken) return Promise.resolve(false);
  if (!refreshing) {
    const used = refreshToken;
    refreshing = (async () => {
      try {
        const res = await fetch(`${API_V1}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: used }),
        });
        if (res.ok) {
          const data = await res.json();
          await setTokens(data.tokens);
          return true;
        }
        if (res.status === 401) {
          await setTokens(null);
          onSignedOut?.();
        }
        return false;
      } catch {
        return false;
      } finally {
        refreshing = null;
      }
    })();
  }
  return refreshing;
}

/** fetch() for our own API: adds the Authorization header, and on 401 refreshes the session once and retries. */
export async function authedFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const send = () =>
    fetch(input, { ...init, headers: { ...((init.headers as Record<string, string>) ?? {}), ...authHeader() } });
  const res = await send();
  if (res.status !== 401 || !refreshToken) return res;
  return (await refreshSession()) ? send() : res;
}
