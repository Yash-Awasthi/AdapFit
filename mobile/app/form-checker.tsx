/**
 * Form Checker — camera capture analyzed by real pose estimation on the
 * backend (MediaPipe). Tap "Check Form" to grab a frame; the server
 * extracts landmarks, computes the exercise's joint angle, and scores it.
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Easing,
} from 'react-native';
import { useRouter } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Target, Zap, CheckCircle, AlertTriangle, X, ChevronLeft, Camera as CameraIcon } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { api } from '../src/services/api';
import { useTheme } from '../src/services/theme';

interface ExerciseDefinition {
  id: string;
  backendId: string;
  name: string;
  target_muscle: string;
  visualization: { color: string };
}

const EXERCISE_DEFINITIONS: ExerciseDefinition[] = [
  { id: 'squat', backendId: 'barbell-back-squat', name: 'Squat', target_muscle: 'Quadriceps, Glutes', visualization: { color: '#818CF8' } },
  { id: 'push_up', backendId: 'push-up', name: 'Push-Up', target_muscle: 'Chest, Triceps', visualization: { color: '#22C55E' } },
  { id: 'deadlift', backendId: 'deadlift', name: 'Deadlift', target_muscle: 'Hamstrings, Lower Back', visualization: { color: '#F97316' } },
  { id: 'bicep_curl', backendId: 'bicep-curl', name: 'Bicep Curl', target_muscle: 'Biceps', visualization: { color: '#EC4899' } },
  { id: 'lunge', backendId: 'lunge', name: 'Forward Lunge', target_muscle: 'Quadriceps, Glutes', visualization: { color: '#A855F7' } },
];

type RepState = 'START' | 'DESCENDING' | 'BOTTOM' | 'ASCENDING' | 'TOP';

class RepCounterStateMachine {
  private state: RepState = 'START';
  private repCount = 0;
  private readonly MIN_ANGLE = 90;
  private readonly MAX_ANGLE = 160;
  private readonly HYSTERESIS = 10;

  processAngle(angle: number): { count: number; state: RepState; repCompleted: boolean } {
    let repCompleted = false;
    switch (this.state) {
      case 'START':
        if (angle > this.MAX_ANGLE - this.HYSTERESIS) this.state = 'DESCENDING';
        break;
      case 'DESCENDING':
        if (angle < this.MIN_ANGLE) this.state = 'BOTTOM';
        break;
      case 'BOTTOM':
        if (angle > this.MIN_ANGLE + this.HYSTERESIS) this.state = 'ASCENDING';
        break;
      case 'ASCENDING':
        if (angle > this.MAX_ANGLE - this.HYSTERESIS) {
          this.state = 'TOP';
          this.repCount++;
          repCompleted = true;
        }
        break;
      case 'TOP':
        this.state = 'DESCENDING';
        break;
    }
    return { count: this.repCount, state: this.state, repCompleted };
  }

  reset() {
    this.state = 'START';
    this.repCount = 0;
  }

  getState() { return this.state; }
}

const GRADE_COLOR: Record<string, string> = { A: '#22C55E', B: '#3B82F6', C: '#F59E0B', D: '#F97316', F: '#EF4444' };

export default function FormCheckerScreen() {
  const router = useRouter();
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);

  const [selectedExercise, setSelectedExercise] = useState<ExerciseDefinition | null>(null);
  const [repCount, setRepCount] = useState(0);
  const [grade, setGrade] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isActive, setIsActive] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [autoCounting, setAutoCounting] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const repMachine = useRef(new RepCounterStateMachine());
  const autoTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const frameBuffer = useRef<string[]>([]);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  async function startSession(exercise: ExerciseDefinition) {
    if (!permission?.granted) {
      const res = await requestPermission();
      if (!res.granted) return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setSelectedExercise(exercise);
    setIsActive(true);
    setRepCount(0);
    setGrade(null);
    setSuggestions([]);
    setLastMessage(null);
    repMachine.current.reset();
  }

  function endSession() {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    stopAutoCount();
    setIsActive(false);
  }

  function stopAutoCount() {
    setAutoCounting(false);
    if (autoTimer.current) {
      clearInterval(autoTimer.current);
      autoTimer.current = null;
    }
    frameBuffer.current = [];
  }

  async function flushFrameBuffer() {
    if (!selectedExercise || frameBuffer.current.length === 0) return;
    const frames = frameBuffer.current.splice(0);
    try {
      const result = await api.analyzeFormBatch(selectedExercise.backendId, frames);
      if (result.total_reps > 0) {
        setRepCount((prev) => prev + result.total_reps);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
      const lastDetected = [...result.frames].reverse().find((f) => f.detected && f.grade);
      if (lastDetected?.grade) {
        setGrade(lastDetected.grade);
        setSuggestions(result.suggestions || []);
      }
      if (result.frames.some((f) => !f.detected)) {
        setLastMessage('Some frames missed you — keep your full body in view.');
      }
    } catch {
      // silent — next batch will retry
    }
  }

  async function captureForAutoCount() {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.3, skipProcessing: true });
      if (photo?.base64) {
        frameBuffer.current.push(photo.base64);
        if (frameBuffer.current.length >= 4) await flushFrameBuffer();
      }
    } catch {
      // transient capture failure — keep going
    }
  }

  function startAutoCount() {
    if (!selectedExercise || autoCounting) return;
    setAutoCounting(true);
    setRepCount(0);
    setGrade(null);
    setSuggestions([]);
    setLastMessage('Auto-counting… perform your set now.');
    repMachine.current.reset();
    autoTimer.current = setInterval(captureForAutoCount, 1200);
  }

  async function checkForm() {
    if (!selectedExercise || !cameraRef.current || analyzing) return;
    setAnalyzing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const photo = await cameraRef.current.takePictureAsync({ base64: true, quality: 0.4, skipProcessing: true });
      if (!photo?.base64) throw new Error('capture failed');

      const result = await api.analyzeForm(selectedExercise.backendId, photo.base64);

      if (!result.detected) {
        setLastMessage(result.message || 'No person detected.');
      } else {
        setLastMessage(null);
        setGrade(result.grade || null);
        setSuggestions(result.suggestions || []);
        if (result.angle != null) {
          const rep = repMachine.current.processAngle(result.angle);
          setRepCount(rep.count);
          if (rep.repCompleted) Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        }
      }
    } catch {
      setLastMessage('Could not analyze that frame — try again.');
    }
    setAnalyzing(false);
  }

  const renderExercise = ({ item }: { item: ExerciseDefinition }) => (
    <TouchableOpacity style={s.exerciseCard} onPress={() => startSession(item)}>
      <View style={[s.exerciseIcon, { backgroundColor: item.visualization.color + '20' }]}>
        <Target size={24} color={item.visualization.color} />
      </View>
      <View style={s.exerciseInfo}>
        <Text style={s.exerciseName}>{item.name}</Text>
        <Text style={s.exerciseMuscle}>{item.target_muscle}</Text>
      </View>
      <Zap size={16} color={theme.textMuted} />
    </TouchableOpacity>
  );

  if (isActive && selectedExercise) {
    return (
      <View style={s.container}>
        <View style={s.activeHeader}>
          <TouchableOpacity onPress={endSession}>
            <X size={24} color={theme.textSecondary} />
          </TouchableOpacity>
          <Text style={s.activeTitle}>{selectedExercise.name}</Text>
          <View style={s.repBadge}>
            <Text style={s.repBadgeText}>{repCount}</Text>
          </View>
        </View>

        <View style={s.cameraWrap}>
          <CameraView ref={cameraRef} style={s.camera} facing="back" />
        </View>

        <Animated.View style={[s.repDisplay, { transform: [{ scale: pulseAnim }] }]}>
          <Text style={s.repNumber}>{repCount}</Text>
          <Text style={s.repLabel}>Reps</Text>
        </Animated.View>

        {grade && (
          <View style={s.gradeRow}>
            <View style={[s.gradePill, { borderColor: GRADE_COLOR[grade] }]}>
              <Text style={[s.gradePillText, { color: GRADE_COLOR[grade] }]}>Grade {grade}</Text>
            </View>
          </View>
        )}

        {lastMessage && (
          <View style={s.messageBox}>
            <AlertTriangle size={14} color={theme.warning} />
            <Text style={s.messageText}>{lastMessage}</Text>
          </View>
        )}

        {suggestions.length > 0 && (
          <View style={s.rulesContainer}>
            <Text style={s.rulesTitle}>Corrections:</Text>
            {suggestions.map((s2, i) => (
              <View key={i} style={s.ruleRow}>
                <AlertTriangle size={14} color={theme.danger} />
                <Text style={s.ruleText}>{s2}</Text>
              </View>
            ))}
          </View>
        )}
        {grade === 'A' && suggestions.length === 0 && (
          <View style={s.rulesContainer}>
            <View style={s.ruleRow}>
              <CheckCircle size={14} color={theme.success} />
              <Text style={s.ruleText}>Form looks solid — keep it up.</Text>
            </View>
          </View>
        )}

        <TouchableOpacity style={s.simulateBtn} onPress={checkForm} disabled={analyzing || autoCounting}>
          <CameraIcon size={16} color="#CBD5E1" />
          <Text style={s.simulateBtnText}>{analyzing ? 'Analyzing…' : 'Check Form'}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[s.endBtn, autoCounting && { backgroundColor: theme.danger }]}
          onPress={autoCounting ? stopAutoCount : startAutoCount}
        >
          <Text style={s.endBtnText}>{autoCounting ? 'Stop Auto-Count' : 'Start Auto-Count'}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={s.endBtn} onPress={endSession}>
          <Text style={s.endBtnText}>End Session</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={s.container}>
      <View style={s.topRow}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <ChevronLeft size={22} color={theme.text} />
        </TouchableOpacity>
      </View>
      <Text style={s.title}>Form Checker</Text>
      <Text style={s.subtitle}>Pick an exercise, then hold your phone so your full body is in frame.</Text>

      <FlatList
        data={EXERCISE_DEFINITIONS}
        keyExtractor={(item) => item.id}
        renderItem={renderExercise}
        contentContainerStyle={s.list}
      />
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    topRow: { marginTop: 48 },
    backBtn: { padding: 4, alignSelf: 'flex-start' },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 8 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 16 },
    list: { paddingBottom: 40 },

    exerciseCard: {
      flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface,
      borderRadius: 12, padding: 14, marginBottom: 8,
    },
    exerciseIcon: { width: 48, height: 48, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
    exerciseInfo: { flex: 1 },
    exerciseName: { fontSize: 15, fontWeight: '600', color: theme.text },
    exerciseMuscle: { fontSize: 12, color: theme.primaryLight, marginTop: 2 },

    activeHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 48, marginBottom: 16 },
    activeTitle: { fontSize: 18, fontWeight: '700', color: theme.text },
    repBadge: { backgroundColor: theme.primary, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
    repBadgeText: { color: '#fff', fontWeight: '700', fontSize: 14 },

    cameraWrap: { height: 220, borderRadius: 16, overflow: 'hidden', marginBottom: 16, backgroundColor: '#000' },
    camera: { flex: 1 },

    repDisplay: { alignItems: 'center', marginBottom: 12 },
    repNumber: { fontSize: 56, fontWeight: '800', color: theme.primaryLight },
    repLabel: { fontSize: 14, color: theme.textSecondary, fontWeight: '600' },

    gradeRow: { alignItems: 'center', marginBottom: 12 },
    gradePill: { borderWidth: 2, borderRadius: 20, paddingHorizontal: 16, paddingVertical: 4 },
    gradePillText: { fontSize: 14, fontWeight: '700' },

    messageBox: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: theme.surface, borderRadius: 10, padding: 10, marginBottom: 12 },
    messageText: { color: '#CBD5E1', fontSize: 12, flex: 1 },

    rulesContainer: { backgroundColor: theme.surface, borderRadius: 12, padding: 14, marginBottom: 16 },
    rulesTitle: { fontSize: 14, fontWeight: '600', color: theme.text, marginBottom: 8 },
    ruleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
    ruleText: { flex: 1, fontSize: 12, color: '#CBD5E1' },

    simulateBtn: {
      flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
      backgroundColor: theme.surfaceHover, borderRadius: 12, padding: 14, marginBottom: 8,
    },
    simulateBtnText: { color: '#CBD5E1', fontSize: 14, fontWeight: '600' },
    endBtn: { backgroundColor: theme.primary, borderRadius: 12, padding: 14, marginBottom: 8 },
    endBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  });
}
