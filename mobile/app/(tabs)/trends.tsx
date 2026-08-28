import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import Animated from 'react-native-reanimated';
import { MetricCard, SectionHeader, LoadingScreen } from '../../src/components';
import { useTheme, CARD_SHADOW } from '../../src/services/theme';
import { useEnterAnimation } from '../../src/services/devSettings';
import { api } from '../../src/services/api';
import { useUserStore } from '../../src/stores';

interface TrendData {
  acwr: number;
  acwr_status: string;
  acute_workload_7d: number;
  chronic_workload_28d: number;
}

interface HrvData {
  hrv_history: number[];
  forecast: {
    forecast: number[];
    trend: string;
    slope: number;
    current_mean: number;
  };
}

interface InjuryRiskData {
  overall_risk_score: number | null;
  risk_level: string;
  vulnerable_regions: string[];
  top_factors: string[];
  recommendations: { priority?: string; action: string; reason?: string }[];
}

const RISK_COLORS: Record<string, string> = {
  LOW: '#22C55E',
  MODERATE: '#F59E0B',
  HIGH: '#EF4444',
};

function BarChart({ data, theme }: { data: number[]; theme: any }) {
  if (!data.length) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const recent = data.slice(-14);

  return (
    <View style={chartStyles.container}>
      {recent.map((val, i) => (
        <View key={i} style={chartStyles.barWrapper}>
          <View
            style={[
              chartStyles.bar,
              {
                height: `${((val - min) / range) * 80 + 20}%`,
                backgroundColor: i === recent.length - 1 ? theme.primaryLight : theme.primary,
              },
            ]}
          />
        </View>
      ))}
    </View>
  );
}

