/**
 * Achievements — level, streaks and badges, all computed on the server from
 * what was logged. There is nothing here to tap for points.
 */
import React from 'react';
import {
  View, Text, ScrollView, StyleSheet, StatusBar, ActivityIndicator, RefreshControl, TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { colors, spacing } from '../../src/theme';
import { GlassCard, ScoreRing, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray } from '../../src/services/http';

const TINT = '#EAB308';
const TIER_COLORS: Record<string, string> = { bronze: '#CD7F32', silver: '#94A3B8', gold: '#F59E0B', platinum: '#A78BFA' };
const CATEGORY_TITLES: Record<string, string> = {
  milestone: 'Milestones', consistency: 'Consistency', recovery: 'Recovery', sleep: 'Sleep', mind: 'Mind',
};

interface Badge {
  id: string; name: string; description: string; icon: string; tier: string;
  category: string; xp: number; progress: number; target: number; unlocked: boolean;
}
interface Summary {
  points: number; level: number; level_progress: number; points_to_next_level: number;
  earned: number; total: number; current_streak: number; best_streak: number;
}

export default function AchievementsScreen() {
  const router = useRouter();
  const { data, loading, refresh, refreshing } = useApis<{ badges: Badge[]; summary: Summary }>({
    badges: '/achievements',
    summary: '/achievements/summary',
  });
  const badges = asArray<Badge>(data.badges);
  const summary = data.summary;
  const categories = Object.keys(CATEGORY_TITLES).filter((c) => badges.some((b) => b.category === c));

  if (loading) {
    return <View style={[styles.container, styles.center]}><ActivityIndicator size="large" color={TINT} /></View>;
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={TINT} />}>
        <LinearGradient colors={[TINT, '#B45309', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Achievements</Text>
          {summary ? (
            <View style={styles.heroRow}>
              <ScoreRing score={Math.round(summary.level_progress * 100)} size={112} strokeWidth={9} color="#fff" label={`LEVEL ${summary.level}`} />
              <View style={{ flex: 1 }}>
                <Text style={styles.heroValue}>{summary.points} XP</Text>
                <Text style={styles.heroMuted}>{summary.points_to_next_level} XP to level {summary.level + 1}</Text>
                <Text style={[styles.heroMuted, { marginTop: 8 }]}>
                  {summary.earned} of {summary.total} badges · streak {summary.current_streak} (best {summary.best_streak})
                </Text>
              </View>
            </View>
          ) : (
            <Text style={styles.heroMuted}>Could not load your progress. Pull to retry.</Text>
          )}
        </LinearGradient>

        <View style={styles.section}>
          <TouchableOpacity onPress={() => router.push('/community' as any)}>
            <GlassCard style={styles.linkCard}>
              <Ionicons name="podium" size={20} color={TINT} />
              <Text style={styles.linkText}>See the leaderboard</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.text.muted} />
            </GlassCard>
          </TouchableOpacity>
        </View>

        {categories.map((cat) => (
          <View key={cat} style={styles.section}>
            <SectionHeaderPremium title={CATEGORY_TITLES[cat]} icon="ribbon" iconColor={TINT} />
            {badges.filter((b) => b.category === cat).map((b) => {
              const tier = TIER_COLORS[b.tier] ?? TINT;
              return (
                <GlassCard key={b.id} style={[styles.badgeCard, !b.unlocked && styles.locked]}>
                  <View style={[styles.badgeIcon, { backgroundColor: tier + (b.unlocked ? '30' : '12') }]}>
                    <Ionicons name={(b.unlocked ? b.icon : 'lock-closed') as any} size={22} color={b.unlocked ? tier : colors.text.muted} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.badgeName}>{b.name}</Text>
                    <Text style={styles.badgeDesc}>{b.description}</Text>
                    {!b.unlocked && (
                      <View style={styles.barBg}>
                        <View style={[styles.barFill, { width: `${(b.progress / b.target) * 100}%`, backgroundColor: tier }]} />
                      </View>
                    )}
                  </View>
                  <Text style={[styles.xp, { color: tier }]}>{b.unlocked ? `+${b.xp}` : `${b.progress}/${b.target}`}</Text>
                </GlassCard>
              );
            })}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 16, marginTop: 12 },
  heroValue: { color: '#fff', fontSize: 30, fontWeight: '800' },
  heroMuted: { paddingLeft: 40, color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  linkCard: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  linkText: { flex: 1, color: colors.text.primary, fontWeight: '600' },
  badgeCard: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  locked: { opacity: 0.75 },
  badgeIcon: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  badgeName: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  badgeDesc: { color: colors.text.muted, fontSize: 12, marginTop: 2 },
  barBg: { height: 5, borderRadius: 3, backgroundColor: colors.bg.card, marginTop: 6 },
  barFill: { height: 5, borderRadius: 3 },
  xp: { fontSize: 13, fontWeight: '700' },
});
