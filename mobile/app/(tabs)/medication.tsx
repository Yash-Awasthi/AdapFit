/**
 * Medication Tracker — Premium Medication Management
 * Glassmorphism cards, adherence tracking, schedule, reminders
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';

const MEDICATIONS = [
  { id: 1, name: 'Vitamin D3', dosage: '2000 IU', frequency: 'Daily', time: '8:00 AM', color: '#F59E0B', taken: true, refillDays: 45 },
  { id: 2, name: 'Omega-3', dosage: '1000mg', frequency: 'Daily', time: '8:00 AM', color: '#3B82F6', taken: true, refillDays: 30 },
  { id: 3, name: 'Magnesium', dosage: '400mg', frequency: 'Daily', time: '9:00 PM', color: '#8B5CF6', taken: false, refillDays: 20 },
  { id: 4, name: 'Probiotics', dosage: '10B CFU', frequency: 'Daily', time: '7:00 AM', color: '#22C55E', taken: true, refillDays: 15 },
];

export default function MedicationScreen() {
  const [fadeAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  const adherence = Math.round((MEDICATIONS.filter(m => m.taken).length / MEDICATIONS.length) * 100);
  const takenCount = MEDICATIONS.filter(m => m.taken).length;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      <LinearGradient colors={['#F59E0B', '#F97316']} style={styles.header}>
        <Text style={styles.headerTitle}>💊 Medications</Text>
        <Text style={styles.headerSubtitle}>Track your medication schedule</Text>
      </LinearGradient>

      {/* Adherence Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={adherence} size={120} strokeWidth={8} color={colors.health.calm} label="ADHERENCE" />
        <View style={styles.scoreInfo}>
          <Text style={styles.scoreValue}>{takenCount}/{MEDICATIONS.length}</Text>
          <Text style={styles.scoreLabel}>taken today</Text>
          <ProgressBarPremium value={takenCount} max={MEDICATIONS.length} color={colors.health.calm} height={6} />
        </View>
      </View>

      {/* Today's Schedule */}
      <SectionHeaderPremium icon="calendar" iconColor="#F59E0B" title="Today's Schedule" />
      {MEDICATIONS.map((med, i) => (
        <GlassCard key={med.id} variant="light" style={styles.medCard}>
          <View style={styles.medRow}>
            <View style={[styles.medIcon, { backgroundColor: med.color + '15' }]}>
              <Ionicons name="medical" size={20} color={med.color} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.medName}>{med.name}</Text>
              <Text style={styles.medDetail}>{med.dosage} • {med.time}</Text>
            </View>
            <TouchableOpacity style={[styles.medCheck, med.taken && { backgroundColor: colors.health.calm }]}>
              {med.taken ? (
                <Ionicons name="checkmark" size={18} color="#FFF" />
              ) : (
                <Ionicons name="add" size={18} color={colors.text.muted} />
              )}
            </TouchableOpacity>
          </View>
          {med.refillDays <= 20 && (
            <View style={styles.refillWarning}>
              <Ionicons name="warning" size={12} color="#F59E0B" />
              <Text style={styles.refillText}>Refill in {med.refillDays} days</Text>
            </View>
          )}
        </GlassCard>
      ))}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  scoreSection: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xl, marginTop: spacing.xl, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  scoreInfo: { flex: 1 },
  scoreValue: { fontSize: 28, fontWeight: '800', color: colors.text.primary },
  scoreLabel: { fontSize: 13, color: colors.text.muted, marginBottom: spacing.sm },

  medCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  medRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  medIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  medName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  medDetail: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  medCheck: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.surface.divider, justifyContent: 'center', alignItems: 'center' },
  refillWarning: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, backgroundColor: '#F59E0B15', borderRadius: 6 },
  refillText: { fontSize: 11, color: '#F59E0B', fontWeight: '600' },
});
