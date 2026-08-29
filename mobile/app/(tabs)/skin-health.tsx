/**
 * Skin Health — Premium Skin Analysis & Mole Tracking
 * Glassmorphism cards, mole ABCDE tracking, UV exposure, skin type assessment
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

const MOLES = [
  { id: 1, name: 'Left forearm', location: 'Arm', date: '2024-01-15', risk: 'low', color: '#22C55E', abcde: { a: false, b: false, c: false, d: false, e: false } },
  { id: 2, name: 'Back right shoulder', location: 'Back', date: '2024-02-20', risk: 'medium', color: '#F59E0B', abcde: { a: false, b: true, c: false, d: false, e: false } },
  { id: 3, name: 'Right calf', location: 'Leg', date: '2024-03-10', risk: 'low', color: '#22C55E', abcde: { a: false, b: false, c: false, d: false, e: false } },
];

const UV_LEVELS = [
  { level: 'Low', range: '1-2', color: '#22C55E', icon: 'sunny', protection: 'No protection needed' },
  { level: 'Moderate', range: '3-5', color: '#F59E0B', icon: 'sunny', protection: 'Wear sunscreen SPF 30+' },
  { level: 'High', range: '6-7', color: '#F97316', icon: 'sunny', protection: 'Seek shade, SPF 50+' },
  { level: 'Very High', range: '8-10', color: '#EF4444', icon: 'sunny', protection: 'Avoid sun 10am-4pm' },
  { level: 'Extreme', range: '11+', color: '#DC2626', icon: 'sunny', protection: 'Stay indoors if possible' },
];

export default function SkinHealthScreen() {
  const [skinType] = useState({ type: 'Type II', description: 'Fair skin, burns easily, tans minimally', fitzpatrick: 2 });

  return (
    <ScreenWrapper
      title="Skin Health"
      subtitle="Track and monitor your skin"
      gradient={['#F97316', '#F59E0B']}
      rightAction={{ icon: 'camera', onPress: () => {} }}
    >
      {/* Skin Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={85} size={120} strokeWidth={8} color={colors.health.calm} label="SKIN" sublabel="Good Health" />
      </View>

      {/* Skin Type */}
      <SectionHeaderPremium icon="person" iconColor="#F97316" title="Skin Type" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={styles.skinTypeRow}>
          <View style={styles.skinTypeBadge}>
            <Text style={styles.skinTypeValue}>{skinType.type}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.skinTypeDesc}>{skinType.description}</Text>
            <Text style={styles.skinTypeFitz}>Fitzpatrick Scale: {skinType.fitzpatrick}/6</Text>
          </View>
        </View>
      </GlassCard>

      {/* Mole Tracker */}
      <SectionHeaderPremium icon="medical" iconColor="#EF4444" title="Mole Tracker" action={{ label: 'Add Mole', onPress: () => {} }} />
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {MOLES.map(mole => (
          <GlassCard key={mole.id} variant="light" style={styles.moleCard}>
            <View style={styles.moleHeader}>
              <View style={[styles.moleIcon, { backgroundColor: mole.color + '15' }]}>
                <Ionicons name="medical" size={18} color={mole.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.moleName}>{mole.name}</Text>
                <Text style={styles.moleMeta}>{mole.location} • {mole.date}</Text>
              </View>
              <View style={[styles.riskBadge, { backgroundColor: mole.color + '15' }]}>
                <Text style={[styles.riskText, { color: mole.color }]}>{mole.risk}</Text>
              </View>
            </View>
            <View style={styles.abcdeRow}>
              {['A', 'B', 'C', 'D', 'E'].map((letter, i) => {
                const keys = ['a', 'b', 'c', 'd', 'e'] as const;
                const active = mole.abcde[keys[i]];
                return (
                  <View key={letter} style={[styles.abcdeItem, active && styles.abcdeItemActive]}>
                    <Text style={[styles.abcdeLetter, active && styles.abcdeLetterActive]}>{letter}</Text>
                  </View>
                );
              })}
            </View>
          </GlassCard>
        ))}
      </StaggeredList>

      {/* ABCDE Guide */}
      <SectionHeaderPremium icon="information-circle" iconColor="#3B82F6" title="ABCDE Guide" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {[
          { letter: 'A', label: 'Asymmetry', desc: 'One half unlike the other' },
          { letter: 'B', label: 'Border', desc: 'Irregular, scalloped, or poorly defined' },
          { letter: 'C', label: 'Color', desc: 'Varied from one area to another' },
          { letter: 'D', label: 'Diameter', desc: 'Larger than 6mm (pencil eraser)' },
          { letter: 'E', label: 'Evolving', desc: 'Changing in size, shape, or color' },
        ].map((item, i) => (
          <View key={i} style={[styles.abcdeGuideItem, i < 4 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <View style={styles.abcdeGuideLetter}>
              <Text style={styles.abcdeGuideLetterText}>{item.letter}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.abcdeGuideLabel}>{item.label}</Text>
              <Text style={styles.abcdeGuideDesc}>{item.desc}</Text>
            </View>
          </View>
        ))}
      </GlassCard>

      {/* UV Exposure */}
      <SectionHeaderPremium icon="sunny" iconColor="#F59E0B" title="UV Index" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={styles.uvCurrent}>
          <Text style={styles.uvValue}>4</Text>
          <Text style={styles.uvLabel}>Moderate</Text>
          <Text style={styles.uvProtection}>Wear sunscreen SPF 30+</Text>
        </View>
        <View style={styles.uvBar}>
          {UV_LEVELS.map((uv, i) => (
            <View key={i} style={[styles.uvSegment, { backgroundColor: uv.color, flex: 1 }]} />
          ))}
        </View>
        <View style={styles.uvLabels}>
          {UV_LEVELS.map((uv, i) => (
            <Text key={i} style={styles.uvLabelSmall}>{uv.level}</Text>
          ))}
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Skin Type
  skinTypeRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  skinTypeBadge: { width: 48, height: 48, borderRadius: 14, backgroundColor: '#F9731615', justifyContent: 'center', alignItems: 'center' },
  skinTypeValue: { fontSize: 16, fontWeight: '800', color: '#F97316' },
  skinTypeDesc: { fontSize: 14, fontWeight: '600', color: colors.text.primary },
  skinTypeFitz: { fontSize: 12, color: colors.text.muted, marginTop: 2 },

  // Mole
  moleCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  moleHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  moleIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  moleName: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  moleMeta: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  riskText: { fontSize: 11, fontWeight: '700', textTransform: 'capitalize' },
  abcdeRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.md },
  abcdeItem: { width: 32, height: 32, borderRadius: 8, backgroundColor: colors.surface.divider, justifyContent: 'center', alignItems: 'center' },
  abcdeItemActive: { backgroundColor: '#EF444420', borderWidth: 1, borderColor: '#EF4444' },
  abcdeLetter: { fontSize: 12, fontWeight: '700', color: colors.text.muted },
  abcdeLetterActive: { color: '#EF4444' },

  // ABCDE Guide
  abcdeGuideItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  abcdeGuideLetter: { width: 32, height: 32, borderRadius: 8, backgroundColor: '#3B82F615', justifyContent: 'center', alignItems: 'center' },
  abcdeGuideLetterText: { fontSize: 14, fontWeight: '800', color: '#3B82F6' },
  abcdeGuideLabel: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  abcdeGuideDesc: { fontSize: 12, color: colors.text.muted, marginTop: 1 },

  // UV
  uvCurrent: { alignItems: 'center', marginBottom: spacing.lg },
  uvValue: { fontSize: 48, fontWeight: '800', color: '#F59E0B' },
  uvLabel: { fontSize: 16, fontWeight: '700', color: colors.text.primary, marginTop: 4 },
  uvProtection: { fontSize: 13, color: '#F59E0B', marginTop: 4 },
  uvBar: { flexDirection: 'row', height: 8, borderRadius: 4, overflow: 'hidden' },
  uvSegment: { height: '100%' },
  uvLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.xs },
  uvLabelSmall: { fontSize: 9, color: colors.text.muted, flex: 1, textAlign: 'center' },
});
