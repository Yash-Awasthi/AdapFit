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

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading workout...</Text>
      </View>
    );
  }

  if (!workout) {
    return (
      <View style={styles.container}>
        <TouchableOpacity onPress={() => router.back()}>
          <ArrowLeft size={24} color="#F8FAFC" />
        </TouchableOpacity>
        <Text style={styles.loadingText}>Workout not found</Text>
      </View>
    );
  }

  const totalVolume = workout.exercises.reduce((sum, ex) => {
    return sum + (ex.actual_weight || 0) * (ex.actual_reps || 0) * ex.sets;
  }, 0);

  const completedSets = workout.exercises.filter((e) => e.completed).length;
  const totalSets = workout.exercises.reduce((s, e) => s + e.sets, 0);

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <ArrowLeft size={24} color="#F8FAFC" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Workout Detail</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Workout Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.workoutTitle}>{workout.title}</Text>
        <Text style={styles.workoutDate}>{workout.target_date}</Text>

        <View style={styles.summaryStats}>
          <View style={styles.summaryStat}>
            <Clock size={16} color="#F59E0B" />
            <Text style={styles.summaryValue}>{workout.actual_duration_minutes || '--'}m</Text>
            <Text style={styles.summaryLabel}>Duration</Text>
          </View>
          <View style={styles.summaryStat}>
            <Flame size={16} color="#EF4444" />
            <Text style={styles.summaryValue}>{calcCalories()}</Text>
            <Text style={styles.summaryLabel}>Calories</Text>
          </View>
          <View style={styles.summaryStat}>
            <Dumbbell size={16} color="#818CF8" />
            <Text style={styles.summaryValue}>{(totalVolume / 1000).toFixed(1)}k</Text>
            <Text style={styles.summaryLabel}>Volume (kg)</Text>
          </View>
          <View style={styles.summaryStat}>
            <TrendingUp size={16} color="#22C55E" />
            <Text style={styles.summaryValue}>{workout.session_rpe || '--'}</Text>
            <Text style={styles.summaryLabel}>Avg RPE</Text>
          </View>
        </View>

        {/* Readiness Badge */}
        <View style={styles.readinessBadge}>
          <Text style={styles.readinessText}>{workout.readiness_state}</Text>
          {workout.recovery_score != null && (
            <Text style={styles.recoveryText}>Recovery: {workout.recovery_score}%</Text>
          )}
        </View>

        {/* Rationale */}
        {workout.adaptation_rationale && (
          <Text style={styles.rationale}>{workout.adaptation_rationale}</Text>
        )}
      </View>

      {/* Exercise List */}
      <Text style={styles.sectionTitle}>Exercises ({completedSets}/{totalSets} sets)</Text>
      {workout.exercises.map((ex, i) => {
        const comparison = getComparison(ex);
        return (
          <View key={i} style={styles.exerciseCard}>
            <View style={styles.exerciseHeader}>
              <View style={styles.exerciseNumber}>
                <Text style={styles.exerciseNumberText}>{i + 1}</Text>
              </View>
              <View style={styles.exerciseInfo}>
                <Text style={styles.exerciseName}>{ex.name || ex.exercise_id}</Text>
                <Text style={styles.exerciseMuscle}>{ex.target_muscle}</Text>
              </View>
              {ex.completed ? (
                <CheckCircle size={18} color="#22C55E" />
              ) : (
                <AlertTriangle size={18} color="#F59E0B" />
              )}
            </View>

            {/* Set Details */}
            <View style={styles.setDetails}>
              <View style={styles.setHeader}>
                <Text style={styles.setHeaderText}>Sets</Text>
                <Text style={styles.setHeaderText}>Target</Text>
                <Text style={styles.setHeaderText}>Actual</Text>
                {comparison && <Text style={styles.setHeaderText}>vs Last</Text>}
              </View>
              {Array.from({ length: ex.sets }).map((_, si) => (
                <View key={si} style={styles.setRow}>
                  <Text style={styles.setValue}>{si + 1}</Text>
                  <Text style={styles.setValue}>
                    {ex.actual_weight || '--'}kg × {ex.target_reps}
                  </Text>
                  <Text style={styles.setValue}>
                    {ex.actual_weight || '--'}kg × {ex.actual_reps || '--'}
                  </Text>
                  {comparison && (
                    <Text
                      style={[
                        styles.setValue,
                        {
                          color: comparison.weightDelta > 0
                            ? '#22C55E'
                            : comparison.weightDelta < 0
                            ? '#EF4444'
                            : '#8B96AB',
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
              <View style={styles.rpeRow}>
                <Text style={styles.rpeLabel}>RPE:</Text>
                <Text style={styles.rpeValue}>{ex.actual_rpe}</Text>
              </View>
            )}
          </View>
        );
      })}

      {/* Previous Comparison */}
      {previous && (
        <View style={styles.comparisonCard}>
          <Text style={styles.comparisonTitle}>vs Previous Workout</Text>
          <Text style={styles.comparisonSubtitle}>{previous.title} ({previous.target_date})</Text>
          <View style={styles.comparisonRow}>
            <View style={styles.comparisonItem}>
              <Text style={styles.comparisonLabel}>Exercises</Text>
              <Text style={styles.comparisonValue}>
                {workout.exercises.length} vs {previous.exercises.length}
              </Text>
            </View>
            <View style={styles.comparisonItem}>
              <Text style={styles.comparisonLabel}>Volume Change</Text>
              <Text
                style={[
                  styles.comparisonValue,
                  { color: totalVolume > 0 ? '#22C55E' : '#EF4444' },
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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', padding: 20 },
  loadingText: { color: '#8B96AB', textAlign: 'center', marginTop: 100 },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 48,
    marginBottom: 16,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: '#F8FAFC' },

  // Summary
  summaryCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  workoutTitle: { fontSize: 20, fontWeight: '700', color: '#F8FAFC' },
  workoutDate: { fontSize: 13, color: '#8B96AB', marginBottom: 12 },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  summaryStat: { alignItems: 'center' },
  summaryValue: { fontSize: 16, fontWeight: '800', color: '#F8FAFC', marginTop: 4 },
  summaryLabel: { fontSize: 10, color: '#8B96AB' },
  readinessBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 8,
    marginBottom: 8,
  },
  readinessText: { fontSize: 12, fontWeight: '700', color: '#818CF8' },
  recoveryText: { fontSize: 12, color: '#8B96AB' },
  rationale: { fontSize: 12, color: '#94A3B8', fontStyle: 'italic' },

  // Exercises
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#F8FAFC', marginBottom: 10 },
  exerciseCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  exerciseHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  exerciseNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#4F46E5',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  exerciseNumberText: { color: '#fff', fontWeight: '700', fontSize: 12 },
  exerciseInfo: { flex: 1 },
  exerciseName: { fontSize: 14, fontWeight: '600', color: '#F8FAFC' },
  exerciseMuscle: { fontSize: 11, color: '#818CF8', textTransform: 'capitalize' },

  setDetails: { marginBottom: 4 },
  setHeader: { flexDirection: 'row', marginBottom: 4, gap: 8 },
  setHeaderText: { fontSize: 10, color: '#8B96AB', fontWeight: '600', width: 60 },
  setRow: { flexDirection: 'row', marginBottom: 2, gap: 8 },
  setValue: { fontSize: 12, color: '#CBD5E1', width: 60 },

  rpeRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  rpeLabel: { fontSize: 11, color: '#8B96AB' },
  rpeValue: { fontSize: 12, fontWeight: '600', color: '#F59E0B' },

  // Comparison
  comparisonCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  comparisonTitle: { fontSize: 14, fontWeight: '600', color: '#F8FAFC', marginBottom: 4 },
  comparisonSubtitle: { fontSize: 12, color: '#8B96AB', marginBottom: 10 },
  comparisonRow: { flexDirection: 'row', gap: 12 },
  comparisonItem: { flex: 1, backgroundColor: '#0F172A', borderRadius: 8, padding: 8, alignItems: 'center' },
  comparisonLabel: { fontSize: 10, color: '#8B96AB' },
  comparisonValue: { fontSize: 14, fontWeight: '700', color: '#F8FAFC' },
});
