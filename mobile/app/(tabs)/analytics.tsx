/**
 * Analytics — Premium Health Analytics Dashboard
 * Animated charts, metric cards with sparklines, insights
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, PillChip } from '../../src/components/PremiumComponents';
import { MetricCardWithChart, InteractiveBarChart, InteractiveRingChart } from '../../src/components/InteractiveCharts';
import { StaggeredList } from '../../src/components/AnimationSystem';

const METRICS = [
  { title: 'Heart Rate', value: '72 bpm', change: '-3%', changeType: 'down' as const, data: [75, 73, 74, 72, 71, 72, 72], color: colors.health.heart, icon: 'heart' },
  { title: 'Steps', value: '8,200', change: '+12%', changeType: 'up' as const, data: [6500, 7000, 7200, 7800, 8000, 8100, 8200], color: colors.health.activity, icon: 'footsteps' },
  { title: 'Sleep Score', value: '78', change: '+5%', changeType: 'up' as const, data: [70, 72, 74, 75, 76, 77, 78], color: colors.health.sleep, icon: 'moon' },
  { title: 'Calories', value: '2,150', change: '+3%', changeType: 'up' as const, data: [2000, 2050, 2100, 2120, 2130, 2140, 2150], color: colors.health.energy, icon: 'flame' },
];

const WEEKLY_DATA = [
  { value: 6500, label: 'Mon', color: colors.health.activity },
  { value: 8200, label: 'Tue', color: colors.health.activity },
  { value: 7100, label: 'Wed', color: colors.health.activity },
  { value: 9300, label: 'Thu', color: colors.health.calm },
  { value: 8800, label: 'Fri', color: colors.health.activity },
  { value: 5200, label: 'Sat', color: colors.health.heart },
  { value: 8200, label: 'Sun', color: colors.health.activity },
];

const DISTRIBUTION = [
  { value: 35, color: colors.health.heart, label: 'Exercise' },
  { value: 25, color: colors.health.sleep, label: 'Sleep' },
  { value: 20, color: colors.health.nutrition, label: 'Nutrition' },
  { value: 15, color: colors.health.mental, label: 'Mental' },
  { value: 5, color: '#F59E0B', label: 'Other' },
];

export default function AnalyticsScreen() {
  const [timeRange, setTimeRange] = useState('1W');

  return (
    <ScreenWrapper
      title="Analytics"
      subtitle="Your health insights"
      gradient={['#06B6D4', '#3B82F6']}
      rightAction={{ icon: 'download', onPress: () => {} }}
    >
      {/* Time Range */}
      <View style={styles.timeRow}>
        {['1W', '1M', '3M', '6M', '1Y'].map(t => (
          <TouchableOpacity key={t} style={[styles.timePill, timeRange === t && styles.timePillActive]} onPress={() => setTimeRange(t)}>
            <Text style={[styles.timePillText, timeRange === t && styles.timePillTextActive]}>{t}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Metric Cards with Charts */}
      <StaggeredList staggerDelay={100} animationType="slideIn">
        {METRICS.map((m, i) => (
          <View key={i} style={{ paddingHorizontal: spacing.screenPadding }}>
            <MetricCardWithChart {...m} />
          </View>
        ))}
      </StaggeredList>

      {/* Weekly Activity Bar Chart */}
      <SectionHeaderPremium icon="bar-chart" iconColor={colors.health.activity} title="Weekly Activity" />
      <GlassCard variant="light" style={styles.chartCard}>
        <InteractiveBarChart data={WEEKLY_DATA} height={180} showValues />
      </GlassCard>

      {/* Health Distribution Ring */}
      <SectionHeaderPremium icon="pie-chart" iconColor={colors.primary} title="Health Distribution" />
      <GlassCard variant="light" style={styles.chartCard}>
        <InteractiveRingChart
          segments={DISTRIBUTION}
          size={180}
          strokeWidth={24}
          centerValue="100%"
          centerLabel="Health"
        />
      </GlassCard>

      {/* Insights */}
      <SectionHeaderPremium icon="bulb" iconColor="#F59E0B" title="Insights" />
      <GlassCard variant="primary" style={styles.insightCard}>
        <View style={styles.insightRow}>
          <View style={styles.insightIcon}>
            <Ionicons name="trending-up" size={20} color={colors.health.calm} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.insightTitle}>Activity Up 12%</Text>
            <Text style={styles.insightText}>Your step count has increased significantly this week. Great progress!</Text>
          </View>
        </View>
      </GlassCard>
      <GlassCard variant="light" style={styles.insightCard}>
        <View style={styles.insightRow}>
          <View style={[styles.insightIcon, { backgroundColor: '#F59E0B15' }]}>
            <Ionicons name="moon" size={20} color="#F59E0B" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.insightTitle}>Sleep Quality Improving</Text>
            <Text style={styles.insightText}>Deep sleep increased 15% over the past week.</Text>
          </View>
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  timeRow: { flexDirection: 'row', justifyContent: 'center', gap: spacing.sm, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  timePill: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  timePillActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  timePillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  timePillTextActive: { color: '#FFF' },

  chartCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },

  insightCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  insightRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  insightIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.health.calmBg, justifyContent: 'center', alignItems: 'center' },
  insightTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  insightText: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 16 },
});
