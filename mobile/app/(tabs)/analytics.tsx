/**
 * Analytics — the user's own recovery log history.
 *
 * Read from the recovery logs rather than a separate analytics store: these
 * are the same rows the recovery score and daily decision are computed from,
 * so the trends here cannot disagree with the number on the home screen.
 *
 * A metric with no readings is left out of the list instead of being drawn
 * flat at zero, which reads as "you did nothing" rather than "nothing was
 * recorded".
 */
import React, { useMemo, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { MetricCardWithChart, InteractiveBarChart, InteractiveRingChart } from '../../src/components/InteractiveCharts';
import { useApi } from '../../src/hooks/useApi';
import { asArray } from '../../src/services/http';

interface RecoveryLog {
  log_date?: string;
  recovery_score?: number | null;
  hrv_rmssd?: number | null;
  resting_heart_rate?: number | null;
  sleep_duration_hours?: number | null;
  sleep_score?: number | null;
  steps?: number | null;
  active_calories?: number | null;
  soreness_score?: number | null;
  fatigue_score?: number | null;
}

const RANGES: { label: string; days: number }[] = [
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 365 },
];

type MetricKey = keyof RecoveryLog;

const METRICS: {
  key: MetricKey;
  title: string;
  icon: string;
  color: string;
  format: (v: number) => string;
  // Whether a fall is an improvement, which decides the arrow's colour.
  lowerIsBetter?: boolean;
}[] = [
  { key: 'recovery_score', title: 'Recovery Score', icon: 'battery-charging', color: colors.health.calm, format: (v) => String(Math.round(v)) },
  { key: 'resting_heart_rate', title: 'Resting Heart Rate', icon: 'heart', color: colors.health.heart, format: (v) => `${Math.round(v)} bpm`, lowerIsBetter: true },
  { key: 'hrv_rmssd', title: 'HRV (RMSSD)', icon: 'pulse', color: colors.health.mental, format: (v) => `${Math.round(v)} ms` },
  { key: 'sleep_duration_hours', title: 'Sleep', icon: 'moon', color: colors.health.sleep, format: (v) => `${v.toFixed(1)} h` },
  { key: 'steps', title: 'Steps', icon: 'footsteps', color: colors.health.activity, format: (v) => Math.round(v).toLocaleString() },
  { key: 'active_calories', title: 'Active Calories', icon: 'flame', color: colors.health.energy, format: (v) => Math.round(v).toLocaleString() },
];

function numbers(logs: RecoveryLog[], key: MetricKey): number[] {
  return logs
    .map((log) => log[key])
    .filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
}

function percentChange(series: number[]): { change: string; changeType: 'up' | 'down' | 'flat' } | null {
  if (series.length < 4) return null;
  const half = Math.floor(series.length / 2);
  const earlier = series.slice(0, half);
  const recent = series.slice(half);
  const before = earlier.reduce((a, b) => a + b, 0) / earlier.length;
  const after = recent.reduce((a, b) => a + b, 0) / recent.length;
  if (before === 0) return null;
  const delta = ((after - before) / before) * 100;
  if (Math.abs(delta) < 1) return { change: 'steady', changeType: 'flat' };
  return {
    change: `${delta > 0 ? '+' : ''}${delta.toFixed(0)}%`,
    changeType: delta > 0 ? 'up' : 'down',
  };
}

