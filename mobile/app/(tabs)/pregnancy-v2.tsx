/**
 * Pregnancy Tracker — Comprehensive Prenatal Care
 * Trimester progress, fetal development, appointments, symptoms, nutrition.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  week: 24,
  trimester: 2,
  dueDate: '2025-12-15',
  babySize: 'Ear of Corn',
  babyWeight: '600g',
  babyLength: '30cm',
  fetalDevelopment: [
    { week: 24, milestone: 'Inner ear fully formed — baby can sense gravity', icon: 'ear' },
    { week: 25, milestone: 'Fat deposits smooth out wrinkled skin', icon: 'body' },
    { week: 26, milestone: 'Eyes begin to open and respond to light', icon: 'eye' },
    { week: 28, milestone: 'Brain development accelerates', icon: 'fitness' },
  ],
  appointments: [
    { doctor: 'Dr. Smith', type: 'Monthly Checkup', date: 'Jun 20', completed: true },
    { doctor: 'Dr. Lee', type: 'Anatomy Scan', date: 'Jul 5', completed: false },
    { doctor: 'Dr. Smith', type: 'Glucose Screening', date: 'Jul 15', completed: false },
  ],
  symptoms: [
    { name: 'Back Pain', severity: 6, icon: 'body' },
    { name: 'Fatigue', severity: 4, icon: 'moon' },
    { name: 'Swelling', severity: 3, icon: 'water' },
    { name: 'Heartburn', severity: 5, icon: 'flame' },
  ],
  nutrition: {
    folate: { current: 600, target: 800, unit: 'mcg' },
    iron: { current: 27, target: 27, unit: 'mg' },
    calcium: { current: 800, target: 1000, unit: 'mg' },
    protein: { current: 65, target: 75, unit: 'g' },
    water: { current: 6, target: 8, unit: 'glasses' },
  },
  weightGain: 12,
  targetWeightGain: 15,
};

const trimesterColors = ['#EC4899', '#F472B6', '#F9A8D4'];

export default function PregnancyV2Screen() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#EC4899', '#F472B6', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Pregnancy Tracker</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Week {mockData.week}</Text>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 2 }]}>Trimester {mockData.trimester} • Due {mockData.dueDate}</Text>
          <View style={styles.scoreRow}>
            <ScoreRing score={Math.round(mockData.week / 40 * 100)} size={100} color="#EC4899" />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Pregnancy Progress</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{mockData.week}/40 weeks</Text>
              <Text style={[typography.body.sm, { color: '#EC4899' }]}>{160 - mockData.week} weeks to go</Text>
            </View>
          </View>
          <ProgressBarPremium value={mockData.week} max={40} color="#EC4899" showLabel />
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Baby This Week" icon="baby" iconColor="#EC4899" />
          <GlassCard>
            <View style={styles.babyInfo}>
              <View style={styles.babyStat}>
                <Ionicons name="resize" size={18} color="#EC4899" />
                <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 4 }]}>Size</Text>
                <Text style={[typography.body.md, { color: colors.text.primary, fontWeight: '600' }]}>{mockData.babySize}</Text>
              </View>
              <View style={styles.babyStat}>
                <Ionicons name="fitness" size={18} color="#EC4899" />
                <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 4 }]}>Weight</Text>
                <Text style={[typography.body.md, { color: colors.text.primary, fontWeight: '600' }]}>{mockData.babyWeight}</Text>
              </View>
              <View style={styles.babyStat}>
                <Ionicons name="resize" size={18} color="#EC4899" />
                <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 4 }]}>Length</Text>
                <Text style={[typography.body.md, { color: colors.text.primary, fontWeight: '600' }]}>{mockData.babyLength}</Text>
              </View>
            </View>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Upcoming Milestones" icon="ribbon" iconColor="#F472B6" />
          {mockData.fetalDevelopment.map((m, i) => (
            <View key={i} style={styles.milestoneRow}>
              <View style={[styles.milestoneWeek, { backgroundColor: colors.health.heart + '18' }]}>
                <Text style={[typography.body.sm, { color: colors.health.heart, fontWeight: '600' }]}>W{m.week}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{m.milestone}</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Nutrition" icon="nutrition" iconColor="#22C55E" />
          {Object.entries(mockData.nutrition).map(([key, n]) => (
            <View key={key} style={styles.nutrientRow}>
              <Text style={[typography.body.md, { flex: 1, color: colors.text.primary, textTransform: 'capitalize' }]}>{key}</Text>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>{n.current}/{n.target} {n.unit}</Text>
              <View style={[styles.nutrientBar, { backgroundColor: colors.health.nutrition + '20' }]}>
                <View style={[styles.nutrientBarFill, { width: `${Math.min(n.current / n.target * 100, 100)}%`, backgroundColor: n.current >= n.target ? colors.health.success : colors.health.warning }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Symptoms" icon="alert-circle" iconColor={colors.health.warning} />
          {mockData.symptoms.map((s, i) => (
            <View key={i} style={styles.symptomRow}>
              <Ionicons name={s.icon as any} size={18} color={colors.health.warning} />
              <Text style={[typography.body.md, { flex: 1, color: colors.text.primary }]}>{s.name}</Text>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>{s.severity}/10</Text>
              <View style={[styles.painBar, { backgroundColor: colors.health.warning + '20' }]}>
                <View style={[styles.painBarFill, { width: `${s.severity * 10}%`, backgroundColor: colors.health.warning }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Appointments" icon="calendar" iconColor={colors.primary} />
          {mockData.appointments.map((a, i) => (
            <View key={i} style={[styles.appointmentCard, a.completed && { opacity: 0.6 }]}>
              <View style={[styles.apptIcon, { backgroundColor: a.completed ? colors.health.success + '18' : colors.primary + '18' }]}>
                <Ionicons name={a.completed ? 'checkmark' : 'calendar'} size={16} color={a.completed ? colors.health.success : colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{a.type}</Text>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>{a.doctor} • {a.date}</Text>
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
  babyInfo: { flexDirection: 'row', justifyContent: 'space-around' },
  babyStat: { alignItems: 'center' },
  milestoneRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 12 },
  milestoneWeek: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  nutrientRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  nutrientBar: { width: 80, height: 6, borderRadius: 3, overflow: 'hidden' },
  nutrientBarFill: { height: '100%', borderRadius: 3 },
  symptomRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  painBar: { width: 60, height: 6, borderRadius: 3, overflow: 'hidden' },
  painBarFill: { height: '100%', borderRadius: 3 },
  appointmentCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border, gap: 12 },
  apptIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
});
