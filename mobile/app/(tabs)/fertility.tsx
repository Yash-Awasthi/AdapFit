import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function FertilityScreen() {
  const [activeTab, setActiveTab] = useState<'cycle' | 'log' | 'insights' | 'predict'>('cycle');

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🌸 Fertility Tracker</Text>
        <Text style={styles.headerSubtitle}>Cycle day 14 — Ovulation window</Text>
      </View>

      <View style={styles.tabBar}>
        {(['cycle', 'log', 'insights', 'predict'] as const).map(tab => (
          <TouchableOpacity key={tab} style={[styles.tab, activeTab === tab && styles.activeTab]} onPress={() => setActiveTab(tab)}>
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'cycle' ? '🔄' : tab === 'log' ? '📝' : tab === 'insights' ? '📊' : '🔮'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'cycle' && (
          <>
            <View style={styles.cycleHero}>
              <View style={styles.cycleRing}>
                <Text style={styles.cycleDay}>14</Text>
                <Text style={styles.cycleLabel}>Day</Text>
              </View>
              <Text style={styles.cyclePhase}>🔥 Ovulation Phase</Text>
              <Text style={styles.fertilityStatus}>Peak Fertility</Text>
            </View>

            <View style={styles.fertileWindow}>
              <Text style={styles.fertileTitle}>Fertile Window</Text>
              <View style={styles.fertileBar}>
                {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15].map(d => (
                  <View key={d} style={[styles.fertileDay, d >= 10 && d <= 15 && styles.fertileActive, d === 14 && styles.fertilePeak]}>
                    <Text style={styles.fertileDayText}>{d}</Text>
                  </View>
                ))}
              </View>
              <View style={styles.fertileLegend}>
                <View style={styles.legendItem}><View style={[styles.legendDot, { backgroundColor: '#334155' }]} /><Text style={styles.legendText}>Low</Text></View>
                <View style={styles.legendItem}><View style={[styles.legendDot, { backgroundColor: '#F59E0B' }]} /><Text style={styles.legendText}>Fertile</Text></View>
                <View style={styles.legendItem}><View style={[styles.legendDot, { backgroundColor: '#EC4899' }]} /><Text style={styles.legendText}>Peak</Text></View>
              </View>
            </View>
          </>
        )}

        {activeTab === 'log' && (
          <>
            <Text style={styles.sectionTitle}>Today's Log</Text>
            <View style={styles.logCard}>
              <Text style={styles.logLabel}>🌡️ Basal Body Temperature</Text>
              <Text style={styles.logValue}>36.6°C</Text>
            </View>
            <View style={styles.logCard}>
              <Text style={styles.logLabel}>💧 Cervical Mucus</Text>
              <View style={styles.cmOptions}>
                {['Dry', 'Sticky', 'Creamy', 'Watery', 'Egg White'].map((cm, i) => (
                  <TouchableOpacity key={cm} style={[styles.cmBtn, i === 4 && styles.cmActive]}>
                    <Text style={[styles.cmText, i === 4 && styles.cmTextActive]}>{cm}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            <View style={styles.logCard}>
              <Text style={styles.logLabel}>🧪 LH Strip Result</Text>
              <View style={styles.lhOptions}>
                <TouchableOpacity style={[styles.lhBtn, styles.lhPositive]}><Text style={styles.lhText}>Positive ✅</Text></TouchableOpacity>
                <TouchableOpacity style={styles.lhBtn}><Text style={styles.lhText}>Negative</Text></TouchableOpacity>
              </View>
            </View>
          </>
        )}

        {activeTab === 'insights' && (
          <>
            <Text style={styles.sectionTitle}>Cycle Insights</Text>
            <View style={styles.insightCard}>
              <Text style={styles.insightTitle}>Cycle Regularity</Text>
              <Text style={styles.insightValue}>Regular (±2 days)</Text>
              <Text style={styles.insightDesc}>Average cycle: 28 days</Text>
            </View>
            <View style={styles.insightCard}>
              <Text style={styles.insightTitle}>BBT Pattern</Text>
              <Text style={styles.insightValue}>Shift detected</Text>
              <Text style={styles.insightDesc}>Temperature rose 0.3°C — ovulation likely</Text>
            </View>
            <View style={styles.insightCard}>
              <Text style={styles.insightTitle}>CM Pattern</Text>
              <Text style={styles.insightValue}>Fertile pattern</Text>
              <Text style={styles.insightDesc}>Egg white mucus observed — peak fertility</Text>
            </View>
          </>
        )}

        {activeTab === 'predict' && (
          <>
            <Text style={styles.sectionTitle}>Predictions</Text>
            <View style={styles.predCard}>
              <Ionicons name="calendar" size={24} color="#EC4899" />
              <View style={styles.predInfo}>
                <Text style={styles.predTitle}>Next Period</Text>
                <Text style={styles.predValue}>September 12, 2026</Text>
                <Text style={styles.predSub}>In 14 days</Text>
              </View>
            </View>
            <View style={styles.predCard}>
              <Ionicons name="flower" size={24} color="#EC4899" />
              <View style={styles.predInfo}>
                <Text style={styles.predTitle}>Next Ovulation</Text>
                <Text style={styles.predValue}>September 28, 2026</Text>
                <Text style={styles.predSub}>Day 14 of next cycle</Text>
              </View>
            </View>
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
  cycleHero: { alignItems: 'center', marginBottom: 20 },
  cycleRing: { width: 120, height: 120, borderRadius: 60, borderWidth: 4, borderColor: '#EC4899', justifyContent: 'center', alignItems: 'center', backgroundColor: '#1E293B' },
  cycleDay: { fontSize: 42, fontWeight: 'bold', color: '#EC4899' },
  cycleLabel: { fontSize: 14, color: '#94A3B8' },
  cyclePhase: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginTop: 12 },
  fertilityStatus: { fontSize: 14, color: '#EC4899', marginTop: 4, fontWeight: '600' },
  fertileWindow: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 16 },
  fertileTitle: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  fertileBar: { flexDirection: 'row', gap: 4, justifyContent: 'center' },
  fertileDay: { width: 20, height: 20, borderRadius: 10, backgroundColor: '#334155', justifyContent: 'center', alignItems: 'center' },
  fertileActive: { backgroundColor: '#F59E0B' },
  fertilePeak: { backgroundColor: '#EC4899' },
  fertileDayText: { fontSize: 8, color: '#FFF', fontWeight: 'bold' },
  fertileLegend: { flexDirection: 'row', gap: 16, marginTop: 10, justifyContent: 'center' },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendText: { fontSize: 10, color: '#94A3B8' },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  logCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 12 },
  logLabel: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  logValue: { fontSize: 24, fontWeight: 'bold', color: '#EC4899' },
  cmOptions: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  cmBtn: { backgroundColor: '#334155', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8 },
  cmActive: { backgroundColor: '#EC4899' },
  cmText: { fontSize: 12, color: '#94A3B8' },
  cmTextActive: { color: '#FFF', fontWeight: 'bold' },
  lhOptions: { flexDirection: 'row', gap: 8 },
  lhBtn: { flex: 1, backgroundColor: '#334155', borderRadius: 8, padding: 12, alignItems: 'center' },
  lhPositive: { backgroundColor: '#10B981' },
  lhText: { fontSize: 14, fontWeight: '600', color: '#FFF' },
  insightCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 14, marginBottom: 10 },
  insightTitle: { fontSize: 13, color: '#94A3B8' },
  insightValue: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginTop: 4 },
  insightDesc: { fontSize: 13, color: '#64748B', marginTop: 2 },
  predCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  predInfo: { flex: 1 },
  predTitle: { fontSize: 14, color: '#94A3B8' },
  predValue: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC' },
  predSub: { fontSize: 12, color: '#64748B', marginTop: 2 },
});
