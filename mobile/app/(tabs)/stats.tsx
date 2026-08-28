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
    return <View style={styles.container}><Text style={styles.loadingText}>Loading stats...</Text></View>;
  }

  if (!stats || stats.total_workouts === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Workout Stats</Text>
        <View style={styles.emptyCard}>
          <Dumbbell size={40} color="#334155" />
          <Text style={styles.emptyText}>No workouts yet</Text>
          <Text style={styles.emptySubtext}>Complete workouts to see your stats here</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 100 }}>
      <Text style={styles.title}>Workout Stats</Text>

      {/* Summary Cards */}
      <View style={styles.summaryGrid}>
        <View style={styles.summaryCard}>
          <Dumbbell size={20} color="#818CF8" />
          <Text style={styles.summaryValue}>{stats.total_workouts}</Text>
          <Text style={styles.summaryLabel}>Workouts</Text>
        </View>
        <View style={styles.summaryCard}>
          <TrendingUp size={20} color="#22C55E" />
          <Text style={styles.summaryValue}>{(stats.total_volume_kg / 1000).toFixed(1)}k</Text>
          <Text style={styles.summaryLabel}>kg Volume</Text>
        </View>
        <View style={styles.summaryCard}>
          <Clock size={20} color="#F59E0B" />
          <Text style={styles.summaryValue}>{Math.round(stats.total_duration_minutes / 60)}h</Text>
          <Text style={styles.summaryLabel}>Total Time</Text>
        </View>
        <View style={styles.summaryCard}>
          <Zap size={20} color="#EF4444" />
          <Text style={styles.summaryValue}>{stats.avg_session_rpe}</Text>
          <Text style={styles.summaryLabel}>Avg RPE</Text>
        </View>
      </View>

      {/* Muscle Distribution */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Muscle Distribution</Text>
        <View style={styles.muscleChart}>
          {Object.entries(stats.muscle_distribution).slice(0, 8).map(([muscle, pct]) => (
            <View key={muscle} style={styles.muscleRow}>
              <View style={[styles.muscleDot, { backgroundColor: MUSCLE_COLORS[muscle] || '#64748B' }]} />
              <Text style={styles.muscleName}>{muscle}</Text>
              <View style={styles.muscleBarBg}>
                <View style={[styles.muscleBarFill, { width: `${pct}%`, backgroundColor: MUSCLE_COLORS[muscle] || '#64748B' }]} />
              </View>
              <Text style={styles.musclePct}>{pct}%</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Personal Records */}
      {stats.personal_records.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Personal Records</Text>
          {stats.personal_records.slice(0, 5).map((pr, i) => (
            <View key={i} style={styles.prRow}>
              <Trophy size={16} color={i === 0 ? '#F59E0B' : i === 1 ? '#94A3B8' : '#CD7F32'} />
              <View style={styles.prInfo}>
                <Text style={styles.prExercise}>{pr.exercise_id.replace(/-/g, ' ')}</Text>
                <Text style={styles.prDate}>{pr.date}</Text>
              </View>
              <Text style={styles.prWeight}>{pr.weight_kg}kg × {pr.reps}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Monthly Comparison */}
      {stats.monthly_comparison.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Monthly Trend</Text>
          <View style={styles.monthlyChart}>
            {stats.monthly_comparison.slice(0, 6).reverse().map((m, i) => {
              const maxWorkouts = Math.max(...stats.monthly_comparison.map(x => x.workouts), 1);
              const barHeight = (m.workouts / maxWorkouts) * 80;
              return (
                <View key={i} style={styles.monthBar}>
                  <Text style={styles.monthValue}>{m.workouts}</Text>
                  <View style={[styles.monthFill, { height: barHeight }]} />
                  <Text style={styles.monthLabel}>{m.month.slice(5)}</Text>
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Top Exercises */}
      {stats.top_exercises.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top Exercises by Volume</Text>
          {stats.top_exercises.map((ex, i) => (
            <View key={i} style={styles.topExRow}>
              <Text style={styles.topExRank}>#{i + 1}</Text>
              <Text style={styles.topExName}>{ex.exercise_id.replace(/-/g, ' ')}</Text>
              <Text style={styles.topExVol}>{(ex.total_volume / 1000).toFixed(1)}k kg</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', padding: 20 },
  title: { fontSize: 28, fontWeight: '700', color: '#F8FAFC', marginTop: 48, marginBottom: 16 },
  loadingText: { color: '#8B96AB', textAlign: 'center', marginTop: 100 },

  // Empty state
  emptyCard: { backgroundColor: '#1E293B', borderRadius: 16, padding: 40, alignItems: 'center' },
  emptyText: { fontSize: 18, fontWeight: '600', color: '#F8FAFC', marginTop: 12 },
  emptySubtext: { fontSize: 13, color: '#8B96AB', marginTop: 4 },

  // Summary grid
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  summaryCard: {
    width: (SCREEN_WIDTH - 8) / 2,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  summaryValue: { fontSize: 22, fontWeight: '800', color: '#F8FAFC', marginTop: 6 },
  summaryLabel: { fontSize: 11, color: '#8B96AB', marginTop: 2 },

  // Sections
  section: { marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#F8FAFC', marginBottom: 10 },

  // Muscle distribution
  muscleChart: { backgroundColor: '#1E293B', borderRadius: 12, padding: 14 },
  muscleRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  muscleDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
  muscleName: { fontSize: 12, color: '#CBD5E1', width: 80, textTransform: 'capitalize' },
  muscleBarBg: { flex: 1, height: 8, backgroundColor: '#334155', borderRadius: 4, overflow: 'hidden' },
  muscleBarFill: { height: 8, borderRadius: 4 },
  musclePct: { fontSize: 11, color: '#8B96AB', width: 40, textAlign: 'right' },

  // PRs
  prRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    gap: 8,
  },
  prInfo: { flex: 1 },
  prExercise: { fontSize: 13, fontWeight: '600', color: '#F8FAFC', textTransform: 'capitalize' },
  prDate: { fontSize: 10, color: '#8B96AB' },
  prWeight: { fontSize: 14, fontWeight: '700', color: '#F59E0B' },

  // Monthly chart
  monthlyChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    height: 130,
  },
  monthBar: { alignItems: 'center', flex: 1 },
  monthValue: { fontSize: 10, color: '#8B96AB', marginBottom: 4 },
  monthFill: { width: 24, backgroundColor: '#818CF8', borderRadius: 4, minHeight: 4 },
  monthLabel: { fontSize: 10, color: '#8B96AB', marginTop: 4 },

  // Top exercises
  topExRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 10,
    marginBottom: 4,
  },
  topExRank: { fontSize: 14, fontWeight: '700', color: '#818CF8', width: 30 },
  topExName: { flex: 1, fontSize: 13, color: '#CBD5E1', textTransform: 'capitalize' },
  topExVol: { fontSize: 12, fontWeight: '600', color: '#F8FAFC' },
});
