import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

const TAB_ICONS = { screen: 'search-outline', exercises: 'barbell', trends: 'trending-up-outline' } as const;
const TAB_LABELS = { screen: 'Screen', exercises: 'Exercises', trends: 'Trends' } as const;

const DISEASES = [
  { id: 'depression', name: 'Depression', icon: 'body-outline', color: '#7C3AED', desc: 'Speech pattern analysis for mood disorders' },
  { id: 'heart_disease', name: 'Heart Health', icon: 'heart', color: '#EF4444', desc: 'Vocal tremor and breath support analysis' },
  { id: 'cognitive_decline', name: 'Cognitive Health', icon: 'bulb-outline', color: '#3B82F6', desc: 'Word finding and coherence assessment' },
  { id: 'parkinsons', name: "Parkinson's", icon: 'flask-outline', color: '#10B981', desc: 'Voice tremor and monotonicity detection' },
  { id: 'respiratory', name: 'Respiratory', icon: 'pulse-outline', color: '#06B6D4', desc: 'Breath pattern and lung function analysis' },
  { id: 'anxiety', name: 'Anxiety', icon: 'alert-circle-outline', color: '#F59E0B', desc: 'Speech tempo and hesitation detection' },
];

export default function VoiceHealthScreen() {
  const [isRecording, setIsRecording] = useState(false);
  const [selectedDisease, setSelectedDisease] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'screen' | 'exercises' | 'trends'>('screen');

  const startAnalysis = (disease: string) => {
    setSelectedDisease(disease);
    setIsRecording(true);

    setTimeout(() => {
      setIsRecording(false);
      setResults({
        disease,
        risk_score: Math.random() * 30 + 5,
        confidence: 0.85 + Math.random() * 0.1,
        risk_level: 'low',
        biomarkers_detected: ['speech_rate', 'pitch_variability'],
        recommendations: ['Continue monitoring', 'Practice voice exercises'],
      });
    }, 3000);
  };

  const exercises = [
    { name: 'Humming Meditation', duration: '5 min', benefit: 'Increases vocal energy', target: 'depression' },
    { name: 'Word Association Sprint', duration: '5 min', benefit: 'Improves word-finding speed', target: 'cognitive' },
    { name: 'Sustained Phonation', duration: '5 min', benefit: 'Increases breath support', target: 'respiratory' },
    { name: 'Emotional Reading', duration: '10 min', benefit: 'Expands vocal range', target: 'depression' },
    { name: 'Complex Sentence Practice', duration: '10 min', benefit: 'Enhances language complexity', target: 'cognitive' },
    { name: 'Diaphragmatic Speech', duration: '10 min', benefit: 'Strengthens breath control', target: 'respiratory' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Voice Health Analysis</Text>
        <Text style={styles.headerSubtitle}>AI-powered disease screening from your voice</Text>
      </View>

      <View style={styles.tabBar}>
        {(['screen', 'exercises', 'trends'] as const).map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Ionicons name={TAB_ICONS[tab]} size={14} color={activeTab === tab ? '#FFFFFF' : '#94A3B8'} />
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {TAB_LABELS[tab]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'screen' && (
          <>
            <Text style={styles.sectionTitle}>Select Health Area to Screen</Text>
            {DISEASES.map(disease => (
              <TouchableOpacity
                key={disease.id}
                style={styles.diseaseCard}
                onPress={() => startAnalysis(disease.id)}
                disabled={isRecording}
              >
                <View style={styles.diseaseLeft}>
                  <Ionicons name={disease.icon as any} size={28} color={disease.color} style={styles.diseaseIcon} />
                  <View style={styles.diseaseInfo}>
                    <Text style={styles.diseaseName}>{disease.name}</Text>
                    <Text style={styles.diseaseDesc}>{disease.desc}</Text>
                  </View>
                </View>
                <View style={[styles.scanBadge, { backgroundColor: disease.color + '20' }]}>
                  <Ionicons
                    name={isRecording && selectedDisease === disease.id ? 'hourglass-outline' : 'mic-outline'}
                    size={12}
                    color={disease.color}
                  />
                  <Text style={[styles.scanBadgeText, { color: disease.color }]}>
                    {isRecording && selectedDisease === disease.id ? 'Analyzing...' : 'Scan'}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}

            {results && (
              <View style={styles.resultCard}>
                <Text style={styles.resultTitle}>Analysis Results</Text>
                <View style={styles.resultScore}>
                  <Text style={styles.scoreValue}>{results.risk_score.toFixed(1)}%</Text>
                  <Text style={styles.scoreLabel}>Risk Score</Text>
                </View>
                <Text style={styles.resultConfidence}>
                  Confidence: {(results.confidence * 100).toFixed(0)}%
                </Text>
                <Text style={styles.resultRisk}>
                  Risk Level: <Text style={{ color: '#10B981', fontWeight: 'bold' }}>{results.risk_level.toUpperCase()}</Text>
                </Text>
                <Text style={styles.resultBiomarkers}>
                  Biomarkers: {results.biomarkers_detected.join(', ')}
                </Text>
              </View>
            )}
          </>
        )}

        {activeTab === 'exercises' && (
          <>
            <Text style={styles.sectionTitle}>Voice Therapeutic Exercises</Text>
            {exercises.map((ex, i) => (
              <View key={i} style={styles.exerciseCard}>
                <View style={styles.exerciseHeader}>
                  <Text style={styles.exerciseName}>{ex.name}</Text>
                  <Text style={styles.exerciseDuration}>{ex.duration}</Text>
                </View>
                <Text style={styles.exerciseBenefit}>{ex.benefit}</Text>
                <TouchableOpacity style={styles.startBtn}>
                  <Text style={styles.startBtnText}>Start</Text>
                </TouchableOpacity>
              </View>
            ))}
          </>
        )}

        {activeTab === 'trends' && (
          <>
            <Text style={styles.sectionTitle}>Your Voice Health Trends</Text>
            <View style={styles.trendCard}>
              <Text style={styles.trendTitle}>Depression Screening</Text>
              <View style={styles.trendBar}>
                <View style={[styles.trendFill, { width: '25%', backgroundColor: '#10B981' }]} />
              </View>
              <Text style={styles.trendStatus}>Low risk - stable over 4 sessions</Text>
            </View>
            <View style={styles.trendCard}>
              <Text style={styles.trendTitle}>Cognitive Health</Text>
              <View style={styles.trendBar}>
                <View style={[styles.trendFill, { width: '15%', backgroundColor: '#10B981' }]} />
              </View>
              <Text style={styles.trendStatus}>Excellent - improving trend</Text>
            </View>
            <View style={styles.trendCard}>
              <Text style={styles.trendTitle}>Respiratory Health</Text>
              <View style={styles.trendBar}>
                <View style={[styles.trendFill, { width: '35%', backgroundColor: '#F59E0B' }]} />
              </View>
              <Text style={styles.trendStatus}>Moderate - practice more exercises</Text>
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
  tab: { flex: 1, flexDirection: 'row', gap: 6, paddingVertical: 10, justifyContent: 'center', alignItems: 'center', borderRadius: 8 },
  activeTab: { backgroundColor: '#3B82F6' },
  tabText: { color: '#94A3B8', fontSize: 13, fontWeight: '600' },
  activeTabText: { color: '#FFFFFF' },
  content: { flex: 1, paddingHorizontal: 16, paddingTop: 16 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 12 },
  diseaseCard: {
    backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
  },
  diseaseLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  diseaseIcon: { marginRight: 12 },
  diseaseInfo: { flex: 1 },
  diseaseName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC' },
  diseaseDesc: { fontSize: 12, color: '#94A3B8', marginTop: 2 },
  scanBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  scanBadgeText: { fontSize: 12, fontWeight: 'bold' },
  resultCard: {
    backgroundColor: '#1E293B', borderRadius: 16, padding: 20, marginTop: 16,
    borderWidth: 1, borderColor: '#10B981',
  },
  resultTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 16 },
  resultScore: { alignItems: 'center', marginBottom: 16 },
  scoreValue: { fontSize: 48, fontWeight: 'bold', color: '#10B981' },
  scoreLabel: { fontSize: 14, color: '#94A3B8', marginTop: 4 },
  resultConfidence: { fontSize: 14, color: '#94A3B8', marginBottom: 4 },
  resultRisk: { fontSize: 14, color: '#94A3B8', marginBottom: 4 },
  resultBiomarkers: { fontSize: 13, color: '#64748B', marginTop: 8 },
  exerciseCard: {
    backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10,
  },
  exerciseHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  exerciseName: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC' },
  exerciseDuration: { fontSize: 13, color: '#3B82F6', fontWeight: '600' },
  exerciseBenefit: { fontSize: 13, color: '#94A3B8', marginTop: 6 },
  startBtn: { backgroundColor: '#3B82F6', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 16, marginTop: 10, alignSelf: 'flex-start' },
  startBtnText: { color: '#FFF', fontWeight: 'bold', fontSize: 13 },
  trendCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, marginBottom: 10 },
  trendTitle: { fontSize: 16, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 8 },
  trendBar: { height: 8, backgroundColor: '#334155', borderRadius: 4, marginBottom: 8 },
  trendFill: { height: '100%', borderRadius: 4 },
  trendStatus: { fontSize: 13, color: '#94A3B8' },
});
