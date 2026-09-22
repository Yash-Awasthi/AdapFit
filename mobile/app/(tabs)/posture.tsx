/**
 * Posture Analysis — assessments the pose detector produced, and what to do
 * about them.
 *
 * Posture is measured from body landmarks. This build has no pose detector
 * wired to the camera, so the screen shows the assessment history, the
 * corrective exercises and the workspace tips — all real — and says plainly
 * that a new assessment needs landmarks, instead of scoring a body it has not
 * seen. The analyser used to pick a finding at random: one call in four
 * reported kyphosis.
 */
import React from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Dimensions, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, asNumber } from '../../src/services/http';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface ScorePoint {
  score: number;
  timestamp: number;
}

interface CorrectiveExercise {
  exercise: string;
  target: string;
}

interface ErgonomicTip {
  area: string;
  tip: string;
  priority: string;
}

interface ImprovementPlan {
  duration_weeks?: number;
  weekly_focus?: { week: number; focus: string; exercises?: string[] }[];
  daily_habits?: string[];
}

const PRIORITY_COLOR: Record<string, string> = {
  high: '#EF4444',
  medium: '#F59E0B',
  low: '#22C55E',
};

function targetColor(target: string): string {
  const palette = ['#3B82F6', '#8B5CF6', '#22C55E', '#F97316', '#EC4899'];
  let hash = 0;
  for (const ch of target) hash = (hash + ch.charCodeAt(0)) % palette.length;
  return palette[hash];
}

export default function PostureScreen() {
  const { data, loading, refreshing, refresh } = useApis<{
    history: { history: ScorePoint[] };
    exercises: { exercises: CorrectiveExercise[] };
    tips: { tips: ErgonomicTip[] };
    plan: ImprovementPlan;
  }>({
    history: '/posture/score-history?days=30',
    exercises: '/posture/exercises',
    tips: '/posture/ergonomic-tips',
    plan: '/posture/improvement-plan',
  });

  const history = asArray<ScorePoint>(data.history?.history);
  const exercises = asArray<CorrectiveExercise>(data.exercises?.exercises);
  const tips = asArray<ErgonomicTip>(data.tips?.tips);
  const plan = data.plan ?? {};

  const latest = history.length ? history[history.length - 1].score : null;
  const average = history.length
    ? Math.round(history.reduce((sum, point) => sum + point.score, 0) / history.length)
    : null;

  const explainAssessment = () =>
    Alert.alert(
      'Posture assessment',
      'An assessment measures the angle of your head, shoulders and hips from detected body landmarks. This build has no pose detector connected to the camera, so it cannot take one — and it will not guess at a score instead.'
    );

  return (
    <ScreenWrapper
      title="Posture Analysis"
      subtitle="Assessments, exercises and workspace setup"
      gradient={['#06B6D4', '#3B82F6']}
      rightAction={{ icon: 'information-circle', onPress: explainAssessment }}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <View style={styles.scoreSection}>
        <ScoreRing
          score={latest ?? 0}
          size={130}
          strokeWidth={10}
          color="#06B6D4"
          label="POSTURE"
          sublabel={latest !== null ? `${history.length} assessments` : 'No assessments'}
        />
      </View>

      {latest === null ? (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.emptyTitle}>No assessment yet</Text>
          <Text style={styles.emptyText}>
            Posture is measured from the angle of your head, shoulders and hips. That needs a
            pose detector reading body landmarks, which this build does not have — so rather
            than score a body it has not seen, it shows you nothing here.
          </Text>
          <Text style={styles.emptyText}>
            The exercises and workspace tips below stand on their own.
          </Text>
        </GlassCard>
      ) : (
        <GlassCard variant="light" style={styles.sectionCard}>
          <View style={styles.statsRow}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{latest}</Text>
              <Text style={styles.statLabel}>Latest</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{average}</Text>
              <Text style={styles.statLabel}>Average</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{history.length}</Text>
              <Text style={styles.statLabel}>Assessments</Text>
            </View>
          </View>
          <ProgressBarPremium value={latest} max={100} color="#06B6D4" height={6} />
        </GlassCard>
      )}

      <SectionHeaderPremium icon="fitness" iconColor="#8B5CF6" title="Corrective Exercises" />
      {exercises.length === 0 ? (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.emptyText}>The exercise list could not be loaded.</Text>
        </GlassCard>
      ) : (
        exercises.map((exercise, i) => {
          const tint = targetColor(exercise.target);
          return (
            <GlassCard key={i} variant="light" style={styles.exerciseCard}>
              <View style={styles.exerciseRow}>
                <View style={[styles.exerciseIcon, { backgroundColor: tint + '15' }]}>
                  <Ionicons name="body" size={18} color={tint} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.exerciseName}>{exercise.exercise}</Text>
                  <Text style={styles.exerciseTarget}>{exercise.target}</Text>
                </View>
              </View>
            </GlassCard>
          );
        })
      )}

      <SectionHeaderPremium icon="desktop" iconColor="#F59E0B" title="Workspace Setup" />
      {tips.map((tip, i) => {
        const tint = PRIORITY_COLOR[tip.priority] ?? '#94A3B8';
        return (
          <GlassCard key={i} variant="light" style={styles.exerciseCard}>
            <View style={styles.exerciseRow}>
              <View style={[styles.exerciseIcon, { backgroundColor: tint + '15' }]}>
                <Ionicons name="build" size={18} color={tint} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.exerciseName}>{tip.tip}</Text>
                <Text style={styles.exerciseTarget}>{tip.area} · {tip.priority} priority</Text>
              </View>
            </View>
          </GlassCard>
        );
      })}

      {asArray(plan.daily_habits).length > 0 && (
        <>
          <SectionHeaderPremium icon="calendar" iconColor="#22C55E" title="Daily Habits" />
          <GlassCard variant="light" style={styles.sectionCard}>
            {asArray<string>(plan.daily_habits).map((habit, i) => (
              <View key={i} style={styles.habitRow}>
                <Ionicons name="checkmark-circle-outline" size={16} color="#22C55E" />
                <Text style={styles.habitText}>{habit}</Text>
              </View>
            ))}
          </GlassCard>
        </>
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyText: { fontSize: 13, color: colors.text.muted, marginTop: 6, lineHeight: 19 },

  statsRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.md },
  stat: { alignItems: 'center' },
  statValue: { fontSize: 22, fontWeight: '800', color: colors.text.primary },
  statLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  exerciseCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  exerciseRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  exerciseIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  exerciseName: { fontSize: 14, fontWeight: '600', color: colors.text.primary, lineHeight: 19 },
  exerciseTarget: { fontSize: 12, color: colors.text.muted, marginTop: 2, textTransform: 'capitalize' },

  habitRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: 6 },
  habitText: { fontSize: 13, color: colors.text.secondary, flex: 1, lineHeight: 18 },
});
