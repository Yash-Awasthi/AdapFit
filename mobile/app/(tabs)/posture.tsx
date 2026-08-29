/**
 * Posture Analysis — Premium AI Posture Assessment
 * Camera-based analysis, corrective exercises, workspace tips
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { StaggeredList } from '../../src/components/AnimationSystem';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const POSTURE_AREAS = [
  { area: 'Head Position', score: 85, icon: 'person', color: '#22C55E', status: 'Good', tip: 'Keep ears aligned with shoulders' },
  { area: 'Shoulder Alignment', score: 60, icon: 'body', color: '#F59E0B', status: 'Fair', tip: 'Roll shoulders back and down' },
  { area: 'Spine Curvature', score: 75, icon: 'fitness', color: '#22C55E', status: 'Good', tip: 'Maintain natural S-curve' },
  { area: 'Hip Position', score: 70, icon: 'walk', color: '#F59E0B', status: 'Fair', tip: 'Keep hips level and centered' },
  { area: 'Knee Alignment', score: 90, icon: 'footsteps', color: '#22C55E', status: 'Excellent', tip: 'Knees over ankles when standing' },
];

const EXERCISES = [
  { name: 'Chin Tucks', duration: '30s x 3', difficulty: 'Beginner', color: '#3B82F6', target: 'Neck' },
  { name: 'Wall Angels', duration: '60s x 3', difficulty: 'Intermediate', color: '#8B5CF6', target: 'Shoulders' },
  { name: 'Cat-Cow Stretch', duration: '10 reps x 3', difficulty: 'Beginner', color: '#22C55E', target: 'Spine' },
  { name: 'Hip Flexor Stretch', duration: '30s each x 2', difficulty: 'Beginner', color: '#F97316', target: 'Hips' },
  { name: 'Thoracic Rotation', duration: '10 each side', difficulty: 'Intermediate', color: '#EC4899', target: 'Upper Back' },
];

export default function PostureScreen() {
  const overallScore = Math.round(POSTURE_AREAS.reduce((sum, a) => sum + a.score, 0) / POSTURE_AREAS.length);

  return (
    <ScreenWrapper
      title="Posture Analysis"
      subtitle="AI-powered posture assessment"
      gradient={['#06B6D4', '#3B82F6']}
      rightAction={{ icon: 'camera', onPress: () => {} }}
    >
      {/* Overall Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={overallScore} size={130} strokeWidth={8} color={overallScore >= 80 ? colors.health.calm : '#F59E0B'} label="POSTURE" />
      </View>

      {/* Area Breakdown */}
      <SectionHeaderPremium icon="body" iconColor="#06B6D4" title="Posture Breakdown" />
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {POSTURE_AREAS.map((area, i) => (
          <GlassCard key={i} variant="light" style={styles.areaCard}>
            <View style={styles.areaRow}>
              <View style={[styles.areaIcon, { backgroundColor: area.color + '15' }]}>
                <Ionicons name={area.icon as any} size={18} color={area.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.areaName}>{area.area}</Text>
                <ProgressBarPremium value={area.score} max={100} color={area.color} height={4} />
              </View>
              <Text style={[styles.areaScore, { color: area.color }]}>{area.score}%</Text>
            </View>
            <Text style={styles.areaTip}>💡 {area.tip}</Text>
          </GlassCard>
        ))}
      </StaggeredList>

      {/* Corrective Exercises */}
      <SectionHeaderPremium icon="fitness" iconColor="#22C55E" title="Corrective Exercises" />
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {EXERCISES.map((ex, i) => (
          <GlassCard key={i} variant="light" style={styles.exerciseCard}>
            <View style={styles.exerciseRow}>
              <View style={[styles.exerciseIcon, { backgroundColor: ex.color + '15' }]}>
                <Ionicons name="fitness" size={18} color={ex.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.exerciseName}>{ex.name}</Text>
                <Text style={styles.exerciseMeta}>{ex.duration} • {ex.target}</Text>
              </View>
              <View style={[styles.diffBadge, { backgroundColor: ex.color + '15' }]}>
                <Text style={[styles.diffText, { color: ex.color }]}>{ex.difficulty}</Text>
              </View>
            </View>
          </GlassCard>
        ))}
      </StaggeredList>

      {/* Workspace Tips */}
      <GlassCard variant="primary" style={styles.sectionCard}>
        <View style={styles.tipRow}>
          <Ionicons name="bulb" size={20} color={colors.primary} />
          <View style={{ flex: 1 }}>
            <Text style={styles.tipTitle}>Workspace Ergonomics</Text>
            <Text style={styles.tipText}>Monitor at eye level, elbows at 90°, feet flat on floor. Take a 2-minute stretch break every 30 minutes.</Text>
          </View>
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },

  // Areas
  areaCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  areaRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  areaIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  areaName: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: 4 },
  areaScore: { fontSize: 16, fontWeight: '800' },
  areaTip: { fontSize: 12, color: colors.text.muted, marginTop: spacing.sm, lineHeight: 16 },

  // Exercises
  exerciseCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  exerciseRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  exerciseIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  exerciseName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  exerciseMeta: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  diffBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  diffText: { fontSize: 11, fontWeight: '600' },

  // Tips
  tipRow: { flexDirection: 'row', gap: spacing.md },
  tipTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: 4 },
  tipText: { fontSize: 13, color: colors.text.secondary, lineHeight: 18 },
});
