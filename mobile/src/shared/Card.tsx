/**
 * Card — reusable card component with consistent styling.
 */

import React from "react";
import { View, Text, StyleSheet, ViewStyle, TouchableOpacity } from "react-native";
import { COLORS } from "./styles";

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
}

export function Card({ children, style, onPress }: CardProps) {
  if (onPress) {
    return (
      <TouchableOpacity style={[styles.card, style]} onPress={onPress} activeOpacity={0.7}>
        {children}
      </TouchableOpacity>
    );
  }
  return <View style={[styles.card, style]}>{children}</View>;
}

interface StatCardProps {
  value: string | number;
  label: string;
  icon?: React.ReactNode;
  color?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
}

export function StatCard({ value, label, icon, color = COLORS.accent, trend, trendValue }: StatCardProps) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <View style={styles.statHeader}>
        {icon}
        {trend && (
          <Text style={[styles.trend, { color: trend === "up" ? COLORS.success : trend === "down" ? COLORS.danger : COLORS.textMuted }]}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
          </Text>
        )}
      </View>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

interface ProgressCardProps {
  title: string;
  current: number;
  target: number;
  color?: string;
  unit?: string;
}

export function ProgressCard({ title, current, target, color = COLORS.accent, unit = "" }: ProgressCardProps) {
  const pct = Math.min(100, (current / target) * 100);
  return (
    <View style={styles.card}>
      <View style={styles.progressHeader}>
        <Text style={styles.progressTitle}>{title}</Text>
        <Text style={[styles.progressValue, { color }]}>
          {Math.round(current)}{unit} / {target}{unit}
        </Text>
      </View>
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

interface ListItemProps {
  icon?: React.ReactNode;
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  onPress?: () => void;
}

export function ListItem({ icon, title, subtitle, right, onPress }: ListItemProps) {
  const content = (
    <View style={styles.listItem}>
      {icon && <View style={styles.listIcon}>{icon}</View>}
      <View style={styles.listContent}>
        <Text style={styles.listTitle}>{title}</Text>
        {subtitle && <Text style={styles.listSubtitle}>{subtitle}</Text>}
      </View>
      {right}
    </View>
  );

  if (onPress) {
    return <TouchableOpacity onPress={onPress} activeOpacity={0.7}>{content}</TouchableOpacity>;
  }
  return content;
}

interface BadgeProps {
  text: string;
  color?: string;
  bgColor?: string;
}

export function Badge({ text, color = COLORS.text, bgColor = COLORS.surfaceElevated }: BadgeProps) {
  return (
    <View style={[styles.badge, { backgroundColor: bgColor }]}>
      <Text style={[styles.badgeText, { color }]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  statCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 14,
    borderLeftWidth: 3,
    flex: 1,
  },
  statHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: "700",
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  trend: {
    fontSize: 12,
    fontWeight: "600",
  },
  progressHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  progressTitle: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: "500",
  },
  progressValue: {
    fontSize: 13,
    fontWeight: "600",
  },
  progressTrack: {
    height: 8,
    backgroundColor: COLORS.surfaceElevated,
    borderRadius: 4,
  },
  progressFill: {
    height: 8,
    borderRadius: 4,
  },
  listItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: COLORS.surface,
    borderRadius: 10,
    marginBottom: 6,
  },
  listIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  listContent: {
    flex: 1,
  },
  listTitle: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: "500",
  },
  listSubtitle: {
    color: COLORS.textMuted,
    fontSize: 12,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "600",
  },
});
