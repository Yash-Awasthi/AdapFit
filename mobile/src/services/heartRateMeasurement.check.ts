// Run: node src/services/heartRateMeasurement.check.ts
import assert from 'node:assert/strict';
import { parseHeartRateMeasurement } from './heartRateMeasurement.ts';

// 8-bit HR 72, RR present: 1024 and 922 (1/1024 s) -> 1000 ms and 900 ms.
const r = parseHeartRateMeasurement(new Uint8Array([0x10, 72, 0x00, 0x04, 0x9a, 0x03]));
assert.equal(r.heartRate, 72);
assert.deepEqual(r.rrIntervalsMs, [1000, 900]);
assert.equal(r.contactDetected, null);

// 16-bit HR 300 with energy field and contact detected, no RR.
const w = parseHeartRateMeasurement(new Uint8Array([0x0f, 0x2c, 0x01, 0x10, 0x00]));
assert.equal(w.heartRate, 300);
assert.deepEqual(w.rrIntervalsMs, []);
assert.equal(w.contactDetected, true);
console.log('heartRateMeasurement ok');
