/**
 * Health Calendar — Menstrual cycle tracker, appointments, medications
 */
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets, glass } from '../../src/theme';

const API = 'http://localhost:8000/api/v1';

export default function HealthCalendarScreen() {
  const [predictions, setPredictions] = useState<any>({});
  const [summary, setSummary] = useState<any>({});
  const [appointments, setAppointments] = useState<any[]>([]);
  const [medications, setMedications] = useState<any[]>([]);
  const [tab, setTab] = useState<'cycle' | 'appointments' | 'medications'>('cycle');

  useEffect(() => {
    fetch(`${API}/calendar/cycle/predictions`).then(r => r.ok ? r.json() : null).then(setPredictions).catch(() => {});
    fetch(`${API}/calendar/cycle/summary`).then(r => r.ok ? r.json() : null).then(setSummary).catch(() => {});
    fetch(`${API}/calendar/appointments/upcoming`).then(r => r.ok ? r.json() : null).then(d => setAppointments(d?.appointments || [])).catch(() => {});
    fetch(`${API}/calendar/medications`).then(r => r.ok ? r.json() : null).then(d => setMedications(d?.medications || [])).catch(() => {});
  }, []);

  return (
    <ScrollView style={ns.container}>
      <View style={ns.header}>
        <Text style={typography.heading.h1 as any}>Health Calendar</Text>
        <Text style={typography.body.sm as any}>Track cycles, appointments & medications</Text>
      </View>

      {/* Tab Bar */}
      <View style={ns.tabBar}>
        {[{ key: 'cycle', label: 'Cycle' }, { key: 'appointments', label: 'Appointments' }, { key: 'medications', label: 'Meds' }].map(t => (
          <TouchableOpacity key={t.key} style={[ns.tab, tab === t.key && ns.tabActive]} onPress={() => setTab(t.key as any)}>
            <Text style={[ns.tabText, tab === t.key && ns.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {tab === 'cycle' && (
        <>
          {/* Cycle Summary */}
          {summary.total_cycles > 0 && (
            <View style={[glass.light, { marginHorizontal: spacing.lg, padding: spacing.lg, marginBottom: spacing.lg }]}>
              <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Cycle Summary</Text>
              <View style={ns.summaryRow}>
                <View style={ns.summaryItem}>
                  <Text style={[typography.metric.large as any, { color: colors.health.heart }]}>{summary.average_cycle_length || 28}</Text>
                  <Text style={typography.body.xs as any}>Avg Cycle</Text>
                </View>
                <View style={ns.summaryItem}>
                  <Text style={[typography.metric.large as any, { color: colors.health.sleep }]}>{summary.average_period_length || 5}</Text>
                  <Text style={typography.body.xs as any}>Avg Period</Text>
                </View>
                <View style={ns.summaryItem}>
                  <Text style={[typography.metric.large as any, { color: summary.regularity === 'regular' ? colors.health.calm : colors.health.stress }]}>
                    {summary.regularity || 'N/A'}
                  </Text>
                  <Text style={typography.body.xs as any}>Regularity</Text>
                </View>
              </View>
            </View>
          )}

          {/* Predictions */}
          {predictions.predictions?.length > 0 && (
            <View style={[presets.card, { marginHorizontal: spacing.lg, marginBottom: spacing.lg }]}>
              <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Upcoming Predictions</Text>
              {predictions.predictions.slice(0, 3).map((p: any, i: number) => (
                <View key={i} style={ns.predictionRow}>
                  <View style={[ns.predictionDot, { backgroundColor: colors.health.heart }]} />
                  <View style={{ flex: 1 }}>
                    <Text style={[typography.label.sm as any]}>Period #{p.cycle}</Text>
                    <Text style={typography.body.xs as any}>{p.predicted_start} - {p.predicted_end}</Text>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={[typography.body.xs as any, { color: colors.health.sleep }]}>Ovulation: {p.ovulation_date}</Text>
                    <Text style={[typography.body.xs as any, { color: colors.health.calm }]}>Fertile: {p.fertile_window?.start}</Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* Log Period Button */}
          <TouchableOpacity style={[presets.buttonPrimary, { marginHorizontal: spacing.lg, marginBottom: spacing.lg }]}>
            <Ionicons name="add-circle" size={18} color="#FFF" />
            <Text style={[typography.label.lg as any, { color: '#FFF' }]}>Log Period</Text>
          </TouchableOpacity>
        </>
      )}

      {tab === 'appointments' && (
        <View style={[presets.card, { marginHorizontal: spacing.lg, marginBottom: spacing.lg }]}>
          <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Upcoming Appointments</Text>
          {appointments.length === 0 ? (
            <Text style={[typography.body.sm as any, { color: colors.text.muted, textAlign: 'center', padding: spacing.xl }]}>No upcoming appointments</Text>
          ) : appointments.map((a, i) => (
            <View key={i} style={ns.appointmentRow}>
              <Ionicons name="calendar" size={18} color={colors.primary} />
              <View style={{ flex: 1 }}>
                <Text style={[typography.label.sm as any]}>{a.title}</Text>
                <Text style={typography.body.xs as any}>{a.date} at {a.time}</Text>
              </View>
              {a.doctor && <Text style={[typography.body.xs as any, { color: colors.text.muted }]}>{a.doctor}</Text>}
            </View>
          ))}
          <TouchableOpacity style={[presets.buttonSecondary, { marginTop: spacing.md }]}>
            <Ionicons name="add" size={16} color={colors.primary} />
            <Text style={[typography.label.sm as any, { color: colors.primary }]}>Add Appointment</Text>
          </TouchableOpacity>
        </View>
      )}

      {tab === 'medications' && (
        <View style={[presets.card, { marginHorizontal: spacing.lg, marginBottom: spacing.lg }]}>
          <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Medication Schedule</Text>
          {medications.length === 0 ? (
            <Text style={[typography.body.sm as any, { color: colors.text.muted, textAlign: 'center', padding: spacing.xl }]}>No medications scheduled</Text>
          ) : medications.map((m, i) => (
            <View key={i} style={ns.medRow}>
              <View style={[ns.medIcon, { backgroundColor: colors.health.sleep + '20' }]}>
                <Ionicons name="medical" size={18} color={colors.health.sleep} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.label.sm as any]}>{m.name}</Text>
                <Text style={typography.body.xs as any}>{m.dosage} — {m.times?.join(', ')}</Text>
              </View>
              <TouchableOpacity style={ns.takeButton}>
                <Ionicons name="checkmark" size={16} color="#FFF" />
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const ns = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  header: { padding: spacing.screenPadding, paddingTop: 50, paddingBottom: spacing.md },
  tabBar: { flexDirection: 'row', marginHorizontal: spacing.lg, marginBottom: spacing.lg, backgroundColor: colors.bg.card, borderRadius: radius.md, padding: 4 },
  tab: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: radius.sm },
  tabActive: { backgroundColor: colors.health.heart },
  tabText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  tabTextActive: { color: '#FFF' },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-around' },
  summaryItem: { alignItems: 'center' },
  predictionRow: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, backgroundColor: colors.bg.input, borderRadius: radius.sm, marginBottom: spacing.sm, gap: spacing.md },
  predictionDot: { width: 10, height: 10, borderRadius: 5 },
  appointmentRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md, backgroundColor: colors.bg.input, borderRadius: radius.sm, marginBottom: spacing.sm },
  medRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, padding: spacing.md, backgroundColor: colors.bg.input, borderRadius: radius.sm, marginBottom: spacing.sm },
  medIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  takeButton: { width: 32, height: 32, borderRadius: 16, backgroundColor: colors.health.calm, justifyContent: 'center', alignItems: 'center' },
});
