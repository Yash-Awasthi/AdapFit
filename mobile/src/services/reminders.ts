/**
 * Reminders delivered by the phone itself (no push server yet).
 *
 * The schedule lives on the server (/notifications, /health/medications); this
 * mirrors it into the Android alarm schedule. Every apply cancels what this
 * module scheduled before and schedules again, so edits and deletions follow.
 */
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { getJson } from './http';
import { Medication, plan, Preferences, ServerReminder } from './reminderPlan';

const CHANNEL = 'reminders';
const TAG = 'adapfit-reminder';
Notifications.setNotificationHandler({
  handleNotification: async () => ({ shouldShowBanner: true, shouldShowList: true, shouldPlaySound: true, shouldSetBadge: false }),
});

export async function ensureNotificationPermission(ask: boolean): Promise<boolean> {
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync(CHANNEL, {
      name: 'Reminders', importance: Notifications.AndroidImportance.HIGH,
      description: 'Workout, check-in, bedtime and medication reminders you set',
    });
  }
  const current = await Notifications.getPermissionsAsync();
  if (current.granted || !ask) return current.granted;
  return (await Notifications.requestPermissionsAsync()).granted;
}

/** Re-schedule everything. Returns how many reminders are now set, or null without permission. */
export async function applyReminders(ask = false): Promise<number | null> {
  if (!(await ensureNotificationPermission(ask))) return null;
  const [reminders, prefs, meds] = await Promise.all([
    getJson<ServerReminder[]>('/notifications'),
    getJson<Preferences>('/notifications/preferences'),
    getJson<{ medications: Medication[] }>('/health/medications'),
  ]);
  if (reminders === null && meds === null) return null;
  const planned = plan(reminders ?? [], prefs, meds?.medications ?? []);
  for (const n of await Notifications.getAllScheduledNotificationsAsync()) {
    if (n.content.data?.tag === TAG) await Notifications.cancelScheduledNotificationAsync(n.identifier);
  }
  for (const p of planned) {
    const trigger: Notifications.NotificationTriggerInput = p.weekday
      ? { type: Notifications.SchedulableTriggerInputTypes.WEEKLY, weekday: p.weekday, hour: p.hour, minute: p.minute, channelId: CHANNEL }
      : { type: Notifications.SchedulableTriggerInputTypes.DAILY, hour: p.hour, minute: p.minute, channelId: CHANNEL };
    await Notifications.scheduleNotificationAsync({ content: { title: p.title, body: p.body, data: { tag: TAG } }, trigger });
  }
  return planned.length;
}

/** Sign-out: nothing of the last account should keep firing. */
export async function cancelAllReminders(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync().catch(() => undefined);
}
