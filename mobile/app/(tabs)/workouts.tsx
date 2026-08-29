/**
 * Workouts — Exercise library, plans, active workout, and PR tracking
 */
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl, Alert, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets, getScoreColor } from '../../src/theme';

import { API_V1 as API } from '../../src/services/config';
const api = async (p: string, o?: RequestInit) => { try { const r = await fetch(`${API}${p}`, { headers: { 'Content-Type': 'application/json' }, ...o }); return r.ok ? await r.json() : null; } catch { return null; } };

const MUSCLE_GROUPS = ['All', 'chest', 'back', 'shoulders', 'quads', 'hamstrings', 'glutes', 'core', 'biceps', 'triceps'];
const DIFFICULTY_COLORS: Record<string, string> = { beginner: colors.health.calm, intermediate: colors.health.energy, advanced: colors.health.danger };

export default function WorkoutsScreen() {
  const [exercises, setExercises] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [prs, setPrs] = useState<any>({});
  const [activeTab, setActiveTab] = useState<'library' | 'plans' | 'stats'>('library');
  const [muscleFilter, setMuscleFilter] = useState('All');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeSession, setActiveSession] = useState<any>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const mP = muscleFilter !== 'All' ? `?muscle_group=${muscleFilter}` : '';
    const [e, p, st, pr] = await Promise.allSettled([
      api(`/workout-engine/exercises${mP}`), api('/workout-engine/plans'),
      api('/workout-engine/stats'), api('/workout-engine/prs'),
    ]);
    if (e.status === 'fulfilled') setExercises(e.value?.exercises || []);
    if (p.status === 'fulfilled') setPlans(p.value?.plans || []);
    if (st.status === 'fulfilled') setStats(st.value || {});
    if (pr.status === 'fulfilled') setPrs(pr.value?.personal_records || {});
    setLoading(false);
  }, [muscleFilter]);

  useEffect(() => { load(); }, [load]);
  const onRefresh = useCallback(async () => { setRefreshing(true); await load(); setRefreshing(false); }, [load]);

  const startWorkout = async () => {
    const r = await api('/workout-engine/session/start', { method: 'POST', body: '{}' });
    if (r?.session_id) { setActiveSession(r); Alert.alert('Workout Started!', `Session: ${r.session_id}\nTime: ${r.start_time}`); }
  };

  const completeWorkout = async () => {
    if (!activeSession) return;
    const r = await api(`/workout-engine/session/complete/${activeSession.session_id}`, { method: 'POST' });
    if (r?.completed) { Alert.alert('Workout Complete!', `Duration: ${r.duration_min}min\nVolume: ${r.total_volume}kg\nCalories: ${r.total_calories}`); setActiveSession(null); load(); }
  };

  return (
    <ScrollView style={ws.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}>
      <View style={ws.header}>
        <Text style={typography.heading.h1}>Workouts</Text>
        <Text style={typography.body.sm}>Exercise library, plans & tracking</Text>
      </View>

      {/* Active Workout Banner */}
      {activeSession && (
        <View style={ws.activeBanner}>
          <View style={{ flex: 1 }}><Text style={[typography.label.lg, { color: '#FFF' }]}>Workout in Progress</Text><Text style={[typography.body.xs, { color: '#FFFFFFCC' }]}>Started at {activeSession.start_time}</Text></View>
          <TouchableOpacity style={ws.completeBtn} onPress={completeWorkout}><Text style={[typography.label.lg, { color: colors.health.danger }]}>Finish</Text></TouchableOpacity>
        </View>
      )}

      {/* Tabs */}
      <View style={ws.tabRow}>
        {(['library', 'plans', 'stats'] as const).map(t => (
          <TouchableOpacity key={t} style={[ws.tab, activeTab === t && ws.tabActive]} onPress={() => setActiveTab(t)}>
            <Text style={[ws.tabText, activeTab === t && ws.tabTextActive]}>{t.charAt(0).toUpperCase() + t.slice(1)}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Library */}
      {activeTab === 'library' && (
        <>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: spacing.md }}>
            <View style={{ flexDirection: 'row', paddingHorizontal: spacing.lg, gap: spacing.sm }}>
              {MUSCLE_GROUPS.map(m => (
                <TouchableOpacity key={m} style={[ws.pill, muscleFilter === m && ws.pillActive]} onPress={() => setMuscleFilter(m)}>
                  <Text style={[ws.pillText, muscleFilter === m && ws.pillTextActive]}>{m === 'All' ? 'All' : m.charAt(0).toUpperCase() + m.slice(1)}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
          {loading ? <ActivityIndicator color={colors.primary} style={{ marginTop: 30 }} /> : exercises.map((ex, i) => (
            <View key={i} style={ws.exerciseCard}>
              <View style={{ flex: 1 }}>
                <Text style={typography.label.lg}>{ex.name}</Text>
                <Text style={typography.body.xs}>{ex.muscle_groups?.join(', ')} • {ex.equipment}</Text>
              </View>
              <View style={[ws.diffBadge, { backgroundColor: (DIFFICULTY_COLORS[ex.difficulty] || colors.text.muted) + '20' }]}>
                <Text style={[typography.body.xs, { color: DIFFICULTY_COLORS[ex.difficulty] || colors.text.muted }]}>{ex.difficulty}</Text>
              </View>
            </View>
          ))}
          <TouchableOpacity style={[presets.buttonPrimary, { margin: spacing.lg }]} onPress={startWorkout}>
            <Ionicons name="play" size={18} color="#FFF" />
            <Text style={[typography.heading.h4, { color: '#FFF' }]}>Start Workout</Text>
          </TouchableOpacity>
        </>
      )}

      {/* Plans */}
      {activeTab === 'plans' && plans.map((p, i) => (
        <View key={i} style={ws.planCard}>
          <Text style={typography.heading.h4}>{p.name}</Text>
          <Text style={typography.body.sm}>{p.description}</Text>
          <View style={{ flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm }}>
            <View style={ws.planMetaItem}>
              <Ionicons name="time-outline" size={12} color={colors.text.muted} />
              <Text style={typography.body.xs}>{p.duration}min</Text>
            </View>
            <View style={ws.planMetaItem}>
              <Ionicons name="flag-outline" size={12} color={colors.text.muted} />
              <Text style={typography.body.xs}>{p.goal}</Text>
            </View>
            <View style={ws.planMetaItem}>
              <Ionicons name="stats-chart-outline" size={12} color={colors.text.muted} />
              <Text style={typography.body.xs}>{p.exercises} exercises</Text>
            </View>
          </View>
        </View>
      ))}

      {/* Stats */}
      {activeTab === 'stats' && (
        <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
          <View style={ws.statsGrid}>
            {[{ label: 'Workouts', value: stats.total_workouts || 0, icon: 'barbell' }, { label: 'Volume', value: `${((stats.total_volume_kg || 0) / 1000).toFixed(1)}t`, icon: 'trending-up' }, { label: 'Calories', value: stats.total_calories || 0, icon: 'flame' }, { label: 'Hours', value: ((stats.total_minutes || 0) / 60).toFixed(1), icon: 'time' }].map((s, i) => (
              <View key={i} style={ws.statItem}>
                <Ionicons name={s.icon as any} size={20} color={colors.primary} />
                <Text style={[typography.metric.small, { color: colors.primary }]}>{s.value}</Text>
                <Text style={typography.body.xs}>{s.label}</Text>
              </View>
            ))}
          </View>
          {Object.keys(prs).length > 0 && (
            <>
              <Text style={[typography.heading.h4, { marginTop: spacing.lg, marginBottom: spacing.sm }]}>Personal Records</Text>
              {Object.entries(prs).map(([ex, data]: [string, any]) => (
                <View key={ex} style={ws.prRow}>
                  <Text style={typography.label.lg}>{ex}</Text>
                  <Text style={[typography.label.lg, { color: colors.health.energy }]}>{data.weight}kg × {data.reps}</Text>
                </View>
              ))}
            </>
          )}
        </View>
      )}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const ws = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.primary },
  header: { padding: spacing.screenPadding, paddingTop: 50, paddingBottom: spacing.lg },
  activeBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.primary, marginHorizontal: spacing.lg, marginBottom: spacing.lg, padding: spacing.lg, borderRadius: radius.lg },
  completeBtn: { backgroundColor: '#FFF', paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, borderRadius: radius.md },
  tabRow: { flexDirection: 'row', marginHorizontal: spacing.lg, marginBottom: spacing.lg, backgroundColor: colors.bg.card, borderRadius: radius.md, padding: spacing.xs, borderWidth: 1, borderColor: colors.surface.border },
  tab: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: radius.sm - 2 },
  tabActive: { backgroundColor: colors.primary },
  tabText: { fontSize: typography.fontSize.sm, color: colors.text.muted, fontWeight: typography.fontWeight.medium },
  tabTextActive: { color: '#FFF' },
  pill: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs + 2, borderRadius: radius.pill, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  pillActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  pillText: { fontSize: typography.fontSize.sm, color: colors.text.muted },
  pillTextActive: { color: '#FFF' },
  exerciseCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, marginHorizontal: spacing.lg, padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.surface.border },
  diffBadge: { paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: radius.badge },
  planCard: { backgroundColor: colors.bg.card, marginHorizontal: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, marginBottom: spacing.md, borderWidth: 1, borderColor: colors.surface.border },
  planMetaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  statItem: { width: '48%', backgroundColor: colors.bg.input, padding: spacing.lg, borderRadius: radius.md, alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border },
  prRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
});
