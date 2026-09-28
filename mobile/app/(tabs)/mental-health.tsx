/**
 * Mind — mood check-ins, a journal, validated questionnaires (WHO-5, PHQ-9,
 * GAD-7) and crisis lines. Scores are screening results with a next step,
 * never a diagnosis.
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar, TextInput,
  ActivityIndicator, RefreshControl, Alert, Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { colors, spacing } from '../../src/theme';
import { GlassCard, ScoreRing, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, getJson, postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const TINT = '#8B5CF6';
const TAGS = ['work', 'sleep', 'exercise', 'family', 'friends', 'health', 'money', 'weather'];
const CRISIS = [
  { name: 'Tele-MANAS (free, 24/7)', phone: '14416' },
  { name: 'iCall (TISS)', phone: '9152987821' },
  { name: 'Emergency', phone: '112' },
];
const QUESTIONNAIRES = [
  { id: 'who5', title: 'WHO-5 Wellbeing', about: '5 questions · 1 min', icon: 'sunny' },
  { id: 'phq9', title: 'PHQ-9 Mood', about: '9 questions · 2 min', icon: 'cloudy' },
  { id: 'gad7', title: 'GAD-7 Worry & anxiety', about: '7 questions · 2 min', icon: 'pulse' },
] as const;

interface MoodEntry { id: string; mood: number; energy: number; anxiety: number; notes?: string; tags: string[]; logged_at: string }
interface MoodTrend { entries: MoodEntry[]; avg_mood: number; avg_energy: number; avg_anxiety: number; mood_trend: string; count: number }
interface QResult { questionnaire: string; title: string; score: number; max_score: number; range: string; next_step: string; taken_at: string; crisis?: { message: string } }
interface Questionnaire { id: string; title: string; prompt: string; options: string[]; questions: string[] }

function Scale({ label, value, onChange, low, high }: { label: string; value: number; onChange: (v: number) => void; low: string; high: string }) {
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.fieldLabel}>{label}: {value}/10</Text>
      <View style={styles.scaleRow}>
        {Array.from({ length: 10 }, (_, i) => i + 1).map((v) => (
          <TouchableOpacity key={v} onPress={() => onChange(v)} style={[styles.scaleDot, v <= value && { backgroundColor: TINT }]}
            accessibilityLabel={`${label} ${v}`} />
        ))}
      </View>
      <View style={styles.scaleEnds}><Text style={styles.muted}>{low}</Text><Text style={styles.muted}>{high}</Text></View>
    </View>
  );
}

interface ThoughtRecord { id: string; situation: string; thought: string; emotion: string; intensity_before: number; balanced_thought: string; intensity_after: number; created_at: string }

const TR_STEPS = [
  { key: 'situation', label: 'What happened?', placeholder: 'Where were you, what was going on' },
  { key: 'thought', label: 'What went through your mind?', placeholder: 'The automatic thought, word for word' },
  { key: 'emotion', label: 'What did you feel?', placeholder: 'e.g. anxious, angry, ashamed' },
  { key: 'evidence_for', label: 'What supports that thought?', placeholder: 'Facts only' },
  { key: 'evidence_against', label: 'What does not fit it?', placeholder: 'Facts only' },
  { key: 'balanced_thought', label: 'A more balanced thought', placeholder: 'What would you tell a friend?' },
] as const;

function ThoughtRecords({ userId }: { userId: string }) {
  const [open, setOpen] = useState(false);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [before, setBefore] = useState(70);
  const [after, setAfter] = useState(40);
  const { data, reload } = useApis<{ records: ThoughtRecord[] }>({ records: `/mental-health/thought-records?user_id=${userId}&limit=5` });
  const save = async () => {
    if (!fields.situation?.trim() || !fields.thought?.trim() || !fields.emotion?.trim()) {
      return Alert.alert('Almost there', 'Fill in what happened, the thought and the feeling.');
    }
    const r = await postJson<{ change: number }>('/mental-health/thought-records', {
      user_id: userId, ...fields, intensity_before: before, intensity_after: after,
    });
    if (!r) return Alert.alert('Not saved', 'The record could not be saved.');
    setFields({});
    setOpen(false);
    reload();
  };
  const step = (v: number, d: number) => Math.max(0, Math.min(100, v + d));
  return (
    <View style={styles.section}>
      <SectionHeaderPremium title="Thought Record" subtitle="A CBT exercise for a thought that keeps coming back" icon="git-compare" iconColor={TINT} />
      {!open ? (
        <TouchableOpacity style={styles.primaryBtn} onPress={() => setOpen(true)}>
          <Text style={styles.primaryBtnText}>Work through a thought</Text>
        </TouchableOpacity>
      ) : (
        <GlassCard>
          {TR_STEPS.map((f) => (
            <View key={f.key}>
              <Text style={[styles.fieldLabel, { marginTop: 10 }]}>{f.label}</Text>
              <TextInput style={styles.input} placeholder={f.placeholder} placeholderTextColor={colors.text.muted} multiline
                value={fields[f.key] ?? ''} onChangeText={(t) => setFields((x) => ({ ...x, [f.key]: t }))} maxLength={500} />
            </View>
          ))}
          {[['How strong was the feeling before?', before, setBefore], ['And now?', after, setAfter]].map(([label, v, set]: any) => (
            <View key={label} style={styles.qCard}>
              <Text style={[styles.fieldLabel, { flex: 1 }]}>{label}</Text>
              <TouchableOpacity onPress={() => set(step(v, -10))}><Ionicons name="remove-circle-outline" size={24} color={colors.text.secondary} /></TouchableOpacity>
              <Text style={styles.cardTitle}>{v}%</Text>
              <TouchableOpacity onPress={() => set(step(v, 10))}><Ionicons name="add-circle-outline" size={24} color={colors.text.secondary} /></TouchableOpacity>
            </View>
          ))}
          <TouchableOpacity style={styles.primaryBtn} onPress={save}><Text style={styles.primaryBtnText}>Save record</Text></TouchableOpacity>
        </GlassCard>
      )}
      {asArray<ThoughtRecord>(data.records).map((r) => (
        <GlassCard key={r.id} style={[styles.gap, { marginTop: 10 }]}>
          <Text style={styles.cardTitle}>{r.emotion}: {r.intensity_before}% to {r.intensity_after}%</Text>
          <Text style={styles.body}>"{r.thought}"</Text>
          {r.balanced_thought ? <Text style={[styles.body, { color: TINT }]}>{r.balanced_thought}</Text> : null}
          <Text style={styles.muted}>{r.created_at.slice(0, 10)}</Text>
        </GlassCard>
      ))}
    </View>
  );
}

export default function MindScreen() {
  const router = useRouter();
  const userId = useUserStore((s) => s.userId);
  const [mood, setMood] = useState(6);
  const [energy, setEnergy] = useState(6);
  const [anxiety, setAnxiety] = useState(3);
  const [tags, setTags] = useState<string[]>([]);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [active, setActive] = useState<Questionnaire | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [lastResult, setLastResult] = useState<QResult | null>(null);

  const { data, loading, refresh, refreshing, reload } = useApis<{
    trend: MoodTrend;
    results: { latest: Record<string, QResult> };
  }>({
    trend: `/mental-health?user_id=${userId}&days=14`,
    results: `/mental-health/questionnaires?user_id=${userId}`,
  });
  const trend = data.trend;
  const latest = data.results?.latest ?? {};
  const who5 = latest.who5;

  const logMood = async () => {
    setBusy(true);
    const r = await postJson('/mental-health', { user_id: userId, mood, energy, anxiety, notes: note.trim() || undefined, tags });
    setBusy(false);
    if (!r) return Alert.alert('Not saved', 'Your check-in could not be saved.');
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setNote('');
    setTags([]);
    await reload();
  };

  const start = async (id: string) => {
    const q = await getJson<Questionnaire>(`/mental-health/questionnaires/${id}`);
    if (!q) return Alert.alert('Unavailable', 'The questionnaire could not be loaded.');
    setLastResult(null);
    setAnswers([]);
    setActive(q);
  };

  const answer = async (value: number) => {
    if (!active) return;
    const next = [...answers, value];
    if (next.length < active.questions.length) return setAnswers(next);
    const r = await postJson<QResult>(`/mental-health/questionnaires/${active.id}`, { user_id: userId, answers: next });
    setActive(null);
    setAnswers([]);
    if (!r) return Alert.alert('Not saved', 'Your answers could not be scored.');
    setLastResult(r);
    await reload();
  };

  if (loading) {
    return <View style={[styles.container, styles.center]}><ActivityIndicator size="large" color={TINT} /></View>;
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={TINT} />}>
        <LinearGradient colors={[TINT, '#6D28D9', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Mind</Text>
          <View style={styles.heroRow}>
            {who5 ? (
              <ScoreRing score={who5.score} size={112} strokeWidth={9} color="#fff" label="WELLBEING" sublabel={who5.range} />
            ) : (
              <TouchableOpacity onPress={() => start('who5')} style={styles.heroCta}>
                <Ionicons name="sunny" size={22} color="#fff" />
                <Text style={styles.heroCtaText}>Measure your wellbeing</Text>
              </TouchableOpacity>
            )}
            <View style={{ flex: 1 }}>
              {trend && trend.count > 0 ? (
                <>
                  <Text style={styles.heroValue}>{trend.avg_mood}/10</Text>
                  <Text style={styles.heroMuted}>average mood over {trend.count} check-ins</Text>
                  {trend.mood_trend !== 'insufficient_data' && <Text style={[styles.heroMuted, { marginTop: 4 }]}>Trend: {trend.mood_trend}</Text>}
                </>
              ) : (
                <Text style={styles.heroMuted}>Check in below to start tracking your mood.</Text>
              )}
            </View>
          </View>
        </LinearGradient>

        {active && (
          <View style={styles.section}>
            <GlassCard>
              <Text style={styles.muted}>{active.title} · question {answers.length + 1} of {active.questions.length}</Text>
              <Text style={styles.qPrompt}>{active.prompt}</Text>
              <Text style={styles.qText}>{active.questions[answers.length]}</Text>
              {active.options.map((opt, i) => (
                <TouchableOpacity key={opt} style={styles.option} onPress={() => answer(i)}>
                  <Text style={styles.optionText}>{opt}</Text>
                </TouchableOpacity>
              ))}
              <TouchableOpacity onPress={() => setActive(null)}><Text style={[styles.muted, { marginTop: 10 }]}>Cancel</Text></TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {lastResult && (
          <View style={styles.section}>
            <GlassCard style={{ borderLeftWidth: 3, borderLeftColor: lastResult.crisis ? '#EF4444' : TINT }}>
              <Text style={styles.cardTitle}>{lastResult.title}: {lastResult.score}/{lastResult.max_score} ({lastResult.range})</Text>
              <Text style={styles.body}>{lastResult.next_step}</Text>
              {lastResult.crisis && <Text style={[styles.body, { color: '#EF4444' }]}>{lastResult.crisis.message}</Text>}
              <Text style={styles.muted}>A screening score, not a diagnosis.</Text>
            </GlassCard>
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Check In" icon="happy" iconColor={TINT} />
          <GlassCard>
            <Scale label="Mood" value={mood} onChange={setMood} low="very low" high="great" />
            <Scale label="Energy" value={energy} onChange={setEnergy} low="exhausted" high="energised" />
            <Scale label="Anxiety" value={anxiety} onChange={setAnxiety} low="calm" high="very anxious" />
            <Text style={[styles.fieldLabel, { marginTop: 14 }]}>What is affecting you? (optional)</Text>
            <View style={styles.chipRow}>
              {TAGS.map((t) => (
                <TouchableOpacity key={t} style={[styles.chip, tags.includes(t) && styles.chipActive]}
                  onPress={() => setTags(tags.includes(t) ? tags.filter((x) => x !== t) : [...tags, t])}>
                  <Text style={[styles.chipText, tags.includes(t) && styles.chipTextActive]}>{t}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TextInput style={styles.input} placeholder="Journal note (optional)" placeholderTextColor={colors.text.muted}
              value={note} onChangeText={setNote} multiline maxLength={500} />
            <TouchableOpacity style={styles.primaryBtn} onPress={logMood} disabled={busy}>
              <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save check-in'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Questionnaires" subtitle="Validated, 1-2 minutes each" icon="clipboard" iconColor={TINT} />
          {QUESTIONNAIRES.map((q) => {
            const r = latest[q.id];
            return (
              <TouchableOpacity key={q.id} onPress={() => start(q.id)}>
                <GlassCard style={styles.qCard}>
                  <Ionicons name={q.icon as any} size={22} color={TINT} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.cardTitle}>{q.title}</Text>
                    <Text style={styles.muted}>{r ? `Last: ${r.score}/${r.max_score}, ${r.range} · ${r.taken_at.slice(0, 10)}` : q.about}</Text>
                  </View>
                  <Ionicons name="chevron-forward" size={18} color={colors.text.muted} />
                </GlassCard>
              </TouchableOpacity>
            );
          })}
        </View>

        {trend && trend.count > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Journal" icon="book" iconColor={TINT} />
            {asArray<MoodEntry>(trend.entries).slice().reverse().slice(0, 10).map((e) => (
              <GlassCard key={e.id} style={styles.gap}>
                <Text style={styles.cardTitle}>Mood {e.mood} · energy {e.energy} · anxiety {e.anxiety}</Text>
                <Text style={styles.muted}>{e.logged_at.slice(0, 16).replace('T', ' ')}{e.tags.length ? ` · ${e.tags.join(', ')}` : ''}</Text>
                {e.notes ? <Text style={styles.body}>{e.notes}</Text> : null}
              </GlassCard>
            ))}
          </View>
        )}

        <ThoughtRecords userId={userId} />

        <View style={styles.section}>
          <TouchableOpacity onPress={() => router.push('/hrv' as any)}>
            <GlassCard style={styles.qCard}>
              <Ionicons name="leaf" size={22} color="#10B981" />
              <Text style={[styles.cardTitle, { flex: 1 }]}>Calm down now: breathing coach</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.text.muted} />
            </GlassCard>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Talk To Someone" icon="call" iconColor="#EF4444" />
          {CRISIS.map((c) => (
            <TouchableOpacity key={c.phone} onPress={() => Linking.openURL(`tel:${c.phone}`)}>
              <GlassCard style={[styles.qCard, styles.gap]}>
                <Ionicons name="call" size={20} color="#EF4444" />
                <Text style={[styles.cardTitle, { flex: 1 }]}>{c.name}</Text>
                <Text style={styles.phone}>{c.phone}</Text>
              </GlassCard>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 16, marginTop: 12 },
  heroValue: { color: '#fff', fontSize: 30, fontWeight: '800' },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroCta: { width: 112, height: 112, borderRadius: 56, borderWidth: 2, borderColor: 'rgba(255,255,255,0.6)', alignItems: 'center', justifyContent: 'center', padding: 8 },
  heroCtaText: { color: '#fff', fontSize: 12, fontWeight: '700', textAlign: 'center', marginTop: 4 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  fieldLabel: { color: colors.text.secondary, fontSize: 13, fontWeight: '600' },
  scaleRow: { flexDirection: 'row', gap: 6, marginTop: 8 },
  scaleDot: { flex: 1, height: 22, borderRadius: 6, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  scaleEnds: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  muted: { color: colors.text.muted, fontSize: 12, marginTop: 2 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: TINT + '25', borderColor: TINT },
  chipText: { color: colors.text.muted, fontSize: 12, textTransform: 'capitalize' },
  chipTextActive: { color: TINT, fontWeight: '700' },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, marginTop: 12, minHeight: 60 },
  primaryBtn: { backgroundColor: TINT, borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 14 },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  qCard: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  qPrompt: { color: colors.text.secondary, fontSize: 13, marginTop: 8 },
  qText: { color: colors.text.primary, fontSize: 17, fontWeight: '700', marginTop: 6, marginBottom: 10 },
  option: { borderWidth: 1, borderColor: TINT + '60', borderRadius: 12, padding: 12, marginTop: 8 },
  optionText: { color: colors.text.primary, fontSize: 14 },
  cardTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  body: { color: colors.text.secondary, fontSize: 14, marginTop: 6, lineHeight: 20 },
  gap: { marginBottom: 10 },
  phone: { color: '#EF4444', fontWeight: '700' },
});
