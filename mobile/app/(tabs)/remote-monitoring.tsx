/**
 * Remote Monitoring — Premium IoT Device Dashboard
 * Vital trends, connected devices, alert management
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
import { MetricCardWithChart } from '../../src/components/InteractiveCharts';
import { StaggeredList } from '../../src/components/AnimationSystem';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const DEVICES = [
  { id: 1, name: 'Blood Pressure Monitor', type: 'bp', icon: 'pulse', color: '#EF4444', status: 'connected', lastReading: '122/78', time: '2h ago' },
  { id: 2, name: 'Glucose Meter', type: 'glucose', icon: 'water', color: '#22C55E', status: 'connected', lastReading: '105 mg/dL', time: '4h ago' },
  { id: 3, name: 'Pulse Oximeter', type: 'spo2', icon: 'heart', color: '#3B82F6', status: 'disconnected', lastReading: '97%', time: '1d ago' },
  { id: 4, name: 'Smart Scale', type: 'weight', icon: 'scale', color: '#8B5CF6', status: 'connected', lastReading: '74.5 kg', time: '8h ago' },
];

const VITALS = [
  { title: 'Blood Pressure', value: '122/78', change: '-3%', changeType: 'down' as const, data: [128, 125, 124, 122, 123, 121, 122], color: '#EF4444', icon: 'pulse' },
  { title: 'Heart Rate', value: '72 bpm', change: '-2%', changeType: 'down' as const, data: [74, 73, 72, 71, 72, 73, 72], color: '#22C55E', icon: 'heart' },
  { title: 'Blood Glucose', value: '105 mg/dL', change: '-5%', changeType: 'down' as const, data: [115, 112, 110, 108, 106, 105, 105], color: '#F59E0B', icon: 'water' },
  { title: 'SpO2', value: '97%', change: '0%', changeType: 'flat' as const, data: [97, 96, 97, 98, 97, 97, 97], color: '#3B82F6', icon: 'fitness' },
];

export default function RemoteMonitoringScreen() {
  return (
    <ScreenWrapper
      title="Remote Monitoring"
      subtitle="Connected health devices"
      gradient={['#06B6D4', '#3B82F6']}
      rightAction={{ icon: 'add', onPress: () => {} }}
    >
      {/* Health Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={88} size={120} strokeWidth={8} color="#06B6D4" label="MONITORING" sublabel="Good" />
      </View>

      {/* Connected Devices */}
      <SectionHeaderPremium icon="watch" iconColor="#06B6D4" title="Connected Devices" action={{ label: 'Add Device', onPress: () => {} }} />
      <StaggeredList staggerDelay={80} animationType="slideIn">
        {DEVICES.map(device => (
          <GlassCard key={device.id} variant="light" style={styles.deviceCard}>
            <View style={styles.deviceRow}>
              <View style={[styles.deviceIcon, { backgroundColor: device.color + '15' }]}>
                <Ionicons name={device.icon as any} size={20} color={device.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.deviceName}>{device.name}</Text>
                <Text style={styles.deviceReading}>{device.lastReading} • {device.time}</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: device.status === 'connected' ? '#22C55E15' : '#F59E0B15' }]}>
                <View style={[styles.statusDot, { backgroundColor: device.status === 'connected' ? '#22C55E' : '#F59E0B' }]} />
                <Text style={[styles.statusText, { color: device.status === 'connected' ? '#22C55E' : '#F59E0B' }]}>{device.status}</Text>
              </View>
            </View>
          </GlassCard>
        ))}
      </StaggeredList>

      {/* Vital Trends */}
      <SectionHeaderPremium icon="trending-up" iconColor="#22C55E" title="Vital Trends" />
      <View style={{ paddingHorizontal: spacing.screenPadding }}>
        {VITALS.map((vital, i) => (
          <MetricCardWithChart key={i} {...vital} />
        ))}
      </View>

      {/* Alerts */}
      <SectionHeaderPremium icon="alert" iconColor="#EF4444" title="Recent Alerts" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={styles.alertRow}>
          <View style={[styles.alertIcon, { backgroundColor: '#22C55E15' }]}>
            <Ionicons name="checkmark-circle" size={18} color="#22C55E" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.alertTitle}>All vitals within normal range</Text>
            <Text style={styles.alertTime}>Last checked: 2 hours ago</Text>
          </View>
        </View>
      </GlassCard>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },

  // Devices
  deviceCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  deviceRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  deviceIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  deviceName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  deviceReading: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  statusDot: { width: 6, height: 6, borderRadius: 3 },
  statusText: { fontSize: 11, fontWeight: '600' },

  // Alerts
  alertRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  alertIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  alertTitle: { fontSize: 14, fontWeight: '600', color: colors.text.primary },
  alertTime: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
});
