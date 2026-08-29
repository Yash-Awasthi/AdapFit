/**
 * Addiction Recovery — Recovery Journey Tracker
 * Sobriety counter, trigger tracking, coping strategies, support network, milestones.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium, StatCard } from '../../src/components/PremiumComponents';
import { MiniLineChart, Sparkline } from '../../src/components/HealthCharts';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  substance: 'Alcohol',
  soberDays: 142,
  longestStreak: 142,
  milestones: [
    { days: 1, label: 'First Step', emoji: '🌱', achieved: true },
    { days: 7, label: 'One Week', emoji: '💪', achieved: true },
    { days: 30, label: '30 Days', emoji: '⭐', achieved: true },
    { days: 90, label: '90 Days', emoji: '🎯', achieved: true },
    { days: 180, label: '6 Months', emoji: '🏆', achieved: false },
    { days: 365, label: '1 Year', emoji: '🌟', achieved: false },
  ],
  triggers: [
    { name: 'Stress', frequency: 8, resisted: 6, icon: 'flash' },
    { name: 'Social Pressure', frequency: 5, resisted: 5, icon: 'people' },
    { name: 'Loneliness', frequency: 4, resisted: 3, icon: 'person' },
    { name: 'Boredom', frequency: 6, resisted: 5, icon: 'time' },
    { name: 'Celebration', frequency: 3, resisted: 3, icon: 'wine' },
  ],
  copingStrategies: [
    { name: 'Deep Breathing', uses: 24, effectiveness: 85, icon: 'leaf' },
    { name: 'Call Support', uses: 12, effectiveness: 90, icon: 'call' },
    { name: 'Exercise', uses: 18, effectiveness: 80, icon: 'fitness' },
    { name: 'Journaling', uses: 15, effectiveness: 70, icon: 'book' },
    { name: 'Meditation', uses: 20, effectiveness: 75, icon: 'meditation' },
  ],
  supportNetwork: [
    { name: 'Sarah M.', role: 'Sponsor', available: true },
    { name: 'Mike R.', role: 'Accountability Partner', available: false },
    { name: 'Dr. Chen', role: 'Therapist', available: true },
  ],
  weeklyMood: [6, 7, 5, 7, 8, 7, 8],
  cravingsOverTime: [8, 7, 6, 5, 4, 3, 2],
  resistanceRate: 91,
  journalEntries: 28,
};

export default function AddictionRecoveryScreen() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#10B981', '#06B6D4', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Recovery Journey</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{mockData.substance}</Text>
          <View style={styles.soberCount}>
            <Text style={[typography.metric.hero, { color: '#fff' }]}>{mockData.soberDays}</Text>
            <Text style={[typography.body.lg, { color: 'rgba(255,255,255,0.7)' }]}>Days Sober</Text>
          </View>
          <View style={styles.statsRow}>
            <View style={styles.statBox}>
              <Text style={[typography.metric.small, { color: '#fff' }]}>{mockData.resistanceRate}%</Text>
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Resistance</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Text style={[typography.metric.small, { color: '#fff' }]}>{mockData.journalEntries}</Text>
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Journal Entries</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Text style={[typography.metric.small, { color: '#fff' }]}>{mockData.longestStreak}</Text>
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Best Streak</Text>
            </View>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Milestones" icon="trophy" iconColor={colors.health.energy} />
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
            {mockData.milestones.map((m, i) => (
              <View key={i} style={[styles.milestoneCard, m.achieved && styles.milestoneAchieved]}>
                <Text style={{ fontSize: 28 }}>{m.emoji}</Text>
                <Text style={[typography.body.sm, { color: m.achieved ? colors.health.success : colors.text.muted, marginTop: 4 }]}>{m.days} days</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{m.label}</Text>
                {m.achieved && <Ionicons name="checkmark-circle" size={16} color={colors.health.success} style={{ marginTop: 4 }} />}
              </View>
            ))}
          </ScrollView>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Trends" icon="trending-up" iconColor={colors.health.calm} />
          <View style={styles.trendRow}>
            <GlassCard style={{ flex: 1 }}>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>Mood</Text>
              <MiniLineChart data={mockData.weeklyMood} color={colors.health.calm} height={50} width={140} />
            </GlassCard>
            <GlassCard style={{ flex: 1 }}>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>Cravings ↓</Text>
              <MiniLineChart data={mockData.cravingsOverTime} color={colors.health.heart} height={50} width={140} />
            </GlassCard>
          </View>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Triggers" icon="warning" iconColor={colors.health.warning} />
          {mockData.triggers.map((t, i) => (
            <View key={i} style={styles.triggerRow}>
              <Ionicons name={t.icon as any} size={18} color={colors.health.warning} />
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{t.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{t.resisted}/{t.frequency} resisted ({Math.round(t.resisted / t.frequency * 100)}%)</Text>
              </View>
              <View style={[styles.resistBar, { backgroundColor: colors.health.success + '20' }]}>
                <View style={[styles.resistBarFill, { width: `${t.resisted / t.frequency * 100}%`, backgroundColor: colors.health.success }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Coping Strategies" icon="shield-checkmark" iconColor={colors.health.calm} />
          {mockData.copingStrategies.map((c, i) => (
            <View key={i} style={styles.copingRow}>
              <Ionicons name={c.icon as any} size={18} color={colors.primary} />
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{c.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{c.uses} uses • {c.effectiveness}% effective</Text>
              </View>
              <View style={[styles.effBar, { backgroundColor: colors.health.success + '20' }]}>
                <View style={[styles.effBarFill, { width: `${c.effectiveness}%`, backgroundColor: colors.health.success }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Support Network" icon="people" iconColor={colors.primary} />
          {mockData.supportNetwork.map((s, i) => (
            <View key={i} style={styles.supportRow}>
              <View style={[styles.avatar, { backgroundColor: colors.primary + '20' }]}>
                <Text style={[typography.body.md, { color: colors.primary, fontWeight: '700' }]}>{s.name[0]}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{s.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{s.role}</Text>
              </View>
              <View style={[styles.statusDot, { backgroundColor: s.available ? colors.health.success : colors.text.muted }]} />
            </View>
          ))}
        </View>
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
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
  trendRow: { flexDirection: 'row', gap: 10 },
  triggerRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, gap: 10, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  resistBar: { width: 60, height: 6, borderRadius: 3, overflow: 'hidden' },
  resistBarFill: { height: '100%', borderRadius: 3 },
  copingRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  effBar: { width: 50, height: 6, borderRadius: 3, overflow: 'hidden' },
  effBarFill: { height: '100%', borderRadius: 3 },
  supportRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, gap: 12, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  avatar: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  statusDot: { width: 10, height: 10, borderRadius: 5 },
});
