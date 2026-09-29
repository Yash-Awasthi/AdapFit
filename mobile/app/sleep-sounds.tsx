/**
 * Overnight snoring and noise check. The phone listens to sound levels only;
 * the recording file exists because Android needs one to meter the microphone,
 * and it is deleted as soon as listening stops.
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, Linking, StatusBar } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AudioModule, RecordingPresets, setAudioModeAsync, useAudioRecorder } from 'expo-audio';
import { File } from 'expo-file-system';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import { colors, spacing, radius } from '../src/theme';
import { postJson } from '../src/services/http';
import { SleepSoundDetector } from '../src/services/sleepSoundDetector';
import { localDay } from '../src/utils/date';

const PENDING_FILE_KEY = 'adapfit.sleepAudio.file';
const KEEP_AWAKE_TAG = 'sleep-sounds';
// Levels only are used; a small mono file keeps a full night to tens of megabytes.
const OPTIONS = {
  ...RecordingPresets.LOW_QUALITY,
  sampleRate: 8000,
  numberOfChannels: 1,
  bitRate: 16000,
  isMeteringEnabled: true,
};

type Result = {
  status?: string;
  message?: string;
  snoring?: { total_events: number };
  apnea_risk?: { risk_level: string; recommendation?: string };
  insights?: string[];
};

function deleteFile(uri: string | null | undefined) {
  if (!uri) return;
  try {
    const f = new File(uri);
    if (f.exists) f.delete();
  } catch {}
}

export default function SleepSoundsScreen() {
  const router = useRouter();
  const recorder = useAudioRecorder(OPTIONS);
  const detector = useRef<SleepSoundDetector | null>(null);
  const [listening, setListening] = useState(false);
  const [dimmed, setDimmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [minutes, setMinutes] = useState(0);

  useEffect(() => {
    // A recording left behind by a crash or a killed app is removed on the next visit.
    AsyncStorage.getItem(PENDING_FILE_KEY).then((uri) => {
      deleteFile(uri);
      AsyncStorage.removeItem(PENDING_FILE_KEY);
    }).catch(() => {});
    return () => { deactivateKeepAwake(KEEP_AWAKE_TAG); };
  }, []);

  useEffect(() => {
    if (!listening) return;
    let lastMinute = 0;
    const tick = setInterval(() => {
      const st = recorder.getStatus();
      if (!st.isRecording || st.metering == null) return;
      const now = Date.now();
      detector.current?.push(now, st.metering);
      const m = Math.floor(st.durationMillis / 60000);
      if (m !== lastMinute) setMinutes((lastMinute = m));
    }, 250);
    return () => clearInterval(tick);
  }, [listening, recorder]);

  const start = async () => {
    const perm = await AudioModule.requestRecordingPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Microphone needed', 'Allow the microphone to listen for snoring.', [
        { text: 'Cancel' }, { text: 'Open settings', onPress: () => Linking.openSettings() },
      ]);
      return;
    }
    try {
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
      if (recorder.uri) await AsyncStorage.setItem(PENDING_FILE_KEY, recorder.uri);
      await activateKeepAwakeAsync(KEEP_AWAKE_TAG);
    } catch {
      Alert.alert('Could not start', 'The microphone is in use by another app.');
      return;
    }
    detector.current = new SleepSoundDetector();
    setResult(null);
    setMinutes(0);
    setListening(true);
    setDimmed(true);
  };

  const stop = async () => {
    setListening(false);
    setDimmed(false);
    setBusy(true);
    deactivateKeepAwake(KEEP_AWAKE_TAG);
    const uri = recorder.uri;
    try {
      await recorder.stop();
    } catch {}
    deleteFile(uri);
    await AsyncStorage.removeItem(PENDING_FILE_KEY).catch(() => {});
    await setAudioModeAsync({ allowsRecording: false }).catch(() => {});

    const report = detector.current?.report();
    detector.current = null;
    if (!report || report.duration_minutes < 1) {
      setBusy(false);
      setResult({ status: 'insufficient_data', message: 'Less than a minute was heard, so there is nothing to score.' });
      return;
    }
    const today = new Date();
    const date = localDay(today);
    const r = await postJson<{ data: Result }>('/sleep-audio/analyze', { user_id: 'me', audio_data: { ...report, date } });
    setBusy(false);
    setResult(r?.data ?? { status: 'error', message: `The server could not be reached. Heard ${report.duration_minutes} min, ${report.snoring_events.length} snoring stretches.` });
  };

  if (dimmed) {
    return (
      <TouchableOpacity activeOpacity={1} style={s.black} onPress={() => setDimmed(false)} accessibilityLabel="Listening. Tap to show controls.">
        <StatusBar hidden />
        <Text style={s.dimText}>Listening · {minutes} min · tap to show</Text>
      </TouchableOpacity>
    );
  }

  return (
    <View style={s.container}>
      <TouchableOpacity onPress={() => router.back()} style={s.back} accessibilityLabel="Back" disabled={listening}>
        <Ionicons name="chevron-back" size={26} color={listening ? colors.text.muted : colors.text.primary} />
      </TouchableOpacity>
      <Text style={s.title}>Sleep sounds</Text>

      {!listening && !result && (
        <View style={s.body}>
          <Text style={s.p}>Put the phone on charge near your bed, screen up, and start before you sleep. It listens for snoring and loud noises.</Text>
          <Text style={s.p}>The screen goes black but stays on: Android pauses listening when the screen turns off, so do not lock the phone. Stop when you wake up.</Text>
          <Text style={s.p}>Only sound levels are used. The recording is deleted when you stop, and no audio leaves the phone.</Text>
          <Text style={s.p}>This does not detect breathing pauses and is not a sleep apnoea test.</Text>
        </View>
      )}

      {listening && (
        <View style={s.body}>
          <Text style={s.big}>{minutes}<Text style={s.unit}> min</Text></Text>
          <Text style={s.p}>Listening. Keep the screen on; tap the black screen to see this again.</Text>
        </View>
      )}

      {result && (
        <View style={s.body}>
          {result.status === 'scored' ? (
            <>
              <Text style={s.big}>{result.snoring?.total_events ?? 0}<Text style={s.unit}> snoring stretches</Text></Text>
              {(result.insights ?? []).map((t) => <Text key={t} style={s.p}>{t}</Text>)}
              {result.apnea_risk?.recommendation ? <Text style={s.p}>{result.apnea_risk.recommendation}</Text> : null}
            </>
          ) : (
            <Text style={s.p}>{result.message ?? 'Nothing to score.'}</Text>
          )}
        </View>
      )}

      <View style={s.actions}>
        {busy ? <ActivityIndicator color={colors.primary} /> : listening ? (
          <>
            <TouchableOpacity style={[s.button, s.stop]} onPress={stop} accessibilityRole="button"><Text style={s.buttonText}>Stop</Text></TouchableOpacity>
            <TouchableOpacity onPress={() => setDimmed(true)} accessibilityRole="button"><Text style={s.link}>Black screen</Text></TouchableOpacity>
          </>
        ) : (
          <TouchableOpacity style={s.button} onPress={start} accessibilityRole="button">
            <Text style={s.buttonText}>{result ? 'Listen again' : 'Start listening'}</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep, padding: spacing.lg, paddingTop: 56 },
  black: { flex: 1, backgroundColor: '#000', justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 40 },
  dimText: { color: '#333', fontSize: 13 },
  back: { position: 'absolute', top: 48, left: 12, padding: 8, zIndex: 1 },
  title: { fontSize: 26, fontWeight: '800', color: colors.text.primary, textAlign: 'center', marginBottom: spacing.xl },
  body: { gap: 12, alignItems: 'center' },
  p: { fontSize: 14, color: colors.text.secondary, lineHeight: 20, textAlign: 'center' },
  big: { fontSize: 56, fontWeight: '800', color: colors.text.primary, textAlign: 'center' },
  unit: { fontSize: 20, color: colors.text.muted },
  actions: { position: 'absolute', bottom: 48, left: spacing.lg, right: spacing.lg, alignItems: 'center', gap: 16 },
  button: { alignSelf: 'stretch', backgroundColor: colors.primary, paddingVertical: 18, borderRadius: radius.lg, alignItems: 'center' },
  stop: { backgroundColor: colors.health.danger },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '800' },
  link: { color: colors.text.muted, fontSize: 15 },
});
