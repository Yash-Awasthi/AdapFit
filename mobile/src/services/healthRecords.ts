/** Health Connect records to the server's shape. No device APIs, so `node healthRecords.check.ts` runs it. */
export const HC_RECORD_TYPES = [
  'Steps', 'SleepSession', 'HeartRate', 'RestingHeartRate', 'HeartRateVariabilityRmssd', 'Weight', 'BodyFat',
  'BloodGlucose', 'ExerciseSession', 'ActiveCaloriesBurned', 'Distance', 'OxygenSaturation', 'BloodPressure',
  'BodyTemperature', 'Nutrition', 'MenstruationFlow',
] as const;
export type HcType = (typeof HC_RECORD_TYPES)[number];

export type DeviceRecord = {
  id: string;
  type: string;
  start: number;
  end: number;
  value?: number;
  data?: Record<string, unknown>;
  source?: string;
};

const sec = (iso: string) => new Date(iso).getTime() / 1000;
const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : undefined);

/** One Health Connect record to the server's shape; undefined when it carries no usable value. */
export function toDeviceRecord(type: HcType, r: any): DeviceRecord | undefined {
  const id = r.metadata?.id;
  if (!id) return undefined;
  const base = { id, source: r.metadata?.dataOrigin ?? '' };
  const at = r.time ? { start: sec(r.time), end: sec(r.time) } : { start: sec(r.startTime), end: sec(r.endTime) };
  switch (type) {
    case 'Steps':
      return { ...base, ...at, type: 'steps', value: r.count };
    case 'SleepSession': {
      const stages = (r.stages ?? []).map((s: any) => ({ stage: s.stage, start: sec(s.startTime), end: sec(s.endTime) }));
      return { ...base, ...at, type: 'sleep', data: stages.length ? { stages } : {} };
    }
    case 'HeartRate': {
      // A record can hold hours of samples; the server keeps the mean, range and count.
      const bpm = (r.samples ?? []).map((s: any) => s.beatsPerMinute).filter((v: number) => v > 0);
      if (!bpm.length) return undefined;
      return { ...base, ...at, type: 'heart_rate', value: Math.round(mean(bpm)!), data: { min: Math.min(...bpm), max: Math.max(...bpm), samples: bpm.length } };
    }
    case 'RestingHeartRate':
      return { ...base, ...at, type: 'resting_heart_rate', value: r.beatsPerMinute };
    case 'HeartRateVariabilityRmssd':
      return { ...base, ...at, type: 'hrv_rmssd', value: r.heartRateVariabilityMillis };
    case 'Weight':
      return { ...base, ...at, type: 'weight', value: r.weight?.inKilograms };
    case 'BodyFat':
      return { ...base, ...at, type: 'body_fat', value: r.percentage };
    case 'BloodGlucose':
      return { ...base, ...at, type: 'blood_glucose', value: r.level?.inMilligramsPerDeciliter, data: { relation_to_meal: r.relationToMeal, meal_type: r.mealType } };
    case 'ExerciseSession':
      return { ...base, ...at, type: 'exercise', data: { exercise_type: r.exerciseType, title: r.title ?? '' } };
    case 'ActiveCaloriesBurned':
      return { ...base, ...at, type: 'active_calories', value: r.energy?.inKilocalories };
    case 'Distance':
      return { ...base, ...at, type: 'distance', value: r.distance?.inMeters };
    case 'OxygenSaturation':
      return { ...base, ...at, type: 'oxygen_saturation', value: r.percentage };
    case 'BloodPressure':
      return {
        ...base, ...at, type: 'blood_pressure',
        data: { systolic: Math.round(r.systolic?.inMillimetersOfMercury), diastolic: Math.round(r.diastolic?.inMillimetersOfMercury) },
      };
    case 'BodyTemperature':
      return { ...base, ...at, type: 'body_temperature', value: r.temperature?.inCelsius };
    case 'Nutrition':
      return {
        ...base, ...at, type: 'nutrition', value: r.energy?.inKilocalories,
        data: { protein_g: r.protein?.inGrams, carbs_g: r.totalCarbohydrate?.inGrams, fat_g: r.totalFat?.inGrams, name: r.name ?? '' },
      };
    case 'MenstruationFlow':
      return { ...base, ...at, type: 'menstruation_flow', value: r.flow };
  }
}

