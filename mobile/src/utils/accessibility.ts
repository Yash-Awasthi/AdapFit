/**
 * Accessibility utilities for AdapFit
 * 
 * WCAG 2.1 AA requirements:
 * - Text contrast: 4.5:1 for normal text, 3:1 for large text (18pt+)
 * - Touch targets: minimum 44x44 points
 * - All interactive elements need accessibility labels
 * - Screen reader support via accessibilityLabel, accessibilityRole, accessibilityHint
 */

import { Platform } from 'react-native';

// --- Contrast helpers ---

function luminance(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const toLinear = (c: number) => c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

export function contrastRatio(hex1: string, hex2: string): number {
  const l1 = luminance(hex1);
  const l2 = luminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

export function meetsWCAG_AA(foreground: string, background: string, isLargeText = false): boolean {
  const ratio = contrastRatio(foreground, background);
  return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

// --- AdapFit color contrast audit ---
// All text-on-background pairs used in the app

const COLOR_PAIRS = [
  // Primary text
  { fg: '#F8FAFC', bg: '#0F172A', name: 'primary text on dark bg' },
  { fg: '#F8FAFC', bg: '#1E293B', name: 'primary text on card' },
  { fg: '#CBD5E1', bg: '#0F172A', name: 'secondary text on dark bg' },
  { fg: '#CBD5E1', bg: '#1E293B', name: 'secondary text on card' },
  // Muted text
  { fg: '#94A3B8', bg: '#0F172A', name: 'muted text on dark bg' },
  { fg: '#94A3B8', bg: '#1E293B', name: 'muted text on card' },
  { fg: '#8B96AB', bg: '#0F172A', name: 'dimmed text on dark bg' },
  { fg: '#8B96AB', bg: '#1E293B', name: 'dimmed text on card' },
  // Accent colors
  { fg: '#818CF8', bg: '#0F172A', name: 'accent on dark bg' },
  { fg: '#818CF8', bg: '#1E293B', name: 'accent on card' },
  { fg: '#22C55E', bg: '#0F172A', name: 'green on dark bg' },
  { fg: '#EF4444', bg: '#1E293B', name: 'red on card' },
  { fg: '#EAB308', bg: '#1E293B', name: 'yellow on card' },
  // Button text
  { fg: '#FFFFFF', bg: '#4F46E5', name: 'white on indigo button' },
  { fg: '#FFFFFF', bg: '#22C55E', name: 'white on green button' },
];

export interface ContrastReport {
  pair: string;
  ratio: number;
  passes_AA: boolean;
  passes_AA_large: boolean;
}

export function auditContrast(): ContrastReport[] {
  return COLOR_PAIRS.map(({ fg, bg, name }) => {
    const ratio = contrastRatio(fg, bg);
    return {
      pair: name,
      ratio: parseFloat(ratio.toFixed(2)),
      passes_AA: ratio >= 4.5,
      passes_AA_large: ratio >= 3,
    };
  });
}

// --- Accessibility label helpers ---

export function buttonLabel(label: string, hint?: string) {
  return {
    accessible: true,
    accessibilityRole: 'button' as const,
    accessibilityLabel: label,
    ...(hint ? { accessibilityHint: hint } : {}),
  };
}

export function headingLabel(level: 1 | 2 | 3 = 1) {
  return {
    accessible: true,
    accessibilityRole: 'header' as const,
  };
}

export function imageLabel(label: string) {
  return {
    accessible: true,
    accessibilityRole: 'image' as const,
    accessibilityLabel: label,
  };
}

export function adjustableLabel(label: string, current: string, min?: string, max?: string) {
  return {
    accessible: true,
    accessibilityRole: 'adjustable' as const,
    accessibilityLabel: label,
    accessibilityHint: `Currently ${current}${min ? `, min ${min}` : ''}${max ? `, max ${max}` : ''}`,
  };
}

// --- Minimum touch target size (44x44 pt) ---

export const MIN_TOUCH_SIZE = 44;

export function ensureTouchTarget(width: number, height: number): { width: number; height: number } {
  return {
    width: Math.max(width, MIN_TOUCH_SIZE),
    height: Math.max(height, MIN_TOUCH_SIZE),
  };
}
