import React, { useState, useEffect, useRef } from "react";
import {
  View, Text, StyleSheet, TouchableOpacity, Animated, Easing,
} from "react-native";
import { Play, Pause, SkipForward, X, Wind, Clock } from "lucide-react-native";
import { useTheme } from "../services/theme";

interface MeditationStep {
  step: number;
  instruction: string;
  duration_seconds: number;
}

interface MeditationSession {
  id: string;
  name: string;
  category: string;
  duration_minutes: number;
  difficulty: string;
  steps: MeditationStep[];
  benefits: string[];
}

interface Props {
  session: MeditationSession;
  onComplete: () => void;
  onClose: () => void;
}

export default function MeditationPlayer({ session, onComplete, onClose }: Props) {
  const { theme } = useTheme();
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(session.steps[0]?.duration_seconds || 0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [totalElapsed, setTotalElapsed] = useState(0);
  const breathAnim = useRef(new Animated.Value(1)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  const currentStep = session.steps[currentStepIdx];
  const totalSteps = session.steps.length;
  const progress = totalSteps > 0 ? ((currentStepIdx + 1) / totalSteps) * 100 : 0;

  // Timer
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          // Move to next step
          if (currentStepIdx < totalSteps - 1) {
            setCurrentStepIdx((i) => i + 1);
            return session.steps[currentStepIdx + 1]?.duration_seconds || 0;
          } else {
            setIsPlaying(false);
            onComplete();
            return 0;
          }
        }
        return prev - 1;
      });
      setTotalElapsed((e) => e + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isPlaying, currentStepIdx]);

  // Breathing animation
  useEffect(() => {
    if (!isPlaying) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(breathAnim, { toValue: 1.4, duration: 4000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(breathAnim, { toValue: 1, duration: 4000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [isPlaying]);

  // Pulse animation for current step
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.05, duration: 2000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 2000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const skipStep = () => {
    if (currentStepIdx < totalSteps - 1) {
      setCurrentStepIdx((i) => i + 1);
      setTimeLeft(session.steps[currentStepIdx + 1]?.duration_seconds || 0);
    }
  };

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, "0")}`;

  const totalDuration = session.steps.reduce((acc, s) => acc + s.duration_seconds, 0);

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Close button */}
      <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
        <X size={24} color={theme.textSecondary} />
      </TouchableOpacity>

      {/* Session info */}
      <Text style={[styles.sessionName, { color: theme.text }]}>{session.name}</Text>
      <Text style={[styles.sessionMeta, { color: theme.textSecondary }]}>
        Step {currentStepIdx + 1} of {totalSteps} • {formatTime(totalElapsed)} / {formatTime(totalDuration)}
      </Text>

      {/* Breathing Circle */}
      <View style={styles.breathContainer}>
        <Animated.View
          style={[
            styles.breathCircle,
            {
              backgroundColor: theme.primaryBg,
              borderColor: `${theme.primaryLight}4D`,
              transform: [{ scale: breathAnim }],
            },
          ]}
        />
        <Animated.View
          style={[
            styles.breathInner,
            { backgroundColor: theme.primaryBg, transform: [{ scale: pulseAnim }] },
          ]}
        />
        <Text style={[styles.breathTime, { color: theme.text }]}>{formatTime(timeLeft)}</Text>
        <Text style={[styles.breathLabel, { color: theme.textSecondary }]}>remaining</Text>
      </View>

      {/* Current instruction */}
      <Animated.View style={[styles.instructionCard, { backgroundColor: theme.surface, transform: [{ scale: pulseAnim }] }]}>
        <Wind size={20} color={theme.primaryLight} />
        <Text style={[styles.instructionText, { color: theme.text }]}>{currentStep?.instruction || "Session complete"}</Text>
      </Animated.View>

      {/* Progress bar */}
      <View style={[styles.progressTrack, { backgroundColor: theme.border }]}>
        <View style={[styles.progressFill, { backgroundColor: theme.primaryLight, width: `${progress}%` }]} />
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity style={styles.controlBtn} onPress={skipStep}>
          <SkipForward size={24} color={theme.textSecondary} />
          <Text style={[styles.controlLabel, { color: theme.textSecondary }]}>Skip</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.playBtn, { backgroundColor: theme.primary }]}
          onPress={() => setIsPlaying(!isPlaying)}
        >
          {isPlaying ? (
            <Pause size={32} color="#FFF" />
          ) : (
            <Play size={32} color="#FFF" style={{ marginLeft: 4 }} />
          )}
        </TouchableOpacity>

        <TouchableOpacity style={styles.controlBtn} onPress={onComplete}>
          <Clock size={24} color={theme.textSecondary} />
          <Text style={[styles.controlLabel, { color: theme.textSecondary }]}>End</Text>
        </TouchableOpacity>
      </View>

      {/* Benefits */}
      <View style={styles.benefitsRow}>
        {session.benefits.slice(0, 3).map((b, i) => (
          <Text key={i} style={[styles.benefitTag, { backgroundColor: theme.surface, color: theme.textSecondary }]}>{b}</Text>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1, alignItems: "center",
    justifyContent: "center", padding: 24,
  },
  closeBtn: { position: "absolute", top: 50, right: 20 },
  sessionName: { fontSize: 22, fontWeight: "700", marginBottom: 4 },
  sessionMeta: { fontSize: 13, marginBottom: 30 },
  breathContainer: { alignItems: "center", marginBottom: 30, position: "relative" },
  breathCircle: {
    width: 180, height: 180, borderRadius: 90,
    borderWidth: 2,
  },
  breathInner: {
    position: "absolute", width: 140, height: 140, borderRadius: 70,
    top: 20,
  },
  breathTime: {
    position: "absolute", fontSize: 36, fontWeight: "300",
    top: 65,
  },
  breathLabel: { position: "absolute", fontSize: 12, top: 110 },
  instructionCard: {
    flexDirection: "row", alignItems: "center", gap: 10,
    borderRadius: 12, padding: 16,
    marginBottom: 20, width: "100%",
  },
  instructionText: { fontSize: 15, flex: 1, lineHeight: 22 },
  progressTrack: {
    width: "100%", height: 4, borderRadius: 2, marginBottom: 30,
  },
  progressFill: { height: 4, borderRadius: 2 },
  controls: { flexDirection: "row", alignItems: "center", gap: 40, marginBottom: 30 },
  controlBtn: { alignItems: "center", gap: 4 },
  controlLabel: { fontSize: 11 },
  playBtn: {
    width: 72, height: 72, borderRadius: 36,
    alignItems: "center", justifyContent: "center",
  },
  benefitsRow: { flexDirection: "row", gap: 8, flexWrap: "wrap", justifyContent: "center" },
  benefitTag: {
    fontSize: 11,
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12,
  },
});
