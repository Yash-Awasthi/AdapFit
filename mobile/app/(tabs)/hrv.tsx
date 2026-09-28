/**
 * HRV — trend from daily check-ins, a measured reading from a chest strap,
 * and paced breathing that scores coherence when a strap is connected.
 *
 * A reading needs beat-to-beat intervals. Without a strap the breathing coach
 * still paces, but no coherence score is claimed.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar,
  ActivityIndicator, RefreshControl, Alert, Animated, Easing,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { colors, spacing, typography } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApi } from '../../src/hooks/useApi';
import { asArray, getJson, postJson } from '../../src/services/http';
import { findStrap, streamHeartRate } from '../../src/services/heartRateStrap';

const TINT = '#10B981';
const READING_SECONDS = 180;
const ZONE_COLORS: Record<string, string> = { optimal: '#10B981', normal: '#06B6D4', caution: '#F59E0B', stress: '#EF4444' };
const GOALS = ['relax', 'sleep', 'focus', 'energize'] as const;

interface Trend {
  data_points: { date: string; value: number }[];
  statistics: { mean: number; std: number; min: number; max: number; trend: string; data_points_count?: number };
  zones?: { date: string; zone: string }[];
}
interface Report {
  duration_seconds: number;
  time_domain: { rmssd: number; sdnn: number; hr_mean: number; pnn50: number };
  frequency_domain: { lf_hf_ratio: number } | null;
  quality_score: number;
  interpretation: string;
  artifacts: { found: number };
}
interface Pattern { name: string; inhale_seconds: number; hold_in_seconds: number; exhale_seconds: number; hold_out_seconds: number; description: string; breaths_per_minute: number }
interface Beat { timestamp_ms: number; rr_interval_ms: number; heart_rate: number }

type Stop = () => Promise<void>;

export default function HrvScreen() {
  const { data: trend, loading, refresh, refreshing } = useApi<Trend>('/hrv/trend?days=30');
  const [strapName, setStrapName] = useState<string | null>(null);
  const [liveHr, setLiveHr] = useState<number | null>(null);
  const [recording, setRecording] = useState<'reading' | 'breathing' | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [report, setReport] = useState<Report | null>(null);
  const [goal, setGoal] = useState<(typeof GOALS)[number]>('relax');
  const [pattern, setPattern] = useState<Pattern | null>(null);
  const [phase, setPhase] = useState('');
  const [coherence, setCoherence] = useState<{ coherence_score: number; coherence_level: string; breathing_rate_bpm: number } | null>(null);

  const stopRef = useRef<Stop | null>(null);
  const beatsRef = useRef<Beat[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const phaseRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const breath = useRef(new Animated.Value(0.6)).current;

  useEffect(() => () => {
    stopRef.current?.();
    if (timerRef.current) clearInterval(timerRef.current);
    if (phaseRef.current) clearTimeout(phaseRef.current);
  }, []);

  useEffect(() => {
    getJson<Pattern>(`/hrv/breathing-pattern?goal=${goal}`).then(setPattern);
  }, [goal]);

  const connect = useCallback(async () => {
    try {
      const device = await findStrap();
      const stop = await streamHeartRate(device, (r) => {
        setLiveHr(r.heartRate);
        let t = beatsRef.current.length ? beatsRef.current[beatsRef.current.length - 1].timestamp_ms : 0;
        for (const rr of r.rrIntervalsMs) {
          t += rr;
          beatsRef.current.push({ timestamp_ms: t, rr_interval_ms: rr, heart_rate: 60000 / rr });
        }
      });
      stopRef.current = stop;
      setStrapName(device.name ?? 'Heart-rate strap');
    } catch (e: any) {
      Alert.alert('No strap connected', e?.message ?? String(e));
    }
  }, []);

  const finish = useCallback(async (kind: 'reading' | 'breathing') => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (phaseRef.current) clearTimeout(phaseRef.current);
    timerRef.current = null;
    breath.stopAnimation();
    setRecording(null);
    setPhase('');
    const beats = beatsRef.current;
    if (!strapName) return;
    if (beats.length < 30) {
      Alert.alert('Not enough beats', 'The strap sent too few beat-to-beat intervals. Check it supports RR intervals and is worn snugly.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    if (kind === 'reading') {
      const r = await postJson<Report>('/hrv/analyze', { rr_intervals_ms: beats.map((b) => b.rr_interval_ms) });
      if (r) setReport(r);
      else Alert.alert('Not analysed', 'The recording could not be analysed. Sit still and try again.');
    } else if (pattern) {
      const r = await postJson<any>('/hrv/biofeedback', { pattern: pattern.name, beats });
      if (r) setCoherence(r);
    }
  }, [strapName, pattern, breath]);

  const startTimer = useCallback((kind: 'reading' | 'breathing', seconds: number) => {
    beatsRef.current = [];
    setElapsed(0);
    setRecording(kind);
    const start = Date.now();
    timerRef.current = setInterval(() => {
      const s = Math.floor((Date.now() - start) / 1000);
      setElapsed(s);
      if (s >= seconds) finish(kind);
    }, 500);
  }, [finish]);

  const startReading = useCallback(() => {
    if (!strapName) {
      Alert.alert('Connect a strap first', 'A reading needs beat-to-beat intervals from a chest strap.');
      return;
    }
    setReport(null);
    startTimer('reading', READING_SECONDS);
  }, [strapName, startTimer]);

  const startBreathing = useCallback(() => {
    if (!pattern) return;
    setCoherence(null);
    const steps: [string, number, number][] = [
      ['Breathe in', pattern.inhale_seconds, 1],
      ['Hold', pattern.hold_in_seconds, 1],
      ['Breathe out', pattern.exhale_seconds, 0.6],
      ['Hold', pattern.hold_out_seconds, 0.6],
    ];
    const cycle = () => Animated.sequence(
      steps.filter(([, secs]) => secs > 0).map(([, secs, to]) => Animated.timing(breath, {
        toValue: to, duration: secs * 1000, easing: Easing.inOut(Easing.sin), useNativeDriver: true,
      })),
    );
    const active = steps.filter(([, secs]) => secs > 0);
    let i = 0;
    const phaseLoop = () => {
      const [label, secs] = active[i % active.length];
      setPhase(label);
      i += 1;
      phaseRef.current = setTimeout(phaseLoop, secs * 1000);
    };
    phaseLoop();
    Animated.loop(cycle()).start();
    startTimer('breathing', 300);
  }, [pattern, breath, startTimer]);

  if (loading) {
    return <View style={[styles.container, styles.center]}><ActivityIndicator size="large" color={TINT} /></View>;
  }

  const stats = trend?.statistics;
  const points = asArray<{ date: string; value: number }>(trend?.data_points).slice(-14);
  const maxVal = points.reduce((m, p) => Math.max(m, p.value), 1);
  const zones = asArray<{ date: string; zone: string }>(trend?.zones).slice(-14);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={TINT} />}>
        <LinearGradient colors={[TINT, '#059669', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Heart Rate Variability</Text>
          {points.length > 0 && stats ? (
            <>
              <Text style={styles.heroValue}>{points[points.length - 1].value} ms</Text>
              <Text style={styles.heroMuted}>
                Latest RMSSD · your 30-day mean {stats.mean} ms · {stats.trend.replace('_', ' ')}
              </Text>
            </>
          ) : (
            <Text style={[typography.heading.h2, { color: '#fff', marginTop: 8 }]}>Add HRV to a check-in, or take a reading</Text>
          )}
        </LinearGradient>

        {points.length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Last 14 Readings" icon="pulse" iconColor={TINT} />
            <GlassCard>
              <View style={styles.bars}>
                {points.map((p, i) => (
                  <View key={p.date + i} style={styles.barCol}>
                    <View style={[styles.bar, {
                      height: Math.max(4, (p.value / maxVal) * 90),
                      backgroundColor: ZONE_COLORS[zones[i]?.zone] ?? TINT,
                    }]} />
                  </View>
                ))}
              </View>
              <Text style={styles.helperText}>Colour shows each reading against your own normal, not a population average.</Text>
            </GlassCard>
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Measured Reading" subtitle="3 minutes, sitting still" icon="bluetooth" iconColor={TINT} />
          <GlassCard>
            {strapName ? (
              <Text style={styles.bodyText}>{strapName} connected{liveHr ? ` · ${liveHr} bpm` : ''}</Text>
            ) : (
              <TouchableOpacity style={styles.secondaryBtn} onPress={connect}>
                <Text style={styles.secondaryBtnText}>Connect heart-rate strap</Text>
              </TouchableOpacity>
            )}
            {recording === 'reading' ? (
              <Text style={styles.bigValue}>{Math.max(0, READING_SECONDS - elapsed)}s</Text>
            ) : (
              <TouchableOpacity style={styles.primaryBtn} onPress={startReading} disabled={!!recording}>
                <Text style={styles.primaryBtnText}>Start reading</Text>
              </TouchableOpacity>
            )}
            {report && (
              <View style={styles.reportGrid}>
                <Metric label="RMSSD" value={`${Math.round(report.time_domain.rmssd)} ms`} />
                <Metric label="SDNN" value={`${Math.round(report.time_domain.sdnn)} ms`} />
                <Metric label="Heart rate" value={`${Math.round(report.time_domain.hr_mean)} bpm`} />
                {report.frequency_domain && <Metric label="LF/HF" value={report.frequency_domain.lf_hf_ratio.toFixed(2)} />}
                <Text style={styles.helperText}>
                  Signal quality {Math.round(report.quality_score)}/100 · {report.artifacts.found} irregular beats corrected. {report.interpretation}
                </Text>
              </View>
            )}
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Breathing Coach" subtitle={pattern?.description} icon="leaf" iconColor={TINT} />
          <GlassCard>
            <View style={styles.chipRow}>
              {GOALS.map((g) => (
                <TouchableOpacity key={g} style={[styles.chip, goal === g && styles.chipActive]} onPress={() => setGoal(g)} disabled={!!recording}>
                  <Text style={[styles.chipText, goal === g && styles.chipTextActive]}>{g}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <View style={styles.pacerWrap}>
              <Animated.View style={[styles.pacer, { transform: [{ scale: breath }] }]} />
              <Text style={styles.pacerText}>{recording === 'breathing' ? phase : pattern ? `${pattern.breaths_per_minute} breaths/min` : ''}</Text>
            </View>
            {recording === 'breathing' ? (
              <TouchableOpacity style={styles.secondaryBtn} onPress={() => finish('breathing')}>
                <Text style={styles.secondaryBtnText}>Finish ({Math.max(0, 300 - elapsed)}s left)</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={styles.primaryBtn} onPress={startBreathing} disabled={!!recording || !pattern}>
                <Text style={styles.primaryBtnText}>Start 5-minute session</Text>
              </TouchableOpacity>
            )}
            {coherence && (
              <Text style={styles.bodyText}>
                Coherence {Math.round(coherence.coherence_score * 100)}/100 ({coherence.coherence_level}) · you breathed at {coherence.breathing_rate_bpm} per minute.
              </Text>
            )}
            {!strapName && <Text style={styles.helperText}>Connect a strap to get a coherence score for the session.</Text>}
          </GlassCard>
        </View>
      </ScrollView>
    </View>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroValue: { color: '#fff', fontSize: 34, fontWeight: '800', marginTop: 6 },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  bars: { flexDirection: 'row', alignItems: 'flex-end', height: 96, gap: 4 },
  barCol: { flex: 1, justifyContent: 'flex-end' },
  bar: { borderRadius: 3 },
  helperText: { color: colors.text.muted, fontSize: 13, marginTop: 8, lineHeight: 18 },
  bodyText: { color: colors.text.secondary, fontSize: 14, marginTop: 8, lineHeight: 20 },
  bigValue: { color: colors.text.primary, fontSize: 32, fontWeight: '800', textAlign: 'center', marginTop: 12 },
  primaryBtn: { backgroundColor: TINT, borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 12 },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  secondaryBtn: { borderWidth: 1, borderColor: TINT, borderRadius: 12, padding: 12, alignItems: 'center', marginTop: 8 },
  secondaryBtnText: { color: TINT, fontWeight: '700' },
  reportGrid: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 12, gap: 12 },
  metric: { width: '45%' },
  metricValue: { color: colors.text.primary, fontSize: 20, fontWeight: '700' },
  metricLabel: { color: colors.text.muted, fontSize: 12 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: TINT + '25', borderColor: TINT },
  chipText: { color: colors.text.muted, fontSize: 13, textTransform: 'capitalize' },
  chipTextActive: { color: TINT, fontWeight: '700' },
  pacerWrap: { height: 180, alignItems: 'center', justifyContent: 'center', marginTop: 12 },
  pacer: { position: 'absolute', width: 150, height: 150, borderRadius: 75, backgroundColor: TINT + '40', borderWidth: 2, borderColor: TINT },
  pacerText: { color: colors.text.primary, fontSize: 16, fontWeight: '700' },
});
