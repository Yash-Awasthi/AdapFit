import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Dumbbell, Calendar, Sparkles, ChevronDown, ChevronUp, Flame, Snowflake, Timer, Target } from 'lucide-react-native';
import { WorkoutCard, Button, SectionHeader, LoadingScreen, EmptyState } from '../../src/components';
import { WorkoutCalendar } from '../../src/components/WorkoutCalendar';
import { api } from '../../src/services/api';
import * as Haptics from 'expo-haptics';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';

interface Exercise {
  exercise_id: string;
  name: string;
  target_muscle: string;
  sets: number;
  target_reps: string;
  target_rpe?: number;
  gif_url?: string;
}

interface Workout {
  workout_id: string;
  title: string;
  exercises: Exercise[];
  adaptation_rationale: string;
  created_at?: string;
}

export default function WorkoutScreen() {
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const userId = useUserStore((s) => s.userId);
  const router = useRouter();
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [warmupData, setWarmupData] = useState<any | null>(null);
  const [cooldownData, setCooldownData] = useState<any | null>(null);
  const [showRoutines, setShowRoutines] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchWorkouts();
    fetchRoutines();
  }, []);

  async function fetchWorkouts() {
    try {
      const res = await api.getWorkouts(userId, 14);
      setWorkouts(res.items || []);
    } catch {}
    setLoading(false);
  }

  async function fetchRoutines() {
    try {
      const [w, c] = await Promise.all([
        api.getWarmupRoutine(['chest', 'back', 'quadriceps']).catch(() => null),
        api.getCooldownRoutine(['chest', 'back', 'quadriceps']).catch(() => null),
      ]);
      if (w) setWarmupData(w);
      if (c) setCooldownData(c);
    } catch {}
  }

  async function generateWorkout() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setGenerating(true);
    try {
      const workout = await api.generateWorkout({
        user_id: userId,
        target_date: new Date().toISOString().split('T')[0],
        target_duration_minutes: 45,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setWorkouts((prev) => [workout, ...prev]);
    } catch {}
    setGenerating(false);
  }

  function formatDate(dateStr?: string) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  }

  if (loading) return <LoadingScreen />;

  return (
    <View style={s.container}>
      <View style={s.header}>
        <Text style={s.title} accessibilityRole="header">Workouts</Text>
        <Text style={s.count}>{workouts.length} workouts</Text>
      </View>

      <WorkoutCalendar
        workoutDays={workouts.map((w: any) => w.target_date || w.created_at || '')}
      />

      <Button
        title={generating ? 'Generating...' : 'Generate Adaptive Workout'}
        onPress={generateWorkout}
        loading={generating}
        accessibilityLabel="Generate a new AI-powered workout"
        accessibilityHint="Creates a personalized workout based on your recovery state"
      />

      <TouchableOpacity
        style={s.formCheckerBtn}
        onPress={() => {
          Haptics.selectionAsync();
          router.push('/form-checker');
        }}
      >
        <Target size={16} color={theme.success} />
        <Text style={s.formCheckerBtnText}>Form Checker</Text>
      </TouchableOpacity>

      {/* Warmup & Cooldown Accordion */}
      <TouchableOpacity
        style={s.routineAccordion}
        onPress={() => {
          Haptics.selectionAsync();
          setShowRoutines(!showRoutines);
        }}
      >
        <View style={s.routineAccordionHeader}>
          <Flame size={16} color={theme.warning} />
          <Text style={s.routineAccordionTitle}>Warmup & Cooldown Routines</Text>
          {showRoutines ? (
            <ChevronUp size={16} color={theme.textSecondary} />
          ) : (
            <ChevronDown size={16} color={theme.textSecondary} />
          )}
        </View>

        {showRoutines && (
          <View style={s.routineContent}>
            {warmupData?.warmup_routine && (
              <View style={s.routineSection}>
                <Text style={s.sectionHeading}>Dynamic Warmup:</Text>
                {warmupData.warmup_routine.map((item: any, idx: number) => (
                  <View key={idx} style={s.routineItemRow}>
                    <View style={s.routineNumber}>
                      <Text style={s.routineNumberText}>{idx + 1}</Text>
                    </View>
                    <View style={s.routineItemContent}>
                      <Text style={s.routineItemName}>{item.name}</Text>
                      <Text style={s.routineItemDetail}>
                        {item.duration ? `${item.duration}s` : `${item.reps ?? 10} reps`}
                      </Text>
                    </View>
                    <TouchableOpacity
                      style={s.timerChip}
                      onPress={() => {
                        Haptics.selectionAsync();
                        // Timer would count down from duration
                      }}
                    >
                      <Timer size={12} color={theme.warning} />
                      <Text style={s.timerChipText}>Start</Text>
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            )}

            {cooldownData?.cooldown_routine && (
              <View style={s.routineSection}>
                <Text style={[s.sectionHeading, { color: '#38BDF8', marginTop: 8 }]}>
                  Static Cooldown:
                </Text>
                {cooldownData.cooldown_routine.map((item: any, idx: number) => (
                  <View key={idx} style={s.routineItemRow}>
                    <View style={[s.routineNumber, { backgroundColor: '#1E3A5F' }]}>
                      <Text style={[s.routineNumberText, { color: '#38BDF8' }]}>{idx + 1}</Text>
                    </View>
                    <View style={s.routineItemContent}>
                      <Text style={s.routineItemName}>{item.name}</Text>
                      <Text style={s.routineItemDetail}>
                        {item.duration ? `${item.duration}s hold` : '30s hold'}
                      </Text>
                    </View>
                    <TouchableOpacity
                      style={[s.timerChip, { backgroundColor: '#1E3A5F' }]}
                      onPress={() => Haptics.selectionAsync()}
                    >
                      <Timer size={12} color="#38BDF8" />
                      <Text style={[s.timerChipText, { color: '#38BDF8' }]}>Start</Text>
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            )}
          </View>
        )}
      </TouchableOpacity>

      {workouts.length === 0 ? (
        <EmptyState
          title="No Workouts"
          message="Generate your first AI-powered workout based on your recovery state."
        />
      ) : (
        <FlatList
          data={workouts}
          keyExtractor={(item) => item.workout_id}
          renderItem={({ item }) => (
            <View style={s.workoutCard}>
              <View style={s.workoutHeader}>
                <Dumbbell size={16} color={theme.primaryLight} />
                <Text style={s.workoutTitle}>{item.title}</Text>
              </View>
              {item.created_at && (
                <View style={s.dateRow}>
                  <Calendar size={12} color={theme.textMuted} />
                  <Text style={s.dateText}>{formatDate(item.created_at)}</Text>
                </View>
              )}
              <Text style={s.rationale}>{item.adaptation_rationale}</Text>
              <View style={s.exerciseCount}>
                <Sparkles size={12} color={theme.primaryLight} />
                <Text style={s.exerciseCountText}>
                  {item.exercises.length} exercises
                </Text>
              </View>
              {item.exercises.map((ex) => (
                <WorkoutCard key={ex.exercise_id} exercise={ex} />
              ))}
            </View>
          )}
          contentContainerStyle={s.list}
        />
      )}
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 48, marginBottom: 16 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text },
    count: { fontSize: 14, color: theme.textMuted },
    routineAccordion: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 14,
      marginTop: 12,
      borderWidth: 1,
      borderColor: theme.border,
    },
    routineAccordionHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    routineAccordionTitle: { fontSize: 14, fontWeight: '600', color: theme.text, flex: 1, marginLeft: 8 },
    routineContent: { marginTop: 12, paddingTop: 8, borderTopWidth: 1, borderTopColor: theme.border },
    routineSection: { marginBottom: 4 },
    sectionHeading: { fontSize: 12, fontWeight: '700', color: theme.warning, marginBottom: 4 },
    routineItem: { fontSize: 12, color: '#CBD5E1', marginBottom: 2 },
    routineItemRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      paddingVertical: 6,
      borderBottomWidth: 1,
      borderBottomColor: theme.surface,
    },
    routineNumber: {
      width: 24,
      height: 24,
      borderRadius: 12,
      backgroundColor: '#422006',
      alignItems: 'center',
      justifyContent: 'center',
    },
    routineNumberText: { fontSize: 11, fontWeight: '700', color: theme.warning },
    routineItemContent: { flex: 1 },
    routineItemName: { fontSize: 13, color: theme.text, fontWeight: '600' },
    routineItemDetail: { fontSize: 11, color: theme.textMuted },
    timerChip: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 4,
      backgroundColor: '#422006',
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 6,
    },
    timerChipText: { fontSize: 10, fontWeight: '600', color: theme.warning },
    formCheckerBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 8,
      backgroundColor: '#052E16',
      borderRadius: 12,
      padding: 12,
      marginTop: 8,
      borderWidth: 1,
      borderColor: '#166534',
    },
    formCheckerBtnText: { color: theme.success, fontSize: 14, fontWeight: '600' },
    list: { paddingBottom: 40 },
    workoutCard: {
      backgroundColor: theme.surface, borderRadius: 16, padding: 16, marginTop: 16,
    },
    workoutHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
    workoutTitle: { fontSize: 16, fontWeight: '600', color: theme.text, flex: 1 },
    dateRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 8 },
    dateText: { fontSize: 12, color: theme.textMuted },
    rationale: { fontSize: 13, color: theme.textSecondary, marginBottom: 8, lineHeight: 18 },
    exerciseCount: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 12 },
    exerciseCountText: { fontSize: 12, color: theme.primaryLight, fontWeight: '500' },
  });
}
