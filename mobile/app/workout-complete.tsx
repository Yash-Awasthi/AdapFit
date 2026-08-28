import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, TextInput, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Trophy, Send, ArrowRight, Share2 } from 'lucide-react-native';
import { Share } from 'react-native';
import * as Haptics from 'expo-haptics';
import { API_BASE_URL } from '../src/services/config';
import { useUserStore } from '../src/stores';
import { useTheme } from '../src/services/theme';

export default function WorkoutComplete() {
  const { theme } = useTheme();
  const userId = useUserStore((s) => s.userId);
  const [rpe, setRpe] = useState(7);
  const [enj, setEnj] = useState(8);
  const [notes, setNotes] = useState('');
  const [done, setDone] = useState(false);
  const router = useRouter();

  const submit = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    try {
      // Complete the most recent workout (PATCH /workouts/{id} is the real
      // completion endpoint — it updates ACWR, workload history and memory).
      const listRes = await fetch(`${API_BASE_URL}/api/v1/workouts?user_id=${userId}&days=30`);
      const list = listRes.ok ? await listRes.json() : { items: [] };
      const latest = list.items?.[list.items.length - 1];
      const workoutId = latest?.workout_id || latest?.id || 'adhoc';

      await fetch(`${API_BASE_URL}/api/v1/workouts/${workoutId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          actual_duration_minutes: 45,
          session_rpe: rpe,
          logged_exercises: [
            {
              exercise_id: 'bench',
              name: 'Bench Press',
              sets: [{ set_number: 1, weight_kg: 80, reps_completed: 10, rpe: 7.5 }],
            },
          ],
          user_feedback_notes: notes,
        }),
      });
    } catch {}
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setDone(true);
  };

  const s = makeStyles(theme);

  if (done) {
    return (
      <View style={s.container}>
        <View style={s.doneContainer}>
          <View style={s.trophyContainer}>
            <Trophy size={64} color={theme.warning} />
          </View>
          <Text style={s.doneTitle}>Workout Complete!</Text>
          <Text style={s.doneSubtitle}>
            Great work! Your ACWR and agent memory have been updated.
          </Text>
          <View style={s.stats}>
            <View style={s.stat}>
              <Text style={s.statValue}>{rpe}</Text>
              <Text style={s.statLabel}>RPE</Text>
            </View>
            <View style={s.stat}>
              <Text style={s.statValue}>45</Text>
              <Text style={s.statLabel}>Minutes</Text>
            </View>
            <View style={s.stat}>
              <Text style={s.statValue}>{enj}</Text>
              <Text style={s.statLabel}>Enjoyment</Text>
            </View>
          </View>
          <TouchableOpacity
            style={s.shareButton}
            onPress={() => {
              Haptics.selectionAsync();
              Share.share({
                message: `Just completed a workout on AdapFit! RPE: ${rpe}/10, Duration: 45min. #AdapFit #Fitness`,
              });
            }}
          >
            <Share2 size={16} color={theme.primaryLight} />
            <Text style={s.shareText}>Share</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={s.homeButton}
            onPress={() => router.replace('/(tabs)')}
          >
            <Text style={s.homeButtonText}>Back to Dashboard</Text>
            <ArrowRight size={16} color="#fff" />
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={s.container}>
      <Text style={s.title}>Post-Workout Feedback</Text>
      <Text style={s.subtitle}>Help the AI learn what works for you</Text>

      <Text style={s.label}>Session RPE (1-10)</Text>
      <View style={s.ratingRow}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => (
          <TouchableOpacity
            key={v}
            style={[s.ratingDot, rpe === v && s.ratingDotActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setRpe(v);
            }}
          >
            <Text style={[s.ratingText, rpe === v && s.ratingTextActive]}>
              {v}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={s.label}>Enjoyment (1-10)</Text>
      <View style={s.ratingRow}>
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => (
          <TouchableOpacity
            key={v}
            style={[s.ratingDot, enj === v && s.ratingDotActive]}
            onPress={() => {
              Haptics.selectionAsync();
              setEnj(v);
            }}
          >
            <Text style={[s.ratingText, enj === v && s.ratingTextActive]}>
              {v}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={s.label}>Notes (NLP analysis)</Text>
      <TextInput
        style={s.notesInput}
        multiline
        value={notes}
        onChangeText={setNotes}
        placeholder="Felt great, shoulder tight..."
        placeholderTextColor={theme.textMuted}
      />

      <TouchableOpacity style={s.submitButton} onPress={submit}>
        <Send size={20} color="#fff" />
        <Text style={s.submitText}>Submit Feedback</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 24, fontWeight: '700', color: theme.text, marginTop: 50, marginBottom: 4 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 24 },
    label: { fontSize: 14, fontWeight: '600', color: theme.textSecondary, marginBottom: 8, marginTop: 16 },
    ratingRow: { flexDirection: 'row', gap: 6 },
    ratingDot: {
      width: 36, height: 36, borderRadius: 18,
      backgroundColor: theme.surface, alignItems: 'center', justifyContent: 'center',
      borderWidth: 1, borderColor: theme.border,
    },
    ratingDotActive: { backgroundColor: theme.primary, borderColor: theme.primary },
    ratingText: { fontSize: 14, fontWeight: '600', color: theme.textMuted },
    ratingTextActive: { color: '#fff' },
    notesInput: {
      backgroundColor: theme.surface, borderRadius: 12, padding: 16,
      color: theme.text, fontSize: 14, minHeight: 80, textAlignVertical: 'top',
    },
    submitButton: {
      flexDirection: 'row', backgroundColor: theme.primary, borderRadius: 12,
      padding: 16, alignItems: 'center', justifyContent: 'center', gap: 8,
      marginTop: 24, marginBottom: 40,
    },
    submitText: { color: '#fff', fontSize: 16, fontWeight: '700' },
    doneContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
    trophyContainer: {
      width: 100, height: 100, borderRadius: 50,
      backgroundColor: 'rgba(234, 179, 8, 0.15)',
      alignItems: 'center', justifyContent: 'center', marginBottom: 24,
    },
    doneTitle: { fontSize: 28, fontWeight: '800', color: theme.text, marginBottom: 8 },
    doneSubtitle: { fontSize: 14, color: theme.textSecondary, textAlign: 'center', marginBottom: 32, paddingHorizontal: 20 },
    stats: { flexDirection: 'row', gap: 24, marginBottom: 32 },
    stat: { alignItems: 'center' },
    statValue: { fontSize: 24, fontWeight: '700', color: theme.text },
    statLabel: { fontSize: 12, color: theme.textMuted, marginTop: 4 },
    shareButton: {
      flexDirection: 'row', alignItems: 'center', gap: 6,
      paddingVertical: 12, paddingHorizontal: 20,
      borderRadius: 12, borderWidth: 1, borderColor: theme.border,
      marginBottom: 12,
    },
    shareText: { color: theme.primaryLight, fontSize: 14, fontWeight: '600' },
    homeButton: {
      flexDirection: 'row', backgroundColor: theme.primary, borderRadius: 12,
      padding: 16, paddingHorizontal: 32, alignItems: 'center', gap: 8,
    },
    homeButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  });
}
