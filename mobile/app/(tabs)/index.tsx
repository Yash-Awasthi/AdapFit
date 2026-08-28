import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import Animated from 'react-native-reanimated';
import { RecoveryCard, MetricCard, Button, SectionHeader, LoadingScreen } from '../../src/components';
import { useTheme, CARD_SHADOW } from '../../src/services/theme';
import { useEnterAnimation } from '../../src/services/devSettings';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';

const API = API_BASE_URL;

interface RecoveryData {
  recovery_score: number;
  readiness_state: 'OPTIMAL' | 'MODERATE' | 'REDUCED' | 'DEPLETED';
  metrics_breakdown: {
    hrv_z_score: number | null;
    sleep_score: number;
    subjective_score: number;
    acwr: number | null;
  };
  recommendation_directive: string;
}

export default function RecoveryScreen() {
  const userId = useUserStore((s) => s.userId);
  const { theme } = useTheme();
  const [data, setData] = useState<RecoveryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [hrvTrend] = useState<number[]>([45, 48, 42, 50, 47, 52, 49]);
  const [workoutStreak] = useState(5);
  const router = useRouter();
  const enter = useEnterAnimation();

  useEffect(() => {
    fetchRecovery();
  }, []);

  async function fetchRecovery() {
    try {
      const res = await fetch(`${API}/api/v1/recovery-logs?user_id=${userId}&days=1`);
      if (res.ok) {
        const json = await res.json();
        if (json.items?.length > 0) {
          setData(json.items[json.items.length - 1]);
        }
      }
    } catch {}
    setLoading(false);
  }

  if (loading) return <LoadingScreen />;

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.background }]} contentContainerStyle={{ paddingBottom: 100 }}>
      <Animated.View entering={enter(0)}>
        <Text style={[styles.greeting, { color: theme.text }]} accessibilityRole="header">Good Morning</Text>
        <Text style={[styles.date, { color: theme.textMuted }]}>
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
          })}
        </Text>
      </Animated.View>

      <Animated.View entering={enter(60)}>
        {data ? (
          <RecoveryCard
            score={data.recovery_score}
            state={data.readiness_state}
            directive={data.recommendation_directive}
            accessibilityLabel={`Recovery score ${data.recovery_score} out of 100, readiness state ${data.readiness_state}`}
            accessibilityHint="Shows your current recovery status"
          />
        ) : (
          <View style={[styles.empty, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border, borderWidth: 1 }]}>
            <Text style={[styles.emptyTitle, { color: theme.text }]}>No Data Yet</Text>
            <Text style={[styles.emptyMessage, { color: theme.textMuted }]}>
              Complete your morning check-in to see your recovery score.
            </Text>
          </View>
        )}
      </Animated.View>

      <Animated.View entering={enter(110)}>
        <SectionHeader title="Metrics" />
        <View style={styles.metrics}>
          <MetricCard label="HRV Z-Score" value={data?.metrics_breakdown?.hrv_z_score?.toFixed(2) ?? '--'} />
          <MetricCard label="Sleep Score" value={data?.metrics_breakdown?.sleep_score?.toFixed(1) ?? '--'} />
          <MetricCard label="ACWR" value={data?.metrics_breakdown?.acwr?.toFixed(2) ?? '--'} />
          <MetricCard label="Subjective" value={data?.metrics_breakdown?.subjective_score?.toFixed(1) ?? '--'} />
        </View>
      </Animated.View>

      <Animated.View entering={enter(160)}>
        <SectionHeader title="HRV Trend (7 Days)" />
        <View style={[styles.hrvChart, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border, borderWidth: 1 }]}>
          {hrvTrend.map((val, i) => {
            const height = Math.max(4, (val / 80) * 60);
            return (
              <View key={i} style={styles.hrvBarContainer}>
                <View
                  style={[
                    styles.hrvBar,
                    { height, backgroundColor: val > 50 ? theme.success : val > 35 ? theme.warning : theme.danger },
                  ]}
                />
                <Text style={[styles.hrvBarLabel, { color: theme.textMuted }]}>{val.toFixed(0)}</Text>
              </View>
            );
          })}
        </View>
      </Animated.View>

      <Animated.View entering={enter(210)}>
        <SectionHeader title="Workout Streak" />
        <View style={[styles.streakCard, CARD_SHADOW, { backgroundColor: theme.surface, borderColor: theme.border, borderWidth: 1 }]}>
          <Text style={[styles.streakNumber, { color: theme.orange }]}>{workoutStreak}</Text>
          <Text style={[styles.streakLabel, { color: theme.textSecondary }]}>day streak</Text>
          <View style={styles.streakDots}>
            {Array.from({ length: 7 }).map((_, i) => (
              <View
                key={i}
                style={[
                  styles.streakDot,
                  { backgroundColor: i < workoutStreak ? theme.orange : theme.border },
                ]}
              />
            ))}
          </View>
        </View>
      </Animated.View>

      <Animated.View entering={enter(260)}>
        <Button
          title="Morning Check-in"
          onPress={() => router.push('/checkin')}
          accessibilityLabel="Start morning check-in"
          accessibilityHint="Opens the daily wellness check-in form"
        />
      </Animated.View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  greeting: { fontSize: 28, fontWeight: '700', marginTop: 48 },
  date: { fontSize: 14, marginBottom: 24 },
  empty: { borderRadius: 16, padding: 24, alignItems: 'center', marginBottom: 16 },
  emptyTitle: { fontSize: 18, fontWeight: '600', marginBottom: 8 },
  emptyMessage: { fontSize: 14, textAlign: 'center' },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 },
  hrvChart: {
    flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between',
    borderRadius: 12, padding: 12, marginBottom: 16, height: 100,
  },
  hrvBarContainer: { alignItems: 'center', flex: 1 },
  hrvBar: { width: 16, borderRadius: 4, marginBottom: 4 },
  hrvBarLabel: { fontSize: 9 },
  streakCard: { borderRadius: 12, padding: 16, alignItems: 'center', marginBottom: 16 },
  streakNumber: { fontSize: 36, fontWeight: '800' },
  streakLabel: { fontSize: 14, marginBottom: 8 },
  streakDots: { flexDirection: 'row', gap: 6 },
  streakDot: { width: 12, height: 12, borderRadius: 6 },
});
