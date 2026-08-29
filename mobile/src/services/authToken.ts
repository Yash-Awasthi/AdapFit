import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = '@adapfit/access_token';

/**
 * Cached in memory so the request path stays synchronous — AsyncStorage is
 * only touched on login, logout, and the one restore at startup.
 */
let accessToken: string | null = null;

export async function restoreToken(): Promise<void> {
  try {
    accessToken = await AsyncStorage.getItem(STORAGE_KEY);
  } catch {
    accessToken = null;
  }
}

export async function setToken(token: string | null): Promise<void> {
  accessToken = token;
  try {
    if (token) await AsyncStorage.setItem(STORAGE_KEY, token);
    else await AsyncStorage.removeItem(STORAGE_KEY);
  } catch {
    /* in-memory token still applies for this session */
  }
}

export function getToken(): string | null {
  return accessToken;
}

/** Authorization header for a request, or an empty object when signed out. */
export function authHeader(): Record<string, string> {
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}
