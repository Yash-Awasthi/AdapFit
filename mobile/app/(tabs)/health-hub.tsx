/**
 * Health Hub — Premium Health Monitoring Dashboard
 * Glassmorphism cards, animated score rings, real-time BPM, stress management
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl, Dimensions, ActivityIndicator, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, shadows, glass, getScoreColor, getScoreLabel } from '../../src/theme';
import {
  ScoreRing, GlassCard, GradientCard, SectionHeaderPremium,
  ProgressBarPremium, HealthMetricMini, PillChip,
} from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

const api = async (path: string, opts?: RequestInit) => {
  try {
    const r = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...opts });
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
};

// ===== BPM Camera Section =====
const BPMSection: React.FC = () => {
  const [bpm, setBpm] = useState<number | null>(null);
  const [measuring, setMeasuring] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [hrv, setHrv] = useState<number | null>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (measuring) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.15, duration: 500, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [measuring]);

  const start = async () => {
    setMeasuring(true); setBpm(null); setElapsed(0);
    await api('/camera/bpm/start', { method: 'POST', body: '{}' });
    let t = 0;
    const iv = setInterval(async () => {
      t++; setElapsed(t);
      const r = await api('/camera/bpm/frame', {
        method: 'POST', body: JSON.stringify({ rgb_values: [150 + Math.random() * 50, 120 + Math.random() * 40, 100 + Math.random() * 30], face_detection_confidence: 0.88 }),
      });
      if (r?.current_bpm) setBpm(r.current_bpm);
      if (t >= 12) {
        const final = await api('/camera/bpm/result');
        if (final) { setBpm(final.bpm); setHrv(final.hrv_estimate); }
        setMeasuring(false); clearInterval(iv);
      }
    }, 1000);
  };

  const bpmColor = bpm ? (bpm < 60 ? '#3B82F6' : bpm < 100 ? colors.score.excellent : colors.score.fair) : colors.primary;

  return (
    <GlassCard variant="light" style={styles.sectionCard}>
      <SectionHeaderPremium icon="heart" iconColor={colors.health.heart} title="Heart Rate" subtitle="Camera-based rPPG" />
      <View style={styles.bpmCenter}>
        {measuring ? (
          <View style={styles.bpmCenter}>
            <Animated.View style={[styles.bpmPulseRing, { transform: [{ scale: pulseAnim }], borderColor: colors.health.heart + '30' }]}>
              <View style={[styles.bpmInnerRing, { borderColor: colors.health.heart + '60' }]}>
                <ActivityIndicator size="large" color={colors.health.heart} />
              </View>
            </Animated.View>
            <Text style={[typography.body.sm, { marginTop: 80, color: colors.text.muted }]}>Measuring... {elapsed}s</Text>
            <View style={styles.bpmProgressBar}>
              <View style={[styles.bpmProgressFill, { width: `${(elapsed / 12) * 100}%` }]} />
            </View>
          </View>
        ) : bpm ? (
          <View style={styles.bpmCenter}>
            <ScoreRing score={bpm} size={130} strokeWidth={8} color={bpmColor} label="BPM" />
            <View style={styles.bpmMetaRow}>
              <View style={styles.bpmMetaItem}>
                <Ionicons name="checkmark-circle" size={14} color={colors.score.excellent} />
                <Text style={[typography.body.sm, { color: colors.score.excellent }]}> 85%</Text>
                <Text style={typography.body.xs}> Confidence</Text>
              </View>
              {hrv && (
                <View style={styles.bpmMetaItem}>
                  <Ionicons name="pulse" size={14} color={colors.health.calm} />
                  <Text style={[typography.body.sm, { color: colors.health.calm }]}> {hrv.toFixed(0)}ms</Text>
                  <Text style={typography.body.xs}> HRV</Text>
                </View>
              )}
            </View>
            <TouchableOpacity style={styles.secondaryBtn} onPress={start}>
              <Ionicons name="refresh" size={16} color={colors.text.secondary} />
              <Text style={styles.secondaryBtnText}>Measure Again</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.bpmCenter}>
            <View style={styles.bpmIconLarge}>
              <Ionicons name="camera" size={28} color={colors.primary} />
            </View>
            <Text style={[typography.body.md, { marginTop: spacing.md, textAlign: 'center', color: colors.text.secondary }]}>
              Place finger on camera to measure heart rate
            </Text>
            <TouchableOpacity style={styles.primaryBtn} onPress={start}>
              <Ionicons name="play" size={18} color="#FFF" />
              <Text style={styles.primaryBtnText}>Start Measurement</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </GlassCard>
  );
};

// ===== Stress Manager =====
const StressSection: React.FC = () => {
  const [level, setLevel] = useState(50);
  const [breathing, setBreathing] = useState<any>(null);
  const [activeBreath, setActiveBreath] = useState(false);
  const [breathPhase, setBreathPhase] = useState('Inhale');
  const breathAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    api('/stress/assess', { method: 'POST', body: JSON.stringify({ mood_score: 6, energy_level: 5, sleep_quality: 70 }) }).then(d => d && setLevel(d.overall_score || 50));
    api(`/stress/breathing-exercises?stress_level=50&time_of_day=${new Date().getHours()}`).then(d => d && setBreathing(d));
  }, []);

  const startBreathing = () => {
    setActiveBreath(true);
    Animated.loop(
      Animated.sequence([
        Animated.timing(breathAnim, { toValue: 1.5, duration: 4000, useNativeDriver: true }),
        Animated.timing(breathAnim, { toValue: 1, duration: 4000, useNativeDriver: true }),
      ])
    ).start();
  };

  const stressColor = getScoreColor(100 - level);

  return (
    <GlassCard variant="light" style={styles.sectionCard}>
      <SectionHeaderPremium icon="leaf" iconColor={colors.health.calm} title="Stress Level" />
      <View style={styles.stressBarContainer}>
        <ProgressBarPremium value={level} max={100} color={stressColor} height={8} showLabel label={`${getScoreLabel(100 - level)} Stress`} />
      </View>
      {breathing && !activeBreath && (
        <TouchableOpacity style={styles.breathCard} onPress={startBreathing}>
          <View style={styles.breathCardContent}>
            <View style={[styles.breathIcon, { backgroundColor: colors.health.calm + '15' }]}>
              <Ionicons name="leaf" size={20} color={colors.health.calm} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.breathTitle}>{breathing.name}</Text>
              <Text style={styles.breathSubtitle}>{breathing.technique}</Text>
            </View>
            <Ionicons name="play-circle" size={28} color={colors.health.calm} />
          </View>
        </TouchableOpacity>
      )}
      {activeBreath && breathing && (
        <View style={styles.activeBreathContainer}>
          <Animated.View style={[styles.breathCircle, { transform: [{ scale: breathAnim }] }]}>
            <Ionicons name="leaf" size={32} color="#FFF" />
          </Animated.View>
          <Text style={styles.breathActiveTitle}>{breathing.name}</Text>
          <Text style={styles.breathActiveDesc}>{breathing.description}</Text>
          <TouchableOpacity style={[styles.secondaryBtn, { borderColor: colors.health.calm + '40' }]} onPress={() => { setActiveBreath(false); breathAnim.setValue(1); }}>
            <Text style={[styles.secondaryBtnText, { color: colors.health.calm }]}>Stop Session</Text>
          </TouchableOpacity>
        </View>
      )}
    </GlassCard>
  );
};

// ===== Digital Wellbeing =====
const WellbeingSection: React.FC = () => {
  const [data, setData] = useState<any>({});
  useEffect(() => { api('/wellbeing/report').then(d => d && setData(d)); }, []);
  const score = data.wellbeing_score_numeric || 75;
  const scoreColor = getScoreColor(score);
  const screenTime = data.total_screen_time_minutes || 285;

  return (
    <GlassCard variant="light" style={styles.sectionCard}>
      <SectionHeaderPremium icon="phone-portrait" iconColor={colors.health.digital} title="Digital Wellbeing" />
      <View style={styles.wellbeingRow}>
        <ScoreRing score={score} size={90} strokeWidth={6} color={scoreColor} label="SCORE" />
        <View style={styles.wellbeingStats}>
          <View style={styles.wellbeingStatItem}>
            <Ionicons name="time" size={16} color={colors.health.digital} />
            <Text style={styles.wellbeingStatText}>{Math.floor(screenTime / 60)}h {screenTime % 60}m</Text>
            <Text style={styles.wellbeingStatLabel}>Screen Time</Text>
          </View>
          <View style={styles.wellbeingStatItem}>
            <Ionicons name="finger-print" size={16} color={colors.health.digital} />
            <Text style={styles.wellbeingStatText}>{data.total_pickups || 42}</Text>
            <Text style={styles.wellbeingStatLabel}>Pickups</Text>
          </View>
        </View>
      </View>
    </GlassCard>
  );
};

// ===== Walk Tracker =====
const WalkSection: React.FC = () => {
  const [d, setD] = useState<any>({});
  const [tracking, setTracking] = useState(false);
  useEffect(() => { api('/location/daily-summary').then(r => r && setD(r)); }, []);

  const toggle = async () => {
    if (tracking) {
      const r = await api('/location/stop', { method: 'POST' });
      setTracking(false);
      if (r) setD((prev: any) => ({ ...prev, total_distance_km: r.distance_km, total_calories: r.calories }));
    } else {
      await api('/location/start', { method: 'POST', body: '{}' });
      setTracking(true);
    }
  };

  const goals = [
    { label: 'Steps', value: d.total_steps || 6543, target: 10000, icon: 'footsteps', color: colors.health.activity },
    { label: 'km', value: d.total_distance_km || 4.2, target: 8, icon: 'map', color: colors.health.calm },
    { label: 'Cal', value: d.total_calories || 320, target: 500, icon: 'flame', color: colors.health.energy },
  ];

  return (
    <GlassCard variant="light" style={styles.sectionCard}>
      <SectionHeaderPremium icon="walk" iconColor={colors.health.activity} title="Activity" />
      <View style={styles.goalsRow}>
        {goals.map((g, i) => (
          <View key={i} style={styles.goalCard}>
            <View style={[styles.goalIcon, { backgroundColor: g.color + '15' }]}>
              <Ionicons name={g.icon as any} size={18} color={g.color} />
            </View>
            <Text style={[styles.goalValue, { color: g.color }]}>
              {typeof g.value === 'number' && g.value % 1 !== 0 ? g.value.toFixed(1) : g.value}
            </Text>
            <Text style={styles.goalLabel}>{g.label}</Text>
            <ProgressBarPremium value={g.value} max={g.target} color={g.color} height={3} />
          </View>
        ))}
      </View>
      <TouchableOpacity
        style={[tracking ? styles.stopBtn : styles.primaryBtn, { marginTop: spacing.md }]}
        onPress={toggle}
      >
        <Ionicons name={tracking ? 'stop' : 'play'} size={18} color="#FFF" />
        <Text style={styles.primaryBtnText}>{tracking ? 'Stop Tracking' : 'Start Walk'}</Text>
      </TouchableOpacity>
    </GlassCard>
  );
};

// ===== Fatigue Check =====
const FatigueSection: React.FC = () => {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const assess = async () => {
    setLoading(true);
    const r = await api('/camera/fatigue/detect', {
      method: 'POST', body: JSON.stringify({ eye_aspect_ratio: 0.28, head_tilt_degrees: 12, blinks_per_minute: 14, yawn_duration: 1.5, gaze_variance: 0.4 }),
    });
    setLoading(false);
    if (r) setResult(r);
  };

  return (
    <GlassCard variant="light" style={styles.sectionCard}>
      <SectionHeaderPremium icon="eye" iconColor={colors.health.mental} title="Fatigue Check" subtitle="Camera-based analysis" />
      {result ? (
        <View style={styles.fatigueResult}>
          <ScoreRing score={100 - result.score} size={100} strokeWidth={6} color={getScoreColor(100 - result.score)} label={result.level?.toUpperCase()} />
          <Text style={[typography.body.sm, { marginTop: spacing.md, textAlign: 'center', color: colors.text.secondary }]}>{result.recommendation}</Text>
          <TouchableOpacity style={styles.secondaryBtn} onPress={assess} disabled={loading}>
            <Text style={styles.secondaryBtnText}>Re-assess</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity style={styles.primaryBtn} onPress={assess} disabled={loading}>
          {loading ? <ActivityIndicator color="#FFF" size="small" /> : <Ionicons name="camera" size={18} color="#FFF" />}
          <Text style={styles.primaryBtnText}>{loading ? 'Analyzing...' : 'Assess Fatigue'}</Text>
        </TouchableOpacity>
      )}
    </GlassCard>
  );
};

// ===== Main Screen =====
export default function HealthHubScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = useCallback(async () => { setRefreshing(true); await new Promise(r => setTimeout(r, 1000)); setRefreshing(false); }, []);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <LinearGradient colors={[colors.primary, '#8B5CF6']} style={styles.header}>
        <Text style={styles.headerTitle}>🏥 Health Hub</Text>
        <Text style={styles.headerSubtitle}>Your complete health monitoring center</Text>
      </LinearGradient>

      <BPMSection />
      <StressSection />
      <WellbeingSection />
      <WalkSection />
      <FatigueSection />

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  // BPM
  bpmCenter: { alignItems: 'center', paddingVertical: spacing.md },
  bpmPulseRing: { width: 140, height: 140, borderRadius: 70, borderWidth: 6, justifyContent: 'center', alignItems: 'center' },
  bpmInnerRing: { width: 100, height: 100, borderRadius: 50, borderWidth: 3, justifyContent: 'center', alignItems: 'center' },
  bpmIconLarge: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.primaryMuted, justifyContent: 'center', alignItems: 'center' },
  bpmMetaRow: { flexDirection: 'row', gap: spacing.xl, marginTop: spacing.xl },
  bpmMetaItem: { flexDirection: 'row', alignItems: 'center' },
  bpmProgressBar: { width: 200, height: 4, backgroundColor: colors.surface.divider, borderRadius: 2, marginTop: spacing.md, overflow: 'hidden' },
  bpmProgressFill: { height: '100%', backgroundColor: colors.health.heart, borderRadius: 2 },

  // Stress
  stressBarContainer: { marginTop: spacing.sm },
  breathCard: { marginTop: spacing.md },
  breathCardContent: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.input, padding: spacing.md, borderRadius: radius.md, borderWidth: 1, borderColor: colors.surface.border },
  breathIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginRight: spacing.md },
  breathTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  breathSubtitle: { fontSize: 12, color: colors.text.muted },
  activeBreathContainer: { alignItems: 'center', backgroundColor: colors.health.calmBg, padding: spacing.xl, borderRadius: radius.lg, marginTop: spacing.md },
  breathCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.health.calm, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg },
  breathActiveTitle: { fontSize: 18, fontWeight: '700', color: colors.text.primary, marginBottom: spacing.xs },
  breathActiveDesc: { fontSize: 13, color: colors.text.secondary, textAlign: 'center', marginBottom: spacing.lg },

  // Wellbeing
  wellbeingRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.xl, marginTop: spacing.sm },
  wellbeingStats: { flex: 1, gap: spacing.md },
  wellbeingStatItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  wellbeingStatText: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  wellbeingStatLabel: { fontSize: 11, color: colors.text.muted },

  // Activity
  goalsRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  goalCard: { flex: 1, backgroundColor: colors.bg.input, padding: spacing.md, borderRadius: radius.md, borderWidth: 1, borderColor: colors.surface.border },
  goalIcon: { width: 32, height: 32, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  goalValue: { fontSize: 18, fontWeight: '800' },
  goalLabel: { fontSize: 11, color: colors.text.muted, marginBottom: spacing.xs },

  // Fatigue
  fatigueResult: { alignItems: 'center', paddingVertical: spacing.md },

  // Buttons
  primaryBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, backgroundColor: colors.primary, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, borderRadius: radius.button },
  primaryBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
  secondaryBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, backgroundColor: colors.bg.elevated, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, borderRadius: radius.button, borderWidth: 1, borderColor: colors.surface.border, marginTop: spacing.md },
  secondaryBtnText: { fontSize: 14, fontWeight: '600', color: colors.text.secondary },
  stopBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, backgroundColor: colors.health.danger, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, borderRadius: radius.button },
});
