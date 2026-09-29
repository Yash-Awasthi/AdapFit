/**
 * Voice Health — vocal exercises, and acoustic trends where a recording
 * supplied measurements.
 *
 * This screen used to screen for Parkinson's, depression, anxiety and
 * cognitive decline, computing each risk with `Math.random()` in the client
 * and showing a confidence beside it. Voice does carry real signal for some
 * of those conditions, but nothing in this app implements a validated
 * instrument, and a number with nothing behind it is worst on exactly these
 * subjects.
 *
 * What is real: the vocal exercises, and the acoustic features of a recording
 * compared with the user's own earlier ones.
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useApis } from '../../src/hooks/useApi';
import { asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

type Tab = 'exercises' | 'trends';

const TAB_ICONS: Record<Tab, string> = { exercises: 'barbell', trends: 'trending-up-outline' };
const TAB_LABELS: Record<Tab, string> = { exercises: 'Exercises', trends: 'Trends' };

interface VoiceExercise {
  name: string;
  duration: string;
  description: string;
  benefit: string;
}

interface FeatureTrend {
  feature: string;
  status: 'ok' | 'insufficient_data';
  data_points?: number;
  latest?: number;
  change?: number;
  direction?: string;
  average?: number;
  message?: string;
}

// The exercise sets the service groups by. Named for what they train rather
// than for a condition, because that is what they actually do.
const EXERCISE_TARGETS = [
  { key: 'depression', label: 'Energy & range', icon: 'sunny-outline', color: '#F59E0B' },
  { key: 'parkinsons', label: 'Volume & clarity', icon: 'volume-high-outline', color: '#8B5CF6' },
  { key: 'cognitive', label: 'Fluency', icon: 'chatbubbles-outline', color: '#3B82F6' },
  { key: 'respiratory', label: 'Breath support', icon: 'fitness-outline', color: '#22C55E' },
];

// Shown in the trends tab. These are the measurements a recording supplies.
const TRACKED_FEATURES = [
  { key: 'voice_tremor', label: 'Tremor' },
  { key: 'speech_rate', label: 'Speech rate' },
  { key: 'pitch_variability', label: 'Pitch variability' },
  { key: 'breath_support', label: 'Breath support' },
];

export default function VoiceHealthScreen() {
  const userId = useUserStore((s) => s.userId);
  const [activeTab, setActiveTab] = useState<Tab>('exercises');
  const [target, setTarget] = useState(EXERCISE_TARGETS[0].key);

  const { data, loading, refreshing, refresh } = useApis<{
    exercises: { data: VoiceExercise[] };
    tremor: { data: FeatureTrend };
    rate: { data: FeatureTrend };
    pitch: { data: FeatureTrend };
    breath: { data: FeatureTrend };
  }>({
    exercises: `/voice-biomarker/exercises?target=${target}`,
    tremor: `/voice-biomarker/trend/${userId}/voice_tremor`,
    rate: `/voice-biomarker/trend/${userId}/speech_rate`,
    pitch: `/voice-biomarker/trend/${userId}/pitch_variability`,
    breath: `/voice-biomarker/trend/${userId}/breath_support`,
  });

  const exercises = asArray<VoiceExercise>(data.exercises?.data);
  const trends: Record<string, FeatureTrend | undefined> = {
    voice_tremor: data.tremor?.data,
    speech_rate: data.rate?.data,
    pitch_variability: data.pitch?.data,
    breath_support: data.breath?.data,
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle} accessibilityRole="header">Voice Health</Text>
        <Text style={styles.headerSubtitle}>Vocal exercises and acoustic trends</Text>
      </View>

      <View style={styles.tabBar}>
        {(['exercises', 'trends'] as Tab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
            accessibilityRole="tab"
            accessibilityState={{ selected: activeTab === tab }}
          >
            <Ionicons
              name={TAB_ICONS[tab] as any}
              size={16}
              color={activeTab === tab ? '#FFFFFF' : '#94A3B8'}
            />
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {TAB_LABELS[tab]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <ScrollView
          style={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#3B82F6" />}
        >
          {activeTab === 'exercises' && (
            <>
              <Text style={styles.sectionTitle}>What would you like to work on?</Text>
              <View style={styles.targetRow}>
                {EXERCISE_TARGETS.map((option) => {
                  const on = option.key === target;
                  return (
                    <TouchableOpacity
                      key={option.key}
                      style={[styles.targetChip, on && { backgroundColor: option.color }]}
                      onPress={() => setTarget(option.key)}
                      accessibilityRole="radio"
                      accessibilityState={{ selected: on }}
                      accessibilityLabel={option.label}
                    >
                      <Ionicons name={option.icon as any} size={14} color={on ? '#FFF' : option.color} />
                      <Text style={[styles.targetText, on && styles.targetTextOn]}>{option.label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {exercises.length === 0 ? (
                <Text style={styles.emptyText}>The exercise list could not be loaded.</Text>
              ) : (
                exercises.map((exercise, i) => (
                  <View key={i} style={styles.exerciseCard}>
                    <View style={styles.exerciseHeader}>
                      <Text style={styles.exerciseName}>{exercise.name}</Text>
                      <Text style={styles.exerciseDuration}>{exercise.duration}</Text>
                    </View>
                    <Text style={styles.exerciseDesc}>{exercise.description}</Text>
                    <Text style={styles.exerciseBenefit}>{exercise.benefit}</Text>
                  </View>
                ))
              )}
            </>
          )}

          {activeTab === 'trends' && (
            <>
              <Text style={styles.sectionTitle}>Your Voice Over Time</Text>
              <Text style={styles.emptyText}>
                Each of these is measured from a recording and compared with your own earlier
                ones. They are acoustic measurements, not a screening for any condition.
              </Text>
              {TRACKED_FEATURES.map((feature) => {
                const trend = trends[feature.key];
                const ok = trend?.status === 'ok';
                return (
                  <View key={feature.key} style={styles.trendCard}>
                    <View style={styles.trendHeader}>
                      <Text style={styles.trendName}>{feature.label}</Text>
                      {!!ok && (
                        <View style={styles.trendDirection}>
                          <Ionicons
                            name={trend!.direction === 'increased' ? 'arrow-up' : trend!.direction === 'decreased' ? 'arrow-down' : 'remove'}
                            size={14}
                            color="#94A3B8"
                          />
                          <Text style={styles.trendChange}>
                            {trend!.change !== undefined ? Math.abs(trend!.change).toFixed(2) : ''}
                          </Text>
                        </View>
                      )}
                    </View>
                    {ok ? (
                      <Text style={styles.trendDetail}>
                        Latest {trend!.latest?.toFixed(2)} · average {trend!.average?.toFixed(2)} across{' '}
                        {trend!.data_points} recordings
                      </Text>
                    ) : (
                      <Text style={styles.trendDetail}>
                        {trend?.message ?? 'Not enough recordings yet.'}
                      </Text>
                    )}
                  </View>
                );
              })}

              <View style={styles.noteCard}>
                <Ionicons name="information-circle-outline" size={18} color="#3B82F6" />
                <Text style={styles.noteText}>
                  This app does not screen for Parkinson's, depression or any other condition
                  from your voice. Research links some vocal changes to some conditions, but
                  nothing here implements a validated instrument, so nothing here claims to.
                </Text>
              </View>
            </>
          )}

          <View style={{ height: 80 }} />
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 16, backgroundColor: '#1E293B' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#F8FAFC' },
  headerSubtitle: { fontSize: 14, color: '#94A3B8', marginTop: 4 },
  tabBar: { flexDirection: 'row', backgroundColor: '#1E293B', paddingHorizontal: 16, paddingVertical: 8 },
  tab: { flex: 1, flexDirection: 'row', gap: 6, paddingVertical: 10, justifyContent: 'center', alignItems: 'center', borderRadius: 8 },
  activeTab: { backgroundColor: '#3B82F6' },
  tabText: { color: '#94A3B8', fontSize: 13, fontWeight: '600' },
  activeTabText: { color: '#FFFFFF' },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  emptyText: { fontSize: 13, color: '#94A3B8', lineHeight: 19, marginBottom: 16 },

  targetRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  targetChip: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: '#1E293B' },
  targetText: { fontSize: 12, fontWeight: '600', color: '#94A3B8' },
  targetTextOn: { color: '#FFF' },

  exerciseCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  exerciseHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  exerciseName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', flex: 1 },
  exerciseDuration: { fontSize: 12, color: '#3B82F6', fontWeight: '600' },
  exerciseDesc: { fontSize: 13, color: '#94A3B8', lineHeight: 18 },
  exerciseBenefit: { fontSize: 12, color: '#64748B', marginTop: 6 },

  trendCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  trendHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  trendName: { fontSize: 15, fontWeight: 'bold', color: '#F8FAFC' },
  trendDirection: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  trendChange: { fontSize: 12, color: '#94A3B8', fontWeight: '600' },
  trendDetail: { fontSize: 12, color: '#94A3B8', marginTop: 6, lineHeight: 17 },

  noteCard: { flexDirection: 'row', gap: 10, backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginTop: 8 },
  noteText: { flex: 1, fontSize: 12, color: '#94A3B8', lineHeight: 18 },
});
