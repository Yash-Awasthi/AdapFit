import { Platform } from 'react-native';

/**
 * Central API configuration.
 *
 * Resolution order:
 *   1. EXPO_PUBLIC_API_URL env var (set in .env or when launching expo)
 *   2. Platform default:
 *      - Android emulator  -> http://10.0.2.2:8000 (host loopback)
 *      - iOS simulator/web -> http://localhost:8000
 *   3. Fallback: http://localhost:8000
 *
 * For a physical device, set EXPO_PUBLIC_API_URL to your machine's LAN IP,
 * e.g.  EXPO_PUBLIC_API_URL=http://192.168.1.20:8000 npx expo start
 */
const DEFAULT_HOST = Platform.OS === 'android' ? '10.0.2.2' : 'localhost';
const FALLBACK_API = `http://${DEFAULT_HOST}:8000`;

const ENV_API: string | undefined = (process.env as any).EXPO_PUBLIC_API_URL;

export const API_BASE_URL: string = ENV_API?.trim() || FALLBACK_API;

export const WS_BASE_URL: string = API_BASE_URL.replace(/^http/, 'ws');

export const API_V1 = `${API_BASE_URL}/api/v1`;

/** Resolve a relative /api/v1 path against the configured base. */
export function apiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

/** Resolve a websocket path against the configured base. */
export function wsUrl(path: string): string {
  if (/^wss?:\/\//.test(path)) return path;
  return `${WS_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}