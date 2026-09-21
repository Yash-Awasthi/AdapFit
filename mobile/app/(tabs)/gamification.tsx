/**
 * Achievements — level, badges and the leaderboard, read from the server.
 *
 * The badge grid is the full catalogue with the earned ones marked, so a
 * locked badge still shows what it is and what earning it is worth. Icons are
 * whatever the catalogue carries, which is emoji, rather than a second icon
 * table here that would drift from it.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { Confetti } from '../../src/components/AnimationSystem';
import { useApis } from '../../src/hooks/useApi';
import { asArray, asNumber } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface LevelInfo {
  total_points: number;
  level: number;
  level_progress: number;
  points_into_level: number;
  points_to_next_level: number;
  badge_count: number;
}

interface Badge {
  badge_id: string;
  name: string;
  description: string;
  rarity: string;
  color: string;
  icon: string;
  points: number;
  earned_at?: string;
}

interface LeaderboardEntry {
  user_id: string;
  username: string;
  score: number;
  rank: number;
}

// Presentation only: the server tracks the level number, not a name for it.
const TITLES = [
  { from: 15, title: 'Elite' },
  { from: 10, title: 'Fitness Enthusiast' },
  { from: 5, title: 'Consistent' },
  { from: 1, title: 'Getting Started' },
];

function titleFor(level: number): string {
  return TITLES.find((t) => level >= t.from)?.title ?? 'Newcomer';
}

export default function GamificationScreen() {
  const userId = useUserStore((s) => s.userId);
  const [showConfetti, setShowConfetti] = useState(false);
  const fireAnim = useRef(new Animated.Value(1)).current;
  const xpAnim = useRef(new Animated.Value(0)).current;

  const { data, loading, refreshing, refresh } = useApis<{
    level: LevelInfo;
    earned: { badges: Badge[]; total: number; points_from_badges: number };
    catalogue: { badges: Badge[]; total: number };
    leaderboard: { leaderboard: LeaderboardEntry[] };
  }>({
    level: `/gamification/level/${userId}`,
    earned: `/gamification/badges/${userId}`,
    catalogue: '/gamification/all-badges',
    leaderboard: '/gamification/leaderboard?limit=10',
  });

  const level = data.level ?? null;
  const earned = asArray<Badge>(data.earned?.badges);
  const catalogue = asArray<Badge>(data.catalogue?.badges);
  const leaderboard = asArray<LeaderboardEntry>(data.leaderboard?.leaderboard);

  const earnedIds = useMemo(() => new Set(earned.map((b) => b.badge_id)), [earned]);
  const progress = level ? Math.max(0, Math.min(1, level.level_progress)) : 0;

  useEffect(() => {
    Animated.timing(xpAnim, { toValue: progress, duration: 800, useNativeDriver: false }).start();
  }, [progress, xpAnim]);

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(fireAnim, { toValue: 1.2, duration: 300, useNativeDriver: true }),
        Animated.timing(fireAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [fireAnim]);

  const stats = [
    { title: 'Total XP', value: asNumber(level?.total_points).toLocaleString(), icon: 'flash', color: '#F59E0B' },
    { title: 'Level', value: String(asNumber(level?.level)), icon: 'trending-up', color: '#22C55E' },
    { title: 'Badges Earned', value: `${earned.length}/${catalogue.length || earned.length}`, icon: 'trophy', color: '#F59E0B' },
    { title: 'XP to Next', value: asNumber(level?.points_to_next_level).toLocaleString(), icon: 'arrow-up', color: '#3B82F6' },
  ];

  return (
    <ScreenWrapper
      title="Achievements"
      subtitle="Your fitness journey milestones"
      gradient={['#F59E0B', '#F97316']}
      rightAction={{ icon: 'trophy', onPress: () => {} }}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <Confetti visible={showConfetti} />

      <GlassCard variant="light" style={styles.levelCard}>
        <View style={styles.levelHeader}>
          <View style={styles.levelBadge}>
            <Animated.Text style={[styles.levelNumber, { transform: [{ scale: fireAnim }] }]}>🔥</Animated.Text>
            <Text style={styles.levelValue}>{asNumber(level?.level)}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.levelTitle}>{titleFor(asNumber(level?.level))}</Text>
            <Text style={styles.levelXP}>
              {asNumber(level?.points_into_level).toLocaleString()} XP into this level
            </Text>
          </View>
        </View>
        <View style={styles.xpBarContainer}>
          <View style={styles.xpBar}>
            <Animated.View
              style={[styles.xpBarFill, {
                width: xpAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }),
              }]}
            />
          </View>
          <Text style={styles.xpPercent}>{Math.round(progress * 100)}%</Text>
        </View>
        <Text style={styles.xpRemaining}>
          {asNumber(level?.points_to_next_level).toLocaleString()} XP to next level
        </Text>
      </GlassCard>

      <View style={styles.statsGrid}>
        {stats.map((a) => (
          <GlassCard key={a.title} variant="light" style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: a.color + '15' }]}>
              <Ionicons name={a.icon as any} size={18} color={a.color} />
            </View>
            <Text style={[styles.statValue, { color: a.color }]}>{a.value}</Text>
            <Text style={styles.statLabel}>{a.title}</Text>
          </GlassCard>
        ))}
      </View>

      <SectionHeaderPremium
        icon="trophy"
        iconColor="#F59E0B"
        title="Badge Collection"
        subtitle={`${earned.length}/${catalogue.length || earned.length} unlocked`}
      />
      {catalogue.length === 0 ? (
        <Text style={styles.emptyText}>The badge catalogue could not be loaded.</Text>
      ) : (
        <View style={styles.badgeGrid}>
          {catalogue.map((badge) => {
            const unlocked = earnedIds.has(badge.badge_id);
            return (
              <TouchableOpacity
                key={badge.badge_id}
                style={[styles.badgeItem, !unlocked && styles.badgeLocked]}
                accessibilityRole="button"
                accessibilityLabel={
                  unlocked
                    ? `${badge.name}, earned. ${badge.description}`
                    : `${badge.name}, locked. ${badge.description}. Worth ${badge.points} XP`
                }
                onPress={() => {
                  if (!unlocked) return;
                  setShowConfetti(true);
                  setTimeout(() => setShowConfetti(false), 3000);
                }}
              >
                <View style={[styles.badgeIcon, unlocked && { backgroundColor: (badge.color || '#F59E0B') + '15' }]}>
                  {unlocked ? (
                    <Text style={styles.badgeEmoji}>{badge.icon}</Text>
                  ) : (
                    <Ionicons name="lock-closed" size={22} color={colors.text.muted} />
                  )}
                </View>
                <Text
                  style={[styles.badgeName, !unlocked && { color: colors.text.muted }]}
                  numberOfLines={2}
                >
                  {badge.name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      )}

      <SectionHeaderPremium icon="podium" iconColor="#EF4444" title="Leaderboard" />
      <GlassCard variant="light" style={styles.leaderboardCard}>
        {leaderboard.length === 0 ? (
          <Text style={styles.emptyText}>
            Nobody has scored yet. Log a session and the board fills in.
          </Text>
        ) : (
          leaderboard.map((entry) => {
            const isUser = entry.user_id === userId;
            return (
              <View key={entry.user_id} style={[styles.lbRow, isUser && styles.lbRowUser]}>
                <Text style={[styles.lbRank, entry.rank === 1 && { color: '#F59E0B' }]}>#{entry.rank}</Text>
                <Ionicons name="person" size={24} color={colors.text.secondary} style={styles.lbAvatar} />
                <Text style={[styles.lbName, isUser && { color: colors.primary }]} numberOfLines={1}>
                  {isUser ? 'You' : entry.username}
                </Text>
                <Text style={[styles.lbScore, { color: colors.primary }]}>
                  {Math.round(entry.score).toLocaleString()}
                </Text>
              </View>
            );
          })
        )}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, backgroundColor: colors.bg.deep, justifyContent: 'center', alignItems: 'center' },
  emptyText: { fontSize: 13, color: colors.text.muted, lineHeight: 19, paddingHorizontal: spacing.screenPadding, paddingVertical: spacing.md },

  levelCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  levelHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  levelBadge: { alignItems: 'center' },
  levelNumber: { fontSize: 32 },
  levelValue: { fontSize: 24, fontWeight: '800', color: '#F59E0B' },
  levelTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary },
  levelXP: { fontSize: 13, color: colors.text.muted, marginTop: 2 },
  xpBarContainer: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  xpBar: { flex: 1, height: 8, backgroundColor: colors.surface.divider, borderRadius: 4, overflow: 'hidden' },
  xpBarFill: { height: '100%', backgroundColor: '#F59E0B', borderRadius: 4 },
  xpPercent: { fontSize: 12, fontWeight: '700', color: '#F59E0B', width: 36 },
  xpRemaining: { fontSize: 12, color: colors.text.muted, marginTop: spacing.xs },

  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  statCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md) / 2, alignItems: 'center', paddingVertical: spacing.md },
  statIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  statValue: { fontSize: 20, fontWeight: '800' },
  statLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  badgeItem: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md * 3) / 4, alignItems: 'center' },
  badgeLocked: { opacity: 0.5 },
  badgeIcon: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.bg.card, justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border },
  badgeEmoji: { fontSize: 24 },
  badgeName: { fontSize: 10, fontWeight: '600', color: colors.text.secondary, marginTop: 4, textAlign: 'center' },

  leaderboardCard: { marginHorizontal: spacing.screenPadding },
  lbRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  lbRowUser: { backgroundColor: colors.primary + '08', marginHorizontal: -spacing.lg, paddingHorizontal: spacing.lg, borderRadius: radius.md },
  lbRank: { fontSize: 16, fontWeight: '800', color: colors.text.muted, width: 40 },
  lbAvatar: { marginRight: spacing.md },
  lbName: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.text.primary },
  lbScore: { fontSize: 16, fontWeight: '800' },
});
