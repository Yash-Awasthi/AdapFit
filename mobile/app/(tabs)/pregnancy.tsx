/**
 * Pregnancy Tracker — week-by-week development from a real last-period date.
 *
 * "Week 24, size of an ear of corn" only appears once someone has actually
 * entered a last period date; until then the screen asks for it instead of
 * assuming a week.
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
import { postJson, getJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

interface WeekInfo {
  error?: string;
  status?: 'week_unknown';
  message?: string;
  current_week?: number;
  trimester?: number;
  days_until_due?: number | null;
  baby_development?: { size: string; weight_g: number; milestones: string[]; tip: string };
  health_tips?: string[];
  warning_signs?: string[];
}

interface KickSession { date: string; kicks: number; duration_minutes: number; status: string }

export default function PregnancyScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [lastPeriod, setLastPeriod] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [kicks, setKicks] = useState('');
  const [duration, setDuration] = useState('10');
  const [history, setHistory] = useState<KickSession[]>([]);

  const { data, loading, refresh, refreshing, reload } = useApis<{ weekInfo: { data: WeekInfo } }>({
    weekInfo: `/pregnancy/week-info/${userId}`,
  });

  const weekInfo = data.weekInfo?.data;
  const needsSetup = weekInfo?.error === 'Set up pregnancy profile first';
  const needsLastPeriod = weekInfo?.status === 'week_unknown';
  const hasWeek = !!weekInfo && !weekInfo.error && !weekInfo.status;

  const loadHistory = useCallback(async () => {
    const result = await getJson<{ data: KickSession[] }>(`/pregnancy/kick-history/${userId}`);
    setHistory(asArray<KickSession>(result?.data));
  }, [userId]);

  React.useEffect(() => { if (!needsSetup) loadHistory(); }, [needsSetup, loadHistory]);

  const setup = useCallback(async () => {
    if (!lastPeriod.trim()) {
      Alert.alert('Date needed', 'Enter your last period start date, as YYYY-MM-DD.');
      return;
    }
    setBusy(true);
    const result = await postJson('/pregnancy/setup', {
      user_id: userId,
      data: { last_period: lastPeriod.trim(), due_date: dueDate.trim() || undefined },
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not saved', 'The profile could not be created.');
      return;
    }
    await reload();
  }, [lastPeriod, dueDate, userId, reload]);

  const logKicks = useCallback(async () => {
    const k = Number(kicks);
    const d = Number(duration);
    if (!Number.isFinite(k) || k < 0 || !Number.isFinite(d) || d <= 0) {
      Alert.alert('Details needed', 'Enter kicks counted and how many minutes.');
      return;
    }
    setBusy(true);
    const result = await postJson('/pregnancy/kick-counter', {
      user_id: userId,
      data: { kicks: Math.round(k), duration_minutes: Math.round(d) },
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not recorded', 'The session could not be saved.');
      return;
    }
    setKicks('');
    await loadHistory();
  }, [kicks, duration, userId, loadHistory]);

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
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Pregnancy Tracker</Text>
          {hasWeek ? (
            <>
              <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Week {weekInfo!.current_week}</Text>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 2 }]}>
                Trimester {weekInfo!.trimester} · Size of a {weekInfo!.baby_development?.size}
              </Text>
              {weekInfo!.days_until_due != null && (
                <Text style={[typography.metric.large, { color: '#fff', marginTop: 12 }]}>{weekInfo!.days_until_due} days until due</Text>
              )}
            </>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 8 }]}>
              {needsSetup ? 'Set up your pregnancy to begin.' : weekInfo?.message ?? 'Add your last period date.'}
            </Text>
          )}
        </LinearGradient>

        {(needsSetup || needsLastPeriod) && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Set Up Tracking" icon="happy" iconColor="#EC4899" />
            <GlassCard>
              <TextInput
                style={styles.input}
                placeholder="Last period start (YYYY-MM-DD)"
                placeholderTextColor={colors.text.muted}
                value={lastPeriod}
                onChangeText={setLastPeriod}
              />
              <TextInput
                style={styles.input}
                placeholder="Due date (YYYY-MM-DD, optional)"
                placeholderTextColor={colors.text.muted}
                value={dueDate}
                onChangeText={setDueDate}
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={setup} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {hasWeek && weekInfo!.baby_development && (
          <View style={styles.section}>
            <SectionHeaderPremium title="This Week's Milestones" icon="checkmark-circle" iconColor="#10B981" />
            {weekInfo!.baby_development.milestones.map((m) => (
              <View key={m} style={styles.milestoneRow}>
                <Ionicons name="checkmark-circle" size={18} color="#10B981" />
                <Text style={[typography.body.md, { color: colors.text.primary, marginLeft: 8, flex: 1 }]}>{m}</Text>
              </View>
            ))}
          </View>
        )}

        {!needsSetup && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Kick Counter" icon="footsteps" iconColor="#EC4899" />
            <GlassCard>
              <TextInput
                style={styles.input}
                placeholder="Kicks counted"
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={kicks}
                onChangeText={setKicks}
              />
              <TextInput
                style={styles.input}
                placeholder="Duration (minutes)"
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={duration}
                onChangeText={setDuration}
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={logKicks} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Log session'}</Text>
              </TouchableOpacity>
            </GlassCard>
            {history.length === 0 ? (
              <Text style={[styles.emptyText, { marginTop: 8 }]}>No kick sessions logged yet.</Text>
            ) : (
              history.map((s, i) => (
                <View key={i} style={styles.sessionRow}>
                  <Text style={[typography.body.sm, { color: colors.text.muted }]}>{s.date}</Text>
                  <Text style={[typography.body.md, { color: colors.text.primary }]}>{s.kicks} kicks / {s.duration_minutes} min</Text>
                  <Text style={[typography.body.sm, { color: s.status === 'normal' ? colors.health.success : colors.health.warning }]}>{s.status}</Text>
                </View>
              ))
            )}
          </View>
        )}

        {hasWeek && weekInfo!.health_tips && (
          <View style={styles.section}>
            <SectionHeaderPremium title="This Week's Tips" icon="bulb" iconColor="#F59E0B" />
            {weekInfo!.health_tips.map((t) => (
              <Text key={t} style={[typography.body.sm, { color: colors.text.muted, marginBottom: 6 }]}>• {t}</Text>
            ))}
          </View>
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
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  milestoneRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 },
  emptyText: { color: colors.text.muted, fontSize: 13 },
  sessionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#EC4899', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
});
