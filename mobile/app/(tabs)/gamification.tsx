/**
 * Gamification — Premium XP, Badges, Streaks, Leaderboard
 * Animated XP bar, badge grid with unlock effects, streak fire
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
const { width: SCREEN_WIDTH } = Dimensions.get('window');
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { Confetti, Pulse } from '../../src/components/AnimationSystem';
import { StaggeredList } from '../../src/components/AnimationSystem';

const XP_LEVEL = { current: 12, xp: 2750, xpNeeded: 3000, title: 'Fitness Enthusiast' };

const BADGES = [
  { id: 1, name: 'First Workout', icon: '🏋️', unlocked: true, color: '#22C55E' },
  { id: 2, name: '7-Day Streak', icon: '🔥', unlocked: true, color: '#F97316' },
  { id: 3, name: 'Early Bird', icon: '🌅', unlocked: true, color: '#F59E0B' },
  { id: 4, name: 'Hydration Hero', icon: '💧', unlocked: true, color: '#3B82F6' },
  { id: 5, name: '100 Workouts', icon: '💪', unlocked: false, color: '#8B5CF6' },
  { id: 6, name: 'Sleep Master', icon: '😴', unlocked: true, color: '#6366F1' },
  { id: 7, name: 'Meditation Guru', icon: '🧘', unlocked: false, color: '#EC4899' },
  { id: 8, name: 'Marathon Runner', icon: '🏃', unlocked: false, color: '#EF4444' },
  { id: 9, name: 'Nutrition Pro', icon: '🥗', unlocked: true, color: '#22C55E' },
  { id: 10, name: 'Social Butterfly', icon: '🦋', unlocked: false, color: '#F59E0B' },
  { id: 11, name: 'Iron Will', icon: '⚡', unlocked: false, color: '#F97316' },
  { id: 12, name: 'Health Champion', icon: '🏆', unlocked: false, color: '#F59E0B' },
];

const ACHIEVEMENTS = [
  { title: 'Workout Streak', value: '5 days', icon: 'flame', color: '#F97316' },
  { title: 'Total Workouts', value: '47', icon: 'barbell', color: '#22C55E' },
  { title: 'Calories Burned', value: '12,400', icon: 'flame', color: '#EF4444' },
  { title: 'Badges Earned', value: '8/12', icon: 'trophy', color: '#F59E0B' },
];

export default function GamificationScreen() {
  const [showConfetti, setShowConfetti] = useState(false);
  const fireAnim = useRef(new Animated.Value(1)).current;
  const xpAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animate XP bar
    Animated.timing(xpAnim, { toValue: XP_LEVEL.xp / XP_LEVEL.xpNeeded, duration: 1000, useNativeDriver: false }).start();

    // Fire animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(fireAnim, { toValue: 1.2, duration: 300, useNativeDriver: true }),
        Animated.timing(fireAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <ScreenWrapper
      title="Achievements"
      subtitle="Your fitness journey milestones"
      gradient={['#F59E0B', '#F97316']}
      rightAction={{ icon: 'trophy', onPress: () => {} }}
    >
      <Confetti visible={showConfetti} />

      {/* Level & XP */}
      <GlassCard variant="light" style={styles.levelCard}>
        <View style={styles.levelHeader}>
          <View style={styles.levelBadge}>
            <Animated.Text style={[styles.levelNumber, { transform: [{ scale: fireAnim }] }]}>🔥</Animated.Text>
            <Text style={styles.levelValue}>{XP_LEVEL.current}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.levelTitle}>{XP_LEVEL.title}</Text>
            <Text style={styles.levelXP}>{XP_LEVEL.xp.toLocaleString()} / {XP_LEVEL.xpNeeded.toLocaleString()} XP</Text>
          </View>
        </View>
        <View style={styles.xpBarContainer}>
          <View style={styles.xpBar}>
            <Animated.View style={[styles.xpBarFill, { width: xpAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }) }]} />
          </View>
          <Text style={styles.xpPercent}>{Math.round((XP_LEVEL.xp / XP_LEVEL.xpNeeded) * 100)}%</Text>
        </View>
        <Text style={styles.xpRemaining}>{XP_LEVEL.xpNeeded - XP_LEVEL.xp} XP to next level</Text>
      </GlassCard>

      {/* Quick Stats */}
      <View style={styles.statsGrid}>
        {ACHIEVEMENTS.map((a, i) => (
          <GlassCard key={i} variant="light" style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: a.color + '15' }]}>
              <Ionicons name={a.icon as any} size={18} color={a.color} />
            </View>
            <Text style={[styles.statValue, { color: a.color }]}>{a.value}</Text>
            <Text style={styles.statLabel}>{a.title}</Text>
          </GlassCard>
        ))}
      </View>

      {/* Badges */}
      <SectionHeaderPremium icon="trophy" iconColor="#F59E0B" title="Badge Collection" subtitle={`${BADGES.filter(b => b.unlocked).length}/${BADGES.length} unlocked`} />
      <View style={styles.badgeGrid}>
        {BADGES.map((badge, i) => (
          <TouchableOpacity
            key={badge.id}
            style={[styles.badgeItem, !badge.unlocked && styles.badgeLocked]}
            onPress={() => {
              if (badge.unlocked) {
                setShowConfetti(true);
                setTimeout(() => setShowConfetti(false), 3000);
              }
            }}
          >
            <View style={[styles.badgeIcon, badge.unlocked && { backgroundColor: badge.color + '15' }]}>
              <Text style={styles.badgeEmoji}>{badge.unlocked ? badge.icon : '🔒'}</Text>
            </View>
            <Text style={[styles.badgeName, !badge.unlocked && { color: colors.text.muted }]} numberOfLines={1}>{badge.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Leaderboard */}
      <SectionHeaderPremium icon="podium" iconColor="#EF4444" title="Leaderboard" />
      <GlassCard variant="light" style={styles.leaderboardCard}>
        {[
          { rank: 1, name: 'Sarah M.', score: 9850, avatar: '👩', isUser: false },
          { rank: 2, name: 'You', score: 8720, avatar: '🧑', isUser: true },
          { rank: 3, name: 'Mike R.', score: 8200, avatar: '👨', isUser: false },
        ].map((entry, i) => (
          <View key={i} style={[styles.lbRow, entry.isUser && styles.lbRowUser]}>
            <Text style={[styles.lbRank, entry.rank === 1 && { color: '#F59E0B' }]}>#{entry.rank}</Text>
            <Text style={styles.lbAvatar}>{entry.avatar}</Text>
            <Text style={[styles.lbName, entry.isUser && { color: colors.primary }]}>{entry.name}</Text>
            <Text style={[styles.lbScore, { color: colors.primary }]}>{entry.score.toLocaleString()}</Text>
          </View>
        ))}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  // Level
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

  // Stats
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  statCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md) / 2, alignItems: 'center', paddingVertical: spacing.md },
  statIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  statValue: { fontSize: 20, fontWeight: '800' },
  statLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  // Badges
  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  badgeItem: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md * 3) / 4, alignItems: 'center' },
  badgeLocked: { opacity: 0.5 },
  badgeIcon: { width: 56, height: 56, borderRadius: 28, backgroundColor: colors.bg.card, justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border },
  badgeEmoji: { fontSize: 24 },
  badgeName: { fontSize: 10, fontWeight: '600', color: colors.text.secondary, marginTop: 4, textAlign: 'center' },

  // Leaderboard
  leaderboardCard: { marginHorizontal: spacing.screenPadding },
  lbRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  lbRowUser: { backgroundColor: colors.primary + '08', marginHorizontal: -spacing.lg, paddingHorizontal: spacing.lg, borderRadius: radius.md },
  lbRank: { fontSize: 16, fontWeight: '800', color: colors.text.muted, width: 40 },
  lbAvatar: { fontSize: 24, marginRight: spacing.md },
  lbName: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.text.primary },
  lbScore: { fontSize: 16, fontWeight: '800' },
});
