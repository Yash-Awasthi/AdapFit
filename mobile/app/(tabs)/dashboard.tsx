/**
 * Dashboard — Unified Health Overview
 * Premium glassmorphism design with animated health score ring,
 * today's summary, quick actions, medications, challenges, activity feed.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Animated, Dimensions, RefreshControl, StatusBar, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { colors, spacing, radius, glass, typography, shadows } from '../../src/theme';
import { ScoreRing, GlassCard, AnimatedHeader, HealthMetricMini, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { useUserStore } from '../../src/stores/userStore';
import { api } from '../../src/services/api';
import { getJson } from '../../src/services/http';
import { fetchHealthData } from '../../src/services/healthBridge';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ─── Health tip pool ──────────────────────────────────────────
const HEALTH_TIPS = [
  { title: 'Sleep Hygiene Tip', text: 'Keep your bedroom cool (65-68°F) and dark for optimal sleep quality.', icon: 'moon', color: colors.health.sleep },
  { title: 'Hydration Reminder', text: 'Drink a glass of water 30 minutes before each meal to improve digestion and avoid overeating.', icon: 'water', color: '#3B82F6' },
  { title: 'Movement Break', text: 'Stand up and stretch for 2 minutes every hour. Small movements add up to big health benefits.', icon: 'walk', color: colors.health.activity },
  { title: 'Stress Relief', text: 'Try 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s. Repeat 3 times for immediate calm.', icon: 'leaf', color: colors.health.calm },
  { title: 'Nutrition Tip', text: 'Include protein in every meal. It keeps you full longer and supports muscle recovery.', icon: 'nutrition', color: colors.health.nutrition },
];

function getDailyTip() {
  const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000);
  return HEALTH_TIPS[dayOfYear % HEALTH_TIPS.length];
}

// ─── Mini Activity Ring ───────────────────────────────────────
function MiniActivityRing({ progress, color, size = 48, strokeWidth = 4 }: { progress: number; color: string; size?: number; strokeWidth?: number }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(anim, { toValue: 1, duration: 800, useNativeDriver: false }).start();
  }, []);
  const fill = anim.interpolate({ inputRange: [0, 1], outputRange: [0, progress / 100] });
  return (
    <View style={{ width: size, height: size }}>
      <View style={[styles.ringBg, { width: size, height: size, borderRadius: size / 2, borderWidth: strokeWidth, borderColor: color + '20' }]} />
      <Animated.View style={[styles.ringFill, {
        width: size, height: size, borderRadius: size / 2,
        borderWidth: strokeWidth, borderColor: color,
        transform: [{ rotate: '-90deg' }],
        // Use border trick: we fake partial ring with opacity
        opacity: fill,
      }]} />
      <View style={[styles.ringCenter, { width: size - strokeWidth * 2, height: size - strokeWidth * 2, borderRadius: (size - strokeWidth * 2) / 2 }]}>
        <Text style={[typography.label.sm, { color: color }]}>{Math.round(progress)}%</Text>
      </View>
    </View>
  );
}

// ─── Today Metric Card ────────────────────────────────────────
function TodayMetric({ icon, label, value, unit, goal, color, progress }: {
  icon: string; label: string; value: number | string; unit: string; goal: number; color: string; progress: number;
}) {
  return (
    <View style={styles.metricCard}>
      <View style={[styles.metricIcon, { backgroundColor: color + '18' }]}>
        <Ionicons name={icon as any} size={18} color={color} />
      </View>
      <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 6 }]}>{label}</Text>
      <Text style={[typography.metric.small, { color: colors.text.primary, marginTop: 2 }]}>
        {value}<Text style={[typography.body.xs, { color: colors.text.muted }]}> {unit}</Text>
      </Text>
      <View style={[styles.miniProgress, { backgroundColor: color + '20' }]}>
        <View style={[styles.miniProgressFill, { width: `${Math.min(progress, 100)}%`, backgroundColor: color }]} />
      </View>
      <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 4 }]}>Goal: {goal.toLocaleString()} {unit}</Text>
    </View>
  );
}

// ─── Quick Action Button ──────────────────────────────────────
function QuickActionButton({ icon, label, color, onPress }: { icon: string; label: string; color: string; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7} style={styles.quickAction}>
      <View style={[styles.quickActionIcon, { backgroundColor: color + '18' }]}>
        <Ionicons name={icon as any} size={22} color={color} />
      </View>
      <Text style={[typography.body.sm, { color: colors.text.secondary, marginTop: 6 }]}>{label}</Text>
    </TouchableOpacity>
  );
}

// ─── Medication Card ──────────────────────────────────────────
function MedicationCard({ name, dosage, time, taken }: { name: string; dosage: string; time: string; taken: boolean }) {
  return (
    <TouchableOpacity activeOpacity={0.7} style={[styles.medCard, taken && styles.medCardTaken]}>
      <View style={[styles.medCheck, { backgroundColor: taken ? colors.health.success : 'transparent', borderColor: taken ? colors.health.success : colors.surface.border }]}>
        {taken && <Ionicons name="checkmark" size={12} color="#fff" />}
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[typography.body.md, { color: taken ? colors.text.muted : colors.text.primary, textDecorationLine: taken ? 'line-through' : 'none' }]}>{name}</Text>
        <Text style={[typography.body.sm, { color: colors.text.muted }]}>{dosage} • {time}</Text>
      </View>
      <Ionicons name={taken ? "checkmark-circle" : "ellipse-outline"} size={20} color={taken ? colors.health.success : colors.text.muted} />
    </TouchableOpacity>
  );
}

// ─── Challenge Card ───────────────────────────────────────────
function ChallengeCard({ title, progress, daysLeft, icon }: { title: string; progress: number; daysLeft: number; icon: string }) {
  return (
    <View style={styles.challengeCard}>
      <View style={[styles.challengeIcon, { backgroundColor: colors.health.energy + '18' }]}>
        <Ionicons name={icon as any} size={20} color={colors.health.energy} />
      </View>
      <Text style={[typography.body.md, { color: colors.text.primary, marginTop: 8 }]}>{title}</Text>
      <View style={[styles.miniProgress, { backgroundColor: colors.health.energy + '20', marginTop: 6 }]}>
        <View style={[styles.miniProgressFill, { width: `${progress}%`, backgroundColor: colors.health.energy }]} />
      </View>
      <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 4 }]}>{daysLeft} days left • {progress}%</Text>
    </View>
  );
}

// ─── Activity Feed Item ───────────────────────────────────────
function ActivityItem({ type, title, detail, time, icon, color }: {
  type: string; title: string; detail: string; time: string; icon: string; color: string;
}) {
  return (
    <View style={styles.activityItem}>
      <View style={[styles.activityIcon, { backgroundColor: color + '18' }]}>
        <Ionicons name={icon as any} size={16} color={color} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[typography.body.md, { color: colors.text.primary }]}>{title}</Text>
        <Text style={[typography.body.sm, { color: colors.text.muted }]}>{detail}</Text>
      </View>
      <Text style={[typography.body.xs, { color: colors.text.muted }]}>{time}</Text>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
// ─── MAIN DASHBOARD ──────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════
export default function DashboardScreen() {
  const router = useRouter();
  const { userId } = useUserStore();
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  
  // Live data state — steps/calories/activeMinutes are null until a real
  // reading comes back from the device; the UI shows '--' rather than guess.
  const [healthScore, setHealthScore] = useState<number | null>(null);
  const [todayData, setTodayData] = useState<{
    steps: number | null; stepsGoal: number;
    sleep: number; sleepGoal: number;
    calories: number | null; caloriesGoal: number;
    water: number; waterGoal: number;
    activeMinutes: number | null; activeMinutesGoal: number;
  }>({
    steps: null, stepsGoal: 10000,
    sleep: 0, sleepGoal: 8,
    calories: null, caloriesGoal: 2200,
    water: 0, waterGoal: 8,
    activeMinutes: null, activeMinutesGoal: 30,
  });
  const [medications, setMedications] = useState<any[]>([]);
  const [challenges, setChallenges] = useState<any[]>([]);
  const [activityFeed, setActivityFeed] = useState<any[]>([]);
  const [recoveryScore, setRecoveryScore] = useState(0);
  const [hrv, setHrv] = useState(0);
  const [acwr, setAcwr] = useState(0);
  const [streak, setStreak] = useState(0);
  const dailyTip = getDailyTip();

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    loadData();
  }, []);

  const loadData = useCallback(async () => {
    try {
      // Fetch multiple data sources in parallel
      const [recoveryRes, hydrationRes, sleepRes, medRes, challengeRes, activityRes, streakRes, acwrRes, healthRes] = await Promise.allSettled([
        api.getRecoveryLogs(userId, 1),
        api.getHydrationToday(userId),
        api.getSleepAnalysis(userId, 1),
        api.post('/api/v1/medication/today', { user_id: userId }),
        getJson<any>(`/challenges?user_id=${userId}`),
        api.post('/api/v1/activity-feed', { user_id: userId, limit: 5 }),
        getJson<any>(`/streaks?user_id=${userId}`),
        api.getAcwr(userId),
        fetchHealthData(),
      ]);

      // Recovery data — leave healthScore unset (renders as '--') when no
      // real score is available, rather than showing a plausible-looking one.
      if (recoveryRes.status === 'fulfilled' && recoveryRes.value?.items?.length > 0) {
        const latest = recoveryRes.value.items[0];
        const score = latest.recovery_score ?? latest.score;
        if (score != null) {
          setHealthScore(Math.round(score));
          setRecoveryScore(Math.round(score));
        }
        setHrv(Math.round(latest.hrv_rmssd ?? latest.wearable_data?.hrv_rmssd ?? 0));
      }

      // Hydration
      if (hydrationRes.status === 'fulfilled') {
        const hyd = hydrationRes.value;
        setTodayData(prev => ({
          ...prev,
          water: Math.round((hyd.total_ml ?? 0) / 250),
          waterGoal: Math.round((hyd.daily_goal_ml ?? 2000) / 250),
        }));
      }

      // Sleep
      if (sleepRes.status === 'fulfilled' && sleepRes.value) {
        setTodayData(prev => ({
          ...prev,
          sleep: Math.round((sleepRes.value.avg_duration_hours ?? 7.2) * 10) / 10,
        }));
      }

      // Medications
      if (medRes.status === 'fulfilled' && medRes.value?.medications) {
        setMedications(medRes.value.medications.slice(0, 3));
      }

      // Challenges
      if (challengeRes.status === 'fulfilled' && challengeRes.value?.challenges) {
        setChallenges(challengeRes.value.challenges.slice(0, 3));
      }

      // Activity feed
      if (activityRes.status === 'fulfilled' && activityRes.value?.items) {
        setActivityFeed(activityRes.value.items.slice(0, 4));
      }

      // Streaks
      if (streakRes.status === 'fulfilled') {
        setStreak(streakRes.value?.current_streak ?? streakRes.value?.streak ?? 5);
      }

      // ACWR
      if (acwrRes.status === 'fulfilled') {
        setAcwr(acwrRes.value?.acwr ?? 0);
      }

      // Steps and active calories come from the device's health API. When
      // the platform module, permission, or fetch isn't available they stay
      // null and render as '--' instead of a fabricated number.
      if (healthRes.status === 'fulfilled') {
        const h = healthRes.value;
        if (h.source === 'simulated' && __DEV__) {
          console.warn('[dashboard] showing simulated health data (EXPO_PUBLIC_USE_SIMULATED_HEALTH_DATA=true)');
        }
        if (h.source !== 'unavailable') {
          setTodayData(prev => ({
            ...prev,
            steps: h.steps ?? null,
            calories: h.activeCalories ?? null,
          }));
        }
      }

    } catch (err) {
      // No sensible default exists here; state simply keeps its last value.
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, [loadData]);

  const scoreColor = healthScore == null ? colors.text.muted : healthScore >= 80 ? colors.health.success : healthScore >= 60 ? colors.health.activity : colors.health.warning;
  const scoreLabel = healthScore == null ? 'No data yet' : healthScore >= 80 ? 'Excellent' : healthScore >= 60 ? 'Good' : healthScore >= 40 ? 'Fair' : 'Needs attention';
  const todaySummary = { ...todayData };
  const pct = (value: number | null, goal: number) => (value == null ? 0 : (value / goal) * 100);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[typography.body.md, { color: colors.text.muted, marginTop: 12 }]}>Loading dashboard...</Text>
        </View>
      ) : (
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      >
        {/* ─── Gradient Hero Header ─────────────── */}
        <LinearGradient colors={['#6366F1', '#8B5CF6', '#0F1629']} style={styles.heroHeader}>            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginBottom: 4 }]}>Good {new Date().getHours() < 12 ? 'Morning' : new Date().getHours() < 17 ? 'Afternoon' : 'Evening'} {new Date().getHours() < 12 ? '☀️' : new Date().getHours() < 17 ? '🌤️' : '🌙'}</Text>
            <Text style={[typography.heading.h1, { color: '#fff', marginBottom: 20 }]}>Dashboard</Text>

          {/* Health Score Ring */}
          <View style={styles.scoreContainer}>
            <ScoreRing score={healthScore ?? 0} size={140} color={scoreColor} />
            <View style={styles.scoreInfo}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Health Score</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{healthScore ?? '--'}</Text>
              <Text style={[typography.body.sm, { color: scoreColor }]}>{scoreLabel}</Text>
            </View>
          </View>

          {/* Today's Activity Rings */}
          <View style={styles.activityRingsContainer}>
            <View style={styles.activityRingItem}>
              <MiniActivityRing progress={pct(todaySummary.steps, todaySummary.stepsGoal)} color={colors.health.activity} size={52} strokeWidth={5} />
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)', marginTop: 4 }]}>Steps</Text>
            </View>
            <View style={styles.activityRingItem}>
              <MiniActivityRing progress={pct(todaySummary.activeMinutes, todaySummary.activeMinutesGoal)} color={colors.health.heart} size={52} strokeWidth={5} />
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)', marginTop: 4 }]}>Active</Text>
            </View>
            <View style={styles.activityRingItem}>
              <MiniActivityRing progress={pct(todaySummary.calories, todaySummary.caloriesGoal)} color={colors.health.energy} size={52} strokeWidth={5} />
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)', marginTop: 4 }]}>Calories</Text>
            </View>
            <View style={styles.activityRingItem}>
              <MiniActivityRing progress={pct(todaySummary.water, todaySummary.waterGoal)} color={colors.health.activity} size={52} strokeWidth={5} />
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)', marginTop: 4 }]}>Water</Text>
            </View>
          </View>
        </LinearGradient>

        {/* ─── Today's Summary ──────────────────── */}
        <Animated.View style={[styles.section, { opacity: fadeAnim }]}>
          <SectionHeaderPremium title="Today's Summary" icon="today" iconColor={colors.health.activity} />
          <View style={styles.metricsGrid}>
            <TodayMetric icon="footsteps" label="Steps" value={todaySummary.steps != null ? todaySummary.steps.toLocaleString() : '--'} unit="steps" goal={todaySummary.stepsGoal} color={colors.health.activity} progress={pct(todaySummary.steps, todaySummary.stepsGoal)} />
            <TodayMetric icon="bed" label="Sleep" value={todaySummary.sleep} unit="hrs" goal={todaySummary.sleepGoal} color={colors.health.sleep} progress={(todaySummary.sleep / todaySummary.sleepGoal) * 100} />
            <TodayMetric icon="flame" label="Calories" value={todaySummary.calories ?? '--'} unit="cal" goal={todaySummary.caloriesGoal} color={colors.health.energy} progress={pct(todaySummary.calories, todaySummary.caloriesGoal)} />
            <TodayMetric icon="water" label="Water" value={todaySummary.water} unit="glasses" goal={todaySummary.waterGoal} color={colors.health.activity} progress={(todaySummary.water / todaySummary.waterGoal) * 100} />
          </View>
        </Animated.View>

        {/* ─── Quick Actions ────────────────────── */}
        <View style={styles.section}>
          <SectionHeaderPremium title="Quick Actions" icon="flash" iconColor={colors.health.energy} />
          <View style={styles.quickActionsGrid}>
            {[
              { id: 'water', icon: 'water', label: 'Log Water', color: colors.health.activity, screen: 'nutrition-log' },
              { id: 'mood', icon: 'happy', label: 'Log Mood', color: colors.health.mental, screen: 'mental-health' },
              { id: 'weight', icon: 'scale', label: 'Log Weight', color: colors.health.nutrition, screen: 'health' },
              { id: 'meditate', icon: 'leaf', label: 'Meditate', color: colors.health.calm, screen: 'wellness' },
              { id: 'sleep', icon: 'moon', label: 'Sleep Log', color: colors.health.sleep, screen: 'sleep-tracker' },
              { id: 'meds', icon: 'medical', label: 'Medication', color: colors.health.heart, screen: 'medication' },
              { id: 'recovery', icon: 'pulse', label: 'Recovery', color: colors.health.sleep, screen: 'recovery-dashboard' },
            ].map((action) => (
              <QuickActionButton key={action.id} icon={action.icon} label={action.label} color={action.color} onPress={() => router.push(action.screen as any)} />
            ))}
          </View>
        </View>

        {/* ─── Medications ──────────────────────── */}
        <View style={styles.section}>
          <SectionHeaderPremium title="Medications" icon="medical" iconColor={colors.health.heart} action={{ label: 'View All', onPress: () => router.push('/medication' as any) }} />
          {medications.length > 0 ? medications.map((med: any) => (
            <MedicationCard key={med.id ?? med.name} name={med.name} dosage={med.dosage} time={med.time} taken={med.taken} />
          )) : (
            <View style={styles.emptyState}>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>No medications tracked yet</Text>
            </View>
          )}
        </View>

        {/* ─── Active Challenges ─────────────────── */}
        <View style={styles.section}>
          <SectionHeaderPremium title="Active Challenges" icon="trophy" iconColor={colors.health.energy} action={{ label: 'Join More', onPress: () => router.push('/social' as any) }} />
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12 }}>
            {challenges.length > 0 ? challenges.map((ch: any) => (
              <ChallengeCard key={ch.id ?? ch.title} title={ch.title} progress={ch.progress} daysLeft={ch.daysLeft} icon={ch.icon ?? 'trophy'} />
            )) : (
              <View style={[styles.emptyState, { width: SCREEN_WIDTH - 40 }]}>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>No active challenges</Text>
              </View>
            )}
          </ScrollView>
        </View>

        {/* ─── Daily Tip ────────────────────────── */}
        <View style={styles.section}>
          <LinearGradient colors={[dailyTip.color + '20', dailyTip.color + '08']} style={styles.tipCard}>
            <View style={[styles.tipIcon, { backgroundColor: dailyTip.color + '30' }]}>
              <Ionicons name={dailyTip.icon as any} size={20} color={dailyTip.color} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[typography.label.md, { color: dailyTip.color }]}>{dailyTip.title}</Text>
              <Text style={[typography.body.sm, { color: colors.text.secondary, marginTop: 4 }]}>{dailyTip.text}</Text>
            </View>
          </LinearGradient>
        </View>

        {/* ─── Activity Feed ────────────────────── */}
        <View style={styles.section}>
          <SectionHeaderPremium title="Recent Activity" icon="time" iconColor={colors.health.calm} />
          {activityFeed.length > 0 ? activityFeed.map((item: any) => (
            <ActivityItem key={item.id ?? item.title} type={item.type ?? 'general'} title={item.title ?? item.name ?? 'Activity'} detail={item.detail ?? item.description ?? ''} time={item.time ?? item.created_at ?? ''} icon={item.icon ?? 'pulse'} color={item.color ?? colors.health.calm} />
          )) : (
            <View style={styles.emptyState}>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>No recent activity</Text>
            </View>
          )}
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>
      )}
    </View>
  );
}

