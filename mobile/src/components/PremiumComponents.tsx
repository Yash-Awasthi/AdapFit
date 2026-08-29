/**
 * Premium UI Components — AdapFit Design System
 * High-quality reusable components with glassmorphism, gradients, animations
 */
import React, { useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated,
  Dimensions, Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, shadows, glass } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ===== ANIMATED SCORE RING =====
interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
  sublabel?: string;
  animated?: boolean;
  icon?: string;
}

export const ScoreRing: React.FC<ScoreRingProps> = ({
  score,
  size = 120,
  strokeWidth = 8,
  color,
  label,
  sublabel,
  animated = true,
  icon,
}) => {
  const animValue = useRef(new Animated.Value(0)).current;
  const rotation = animValue.interpolate({
    inputRange: [0, 100],
    outputRange: ['0deg', '360deg'],
  });

  useEffect(() => {
    if (animated) {
      Animated.timing(animValue, {
        toValue: score,
        duration: 1200,
        useNativeDriver: false,
      }).start();
    } else {
      animValue.setValue(score);
    }
  }, [score]);

  const scoreColor = color || (score >= 80 ? colors.score.excellent : score >= 60 ? colors.score.good : score >= 40 ? colors.score.fair : colors.score.critical);
  const bgColor = scoreColor + '15';
  const trackColor = colors.surface.divider;

  return (
    <View style={{ alignItems: 'center' }}>
      <View style={[styles.ringOuter, { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth, borderColor: trackColor }]}>
        <View style={[styles.ringInner, { width: size - strokeWidth * 2, height: size - strokeWidth * 2, borderRadius: (size - strokeWidth * 2) / 2, backgroundColor: bgColor }]}>
          {icon && <Ionicons name={icon as any} size={size * 0.18} color={scoreColor} style={{ marginBottom: 2 }} />}
          <Text style={[styles.ringScore, { fontSize: size * 0.3, color: scoreColor }]}>{Math.round(score)}</Text>
          {label && <Text style={[styles.ringLabel, { fontSize: size * 0.09 }]}>{label}</Text>}
        </View>
      </View>
      {sublabel && <Text style={[styles.ringSublabel, { color: scoreColor }]}>{sublabel}</Text>}
    </View>
  );
};

// ===== GRADIENT CARD =====
interface GradientCardProps {
  colors: string[];
  children: React.ReactNode;
  style?: any;
  onPress?: () => void;
  padding?: number;
}

export const GradientCard: React.FC<GradientCardProps> = ({ colors: gradientColors, children, style, onPress, padding = spacing.cardPadding }) => {
  const content = (
    <LinearGradient
      colors={gradientColors as any}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.gradientCard, { padding }, style]}
    >
      {children}
    </LinearGradient>
  );

  if (onPress) {
    return <TouchableOpacity onPress={onPress} activeOpacity={0.85}>{content}</TouchableOpacity>;
  }
  return content;
};

// ===== GLASS CARD =====
interface GlassCardProps {
  children: React.ReactNode;
  style?: any;
  onPress?: () => void;
  variant?: 'light' | 'dark' | 'primary' | 'health';
  healthType?: 'heart' | 'calm' | 'sleep' | 'energy' | 'mental' | 'nutrition';
  padding?: number;
}

export const GlassCard: React.FC<GlassCardProps> = ({ children, style, onPress, variant = 'light', healthType, padding = spacing.cardPadding }) => {
  const glassStyle = variant === 'health' && healthType
    ? glass.health[healthType]
    : glass[variant];

  const content = (
    <View style={[glassStyle, { padding }, style]}>
      {children}
    </View>
  );

  if (onPress) {
    return <TouchableOpacity onPress={onPress} activeOpacity={0.85}>{content}</TouchableOpacity>;
  }
  return content;
};

// ===== HEALTH METRIC MINI =====
interface HealthMetricMiniProps {
  icon: string;
  value: string | number;
  label: string;
  color: string;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  onPress?: () => void;
}

export const HealthMetricMini: React.FC<HealthMetricMiniProps> = ({ icon, value, label, color, trend, trendValue, onPress }) => {
  const trendIcon = trend === 'up' ? 'trending-up' : trend === 'down' ? 'trending-down' : 'remove';
  const trendColor = trend === 'up' ? colors.score.excellent : trend === 'down' ? colors.score.critical : colors.text.muted;

  return (
    <TouchableOpacity
      style={[styles.metricMini, { borderColor: color + '20' }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.metricMiniIcon, { backgroundColor: color + '18' }]}>
        <Ionicons name={icon as any} size={18} color={color} />
      </View>
      <Text style={[styles.metricMiniValue, { color }]}>{value}</Text>
      <Text style={styles.metricMiniLabel}>{label}</Text>
      {trend && (
        <View style={styles.metricMiniTrend}>
          <Ionicons name={trendIcon as any} size={10} color={trendColor} />
          {trendValue && <Text style={[styles.metricMiniTrendText, { color: trendColor }]}>{trendValue}</Text>}
        </View>
      )}
    </TouchableOpacity>
  );
};