function weekdayLabel(isoDate?: string): string {
  if (!isoDate) return '';
  const parsed = new Date(`${isoDate}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? '' : parsed.toLocaleDateString([], { weekday: 'short' });
}

export default function AnalyticsScreen() {
  const [range, setRange] = useState(RANGES[0]);
  const { data, loading, refreshing, refresh } = useApi<{ items: RecoveryLog[]; count: number }>(
    `/recovery-logs?days=${range.days}`,
    [range.days]
  );

  const logs = asArray<RecoveryLog>(data?.items);

  const metricCards = useMemo(
    () => METRICS.map((metric) => {
      const series = numbers(logs, metric.key);
      if (series.length === 0) return null;
      const latest = series[series.length - 1];
      const movement = percentChange(series);
      // An improvement is drawn as "up" whichever direction the number moved.
      const changeType = movement && metric.lowerIsBetter && movement.changeType !== 'flat'
        ? (movement.changeType === 'down' ? 'up' : 'down')
        : movement?.changeType;
      return {
        ...metric,
        value: metric.format(latest),
        data: series.slice(-14),
        change: movement?.change,
        changeType,
        readings: series.length,
      };
    }).filter(Boolean) as (typeof METRICS[number] & {
      value: string; data: number[]; change?: string; changeType?: 'up' | 'down' | 'flat'; readings: number;
    })[],
    [logs]
  );

  const activity = useMemo(() => {
    const withSteps = logs.filter((l) => typeof l.steps === 'number');
    return withSteps.slice(-7).map((log) => ({
      value: Math.round(log.steps as number),
      label: weekdayLabel(log.log_date),
      color: colors.health.activity,
    }));
  }, [logs]);

  // The latest day's recovery breakdown, which is what the score is made of.
  const breakdown = useMemo(() => {
    const latest = logs[logs.length - 1];
    if (!latest) return [];
    const parts: { value: number | null | undefined; color: string; label: string }[] = [
      { value: latest.sleep_score, color: colors.health.sleep, label: 'Sleep' },
      { value: typeof latest.hrv_rmssd === 'number' ? Math.min(100, latest.hrv_rmssd) : null, color: colors.health.mental, label: 'HRV' },
      {
        value: typeof latest.soreness_score === 'number' ? (10 - latest.soreness_score) * 10 : null,
        color: colors.health.heart,
        label: 'Freshness',
      },
    ];
    return parts.flatMap((part) =>
      typeof part.value === 'number' ? [{ value: part.value, color: part.color, label: part.label }] : []
    );
  }, [logs]);

  const latestScore = logs.length ? logs[logs.length - 1].recovery_score : null;

  return (
    <ScreenWrapper
      title="Analytics"
      subtitle="Your health insights"
      gradient={['#06B6D4', '#3B82F6']}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <View style={styles.timeRow}>
        {RANGES.map((option) => {
          const active = option.label === range.label;
          return (
            <TouchableOpacity
              key={option.label}
              style={[styles.timePill, active && styles.timePillActive]}
              onPress={() => setRange(option)}
              accessibilityRole="radio"
              accessibilityState={{ selected: active }}
              accessibilityLabel={`Last ${option.days} days`}
            >
              <Text style={[styles.timePillText, active && styles.timePillTextActive]}>{option.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {logs.length === 0 ? (
        <GlassCard variant="light" style={styles.chartCard}>
          <Text style={styles.emptyTitle}>Nothing logged in this period</Text>
          <Text style={styles.emptyText}>
            Complete a morning check-in and your recovery, sleep, heart rate and activity
            trends build up here.
          </Text>
        </GlassCard>
      ) : (
        <>
          {metricCards.map((metric) => (
            <View key={String(metric.key)} style={{ paddingHorizontal: spacing.screenPadding }}>
              <MetricCardWithChart
                title={metric.title}
                value={metric.value}
                change={metric.change}
                changeType={metric.changeType}
                data={metric.data}
                color={metric.color}
                icon={metric.icon}
              />
            </View>
          ))}

          {activity.length > 0 && (
            <>
              <SectionHeaderPremium icon="bar-chart" iconColor={colors.health.activity} title="Recent Activity" />
              <GlassCard variant="light" style={styles.chartCard}>
                <InteractiveBarChart data={activity} height={180} showValues />
              </GlassCard>
            </>
          )}

          {breakdown.length > 0 && (
            <>
              <SectionHeaderPremium icon="pie-chart" iconColor={colors.primary} title="Latest Recovery Breakdown" />
              <GlassCard variant="light" style={styles.chartCard}>
                <InteractiveRingChart
                  segments={breakdown}
                  size={180}
                  strokeWidth={24}
                  centerValue={typeof latestScore === 'number' ? String(Math.round(latestScore)) : '—'}
                  centerLabel="Recovery"
                />
              </GlassCard>
            </>
          )}

          <SectionHeaderPremium icon="information-circle" iconColor="#F59E0B" title="About These Numbers" />
          <GlassCard variant="light" style={styles.insightCard}>
            <View style={styles.insightRow}>
              <View style={[styles.insightIcon, { backgroundColor: '#F59E0B15' }]}>
                <Ionicons name="calendar" size={20} color="#F59E0B" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.insightTitle}>{logs.length} days logged</Text>
                <Text style={styles.insightText}>
                  Changes compare the second half of this period with the first. A metric you
                  have not recorded is left out rather than shown as zero.
                </Text>
              </View>
            </View>
          </GlassCard>
        </>
      )}
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
  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyText: { fontSize: 13, color: colors.text.muted, marginTop: 4, lineHeight: 19 },

  insightCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  insightRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  insightIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.health.calmBg, justifyContent: 'center', alignItems: 'center' },
  insightTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  insightText: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 16 },
});
