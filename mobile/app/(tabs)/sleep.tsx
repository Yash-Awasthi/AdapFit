/**
 * Sleep — the journal, its analysis, and a bedtime plan.
 *
 * A manual log records bedtime, wake time and how the night felt. Stages only
 * appear when a wearable measured them; the score is built from whatever was
 * measured and says which parts that was.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar,
  ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { colors, spacing, typography, getScoreColor } from '../../src/theme';
import { GlassCard, ScoreRing, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, deleteJson, postJson, putJson } from '../../src/services/http';

const TINT = '#6366F1';
const STAGE_COLORS: Record<string, string> = { deep: '#4F46E5', rem: '#8B5CF6', light: '#06B6D4', awake: '#EF4444' };
const MEASURED_LABELS: Record<string, string> = {
  duration: 'duration', efficiency: 'efficiency', deep_sleep: 'deep sleep', rem_sleep: 'REM',
  consistency: 'schedule', interruptions: 'awakenings',
};

interface Stage { name: string; minutes: number; percentage: number }
interface Recommendation { category: string; priority: string; title: string; description: string; tips: string[] }
interface PlanOption { bedtime: string; cycles: number; sleep_hours: number; within_recommended: boolean }
interface Analysis {
  score: number;
  grade: string | null;
  quality_label: string;
  nights_analyzed: number;
  avg_duration_hours: number | null;
  avg_efficiency_pct: number | null;
  bedtime_consistency_min: number | null;
  stage_breakdown: Stage[];
  measured: string[];
  debt: { debt_hours: number | null; nights_counted: number; short_nights?: number; target_hours: number; recovery_plan?: string };
  trend: { trend: string; average_score?: number; data_points: number };
  recommendations: Recommendation[];
  bedtime_plan: { target_wake: string; minutes_to_fall_asleep: number; onset_source: string; options: PlanOption[] } | null;
}
interface Night { id: string; date: string; bedtime: string; wake_time: string; total_minutes: number; source: string; quality_rating: number | null; score: number }

const pad = (n: number) => n.toString().padStart(2, '0');
const shift = (clock: string, minutes: number) => {
  const [h, m] = clock.split(':').map(Number);
  const t = (((h * 60 + m + minutes) % 1440) + 1440) % 1440;
  return `${pad(Math.floor(t / 60))}:${pad(t % 60)}`;
};

function ClockStepper({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <View style={styles.stepper}>
      <Text style={styles.stepperLabel}>{label}</Text>
      <View style={styles.stepperRow}>
        <TouchableOpacity accessibilityLabel={`${label} 15 minutes earlier`} onPress={() => onChange(shift(value, -15))}>
          <Ionicons name="remove-circle-outline" size={28} color={colors.text.secondary} />
        </TouchableOpacity>
        <Text style={styles.stepperValue}>{value}</Text>
        <TouchableOpacity accessibilityLabel={`${label} 15 minutes later`} onPress={() => onChange(shift(value, 15))}>
          <Ionicons name="add-circle-outline" size={28} color={colors.text.secondary} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

export default function SleepScreen() {
  const [bedtime, setBedtime] = useState('23:00');
  const [wake, setWake] = useState('07:00');
  const [quality, setQuality] = useState<number | null>(null);
  const [awakenings, setAwakenings] = useState<number | null>(null);
  const [targetWake, setTargetWake] = useState('06:30');
  const [busy, setBusy] = useState(false);

  const { data, loading, refresh, refreshing, reload } = useApis<{ analysis: Analysis; logs: Night[] }>({
    analysis: '/sleep/analysis?days=7',
    logs: '/sleep/logs?days=14',
  });
  const analysis = data.analysis;
  const logs = asArray<Night>(data.logs).slice().reverse();
  const hasData = !!analysis && analysis.nights_analyzed > 0;

  const logNight = useCallback(async () => {
    setBusy(true);
    const result = await postJson('/sleep/logs', {
      bedtime, wake_time: wake, source: 'manual',
      quality_rating: quality ?? undefined,
      interruptions: awakenings ?? undefined,
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not saved', 'The night could not be logged. Check your connection and try again.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setQuality(null);
    setAwakenings(null);
    await reload();
  }, [bedtime, wake, quality, awakenings, reload]);

  const removeNight = useCallback(async (id: string) => {
    if (await deleteJson(`/sleep/logs/${id}`)) await reload();
    else Alert.alert('Not deleted', 'The night could not be removed.');
  }, [reload]);

  const saveTarget = useCallback(async () => {
    if (await putJson('/sleep/profile', { target_wake: targetWake })) await reload();
    else Alert.alert('Not saved', 'The wake time could not be saved.');
  }, [targetWake, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color={TINT} />
      </View>
    );
  }

  const scoreColor = hasData ? getScoreColor(analysis!.score) : colors.text.muted;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={TINT} />}
      >
        <LinearGradient colors={[TINT, '#8B5CF6', colors.bg.deep]} style={styles.hero}>
          <Text style={[typography.body.sm, styles.heroMuted]}>Sleep</Text>
          {hasData ? (
            <View style={styles.heroRow}>
              <ScoreRing score={analysis!.score} size={132} strokeWidth={10} color={scoreColor} label="SCORE" />
              <View style={styles.heroStats}>
                <Text style={styles.heroValue}>{analysis!.avg_duration_hours}h</Text>
                <Text style={styles.heroMuted}>average over {analysis!.nights_analyzed} night{analysis!.nights_analyzed === 1 ? '' : 's'}</Text>
                {analysis!.trend.trend !== 'insufficient_data' && (
                  <Text style={[styles.heroMuted, { marginTop: 6, textTransform: 'capitalize' }]}>Trend: {analysis!.trend.trend}</Text>
                )}
                <Text style={[styles.heroMuted, { marginTop: 6 }]}>
                  From {analysis!.measured.map((m) => MEASURED_LABELS[m] ?? m).join(', ')}
                </Text>
              </View>
            </View>
          ) : (
            <Text style={[typography.heading.h2, { color: '#fff', marginTop: 8 }]}>Log last night to begin</Text>
          )}
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Log a Night" icon="moon" iconColor={TINT} />
          <GlassCard>
            <View style={styles.row}>
              <ClockStepper label="Bedtime" value={bedtime} onChange={setBedtime} />
              <ClockStepper label="Woke up" value={wake} onChange={setWake} />
            </View>
            <Text style={styles.fieldLabel}>How did it feel? (optional)</Text>
            <View style={styles.chipRow}>
              {[1, 2, 3, 4, 5].map((v) => (
                <TouchableOpacity key={v} style={[styles.chip, quality === v && styles.chipActive]}
                  onPress={() => setQuality(quality === v ? null : v)} accessibilityLabel={`Quality ${v} of 5`}>
                  <Text style={[styles.chipText, quality === v && styles.chipTextActive]}>{v}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.fieldLabel}>Times you woke up (optional)</Text>
            <View style={styles.chipRow}>
              {[0, 1, 2, 3, 4, 5].map((v) => (
                <TouchableOpacity key={v} style={[styles.chip, awakenings === v && styles.chipActive]}
                  onPress={() => setAwakenings(awakenings === v ? null : v)}>
                  <Text style={[styles.chipText, awakenings === v && styles.chipTextActive]}>{v === 5 ? '5+' : v}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity style={styles.primaryBtn} onPress={logNight} disabled={busy}>
              <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save night'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>

        {hasData && analysis!.stage_breakdown.length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Sleep Stages" subtitle="From your wearable" icon="layers" iconColor={TINT} />
            <GlassCard>
              {analysis!.stage_breakdown.map((st) => (
                <View key={st.name} style={styles.stageRow}>
                  <Text style={styles.stageName}>{st.name}</Text>
                  <View style={styles.barBg}>
                    <View style={[styles.barFill, { width: `${Math.min(100, st.percentage)}%`, backgroundColor: STAGE_COLORS[st.name] ?? TINT }]} />
                  </View>
                  <Text style={styles.stageValue}>{Math.round(st.minutes)}m</Text>
                </View>
              ))}
            </GlassCard>
          </View>
        )}

        {hasData && analysis!.debt.debt_hours !== null && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Sleep Debt" icon="hourglass" iconColor="#F59E0B" />
            <GlassCard>
              <Text style={styles.bigValue}>{analysis!.debt.debt_hours}h</Text>
              <Text style={styles.helperText}>
                Short of {analysis!.debt.target_hours}h on {analysis!.debt.short_nights ?? 0} of {analysis!.debt.nights_counted} nights.
              </Text>
              {analysis!.debt.recovery_plan && <Text style={styles.bodyText}>{analysis!.debt.recovery_plan}</Text>}
            </GlassCard>
          </View>
        )}

        {hasData && analysis!.recommendations.length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="What To Try" icon="bulb" iconColor="#10B981" />
            {analysis!.recommendations.map((r) => (
              <GlassCard key={r.title} style={styles.cardGap}>
                <Text style={styles.recTitle}>{r.title}</Text>
                <Text style={styles.helperText}>{r.description}</Text>
                {asArray<string>(r.tips).slice(0, 3).map((tip) => (
                  <Text key={tip} style={styles.bodyText}>• {tip}</Text>
                ))}
              </GlassCard>
            ))}
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Bedtime Plan" subtitle="Wake at the end of a 90-minute cycle" icon="alarm" iconColor={TINT} />
          <GlassCard>
            {analysis?.bedtime_plan ? (
              <>
                {analysis.bedtime_plan.options.map((o) => (
                  <View key={o.cycles} style={styles.planRow}>
                    <Text style={styles.planTime}>{o.bedtime}</Text>
                    <Text style={styles.helperText}>{o.cycles} cycles · {o.sleep_hours}h{o.within_recommended ? '' : ' · below your range'}</Text>
                  </View>
                ))}
                <Text style={styles.helperText}>
                  Includes {analysis.bedtime_plan.minutes_to_fall_asleep} min to fall asleep ({analysis.bedtime_plan.onset_source}).
                </Text>
              </>
            ) : (
              <Text style={styles.helperText}>Set the time you want to wake up.</Text>
            )}
            <View style={[styles.row, { marginTop: 8 }]}>
              <ClockStepper label="Wake at" value={targetWake} onChange={setTargetWake} />
              <TouchableOpacity style={[styles.primaryBtn, styles.inlineBtn]} onPress={saveTarget}>
                <Text style={styles.primaryBtnText}>Save</Text>
              </TouchableOpacity>
            </View>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Recent Nights" icon="calendar" iconColor={TINT} />
          {logs.length === 0 ? (
            <Text style={styles.helperText}>No nights logged yet.</Text>
          ) : logs.map((n) => (
            <GlassCard key={n.id} style={styles.cardGap}>
              <View style={styles.logRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.recTitle}>{n.date}</Text>
                  <Text style={styles.helperText}>
                    {n.bedtime}–{n.wake_time} · {Math.floor(n.total_minutes / 60)}h {n.total_minutes % 60}m · score {n.score}
                    {n.source === 'wearable' ? ' · wearable' : ''}
                  </Text>
                </View>
                <TouchableOpacity onPress={() => removeNight(n.id)} accessibilityLabel={`Delete night of ${n.date}`}>
                  <Ionicons name="trash-outline" size={18} color={colors.text.muted} />
                </TouchableOpacity>
              </View>
            </GlassCard>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 16 },
  heroStats: { flex: 1 },
  heroValue: { color: '#fff', fontSize: 30, fontWeight: '800' },
  heroMuted: { color: 'rgba(255,255,255,0.75)', fontSize: 13 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12 },
  stepper: { flex: 1 },
  stepperLabel: { color: colors.text.muted, fontSize: 12, marginBottom: 6 },
  stepperRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  stepperValue: { color: colors.text.primary, fontSize: 22, fontWeight: '700', minWidth: 64, textAlign: 'center' },
  fieldLabel: { color: colors.text.secondary, fontSize: 13, fontWeight: '600', marginTop: 14, marginBottom: 8 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { minWidth: 40, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, alignItems: 'center', backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: TINT + '25', borderColor: TINT },
  chipText: { color: colors.text.muted, fontSize: 13 },
  chipTextActive: { color: TINT, fontWeight: '700' },
  primaryBtn: { backgroundColor: TINT, borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 16 },
  inlineBtn: { marginTop: 0, paddingHorizontal: 20 },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  stageRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  stageName: { color: colors.text.secondary, width: 52, textTransform: 'capitalize', fontSize: 13 },
  barBg: { flex: 1, height: 8, borderRadius: 4, backgroundColor: colors.bg.card, marginHorizontal: 8 },
  barFill: { height: 8, borderRadius: 4 },
  stageValue: { color: colors.text.muted, width: 44, textAlign: 'right', fontSize: 12 },
  bigValue: { color: colors.text.primary, fontSize: 28, fontWeight: '800' },
  helperText: { color: colors.text.muted, fontSize: 13, marginTop: 4, lineHeight: 18 },
  bodyText: { color: colors.text.secondary, fontSize: 13, marginTop: 6, lineHeight: 18 },
  recTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  cardGap: { marginBottom: 10 },
  planRow: { flexDirection: 'row', alignItems: 'baseline', gap: 12, paddingVertical: 4 },
  planTime: { color: colors.text.primary, fontSize: 20, fontWeight: '700', width: 64 },
  logRow: { flexDirection: 'row', alignItems: 'center' },
});
