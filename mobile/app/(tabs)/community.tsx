/**
 * Community — challenges, the leaderboard and the shared feed.
 *
 * The leaderboard ranks by achievement points, which only logged activity
 * earns. Other members appear by rank alone. The feed is
 * what people chose to share; an empty community reads as empty rather than
 * as five invented members with streaks.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, Alert, RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { GlassCard } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type Tab = 'challenges' | 'leaderboard' | 'feed';

interface Challenge {
  id: string;
  name: string;
  description: string;
  category: string;
  target_value: number;
  target_unit: string;
  duration_days: number;
  difficulty: string;
  participant_count: number;
  is_active: boolean;
  ends_at: string;
}

interface LeaderboardEntry {
  rank: number;
  name: string;
  points: number;
  is_you: boolean;
}

interface Share {
  id: string;
  user_id: string;
  user_name: string;
  title: string;
  caption: string;
  exercises_summary: string;
  duration_minutes: number;
  likes: number;
  comments_count: number;
  shared_at: string;
}

const CATEGORY_STYLE: Record<string, { icon: string; color: string }> = {
  steps: { icon: 'footsteps', color: colors.health.activity },
  cardio: { icon: 'heart', color: colors.health.heart },
  strength: { icon: 'barbell', color: colors.health.energy },
  mindfulness: { icon: 'leaf', color: colors.health.mental },
  hydration: { icon: 'water', color: '#3B82F6' },
  sleep: { icon: 'moon', color: colors.health.sleep },
  nutrition: { icon: 'restaurant', color: colors.health.nutrition },
};

function styleFor(category: string) {
  return CATEGORY_STYLE[category?.toLowerCase()] ?? { icon: 'trophy', color: colors.primary };
}

function daysLeft(endsAt: string): number | null {
  const end = new Date(endsAt).getTime();
  if (Number.isNaN(end)) return null;
  return Math.max(0, Math.ceil((end - Date.now()) / 86400_000));
}

function timeAgo(iso: string): string {
  const when = new Date(iso).getTime();
  if (Number.isNaN(when)) return '';
  const hours = Math.floor((Date.now() - when) / 3600_000);
  if (hours < 1) return 'just now';
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

export default function CommunityScreen() {
  const userId = useUserStore((s) => s.userId);
  const [activeTab, setActiveTab] = useState<Tab>('challenges');
  const [joining, setJoining] = useState<string | null>(null);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    challenges: Challenge[];
    leaderboard: { leaderboard: LeaderboardEntry[] };
    feed: Share[];
  }>({
    challenges: '/challenges',
    leaderboard: '/achievements/leaderboard?limit=20',
    feed: '/community/feed',
  });

  const challenges = asArray<Challenge>(data.challenges);
  const leaderboard = asArray<LeaderboardEntry>(data.leaderboard?.leaderboard);
  const feed = asArray<Share>(data.feed);

  const join = useCallback(async (challenge: Challenge) => {
    setJoining(challenge.id);
    const result = await postJson(`/challenges/join/${challenge.id}`, {});
    setJoining(null);
    if (!result) {
      Alert.alert('Could not join', 'The challenge could not be joined. Try again when you are online.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    await reload();
  }, [reload]);

  const like = useCallback(async (share: Share) => {
    Haptics.selectionAsync();
    await postJson(`/community/${share.id}/like`, {});
    await reload();
  }, [reload]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />
      }
    >
      <LinearGradient colors={['#EC4899', '#F472B6']} style={styles.header}>
        <Text style={styles.headerTitle} accessibilityRole="header">Community</Text>
        <Text style={styles.headerSubtitle}>Connect, compete, and grow together</Text>
      </LinearGradient>

      <View style={styles.tabRow}>
        {(['challenges', 'leaderboard', 'feed'] as Tab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tabPill, activeTab === tab && styles.tabPillActive]}
            onPress={() => setActiveTab(tab)}
            accessibilityRole="tab"
            accessibilityState={{ selected: activeTab === tab }}
          >
            <Text style={[styles.tabPillText, activeTab === tab && styles.tabPillTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && <Text style={styles.emptyText}>Loading…</Text>}

      {!loading && activeTab === 'challenges' && (
        challenges.length === 0 ? (
          <GlassCard variant="light" style={styles.challengeCard}>
            <Text style={styles.emptyTitle}>No challenges running</Text>
            <Text style={styles.emptyText}>
              When a challenge is created it appears here with how many people have joined.
            </Text>
          </GlassCard>
        ) : (
          challenges.map((challenge) => {
            const style = styleFor(challenge.category);
            const remaining = daysLeft(challenge.ends_at);
            return (
              <GlassCard key={challenge.id} variant="light" style={styles.challengeCard}>
                <View style={styles.challengeHeader}>
                  <View style={[styles.challengeIcon, { backgroundColor: style.color + '15' }]}>
                    <Ionicons name={style.icon as any} size={24} color={style.color} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.challengeTitle}>{challenge.name}</Text>
                    <Text style={styles.challengeMeta}>
                      {challenge.participant_count} participant{challenge.participant_count === 1 ? '' : 's'}
                      {remaining !== null ? ` • ${remaining} day${remaining === 1 ? '' : 's'} left` : ''}
                    </Text>
                  </View>
                  <View style={[styles.joinedBadge, { backgroundColor: style.color + '15' }]}>
                    <Text style={[styles.joinedText, { color: style.color }]}>{challenge.difficulty}</Text>
                  </View>
                </View>
                <Text style={styles.challengeDesc}>{challenge.description}</Text>
                <Text style={styles.challengeTarget}>
                  Target: {challenge.target_value} {challenge.target_unit} over {challenge.duration_days} days
                </Text>
                <TouchableOpacity
                  style={[styles.joinBtn, { backgroundColor: style.color }]}
                  onPress={() => join(challenge)}
                  disabled={joining === challenge.id}
                  accessibilityRole="button"
                  accessibilityLabel={`Join ${challenge.name}`}
                >
                  <Text style={styles.joinBtnText}>
                    {joining === challenge.id ? 'Joining…' : 'Join Challenge'}
                  </Text>
                </TouchableOpacity>
              </GlassCard>
            );
          })
        )
      )}

      {!loading && activeTab === 'leaderboard' && (
        <View style={styles.leaderboardContainer}>
          {leaderboard.length === 0 ? (
            <GlassCard variant="light" style={styles.leaderboardCard}>
              <Text style={styles.emptyTitle}>Nobody on the board yet</Text>
              <Text style={styles.emptyText}>
                Points come from logged sessions and earned badges. The board fills in as
                people train.
              </Text>
            </GlassCard>
          ) : (
            leaderboard.map((entry) => {
              const isUser = entry.is_you;
              return (
                <GlassCard
                  key={entry.rank}
                  variant="light"
                  style={[styles.leaderboardCard, isUser && styles.leaderboardCardUser]}
                >
                  <View style={styles.leaderboardRank}>
                    {entry.rank <= 3 ? (
                      <View style={[styles.rankBadge, {
                        backgroundColor: entry.rank === 1 ? '#F59E0B' : entry.rank === 2 ? '#94A3B8' : '#CD7F32',
                      }]}>
                        <Text style={styles.rankBadgeText}>{entry.rank}</Text>
                      </View>
                    ) : (
                      <Text style={styles.rankNumber}>#{entry.rank}</Text>
                    )}
                  </View>
                  <Ionicons name="person" size={28} color={colors.text.secondary} style={styles.leaderboardAvatar} />
                  <View style={{ flex: 1 }}>
                    <Text
                      style={[styles.leaderboardName, isUser && { color: colors.primary }]}
                      numberOfLines={1}
                    >
                      {entry.name}
                    </Text>
                  </View>
                  <Text style={[styles.leaderboardScore, { color: colors.primary }]}>
                    {entry.points.toLocaleString()}
                  </Text>
                </GlassCard>
              );
            })
          )}
        </View>
      )}

      {!loading && activeTab === 'feed' && (
        <View style={styles.feedContainer}>
          {feed.length === 0 ? (
            <GlassCard variant="light" style={styles.feedCard}>
              <Text style={styles.emptyTitle}>Nothing shared yet</Text>
              <Text style={styles.emptyText}>
                Finish a workout and share it, and it appears here for everyone else.
              </Text>
            </GlassCard>
          ) : (
            feed.map((share) => (
              <GlassCard key={share.id} variant="light" style={styles.feedCard}>
                <View style={styles.feedHeader}>
                  <Ionicons name="person-circle" size={36} color={colors.text.secondary} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.feedName}>
                      {share.user_id === userId ? 'You' : share.user_name}
                    </Text>
                    <Text style={styles.feedTime}>{timeAgo(share.shared_at)}</Text>
                  </View>
                </View>
                <Text style={styles.feedTitle}>{share.title}</Text>
                {share.caption ? <Text style={styles.feedCaption}>{share.caption}</Text> : null}
                <Text style={styles.feedSummary}>
                  {share.exercises_summary} · {share.duration_minutes} min
                </Text>
                <View style={styles.feedActions}>
                  <TouchableOpacity
                    style={styles.feedAction}
                    onPress={() => like(share)}
                    accessibilityRole="button"
                    accessibilityLabel={`Like ${share.title}`}
                  >
                    <Ionicons name="heart-outline" size={18} color={colors.health.heart} />
                    <Text style={styles.feedActionText}>{share.likes}</Text>
                  </TouchableOpacity>
                  <View style={styles.feedAction}>
                    <Ionicons name="chatbubble-outline" size={16} color={colors.text.muted} />
                    <Text style={styles.feedActionText}>{share.comments_count}</Text>
                  </View>
                </View>
              </GlassCard>
            ))
          )}
        </View>
      )}

      <View style={{ height: 80 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },
  header: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 26, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.75)', marginTop: 4 },

  tabRow: { flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.screenPadding, marginTop: spacing.lg, marginBottom: spacing.md },
  tabPill: { flex: 1, paddingVertical: 10, borderRadius: 999, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
  tabPillActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  tabPillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  tabPillTextActive: { color: '#FFF' },

  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyText: { fontSize: 13, color: colors.text.muted, marginTop: 6, lineHeight: 19, paddingHorizontal: spacing.screenPadding },

  challengeCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  challengeHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  challengeIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  challengeTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  challengeMeta: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  challengeDesc: { fontSize: 13, color: colors.text.secondary, marginTop: spacing.md, lineHeight: 18 },
  challengeTarget: { fontSize: 12, color: colors.text.muted, marginTop: spacing.xs },
  joinedBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  joinedText: { fontSize: 11, fontWeight: '700', textTransform: 'capitalize' },
  joinBtn: { paddingVertical: spacing.md, borderRadius: radius.button, alignItems: 'center', marginTop: spacing.md },
  joinBtnText: { fontSize: 14, fontWeight: '700', color: '#FFF' },

  leaderboardContainer: { paddingHorizontal: 0 },
  leaderboardCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm, flexDirection: 'row', alignItems: 'center' },
  leaderboardCardUser: { borderColor: colors.primary, borderWidth: 1 },
  leaderboardRank: { width: 44, alignItems: 'center' },
  rankBadge: { width: 28, height: 28, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  rankBadgeText: { fontSize: 13, fontWeight: '800', color: '#FFF' },
  rankNumber: { fontSize: 14, fontWeight: '700', color: colors.text.muted },
  leaderboardAvatar: { marginRight: spacing.md },
  leaderboardName: { fontSize: 15, fontWeight: '600', color: colors.text.primary },
  leaderboardScore: { fontSize: 16, fontWeight: '800' },

  feedContainer: {},
  feedCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  feedHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm },
  feedName: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  feedTime: { fontSize: 11, color: colors.text.muted, marginTop: 1 },
  feedTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  feedCaption: { fontSize: 13, color: colors.text.secondary, marginTop: 4, lineHeight: 18 },
  feedSummary: { fontSize: 12, color: colors.text.muted, marginTop: spacing.xs },
  feedActions: { flexDirection: 'row', gap: spacing.lg, marginTop: spacing.md },
  feedAction: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  feedActionText: { fontSize: 12, color: colors.text.muted, fontWeight: '600' },
});
