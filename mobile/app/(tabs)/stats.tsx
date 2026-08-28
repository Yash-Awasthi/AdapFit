/**
 * Workout Stats Dashboard — comprehensive stats with volume charts,
 * personal records, muscle distribution, and monthly comparison.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { TrendingUp, Trophy, Dumbbell, Clock, Zap } from 'lucide-react-native';
import { API_BASE_URL as API } from '../../src/services/config';
import { useTheme } from '../../src/services/theme';
const SCREEN_WIDTH = Dimensions.get('window').width - 40;

interface WorkoutStats {
  total_workouts: number;
  total_volume_kg: number;
  total_duration_minutes: number;
  avg_session_rpe: number;
  personal_records: { exercise_id: string; weight_kg: number; reps: number; date: string }[];
  muscle_distribution: Record<string, number>;
  monthly_comparison: { month: string; workouts: number; duration: number; volume: number }[];
  top_exercises: { exercise_id: string; total_volume: number }[];
}

const MUSCLE_COLORS: Record<string, string> = {
  chest: '#EF4444',
  back: '#3B82F6',
  quadriceps: '#22C55E',
  shoulders: '#F59E0B',
  hamstrings: '#A855F7',
  biceps: '#EC4899',
  triceps: '#06B6D4',
  core: '#F97316',
  glutes: '#8B5CF6',
  full_body: '#6366F1',
  unknown: '#64748B',
};

export default function StatsScreen() {
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const [stats, setStats] = useState<WorkoutStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchStats(); }, []);

  async function fetchStats() {
    try {
      const res = await fetch(`${API}/api/v1/workout-stats/default?days=365`);
      if (res.ok) setStats(await res.json());
    } catch {}
    setLoading(false);
  }

  if (loading) {
    return <View style={s.container}><Text style={s.loadingText}>Loading stats...</Text></View>;
  }

  if (!stats || stats.total_workouts === 0) {
    return (
      <View style={s.container}>
        <Text style={s.title}>Workout Stats</Text>
        <View style={s.emptyCard}>
          <Dumbbell size={40} color={theme.border} />
          <Text style={s.emptyText}>No workouts yet</Text>
          <Text style={s.emptySubtext}>Complete workouts to see your stats here</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={s.container} contentContainerStyle={{ paddingBottom: 100 }}>
      <Text style={s.title}>Workout Stats</Text>

      {/* Summary Cards */}
      <View style={s.summaryGrid}>
        <View style={s.summaryCard}>
          <Dumbbell size={20} color={theme.primaryLight} />
          <Text style={s.summaryValue}>{stats.total_workouts}</Text>
          <Text style={s.summaryLabel}>Workouts</Text>
        </View>
        <View style={s.summaryCard}>
          <TrendingUp size={20} color={theme.success} />
          <Text style={s.summaryValue}>{(stats.total_volume_kg / 1000).toFixed(1)}k</Text>
          <Text style={s.summaryLabel}>kg Volume</Text>
        </View>
        <View style={s.summaryCard}>
          <Clock size={20} color={theme.warning} />
          <Text style={s.summaryValue}>{Math.round(stats.total_duration_minutes / 60)}h</Text>
          <Text style={s.summaryLabel}>Total Time</Text>
        </View>
        <View style={s.summaryCard}>
          <Zap size={20} color={theme.danger} />
          <Text style={s.summaryValue}>{stats.avg_session_rpe}</Text>
          <Text style={s.summaryLabel}>Avg RPE</Text>
        </View>
      </View>

      {/* Muscle Distribution */}
      <View style={s.section}>
        <Text style={s.sectionTitle}>Muscle Distribution</Text>
        <View style={s.muscleChart}>
          {Object.entries(stats.muscle_distribution).slice(0, 8).map(([muscle, pct]) => (
            <View key={muscle} style={s.muscleRow}>
              <View style={[s.muscleDot, { backgroundColor: MUSCLE_COLORS[muscle] || '#64748B' }]} />
              <Text style={s.muscleName}>{muscle}</Text>
              <View style={s.muscleBarBg}>
                <View style={[s.muscleBarFill, { width: `${pct}%`, backgroundColor: MUSCLE_COLORS[muscle] || '#64748B' }]} />
              </View>
              <Text style={s.musclePct}>{pct}%</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Personal Records */}
      {stats.personal_records.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Personal Records</Text>
          {stats.personal_records.slice(0, 5).map((pr, i) => (
            <View key={i} style={s.prRow}>
              <Trophy size={16} color={i === 0 ? theme.warning : i === 1 ? theme.textSecondary : '#CD7F32'} />
              <View style={s.prInfo}>
                <Text style={s.prExercise}>{pr.exercise_id.replace(/-/g, ' ')}</Text>
                <Text style={s.prDate}>{pr.date}</Text>
              </View>
              <Text style={s.prWeight}>{pr.weight_kg}kg × {pr.reps}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Monthly Comparison */}
      {stats.monthly_comparison.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Monthly Trend</Text>
          <View style={s.monthlyChart}>
            {stats.monthly_comparison.slice(0, 6).reverse().map((m, i) => {
              const maxWorkouts = Math.max(...stats.monthly_comparison.map(x => x.workouts), 1);
              const barHeight = (m.workouts / maxWorkouts) * 80;
              return (
                <View key={i} style={s.monthBar}>
                  <Text style={s.monthValue}>{m.workouts}</Text>
                  <View style={[s.monthFill, { height: barHeight }]} />
                  <Text style={s.monthLabel}>{m.month.slice(5)}</Text>
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Top Exercises */}
      {stats.top_exercises.length > 0 && (
        <View style={s.section}>
          <Text style={s.sectionTitle}>Top Exercises by Volume</Text>
          {stats.top_exercises.map((ex, i) => (
            <View key={i} style={s.topExRow}>
              <Text style={s.topExRank}>#{i + 1}</Text>
              <Text style={s.topExName}>{ex.exercise_id.replace(/-/g, ' ')}</Text>
              <Text style={s.topExVol}>{(ex.total_volume / 1000).toFixed(1)}k kg</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48, marginBottom: 16 },
    loadingText: { color: theme.textMuted, textAlign: 'center', marginTop: 100 },

    // Empty state
    emptyCard: { backgroundColor: theme.surface, borderRadius: 16, padding: 40, alignItems: 'center' },
    emptyText: { fontSize: 18, fontWeight: '600', color: theme.text, marginTop: 12 },
    emptySubtext: { fontSize: 13, color: theme.textMuted, marginTop: 4 },

    // Summary grid
    summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
    summaryCard: {
      width: (SCREEN_WIDTH - 8) / 2,
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 14,
      alignItems: 'center',
    },
    summaryValue: { fontSize: 22, fontWeight: '800', color: theme.text, marginTop: 6 },
    summaryLabel: { fontSize: 11, color: theme.textMuted, marginTop: 2 },

    // Sections
    section: { marginBottom: 20 },
    sectionTitle: { fontSize: 16, fontWeight: '600', color: theme.text, marginBottom: 10 },

    // Muscle distribution
    muscleChart: { backgroundColor: theme.surface, borderRadius: 12, padding: 14 },
    muscleRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
    muscleDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
    muscleName: { fontSize: 12, color: theme.textSecondary, width: 80, textTransform: 'capitalize' },
    muscleBarBg: { flex: 1, height: 8, backgroundColor: theme.surfaceHover, borderRadius: 4, overflow: 'hidden' },
    muscleBarFill: { height: 8, borderRadius: 4 },
    musclePct: { fontSize: 11, color: theme.textMuted, width: 40, textAlign: 'right' },

    // PRs
    prRow: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: theme.surface,
      borderRadius: 8,
      padding: 10,
      marginBottom: 6,
      gap: 8,
    },
    prInfo: { flex: 1 },
    prExercise: { fontSize: 13, fontWeight: '600', color: theme.text, textTransform: 'capitalize' },
    prDate: { fontSize: 10, color: theme.textMuted },
    prWeight: { fontSize: 14, fontWeight: '700', color: theme.warning },

    // Monthly chart
    monthlyChart: {
      flexDirection: 'row',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 14,
      height: 130,
    },
    monthBar: { alignItems: 'center', flex: 1 },
    monthValue: { fontSize: 10, color: theme.textMuted, marginBottom: 4 },
    monthFill: { width: 24, backgroundColor: theme.primaryLight, borderRadius: 4, minHeight: 4 },
    monthLabel: { fontSize: 10, color: theme.textMuted, marginTop: 4 },

    // Top exercises
    topExRow: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: theme.surface,
      borderRadius: 8,
      padding: 10,
      marginBottom: 4,
    },
    topExRank: { fontSize: 14, fontWeight: '700', color: theme.primaryLight, width: 30 },
    topExName: { flex: 1, fontSize: 13, color: theme.textSecondary, textTransform: 'capitalize' },
    topExVol: { fontSize: 12, fontWeight: '600', color: theme.text },
  });
}
