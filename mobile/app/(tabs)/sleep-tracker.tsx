/**
 * Sleep Tracker — Premium Sleep Visualization
 * Glassmorphism cards, animated score ring, sleep stages, insights
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl, ActivityIndicator, Animated, Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, glass, getScoreColor } from '../../src/theme';
import {
  ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium,
} from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

const api = async (p: string, o?: RequestInit) => {
  try {
    const r = await fetch(`${API}${p}`, { headers: { 'Content-Type': 'application/json' }, ...o });
    return r.ok ? await r.json() : null;
  } catch { return null; }
};

const SLEEP_STAGES = [
  { label: 'Awake', color: '#EF4444', icon: 'alert-circle' },
  { label: 'REM', color: '#8B5CF6', icon: 'flash' },
  { label: 'Light', color: '#06B6D4', icon: 'cloud' },
  { label: 'Deep', color: '#6366F1', icon: 'moon' },
];

export default function SleepTrackerScreen() {
  const [score, setScore] = useState(0);
  const [quality, setQuality] = useState('no_data');
  const [hours, setHours] = useState(0);
  const [deep, setDeep] = useState(0);
  const [rem, setRem] = useState(0);
  const [light, setLight] = useState(0);
  const [awake, setAwake] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [rating, setRating] = useState(5);
  const [logging, setLogging] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  const load = useCallback(async () => {
    const [s, d, t, i] = await Promise.allSettled([
      api('/sleep/score'), api('/sleep/debt'), api('/sleep/trend?days=7'), api('/sleep/insights'),
    ]);
    if (s.status === 'fulfilled' && s.value) {
      setScore(s.value.score || 78);
      setQuality(s.value.quality || 'good');
      setHours(s.value.total_sleep_hours || 7.5);
      setDeep(s.value.deep_sleep_minutes || 90);
      setRem(s.value.rem_sleep_minutes || 105);
    }
    if (d.status === 'fulfilled' && d.value) {
      setAwake(d.value.debt_hours ? d.value.debt_hours * 10 : 15);
    }
    setLight(Math.round((hours || 7.5) * 60 - (deep || 90) - (rem || 105) - (awake || 15)));
  }, []);

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    load();
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const logSleep = async () => {
    setLogging(true);
    const r = await api('/sleep/log', {
      method: 'POST',
      body: JSON.stringify({ bedtime: '23:00', wake_time: '07:00', quality_rating: rating }),
    });
    setLogging(false);
    if (r) {
      setScore(r.sleep_score || 78);
      setQuality(r.quality || 'good');
      setHours(r.total_sleep_hours || 7.5);
    }
  };

  const sleepColor = getScoreColor(score);
  const totalMinutes = deep + rem + light + awake;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.health.sleep} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <LinearGradient colors={['#6366F1', '#8B5CF6']} style={styles.header}>
        <Text style={styles.headerTitle}>🌙 Sleep Tracker</Text>
        <Text style={styles.headerSubtitle}>Optimize your sleep for better recovery</Text>
      </LinearGradient>

      {/* Score Ring */}
      <View style={styles.scoreSection}>
        <ScoreRing score={score} size={160} strokeWidth={10} color={sleepColor} label="SLEEP SCORE" />
        <View style={styles.scoreMeta}>
          <View style={styles.scoreMetaItem}>
            <View style={[styles.scoreMetaIcon, { backgroundColor: colors.health.sleep + '15' }]}>
              <Ionicons name="moon" size={16} color={colors.health.sleep} />
            </View>
            <Text style={styles.scoreMetaValue}>{hours}h</Text>
            <Text style={styles.scoreMetaLabel}>Duration</Text>
          </View>
          <View style={styles.scoreMetaItem}>
            <View style={[styles.scoreMetaIcon, { backgroundColor: '#6366F1' + '15' }]}>
              <Ionicons name="water" size={16} color="#6366F1" />
            </View>
            <Text style={styles.scoreMetaValue}>{deep}m</Text>
            <Text style={styles.scoreMetaLabel}>Deep</Text>
          </View>
          <View style={styles.scoreMetaItem}>
            <View style={[styles.scoreMetaIcon, { backgroundColor: '#8B5CF6' + '15' }]}>
              <Ionicons name="flash" size={16} color="#8B5CF6" />
            </View>
            <Text style={styles.scoreMetaValue}>{rem}m</Text>
            <Text style={styles.scoreMetaLabel}>REM</Text>
          </View>
        </View>
      </View>

      {/* Sleep Stages */}
      <SectionHeaderPremium icon="layers" iconColor={colors.health.sleep} title="Sleep Stages" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {SLEEP_STAGES.map((stage, i) => {
          const minutes = i === 0 ? awake : i === 1 ? rem : i === 2 ? light : deep;
          return (
            <View key={i} style={styles.stageRow}>
              <View style={[styles.stageIcon, { backgroundColor: stage.color + '15' }]}>
                <Ionicons name={stage.icon as any} size={14} color={stage.color} />
              </View>
              <Text style={styles.stageLabel}>{stage.label}</Text>
              <View style={styles.stageBarContainer}>
                <View style={[styles.stageBar, { backgroundColor: stage.color + '20' }]}>
                  <View style={[styles.stageFill, { width: `${(minutes / Math.max(totalMinutes, 1)) * 100}%`, backgroundColor: stage.color }]} />
                </View>
              </View>
              <Text style={styles.stageMinutes}>{minutes}m</Text>
            </View>
          );
        })}
      </GlassCard>

      {/* Sleep Timeline */}
      <SectionHeaderPremium icon="time" iconColor="#06B6D4" title="Sleep Timeline" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={styles.timelineBar}>
          {SLEEP_STAGES.map((stage, i) => {
            const minutes = i === 0 ? awake : i === 1 ? rem : i === 2 ? light : deep;
            const pct = (minutes / Math.max(totalMinutes, 1)) * 100;
            return <View key={i} style={[styles.timelineSegment, { width: `${pct}%`, backgroundColor: stage.color }]} />;
          })}
        </View>
        <View style={styles.timelineLegend}>
          {SLEEP_STAGES.map((stage, i) => (
            <View key={i} style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: stage.color }]} />
              <Text style={styles.legendText}>{stage.label}</Text>
            </View>
          ))}
        </View>
        <View style={styles.timelineTimes}>
          <Text style={styles.timelineTime}>11:00 PM</Text>
          <Text style={styles.timelineTime}>1:00 AM</Text>
          <Text style={styles.timelineTime}>3:00 AM</Text>
          <Text style={styles.timelineTime}>5:00 AM</Text>
          <Text style={styles.timelineTime}>7:00 AM</Text>
        </View>
      </GlassCard>

      {/* Log Sleep */}
      <SectionHeaderPremium icon="log-in" iconColor={colors.health.sleep} title="Log Sleep" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <Text style={styles.logTitle}>How did you sleep?</Text>
        <View style={styles.ratingRow}>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
            <TouchableOpacity
              key={n}
              style={[styles.ratingBtn, rating === n && styles.ratingBtnActive]}
              onPress={() => setRating(n)}
            >
              <Text style={[styles.ratingText, rating === n && styles.ratingTextActive]}>{n}</Text>
            </TouchableOpacity>
          ))}
        </View>
        <TouchableOpacity style={styles.logBtn} onPress={logSleep} disabled={logging}>
          {logging ? (
            <ActivityIndicator color="#FFF" size="small" />
          ) : (
            <Ionicons name="moon" size={18} color="#FFF" />
          )}
          <Text style={styles.logBtnText}>{logging ? 'Logging...' : 'Log Sleep'}</Text>
        </TouchableOpacity>
      </GlassCard>

      {/* Quick Tips */}
      <SectionHeaderPremium icon="bulb" iconColor="#F59E0B" title="Sleep Tips" />
      <GlassCard variant="primary" style={styles.sectionCard}>
        <View style={styles.tipRow}>
          <View style={styles.tipIcon}>
            <Ionicons name="bulb" size={20} color={colors.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.tipTitle}>Consistent Schedule</Text>
            <Text style={styles.tipText}>Go to bed and wake up at the same time every day, even on weekends.</Text>
          </View>
        </View>
      </GlassCard>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  // Score
  scoreSection: { alignItems: 'center', marginTop: spacing.xl, marginBottom: spacing.lg },
  scoreMeta: { flexDirection: 'row', gap: spacing['3xl'], marginTop: spacing.xl },
  scoreMetaItem: { alignItems: 'center' },
  scoreMetaIcon: { width: 32, height: 32, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: 4 },
  scoreMetaValue: { fontSize: 18, fontWeight: '700', color: colors.text.primary },
  scoreMetaLabel: { fontSize: 11, color: colors.text.muted },

  // Stages
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  stageRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
  stageIcon: { width: 28, height: 28, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  stageLabel: { width: 50, fontSize: 12, fontWeight: '600', color: colors.text.secondary, marginLeft: spacing.sm },
  stageBarContainer: { flex: 1, marginHorizontal: spacing.sm },
  stageBar: { height: 8, borderRadius: 4, overflow: 'hidden' },
  stageFill: { height: '100%', borderRadius: 4 },
  stageMinutes: { width: 36, fontSize: 12, fontWeight: '600', color: colors.text.muted, textAlign: 'right' },

  // Timeline
  timelineBar: { flexDirection: 'row', height: 24, borderRadius: 12, overflow: 'hidden' },
  timelineSegment: { height: '100%' },
  timelineLegend: { flexDirection: 'row', justifyContent: 'center', gap: spacing.lg, marginTop: spacing.md },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendText: { fontSize: 11, color: colors.text.muted },
  timelineTimes: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.sm },
  timelineTime: { fontSize: 10, color: colors.text.muted },

  // Log
  logTitle: { fontSize: 16, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.md },
  ratingRow: { flexDirection: 'row', gap: spacing.xs, marginBottom: spacing.xl, flexWrap: 'wrap' },
  ratingBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.bg.input, justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: colors.surface.border },
  ratingBtnActive: { backgroundColor: colors.health.sleep, borderColor: colors.health.sleep },
  ratingText: { fontSize: 14, fontWeight: '600', color: colors.text.muted },
  ratingTextActive: { color: '#FFF' },
  logBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm,
    backgroundColor: colors.health.sleep, paddingVertical: spacing.md, borderRadius: radius.button,
  },
  logBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },

  // Tips
  tipRow: { flexDirection: 'row', gap: spacing.md },
  tipIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },
  tipTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary, marginBottom: 4 },
  tipText: { fontSize: 13, color: colors.text.secondary, lineHeight: 18 },
});
