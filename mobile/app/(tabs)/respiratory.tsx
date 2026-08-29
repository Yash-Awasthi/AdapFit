/**
 * Respiratory Training — Premium Breathing Exercises & Lung Health
 * Guided breathing, lung capacity, COPD management
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing } from '../../src/components/PremiumComponents';
import { StaggeredList, Pulse } from '../../src/components/AnimationSystem';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const BREATHING_EXERCISES = [
  { name: 'Box Breathing', duration: '4-4-4-4', desc: 'Navy SEAL calming technique', color: '#3B82F6', icon: 'square', benefit: 'Stress Relief' },
  { name: '4-7-8 Technique', duration: '4-7-8', desc: 'Dr. Weil\'s sleep aid', color: '#8B5CF6', icon: 'moon', benefit: 'Sleep' },
  { name: 'Diaphragmatic', duration: '5 min', desc: 'Deep belly breathing', color: '#22C55E', icon: 'body', benefit: 'Core Strength' },
  { name: 'Wim Hof Method', duration: '3 rounds', desc: 'Power breathing for energy', color: '#F97316', icon: 'flash', benefit: 'Energy' },
  { name: 'Alternate Nostril', duration: '5 min', desc: 'Nadi Shodhana pranayama', color: '#EC4899', icon: 'leaf', benefit: 'Balance' },
  { name: 'Pursed Lip', duration: '10 reps', desc: 'COPD-friendly breathing', color: '#06B6D4', icon: 'fitness', benefit: 'Lung Health' },
];

export default function RespiratoryScreen() {
  const [activeExercise, setActiveExercise] = useState<number | null>(null);

  return (
    <ScreenWrapper
      title="Respiratory Training"
      subtitle="Strengthen your lungs"
      gradient={['#06B6D4', '#3B82F6']}
      rightAction={{ icon: 'stats-chart', onPress: () => {} }}
    >
      {/* Lung Capacity */}
      <View style={styles.scoreSection}>
        <ScoreRing score={82} size={120} strokeWidth={8} color="#06B6D4" label="LUNG" sublabel="Good Capacity" />
      </View>

      {/* Breathing Exercises */}
      <SectionHeaderPremium icon="leaf" iconColor="#06B6D4" title="Breathing Exercises" />
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {BREATHING_EXERCISES.map((ex, i) => (
          <GlassCard key={i} variant="light" style={styles.exerciseCard}>
            <TouchableOpacity
              onPress={() => setActiveExercise(activeExercise === i ? null : i)}
              style={styles.exerciseRow}
            >
              <View style={[styles.exerciseIcon, { backgroundColor: ex.color + '15' }]}>
                <Ionicons name={ex.icon as any} size={20} color={ex.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.exerciseName}>{ex.name}</Text>
                <Text style={styles.exerciseDesc}>{ex.desc}</Text>
              </View>
              <View style={[styles.benefitBadge, { backgroundColor: ex.color + '15' }]}>
                <Text style={[styles.benefitText, { color: ex.color }]}>{ex.benefit}</Text>
              </View>
            </TouchableOpacity>

            {activeExercise === i && (
              <View style={styles.activeExercise}>
                <View style={styles.breathingVisual}>
                  <Pulse color={ex.color} size={100}>
                    <View style={[styles.breathCircle, { backgroundColor: ex.color + '20', borderColor: ex.color }]}>
                      <Text style={[styles.breathDuration, { color: ex.color }]}>{ex.duration}</Text>
                    </View>
                  </Pulse>
                </View>
                <TouchableOpacity style={[styles.startBtn, { backgroundColor: ex.color }]}>
                  <Ionicons name="play" size={18} color="#FFF" />
                  <Text style={styles.startBtnText}>Start Session</Text>
                </TouchableOpacity>
              </View>
            )}
          </GlassCard>
        ))}
      </StaggeredList>

      {/* Lung Stats */}
      <SectionHeaderPremium icon="analytics" iconColor="#3B82F6" title="Lung Statistics" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {[
          { label: 'Estimated Capacity', value: '4.8L', color: '#06B6D4' },
          { label: 'Breathing Rate', value: '14/min', color: '#22C55E' },
          { label: 'Oxygen Saturation', value: '98%', color: '#3B82F6' },
          { label: 'Sessions This Week', value: '5', color: '#8B5CF6' },
        ].map((stat, i) => (
          <View key={i} style={[styles.statRow, i < 3 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <Text style={styles.statLabel}>{stat.label}</Text>
            <Text style={[styles.statValue, { color: stat.color }]}>{stat.value}</Text>
          </View>
        ))}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Exercises
  exerciseCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm, overflow: 'hidden' },
  exerciseRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  exerciseIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  exerciseName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  exerciseDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  benefitBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  benefitText: { fontSize: 10, fontWeight: '600' },

  // Active Exercise
  activeExercise: { marginTop: spacing.lg, alignItems: 'center' },
  breathingVisual: { marginBottom: spacing.lg },
  breathCircle: { width: 100, height: 100, borderRadius: 50, justifyContent: 'center', alignItems: 'center', borderWidth: 3 },
  breathDuration: { fontSize: 16, fontWeight: '700' },
  startBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, paddingVertical: spacing.md, borderRadius: radius.button, width: '100%' },
  startBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },

  // Stats
  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.md },
  statLabel: { fontSize: 14, color: colors.text.muted },
  statValue: { fontSize: 16, fontWeight: '700' },
});
