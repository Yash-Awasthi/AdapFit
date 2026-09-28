// Run: node src/services/sleepSoundDetector.check.ts
import assert from 'node:assert/strict';
import { SleepSoundDetector } from './sleepSoundDetector.ts';

const STEP = 250;
function night(sound: (tMs: number) => number, minutes: number) {
  const d = new SleepSoundDetector();
  for (let t = 0; t < minutes * 60000; t += STEP) d.push(t, sound(t));
  return d.report();
}
const QUIET = -55;

// Quiet room: listened time counted, nothing detected.
const quiet = night((t) => QUIET + (((t / STEP) % 3) - 1) * 0.5, 10);
assert.equal(quiet.duration_minutes, 10);
assert.deepEqual(quiet.snoring_events, []);
assert.deepEqual(quiet.noise_events, []);

// Snoring: 1.2 s bursts 15 dB up every 4 s, from minute 2 to minute 5.
const snore = night((t) => (t > 120000 && t < 300000 && t % 4000 < 1200 ? QUIET + 15 : QUIET), 10);
assert.equal(snore.snoring_events.length, 1);
const ep = snore.snoring_events[0];
assert.ok(ep.bursts >= 40 && ep.start_min >= 2 && ep.start_min < 2.2 && ep.duration_min > 2.8, JSON.stringify(ep));
assert.deepEqual(snore.noise_events, []);

// A door slam (loud, one-off) is noise, not snoring; irregular bursts are not snoring either.
const slam = night((t) => (t > 180000 && t < 180800 ? QUIET + 30 : QUIET), 10);
assert.equal(slam.snoring_events.length, 0);
assert.equal(slam.noise_events.length, 1);
const irregular = [130, 131.5, 139, 140, 152, 153.2, 170].map((s) => s * 1000);
const random = night((t) => (irregular.some((s) => t >= s && t < s + 800) ? QUIET + 25 : QUIET), 10);
assert.equal(random.snoring_events.length, 0);

// Time with no readings (screen off) is not counted as listened.
const d = new SleepSoundDetector();
for (let t = 0; t < 60000; t += STEP) d.push(t, QUIET);
for (let t = 600000; t < 660000; t += STEP) d.push(t, QUIET);
assert.equal(d.report().duration_minutes, 2);
console.log('sleepSoundDetector ok');
