/**
 * Family & Caregiver Mode — Monitor family members' health
 */
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets, glass } from '../../src/theme';

import { API_V1 as API } from '../../src/services/config';
function MemberCard({ member, onPress }: { member: any; onPress: () => void }) {
  const relationshipColors: Record<string, string> = { parent: colors.health.heart, child: colors.health.sleep, spouse: '#EC4899', sibling: colors.health.energy, self: colors.primary };
  const color = relationshipColors[member.relationship] || colors.primary;
  return (
    <TouchableOpacity style={[ns.memberCard, { borderLeftColor: color }]} onPress={onPress}>
      <View style={[ns.memberAvatar, { backgroundColor: color + '20' }]}>
        <Ionicons
          name={member.relationship === 'parent' ? 'person' : member.relationship === 'child' ? 'happy-outline' : member.relationship === 'spouse' ? 'heart' : 'person-outline'}
          size={20}
          color={color}
        />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[typography.label.lg as any, { color: colors.text.primary }]}>{member.name}</Text>
        <Text style={[typography.body.xs as any, { color }]}>{member.relationship}</Text>
        <Text style={typography.body.xs as any}>Age: {member.age}</Text>
      </View>
      {member.is_caregiver && <View style={ns.caregiverBadge}><Text style={ns.caregiverText}>Caregiver</Text></View>}
      <Ionicons name="chevron-forward" size={18} color={colors.text.muted} />
    </TouchableOpacity>
  );
}

