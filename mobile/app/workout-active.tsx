import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Image, StyleSheet, Animated, Easing } from 'react-native';
import { useRouter } from 'expo-router';
import { Timer, Check, ArrowRight, SkipForward, Mic } from 'lucide-react-native';
import { SmartMusicPlayer } from '../src/components/SmartMusicPlayer';
import { VoiceLoggerModal } from '../src/components/VoiceLoggerModal';
import { speak } from '../src/services/tts';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../src/services/theme';

export default function WorkoutActive() {
  const { theme } = useTheme();
  const [cur, setCur] = useState(1);
  const [tot] = useState(3);
  const [rest, setRest] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [loggedWeight, setLoggedWeight] = useState<number | null>(80);
  const [loggedReps, setLoggedReps] = useState<number | null>(10);
  const [loggedRpe, setLoggedRpe] = useState<number | null>(8.0);
  const router = useRouter();

  const spokeMilestones = useRef(new Set<number>());

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
          // TTS coaching cues at milestones
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
    Math.floor(n / 60)
      .toString()
      .padStart(2, '0') +
    ':' +
    (n % 60).toString().padStart(2, '0');

  const completeSet = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    if (cur < tot) {
      setCur((c) => c + 1);
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
    if (setDetails.weight_kg) setLoggedWeight(setDetails.weight_kg);
    if (setDetails.reps) setLoggedReps(setDetails.reps);
    if (setDetails.rpe) setLoggedRpe(setDetails.rpe);
    completeSet();
  };

  const skipRest = () => {
    Haptics.selectionAsync();
    setRest(0);
  };

  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      {/* Header with Timer & Voice Button */}
      <View style={s.headerRow}>
        <View style={s.timerHeader}>
          <Timer size={20} color={theme.primaryLight} />
          <Text style={s.timerText}>{fmt(elapsed)}</Text>
        </View>

        <TouchableOpacity
          style={s.voiceMicBtn}
          onPress={() => setShowVoiceModal(true)}
        >
          <Mic size={18} color={theme.primaryLight} />
          <Text style={s.voiceMicText}>Voice Log</Text>
        </TouchableOpacity>
      </View>

      {/* Exercise Info */}
      <View style={s.exerciseInfo}>
        <Text style={s.exerciseName}>Barbell Bench Press</Text>
        <Text style={s.exerciseMuscle}>
          Chest · Target: {loggedWeight}kg × {loggedReps} reps (RPE {loggedRpe})
        </Text>
        <Image
          source={{
            uri: 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/Barbell_Bench_Press_-_Medium_Grip/0.jpg',
          }}
          style={s.exerciseGif}
        />
      </View>

      {/* Set Progress */}
      <View style={s.progress}>
        <Text style={s.progressText}>
          Set {cur} of {tot}
        </Text>
        <View style={s.progressBar}>
          <View style={[s.progressFill, { width: `${(cur / tot) * 100}%` }]} />
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
        <TouchableOpacity style={s.completeButton} onPress={completeSet}>
          <Check size={24} color={theme.background} />
          <Text style={s.completeText}>Complete Set</Text>
        </TouchableOpacity>
      )}

      {/* Music Player */}
      <SmartMusicPlayer compact currentSet={cur} totalSets={tot} />

      {/* Finish Workout */}
      <TouchableOpacity
        style={s.finishButton}
        onPress={() => router.push('/workout-complete')}
      >
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
      backgroundColor: '#1E1B4B',
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
      marginBottom: 24,
    },
    exerciseName: {
      fontSize: 22,
      fontWeight: '700',
      color: theme.text,
      marginBottom: 4,
    },
    exerciseMuscle: {
      fontSize: 13,
      color: theme.primaryLight,
      marginBottom: 16,
    },
    exerciseGif: {
      width: 180,
      height: 180,
      borderRadius: 12,
    },
    progress: {
      marginBottom: 24,
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
      marginBottom: 24,
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
