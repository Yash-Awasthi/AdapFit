import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Check } from 'lucide-react-native';
import Animated from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../../src/services/theme';
import { useEnterAnimation } from '../../src/services/devSettings';
import { api } from '../../src/services/api';
import { useUserStore } from '../../src/stores';
import { LoadingScreen, ScreenHeader } from '../../src/components';

import { GENDER_OPTIONS } from '../../src/services/gender';
const FITNESS_LEVELS = ['beginner', 'intermediate', 'advanced'];
const GOALS = ['hypertrophy', 'strength', 'endurance', 'fat_loss', 'general_fitness'];

function Chip({ label, active, onPress, theme }: { label: string; active: boolean; onPress: () => void; theme: any }) {
  return (
    <TouchableOpacity
      onPress={() => { Haptics.selectionAsync(); onPress(); }}
      style={[
        styles.chip,
        { backgroundColor: active ? theme.primary : theme.surface, borderColor: active ? theme.primary : theme.border },
      ]}
    >
      <Text style={[styles.chipText, { color: active ? '#fff' : theme.textSecondary }]}>
        {label.replace(/_/g, ' ')}
      </Text>
    </TouchableOpacity>
  );
}

function Field({ label, children, theme }: { label: string; children: React.ReactNode; theme: any }) {
  return (
    <View style={styles.field}>
      <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>{label}</Text>
      {children}
    </View>
  );
}

export default function PersonalInfoScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const userId = useUserStore((s) => s.userId);
  const updateProfile = useUserStore((s) => s.updateProfile);

  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [workStart, setWorkStart] = useState('');
  const [workEnd, setWorkEnd] = useState('');
  const [fitnessLevel, setFitnessLevel] = useState('intermediate');
  const [primaryGoal, setPrimaryGoal] = useState('hypertrophy');
  const [daysPerWeek, setDaysPerWeek] = useState('4');
  const enter = useEnterAnimation();

  useEffect(() => {
    api.getUser(userId).then((u) => {
      setAge(u.age != null ? String(u.age) : '');
      setGender(u.gender || '');
      setHeightCm(u.height_cm != null ? String(u.height_cm) : '');
      setWorkStart(u.work_start || '');
      setWorkEnd(u.work_end || '');
      setFitnessLevel(u.fitness_level || 'intermediate');
      setPrimaryGoal(u.primary_goal || 'hypertrophy');
      setDaysPerWeek(String(u.preferred_days_per_week ?? 4));
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setSaving(true);
    try {
      await updateProfile({
        age: age ? Number(age) : undefined,
        gender: gender || undefined,
        height_cm: heightCm ? Number(heightCm) : undefined,
        work_start: workStart || undefined,
        work_end: workEnd || undefined,
        fitness_level: fitnessLevel,
        primary_goal: primaryGoal,
        preferred_days_per_week: Number(daysPerWeek) || 4,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Profile updated', 'Your details have been saved.', [
        { text: 'Done', onPress: () => router.back() },
      ]);
    } catch {
      Alert.alert('Save failed', 'Could not update your profile. Try again.');
    }
    setSaving(false);
  }

  if (loading) return <LoadingScreen />;

  const inputStyle = [styles.input, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }];

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScreenHeader
        title="Personal Info"
        right={
          <TouchableOpacity onPress={handleSave} disabled={saving} hitSlop={10}>
            <Check size={22} color={theme.primaryLight} />
          </TouchableOpacity>
        }
      />

      <ScrollView contentContainerStyle={styles.content}>
        <Animated.View entering={enter(40)}>
          <Field label="Age" theme={theme}>
            <TextInput style={inputStyle} value={age} onChangeText={setAge} keyboardType="number-pad" placeholder="28" placeholderTextColor={theme.textMuted} maxLength={3} />
          </Field>
        </Animated.View>

        <Animated.View entering={enter(90)}>
          <Field label="Gender" theme={theme}>
            <View style={styles.chipRow}>
              {GENDER_OPTIONS.map(({ value, label }) => (
                <Chip key={value} label={label} active={gender === value} onPress={() => setGender(value)} theme={theme} />
              ))}
            </View>
          </Field>
        </Animated.View>

        <Animated.View entering={enter(140)}>
          <Field label="Height (cm)" theme={theme}>
            <TextInput style={inputStyle} value={heightCm} onChangeText={setHeightCm} keyboardType="number-pad" placeholder="175" placeholderTextColor={theme.textMuted} maxLength={3} />
          </Field>
        </Animated.View>

        <Animated.View entering={enter(190)}>
          <Field label="Work hours" theme={theme}>
            <View style={styles.row}>
              <TextInput style={[inputStyle, styles.rowInput]} value={workStart} onChangeText={setWorkStart} placeholder="09:00" placeholderTextColor={theme.textMuted} maxLength={5} />
              <Text style={{ color: theme.textMuted }}>to</Text>
              <TextInput style={[inputStyle, styles.rowInput]} value={workEnd} onChangeText={setWorkEnd} placeholder="17:00" placeholderTextColor={theme.textMuted} maxLength={5} />
            </View>
            <Text style={[styles.hint, { color: theme.textMuted }]}>Used to schedule workouts around your day</Text>
          </Field>
        </Animated.View>

        <Animated.View entering={enter(240)}>
          <Field label="Fitness level" theme={theme}>
            <View style={styles.chipRow}>
              {FITNESS_LEVELS.map((f) => (
                <Chip key={f} label={f} active={fitnessLevel === f} onPress={() => setFitnessLevel(f)} theme={theme} />
              ))}
            </View>
          </Field>
        </Animated.View>

        <Animated.View entering={enter(290)}>
          <Field label="Primary goal" theme={theme}>
            <View style={styles.chipRow}>
              {GOALS.map((g) => (
                <Chip key={g} label={g} active={primaryGoal === g} onPress={() => setPrimaryGoal(g)} theme={theme} />
              ))}
            </View>
          </Field>
        </Animated.View>

        <Animated.View entering={enter(340)}>
          <Field label="Training days per week" theme={theme}>
            <View style={styles.chipRow}>
              {['2', '3', '4', '5', '6', '7'].map((d) => (
                <Chip key={d} label={d} active={daysPerWeek === d} onPress={() => setDaysPerWeek(d)} theme={theme} />
              ))}
            </View>
          </Field>
        </Animated.View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 20, paddingBottom: 100, gap: 4 },
  field: { marginBottom: 20 },
  fieldLabel: { fontSize: 13, fontWeight: '600', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  input: { borderRadius: 12, borderWidth: 1, padding: 14, fontSize: 16 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  rowInput: { flex: 1 },
  hint: { fontSize: 12, marginTop: 6 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  chipText: { fontSize: 13, fontWeight: '600', textTransform: 'capitalize' },
});
