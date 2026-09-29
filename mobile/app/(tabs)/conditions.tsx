/**
 * Conditions & Recovery — check-ups due, lab results over time, physio
 * programmes, fall prevention, eye care and allergies. Each result says what
 * to do next; none names a condition.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing } from '../../src/theme';
import { GlassCard } from '../../src/components/PremiumComponents';
import { asArray, getJson, postJson, putJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';
import { localDay } from '../../src/utils/date';

const TINT = '#0EA5E9';
const today = () => localDay();

function Section({ icon, title, sub, children }: { icon: string; title: string; sub: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <GlassCard style={styles.section}>
      <TouchableOpacity style={styles.head} onPress={() => setOpen(!open)} accessibilityRole="button" accessibilityState={{ expanded: open }}>
        <Ionicons name={icon as any} size={22} color={TINT} />
        <View style={{ flex: 1 }}><Text style={styles.title}>{title}</Text><Text style={styles.sub}>{sub}</Text></View>
        <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={18} color={colors.text.muted} />
      </TouchableOpacity>
      {!!open && <View style={{ marginTop: 12 }}>{children}</View>}
    </GlassCard>
  );
}
const Btn = ({ label, onPress }: { label: string; onPress: () => void }) => (
  <TouchableOpacity style={styles.btn} onPress={onPress}><Text style={styles.btnText}>{label}</Text></TouchableOpacity>
);
const Chips = ({ options, value, onChange }: { options: { id: string; label: string }[]; value: string | null; onChange: (v: string) => void }) => (
  <View style={styles.chips}>
    {options.map((o) => (
      <TouchableOpacity key={o.id} style={[styles.chip, value === o.id && styles.chipOn]} onPress={() => onChange(o.id)}>
        <Text style={[styles.chipText, value === o.id && styles.chipTextOn]}>{o.label}</Text>
      </TouchableOpacity>
    ))}
  </View>
);
const Input = (p: any) => <TextInput style={styles.input} placeholderTextColor={colors.text.muted} {...p} />;

function Checkups() {
  const [data, setData] = useState<any>(null);
  const [age, setAge] = useState('');
  const [sex, setSex] = useState<string | null>(null);
  const load = () => getJson('/screening/schedule').then(setData);
  useEffect(() => { load(); }, []);
  const save = async () => { if (age && sex && await postJson('/screening/profile', { age: Number(age), sex })) load(); };
  const done = async (id: string) => { if (await postJson('/screening/log', { check_id: id, done_on: today() })) load(); };
  if (data?.status !== 'ok') {
    return (
      <>
        <Text style={styles.sub}>{data?.message ?? 'Add your age and sex.'}</Text>
        <Input value={age} onChangeText={setAge} keyboardType="number-pad" placeholder="Age" />
        <Chips options={[{ id: 'female', label: 'Female' }, { id: 'male', label: 'Male' }]} value={sex} onChange={setSex} />
        <Btn label="Show my check-ups" onPress={save} />
      </>
    );
  }
  return (
    <>
      {asArray<any>(data.checks).map((c) => (
        <View key={c.id} style={styles.item}>
          <Text style={[styles.itemTitle, { color: c.due ? '#F59E0B' : colors.text.primary }]}>{c.name}{c.due ? ' · due' : ''}</Text>
          <Text style={styles.sub}>Every {c.every_years} year{c.every_years > 1 ? 's' : ''} · {c.where}</Text>
          <Text style={styles.sub}>{c.last_done ? `Last done ${c.last_done}` : 'No record yet'}</Text>
          {!!c.due && <Text style={styles.link} onPress={() => done(c.id)}>I had this done today</Text>}
        </View>
      ))}
      <Text style={styles.sub}>{data.note}</Text>
    </>
  );
}

function Labs() {
  const [tests, setTests] = useState<{ id: string; label: string; unit: string }[]>([]);
  const [summary, setSummary] = useState<any[]>([]);
  const [test, setTest] = useState<string | null>(null);
  const [value, setValue] = useState('');
  const [low, setLow] = useState('');
  const [high, setHigh] = useState('');
  const [date, setDate] = useState(today());
  const load = () => getJson<any>('/biomarkers/summary').then((r) => setSummary(asArray(r?.tests)));
  useEffect(() => { getJson<any[]>('/biomarkers/tests').then((r) => setTests(asArray(r))); load(); }, []);
  const add = async () => {
    if (!test || !value) return;
    const r = await postJson('/biomarkers/readings', {
      test, value: Number(value), taken_on: date,
      ref_low: low ? Number(low) : undefined, ref_high: high ? Number(high) : undefined,
    });
    if (!r) return Alert.alert('Not saved', 'Check the value and date (YYYY-MM-DD).');
    setValue(''); setLow(''); setHigh(''); load();
  };
  const color = (s: string) => (s === 'in_range' ? '#10B981' : s === 'no_range' ? colors.text.muted : '#F59E0B');
  return (
    <>
      <Chips options={tests.map((t) => ({ id: t.id, label: t.label }))} value={test} onChange={setTest} />
      {!!test && (
        <>
          <Input value={value} onChangeText={setValue} keyboardType="decimal-pad" placeholder={`Result (${tests.find((t) => t.id === test)?.unit})`} />
          <View style={styles.row}>
            <View style={{ flex: 1 }}><Input value={low} onChangeText={setLow} keyboardType="decimal-pad" placeholder="Range low (from report)" /></View>
            <View style={{ flex: 1 }}><Input value={high} onChangeText={setHigh} keyboardType="decimal-pad" placeholder="Range high" /></View>
          </View>
          <Input value={date} onChangeText={setDate} placeholder="Date YYYY-MM-DD" />
          <Btn label="Save result" onPress={add} />
        </>
      )}
      {summary.map((t) => (
        <View key={t.test} style={styles.item}>
          <Text style={styles.itemTitle}>{t.label}: {t.latest.value} {t.unit}</Text>
          <Text style={[styles.sub, { color: color(t.latest.status) }]}>
            {t.latest.status.replace('_', ' ')}{t.latest.range_source ? ` (${t.latest.range_source})` : ''}
            {t.change !== null ? ` · ${t.change > 0 ? '+' : ''}${t.change} since last` : ''}
          </Text>
          <Text style={styles.sub}>{t.history.map((h: any) => `${h.taken_on.slice(2)}: ${h.value}`).join('  ·  ')}</Text>
          {!!t.next_step && <Text style={styles.body}>{t.next_step}</Text>}
        </View>
      ))}
    </>
  );
}

function Physio() {
  const [programs, setPrograms] = useState<any[]>([]);
  const [active, setActive] = useState<any>(null);
  const [pain, setPain] = useState(3);
  useEffect(() => { getJson<any>('/rehab/programs').then((r) => setPrograms(asArray(r?.programs))); }, []);
  const start = async (id: string) => { const r = await postJson<any>('/rehab/program/start', { injury_type: id }); if (r?.program) setActive({ ...r.program, detail: programs.find((p) => p.id === id) }); };
  const log = async () => { if (active && await postJson('/rehab/progress', { program_id: active.program_id, pain_level: pain })) Alert.alert('Logged', `Pain ${pain}/10 recorded.`); };
  if (!active) {
    return (
      <>
        <Text style={styles.sub}>Use these alongside your physiotherapist's advice, not instead of it.</Text>
        {programs.map((p) => (
          <TouchableOpacity key={p.id} style={styles.item} onPress={() => start(p.id)}>
            <Text style={styles.itemTitle}>{p.name}</Text>
            <Text style={styles.sub}>{p.duration_weeks} weeks · {asArray<string>(p.phases).length} phases</Text>
          </TouchableOpacity>
        ))}
      </>
    );
  }
  return (
    <>
      <Text style={styles.itemTitle}>{active.name}</Text>
      {asArray<string>(active.detail?.phases).map((ph) => <Text key={ph} style={styles.body}>• {ph}</Text>)}
      <Text style={styles.label}>Exercises</Text>
      <Text style={styles.body}>{asArray<string>(active.detail?.exercises).join(', ')}</Text>
      <Text style={styles.label}>Pain today: {pain}/10</Text>
      <View style={styles.row}>
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
          <TouchableOpacity key={n} accessibilityRole="radio" accessibilityLabel={`Pain ${n} of 10`} accessibilityState={{ selected: n === pain }} style={[styles.dot, n <= pain && { backgroundColor: TINT }]} onPress={() => setPain(n)} />
        ))}
      </View>
      <Btn label="Log today's pain" onPress={log} />
      <Text style={styles.sub}>Stop any exercise that causes sharp pain, and tell your physiotherapist.</Text>
    </>
  );
}

function Falls() {
  const [qs, setQs] = useState<any[]>([]);
  const [ans, setAns] = useState<Record<string, boolean>>({});
  const [res, setRes] = useState<any>(null);
  const [safety, setSafety] = useState<any[]>([]);
  useEffect(() => { getJson<any[]>('/senior-health/fall-check').then((r) => setQs(asArray(r))); getJson<any[]>('/senior-health/home-safety').then((r) => setSafety(asArray(r))); }, []);
  return (
    <>
      <Text style={styles.sub}>For anyone 60+ or a parent you care for. Tick what is true.</Text>
      {qs.map((q) => (
        <TouchableOpacity key={q.id} onPress={() => setAns({ ...ans, [q.id]: !ans[q.id] })}>
          <Text style={styles.body}>{ans[q.id] ? '☑' : '☐'} {q.question}</Text>
        </TouchableOpacity>
      ))}
      <Btn label="Check fall risk" onPress={async () => setRes(await postJson('/senior-health/fall-check', ans))} />
      {!!res && <View style={styles.result}><Text style={styles.itemTitle}>Score {res.score}{res.at_risk ? ' · worth a review' : ''}</Text><Text style={styles.body}>{res.next_step}</Text></View>}
      <Text style={styles.label}>Home safety</Text>
      {safety.map((a) => <Text key={a.area} style={styles.body}>{a.area}: {asArray<string>(a.checks).join('; ')}</Text>)}
    </>
  );
}

function Eyes() {
  const [ex, setEx] = useState<any[]>([]);
  useEffect(() => { getJson<any[]>('/vision/exercises/all').then((r) => setEx(asArray(r))); }, []);
  return (
    <>
      {ex.map((e) => (
        <View key={e.id} style={styles.item}>
          <Text style={styles.itemTitle}>{e.name}</Text>
          <Text style={styles.body}>{e.description}</Text>
        </View>
      ))}
      <Text style={styles.sub}>Sudden vision loss, flashes or a curtain over your sight need emergency care.</Text>
    </>
  );
}

function Allergies() {
  const userId = useUserStore((s) => s.userId);
  const [severity, setSeverity] = useState(3);
  const [flags, setFlags] = useState({ sneezing: false, itchy_eyes: false, wheezing: false, breathlessness: false, hives: false });
  const [triggers, setTriggers] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const save = async () => {
    const r = await postJson<any>('/allergies/symptoms', {
      user_id: userId, date: today(), data: {
        severity, triggers: triggers.split(',').map((t) => t.trim()).filter(Boolean),
        nose: { sneezing: flags.sneezing }, eyes: { itchy: flags.itchy_eyes },
        respiratory: { wheezing: flags.wheezing, breathlessness: flags.breathlessness }, skin: { hives: flags.hives },
      },
    });
    setMsg(r ? (r.next_step ?? 'Saved.') : 'Not saved.');
  };
  return (
    <>
      <Text style={styles.label}>How bad today: {severity}/10</Text>
      <View style={styles.row}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => <TouchableOpacity key={n} accessibilityRole="radio" accessibilityLabel={`Severity ${n} of 10`} accessibilityState={{ selected: n === severity }} style={[styles.dot, n <= severity && { backgroundColor: TINT }]} onPress={() => setSeverity(n)} />)}
      </View>
      {(Object.keys(flags) as (keyof typeof flags)[]).map((k) => (
        <TouchableOpacity key={k} onPress={() => setFlags({ ...flags, [k]: !flags[k] })}>
          <Text style={styles.body}>{flags[k] ? '☑' : '☐'} {k.replace('_', ' ')}</Text>
        </TouchableOpacity>
      ))}
      <Input value={triggers} onChangeText={setTriggers} placeholder="Possible triggers (dust, pollen, food...)" />
      <Btn label="Log symptoms" onPress={save} />
      {!!msg && <Text style={styles.body}>{msg}</Text>}
    </>
  );
}

function Pacing() {
  const [d, setD] = useState<any>(null);
  const [rhr, setRhr] = useState('');
  const [energy, setEnergy] = useState<string | null>(null);
  const [minutes, setMinutes] = useState('');
  const [peak, setPeak] = useState('');
  const load = () => getJson('/fatigue-pacing/summary').then(setD);
  useEffect(() => { load(); }, []);
  const plan = d?.plan;
  const saveRhr = async () => { if (Number(rhr) >= 30 && await putJson('/fatigue-pacing/resting-hr', { bpm: Number(rhr) })) load(); };
  const logDay = async () => {
    if (energy === null || minutes === '') return Alert.alert('Log today', 'Pick an energy level and enter active minutes.');
    const r = await postJson<{ advice: string[] }>('/fatigue-pacing/day', {
      date: today(), energy: Number(energy), activity_minutes: Number(minutes), peak_hr: peak ? Number(peak) : null,
    });
    if (r?.advice?.length) Alert.alert('Pacing', r.advice.join('\n\n'));
    setMinutes(''); setPeak(''); load();
  };
  const crash = async (severity: string) => {
    const r = await postJson<{ guidance: string[] }>('/fatigue-pacing/crash', { date: today(), severity });
    if (r) Alert.alert('Crash logged', r.guidance.join('\n\n'));
    load();
  };
  return (
    <>
      <Text style={styles.sub}>For people whose doctor has assessed their fatigue. Keeps activity under a heart-rate ceiling and shows crashes after busy days.</Text>
      {plan?.heart_rate_ceiling
        ? <Text style={styles.body}>Your ceiling: {plan.heart_rate_ceiling} bpm (resting {plan.resting_hr} + 15)</Text>
        : <>
            <Text style={styles.body}>{plan?.ceiling_note ?? 'Enter your resting heart rate.'}</Text>
            <Input value={rhr} onChangeText={setRhr} keyboardType="number-pad" placeholder="Resting heart rate (bpm)" />
            <Btn label="Set ceiling" onPress={saveRhr} />
          </>}
      <Text style={styles.label}>Energy today (0-10)</Text>
      <Chips options={['0', '2', '4', '6', '8', '10'].map((v) => ({ id: v, label: v }))} value={energy} onChange={setEnergy} />
      <Input value={minutes} onChangeText={setMinutes} keyboardType="number-pad" placeholder="Active minutes today" />
      <Input value={peak} onChangeText={setPeak} keyboardType="number-pad" placeholder="Highest heart rate (optional)" />
      <Btn label="Log today" onPress={logDay} />
      <Text style={styles.label}>Having a crash?</Text>
      <Chips options={[{ id: 'mild', label: 'Mild' }, { id: 'moderate', label: 'Moderate' }, { id: 'severe', label: 'Severe' }]} value={null} onChange={crash} />
      {d?.status === 'ok' && (
        <Text style={styles.body}>
          Last {d.days_logged} days: energy {d.average_energy}/10, {d.average_activity_minutes} active min a day,
          {' '}{d.crashes.length} crash(es){d.days_with_heart_rate ? `, ${d.days_over_ceiling} day(s) over ceiling` : ''}.
          {d.boom_bust_days.length ? ` A crash followed a busy day on ${d.boom_bust_days.join(', ')}.` : ''}
        </Text>
      )}
      {asArray<string>(plan?.rules).map((r) => <Text key={r} style={styles.sub}>• {r}</Text>)}
      {!!plan?.see_a_doctor && <Text style={styles.sub}>{plan.see_a_doctor}</Text>}
    </>
  );
}

export default function ConditionsScreen() {
  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <LinearGradient colors={[TINT, '#0369A1', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Conditions & Recovery</Text>
          <Text style={styles.heroTitle}>Stay ahead of your health</Text>
        </LinearGradient>
        <View style={styles.list}>
          <Section icon="calendar-number" title="Check-ups due" sub="By age and sex, free NCD screening from 30"><Checkups /></Section>
          <Section icon="flask" title="Lab results" sub="Track reports over time"><Labs /></Section>
          <Section icon="walk" title="Physio programmes" sub="Knee, shoulder, back and more"><Physio /></Section>
          <Section icon="accessibility" title="Falls" sub="CDC STEADI check and home safety"><Falls /></Section>
          <Section icon="eye" title="Eye care" sub="Screen strain relief"><Eyes /></Section>
          <Section icon="battery-half" title="Energy pacing" sub="ME/CFS and long-lasting fatigue"><Pacing /></Section>
          <Section icon="flower" title="Allergies" sub="Log symptoms and triggers"><Allergies /></Section>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { paddingLeft: 40, color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroTitle: { paddingLeft: 40, color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  list: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  section: { marginBottom: 12 },
  head: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { color: colors.text.primary, fontSize: 16, fontWeight: '700' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 3, lineHeight: 17 },
  body: { color: colors.text.secondary, fontSize: 14, marginTop: 6, lineHeight: 20 },
  label: { color: colors.text.secondary, fontSize: 13, fontWeight: '600', marginTop: 10 },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, marginTop: 8 },
  btn: { backgroundColor: TINT, borderRadius: 12, padding: 13, alignItems: 'center', marginTop: 10 },
  btnText: { color: '#fff', fontWeight: '700' },
  row: { flexDirection: 'row', gap: 6, marginTop: 6 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipOn: { backgroundColor: TINT + '25', borderColor: TINT },
  chipText: { color: colors.text.muted, fontSize: 12 },
  chipTextOn: { color: TINT, fontWeight: '700' },
  dot: { flex: 1, height: 22, borderRadius: 6, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  item: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.surface.border },
  itemTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  link: { color: '#60A5FA', fontSize: 13, marginTop: 6 },
  result: { borderWidth: 1, borderColor: colors.surface.border, borderRadius: 12, padding: 12, marginTop: 12 },
});
