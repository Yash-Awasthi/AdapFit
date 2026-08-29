/**
 * Home Screen — Premium Health Dashboard
 * Modern glassmorphism design with animated elements, health metrics, quick actions
 */
import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  RefreshControl, Dimensions, Animated, Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, spacing, radius } from '../../src/theme';
import { useGrid } from '../../src/theme/layout';
import {
  ScoreRing, GradientCard, GlassCard, HealthMetricMini,
  SectionHeaderPremium, ProgressBarPremium, StatCard, QuickAction, PillChip,
} from '../../src/components/PremiumComponents';
import { InteractiveLineChart, MetricCardWithChart, Sparkline } from '../../src/components/InteractiveCharts';
import { HapticButton, SwipeableCard } from '../../src/components/GestureSystem';
import { useToast, QuickAlert } from '../../src/components/ToastSystem';
import { FloatingActionButton, SectionDivider } from '../../src/components/NavigationHelpers';
import { TodayDecision } from '../../src/components/TodayDecision';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
import { API_V1 as API } from '../../src/services/config';
const api = async (path: string, opts?: RequestInit) => {
  try {
    const r = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...opts });
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
};

// ===== Greeting based on time of day =====
const getGreeting = () => {
  const h = new Date().getHours();
  if (h < 12) return { text: 'Good morning', icon: 'sunny', gradient: ['#E8814A', '#C2542A'] };
  if (h < 17) return { text: 'Good afternoon', icon: 'partly-sunny', gradient: ['#3E7BC4', '#2E8BA0'] };
  if (h < 21) return { text: 'Good evening', icon: 'moon', gradient: ['#6D5BC7', '#4F51B8'] };
  return { text: 'Good night', icon: 'moon', gradient: ['#2A2A5E', '#312E81'] };
};

