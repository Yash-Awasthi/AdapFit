/**
 * Care & Safety — getting the right help: care nearby, how urgent a symptom
 * is, first aid, checking a forward, diabetes risk, government schemes, and
 * notes for the doctor. Everything here points to a next step; nothing here
 * diagnoses.
 */
import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator, Alert, Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Location from 'expo-location';
import { colors, spacing } from '../../src/theme';
import { GlassCard } from '../../src/components/PremiumComponents';
import { asArray, getJson, postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const TINT = '#EF4444';
const LEVEL_COLOR: Record<string, string> = { emergency: '#DC2626', urgent: '#F97316', doctor: '#F59E0B', self_care: '#10B981' };

function Section({ icon, title, sub, children }: { icon: string; title: string; sub: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <GlassCard style={styles.section}>
      <TouchableOpacity style={styles.sectionHead} onPress={() => setOpen(!open)} accessibilityRole="button" accessibilityState={{ expanded: open }}>
        <Ionicons name={icon as any} size={22} color={TINT} />
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.sub}>{sub}</Text>
        </View>
        <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={18} color={colors.text.muted} />
      </TouchableOpacity>
      {open && <View style={{ marginTop: 12 }}>{children}</View>}
    </GlassCard>
  );
}

const Button = ({ label, onPress, busy }: { label: string; onPress: () => void; busy?: boolean }) => (
  <TouchableOpacity style={styles.btn} onPress={onPress} disabled={busy}>
    {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>{label}</Text>}
  </TouchableOpacity>
);

const Chips = ({ options, value, onChange }: { options: string[]; value: string | null; onChange: (v: string) => void }) => (
  <View style={styles.chips}>
    {options.map((o) => (
      <TouchableOpacity key={o} style={[styles.chip, value === o && styles.chipOn]} onPress={() => onChange(o)}>
        <Text style={[styles.chipText, value === o && styles.chipTextOn]}>{o.replace(/_/g, ' ')}</Text>
      </TouchableOpacity>
    ))}
  </View>
);

