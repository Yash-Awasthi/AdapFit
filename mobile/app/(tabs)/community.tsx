/**
 * Community — Premium Health Challenges & Social Features
 * Glassmorphism cards, animated elements, leaderboard, challenges
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, glass } from '../../src/theme';
import {
  ScoreRing, GlassCard, SectionHeaderPremium, QuickAction, PillChip,
} from '../../src/components/PremiumComponents';
import { StaggeredList } from '../../src/components/AnimationSystem';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const CHALLENGES = [
  { id: 1, title: '10K Steps Daily', icon: 'footsteps', color: colors.health.activity, participants: 234, progress: 72, daysLeft: 5, joined: true },
  { id: 2, title: '30-Day Meditation', icon: 'meditate', color: colors.health.mental, participants: 189, progress: 45, daysLeft: 18, joined: true },
  { id: 3, title: 'Hydration Hero', icon: 'water', color: '#3B82F6', participants: 312, progress: 0, daysLeft: 30, joined: false },
  { id: 4, title: 'No Sugar Week', icon: 'restaurant', color: colors.health.nutrition, participants: 156, progress: 30, daysLeft: 4, joined: false },
  { id: 5, title: 'Sleep Champion', icon: 'moon', color: colors.health.sleep, participants: 98, progress: 60, daysLeft: 10, joined: true },
];

const LEADERBOARD = [
  { rank: 1, name: 'Sarah M.', score: 9850, avatar: '👩', streak: 15 },
  { rank: 2, name: 'You', score: 8720, avatar: '🧑', streak: 5, isUser: true },
  { rank: 3, name: 'Mike R.', score: 8200, avatar: '👨', streak: 8 },
  { rank: 4, name: 'Emma L.', score: 7800, avatar: '👩', streak: 12 },
  { rank: 5, name: 'James K.', score: 7200, avatar: '🧑', streak: 3 },
];

export default function CommunityScreen() {
  const [activeTab, setActiveTab] = useState<'challenges' | 'leaderboard' | 'feed'>('challenges');
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <LinearGradient colors={['#EC4899', '#F472B6']} style={styles.header}>
        <Text style={styles.headerTitle}>👥 Community</Text>
        <Text style={styles.headerSubtitle}>Connect, compete, and grow together</Text>
      </LinearGradient>

      {/* Tab Selector */}
      <View style={styles.tabRow}>
        {(['challenges', 'leaderboard', 'feed'] as const).map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tabPill, activeTab === tab && styles.tabPillActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabPillText, activeTab === tab && styles.tabPillTextActive]}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeTab === 'challenges' && (
        <StaggeredList staggerDelay={100} animationType="slideIn">
          {CHALLENGES.map(challenge => (
            <GlassCard key={challenge.id} variant="light" style={styles.challengeCard}>
              <View style={styles.challengeHeader}>
                <View style={[styles.challengeIcon, { backgroundColor: challenge.color + '15' }]}>
                  <Ionicons name={challenge.icon as any} size={24} color={challenge.color} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.challengeTitle}>{challenge.title}</Text>
                  <Text style={styles.challengeMeta}>{challenge.participants} participants • {challenge.daysLeft} days left</Text>
                </View>
                {challenge.joined && (
                  <View style={[styles.joinedBadge, { backgroundColor: challenge.color + '15' }]}>
                    <Text style={[styles.joinedText, { color: challenge.color }]}>Joined</Text>
                  </View>
                )}
              </View>
              {challenge.joined && (
                <View style={styles.challengeProgress}>
                  <View style={styles.progressBar}>
                    <View style={[styles.progressFill, { width: `${challenge.progress}%`, backgroundColor: challenge.color }]} />
                  </View>
                  <Text style={[styles.progressText, { color: challenge.color }]}>{challenge.progress}%</Text>
                </View>
              )}
              {!challenge.joined && (
                <TouchableOpacity style={[styles.joinBtn, { backgroundColor: challenge.color }]}>
                  <Text style={styles.joinBtnText}>Join Challenge</Text>
                </TouchableOpacity>
              )}
            </GlassCard>
          ))}
        </StaggeredList>
      )}

      {activeTab === 'leaderboard' && (
        <View style={styles.leaderboardContainer}>
          {LEADERBOARD.map((entry, i) => (
            <GlassCard key={i} variant="light" style={[styles.leaderboardCard, entry.isUser && styles.leaderboardCardUser]}>
              <View style={styles.leaderboardRank}>
                {entry.rank <= 3 ? (
                  <View style={[styles.rankBadge, { backgroundColor: entry.rank === 1 ? '#F59E0B' : entry.rank === 2 ? '#94A3B8' : '#CD7F32' }]}>
                    <Text style={styles.rankBadgeText}>{entry.rank}</Text>
                  </View>
                ) : (
                  <Text style={styles.rankNumber}>#{entry.rank}</Text>
                )}
              </View>
              <Text style={styles.leaderboardAvatar}>{entry.avatar}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[styles.leaderboardName, entry.isUser && { color: colors.primary }]}>{entry.name}</Text>
                <Text style={styles.leaderboardStreak}>🔥 {entry.streak} day streak</Text>
              </View>
              <Text style={[styles.leaderboardScore, { color: colors.primary }]}>{entry.score.toLocaleString()}</Text>
            </GlassCard>
          ))}
        </View>
      )}

      {activeTab === 'feed' && (
        <View style={styles.feedContainer}>
          <GlassCard variant="light" style={styles.feedCard}>
            <View style={styles.feedHeader}>
              <Text style={styles.feedAvatar}>👩</Text>
              <View>
                <Text style={styles.feedName}>Sarah M.</Text>
                <Text style={styles.feedTime}>2 hours ago</Text>
              </View>
            </View>
            <Text style={styles.feedText}>Just completed my 10K steps challenge! 🎉 15-day streak! Who's joining me tomorrow?</Text>
            <View style={styles.feedActions}>
              <TouchableOpacity style={styles.feedAction}>
                <Ionicons name="heart-outline" size={18} color={colors.text.muted} />
                <Text style={styles.feedActionText}>24</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.feedAction}>
                <Ionicons name="chatbubble-outline" size={18} color={colors.text.muted} />
                <Text style={styles.feedActionText}>8</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.feedAction}>
                <Ionicons name="share-outline" size={18} color={colors.text.muted} />
              </TouchableOpacity>
            </View>
          </GlassCard>
        </View>
      )}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  // Tabs
  tabRow: { flexDirection: 'row', justifyContent: 'center', gap: spacing.sm, marginTop: spacing.lg, paddingHorizontal: spacing.screenPadding },
  tabPill: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  tabPillActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  tabPillText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  tabPillTextActive: { color: '#FFF' },

  // Challenges
  challengeCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  challengeHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  challengeIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  challengeTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  challengeMeta: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  joinedBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6 },
  joinedText: { fontSize: 11, fontWeight: '700' },
  challengeProgress: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md },
  progressBar: { flex: 1, height: 6, backgroundColor: colors.surface.divider, borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3 },
  progressText: { fontSize: 12, fontWeight: '700' },
  joinBtn: { marginTop: spacing.md, paddingVertical: spacing.md, borderRadius: radius.button, alignItems: 'center' },
  joinBtnText: { fontSize: 14, fontWeight: '700', color: '#FFF' },

  // Leaderboard
  leaderboardContainer: { paddingHorizontal: spacing.screenPadding },
  leaderboardCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  leaderboardCardUser: { borderColor: colors.primary + '40', borderWidth: 2 },
  leaderboardRank: { width: 32 },
  rankBadge: { width: 28, height: 28, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  rankBadgeText: { fontSize: 12, fontWeight: '800', color: '#FFF' },
  rankNumber: { fontSize: 14, fontWeight: '700', color: colors.text.muted, textAlign: 'center' },
  leaderboardAvatar: { fontSize: 28 },
  leaderboardName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  leaderboardStreak: { fontSize: 11, color: colors.text.muted, marginTop: 2 },
  leaderboardScore: { fontSize: 16, fontWeight: '800' },

  // Feed
  feedContainer: { paddingHorizontal: spacing.screenPadding },
  feedCard: {},
  feedHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  feedAvatar: { fontSize: 32 },
  feedName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  feedTime: { fontSize: 12, color: colors.text.muted },
  feedText: { fontSize: 14, color: colors.text.secondary, lineHeight: 20, marginBottom: spacing.md },
  feedActions: { flexDirection: 'row', gap: spacing.xl },
  feedAction: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  feedActionText: { fontSize: 13, color: colors.text.muted },
});
