import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Animated,
  Easing,
  Platform,
} from 'react-native';
import { Mic, MicOff, Check, X, Sparkles, Volume2 } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { useAudioRecorder, RecordingPresets, requestRecordingPermissionsAsync } from 'expo-audio';
import { File } from 'expo-file-system';
import { api } from '../services/api';
import { speak } from '../services/tts';
import { useTheme } from '../services/theme';

interface VoiceLoggerModalProps {
  visible: boolean;
  onClose: () => void;
  onSetLogged: (setDetails: {
    exercise_name?: string | null;
    weight_kg?: number | null;
    reps?: number | null;
    rpe?: number | null;
  }) => void;
}

const PRESET_PHRASES = [
  '3 sets of 10 bench press at 80 kilos RPE 8',
  '4 reps squat at 100 kg RPE 9',
  '12 reps dumbbell curl at 16 kilos RPE 7',
];

// Soundwave bar component
function SoundwaveBar({ index, isActive }: { index: number; isActive: boolean }) {
  const { theme } = useTheme();
  const animValue = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    if (isActive) {
      const loop = Animated.loop(
        Animated.sequence([
          Animated.timing(animValue, {
            toValue: 0.3 + Math.random() * 0.7,
            duration: 150 + Math.random() * 200,
            easing: Easing.bezier(0.4, 0, 0.2, 1),
            useNativeDriver: false,
          }),
          Animated.timing(animValue, {
            toValue: 0.2 + Math.random() * 0.3,
            duration: 150 + Math.random() * 200,
            easing: Easing.bezier(0.4, 0, 0.2, 1),
            useNativeDriver: false,
          }),
        ])
      );
      loop.start();
      return () => loop.stop();
    } else {
      Animated.timing(animValue, {
        toValue: 0.15,
        duration: 300,
        useNativeDriver: false,
      }).start();
    }
  }, [isActive]);

  const height = animValue.interpolate({
    inputRange: [0, 1],
    outputRange: [4, 40],
  });

  return (
    <Animated.View
      style={[
        styles.waveBar,
        {
          height,
          backgroundColor: isActive ? theme.primaryLight : theme.border,
        },
      ]}
    />
  );
}

