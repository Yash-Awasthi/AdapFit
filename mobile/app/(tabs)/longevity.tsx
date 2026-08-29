/**
 * Longevity Tracker — Premium Biological Age & Blue Zones
 * Biological age estimation, health span optimization, Blue Zones alignment
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

const BLUE_ZONES = [
  { name: 'Move Naturally', score: 75, icon: 'walk', color: '#22C55E', desc: 'Stay active without structured exercise' },
  { name: 'Purpose', score: 80, icon: 'compass', color: '#3B82F6', desc: 'Wake up with a reason to live' },
  { name: 'Down Shift', score: 60, icon: 'moon', color: '#8B5CF6', desc: 'Manage stress with daily rituals' },
  { name: '80% Rule', score: 70, icon: 'restaurant', color: '#F59E0B', desc: 'Stop eating when 80% full' },
  { name: 'Plant Slant', score: 65, icon: 'leaf', color: '#22C55E', desc: '95% plant-based diet' },
  { name: 'Wine at 5', score: 50, icon: 'wine', color: '#EC4899', desc: 'Moderate alcohol with friends' },
  { name: 'Belong', score: 70, icon: 'people', color: '#F97316', desc: 'Faith-based community' },
  { name: 'Loved Ones First', score: 85, icon: 'heart', color: '#EF4444', desc: 'Commit to a life partner' },
];

export default function LongevityScreen() {
  const biologicalAge = 26;
  const chronologicalAge = 28;
  const yearsYounger = chronologicalAge - biologicalAge;

  return (
    <ScreenWrapper
      title="Longevity"
      subtitle="Optimize your lifespan"
      gradient={['#22C55E', '#06B6D4']}
      rightAction={{ icon: 'trending-up', onPress: () => {} }}
    >
      {/* Biological Age */}
      <View style={styles.ageSection}>
        <GlassCard variant="light" style={styles.ageCard}>
          <View style={styles.ageRow}>
            <View style={styles.ageCol}>
              <Text style={styles.ageLabel}>Biological Age</Text>
              <Text style={[styles.ageValue, { color: '#22C55E' }]}>{biologicalAge}</Text>
              <Text style={styles.ageHint}>{yearsYounger} years younger!</Text>
            </View>
            <View style={styles.ageDivider} />
            <View style={styles.ageCol}>
              <Text style={styles.ageLabel}>Chronological</Text>
              <Text style={styles.ageValue}>{chronologicalAge}</Text>
              <Text style={styles.ageHint}>Actual age</Text>
            </View>
          </View>
        </GlassCard>
      </View>

      {/* Health Span Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={78} size={120} strokeWidth={8} color="#22C55E" label="HEALTHSPAN" sublabel="Good" />
      </View>

      {/* Blue Zones Alignment */}
      <SectionHeaderPremium icon="globe" iconColor="#22C55E" title="Blue Zones Alignment" />
      <StaggeredList staggerDelay={60} animationType="slideIn">
        {BLUE_ZONES.map((zone, i) => (
          <GlassCard key={i} variant="light" style={styles.zoneCard}>
            <View style={styles.zoneRow}>
              <View style={[styles.zoneIcon, { backgroundColor: zone.color + '15' }]}>
                <Ionicons name={zone.icon as any} size={18} color={zone.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.zoneName}>{zone.name}</Text>
                <Text style={styles.zoneDesc}>{zone.desc}</Text>
              </View>
              <Text style={[styles.zoneScore, { color: zone.color }]}>{zone.score}%</Text>
            </View>
            <ProgressBarPremium value={zone.score} max={100} color={zone.color} height={4} />
          </GlassCard>
        ))}
      </StaggeredList>

      {/* Longevity Tips */}
      <SectionHeaderPremium icon="bulb" iconColor="#F59E0B" title="Longevity Tips" />
      <GlassCard variant="primary" style={styles.sectionCard}>
        <View style={styles.tipRow}>
          <Ionicons name="bulb" size={20} color={colors.primary} />
          <View style={{ flex: 1 }}>
            <Text style={styles.tipTitle}>Daily Longevity Habit</Text>
            <Text style={styles.tipText}>Walk 30 minutes daily, eat a handful of nuts, practice gratitude, and connect with loved ones. These simple habits can add years to your life.</Text>
          </View>
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  ageSection: { paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  ageCard: {},
  ageRow: { flexDirection: 'row', alignItems: 'center' },
  ageCol: { flex: 1, alignItems: 'center' },
  ageDivider: { width: 1, height: 50, backgroundColor: colors.surface.divider },
  ageLabel: { fontSize: 12, color: colors.text.muted },
  ageValue: { fontSize: 36, fontWeight: '800', color: colors.text.primary, marginTop: 4 },
  ageHint: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Zones
  zoneCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  zoneRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  zoneIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  zoneName: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  zoneDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  zoneScore: { fontSize: 16, fontWeight: '800' },

  // Tips
  tipRow: { flexDirection: 'row', gap: spacing.md },
  tipTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: 4 },
  tipText: { fontSize: 13, color: colors.text.secondary, lineHeight: 18 },
});
