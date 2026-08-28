/**
 * Workout Timer — countdown with audio cues at milestones and haptic feedback.
 * Supports: countdown timer, rest timer, interval timer, AMRAP timer.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Easing,
} from 'react-native';
import { Play, Pause, RotateCcw, SkipForward, Bell } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { speak } from '../../src/services/tts';
import { useTheme } from '../services/theme';

type TimerMode = 'countdown' | 'rest' | 'interval' | 'amrap';

interface WorkoutTimerProps {
  initialSeconds?: number;
  mode?: TimerMode;
  restSeconds?: number;
  workSeconds?: number;
  rounds?: number;
  onComplete?: () => void;
  onTick?: (remaining: number) => void;
}

const SPOKEN_MILESTONES = new Set([30, 10, 5, 3, 2, 1]);

export function WorkoutTimer({
  initialSeconds = 90,
  mode = 'rest',
  restSeconds = 90,
  workSeconds = 40,
  rounds = 5,
  onComplete,
  onTick,
}: WorkoutTimerProps) {
  const { theme } = useTheme();
  const [remaining, setRemaining] = useState(initialSeconds);
  const [isRunning, setIsRunning] = useState(false);
  const [currentRound, setCurrentRound] = useState(1);
  const [isWorkPhase, setIsWorkPhase] = useState(true);
  const spokeMilestones = useRef(new Set<number>());
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(1)).current;

  // Pulse animation when running
  useEffect(() => {
    if (isRunning) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    }
  }, [isRunning]);

  // Progress bar animation
  useEffect(() => {
    const total = mode === 'interval' ? (isWorkPhase ? workSeconds : restSeconds) : initialSeconds;
    const progress = remaining / Math.max(1, total);
    Animated.timing(progressAnim, {
      toValue: progress,
      duration: 200,
      useNativeDriver: false,
    }).start();
  }, [remaining]);

  // Main timer loop
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          // Timer complete
          clearInterval(interval);
          setIsRunning(false);

          // Audio cue
          speak('Time!');

          if (mode === 'interval') {
            if (isWorkPhase && currentRound < rounds) {
              // Switch to rest
              setIsWorkPhase(false);
              setRemaining(restSeconds);
              spokeMilestones.current.clear();
              setTimeout(() => {
                setIsRunning(true);
                speak('Rest period. Breathe.');
              }, 500);
              return restSeconds;
            } else {
              // All rounds done
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              onComplete?.();
              return 0;
            }
          } else {
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            onComplete?.();
            return 0;
          }
        }

        // Audio milestones
        if (SPOKEN_MILESTONES.has(r) && !spokeMilestones.current.has(r)) {
          spokeMilestones.current.add(r);
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

          if (r === 30) speak('30 seconds remaining');
          else if (r === 10) speak('10 seconds');
          else if (r <= 3) speak(`${r}`);
        }

        onTick?.(r - 1);
        return r - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning, mode, isWorkPhase, currentRound]);

  function toggle() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setIsRunning(!isRunning);
  }

  function reset() {
    Haptics.selectionAsync();
    setIsRunning(false);
    spokeMilestones.current.clear();
    if (mode === 'interval') {
      setCurrentRound(1);
      setIsWorkPhase(true);
      setRemaining(workSeconds);
    } else {
      setRemaining(initialSeconds);
    }
  }

  function formatTime(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  const isUrgent = remaining <= 10;
  const isComplete = remaining === 0 && !isRunning;

  return (
    <View style={styles.container}>
      {/* Phase Indicator (interval mode) */}
      {mode === 'interval' && (
        <View style={styles.phaseRow}>
          <View
            style={[
              styles.phaseChip,
              { backgroundColor: isWorkPhase ? `${theme.success}26` : theme.surfaceHover },
            ]}
          >
            <Text style={[styles.phaseText, { color: isWorkPhase ? theme.success : theme.textMuted }]}>WORK</Text>
          </View>
          <Text style={[styles.roundText, { color: theme.text }]}>Round {currentRound}/{rounds}</Text>
          <View
            style={[
              styles.phaseChip,
              { backgroundColor: !isWorkPhase ? `${theme.primary}26` : theme.surfaceHover },
            ]}
          >
            <Text style={[styles.phaseText, { color: !isWorkPhase ? theme.primary : theme.textMuted }]}>REST</Text>
          </View>
        </View>
      )}

      {/* Timer Display */}
      <Animated.View style={[styles.timerContainer, { transform: [{ scale: pulseAnim }] }]}>
        <Text
          style={[
            styles.timerText,
            { color: isUrgent ? theme.danger : isComplete ? theme.success : theme.text },
          ]}
        >
          {formatTime(remaining)}
        </Text>
        <Text style={[styles.timerLabel, { color: theme.textMuted }]}>
          {mode === 'interval' ? (isWorkPhase ? 'Work' : 'Rest') : 'Remaining'}
        </Text>
      </Animated.View>

      {/* Progress Bar */}
      <View style={[styles.progressBg, { backgroundColor: theme.surfaceHover }]}>
        <Animated.View
          style={[
            styles.progressFill,
            {
              width: progressWidth,
              backgroundColor: isUrgent ? theme.danger : isWorkPhase ? theme.success : theme.primary,
            },
          ]}
        />
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity style={styles.controlBtn} onPress={reset}>
          <RotateCcw size={20} color={theme.textSecondary} />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.playBtn, { backgroundColor: isRunning ? theme.danger : theme.success }]}
          onPress={toggle}
        >
          {isRunning ? (
            <Pause size={28} color="#fff" />
          ) : (
            <Play size={28} color="#fff" />
          )}
        </TouchableOpacity>
        {mode === 'interval' && (
          <TouchableOpacity
            style={styles.controlBtn}
            onPress={() => {
              Haptics.selectionAsync();
              if (currentRound < rounds) {
                setCurrentRound((r) => r + 1);
                setIsWorkPhase(true);
                setRemaining(workSeconds);
                spokeMilestones.current.clear();
              }
            }}
          >
            <SkipForward size={20} color={theme.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Audio cue indicator */}
      <View style={styles.cueIndicator}>
        <Bell size={12} color={isRunning ? theme.warning : theme.border} />
        <Text style={[styles.cueText, { color: isRunning ? theme.warning : theme.border }]}>Audio cues active</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', paddingVertical: 20 },
  phaseRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  phaseChip: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 8,
  },
  phaseText: { fontSize: 12, fontWeight: '700' },
  roundText: { fontSize: 14, fontWeight: '600' },

  timerContainer: { alignItems: 'center', marginBottom: 20 },
  timerText: { fontSize: 64, fontWeight: '800', fontVariant: ['tabular-nums'] },
  timerLabel: { fontSize: 14, marginTop: 4 },

  progressBg: {
    width: 200,
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 24,
  },
  progressFill: { height: 6, borderRadius: 3 },

  controls: { flexDirection: 'row', alignItems: 'center', gap: 24, marginBottom: 16 },
  controlBtn: { padding: 12 },
  playBtn: { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center' },

  cueIndicator: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  cueText: { fontSize: 11 },
});
