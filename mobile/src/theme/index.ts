/**
 * AdapFit Design System — Premium Health App Theme
 * Inspired by Apple Health, Samsung Health, Oura Ring
 */

// ===== COLORS =====
export const colors = {
  // Primary palette
  primary: '#6366F1',        // Indigo — primary actions
  primaryLight: '#818CF8',
  primaryDark: '#4F46E5',
  primaryMuted: '#6366F120',

  // Background layers. Desaturated slate rather than near-black blue, which
  // pushes saturated accents into a visible halo over a long session.
  bg: {
    deep: '#0C111C',         // Deepest background
    primary: '#111827',       // Main screen bg
    card: '#182031',          // Card surfaces
    elevated: '#1E2739',      // Elevated cards
    input: '#141B2A',         // Input fields
    overlay: '#00000080',     // Modal overlay
  },

  // Surface & borders
  surface: {
    card: '#182031',
    border: '#2A3550',
    divider: '#232D42',
  },

  // Text hierarchy. Every value clears WCAG AA (4.5:1) against bg.deep at
  // body sizes, which constrains how far `muted` can be darkened.
  text: {
    primary: '#F1F5F9',       // Main headings
    secondary: '#CBD5E1',     // Body text
    muted: '#9AA8BF',         // Captions, labels
    inverse: '#0F172A',       // On light backgrounds
    link: '#A5B4FC',          // Links
  },

  // Semantic colors — Health & Activity
  health: {
    heart: '#EF4444',         // Heart rate, BPM
    heartBg: '#EF444420',
    stress: '#F59E0B',        // Stress indicators
    stressBg: '#F59E0B20',
    calm: '#10B981',          // Low stress, good health
    calmBg: '#10B98120',
    energy: '#F97316',        // High energy, calories
    energyBg: '#F9731620',
    sleep: '#8B5CF6',         // Sleep, recovery
    sleepBg: '#8B5CF620',
    activity: '#06B6D4',      // Steps, distance, walking
    activityBg: '#06B6D420',
    nutrition: '#22C55E',     // Food, macros
    nutritionBg: '#22C55E20',
    mental: '#A78BFA',        // Meditation, mindfulness
    mentalBg: '#A78BFA20',
    digital: '#6366F1',       // Digital wellbeing
    digitalBg: '#6366F120',
    danger: '#EF4444',        // Warnings, alerts
    dangerBg: '#EF444420',
    warning: '#F59E0B',
    warningBg: '#F59E0B20',
    success: '#10B981',
    successBg: '#10B98120',
  },

  // Status colors for score rings
  score: {
    excellent: '#10B981',
    good: '#3B82F6',
    fair: '#F59E0B',
    poor: '#F97316',
    critical: '#EF4444',
  },

  // Gradients (arrays for linear-gradient)
  gradient: {
    primary: ['#6366F1', '#8B5CF6'],
    heart: ['#EF4444', '#F97316'],
    calm: ['#10B981', '#06B6D4'],
    sleep: ['#8B5CF6', '#6366F1'],
    energy: ['#F97316', '#F59E0B'],
    dark: ['#0F1629', '#1A2238'],
    card: ['#1A2238', '#1E293B'],
  },
} as const;

// ===== TYPOGRAPHY =====
export const typography = {
  fontFamily: {
    regular: 'System',
    medium: 'System',
    bold: 'System',
    mono: 'System',
  },
  fontSize: {
    xs: 10,
    sm: 12,
    base: 14,
    md: 16,
    lg: 18,
    xl: 22,
    '2xl': 28,
    '3xl': 36,
    '4xl': 48,
    hero: 64,
  },
  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
    extrabold: '800' as const,
  },
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.7,
  },
  // Preset text styles
  heading: {
    hero: { fontSize: 48, fontWeight: '800' as const, lineHeight: 56, color: '#F1F5F9' },
    h1: { fontSize: 28, fontWeight: '700' as const, lineHeight: 34, color: '#F1F5F9' },
    h2: { fontSize: 22, fontWeight: '700' as const, lineHeight: 28, color: '#F1F5F9' },
    h3: { fontSize: 18, fontWeight: '700' as const, lineHeight: 24, color: '#F1F5F9' },
    h4: { fontSize: 16, fontWeight: '600' as const, lineHeight: 22, color: '#CBD5E1' },
  },
  body: {
    lg: { fontSize: 16, fontWeight: '400' as const, lineHeight: 24, color: '#CBD5E1' },
    md: { fontSize: 14, fontWeight: '400' as const, lineHeight: 21, color: '#CBD5E1' },
    sm: { fontSize: 12, fontWeight: '400' as const, lineHeight: 18, color: '#B3BFD2' },
    xs: { fontSize: 11, fontWeight: '400' as const, lineHeight: 16, color: '#9AA8BF' },
  },
  label: {
    lg: { fontSize: 14, fontWeight: '600' as const, color: '#CBD5E1' },
    md: { fontSize: 12, fontWeight: '600' as const, color: '#B3BFD2' },
    sm: { fontSize: 11, fontWeight: '600' as const, color: '#9AA8BF' },
    tag: { fontSize: 10, fontWeight: '700' as const, textTransform: 'uppercase' as const, letterSpacing: 0.5 },
  },
  metric: {
    hero: { fontSize: 64, fontWeight: '800' as const, color: '#F1F5F9' },
    large: { fontSize: 36, fontWeight: '700' as const, color: '#F1F5F9' },
    medium: { fontSize: 24, fontWeight: '700' as const, color: '#F1F5F9' },
    small: { fontSize: 18, fontWeight: '600' as const, color: '#F1F5F9' },
  },
} as const;

