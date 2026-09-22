/**
 * Ambient Health — smart-home environment monitoring.
 *
 * There is no ambient reading without a registered home and at least one
 * device reporting to it, so the screen leads with that instead of a
 * roomful of numbers nobody's sensor produced.
 */
import React, { useCallback, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing } from '../../src/components/PremiumComponents';
import { useApi, useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

interface Home { home_id: string; name: string; devices: string[] }
interface EnvHealth { status?: string; message?: string; overall_health_score?: number; room_scores?: Record<string, { score: number; devices: number }> }
interface SleepEnv { status?: string; message?: string; sleep_environment_score?: number; component_scores?: Record<string, number> }

export default function AmbientScreen() {
  const userId = useUserStore((s) => s.userId);
  const [homeName, setHomeName] = useState('My Home');
  const [busy, setBusy] = useState(false);

  const { data: homesData, loading: homesLoading, reload: reloadHomes } = useApi<{ success: boolean; data: Home[] }>('/ambient/homes');
  const homes = asArray<Home>(homesData?.data);
  const home = homes[0];

  const { data, loading, refresh, refreshing } = useApis<{
    health: { data: EnvHealth };
    sleep: { data: SleepEnv };
  }>(home ? {
    health: `/ambient/health/${home.home_id}`,
    sleep: `/ambient/sleep/${home.home_id}`,
  } : null);

  const health = data.health?.data;
  const sleep = data.sleep?.data;

  const registerHome = useCallback(async () => {
    setBusy(true);
    const result = await postJson('/ambient/home', { user_id: userId, home_config: { name: homeName.trim() || 'My Home' } });
    setBusy(false);
    if (!result) return;
    await reloadHomes();
  }, [userId, homeName, reloadHomes]);

  if (homesLoading) {
    return (
      <View style={[styles.center, { flex: 1, backgroundColor: colors.bg.deep }]}>
        <ActivityIndicator size="large" color="#8B5CF6" />
      </View>
    );
  }

  if (!home) {
    return (
      <ScreenWrapper title="Ambient Health" subtitle="Smart home & environment" gradient={['#6366F1', '#8B5CF6']}>
        <View style={styles.section}>
          <SectionHeaderPremium icon="home" iconColor="#8B5CF6" title="Register Your Home" />
          <GlassCard variant="light">
            <Text style={styles.helperText}>
              Ambient readings come from devices paired to a home. Register one to start.
            </Text>
            <TextInput
              style={styles.input}
              placeholder="Home name"
              placeholderTextColor={colors.text.muted}
              value={homeName}
              onChangeText={setHomeName}
            />
            <TouchableOpacity style={styles.primaryBtn} onPress={registerHome} disabled={busy}>
              <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Register home'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper
      title="Ambient Health"
      subtitle={home.name}
      gradient={['#6366F1', '#8B5CF6']}
      onRefresh={refresh}
      refreshing={refreshing}
    >
      {loading ? (
        <View style={styles.center}><ActivityIndicator color="#8B5CF6" /></View>
      ) : (
        <>
          <View style={styles.scoreSection}>
            {health && health.status !== 'no_data' && typeof health.overall_health_score === 'number' ? (
              <ScoreRing score={Math.round(health.overall_health_score)} size={120} strokeWidth={8} color="#8B5CF6" label="AMBIENT" sublabel="Score" />
            ) : (
              <GlassCard variant="light" style={styles.emptyCard}>
                <Text style={styles.emptyTitle}>No readings yet</Text>
                <Text style={styles.helperText}>{health?.message ?? 'Pair a device with this home to see room conditions.'}</Text>
              </GlassCard>
            )}
          </View>

          {health?.room_scores && Object.keys(health.room_scores).length > 0 && (
            <>
              <SectionHeaderPremium icon="home" iconColor="#8B5CF6" title="Room Conditions" />
              {Object.entries(health.room_scores).map(([room, r]) => (
                <GlassCard key={room} variant="light" style={styles.roomCard}>
                  <Text style={styles.roomName}>{room.replace('_', ' ')}</Text>
                  <Text style={styles.roomScore}>Score {r.score}/100 · {r.devices} device{r.devices === 1 ? '' : 's'}</Text>
                </GlassCard>
              ))}
            </>
          )}

          <SectionHeaderPremium icon="moon" iconColor={colors.health.sleep} title="Sleep Environment" />
          <GlassCard variant="light" style={styles.sectionCard}>
            {!sleep || sleep.status === 'no_data' ? (
              <Text style={styles.helperText}>{sleep?.message ?? 'No bedroom sensor has reported a reading yet.'}</Text>
            ) : (
              <>
                <Text style={styles.roomScore}>Overall: {sleep.sleep_environment_score}/100</Text>
                {sleep.component_scores && Object.entries(sleep.component_scores).map(([k, v]) => (
                  <View key={k} style={styles.sleepRow}>
                    <Text style={styles.sleepLabel}>{k}</Text>
                    <Text style={styles.sleepValue}>{Math.round(v)}</Text>
                  </View>
                ))}
              </>
            )}
          </GlassCard>
        </>
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  center: { justifyContent: 'center', alignItems: 'center', paddingVertical: 40 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg },
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  emptyCard: { width: '100%', alignItems: 'center', padding: spacing.lg },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary, marginBottom: 6 },
  helperText: { color: colors.text.muted, fontSize: 13, textAlign: 'center', marginBottom: 8 },
  roomCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  roomName: { fontSize: 15, fontWeight: '700', color: colors.text.primary, textTransform: 'capitalize' },
  roomScore: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  sleepRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  sleepLabel: { fontSize: 13, color: colors.text.primary, textTransform: 'capitalize' },
  sleepValue: { fontSize: 13, fontWeight: '700', color: colors.text.primary },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#8B5CF6', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
});