// ===== ANIMATED HEADER =====
interface AnimatedHeaderProps {
  title: string;
  subtitle?: string;
  gradient?: string[];
  rightAction?: { icon: string; onPress: () => void };
  large?: boolean;
}

export const AnimatedHeader: React.FC<AnimatedHeaderProps> = ({ title, subtitle, gradient, rightAction, large }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <Animated.View style={[styles.headerContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
      {gradient ? (
        <LinearGradient colors={gradient as any} style={styles.headerGradient}>
          <View style={styles.headerContent}>
            <Text style={[styles.headerTitle, large && styles.headerTitleLarge]}>{title}</Text>
            {subtitle && <Text style={styles.headerSubtitle}>{subtitle}</Text>}
          </View>
          {rightAction && (
            <TouchableOpacity onPress={rightAction.onPress} style={styles.headerAction}>
              <Ionicons name={rightAction.icon as any} size={22} color="#FFF" />
            </TouchableOpacity>
          )}
        </LinearGradient>
      ) : (
        <View style={styles.headerContentPlain}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.headerTitlePlain, large && styles.headerTitleLarge]}>{title}</Text>
            {subtitle && <Text style={styles.headerSubtitlePlain}>{subtitle}</Text>}
          </View>
          {rightAction && (
            <TouchableOpacity onPress={rightAction.onPress} style={styles.headerActionPlain}>
              <Ionicons name={rightAction.icon as any} size={22} color={colors.primary} />
            </TouchableOpacity>
          )}
        </View>
      )}
    </Animated.View>
  );
};

// ===== SECTION HEADER PREMIUM =====
interface SectionHeaderPremiumProps {
  icon: string;
  iconColor: string;
  title: string;
  subtitle?: string;
  action?: { label: string; onPress: () => void };
}

export const SectionHeaderPremium: React.FC<SectionHeaderPremiumProps> = ({ icon, iconColor, title, subtitle, action }) => (
  <View style={styles.sectionPremium}>
    <View style={styles.sectionPremiumLeft}>
      <View style={[styles.sectionPremiumIcon, { backgroundColor: iconColor + '18' }]}>
        <Ionicons name={icon as any} size={16} color={iconColor} />
      </View>
      <View>
        <Text style={styles.sectionPremiumTitle}>{title}</Text>
        {subtitle && <Text style={styles.sectionPremiumSubtitle}>{subtitle}</Text>}
      </View>
    </View>
    {action && (
      <TouchableOpacity onPress={action.onPress}>
        <Text style={[styles.sectionPremiumAction, { color: colors.primary }]}>{action.label}</Text>
      </TouchableOpacity>
    )}
  </View>
);

// ===== PROGRESS BAR PREMIUM =====
interface ProgressBarPremiumProps {
  value: number;
  max: number;
  color?: string;
  height?: number;
  showLabel?: boolean;
  label?: string;
}

export const ProgressBarPremium: React.FC<ProgressBarPremiumProps> = ({ value, max, color = colors.primary, height = 6, showLabel, label }) => {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <View>
      {showLabel && (
        <View style={styles.progressLabelRow}>
          <Text style={styles.progressLabelText}>{label || `${Math.round(pct)}%`}</Text>
          <Text style={styles.progressLabelValue}>{value} / {max}</Text>
        </View>
      )}
      <View style={[styles.progressTrack, { height, borderRadius: height / 2 }]}>
        <View style={[styles.progressFill, { width: `${pct}%`, backgroundColor: color, borderRadius: height / 2 }]} />
      </View>
    </View>
  );
};

// ===== STAT CARD =====
interface StatCardProps {
  value: string | number;
  label: string;
  icon?: string;
  color?: string;
  trend?: 'up' | 'down' | 'flat';
}

