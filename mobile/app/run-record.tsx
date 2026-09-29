/**
 * Record a run, walk, ride or hike. Keeps recording with the screen off
 * (a notification shows while it does); the server filters bad GPS fixes and
 * saves the finished route to workout history.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, Linking } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../src/theme';
import { activeRun, ActiveRun, discardRun, finishRun, FinishResult, Fix, haversineM, onFixes, startRun } from '../src/services/runTracker';

const TYPES = [
  { id: 'running', label: 'Run', icon: 'walk' },
  { id: 'walking', label: 'Walk', icon: 'footsteps' },
  { id: 'cycling', label: 'Ride', icon: 'bicycle' },
  { id: 'hiking', label: 'Hike', icon: 'trail-sign' },
] as const;

const clock = (s: number) => {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return `${h ? `${h}:` : ''}${String(m).padStart(h ? 2 : 1, '0')}:${String(sec).padStart(2, '0')}`;
};
const pace = (secPerKm: number) => (secPerKm > 0 && Number.isFinite(secPerKm) ? `${Math.floor(secPerKm / 60)}:${String(Math.round(secPerKm % 60)).padStart(2, '0')} /km` : '–');

export default function RunRecordScreen() {
  const router = useRouter();
  const [type, setType] = useState<(typeof TYPES)[number]['id']>('running');
  const [run, setRun] = useState<ActiveRun | null>(null);
  const [meters, setMeters] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<FinishResult | null>(null);
  const last = useRef<Fix | null>(null);

  useEffect(() => {
    activeRun().then(setRun);
  }, []);

  useEffect(() => {
    if (!run) return;
    const tick = setInterval(() => setNow(Date.now()), 1000);
    // On-screen distance is a rough running total from good fixes; the saved figure comes from the server.
    const off = onFixes((fixes) => {
      let add = 0;
      for (const f of fixes) {
        if ((f.accuracy_m ?? 0) > 30) continue;
        if (last.current) add += haversineM(last.current, f);
        last.current = f;
      }
      setMeters((m) => m + add);
    });
    return () => {
      clearInterval(tick);
      off();
    };
  }, [run]);

  const start = async () => {
    setBusy(true);
    const r = await startRun(type);
    setBusy(false);
    if (r.ok) {
      last.current = null;
      setMeters(0);
      setResult(null);
      setRun(r.run);
    } else if (r.reason === 'permission') {
      Alert.alert('Location needed', 'Allow location while using the app to record a route.', [
        { text: 'Cancel' }, { text: 'Open settings', onPress: () => Linking.openSettings() },
      ]);
    } else if (r.reason === 'services-off') {
      Alert.alert('Location is off', 'Turn on location in quick settings, then start again.');
    } else {
      Alert.alert('Could not start', 'The server could not be reached. Check your connection.');
    }
  };

  const stop = async () => {
    setBusy(true);
    const r = await finishRun();
    setBusy(false);
    if (!r) {
      Alert.alert('Saved on this phone', 'The route could not be uploaded yet. Open this screen again when you are online and tap Finish.');
      return;
    }
    setRun(null);
    setResult(r);
  };

  const discard = () =>
    Alert.alert('Discard this recording?', 'Nothing will be saved.', [
      { text: 'Keep recording' },
      { text: 'Discard', style: 'destructive', onPress: async () => { await discardRun(); setRun(null); } },
    ]);

  const elapsed = run ? (now - run.startedAt) / 1000 : 0;

  return (
    <View style={s.container}>
      <TouchableOpacity onPress={() => router.back()} style={s.back} accessibilityLabel="Back">
        <Ionicons name="chevron-back" size={26} color={colors.text.primary} />
      </TouchableOpacity>
      <Text style={s.title}>{run ? 'Recording' : 'Record a route'}</Text>

      {!run && !result && (
        <View style={s.types}>
          {TYPES.map((t) => (
            <TouchableOpacity key={t.id} onPress={() => setType(t.id)} style={[s.type, type === t.id && s.typeOn]} accessibilityRole="radio"
              accessibilityState={{ selected: type === t.id }}>
              <Ionicons name={t.icon as any} size={22} color={type === t.id ? '#fff' : colors.text.secondary} />
              <Text style={[s.typeText, type === t.id && { color: '#fff' }]}>{t.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {!run && !result && (
        <View style={s.explain}>
          <Text style={s.explainText}>Pick an activity and tap Start. AdapFit records your route with GPS, even with the screen off.</Text>
          <Text style={s.explainText}>The distance you see while moving is rough. The saved figure is recalculated when you finish, and anything under 50 m is not saved.</Text>
          <Text style={s.explainText}>Location is used only while you record, and only for this route.</Text>
        </View>
      )}

      {!!run && (
        <View style={s.stats}>
          <Text style={s.big}>{(meters / 1000).toFixed(2)}<Text style={s.unit}> km</Text></Text>
          <View style={s.row}>
            <View style={s.cell}><Text style={s.value}>{clock(elapsed)}</Text><Text style={s.label}>Time</Text></View>
            <View style={s.cell}><Text style={s.value}>{pace(meters > 50 ? elapsed / (meters / 1000) : 0)}</Text><Text style={s.label}>Average pace</Text></View>
          </View>
          <Text style={s.note}>Keeps recording with the screen off. The final distance is recalculated after you finish.</Text>
        </View>
      )}

      {!!result && (
        <View style={s.stats}>
          <Text style={s.big}>{result.stats.distance_km.toFixed(2)}<Text style={s.unit}> km</Text></Text>
          <View style={s.row}>
            <View style={s.cell}><Text style={s.value}>{clock(result.stats.duration_seconds)}</Text><Text style={s.label}>Time</Text></View>
            <View style={s.cell}><Text style={s.value}>{pace(result.stats.distance_km >= 0.05 ? result.stats.avg_pace_seconds_per_km : 0)}</Text><Text style={s.label}>Average pace</Text></View>
            <View style={s.cell}><Text style={s.value}>{Math.round(result.stats.elevation_gain_m)} m</Text><Text style={s.label}>Climb</Text></View>
          </View>
          <Text style={s.note}>{result.saved_to_history ? 'Saved to your workout history.' : 'Too short to save: under 50 m, or too few good GPS fixes.'}</Text>
        </View>
      )}

      <View style={s.actions}>
        {busy ? <ActivityIndicator color={colors.primary} /> : run ? (
          <>
            <TouchableOpacity style={[s.button, s.stop]} onPress={stop} accessibilityRole="button"><Text style={s.buttonText}>Finish</Text></TouchableOpacity>
            <TouchableOpacity onPress={discard} accessibilityRole="button"><Text style={s.link}>Discard</Text></TouchableOpacity>
          </>
        ) : (
          <TouchableOpacity style={s.button} onPress={start} accessibilityRole="button">
            <Text style={s.buttonText}>{result ? 'Record another' : 'Start'}</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep, padding: spacing.lg, paddingTop: 56 },
  back: { position: 'absolute', top: 48, left: 12, padding: 8, zIndex: 1 },
  title: { fontSize: 26, fontWeight: '800', color: colors.text.primary, textAlign: 'center', marginBottom: spacing.xl },
  explain: { marginTop: 32, paddingHorizontal: 24, gap: 14 },
  explainText: { color: colors.text.secondary, fontSize: 14, lineHeight: 21, textAlign: 'center' },
  types: { flexDirection: 'row', gap: 10, justifyContent: 'center' },
  type: { alignItems: 'center', gap: 4, paddingVertical: 12, paddingHorizontal: 16, borderRadius: radius.md, backgroundColor: colors.bg.card },
  typeOn: { backgroundColor: colors.primary },
  typeText: { color: colors.text.secondary, fontWeight: '600' },
  stats: { alignItems: 'center', marginTop: spacing.lg },
  big: { fontSize: 72, fontWeight: '800', color: colors.text.primary },
  unit: { fontSize: 24, color: colors.text.muted },
  row: { flexDirection: 'row', gap: 28, marginTop: spacing.lg },
  cell: { alignItems: 'center' },
  value: { fontSize: 22, fontWeight: '700', color: colors.text.primary },
  label: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  note: { fontSize: 12, color: colors.text.muted, textAlign: 'center', marginTop: spacing.lg, lineHeight: 17 },
  actions: { position: 'absolute', bottom: 48, left: spacing.lg, right: spacing.lg, alignItems: 'center', gap: 16 },
  button: { alignSelf: 'stretch', backgroundColor: colors.primary, paddingVertical: 18, borderRadius: radius.lg, alignItems: 'center' },
  stop: { backgroundColor: colors.health.danger },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '800' },
  link: { color: colors.text.muted, fontSize: 15 },
});
