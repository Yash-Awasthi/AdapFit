/**
 * Recovery Dashboard — Cross-Domain Recovery Intelligence
 *
 * Displays Recovery Engine V2 output: overall score as a large circular
 * progress indicator, domain breakdown with icons, cross-domain insights,
 * actionable recommendations, and training guidance.
 *
 * UI Principles Applied:
 * - Accessibility-first: all interactive elements have labels and roles
 * - Consistent tokens: theme colors, spacing, radius used throughout
 * - Visual hierarchy: score ring → training card → domains → insights → recs
 * - Micro-interactions: touch feedback on all tappable elements
 * - Loading states: animated skeleton with pulse effect
 * - Empty states: clear messaging when data unavailable
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Animated, RefreshControl, ActivityIndicator, Dimensions,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { colors, typography, spacing, radius, shadows, glass, getScoreColor, getScoreLabel, accessibility } from '../src/theme';
import { useUserStore } from '../src/stores/userStore';
import { api } from '../src/services/api';
import { SCREEN_HEADER_TOP } from '../src/theme/layout';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ─── Domain config ───────────────────────────────────────────
const DOMAIN_META: Record<string, { icon: string; color: string; label: string }> = {
  sleep:          { icon: 'moon',           color: colors.health.sleep,      label: 'Sleep' },
  hrv:            { icon: 'pulse',          color: colors.health.heart,      label: 'HRV' },
  training_load:  { icon: 'barbell',        color: colors.health.energy,     label: 'Training Load' },
  subjective:     { icon: 'happy-outline',  color: colors.health.mental,     label: 'Subjective' },
  nutrition:      { icon: 'nutrition',      color: colors.health.nutrition,  label: 'Nutrition' },
  heart_rate:     { icon: 'heart',          color: colors.health.heart,      label: 'Heart Rate' },
};

const STATUS_COLORS: Record<string, string> = {
  excellent: colors.score.excellent,
  good:      colors.score.good,
  fair:      colors.score.fair,
  poor:      colors.score.poor,
  critical:  colors.score.critical,
  no_data:   colors.text.muted,
};

const PRIORITY_META: Record<string, { color: string; bg: string; icon: string }> = {
  high:   { color: colors.health.danger,  bg: colors.health.dangerBg,  icon: 'alert-circle' },
  medium: { color: colors.health.warning, bg: colors.health.warningBg, icon: 'information-circle' },
  low:    { color: colors.health.success, bg: colors.health.successBg, icon: 'checkmark-circle' },
};

// ─── Animated Circular Progress ──────────────────────────────
function RecoveryScoreRing({ score, size = 200 }: { score: number; size?: number }) {
  const animValue = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scoreColor = getScoreColor(score);
  const strokeWidth = size * 0.07;
  const innerSize = size - strokeWidth * 2;

  useEffect(() => {
    // Animate score fill
    Animated.timing(animValue, {
      toValue: score,
      duration: 1400,
      useNativeDriver: false,
    }).start();

    // Subtle pulse on mount
    Animated.sequence([
      Animated.timing(pulseAnim, { toValue: 1.02, duration: 600, useNativeDriver: true }),
      Animated.timing(pulseAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
    ]).start();
  }, [score]);

  return (
    <Animated.View
      style={[{ transform: [{ scale: pulseAnim }] }]}
      accessible={true}
      accessibilityRole="text"
      accessibilityLabel={`Recovery score ${Math.round(score)} out of 100, ${getScoreLabel(score)}`}
    >
      <View style={[styles.ringOuter, { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth, borderColor: colors.surface.divider }]}>
        <View style={[styles.ringInner, { width: innerSize, height: innerSize, borderRadius: innerSize / 2, backgroundColor: scoreColor + '12' }]}>
          <Text style={[styles.ringScore, { fontSize: size * 0.28, color: scoreColor }]}>{Math.round(score)}</Text>
          <Text style={[styles.ringMax, { fontSize: size * 0.1, color: colors.text.muted }]}>/ 100</Text>
        </View>
        {/* Glow effect */}
        <View style={[styles.ringGlow, { width: size + 20, height: size + 20, borderRadius: (size + 20) / 2, borderColor: scoreColor + '15' }]} />
      </View>
    </Animated.View>
  );
}

