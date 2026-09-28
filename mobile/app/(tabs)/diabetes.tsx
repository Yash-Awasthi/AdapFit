/**
 * Diabetes Manager — glucose, insulin, carbs and the patterns across them.
 *
 * Every figure here is read back from the server after a write rather than
 * kept alongside it: time-in-range and the estimated HbA1c are derived from
 * the whole reading history, so a locally appended row would show a value the
 * summary above it disagrees with.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray, asNumber } from '../../src/services/http';

type Tab = 'glucose' | 'insulin' | 'carbs' | 'trends';

interface GlucoseReading {
  value: number;
  context: string;
  level: string;
  timestamp: number;
  notes?: string;
}

interface GlucoseSummary {
  message?: string;
  readings?: number;
  mean_glucose?: number;
  gmi?: number;
  time_in_range?: { target: number; above_target: number; below_target: number };
  variability?: { cv: number };
  episodes?: { hypo_count: number; hyper_count: number };
  targets_met?: Record<string, boolean>;
  next_step?: string;
}

interface InsulinEntry {
  type: string;
  units: number;
  site: string;
  notes?: string;
  timestamp: number;
}

interface CarbSummary {
  total_carbs: number;
  meals_logged?: number;
  avg_per_meal?: number;
}

interface Pattern {
  pattern: string;
  value?: number;
  message: string;
}

// The context values the backend stores. The labels are what the button says.
const CONTEXTS: { label: string; value: string }[] = [
  { label: 'Fasting', value: 'fasting' },
  { label: 'Before Meal', value: 'pre_meal' },
  { label: 'After Meal', value: 'post_meal' },
  { label: 'Bedtime', value: 'bedtime' },
];

const DAILY_CARB_GOAL = 250;

function glucoseColor(value: number): string {
  if (value < 70) return '#EF4444';
  if (value <= 140) return '#10B981';
  if (value <= 180) return '#F59E0B';
  return '#EF4444';
}

function glucoseLabel(value: number): string {
  if (value < 70) return 'Low';
  if (value <= 140) return 'Normal';
  if (value <= 180) return 'Elevated';
  return 'High';
}

function clockTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function prettyContext(context: string): string {
  return CONTEXTS.find((c) => c.value === context)?.label ?? context.replace(/_/g, ' ');
}

export default function DiabetesScreen() {
  const [activeTab, setActiveTab] = useState<Tab>('glucose');
  const [glucoseValue, setGlucoseValue] = useState('');
  const [insulinUnits, setInsulinUnits] = useState('');
  const [saving, setSaving] = useState(false);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    readings: { readings: GlucoseReading[] };
    summary: GlucoseSummary;
    insulin: { history: InsulinEntry[] };
    carbs: CarbSummary;
    patterns: { patterns: Pattern[] };
  }>({
    readings: '/diabetes/glucose/readings?hours=24',
    summary: '/diabetes/glucose/summary',
    insulin: '/diabetes/insulin/history?days=7',
    carbs: '/diabetes/carbs/summary',
    patterns: '/diabetes/glucose/patterns',
  });

  const readings = asArray<GlucoseReading>(data.readings?.readings);
  const summary = data.summary ?? {};
  const insulin = asArray<InsulinEntry>(data.insulin?.history);
  const carbs = data.carbs ?? { total_carbs: 0 };
  const patterns = asArray<Pattern>(data.patterns?.patterns);

  // Newest first for the hero reading; the list below reads oldest to newest.
  const latest = readings.length ? readings[readings.length - 1] : null;

  const logGlucose = useCallback(async (context: string) => {
    const value = Number(glucoseValue);
    if (!Number.isFinite(value) || value <= 0) {
      Alert.alert('Log reading', 'Enter the glucose value first.');
      return;
    }
    setSaving(true);
    const result = await postJson('/diabetes/glucose', { value_mgdl: Math.round(value), context });
    setSaving(false);
    if (!result) {
      Alert.alert('Not recorded', 'The reading could not be saved. Try again when you are back online.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setGlucoseValue('');
    await reload();
  }, [glucoseValue, reload]);

  const logInsulin = useCallback(async (insulinType: string) => {
    const units = Number(insulinUnits);
    if (!Number.isFinite(units) || units <= 0) {
      Alert.alert('Log dose', 'Enter the number of units first.');
      return;
    }
    setSaving(true);
    const result = await postJson('/diabetes/insulin', { insulin_type: insulinType, units, site: 'abdomen' });
    setSaving(false);
    if (!result) {
      Alert.alert('Not recorded', 'The dose could not be saved. Try again when you are back online.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setInsulinUnits('');
    await reload();
  }, [insulinUnits, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  const carbsEaten = asNumber(carbs.total_carbs);
  const carbPct = Math.min(100, Math.round((carbsEaten / DAILY_CARB_GOAL) * 100));
  const timeInRange = asNumber(summary.time_in_range?.target);
  const timeBelow = asNumber(summary.time_in_range?.below_target);
  const average = asNumber(summary.mean_glucose);
  const hba1c = asNumber(summary.gmi);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle} accessibilityRole="header">Diabetes Manager</Text>
        <Text style={styles.headerSubtitle}>Track glucose, insulin &amp; carbs</Text>
      </View>

      <View style={styles.tabBar}>
        {(['glucose', 'insulin', 'carbs', 'trends'] as Tab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
            accessibilityRole="tab"
            accessibilityLabel={tab}
            accessibilityState={{ selected: activeTab === tab }}
          >
            <Ionicons
              name={tab === 'glucose' ? 'water' : tab === 'insulin' ? 'medkit-outline' : tab === 'carbs' ? 'nutrition-outline' : 'trending-up'}
              size={20}
              color={activeTab === tab ? '#FFF' : '#94A3B8'}
            />
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#3B82F6" />}
      >
        {activeTab === 'glucose' && (
          <>
            <View style={styles.glucoseHero}>
              <View style={[styles.glucoseRing, { borderColor: latest ? glucoseColor(latest.value) : '#334155' }]}>
                <Text style={styles.glucoseValue}>{latest ? latest.value : '—'}</Text>
                <Text style={styles.glucoseUnit}>mg/dL</Text>
                {latest && (
                  <Text style={[styles.glucoseStatus, { color: glucoseColor(latest.value) }]}>
                    {glucoseLabel(latest.value)}
                  </Text>
                )}
              </View>
              <Text style={styles.glucoseTime}>
                {latest ? `Last reading: ${clockTime(latest.timestamp)}` : 'No readings in the last 24 hours'}
              </Text>
            </View>

            <Text style={styles.sectionTitle}>Log Glucose Reading</Text>
            <View style={styles.logCard}>
              <TextInput
                style={styles.input}
                placeholder="Enter glucose (mg/dL)"
                placeholderTextColor="#64748B"
                keyboardType="numeric"
                value={glucoseValue}
                onChangeText={setGlucoseValue}
                accessibilityLabel="Glucose value in milligrams per decilitre"
              />
              <View style={styles.logButtons}>
                {CONTEXTS.map((context) => (
                  <TouchableOpacity
                    key={context.value}
                    style={styles.logBtn}
                    disabled={saving}
                    onPress={() => logGlucose(context.value)}
                    accessibilityRole="button"
                    accessibilityLabel={`Log reading taken ${context.label.toLowerCase()}`}
                  >
                    <Text style={styles.logBtnText}>{context.label}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <Text style={styles.sectionTitle}>Today's Readings</Text>
            {readings.length === 0 && (
              <Text style={styles.emptyText}>
                Nothing logged in the last 24 hours. Readings appear here as you add them.
              </Text>
            )}
            {[...readings].reverse().map((r, i) => (
              <View key={`${r.timestamp}-${i}`} style={styles.readingCard}>
                <View style={styles.readingLeft}>
                  <Text style={styles.readingTime}>{clockTime(r.timestamp)}</Text>
                  <Text style={styles.readingType}>{prettyContext(r.context)}</Text>
                </View>
                <View style={styles.readingRight}>
                  <Text style={[styles.readingValue, { color: glucoseColor(r.value) }]}>{r.value}</Text>
                  <Text style={styles.readingUnit}>mg/dL</Text>
                </View>
              </View>
            ))}
          </>
        )}

        {activeTab === 'insulin' && (
          <>
            <Text style={styles.sectionTitle}>Log Insulin Dose</Text>
            <View style={styles.logCard}>
              <TextInput
                style={styles.input}
                placeholder="Units"
                placeholderTextColor="#64748B"
                keyboardType="numeric"
                value={insulinUnits}
                onChangeText={setInsulinUnits}
                accessibilityLabel="Insulin units"
              />
              <View style={styles.logButtons}>
                {['rapid', 'short', 'intermediate', 'long'].map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={styles.logBtn}
                    disabled={saving}
                    onPress={() => logInsulin(type)}
                    accessibilityRole="button"
                    accessibilityLabel={`Log ${type}-acting insulin`}
                  >
                    <Text style={styles.logBtnText}>{type}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <Text style={styles.sectionTitle}>Insulin Log</Text>
            {insulin.length === 0 && (
              <Text style={styles.emptyText}>No doses logged in the last seven days.</Text>
            )}
            {[...insulin].reverse().map((entry, i) => (
              <View key={`${entry.timestamp}-${i}`} style={styles.insCard}>
                <View style={styles.insLeft}>
                  <Text style={styles.insTime}>{clockTime(entry.timestamp)}</Text>
                  <Text style={styles.insType}>{entry.type} — {entry.site}</Text>
                </View>
                <Text style={styles.insDose}>{entry.units} units</Text>
              </View>
            ))}
          </>
        )}

        {activeTab === 'carbs' && (
          <>
            <Text style={styles.sectionTitle}>Carb Counter</Text>
            <View style={styles.carbProgress}>
              <Text style={styles.carbEaten}>{carbsEaten}g eaten</Text>
              <View style={styles.carbBar}>
                <View style={[styles.carbFill, { width: `${carbPct}%` }]} />
              </View>
              <Text style={styles.carbGoal}>Goal: {DAILY_CARB_GOAL}g</Text>
            </View>
            <View style={styles.carbCard}>
              <Text style={styles.carbMeal}>Meals logged</Text>
              <Text style={styles.carbAmount}>{asNumber(carbs.meals_logged)}</Text>
            </View>
            <View style={styles.carbCard}>
              <Text style={styles.carbMeal}>Average per meal</Text>
              <Text style={styles.carbAmount}>{asNumber(carbs.avg_per_meal)}g</Text>
            </View>
            {carbsEaten === 0 && (
              <Text style={styles.emptyText}>
                Nothing logged yet. Carbs recorded against a meal appear in this total.
              </Text>
            )}
          </>
        )}

        {activeTab === 'trends' && (
          <>
            <Text style={styles.sectionTitle}>Glucose Trends</Text>
            {summary.message ? (
              <Text style={styles.emptyText}>{summary.message}</Text>
            ) : (
              <>
                <View style={styles.trendCard}>
                  <Text style={styles.trendTitle}>Average: {average} mg/dL</Text>
                  <View style={styles.trendBar}>
                    <View style={[styles.trendFill, {
                      width: `${Math.min(100, Math.round((average / 300) * 100))}%`,
                      backgroundColor: glucoseColor(average),
                    }]} />
                  </View>
                  <Text style={styles.trendStatus}>
                    Target range 70-180 mg/dL · {asNumber(summary.episodes?.hypo_count)} low and {asNumber(summary.episodes?.hyper_count)} high episodes
                  </Text>
                </View>
                <View style={styles.trendCard}>
                  <Text style={styles.trendTitle}>Time in Range: {timeInRange}%</Text>
                  <View style={styles.trendBar}>
                    <View style={[styles.trendFill, {
                      width: `${Math.min(100, Math.round(timeInRange))}%`,
                      backgroundColor: timeInRange >= 70 ? '#10B981' : '#F59E0B',
                    }]} />
                  </View>
                  <Text style={styles.trendStatus}>Goal: over 70% in range, under 4% below ({timeBelow}% below) · variability {asNumber(summary.variability?.cv)}% (goal 36% or less)</Text>
                </View>
                <View style={styles.trendCard}>
                  <Text style={styles.trendTitle}>GMI (estimated A1C): {hba1c}%</Text>
                  <View style={styles.trendBar}>
                    <View style={[styles.trendFill, {
                      width: `${Math.min(100, Math.round((hba1c / 10) * 100))}%`,
                      backgroundColor: hba1c < 7 ? '#10B981' : '#F59E0B',
                    }]} />
                  </View>
                  <Text style={styles.trendStatus}>
                    From {asNumber(summary.readings)} readings. Estimated, not a lab result. {summary.next_step ?? ''}
                  </Text>
                </View>
              </>
            )}

            <Text style={styles.sectionTitle}>Patterns</Text>
            {patterns.map((p, i) => (
              <View key={i} style={styles.trendCard}>
                <Text style={styles.trendTitle}>
                  {p.pattern}{typeof p.value === 'number' ? ` — ${p.value} mg/dL` : ''}
                </Text>
                <Text style={styles.trendStatus}>{p.message}</Text>
              </View>
            ))}
          </>
        )}

        <View style={{ height: 80 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  center: { justifyContent: 'center', alignItems: 'center' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 16, backgroundColor: '#1E293B' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#F8FAFC' },
  headerSubtitle: { fontSize: 14, color: '#94A3B8', marginTop: 4 },
  tabBar: { flexDirection: 'row', backgroundColor: '#1E293B', paddingHorizontal: 16, paddingVertical: 8 },
  tab: { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: 8 },
  activeTab: { backgroundColor: '#3B82F6' },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  glucoseHero: { alignItems: 'center', marginBottom: 20 },
  glucoseRing: { width: 160, height: 160, borderRadius: 80, borderWidth: 6, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1E293B' },
  glucoseValue: { fontSize: 48, fontWeight: 'bold', color: '#F8FAFC' },
  glucoseUnit: { fontSize: 14, color: '#94A3B8' },
  glucoseStatus: { fontSize: 16, fontWeight: 'bold', marginTop: 4 },
  glucoseTime: { fontSize: 13, color: '#64748B', marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12, marginTop: 8 },
  emptyText: { fontSize: 13, color: '#94A3B8', lineHeight: 19, marginBottom: 12 },
  logCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 16 },
  input: { backgroundColor: '#334155', borderRadius: 8, padding: 12, color: '#F8FAFC', fontSize: 16, marginBottom: 12 },
  logButtons: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  logBtn: { backgroundColor: '#334155', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8 },
  logBtnText: { color: '#94A3B8', fontSize: 12, fontWeight: '600' },
  readingCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between' },
  readingLeft: {},
  readingTime: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  readingType: { fontSize: 12, color: '#94A3B8', marginTop: 2, textTransform: 'capitalize' },
  readingRight: { alignItems: 'flex-end' },
  readingValue: { fontSize: 22, fontWeight: 'bold' },
  readingUnit: { fontSize: 11, color: '#64748B' },
  insCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  insLeft: {},
  insTime: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  insType: { fontSize: 12, color: '#94A3B8', marginTop: 2, textTransform: 'capitalize' },
  insDose: { fontSize: 16, fontWeight: 'bold', color: '#3B82F6' },
  carbProgress: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 16 },
  carbEaten: { fontSize: 20, fontWeight: 'bold', color: '#F8FAFC' },
  carbBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginTop: 8, marginBottom: 4 },
  carbFill: { height: '100%', backgroundColor: '#10B981', borderRadius: 4 },
  carbGoal: { fontSize: 12, color: '#94A3B8' },
  carbCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between' },
  carbMeal: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC', flex: 1 },
  carbAmount: { fontSize: 16, fontWeight: 'bold', color: '#F59E0B', textAlign: 'right' },
  trendCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  trendTitle: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  trendBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 8 },
  trendFill: { height: '100%', borderRadius: 4 },
  trendStatus: { fontSize: 13, color: '#94A3B8' },
});