export default function HomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const grid = useGrid(3);
  const [refreshing, setRefreshing] = useState(false);
  const [healthScore, setHealthScore] = useState(72);
  const [bpm, setBpm] = useState<number | null>(null);
  const [stressLevel, setStressLevel] = useState(35);
  const [steps, setSteps] = useState(0);
  const [sleepScore, setSleepScore] = useState(0);
  const [waterIntake, setWaterIntake] = useState(0);
  const greeting = getGreeting();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 600, useNativeDriver: true }),
    ]).start();
    loadData();
  }, []);

  const loadData = async () => {
    const [stressRes, wellbeingRes, sleepRes] = await Promise.all([
      api('/stress/assess', { method: 'POST', body: JSON.stringify({ mood_score: 7, energy_level: 6, sleep_quality: 75 }) }),
      api('/wellbeing/report'),
      api('/sleep/log', { method: 'POST', body: JSON.stringify({ bedtime: '23:00', wake_time: '07:00', quality_score: 78 }) }),
    ]);
    if (stressRes?.overall_score) setStressLevel(stressRes.overall_score);
    // A placeholder value here is indistinguishable from a real reading, so
    // only a count the backend actually reported may be displayed.
    if (typeof wellbeingRes?.step_count === 'number') setSteps(wellbeingRes.step_count);
    if (typeof sleepRes?.quality_score === 'number') setSleepScore(sleepRes.quality_score);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const quickActions = [
    { icon: 'heart', label: 'Heart Rate', color: colors.health.heart, route: '/health-hub' },
    { icon: 'moon', label: 'Sleep', color: colors.health.sleep, route: '/sleep-tracker' },
    { icon: 'fitness', label: 'Workout', color: colors.health.activity, route: '/workout' },
    { icon: 'restaurant', label: 'Nutrition', color: colors.health.nutrition, route: '/nutrition-log' },
    { icon: 'brain', label: 'Mental', color: colors.health.mental, route: '/mental-health' },
    { icon: 'meditate', label: 'Meditate', color: colors.health.calm, route: '/meditation' },
  ];

  const healthMetrics = [
    { icon: 'heart', value: bpm ?? '--', label: 'BPM', color: colors.health.heart },
    { icon: 'walk', value: steps ? steps.toLocaleString() : '--', label: 'Steps', color: colors.health.activity },
    { icon: 'moon', value: sleepScore || '--', label: 'Sleep', color: colors.health.sleep },
    { icon: 'flame', value: steps ? Math.floor(steps * 0.04) : '--', label: 'Calories', color: colors.health.energy },
    { icon: 'water', value: `${waterIntake}/8`, label: 'Water', color: '#3B82F6' },
    { icon: 'leaf', value: stressLevel, label: 'Stress', color: colors.health.calm },
  ];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Hero Header with Gradient */}
      <LinearGradient colors={greeting.gradient as any} style={[styles.heroHeader, { paddingTop: insets.top + spacing.md }]}>
        <View style={styles.heroContent}>
          <View style={styles.heroTop}>
            <View style={styles.heroTitleBlock}>
              <View style={styles.heroGreetingRow}>
                <Ionicons name={greeting.icon as any} size={20} color="rgba(255,255,255,0.9)" />
                <Text style={styles.heroGreeting} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.8}>
                  {greeting.text}
                </Text>
              </View>
              <Text style={styles.heroDate} numberOfLines={1}>
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </Text>
            </View>
            <TouchableOpacity style={styles.heroAvatar} onPress={() => router.push('/menu' as any)}>
              <Ionicons name="person" size={20} color="#FFF" />
            </TouchableOpacity>
          </View>

          {/* Health Score Ring */}
          <View style={styles.heroScoreRow}>
            <ScoreRing
              score={healthScore}
              size={110}
              strokeWidth={8}
              color="#FFF"
              label="HEALTH"
              sublabel={getScoreLabel(healthScore)}
            />
            <View style={styles.heroScoreDetails}>
              <Text style={styles.heroScoreTitle}>Your Health Score</Text>
              <Text style={styles.heroScoreSubtitle}>
                {healthScore >= 80 ? "You're doing amazing!" : healthScore >= 60 ? 'Keep up the good work!' : 'Let\'s improve together'}
              </Text>
              <View style={styles.heroScoreBreakdown}>
                <View style={styles.heroBreakdownItem}>
                  <View style={[styles.heroBreakdownDot, { backgroundColor: colors.health.heart }]} />
                  <Text style={styles.heroBreakdownText}>Heart: 85</Text>
                </View>
                <View style={styles.heroBreakdownItem}>
                  <View style={[styles.heroBreakdownDot, { backgroundColor: colors.health.sleep }]} />
                  <Text style={styles.heroBreakdownText}>Sleep: 78</Text>
                </View>
                <View style={styles.heroBreakdownItem}>
                  <View style={[styles.heroBreakdownDot, { backgroundColor: colors.health.activity }]} />
                  <Text style={styles.heroBreakdownText}>Activity: 72</Text>
                </View>
              </View>
            </View>
          </View>
        </View>
      </LinearGradient>

      <TodayDecision />

      {/* Quick Actions Row */}
      <View style={styles.section}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.quickActionsScroll}>
          {quickActions.map((action, i) => (
            <QuickAction
              key={i}
              icon={action.icon}
              label={action.label}
              color={action.color}
              onPress={() => router.push(action.route as any)}
            />
          ))}
        </ScrollView>
      </View>

      {/* Health Metrics Grid */}
      <SectionHeaderPremium
        icon="pulse"
        iconColor={colors.health.heart}
        title="Today's Metrics"
        action={{ label: 'See All', onPress: () => router.push('/health-hub' as any) }}
      />
      <View style={[styles.metricsGrid, { gap: grid.gap, paddingHorizontal: grid.padding }]}>
        {healthMetrics.map((metric) => (
          <HealthMetricMini
            key={metric.label}
            icon={metric.icon}
            value={metric.value}
            label={metric.label}
            color={metric.color}
            width={grid.cell}
            onPress={() => router.push('/health-hub' as any)}
          />
        ))}
      </View>

      {/* Activity Rings */}
      <View style={styles.section}>
        <SectionHeaderPremium
          icon="fitness"
          iconColor={colors.health.activity}
          title="Activity Rings"
        />
        <GlassCard variant="light" style={styles.activityRingsCard}>
          <View style={styles.activityRingsRow}>
            <ScoreRing score={Math.min(100, (steps / 10000) * 100)} size={100} strokeWidth={8} color={colors.health.heart} label="MOVE" />
            <ScoreRing score={Math.min(100, (steps / 10000) * 80)} size={100} strokeWidth={8} color={colors.health.calm} label="EXERCISE" />
            <ScoreRing score={Math.min(100, sleepScore)} size={100} strokeWidth={8} color={colors.health.sleep} label="STAND" />
          </View>
          <View style={styles.activityRingsLabels}>
            <Text style={styles.activityRingsLabel}>Move: {Math.floor(steps * 0.04)} kcal</Text>
            <Text style={styles.activityRingsLabel}>Exercise: 23 min</Text>
            <Text style={styles.activityRingsLabel}>Stand: 9/12 hrs</Text>
          </View>
        </GlassCard>
      </View>

      {/* Stress & Mental Wellness */}
      <View style={styles.section}>
        <SectionHeaderPremium
          icon="leaf"
          iconColor={colors.health.calm}
          title="Wellness"
          action={{ label: 'Details', onPress: () => router.push('/health-hub' as any) }}
        />
        <View style={styles.wellnessRow}>
          <GlassCard variant="health" healthType="calm" style={styles.wellnessCard} onPress={() => router.push('/health-hub' as any)}>
            <Ionicons name="leaf" size={24} color={colors.health.calm} />
            <Text style={styles.wellnessCardValue}>{stressLevel}</Text>
            <Text style={styles.wellnessCardLabel}>Stress Level</Text>
            <View style={styles.miniProgressBar}>
              <View style={[styles.miniProgressFill, { width: `${stressLevel}%`, backgroundColor: colors.health.calm }]} />
            </View>
          </GlassCard>
          <GlassCard variant="health" healthType="sleep" style={styles.wellnessCard} onPress={() => router.push('/sleep-tracker' as any)}>
            <Ionicons name="moon" size={24} color={colors.health.sleep} />
            <Text style={styles.wellnessCardValue}>{sleepScore}</Text>
            <Text style={styles.wellnessCardLabel}>Sleep Score</Text>
            <View style={styles.miniProgressBar}>
              <View style={[styles.miniProgressFill, { width: `${sleepScore}%`, backgroundColor: colors.health.sleep }]} />
            </View>
          </GlassCard>
        </View>
      </View>

      {/* Water Intake */}
      <View style={styles.section}>
        <SectionHeaderPremium
          icon="water"
          iconColor="#3B82F6"
          title="Hydration"
        />
        <GlassCard variant="light" style={styles.hydrationCard}>
          <View style={styles.hydrationRow}>
            <View style={styles.hydrationGlasses}>
              {Array.from({ length: 8 }).map((_, i) => (
                <TouchableOpacity
                  key={i}
                  style={[styles.waterGlass, i < waterIntake && styles.waterGlassFilled]}
                  onPress={() => setWaterIntake(i < waterIntake ? i : i + 1)}
                >
                  <Ionicons
                    name={i < waterIntake ? 'water' : 'water-outline'}
                    size={18}
                    color={i < waterIntake ? '#3B82F6' : colors.text.muted}
                  />
                </TouchableOpacity>
              ))}
            </View>
            <View style={styles.hydrationInfo}>
              <Text style={styles.hydrationCount}>{waterIntake}/8</Text>
              <Text style={styles.hydrationLabel}>glasses today</Text>
              <Text style={styles.hydrationPercent}>{Math.round((waterIntake / 8) * 100)}% of goal</Text>
            </View>
          </View>
        </GlassCard>
      </View>

      {/* Weekly Streak */}
      <View style={styles.section}>
        <SectionHeaderPremium
          icon="flame"
          iconColor={colors.health.energy}
          title="Weekly Streak"
        />
        <GradientCard colors={[colors.health.energy, '#F59E0B']} style={styles.streakCard}>
          <View style={styles.streakContent}>
            <View>
              <Text style={styles.streakNumber}>5</Text>
              <Text style={styles.streakLabel}>day streak</Text>
            </View>
            <View style={styles.streakDots}>
              {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => (
                <View key={i} style={styles.streakDotContainer}>
                  <View style={[styles.streakDot, i < 5 && styles.streakDotActive]} />
                  <Text style={styles.streakDotLabel}>{day}</Text>
                </View>
              ))}
            </View>
          </View>
          <View style={styles.streakMessageRow}>
            <Ionicons name="flame" size={16} color="#FFF" />
            <Text style={styles.streakMessage}>Five sessions in a row. Keep it going.</Text>
          </View>
        </GradientCard>
      </View>

      {/* Health Trends Mini Chart */}
      <View style={styles.section}>
        <SectionHeaderPremium
          icon="trending-up"
          iconColor={colors.primary}
          title="Weekly Trends"
          action={{ label: 'See All', onPress: () => router.push('/trends' as any) }}
        />
        <MetricCardWithChart
          title="Heart Rate"
          value="72 bpm"
          change="-3%"
          changeType="down"
          data={[75, 73, 74, 72, 71, 72, 72]}
          color={colors.health.heart}
          icon="heart"
        />
        <MetricCardWithChart
          title="Steps"
          value="8,200"
          change="+12%"
          changeType="up"
          data={[6500, 7000, 7200, 7800, 8000, 8100, 8200]}
          color={colors.health.activity}
          icon="footsteps"
        />
        <MetricCardWithChart
          title="Sleep Score"
          value="78"
          change="+5%"
          changeType="up"
          data={[70, 72, 74, 75, 76, 77, 78]}
          color={colors.health.sleep}
          icon="moon"
        />
      </View>

      {/* Tips */}
      <View style={styles.section}>
        <SectionHeaderPremium
          icon="bulb"
          iconColor="#F59E0B"
          title="Daily Tip"
        />
        <GlassCard variant="primary" style={styles.tipCard}>
          <View style={styles.tipRow}>
            <View style={styles.tipIcon}>
              <Ionicons name="bulb" size={20} color={colors.primary} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.tipTitle}>Stay Hydrated</Text>
              <Text style={styles.tipText}>Drinking water first thing in the morning kickstarts your metabolism and helps your body flush out toxins.</Text>
            </View>
          </View>
        </GlassCard>
      </View>

      {/* Quick Log FAB */}
      <FloatingActionButton
        icon="add"
        onPress={() => router.push('/checkin' as any)}
        color={colors.primary}
        label="Log"
      />

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

