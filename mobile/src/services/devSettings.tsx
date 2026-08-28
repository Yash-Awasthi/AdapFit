/**
 * Dev Tools settings — bring-your-own LLM key/endpoint/model, and a
 * reduce-motion switch that screens can check before firing entrance
 * animations. Session-only: this does not persist across app restarts.
 */
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { FadeInDown } from 'react-native-reanimated';

export type LlmProvider = 'gemini' | 'groq' | 'custom';

export interface LlmOverride {
  provider: LlmProvider;
  apiKey: string;
  model?: string;
  baseUrl?: string;
}

interface DevSettingsState {
  llmOverride: LlmOverride | null;
  setLlmOverride: (o: LlmOverride | null) => void;
  reduceMotion: boolean;
  setReduceMotion: (v: boolean) => void;
}

const DevSettingsContext = createContext<DevSettingsState>({
  llmOverride: null,
  setLlmOverride: () => {},
  reduceMotion: false,
  setReduceMotion: () => {},
});

export function DevSettingsProvider({ children }: { children: ReactNode }) {
  const [llmOverride, setLlmOverride] = useState<LlmOverride | null>(null);
  const [reduceMotion, setReduceMotion] = useState(false);

  return (
    <DevSettingsContext.Provider value={{ llmOverride, setLlmOverride, reduceMotion, setReduceMotion }}>
      {children}
    </DevSettingsContext.Provider>
  );
}

export function useDevSettings() {
  return useContext(DevSettingsContext);
}

/** Entrance animation honoring the reduce-motion switch — pass a stagger delay in ms. */
export function useEnterAnimation() {
  const { reduceMotion } = useDevSettings();
  return (delayMs = 0) => (reduceMotion ? undefined : FadeInDown.duration(280).delay(delayMs));
}