// ═══════════════════════════════════════════════════════════════
// ─── STYLES ──────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.bg.deep },
  emptyState: { paddingVertical: 24, alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 16, borderWidth: 1, borderColor: colors.surface.border },

  // Hero Header
  heroHeader: {
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: spacing.screenPadding,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
    marginBottom: 20,
  },
  scoreInfo: { flex: 1 },
  activityRingsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(0,0,0,0.2)',
    borderRadius: 16,
    padding: 16,
  },
  activityRingItem: { alignItems: 'center' },

  // Sections
  section: {
    paddingHorizontal: spacing.screenPadding,
    marginTop: spacing.xl,
  },

  // Metrics Grid
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricCard: {
    width: (SCREEN_WIDTH - spacing.screenPadding * 2 - 10) / 2,
    backgroundColor: colors.bg.card,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  metricIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  miniProgress: {
    height: 4,
    borderRadius: 2,
    marginTop: 8,
    overflow: 'hidden',
  },
  miniProgressFill: {
    height: '100%',
    borderRadius: 2,
  },

  // Quick Actions
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  quickAction: {
    width: (SCREEN_WIDTH - spacing.screenPadding * 2 - 20) / 3,
    alignItems: 'center',
    backgroundColor: colors.bg.card,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  quickActionIcon: {
    width: 44,
    height: 44,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Medications
  medCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bg.card,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.surface.border,
    gap: 12,
  },
  medCardTaken: { opacity: 0.6 },
  medCheck: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Challenges
  challengeCard: {
    width: 160,
    backgroundColor: colors.bg.card,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: colors.surface.border,
  },
  challengeIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Activity Rings
  ringBg: { position: 'absolute' },
  ringFill: { position: 'absolute' },
  ringCenter: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    top: '50%',
    marginTop: -16,
    left: '50%',
    marginLeft: -16,
  },

  // Daily Tip
  tipCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 16,
    padding: 16,
    gap: 12,
  },
  tipIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Activity Feed
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: colors.surface.divider,
    gap: 12,
  },
  activityIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
