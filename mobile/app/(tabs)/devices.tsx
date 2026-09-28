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

const TINT = '#64748B';

interface SourceStatus { imports: number; records: number; last_import: string | null }

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
    Alert.alert('Imported', `${r.workouts_saved ?? 0} workouts${nights}. ${r.skipped_duplicates ?? 0} already imported.`);
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
          <GlassCard>
            <Text style={styles.sub}>Automatic sync with Health Connect (Android) and Apple Health is being built. Until then, add readings in your morning check-in or import files above.</Text>
          </GlassCard>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroTitle: { color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  title: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 2, lineHeight: 17 },
});
