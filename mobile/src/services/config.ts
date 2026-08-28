import { Platform } from 'react-native';

/**
 * Central API configuration.
 *
 * Resolution order:
 *   1. EXPO_PUBLIC_API_URL env var (set in .env or when launching expo) —
 *      relies on Metro inlining this at build time, which can go stale
 *      across cached builds, so it's not trusted alone in release builds.
 *   2. In a release build (__DEV__ false): the deployed backend.
 *   3. In a dev build: local loopback for the platform.
 *
 * For a physical device in dev, set EXPO_PUBLIC_API_URL to your machine's
 * LAN IP, e.g.  EXPO_PUBLIC_API_URL=http://192.168.1.20:8000 npx expo start
 */
const PRODUCTION_API = 'https://adapfit-production.up.railway.app';
const DEFAULT_HOST = Platform.OS === 'android' ? '10.0.2.2' : 'localhost';
const DEV_FALLBACK_API = `http://${DEFAULT_HOST}:8000`;

const ENV_API: string | undefined = (process.env as any).EXPO_PUBLIC_API_URL;

export const API_BASE_URL: string =
  ENV_API?.trim() || (__DEV__ ? DEV_FALLBACK_API : PRODUCTION_API);

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