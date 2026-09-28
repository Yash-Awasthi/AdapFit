/**
 * Circadian Rhythm — chronotype, energy curve and the day it implies.
 *
 * Choosing a chronotype refetches the schedule and energy curve rather than
 * re-styling a fixed one: the peak hours, exercise window and wind-down time
 * all move with it, and a Wolf shown a Bear's schedule is worse than no
 * schedule at all.
 */
import React, { useMemo, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Dimensions, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { InteractiveBarChart } from '../../src/components/InteractiveCharts';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray, asNumber } from '../../src/services/http';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type ChronotypeKey = 'lion' | 'bear' | 'wolf' | 'dolphin';

const CHRONOTYPES: { key: ChronotypeKey; label: string; icon: string; color: string }[] = [
  { key: 'lion', label: 'Lion', icon: 'sunny', color: '#F59E0B' },
  { key: 'bear', label: 'Bear', icon: 'partly-sunny', color: '#22C55E' },
  { key: 'wolf', label: 'Wolf', icon: 'moon', color: '#8B5CF6' },
  { key: 'dolphin', label: 'Dolphin', icon: 'water', color: '#3B82F6' },
];

interface ChronotypeInfo {
  name: string;
  description: string;
  wake_time: string;
  peak_hours: string;
  wind_down: string;
  best_exercise: string;
  tips: string[];
  percentage: number;
}

interface EnergyPoint {
  hour: number;
  energy_level: number;
  recommendation: string;
}

interface ScheduleBlock {
  time: string;
  activities?: string[];
  type?: string;
}

interface Schedule {
  chronotype: string;
  wake_up: string;
  [block: string]: ScheduleBlock | string;
}

interface Alertness {
  status: 'ok' | 'insufficient_data';
  curve?: { time: string; alertness: number | null }[];
  peak_window?: string;
  dip_window?: string;
  suggestions?: string[];
  message?: string;
}

interface RhythmScore {
  status: 'ok' | 'insufficient_data';
  overall_score?: number | null;
  consistency?: number;
  light_exposure?: number;
  days_of_data?: number;
  message?: string;
  tips: string[];
}

// The schedule blocks in the order a day runs, since the response is an object.
const BLOCK_ORDER = [
  'morning_routine', 'peak_productivity', 'lunch',
  'afternoon', 'exercise', 'dinner', 'wind_down',
];

const BLOCK_STYLE: Record<string, { label: string; icon: string; color: string }> = {
  morning_routine: { label: 'Morning routine', icon: 'sunny', color: '#F59E0B' },
  peak_productivity: { label: 'Deep work', icon: 'bulb', color: '#3B82F6' },
  lunch: { label: 'Lunch', icon: 'restaurant', color: '#F97316' },
  afternoon: { label: 'Afternoon', icon: 'document', color: '#8B5CF6' },
  exercise: { label: 'Exercise', icon: 'fitness', color: '#22C55E' },
  dinner: { label: 'Dinner', icon: 'restaurant', color: '#F97316' },
  wind_down: { label: 'Wind down', icon: 'moon', color: '#6366F1' },
};

function energyColor(level: number): string {
  return level >= 75 ? '#22C55E' : level >= 50 ? '#F59E0B' : '#EF4444';
}

function hourLabel(hour: number): string {
  const suffix = hour < 12 ? 'AM' : 'PM';
  const display = hour % 12 === 0 ? 12 : hour % 12;
  return `${display}${suffix}`;
}

