/**
 * Trends Screen — Premium Health Analytics & Trends Dashboard
 * Interactive charts, trend analysis, health insights
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Animated, ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/theme';
import {
  GlassCard, SectionHeaderPremium, HealthMetricMini,
} from '../../src/components/PremiumComponents';
import { SCREEN_HEADER_TOP, useGrid, useTabBarHeight } from '../../src/theme/layout';
import { getJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

type Period = '1W' | '1M' | '3M' | '6M' | '1Y';
type Trend = 'up' | 'down' | 'flat';

const TIME_PERIODS: Period[] = ['1W', '1M', '3M', '6M', '1Y'];
const PERIOD_DAYS: Record<Period, number> = { '1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365 };

interface HrvResponse {
  hrv_history: number[];
  forecast: { trend: string; slope?: number };
  anomalies: { anomaly_count: number };
}
interface AcwrResponse {
  acwr: number | null;
  acwr_status: string;
  history_count: number;
}
interface FatigueResponse {
  current_fatigue: number;
  status?: string;
  trajectory?: string;
  future_trajectory?: number[];
  recommendation?: string;
}
interface MlInsightsResponse {
  readiness_prediction: { predicted_state: string; confidence: number };
}

interface MetricCard {
  key: string;
  label: string;
  icon: string;
  color: string;
  value: string;
  unit: string;
  trendLabel: string;
  direction: Trend;
  sparkline: number[];
  hasData: boolean;
}

interface Insight {
  title: string;
  description: string;
  icon: string;
  color: string;
}

/** "SWEET_SPOT" -> "Sweet Spot"; also handles single lowercase words. */
function titleCase(s: string): string {
  return s.toLowerCase().split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function buildMetrics(hrv: HrvResponse | null, acwr: AcwrResponse | null, fatigue: FatigueResponse | null, ml: MlInsightsResponse | null): MetricCard[] {
  const hrvValues = asArray<number>(hrv?.hrv_history);
  const hrvHasData = hrvValues.length > 0;
  const hrvTrend = hrv?.forecast?.trend ?? 'no_data';

  const acwrHasData = (acwr?.history_count ?? 0) > 0 && typeof acwr?.acwr === 'number';

  const fatigueHasData = !!fatigue && fatigue.trajectory !== 'insufficient_data';

  // predict_readiness always returns a confident state even from default
  // features, so treat it as real only once some underlying history exists.
  const hasAnyHistory = hrvHasData || (acwr?.history_count ?? 0) > 0;
  const readiness = ml?.readiness_prediction;
  const readinessHasData = !!readiness && hasAnyHistory;

  return [
    {
      key: 'hrv',
      label: 'HRV',
      icon: 'pulse',
      color: colors.health.heart,
      value: hrvHasData ? String(Math.round(hrvValues[hrvValues.length - 1])) : '—',
      unit: hrvHasData ? 'ms' : '',
      trendLabel: hrvHasData || hrvTrend === 'insufficient_data' ? titleCase(hrvTrend) : 'No Data',
      direction: hrvTrend === 'improving' ? 'up' : hrvTrend === 'declining' ? 'down' : 'flat',
      sparkline: hrvValues.slice(-7),
      hasData: hrvHasData,
    },
    {
      key: 'acwr',
      label: 'ACWR',
      icon: 'speedometer',
      color: colors.health.activity,
      value: acwrHasData ? acwr!.acwr!.toFixed(2) : '—',
      unit: '',
      trendLabel: acwrHasData ? titleCase(acwr!.acwr_status) : 'No Data',
      direction: !acwrHasData ? 'flat' : acwr!.acwr_status === 'DANGER_ZONE' || acwr!.acwr_status === 'CAUTION' ? 'down' : acwr!.acwr_status === 'SWEET_SPOT' ? 'up' : 'flat',
      sparkline: [],
      hasData: acwrHasData,
    },
    {
      key: 'fatigue',
      label: 'Fatigue',
      icon: 'flash',
      color: colors.health.stress,
      value: fatigueHasData ? String(Math.round(fatigue!.current_fatigue)) : '—',
      unit: '',
      trendLabel: fatigueHasData && fatigue!.status ? titleCase(fatigue!.status) : 'No Data',
      direction: !fatigueHasData ? 'flat' : fatigue!.status === 'NEAR_DELOAD' ? 'down' : fatigue!.status === 'MANAGEABLE' ? 'up' : 'flat',
      sparkline: fatigueHasData ? asArray<number>(fatigue!.future_trajectory) : [],
      hasData: fatigueHasData,
    },
    {
      key: 'readiness',
      label: 'Readiness',
      icon: 'battery-charging',
      color: colors.health.calm,
      value: readinessHasData ? titleCase(readiness!.predicted_state) : '—',
      unit: '',
      trendLabel: readinessHasData ? `${Math.round(readiness!.confidence * 100)}% conf.` : 'No Data',
      direction: !readinessHasData ? 'flat' : readiness!.predicted_state === 'OPTIMAL' ? 'up' : readiness!.predicted_state === 'DEPLETED' ? 'down' : 'flat',
      sparkline: [],
      hasData: readinessHasData,
    },
  ];
}

function buildInsights(hrv: HrvResponse | null, acwr: AcwrResponse | null, fatigue: FatigueResponse | null): Insight[] {
  const insights: Insight[] = [];
  const hrvTrend = hrv?.forecast?.trend;

  if (hrvTrend === 'improving') {
    insights.push({ title: 'HRV Improving', description: 'Your heart rate variability has been trending upward — recovery capacity looks strong.', icon: 'trending-up', color: colors.health.heart });
  } else if (hrvTrend === 'declining') {
    insights.push({ title: 'HRV Declining', description: 'Your heart rate variability has been trending downward. Consider prioritizing sleep and easing intensity.', icon: 'trending-down', color: colors.health.heart });
  }

  const anomalyCount = hrv?.anomalies?.anomaly_count ?? 0;
  if (anomalyCount > 0) {
    insights.push({ title: 'HRV Anomaly Detected', description: `${anomalyCount} unusual HRV reading${anomalyCount > 1 ? 's' : ''} in the recent window — worth a closer look.`, icon: 'alert-circle', color: colors.health.heart });
  }

  if ((acwr?.history_count ?? 0) > 0) {
    if (acwr!.acwr_status === 'DANGER_ZONE') {
      insights.push({ title: 'Workload Danger Zone', description: `ACWR is ${acwr!.acwr}. Acute load is spiking well above chronic — a deload is recommended.`, icon: 'warning', color: colors.health.activity });
    } else if (acwr!.acwr_status === 'CAUTION') {
      insights.push({ title: 'Workload Caution', description: `ACWR is ${acwr!.acwr}, trending into the caution zone. Reduce volume this week.`, icon: 'alert', color: colors.health.activity });
    } else if (acwr!.acwr_status === 'SWEET_SPOT') {
      insights.push({ title: 'Workload Balanced', description: `ACWR is ${acwr!.acwr} — acute and chronic load are well matched.`, icon: 'checkmark-circle', color: colors.health.activity });
    } else if (acwr!.acwr_status === 'UNDER_TRAINING') {
      insights.push({ title: 'Room to Train More', description: `ACWR is ${acwr!.acwr} — your acute load is low relative to your base. There's room to add volume.`, icon: 'trending-up', color: colors.health.activity });
    }
  }

  if (fatigue && fatigue.trajectory !== 'insufficient_data' && fatigue.recommendation) {
    const title = fatigue.status === 'NEAR_DELOAD' ? 'Deload Recommended' : fatigue.status === 'ACCUMULATING' ? 'Fatigue Accumulating' : 'Fatigue Manageable';
    insights.push({ title, description: fatigue.recommendation, icon: 'flash', color: colors.health.stress });
  }

  return insights;
}

// ===== Mini Chart Component =====
const MiniChart: React.FC<{ data: number[]; color: string; height?: number }> = ({ data, color, height = 60 }) => {
  if (data.length === 0) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  return (
    <View style={[miniChartStyles.container, { height }]}>
      {data.map((val, i) => {
        const barHeight = ((val - min) / range) * (height - 20) + 10;
        return (
          <View key={i} style={miniChartStyles.barContainer}>
            <View style={[miniChartStyles.bar, { height: barHeight, backgroundColor: color + (i === data.length - 1 ? '' : '60') }]} />
          </View>
        );
      })}
    </View>
  );
};

const miniChartStyles = StyleSheet.create({
  container: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 4 },
  barContainer: { flex: 1, alignItems: 'center' },
  bar: { width: '100%', borderRadius: 4, minHeight: 4 },
});

