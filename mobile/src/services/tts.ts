/**
 * Text-to-Speech service for voice-guided workouts.
 * Uses expo-speech on native, silent no-op on web.
 */
import { Platform } from 'react-native';

let Speech: any = null;
try {
  Speech = require('expo-speech');
} catch {}

export interface VoiceOptions {
  pitch?: number;     // 0.0 - 2.0, default 1.0
  rate?: number;      // 0.0 - 2.0, default 1.0
  language?: string;  // BCP-47 tag
  voice?: string;     // specific voice ID
}

const DEFAULT_OPTS: VoiceOptions = {
  pitch: 1.0,
  rate: 0.9,
  language: 'en-US',
};

export function speak(text: string, options?: VoiceOptions) {
  if (!Speech || Platform.OS === 'web') return;
  Speech.speak(text, { ...DEFAULT_OPTS, ...options });
}

export function stopSpeaking() {
  if (!Speech || Platform.OS === 'web') return;
  Speech.stop();
}

export function isAvailable(): boolean {
  return !!(Speech && Platform.OS !== 'web');
}

// --- Workout coaching messages ---

export function announceExercise(name: string, sets: number, reps: string) {
  speak(`Next up: ${name}. ${sets} sets of ${reps}. Let's go!`);
}

export function announceRest(seconds: number) {
  if (seconds >= 60) {
    speak(`Rest for ${Math.floor(seconds / 60)} minutes.`);
  } else {
    speak(`Rest for ${seconds} seconds.`);
  }
}

export function announceSetComplete(setNumber: number, totalSets: number) {
  speak(`Set ${setNumber} of ${totalSets} complete.`);
  if (setNumber === totalSets) {
    speak('All sets done! Great work.');
  } else {
    speak(`Rest now, then do set ${setNumber + 1}.`);
  }
}

export function announceWorkoutComplete(durationMin: number) {
  speak(`Workout complete! You trained for ${durationMin} minutes. Outstanding effort.`);
}

export function announceCountdown(seconds: number) {
  if (seconds <= 3 && seconds > 0) {
    speak(`${seconds}`);
  } else if (seconds === 0) {
    speak('Go!');
  }
}
