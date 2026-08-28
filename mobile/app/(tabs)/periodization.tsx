import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { Calendar, TrendingUp, Zap, Dumbbell, Coffee } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { LoadingScreen } from '../../src/components';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';

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
  const { theme } = useTheme();
  const s = makeStyles(theme);
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
    <View style={s.container}>
      <Text style={s.title}>Periodization</Text>
      <Text style={s.subtitle}>Structured training blocks</Text>

      <View style={s.goalRow}>
        {GOALS.map((g) => (
          <TouchableOpacity
            key={g}
            style={[s.goalBtn, selectedGoal === g && s.goalBtnActive]}
            onPress={() => generatePlan(g)}
          >
            <Text style={[s.goalText, selectedGoal === g && s.goalTextActive]}>
              {g.charAt(0).toUpperCase() + g.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {plan && (
        <>
          <View style={s.planHeader}>
            <Calendar size={16} color={theme.primaryLight} />
            <Text style={s.planName}>{plan.name}</Text>
            <Text style={s.planWeeks}>{plan.duration_weeks} weeks</Text>
          </View>

          <Text style={s.rationale}>{plan.rationale}</Text>

          <FlatList
            data={plan.weeks}
            keyExtractor={(i) => i.week.toString()}
            contentContainerStyle={s.list}
            renderItem={({ item }) => {
              const color = PHASE_COLORS[item.phase] || '#818CF8';
              const Icon = PHASE_ICONS[item.phase] || Dumbbell;
              const isCurrent = item.week === plan.current_week;
              return (
                <View style={[s.weekCard, isCurrent && { borderColor: color }]}>
                  <View style={s.weekLeft}>
                    <View style={[s.phaseIcon, { backgroundColor: color + '20' }]}>
                      <Icon size={16} color={color} />
                    </View>
                    <View style={s.weekInfo}>
                      <Text style={s.weekTitle}>Week {item.week}</Text>
                      <Text style={[s.phaseName, { color }]}>{item.phase}</Text>
                      <Text style={s.weekNotes}>{item.notes}</Text>
                    </View>
                  </View>
                  <View style={s.weekStats}>
                    <View style={s.statRow}>
                      <Text style={s.statLabel}>Vol</Text>
                      <View style={s.barBg}>
                        <View style={[s.barFill, { width: `${item.volume_pct}%`, backgroundColor: theme.primaryLight }]} />
                      </View>
                      <Text style={s.statValue}>{item.volume_pct}%</Text>
                    </View>
                    <View style={s.statRow}>
                      <Text style={s.statLabel}>Int</Text>
                      <View style={s.barBg}>
                        <View style={[s.barFill, { width: `${item.intensity_pct}%`, backgroundColor: theme.orange }]} />
                      </View>
                      <Text style={s.statValue}>{item.intensity_pct}%</Text>
                    </View>
                    <Text style={s.daysText}>{item.days_per_week}d/week</Text>
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

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 16 },
    goalRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
    goalBtn: {
      flex: 1, paddingVertical: 10, borderRadius: 12,
      backgroundColor: theme.surface, alignItems: 'center',
    },
    goalBtnActive: { backgroundColor: theme.primary },
    goalText: { fontSize: 13, color: theme.textMuted, fontWeight: '500' },
    goalTextActive: { color: theme.text },
    planHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
    planName: { fontSize: 16, fontWeight: '600', color: theme.text, flex: 1 },
    planWeeks: { fontSize: 13, color: theme.textMuted },
    rationale: { fontSize: 13, color: theme.textSecondary, marginBottom: 16, lineHeight: 18 },
    list: { paddingBottom: 40 },
    weekCard: {
      flexDirection: 'row', backgroundColor: theme.surface, borderRadius: 12,
      padding: 14, marginBottom: 8, borderWidth: 1, borderColor: theme.border,
    },
    weekLeft: { flexDirection: 'row', flex: 1, gap: 10 },
    phaseIcon: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
    weekInfo: { flex: 1 },
    weekTitle: { fontSize: 14, fontWeight: '600', color: theme.text },
    phaseName: { fontSize: 12, fontWeight: '500', textTransform: 'capitalize' },
    weekNotes: { fontSize: 11, color: theme.textMuted, marginTop: 2 },
    weekStats: { width: 90, justifyContent: 'center' },
    statRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 4 },
    statLabel: { fontSize: 10, color: theme.textMuted, width: 18 },
    barBg: { flex: 1, height: 3, backgroundColor: theme.surfaceHover, borderRadius: 2 },
    barFill: { height: 3, borderRadius: 2 },
    statValue: { fontSize: 10, color: theme.textSecondary, width: 28, textAlign: 'right' },
    daysText: { fontSize: 10, color: theme.textMuted, textAlign: 'right', marginTop: 2 },
  });
}