function getScoreLabel(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Fair';
  return 'Needs Work';
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Hero Header
  heroHeader: { paddingBottom: spacing.xl, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  heroContent: { paddingHorizontal: spacing.screenPadding },
  heroTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.xl, gap: spacing.md },
  heroTitleBlock: { flex: 1 },
  heroGreetingRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  heroGreeting: { flexShrink: 1, fontSize: 24, fontWeight: '800', color: '#FFF', letterSpacing: -0.4 },
  heroDate: { fontSize: 14, color: 'rgba(255,255,255,0.85)', marginTop: 4 },
  heroAvatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center' },
  heroScoreRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xl },
  heroScoreDetails: { flex: 1 },
  heroScoreTitle: { fontSize: 16, fontWeight: '700', color: '#FFF' },
  heroScoreSubtitle: { fontSize: 13, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  heroScoreBreakdown: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.md },
  heroBreakdownItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  heroBreakdownDot: { width: 6, height: 6, borderRadius: 3 },
  heroBreakdownText: { fontSize: 11, color: 'rgba(255,255,255,0.8)' },

  // Quick Actions
  section: { marginTop: spacing.xl },
  quickActionsScroll: { paddingHorizontal: spacing.screenPadding, gap: spacing.lg },
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap' },

  // Activity Rings
  activityRingsCard: { marginHorizontal: spacing.screenPadding },
  activityRingsRow: { flexDirection: 'row', justifyContent: 'space-around' },
  activityRingsLabels: { flexDirection: 'row', justifyContent: 'space-around', marginTop: spacing.md },
  activityRingsLabel: { fontSize: 11, color: colors.text.muted },

  // Wellness
  wellnessRow: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.screenPadding },
  wellnessCard: { flex: 1, alignItems: 'center' },
  wellnessCardValue: { fontSize: 28, fontWeight: '800', color: colors.text.primary, marginTop: spacing.sm },
  wellnessCardLabel: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  miniProgressBar: { height: 4, backgroundColor: colors.surface.divider, borderRadius: 2, width: '100%', marginTop: spacing.sm, overflow: 'hidden' },
  miniProgressFill: { height: '100%', borderRadius: 2 },

  // Hydration
  hydrationCard: { marginHorizontal: spacing.screenPadding },
  hydrationRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xl },
  hydrationGlasses: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, flex: 1 },
  waterGlass: { width: 36, height: 36, borderRadius: 10, backgroundColor: colors.bg.input, justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border },
  waterGlassFilled: { backgroundColor: '#3B82F615', borderColor: '#3B82F640' },
  hydrationInfo: { alignItems: 'center' },
  hydrationCount: { fontSize: 28, fontWeight: '800', color: '#3B82F6' },
  hydrationLabel: { fontSize: 12, color: colors.text.muted },
  hydrationPercent: { fontSize: 11, color: '#3B82F6', fontWeight: '600', marginTop: 4 },

  // Streak
  streakCard: { marginHorizontal: spacing.screenPadding },
  streakContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  streakNumber: { fontSize: 48, fontWeight: '800', color: '#FFF' },
  streakLabel: { fontSize: 16, color: 'rgba(255,255,255,0.8)', fontWeight: '600' },
  streakDots: { flexDirection: 'row', gap: 8 },
  streakDotContainer: { alignItems: 'center', gap: 4 },
  streakDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: 'rgba(255,255,255,0.3)' },
  streakDotActive: { backgroundColor: '#FFF' },
  streakDotLabel: { fontSize: 10, color: 'rgba(255,255,255,0.7)', fontWeight: '600' },
  streakMessageRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md },
  streakMessage: { flex: 1, fontSize: 14, color: 'rgba(255,255,255,0.95)', fontWeight: '600' },

  // Tips
  tipCard: { marginHorizontal: spacing.screenPadding },
  tipRow: { flexDirection: 'row', gap: spacing.md },
  tipIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },
  tipTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary, marginBottom: 4 },
  tipText: { fontSize: 13, color: colors.text.secondary, lineHeight: 18 },
});