export default function TrendsScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme } = useTheme();
  const enter = useEnterAnimation();
  const [data, setData] = useState<TrendData | null>(null);
  const [hrv, setHrv] = useState<HrvData | null>(null);
  const [injuryRisk, setInjuryRisk] = useState<InjuryRiskData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrends();
  }, []);

  async function fetchTrends() {
    try {
      const [acwrData, hrvData, riskData] = await Promise.all([
        api.getAcwr(userId).catch(() => null),
        api.getHrvTrend(userId, 14).catch(() => null),
        api.getInjuryRisk(userId).catch(() => null),
      ]);
      if (acwrData) setData(acwrData);
      if (hrvData) setHrv(hrvData);
      if (riskData) setInjuryRisk(riskData);
    } catch {}
    setLoading(false);
  }

  if (loading) return <LoadingScreen />;

  const hasRisk = !!injuryRisk && injuryRisk.risk_level !== 'NO_DATA' && injuryRisk.overall_risk_score != null;
  const riskColor = hasRisk ? (RISK_COLORS[injuryRisk!.risk_level] || theme.textMuted) : theme.textMuted;

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.background }]} contentContainerStyle={{ paddingBottom: 100 }}>
      <Animated.View entering={enter(0)}>
        <Text style={[styles.title, { color: theme.text }]}>Trends & Risk</Text>
      </Animated.View>

      <Animated.View entering={enter(50)}>
        {hasRisk ? (
          <View style={[styles.riskCard, CARD_SHADOW, { backgroundColor: theme.surface, borderLeftColor: riskColor }]}>
            <View style={styles.riskHeader}>
              <Text style={[styles.riskTitle, { color: theme.text }]}>Injury Risk Score</Text>
              <View style={[styles.badge, { backgroundColor: riskColor + '22' }]}>
                <Text style={[styles.badgeText, { color: riskColor }]}>
                  {injuryRisk!.risk_level} ({injuryRisk!.overall_risk_score}/100)
                </Text>
              </View>
            </View>
            {injuryRisk!.vulnerable_regions.length > 0 && (
              <Text style={[styles.riskSubtitle, { color: theme.textSecondary }]}>
                Vulnerable regions: {injuryRisk!.vulnerable_regions.join(', ')}
              </Text>
            )}
            {injuryRisk!.recommendations.length > 0 && (
              <View style={[styles.recommendationBox, { backgroundColor: theme.background }]}>
                <Text style={[styles.recText, { color: theme.textSecondary }]}>• {injuryRisk!.recommendations[0].action}</Text>
              </View>
            )}
          </View>
        ) : (
          <View style={[styles.placeholder, CARD_SHADOW, { backgroundColor: theme.surface }]}>
            <Text style={[styles.placeholderText, { color: theme.textMuted }]}>
              Injury risk score appears once you've logged a few workouts — nothing concerning yet, just not enough data.
            </Text>
          </View>
        )}
      </Animated.View>

      <Animated.View entering={enter(100)}>
        <SectionHeader title="Workload Ratio" />
        <View style={styles.metrics}>
          <MetricCard label="ACWR" value={data?.acwr?.toFixed(2) ?? '--'} />
          <MetricCard label="Status" value={data?.acwr_status ? data.acwr_status.replace(/_/g, ' ') : '--'} />
          <MetricCard label="Acute (7d)" value={data?.acute_workload_7d?.toFixed(0) ?? '--'} />
          <MetricCard label="Chronic (28d)" value={data?.chronic_workload_28d?.toFixed(0) ?? '--'} />
        </View>
      </Animated.View>

      <Animated.View entering={enter(150)}>
        <SectionHeader title="HRV Trend" />
        {hrv && hrv.hrv_history.length > 0 ? (
          <View style={[styles.chartCard, CARD_SHADOW, { backgroundColor: theme.surface }]}>
            <BarChart data={hrv.hrv_history} theme={theme} />
            <View style={styles.chartLegend}>
              <Text style={[styles.legendText, { color: theme.textSecondary }]}>
                Mean: {hrv.forecast.current_mean}ms
              </Text>
              <Text
                style={[
                  styles.legendText,
                  {
                    color:
                      hrv.forecast.trend === 'improving'
                        ? theme.success
                        : hrv.forecast.trend === 'declining'
                        ? theme.danger
                        : theme.textMuted,
                  },
                ]}
              >
                Trend: {hrv.forecast.trend} ({hrv.forecast.slope > 0 ? '+' : ''}
                {hrv.forecast.slope.toFixed(2)})
              </Text>
            </View>
            {hrv.forecast.forecast.length > 0 && (
              <View style={[styles.forecastRow, { backgroundColor: theme.background }]}>
                <Text style={[styles.forecastLabel, { color: theme.textMuted }]}>7-day forecast</Text>
                <Text style={[styles.forecastValues, { color: theme.primaryLight }]}>
                  {hrv.forecast.forecast.map((v) => v.toFixed(0)).join(' → ')}
                </Text>
              </View>
            )}
          </View>
        ) : (
          <View style={[styles.placeholder, CARD_SHADOW, { backgroundColor: theme.surface }]}>
            <Text style={[styles.placeholderText, { color: theme.textMuted }]}>
              HRV trend will appear after 3+ days of data.
            </Text>
          </View>
        )}
      </Animated.View>

      <Animated.View entering={enter(200)}>
        <SectionHeader title="Sleep Pattern" />
        <View style={[styles.placeholder, CARD_SHADOW, { backgroundColor: theme.surface }]}>
          <Text style={[styles.placeholderText, { color: theme.textMuted }]}>
            Sleep analysis will appear after 3+ days of data.
          </Text>
        </View>
      </Animated.View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { fontSize: 28, fontWeight: '700', marginTop: 48, marginBottom: 16 },
  riskCard: {
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
  },
  riskHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  riskTitle: { fontSize: 16, fontWeight: '600' },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeText: { fontSize: 12, fontWeight: '700' },
  riskSubtitle: { fontSize: 13, marginTop: 6 },
  recommendationBox: {
    marginTop: 8,
    padding: 8,
    borderRadius: 6,
  },
  recText: { fontSize: 12 },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  chartCard: {
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
  },
  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  legendText: { fontSize: 13 },
  forecastRow: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
  },
  forecastLabel: { fontSize: 12, marginBottom: 4 },
  forecastValues: { fontSize: 14, fontWeight: '600' },
  placeholder: {
    borderRadius: 14,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
  },
  placeholderText: { fontSize: 14, textAlign: 'center' },
});

const chartStyles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 120,
    gap: 4,
  },
  barWrapper: {
    flex: 1,
    height: '100%',
    justifyContent: 'flex-end',
  },
  bar: {
    width: '100%',
    borderRadius: 4,
    minHeight: 4,
  },
});
