/**
 * Circadian Rhythm — Premium Chronotype & Sleep-Wake Optimization
 * Chronotype assessment, light exposure tracking, energy predictions
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../../src/theme';
const { width: SCREEN_WIDTH } = Dimensions.get('window');
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { InteractiveBarChart } from '../../src/components/InteractiveCharts';

const CHRONOTYPES = [
  { type: 'Lion', emoji: '🦁', description: 'Early riser, peak energy morning', color: '#F59E0B', bestTime: '5:30 AM - 9:00 PM' },
  { type: 'Bear', emoji: '🐻', description: 'Follows solar cycle, most common', color: '#22C55E', bestTime: '7:00 AM - 11:00 PM' },
  { type: 'Wolf', emoji: '🐺', description: 'Night owl, peak energy evening', color: '#8B5CF6', bestTime: '12:00 PM - 12:00 AM' },
  { type: 'Dolphin', emoji: '🐬', description: 'Light sleeper, irregular patterns', color: '#3B82F6', bestTime: '6:00 AM - 10:00 PM' },
];

const ENERGY_DATA = [
  { value: 85, label: '6AM', color: '#22C55E' },
  { value: 95, label: '9AM', color: '#22C55E' },
  { value: 90, label: '12PM', color: '#22C55E' },
  { value: 70, label: '3PM', color: '#F59E0B' },
  { value: 80, label: '6PM', color: '#22C55E' },
  { value: 60, label: '9PM', color: '#F59E0B' },
  { value: 30, label: '12AM', color: '#EF4444' },
];

export default function CircadianScreen() {
  const [selectedChronotype, setSelectedChronotype] = useState(1); // Bear

  return (
    <ScreenWrapper
      title="Circadian Rhythm"
      subtitle="Optimize your body clock"
      gradient={['#8B5CF6', '#6366F1']}
      rightAction={{ icon: 'settings', onPress: () => {} }}
    >
      {/* Chronotype */}
      <SectionHeaderPremium icon="compass" iconColor="#8B5CF6" title="Your Chronotype" />
      <View style={styles.chronotypeGrid}>
        {CHRONOTYPES.map((ct, i) => (
          <TouchableOpacity
            key={i}
            style={[styles.chronotypeCard, selectedChronotype === i && { borderColor: ct.color + '80', backgroundColor: ct.color + '10' }]}
            onPress={() => setSelectedChronotype(i)}
          >
            <Text style={styles.chronotypeEmoji}>{ct.emoji}</Text>
            <Text style={[styles.chronotypeType, selectedChronotype === i && { color: ct.color }]}>{ct.type}</Text>
            <Text style={styles.chronotypeDesc} numberOfLines={2}>{ct.description}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Energy Curve */}
      <SectionHeaderPremium icon="trending-up" iconColor="#22C55E" title="Energy Curve" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <InteractiveBarChart data={ENERGY_DATA} height={160} showValues />
        <Text style={styles.energyInsight}>💡 Your peak focus hours are 9-11 AM. Schedule deep work here.</Text>
      </GlassCard>

      {/* Light Exposure */}
      <SectionHeaderPremium icon="sunny" iconColor="#F59E0B" title="Light Exposure" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={styles.lightRow}>
          <View style={styles.lightStat}>
            <Ionicons name="sunny" size={24} color="#F59E0B" />
            <Text style={styles.lightValue}>4.2h</Text>
            <Text style={styles.lightLabel}>Outdoor Light</Text>
          </View>
          <View style={styles.lightStat}>
            <Ionicons name="phone-portrait" size={24} color="#3B82F6" />
            <Text style={styles.lightValue}>6.5h</Text>
            <Text style={styles.lightLabel}>Screen Time</Text>
          </View>
          <View style={styles.lightStat}>
            <Ionicons name="moon" size={24} color="#8B5CF6" />
            <Text style={styles.lightValue}>2h</Text>
            <Text style={styles.lightLabel}>Dark Exposure</Text>
          </View>
        </View>
        <ProgressBarPremium value={4.2} max={8} color="#F59E0B" height={6} showLabel label="Daily Light Target" />
      </GlassCard>

      {/* Optimal Schedule */}
      <SectionHeaderPremium icon="calendar" iconColor={colors.health.calm} title="Optimal Schedule" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {[
          { time: '6:00 AM', activity: 'Wake + Sunlight', icon: 'sunny', color: '#F59E0B' },
          { time: '7:00 AM', activity: 'Exercise', icon: 'fitness', color: '#22C55E' },
          { time: '9:00 AM', activity: 'Deep Work', icon: 'bulb', color: '#3B82F6' },
          { time: '12:00 PM', activity: 'Lunch + Walk', icon: 'restaurant', color: '#F97316' },
          { time: '3:00 PM', activity: 'Light Tasks', icon: 'document', color: '#8B5CF6' },
          { time: '6:00 PM', activity: 'Dinner', icon: 'restaurant', color: '#F97316' },
          { time: '9:00 PM', activity: 'Wind Down', icon: 'moon', color: '#6366F1' },
          { time: '10:30 PM', activity: 'Sleep', icon: 'bed', color: '#312E81' },
        ].map((item, i) => (
          <View key={i} style={[styles.scheduleItem, i < 7 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <Text style={styles.scheduleTime}>{item.time}</Text>
            <View style={[styles.scheduleIcon, { backgroundColor: item.color + '15' }]}>
              <Ionicons name={item.icon as any} size={14} color={item.color} />
            </View>
            <Text style={styles.scheduleActivity}>{item.activity}</Text>
          </View>
        ))}
      </GlassCard>

      {/* Tips */}
      <GlassCard variant="primary" style={styles.sectionCard}>
        <View style={styles.tipRow}>
          <Ionicons name="bulb" size={20} color={colors.primary} />
          <View style={{ flex: 1 }}>
            <Text style={styles.tipTitle}>Circadian Tip</Text>
            <Text style={styles.tipText}>Get 10 minutes of sunlight within 30 minutes of waking to anchor your circadian rhythm.</Text>
          </View>
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Chronotype
  chronotypeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  chronotypeCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md) / 2, backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.lg, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
  chronotypeEmoji: { fontSize: 32, marginBottom: spacing.xs },
  chronotypeType: { fontSize: 16, fontWeight: '700', color: colors.text.primary },
  chronotypeDesc: { fontSize: 11, color: colors.text.muted, textAlign: 'center', marginTop: 4 },

  // Energy
  energyInsight: { fontSize: 12, color: colors.text.muted, marginTop: spacing.md, lineHeight: 18 },

  // Light
  lightRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.lg },
  lightStat: { alignItems: 'center' },
  lightValue: { fontSize: 18, fontWeight: '800', color: colors.text.primary, marginTop: 4 },
  lightLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },

  // Schedule
  scheduleItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  scheduleTime: { fontSize: 13, fontWeight: '600', color: colors.text.muted, width: 60 },
  scheduleIcon: { width: 28, height: 28, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
  scheduleActivity: { fontSize: 14, fontWeight: '600', color: colors.text.primary, flex: 1 },

  // Tips
  tipRow: { flexDirection: 'row', gap: spacing.md },
  tipTitle: { fontSize: 14, fontWeight: '700', color: colors.text.primary, marginBottom: 4 },
  tipText: { fontSize: 13, color: colors.text.secondary, lineHeight: 18 },
});
