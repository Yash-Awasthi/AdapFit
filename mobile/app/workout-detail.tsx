/**
 * Workout History Detail Screen — detailed view of a completed workout.
 * Shows all exercises, sets/reps/weight, duration, calories, and comparison to previous sessions.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import {
  ArrowLeft, Clock, Flame, TrendingUp, TrendingDown,
  Dumbbell, CheckCircle, AlertTriangle,
} from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../src/services/config';
import { useUserStore } from '../src/stores';
import { useTheme } from '../src/services/theme';

const API = API_BASE_URL;

interface ExerciseSet {
  exercise_id: string;
  name: string;
  target_muscle: string;
  sets: number;
  target_reps: string;
  target_rpe?: number;
  actual_weight?: number;
  actual_reps?: number;
  actual_rpe?: number;
  completed: boolean;
}

interface WorkoutDetail {
  workout_id: string;
  title: string;
  created_at: string;
  target_date: string;
  readiness_state: string;
  recovery_score: number;
  adaptation_rationale: string;
  actual_duration_minutes: number;
  session_rpe: number;
  exercises: ExerciseSet[];
}

interface PreviousWorkout {
  workout_id: string;
  title: string;
  target_date: string;
  exercises: { exercise_id: string; actual_weight: number; actual_reps: number }[];
}

export default function WorkoutDetailScreen() {
  const { theme } = useTheme();
  const userId = useUserStore((s) => s.userId);
  const router = useRouter();
  const { workoutId } = useLocalSearchParams<{ workoutId: string }>();
  const [workout, setWorkout] = useState<WorkoutDetail | null>(null);
  const [previous, setPrevious] = useState<PreviousWorkout | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchWorkout(); }, [workoutId]);

  async function fetchWorkout() {
    try {
      // Fetch recent workouts and find the one by ID
      const res = await fetch(`${API}/api/v1/workouts?user_id=${userId}&days=90`);
      if (res.ok) {
        const data = await res.json();
        const workouts = data.items || [];
        const found = workouts.find((w: any) => w.workout_id === workoutId);
        if (found) {
          setWorkout(found);
          // Find previous workout for comparison
          const idx = workouts.indexOf(found);
          if (idx < workouts.length - 1) {
            setPrevious(workouts[idx + 1]);
          }
        }
      }
    } catch {}
    setLoading(false);
  }

  function getComparison(exercise: ExerciseSet) {
    if (!previous) return null;
    const prevEx = previous.exercises.find(
      (e) => e.exercise_id === exercise.exercise_id
    );
    if (!prevEx || !exercise.actual_weight || !prevEx.actual_weight) return null;

    const weightDelta = exercise.actual_weight - prevEx.actual_weight;
    const repDelta = (exercise.actual_reps || 0) - (prevEx.actual_reps || 0);

    return { weightDelta, repDelta, prevWeight: prevEx.actual_weight };
  }

  function calcCalories(): number {
    if (!workout) return 0;
    // Rough estimate: ~8 cal/min at RPE 7
    const rpe = workout.session_rpe || 7;
    const duration = workout.actual_duration_minutes || 45;
    return Math.round(duration * (5 + rpe * 0.8));
  }

  const s = makeStyles(theme);

  if (loading) {
    return (
      <View style={s.container}>
        <Text style={s.loadingText}>Loading workout...</Text>
      </View>
    );
  }

  if (!workout) {
    return (
      <View style={s.container}>
        <TouchableOpacity onPress={() => router.back()}>
          <ArrowLeft size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={s.loadingText}>Workout not found</Text>
      </View>
    );
  }

  const totalVolume = workout.exercises.reduce((sum, ex) => {
    return sum + (ex.actual_weight || 0) * (ex.actual_reps || 0) * ex.sets;
  }, 0);

  const completedSets = workout.exercises.filter((e) => e.completed).length;
  const totalSets = workout.exercises.reduce((s, e) => s + e.sets, 0);

  return (
    <ScrollView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <ArrowLeft size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>Workout Detail</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Workout Summary */}
      <View style={s.summaryCard}>
        <Text style={s.workoutTitle}>{workout.title}</Text>
        <Text style={s.workoutDate}>{workout.target_date}</Text>

        <View style={s.summaryStats}>
          <View style={s.summaryStat}>
            <Clock size={16} color={theme.warning} />
            <Text style={s.summaryValue}>{workout.actual_duration_minutes || '--'}m</Text>
            <Text style={s.summaryLabel}>Duration</Text>
          </View>
          <View style={s.summaryStat}>
            <Flame size={16} color={theme.danger} />
            <Text style={s.summaryValue}>{calcCalories()}</Text>
            <Text style={s.summaryLabel}>Calories</Text>
          </View>
          <View style={s.summaryStat}>
            <Dumbbell size={16} color={theme.primaryLight} />
            <Text style={s.summaryValue}>{(totalVolume / 1000).toFixed(1)}k</Text>
            <Text style={s.summaryLabel}>Volume (kg)</Text>
          </View>
          <View style={s.summaryStat}>
            <TrendingUp size={16} color={theme.success} />
            <Text style={s.summaryValue}>{workout.session_rpe || '--'}</Text>
            <Text style={s.summaryLabel}>Avg RPE</Text>
          </View>
        </View>

        {/* Readiness Badge */}
        <View style={s.readinessBadge}>
          <Text style={s.readinessText}>{workout.readiness_state}</Text>
          {workout.recovery_score != null && (
            <Text style={s.recoveryText}>Recovery: {workout.recovery_score}%</Text>
          )}
        </View>

        {/* Rationale */}
        {workout.adaptation_rationale && (
          <Text style={s.rationale}>{workout.adaptation_rationale}</Text>
        )}
      </View>

      {/* Exercise List */}
      <Text style={s.sectionTitle}>Exercises ({completedSets}/{totalSets} sets)</Text>
      {workout.exercises.map((ex, i) => {
        const comparison = getComparison(ex);
        return (
          <View key={i} style={s.exerciseCard}>
            <View style={s.exerciseHeader}>
              <View style={s.exerciseNumber}>
                <Text style={s.exerciseNumberText}>{i + 1}</Text>
              </View>
              <View style={s.exerciseInfo}>
                <Text style={s.exerciseName}>{ex.name || ex.exercise_id}</Text>
                <Text style={s.exerciseMuscle}>{ex.target_muscle}</Text>
              </View>
              {ex.completed ? (
                <CheckCircle size={18} color={theme.success} />
              ) : (
                <AlertTriangle size={18} color={theme.warning} />
              )}
            </View>

            {/* Set Details */}
            <View style={s.setDetails}>
              <View style={s.setHeader}>
                <Text style={s.setHeaderText}>Sets</Text>
                <Text style={s.setHeaderText}>Target</Text>
                <Text style={s.setHeaderText}>Actual</Text>
                {comparison && <Text style={s.setHeaderText}>vs Last</Text>}
              </View>
              {Array.from({ length: ex.sets }).map((_, si) => (
                <View key={si} style={s.setRow}>
                  <Text style={s.setValue}>{si + 1}</Text>
                  <Text style={s.setValue}>
                    {ex.actual_weight || '--'}kg × {ex.target_reps}
                  </Text>
                  <Text style={s.setValue}>
                    {ex.actual_weight || '--'}kg × {ex.actual_reps || '--'}
                  </Text>
                  {comparison && (
                    <Text
                      style={[
                        s.setValue,
                        {
                          color: comparison.weightDelta > 0
                            ? theme.success
                            : comparison.weightDelta < 0
                            ? theme.danger
                            : theme.textMuted,
                        },
                      ]}
                    >
                      {comparison.weightDelta > 0 ? '+' : ''}{comparison.weightDelta}kg
                    </Text>
                  )}
                </View>
              ))}
            </View>

            {/* RPE */}
            {ex.actual_rpe != null && (
              <View style={s.rpeRow}>
                <Text style={s.rpeLabel}>RPE:</Text>
                <Text style={s.rpeValue}>{ex.actual_rpe}</Text>
              </View>
            )}
          </View>
        );
      })}

      {/* Previous Comparison */}
      {previous && (
        <View style={s.comparisonCard}>
          <Text style={s.comparisonTitle}>vs Previous Workout</Text>
          <Text style={s.comparisonSubtitle}>{previous.title} ({previous.target_date})</Text>
          <View style={s.comparisonRow}>
            <View style={s.comparisonItem}>
              <Text style={s.comparisonLabel}>Exercises</Text>
              <Text style={s.comparisonValue}>
                {workout.exercises.length} vs {previous.exercises.length}
              </Text>
            </View>
            <View style={s.comparisonItem}>
              <Text style={s.comparisonLabel}>Volume Change</Text>
              <Text
                style={[
                  s.comparisonValue,
                  { color: totalVolume > 0 ? theme.success : theme.danger },
                ]}
              >
                {totalVolume > 0 ? '+' : ''}{((totalVolume / 1000)).toFixed(1)}k kg
              </Text>
            </View>
          </View>
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    loadingText: { color: theme.textMuted, textAlign: 'center', marginTop: 100 },

    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: 48,
      marginBottom: 16,
    },
    headerTitle: { fontSize: 18, fontWeight: '700', color: theme.text },

    // Summary
    summaryCard: {
      backgroundColor: theme.surface,
      borderRadius: 16,
      padding: 16,
      marginBottom: 16,
    },
    workoutTitle: { fontSize: 20, fontWeight: '700', color: theme.text },
    workoutDate: { fontSize: 13, color: theme.textMuted, marginBottom: 12 },
    summaryStats: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginBottom: 12,
    },
    summaryStat: { alignItems: 'center' },
    summaryValue: { fontSize: 16, fontWeight: '800', color: theme.text, marginTop: 4 },
    summaryLabel: { fontSize: 10, color: theme.textMuted },
    readinessBadge: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      backgroundColor: theme.background,
      borderRadius: 8,
      padding: 8,
      marginBottom: 8,
    },
    readinessText: { fontSize: 12, fontWeight: '700', color: theme.primaryLight },
    recoveryText: { fontSize: 12, color: theme.textMuted },
    rationale: { fontSize: 12, color: theme.textSecondary, fontStyle: 'italic' },

    // Exercises
    sectionTitle: { fontSize: 16, fontWeight: '600', color: theme.text, marginBottom: 10 },
    exerciseCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 12,
      marginBottom: 8,
    },
    exerciseHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
    exerciseNumber: {
      width: 28,
      height: 28,
      borderRadius: 14,
      backgroundColor: theme.primary,
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: 10,
    },
    exerciseNumberText: { color: '#fff', fontWeight: '700', fontSize: 12 },
    exerciseInfo: { flex: 1 },
    exerciseName: { fontSize: 14, fontWeight: '600', color: theme.text },
    exerciseMuscle: { fontSize: 11, color: theme.primaryLight, textTransform: 'capitalize' },

    setDetails: { marginBottom: 4 },
    setHeader: { flexDirection: 'row', marginBottom: 4, gap: 8 },
    setHeaderText: { fontSize: 10, color: theme.textMuted, fontWeight: '600', width: 60 },
    setRow: { flexDirection: 'row', marginBottom: 2, gap: 8 },
    setValue: { fontSize: 12, color: theme.textSecondary, width: 60 },

    rpeRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
    rpeLabel: { fontSize: 11, color: theme.textMuted },
    rpeValue: { fontSize: 12, fontWeight: '600', color: theme.warning },

    // Comparison
    comparisonCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 14,
      marginTop: 8,
      borderWidth: 1,
      borderColor: theme.border,
    },
    comparisonTitle: { fontSize: 14, fontWeight: '600', color: theme.text, marginBottom: 4 },
    comparisonSubtitle: { fontSize: 12, color: theme.textMuted, marginBottom: 10 },
    comparisonRow: { flexDirection: 'row', gap: 12 },
    comparisonItem: { flex: 1, backgroundColor: theme.background, borderRadius: 8, padding: 8, alignItems: 'center' },
    comparisonLabel: { fontSize: 10, color: theme.textMuted },
    comparisonValue: { fontSize: 14, fontWeight: '700', color: theme.text },
  });
}
