/**
 * AdapFit Theme System
 * Dark/light mode combined with a selectable accent palette.
 * Preference persists across launches; initial value follows the OS setting.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Appearance } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type AccentName = 'indigo' | 'emerald' | 'rose' | 'amber' | 'cyan';

const ACCENTS: Record<AccentName, { primary: string; primaryLight: string }> = {
  indigo: { primary: '#6366F1', primaryLight: '#818CF8' },
  emerald: { primary: '#059669', primaryLight: '#34D399' },
  rose: { primary: '#E11D48', primaryLight: '#FB7185' },
  amber: { primary: '#D97706', primaryLight: '#FBBF24' },
  cyan: { primary: '#0891B2', primaryLight: '#22D3EE' },
};

const DARK_MODE_KEY = 'adapfit:isDark';
const ACCENT_KEY = 'adapfit:accent';

function buildTheme(isDark: boolean, accent: AccentName) {
  const a = ACCENTS[accent];
  return isDark
    ? {
        // Kept in step with the static tokens in src/theme so screens built
        // on either system sit on the same surfaces.
        background: '#0C111C',
        surface: '#182031',
        surfaceHover: '#2A3550',
        border: '#2A3550',
        text: '#F1F5F9',
        textSecondary: '#CBD5E1',
        textMuted: '#9AA8BF',
        primary: a.primary,
        primaryLight: a.primaryLight,
        primaryBg: `${a.primary}26`,
        success: '#22C55E',
        warning: '#EAB308',
        danger: '#EF4444',
        orange: '#F97316',
      }
    : {
        // Warm, slightly tinted neutrals instead of stark white — easier on the eye,
        // still enough contrast against dark text (WCAG AA at body-text sizes).
        background: '#F3F1EC',
        surface: '#FBFAF7',
        surfaceHover: '#EDEAE2',
        border: '#E2DFD5',
        text: '#25291F',
        textSecondary: '#585B4F',
        textMuted: '#8A8D80',
        primary: a.primary,
        primaryLight: a.primaryLight,
        primaryBg: `${a.primary}1A`,
        success: '#15803D',
        warning: '#A16207',
        danger: '#B91C1C',
        orange: '#C2410C',
      };
}

export const CARD_SHADOW = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 6 },
  shadowOpacity: 0.25,
  shadowRadius: 12,
  elevation: 6,
} as const;

export type Theme = ReturnType<typeof buildTheme>;

const ThemeContext = createContext<{
  theme: Theme;
  isDark: boolean;
  accent: AccentName;
  toggle: () => void;
  setAccent: (a: AccentName) => void;
  accents: typeof ACCENTS;
}>({
  theme: buildTheme(true, 'indigo'),
  isDark: true,
  accent: 'indigo',
  toggle: () => {},
  setAccent: () => {},
  accents: ACCENTS,
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(Appearance.getColorScheme() !== 'light');
  const [accent, setAccentState] = useState<AccentName>('indigo');

  useEffect(() => {
    (async () => {
      const [savedDark, savedAccent] = await Promise.all([
        AsyncStorage.getItem(DARK_MODE_KEY),
        AsyncStorage.getItem(ACCENT_KEY),
      ]);
      if (savedDark != null) setIsDark(savedDark === '1');
      if (savedAccent && savedAccent in ACCENTS) setAccentState(savedAccent as AccentName);
    })();
  }, []);

  function toggle() {
    setIsDark((prev) => {
      const next = !prev;
      AsyncStorage.setItem(DARK_MODE_KEY, next ? '1' : '0');
      return next;
    });
  }

  function setAccent(a: AccentName) {
    setAccentState(a);
    AsyncStorage.setItem(ACCENT_KEY, a);
  }

  return (
    <ThemeContext.Provider
      value={{
        theme: buildTheme(isDark, accent),
        isDark,
        accent,
        toggle,
        setAccent,
        accents: ACCENTS,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
