import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function DiabetesScreen() {
  const [activeTab, setActiveTab] = useState<'glucose' | 'insulin' | 'carbs' | 'trends'>('glucose');
  const [glucoseValue, setGlucoseValue] = useState('');

  const getGlucoseColor = (val: number) => {
    if (val < 70) return '#EF4444';
    if (val <= 140) return '#10B981';
    if (val <= 180) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>💉 Diabetes Manager</Text>
        <Text style={styles.headerSubtitle}>Track glucose, insulin & carbs</Text>
      </View>

      <View style={styles.tabBar}>
        {(['glucose', 'insulin', 'carbs', 'trends'] as const).map(tab => (
          <TouchableOpacity key={tab} style={[styles.tab, activeTab === tab && styles.activeTab]} onPress={() => setActiveTab(tab)}>
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'glucose' ? '🩸' : tab === 'insulin' ? '💉' : tab === 'carbs' ? '🍞' : '📈'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'glucose' && (
          <>
            <View style={styles.glucoseHero}>
              <View style={[styles.glucoseRing, { borderColor: getGlucoseColor(118) }]}>
                <Text style={styles.glucoseValue}>118</Text>
                <Text style={styles.glucoseUnit}>mg/dL</Text>
                <Text style={[styles.glucoseStatus, { color: '#10B981' }]}>Normal</Text>
              </View>
              <Text style={styles.glucoseTime}>Last reading: 2 min ago</Text>
            </View>

            <Text style={styles.sectionTitle}>Log Glucose Reading</Text>
            <View style={styles.logCard}>
              <TextInput style={styles.input} placeholder="Enter glucose (mg/dL)" placeholderTextColor="#64748B" keyboardType="numeric" value={glucoseValue} onChangeText={setGlucoseValue} />
              <View style={styles.logButtons}>
                {['Before Meal', 'After Meal', 'Bedtime', 'Fasting'].map(type => (
                  <TouchableOpacity key={type} style={styles.logBtn}>
                    <Text style={styles.logBtnText}>{type}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <Text style={styles.sectionTitle}>Today's Readings</Text>
            {[
              { time: '7:00 AM', value: 95, type: 'Fasting', color: '#10B981' },
              { time: '12:30 PM', value: 142, type: 'After Lunch', color: '#F59E0B' },
              { time: '6:00 PM', value: 118, type: 'Before Dinner', color: '#10B981' },
            ].map((r, i) => (
              <View key={i} style={styles.readingCard}>
                <View style={styles.readingLeft}>
                  <Text style={styles.readingTime}>{r.time}</Text>
                  <Text style={styles.readingType}>{r.type}</Text>
                </View>
                <View style={styles.readingRight}>
                  <Text style={[styles.readingValue, { color: r.color }]}>{r.value}</Text>
                  <Text style={styles.readingUnit}>mg/dL</Text>
                </View>
              </View>
            ))}
          </>
        )}

        {activeTab === 'insulin' && (
          <>
            <Text style={styles.sectionTitle}>Insulin Log</Text>
            {[
              { time: '7:30 AM', type: 'Rapid', dose: '12 units', before: 'Breakfast' },
              { time: '12:00 PM', type: 'Rapid', dose: '8 units', before: 'Lunch' },
              { time: '10:00 PM', type: 'Long-acting', dose: '24 units', before: 'Bedtime' },
            ].map((ins, i) => (
              <View key={i} style={styles.insCard}>
                <View style={styles.insLeft}>
                  <Text style={styles.insTime}>{ins.time}</Text>
                  <Text style={styles.insType}>{ins.type} — {ins.before}</Text>
                </View>
                <Text style={styles.insDose}>{ins.dose}</Text>
              </View>
            ))}
            <TouchableOpacity style={styles.addBtn}>
              <Ionicons name="add-circle" size={20} color="#FFF" />
              <Text style={styles.addBtnText}>Log Insulin Dose</Text>
            </TouchableOpacity>
          </>
        )}

        {activeTab === 'carbs' && (
          <>
            <Text style={styles.sectionTitle}>Carb Counter</Text>
            <View style={styles.carbProgress}>
              <Text style={styles.carbEaten}>145g eaten</Text>
              <View style={styles.carbBar}>
                <View style={[styles.carbFill, { width: '58%' }]} />
              </View>
              <Text style={styles.carbGoal}>Goal: 250g</Text>
            </View>
            {[
              { meal: 'Breakfast', items: 'Oatmeal, banana', carbs: 45 },
              { meal: 'Lunch', items: 'Grilled chicken salad', carbs: 35 },
              { meal: 'Snack', items: 'Apple, almonds', carbs: 25 },
              { meal: 'Dinner', items: 'Pasta, vegetables', carbs: 65 },
            ].map((m, i) => (
              <View key={i} style={styles.carbCard}>
                <Text style={styles.carbMeal}>{m.meal}</Text>
                <Text style={styles.carbItems}>{m.items}</Text>
                <Text style={styles.carbAmount}>{m.carbs}g</Text>
              </View>
            ))}
          </>
        )}

        {activeTab === 'trends' && (
          <>
            <Text style={styles.sectionTitle}>Weekly Glucose Trends</Text>
            <View style={styles.trendCard}>
              <Text style={styles.trendTitle}>Average: 128 mg/dL</Text>
              <View style={styles.trendBar}>
                <View style={[styles.trendFill, { width: '64%', backgroundColor: '#10B981' }]} />
              </View>
              <Text style={styles.trendStatus}>✅ Within target range (70-180)</Text>
            </View>
            <View style={styles.trendCard}>
              <Text style={styles.trendTitle}>Time in Range: 72%</Text>
              <View style={styles.trendBar}>
                <View style={[styles.trendFill, { width: '72%', backgroundColor: '#10B981' }]} />
              </View>
              <Text style={styles.trendStatus}>Goal: 70%+ time in range</Text>
            </View>
            <View style={styles.trendCard}>
              <Text style={styles.trendTitle}>A1C Estimate: 6.8%</Text>
              <View style={styles.trendBar}>
                <View style={[styles.trendFill, { width: '68%', backgroundColor: '#F59E0B' }]} />
              </View>
              <Text style={styles.trendStatus}>⚠️ Slightly above target (under 7%)</Text>
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
  activeTab: { backgroundColor: '#3B82F6' },
  tabText: { fontSize: 20 },
  activeTabText: { color: '#FFF' },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  glucoseHero: { alignItems: 'center', marginBottom: 20 },
  glucoseRing: { width: 160, height: 160, borderRadius: 80, borderWidth: 6, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1E293B' },
  glucoseValue: { fontSize: 48, fontWeight: 'bold', color: '#F8FAFC' },
  glucoseUnit: { fontSize: 14, color: '#94A3B8' },
  glucoseStatus: { fontSize: 16, fontWeight: 'bold', marginTop: 4 },
  glucoseTime: { fontSize: 13, color: '#64748B', marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  logCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 16 },
  input: { backgroundColor: '#334155', borderRadius: 8, padding: 12, color: '#F8FAFC', fontSize: 16, marginBottom: 12 },
  logButtons: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  logBtn: { backgroundColor: '#334155', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8 },
  logBtnText: { color: '#94A3B8', fontSize: 12, fontWeight: '600' },
  readingCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between' },
  readingLeft: {},
  readingTime: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  readingType: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  readingRight: { alignItems: 'flex-end' },
  readingValue: { fontSize: 22, fontWeight: 'bold' },
  readingUnit: { fontSize: 11, color: '#64748B' },
  insCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  insLeft: {},
  insTime: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  insType: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  insDose: { fontSize: 16, fontWeight: 'bold', color: '#3B82F6' },
  addBtn: { backgroundColor: '#3B82F6', borderRadius: 12, padding: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 12, gap: 8 },
  addBtnText: { color: '#FFF', fontSize: 15, fontWeight: 'bold' },
  carbProgress: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 16 },
  carbEaten: { fontSize: 20, fontWeight: 'bold', color: '#F8FAFC' },
  carbBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginTop: 8, marginBottom: 4 },
  carbFill: { height: '100%', backgroundColor: '#10B981', borderRadius: 4 },
  carbGoal: { fontSize: 12, color: '#94A3B8' },
  carbCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between' },
  carbMeal: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC', flex: 1 },
  carbItems: { fontSize: 12, color: '#94A3B8', flex: 2 },
  carbAmount: { fontSize: 16, fontWeight: 'bold', color: '#F59E0B', width: 50, textAlign: 'right' },
  trendCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  trendTitle: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  trendBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 8 },
  trendFill: { height: '100%', borderRadius: 4 },
  trendStatus: { fontSize: 13, color: '#94A3B8' },
});
