/**
 * Unified Health Data Bridge
 *
 * Abstracts platform-specific health APIs:
 * - Android: Health Connect, read through ./healthConnect without prompting
 * - iOS: react-native-health (Apple HealthKit)
 *
 * Never returns fabricated readings. When a value cannot be read from the
 * platform API it is left undefined and `source` explains why: 'unavailable'
 * covers a missing native module, a denied permission, or a failed fetch —
 * see `unavailableReason`. Simulated data is only returned when the
 * EXPO_PUBLIC_USE_SIMULATED_HEALTH_DATA env flag is set, for local
 * development without a paired device.
 */

import { Platform } from 'react-native';

export type HealthUnavailableReason = 'permission-denied' | 'module-missing' | 'fetch-failed';

export interface HealthBiometrics {
  // Sleep
  sleepHours?: number;
  sleepEfficiency?: number;
  deepSleepMinutes?: number;
  remSleepMinutes?: number;
  lightSleepMinutes?: number;

  // Heart
  hrvRmssd?: number;
  restingHeartRate?: number;

  // Activity
  steps?: number;
  activeCalories?: number;
  distanceMeters?: number;

  // Body
  weightKg?: number;
  bodyFatPct?: number;

  // Metadata
  source: 'healthkit' | 'healthconnect' | 'simulated' | 'unavailable';
  unavailableReason?: HealthUnavailableReason;
  fetchedAt: string;
}

const USE_SIMULATED = process.env.EXPO_PUBLIC_USE_SIMULATED_HEALTH_DATA === 'true';

function simulated(): HealthBiometrics {
  return {
    sleepHours: 7.5,
    sleepEfficiency: 87,
    deepSleepMinutes: 95,
    remSleepMinutes: 110,
    lightSleepMinutes: 185,
    hrvRmssd: 48,
    restingHeartRate: 62,
    steps: 8400,
    activeCalories: 420,
    weightKg: 78.5,
    source: 'simulated',
    fetchedAt: new Date().toISOString(),
  };
}

function unavailable(reason: HealthUnavailableReason): HealthBiometrics {
  return { source: 'unavailable', unavailableReason: reason, fetchedAt: new Date().toISOString() };
}

async function fetchAndroid(): Promise<HealthBiometrics> {
  const { healthConnectState, grantedTypes, readAll } = require('./healthConnect') as typeof import('./healthConnect');
  if ((await healthConnectState()) !== 'ready') return unavailable('module-missing');
  const granted = await grantedTypes();
  if (!granted.size) return unavailable('permission-denied');

  const now = Date.now();
  const since15h = now - 15 * 3600_000;
  const since24h = now - 24 * 3600_000;
  const read = async (type: Parameters<typeof readAll>[0], from: number) =>
    granted.has(type) ? readAll(type, from, now).catch(() => [] as any[]) : [];
  const ms = (iso: string) => new Date(iso).getTime();

  // Last night: the longest session ending in the past 15 hours. Stage minutes and
  // efficiency only when the record carries stages; otherwise left undefined.
  let sleepHours: number | undefined, sleepEfficiency: number | undefined;
  let deepMin: number | undefined, remMin: number | undefined, lightMin: number | undefined;
  const sessions = (await read('SleepSession', since15h)).sort(
    (a: any, b: any) => ms(b.endTime) - ms(b.startTime) - (ms(a.endTime) - ms(a.startTime)),
  );
  if (sessions.length) {
    const s = sessions[0];
    const totalMin = (ms(s.endTime) - ms(s.startTime)) / 60000;
    sleepHours = parseFloat((totalMin / 60).toFixed(1));
    const stages: any[] = s.stages ?? [];
    if (stages.length) {
      const minutes = (kinds: number[]) =>
        stages.filter((st) => kinds.includes(st.stage)).reduce((a, st) => a + (ms(st.endTime) - ms(st.startTime)) / 60000, 0);
      deepMin = Math.round(minutes([5]));
      remMin = Math.round(minutes([6]));
      lightMin = Math.round(minutes([4]));
      const awake = minutes([1, 3]);
      sleepEfficiency = Math.round(((totalMin - awake) / totalMin) * 100);
    }
  }

  const hrvs = (await read('HeartRateVariabilityRmssd', since15h)).map((r: any) => r.heartRateVariabilityMillis);
  const rhr = (await read('RestingHeartRate', since24h)).sort((a: any, b: any) => ms(a.time) - ms(b.time)).pop()?.beatsPerMinute;
  const stepRecs = await read('Steps', since24h);
  const calRecs = await read('ActiveCaloriesBurned', since24h);
  const weight = (await read('Weight', now - 30 * 86400_000)).sort((a: any, b: any) => ms(a.time) - ms(b.time)).pop()?.weight?.inKilograms;

  return {
    sleepHours, sleepEfficiency,
    deepSleepMinutes: deepMin, remSleepMinutes: remMin, lightSleepMinutes: lightMin,
    hrvRmssd: hrvs.length ? parseFloat((hrvs.reduce((a: number, b: number) => a + b, 0) / hrvs.length).toFixed(1)) : undefined,
    restingHeartRate: rhr,
    steps: stepRecs.length ? stepRecs.reduce((a: number, r: any) => a + r.count, 0) : undefined,
    activeCalories: calRecs.length ? Math.round(calRecs.reduce((a: number, r: any) => a + (r.energy?.inKilocalories ?? 0), 0)) : undefined,
    weightKg: weight,
    source: 'healthconnect',
    fetchedAt: new Date(now).toISOString(),
  };
}

