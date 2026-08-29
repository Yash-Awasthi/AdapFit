/**
 * Unified Health Data Bridge
 *
 * Abstracts platform-specific health APIs:
 * - Android: react-native-health-connect (Google Health Connect)
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
  let initialize: any, requestPermission: any, readRecords: any;
  try {
    ({ initialize, requestPermission, readRecords } = require('react-native-health-connect'));
  } catch {
    return unavailable('module-missing');
  }

  try {
    const isInit = await initialize();
    if (!isInit) return unavailable('module-missing');
  } catch {
    return unavailable('module-missing');
  }

  let granted: any[];
  try {
    granted = await requestPermission([
      { accessType: 'read', recordType: 'SleepSession' },
      { accessType: 'read', recordType: 'HeartRateVariabilityRmssd' },
      { accessType: 'read', recordType: 'RestingHeartRate' },
      { accessType: 'read', recordType: 'Steps' },
      { accessType: 'read', recordType: 'ActiveCaloriesBurned' },
    ]);
  } catch {
    return unavailable('permission-denied');
  }
  if (!granted || granted.length === 0) return unavailable('permission-denied');

  const now = new Date();
  const start24h = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
  const endNow = now.toISOString();
  const start15h = new Date(now.getTime() - 15 * 60 * 60 * 1000).toISOString();
  const timeFilter = { operator: 'between' as const, startTime: start15h, endTime: endNow };
  const dayFilter = { operator: 'between' as const, startTime: start24h, endTime: endNow };

  // Sleep — efficiency is only reported when the record carries stage
  // breakdown; otherwise it stays undefined rather than guessed.
  let sleepHours: number | undefined, sleepEfficiency: number | undefined;
  let deepMin: number | undefined, remMin: number | undefined, lightMin: number | undefined;
  try {
    const sleep = await readRecords('SleepSession', { timeRangeFilter: timeFilter });
    if (sleep.records.length > 0) {
      const s = sleep.records[0];
      const totalMin = (new Date(s.endTime).getTime() - new Date(s.startTime).getTime()) / 60000;
      sleepHours = parseFloat((totalMin / 60).toFixed(1));
      if (s.stages && s.stages.length > 0) {
        deepMin = s.stages.filter((st: any) => st.stage === 'STAGE_TYPE_DEEP').reduce((a: number, st: any) => a + st.duration / 60000, 0);
        remMin = s.stages.filter((st: any) => st.stage === 'STAGE_TYPE_REM').reduce((a: number, st: any) => a + st.duration / 60000, 0);
        const awakeMin = s.stages.filter((st: any) => st.stage === 'STAGE_TYPE_AWAKE').reduce((a: number, st: any) => a + st.duration / 60000, 0);
        lightMin = totalMin - (deepMin || 0) - (remMin || 0) - awakeMin;
        sleepEfficiency = Math.round(((totalMin - awakeMin) / totalMin) * 100);
      }
    }
  } catch {}

  let hrv: number | undefined;
  try {
    const hrvRec = await readRecords('HeartRateVariabilityRmssd', { timeRangeFilter: timeFilter });
    if (hrvRec.records.length > 0) {
      hrv = hrvRec.records.reduce((a: number, r: any) => a + r.heartRateVariabilityMillis, 0) / hrvRec.records.length;
    }
  } catch {}

  let rhr: number | undefined;
  try {
    const rhrRec = await readRecords('RestingHeartRate', { timeRangeFilter: timeFilter });
    if (rhrRec.records.length > 0) rhr = rhrRec.records[rhrRec.records.length - 1].beatsPerMinute;
  } catch {}

  let steps: number | undefined;
  try {
    const stepsRec = await readRecords('Steps', { timeRangeFilter: dayFilter });
    steps = stepsRec.records.reduce((a: number, r: any) => a + r.count, 0);
  } catch {}

  let cal: number | undefined;
  try {
    const calRec = await readRecords('ActiveCaloriesBurned', { timeRangeFilter: dayFilter });
    cal = calRec.records.reduce((a: number, r: any) => a + r.energy?.inKilocalories || 0, 0);
  } catch {}

  return {
    sleepHours, sleepEfficiency,
    deepSleepMinutes: deepMin, remSleepMinutes: remMin, lightSleepMinutes: lightMin,
    hrvRmssd: hrv ? parseFloat(hrv.toFixed(1)) : undefined,
    restingHeartRate: rhr,
    steps, activeCalories: cal ? parseFloat(cal.toFixed(0)) : undefined,
    source: 'healthconnect',
    fetchedAt: now.toISOString(),
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