export function VoiceLoggerModal({ visible, onClose, onSetLogged }: VoiceLoggerModalProps) {
  const { theme } = useTheme();
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [parsedResult, setParsedResult] = useState<any | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Pulse animation for recording button
  useEffect(() => {
    if (isRecording) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 600,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 600,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();

      durationInterval.current = setInterval(() => {
        setRecordingDuration((d) => d + 1);
      }, 1000);

      return () => {
        pulse.stop();
        if (durationInterval.current) clearInterval(durationInterval.current);
      };
    } else {
      pulseAnim.setValue(1);
      setRecordingDuration(0);
    }
  }, [isRecording]);

  async function toggleRecording() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setErrorText(null);
    if (isRecording) {
      // Stop and transcribe
      setIsRecording(false);
      if (durationInterval.current) clearInterval(durationInterval.current);
      setTranscribing(true);
      try {
        await recorder.stop();
        const uri = recorder.uri;
        if (uri) {
          const file = new File(uri);
          const b64 = await file.base64();
          const stt = await api.transcribeAudio(b64, 'default');
          if (stt?.text?.trim()) {
            setInputText(stt.text.trim());
            await handleParse(stt.text.trim());
          } else {
            setErrorText('Could not hear you — try again or type instead.');
          }
        } else {
          setErrorText('Recording was empty — try again.');
        }
      } catch (err) {
        console.warn('Transcription failed', err);
        setErrorText('Transcription failed — try again or type instead.');
      }
      setTranscribing(false);
    } else {
      const perm = await requestRecordingPermissionsAsync();
      if (!perm.granted) {
        setErrorText('Microphone permission is required for voice logging.');
        return;
      }
      setIsRecording(true);
      try {
        await recorder.prepareToRecordAsync();
        recorder.record();
      } catch (err) {
        console.warn('Record start failed', err);
        setIsRecording(false);
        setErrorText('Could not start recording.');
      }
    }
  }

  async function handleParse(text: string) {
    if (!text.trim()) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setLoading(true);
    setErrorText(null);
    try {
      const res = await api.parseVoiceWorkout(text);
      setParsedResult(res);
      if (res.voice_feedback) {
        speak(res.voice_feedback);
      }
    } catch (err) {
      console.warn('Voice parse failed', err);
      setErrorText('Could not parse that — try the preset phrases.');
    }
    setLoading(false);
  }

  function handleConfirm() {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    if (parsedResult?.parsed_set) {
      onSetLogged(parsedResult.parsed_set);
    }
    setParsedResult(null);
    setInputText('');
    setIsRecording(false);
    onClose();
  }

  function formatDuration(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={[styles.overlay, { backgroundColor: `${theme.background}D9` }]}>
        <View style={[styles.card, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerTitle}>
              <Mic size={20} color={theme.primaryLight} />
              <Text style={[styles.title, { color: theme.text }]}>Voice Workout Logger</Text>
            </View>
            <TouchableOpacity onPress={onClose}>
              <X size={20} color={theme.textSecondary} />
            </TouchableOpacity>
          </View>

          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Speak or type: "3x10 bench press at 80kg RPE 8"
          </Text>

          {/* Soundwave Visualizer */}
          <View style={[styles.waveContainer, { backgroundColor: theme.background }]}>
            {Array.from({ length: 20 }).map((_, i) => (
              <SoundwaveBar key={i} index={i} isActive={isRecording} />
            ))}
          </View>

          {/* Recording Button */}
          <View style={styles.recordRow}>
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <TouchableOpacity
                style={[
                  styles.recordBtn,
                  { backgroundColor: theme.primary },
                  isRecording && { backgroundColor: theme.danger },
                  transcribing && { backgroundColor: theme.border },
                ]}
                onPress={toggleRecording}
                disabled={transcribing}
              >
                {isRecording ? (
                  <MicOff size={24} color="#fff" />
                ) : (
                  <Mic size={24} color="#fff" />
                )}
              </TouchableOpacity>
            </Animated.View>
            <Text style={[styles.recordStatus, { color: theme.textSecondary }]}>
              {transcribing
                ? 'Transcribing…'
                : isRecording
                  ? `Recording ${formatDuration(recordingDuration)}...`
                  : 'Tap to start recording'}
            </Text>
          </View>

          {/* Text Input */}
          <TextInput
            style={[styles.input, { backgroundColor: theme.background, color: theme.text, borderColor: theme.border }]}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Or type your set here..."
            placeholderTextColor={theme.textMuted}
            multiline
          />

          {/* Presets */}
          <View style={styles.presetContainer}>
            <Text style={[styles.presetLabel, { color: theme.textMuted }]}>Quick Presets:</Text>
            {PRESET_PHRASES.map((phrase, i) => (
              <TouchableOpacity
                key={i}
                style={[styles.presetChip, { backgroundColor: theme.background }]}
                onPress={() => {
                  setInputText(phrase);
                  handleParse(phrase);
                }}
              >
                <Sparkles size={12} color={theme.primaryLight} />
                <Text style={[styles.presetText, { color: theme.textSecondary }]}>{phrase}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {errorText && (
            <View style={[styles.errorBox, { backgroundColor: `${theme.danger}1F` }]}>
              <X size={14} color={theme.danger} />
              <Text style={[styles.errorText, { color: theme.danger }]}>{errorText}</Text>
            </View>
          )}

          {/* Parse Button */}
          <TouchableOpacity
            style={[
              styles.parseBtn,
              { backgroundColor: theme.primary },
              (!inputText.trim() || loading || transcribing) && styles.parseBtnDisabled,
            ]}
            onPress={() => handleParse(inputText)}
            disabled={loading || transcribing || !inputText.trim()}
          >
            {loading ? (
              <Animated.View style={styles.loadingDots}>
                {[0, 1, 2].map((i) => (
                  <Animated.View key={i} style={[styles.dot, { opacity: 0.4 }]} />
                ))}
              </Animated.View>
            ) : (
              <Text style={styles.parseBtnText}>Parse Voice Telemetry</Text>
            )}
          </TouchableOpacity>

          {/* Parsed Result */}
          {parsedResult?.parsed_set && (
            <View style={[styles.resultBox, { backgroundColor: theme.background, borderLeftColor: theme.success }]}>
              <View style={styles.resultHeaderRow}>
                <Text style={[styles.resultHeader, { color: theme.text }]}>Parsed Set:</Text>
                <TouchableOpacity
                  style={styles.playBtn}
                  onPress={() => {
                    const ps = parsedResult.parsed_set;
                    speak(
                      `Logged ${ps.reps || '?'} reps of ${ps.exercise_name || 'exercise'} at ${ps.weight_kg || '?'} kilograms, RPE ${ps.rpe || '?'}`
                    );
                  }}
                >
                  <Volume2 size={16} color={theme.primaryLight} />
                </TouchableOpacity>
              </View>
              <Text style={[styles.resultText, { color: theme.textSecondary }]}>
                Exercise: {parsedResult.parsed_set.exercise_name ?? 'Current'}
              </Text>
              <Text style={[styles.resultText, { color: theme.textSecondary }]}>
                Weight: {parsedResult.parsed_set.weight_kg ?? '--'} kg
              </Text>
              <Text style={[styles.resultText, { color: theme.textSecondary }]}>
                Reps: {parsedResult.parsed_set.reps ?? '--'}
              </Text>
              <Text style={[styles.resultText, { color: theme.textSecondary }]}>
                RPE: {parsedResult.parsed_set.rpe ?? '--'}
              </Text>
              <Text style={[styles.confidenceText, { color: theme.success }]}>
                Confidence: {((parsedResult.confidence || 0) * 100).toFixed(0)}%
              </Text>

              <TouchableOpacity style={[styles.confirmBtn, { backgroundColor: theme.success }]} onPress={handleConfirm}>
                <Check size={18} color="#0F172A" />
                <Text style={styles.confirmBtnText}>Apply & Complete Set</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  card: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    borderTopWidth: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  headerTitle: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontSize: 18, fontWeight: '700' },
  subtitle: { fontSize: 13, marginBottom: 16 },

  // Soundwave
  waveContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
    height: 50,
    marginBottom: 16,
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  waveBar: {
    width: 4,
    borderRadius: 2,
    minHeight: 4,
  },

  // Recording
  recordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  errorBox: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    borderRadius: 10, padding: 10, marginBottom: 10,
  },
  errorText: { fontSize: 12, flex: 1 },

  recordBtn: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordStatus: {
    fontSize: 13,
    flex: 1,
  },

  // Input
  input: {
    borderRadius: 12,
    padding: 14,
    fontSize: 14,
    borderWidth: 1,
    minHeight: 60,
    marginBottom: 12,
  },

  // Presets
  presetContainer: { marginBottom: 16 },
  presetLabel: { fontSize: 12, marginBottom: 6 },
  presetChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 6,
  },
  presetText: { fontSize: 12 },

  // Parse button
  parseBtn: {
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  parseBtnDisabled: {
    opacity: 0.5,
  },
  parseBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  loadingDots: { flexDirection: 'row', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#fff' },

  // Result
  resultBox: {
    borderRadius: 12,
    padding: 14,
    borderLeftWidth: 4,
    marginTop: 8,
  },
  resultHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  resultHeader: { fontSize: 14, fontWeight: '700' },
  playBtn: { padding: 4 },
  resultText: { fontSize: 13, marginBottom: 2 },
  confidenceText: { fontSize: 11, marginTop: 4, fontWeight: '600' },
  confirmBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 8,
    padding: 12,
    marginTop: 10,
  },
  confirmBtnText: { color: '#0F172A', fontSize: 14, fontWeight: '700' },
});
