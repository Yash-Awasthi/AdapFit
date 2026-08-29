/**
 * Mental Health — Premium Mental Wellness Dashboard
 * Mood tracker, PHQ-9/GAD-7 assessments, journal, crisis resources
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, glass } from '../../src/theme';
import {
  ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium, QuickAction,
} from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

const MOOD_EMOJIS = [
  { emoji: '😊', label: 'Happy', value: 8, color: '#22C55E' },
  { emoji: '😌', label: 'Calm', value: 7, color: '#06B6D4' },
  { emoji: '😐', label: 'Neutral', value: 5, color: '#F59E0B' },
  { emoji: '😔', label: 'Sad', value: 3, color: '#6366F1' },
  { emoji: '😰', label: 'Anxious', value: 2, color: '#EF4444' },
  { emoji: '😤', label: 'Angry', value: 2, color: '#F97316' },
  { emoji: '😴', label: 'Tired', value: 4, color: '#8B5CF6' },
  { emoji: '🥳', label: 'Excited', value: 9, color: '#EC4899' },
];

const ASSESSMENTS = [
  { id: 'phq9', title: 'PHQ-9 Depression', description: 'Standard depression screening', icon: 'heart-half', color: '#6366F1', questions: 9 },
  { id: 'gad7', title: 'GAD-7 Anxiety', description: 'Generalized anxiety assessment', icon: 'brain', color: '#EF4444', questions: 7 },
  { id: 'audit', title: 'AUDIT Alcohol', description: 'Alcohol use screening', icon: 'wine', color: '#F97316', questions: 10 },
];

const JOURNAL_ENTRIES = [
  { date: 'Today', mood: 7, entry: 'Had a great workout this morning. Feeling accomplished.', emoji: '😊' },
  { date: 'Yesterday', mood: 5, entry: 'Busy day at work, need to manage stress better.', emoji: '😐' },
  { date: '2 days ago', mood: 8, entry: 'Meditation session was amazing. Clear mind.', emoji: '😌' },
];

const CRISIS_RESOURCES = [
  { name: '988 Suicide & Crisis Lifeline', phone: '988', icon: 'call', color: '#EF4444' },
  { name: 'Crisis Text Line', phone: 'Text HOME to 741741', icon: 'chatbubble', color: '#6366F1' },
  { name: 'SAMHSA Helpline', phone: '1-800-662-4357', icon: 'medical', color: '#22C55E' },
];

export default function MentalHealthScreen() {
  const [selectedMood, setSelectedMood] = useState<number | null>(null);
  const [wellbeingScore, setWellbeingScore] = useState(72);
  const [fadeAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  const logMood = async () => {
    if (selectedMood === null) return;
    try {
      await fetch(`${API}/mental-health/mood`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood_score: selectedMood, notes: '' }),
      });
    } catch {}
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <LinearGradient colors={['#8B5CF6', '#A78BFA']} style={styles.header}>
        <Text style={styles.headerTitle}>🧠 Mental Health</Text>
        <Text style={styles.headerSubtitle}>Your emotional wellness companion</Text>
      </LinearGradient>

      {/* Wellbeing Score */}
      <View style={styles.scoreSection}>
        <ScoreRing score={wellbeingScore} size={130} strokeWidth={8} color={colors.health.mental} label="WELLBEING" sublabel="Good" />
      </View>

      {/* Mood Check-in */}
      <SectionHeaderPremium icon="happy" iconColor={colors.health.mental} title="How are you feeling?" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <View style={styles.moodGrid}>
          {MOOD_EMOJIS.map((mood, i) => (
            <TouchableOpacity
              key={i}
              style={[styles.moodBtn, selectedMood === mood.value && { backgroundColor: mood.color + '25', borderColor: mood.color + '50', transform: [{ scale: 1.1 }] }]}
              onPress={() => setSelectedMood(mood.value)}
            >
              <Text style={styles.moodEmoji}>{mood.emoji}</Text>
              <Text style={[styles.moodLabel, selectedMood === mood.value && { color: mood.color }]}>{mood.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {selectedMood !== null && (
          <TouchableOpacity style={styles.logMoodBtn} onPress={logMood}>
            <Ionicons name="checkmark-circle" size={18} color="#FFF" />
            <Text style={styles.logMoodBtnText}>Log Mood</Text>
          </TouchableOpacity>
        )}
      </GlassCard>

      {/* Quick Actions */}
      <View style={styles.quickActionsRow}>
        <QuickAction icon="book" label="Journal" color={colors.health.mental} onPress={() => {}} />
        <QuickAction icon="meditate" label="Meditate" color={colors.health.calm} onPress={() => {}} />
        <QuickAction icon="phone" label="Crisis Help" color={colors.health.heart} onPress={() => {}} />
        <QuickAction icon="analytics" label="Trends" color="#F59E0B" onPress={() => {}} />
      </View>

      {/* Assessments */}
      <SectionHeaderPremium icon="clipboard" iconColor="#6366F1" title="Screening Assessments" />
      {ASSESSMENTS.map((assessment, i) => (
        <GlassCard key={i} variant="light" style={styles.assessmentCard}>
          <View style={styles.assessmentRow}>
            <View style={[styles.assessmentIcon, { backgroundColor: assessment.color + '15' }]}>
              <Ionicons name={assessment.icon as any} size={20} color={assessment.color} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.assessmentTitle}>{assessment.title}</Text>
              <Text style={styles.assessmentDesc}>{assessment.description}</Text>
              <Text style={styles.assessmentQuestions}>{assessment.questions} questions • ~3 min</Text>
            </View>
            <TouchableOpacity style={[styles.assessmentBtn, { backgroundColor: assessment.color + '15' }]}>
              <Text style={[styles.assessmentBtnText, { color: assessment.color }]}>Start</Text>
            </TouchableOpacity>
          </View>
        </GlassCard>
      ))}

      {/* Journal Entries */}
      <SectionHeaderPremium icon="book" iconColor="#EC4899" title="Recent Journal Entries" />
      {JOURNAL_ENTRIES.map((entry, i) => (
        <GlassCard key={i} variant="light" style={styles.journalCard}>
          <View style={styles.journalHeader}>
            <Text style={styles.journalDate}>{entry.date}</Text>
            <Text style={styles.journalMood}>{entry.emoji} {entry.mood}/10</Text>
          </View>
          <Text style={styles.journalEntry}>{entry.entry}</Text>
        </GlassCard>
      ))}

      {/* Crisis Resources */}
      <SectionHeaderPremium icon="alert-circle" iconColor={colors.health.heart} title="Crisis Resources" />
      {CRISIS_RESOURCES.map((resource, i) => (
        <TouchableOpacity key={i} style={styles.crisisCard}>
          <View style={[styles.crisisIcon, { backgroundColor: resource.color + '15' }]}>
            <Ionicons name={resource.icon as any} size={18} color={resource.color} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.crisisName}>{resource.name}</Text>
            <Text style={styles.crisisPhone}>{resource.phone}</Text>
          </View>
          <Ionicons name="call" size={20} color={resource.color} />
        </TouchableOpacity>
      ))}

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },

  // Header
  header: { paddingTop: 56, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  // Score
  scoreSection: { alignItems: 'center', marginTop: spacing.xl, marginBottom: spacing.lg },

  // Mood
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  moodGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, justifyContent: 'center' },
  moodBtn: { alignItems: 'center', width: 72, padding: spacing.sm, borderRadius: radius.lg, backgroundColor: colors.bg.input, borderWidth: 1, borderColor: colors.surface.border },
  moodEmoji: { fontSize: 28 },
  moodLabel: { fontSize: 10, fontWeight: '600', color: colors.text.muted, marginTop: 4 },
  logMoodBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm,
    backgroundColor: colors.health.sleep, paddingVertical: spacing.md, borderRadius: radius.button, marginTop: spacing.lg,
  },
  logMoodBtnText: { fontSize: 15, fontWeight: '700', color: '#FFF' },

  // Quick Actions
  quickActionsRow: { flexDirection: 'row', justifyContent: 'space-around', paddingHorizontal: spacing.screenPadding, marginBottom: spacing.xl },

  // Assessments
  assessmentCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  assessmentRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  assessmentIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  assessmentTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  assessmentDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  assessmentQuestions: { fontSize: 11, color: colors.text.muted, marginTop: 4 },
  assessmentBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8 },
  assessmentBtnText: { fontSize: 13, fontWeight: '700' },

  // Journal
  journalCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  journalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xs },
  journalDate: { fontSize: 12, fontWeight: '600', color: colors.text.muted },
  journalMood: { fontSize: 13, fontWeight: '600', color: colors.health.mental },
  journalEntry: { fontSize: 14, color: colors.text.secondary, lineHeight: 20 },

  // Crisis
  crisisCard: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm,
    backgroundColor: colors.bg.card, padding: spacing.lg, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.health.danger + '20',
  },
  crisisIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  crisisName: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  crisisPhone: { fontSize: 12, color: colors.health.danger, marginTop: 2 },
});
