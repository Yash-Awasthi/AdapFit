/**
 * Vital Signs — heart rate, blood oxygen and temperature as actually measured.
 *
 * A metric with no reading shows as "no reading" rather than a placeholder
 * number: on this screen a plausible-looking figure is indistinguishable from
 * a measured one. ECG needs hardware a phone does not have, so that panel
 * says so instead of drawing a waveform.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, TextInput, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { getJson, postJson, asArray } from '../../src/services/http';

interface Measurement<T> {
  value: T | null;
  classification?: string;
  rhythm?: string;
}

interface VitalsSummary {
  heart_rate: Measurement<number>;
  spo2: Measurement<number>;
  temperature: Measurement<number>;
  total_readings: number;
}

interface TemperatureReading {
  timestamp: number;
  temp_c: number;
  temp_f: number;
  classification: string;
  site: string;
}

interface ECGReading {
  timestamp: number;
  heart_rate: number;
  rhythm: string;
  classification: string;
  pr_interval: number | null;
  qrs_duration: number | null;
  qt_interval: number | null;
}

function prettify(value?: string): string {
  if (!value || value === 'unknown') return 'No reading';
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function whenever(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString([], {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

function VitalGauge({ value, max, label, unit, color, icon, status }: {
  value: number | null;
  max: number;
  label: string;
  unit: string;
  color: string;
  icon: string;
  status: string;
}) {
  const measured = typeof value === 'number';
  const tint = measured ? color : colors.text.muted;
  return (
    <GlassCard variant="light" style={styles.gaugeCard}>
      <View style={styles.gaugeHeader}>
        <View style={[styles.gaugeIcon, { backgroundColor: tint + '15' }]}>
          <Ionicons name={icon as any} size={20} color={tint} />
        </View>
        <View>
          <Text style={styles.gaugeLabel}>{label}</Text>
          <View style={[styles.statusBadge, { backgroundColor: tint + '15' }]}>
            <Text style={[styles.statusText, { color: tint }]}>{status}</Text>
          </View>
        </View>
      </View>
      <View style={styles.gaugeValueRow}>
        <Text style={[styles.gaugeValue, { color: tint }]}>{measured ? value : '—'}</Text>
        {!!measured && <Text style={styles.gaugeUnit}>{unit}</Text>}
      </View>
      <ProgressBarPremium value={measured ? value : 0} max={max} color={tint} height={6} />
    </GlassCard>
  );
}

const CHECK_FIELDS = [
  { key: 'respiratory_rate', label: 'Breaths per minute', hint: 'Count for 30 s, double it' },
  { key: 'oxygen_saturation', label: 'SpO2 %', hint: 'Pulse oximeter' },
  { key: 'systolic_bp', label: 'Systolic BP', hint: 'Top number, mmHg' },
  { key: 'pulse_rate', label: 'Pulse', hint: 'Beats per minute' },
  { key: 'temperature', label: 'Temperature °C', hint: 'e.g. 37.2' },
] as const;

function BloodPressure() {
  const [sys, setSys] = useState('');
  const [dia, setDia] = useState('');
  const [pulse, setPulse] = useState('');
  const [data, setData] = useState<any>(null);
  const [last, setLast] = useState<any>(null);
  const load = useCallback(async () => setData(await getJson('/blood-pressure/log?days=7')), []);
  useEffect(() => { load(); }, [load]);
  const save = async () => {
    const s_ = Number(sys), d_ = Number(dia);
    if (!(s_ > 0 && d_ > 0)) return Alert.alert('Blood pressure', 'Enter both numbers, e.g. 128 and 84.');
    const r = await postJson<any>('/blood-pressure/log', { systolic: s_, diastolic: d_, pulse: pulse ? Number(pulse) : undefined });
    if (!r) return Alert.alert('Not saved', 'Check the values.');
    setLast(r); setSys(''); setDia(''); setPulse(''); load();
  };
  const summ = data?.summary;
  return (
    <GlassCard variant="light" style={styles.logCard}>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <TextInput style={[styles.input, { flex: 1 }]} placeholder="Top (systolic)" placeholderTextColor={colors.text.muted} keyboardType="number-pad" value={sys} onChangeText={setSys} />
        <TextInput style={[styles.input, { flex: 1 }]} placeholder="Bottom" placeholderTextColor={colors.text.muted} keyboardType="number-pad" value={dia} onChangeText={setDia} />
        <TextInput style={[styles.input, { flex: 1 }]} placeholder="Pulse" placeholderTextColor={colors.text.muted} keyboardType="number-pad" value={pulse} onChangeText={setPulse} />
      </View>
      <TouchableOpacity style={[styles.logButton, { backgroundColor: '#8B5CF6' }]} onPress={save}><Text style={styles.logButtonText}>Save reading</Text></TouchableOpacity>
      {!!last && <Text style={styles.emptyText}>{last.systolic}/{last.diastolic}: {last.label}. {last.next_step}</Text>}
      {summ?.count > 0 && (
        <View>
          <Text style={styles.historyTime}>7-day average {summ.average} · {summ.range}</Text>
          <Text style={styles.emptyText}>{summ.next_step}{summ.enough_for_doctor ? '' : ` (${summ.count} readings so far; about 12 over a week gives a reliable average.)`}</Text>
        </View>
      )}
      <Text style={styles.historySub}>{data?.how_to}</Text>
    </GlassCard>
  );
}

function SeekCareCheck() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [confused, setConfused] = useState(false);
  const [result, setResult] = useState<{ score: number; band: string; next_step: string } | null>(null);
  const run = async () => {
    const body: Record<string, number | boolean> = { new_confusion: confused };
    for (const f of CHECK_FIELDS) {
      const n = Number(values[f.key]);
      if (!values[f.key] || !Number.isFinite(n)) return Alert.alert('Missing reading', `Enter ${f.label.toLowerCase()}.`);
      body[f.key] = f.key === 'temperature' ? n : Math.round(n);
    }
    const r = await postJson<{ score: number; band: string; next_step: string }>('/vitals/check', body);
    if (!r) return Alert.alert('Check failed', 'One of the readings looks out of range.');
    setResult(r);
  };
  const color = result?.band === 'high' ? '#EF4444' : result?.band === 'medium' ? '#F59E0B' : '#22C55E';
  return (
    <GlassCard variant="light" style={styles.logCard}>
      {CHECK_FIELDS.map((f) => (
        <TextInput key={f.key} style={styles.input} placeholder={`${f.label} (${f.hint})`} placeholderTextColor={colors.text.muted}
          keyboardType="decimal-pad" value={values[f.key] ?? ''} onChangeText={(t) => setValues((v) => ({ ...v, [f.key]: t }))} />
      ))}
      <TouchableOpacity onPress={() => setConfused(!confused)} accessibilityRole="checkbox" accessibilityState={{ checked: confused }}>
        <Text style={styles.historyTime}>{confused ? '☑' : '☐'} New confusion or unusual drowsiness</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[styles.logButton, { backgroundColor: '#EF4444' }]} onPress={run}>
        <Text style={styles.logButtonText}>Check my readings</Text>
      </TouchableOpacity>
      {!!result && (
        <View>
          <Text style={[styles.historyValue, { color }]}>NEWS2 score {result.score}</Text>
          <Text style={styles.emptyText}>{result.next_step}</Text>
        </View>
      )}
    </GlassCard>
  );
}

export default function VitalSignsScreen() {
  const [tempInput, setTempInput] = useState('');
  const [saving, setSaving] = useState(false);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    summary: VitalsSummary;
    temperature: { readings: TemperatureReading[] };
    ecg: { readings: ECGReading[] };
  }>({
    summary: '/vitals/summary',
    temperature: '/vitals/temperature/history?limit=10',
    ecg: '/vitals/ecg/history?limit=10',
  });

  const summary = data.summary ?? null;
  const temperatures = asArray<TemperatureReading>(data.temperature?.readings);
  const ecg = asArray<ECGReading>(data.ecg?.readings);

  const logTemperature = useCallback(async () => {
    const value = Number(tempInput);
    if (!Number.isFinite(value) || value < 30 || value > 45) {
      Alert.alert('Log temperature', 'Enter a temperature between 30 and 45 °C.');
      return;
    }
    setSaving(true);
    const result = await postJson<{ error?: string }>('/vitals/temperature', {
      temperature_celsius: value,
      measurement_site: 'oral',
    });
    setSaving(false);
    if (!result || result.error) {
      Alert.alert('Not recorded', result?.error ?? 'The reading could not be saved.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setTempInput('');
    await reload();
  }, [tempInput, reload]);

  return (
    <ScreenWrapper
      title="Vital Signs"
      subtitle="Heart rate, blood oxygen and temperature"
      gradient={['#22C55E', '#06B6D4']}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <SectionHeaderPremium icon="fitness" iconColor={colors.health.heart} title="Latest Readings" />
      <VitalGauge
        value={summary?.heart_rate?.value ?? null}
        max={120}
        label="Heart Rate"
        unit="bpm"
        color="#22C55E"
        icon="heart"
        status={prettify(summary?.heart_rate?.rhythm)}
      />
      <VitalGauge
        value={summary?.spo2?.value ?? null}
        max={100}
        label="Blood Oxygen"
        unit="%"
        color="#3B82F6"
        icon="water"
        status={prettify(summary?.spo2?.classification)}
      />
      <VitalGauge
        value={summary?.temperature?.value ?? null}
        max={42}
        label="Body Temperature"
        unit="°C"
        color="#F59E0B"
        icon="thermometer"
        status={prettify(summary?.temperature?.classification)}
      />

      <SectionHeaderPremium icon="speedometer" iconColor="#8B5CF6" title="Blood Pressure" subtitle="Home readings and your weekly average" />
      <BloodPressure />

      <SectionHeaderPremium icon="medkit" iconColor="#EF4444" title="Should I Get Help?" subtitle="NEWS2 on your home readings" />
      <SeekCareCheck />

      <SectionHeaderPremium icon="thermometer" iconColor="#F59E0B" title="Log a Temperature" />
      <GlassCard variant="light" style={styles.logCard}>
        <TextInput
          style={styles.input}
          placeholder="Temperature in °C"
          placeholderTextColor={colors.text.muted}
          keyboardType="decimal-pad"
          value={tempInput}
          onChangeText={setTempInput}
          accessibilityLabel="Body temperature in degrees Celsius"
        />
        <TouchableOpacity
          style={styles.logButton}
          onPress={logTemperature}
          disabled={saving}
          accessibilityRole="button"
          accessibilityLabel="Save temperature reading"
        >
          <Text style={styles.logButtonText}>{saving ? 'Saving…' : 'Save reading'}</Text>
        </TouchableOpacity>
      </GlassCard>

      <SectionHeaderPremium icon="pulse" iconColor="#22C55E" title="ECG" />
      <GlassCard variant="light" style={styles.ecgCard}>
        {ecg.length === 0 ? (
          <View style={styles.ecgUnavailable}>
            <Ionicons name="hardware-chip-outline" size={40} color={colors.text.muted} />
            <Text style={styles.ecgUnavailableTitle}>No ECG recordings</Text>
            <Text style={styles.ecgUnavailableBody}>
              A phone camera cannot measure an ECG. Recordings from a device with an ECG
              sensor appear here. For pulse alone, use the camera heart-rate measurement.
            </Text>
          </View>
        ) : (
          ecg.map((reading, i) => (
            <View
              key={`${reading.timestamp}-${i}`}
              style={[styles.historyRow, i < ecg.length - 1 && styles.historyDivider]}
            >
              <View>
                <Text style={styles.historyTime}>{whenever(reading.timestamp)}</Text>
                <Text style={styles.historySub}>{reading.classification}</Text>
              </View>
              <Text style={[styles.historyValue, { color: '#22C55E' }]}>{reading.heart_rate} bpm</Text>
            </View>
          ))
        )}
      </GlassCard>

      <SectionHeaderPremium icon="time" iconColor={colors.primary} title="Temperature History" />
      <GlassCard variant="light" style={styles.historyCard}>
        {temperatures.length === 0 ? (
          <Text style={styles.emptyText}>Nothing logged yet.</Text>
        ) : (
          [...temperatures].reverse().map((reading, i, all) => (
            <View
              key={`${reading.timestamp}-${i}`}
              style={[styles.historyRow, i < all.length - 1 && styles.historyDivider]}
            >
              <View>
                <Text style={styles.historyTime}>{whenever(reading.timestamp)}</Text>
                <Text style={styles.historySub}>{prettify(reading.classification)} · {reading.site}</Text>
              </View>
              <Text style={[styles.historyValue, { color: '#F59E0B' }]}>{reading.temp_c}°C</Text>
            </View>
          ))
        )}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  gaugeCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  gaugeHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  gaugeIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  gaugeLabel: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  statusBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginTop: 2, alignSelf: 'flex-start' },
  statusText: { fontSize: 10, fontWeight: '600' },
  gaugeValueRow: { flexDirection: 'row', alignItems: 'baseline', gap: 4, marginBottom: spacing.sm },
  gaugeValue: { fontSize: 28, fontWeight: '800' },
  gaugeUnit: { fontSize: 14, color: colors.text.muted },

  logCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg, gap: spacing.md },
  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15 },
  logButton: { backgroundColor: '#F59E0B', borderRadius: radius.md, paddingVertical: spacing.md, alignItems: 'center' },
  logButtonText: { color: '#FFF', fontWeight: '700', fontSize: 15 },

  ecgCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  ecgUnavailable: { alignItems: 'center', paddingVertical: spacing.lg, gap: spacing.xs },
  ecgUnavailableTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary, marginTop: spacing.xs },
  ecgUnavailableBody: { fontSize: 13, color: colors.text.muted, textAlign: 'center', lineHeight: 19 },

  historyCard: { marginHorizontal: spacing.screenPadding },
  historyRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.md },
  historyDivider: { borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  historyTime: { fontSize: 13, color: colors.text.primary, fontWeight: '600' },
  historySub: { fontSize: 11, color: colors.text.muted, marginTop: 2, textTransform: 'capitalize' },
  historyValue: { fontSize: 15, fontWeight: '700' },
  emptyText: { fontSize: 13, color: colors.text.muted, paddingVertical: spacing.md },
});
