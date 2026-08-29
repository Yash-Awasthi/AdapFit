/**
 * Medical Imaging — Premium AI Skin & Wound Analysis
 * Camera-based assessment, ABCDE scoring, wound tracking
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

const ANALYSIS_TYPES = [
  { id: 'lesion', title: 'Skin Lesion', icon: 'medical', color: '#EF4444', desc: 'ABCDE risk assessment' },
  { id: 'wound', title: 'Wound Care', icon: 'bandage', color: '#F97316', desc: 'Wound classification & care' },
  { id: 'rash', title: 'Rash Detection', icon: 'body', color: '#8B5CF6', desc: 'Pattern recognition' },
];

export default function MedicalImagingScreen() {
  const [selectedType, setSelectedType] = useState<string | null>(null);

  return (
    <ScreenWrapper
      title="Medical Imaging"
      subtitle="AI-powered skin analysis"
      gradient={['#EF4444', '#F97316']}
      rightAction={{ icon: 'camera', onPress: () => {} }}
    >
      {/* Analysis Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={85} size={120} strokeWidth={8} color={colors.health.calm} label="SKIN" sublabel="Good Health" />
      </View>

      {/* Analysis Types */}
      <SectionHeaderPremium icon="scan" iconColor="#EF4444" title="Analysis Types" />
      <View style={styles.typeGrid}>
        {ANALYSIS_TYPES.map(type => (
          <TouchableOpacity
            key={type.id}
            style={[styles.typeCard, selectedType === type.id && { borderColor: type.color + '80', backgroundColor: type.color + '10' }]}
            onPress={() => setSelectedType(selectedType === type.id ? null : type.id)}
          >
            <View style={[styles.typeIcon, { backgroundColor: type.color + '15' }]}>
              <Ionicons name={type.icon as any} size={24} color={type.color} />
            </View>
            <Text style={[styles.typeTitle, selectedType === type.id && { color: type.color }]}>{type.title}</Text>
            <Text style={styles.typeDesc}>{type.desc}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Camera Button */}
      <TouchableOpacity style={styles.cameraBtn}>
        <Ionicons name="camera" size={24} color="#FFF" />
        <Text style={styles.cameraBtnText}>Take Photo for Analysis</Text>
      </TouchableOpacity>

      {/* ABCDE Guide */}
      <SectionHeaderPremium icon="information-circle" iconColor="#3B82F6" title="ABCDE Criteria" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {[
          { letter: 'A', label: 'Asymmetry', desc: 'One half unlike the other', color: '#EF4444' },
          { letter: 'B', label: 'Border', desc: 'Irregular or poorly defined', color: '#F97316' },
          { letter: 'C', label: 'Color', desc: 'Varied from one area to another', color: '#F59E0B' },
          { letter: 'D', label: 'Diameter', desc: 'Larger than 6mm', color: '#8B5CF6' },
          { letter: 'E', label: 'Evolving', desc: 'Changing in size or shape', color: '#EC4899' },
        ].map((item, i) => (
          <View key={i} style={[styles.abcdeRow, i < 4 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <View style={[styles.abcdeLetter, { backgroundColor: item.color + '15' }]}>
              <Text style={[styles.abcdeLetterText, { color: item.color }]}>{item.letter}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.abcdeLabel}>{item.label}</Text>
              <Text style={styles.abcdeDesc}>{item.desc}</Text>
            </View>
          </View>
        ))}
      </GlassCard>

      {/* Recent Analyses */}
      <SectionHeaderPremium icon="time" iconColor={colors.primary} title="Recent Analyses" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {[
          { date: 'Today', type: 'Mole - Left Forearm', risk: 'low', color: '#22C55E' },
          { date: '3 days ago', type: 'Wound - Right Knee', risk: 'healing', color: '#3B82F6' },
        ].map((item, i) => (
          <View key={i} style={[styles.historyRow, i < 1 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <Text style={styles.historyDate}>{item.date}</Text>
            <Text style={styles.historyType}>{item.type}</Text>
            <View style={[styles.riskBadge, { backgroundColor: item.color + '15' }]}>
              <Text style={[styles.riskText, { color: item.color }]}>{item.risk}</Text>
            </View>
          </View>
        ))}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Types
  typeGrid: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  typeCard: { flex: 1, backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
  typeIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.sm },
  typeTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: 2 },
  typeDesc: { fontSize: 11, color: colors.text.muted, textAlign: 'center' },

  // Camera
  cameraBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, marginHorizontal: spacing.screenPadding, marginBottom: spacing.xl, backgroundColor: '#EF4444', paddingVertical: spacing.lg, borderRadius: radius.button },
  cameraBtnText: { fontSize: 16, fontWeight: '700', color: '#FFF' },

  // ABCDE
  abcdeRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  abcdeLetter: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  abcdeLetterText: { fontSize: 16, fontWeight: '800' },
  abcdeLabel: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  abcdeDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2 },

  // History
  historyRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md },
  historyDate: { fontSize: 12, color: colors.text.muted, width: 80 },
  historyType: { flex: 1, fontSize: 14, fontWeight: '600', color: colors.text.primary },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  riskText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
});
