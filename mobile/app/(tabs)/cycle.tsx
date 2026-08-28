import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Droplet, Calendar, TrendingUp, Utensils } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../src/services/theme';
import { api } from '../../src/services/api';
import { LoadingScreen } from '../../src/components';
import { useUserStore } from '../../src/stores';

const PHASE_COLOR: Record<string, string> = {
  menstrual: '#EF4444',
  follicular: '#22C55E',
  ovulation: '#F59E0B',
  luteal: '#818CF8',
};

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function Chip({ label, active, onPress, theme }: { label: string; active: boolean; onPress: () => void; theme: any }) {
  return (
    <TouchableOpacity
      onPress={() => { Haptics.selectionAsync(); onPress(); }}
      style={[styles.chip, { backgroundColor: active ? theme.primary : theme.surface, borderColor: active ? theme.primary : theme.border }]}
    >
      <Text style={[styles.chipText, { color: active ? '#fff' : theme.textSecondary }]}>{label}</Text>
    </TouchableOpacity>
  );
}

const SYMPTOMS = ['cramps', 'bloating', 'headache', 'fatigue', 'mood swings', 'tender breasts'];

export default function CycleScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [startDate, setStartDate] = useState(todayISO());
  const [cycleLength, setCycleLength] = useState('28');
  const [periodLength, setPeriodLength] = useState('5');
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [cramping, setCramping] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try {
      const data = await api.getCurrentCyclePhase(userId);
      setCurrent(data);
      setShowForm(!data.has_cycle_data);
    } catch {
      setShowForm(true);
    }
    setLoading(false);
  }

  function toggleSymptom(s: string) {
    setSymptoms((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  }

  async function handleLog() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setSaving(true);
    try {
      await api.logCycle(userId, {
        start_date: startDate,
        length_days: Number(cycleLength) || 28,
        period_length_days: Number(periodLength) || 5,
        symptoms,
        cramping,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setShowForm(false);
      await load();
    } catch {
      Alert.alert('Could not save', 'Try again in a moment.');
    }
    setSaving(false);
  }

  if (loading) return <LoadingScreen />;

  const phase = current?.current_phase;
  const phaseColor = phase ? PHASE_COLOR[phase.phase] || theme.primary : theme.primary;

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.title, { color: theme.text }]}>Cycle Tracking</Text>

      {current?.has_cycle_data && phase && (
        <>
          <View style={[styles.phaseCard, { backgroundColor: theme.surface, borderColor: phaseColor }]}>
            <View style={styles.phaseHeader}>
              <View style={[styles.phaseDot, { backgroundColor: phaseColor }]} />
              <Text style={[styles.phaseName, { color: theme.text }]}>{phase.phase} phase</Text>
              <Text style={[styles.phaseDay, { color: theme.textMuted }]}>Day {phase.day}</Text>
            </View>
            <Text style={[styles.phaseNote, { color: theme.textSecondary }]}>{phase.performance_note}</Text>
            <Text style={[styles.nextPeriod, { color: theme.textMuted }]}>
              Next period in {current.days_until_next_period} days ({current.predicted_next_period})
            </Text>
          </View>

          <View style={styles.sectionRow}>
            <TrendingUp size={16} color={theme.primaryLight} />
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>Training</Text>
          </View>
          <View style={[styles.card, { backgroundColor: theme.surface }]}>
            <Text style={[styles.cardLine, { color: theme.text }]}>Intensity: {current.training_recommendation.intensity.replace('_', ' ')}</Text>
            <Text style={[styles.cardSub, { color: theme.textMuted }]}>{current.training_recommendation.note}</Text>
            {current.training_recommendation.recommended_types?.length > 0 && (
              <Text style={[styles.cardSub, { color: theme.textSecondary, marginTop: 6 }]}>
                Try: {current.training_recommendation.recommended_types.join(', ')}
              </Text>
            )}
          </View>

          <View style={styles.sectionRow}>
            <Utensils size={16} color={theme.warning} />
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>Nutrition</Text>
          </View>
          <View style={[styles.card, { backgroundColor: theme.surface }]}>
            <Text style={[styles.cardSub, { color: theme.textSecondary }]}>
              Focus: {current.nutrition_recommendation.focus.join(', ')}
            </Text>
            {current.nutrition_recommendation.calorie_adjustment !== 0 && (
              <Text style={[styles.cardSub, { color: theme.textMuted, marginTop: 4 }]}>
                {current.nutrition_recommendation.calorie_adjustment > 0 ? '+' : ''}
                {current.nutrition_recommendation.calorie_adjustment} kcal/day
              </Text>
            )}
          </View>

          <TouchableOpacity style={styles.relogBtn} onPress={() => setShowForm((s) => !s)}>
            <Calendar size={14} color={theme.primaryLight} />
            <Text style={[styles.relogText, { color: theme.primaryLight }]}>{showForm ? 'Cancel' : 'Log new cycle start'}</Text>
          </TouchableOpacity>
        </>
      )}

      {showForm && (
        <View style={[styles.card, { backgroundColor: theme.surface, marginTop: 8 }]}>
          <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Period start date</Text>
          <TextInput
            style={[styles.input, { backgroundColor: theme.background, borderColor: theme.border, color: theme.text }]}
            value={startDate} onChangeText={setStartDate} placeholder="YYYY-MM-DD" placeholderTextColor={theme.textMuted}
          />
          <View style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Cycle length</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.background, borderColor: theme.border, color: theme.text }]}
                value={cycleLength} onChangeText={setCycleLength} keyboardType="number-pad" maxLength={2}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Period length</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.background, borderColor: theme.border, color: theme.text }]}
                value={periodLength} onChangeText={setPeriodLength} keyboardType="number-pad" maxLength={2}
              />
            </View>
          </View>

          <Text style={[styles.fieldLabel, { color: theme.textSecondary, marginTop: 8 }]}>Symptoms</Text>
          <View style={styles.chipRow}>
            {SYMPTOMS.map((s) => (
              <Chip key={s} label={s} active={symptoms.includes(s)} onPress={() => toggleSymptom(s)} theme={theme} />
            ))}
          </View>
          <View style={{ marginTop: 8 }}>
            <Chip label="Cramping" active={cramping} onPress={() => setCramping((c) => !c)} theme={theme} />
          </View>

          <TouchableOpacity
            style={[styles.saveBtn, { backgroundColor: theme.primary, opacity: saving ? 0.6 : 1 }]}
            onPress={handleLog}
            disabled={saving}
          >
            <Droplet size={16} color="#fff" />
            <Text style={styles.saveBtnText}>{saving ? 'Saving…' : 'Save'}</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 20, paddingTop: 56, paddingBottom: 100 },
  title: { fontSize: 24, fontWeight: '700', marginBottom: 16 },
  phaseCard: { borderRadius: 16, borderWidth: 1.5, padding: 16, marginBottom: 16 },
  phaseHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  phaseDot: { width: 10, height: 10, borderRadius: 5 },
  phaseName: { fontSize: 17, fontWeight: '700', textTransform: 'capitalize', flex: 1 },
  phaseDay: { fontSize: 12 },
  phaseNote: { fontSize: 13, marginTop: 8, lineHeight: 18 },
  nextPeriod: { fontSize: 12, marginTop: 10 },
  sectionRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8, marginTop: 4 },
  sectionTitle: { fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  card: { borderRadius: 12, padding: 14, marginBottom: 8 },
  cardLine: { fontSize: 14, fontWeight: '600', textTransform: 'capitalize' },
  cardSub: { fontSize: 12, lineHeight: 17 },
  relogBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'center', paddingVertical: 12, marginTop: 8 },
  relogText: { fontSize: 13, fontWeight: '600' },
  fieldLabel: { fontSize: 12, fontWeight: '600', marginBottom: 6 },
  input: { borderRadius: 10, borderWidth: 1, padding: 12, fontSize: 14, marginBottom: 10 },
  row: { flexDirection: 'row', gap: 10 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 18, borderWidth: 1 },
  chipText: { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  saveBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, justifyContent: 'center', borderRadius: 12, paddingVertical: 13, marginTop: 16 },
  saveBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },
});