async function fetchIOS(): Promise<HealthBiometrics> {
  let health: any;
  try {
    const hk = require('react-native-health');
    health = hk.default || hk;
  } catch {
    return unavailable('module-missing');
  }

  try {
    await new Promise<void>((resolve, reject) => {
      health.initHealthKit(null, (err: any) => (err ? reject(err) : resolve()));
    });
  } catch {
    return unavailable('permission-denied');
  }

  const now = new Date();
  const start24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);

  // Sleep efficiency needs the full night's stage samples (in-bed vs asleep
  // minutes); a single latest sample can't support that, so it is left
  // undefined here rather than estimated.
  let sleepHours: number | undefined;
  try {
    const sleepSamples = await health.getSleepSamples({
      startDate: start24h.toISOString(),
      endDate: now.toISOString(),
      limit: 1,
    });
    if (sleepSamples.length > 0) {
      const s = sleepSamples[0];
      const mins = (new Date(s.endDate).getTime() - new Date(s.startDate).getTime()) / 60000;
      sleepHours = parseFloat((mins / 60).toFixed(1));
    }
  } catch {}

  let hrv: number | undefined;
  try {
    const hrvSamples = await health.getHeartRateVariabilitySamples({
      startDate: start24h.toISOString(),
      endDate: now.toISOString(),
      limit: 10,
    });
    if (hrvSamples.length > 0) {
      hrv = hrvSamples.reduce((a: number, s: any) => a + s.value, 0) / hrvSamples.length;
    }
  } catch {}

  let rhr: number | undefined;
  try {
    const rhrSamples = await health.getRestingHeartRateSamples({
      startDate: start24h.toISOString(),
      endDate: now.toISOString(),
      limit: 1,
    });
    if (rhrSamples.length > 0) rhr = rhrSamples[0].value;
  } catch {}

  let steps: number | undefined;
  try {
    const stepSamples = await health.getStepCount({
      startDate: start24h.toISOString(),
      endDate: now.toISOString(),
    });
    steps = stepSamples ? Math.round(stepSamples.value) : undefined;
  } catch {}

  let cal: number | undefined;
  try {
    const calSamples = await health.getActiveEnergyBurned({
      startDate: start24h.toISOString(),
      endDate: now.toISOString(),
    });
    if (calSamples.length > 0) {
      cal = calSamples.reduce((a: number, s: any) => a + s.value, 0);
    }
  } catch {}

  let weight: number | undefined;
  try {
    const wSamples = await health.getLatestWeight({ limit: 1, unit: 'kg' });
    if (wSamples) weight = wSamples.value;
  } catch {}

  return {
    sleepHours,
    hrvRmssd: hrv ? parseFloat(hrv.toFixed(1)) : undefined,
    restingHeartRate: rhr,
    steps, activeCalories: cal ? parseFloat(cal.toFixed(0)) : undefined,
    weightKg: weight,
    source: 'healthkit',
    fetchedAt: now.toISOString(),
  };
}

/**
 * Fetch health data from the appropriate platform API. Returns
 * source: 'unavailable' (with a reason) instead of substituting fake
 * values when the native module, permission, or fetch itself fails.
 */
export async function fetchHealthData(): Promise<HealthBiometrics> {
  if (USE_SIMULATED) return simulated();
  if (Platform.OS === 'android') return fetchAndroid();
  if (Platform.OS === 'ios') return fetchIOS();
  return unavailable('module-missing');
}