// ─── Domain Row ──────────────────────────────────────────────
function DomainRow({ name, score, status, insight, dataAvailable }: {
  name: string; score: number; status: string; insight: string; dataAvailable: boolean;
}) {
  const meta = DOMAIN_META[name] || { icon: 'help-circle', color: colors.text.muted, label: name };
  const statusColor = STATUS_COLORS[status] || colors.text.muted;
  const barAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (dataAvailable) {
      Animated.timing(barAnim, {
        toValue: Math.min(score, 100),
        duration: 800,
        useNativeDriver: false,
      }).start();
    }
  }, [score, dataAvailable]);

  return (
    <Pressable
      style={({ pressed }) => [styles.domainRow, pressed && styles.domainRowPressed]}
      accessibilityRole="summary"
      accessibilityLabel={`${meta.label}: ${dataAvailable ? `${Math.round(score)} out of 100, ${status}` : 'No data available'}`}
      accessibilityHint={dataAvailable ? insight : undefined}
    >
      <View style={[styles.domainIcon, { backgroundColor: meta.color + '18' }]}>
        <Ionicons name={meta.icon as any} size={18} color={dataAvailable ? meta.color : colors.text.muted} />
      </View>
      <View style={styles.domainInfo}>
        <View style={styles.domainTopRow}>
          <Text style={[styles.domainLabel, { color: dataAvailable ? colors.text.primary : colors.text.muted }]}>{meta.label}</Text>
          <Text style={[styles.domainScore, { color: dataAvailable ? statusColor : colors.text.muted }]}>
            {dataAvailable ? `${Math.round(score)}` : '—'}
          </Text>
        </View>
        <View style={[styles.domainBarTrack, { backgroundColor: meta.color + '15' }]}>
          <Animated.View style={[styles.domainBarFill, {
            width: barAnim.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] }),
            backgroundColor: statusColor,
          }]} />
        </View>
        <Text style={[styles.domainInsight, { color: colors.text.muted }]} numberOfLines={2}>
          {dataAvailable ? insight : 'No data available'}
        </Text>
      </View>
    </Pressable>
  );
}

// ─── Recommendation Card ─────────────────────────────────────
function RecommendationCard({ priority, category, message, rationale }: {
  priority: string; category: string; message: string; rationale: string;
}) {
  const pm = PRIORITY_META[priority] || PRIORITY_META.medium;
  return (
    <Pressable
      style={({ pressed }) => [styles.recCard, { borderLeftColor: pm.color }, pressed && styles.recCardPressed]}
      accessibilityRole="text"
      accessibilityLabel={`${priority} priority ${category} recommendation: ${message}`}
    >
      <View style={styles.recHeader}>
        <View style={[styles.recBadge, { backgroundColor: pm.bg }]}>
          <Ionicons name={pm.icon as any} size={14} color={pm.color} />
          <Text style={[styles.recBadgeText, { color: pm.color }]}>{priority.toUpperCase()}</Text>
        </View>
        <Text style={[styles.recCategory, { color: colors.text.muted }]}>{category}</Text>
      </View>
      <Text style={[styles.recMessage, { color: colors.text.primary }]}>{message}</Text>
      {rationale ? (
        <Text style={[styles.recRationale, { color: colors.text.muted }]}>{rationale}</Text>
      ) : null}
    </Pressable>
  );
}

// ─── Insight Row ─────────────────────────────────────────────
function InsightRow({ text }: { text: string }) {
  return (
    <View style={styles.insightRow} accessibilityRole="text">
      <View style={[styles.insightDot, { backgroundColor: colors.primary }]} />
      <Text style={[styles.insightText, { color: colors.text.secondary }]}>{text}</Text>
    </View>
  );
}

