import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Image, StyleSheet, Animated } from 'react-native';
import { useRouter } from 'expo-router';
import { Timer, Check, ArrowRight, SkipForward, Mic, Minus, Plus } from 'lucide-react-native';
import { SmartMusicPlayer } from '../src/components/SmartMusicPlayer';
import { VoiceLoggerModal } from '../src/components/VoiceLoggerModal';
import { speak } from '../src/services/tts';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../src/services/theme';
import { useWorkoutStore } from '../src/stores';

const FALLBACK_IMAGE =
  'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Barbell_Bench_Press_-_Medium_Grip/0.jpg';

function defaultReps(targetReps?: string): number {
  const match = targetReps?.match(/\d+/);
  return match ? parseInt(match[0], 10) : 10;
}

export default function WorkoutActive() {
  const { theme } = useTheme();
  const router = useRouter();
  const { activeWorkout, loggedSets, logSet } = useWorkoutStore();

  const exercises = activeWorkout?.exercises ?? [];
  const totalSets = exercises.reduce((sum, ex) => sum + (ex.sets || 1), 0);

  const [exIdx, setExIdx] = useState(0);
  const [setNum, setSetNum] = useState(1);
  const [rest, setRest] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [showVoiceModal, setShowVoiceModal] = useState(false);

  const currentExercise = exercises[exIdx];
  const [weight, setWeight] = useState(20);
  const [reps, setReps] = useState(defaultReps(currentExercise?.target_reps));
  const [rpe, setRpe] = useState(currentExercise?.target_rpe ?? 8);

  const spokeMilestones = useRef(new Set<number>());

  // Redirect back if this screen is opened without an active session
  // (deep link, stale nav state, or app restart mid-workout).
  useEffect(() => {
    if (!activeWorkout) router.replace('/(tabs)/workout');
  }, [activeWorkout, router]);

  useEffect(() => {
    setReps(defaultReps(currentExercise?.target_reps));
    setRpe(currentExercise?.target_rpe ?? 8);
  }, [exIdx]);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((e) => e + 1);
      if (rest > 0) {
        setRest((r) => {
          if (r <= 1) {
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            spokeMilestones.current.clear();
            return 0;
          }
          if (r === 30 && !spokeMilestones.current.has(30)) {
            spokeMilestones.current.add(30);
            speak('30 seconds remaining. Get ready.');
          } else if (r === 10 && !spokeMilestones.current.has(10)) {
            spokeMilestones.current.add(10);
            speak('10 seconds. Set up for the next exercise.');
          } else if (r === 3 && !spokeMilestones.current.has(3)) {
            spokeMilestones.current.add(3);
            speak('3, 2, 1. Go!');
          }
          return r - 1;
        });
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [rest]);

  const fmt = (n: number) =>
    Math.floor(n / 60).toString().padStart(2, '0') + ':' + (n % 60).toString().padStart(2, '0');

  if (!activeWorkout || !currentExercise) return null;

  const completeSet = (loggedWeight = weight, loggedReps = reps, loggedRpe = rpe) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    logSet({
      exercise_id: currentExercise.exercise_id,
      name: currentExercise.name,
      set_number: setNum,
      weight_kg: loggedWeight,
      reps_completed: loggedReps,
      rpe: loggedRpe,
    });

    if (setNum < (currentExercise.sets || 1)) {
      setSetNum((n) => n + 1);
      setRest(90);
    } else if (exIdx < exercises.length - 1) {
      setExIdx((i) => i + 1);
      setSetNum(1);
      setRest(90);
    } else {
      router.push('/workout-complete');
    }
  };

  const handleVoiceSetLogged = (setDetails: {
    exercise_name?: string | null;
    weight_kg?: number | null;
    reps?: number | null;
    rpe?: number | null;
  }) => {
    const w = setDetails.weight_kg ?? weight;
    const r = setDetails.reps ?? reps;
    const p = setDetails.rpe ?? rpe;
    setWeight(w);
    setReps(r);
    setRpe(p);
    completeSet(w, r, p);
  };

  const skipRest = () => {
    Haptics.selectionAsync();
    setRest(0);
  };

  const s = makeStyles(theme);
  const completedSets = loggedSets.length;

  return (
    <View style={s.container}>
      {/* Header with Timer & Voice Button */}
      <View style={s.headerRow}>
        <View style={s.timerHeader}>
          <Timer size={20} color={theme.primaryLight} />
          <Text style={s.timerText}>{fmt(elapsed)}</Text>
        </View>

        <TouchableOpacity style={s.voiceMicBtn} onPress={() => setShowVoiceModal(true)}>
          <Mic size={18} color={theme.primaryLight} />
          <Text style={s.voiceMicText}>Voice Log</Text>
        </TouchableOpacity>
      </View>

      {/* Exercise Info */}
      <View style={s.exerciseInfo}>
        <Text style={s.exerciseName}>{currentExercise.name}</Text>
        <Text style={s.exerciseMuscle}>
          {currentExercise.target_muscle} · Set {setNum} of {currentExercise.sets}
        </Text>
        <Image source={{ uri: currentExercise.gif_url || FALLBACK_IMAGE }} style={s.exerciseGif} />
      </View>

      {/* Manual set adjusters */}
      <View style={s.adjusterRow}>
        <View style={s.adjuster}>
          <Text style={s.adjusterLabel}>Weight (kg)</Text>
          <View style={s.stepper}>
            <TouchableOpacity onPress={() => setWeight((w) => Math.max(0, w - 2.5))} style={s.stepBtn}>
              <Minus size={14} color={theme.text} />
            </TouchableOpacity>
            <Text style={s.stepValue}>{weight}</Text>
            <TouchableOpacity onPress={() => setWeight((w) => w + 2.5)} style={s.stepBtn}>
              <Plus size={14} color={theme.text} />
            </TouchableOpacity>
          </View>
        </View>
        <View style={s.adjuster}>
          <Text style={s.adjusterLabel}>Reps</Text>
          <View style={s.stepper}>
            <TouchableOpacity onPress={() => setReps((r) => Math.max(0, r - 1))} style={s.stepBtn}>
              <Minus size={14} color={theme.text} />
            </TouchableOpacity>
            <Text style={s.stepValue}>{reps}</Text>
            <TouchableOpacity onPress={() => setReps((r) => r + 1)} style={s.stepBtn}>
              <Plus size={14} color={theme.text} />
            </TouchableOpacity>
          </View>
        </View>
        <View style={s.adjuster}>
          <Text style={s.adjusterLabel}>RPE</Text>
          <View style={s.stepper}>
            <TouchableOpacity onPress={() => setRpe((p) => Math.max(1, p - 0.5))} style={s.stepBtn}>
              <Minus size={14} color={theme.text} />
            </TouchableOpacity>
            <Text style={s.stepValue}>{rpe}</Text>
            <TouchableOpacity onPress={() => setRpe((p) => Math.min(10, p + 0.5))} style={s.stepBtn}>
              <Plus size={14} color={theme.text} />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Set Progress */}
      <View style={s.progress}>
        <Text style={s.progressText}>
          Set {completedSets + 1} of {totalSets}
        </Text>
        <View style={s.progressBar}>
          <View style={[s.progressFill, { width: `${(completedSets / totalSets) * 100}%` }]} />
        </View>
      </View>

      {/* Rest Timer or Complete Button */}
      {rest > 0 ? (
        <View style={s.restTimer}>
          <Text style={s.restLabel}>Rest Timer</Text>
          <Text style={s.restTime}>{fmt(rest)}</Text>
          <TouchableOpacity style={s.skipButton} onPress={skipRest}>
            <SkipForward size={16} color={theme.textSecondary} />
            <Text style={s.skipText}>Skip</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity style={s.completeButton} onPress={() => completeSet()}>
          <Check size={24} color={theme.background} />
          <Text style={s.completeText}>Complete Set</Text>
        </TouchableOpacity>
      )}

      {/* Music Player */}
      <SmartMusicPlayer compact currentSet={completedSets + 1} totalSets={totalSets} />

      {/* Finish Workout early */}
      <TouchableOpacity style={s.finishButton} onPress={() => router.push('/workout-complete')}>
        <Text style={s.finishText}>Finish Workout</Text>
        <ArrowRight size={16} color={theme.textSecondary} />
      </TouchableOpacity>

      {/* Voice Logger Modal */}
      <VoiceLoggerModal
        visible={showVoiceModal}
        onClose={() => setShowVoiceModal(false)}
        onSetLogged={handleVoiceSetLogged}
      />
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.background,
      padding: 20,
    },
    headerRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: 50,
      marginBottom: 20,
    },
    timerHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    timerText: {
      fontSize: 20,
      fontWeight: '700',
      color: theme.text,
    },
    voiceMicBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      backgroundColor: theme.primaryBg,
      borderColor: theme.primary,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 20,
    },
    voiceMicText: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.primaryLight,
    },
    exerciseInfo: {
      alignItems: 'center',
      marginBottom: 16,
    },
    exerciseName: {
      fontSize: 22,
      fontWeight: '700',
      color: theme.text,
      marginBottom: 4,
      textAlign: 'center',
    },
    exerciseMuscle: {
      fontSize: 13,
      color: theme.primaryLight,
      marginBottom: 16,
    },
    exerciseGif: {
      width: 150,
      height: 150,
      borderRadius: 12,
    },
    adjusterRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      gap: 8,
      marginBottom: 16,
    },
    adjuster: {
      flex: 1,
      alignItems: 'center',
      backgroundColor: theme.surface,
      borderRadius: 12,
      paddingVertical: 8,
    },
    adjusterLabel: {
      fontSize: 11,
      color: theme.textMuted,
      marginBottom: 6,
    },
    stepper: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    stepBtn: {
      width: 26,
      height: 26,
      borderRadius: 13,
      backgroundColor: theme.surfaceHover,
      alignItems: 'center',
      justifyContent: 'center',
    },
    stepValue: {
      fontSize: 15,
      fontWeight: '700',
      color: theme.text,
      minWidth: 30,
      textAlign: 'center',
    },
    progress: {
      marginBottom: 20,
    },
    progressText: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.textSecondary,
      marginBottom: 8,
      textAlign: 'center',
    },
    progressBar: {
      height: 8,
      backgroundColor: theme.surfaceHover,
      borderRadius: 4,
      overflow: 'hidden',
    },
    progressFill: {
      height: 8,
      backgroundColor: theme.primary,
      borderRadius: 4,
    },
    restTimer: {
      alignItems: 'center',
      marginBottom: 20,
    },
    restLabel: {
      fontSize: 14,
      color: theme.textSecondary,
      marginBottom: 4,
    },
    restTime: {
      fontSize: 48,
      fontWeight: '800',
      color: theme.primaryLight,
      marginBottom: 16,
    },
    skipButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      paddingHorizontal: 20,
      paddingVertical: 8,
      borderRadius: 8,
      backgroundColor: theme.surfaceHover,
    },
    skipText: {
      color: theme.textSecondary,
      fontSize: 14,
      fontWeight: '600',
    },
    completeButton: {
      flexDirection: 'row',
      backgroundColor: theme.success,
      borderRadius: 12,
      padding: 16,
      alignItems: 'center',
      justifyContent: 'center',
      gap: 8,
      marginBottom: 12,
    },
    completeText: {
      color: theme.background,
      fontSize: 18,
      fontWeight: '700',
    },
    finishButton: {
      flexDirection: 'row',
      backgroundColor: theme.surfaceHover,
      borderRadius: 12,
      padding: 16,
      alignItems: 'center',
      justifyContent: 'center',
      gap: 8,
    },
    finishText: {
      color: theme.textSecondary,
      fontSize: 16,
      fontWeight: '600',
    },
  });
}
