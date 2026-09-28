// Run: node src/services/reminderPlan.check.ts
import assert from 'node:assert/strict';
import { plan } from './reminderPlan.ts';

const workout = { id: 'w', type: 'workout_reminder', title: 'Train', body: 'Go', scheduled_at: '18:30', recurring: true, recurring_days: [0, 6], enabled: true };
const checkin = { id: 'c', type: 'recovery_checkin', title: 'Check in', body: 'How', scheduled_at: '07:00', recurring: true, recurring_days: [0, 1, 2, 3, 4, 5, 6], enabled: true };
const prefs = { workout_reminders: true, recovery_checkins: true, sleep_reminders: true };

// Monday (0) is Android weekday 2, Sunday (6) is 1; every-day becomes one daily alarm.
const p = plan([workout, checkin], prefs, []);
assert.deepEqual(p.filter((x) => x.title === 'Train').map((x) => x.weekday), [2, 1]);
assert.equal(p.find((x) => x.title === 'Check in')!.weekday, undefined);

// A switched-off preference or a disabled reminder schedules nothing.
assert.equal(plan([workout], { ...prefs, workout_reminders: false }, []).length, 0);
assert.equal(plan([{ ...workout, enabled: false }], prefs, []).length, 0);

// Medication slots map to fixed times; bad times are skipped rather than guessed.
const meds = plan([], prefs, [{ name: 'Metformin', dosage: '500 mg', time_of_day: ['morning', 'night', 'whenever'], with_food: true }]);
assert.deepEqual(meds.map((m) => [m.hour, m.minute]), [[8, 0], [22, 0]]);
assert.match(meds[0].body, /with food/);
console.log('reminderPlan ok');
