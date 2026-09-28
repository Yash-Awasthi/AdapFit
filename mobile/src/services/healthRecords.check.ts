// Run: node src/services/healthRecords.check.ts
import assert from 'node:assert/strict';
import { toDeviceRecord } from './healthRecords.ts';

const meta = (id: string) => ({ metadata: { id, dataOrigin: 'com.fitness.app' } });
const iv = { startTime: '2026-09-28T01:00:00.000Z', endTime: '2026-09-28T01:30:00.000Z' };

const steps = toDeviceRecord('Steps', { ...meta('s'), ...iv, count: 812 })!;
assert.deepEqual([steps.type, steps.value, steps.end - steps.start, steps.source], ['steps', 812, 1800, 'com.fitness.app']);

const hr = toDeviceRecord('HeartRate', { ...meta('h'), ...iv, samples: [{ beatsPerMinute: 60 }, { beatsPerMinute: 80 }, { beatsPerMinute: 0 }] })!;
assert.deepEqual([hr.value, hr.data], [70, { min: 60, max: 80, samples: 2 }]);
assert.equal(toDeviceRecord('HeartRate', { ...meta('e'), ...iv, samples: [] }), undefined);

const bp = toDeviceRecord('BloodPressure', { ...meta('b'), time: '2026-09-28T02:00:00Z', systolic: { inMillimetersOfMercury: 121.6 }, diastolic: { inMillimetersOfMercury: 79.2 } })!;
assert.deepEqual([bp.start, bp.end, bp.data], [bp.end, bp.start, { systolic: 122, diastolic: 79 }]);

const g = toDeviceRecord('BloodGlucose', { ...meta('g'), time: '2026-09-28T02:00:00Z', level: { inMilligramsPerDeciliter: 104 }, relationToMeal: 1, mealType: 2 })!;
assert.equal(g.value, 104);

const sleep = toDeviceRecord('SleepSession', { ...meta('z'), ...iv, stages: [{ stage: 5, ...iv }] })!;
assert.equal((sleep.data!.stages as any[])[0].stage, 5);

// A record with no id cannot be de-duplicated and is dropped.
assert.equal(toDeviceRecord('Steps', { ...iv, count: 5 }), undefined);
console.log('healthRecords ok');
