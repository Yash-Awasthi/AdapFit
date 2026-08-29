/**
 * Ambient Health — Premium Smart Home & Environment Monitoring
 * IoT integration, air quality, room conditions, sleep environment
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

const ROOM_CONDITIONS = [
  { room: 'Bedroom', temp: '21°C', humidity: '45%', aqi: 25, color: '#8B5CF6', icon: 'bed', score: 92 },
  { room: 'Living Room', temp: '22°C', humidity: '42%', aqi: 30, color: '#22C55E', icon: 'tv', score: 88 },
  { room: 'Office', temp: '23°C', humidity: '40%', aqi: 35, color: '#3B82F6', icon: 'laptop', score: 85 },
  { room: 'Kitchen', temp: '24°C', humidity: '50%', aqi: 45, color: '#F59E0B', icon: 'restaurant', score: 78 },
];

const ENVIRONMENT = [
  { label: 'UV Index', value: '3', status: 'Moderate', color: '#F59E0B', icon: 'sunny' },
  { label: 'Pollen Count', value: 'Low', status: 'Good', color: '#22C55E', icon: 'leaf' },
  { label: 'Noise Level', value: '35dB', status: 'Quiet', color: '#06B6D4', icon: 'volume-low' },
  { label: 'Light Level', value: '450 lux', status: 'Comfortable', color: '#8B5CF6', icon: 'sunny' },
];

export default function AmbientScreen() {
  return (
    <ScreenWrapper
      title="Ambient Health"
      subtitle="Smart home & environment"
      gradient={['#6366F1', '#8B5CF6']}
      rightAction={{ icon: 'settings', onPress: () => {} }}
    >
      {/* Environment Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={87} size={120} strokeWidth={8} color="#8B5CF6" label="AMBIENT" sublabel="Good" />
      </View>

      {/* Room Conditions */}
      <SectionHeaderPremium icon="home" iconColor="#8B5CF6" title="Room Conditions" />
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {ROOM_CONDITIONS.map((room, i) => (
          <GlassCard key={i} variant="light" style={styles.roomCard}>
            <View style={styles.roomHeader}>
              <View style={[styles.roomIcon, { backgroundColor: room.color + '15' }]}>
                <Ionicons name={room.icon as any} size={20} color={room.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.roomName}>{room.room}</Text>
                <Text style={styles.roomScore}>Score: {room.score}/100</Text>
              </View>
            </View>
            <View style={styles.roomStats}>
              <View style={styles.roomStat}>
                <Ionicons name="thermometer" size={14} color={colors.text.muted} />
                <Text style={styles.roomStatText}>{room.temp}</Text>
              </View>
              <View style={styles.roomStat}>
                <Ionicons name="water" size={14} color="#3B82F6" />
                <Text style={styles.roomStatText}>{room.humidity}</Text>
              </View>
              <View style={styles.roomStat}>
                <Ionicons name="leaf" size={14} color="#22C55E" />
                <Text style={styles.roomStatText}>AQI {room.aqi}</Text>
              </View>
            </View>
          </GlassCard>
        ))}
      </StaggeredList>

      {/* Outdoor Environment */}
      <SectionHeaderPremium icon="globe" iconColor="#06B6D4" title="Outdoor Conditions" />
      <View style={styles.envGrid}>
        {ENVIRONMENT.map((env, i) => (
          <GlassCard key={i} variant="light" style={styles.envCard}>
            <View style={[styles.envIcon, { backgroundColor: env.color + '15' }]}>
              <Ionicons name={env.icon as any} size={18} color={env.color} />
            </View>
            <Text style={[styles.envValue, { color: env.color }]}>{env.value}</Text>
            <Text style={styles.envLabel}>{env.label}</Text>
            <Text style={[styles.envStatus, { color: env.color }]}>{env.status}</Text>
          </GlassCard>
        ))}
      </View>

      {/* Sleep Environment */}
      <SectionHeaderPremium icon="moon" iconColor={colors.health.sleep} title="Sleep Environment" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {[
          { label: 'Temperature', value: '21°C', target: '18-22°C', met: true },
          { label: 'Humidity', value: '45%', target: '30-50%', met: true },
          { label: 'Noise', value: '30dB', target: '<35dB', met: true },
          { label: 'Light', value: '5 lux', target: '<10 lux', met: true },
        ].map((item, i) => (
          <View key={i} style={[styles.sleepRow, i < 3 && { borderBottomWidth: 1, borderBottomColor: colors.surface.divider }]}>
            <Text style={styles.sleepLabel}>{item.label}</Text>
            <Text style={[styles.sleepValue, { color: item.met ? '#22C55E' : '#EF4444' }]}>{item.value}</Text>
            <Text style={styles.sleepTarget}>Target: {item.target}</Text>
            <Ionicons name={item.met ? 'checkmark-circle' : 'close-circle'} size={16} color={item.met ? '#22C55E' : '#EF4444'} />
          </View>
        ))}
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Rooms
  roomCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  roomHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  roomIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  roomName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  roomScore: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  roomStats: { flexDirection: 'row', gap: spacing.xl },
  roomStat: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  roomStatText: { fontSize: 13, fontWeight: '600', color: colors.text.secondary },

  // Environment Grid
  envGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  envCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md) / 2, alignItems: 'center', paddingVertical: spacing.md },
  envIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  envValue: { fontSize: 18, fontWeight: '800' },
  envLabel: { fontSize: 11, color: colors.text.muted, marginTop: 2 },
  envStatus: { fontSize: 10, fontWeight: '600', marginTop: 2 },

  // Sleep Environment
  sleepRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md },
  sleepLabel: { flex: 1, fontSize: 14, color: colors.text.primary },
  sleepValue: { fontSize: 14, fontWeight: '700', width: 60, textAlign: 'right' },
  sleepTarget: { fontSize: 11, color: colors.text.muted, width: 80, textAlign: 'right', marginRight: spacing.sm },
});
