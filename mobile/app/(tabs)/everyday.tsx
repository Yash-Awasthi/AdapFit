/**
 * Everyday Wellbeing — today's air, desk health, a working-memory game,
 * focus modes, and travel health. Small habits that add up.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing } from '../../src/theme';
import { GlassCard } from '../../src/components/PremiumComponents';
import { asArray, getJson, postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const TINT = '#22C55E';
const AQI_COLOR: Record<string, string> = { good: '#10B981', moderate: '#F59E0B', unhealthy_sensitive: '#F97316', unhealthy: '#EF4444', very_unhealthy: '#7C3AED', hazardous: '#7F1D1D' };

function Section({ icon, title, sub, children }: { icon: string; title: string; sub: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <GlassCard style={styles.section}>
      <TouchableOpacity style={styles.head} onPress={() => setOpen(!open)} accessibilityRole="button" accessibilityState={{ expanded: open }}>
        <Ionicons name={icon as any} size={22} color={TINT} />
        <View style={{ flex: 1 }}><Text style={styles.title}>{title}</Text><Text style={styles.sub}>{sub}</Text></View>
        <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={18} color={colors.text.muted} />
      </TouchableOpacity>
      {open && <View style={{ marginTop: 12 }}>{children}</View>}
    </GlassCard>
  );
}
const Btn = ({ label, onPress }: { label: string; onPress: () => void }) => (
  <TouchableOpacity style={styles.btn} onPress={onPress}><Text style={styles.btnText}>{label}</Text></TouchableOpacity>
);

function AirToday() {
  const [city, setCity] = useState('');
  const [data, setData] = useState<any>(null);
  const run = async () => {
    if (!city.trim()) return;
    const r = await getJson<any>(`/environmental/outdoor-safety/${encodeURIComponent(city.trim())}?activity=running`);
    setData(r?.data ?? { status: 'error' });
  };
  const aqi = data?.aqi;
  return (
    <>
      <TextInput style={styles.input} value={city} onChangeText={setCity} placeholder="Your city (e.g. Pune)" placeholderTextColor={colors.text.muted} onSubmitEditing={run} />
      <Btn label="Check the air" onPress={run} />
      {data?.status === 'ok' && (
        <View style={styles.result}>
          {aqi?.aqi != null && <Text style={[styles.big, { color: AQI_COLOR[aqi.level] ?? colors.text.primary }]}>AQI {aqi.aqi} · {String(aqi.level).replace(/_/g, ' ')}</Text>}
          {data.uv?.uv_index != null && <Text style={styles.body}>UV index {data.uv.uv_index}</Text>}
          <Text style={styles.body}>Outdoor run: {data.safety_level}. {data.recommendation}</Text>
          <Text style={styles.sub}>Live data from Open-Meteo.</Text>
        </View>
      )}
      {data && data.status !== 'ok' && <Text style={styles.sub}>Could not get air data for that place.</Text>}
    </>
  );
}

function DeskHealth() {
  const [ex, setEx] = useState<any[]>([]);
  const [rsi, setRsi] = useState<Record<string, string[]>>({});
  useEffect(() => {
    getJson<any>('/ergonomics/exercises').then((r) => setEx(asArray(r?.data)));
    getJson<any>('/ergonomics/rsi-prevention').then((r) => setRsi(r?.data ?? {}));
  }, []);
  return (
    <>
      <Text style={styles.body}>Every 20 minutes, look 20 feet away for 20 seconds. Stand up every hour.</Text>
      {ex.map((e) => <Text key={e.name} style={styles.body}>• {e.name}: {e.description}</Text>)}
      {Object.entries(rsi).map(([k, tips]) => (
        <View key={k}><Text style={styles.label}>{k.replace(/_/g, ' ')}</Text>{asArray<string>(tips).map((t) => <Text key={t} style={styles.sub}>• {t}</Text>)}</View>
      ))}
    </>
  );
}

/** Digit span: a standard working-memory measure. The score is the longest sequence recalled. */
function DigitSpan() {
  const userId = useUserStore((s) => s.userId);
  const [phase, setPhase] = useState<'idle' | 'show' | 'answer' | 'done'>('idle');
  const [length, setLength] = useState(3);
  const [seq, setSeq] = useState('');
  const [answer, setAnswer] = useState('');
  const [best, setBest] = useState(0);
  const session = useRef<string | null>(null);
  const round = (n: number) => {
    const s = Array.from({ length: n }, () => Math.floor(Math.random() * 10)).join('');
    setSeq(s); setAnswer(''); setPhase('show');
    setTimeout(() => setPhase('answer'), 800 * n + 600);
  };
  const start = async () => {
    const r = await postJson<any>('/cognitive/exercise/start', { user_id: userId, exercise_id: 'mem_1' });
    session.current = r?.data?.session_id ?? null;
    setBest(0); setLength(3); round(3);
  };
  const submit = async () => {
    if (answer === seq) { setBest(length); setLength(length + 1); round(length + 1); return; }
    setPhase('done');
    if (session.current) await postJson('/cognitive/exercise/complete', { user_id: userId, session_id: session.current, results: { score: best, measure: 'digit_span' } });
  };
  return (
    <>
      <Text style={styles.sub}>Remember the digits, then type them back. Most adults recall 5 to 9.</Text>
      {phase === 'idle' && <Btn label="Start" onPress={start} />}
      {phase === 'show' && <Text style={[styles.big, { textAlign: 'center', letterSpacing: 6 }]}>{seq}</Text>}
      {phase === 'answer' && (
        <>
          <TextInput style={styles.input} value={answer} onChangeText={setAnswer} keyboardType="number-pad" autoFocus placeholder={`${length} digits`} placeholderTextColor={colors.text.muted} onSubmitEditing={submit} />
          <Btn label="Check" onPress={submit} />
        </>
      )}
      {phase === 'done' && (
        <>
          <Text style={styles.big}>Your span: {best}</Text>
          <Text style={styles.sub}>The sequence was {seq}. Sleep and stress change this day to day.</Text>
          <Btn label="Play again" onPress={start} />
        </>
      )}
    </>
  );
}

