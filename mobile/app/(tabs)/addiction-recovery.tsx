/**
 * Addiction Recovery — sobriety tracker, cravings, and coping strategies.
 *
 * Milestones and the resistance rate come from the sobriety-status endpoint,
 * which derives them from the real start date and logged cravings, so a new
 * profile shows zero days rather than a stranger's streak.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, Dimensions, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { colors, spacing, typography } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { postJson, getJson, asArray, asNumber } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const SUBSTANCES = ['alcohol', 'opioids', 'tobacco', 'cannabis', 'benzodiazepines', 'stimulants'];

interface Milestone { days: number; badge: string; emoji: string }

interface SobrietyStatus {
  status?: 'no_profile';
  message?: string;
  days_sober?: number;
  substance?: string;
  milestones_achieved?: Milestone[];
  next_milestone?: Milestone | null;
  resistance_rate_7d?: number;
  cravings_this_week?: number;
  longest_streak_days?: number;
}

interface CravingAnalytics {
  total?: number;
  total_cravings?: number;
  avg_intensity?: number;
  resistance_rate?: number;
  top_triggers?: { trigger: string; count: number }[];
  message?: string;
}

interface CopingStrategy { id: string; name: string; duration_min: number; description: string }

interface SupportContact { id: string; name: string; relationship: string; is_sponsor: boolean }

export default function AddictionRecoveryScreen() {
  const userId = useUserStore((s) => s.userId);
  const [substance, setSubstance] = useState('alcohol');
  const [startDate, setStartDate] = useState('');
  const [intensity, setIntensity] = useState('5');
  const [trigger, setTrigger] = useState('');
  const [busy, setBusy] = useState(false);
  const [strategies, setStrategies] = useState<CopingStrategy[]>([]);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    sobriety: SobrietyStatus;
    analytics: CravingAnalytics;
    support: SupportContact[];
  }>({
    sobriety: `/substance-use/sobriety/${userId}`,
    analytics: `/substance-use/craving/analytics/${userId}`,
    support: `/substance-use/support/${userId}`,
  });

  const sobriety = data.sobriety;
  const hasProfile = !!sobriety && sobriety.status !== 'no_profile';
  const analytics = data.analytics;
  const topTriggers = asArray<{ trigger: string; count: number }>(analytics?.top_triggers);
  const supportContacts = asArray<SupportContact>(data.support);

  const setup = useCallback(async () => {
    if (!startDate.trim()) {
      Alert.alert('Start date needed', 'Enter the date your sobriety started, as YYYY-MM-DD.');
      return;
    }
    setBusy(true);
    const result = await postJson('/substance-use/profile/create', {
      user_id: userId,
      substance,
      start_date: startDate.trim(),
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not set up', 'The recovery profile could not be created.');
      return;
    }
    await reload();
  }, [substance, startDate, userId, reload]);

  const logCraving = useCallback(async () => {
    const parsed = Number(intensity);
    if (!Number.isFinite(parsed) || parsed < 1 || parsed > 10) {
      Alert.alert('Intensity needed', 'Rate the craving from 1 to 10.');
      return;
    }
    setBusy(true);
    const result = await postJson('/substance-use/craving/log', {
      user_id: userId,
      intensity: Math.round(parsed),
      trigger: trigger.trim() || 'unspecified',
      location: '',
      duration_min: 0,
    });
    if (result) {
      const strategyList = await getJson<CopingStrategy[]>(`/substance-use/coping/${Math.round(parsed)}`);
      setStrategies(asArray<CopingStrategy>(strategyList));
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
    setBusy(false);
    if (!result) {
      Alert.alert('Not recorded', 'The craving could not be logged.');
      return;
    }
    setTrigger('');
    await reload();
  }, [intensity, trigger, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#10B981" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#10B981" />}
      >
        <LinearGradient colors={['#10B981', '#06B6D4', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Recovery Journey</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>
            {hasProfile ? sobriety!.substance : 'Not set up'}
          </Text>
          {hasProfile ? (
            <>
              <View style={styles.soberCount}>
                <Text style={[typography.metric.hero, { color: '#fff' }]}>{sobriety!.days_sober}</Text>
                <Text style={[typography.body.lg, { color: 'rgba(255,255,255,0.7)' }]}>Days Sober</Text>
              </View>
              <View style={styles.statsRow}>
                <View style={styles.statBox}>
                  <Text style={[typography.metric.small, { color: '#fff' }]}>{sobriety!.resistance_rate_7d ?? 0}%</Text>
                  <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Resistance (7d)</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statBox}>
                  <Text style={[typography.metric.small, { color: '#fff' }]}>{sobriety!.cravings_this_week ?? 0}</Text>
                  <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Cravings (7d)</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statBox}>
                  <Text style={[typography.metric.small, { color: '#fff' }]}>{sobriety!.longest_streak_days ?? 0}</Text>
                  <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Longest Streak</Text>
                </View>
              </View>
            </>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 8 }]}>
              Add your sobriety start date to begin tracking.
            </Text>
          )}
        </LinearGradient>

        {!hasProfile && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Set Up Recovery" icon="leaf" iconColor="#10B981" />
            <GlassCard>
              <Text style={styles.helperText}>Choose the substance and the date you became sober.</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, marginBottom: 12 }}>
                {SUBSTANCES.map((s) => (
                  <TouchableOpacity
                    key={s}
                    style={[styles.chip, substance === s && styles.chipActive]}
                    onPress={() => setSubstance(s)}
                  >
                    <Text style={[styles.chipText, substance === s && styles.chipTextActive]}>{s}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
              <TextInput
                style={styles.input}
                placeholder="Start date (YYYY-MM-DD)"
                placeholderTextColor={colors.text.muted}
                value={startDate}
                onChangeText={setStartDate}
                accessibilityLabel="Sobriety start date"
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={setup} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Start tracking'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {!!hasProfile && (
          <>
            <View style={styles.section}>
              <SectionHeaderPremium title="Milestones" icon="trophy" iconColor={colors.health.energy} />
              {(sobriety!.milestones_achieved?.length ?? 0) === 0 ? (
                <Text style={styles.emptyText}>No milestones reached yet.</Text>
              ) : (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
                  {sobriety!.milestones_achieved!.map((m) => (
                    <View key={m.days} style={[styles.milestoneCard, styles.milestoneAchieved]}>
                      <Text style={{ fontSize: 24 }}>{m.emoji}</Text>
                      <Text style={[typography.body.sm, { color: colors.health.success, marginTop: 4 }]}>{m.days} days</Text>
                      <Text style={[typography.body.xs, { color: colors.text.muted }]}>{m.badge}</Text>
                    </View>
                  ))}
                </ScrollView>
              )}
              {sobriety!.next_milestone && (
                <Text style={[styles.helperText, { marginTop: 8 }]}>
                  Next: {sobriety!.next_milestone.badge} at {sobriety!.next_milestone.days} days
                </Text>
              )}
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Log a Craving" icon="flash" iconColor={colors.health.warning} />
              <GlassCard>
                <TextInput
                  style={styles.input}
                  placeholder="Trigger (e.g. stress, social)"
                  placeholderTextColor={colors.text.muted}
                  value={trigger}
                  onChangeText={setTrigger}
                  accessibilityLabel="Craving trigger"
                />
                <TextInput
                  style={styles.input}
                  placeholder="Intensity 1-10"
                  placeholderTextColor={colors.text.muted}
                  keyboardType="numeric"
                  value={intensity}
                  onChangeText={setIntensity}
                  accessibilityLabel="Craving intensity"
                />
                <TouchableOpacity style={styles.primaryBtn} onPress={logCraving} disabled={busy}>
                  <Text style={styles.primaryBtnText}>{busy ? 'Logging…' : 'Log craving'}</Text>
                </TouchableOpacity>
              </GlassCard>
              {strategies.length > 0 && (
                <View style={{ marginTop: 12 }}>
                  {strategies.map((s) => (
                    <View key={s.id} style={styles.copingRow}>
                      <Ionicons name="shield-checkmark" size={18} color={colors.primary} />
                      <View style={{ flex: 1 }}>
                        <Text style={[typography.body.md, { color: colors.text.primary }]}>{s.name} · {s.duration_min} min</Text>
                        <Text style={[typography.body.xs, { color: colors.text.muted }]}>{s.description}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              )}
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Craving Patterns" icon="analytics" iconColor={colors.health.calm} />
              {!analytics || asNumber(analytics.total_cravings ?? analytics.total, 0) === 0 ? (
                <Text style={styles.emptyText}>No cravings logged yet. Patterns appear once you log a few.</Text>
              ) : (
                <GlassCard>
                  <Text style={[typography.body.md, { color: colors.text.primary }]}>
                    {analytics.total_cravings} logged · avg intensity {analytics.avg_intensity} · resisted {analytics.resistance_rate}%
                  </Text>
                  {topTriggers.length > 0 && (
                    <View style={{ marginTop: 8 }}>
                      {topTriggers.map((t) => (
                        <Text key={t.trigger} style={[typography.body.sm, { color: colors.text.muted }]}>
                          {t.trigger}: {t.count}
                        </Text>
                      ))}
                    </View>
                  )}
                </GlassCard>
              )}
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Support Network" icon="people" iconColor={colors.primary} />
              {supportContacts.length === 0 ? (
                <Text style={styles.emptyText}>No support contacts added yet.</Text>
              ) : (
                supportContacts.map((c) => (
                  <View key={c.id} style={styles.supportRow}>
                    <View style={styles.avatar}>
                      <Text style={[typography.body.md, { color: colors.primary, fontWeight: '700' }]}>{c.name[0]}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[typography.body.md, { color: colors.text.primary }]}>{c.name}</Text>
                      <Text style={[typography.body.xs, { color: colors.text.muted }]}>{c.is_sponsor ? 'Sponsor' : c.relationship}</Text>
                    </View>
                  </View>
                ))
              )}
            </View>
          </>
        )}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  soberCount: { alignItems: 'center', marginTop: 20 },
  statsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', marginTop: 20, backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 16, padding: 16 },
  statBox: { alignItems: 'center', flex: 1 },
  statDivider: { width: 1, height: 32, backgroundColor: 'rgba(255,255,255,0.15)' },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  milestoneCard: { width: 100, alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 16, padding: 14, borderWidth: 1, borderColor: colors.surface.border },
  milestoneAchieved: { borderColor: colors.health.success + '40', backgroundColor: colors.health.success + '08' },
  copingRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  supportRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, gap: 12, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  avatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.primary + '20' },
  helperText: { color: colors.text.muted, fontSize: 13, marginBottom: 8 },
  emptyText: { color: colors.text.muted, fontSize: 13 },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#10B981', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: '#10B98120', borderColor: '#10B981' },
  chipText: { color: colors.text.muted, fontSize: 13 },
  chipTextActive: { color: '#10B981', fontWeight: '700' },
});