// ===== SPACING =====
export const spacing = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
  '4xl': 40,
  '5xl': 48,
  '6xl': 64,
  // Screen-level
  screenPadding: 20,
  cardPadding: 16,
  sectionGap: 16,
} as const;

// ===== BORDER RADIUS =====
export const radius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  '2xl': 24,
  full: 9999,
  // Presets
  card: 16,
  pill: 9999,
  button: 12,
  input: 12,
  avatar: 9999,
  badge: 8,
  ring: 9999,
} as const;

// ===== SHADOWS =====
export const shadows = {
  none: {},
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 10,
  },
  glow: (color: string) => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 8,
  }),
} as const;

// ===== PRESET COMPONENT STYLES =====
export const presets = {
  // Card container
  card: {
    backgroundColor: colors.bg.card,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },

  // Elevated card
  elevatedCard: {
    backgroundColor: colors.bg.elevated,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    borderWidth: 1,
    borderColor: colors.surface.border,
    ...shadows.md,
  },

  // Section header
  sectionHeader: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    gap: spacing.sm,
    marginBottom: spacing.md,
  },

  // Pill badge
  pill: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radius.pill,
  },

  // Active pill
  pillActive: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },

  // Primary button
  buttonPrimary: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    gap: spacing.sm,
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.lg,
    borderRadius: radius.button,
  },

  // Secondary button
  buttonSecondary: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    gap: spacing.sm,
    backgroundColor: colors.bg.elevated,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.lg,
    borderRadius: radius.button,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },

  // Score ring container
  scoreRing: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
    borderWidth: 4,
  },

  // Progress bar
  progressBar: {
    height: 6,
    backgroundColor: colors.surface.divider,
    borderRadius: 3,
    overflow: 'hidden' as const,
  },

  progressFill: {
    height: '100%' as const,
    borderRadius: 3,
  },

  // Glassmorphism card
  glassCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 20,
    padding: 16,
  },

  // Gradient overlay for cards
  gradientOverlay: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 16,
    overflow: 'hidden' as const,
  },

  // Achievement badge
  badge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
    borderWidth: 2,
  },

  // Health metric card
  metricCard: {
    flex: 1,
    backgroundColor: colors.bg.card,
    borderRadius: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.surface.border,
    alignItems: 'center' as const,
  },
} as const;

// ===== HELPER FUNCTIONS =====
export function getScoreColor(score: number): string {
  if (score >= 80) return colors.score.excellent;
  if (score >= 60) return colors.score.good;
  if (score >= 40) return colors.score.fair;
  if (score >= 20) return colors.score.poor;
  return colors.score.critical;
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Fair';
  if (score >= 20) return 'Poor';
  return 'Critical';
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function formatDistance(km: number): string {
  return km < 1 ? `${(km * 1000).toFixed(0)}m` : `${km.toFixed(1)}km`;
}

// ===== GLASSMORPHISM COMPONENTS =====
// Premium frosted glass effects inspired by iOS 26 Liquid Glass
export const glass = {
  // Light glass — for cards over colored backgrounds
  light: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderRadius: 20,
  },
  // Dark glass — for overlays and modals
  dark: {
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
    borderRadius: 20,
  },
  // Primary glass — with brand color tint
  primary: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
    borderRadius: 20,
  },
  // Health glass — color-coded by health domain
  health: {
    heart: { backgroundColor: 'rgba(239, 68, 68, 0.12)', borderWidth: 1, borderColor: 'rgba(239, 68, 68, 0.2)', borderRadius: 20 },
    calm: { backgroundColor: 'rgba(16, 185, 129, 0.12)', borderWidth: 1, borderColor: 'rgba(16, 185, 129, 0.2)', borderRadius: 20 },
    sleep: { backgroundColor: 'rgba(139, 92, 246, 0.12)', borderWidth: 1, borderColor: 'rgba(139, 92, 246, 0.2)', borderRadius: 20 },
    energy: { backgroundColor: 'rgba(249, 115, 22, 0.12)', borderWidth: 1, borderColor: 'rgba(249, 115, 22, 0.2)', borderRadius: 20 },
    mental: { backgroundColor: 'rgba(168, 85, 247, 0.12)', borderWidth: 1, borderColor: 'rgba(168, 85, 247, 0.2)', borderRadius: 20 },
    nutrition: { backgroundColor: 'rgba(234, 179, 8, 0.12)', borderWidth: 1, borderColor: 'rgba(234, 179, 8, 0.2)', borderRadius: 20 },
  },
  // Score ring glass
  scoreRing: (color: string) => ({
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    borderWidth: 3,
    borderColor: color + '40',
    borderRadius: 999,
  }),
  // Tab bar glass
  tabBar: {
    backgroundColor: 'rgba(26, 34, 56, 0.85)',
    borderTopWidth: 0.5,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  // Pill / chip glass
  pill: (active: boolean = false) => ({
    backgroundColor: active ? colors.primary + '30' : 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: active ? colors.primary + '50' : 'rgba(255, 255, 255, 0.08)',
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 8,
  }),
} as const;

// ===== ANIMATION PRESETS =====
export const animations = {
  fadeIn: { duration: 300, useNativeDriver: true },
  slideUp: { duration: 400, useNativeDriver: true },
  spring: { tension: 40, friction: 7, useNativeDriver: true },
  bounce: { tension: 100, friction: 8, useNativeDriver: true },
} as const;

// ===== ACCESSIBILITY =====
export const accessibility = {
  minTouchTarget: 44,
  minContrastRatio: 4.5,
  focusRing: { width: 2, color: colors.primary, borderRadius: 4 },
  largeText: { fontSize: 18, lineHeight: 26 },
  extraLargeText: { fontSize: 24, lineHeight: 32 },
} as const;
