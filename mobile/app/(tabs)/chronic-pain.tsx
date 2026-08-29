import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function ChronicPainScreen() {
  const [activeTab, setActiveTab] = useState<'diary' | 'triggers' | 'treatments' | 'cbt'>('diary');

  const painScale = [
    { level: 0, label: 'No pain', color: '#10B981' },
    { level: 3, label: 'Mild', color: '#FBBF24' },
    { level: 5, label: 'Moderate', color: '#F97316' },
    { level: 7, label: 'Severe', color: '#EF4444' },
    { level: 10, label: 'Unbearable', color: '#DC2626' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>💊 Chronic Pain Manager</Text>
        <Text style={styles.headerSubtitle}>Pain diary, triggers & relief tracking</Text>
      </View>

      <View style={styles.tabBar}>
        {(['diary', 'triggers', 'treatments', 'cbt'] as const).map(tab => (
          <TouchableOpacity key={tab} style={[styles.tab, activeTab === tab && styles.activeTab]} onPress={() => setActiveTab(tab)}>
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'diary' ? '📓' : tab === 'triggers' ? '🔍' : tab === 'treatments' ? '💉' : '🧠'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'diary' && (
          <>
            <Text style={styles.sectionTitle}>How's your pain today?</Text>
            <View style={styles.painScale}>
              {painScale.map(p => (
                <TouchableOpacity key={p.level} style={[styles.painBtn, { borderColor: p.color }]}>
                  <Text style={[styles.painLevel, { color: p.color }]}>{p.level}</Text>
                  <Text style={styles.painLabel}>{p.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.sectionTitle}>Recent Entries</Text>
            {[
              { date: 'Today', pain: 4, location: 'Lower back', type: 'Aching', mood: 6 },
              { date: 'Yesterday', pain: 6, location: 'Neck & shoulders', type: 'Sharp', mood: 4 },
              { date: '2 days ago', pain: 3, location: 'Lower back', type: 'Dull', mood: 7 },
            ].map((e, i) => (
              <View key={i} style={styles.diaryCard}>
                <View style={styles.diaryLeft}>
                  <Text style={styles.diaryDate}>{e.date}</Text>
                  <Text style={styles.diaryLocation}>{e.location} — {e.type}</Text>
                </View>
                <View style={styles.diaryRight}>
                  <Text style={[styles.diaryPain, { color: e.pain <= 3 ? '#10B981' : e.pain <= 6 ? '#F59E0B' : '#EF4444' }]}>{e.pain}/10</Text>
                  <Text style={styles.diaryMood}>Mood: {e.mood}/10</Text>
                </View>
              </View>
            ))}
          </>
        )}

        {activeTab === 'triggers' && (
          <>
            <Text style={styles.sectionTitle}>Top Pain Triggers</Text>
            {[
              { trigger: 'Poor sleep', rate: 78, avg_pain: 6.2 },
              { trigger: 'Stress', rate: 65, avg_pain: 5.8 },
              { trigger: 'Weather changes', rate: 52, avg_pain: 5.1 },
              { trigger: 'Prolonged sitting', rate: 45, avg_pain: 4.9 },
            ].map((t, i) => (
              <View key={i} style={styles.triggerCard}>
                <Text style={styles.triggerName}>{t.trigger}</Text>
                <View style={styles.triggerBar}>
                  <View style={[styles.triggerFill, { width: `${t.rate}%` }]} />
                </View>
                <Text style={styles.triggerStats}>{t.rate}% of high-pain days | Avg pain: {t.avg_pain}</Text>
              </View>
            ))}
          </>
        )}

        {activeTab === 'treatments' && (
          <>
            <Text style={styles.sectionTitle}>Treatment Effectiveness</Text>
            {[
              { name: 'Physical therapy', effectiveness: 72, uses: 24 },
              { name: 'Heat therapy', effectiveness: 65, uses: 18 },
              { name: 'Meditation', effectiveness: 58, uses: 12 },
              { name: 'Medication', effectiveness: 45, uses: 30 },
            ].map((t, i) => (
              <View key={i} style={styles.treatCard}>
                <Text style={styles.treatName}>{t.name}</Text>
                <View style={styles.treatBar}>
                  <View style={[styles.treatFill, { width: `${t.effectiveness}%` }]} />
                </View>
                <Text style={styles.treatStats}>{t.effectiveness}% relief | Used {t.uses} times</Text>
              </View>
            ))}
          </>
        )}

        {activeTab === 'cbt' && (
          <>
            <Text style={styles.sectionTitle}>CBT Pain Management Techniques</Text>
            {[
              { name: 'Thought Challenging', desc: 'Challenge catastrophizing thoughts about pain', duration: '10 min', evidence: 'Strong' },
              { name: 'Pacing', desc: 'Break activities into manageable chunks', duration: 'Ongoing', evidence: 'Strong' },
              { name: 'Mindful Breathing', desc: 'Focus on breath to reduce pain perception', duration: '5 min', evidence: 'Moderate' },
              { name: 'Body Scan', desc: 'Progressive relaxation to reduce tension', duration: '15 min', evidence: 'Moderate' },
            ].map((t, i) => (
              <View key={i} style={styles.cbtCard}>
                <View style={styles.cbtHeader}>
                  <Text style={styles.cbtName}>{t.name}</Text>
                  <Text style={styles.cbtDuration}>{t.duration}</Text>
                </View>
                <Text style={styles.cbtDesc}>{t.desc}</Text>
                <Text style={styles.cbtEvidence}>Evidence: {t.evidence}</Text>
                <TouchableOpacity style={styles.cbtStartBtn}>
                  <Text style={styles.cbtStartText}>▶ Start Exercise</Text>
                </TouchableOpacity>
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
  activeTab: { backgroundColor: '#EF4444' },
  tabText: { fontSize: 20 },
  activeTabText: { color: '#FFF' },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  painScale: { flexDirection: 'row', gap: 6, marginBottom: 20 },
  painBtn: { flex: 1, alignItems: 'center', backgroundColor: '#1E293B', borderRadius: 10, padding: 10, borderWidth: 2 },
  painLevel: { fontSize: 22, fontWeight: 'bold' },
  painLabel: { fontSize: 9, color: '#94A3B8', marginTop: 2 },
  diaryCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between' },
  diaryLeft: { flex: 1 },
  diaryDate: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  diaryLocation: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  diaryRight: { alignItems: 'flex-end' },
  diaryPain: { fontSize: 20, fontWeight: 'bold' },
  diaryMood: { fontSize: 12, color: '#64748B', marginTop: 2 },
  triggerCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 10 },
  triggerName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  triggerBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 6 },
  triggerFill: { height: '100%', backgroundColor: '#EF4444', borderRadius: 4 },
  triggerStats: { fontSize: 12, color: '#94A3B8' },
  treatCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 10 },
  treatName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  treatBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 6 },
  treatFill: { height: '100%', backgroundColor: '#10B981', borderRadius: 4 },
  treatStats: { fontSize: 12, color: '#94A3B8' },
  cbtCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 10 },
  cbtHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  cbtName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC' },
  cbtDuration: { fontSize: 13, color: '#3B82F6', fontWeight: '600' },
  cbtDesc: { fontSize: 13, color: '#94A3B8', marginBottom: 4 },
  cbtEvidence: { fontSize: 12, color: '#64748B', marginBottom: 8 },
  cbtStartBtn: { backgroundColor: '#3B82F6', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 16, alignSelf: 'flex-start' },
  cbtStartText: { color: '#FFF', fontWeight: 'bold', fontSize: 13 },
});
