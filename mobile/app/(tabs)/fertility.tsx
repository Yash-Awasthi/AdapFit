/**
 * Fertility Tracker — cycle prediction from a real logged history.
 *
 * Prediction needs a profile and at least one daily log; insights need
 * seven. Each stage says what it is waiting for instead of showing day 14
 * of a cycle nobody logged.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, typography } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';
import { localDay } from '../../src/utils/date';

const CM_OPTIONS = ['dry', 'sticky', 'creamy', 'watery', 'egg_white'];

interface Predict {
  error?: string;
  current_cycle_day?: number;
  current_phase?: string;
  next_period?: string;
  days_until_period?: number;
  estimated_ovulation?: string;
  is_fertile?: boolean;
}

interface Insights {
  message?: string;
  days_logged?: number;
  days_tracked?: number;
  bbt_analysis?: { average: number; shift_detected: boolean; interpretation: string };
  cervical_mucus?: { fertile_type_days: number; pattern: string };
  cycle_regularity?: { regular: boolean | null; variation_days: number | null; assessment: string };
  fertility_score?: number;
}

export default function FertilityScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [cycleLength, setCycleLength] = useState('28');
  const [periodLength, setPeriodLength] = useState('5');
  const [lastPeriod, setLastPeriod] = useState('');
  const [bbt, setBbt] = useState('');
  const [cm, setCm] = useState('dry');
  const [lhPositive, setLhPositive] = useState(false);
  const [spotting, setSpotting] = useState(false);

  const { data, loading, refresh, refreshing, reload } = useApis<{
    predict: { data: Predict };
    insights: { data: Insights };
  }>({
    predict: `/fertility/predict/${userId}`,
    insights: `/fertility/insights/${userId}`,
  });

  const predict = data.predict?.data;
  const insights = data.insights?.data;
  const needsProfile = predict?.error === 'Set up profile first';
  const needsFirstLog = predict?.error === 'No cycle data logged yet' || predict?.error === 'Cannot determine last period start';
  const hasPrediction = !!predict && !predict.error;

  const setup = useCallback(async () => {
    const cLen = Number(cycleLength);
    const pLen = Number(periodLength);
    if (!Number.isFinite(cLen) || cLen < 15 || cLen > 60) {
      Alert.alert('Cycle length needed', 'Enter your average cycle length in days (15-60).');
      return;
    }
    setBusy(true);
    const result = await postJson('/fertility/profile', {
      user_id: userId,
      profile_data: {
        average_cycle_length: Math.round(cLen),
        average_period_length: Math.round(pLen) || 5,
        last_period_start: lastPeriod.trim() || undefined,
      },
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not set up', 'The profile could not be created.');
      return;
    }
    await reload();
  }, [cycleLength, periodLength, lastPeriod, userId, reload]);

  const logToday = useCallback(async () => {
    setBusy(true);
    const result = await postJson('/fertility/log', {
      user_id: userId,
      date: localDay(),
      data: {
        bbt: bbt.trim() ? Number(bbt) : undefined,
        cervical_mucus: cm,
        lh_strip: lhPositive ? 'positive' : 'negative',
        spotting,
      },
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not recorded', 'The entry could not be saved.');
      return;
    }
    setBbt('');
    await reload();
  }, [bbt, cm, lhPositive, spotting, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#EC4899" />
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
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#EC4899" />}
      >
        <LinearGradient colors={['#EC4899', '#F472B6', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Fertility Tracker</Text>
          {hasPrediction ? (
            <>
              <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4, textTransform: 'capitalize' }]}>
                {predict!.current_phase} phase
              </Text>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 4 }]}>
                Cycle day {predict!.current_cycle_day} · {predict!.is_fertile ? 'Fertile window' : 'Not currently fertile'}
              </Text>
            </>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 8 }]}>
              {needsProfile ? 'Set up your cycle to begin.' : 'Log a day to get predictions.'}
            </Text>
          )}
        </LinearGradient>

        {needsProfile && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Set Up Cycle" icon="sync" iconColor="#EC4899" />
            <GlassCard>
              <TextInput
                style={styles.input}
                placeholder="Average cycle length (days)"
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={cycleLength}
                onChangeText={setCycleLength}
              />
              <TextInput
                style={styles.input}
                placeholder="Average period length (days)"
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={periodLength}
                onChangeText={setPeriodLength}
              />
              <TextInput
                style={styles.input}
                placeholder="Last period start (YYYY-MM-DD, optional)"
                placeholderTextColor={colors.text.muted}
                value={lastPeriod}
                onChangeText={setLastPeriod}
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={setup} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save cycle'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {!needsProfile && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Today's Log" icon="create" iconColor="#EC4899" />
            <GlassCard>
              <TextInput
                style={styles.input}
                placeholder="Basal body temperature °C (optional)"
                placeholderTextColor={colors.text.muted}
                keyboardType="decimal-pad"
                value={bbt}
                onChangeText={setBbt}
              />
              <Text style={styles.helperText}>Cervical mucus</Text>
              <View style={styles.chipRow}>
                {CM_OPTIONS.map((o) => (
                  <TouchableOpacity key={o} style={[styles.chip, cm === o && styles.chipActive]} onPress={() => setCm(o)}>
                    <Text style={[styles.chipText, cm === o && styles.chipTextActive]}>{o.replace('_', ' ')}</Text>
                  </TouchableOpacity>
                ))}
              </View>
              <View style={styles.toggleRow}>
                <TouchableOpacity style={[styles.toggleBtn, lhPositive && styles.toggleActive]} onPress={() => setLhPositive(!lhPositive)}>
                  <Text style={[styles.toggleText, lhPositive && styles.toggleTextActive]}>LH Positive</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.toggleBtn, spotting && styles.toggleActive]} onPress={() => setSpotting(!spotting)}>
                  <Text style={[styles.toggleText, spotting && styles.toggleTextActive]}>Spotting / Period</Text>
                </TouchableOpacity>
              </View>
              <TouchableOpacity style={styles.primaryBtn} onPress={logToday} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Log today'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {hasPrediction && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Predictions" icon="calendar" iconColor="#EC4899" />
            <GlassCard>
              <View style={styles.predRow}>
                <Ionicons name="calendar" size={20} color="#EC4899" />
                <View style={{ flex: 1, marginLeft: 10 }}>
                  <Text style={[typography.body.md, { color: colors.text.primary }]}>Next period</Text>
                  <Text style={[typography.body.sm, { color: colors.text.muted }]}>{predict!.next_period} · in {predict!.days_until_period} days</Text>
                </View>
              </View>
              <View style={styles.predRow}>
                <Ionicons name="flower" size={20} color="#EC4899" />
                <View style={{ flex: 1, marginLeft: 10 }}>
                  <Text style={[typography.body.md, { color: colors.text.primary }]}>Estimated ovulation</Text>
                  <Text style={[typography.body.sm, { color: colors.text.muted }]}>{predict!.estimated_ovulation}</Text>
                </View>
              </View>
            </GlassCard>
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Cycle Insights" icon="stats-chart" iconColor={colors.health.calm} />
          {!insights || insights.message ? (
            <Text style={styles.emptyText}>{insights?.message ?? 'Log at least 7 days for insights'} ({insights?.days_logged ?? 0}/7)</Text>
          ) : (
            <GlassCard>
              <Text style={[typography.body.md, { color: colors.text.primary }]}>
                Regularity: {insights.cycle_regularity?.regular === null ? 'Not enough cycles yet' : insights.cycle_regularity?.assessment}
              </Text>
              {insights.bbt_analysis && (
                <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 6 }]}>
                  BBT avg {insights.bbt_analysis.average}°C · {insights.bbt_analysis.interpretation}
                </Text>
              )}
              {insights.cervical_mucus && (
                <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 6 }]}>
                  Cervical mucus: {insights.cervical_mucus.pattern.replace('_', ' ')}
                </Text>
              )}
            </GlassCard>
          )}
        </View>
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
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  helperText: { color: colors.text.muted, fontSize: 13, marginBottom: 8 },
  emptyText: { color: colors.text.muted, fontSize: 13 },
  predRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8 },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#EC4899', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: '#EC489920', borderColor: '#EC4899' },
  chipText: { color: colors.text.muted, fontSize: 12, textTransform: 'capitalize' },
  chipTextActive: { color: '#EC4899', fontWeight: '700' },
  toggleRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  toggleBtn: { flex: 1, padding: 10, borderRadius: 10, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
  toggleActive: { backgroundColor: '#10B98120', borderColor: '#10B981' },
  toggleText: { color: colors.text.muted, fontSize: 12, fontWeight: '600' },
  toggleTextActive: { color: '#10B981' },
});