export default function CircadianScreen() {
  const [chronotype, setChronotype] = useState<ChronotypeKey>('bear');
  const [logging, setLogging] = useState(false);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    info: ChronotypeInfo;
    energy: { energy_curve: EnergyPoint[] };
    schedule: Schedule;
    rhythm: RhythmScore;
    alertness: Alertness;
  }>({
    info: `/circadian/chronotype/${chronotype}`,
    energy: `/circadian/energy/${chronotype}`,
    schedule: `/circadian/schedule/${chronotype}`,
    rhythm: '/circadian/rhythm-score',
    alertness: '/sleep/alertness',
  });
  const alertness = data.alertness ?? null;
  const personalBars = useMemo(
    () => asArray<{ time: string; alertness: number | null }>(alertness?.curve)
      .filter((p, i) => p.alertness !== null && i % 2 === 0)
      .map((p) => ({ value: Math.round(p.alertness!), label: p.time.slice(0, 2), color: energyColor(p.alertness!) })),
    [alertness]
  );

  const info = data.info ?? null;
  const rhythm = data.rhythm ?? null;
  const curve = asArray<EnergyPoint>(data.energy?.energy_curve);
  const schedule = data.schedule ?? null;

  // Every third hour: eighteen bars do not fit a phone.
  const chartData = useMemo(
    () => curve
      .filter((_, i) => i % 3 === 0)
      .map((point) => ({
        value: Math.round(point.energy_level),
        label: hourLabel(point.hour),
        color: energyColor(point.energy_level),
      })),
    [curve]
  );

  const peak = useMemo(
    () => curve.reduce<EnergyPoint | null>((best, p) => (!best || p.energy_level > best.energy_level ? p : best), null),
    [curve]
  );

  const logSunlight = async () => {
    setLogging(true);
    // 10,000 lux for 20 minutes is the standard morning-light prescription,
    // which is what this button is for.
    const result = await postJson('/circadian/light-exposure', {
      lux: 10000,
      duration_minutes: 20,
    });
    setLogging(false);
    if (!result) {
      Alert.alert('Not recorded', 'The light exposure could not be saved.');
      return;
    }
    await reload();
  };

  return (
    <ScreenWrapper
      title="Circadian Rhythm"
      subtitle="Optimize your body clock"
      gradient={['#8B5CF6', '#6366F1']}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <SectionHeaderPremium icon="pulse" iconColor="#8B5CF6" title="Your Alertness Today" subtitle="From your own sleep times" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {alertness?.status === 'ok' ? (
          <>
            <InteractiveBarChart data={personalBars} height={160} showValues={false} />
            <Text style={styles.energyInsight}>Peak {alertness.peak_window} · dip {alertness.dip_window}</Text>
            {asArray<string>(alertness.suggestions).map((t) => <Text key={t} style={styles.infoLine}>{t}</Text>)}
          </>
        ) : (
          <Text style={styles.emptyText}>{alertness?.message ?? 'Log your sleep to see your own curve.'}</Text>
        )}
      </GlassCard>

      <SectionHeaderPremium icon="compass" iconColor="#8B5CF6" title="Chronotype Guide" subtitle="General patterns, not measured" />
      <View style={styles.chronotypeGrid}>
        {CHRONOTYPES.map((ct) => {
          const selected = ct.key === chronotype;
          return (
            <TouchableOpacity
              key={ct.key}
              style={[styles.chronotypeCard, selected && { borderColor: ct.color + '80', backgroundColor: ct.color + '10' }]}
              onPress={() => setChronotype(ct.key)}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              accessibilityLabel={`${ct.label} chronotype`}
            >
              <Ionicons name={ct.icon as any} size={28} color={ct.color} style={styles.chronotypeIcon} />
              <Text style={[styles.chronotypeType, selected && { color: ct.color }]}>{ct.label}</Text>
              <Text style={styles.chronotypeDesc} numberOfLines={2}>
                {selected && info ? info.description : ''}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {info && (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.infoTitle}>{info.name}</Text>
          <Text style={styles.infoLine}>Wake {info.wake_time} · Wind down {info.wind_down}</Text>
          <Text style={styles.infoLine}>Peak hours {info.peak_hours}</Text>
          <Text style={styles.infoLine}>Best exercise {info.best_exercise}</Text>
          <Text style={styles.infoShare}>{info.percentage}% of people share this chronotype</Text>
        </GlassCard>
      )}

      <SectionHeaderPremium icon="trending-up" iconColor="#22C55E" title="Typical Curve for This Chronotype" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {chartData.length > 0 ? (
          <>
            <InteractiveBarChart data={chartData} height={160} showValues />
            {peak && (
              <Text style={styles.energyInsight}>
                Peak energy around {hourLabel(peak.hour)}. {peak.recommendation}
              </Text>
            )}
          </>
        ) : (
          <Text style={styles.emptyText}>The energy curve could not be loaded.</Text>
        )}
      </GlassCard>

      <SectionHeaderPremium icon="sunny" iconColor="#F59E0B" title="Rhythm Regularity" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {rhythm?.status === 'ok' ? (
          <>
            <View style={styles.lightRow}>
              <View style={styles.lightStat}>
                <Ionicons name="repeat" size={24} color="#22C55E" />
                <Text style={styles.lightValue}>{asNumber(rhythm.consistency)}</Text>
                <Text style={styles.lightLabel}>Consistency</Text>
              </View>
              <View style={styles.lightStat}>
                <Ionicons name="sunny" size={24} color="#F59E0B" />
                <Text style={styles.lightValue}>{asNumber(rhythm.light_exposure)}</Text>
                <Text style={styles.lightLabel}>Light</Text>
              </View>
              <View style={styles.lightStat}>
                <Ionicons name="calendar" size={24} color="#8B5CF6" />
                <Text style={styles.lightValue}>{asNumber(rhythm.days_of_data)}</Text>
                <Text style={styles.lightLabel}>Days logged</Text>
              </View>
            </View>
            <ProgressBarPremium
              value={asNumber(rhythm.overall_score)}
              max={100}
              color="#8B5CF6"
              height={6}
              showLabel
              label="Overall rhythm score"
            />
          </>
        ) : (
          <Text style={styles.emptyText}>
            {rhythm?.message ?? 'Log your morning light and daily energy to see how regular your rhythm is.'}
          </Text>
        )}
        <TouchableOpacity
          style={styles.logButton}
          onPress={logSunlight}
          disabled={logging}
          accessibilityRole="button"
          accessibilityLabel="Log twenty minutes of morning sunlight"
        >
          <Ionicons name="sunny" size={16} color="#FFF" />
          <Text style={styles.logButtonText}>{logging ? 'Saving…' : 'Log 20 min of sunlight'}</Text>
        </TouchableOpacity>
      </GlassCard>

      <SectionHeaderPremium icon="calendar" iconColor={colors.health.calm} title="Optimal Schedule" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {schedule ? (
          <>
            <View style={styles.scheduleItem}>
              <Text style={styles.scheduleTime}>{schedule.wake_up as string}</Text>
              <View style={[styles.scheduleIcon, { backgroundColor: '#F59E0B15' }]}>
                <Ionicons name="alarm" size={14} color="#F59E0B" />
              </View>
              <Text style={styles.scheduleActivity}>Wake up</Text>
            </View>
            {BLOCK_ORDER.map((key) => {
              const block = schedule[key];
              if (!block || typeof block === 'string') return null;
              const style = BLOCK_STYLE[key];
              return (
                <View key={key} style={[styles.scheduleItem, styles.scheduleDivider]}>
                  <Text style={styles.scheduleTime}>{block.time}</Text>
                  <View style={[styles.scheduleIcon, { backgroundColor: style.color + '15' }]}>
                    <Ionicons name={style.icon as any} size={14} color={style.color} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.scheduleActivity}>{style.label}</Text>
                    {block.activities && (
                      <Text style={styles.scheduleDetail} numberOfLines={2}>
                        {block.activities.join(' · ')}
                      </Text>
                    )}
                  </View>
                </View>
              );
            })}
          </>
        ) : (
          <Text style={styles.emptyText}>The schedule could not be loaded.</Text>
        )}
      </GlassCard>

      {info?.tips?.length ? (
        <GlassCard variant="primary" style={styles.sectionCard}>
          <View style={styles.tipRow}>
            <Ionicons name="bulb" size={20} color={colors.primary} />
            <View style={{ flex: 1 }}>
              <Text style={styles.tipTitle}>Circadian Tips</Text>
              {info.tips.map((tip, i) => (
                <Text key={i} style={styles.tipText}>• {tip}</Text>
              ))}
            </View>
          </View>
        </GlassCard>
      ) : null}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  chronotypeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  chronotypeCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md) / 2, padding: spacing.md, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.surface.border, backgroundColor: colors.bg.card, alignItems: 'center' },
  chronotypeIcon: { marginBottom: spacing.xs },
  chronotypeType: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  chronotypeDesc: { fontSize: 11, color: colors.text.muted, textAlign: 'center', marginTop: 2, minHeight: 28 },

  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  infoTitle: { fontSize: 16, fontWeight: '800', color: colors.text.primary, marginBottom: spacing.xs },
  infoLine: { fontSize: 13, color: colors.text.secondary, marginTop: 2 },
  infoShare: { fontSize: 12, color: colors.text.muted, marginTop: spacing.sm },

  energyInsight: { fontSize: 13, color: colors.text.secondary, marginTop: spacing.md, lineHeight: 19 },
  emptyText: { fontSize: 13, color: colors.text.muted, lineHeight: 19 },

  lightRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.md },
  lightStat: { alignItems: 'center' },
  lightValue: { fontSize: 20, fontWeight: '800', color: colors.text.primary, marginTop: 4 },
  lightLabel: { fontSize: 11, color: colors.text.muted },

  logButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xs, marginTop: spacing.md, paddingVertical: spacing.md, borderRadius: radius.md, backgroundColor: '#F59E0B' },
  logButtonText: { color: '#FFF', fontWeight: '700', fontSize: 14 },

  scheduleItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  scheduleDivider: { borderTopWidth: 1, borderTopColor: colors.surface.divider },
  scheduleTime: { fontSize: 12, color: colors.text.muted, width: 90 },
  scheduleIcon: { width: 26, height: 26, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  scheduleActivity: { fontSize: 14, fontWeight: '600', color: colors.text.primary },
  scheduleDetail: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  tipRow: { flexDirection: 'row', gap: spacing.md },
  tipTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.xs },
  tipText: { fontSize: 12, color: colors.text.secondary, lineHeight: 18, marginTop: 2 },
});
