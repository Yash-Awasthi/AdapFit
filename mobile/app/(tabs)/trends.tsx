/**
 * Trends Screen — Premium Health Analytics & Trends Dashboard
 * Interactive charts, trend analysis, health insights
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, glass } from '../../src/theme';
import {
  GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium, PillChip,
} from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

const TIME_PERIODS = ['1W', '1M', '3M', '6M', '1Y'];

const TREND_DATA = [
  { label: 'Heart Rate', value: '72', unit: 'bpm', trend: 'down', change: '-3%', color: colors.health.heart, icon: 'heart', data: [75, 73, 74, 72, 71, 72, 72] },
  { label: 'Sleep Score', value: '78', unit: '', trend: 'up', change: '+5%', color: colors.health.sleep, icon: 'moon', data: [70, 72, 74, 75, 76, 77, 78] },
  { label: 'Steps', value: '8.2k', unit: '', trend: 'up', change: '+12%', color: colors.health.activity, icon: 'footsteps', data: [6.5, 7.0, 7.2, 7.8, 8.0, 8.1, 8.2] },
  { label: 'Stress', value: '35', unit: '/100', trend: 'down', change: '-8%', color: colors.health.calm, icon: 'leaf', data: [42, 40, 38, 37, 36, 35, 35] },
  { label: 'Weight', value: '72.5', unit: 'kg', trend: 'down', change: '-0.5kg', color: colors.health.energy, icon: 'scale', data: [73.5, 73.2, 73.0, 72.8, 72.7, 72.6, 72.5] },
  { label: 'Calories', value: '2,150', unit: 'kcal', trend: 'up', change: '+3%', color: '#F59E0B', icon: 'flame', data: [2000, 2050, 2100, 2120, 2130, 2140, 2150] },
];

const INSIGHTS = [
  { title: 'Sleep Improving', description: 'Your sleep score has increased 5% this week. Keep up the consistent bedtime!', icon: 'moon', color: colors.health.sleep, type: 'positive' },
  { title: 'Stress Trending Down', description: 'Meditation sessions are paying off. Your average stress dropped 8 points.', icon: 'leaf', color: colors.health.calm, type: 'positive' },
  { title: 'Activity Plateau', description: 'Steps have been flat for 3 days. Try adding a 10-minute walk after lunch.', icon: 'footsteps', color: colors.health.activity, type: 'suggestion' },
  { title: 'Heart Rate Variability', description: 'HRV improved 12% — your recovery capacity is increasing.', icon: 'pulse', color: colors.health.heart, type: 'positive' },
];

// ===== Mini Chart Component =====
const MiniChart: React.FC<{ data: number[]; color: string; height?: number }> = ({ data, color, height = 60 }) => {
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
  const [activePeriod, setActivePeriod] = useState('1W');
  const [selectedMetric, setSelectedMetric] = useState(0);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  const selected = TREND_DATA[selectedMetric];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <LinearGradient colors={['#8B5CF6', '#6366F1']} style={styles.header}>
        <Text style={styles.headerTitle}>📊 Health Trends</Text>
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

      {/* Metric Selector */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.metricScroll}>
        <View style={styles.metricRow}>
          {TREND_DATA.map((m, i) => (
            <TouchableOpacity
              key={i}
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
      <GlassCard variant="light" style={styles.detailCard}>
        <View style={styles.detailHeader}>
          <View style={[styles.detailIcon, { backgroundColor: selected.color + '15' }]}>
            <Ionicons name={selected.icon as any} size={24} color={selected.color} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.detailTitle}>{selected.label}</Text>
            <View style={styles.detailValueRow}>
              <Text style={[styles.detailValue, { color: selected.color }]}>{selected.value}</Text>
              <Text style={styles.detailUnit}>{selected.unit}</Text>
              <View style={[styles.trendBadge, { backgroundColor: selected.trend === 'up' ? colors.health.calm + '15' : colors.health.heart + '15' }]}>
                <Ionicons name={selected.trend === 'up' ? 'trending-up' : 'trending-down'} size={12} color={selected.trend === 'up' ? colors.health.calm : colors.health.heart} />
                <Text style={[styles.trendText, { color: selected.trend === 'up' ? colors.health.calm : colors.health.heart }]}>{selected.change}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Chart */}
        <View style={styles.chartContainer}>
          <MiniChart data={selected.data} color={selected.color} height={100} />
          <View style={styles.chartLabels}>
            <Text style={styles.chartLabel}>Mon</Text>
            <Text style={styles.chartLabel}>Tue</Text>
            <Text style={styles.chartLabel}>Wed</Text>
            <Text style={styles.chartLabel}>Thu</Text>
            <Text style={styles.chartLabel}>Fri</Text>
            <Text style={styles.chartLabel}>Sat</Text>
            <Text style={styles.chartLabel}>Sun</Text>
          </View>
        </View>
      </GlassCard>

      {/* All Metrics Overview */}
      <SectionHeaderPremium icon="grid" iconColor={colors.primary} title="Overview" />
      <View style={styles.overviewGrid}>
        {TREND_DATA.map((m, i) => (
          <TouchableOpacity
            key={i}
            style={styles.overviewCard}
            onPress={() => setSelectedMetric(i)}
          >
            <View style={[styles.overviewIcon, { backgroundColor: m.color + '15' }]}>
              <Ionicons name={m.icon as any} size={16} color={m.color} />
            </View>
            <Text style={[styles.overviewValue, { color: m.color }]}>{m.value}</Text>
            <Text style={styles.overviewLabel}>{m.label}</Text>
            <View style={styles.overviewTrend}>
              <Ionicons name={m.trend === 'up' ? 'trending-up' : 'trending-down'} size={10} color={m.trend === 'up' ? colors.health.calm : colors.health.heart} />
              <Text style={[styles.overviewTrendText, { color: m.trend === 'up' ? colors.health.calm : colors.health.heart }]}>{m.change}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Insights */}
      <SectionHeaderPremium icon="bulb" iconColor="#F59E0B" title="Health Insights" />
      {INSIGHTS.map((insight, i) => (
        <GlassCard key={i} variant="light" style={styles.insightCard}>
          <View style={styles.insightRow}>
            <View style={[styles.insightIcon, { backgroundColor: insight.color + '15' }]}>
              <Ionicons name={insight.icon as any} size={18} color={insight.color} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.insightTitle}>{insight.title}</Text>
              <Text style={styles.insightText}>{insight.description}</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color={colors.text.muted} />
          </View>
        </GlassCard>
      ))}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
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
  chartLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.sm },
  chartLabel: { fontSize: 10, color: colors.text.muted, textAlign: 'center', flex: 1 },

  // Overview Grid
  overviewGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding },
  overviewCard: {
    width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md * 2) / 3,
    backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.md,
    borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center',
  },
  overviewIcon: { width: 32, height: 32, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  overviewValue: { fontSize: 18, fontWeight: '800' },
  overviewLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },
  overviewTrend: { flexDirection: 'row', alignItems: 'center', gap: 2, marginTop: 4 },
  overviewTrendText: { fontSize: 10, fontWeight: '600' },

  // Insights
  insightCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  insightRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  insightIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  insightTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  insightText: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 16 },
});