export default function FamilyScreen() {
  const [dashboard, setDashboard] = useState<any>({});
  const [elderly, setElderly] = useState<any>({});
  const [child, setChild] = useState<any>({});

  useEffect(() => {
    // Demo data
    setDashboard({
      total_members: 4, caregivers: 1, dependents: 3, unread_alerts: 2,
      members: [
        { user_id: 'u1', name: 'You', relationship: 'self', age: 35, is_caregiver: true },
        { user_id: 'u2', name: 'Mom', relationship: 'parent', age: 65, is_caregiver: false },
        { user_id: 'u3', name: 'Dad', relationship: 'parent', age: 68, is_caregiver: false },
        { user_id: 'u4', name: 'Sarah', relationship: 'child', age: 8, is_caregiver: false },
      ],
    });
    setElderly({ medication_adherence: 92, activity_level: 'moderate', sleep_quality: 7, mood_trend: 'stable', fall_risk: 'low', alerts: ['Medication due in 2 hours', 'Blood pressure check recommended'] });
    setChild({ activity_minutes_today: 45, screen_time_today: 120, sleep_hours_last_night: 9.5, nutrition_score: 82 });
  }, []);

  return (
    <ScrollView style={ns.container}>
      <View style={ns.header}>
        <Text style={typography.heading.h1 as any}>Family</Text>
        <Text style={typography.body.sm as any}>Keep your loved ones healthy</Text>
      </View>

      {/* Quick Stats */}
      <View style={ns.statsRow}>
        <View style={[ns.statCard, glass.light]}>
          <Text style={[typography.metric.large as any, { color: colors.primary }]}>{dashboard.total_members || 0}</Text>
          <Text style={typography.body.xs as any}>Members</Text>
        </View>
        <View style={[ns.statCard, glass.light]}>
          <Text style={[typography.metric.large as any, { color: colors.health.heart }]}>{dashboard.unread_alerts || 0}</Text>
          <Text style={typography.body.xs as any}>Alerts</Text>
        </View>
        <View style={[ns.statCard, glass.light]}>
          <Text style={[typography.metric.large as any, { color: colors.health.calm }]}>{dashboard.caregivers || 0}</Text>
          <Text style={typography.body.xs as any}>Caregivers</Text>
        </View>
      </View>

      {/* Family Members */}
      <View style={[presets.card, { marginHorizontal: spacing.lg, marginBottom: spacing.lg }]}>
        <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Family Members</Text>
        {(dashboard.members || []).map((m: any) => (
          <MemberCard key={m.user_id} member={m} onPress={() => Alert.alert(m.name, `Relationship: ${m.relationship}\nAge: ${m.age}`)} />
        ))}
        <TouchableOpacity style={[presets.buttonSecondary, { marginTop: spacing.md }]}>
          <Ionicons name="person-add" size={16} color={colors.primary} />
          <Text style={[typography.label.sm as any, { color: colors.primary }]}>Invite Family Member</Text>
        </TouchableOpacity>
      </View>

      {/* Elderly Monitoring */}
      {elderly.medication_adherence && (
        <View style={[glass.light, { marginHorizontal: spacing.lg, padding: spacing.lg, marginBottom: spacing.lg }]}>
          <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Elderly Care Dashboard</Text>
          <View style={ns.monitorRow}>
            <View style={ns.monitorItem}>
              <Text style={[typography.metric.large as any, { color: elderly.medication_adherence >= 90 ? colors.health.calm : colors.health.stress }]}>{elderly.medication_adherence}%</Text>
              <Text style={typography.body.xs as any}>Med Adherence</Text>
            </View>
            <View style={ns.monitorItem}>
              <Text style={[typography.metric.large as any, { color: colors.health.sleep }]}>{elderly.sleep_quality}/10</Text>
              <Text style={typography.body.xs as any}>Sleep Quality</Text>
            </View>
            <View style={ns.monitorItem}>
              <Text style={[typography.metric.large as any, { color: colors.health.calm }]}>{elderly.fall_risk}</Text>
              <Text style={typography.body.xs as any}>Fall Risk</Text>
            </View>
          </View>
          {elderly.alerts?.map((a: string, i: number) => (
            <View key={i} style={ns.alertRow}>
              <Ionicons name="alert-circle" size={16} color={colors.health.stress} />
              <Text style={[typography.body.sm as any, { flex: 1 }]}>{a}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Child Health */}
      {child.activity_minutes_today && (
        <View style={[glass.light, { marginHorizontal: spacing.lg, padding: spacing.lg, marginBottom: spacing.lg }]}>
          <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Child Activity</Text>
          <View style={ns.monitorRow}>
            <View style={ns.monitorItem}>
              <Text style={[typography.metric.large as any, { color: colors.health.calm }]}>{child.activity_minutes_today}m</Text>
              <Text style={typography.body.xs as any}>Active Time</Text>
            </View>
            <View style={ns.monitorItem}>
              <Text style={[typography.metric.large as any, { color: child.screen_time_today > 120 ? colors.health.stress : colors.primary }]}>{child.screen_time_today}m</Text>
              <Text style={typography.body.xs as any}>Screen Time</Text>
            </View>
            <View style={ns.monitorItem}>
              <Text style={[typography.metric.large as any, { color: colors.health.sleep }]}>{child.sleep_hours_last_night}h</Text>
              <Text style={typography.body.xs as any}>Sleep</Text>
            </View>
          </View>
        </View>
      )}

      {/* Emergency SOS */}
      <TouchableOpacity style={[ns.sosButton, { marginHorizontal: spacing.lg }]}>
        <Ionicons name="alert-circle" size={24} color="#FFF" />
        <Text style={[typography.heading.h4 as any, { color: '#FFF' }]}>Emergency Family Alert</Text>
      </TouchableOpacity>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const ns = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  header: { padding: spacing.screenPadding, paddingTop: 50, paddingBottom: spacing.md },
  statsRow: { flexDirection: 'row', gap: spacing.sm, marginHorizontal: spacing.lg, marginBottom: spacing.lg },
  statCard: { flex: 1, padding: spacing.md, borderRadius: radius.md, alignItems: 'center' },
  memberCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.input, padding: spacing.md, borderRadius: radius.md, marginBottom: spacing.sm, borderLeftWidth: 3, gap: spacing.md },
  memberAvatar: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  caregiverBadge: { backgroundColor: colors.primary + '20', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  caregiverText: { fontSize: 10, color: colors.primary, fontWeight: '700' },
  monitorRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.md },
  monitorItem: { alignItems: 'center' },
  alertRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, padding: spacing.sm, backgroundColor: colors.health.stress + '10', borderRadius: radius.sm, marginBottom: spacing.xs },
  sosButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, backgroundColor: colors.health.heart, padding: spacing.lg, borderRadius: radius.md, marginBottom: spacing.xl },
});
