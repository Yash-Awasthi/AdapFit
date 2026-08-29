import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function PregnancyScreen() {
  const [activeTab, setActiveTab] = useState<'baby' | 'kick' | 'appointments' | 'tips'>('baby');

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Pregnancy Tracker</Text>
        <Text style={styles.headerSubtitle}>Week 24 — Third trimester approaching</Text>
      </View>

      <View style={styles.tabBar}>
        {(['baby', 'kick', 'appointments', 'tips'] as const).map(tab => (
          <TouchableOpacity key={tab} style={[styles.tab, activeTab === tab && styles.activeTab]} onPress={() => setActiveTab(tab)}>
            <Ionicons
              name={tab === 'baby' ? 'happy-outline' : tab === 'kick' ? 'footsteps-outline' : tab === 'appointments' ? 'calendar-outline' : 'bulb-outline'}
              size={20}
              color={activeTab === tab ? '#FFF' : '#94A3B8'}
            />
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'baby' && (
          <>
            <View style={styles.babyHero}>
              <Text style={styles.babySize}></Text>
              <Text style={styles.babySizeText}>Baby is the size of an ear of corn</Text>
              <Text style={styles.babyWeight}>~600g / 1.3 lbs</Text>
            </View>

            <Text style={styles.sectionTitle}>This Week's Milestones</Text>
            {['Eyes can open and close', 'Regular sleep/wake cycle', 'Viable outside the womb', 'Hearing is developing'].map((m, i) => (
              <View key={i} style={styles.milestoneCard}>
                <Ionicons name="checkmark-circle" size={20} color="#10B981" />
                <Text style={styles.milestoneText}>{m}</Text>
              </View>
            ))}

            <View style={styles.countdownCard}>
              <Text style={styles.countdownLabel}>Days Until Due Date</Text>
              <Text style={styles.countdownValue}>112</Text>
              <Text style={styles.countdownSub}>Due: November 15, 2026</Text>
            </View>
          </>
        )}

        {activeTab === 'kick' && (
          <>
            <View style={styles.kickHero}>
              <Text style={styles.kickCount}>12</Text>
              <Text style={styles.kickLabel}>Kicks counted today</Text>
              <Text style={styles.kickStatus}>Normal (target: 10 in 2 hours)</Text>
            </View>
            <TouchableOpacity style={styles.kickBtn}>
              <Text style={styles.kickBtnText}>Start Kick Counting</Text>
            </TouchableOpacity>
            <Text style={styles.sectionTitle}>Recent Sessions</Text>
            {[
              { date: 'Today', kicks: 12, duration: '15 min', status: 'Normal' },
              { date: 'Yesterday', kicks: 15, duration: '12 min', status: 'Normal' },
              { date: '2 days ago', kicks: 8, duration: '20 min', status: 'Low' },
            ].map((s, i) => (
              <View key={i} style={styles.sessionCard}>
                <Text style={styles.sessionDate}>{s.date}</Text>
                <Text style={styles.sessionKicks}>{s.kicks} kicks</Text>
                <Text style={[styles.sessionStatus, { color: s.status === 'Normal' ? '#10B981' : '#F59E0B' }]}>{s.status}</Text>
              </View>
            ))}
          </>
        )}

        {activeTab === 'appointments' && (
          <>
            <Text style={styles.sectionTitle}>Upcoming Appointments</Text>
            {[
              { week: 28, name: 'Third Trimester Start', tests: ['Blood type check', 'Antibodies screen'], date: 'Sep 12' },
              { week: 32, name: 'Growth Scan', tests: ['Ultrasound', 'Position check'], date: 'Oct 10' },
              { week: 36, name: 'Group B Strep Test', tests: ['GBS swab', 'Cervical check'], date: 'Nov 7' },
            ].map((a, i) => (
              <View key={i} style={styles.apptCard}>
                <View style={styles.apptLeft}>
                  <Text style={styles.apptWeek}>Week {a.week}</Text>
                  <Text style={styles.apptName}>{a.name}</Text>
                  <Text style={styles.apptTests}>{a.tests.join(', ')}</Text>
                </View>
                <Text style={styles.apptDate}>{a.date}</Text>
              </View>
            ))}
          </>
        )}

        {activeTab === 'tips' && (
          <>
            <Text style={styles.sectionTitle}>Week 24 Tips</Text>
            {['Eat fatty fish for baby\'s brain development', 'Stay hydrated — aim for 8-10 glasses/day', 'Sleep on your side for better blood flow', 'Start thinking about your birth plan'].map((tip, i) => (
              <View key={i} style={styles.tipCard}>
                <Ionicons name="bulb" size={18} color="#F59E0B" />
                <Text style={styles.tipText}>{tip}</Text>
              </View>
            ))}
            <Text style={styles.sectionTitle}>Warning Signs</Text>
            {['Severe abdominal pain', 'Heavy vaginal bleeding', 'Fluid leaking', 'Sudden severe swelling', 'Decreased fetal movement'].map((w, i) => (
              <View key={i} style={styles.warningCard}>
                <Ionicons name="warning" size={16} color="#EF4444" />
                <Text style={styles.warningText}>{w}</Text>
              </View>
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 16, backgroundColor: '#1E293B' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#F8FAFC' },
  headerSubtitle: { fontSize: 14, color: '#94A3B8', marginTop: 4 },
  tabBar: { flexDirection: 'row', backgroundColor: '#1E293B', paddingHorizontal: 16, paddingVertical: 8 },
  tab: { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: 8 },
  activeTab: { backgroundColor: '#EC4899' },
  tabText: { fontSize: 20 },
  activeTabText: { color: '#FFF' },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  babyHero: { alignItems: 'center', marginBottom: 20, backgroundColor: '#1E293B', borderRadius: 16, padding: 24 },
  babySize: { fontSize: 64 },
  babySizeText: { fontSize: 16, color: '#F8FAFC', fontWeight: 'bold', marginTop: 8 },
  babyWeight: { fontSize: 14, color: '#94A3B8', marginTop: 4 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  milestoneCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1E293B', borderRadius: 10, padding: 12, marginBottom: 8, gap: 10 },
  milestoneText: { fontSize: 14, color: '#F8FAFC', flex: 1 },
  countdownCard: { backgroundColor: '#1E293B', borderRadius: 16, padding: 20, alignItems: 'center', marginTop: 12 },
  countdownLabel: { fontSize: 14, color: '#94A3B8' },
  countdownValue: { fontSize: 48, fontWeight: 'bold', color: '#EC4899' },
  countdownSub: { fontSize: 13, color: '#64748B' },
  kickHero: { alignItems: 'center', backgroundColor: '#1E293B', borderRadius: 16, padding: 24, marginBottom: 16 },
  kickCount: { fontSize: 56, fontWeight: 'bold', color: '#F8FAFC' },
  kickLabel: { fontSize: 16, color: '#94A3B8', marginTop: 4 },
  kickStatus: { fontSize: 14, color: '#10B981', marginTop: 8 },
  kickBtn: { backgroundColor: '#EC4899', borderRadius: 12, padding: 16, alignItems: 'center', marginBottom: 20 },
  kickBtnText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  sessionCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sessionDate: { fontSize: 14, color: '#94A3B8', flex: 1 },
  sessionKicks: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC', flex: 1 },
  sessionStatus: { fontSize: 13, fontWeight: '600', flex: 1, textAlign: 'right' },
  apptCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between' },
  apptLeft: { flex: 1 },
  apptWeek: { fontSize: 12, color: '#EC4899', fontWeight: 'bold' },
  apptName: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC', marginTop: 2 },
  apptTests: { fontSize: 12, color: '#94A3B8', marginTop: 4 },
  apptDate: { fontSize: 14, color: '#94A3B8', fontWeight: '600' },
  tipCard: { flexDirection: 'row', backgroundColor: '#1E293B', borderRadius: 10, padding: 12, marginBottom: 8, gap: 10, alignItems: 'flex-start' },
  tipText: { fontSize: 14, color: '#F8FAFC', flex: 1 },
  warningCard: { flexDirection: 'row', backgroundColor: '#1E293B', borderRadius: 10, padding: 12, marginBottom: 8, gap: 8, alignItems: 'center', borderLeftWidth: 3, borderLeftColor: '#EF4444' },
  warningText: { fontSize: 14, color: '#EF4444', flex: 1 },
});
