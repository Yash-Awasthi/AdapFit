/**
 * Workout Screen — Premium AI-Powered Workout Generator
 * Glassmorphism cards, animated elements, modern workout UI
 */
import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  ScrollView, Animated, Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, glass } from '../../src/theme';
import {
  GlassCard, GradientCard, SectionHeaderPremium, QuickAction, PillChip,
} from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

interface Exercise {
  exercise_id: string;
  name: string;
  target_muscle: string;
  sets: number;
  target_reps: string;
  target_rpe?: number;
}

interface Workout {
  workout_id: string;
  title: string;
  exercises: Exercise[];
  adaptation_rationale: string;
  created_at?: string;
}

const MUSCLE_GROUPS = [
  { label: 'All', icon: 'fitness', color: colors.primary },
  { label: 'Chest', icon: 'body', color: colors.health.heart },
  { label: 'Back', icon: 'arrow-up', color: colors.health.activity },
  { label: 'Legs', icon: 'walk', color: colors.health.calm },
  { label: 'Arms', icon: 'barbell', color: colors.health.energy },
  { label: 'Core', icon: 'radio-button-on', color: '#F59E0B' },
];

export default function WorkoutScreen() {
  const router = useRouter();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedMuscle, setSelectedMuscle] = useState('All');
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
    fetchWorkouts();
  }, []);

  const fetchWorkouts = async () => {
    try {
      const res = await fetch(`${API}/workouts?user_id=default&days=14`);
      if (res.ok) {
        const data = await res.json();
        setWorkouts(data.items || []);
      }
    } catch {}
    setLoading(false);
  };

  const generateWorkout = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/workouts/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'default',
          target_date: new Date().toISOString().split('T')[0],
          target_duration_minutes: 45,
        }),
      });
      if (res.ok) {
        const workout = await res.json();
        setWorkouts(prev => [workout, ...prev]);
      }
    } catch {}
    setGenerating(false);
  };

  const filteredWorkouts = selectedMuscle === 'All'
    ? workouts
    : workouts.filter(w => w.exercises.some(e => e.target_muscle.toLowerCase().includes(selectedMuscle.toLowerCase())));

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <LinearGradient colors={[colors.health.heart, '#F97316']} style={styles.header}>
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>💪 Workouts</Text>
            <Text style={styles.headerSubtitle}>AI-powered adaptive training</Text>
          </View>
          <View style={styles.workoutCount}>
            <Text style={styles.workoutCountNumber}>{workouts.length}</Text>
            <Text style={styles.workoutCountLabel}>workouts</Text>
          </View>
        </View>
      </LinearGradient>

      {/* Quick Actions */}
      <View style={styles.quickActionsRow}>
        <TouchableOpacity style={styles.generateBtn} onPress={generateWorkout} disabled={generating}>
          <LinearGradient colors={[colors.primary, '#8B5CF6']} style={styles.generateBtnGradient}>
            <Ionicons name={generating ? 'hourglass' : 'sparkles'} size={20} color="#FFF" />
            <Text style={styles.generateBtnText}>{generating ? 'Generating...' : 'Generate Workout'}</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>

      <View style={styles.quickActionsRow}>
        <QuickAction icon="checkmark-circle" label="Form Check" color={colors.health.calm} onPress={() => router.push('/form-checker' as any)} />
        <QuickAction icon="timer" label="Quick Workout" color={colors.health.energy} onPress={() => {}} />
        <QuickAction icon="analytics" label="Analytics" color={colors.health.mental} onPress={() => {}} />
        <QuickAction icon="calendar" label="Schedule" color="#3B82F6" onPress={() => {}} />
      </View>

      {/* Muscle Group Filter */}
      <SectionHeaderPremium icon="barbell" iconColor={colors.health.heart} title="Filter by Muscle" />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
        <View style={styles.filterRow}>
          {MUSCLE_GROUPS.map(mg => (
            <TouchableOpacity
              key={mg.label}
              style={[styles.filterPill, selectedMuscle === mg.label && { backgroundColor: mg.color + '20', borderColor: mg.color + '50' }]}
              onPress={() => setSelectedMuscle(mg.label)}
            >
              <Ionicons name={mg.icon as any} size={14} color={selectedMuscle === mg.label ? mg.color : colors.text.muted} />
              <Text style={[styles.filterPillText, selectedMuscle === mg.label && { color: mg.color }]}>{mg.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Workout List */}
      <SectionHeaderPremium
        icon="list"
        iconColor={colors.primary}
        title="Recent Workouts"
        subtitle={`${filteredWorkouts.length} workouts`}
      />

      {filteredWorkouts.length === 0 ? (
        <GlassCard variant="light" style={styles.emptyCard}>
          <Ionicons name="barbell" size={48} color={colors.text.muted} />
          <Text style={styles.emptyTitle}>No Workouts Yet</Text>
          <Text style={styles.emptyText}>Generate your first AI-powered workout based on your recovery state.</Text>
          <TouchableOpacity style={styles.generateBtnSmall} onPress={generateWorkout}>
            <Ionicons name="sparkles" size={16} color="#FFF" />
            <Text style={styles.generateBtnSmallText}>Generate First Workout</Text>
          </TouchableOpacity>
        </GlassCard>
      ) : (
        filteredWorkouts.map((workout, index) => (
          <Animated.View key={workout.workout_id || index} style={{ opacity: fadeAnim }}>
            <GlassCard variant="light" style={styles.workoutCard}>
              <View style={styles.workoutHeader}>
                <View style={styles.workoutIcon}>
                  <Ionicons name="barbell" size={18} color={colors.health.heart} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.workoutTitle}>{workout.title}</Text>
                  {workout.created_at && (
                    <View style={styles.workoutDate}>
                      <Ionicons name="calendar" size={10} color={colors.text.muted} />
                      <Text style={styles.workoutDateText}>{formatDate(workout.created_at)}</Text>
                    </View>
                  )}
                </View>
                <View style={styles.exerciseBadge}>
                  <Text style={styles.exerciseBadgeText}>{workout.exercises.length}</Text>
                  <Text style={styles.exerciseBadgeLabel}>exercises</Text>
                </View>
              </View>

              <Text style={styles.workoutRationale}>{workout.adaptation_rationale}</Text>

              {/* Exercise List */}
              <View style={styles.exerciseList}>
                {workout.exercises.slice(0, 5).map((ex, i) => (
                  <View key={ex.exercise_id || i} style={styles.exerciseItem}>
                    <View style={styles.exerciseNumber}>
                      <Text style={styles.exerciseNumberText}>{i + 1}</Text>
                    </View>
                    <View style={styles.exerciseInfo}>
                      <Text style={styles.exerciseName}>{ex.name}</Text>
                      <Text style={styles.exerciseDetail}>
                        {ex.sets} sets × {ex.target_reps} • {ex.target_muscle}
                      </Text>
                    </View>
                    {ex.target_rpe && (
                      <View style={styles.rpeBadge}>
                        <Text style={styles.rpeText}>RPE {ex.target_rpe}</Text>
                      </View>
                    )}
                  </View>
                ))}
                {workout.exercises.length > 5 && (
                  <Text style={styles.moreExercises}>+{workout.exercises.length - 5} more exercises</Text>
                )}
              </View>

              {/* Start Button */}
              <TouchableOpacity
                style={styles.startBtn}
                onPress={() => router.push('/workout-active' as any)}
              >
                <Ionicons name="play" size={18} color="#FFF" />
                <Text style={styles.startBtnText}>Start Workout</Text>
              </TouchableOpacity>
            </GlassCard>
          </Animated.View>
        ))
      )}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  workoutCount: { alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: 16, padding: 12 },
  workoutCountNumber: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  workoutCountLabel: { fontSize: 10, color: 'rgba(255,255,255,0.8)' },

  // Quick Actions
  quickActionsRow: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  generateBtn: { flex: 1 },
  generateBtnGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, paddingVertical: spacing.md, borderRadius: radius.button },
  generateBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
  generateBtnSmall: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, backgroundColor: colors.primary, paddingVertical: spacing.md, borderRadius: radius.button, marginTop: spacing.md },
  generateBtnSmallText: { fontSize: 14, fontWeight: '700', color: '#FFF' },

  // Filter
  filterScroll: { marginTop: spacing.sm },
  filterRow: { flexDirection: 'row', paddingHorizontal: spacing.screenPadding, gap: spacing.sm },
  filterPill: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
    backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border,
  },
  filterPillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },

  // Empty
  emptyCard: { alignItems: 'center', paddingVertical: spacing['3xl'], marginHorizontal: spacing.screenPadding },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, marginTop: spacing.lg, marginBottom: spacing.sm },
  emptyText: { fontSize: 14, color: colors.text.muted, textAlign: 'center', paddingHorizontal: spacing.xl },

  // Workout Card
  workoutCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  workoutHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  workoutIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.health.heartBg, justifyContent: 'center', alignItems: 'center' },
  workoutTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  workoutDate: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  workoutDateText: { fontSize: 11, color: colors.text.muted },
  exerciseBadge: { alignItems: 'center', backgroundColor: colors.primaryMuted, borderRadius: 10, padding: 8 },
  exerciseBadgeText: { fontSize: 18, fontWeight: '800', color: colors.primary },
  exerciseBadgeLabel: { fontSize: 9, color: colors.text.muted },

  workoutRationale: { fontSize: 13, color: colors.text.secondary, marginTop: spacing.md, lineHeight: 18 },

  // Exercise List
  exerciseList: { marginTop: spacing.md },
  exerciseItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  exerciseNumber: { width: 24, height: 24, borderRadius: 12, backgroundColor: colors.health.heartBg, justifyContent: 'center', alignItems: 'center' },
  exerciseNumberText: { fontSize: 11, fontWeight: '700', color: colors.health.heart },
  exerciseInfo: { flex: 1 },
  exerciseName: { fontSize: 13, fontWeight: '600', color: colors.text.primary },
  exerciseDetail: { fontSize: 11, color: colors.text.muted, marginTop: 1 },
  rpeBadge: { backgroundColor: colors.health.energyBg, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  rpeText: { fontSize: 10, fontWeight: '600', color: colors.health.energy },
  moreExercises: { fontSize: 12, color: colors.text.muted, marginTop: spacing.sm, textAlign: 'center' },

  // Start Button
  startBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm,
    backgroundColor: colors.health.heart, paddingVertical: spacing.md, borderRadius: radius.button, marginTop: spacing.md,
  },
  startBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
});