// ===== Main Screen =====
export default function TrendsScreen() {
  const [activePeriod, setActivePeriod] = useState<Period>('1W');
  const [selectedMetric, setSelectedMetric] = useState(0);
  const [loading, setLoading] = useState(true);
  const [hrv, setHrv] = useState<HrvResponse | null>(null);
  const [acwr, setAcwr] = useState<AcwrResponse | null>(null);
  const [fatigue, setFatigue] = useState<FatigueResponse | null>(null);
  const [ml, setMl] = useState<MlInsightsResponse | null>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const userId = useUserStore((s) => s.userId);
  const grid = useGrid(3);
  const tabBarHeight = useTabBarHeight();

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const days = PERIOD_DAYS[activePeriod];
    Promise.all([
      getJson<HrvResponse>(`/trends/hrv?user_id=${userId}&days=${days}`),
      getJson<AcwrResponse>(`/trends/acwr?user_id=${userId}`),
      getJson<MlInsightsResponse>(`/trends/ml-insights?user_id=${userId}`),
      getJson<FatigueResponse>(`/trends/fatigue-forecast/${userId}`),
    ]).then(([h, a, m, f]) => {
      if (cancelled) return;
      setHrv(h);
      setAcwr(a);
      setMl(m);
      setFatigue(f);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [activePeriod, userId]);

  const metrics = useMemo(() => buildMetrics(hrv, acwr, fatigue, ml), [hrv, acwr, fatigue, ml]);
  const insights = useMemo(() => buildInsights(hrv, acwr, fatigue), [hrv, acwr, fatigue]);
  const selected = metrics[selectedMetric] ?? metrics[0];

  return (
    <ScrollView style={styles.container} contentContainerStyle={[styles.contentContainer, { paddingBottom: tabBarHeight + spacing.xl }]} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <LinearGradient colors={['#8B5CF6', '#6366F1']} style={styles.header}>
        <Text style={styles.headerTitle}>Health Trends</Text>
        <Text style={styles.headerSubtitle}>Track your progress over time</Text>
      </LinearGradient>

      {/* Time Period Selector */}
      <View style={styles.periodRow}>
        {TIME_PERIODS.map(p => (
          <TouchableOpacity
            key={p}
            style={[styles.periodPill, activePeriod === p && styles.periodPillActive]}
            onPress={() => setActivePeriod(p)}
          >
            <Text style={[styles.periodPillText, activePeriod === p && styles.periodPillTextActive]}>{p}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator style={{ marginTop: spacing['2xl'] }} color={colors.primary} />
      ) : (
        <>
          {/* Metric Selector */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.metricScroll}>
            <View style={styles.metricRow}>
              {metrics.map((m, i) => (
                <TouchableOpacity
                  key={m.key}
                  style={[styles.metricChip, selectedMetric === i && { backgroundColor: m.color + '20', borderColor: m.color + '50' }]}
                  onPress={() => setSelectedMetric(i)}
                >
                  <Ionicons name={m.icon as any} size={14} color={selectedMetric === i ? m.color : colors.text.muted} />
                  <Text style={[styles.metricChipText, selectedMetric === i && { color: m.color }]}>{m.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>

          {/* Selected Metric Detail */}
          {selected && (
            <GlassCard variant="light" style={styles.detailCard}>
              <View style={styles.detailHeader}>
                <View style={[styles.detailIcon, { backgroundColor: selected.color + '15' }]}>
                  <Ionicons name={selected.icon as any} size={24} color={selected.color} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.detailTitle}>{selected.label}</Text>
                  <View style={styles.detailValueRow}>
                    <Text style={[styles.detailValue, { color: selected.color }]}>{selected.value}</Text>
                    {!!selected.unit && <Text style={styles.detailUnit}>{selected.unit}</Text>}
                    <View style={[styles.trendBadge, { backgroundColor: (selected.direction === 'up' ? colors.health.calm : selected.direction === 'down' ? colors.health.heart : colors.text.muted) + '15' }]}>
                      <Ionicons
                        name={selected.direction === 'up' ? 'trending-up' : selected.direction === 'down' ? 'trending-down' : 'remove'}
                        size={12}
                        color={selected.direction === 'up' ? colors.health.calm : selected.direction === 'down' ? colors.health.heart : colors.text.muted}
                      />
                      <Text style={[styles.trendText, { color: selected.direction === 'up' ? colors.health.calm : selected.direction === 'down' ? colors.health.heart : colors.text.muted }]}>{selected.trendLabel}</Text>
                    </View>
                  </View>
                </View>
              </View>

              {/* Chart */}
              {selected.sparkline.length >= 2 ? (
                <View style={styles.chartContainer}>
                  <MiniChart data={selected.sparkline} color={selected.color} height={100} />
                </View>
              ) : (
                <View style={styles.emptyChart}>
                  <Text style={styles.emptyChartText}>Not enough data yet to chart this metric.</Text>
                </View>
              )}
            </GlassCard>
          )}

          {/* All Metrics Overview */}
          <SectionHeaderPremium icon="grid" iconColor={colors.primary} title="Overview" />
          <View style={[styles.overviewGrid, { gap: grid.gap, paddingHorizontal: grid.padding }]}>
            {metrics.map((m, i) => (
              <HealthMetricMini
                key={m.key}
                icon={m.icon}
                value={m.value}
                label={m.label}
                color={m.color}
                trend={m.direction}
                trendValue={m.trendLabel}
                onPress={() => setSelectedMetric(i)}
                width={grid.cell}
              />
            ))}
          </View>

          {/* Insights */}
          <SectionHeaderPremium icon="bulb" iconColor="#F59E0B" title="Health Insights" />
          {insights.length === 0 ? (
            <GlassCard variant="light" style={styles.insightCard}>
              <Text style={styles.emptyChartText}>No insights yet — keep logging recovery and workouts to unlock them.</Text>
            </GlassCard>
          ) : (
            insights.map((insight, i) => (
              <GlassCard key={i} variant="light" style={styles.insightCard}>
                <View style={styles.insightRow}>
                  <View style={[styles.insightIcon, { backgroundColor: insight.color + '15' }]}>
                    <Ionicons name={insight.icon as any} size={18} color={insight.color} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.insightTitle}>{insight.title}</Text>
                    <Text style={styles.insightText}>{insight.description}</Text>
                  </View>
                </View>
              </GlassCard>
            ))
          )}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: SCREEN_HEADER_TOP, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  // Period Selector
  periodRow: { flexDirection: 'row', justifyContent: 'center', gap: spacing.sm, marginTop: spacing.lg, paddingHorizontal: spacing.screenPadding },
  periodPill: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  periodPillActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  periodPillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  periodPillTextActive: { color: '#FFF' },

  // Metric Selector
  metricScroll: { marginTop: spacing.lg },
  metricRow: { flexDirection: 'row', paddingHorizontal: spacing.screenPadding, gap: spacing.sm },
  metricChip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
    backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border,
  },
  metricChipText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },

  // Detail Card
  detailCard: { marginHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  detailHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  detailIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  detailTitle: { fontSize: 14, fontWeight: '600', color: colors.text.muted },
  detailValueRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: 4 },
  detailValue: { fontSize: 28, fontWeight: '800' },
  detailUnit: { fontSize: 14, color: colors.text.muted },
  trendBadge: { flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  trendText: { fontSize: 12, fontWeight: '600' },

  // Chart
  chartContainer: { marginTop: spacing.xl },
  emptyChart: { marginTop: spacing.xl, paddingVertical: spacing.lg, alignItems: 'center' },
  emptyChartText: { fontSize: 13, color: colors.text.muted, textAlign: 'center' },

  // Overview Grid
  overviewGrid: { flexDirection: 'row', flexWrap: 'wrap' },

  // Insights
  insightCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  insightRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  insightIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  insightTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  insightText: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 16 },
});