function NearbyCare() {
  const [kind, setKind] = useState('hospital');
  const [busy, setBusy] = useState(false);
  const [places, setPlaces] = useState<any[] | null>(null);
  const find = async () => {
    const perm = await Location.requestForegroundPermissionsAsync();
    if (perm.status !== 'granted') return Alert.alert('Location needed', 'Allow location to find care near you. In an emergency call 108 or 112.');
    setBusy(true);
    const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    const r = await getJson<{ places: any[]; message?: string }>(`/hospitals/nearby?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&kind=${kind}`);
    setBusy(false);
    setPlaces(asArray(r?.places));
    if (r?.message) Alert.alert('Map unavailable', r.message);
  };
  return (
    <>
      <View style={styles.row}>
        <TouchableOpacity style={[styles.btn, styles.danger]} onPress={() => Linking.openURL('tel:108')}><Text style={styles.btnText}>Call 108</Text></TouchableOpacity>
        <TouchableOpacity style={[styles.btn, styles.danger]} onPress={() => Linking.openURL('tel:112')}><Text style={styles.btnText}>Call 112</Text></TouchableOpacity>
      </View>
      <Chips options={['hospital', 'clinic', 'pharmacy']} value={kind} onChange={setKind} />
      <Button label="Find near me" onPress={find} busy={busy} />
      {places?.length === 0 && <Text style={styles.sub}>Nothing mapped within 5 km.</Text>}
      {places?.slice(0, 15).map((p) => (
        <TouchableOpacity key={`${p.name}${p.lat}`} style={styles.item}
          onPress={() => Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${p.lat},${p.lon}`)}>
          <Text style={styles.itemTitle}>{p.name}</Text>
          <Text style={styles.sub}>{p.distance_km} km{p.emergency_department ? ' · emergency department' : ''}{p.address ? ` · ${p.address}` : ''}</Text>
          {p.phone ? <Text style={styles.link} onPress={() => Linking.openURL(`tel:${p.phone}`)}>{p.phone}</Text> : null}
        </TouchableOpacity>
      ))}
      {places && <Text style={styles.sub}>Map data © OpenStreetMap contributors. Call ahead; details may be out of date.</Text>}
    </>
  );
}

function SymptomCheck() {
  const [symptoms, setSymptoms] = useState<{ id: string; name: string; red_flags: string[] }[]>([]);
  const [pick, setPick] = useState<string | null>(null);
  const [severity, setSeverity] = useState(5);
  const [days, setDays] = useState('1');
  const [flags, setFlags] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  useEffect(() => { getJson<{ symptoms: any[] }>('/symptoms/symptoms').then((r) => setSymptoms(asArray(r?.symptoms))); }, []);
  const chosen = symptoms.find((s) => s.id === pick);
  const run = async () => {
    if (!pick) return;
    setResult(await postJson('/symptoms/check', { symptom: pick, severity, days: Number(days) || 0, red_flags: flags }));
  };
  return (
    <>
      <Chips options={symptoms.map((s) => s.id)} value={pick} onChange={(v) => { setPick(v); setFlags([]); setResult(null); }} />
      {chosen && (
        <>
          <Text style={styles.label}>How bad, 1 to 10: {severity}</Text>
          <View style={styles.row}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
              <TouchableOpacity key={n} style={[styles.dot, n <= severity && { backgroundColor: TINT }]} onPress={() => setSeverity(n)} accessibilityLabel={`Severity ${n}`} />
            ))}
          </View>
          <TextInput style={styles.input} value={days} onChangeText={setDays} keyboardType="decimal-pad" placeholder="For how many days?" placeholderTextColor={colors.text.muted} />
          <Text style={styles.label}>Any of these?</Text>
          {chosen.red_flags.map((f) => (
            <TouchableOpacity key={f} onPress={() => setFlags(flags.includes(f) ? flags.filter((x) => x !== f) : [...flags, f])}>
              <Text style={styles.body}>{flags.includes(f) ? '☑' : '☐'} {f}</Text>
            </TouchableOpacity>
          ))}
          <Button label="How soon should I get care?" onPress={run} />
        </>
      )}
      {result?.level && (
        <View style={[styles.result, { borderColor: LEVEL_COLOR[result.level] }]}>
          <Text style={[styles.itemTitle, { color: LEVEL_COLOR[result.level] }]}>{result.message}</Text>
          <Text style={styles.body}>{result.action}</Text>
          <Text style={styles.sub}>{result.note}</Text>
        </View>
      )}
    </>
  );
}

function FirstAid() {
  const [protocols, setProtocols] = useState<Record<string, any>>({});
  const [open, setOpen] = useState<string | null>(null);
  useEffect(() => { getJson<{ data: Record<string, any> }>('/first-aid/protocols').then((r) => setProtocols(r?.data ?? {})); }, []);
  return (
    <>
      <Text style={styles.sub}>Call 112 first for anything life-threatening, then follow the steps.</Text>
      {Object.entries(protocols).map(([key, p]) => (
        <View key={key}>
          <TouchableOpacity onPress={() => setOpen(open === key ? null : key)}>
            <Text style={styles.itemTitle}>{p.name}</Text>
          </TouchableOpacity>
          {open === key && asArray<any>(p.steps).map((st) => (
            <Text key={st.step} style={styles.body}>{st.step}. {st.action}{st.detail ? ` — ${st.detail}` : ''}</Text>
          ))}
        </View>
      ))}
    </>
  );
}

function CheckForward() {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [r, setR] = useState<any>(null);
  const run = async () => {
    if (text.trim().length < 10) return;
    setBusy(true);
    setR(await postJson('/misinformation/check', { text }));
    setBusy(false);
  };
  const color = { false: '#DC2626', misleading: '#F97316', unproven: '#F59E0B', supported: '#10B981' } as Record<string, string>;
  return (
    <>
      <TextInput style={[styles.input, { minHeight: 90 }]} multiline value={text} onChangeText={setText} maxLength={4000}
        placeholder="Paste the health message you received" placeholderTextColor={colors.text.muted} />
      <Button label="Check it" onPress={run} busy={busy} />
      {r && (
        <View style={[styles.result, { borderColor: color[r.verdict] ?? colors.text.muted }]}>
          <Text style={[styles.itemTitle, { color: color[r.verdict] ?? colors.text.primary, textTransform: 'capitalize' }]}>{r.verdict}</Text>
          <Text style={styles.body}>{r.explanation}</Text>
          <Text style={styles.body}>{r.what_to_do}</Text>
          {asArray<string>(r.sources).length > 0 && <Text style={styles.sub}>Trusted sources: {r.sources.join(', ')}</Text>}
        </View>
      )}
    </>
  );
}

function DiabetesRisk() {
  const [age, setAge] = useState('');
  const [sex, setSex] = useState<string | null>(null);
  const [waist, setWaist] = useState('');
  const [activity, setActivity] = useState<string | null>(null);
  const [parents, setParents] = useState<string | null>(null);
  const [r, setR] = useState<any>(null);
  const run = async () => {
    if (!age || !sex || !waist || !activity || parents === null) return Alert.alert('Answer all four', 'Age, waist, activity and family history are all needed.');
    setR(await postJson('/health-risk/idrs', { age: Number(age), sex, waist_cm: Number(waist), activity, parents_with_diabetes: Number(parents) }));
  };
  return (
    <>
      <TextInput style={styles.input} value={age} onChangeText={setAge} keyboardType="number-pad" placeholder="Age" placeholderTextColor={colors.text.muted} />
      <Chips options={['female', 'male']} value={sex} onChange={setSex} />
      <TextInput style={styles.input} value={waist} onChangeText={setWaist} keyboardType="decimal-pad" placeholder="Waist in cm, measured at the navel" placeholderTextColor={colors.text.muted} />
      <Text style={styles.label}>Physical activity</Text>
      <Chips options={['vigorous', 'moderate', 'mild', 'sedentary']} value={activity} onChange={setActivity} />
      <Text style={styles.label}>Parents with diabetes</Text>
      <Chips options={['0', '1', '2']} value={parents} onChange={setParents} />
      <Button label="Work out my score" onPress={run} />
      {r?.score !== undefined && (
        <View style={styles.result}>
          <Text style={styles.itemTitle}>IDRS {r.score}/100 · {r.band} risk</Text>
          <Text style={styles.body}>{r.next_step}</Text>
          <Text style={styles.sub}>{r.note}</Text>
        </View>
      )}
    </>
  );
}

function Schemes() {
  const [age, setAge] = useState('');
  const [pregnant, setPregnant] = useState(false);
  const [employee, setEmployee] = useState(false);
  const [wage, setWage] = useState('');
  const [govt, setGovt] = useState(false);
  const [list, setList] = useState<any[] | null>(null);
  const run = async () => {
    const r = await postJson<{ schemes: any[] }>('/government-schemes/eligibility', {
      age: age ? Number(age) : undefined, is_pregnant: pregnant, formal_employee: employee,
      monthly_wage: wage ? Number(wage) : undefined, central_govt: govt,
    });
    setList(asArray(r?.schemes));
  };
  const Toggle = ({ label, v, set }: { label: string; v: boolean; set: (b: boolean) => void }) => (
    <TouchableOpacity onPress={() => set(!v)}><Text style={styles.body}>{v ? '☑' : '☐'} {label}</Text></TouchableOpacity>
  );
  return (
    <>
      <TextInput style={styles.input} value={age} onChangeText={setAge} keyboardType="number-pad" placeholder="Age of the person" placeholderTextColor={colors.text.muted} />
      <Toggle label="Pregnant" v={pregnant} set={setPregnant} />
      <Toggle label="Salaried with an employer" v={employee} set={setEmployee} />
      {employee && <TextInput style={styles.input} value={wage} onChangeText={setWage} keyboardType="number-pad" placeholder="Monthly wage (₹)" placeholderTextColor={colors.text.muted} />}
      <Toggle label="Central government employee or pensioner" v={govt} set={setGovt} />
      <Button label="Show schemes that may apply" onPress={run} />
      {list?.map((s) => (
        <View key={s.id} style={styles.item}>
          <Text style={styles.itemTitle}>{s.name}</Text>
          <Text style={styles.body}>{s.description}</Text>
          <Text style={styles.sub}>{s.reason}</Text>
          <Text style={styles.link} onPress={() => Linking.openURL(s.official_portal)}>{s.official_portal}</Text>
          {s.helpline ? <Text style={styles.link} onPress={() => Linking.openURL(`tel:${s.helpline}`)}>Helpline {s.helpline}</Text> : null}
        </View>
      ))}
      {list && <Text style={styles.sub}>Eligibility shown here is a guide. Confirm on the official portal.</Text>}
    </>
  );
}

function DoctorNotes() {
  const userId = useUserStore((s) => s.userId);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [notes, setNotes] = useState<any[]>([]);
  const load = () => getJson<any>(`/notepad/notes/${userId}`).then((r) => setNotes(asArray(r?.notes ?? r)));
  useEffect(() => { load(); }, []);
  const add = async () => {
    if (!title.trim() || !content.trim()) return;
    if (await postJson('/notepad/add', { user_id: userId, title, content, category: 'doctor_visit' })) {
      setTitle(''); setContent(''); load();
    }
  };
  return (
    <>
      <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="Title (e.g. questions for Dr. visit)" placeholderTextColor={colors.text.muted} />
      <TextInput style={[styles.input, { minHeight: 70 }]} multiline value={content} onChangeText={setContent} placeholder="Symptoms, dates, questions to ask" placeholderTextColor={colors.text.muted} />
      <Button label="Save note" onPress={add} />
      {notes.slice(0, 10).map((n: any) => (
        <View key={n.id ?? n.note_id ?? n.title} style={styles.item}>
          <Text style={styles.itemTitle}>{n.title}</Text>
          <Text style={styles.body}>{n.content}</Text>
        </View>
      ))}
    </>
  );
}

export default function CareScreen() {
  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}>
        <LinearGradient colors={[TINT, '#B91C1C', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Care & Safety</Text>
          <Text style={styles.heroTitle}>The right help, quickly</Text>
          <Text style={styles.heroBody}>In an emergency, call 112 or 108 first.</Text>
        </LinearGradient>
        <View style={styles.list}>
          <Section icon="location" title="Care near me" sub="Hospitals, clinics and pharmacies"><NearbyCare /></Section>
          <Section icon="medkit" title="How urgent is this?" sub="Symptom check with warning signs"><SymptomCheck /></Section>
          <Section icon="bandage" title="First aid" sub="Step-by-step guides"><FirstAid /></Section>
          <Section icon="chatbubbles" title="Check a forward" sub="Is that health message true?"><CheckForward /></Section>
          <Section icon="water" title="Diabetes risk" sub="Indian Diabetes Risk Score, 4 questions"><DiabetesRisk /></Section>
          <Section icon="ribbon" title="Government schemes" sub="PM-JAY, ESIC, eSanjeevani and more"><Schemes /></Section>
          <Section icon="document-text" title="Notes for my doctor" sub="Keep symptoms and questions together"><DoctorNotes /></Section>
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
  heroBody: { color: 'rgba(255,255,255,0.9)', fontSize: 14, marginTop: 6 },
  list: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  section: { marginBottom: 12 },
  sectionHead: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { color: colors.text.primary, fontSize: 16, fontWeight: '700' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 3, lineHeight: 17 },
  body: { color: colors.text.secondary, fontSize: 14, marginTop: 6, lineHeight: 20 },
  label: { color: colors.text.secondary, fontSize: 13, fontWeight: '600', marginTop: 10 },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, marginTop: 8 },
  btn: { flex: 1, backgroundColor: TINT, borderRadius: 12, padding: 13, alignItems: 'center', marginTop: 10 },
  danger: { backgroundColor: '#991B1B' },
  btnText: { color: '#fff', fontWeight: '700' },
  row: { flexDirection: 'row', gap: 8, marginTop: 6 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipOn: { backgroundColor: TINT + '25', borderColor: TINT },
  chipText: { color: colors.text.muted, fontSize: 12, textTransform: 'capitalize' },
  chipTextOn: { color: TINT, fontWeight: '700' },
  dot: { flex: 1, height: 22, borderRadius: 6, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  item: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.surface.border },
  itemTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  link: { color: '#60A5FA', fontSize: 13, marginTop: 4 },
  result: { borderWidth: 1, borderColor: colors.surface.border, borderRadius: 12, padding: 12, marginTop: 12 },
});
