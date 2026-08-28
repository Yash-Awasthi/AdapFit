import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, Switch, StyleSheet } from 'react-native';
import { Bell, BellOff, Moon, Dumbbell, Activity, Droplets } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../services/config';
import { useUserStore } from '../stores';
import { useTheme } from '../services/theme';

const API = API_BASE_URL;

interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body: string;
  enabled: boolean;
  recurring: boolean;
}

interface Preferences {
  workout_reminders: boolean;
  recovery_checkins: boolean;
  sleep_reminders: boolean;
  hydration: boolean;
  streak_alerts: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
}

const TYPE_ICONS: Record<string, any> = {
  workout_reminder: Dumbbell,
  recovery_checkin: Activity,
  sleep_reminder: Moon,
  hydration: Droplets,
};

export function NotificationSetup() {
  const { theme } = useTheme();
  const userId = useUserStore((s) => s.userId);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [nRes, pRes] = await Promise.all([
        fetch(`${API}/api/v1/notifications?user_id=${userId}`),
        fetch(`${API}/api/v1/notifications/preferences?user_id=${userId}`),
      ]);
      if (nRes.ok) setNotifications(await nRes.json());
      if (pRes.ok) setPrefs(await pRes.json());
    } catch {}
    setLoading(false);
  }

  async function setupDefaults() {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    try {
      const res = await fetch(`${API}/api/v1/notifications/setup-defaults?user_id=${userId}`, { method: 'POST' });
      if (res.ok) fetchData();
    } catch {}
  }

  async function deleteNotification(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await fetch(`${API}/api/v1/notifications/${id}?user_id=${userId}`, { method: 'DELETE' });
      fetchData();
    } catch {}
  }

  async function updatePref(key: string, value: boolean) {
    Haptics.selectionAsync();
    try {
      const res = await fetch(`${API}/api/v1/notifications/preferences?user_id=${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value }),
      });
      if (res.ok) setPrefs(await res.json());
    } catch {}
  }

  if (loading) return <View style={styles.loading}><Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading...</Text></View>;

  return (
    <View style={styles.container}>
      {notifications.length === 0 ? (
        <View style={styles.empty}>
          <BellOff size={32} color={theme.textMuted} />
          <Text style={[styles.emptyTitle, { color: theme.text }]}>No Notifications</Text>
          <Text style={[styles.emptyDesc, { color: theme.textSecondary }]}>Set up reminders to stay on track.</Text>
          <TouchableOpacity style={[styles.setupBtn, { backgroundColor: theme.primary }]} onPress={setupDefaults}>
            <Bell size={16} color="#fff" />
            <Text style={styles.setupBtnText}>Setup Defaults</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Scheduled Reminders</Text>
          {notifications.map((n) => {
            const Icon = TYPE_ICONS[n.type] || Bell;
            return (
              <View key={n.id} style={[styles.notifCard, { backgroundColor: theme.surface }]}>
                <View style={[styles.notifIcon, { backgroundColor: theme.primaryBg }]}>
                  <Icon size={18} color={theme.primaryLight} />
                </View>
                <View style={styles.notifInfo}>
                  <Text style={[styles.notifTitle, { color: theme.text }]}>{n.title}</Text>
                  <Text style={[styles.notifBody, { color: theme.textSecondary }]}>{n.body}</Text>
                  {n.recurring && <Text style={[styles.notifRecurring, { color: theme.primaryLight }]}>Recurring</Text>}
                </View>
                <TouchableOpacity onPress={() => deleteNotification(n.id)}>
                  <BellOff size={16} color={theme.danger} />
                </TouchableOpacity>
              </View>
            );
          })}
        </>
      )}

      {prefs && (
        <>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Preferences</Text>
          {[
            { key: 'workout_reminders', label: 'Workout Reminders' },
            { key: 'recovery_checkins', label: 'Recovery Check-ins' },
            { key: 'sleep_reminders', label: 'Sleep Reminders' },
            { key: 'hydration', label: 'Hydration Alerts' },
            { key: 'streak_alerts', label: 'Streak Alerts' },
          ].map(({ key, label }) => (
            <View key={key} style={[styles.prefRow, { backgroundColor: theme.surface }]}>
              <Text style={[styles.prefLabel, { color: theme.textSecondary }]}>{label}</Text>
              <Switch
                value={(prefs as any)[key]}
                onValueChange={(v) => updatePref(key, v)}
                trackColor={{ false: theme.surfaceHover, true: theme.primary }}
                thumbColor={theme.text}
              />
            </View>
          ))}
          <View style={[styles.quietRow, { backgroundColor: theme.surface }]}>
            <Text style={[styles.prefLabel, { color: theme.textSecondary }]}>Quiet Hours</Text>
            <Text style={[styles.quietValue, { color: theme.textSecondary }]}>{prefs.quiet_hours_start} - {prefs.quiet_hours_end}</Text>
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingBottom: 20 },
  loading: { padding: 40, alignItems: 'center' },
  loadingText: { fontSize: 14 },
  empty: { alignItems: 'center', padding: 30 },
  emptyTitle: { fontSize: 16, fontWeight: '600', marginTop: 12 },
  emptyDesc: { fontSize: 13, marginTop: 4, marginBottom: 16 },
  setupBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    borderRadius: 12, paddingHorizontal: 20, paddingVertical: 12,
  },
  setupBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  sectionTitle: { fontSize: 14, fontWeight: '600', marginTop: 16, marginBottom: 8 },
  notifCard: {
    flexDirection: 'row', alignItems: 'center',
    borderRadius: 12, padding: 12, marginBottom: 8, gap: 10,
  },
  notifIcon: {
    width: 36, height: 36, borderRadius: 18,
    alignItems: 'center', justifyContent: 'center',
  },
  notifInfo: { flex: 1 },
  notifTitle: { fontSize: 14, fontWeight: '500' },
  notifBody: { fontSize: 12, marginTop: 2 },
  notifRecurring: { fontSize: 11, marginTop: 2 },
  prefRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    borderRadius: 10, padding: 14, marginBottom: 6,
  },
  prefLabel: { fontSize: 14 },
  quietRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    borderRadius: 10, padding: 14, marginTop: 8,
  },
  quietValue: { fontSize: 13 },
});
