/**
 * Health Connect (Android): permission, reading, and sync to the server.
 *
 * Reading never prompts; only `requestHealthAccess` shows the system dialog,
 * from a button the user taps. Records go to POST /device-data/import keyed by
 * their Health Connect id, so re-sending a window is harmless.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { postJson } from './http';
import { DeviceRecord, HC_RECORD_TYPES, HcType, toDeviceRecord } from './healthRecords';

export { HC_RECORD_TYPES };

type HC = typeof import('react-native-health-connect');

export type HealthConnectState = 'unsupported' | 'not-installed' | 'update-required' | 'ready';

const LAST_SYNC_KEY = 'adapfit.hc.last_sync';
const FIRST_SYNC_DAYS = 30;
// Health Connect keeps edits for a while; re-reading two days catches late writes from watches.
const OVERLAP_MS = 2 * 86400_000;

let module: HC | null | undefined;
function hc(): HC | null {
  if (module === undefined) {
    try {
      module = Platform.OS === 'android' ? require('react-native-health-connect') : null;
    } catch {
      module = null;
    }
  }
  return module ?? null;
}

export async function healthConnectState(): Promise<HealthConnectState> {
  const m = hc();
  if (!m) return 'unsupported';
  try {
    const status = await m.getSdkStatus();
    if (status === m.SdkAvailabilityStatus.SDK_UNAVAILABLE) return 'not-installed';
    if (status === m.SdkAvailabilityStatus.SDK_UNAVAILABLE_PROVIDER_UPDATE_REQUIRED) return 'update-required';
    return (await m.initialize()) ? 'ready' : 'not-installed';
  } catch {
    return 'unsupported';
  }
}

/** Record types the user has allowed, without prompting. */
export async function grantedTypes(): Promise<Set<HcType>> {
  const m = hc();
  if (!m || (await healthConnectState()) !== 'ready') return new Set();
  try {
    const granted = await m.getGrantedPermissions();
    // One permission can cover several record types (sleep also grants sleep stages); count only the ones read here.
    const read = new Set(granted.filter((p: any) => p.accessType === 'read').map((p: any) => p.recordType));
    return new Set(HC_RECORD_TYPES.filter((t) => read.has(t)));
  } catch {
    return new Set();
  }
}

/** Shows the Health Connect permission screen for every type the app reads. */
export async function requestHealthAccess(): Promise<Set<HcType>> {
  const m = hc();
  if (!m || (await healthConnectState()) !== 'ready') return new Set();
  try {
    await m.requestPermission(HC_RECORD_TYPES.map((recordType) => ({ accessType: 'read' as const, recordType })));
  } catch {
    /* dialog dismissed */
  }
  return grantedTypes();
}

export function openHealthConnectSettings(): void {
  hc()?.openHealthConnectSettings();
}

export async function readAll(type: HcType, startMs: number, endMs: number): Promise<any[]> {
  const m = hc();
  if (!m) return [];
  const out: any[] = [];
  let pageToken: string | undefined;
  do {
    const page: any = await m.readRecords(type, {
      timeRangeFilter: { operator: 'between', startTime: new Date(startMs).toISOString(), endTime: new Date(endMs).toISOString() },
      pageSize: 1000,
      pageToken,
    });
    out.push(...page.records);
    pageToken = page.pageToken || undefined;
  } while (pageToken);
  return out;
}

export type SyncResult = { sent: number; added: number; types: number } | { error: string };

/** Read everything new since the last sync (30 days the first time) and post it. */
export async function syncHealthConnect(): Promise<SyncResult> {
  const types = await grantedTypes();
  if (!types.size) return { error: 'no-permission' };
  const now = Date.now();
  const last = Number((await AsyncStorage.getItem(LAST_SYNC_KEY)) || 0);
  const from = last ? last - OVERLAP_MS : now - FIRST_SYNC_DAYS * 86400_000;
  const records: DeviceRecord[] = [];
  for (const type of HC_RECORD_TYPES) {
    if (!types.has(type)) continue;
    try {
      for (const r of await readAll(type, from, now)) {
        const rec = toDeviceRecord(type, r);
        if (rec && (rec.value === undefined || Number.isFinite(rec.value))) records.push(rec);
      }
    } catch {
      /* one unreadable type must not block the rest */
    }
  }
  let added = 0;
  const tz = -new Date().getTimezoneOffset();
  for (let i = 0; i < records.length || i === 0; i += 5000) {
    const res = await postJson<{ added: number }>('/device-data/import', { records: records.slice(i, i + 5000), tz_offset_min: tz });
    if (!res) return { error: 'server' };
    added += res.added;
  }
  await AsyncStorage.setItem(LAST_SYNC_KEY, String(now));
  return { sent: records.length, added, types: types.size };
}

/** Background-friendly sync on app open: silent, at most once an hour, only when access was already given. */
export async function syncHealthConnectIfDue(): Promise<void> {
  const last = Number((await AsyncStorage.getItem(LAST_SYNC_KEY)) || 0);
  if (Date.now() - last < 3600_000) return;
  await syncHealthConnect().catch(() => undefined);
}

/** Forget the sync position, so the next sync re-reads 30 days (after sign-out or a new account). */
export async function resetHealthSync(): Promise<void> {
  await AsyncStorage.removeItem(LAST_SYNC_KEY);
}

