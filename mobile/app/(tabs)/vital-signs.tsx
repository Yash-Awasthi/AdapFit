/**
 * Vital Signs — Premium ECG, SpO2, Temperature Monitoring
 * Animated ECG waveform, real-time gauges, pulse animations
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { Pulse } from '../../src/components/AnimationSystem';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ECG Waveform Component
const ECGWaveform: React.FC<{ color?: string }> = ({ color = '#22C55E' }) => {
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(animValue, { toValue: 1, duration: 2000, useNativeDriver: true })
    ).start();
  }, []);

  return (
    <View style={styles.ecgContainer}>
      <View style={styles.ecgGrid}>
        {Array.from({ length: 20 }).map((_, i) => (
          <View key={i} style={[styles.ecgGridLine, { left: i * (SCREEN_WIDTH / 20) }]} />
        ))}
      </View>
      <View style={styles.ecgWaveform}>
        {/* Simplified ECG pattern */}
        {[0, 1, 2, 3, 4, 5, 6, 7].map(i => (
          <View key={i} style={[styles.ecgSegment, {
            left: i * 45,
            height: i % 3 === 1 ? 40 : i % 3 === 2 ? 60 : 20,
            backgroundColor: color,
            opacity: 0.8,
          }]} />
        ))}
      </View>
    </View>
  );
};

// Gauge Component
const VitalGauge: React.FC<{
  value: number;
  max: number;
  label: string;
  unit: string;
  color: string;
  icon: string;
  status: string;
}> = ({ value, max, label, unit, color, icon, status }) => {
  const progress = (value / max) * 100;

  return (
    <GlassCard variant="light" style={styles.gaugeCard}>
      <View style={styles.gaugeHeader}>
        <View style={[styles.gaugeIcon, { backgroundColor: color + '15' }]}>
          <Ionicons name={icon as any} size={20} color={color} />
        </View>
        <View>
          <Text style={styles.gaugeLabel}>{label}</Text>
          <View style={[styles.statusBadge, { backgroundColor: color + '15' }]}>
            <Text style={[styles.statusText, { color }]}>{status}</Text>
          </View>
        </View>
      </View>
      <View style={styles.gaugeValueRow}>
        <Text style={[styles.gaugeValue, { color }]}>{value}</Text>
        <Text style={styles.gaugeUnit}>{unit}</Text>
      </View>
      <ProgressBarPremium value={value} max={max} color={color} height={6} />
    </GlassCard>
  );
};

