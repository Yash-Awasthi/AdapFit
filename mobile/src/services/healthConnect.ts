import {
  initialize,
  requestPermission,
  readRecords,
} from 'react-native-health-connect';
import { Platform } from 'react-native';

export interface MorningBiometrics {
  sleepHours: number;
  sleepEfficiency: number;
  hrvRmssd?: number;
  restingHeartRate?: number;
}

export async function fetchMorningBiometrics(): Promise<MorningBiometrics> {
  if (Platform.OS !== 'android') {
    // Fallback on non-Android dev environments
    return {
      sleepHours: 7.5,
      sleepEfficiency: 85.0,
      hrvRmssd: 52.0,
      restingHeartRate: 64,
    };
  }

  try {
    const isInitialized = await initialize();
    if (!isInitialized) {
      console.warn('Health Connect is not available on this device');
      return { sleepHours: 7.5, sleepEfficiency: 85.0 };
    }

    // Request permissions for Health Connect
    await requestPermission([
      { accessType: 'read', recordType: 'SleepSession' },
      { accessType: 'read', recordType: 'HeartRateVariabilityRmssd' },
      { accessType: 'read', recordType: 'RestingHeartRate' },
    ]);

    // Query 15-hour time window (Last night 8:00 PM to now)
    const now = new Date();
    const startTime = new Date(now.getTime() - 15 * 60 * 60 * 1000).toISOString();
    const endTime = now.toISOString();

    // 1. Fetch Sleep
    const sleepRecords = await readRecords('SleepSession', {
      timeRangeFilter: { operator: 'between', startTime, endTime },
    });

    let totalSleepMinutes = 0;
    if (sleepRecords.records.length > 0) {
      const session = sleepRecords.records[0];
      const start = new Date(session.startTime).getTime();
      const end = new Date(session.endTime).getTime();
      totalSleepMinutes = (end - start) / (1000 * 60);
    }

    // 2. Fetch HRV RMSSD
    const hrvRecords = await readRecords('HeartRateVariabilityRmssd', {
      timeRangeFilter: { operator: 'between', startTime, endTime },
    });
    const avgHrv = hrvRecords.records.length > 0
      ? hrvRecords.records.reduce((acc, curr) => acc + curr.heartRateVariabilityMillis, 0) / hrvRecords.records.length
      : undefined;

    // 3. Fetch Resting Heart Rate
    const rhrRecords = await readRecords('RestingHeartRate', {
      timeRangeFilter: { operator: 'between', startTime, endTime },
    });
    const latestRhr = rhrRecords.records.length > 0
      ? rhrRecords.records[rhrRecords.records.length - 1].beatsPerMinute
      : undefined;

    return {
      sleepHours: totalSleepMinutes > 0 ? parseFloat((totalSleepMinutes / 60).toFixed(2)) : 7.5,
      sleepEfficiency: totalSleepMinutes > 0 ? 88.0 : 80.0,
      hrvRmssd: avgHrv ? parseFloat(avgHrv.toFixed(1)) : undefined,
      restingHeartRate: latestRhr,
    };
  } catch (error) {
    console.error('Failed to query Health Connect:', error);
    return {
      sleepHours: 7.0,
      sleepEfficiency: 80.0,
    };
  }
}
