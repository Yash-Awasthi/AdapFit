/**
 * In-memory cache with TTL for API responses, backed by AsyncStorage so the
 * last-known value survives app restarts and network loss (subterranean gym
 * scenario: no signal, but yesterday's data is still on screen).
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

const store = new Map<string, CacheEntry<any>>();
const DEFAULT_TTL = 60_000; // 1 minute
const PERSIST_PREFIX = 'adapfit:cache:';

export const cache = {
  get<T>(key: string): T | null {
    const entry = store.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      store.delete(key);
      return null;
    }
    return entry.data as T;
  },

  set<T>(key: string, data: T, ttlMs: number = DEFAULT_TTL): void {
    store.set(key, {
      data,
      expiresAt: Date.now() + ttlMs,
    });
    AsyncStorage.setItem(PERSIST_PREFIX + key, JSON.stringify(data)).catch(() => {});
  },

  invalidate(keyPrefix: string): void {
    for (const key of store.keys()) {
      if (key.startsWith(keyPrefix)) {
        store.delete(key);
      }
    }
  },

  clear(): void {
    store.clear();
  },

  /** Last value written for this key, even if expired or the app was restarted since. */
  async getPersisted<T>(key: string): Promise<T | null> {
    const fresh = store.get(key);
    if (fresh) return fresh.data as T;
    try {
      const raw = await AsyncStorage.getItem(PERSIST_PREFIX + key);
      return raw ? (JSON.parse(raw) as T) : null;
    } catch {
      return null;
    }
  },
};