export const StatCard: React.FC<StatCardProps> = ({ value, label, icon, color = colors.primary, trend }) => (
  <View style={styles.statCard}>
    {icon && (
      <View style={[styles.statCardIcon, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon as any} size={16} color={color} />
      </View>
    )}
    <Text style={[styles.statCardValue, { color }]}>{value}</Text>
    <Text style={styles.statCardLabel}>{label}</Text>
    {trend && (
      <Ionicons
        name={trend === 'up' ? 'arrow-up' : trend === 'down' ? 'arrow-down' : 'remove' as any}
        size={12}
        color={trend === 'up' ? colors.score.excellent : trend === 'down' ? colors.score.critical : colors.text.muted}
        style={{ marginTop: 4 }}
      />
    )}
  </View>
);

// ===== QUICK ACTION BUTTON =====
interface QuickActionProps {
  icon: string;
  label: string;
  color: string;
  onPress: () => void;
}

export const QuickAction: React.FC<QuickActionProps> = ({ icon, label, color, onPress }) => (
  <TouchableOpacity style={styles.quickAction} onPress={onPress} activeOpacity={0.7}>
    <View style={[styles.quickActionIcon, { backgroundColor: color + '15' }]}>
      <Ionicons name={icon as any} size={22} color={color} />
    </View>
    <Text style={styles.quickActionLabel}>{label}</Text>
  </TouchableOpacity>
);

// ===== PILL CHIP =====
interface PillChipProps {
  label: string;
  active?: boolean;
  onPress?: () => void;
  color?: string;
}

export const PillChip: React.FC<PillChipProps> = ({ label, active, onPress, color = colors.primary }) => (
  <TouchableOpacity
    style={[styles.pillChip, active && { backgroundColor: color + '25', borderColor: color + '50' }]}
    onPress={onPress}
    activeOpacity={0.7}
  >
    <Text style={[styles.pillChipText, active && { color }]}>{label}</Text>
  </TouchableOpacity>
);

// ===== STYLES =====
const styles = StyleSheet.create({
  // Score Ring
  ringOuter: { justifyContent: 'center', alignItems: 'center' },
  ringInner: { justifyContent: 'center', alignItems: 'center' },
  ringScore: { fontWeight: '800', fontFamily: Platform.OS === 'ios' ? 'System' : 'monospace' },
  ringLabel: { fontWeight: '600', color: colors.text.muted, marginTop: 1 },
  ringSublabel: { fontSize: 12, fontWeight: '600', marginTop: spacing.sm },

  // Gradient Card
  gradientCard: { borderRadius: 20, overflow: 'hidden' },

  // Metric Mini
  metricMini: {
    flex: 1,
    minWidth: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md * 2) / 3,
    backgroundColor: colors.bg.card,
    borderRadius: 16,
    padding: spacing.md,
    borderWidth: 1,
    alignItems: 'center',
  },
  metricMiniIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  metricMiniValue: { fontSize: 18, fontWeight: '700' },
  metricMiniLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },
  metricMiniTrend: { flexDirection: 'row', alignItems: 'center', gap: 2, marginTop: 4 },
  metricMiniTrendText: { fontSize: 10, fontWeight: '600' },

  // Header
  headerContainer: { marginBottom: spacing.lg },
  headerGradient: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  headerContent: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' },
  headerTitle: { fontSize: 22, fontWeight: '700', color: '#FFF' },
  headerTitleLarge: { fontSize: 28, fontWeight: '800' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  headerAction: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.15)', justifyContent: 'center', alignItems: 'center' },
  headerContentPlain: { flexDirection: 'row', alignItems: 'center', paddingTop: 56, paddingHorizontal: spacing.screenPadding, paddingBottom: spacing.lg },
  headerTitlePlain: { fontSize: 28, fontWeight: '800', color: colors.text.primary },
  headerSubtitlePlain: { fontSize: 14, color: colors.text.muted, marginTop: 4 },
  headerActionPlain: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },

  // Section Header
  sectionPremium: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md, paddingHorizontal: spacing.screenPadding },
  sectionPremiumLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  sectionPremiumIcon: { width: 32, height: 32, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  sectionPremiumTitle: { fontSize: 17, fontWeight: '700', color: colors.text.primary },
  sectionPremiumSubtitle: { fontSize: 12, color: colors.text.muted },
  sectionPremiumAction: { fontSize: 13, fontWeight: '600' },

  // Progress Bar
  progressLabelRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xs },
  progressLabelText: { fontSize: 12, fontWeight: '600', color: colors.text.secondary },
  progressLabelValue: { fontSize: 12, color: colors.text.muted },
  progressTrack: { backgroundColor: colors.surface.divider, overflow: 'hidden' },
  progressFill: { height: '100%' },

  // Stat Card
  statCard: {
    flex: 1,
    backgroundColor: colors.bg.card,
    borderRadius: 16,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.surface.border,
    alignItems: 'center',
    minWidth: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md * 2) / 3,
  },
  statCardIcon: { width: 32, height: 32, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  statCardValue: { fontSize: 20, fontWeight: '700' },
  statCardLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  // Quick Action
  quickAction: { alignItems: 'center', width: 72 },
  quickActionIcon: { width: 52, height: 52, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  quickActionLabel: { fontSize: 11, fontWeight: '600', color: colors.text.secondary, textAlign: 'center' },

  // Pill Chip
  pillChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: colors.bg.card,
    borderWidth: 1,
    borderColor: colors.surface.border,
    marginRight: spacing.sm,
  },
  pillChipText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
});
