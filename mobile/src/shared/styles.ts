/**
 * AdapFit Design System — consistent tokens across all screens.
 * Based on enterprise patterns from school-teacher-app.
 */

import { StyleSheet } from "react-native";

export const COLORS = {
  // Backgrounds
  background: "#0F172A",
  surface: "#1E293B",
  surfaceElevated: "#334155",
  card: "#1E293B",

  // Text
  text: "#F8FAFC",
  textSecondary: "#94A3B8",
  textMuted: "#64748B",

  // Primary
  accent: "#818CF8",
  accentBg: "#1E1B4B",
  accentMuted: "#4F46E5",

  // Accent
  gold: "#F59E0B",
  goldBg: "#78350F",

  // Status
  success: "#10B981",
  successBg: "#064E3B",
  warning: "#F59E0B",
  warningBg: "#78350F",
  danger: "#EF4444",
  dangerBg: "#7F1D1D",
  info: "#3B82F6",
  infoBg: "#1E3A5F",

  // Borders
  border: "#334155",
  borderLight: "#475569",

  // Tab bar
  tabBar: "#0F172A",
  tabBarBorder: "#1E293B",

  // Input
  input: "#1E293B",
  inputBorder: "#334155",
  inputFocus: "#818CF8",

  // Overlay
  overlay: "rgba(0, 0, 0, 0.6)",
} as const;

export const STATUS_COLORS = {
  present: "#22C55E",
  absent: "#EF4444",
  leave: "#F59E0B",
} as const;

const AVATAR_COLORS = [
  { bg: "#312E81", text: "#818CF8" },
  { bg: "#1E3A5F", text: "#60A5FA" },
  { bg: "#064E3B", text: "#34D399" },
  { bg: "#78350F", text: "#FBBF24" },
  { bg: "#7F1D1D", text: "#FCA5A5" },
  { bg: "#3B0764", text: "#C084FC" },
];

export const avatarColor = (name?: string) =>
  AVATAR_COLORS[(name?.charCodeAt(0) || 0) % AVATAR_COLORS.length];

export const shared = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
    backgroundColor: COLORS.background,
  },
  loadingText: {
    fontSize: 13,
    color: COLORS.textMuted,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: COLORS.text,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: COLORS.text,
    marginBottom: 10,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  cardRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    alignSelf: "flex-start",
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "600",
  },
  primaryBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: "center",
  },
  primaryBtnText: {
    color: COLORS.text,
    fontSize: 15,
    fontWeight: "600",
  },
  secondaryBtn: {
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  secondaryBtnText: {
    color: COLORS.textSecondary,
    fontSize: 15,
    fontWeight: "600",
  },
  input: {
    backgroundColor: COLORS.input,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.inputBorder,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: COLORS.text,
    fontSize: 14,
  },
  inputFocused: {
    borderColor: COLORS.inputFocus,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: COLORS.textSecondary,
    marginBottom: 6,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: 12,
  },
  emptyState: {
    alignItems: "center",
    padding: 32,
    gap: 8,
  },
  emptyText: {
    color: COLORS.textMuted,
    fontSize: 14,
  },
  shimmer: {
    backgroundColor: COLORS.surface,
    borderRadius: 8,
  },
});