export default function VitalSignsScreen() {
  const [ecgActive, setEcgActive] = useState(true);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (ecgActive) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.1, duration: 500, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      ).start();
    }
  }, [ecgActive]);

  return (
    <ScreenWrapper
      title="Vital Signs"
      subtitle="Real-time health monitoring"
      gradient={['#22C55E', '#06B6D4']}
      rightAction={{ icon: 'download', onPress: () => {} }}
    >
      {/* ECG Section */}
      <SectionHeaderPremium icon="pulse" iconColor="#22C55E" title="ECG Monitor" action={{ label: ecgActive ? 'Stop' : 'Start', onPress: () => setEcgActive(!ecgActive) }} />
      <GlassCard variant="light" style={styles.ecgCard}>
        {ecgActive ? (
          <>
            <ECGWaveform color="#22C55E" />
            <View style={styles.ecgStats}>
              <View style={styles.ecgStat}>
                <Pulse color="#22C55E" size={30}>
                  <Ionicons name="heart" size={14} color="#22C55E" />
                </Pulse>
                <Text style={[styles.ecgStatValue, { color: '#22C55E' }]}>72</Text>
                <Text style={styles.ecgStatLabel}>BPM</Text>
              </View>
              <View style={styles.ecgStat}>
                <Text style={[styles.ecgStatValue, { color: colors.primary }]}>98%</Text>
                <Text style={styles.ecgStatLabel}>SpO2</Text>
              </View>
              <View style={styles.ecgStat}>
                <Text style={[styles.ecgStatValue, { color: '#F59E0B' }]}>36.5°</Text>
                <Text style={styles.ecgStatLabel}>Temp</Text>
              </View>
            </View>
          </>
        ) : (
          <View style={styles.ecgPaused}>
            <Ionicons name="pause-circle" size={48} color={colors.text.muted} />
            <Text style={styles.ecgPausedText}>ECG monitoring paused</Text>
          </View>
        )}
      </GlassCard>

      {/* Vital Gauges */}
      <SectionHeaderPremium icon="fitness" iconColor={colors.health.heart} title="Vital Metrics" />
      <VitalGauge value={72} max={120} label="Heart Rate" unit="bpm" color="#22C55E" icon="heart" status="Normal" />
      <VitalGauge value={98} max={100} label="Blood Oxygen" unit="%" color="#3B82F6" icon="water" status="Excellent" />
      <VitalGauge value={36.5} max={42} label="Body Temperature" unit="°C" color="#F59E0B" icon="thermometer" status="Normal" />
      <VitalGauge value={120} max={180} label="Systolic BP" unit="mmHg" color="#8B5CF6" icon="pulse" status="Normal" />
      <VitalGauge value={80} max={120} label="Diastolic BP" unit="mmHg" color="#8B5CF6" icon="pulse" status="Normal" />

      {/* ECG History */}
      <SectionHeaderPremium icon="time" iconColor={colors.primary} title="Recent Readings" />
      <GlassCard variant="light" style={styles.historyCard}>
        {[
          { time: 'Today 2:30 PM', bpm: 72, spo2: 98, temp: 36.5 },
          { time: 'Today 9:00 AM', bpm: 68, spo2: 97, temp: 36.4 },
          { time: 'Yesterday 8:00 PM', bpm: 75, spo2: 99, temp: 36.6 },
        ].map((reading, i) => (
          <View key={i} style={[styles.historyRow, i < 2 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <Text style={styles.historyTime}>{reading.time}</Text>
            <View style={styles.historyValues}>
              <Text style={[styles.historyValue, { color: '#22C55E' }]}>{reading.bpm} bpm</Text>
              <Text style={[styles.historyValue, { color: '#3B82F6' }]}>{reading.spo2}%</Text>
              <Text style={[styles.historyValue, { color: '#F59E0B' }]}>{reading.temp}°</Text>
            </View>
          </View>
        ))}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  // ECG
  ecgCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg, overflow: 'hidden' },
  ecgContainer: { height: 100, position: 'relative', overflow: 'hidden' },
  ecgGrid: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 },
  ecgGridLine: { position: 'absolute', top: 0, bottom: 0, width: 1, backgroundColor: colors.surface.divider + '30' },
  ecgWaveform: { position: 'absolute', top: 30, left: 0, right: 0, flexDirection: 'row', alignItems: 'center' },
  ecgSegment: { position: 'absolute', width: 2, borderRadius: 1 },
  ecgStats: { flexDirection: 'row', justifyContent: 'space-around', marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: colors.surface.divider },
  ecgStat: { alignItems: 'center' },
  ecgStatValue: { fontSize: 20, fontWeight: '800', marginTop: 4 },
  ecgStatLabel: { fontSize: 11, color: colors.text.muted },
  ecgPaused: { alignItems: 'center', paddingVertical: spacing.xl },
  ecgPausedText: { fontSize: 14, color: colors.text.muted, marginTop: spacing.sm },

  // Gauges
  gaugeCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  gaugeHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  gaugeIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  gaugeLabel: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  statusBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginTop: 2 },
  statusText: { fontSize: 10, fontWeight: '600' },
  gaugeValueRow: { flexDirection: 'row', alignItems: 'baseline', gap: 4, marginBottom: spacing.sm },
  gaugeValue: { fontSize: 28, fontWeight: '800' },
  gaugeUnit: { fontSize: 14, color: colors.text.muted },

  // History
  historyCard: { marginHorizontal: spacing.screenPadding },
  historyRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.md },
  historyTime: { fontSize: 13, color: colors.text.muted },
  historyValues: { flexDirection: 'row', gap: spacing.md },
  historyValue: { fontSize: 13, fontWeight: '600' },
});
