/**
 * Cardiac Rehabilitation — Heart Recovery Tracking
 * Exercise log, HR zones, recovery milestones, medication tracking.
 */
import React, { useState, useRef } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Animated, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium, StatCard } from '../../src/components/PremiumComponents';
import { MiniLineChart, Sparkline, TrendIndicator } from '../../src/components/HealthCharts';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  recoveryScore: 78,
  currentPhase: 'Phase 2',
  phaseDescription: 'Monitored Exercise',
  daysInRehab: 45,
  totalDays: 90,
  heartRateZones: [
    { zone: 'Rest', bpm: '60-70', percent: 15, color: '#22C55E' },
    { zone: 'Warm-up', bpm: '70-90', percent: 25, color: '#06B6D4' },
    { zone: 'Target', bpm: '90-110', percent: 40, color: '#F59E0B' },
    { zone: 'Peak', bpm: '110-130', percent: 15, color: '#F97316' },
    { zone: 'Recovery', bpm: '70-80', percent: 5, color: '#8B5CF6' },
  ],
  weeklyHR: [68, 72, 65, 74, 70, 66, 68],
  recentExercises: [
    { name: 'Walking', duration: '30 min', hr: '95 bpm', calories: 180, date: 'Today' },
    { name: 'Stationary Bike', duration: '20 min', hr: '105 bpm', calories: 150, date: 'Yesterday' },
    { name: 'Resistance Bands', duration: '15 min', hr: '90 bpm', calories: 80, date: '2 days ago' },
  ],
  milestones: [
    { title: 'First Walk', completed: true, date: 'Day 1' },
    { title: '10 Min Exercise', completed: true, date: 'Day 7' },
    { title: '20 Min Exercise', completed: true, date: 'Day 14' },
    { title: '30 Min Exercise', completed: false, date: 'Day 21' },
    { title: 'Return to Work', completed: false, date: 'Day 60' },
  ],
  medications: [
    { name: 'Metoprolol', dosage: '50mg', time: '8 AM', taken: true },
    { name: 'Lisinopril', dosage: '10mg', time: '8 AM', taken: true },
    { name: 'Aspirin', dosage: '81mg', time: '12 PM', taken: false },
  ],
};

export default function CardiacRehabScreen() {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  useState(() => { Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start(); });

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#EF4444', '#F97316', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Cardiac Rehabilitation</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{mockData.currentPhase}</Text>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 2 }]}>{mockData.phaseDescription} • Day {mockData.daysInRehab}/{mockData.totalDays}</Text>
          <View style={styles.scoreRow}>
            <ScoreRing score={mockData.recoveryScore} size={100} color="#22C55E" />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Recovery Score</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{mockData.recoveryScore}/100</Text>
              <Text style={[typography.body.sm, { color: '#22C55E' }]}>Good Progress</Text>
            </View>
          </View>
          <ProgressBarPremium value={mockData.daysInRehab} max={mockData.totalDays} color="#F97316" showLabel />
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Heart Rate Zones" icon="heart" iconColor={colors.health.heart} />
          {mockData.heartRateZones.map((zone, i) => (
            <View key={i} style={styles.zoneRow}>
              <View style={[styles.zoneDot, { backgroundColor: zone.color }]} />
              <Text style={[typography.body.md, { flex: 1, color: colors.text.primary }]}>{zone.zone}</Text>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>{zone.bpm} bpm</Text>
              <View style={[styles.zoneBar, { backgroundColor: zone.color + '30' }]}>
                <View style={[styles.zoneBarFill, { width: `${zone.percent}%`, backgroundColor: zone.color }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Weekly Heart Rate" icon="pulse" iconColor={colors.health.heart} />
          <GlassCard>
            <MiniLineChart data={mockData.weeklyHR} color={colors.health.heart} height={80} width={SCREEN_WIDTH - 80} />
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d, i) => (
                <Text key={i} style={[typography.body.xs, { color: colors.text.muted, textAlign: 'center', flex: 1 }]}>{d}</Text>
              ))}
            </View>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Recent Exercises" icon="fitness" iconColor={colors.health.activity} />
          {mockData.recentExercises.map((ex, i) => (
            <View key={i} style={styles.exerciseCard}>
              <View style={[styles.exerciseIcon, { backgroundColor: colors.health.activity + '18' }]}>
                <Ionicons name="walk" size={18} color={colors.health.activity} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{ex.name}</Text>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>{ex.duration} • {ex.hr} • {ex.calories} cal</Text>
              </View>
              <Text style={[typography.body.xs, { color: colors.text.muted }]}>{ex.date}</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Recovery Milestones" icon="trophy" iconColor={colors.health.energy} />
          {mockData.milestones.map((m, i) => (
            <View key={i} style={styles.milestoneRow}>
              <View style={[styles.milestoneCheck, { backgroundColor: m.completed ? colors.health.success : 'transparent', borderColor: m.completed ? colors.health.success : colors.surface.border }]}>
                {m.completed && <Ionicons name="checkmark" size={12} color="#fff" />}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: m.completed ? colors.text.muted : colors.text.primary, textDecorationLine: m.completed ? 'line-through' : 'none' }]}>{m.title}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{m.date}</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Medications" icon="medical" iconColor={colors.health.heart} />
          {mockData.medications.map((med, i) => (
            <View key={i} style={styles.medRow}>
              <View style={[styles.medCheck, { backgroundColor: med.taken ? colors.health.success : 'transparent', borderColor: med.taken ? colors.health.success : colors.surface.border }]}>
                {med.taken && <Ionicons name="checkmark" size={10} color="#fff" />}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{med.name}</Text>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>{med.dosage} • {med.time}</Text>
              </View>
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
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20, marginBottom: 16 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  zoneRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  zoneDot: { width: 10, height: 10, borderRadius: 5 },
  zoneBar: { width: 60, height: 6, borderRadius: 3, overflow: 'hidden' },
  zoneBarFill: { height: '100%', borderRadius: 3 },
  exerciseCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border, gap: 12 },
  exerciseIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  milestoneRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, gap: 12 },
  milestoneCheck: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, justifyContent: 'center', alignItems: 'center' },
  medRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 12 },
  medCheck: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, justifyContent: 'center', alignItems: 'center' },
});
