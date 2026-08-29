/**
 * Chronic Pain Management — Advanced Pain Tracking
 * Pain diary, flare tracking, treatment log, triggers, mood correlation.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { MiniLineChart, Sparkline } from '../../src/components/HealthCharts';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const painZones = [
  { name: 'Lower Back', level: 7, color: '#EF4444' },
  { name: 'Neck', level: 4, color: '#F97316' },
  { name: 'Left Knee', level: 5, color: '#F59E0B' },
  { name: 'Right Shoulder', level: 3, color: '#22C55E' },
];

const weeklyPain = [6, 5, 7, 4, 5, 3, 4];
const moodData = [5, 6, 4, 7, 6, 8, 7];

const treatments = [
  { name: 'Physical Therapy', type: 'Exercise', effectiveness: 75 },
  { name: 'Ibuprofen 400mg', type: 'Medication', effectiveness: 60 },
  { name: 'Heat Therapy', type: 'Self-Care', effectiveness: 80 },
  { name: 'Meditation', type: 'Mindfulness', effectiveness: 65 },
  { name: 'Yoga', type: 'Exercise', effectiveness: 70 },
];

const triggers = [
  { name: 'Poor Sleep', frequency: 12, icon: 'moon' },
  { name: 'Stress', frequency: 10, icon: 'flash' },
  { name: 'Sitting Too Long', frequency: 8, icon: 'desktop' },
  { name: 'Cold Weather', frequency: 6, icon: 'snow' },
];

const painScale = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];
const painColors = ['#22C55E', '#22C55E', '#84CC16', '#84CC16', '#EAB308', '#EAB308', '#F97316', '#F97316', '#EF4444', '#EF4444', '#DC2626'];

export default function ChronicPainV2Screen() {
  const [selectedPain, setSelectedPain] = useState(5);
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#F97316', '#EF4444', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Chronic Pain Management</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Pain Tracker</Text>
          <View style={styles.scoreRow}>
            <ScoreRing score={100 - (weeklyPain[weeklyPain.length - 1] * 10)} size={100} color={painColors[weeklyPain[weeklyPain.length - 1]]} />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Current Pain Level</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{weeklyPain[weeklyPain.length - 1]}/10</Text>
              <Text style={[typography.body.sm, { color: '#22C55E' }]}>Trending Downward</Text>
            </View>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Log Pain Level" icon="medical" iconColor={colors.health.heart} />
          <GlassCard>
            <View style={styles.painScale}>
              {painScale.map((p, i) => (
                <TouchableOpacity key={i} onPress={() => setSelectedPain(i)} style={[styles.painButton, { backgroundColor: selectedPain === i ? painColors[i] : colors.bg.elevated, borderColor: painColors[i] + '40' }]}>
                  <Text style={[typography.body.sm, { color: selectedPain === i ? '#fff' : colors.text.muted }]}>{p}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={[typography.body.sm, { color: colors.text.muted, textAlign: 'center', marginTop: 8 }]}>Tap to log your current pain level</Text>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Pain by Body Area" icon="body" iconColor={colors.health.heart} />
          {painZones.map((zone, i) => (
            <View key={i} style={styles.zoneRow}>
              <Text style={[typography.body.md, { flex: 1, color: colors.text.primary }]}>{zone.name}</Text>
              <Text style={[typography.body.sm, { color: zone.color, fontWeight: '600', marginRight: 8 }]}>{zone.level}/10</Text>
              <View style={[styles.painBar, { backgroundColor: zone.color + '20' }]}>
                <View style={[styles.painBarFill, { width: `${zone.level * 10}%`, backgroundColor: zone.color }]} />
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Weekly Trend" icon="trending-down" iconColor={colors.health.calm} />
          <GlassCard>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 }}>
              <View>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>Pain</Text>
                <MiniLineChart data={weeklyPain} color={colors.health.heart} height={40} width={120} />
              </View>
              <View>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>Mood</Text>
                <MiniLineChart data={moodData} color={colors.health.calm} height={40} width={120} />
              </View>
            </View>
            <Text style={[typography.body.xs, { color: colors.text.muted }]}>Lower pain correlates with better mood this week</Text>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Treatment Effectiveness" icon="medical" iconColor={colors.health.activity} />
          {treatments.map((t, i) => (
            <View key={i} style={styles.treatmentCard}>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{t.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{t.type}</Text>
              </View>
              <View style={styles.effContainer}>
                <View style={[styles.effBar, { backgroundColor: colors.health.success + '20' }]}>
                  <View style={[styles.effBarFill, { width: `${t.effectiveness}%`, backgroundColor: colors.health.success }]} />
                </View>
                <Text style={[typography.body.xs, { color: colors.health.success, marginTop: 2 }]}>{t.effectiveness}%</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Common Triggers" icon="warning" iconColor={colors.health.warning} />
          {triggers.map((t, i) => (
            <View key={i} style={styles.triggerRow}>
              <Ionicons name={t.icon as any} size={18} color={colors.health.warning} />
              <Text style={[typography.body.md, { flex: 1, color: colors.text.primary }]}>{t.name}</Text>
              <Text style={[typography.body.sm, { color: colors.text.muted }]}>{t.frequency}x this month</Text>
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
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  painScale: { flexDirection: 'row', justifyContent: 'space-between' },
  painButton: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center', borderWidth: 1.5 },
  zoneRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 10 },
  painBar: { width: 80, height: 8, borderRadius: 4, overflow: 'hidden' },
  painBarFill: { height: '100%', borderRadius: 4 },
  treatmentCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border },
  effContainer: { width: 80 },
  effBar: { height: 6, borderRadius: 3, overflow: 'hidden' },
  effBarFill: { height: '100%', borderRadius: 3 },
  triggerRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, gap: 12, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
});
