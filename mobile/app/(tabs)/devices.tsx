/**
 * Devices — the real ways data gets in: a Bluetooth heart-rate strap, and
 * files exported from Garmin, Strava or any app that writes GPX. Nothing here
 * produces a reading the user's own device did not.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system/legacy';
import { colors, spacing } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { getJson, postJson } from '../../src/services/http';
import {
  HealthConnectState, healthConnectState, grantedTypes, requestHealthAccess, syncHealthConnect, openHealthConnectSettings,
  HC_RECORD_TYPES,
} from '../../src/services/healthConnect';
import { plural } from '../../src/utils/plural';

const TINT = '#64748B';

interface SourceStatus { imports: number; records: number; last_import: string | null }
interface DeviceStatus { last_sync: number | null; records: Record<string, number> }
interface Rhythm { status: string; days: number; interdaily_stability?: number; intradaily_variability?: number;
  relative_amplitude?: number; m10_onset_hour?: number; l5_onset_hour?: number; needed_days?: number }

const hour = (h: number) => `${String(h).padStart(2, '0')}:00`;

type Day = Record<string, any> & { date: string };
// What each synced type shows as; a day lists only what a device actually recorded.
const DAY_FIELDS: [string, string, (v: any) => string][] = [
  ['steps', 'Steps', (v) => v.toLocaleString()],
  ['sleep_hours', 'Sleep', (v) => `${v} h`],
  ['resting_heart_rate', 'Resting HR', (v) => `${Math.round(v)} bpm`],
  ['avg_heart_rate', 'Avg HR', (v) => `${Math.round(v)} bpm`],
  ['hrv_rmssd', 'HRV', (v) => `${Math.round(v)} ms`],
  ['weight_kg', 'Weight', (v) => `${v} kg`],
  ['body_fat_pct', 'Body fat', (v) => `${v}%`],
  ['active_calories', 'Active', (v) => `${Math.round(v)} kcal`],
  ['distance_m', 'Distance', (v) => `${(v / 1000).toFixed(1)} km`],
  ['exercise_minutes', 'Exercise', (v) => `${v} min`],
  ['blood_pressure', 'BP', (v) => `${v.systolic}/${v.diastolic}`],
  ['spo2_pct', 'SpO2', (v) => `${Math.round(v)}%`],
  ['body_temperature_c', 'Temp', (v) => `${v} °C`],
  ['nutrition_kcal', 'Food', (v) => `${Math.round(v)} kcal`],
  ['glucose_mgdl_avg', 'Glucose', (v) => `${Math.round(v)} mg/dL`],
  ['menstruation_flow', 'Period', () => 'logged'],
];

function HealthConnectCard() {
  const [state, setState] = useState<HealthConnectState | null>(null);
  const [granted, setGranted] = useState(0);
  const [server, setServer] = useState<DeviceStatus | null>(null);
  const [rhythm, setRhythm] = useState<Rhythm | null>(null);
  const [days, setDays] = useState<Day[]>([]);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setState(await healthConnectState());
    setGranted((await grantedTypes()).size);
    setServer(await getJson<DeviceStatus>('/device-data/status'));
    setRhythm(await getJson<Rhythm>('/device-data/rest-activity?days=14'));
    setDays((await getJson<{ days: Day[] }>('/device-data/daily?days=7'))?.days ?? []);
  }, []);
  useEffect(() => { refresh(); }, [refresh]);

  const sync = async () => {
    setBusy(true);
    const r = await syncHealthConnect();
    setBusy(false);
    if ('error' in r) {
      Alert.alert('Not synced', r.error === 'no-permission' ? 'Allow AdapFit to read at least one type in Health Connect.' : 'The server could not be reached. Try again later.');
    } else {
      Alert.alert('Synced', `${r.sent} records read, ${r.added} new.`);
    }
    refresh();
  };

  const connect = async () => {
    const got = await requestHealthAccess();
    setGranted(got.size);
    if (got.size) sync();
  };

  if (state === null) return <GlassCard><ActivityIndicator /></GlassCard>;
  if (state === 'unsupported') {
    return <GlassCard><Text style={styles.sub}>Health Connect is Android only. Apple Health comes with the iPhone app.</Text></GlassCard>;
  }
  if (state !== 'ready') {
    return (
      <GlassCard>
        <Text style={styles.title}>{state === 'not-installed' ? 'Health Connect is not installed' : 'Health Connect needs an update'}</Text>
        <Text style={styles.sub}>Android 14 and later have it built in. On older phones install or update "Health Connect" from the Play Store, then come back.</Text>
      </GlassCard>
    );
  }
  const total = server ? Object.values(server.records).reduce((a, b) => a + b, 0) : 0;
  return (
    <GlassCard>
      <Text style={styles.title}>Health Connect</Text>
      <Text style={styles.sub}>
        {granted ? `Reading ${granted} of ${HC_RECORD_TYPES.length} data types.` : 'Steps, sleep, heart rate, HRV, weight, glucose, blood pressure, SpO2, temperature, food and cycle from your watch, scale and other apps.'}
        {server?.last_sync ? ` Last sync ${new Date(server.last_sync * 1000).toLocaleString()} · ${plural(total, 'record')} stored.` : ''}
      </Text>
      <View style={styles.buttons}>
        {granted ? (
          <TouchableOpacity style={styles.button} onPress={sync} disabled={busy} accessibilityRole="button">
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Sync now</Text>}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.button} onPress={connect} accessibilityRole="button">
            <Text style={styles.buttonText}>Connect</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={[styles.button, styles.secondary]} onPress={openHealthConnectSettings} accessibilityRole="button">
          <Text style={styles.buttonText}>Choose data</Text>
        </TouchableOpacity>
      </View>
      {rhythm?.status === 'ok' ? (
        <View style={{ marginTop: 12 }}>
          <Text style={styles.title}>Daily rhythm ({rhythm.days} days of steps)</Text>
          <Text style={styles.sub}>
            Most active from about {hour(rhythm.m10_onset_hour!)} for 10 hours; quietest 5 hours start about {hour(rhythm.l5_onset_hour!)}.
            {' '}Day-to-day regularity {Math.round(rhythm.interdaily_stability! * 100)}% · contrast between active and rest {Math.round(rhythm.relative_amplitude! * 100)}%.
            {' '}A regular pattern with a clear quiet night supports sleep and energy.
          </Text>
        </View>
      ) : granted ? (
        <Text style={[styles.sub, { marginTop: 8 }]}>Your daily rhythm appears after 3 full days of step data.</Text>
      ) : null}
      {days.some((d) => DAY_FIELDS.some(([k]) => d[k] != null)) && (
        <View style={{ marginTop: 12 }}>
          <Text style={styles.title}>Last 7 days from Health Connect</Text>
          {[...days].reverse().map((d) => {
            const parts = DAY_FIELDS.filter(([k]) => d[k] != null).map(([k, label, fmt]) => `${label} ${fmt(d[k])}`);
            return parts.length ? <Text key={d.date} style={styles.sub}>{d.date}: {parts.join(' · ')}</Text> : null;
          })}
        </View>
      )}
    </GlassCard>
  );
}

export default function DevicesScreen() {
  const router = useRouter();
  const [status, setStatus] = useState<Record<string, SourceStatus>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus((await getJson<Record<string, SourceStatus>>('/wearable/status')) ?? {});
  }, []);
  useEffect(() => { load(); }, [load]);

  const pick = async (): Promise<string | null> => {
    const res = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true, multiple: false });
    if (res.canceled || !res.assets?.[0]) return null;
    return FileSystem.readAsStringAsync(res.assets[0].uri);
  };

  const importGpx = async (activity: 'run' | 'ride' | 'walk' | 'hike') => {
    const text = await pick();
    if (!text) return;
    setBusy('gpx');
    const r = await postJson<{ saved: boolean; distance_km: number; duration_minutes: number }>('/wearable/gpx/import', { gpx: text, activity });
    setBusy(null);
    if (!r) return Alert.alert('Not imported', 'That file is not a GPX track with times.');
    Alert.alert(r.saved ? 'Imported' : 'Already imported', `${r.distance_km} km in ${r.duration_minutes} min.`);
    load();
  };

  const importJson = async (source: 'garmin' | 'strava') => {
    const text = await pick();
    if (!text) return;
    let parsed: any;
    try { parsed = JSON.parse(text); } catch { return Alert.alert('Not imported', 'That file is not JSON.'); }
    const body = source === 'strava'
      ? { activities: Array.isArray(parsed) ? parsed : parsed.activities ?? [] }
      : { workouts: parsed.workouts ?? (Array.isArray(parsed) ? parsed : []), sleep_records: parsed.sleep_records ?? parsed.sleep ?? [] };
    setBusy(source);
    const r = await postJson<Record<string, number>>(`/wearable/${source}/import`, body);
    setBusy(null);
    if (!r) return Alert.alert('Not imported', 'The file could not be read.');
    const nights = r.nights_saved ? `, ${r.nights_saved} nights` : '';
    Alert.alert('Imported', `${plural(r.workouts_saved ?? 0, 'workout')}${nights}. ${r.skipped_duplicates ?? 0} already imported.`);
    load();
  };

  const Row = ({ icon, title, sub, onPress, id }: { icon: string; title: string; sub: string; onPress: () => void; id: string }) => (
    <TouchableOpacity onPress={onPress} disabled={!!busy}>
      <GlassCard style={styles.row}>
        <Ionicons name={icon as any} size={22} color={colors.text.secondary} />
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.sub}>{sub}</Text>
        </View>
        {busy === id ? <ActivityIndicator /> : <Ionicons name="chevron-forward" size={18} color={colors.text.muted} />}
      </GlassCard>
    </TouchableOpacity>
  );
  const last = (k: string) => status[k]?.last_import ? `Last import ${status[k].last_import!.slice(0, 10)} · ${status[k].records} records` : 'Not imported yet';

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <LinearGradient colors={['#334155', '#1E293B', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Devices & Imports</Text>
          <Text style={styles.heroTitle}>Bring in your real data</Text>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Bluetooth" icon="bluetooth" iconColor={TINT} />
          <Row id="strap" icon="heart" title="Heart-rate strap" sub="Polar, Garmin HRM, Wahoo and other standard straps. Used for HRV readings and breathing."
            onPress={() => router.push('/hrv' as any)} />
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Import Files" icon="document-attach" iconColor={TINT} />
          <Row id="gpx" icon="map" title="GPX track (run)" sub={last('gpx')} onPress={() => importGpx('run')} />
          <Row id="gpx-ride" icon="bicycle" title="GPX track (ride)" sub="From Strava, Komoot, Garmin or a phone app" onPress={() => importGpx('ride')} />
          <Row id="strava" icon="flash" title="Strava activities (JSON)" sub={last('strava')} onPress={() => importJson('strava')} />
          <Row id="garmin" icon="watch" title="Garmin workouts and sleep (JSON)" sub={last('garmin')} onPress={() => importJson('garmin')} />
          <Text style={styles.sub}>Imports are added to your history once; importing the same file again changes nothing.</Text>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Phone Health Apps" icon="phone-portrait" iconColor={TINT} />
          <HealthConnectCard />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { paddingLeft: 40, color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroTitle: { color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  title: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 2, lineHeight: 17 },
  buttons: { flexDirection: 'row', gap: 10, marginTop: 12 },
  button: { flex: 1, backgroundColor: colors.primary, borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  secondary: { backgroundColor: '#334155' },
  buttonText: { color: '#fff', fontWeight: '700', fontSize: 14 },
});
