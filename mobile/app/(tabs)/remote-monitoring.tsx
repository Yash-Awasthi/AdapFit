/**
 * Remote Monitoring — connected-device dashboard from real readings.
 *
 * Vital trend and status come only from readings this patient actually
 * submitted; the dashboard used to hand back a fixed 122/78 and "Dr. Smith"
 * appointment regardless of whether any device had reported anything.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, typography } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const DEVICE_METRICS: Record<string, string[]> = {
  blood_pressure_monitor: ['systolic', 'diastolic', 'pulse'],
  glucose_meter: ['blood_glucose'],
  pulse_oximeter: ['oxygen_saturation', 'pulse_rate'],
  smart_scale: ['weight', 'body_fat', 'bmi'],
  wearable_tracker: ['steps', 'heart_rate', 'sleep', 'activity_minutes'],
  ecg_monitor: ['heart_rate', 'hrv'],
};

interface VitalSummaryEntry { latest: string; trend: string }
interface Dashboard {
  connected_devices: number;
  active_alerts: number;
  measurements_today: number;
  vital_summary: Record<string, VitalSummaryEntry>;
  recent_alerts: { message: string; severity: string }[];
  last_sync: string | null;
}

export default function RemoteMonitoringScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [deviceType, setDeviceType] = useState('blood_pressure_monitor');
  const [readingDevice, setReadingDevice] = useState('blood_pressure_monitor');
  const [values, setValues] = useState<Record<string, string>>({});

  const { data, loading, refresh, refreshing, reload } = useApis<{ dashboard: { data: Dashboard } }>({
    dashboard: `/remote-monitoring/dashboard/${userId}`,
  });

  const dashboard = data.dashboard?.data;
  const hasDevices = (dashboard?.connected_devices ?? 0) > 0;

  const registerDevice = useCallback(async () => {
    setBusy(true);
    const result = await postJson('/remote-monitoring/register-device', {
      patient_id: userId, device_type: deviceType, device_info: {},
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not registered', 'The device could not be registered.');
      return;
    }
    await reload();
  }, [deviceType, userId, reload]);

  const submitReading = useCallback(async () => {
    const readings: Record<string, number> = {};
    for (const m of DEVICE_METRICS[readingDevice] ?? []) {
      const v = values[m];
      if (v && v.trim()) readings[m] = Number(v);
    }
    if (Object.keys(readings).length === 0) {
      Alert.alert('No values entered', 'Enter at least one reading.');
      return;
    }
    setBusy(true);
    const result = await postJson<{ alerts?: { message: string }[] }>('/remote-monitoring/process-reading', {
      patient_id: userId, device_type: readingDevice, readings,
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not recorded', 'The reading could not be saved.');
      return;
    }
    if (result.alerts?.length) {
      Alert.alert('Worth checking', result.alerts.map((a) => a.message).join('\n'));
    }
    setValues({});
    await reload();
  }, [readingDevice, values, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#06B6D4" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#06B6D4" />}
      >
        <LinearGradient colors={['#06B6D4', '#3B82F6', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Remote Monitoring</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>
            {dashboard?.connected_devices ?? 0} device{dashboard?.connected_devices === 1 ? '' : 's'} connected
          </Text>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 4 }]}>
            {dashboard?.active_alerts ?? 0} active alert{dashboard?.active_alerts === 1 ? '' : 's'} · {dashboard?.measurements_today ?? 0} readings today
          </Text>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Register a Device" icon="watch" iconColor="#06B6D4" />
          <GlassCard>
            <View style={styles.chipRow}>
              {Object.keys(DEVICE_METRICS).map((t) => (
                <TouchableOpacity key={t} style={[styles.chip, deviceType === t && styles.chipActive]} onPress={() => setDeviceType(t)}>
                  <Text style={[styles.chipText, deviceType === t && styles.chipTextActive]}>{t.replace(/_/g, ' ')}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity style={styles.primaryBtn} onPress={registerDevice} disabled={busy}>
              <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Register device'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>

        {!!hasDevices && (
          <>
            <View style={styles.section}>
              <SectionHeaderPremium title="Submit a Reading" icon="pulse" iconColor="#EF4444" />
              <GlassCard>
                <View style={styles.chipRow}>
                  {Object.keys(DEVICE_METRICS).map((t) => (
                    <TouchableOpacity key={t} style={[styles.chip, readingDevice === t && styles.chipActive]} onPress={() => setReadingDevice(t)}>
                      <Text style={[styles.chipText, readingDevice === t && styles.chipTextActive]}>{t.replace(/_/g, ' ')}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
                {DEVICE_METRICS[readingDevice].map((m) => (
                  <TextInput
                    key={m}
                    style={styles.input}
                    placeholder={m.replace(/_/g, ' ')}
                    placeholderTextColor={colors.text.muted}
                    keyboardType="numeric"
                    value={values[m] ?? ''}
                    onChangeText={(v) => setValues((prev) => ({ ...prev, [m]: v }))}
                  />
                ))}
                <TouchableOpacity style={styles.primaryBtn} onPress={submitReading} disabled={busy}>
                  <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Submit reading'}</Text>
                </TouchableOpacity>
              </GlassCard>
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Vital Trends" icon="trending-up" iconColor="#22C55E" />
              {!dashboard || Object.keys(dashboard.vital_summary).length === 0 ? (
                <Text style={styles.emptyText}>No readings submitted yet.</Text>
              ) : (
                Object.entries(dashboard.vital_summary).map(([metric, v]) => (
                  <View key={metric} style={styles.vitalRow}>
                    <Ionicons name="pulse" size={16} color="#06B6D4" />
                    <Text style={[typography.body.md, { color: colors.text.primary, flex: 1, marginLeft: 10, textTransform: 'capitalize' }]}>{metric.replace(/_/g, ' ')}</Text>
                    <Text style={[typography.body.md, { color: colors.text.muted }]}>{v.latest} · {v.trend}</Text>
                  </View>
                ))
              )}
            </View>

            {dashboard && dashboard.recent_alerts.length > 0 && (
              <View style={styles.section}>
                <SectionHeaderPremium title="Recent Alerts" icon="warning" iconColor={colors.health.warning} />
                {dashboard.recent_alerts.map((a, i) => (
                  <Text key={i} style={[typography.body.sm, { color: colors.health.warning, marginBottom: 6 }]}>{a.message}</Text>
                ))}
              </View>
            )}
          </>
        )}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  emptyText: { color: colors.text.muted, fontSize: 13 },
  vitalRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#06B6D4', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: '#06B6D420', borderColor: '#06B6D4' },
  chipText: { color: colors.text.muted, fontSize: 12, textTransform: 'capitalize' },
  chipTextActive: { color: '#06B6D4', fontWeight: '700' },
});
