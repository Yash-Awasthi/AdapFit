/**
 * Workout Screen — Premium AI-Powered Workout Generator
 * Glassmorphism cards, animated elements, modern workout UI
 */
import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, TextInput,
  ScrollView, Animated, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { fitText } from '../../src/theme/layout';
import {
  GlassCard, SectionHeaderPremium, QuickAction,
} from '../../src/components/PremiumComponents';
import { api } from '../../src/services/api';
import { useUserStore } from '../../src/stores';
import { API_V1 as API } from '../../src/services/config';
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

const PROMPT_EXAMPLES = [
  '45 minutes, upper body, shoulder is sore',
  'Short session, dumbbells only',
  'What should I train today?',
];

export default function WorkoutScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const userId = useUserStore((s) => s.userId);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedMuscle, setSelectedMuscle] = useState('All');
  const [prompt, setPrompt] = useState('');
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [asking, setAsking] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  const askCoach = async (text: string) => {
    const question = text.trim();
    if (!question || asking) return;
    setAsking(true);
    setSuggestion(null);
    try {
      const data = await api.chat(userId, question);
      setSuggestion(data.reply);
    } catch {
      setSuggestion("Couldn't reach the coach. Check your connection and try again.");
    }
    setAsking(false);
  };

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
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
      {/* Header */}
      <LinearGradient
        colors={[colors.health.heart, colors.health.energy]}
        style={[styles.header, { paddingTop: insets.top + spacing.md }]}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerText}>
            <Text style={styles.headerTitle} {...fitText(1)}>Workouts</Text>
            <Text style={styles.headerSubtitle} numberOfLines={2}>
              Adaptive training built from your recovery data
            </Text>
          </View>
          <View style={styles.workoutCount}>
            <Text style={styles.workoutCountNumber} {...fitText(1)}>{workouts.length}</Text>
            <Text style={styles.workoutCountLabel}>sessions</Text>
          </View>
        </View>
      </LinearGradient>

      {/* Ask the coach */}
      <View style={styles.askSection}>
        <SectionHeaderPremium icon="sparkles" iconColor={colors.primary} title="Ask for a session" />
        <View style={styles.askBox}>
          <TextInput
            style={styles.askInput}
            value={prompt}
            onChangeText={setPrompt}
            placeholder="Describe what you want to train, how long you have, and anything that hurts."
            placeholderTextColor={colors.text.muted}
            multiline
            maxLength={500}
            editable={!asking}
            accessibilityLabel="Describe the workout you want"
          />
          <View style={styles.askActions}>
            <Text style={styles.askCounter}>{prompt.length}/500</Text>
            <TouchableOpacity
              style={[styles.askButton, (!prompt.trim() || asking) && styles.askButtonDisabled]}
              onPress={() => askCoach(prompt)}
              disabled={!prompt.trim() || asking}
              accessibilityRole="button"
              accessibilityLabel="Get a suggestion"
            >
              {asking
                ? <ActivityIndicator size="small" color="#FFF" />
                : <Ionicons name="arrow-up" size={18} color="#FFF" />}
            </TouchableOpacity>
          </View>
        </View>

        {!suggestion && !asking && (
          <View style={styles.exampleRow}>
            {PROMPT_EXAMPLES.map((example) => (
              <TouchableOpacity
                key={example}
                style={styles.examplePill}
                onPress={() => { setPrompt(example); askCoach(example); }}
              >
                <Text style={styles.exampleText} numberOfLines={1}>{example}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {suggestion && (
          <GlassCard variant="primary" style={styles.suggestionCard}>
            <View style={styles.suggestionHeader}>
              <Ionicons name="sparkles" size={14} color={colors.primaryLight} />
              <Text style={styles.suggestionLabel}>Coach suggestion</Text>
              <TouchableOpacity onPress={() => setSuggestion(null)} hitSlop={10}>
                <Ionicons name="close" size={16} color={colors.text.muted} />
              </TouchableOpacity>
            </View>
            <Text style={styles.suggestionText}>{suggestion}</Text>
          </GlassCard>
        )}
      </View>

      {/* Quick Actions */}
      <View style={styles.quickActionsRow}>
        <TouchableOpacity style={styles.generateBtn} onPress={generateWorkout} disabled={generating}>
          <LinearGradient colors={[colors.primary, '#8B5CF6']} style={styles.generateBtnGradient}>
            <Ionicons name={generating ? 'hourglass' : 'sparkles'} size={20} color="#FFF" />
            <Text style={styles.generateBtnText}>{generating ? 'Generating…' : 'Generate Workout'}</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>

      <View style={styles.quickActionsRow}>
        <QuickAction icon="checkmark-circle" label="Form check" color={colors.health.calm} onPress={() => router.push('/form-checker' as any)} />
        <QuickAction
          icon="timer"
          label="Quick 20"
          color={colors.health.energy}
          onPress={() => askCoach('Give me a 20 minute session I can start right now with no equipment.')}
        />
        <QuickAction icon="analytics" label="Stats" color={colors.health.mental} onPress={() => router.push('/stats' as any)} />
        <QuickAction icon="calendar" label="Plan" color="#3B82F6" onPress={() => router.push('/periodization' as any)} />
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
            <Text style={styles.generateBtnSmallText} numberOfLines={1}>Generate first workout</Text>
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

      <View style={{ height: 120 }} />
    </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.lg },
  headerText: { flex: 1 },
  headerTitle: { fontSize: 28, fontWeight: '800', color: '#FFF', letterSpacing: -0.5 },
  headerSubtitle: { fontSize: 13, color: 'rgba(255,255,255,0.85)', marginTop: 4, lineHeight: 18 },
  workoutCount: { minWidth: 72, alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.22)', borderRadius: 16, paddingVertical: 10, paddingHorizontal: 12 },
  workoutCountNumber: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  workoutCountLabel: { fontSize: 10, color: 'rgba(255,255,255,0.85)', marginTop: 2 },

  // Ask the coach
  askSection: { marginTop: spacing.lg },
  askBox: {
    marginHorizontal: spacing.screenPadding,
    backgroundColor: colors.bg.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.surface.border,
    padding: spacing.md,
  },
  askInput: {
    minHeight: 68,
    maxHeight: 140,
    color: colors.text.primary,
    fontSize: 14,
    lineHeight: 20,
    textAlignVertical: 'top',
  },
  askActions: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.sm },
  askCounter: { fontSize: 11, color: colors.text.muted },
  askButton: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: colors.primary,
    alignItems: 'center', justifyContent: 'center',
  },
  askButtonDisabled: { backgroundColor: colors.bg.elevated },
  exampleRow: {
    flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm,
    paddingHorizontal: spacing.screenPadding, marginTop: spacing.md,
  },
  examplePill: {
    maxWidth: '100%',
    backgroundColor: colors.bg.card,
    borderWidth: 1, borderColor: colors.surface.border,
    borderRadius: radius.pill, paddingHorizontal: 12, paddingVertical: 7,
  },
  exampleText: { fontSize: 12, color: colors.text.secondary },
  suggestionCard: { marginHorizontal: spacing.screenPadding, marginTop: spacing.md },
  suggestionHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: spacing.sm },
  suggestionLabel: { flex: 1, fontSize: 11, fontWeight: '700', color: colors.primaryLight, textTransform: 'uppercase', letterSpacing: 0.5 },
  suggestionText: { fontSize: 14, color: colors.text.primary, lineHeight: 21 },

  // Quick Actions
  quickActionsRow: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  generateBtn: { flex: 1 },
  generateBtnGradient: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, paddingVertical: spacing.md, borderRadius: radius.button },
  generateBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
  generateBtnSmall: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm,
    alignSelf: 'stretch', backgroundColor: colors.primary,
    // Horizontal padding is what keeps a long label off the pill's edge.
    paddingVertical: spacing.md, paddingHorizontal: spacing.xl,
    borderRadius: radius.button, marginTop: spacing.lg,
  },
  generateBtnSmallText: { flexShrink: 1, fontSize: 14, fontWeight: '700', color: '#FFF', textAlign: 'center' },

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
