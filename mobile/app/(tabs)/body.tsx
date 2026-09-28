/**
 * Body — weight and measurements over time, goals, and progress photos.
 * Changes are shown per measure, only between entries that recorded it.
 * Photos stay on this phone; only their location on the device is saved.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, Image, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { colors, spacing } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { asArray, deleteJson, getJson, postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const TINT = '#F97316';
const FIELDS = [
  { key: 'weight_kg', label: 'Weight (kg)' },
  { key: 'waist_cm', label: 'Waist (cm)' },
  { key: 'body_fat_pct', label: 'Body fat % (if measured)' },
  { key: 'hips_cm', label: 'Hips (cm)' },
  { key: 'chest_cm', label: 'Chest (cm)' },
] as const;

export default function BodyScreen() {
  const userId = useUserStore((s) => s.userId);
  const [form, setForm] = useState<Record<string, string>>({});
  const [entries, setEntries] = useState<any[]>([]);
  const [trends, setTrends] = useState<any>(null);
  const [goals, setGoals] = useState<any[]>([]);
  const [goalName, setGoalName] = useState('');
  const [goalTarget, setGoalTarget] = useState('');
  const [goalUnit, setGoalUnit] = useState('kg');
  const [progress, setProgress] = useState<Record<string, string>>({});
  const [photos, setPhotos] = useState<any[]>([]);

  const load = useCallback(async () => {
    const [m, t, g, p] = await Promise.all([
      getJson<any[]>(`/body/measurements?user_id=${userId}&days=365`),
      getJson<any>(`/body/trends?user_id=${userId}`),
      getJson<any[]>(`/goals?user_id=${userId}`),
      getJson<any[]>(`/progress-photos?user_id=${userId}`),
    ]);
    setEntries(asArray(m).slice().reverse());
    setTrends(t);
    setGoals(asArray(g));
    setPhotos(asArray(p).slice().reverse());
  }, [userId]);
  useEffect(() => { load(); }, [load]);

  const save = async () => {
    const body: Record<string, number> = {};
    for (const f of FIELDS) if (form[f.key]) body[f.key] = Number(form[f.key]);
    if (!Object.keys(body).length) return;
    if (await postJson(`/body/measurements?user_id=${userId}`, body)) { setForm({}); load(); }
    else Alert.alert('Not saved', 'Check the values are in a sensible range.');
  };
  const addGoal = async () => {
    if (!goalName.trim() || !goalTarget) return;
    if (await postJson(`/goals?user_id=${userId}`, { name: goalName, goal_type: 'body_composition', target_value: Number(goalTarget), target_unit: goalUnit })) {
      setGoalName(''); setGoalTarget(''); load();
    }
  };
  const updateGoal = async (id: string) => {
    const v = Number(progress[id]);
    if (!Number.isFinite(v)) return;
    if (await postJson(`/goals/${id}/update?user_id=${userId}`, { current_value: v })) { setProgress({ ...progress, [id]: '' }); load(); }
  };
  const addPhoto = async (angle: string) => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return;
    const r = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.7 });
    if (r.canceled || !r.assets?.[0]) return;
    const latestWeight = entries.find((e) => e.weight_kg)?.weight_kg;
    if (await postJson(`/progress-photos?user_id=${userId}`, { photo_uri: r.assets[0].uri, angle, weight_kg: latestWeight ?? undefined })) load();
  };
  const t30 = trends?.['30d'];
  const fmt = (v: number | null | undefined, unit: string) => (v == null ? '--' : `${v > 0 ? '+' : ''}${v} ${unit}`);

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <LinearGradient colors={[TINT, '#C2410C', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Body</Text>
          <Text style={styles.heroTitle}>{entries.find((e) => e.weight_kg)?.weight_kg ? `${entries.find((e) => e.weight_kg).weight_kg} kg` : 'Log your first measurement'}</Text>
          {t30 && <Text style={styles.heroMuted}>30 days: weight {fmt(t30.weight_change, 'kg')} · waist {fmt(t30.waist_change, 'cm')}</Text>}
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Log Today" icon="scale" iconColor={TINT} />
          <GlassCard>
            {FIELDS.map((f) => (
              <TextInput key={f.key} style={styles.input} placeholder={f.label} placeholderTextColor={colors.text.muted}
                keyboardType="decimal-pad" value={form[f.key] ?? ''} onChangeText={(v) => setForm({ ...form, [f.key]: v })} />
            ))}
            <TouchableOpacity style={styles.btn} onPress={save}><Text style={styles.btnText}>Save</Text></TouchableOpacity>
            <Text style={styles.sub}>Weigh at the same time of day, ideally mornings before eating. Your nutrition targets use your latest weight.</Text>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Goals" icon="flag" iconColor={TINT} />
          <GlassCard>
            {goals.map((g) => (
              <View key={g.id} style={styles.item}>
                <Text style={styles.itemTitle}>{g.name}</Text>
                <Text style={styles.sub}>{g.current_value} / {g.target_value} {g.target_unit} · {Math.round(g.progress_pct)}% · {g.status}</Text>
                <View style={styles.row}>
                  <TextInput style={[styles.input, { flex: 1 }]} placeholder="Where are you now?" placeholderTextColor={colors.text.muted}
                    keyboardType="decimal-pad" value={progress[g.id] ?? ''} onChangeText={(v) => setProgress({ ...progress, [g.id]: v })} />
                  <TouchableOpacity style={[styles.btn, { paddingHorizontal: 16 }]} onPress={() => updateGoal(g.id)}><Text style={styles.btnText}>Update</Text></TouchableOpacity>
                </View>
              </View>
            ))}
            <TextInput style={styles.input} placeholder="New goal (e.g. Waist 85 cm)" placeholderTextColor={colors.text.muted} value={goalName} onChangeText={setGoalName} />
            <View style={styles.row}>
              <TextInput style={[styles.input, { flex: 1 }]} placeholder="Target" placeholderTextColor={colors.text.muted} keyboardType="decimal-pad" value={goalTarget} onChangeText={setGoalTarget} />
              <TextInput style={[styles.input, { width: 80 }]} placeholder="Unit" placeholderTextColor={colors.text.muted} value={goalUnit} onChangeText={setGoalUnit} />
            </View>
            <TouchableOpacity style={styles.btn} onPress={addGoal}><Text style={styles.btnText}>Add goal</Text></TouchableOpacity>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Progress Photos" subtitle="Stored only on this phone" icon="images" iconColor={TINT} />
          <GlassCard>
            <View style={styles.row}>
              {['front', 'side', 'back'].map((a) => (
                <TouchableOpacity key={a} style={[styles.btn, { flex: 1 }]} onPress={() => addPhoto(a)}><Text style={styles.btnText}>+ {a}</Text></TouchableOpacity>
              ))}
            </View>
            <View style={styles.grid}>
              {photos.slice(0, 12).map((p) => (
                <TouchableOpacity key={p.id} onLongPress={async () => { await deleteJson(`/progress-photos/${p.id}?user_id=${userId}`); load(); }}>
                  <Image source={{ uri: p.photo_uri }} style={styles.photo} />
                  <Text style={styles.sub}>{p.date} · {p.angle}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="History" icon="list" iconColor={TINT} />
          {entries.slice(0, 20).map((e) => (
            <GlassCard key={e.id} style={styles.gap}>
              <Text style={styles.itemTitle}>{e.date}</Text>
              <Text style={styles.sub}>
                {[e.weight_kg && `${e.weight_kg} kg`, e.body_fat_pct && `${e.body_fat_pct}% fat`,
                  ...Object.entries(e.measurements ?? {}).filter(([, v]) => v).map(([k, v]) => `${k} ${v} cm`)].filter(Boolean).join(' · ')}
              </Text>
            </GlassCard>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13, marginTop: 4 },
  heroTitle: { color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, marginTop: 8 },
  btn: { backgroundColor: TINT, borderRadius: 12, padding: 12, alignItems: 'center', marginTop: 8 },
  btnText: { color: '#fff', fontWeight: '700', textTransform: 'capitalize' },
  row: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 4, lineHeight: 17 },
  item: { paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: colors.surface.border },
  itemTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  photo: { width: 96, height: 128, borderRadius: 10, backgroundColor: colors.bg.card },
  gap: { marginBottom: 8 },
});