// ─── Animated Skeleton Placeholder ───────────────────────────
function SkeletonPlaceholder() {
  const pulseAnim = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 0.7, duration: 800, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0.4, duration: 800, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <View style={styles.skeletonContainer} accessibilityRole="progressbar" accessibilityLabel="Loading recovery data">
      {/* Score ring skeleton */}
      <Animated.View style={[styles.skeletonRing, { opacity: pulseAnim }]} />
      <Animated.View style={[styles.skeletonLine, { width: 120, marginTop: spacing.lg, opacity: pulseAnim }]} />
      <Animated.View style={[styles.skeletonLine, { width: 80, marginTop: spacing.sm, opacity: pulseAnim }]} />

      {/* Domain skeletons */}
      {[1, 2, 3].map((i) => (
        <Animated.View key={i} style={[styles.skeletonDomainRow, { opacity: pulseAnim }]}>
          <View style={styles.skeletonDomainIcon} />
          <View style={{ flex: 1, marginLeft: spacing.md }}>
            <View style={[styles.skeletonLine, { width: '60%' }]} />
            <View style={[styles.skeletonLine, { width: '100%', marginTop: spacing.sm, height: 6 }]} />
          </View>
        </Animated.View>
      ))}
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
// ─── MAIN RECOVERY DASHBOARD ────────────────────────────────
// ═══════════════════════════════════════════════════════════════
export default function RecoveryDashboardScreen() {
  const router = useRouter();
  const { userId } = useUserStore();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  const [data, setData] = useState<{
    overall_score: number;
    recovery_level: string;
    domains: { name: string; score: number; weight: number; weighted_score: number; status: string; insight: string; data_available: boolean }[];
    cross_domain_insights: string[];
    recommendations: { priority: string; category: string; message: string; rationale: string }[];
    training_recommendation: string;
    confidence: string;
    data_completeness: number;
    calculated_at: string;
  } | null>(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const result = await api.getRecoveryV2(userId);
      setData(result);
    } catch (err: any) {
      setError(err?.message || 'Failed to load recovery data');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadData();
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, [loadData]);

  const scoreColor = data ? getScoreColor(data.overall_score) : colors.text.muted;
  const levelLabel = data ? getScoreLabel(data.overall_score) : '';
  const confidenceIcon = data?.confidence === 'high' ? 'checkmark-circle' : data?.confidence === 'medium' ? 'help-circle' : 'alert-circle';

  return (
    <View style={styles.container}>
      {loading ? (
        <SkeletonPlaceholder />
      ) : error && !data ? (
        /* ─── Error State ────────────────────── */
        <View style={styles.errorContainer} accessibilityRole="alert">
          <Ionicons name="cloud-offline" size={48} color={colors.text.muted} />
          <Text style={[typography.heading.h3, { color: colors.text.primary, marginTop: spacing.lg }]}>Something went wrong</Text>
          <Text style={[typography.body.md, { color: colors.text.muted, marginTop: spacing.sm, textAlign: 'center', paddingHorizontal: 40 }]}>
            {error}
          </Text>
          <Pressable
            style={({ pressed }) => [styles.retryButton, { backgroundColor: colors.primary }, pressed && { opacity: 0.8 }]}
            onPress={loadData}
            accessibilityRole="button"
            accessibilityLabel="Retry loading recovery data"
          >
            <Ionicons name="refresh" size={18} color="#fff" />
            <Text style={[typography.body.md, { color: '#fff', fontWeight: '600' }]}>Try Again</Text>
          </Pressable>
        </View>
      ) : (
        /* ─── Data Loaded ────────────────────── */
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
        >
          {/* ─── Hero Section ─────────────── */}
          <LinearGradient
            colors={[scoreColor + '30', scoreColor + '08', colors.bg.deep]}
            start={{ x: 0.5, y: 0 }}
            end={{ x: 0.5, y: 1 }}
            style={styles.heroSection}
          >
            {/* Back button */}
            <Pressable
              onPress={() => router.back()}
              style={styles.backButton}
              hitSlop={accessibility.minTouchTarget}
              accessibilityRole="button"
              accessibilityLabel="Go back"
            >
              <Ionicons name="chevron-back" size={24} color={colors.text.primary} />
            </Pressable>

            <Text style={[typography.body.sm, { color: colors.text.muted, marginBottom: spacing.xs }]}>Recovery Score</Text>

            <RecoveryScoreRing score={data?.overall_score ?? 0} size={180} />

            <View style={styles.levelBadge}>
              <Text style={[typography.heading.h3, { color: scoreColor }]}>{levelLabel}</Text>
            </View>

            {/* Confidence & data completeness */}
            <View style={styles.metaRow}>
              <View style={styles.metaItem}>
                <Ionicons name={confidenceIcon as any} size={14} color={colors.text.muted} />
                <Text style={[typography.body.xs, { color: colors.text.muted, marginLeft: spacing.xs }]}>
                  {data?.confidence ?? 'low'} confidence
                </Text>
              </View>
              <View style={styles.metaDivider} />
              <View style={styles.metaItem}>
                <Ionicons name="layers-outline" size={14} color={colors.text.muted} />
                <Text style={[typography.body.xs, { color: colors.text.muted, marginLeft: spacing.xs }]}>
                  {data?.data_completeness ?? 0}% data
                </Text>
              </View>
            </View>
          </LinearGradient>

          {/* ─── Training Recommendation ──── */}
          {data?.training_recommendation ? (
            <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
              <Pressable
                style={({ pressed }) => [styles.trainingCard, { borderColor: scoreColor + '30' }, pressed && { opacity: 0.9 }]}
                accessibilityRole="summary"
                accessibilityLabel={`Today's training recommendation: ${data.training_recommendation}`}
              >
                <View style={[styles.trainingIcon, { backgroundColor: scoreColor + '18' }]}>
                  <Ionicons name="flash" size={20} color={scoreColor} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[typography.label.md, { color: scoreColor }]}>Today's Training</Text>
                  <Text style={[typography.body.sm, { color: colors.text.secondary, marginTop: spacing.xs }]} numberOfLines={3}>
                    {data.training_recommendation}
                  </Text>
                </View>
              </Pressable>
            </Animated.View>
          ) : null}

          {/* ─── Domain Breakdown ─────────── */}
          <View style={styles.section}>
            <View style={styles.sectionHeaderRow}>
              <View style={styles.sectionHeaderLeft}>
                <View style={[styles.sectionIcon, { backgroundColor: colors.primary + '18' }]}>
                  <Ionicons name="analytics" size={16} color={colors.primary} />
                </View>
                <Text style={[typography.heading.h3, { color: colors.text.primary }]}>Domain Breakdown</Text>
              </View>
            </View>
            <View style={styles.domainsContainer}>
              {data?.domains.map((domain) => (
                <DomainRow
                  key={domain.name}
                  name={domain.name}
                  score={domain.score}
                  status={domain.status}
                  insight={domain.insight}
                  dataAvailable={domain.data_available}
                />
              ))}
            </View>
          </View>

          {/* ─── Cross-Domain Insights ────── */}
          {data?.cross_domain_insights && data.cross_domain_insights.length > 0 ? (
            <View style={styles.section}>
              <View style={styles.sectionHeaderRow}>
                <View style={styles.sectionHeaderLeft}>
                  <View style={[styles.sectionIcon, { backgroundColor: colors.health.sleep + '18' }]}>
                    <Ionicons name="bulb" size={16} color={colors.health.sleep} />
                  </View>
                  <Text style={[typography.heading.h3, { color: colors.text.primary }]}>Insights</Text>
                </View>
              </View>
              <View style={styles.insightsContainer} accessibilityRole="list">
                {data.cross_domain_insights.map((insight, i) => (
                  <InsightRow key={i} text={insight} />
                ))}
              </View>
            </View>
          ) : null}

          {/* ─── Recommendations ───────────── */}
          {data?.recommendations && data.recommendations.length > 0 ? (
            <View style={styles.section}>
              <View style={styles.sectionHeaderRow}>
                <View style={styles.sectionHeaderLeft}>
                  <View style={[styles.sectionIcon, { backgroundColor: colors.health.success + '18' }]}>
                    <Ionicons name="checkmark-done-circle" size={16} color={colors.health.success} />
                  </View>
                  <Text style={[typography.heading.h3, { color: colors.text.primary }]}>Recommendations</Text>
                </View>
              </View>
              {data.recommendations.map((rec, i) => (
                <RecommendationCard
                  key={i}
                  priority={rec.priority}
                  category={rec.category}
                  message={rec.message}
                  rationale={rec.rationale}
                />
              ))}
            </View>
          ) : null}

          {/* ─── Last Updated ─────────────── */}
          {data?.calculated_at ? (
            <View style={[styles.section, { alignItems: 'center', paddingBottom: spacing.lg }]}>
              <Text style={[typography.body.xs, { color: colors.text.muted }]}>
                Last updated: {data.calculated_at}
              </Text>
            </View>
          ) : null}

          <View style={{ height: 100 }} />
        </ScrollView>
      )}
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
// ─── STYLES ──────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 40 },

  // Hero
  heroSection: {
    paddingTop: SCREEN_HEADER_TOP,
    paddingBottom: 32,
    paddingHorizontal: spacing.screenPadding,
    alignItems: 'center',
  },
  backButton: {
    position: 'absolute',
    top: 52,
    left: spacing.screenPadding,
    width: accessibility.minTouchTarget,
    height: accessibility.minTouchTarget,
    borderRadius: accessibility.minTouchTarget / 2,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Score Ring
  ringOuter: { justifyContent: 'center', alignItems: 'center' },
  ringInner: { justifyContent: 'center', alignItems: 'center' },
  ringGlow: {
    position: 'absolute',
    borderWidth: 1,
  },
  ringScore: { fontWeight: '800' },
  ringMax: { fontWeight: '500', marginTop: -2 },

  levelBadge: {
    marginTop: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(0,0,0,0.25)',
  },

  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  metaItem: { flexDirection: 'row', alignItems: 'center' },
  metaDivider: { width: 1, height: 12, backgroundColor: 'rgba(255,255,255,0.15)' },

  // Training Card
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  trainingCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg.card,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    borderWidth: 1,
    gap: spacing.md,
  },
  trainingIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Section Headers
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  sectionHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  sectionIcon: {
    width: 32,
    height: 32,
    borderRadius: radius.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Domains
  domainsContainer: { gap: spacing.md },
  domainRow: {
    flexDirection: 'row',
    backgroundColor: colors.bg.card,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    borderWidth: 1,
    borderColor: colors.surface.border,
    gap: spacing.md,
    minHeight: accessibility.minTouchTarget,
  },
  domainRowPressed: {
    opacity: 0.8,
    backgroundColor: colors.bg.elevated,
  },
  domainIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  domainInfo: { flex: 1 },
  domainTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  domainLabel: { fontSize: 14, fontWeight: '600' },
  domainScore: { fontSize: 16, fontWeight: '700' },
  domainBarTrack: {
    height: 5,
    borderRadius: 2.5,
    overflow: 'hidden',
    marginBottom: spacing.xs,
  },
  domainBarFill: {
    height: '100%',
    borderRadius: 2.5,
  },
  domainInsight: { fontSize: 11, lineHeight: 15 },

  // Insights
  insightsContainer: {
    backgroundColor: colors.bg.card,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    borderWidth: 1,
    borderColor: colors.surface.border,
    gap: spacing.md,
  },
  insightRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  insightDot: { width: 6, height: 6, borderRadius: 3, marginTop: 5 },
  insightText: { flex: 1, fontSize: 13, lineHeight: 19 },

  // Recommendations
  recCard: {
    backgroundColor: colors.bg.card,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    borderWidth: 1,
    borderColor: colors.surface.border,
    borderLeftWidth: 3,
    marginBottom: spacing.md,
    minHeight: accessibility.minTouchTarget,
  },
  recCardPressed: {
    opacity: 0.8,
    backgroundColor: colors.bg.elevated,
  },
  recHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  recBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.badge,
    gap: spacing.xs,
  },
  recBadgeText: { fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  recCategory: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  recMessage: { fontSize: 13, lineHeight: 19 },
  recRationale: { fontSize: 11, lineHeight: 16, marginTop: spacing.sm, fontStyle: 'italic' },

  // Error
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.bg.deep,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.lg,
    borderRadius: radius.button,
    marginTop: spacing['2xl'],
    minHeight: accessibility.minTouchTarget,
  },

  // Skeleton
  skeletonContainer: {
    flex: 1,
    backgroundColor: colors.bg.deep,
    alignItems: 'center',
    paddingTop: 80,
    paddingHorizontal: spacing.screenPadding,
  },
  skeletonRing: {
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: colors.bg.card,
  },
  skeletonLine: {
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.bg.card,
  },
  skeletonDomainRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg.card,
    borderRadius: radius.card,
    padding: spacing.cardPadding,
    marginTop: spacing.md,
  },
  skeletonDomainIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    backgroundColor: colors.surface.divider,
  },
});
