/** Which reminders to schedule, from the server's records. No device APIs, so `node reminderPlan.check.ts` runs it. */
export type ServerReminder = {
  id: string; type: string; title: string; body: string; scheduled_at: string;
  recurring: boolean; recurring_days: number[]; enabled: boolean;
};
export type Preferences = { workout_reminders: boolean; recovery_checkins: boolean; sleep_reminders: boolean };
export type Medication = { name: string; dosage: string; time_of_day: string[]; with_food?: boolean };

// Medication slots are words, not times; these are the times the reminder fires for each.
export const MEDICATION_SLOT_TIMES: Record<string, string> = { morning: '08:00', afternoon: '13:00', evening: '19:00', night: '22:00' };
const PREF_FOR_TYPE: Record<string, keyof Preferences> = {
  workout_reminder: 'workout_reminders', recovery_checkin: 'recovery_checkins', sleep_reminder: 'sleep_reminders',
};

export function hhmm(value: string): { hour: number; minute: number } | null {
  const m = /^(\d{1,2}):(\d{2})$/.exec(value.trim());
  if (!m) return null;
  const hour = Number(m[1]);
  const minute = Number(m[2]);
  return hour < 24 && minute < 60 ? { hour, minute } : null;
}

export type Planned = { title: string; body: string; hour: number; minute: number; weekday?: number };

/** What should be scheduled, from the server's records; pure so it can be checked without a device. */
export function plan(reminders: ServerReminder[], prefs: Preferences | null, meds: Medication[]): Planned[] {
  const out: Planned[] = [];
  for (const r of reminders) {
    const pref = PREF_FOR_TYPE[r.type];
    if (!r.enabled || (pref && prefs && !prefs[pref])) continue;
    const t = hhmm(r.scheduled_at);
    if (!t) continue;
    if (r.recurring && r.recurring_days.length && r.recurring_days.length < 7) {
      // Server days are 0=Monday..6=Sunday; Android weekdays are 1=Sunday..7=Saturday.
      for (const d of r.recurring_days) out.push({ title: r.title, body: r.body, ...t, weekday: ((d + 1) % 7) + 1 });
    } else {
      out.push({ title: r.title, body: r.body, ...t });
    }
  }
  for (const med of meds) {
    for (const slot of med.time_of_day ?? []) {
      const t = hhmm(MEDICATION_SLOT_TIMES[slot] ?? slot);
      if (!t) continue;
      out.push({ title: `Medicine: ${med.name}`, body: `${med.dosage}${med.with_food ? ', with food' : ''}. Mark it taken in the app.`, ...t });
    }
  }
  return out;
}

