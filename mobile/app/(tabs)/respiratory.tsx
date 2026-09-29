/**
 * Respiratory Training — breathing exercises from the catalogue, sessions
 * recorded against the user.
 *
 * The exercises, their steps and their benefits come from the server rather
 * than a second copy here, so a new technique appears without a release. Lung
 * capacity is predicted from the user's own height, age and sex, and is absent
 * until the profile carries them — the endpoint used to assume a 175 cm
 * thirty-year-old man.
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Dimensions, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing } from '../../src/components/PremiumComponents';
import { Pulse } from '../../src/components/AnimationSystem';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray, asNumber } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface BreathingExercise {
  id: string;
  name: string;
  category: string;
  difficulty: string;
  duration_seconds: number;
  description: string;
  steps: string[];
  benefits: string[];
  icon: string;
}

interface LungCapacity {
  status: 'ok' | 'insufficient_data';
  predicted_liters?: number;
  normal_range?: string;
  percentile?: string;
  message?: string;
}

interface SessionRecord {
  exercise: string;
  duration: number;
  breaths: number;
  date: string;
}

// Colour by what the exercise is for, so the palette stays stable as the
// catalogue grows.
const CATEGORY_COLOR: Record<string, string> = {
  stress: '#3B82F6',
  sleep: '#8B5CF6',
  energy: '#F97316',
  focus: '#06B6D4',
  lung_health: '#22C55E',
  copd: '#06B6D4',
};

function colorFor(category: string): string {
  return CATEGORY_COLOR[category] ?? '#6366F1';
}

function minutes(seconds: number): string {
  return seconds >= 60 ? `${Math.round(seconds / 60)} min` : `${seconds}s`;
}

export default function RespiratoryScreen() {
  const profile = useUserStore((s) => s.profile);
  const userId = useUserStore((s) => s.userId);
  const [activeExercise, setActiveExercise] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  // Only asked for when the profile can answer it; the endpoint refuses
  // otherwise rather than assuming a body.
  const capacityQuery = profile?.height_cm && profile?.age && profile?.gender
    ? `/respiratory/lung-capacity?height=${profile.height_cm}&age=${profile.age}&gender=${encodeURIComponent(profile.gender)}`
    : '/respiratory/lung-capacity';

  const { data, loading, refreshing, refresh, reload } = useApis<{
    exercises: BreathingExercise[];
    capacity: LungCapacity;
    history: { history: SessionRecord[] };
  }>({
    exercises: '/respiratory/exercises',
    capacity: capacityQuery,
    history: '/respiratory/history',
  });

  const exercises = asArray<BreathingExercise>(data.exercises);
  const capacity = data.capacity;
  const history = asArray<SessionRecord>(data.history?.history);

  const thisWeek = history.filter((session) => {
    const when = new Date(session.date);
    return !Number.isNaN(when.getTime()) && Date.now() - when.getTime() < 7 * 86400_000;
  }).length;

  const startSession = async (exercise: BreathingExercise) => {
    setStarting(true);
    const started = await postJson<{ session_id?: string }>('/respiratory/session/start', {
      user_id: userId,
      exercise_id: exercise.id,
    });
    setStarting(false);
    if (!started?.session_id) {
      Alert.alert('Could not start', 'The session could not be started. Try again when you are online.');
      return;
    }
    Alert.alert(
      exercise.name,
      exercise.steps.join('\n'),
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Done',
          onPress: async () => {
            await postJson(`/respiratory/session/complete/${started.session_id}`, {});
            await reload();
          },
        },
      ]
    );
  };

  const predicted = asNumber(capacity?.predicted_liters);
  // Against the upper end of the usual 3.5-6.0 L range, so the ring reads as
  // a proportion of a normal capacity rather than an achievement score.
  const capacityPct = predicted > 0 ? Math.min(100, Math.round((predicted / 6) * 100)) : 0;

  return (
    <ScreenWrapper
      title="Respiratory Training"
      subtitle="Strengthen your lungs"
      gradient={['#06B6D4', '#3B82F6']}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <View style={styles.scoreSection}>
        <ScoreRing
          score={capacityPct}
          size={120}
          strokeWidth={8}
          color="#06B6D4"
          label="LUNG"
          sublabel={capacity?.status === 'ok' ? `${predicted} L predicted` : 'Not estimated'}
        />
        {capacity?.status !== 'ok' && (
          <Text style={styles.capacityNote}>
            {capacity?.message ?? 'Add your height, age and sex to your profile for a predicted capacity.'}
          </Text>
        )}
      </View>

      <SectionHeaderPremium icon="leaf" iconColor="#06B6D4" title="Breathing Exercises" />
      {exercises.length === 0 && (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.emptyText}>The exercise catalogue could not be loaded.</Text>
        </GlassCard>
      )}
      {exercises.map((exercise) => {
        const tint = colorFor(exercise.category);
        const open = activeExercise === exercise.id;
        return (
          <GlassCard key={exercise.id} variant="light" style={styles.exerciseCard}>
            <TouchableOpacity
              onPress={() => setActiveExercise(open ? null : exercise.id)}
              style={styles.exerciseRow}
              accessibilityRole="button"
              accessibilityState={{ expanded: open }}
              accessibilityLabel={`${exercise.name}. ${exercise.description}`}
            >
              <View style={[styles.exerciseIcon, { backgroundColor: tint + '15' }]}>
                <Text style={styles.exerciseEmoji}>{exercise.icon}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.exerciseName}>{exercise.name}</Text>
                <Text style={styles.exerciseDesc} numberOfLines={2}>{exercise.description}</Text>
              </View>
              <View style={[styles.benefitBadge, { backgroundColor: tint + '15' }]}>
                <Text style={[styles.benefitText, { color: tint }]}>{minutes(exercise.duration_seconds)}</Text>
              </View>
            </TouchableOpacity>

            {!!open && (
              <View style={styles.activeExercise}>
                <View style={styles.breathingVisual}>
                  <Pulse color={tint} size={100}>
                    <View style={[styles.breathCircle, { backgroundColor: tint + '20', borderColor: tint }]}>
                      <Text style={[styles.breathDuration, { color: tint }]}>
                        {minutes(exercise.duration_seconds)}
                      </Text>
                    </View>
                  </Pulse>
                </View>
                {exercise.steps.map((step, i) => (
                  <Text key={i} style={styles.stepText}>{i + 1}. {step}</Text>
                ))}
                {exercise.benefits.length > 0 && (
                  <Text style={styles.benefitsLine}>{exercise.benefits.join(' · ')}</Text>
                )}
                <TouchableOpacity
                  style={[styles.startBtn, { backgroundColor: tint }]}
                  onPress={() => startSession(exercise)}
                  disabled={starting}
                  accessibilityRole="button"
                  accessibilityLabel={`Start ${exercise.name}`}
                >
                  <Ionicons name="play" size={18} color="#FFF" />
                  <Text style={styles.startBtnText}>{starting ? 'Starting…' : 'Start Session'}</Text>
                </TouchableOpacity>
              </View>
            )}
          </GlassCard>
        );
      })}

      <SectionHeaderPremium icon="analytics" iconColor="#3B82F6" title="Your Sessions" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={[styles.statRow, styles.statDivider]}>
          <Text style={styles.statLabel}>Sessions this week</Text>
          <Text style={[styles.statValue, { color: '#8B5CF6' }]}>{thisWeek}</Text>
        </View>
        <View style={[styles.statRow, styles.statDivider]}>
          <Text style={styles.statLabel}>Sessions recorded</Text>
          <Text style={[styles.statValue, { color: '#22C55E' }]}>{history.length}</Text>
        </View>
        <View style={styles.statRow}>
          <Text style={styles.statLabel}>Predicted capacity</Text>
          <Text style={[styles.statValue, { color: '#06B6D4' }]}>
            {capacity?.status === 'ok' ? `${predicted} L` : '—'}
          </Text>
        </View>
        {history.length === 0 && (
          <Text style={styles.emptyText}>
            No sessions yet. Pick a technique above and your history builds up here.
          </Text>
        )}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  capacityNote: { fontSize: 12, color: colors.text.muted, textAlign: 'center', marginTop: spacing.md, lineHeight: 18 },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  emptyText: { fontSize: 13, color: colors.text.muted, lineHeight: 19, marginTop: spacing.sm },

  exerciseCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm, overflow: 'hidden' },
  exerciseRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  exerciseIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  exerciseEmoji: { fontSize: 20 },
  exerciseName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  exerciseDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 16 },
  benefitBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  benefitText: { fontSize: 10, fontWeight: '600' },

  activeExercise: { marginTop: spacing.lg, alignItems: 'center' },
  breathingVisual: { marginBottom: spacing.lg },
  breathCircle: { width: 100, height: 100, borderRadius: 50, justifyContent: 'center', alignItems: 'center', borderWidth: 3 },
  breathDuration: { fontSize: 15, fontWeight: '700' },
  stepText: { fontSize: 13, color: colors.text.secondary, alignSelf: 'stretch', marginBottom: 4, lineHeight: 18 },
  benefitsLine: { fontSize: 12, color: colors.text.muted, alignSelf: 'stretch', marginTop: spacing.xs, marginBottom: spacing.md },
  startBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, paddingVertical: spacing.md, borderRadius: radius.button, width: '100%' },
  startBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },

  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.md },
  statDivider: { borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  statLabel: { fontSize: 14, color: colors.text.muted },
  statValue: { fontSize: 16, fontWeight: '700' },
});
