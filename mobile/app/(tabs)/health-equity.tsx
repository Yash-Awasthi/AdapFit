/**
 * Health Equity — Community Health & Social Determinants
 * SDOH scoring, community resources, intervention recommendations, outcome tracking.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { RadarChart, BarChart } from '../../src/components/HealthCharts';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  communityName: 'Downtown Community',
  overallScore: 58,
  equityGrade: 'C',
  categories: [
    { name: 'Economic Stability', score: 45, icon: 'cash', color: '#F59E0B' },
    { name: 'Education Access', score: 62, icon: 'school', color: '#06B6D4' },
    { name: 'Healthcare Access', score: 38, icon: 'medical', color: '#EF4444' },
    { name: 'Neighborhood', score: 55, icon: 'home', color: '#8B5CF6' },
    { name: 'Social Support', score: 70, icon: 'people', color: '#22C55E' },
    { name: 'Food Security', score: 52, icon: 'nutrition', color: '#F97316' },
  ],
  interventions: [
    { name: 'Telehealth Bridge Program', impact: 'high', cost: 'low', category: 'Healthcare', color: '#EF4444' },
    { name: 'Community Health Worker', impact: 'high', cost: 'moderate', category: 'Healthcare', color: '#EF4444' },
    { name: 'SNAP Enrollment Assistance', impact: 'high', cost: 'low', category: 'Food', color: '#F97316' },
    { name: 'Mobile Food Pantry', impact: 'high', cost: 'moderate', category: 'Food', color: '#F97316' },
    { name: 'Transportation Vouchers', impact: 'moderate', cost: 'low', category: 'Healthcare', color: '#EF4444' },
  ],
  resources: [
    { name: 'Community Health Center', type: 'Health Clinic', distance: '0.5 mi', phone: '555-0100' },
    { name: 'Downtown Food Bank', type: 'Food Bank', distance: '1.2 mi', phone: '555-0101' },
    { name: 'Mental Health Alliance', type: 'Mental Health', distance: '0.8 mi', phone: '555-0102' },
    { name: 'Job Training Center', type: 'Job Center', distance: '1.5 mi', phone: '555-0103' },
  ],
  outcomes: [
    { intervention: 'Telehealth Bridge', metric: 'Appointments Kept', before: 60, after: 85 },
    { intervention: 'Mobile Food Pantry', metric: 'Food Security', before: 35, after: 68 },
    { intervention: 'Transportation Vouchers', metric: 'No-Shows', before: 40, after: 15 },
  ],
};

const radarData = mockData.categories.map(c => ({ label: c.name.split(' ')[0], value: c.score, color: c.color }));

export default function HealthEquityScreen() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#6366F1', '#8B5CF6', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Health Equity</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{mockData.communityName}</Text>
          <View style={styles.scoreRow}>
            <ScoreRing score={mockData.overallScore} size={100} color={colors.health.activity} />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>SDOH Score</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{mockData.overallScore}/100</Text>
              <Text style={[typography.body.sm, { color: colors.health.warning }]}>Grade: {mockData.equityGrade}</Text>
            </View>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="SDOH Categories" icon="analytics" iconColor="#6366F1" />
          {mockData.categories.map((cat, i) => (
            <View key={i} style={styles.categoryRow}>
              <View style={[styles.catIcon, { backgroundColor: cat.color + '18' }]}>
                <Ionicons name={cat.icon as any} size={16} color={cat.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{cat.name}</Text>
                <View style={[styles.catBar, { backgroundColor: cat.color + '20' }]}>
                  <View style={[styles.catBarFill, { width: `${cat.score}%`, backgroundColor: cat.color }]} />
                </View>
              </View>
              <Text style={[typography.body.md, { color: cat.color, fontWeight: '600', width: 40, textAlign: 'right' }]}>{cat.score}</Text>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="SDOH Radar" icon="pulse" iconColor="#8B5CF6" />
          <GlassCard style={{ alignItems: 'center' }}>
            <RadarChart data={radarData} size={200} />
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Recommended Interventions" icon="bulb" iconColor={colors.health.energy} />
          {mockData.interventions.map((int, i) => (
            <View key={i} style={styles.interventionCard}>
              <View style={[styles.intIcon, { backgroundColor: int.color + '18' }]}>
                <Ionicons name="flash" size={16} color={int.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{int.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{int.category} • Impact: {int.impact} • Cost: {int.cost}</Text>
              </View>
              <View style={[styles.impactBadge, { backgroundColor: int.impact === 'high' ? colors.health.success + '20' : colors.health.warning + '20' }]}>
                <Text style={[typography.body.xs, { color: int.impact === 'high' ? colors.health.success : colors.health.warning }]}>{int.impact}</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Community Resources" icon="location" iconColor={colors.primary} />
          {mockData.resources.map((r, i) => (
            <View key={i} style={styles.resourceCard}>
              <View style={[styles.resIcon, { backgroundColor: colors.primary + '18' }]}>
                <Ionicons name="location" size={16} color={colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{r.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{r.type} • {r.distance}</Text>
              </View>
              <Ionicons name="call" size={18} color={colors.primary} />
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Outcomes" icon="trending-up" iconColor={colors.health.calm} />
          {mockData.outcomes.map((o, i) => (
            <GlassCard key={i} style={{ marginBottom: 10 }}>
              <Text style={[typography.label.md, { color: colors.text.primary }]}>{o.intervention}</Text>
              <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 4 }]}>{o.metric}</Text>
              <View style={styles.outcomeRow}>
                <View style={styles.outcomeBox}>
                  <Text style={[typography.body.xs, { color: colors.text.muted }]}>Before</Text>
                  <Text style={[typography.metric.small, { color: colors.health.danger }]}>{o.before}%</Text>
                </View>
                <Ionicons name="arrow-forward" size={16} color={colors.text.muted} />
                <View style={styles.outcomeBox}>
                  <Text style={[typography.body.xs, { color: colors.text.muted }]}>After</Text>
                  <Text style={[typography.metric.small, { color: colors.health.success }]}>{o.after}%</Text>
                </View>
                <View style={[styles.improvementBadge, { backgroundColor: colors.health.success + '20' }]}>
                  <Ionicons name="trending-up" size={12} color={colors.health.success} />
                  <Text style={[typography.body.sm, { color: colors.health.success, fontWeight: '600' }]}>+{o.after - o.before}%</Text>
                </View>
              </View>
            </GlassCard>
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
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  categoryRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  catIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  catBar: { height: 6, borderRadius: 3, marginTop: 4, overflow: 'hidden' },
  catBarFill: { height: '100%', borderRadius: 3 },
  interventionCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border, gap: 10 },
  intIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  impactBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  resourceCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border, gap: 10 },
  resIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  outcomeRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8, gap: 10 },
  outcomeBox: { alignItems: 'center' },
  improvementBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, marginLeft: 'auto' },
});