function Focus() {
  const [presets, setPresets] = useState<Record<string, any>>({});
  useEffect(() => { getJson<any>('/digital-detox/focus-presets').then((r) => setPresets(r?.data ?? {})); }, []);
  return (
    <>
      <Text style={styles.sub}>Set these up in your phone's Focus or Digital Wellbeing settings.</Text>
      {Object.entries(presets).map(([name, p]) => (
        <View key={name} style={styles.item}>
          <Text style={styles.itemTitle}>{name.replace(/_/g, ' ')} · {p.duration}</Text>
          <Text style={styles.sub}>Pause: {asArray<string>(p.blocked_apps).join(', ').replace(/_/g, ' ')}</Text>
          <Text style={styles.sub}>Allow: {asArray<string>(p.allowed).join(', ').replace(/_/g, ' ')}</Text>
        </View>
      ))}
    </>
  );
}

function Travel() {
  const userId = useUserStore((s) => s.userId);
  const [dests, setDests] = useState<any[]>([]);
  const [plan, setPlan] = useState<any>(null);
  useEffect(() => { getJson<any>('/travel-health/destinations').then((r) => setDests(asArray(r?.data))); }, []);
  const choose = async (id: string) => {
    const r = await postJson<any>('/travel-health/plan', { user_id: userId, trip_data: { destination: id } });
    setPlan(r?.data ?? null);
  };
  return (
    <>
      <View style={styles.chips}>
        {dests.map((d) => (
          <TouchableOpacity key={d.id} style={styles.chip} onPress={() => choose(d.id)}><Text style={styles.chipText}>{d.id.replace(/_/g, ' ')}</Text></TouchableOpacity>
        ))}
      </View>
      {plan && (
        <View style={styles.result}>
          <Text style={styles.itemTitle}>{String(plan.destination).replace(/_/g, ' ')}</Text>
          {asArray<string>(plan.health_risks).length > 0 && <Text style={styles.body}>Risks: {plan.health_risks.join(', ').replace(/_/g, ' ')}</Text>}
          {asArray<string>(plan.vaccination_requirements?.required).length > 0 && <Text style={styles.body}>Required: {plan.vaccination_requirements.required.join(', ').replace(/_/g, ' ')}</Text>}
          {asArray<string>(plan.vaccination_requirements?.recommended).length > 0 && <Text style={styles.body}>Recommended: {plan.vaccination_requirements.recommended.join(', ').replace(/_/g, ' ')}</Text>}
          <Text style={styles.sub}>See a travel clinic 4 to 6 weeks before you go; they confirm what you need.</Text>
        </View>
      )}
    </>
  );
}

export default function EverydayScreen() {
  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <LinearGradient colors={[TINT, '#15803D', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Everyday Wellbeing</Text>
          <Text style={styles.heroTitle}>Small things, every day</Text>
        </LinearGradient>
        <View style={styles.list}>
          <Section icon="cloudy" title="Air today" sub="AQI and UV before you head out"><AirToday /></Section>
          <Section icon="desktop" title="Desk health" sub="Eyes, neck, wrists and back"><DeskHealth /></Section>
          <Section icon="bulb" title="Memory game" sub="Digit span, 2 minutes"><DigitSpan /></Section>
          <Section icon="phone-portrait" title="Focus modes" sub="Screen time that works for you"><Focus /></Section>
          <Section icon="airplane" title="Travel health" sub="Vaccines and risks by destination"><Travel /></Section>
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
  list: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  section: { marginBottom: 12 },
  head: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { color: colors.text.primary, fontSize: 16, fontWeight: '700' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 3, lineHeight: 17 },
  body: { color: colors.text.secondary, fontSize: 14, marginTop: 6, lineHeight: 20 },
  label: { color: colors.text.secondary, fontSize: 13, fontWeight: '600', marginTop: 10, textTransform: 'capitalize' },
  big: { color: colors.text.primary, fontSize: 24, fontWeight: '800', marginTop: 10 },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, marginTop: 8 },
  btn: { backgroundColor: TINT, borderRadius: 12, padding: 13, alignItems: 'center', marginTop: 10 },
  btnText: { color: '#fff', fontWeight: '700' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipText: { color: colors.text.secondary, fontSize: 12, textTransform: 'capitalize' },
  item: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.surface.border },
  itemTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700', textTransform: 'capitalize' },
  result: { borderWidth: 1, borderColor: colors.surface.border, borderRadius: 12, padding: 12, marginTop: 12 },
});
