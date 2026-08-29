/**
 * Accessibility Utilities for Freebuff Health App
 * WCAG 2.1 AA compliant helpers
 */

import { AccessibilityInfo, Platform } from 'react-native';

// Screen reader label helper
export function a11yLabel(label: string, hint?: string): object {
  const props: any = { accessible: true, accessibilityLabel: label };
  if (hint) props.accessibilityHint = hint;
  return props;
}

// Accessibility role helpers
export const A11Y_ROLES = {
  button: 'button' as const,
  header: 'header' as const,
  link: 'link' as const,
  image: 'image' as const,
  text: 'text' as const,
  adjustable: 'adjustable' as const,
  search: 'search' as const,
  menu: 'menu' as const,
  menuitem: 'menuitem' as const,
  checkbox: 'checkbox' as const,
  radio: 'radio' as const,
  tab: 'tab' as const,
  tablist: 'tablist' as const,
  progressbar: 'progressbar' as const,
  summary: 'summary' as const,
};

// High contrast color overrides
export const HIGH_CONTRAST_COLORS = {
  primary: '#FFFFFF',
  secondary: '#FFFF00',
  background: '#000000',
  surface: '#1A1A1A',
  text: '#FFFFFF',
  textMuted: '#CCCCCC',
  border: '#FFFFFF',
  success: '#00FF00',
  warning: '#FFFF00',
  error: '#FF0000',
  info: '#00FFFF',
};

// Font scale presets
export const FONT_SCALES = {
  small: 0.85,
  normal: 1.0,
  large: 1.15,
  xlarge: 1.3,
  xxlarge: 1.5,
};

export function scaledFontSize(baseSize: number, scale: number = 1.0): number {
  return Math.round(baseSize * scale);
}

// Minimum touch target size (WCAG 2.5.5)
export const MIN_TOUCH_TARGET = 44; // pixels

// Contrast ratio calculator
export function getContrastRatio(hex1: string, hex2: string): number {
  const luminance = (hex: string) => {
    const rgb = hex.replace('#', '').match(/.{2}/g)!.map(h => parseInt(h, 16) / 255);
    const [r, g, b] = rgb.map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const l1 = luminance(hex1);
  const l2 = luminance(hex2);
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}

// Check if contrast meets WCAG AA (4.5:1 for normal text, 3:1 for large text)
export function meetsWCAG_AA(foreground: string, background: string, largeText: boolean = false): boolean {
  const ratio = getContrastRatio(foreground, background);
  return largeText ? ratio >= 3 : ratio >= 4.5;
}

// Screen reader announcement
export async function announceForScreenReader(message: string) {
  if (Platform.OS === 'ios' || Platform.OS === 'android') {
    AccessibilityInfo.announceForAccessibility(message);
  }
}

// Check if screen reader is active
export async function isScreenReaderEnabled(): Promise<boolean> {
  return await AccessibilityInfo.isScreenReaderEnabled();
}

// Check if reduce motion is enabled
export async function isReduceMotionEnabled(): Promise<boolean> {
  return await AccessibilityInfo.isReduceMotionEnabled();
}

// Accessibility settings state
export interface AccessibilitySettings {
  screenReaderEnabled: boolean;
  reduceMotion: boolean;
  highContrast: boolean;
  fontScale: number;
  voiceControlEnabled: boolean;
  hapticFeedback: boolean;
  largeTouchTargets: boolean;
  captioningEnabled: boolean;
}

export const DEFAULT_ACCESSIBILITY_SETTINGS: AccessibilitySettings = {
  screenReaderEnabled: false,
  reduceMotion: false,
  highContrast: false,
  fontScale: FONT_SCALES.normal,
  voiceControlEnabled: false,
  hapticFeedback: true,
  largeTouchTargets: false,
  captioningEnabled: false,
};

// Voice control command mapping
export const VOICE_COMMANDS = {
  'go home': 'navigate_home',
  'go to workout': 'navigate_workout',
  'go to health': 'navigate_health',
  'go to coach': 'navigate_coach',
  'start workout': 'start_workout',
  'log water': 'log_water',
  'log meal': 'log_meal',
  'check heart rate': 'check_hr',
  'start meditation': 'start_meditation',
  'emergency': 'emergency_sos',
};

// Accessibility-friendly motion config
export function getMotionDuration(reduceMotion: boolean, normalMs: number): number {
  return reduceMotion ? 0 : normalMs;
}

// Generate accessibility report for the app
export function generateA11yReport(screenName: string, elements: Array<{ type: string; hasLabel: boolean; hasRole?: boolean }>): {
  screen: string;
  score: number;
  issues: string[];
  passes: string[];
} {
  const issues: string[] = [];
  const passes: string[] = [];
  let score = 100;

  elements.forEach((el, i) => {
    if (!el.hasLabel) {
      issues.push(`Element ${i + 1} (${el.type}) missing accessibilityLabel`);
      score -= 5;
    } else {
      passes.push(`Element ${i + 1} (${el.type}) has accessibilityLabel`);
    }
    if (el.type === 'button' && !el.hasRole) {
      issues.push(`Button ${i + 1} missing accessibilityRole`);
      score -= 3;
    }
  });

  return { screen: screenName, score: Math.max(0, score), issues, passes };
}
