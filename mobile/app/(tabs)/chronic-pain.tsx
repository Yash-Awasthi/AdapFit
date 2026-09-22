/**
 * Chronic Pain Manager — the diary, and what the diary shows.
 *
 * Triggers and treatment effectiveness are derived from the entries the user
 * logs, so both tabs stay empty until there is enough to derive from. That is
 * the honest state: a trigger list nobody's own pain produced is worse than
 * none, because it invites someone to change their life around it.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

type Tab = 'diary' | 'triggers' | 'treatments' | 'cbt';

interface PainEntry {
  date: string;
  time: string;
  pain_level: number;
  pain_type: string;
  location: string;
  mood: number;
  triggers: string[];
  treatments_used: string[];
}

interface TriggerAnalysis {
  message?: string;
  days_logged?: number;
  top_triggers?: { trigger: string; occurrences: number; avg_pain_when_present: number; high_pain_rate: number }[];
  most_painful_trigger?: string;
  recommendation?: string;
}

interface TreatmentAnalysis {
  message?: string;
  treatments?: { treatment: string; times_used: number; avg_relief_percent: number; effectiveness: string }[];
}

interface CBTTechnique {
  name: string;
  description: string;
  duration: string;
  evidence: string;
}

const PAIN_SCALE = [
  { level: 0, label: 'No pain', color: '#10B981' },
  { level: 3, label: 'Mild', color: '#FBBF24' },
  { level: 5, label: 'Moderate', color: '#F97316' },
  { level: 7, label: 'Severe', color: '#EF4444' },
  { level: 10, label: 'Unbearable', color: '#DC2626' },
];

// Offered as chips rather than free text so the trigger analysis has
// something consistent to correlate against.
const COMMON_TRIGGERS = ['Poor sleep', 'Stress', 'Weather', 'Prolonged sitting', 'Overexertion', 'Travel'];

function painColor(level: number): string {
  return level <= 3 ? '#10B981' : level <= 6 ? '#F59E0B' : '#EF4444';
}

function relativeDay(date: string): string {
  const today = new Date().toISOString().slice(0, 10);
  if (date === today) return 'Today';
  const yesterday = new Date(Date.now() - 86400_000).toISOString().slice(0, 10);
  if (date === yesterday) return 'Yesterday';
  return date;
}

export default function ChronicPainScreen() {
  const userId = useUserStore((s) => s.userId);
  const [activeTab, setActiveTab] = useState<Tab>('diary');
  const [level, setLevel] = useState<number | null>(null);
  const [location, setLocation] = useState('');
  const [triggers, setTriggers] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    history: { data: PainEntry[] };
    triggers: { data: TriggerAnalysis };
    treatments: { data: TreatmentAnalysis };
    cbt: { data: CBTTechnique[] };
  }>({
    history: `/chronic-pain/history/${userId}`,
    triggers: `/chronic-pain/triggers/${userId}`,
    treatments: `/chronic-pain/treatments/${userId}`,
    cbt: '/chronic-pain/cbt-techniques',
  });

  const entries = asArray<PainEntry>(data.history?.data);
  const triggerAnalysis = data.triggers?.data ?? {};
  const treatmentAnalysis = data.treatments?.data ?? {};
  const cbt = asArray<CBTTechnique>(data.cbt?.data);

  const toggleTrigger = (trigger: string) =>
    setTriggers((prev) => (prev.includes(trigger) ? prev.filter((t) => t !== trigger) : [...prev, trigger]));

  const logPain = useCallback(async () => {
    if (level === null) {
      Alert.alert('Log pain', 'Choose a pain level first.');
      return;
    }
    setSaving(true);
    const result = await postJson('/chronic-pain/log', {
      user_id: userId,
      data: {
        pain_level: level,
        location: location.trim() || 'general',
        triggers,
      },
    });
    setSaving(false);
    if (!result) {
      Alert.alert('Not recorded', 'The entry could not be saved.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setLevel(null);
    setLocation('');
    setTriggers([]);
    await reload();
  }, [level, location, triggers, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  const topTriggers = asArray<NonNullable<TriggerAnalysis['top_triggers']>[number]>(triggerAnalysis.top_triggers);
  const treatments = asArray<NonNullable<TreatmentAnalysis['treatments']>[number]>(treatmentAnalysis.treatments);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle} accessibilityRole="header">Chronic Pain Manager</Text>
        <Text style={styles.headerSubtitle}>Pain diary, triggers &amp; relief tracking</Text>
      </View>

      <View style={styles.tabBar}>
        {(['diary', 'triggers', 'treatments', 'cbt'] as Tab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
            accessibilityRole="tab"
            accessibilityState={{ selected: activeTab === tab }}
            accessibilityLabel={tab}
          >
            <Ionicons
              name={tab === 'diary' ? 'book-outline' : tab === 'triggers' ? 'search-outline' : tab === 'treatments' ? 'medkit-outline' : 'analytics-outline'}
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
        {activeTab === 'diary' && (
          <>
            <Text style={styles.sectionTitle}>How's your pain today?</Text>
            <View style={styles.painScale}>
              {PAIN_SCALE.map((p) => (
                <TouchableOpacity
                  key={p.level}
                  style={[
                    styles.painBtn,
                    { borderColor: p.color },
                    level === p.level && { backgroundColor: p.color + '25' },
                  ]}
                  onPress={() => setLevel(p.level)}
                  accessibilityRole="radio"
                  accessibilityState={{ selected: level === p.level }}
                  accessibilityLabel={`Pain level ${p.level}, ${p.label}`}
                >
                  <Text style={[styles.painLevel, { color: p.color }]}>{p.level}</Text>
                  <Text style={styles.painLabel}>{p.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <TextInput
              style={styles.input}
              placeholder="Where does it hurt?"
              placeholderTextColor="#64748B"
              value={location}
              onChangeText={setLocation}
              accessibilityLabel="Pain location"
            />

            <Text style={styles.sectionTitle}>What might have set it off?</Text>
            <View style={styles.chipRow}>
              {COMMON_TRIGGERS.map((trigger) => {
                const on = triggers.includes(trigger);
                return (
                  <TouchableOpacity
                    key={trigger}
                    style={[styles.chip, on && styles.chipOn]}
                    onPress={() => toggleTrigger(trigger)}
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: on }}
                  >
                    <Text style={[styles.chipText, on && styles.chipTextOn]}>{trigger}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <TouchableOpacity style={styles.saveBtn} onPress={logPain} disabled={saving}>
              <Text style={styles.saveText}>{saving ? 'Saving…' : 'Save entry'}</Text>
            </TouchableOpacity>

            <Text style={styles.sectionTitle}>Recent Entries</Text>
            {entries.length === 0 && (
              <Text style={styles.emptyText}>
                Nothing logged yet. Entries here are what the trigger and treatment tabs are
                built from.
              </Text>
            )}
            {[...entries].reverse().map((entry, i) => (
              <View key={`${entry.date}-${entry.time}-${i}`} style={styles.diaryCard}>
                <View style={styles.diaryLeft}>
                  <Text style={styles.diaryDate}>{relativeDay(entry.date)} · {entry.time}</Text>
                  <Text style={styles.diaryLocation}>{entry.location} — {entry.pain_type}</Text>
                  {entry.triggers?.length > 0 && (
                    <Text style={styles.diaryTriggers}>{entry.triggers.join(', ')}</Text>
                  )}
                </View>
                <View style={styles.diaryRight}>
                  <Text style={[styles.diaryPain, { color: painColor(entry.pain_level) }]}>
                    {entry.pain_level}/10
                  </Text>
                  <Text style={styles.diaryMood}>Mood: {entry.mood}/10</Text>
                </View>
              </View>
            ))}
          </>
        )}

        {activeTab === 'triggers' && (
          <>
            <Text style={styles.sectionTitle}>Top Pain Triggers</Text>
            {topTriggers.length === 0 ? (
              <Text style={styles.emptyText}>
                {triggerAnalysis.message ?? 'No triggers identified yet.'}
                {typeof triggerAnalysis.days_logged === 'number'
                  ? ` ${triggerAnalysis.days_logged} entries logged so far.`
                  : ''}
              </Text>
            ) : (
              <>
                {topTriggers.map((t, i) => (
                  <View key={i} style={styles.triggerCard}>
                    <Text style={styles.triggerName}>{t.trigger}</Text>
                    <View style={styles.triggerBar}>
                      <View style={[styles.triggerFill, { width: `${t.high_pain_rate}%` }]} />
                    </View>
                    <Text style={styles.triggerStats}>
                      {t.high_pain_rate}% of high-pain days · Avg pain {t.avg_pain_when_present} · {t.occurrences} times
                    </Text>
                  </View>
                ))}
                {triggerAnalysis.recommendation && (
                  <Text style={styles.recommendation}>{triggerAnalysis.recommendation}</Text>
                )}
              </>
            )}
          </>
        )}

        {activeTab === 'treatments' && (
          <>
            <Text style={styles.sectionTitle}>Treatment Effectiveness</Text>
            {treatments.length === 0 ? (
              <Text style={styles.emptyText}>
                {treatmentAnalysis.message ?? 'Record what you tried and how much it helped, and the comparison appears here.'}
              </Text>
            ) : (
              treatments.map((t, i) => (
                <View key={i} style={styles.treatCard}>
                  <Text style={styles.treatName}>{t.treatment}</Text>
                  <View style={styles.treatBar}>
                    <View style={[styles.treatFill, { width: `${t.avg_relief_percent}%` }]} />
                  </View>
                  <Text style={styles.treatStats}>
                    {t.avg_relief_percent}% relief · used {t.times_used} times · {t.effectiveness}
                  </Text>
                </View>
              ))
            )}
          </>
        )}

        {activeTab === 'cbt' && (
          <>
            <Text style={styles.sectionTitle}>CBT Pain Management Techniques</Text>
            {cbt.map((technique, i) => (
              <View key={i} style={styles.cbtCard}>
                <View style={styles.cbtHeader}>
                  <Text style={styles.cbtName}>{technique.name}</Text>
                  <Text style={styles.cbtDuration}>{technique.duration}</Text>
                </View>
                <Text style={styles.cbtDesc}>{technique.description}</Text>
                <Text style={styles.cbtEvidence}>Evidence: {technique.evidence}</Text>
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
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12, marginTop: 8 },
  emptyText: { fontSize: 13, color: '#94A3B8', lineHeight: 19, marginBottom: 12 },
  recommendation: { fontSize: 13, color: '#F8FAFC', marginTop: 8, lineHeight: 19 },

  painScale: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  painBtn: { flex: 1, marginHorizontal: 3, paddingVertical: 10, borderRadius: 10, borderWidth: 2, alignItems: 'center' },
  painLevel: { fontSize: 18, fontWeight: 'bold' },
  painLabel: { fontSize: 9, color: '#94A3B8', marginTop: 2, textAlign: 'center' },

  input: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, color: '#F8FAFC', fontSize: 15, marginBottom: 8 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: '#1E293B' },
  chipOn: { backgroundColor: '#3B82F6' },
  chipText: { fontSize: 12, color: '#94A3B8', fontWeight: '600' },
  chipTextOn: { color: '#FFF' },
  saveBtn: { backgroundColor: '#3B82F6', borderRadius: 12, paddingVertical: 14, alignItems: 'center', marginBottom: 8 },
  saveText: { color: '#FFF', fontSize: 15, fontWeight: 'bold' },

  diaryCard: { backgroundColor: '#1E293B', borderRadius: 10, padding: 14, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between' },
  diaryLeft: { flex: 1 },
  diaryDate: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  diaryLocation: { fontSize: 12, color: '#94A3B8', marginTop: 2, textTransform: 'capitalize' },
  diaryTriggers: { fontSize: 11, color: '#64748B', marginTop: 2 },
  diaryRight: { alignItems: 'flex-end' },
  diaryPain: { fontSize: 20, fontWeight: 'bold' },
  diaryMood: { fontSize: 11, color: '#64748B', marginTop: 2 },

  triggerCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  triggerName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  triggerBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 8 },
  triggerFill: { height: '100%', backgroundColor: '#EF4444', borderRadius: 4 },
  triggerStats: { fontSize: 12, color: '#94A3B8' },

  treatCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  treatName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8, textTransform: 'capitalize' },
  treatBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 8 },
  treatFill: { height: '100%', backgroundColor: '#10B981', borderRadius: 4 },
  treatStats: { fontSize: 12, color: '#94A3B8' },

  cbtCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  cbtHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  cbtName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', flex: 1 },
  cbtDuration: { fontSize: 12, color: '#3B82F6', fontWeight: '600' },
  cbtDesc: { fontSize: 13, color: '#94A3B8', lineHeight: 18 },
  cbtEvidence: { fontSize: 12, color: '#64748B', marginTop: 6, textTransform: 'capitalize' },
});
