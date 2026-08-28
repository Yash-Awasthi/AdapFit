import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { Calendar, TrendingUp, Zap, Dumbbell, Coffee } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { LoadingScreen } from '../../src/components';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';

const API = API_BASE_URL;

interface WeekPlan {
  week: number;
  phase: string;
  volume_pct: number;
  intensity_pct: number;
  focus: string;
  days_per_week: number;
  target_acwr: number;
  notes: string;
}

interface Plan {
  plan_id: string;
  name: string;
  duration_weeks: number;
  start_date: string;
  end_date: string;
  current_week: number;
  weeks: WeekPlan[];
  rationale: string;
}

const PHASE_COLORS: Record<string, string> = {
  accumulation: '#818CF8',
  intensification: '#F97316',
  peak: '#EF4444',
  deload: '#22C55E',
};

const PHASE_ICONS: Record<string, any> = {
  accumulation: Dumbbell,
  intensification: Zap,
  peak: TrendingUp,
  deload: Coffee,
};

export default function PeriodizationScreen() {
  const userId = useUserStore((s) => s.userId);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [selectedGoal, setSelectedGoal] = useState('strength');
  const [loading, setLoading] = useState(true);

  const GOALS = ['strength', 'hypertrophy', 'endurance'];

  useEffect(() => { fetchPlan(); }, [selectedGoal]);

  async function fetchPlan() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/periodization?user_id=${userId}`);
      if (res.ok) setPlan(await res.json());
    } catch {}
    setLoading(false);
  }

  async function generatePlan(goal: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setSelectedGoal(goal);
    try {
      const res = await fetch(`${API}/api/v1/periodization?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, current_readiness: 'MODERATE' }),
      });
      if (res.ok) setPlan(await res.json());
    } catch {}
  }

  if (loading) return <LoadingScreen />;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Periodization</Text>
      <Text style={styles.subtitle}>Structured training blocks</Text>

      <View style={styles.goalRow}>
        {GOALS.map((g) => (
          <TouchableOpacity
            key={g}
            style={[styles.goalBtn, selectedGoal === g && styles.goalBtnActive]}
            onPress={() => generatePlan(g)}
          >
            <Text style={[styles.goalText, selectedGoal === g && styles.goalTextActive]}>
              {g.charAt(0).toUpperCase() + g.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {plan && (
        <>
          <View style={styles.planHeader}>
            <Calendar size={16} color="#818CF8" />
            <Text style={styles.planName}>{plan.name}</Text>
            <Text style={styles.planWeeks}>{plan.duration_weeks} weeks</Text>
          </View>

          <Text style={styles.rationale}>{plan.rationale}</Text>

          <FlatList
            data={plan.weeks}
            keyExtractor={(i) => i.week.toString()}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => {
              const color = PHASE_COLORS[item.phase] || '#818CF8';
              const Icon = PHASE_ICONS[item.phase] || Dumbbell;
              const isCurrent = item.week === plan.current_week;
              return (
                <View style={[styles.weekCard, isCurrent && { borderColor: color }]}>
                  <View style={styles.weekLeft}>
                    <View style={[styles.phaseIcon, { backgroundColor: color + '20' }]}>
                      <Icon size={16} color={color} />
                    </View>
                    <View style={styles.weekInfo}>
                      <Text style={styles.weekTitle}>Week {item.week}</Text>
                      <Text style={[styles.phaseName, { color }]}>{item.phase}</Text>
                      <Text style={styles.weekNotes}>{item.notes}</Text>
                    </View>
                  </View>
                  <View style={styles.weekStats}>
                    <View style={styles.statRow}>
                      <Text style={styles.statLabel}>Vol</Text>
                      <View style={styles.barBg}>
                        <View style={[styles.barFill, { width: `${item.volume_pct}%`, backgroundColor: '#818CF8' }]} />
                      </View>
                      <Text style={styles.statValue}>{item.volume_pct}%</Text>
                    </View>
                    <View style={styles.statRow}>
                      <Text style={styles.statLabel}>Int</Text>
                      <View style={styles.barBg}>
                        <View style={[styles.barFill, { width: `${item.intensity_pct}%`, backgroundColor: '#F97316' }]} />
                      </View>
                      <Text style={styles.statValue}>{item.intensity_pct}%</Text>
                    </View>
                    <Text style={styles.daysText}>{item.days_per_week}d/week</Text>
                  </View>
                </View>
              );
            }}
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', padding: 20 },
  title: { fontSize: 28, fontWeight: '700', color: '#F8FAFC', marginTop: 48 },
  subtitle: { fontSize: 14, color: '#8B96AB', marginBottom: 16 },
  goalRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  goalBtn: {
    flex: 1, paddingVertical: 10, borderRadius: 12,
    backgroundColor: '#1E293B', alignItems: 'center',
  },
  goalBtnActive: { backgroundColor: '#4F46E5' },
  goalText: { fontSize: 13, color: '#8B96AB', fontWeight: '500' },
  goalTextActive: { color: '#F8FAFC' },
  planHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  planName: { fontSize: 16, fontWeight: '600', color: '#F8FAFC', flex: 1 },
  planWeeks: { fontSize: 13, color: '#8B96AB' },
  rationale: { fontSize: 13, color: '#94A3B8', marginBottom: 16, lineHeight: 18 },
  list: { paddingBottom: 40 },
  weekCard: {
    flexDirection: 'row', backgroundColor: '#1E293B', borderRadius: 12,
    padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#334155',
  },
  weekLeft: { flexDirection: 'row', flex: 1, gap: 10 },
  phaseIcon: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  weekInfo: { flex: 1 },
  weekTitle: { fontSize: 14, fontWeight: '600', color: '#F8FAFC' },
  phaseName: { fontSize: 12, fontWeight: '500', textTransform: 'capitalize' },
  weekNotes: { fontSize: 11, color: '#8B96AB', marginTop: 2 },
  weekStats: { width: 90, justifyContent: 'center' },
  statRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 4 },
  statLabel: { fontSize: 10, color: '#8B96AB', width: 18 },
  barBg: { flex: 1, height: 3, backgroundColor: '#334155', borderRadius: 2 },
  barFill: { height: 3, borderRadius: 2 },
  statValue: { fontSize: 10, color: '#94A3B8', width: 28, textAlign: 'right' },
  daysText: { fontSize: 10, color: '#8B96AB', textAlign: 'right', marginTop: 2 },
});
