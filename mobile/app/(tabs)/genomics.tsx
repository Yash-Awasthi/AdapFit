/**
 * Genomics Insights — DNA-Based Health Dashboard
 * Gene variants, personalized nutrition, pharmacogenomics, ancestry snippets.
 */
import React, { useState, useRef } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Animated, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, StatCard } from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  riskScore: 32,
  geneVariants: [
    { gene: 'MTHFR', variant: 'C677T', impact: 'Folate Metabolism', risk: 'moderate', recommendation: 'Take methylfolate instead of folic acid', color: '#F59E0B' },
    { gene: 'FTO', variant: 'rs9939609', impact: 'Weight Management', risk: 'elevated', recommendation: 'Monitor portion sizes, increase physical activity', color: '#F97316' },
    { gene: 'APOE', variant: 'ε3/ε4', impact: 'Cognitive Health', risk: 'moderate', recommendation: 'Prioritize omega-3, exercise, cognitive stimulation', color: '#8B5CF6' },
    { gene: 'CYP1A2', variant: 'rs762551', impact: 'Caffeine Metabolism', risk: 'low', recommendation: 'Slow metabolizer — limit caffeine after 12 PM', color: '#22C55E' },
    { gene: 'VDR', variant: 'Fok1', impact: 'Vitamin D', risk: 'elevated', recommendation: 'Supplement with Vitamin D3 (2000 IU daily)', color: '#F97316' },
    { gene: 'LCT', variant: 'rs4988235', impact: 'Lactose Tolerance', risk: 'low', recommendation: 'Lactose tolerant — can include dairy freely', color: '#22C55E' },
  ],
  nutrition: [
    { type: 'Protein', recommendation: 'Higher intake (1.2g/kg)', reason: 'FTO variant' },
    { type: 'Omega-3', recommendation: '2000mg EPA/DHA daily', reason: 'APOE ε4 carrier' },
    { type: 'Folate', recommendation: 'Methylfolate 800mcg', reason: 'MTHFR C677T' },
    { type: 'Vitamin D', recommendation: '2000 IU D3 daily', reason: 'VDR variant' },
    { type: 'Caffeine', recommendation: 'Max 1 cup before noon', reason: 'Slow CYP1A2 metabolizer' },
  ],
  traits: [
    { trait: 'Caffeine Sensitivity', value: 'High', icon: 'cafe' },
    { trait: 'Lactose Tolerance', value: 'Normal', icon: 'nutrition' },
    { trait: 'Alcohol Metabolism', value: 'Normal', icon: 'wine' },
    { trait: 'Muscle Fiber Type', value: 'Endurance', icon: 'fitness' },
    { trait: 'Sleep chronotype', value: 'Intermediate', icon: 'moon' },
    { trait: 'Migraine Risk', value: 'Elevated', icon: 'flash' },
  ],
};

const riskColors: Record<string, string> = { low: '#22C55E', moderate: '#F59E0B', elevated: '#F97316', high: '#EF4444' };

export default function GenomicsScreen() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#8B5CF6', '#6366F1', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Genomics Insights</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Your DNA Profile</Text>
          <View style={styles.scoreRow}>
            <ScoreRing score={100 - mockData.riskScore} size={100} color="#22C55E" />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Genetic Risk Score</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{mockData.riskScore}/100</Text>
              <Text style={[typography.body.sm, { color: '#22C55E' }]}>Low Overall Risk</Text>
            </View>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Gene Variants" icon="analytics" iconColor="#8B5CF6" />
          {mockData.geneVariants.map((v, i) => (
            <GlassCard key={i} style={{ marginBottom: 10 }}>
              <View style={styles.variantHeader}>
                <View style={[styles.geneBadge, { backgroundColor: v.color + '20' }]}>
                  <Text style={[typography.label.tag, { color: v.color }]}>{v.gene}</Text>
                </View>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>{v.variant}</Text>
                <View style={[styles.riskBadge, { backgroundColor: riskColors[v.risk] + '20' }]}>
                  <Text style={[typography.label.sm, { color: riskColors[v.risk] }]}>{v.risk.toUpperCase()}</Text>
                </View>
              </View>
              <Text style={[typography.body.md, { color: colors.text.primary, marginTop: 8 }]}>{v.impact}</Text>
              <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 4 }]}>{v.recommendation}</Text>
            </GlassCard>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="DNA-Based Nutrition" icon="nutrition" iconColor="#22C55E" />
          {mockData.nutrition.map((n, i) => (
            <View key={i} style={styles.nutritionCard}>
              <Text style={[typography.label.md, { color: colors.health.nutrition }]}>{n.type}</Text>
              <Text style={[typography.body.md, { color: colors.text.primary, marginTop: 4 }]}>{n.recommendation}</Text>
              <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 2 }]}>Based on: {n.reason}</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Genetic Traits" icon="finger-print" iconColor="#A78BFA" />
          <View style={styles.traitsGrid}>
            {mockData.traits.map((t, i) => (
              <View key={i} style={styles.traitCard}>
                <Ionicons name={t.icon as any} size={20} color={colors.primary} />
                <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 6 }]}>{t.trait}</Text>
                <Text style={[typography.body.md, { color: colors.text.primary, fontWeight: '600', marginTop: 2 }]}>{t.value}</Text>
              </View>
            ))}
          </View>
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
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  variantHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  geneBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6, marginLeft: 'auto' },
  nutritionCard: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border },
  traitsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  traitCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - 20) / 3, backgroundColor: colors.bg.card, borderRadius: 14, padding: 12, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
});
