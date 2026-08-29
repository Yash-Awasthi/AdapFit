/**
 * Performance utilities for the health app.
 * Lazy loading, image optimization, list virtualization helpers.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';

// Skeleton loading component factory
export function createSkeletonScreen(config: {
  rows?: number;
  hasHeader?: boolean;
  hasCards?: boolean;
  cardHeight?: number;
}) {
  return function SkeletonLoader() {
    const { rows = 5, hasHeader = true, hasCards = false, cardHeight = 80 } = config;
    return { rows, hasHeader, hasCards, cardHeight };
  };
}

// Debounced value hook for search inputs
export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// Pagination helper
export function usePagination<T>(items: T[], pageSize: number = 20) {
  const [page, setPage] = useState(1);
  const totalPages = Math.ceil(items.length / pageSize);
  const paginatedItems = useMemo(
    () => items.slice((page - 1) * pageSize, page * pageSize),
    [items, page, pageSize]
  );

  return {
    items: paginatedItems,
    page,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1,
    nextPage: () => setPage(p => Math.min(p + 1, totalPages)),
    prevPage: () => setPage(p => Math.max(p - 1, 1)),
    goToPage: (p: number) => setPage(Math.max(1, Math.min(p, totalPages))),
  };
}

// Lazy loading state hook
export function useLazyLoad<T>(
  fetcher: () => Promise<T>,
  deps: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (e: any) {
      setError(e.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, reload: load };
}

// Image cache utility
const imageCache = new Map<string, string>();
export function getCachedImage(uri: string): string {
  return imageCache.get(uri) || uri;
}

export function setCachedImage(uri: string, localUri: string): void {
  imageCache.set(uri, localUri);
}

// Skeleton animation timing
export const SKELETON_TIMING = {
  duration: 800,
  useNativeDriver: true,
};

// Color palette for skeleton shimmer
export const SKELETON_COLORS = {
  base: '#1E293B',
  highlight: '#334155',
};

// Performance monitoring
export function measureRender(name: string) {
  if (__DEV__) {
    const start = performance.now();
    return () => {
      const end = performance.now();
      if (end - start > 16) {
        console.warn(`[PERF] ${name} took ${(end - start).toFixed(1)}ms (slow render)`);
      }
    };
  }
  return () => {};
}
