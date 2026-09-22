/**
 * Cardiac Rehabilitation — the phase, the target zone, and the daily log.
 *
 * The target heart-rate zone is the one number on this screen that has to be
 * right, and it is derived from the patient's real age, so the screen asks
 * for what it needs before showing a program rather than assuming a
 * sixty-five-year-old.
 *
 * Medications come from the medication tracker rather than a second list, so
 * a dose ticked there is ticked here.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, Dimensions, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { MiniLineChart } from '../../src/components/HealthCharts';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray, asNumber } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface Phase {
  name: string;
  duration_weeks: string;
  exercises: string[];
  heart_rate_zone: string;
  precautions: string[];
}

interface Program {
  status: 'ok' | 'insufficient_data';
  program?: {
    condition: string;
    current_phase: number;
    age: number;
    max_heart_rate: number;
    target_hr_min: number;
    target_hr_max: number;
    resting_hr: number | null;
  };
  current_phase?: Phase;
  heart_rate_zones?: { resting: number | null; target_min: number; target_max: number; maximum: number };
  message?: string;
}

interface Progress {
  message?: string;
  total_exercise_minutes?: number;
  avg_exercise_per_day?: number;
  average_rpe?: number | null;
  days_logged?: number;
  medication_adherence?: number;
  encouragement?: string;
}

interface MedicationEntry {
  medication: string;
  dosage: string;
  time: string;
  status: string;
  med_id: string;
}

export default function CardiacRehabScreen() {
  const userId = useUserStore((s) => s.userId);
  const profile = useUserStore((s) => s.profile);
  const [age, setAge] = useState(profile?.age ? String(profile.age) : '');
  const [exerciseMinutes, setExerciseMinutes] = useState('');
  const [bp, setBp] = useState('');
  const [busy, setBusy] = useState(false);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    exercise: Program;
    progress: Progress;
    phases: { phases: Record<string, Phase> };
    medication: { schedule: MedicationEntry[] };
  }>({
    exercise: `/cardiac-rehab/program/${userId}`,
    progress: `/cardiac-rehab/progress/${userId}`,
    phases: '/cardiac-rehab/phases',
    medication: '/medication/today',
  });

  const program = data.exercise ?? null;
  const progress = data.progress ?? {};
  const zones = program?.heart_rate_zones;
  const phase = program?.current_phase;
  const medications = asArray<MedicationEntry>(data.medication?.schedule);
  const configured = program?.status === 'ok' && !!zones;

  const setupProgram = useCallback(async () => {
    const parsed = Number(age);
    if (!Number.isFinite(parsed) || parsed < 18 || parsed > 100) {
      Alert.alert('Age needed', 'Your target heart-rate zone is calculated from your age. Enter it between 18 and 100.');
      return;
    }
    setBusy(true);
    const result = await postJson<Program>('/cardiac-rehab/setup', {
      user_id: userId,
      data: { age: Math.round(parsed) },
    });
    setBusy(false);
    if (!result || result.status !== 'ok') {
      Alert.alert('Not set up', result?.message ?? 'The program could not be created.');
      return;
    }
    await reload();
  }, [age, userId, reload]);

  const logToday = useCallback(async () => {
    const minutes = Number(exerciseMinutes);
    if (!Number.isFinite(minutes) || minutes < 0) {
      Alert.alert('Log the day', 'Enter how many minutes you exercised.');
      return;
    }
    setBusy(true);
    const payload: Record<string, unknown> = { exercise_min: Math.round(minutes) };
    // Blank stays blank: an unrecorded blood pressure must not be stored as a
    // reassuring 120/80.
    if (bp.trim()) payload.bp = bp.trim();

    const result = await postJson<{ alerts?: string[] }>('/cardiac-rehab/log', {
      user_id: userId,
      data: payload,
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not recorded', 'The entry could not be saved.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    if (result.alerts?.length) {
      Alert.alert('Worth checking', result.alerts.join('\n'));
    }
    setExerciseMinutes('');
    setBp('');
    await reload();
  }, [exerciseMinutes, bp, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color={colors.health.heart} />
      </View>
    );
  }

  const daysLogged = asNumber(progress.days_logged);
  const weeklyMinutes = asNumber(progress.total_exercise_minutes);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.health.heart} />}
      >
        <LinearGradient colors={['#EF4444', '#F97316', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Cardiac Rehabilitation</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>
            {phase?.name ?? 'Not set up'}
          </Text>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 2 }]}>
            {configured
              ? `${phase?.duration_weeks} weeks · ${daysLogged} day${daysLogged === 1 ? '' : 's'} logged`
              : 'Add your age to begin'}
          </Text>
          {configured && (
            <>
              <View style={styles.scoreRow}>
                <ScoreRing score={Math.min(100, Math.round((weeklyMinutes / 150) * 100))} size={100} color="#22C55E" />
                <View style={{ flex: 1, marginLeft: 16 }}>
                  <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>This week</Text>
                  <Text style={[typography.metric.large, { color: '#fff' }]}>{weeklyMinutes} min</Text>
                  <Text style={[typography.body.sm, { color: '#22C55E' }]}>
                    of the 150 min weekly guideline
                  </Text>
                </View>
              </View>
              <ProgressBarPremium value={Math.min(150, weeklyMinutes)} max={150} color="#F97316" showLabel />
            </>
          )}
        </LinearGradient>

        {!configured && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Set Up Your Program" icon="heart" iconColor={colors.health.heart} />
            <GlassCard>
              <Text style={styles.helperText}>
                {program?.message ?? 'Your target heart-rate zone is calculated from your age, so it is needed before a program can start.'}
              </Text>
              <TextInput
                style={styles.input}
                placeholder="Your age"
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={age}
                onChangeText={setAge}
                accessibilityLabel="Your age"
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={setupProgram} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Start program'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {configured && zones && (
          <>
            <View style={styles.section}>
              <SectionHeaderPremium title="Your Heart Rate Zones" icon="heart" iconColor={colors.health.heart} />
              <GlassCard>
                {[
                  { zone: 'Resting', value: zones.resting !== null ? `${zones.resting} bpm` : 'Not recorded', color: '#22C55E' },
                  { zone: 'Target (training)', value: `${zones.target_min}–${zones.target_max} bpm`, color: '#F59E0B' },
                  { zone: 'Maximum', value: `${zones.maximum} bpm`, color: '#EF4444' },
                ].map((row) => (
                  <View key={row.zone} style={styles.zoneRow}>
                    <View style={[styles.zoneDot, { backgroundColor: row.color }]} />
                    <Text style={[typography.body.md, { flex: 1, color: colors.text.primary }]}>{row.zone}</Text>
                    <Text style={[typography.body.sm, { color: colors.text.muted }]}>{row.value}</Text>
                  </View>
                ))}
                <Text style={styles.helperText}>
                  From your age ({program?.program?.age}). {phase?.heart_rate_zone} in this phase.
                </Text>
              </GlassCard>
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Log Today" icon="add-circle" iconColor={colors.health.activity} />
              <GlassCard>
                <TextInput
                  style={styles.input}
                  placeholder="Minutes exercised"
                  placeholderTextColor={colors.text.muted}
                  keyboardType="numeric"
                  value={exerciseMinutes}
                  onChangeText={setExerciseMinutes}
                  accessibilityLabel="Minutes exercised today"
                />
                <TextInput
                  style={styles.input}
                  placeholder="Blood pressure, e.g. 128/82 (optional)"
                  placeholderTextColor={colors.text.muted}
                  value={bp}
                  onChangeText={setBp}
                  accessibilityLabel="Blood pressure reading"
                />
                <TouchableOpacity style={styles.primaryBtn} onPress={logToday} disabled={busy}>
                  <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save today'}</Text>
                </TouchableOpacity>
              </GlassCard>
            </View>

            {phase && (
              <View style={styles.section}>
                <SectionHeaderPremium title="This Phase" icon="fitness" iconColor={colors.health.activity} />
                <GlassCard>
                  {phase.exercises.map((exercise, i) => (
                    <View key={i} style={styles.listRow}>
                      <Ionicons name="ellipse" size={6} color={colors.health.activity} />
                      <Text style={[typography.body.md, { color: colors.text.primary, flex: 1 }]}>{exercise}</Text>
                    </View>
                  ))}
                </GlassCard>
                <GlassCard style={{ marginTop: spacing.md }}>
                  <Text style={[typography.label.md, { color: colors.health.heart, marginBottom: 6 }]}>Precautions</Text>
                  {phase.precautions.map((precaution, i) => (
                    <View key={i} style={styles.listRow}>
                      <Ionicons name="warning" size={12} color={colors.health.heart} />
                      <Text style={[typography.body.sm, { color: colors.text.secondary, flex: 1 }]}>{precaution}</Text>
                    </View>
                  ))}
                </GlassCard>
              </View>
            )}

            <View style={styles.section}>
              <SectionHeaderPremium title="Your Progress" icon="pulse" iconColor={colors.health.heart} />
              <GlassCard>
                {daysLogged === 0 ? (
                  <Text style={styles.helperText}>
                    {progress.message ?? 'Log a day above and your progress appears here.'}
                  </Text>
                ) : (
                  <>
                    <MiniLineChart
                      data={[weeklyMinutes]}
                      color={colors.health.heart}
                      height={60}
                      width={SCREEN_WIDTH - 80}
                    />
                    <View style={styles.statsRow}>
                      <View style={styles.stat}>
                        <Text style={styles.statValue}>{asNumber(progress.avg_exercise_per_day)}</Text>
                        <Text style={styles.statLabel}>min/day</Text>
                      </View>
                      <View style={styles.stat}>
                        <Text style={styles.statValue}>
                          {progress.average_rpe ?? '—'}
                        </Text>
                        <Text style={styles.statLabel}>avg RPE</Text>
                      </View>
                      <View style={styles.stat}>
                        <Text style={styles.statValue}>{asNumber(progress.medication_adherence)}%</Text>
                        <Text style={styles.statLabel}>meds taken</Text>
                      </View>
                    </View>
                    {progress.encouragement && (
                      <Text style={styles.helperText}>{progress.encouragement}</Text>
                    )}
                  </>
                )}
              </GlassCard>
            </View>
          </>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Medications" icon="medical" iconColor={colors.health.heart} />
          {medications.length === 0 ? (
            <GlassCard>
              <Text style={styles.helperText}>
                No medications scheduled. Add them in the medication tracker and today's doses
                appear here.
              </Text>
            </GlassCard>
          ) : (
            medications.map((med, i) => {
              const taken = med.status === 'taken';
              return (
                <View key={`${med.med_id}-${i}`} style={styles.medRow}>
                  <View style={[styles.medCheck, {
                    backgroundColor: taken ? colors.health.success : 'transparent',
                    borderColor: taken ? colors.health.success : colors.surface.border,
                  }]}>
                    {taken && <Ionicons name="checkmark" size={10} color="#fff" />}
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[typography.body.md, { color: colors.text.primary }]}>{med.medication}</Text>
                    <Text style={[typography.body.sm, { color: colors.text.muted }]}>{med.dosage} • {med.time}</Text>
                  </View>
                </View>
              );
            })
          )}
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20, marginBottom: 16 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  helperText: { fontSize: 13, color: colors.text.muted, lineHeight: 19, marginTop: spacing.sm },
  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15, marginTop: spacing.md },
  primaryBtn: { backgroundColor: colors.health.heart, borderRadius: radius.md, paddingVertical: spacing.md, alignItems: 'center', marginTop: spacing.md },
  primaryBtnText: { color: '#FFF', fontWeight: '700', fontSize: 15 },
  zoneRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  zoneDot: { width: 10, height: 10, borderRadius: 5 },
  listRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 6 },
  statsRow: { flexDirection: 'row', justifyContent: 'space-around', marginTop: spacing.md },
  stat: { alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '800', color: colors.text.primary },
  statLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },
  medRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 12 },
  medCheck: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, justifyContent: 'center', alignItems: 'center' },
});
