/**
 * Run recording with the screen off.
 *
 * Location updates come from a foreground service (a persistent notification
 * while recording), which Android allows with the "while using the app"
 * permission because the user starts it. Fixes are queued in storage and
 * uploaded in batches, so a dead zone or a killed app loses nothing already
 * received; the server filters inaccurate fixes and computes the stats.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { postJson } from './http';

export const RUN_TASK = 'adapfit-run-location';
const ACTIVE_KEY = 'adapfit.run.active';
const QUEUE_KEY = 'adapfit.run.queue';
const BATCH = 20;

export type Fix = { lat: number; lon: number; altitude: number | null; accuracy_m: number | null; timestamp: string };
export type ActiveRun = { routeId: string; workoutType: string; startedAt: number };
export type LiveStats = { distance_m: number; duration_seconds: number; avg_pace_seconds_per_km: number; coordinates_used: number };

let listeners: ((fixes: Fix[]) => void)[] = [];
let flushing: Promise<void> | null = null;

async function readQueue(): Promise<Fix[]> {
  try {
    return JSON.parse((await AsyncStorage.getItem(QUEUE_KEY)) || '[]');
  } catch {
    return [];
  }
}

// Task events can overlap; read-modify-write of the queue must not interleave or fixes are lost.
let queueLock: Promise<unknown> = Promise.resolve();
function editQueue(change: (q: Fix[]) => Fix[]): Promise<Fix[]> {
  const next = queueLock.then(async () => {
    const q = change(await readQueue());
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(q));
    return q;
  });
  queueLock = next.catch(() => undefined);
  return next;
}

export async function activeRun(): Promise<ActiveRun | null> {
  try {
    return JSON.parse((await AsyncStorage.getItem(ACTIVE_KEY)) || 'null');
  } catch {
    return null;
  }
}

/** Upload queued fixes; whatever fails stays queued for the next attempt. */
export function flush(): Promise<void> {
  if (!flushing) {
    flushing = (async () => {
      try {
        const run = await activeRun();
        let queue = await readQueue();
        while (run && queue.length) {
          const batch = queue.slice(0, 500);
          const res = await postJson<{ live_stats: LiveStats }>(`/gps/${run.routeId}/points`, { coordinates: batch });
          if (!res) break;
          queue = await editQueue((q) => q.slice(batch.length));
        }
      } finally {
        flushing = null;
      }
    })();
  }
  return flushing;
}

TaskManager.defineTask(RUN_TASK, async ({ data, error }: TaskManager.TaskManagerTaskBody<{ locations: Location.LocationObject[] }>) => {
  if (error || !data?.locations?.length) return;
  const fixes: Fix[] = data.locations.map((l) => ({
    lat: l.coords.latitude, lon: l.coords.longitude, altitude: l.coords.altitude ?? null,
    accuracy_m: l.coords.accuracy ?? null, timestamp: new Date(l.timestamp).toISOString(),
  }));
  const queue = await editQueue((q) => [...q, ...fixes]);
  listeners.forEach((fn) => fn(fixes));
  if (queue.length >= BATCH) flush();
});

export function onFixes(fn: (fixes: Fix[]) => void): () => void {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((f) => f !== fn);
  };
}

export type StartResult = { ok: true; run: ActiveRun } | { ok: false; reason: 'permission' | 'server' | 'services-off' };

export async function startRun(workoutType = 'running'): Promise<StartResult> {
  if (!(await Location.hasServicesEnabledAsync())) return { ok: false, reason: 'services-off' };
  const perm = await Location.requestForegroundPermissionsAsync();
  if (!perm.granted) return { ok: false, reason: 'permission' };
  const started = await postJson<{ route_id: string }>('/gps/start', { workout_type: workoutType });
  if (!started) return { ok: false, reason: 'server' };
  const run: ActiveRun = { routeId: started.route_id, workoutType, startedAt: Date.now() };
  await AsyncStorage.multiSet([[ACTIVE_KEY, JSON.stringify(run)], [QUEUE_KEY, '[]']]);
  await Location.startLocationUpdatesAsync(RUN_TASK, {
    accuracy: Location.Accuracy.BestForNavigation,
    timeInterval: 2000,
    distanceInterval: 5,
    pausesUpdatesAutomatically: false,
    foregroundService: {
      notificationTitle: 'AdapFit is recording your run',
      notificationBody: 'Open the app to see your pace or stop.',
      notificationColor: '#0F172A',
      killServiceOnDestroy: false,
    },
  });
  return { ok: true, run };
}

// expo/expo#50364: after a relaunch with the task still registered, the stop call can hang forever.
async function stopUpdates(): Promise<void> {
  const stop = (async () => {
    if (await TaskManager.isTaskRegisteredAsync(RUN_TASK)) await Location.stopLocationUpdatesAsync(RUN_TASK);
  })().catch(() => undefined);
  await Promise.race([stop, new Promise((r) => setTimeout(r, 3000))]);
}

export type FinishResult = { stats: LiveStats & { distance_km: number; elevation_gain_m: number }; saved_to_history: boolean };

/** Stop the service, upload what is left, and close the route. Null when the upload could not finish (retry later). */
export async function finishRun(): Promise<FinishResult | null> {
  await stopUpdates();
  const run = await activeRun();
  if (!run) return null;
  await flush();
  if ((await readQueue()).length) return null;
  const res = await postJson<FinishResult>(`/gps/${run.routeId}/finish`);
  if (!res) return null;
  await AsyncStorage.multiRemove([ACTIVE_KEY, QUEUE_KEY]);
  return res;
}

/** Throw the recording away without saving. */
export async function discardRun(): Promise<void> {
  await stopUpdates();
  await AsyncStorage.multiRemove([ACTIVE_KEY, QUEUE_KEY]);
}

export function haversineM(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const R = 6371000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lon - a.lon);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}
