/**
 * Screen-level data loading.
 *
 * Every feature screen needs the same four things — the value, a first-load
 * flag, pull-to-refresh, and a way to reload after a write — and writing them
 * out per screen is where the loading state ends up missing from one of them.
 *
 * `getJson` returns null rather than throwing, so a failed request renders the
 * screen's empty state instead of a crash. Screens that need to tell "failed"
 * from "no data yet" apart should check `data === null` after `loading`.
 */
import { useCallback, useEffect, useState } from 'react';

import { getJson } from '../services/http';

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  refreshing: boolean;
  refresh: () => Promise<void>;
  reload: () => Promise<void>;
}

export function useApi<T>(path: string | null, deps: unknown[] = []): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (path === null) {
      setLoading(false);
      return;
    }
    const result = await getJson<T>(path);
    setData(result);
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...deps]);

  useEffect(() => {
    load();
  }, [load]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  return { data, loading, refreshing, refresh, reload: load };
}

/**
 * Two or more endpoints that make up one screen.
 *
 * Fetched together rather than in sequence: a screen with four panels should
 * not take four round trips to appear.
 */
export function useApis<T extends Record<string, unknown>>(
  paths: { [K in keyof T]: string } | null,
): { data: Partial<T>; loading: boolean; refreshing: boolean; refresh: () => Promise<void>; reload: () => Promise<void> } {
  const [data, setData] = useState<Partial<T>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const key = paths ? JSON.stringify(paths) : '';

  const load = useCallback(async () => {
    if (!paths) {
      setLoading(false);
      return;
    }
    const entries = Object.entries(paths) as [keyof T, string][];
    const results = await Promise.all(entries.map(([, path]) => getJson(path)));
    const next: Partial<T> = {};
    entries.forEach(([name], i) => {
      next[name] = results[i] as T[keyof T];
    });
    setData(next);
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    load();
  }, [load]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  return { data, loading, refreshing, refresh, reload: load };
}
