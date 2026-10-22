/**
 * Habits — small daily habits with streaks counted from the days you
 * actually did them. One tap a day; a missed day resets the current streak
 * but never the best one.
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import { colors, spacing } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, deleteJson, postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const TINT = '#14B8A6';

interface MyHabit { habit_id: string; name: string; category: string; current_streak: number; best_streak: number; total_completions: number; completed_today: boolean }
interface CatalogHabit { id: string; name: string; description: string; category: string; time_required: number }

export default function HabitsScreen() {
  const userId = useUserStore((s) => s.userId);
  const [name, setName] = useState('');
  const [cue, setCue] = useState('');
  const { data, loading, refresh, refreshing, reload } = useApis<{
    mine: { habits: MyHabit[] };
    ideas: { suggestions: CatalogHabit[] };
    nudge: { message: string };
  }>({
    mine: `/habits/user/${userId}`,
    ideas: '/habits/suggest',
    nudge: `/habits/nudge/${userId}`,
  });
  const mine = asArray<MyHabit>(data.mine?.habits);
  const tracked = new Set(mine.map((h) => h.habit_id));
  const ideas = asArray<CatalogHabit>(data.ideas?.suggestions).filter((h) => !tracked.has(h.id));

  const complete = async (h: MyHabit) => {
    if (h.completed_today) return;
    if (await postJson(`/habits/complete/${h.habit_id}?user_id=${userId}`)) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      reload();
    }
  };
  const add = async (habitId: string) => {
    if (await postJson('/habits/add', { user_id: userId, habit_id: habitId })) reload();
  };
  const addCustom = async () => {
    if (!name.trim()) return;
    const r = await postJson<{ stacking_tip?: string }>('/habits/custom', { user_id: userId, name: name.trim(), cue: cue.trim() });
    if (!r) return Alert.alert('Not added', 'The habit could not be saved.');
    setName('');
    setCue('');
    if (r.stacking_tip) Alert.alert('Added', r.stacking_tip);
    reload();
  };
  const remove = (h: MyHabit) => Alert.alert('Stop tracking?', h.name, [
    { text: 'Cancel', style: 'cancel' },
    { text: 'Remove', style: 'destructive', onPress: async () => { await deleteJson(`/habits/${h.habit_id}?user_id=${userId}`); reload(); } },
  ]);

  if (loading) return <View style={[styles.container, styles.center]}><ActivityIndicator size="large" color={TINT} /></View>;

  const doneToday = mine.filter((h) => h.completed_today).length;

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={{ paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={TINT} />}>
        <LinearGradient colors={[TINT, '#0F766E', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Habits</Text>
          <Text style={styles.heroTitle}>{mine.length ? `${doneToday} of ${mine.length} done today` : 'Start one small habit'}</Text>
          {mine.length > 0 && data.nudge?.message ? <Text style={styles.heroBody}>{data.nudge.message}</Text> : null}
        </LinearGradient>

        {mine.length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Today" icon="checkbox" iconColor={TINT} />
            {mine.map((h) => (
              <TouchableOpacity key={h.habit_id} onPress={() => complete(h)} onLongPress={() => remove(h)}>
                <GlassCard style={styles.row}>
                  <Ionicons name={h.completed_today ? 'checkmark-circle' : 'ellipse-outline'} size={28} color={h.completed_today ? TINT : colors.text.muted} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.title}>{h.name}</Text>
                    <Text style={styles.sub}>Streak {h.current_streak} · best {h.best_streak} · {h.total_completions} total</Text>
                  </View>
                </GlassCard>
              </TouchableOpacity>
            ))}
            <Text style={styles.sub}>Tap to mark done. Long-press to stop tracking.</Text>
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="Your Own Habit" icon="create" iconColor={TINT} />
          <GlassCard>
            <TextInput style={styles.input} placeholder="Habit (e.g. 10 surya namaskars)" placeholderTextColor={colors.text.muted} value={name} onChangeText={setName} maxLength={60} />
            <TextInput style={styles.input} placeholder="After I… (e.g. brush my teeth)" placeholderTextColor={colors.text.muted} value={cue} onChangeText={setCue} maxLength={80} />
            <TouchableOpacity style={styles.primaryBtn} onPress={addCustom}><Text style={styles.primaryBtnText}>Add habit</Text></TouchableOpacity>
          </GlassCard>
        </View>

        {ideas.length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Ideas" icon="bulb" iconColor={TINT} />
            {ideas.map((h) => (
              <GlassCard key={h.id} style={styles.row}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.title}>{h.name}</Text>
                  <Text style={styles.sub}>{h.description} · {h.time_required} min</Text>
                </View>
                <TouchableOpacity onPress={() => add(h.id)} accessibilityLabel={`Track ${h.name}`}>
                  <Ionicons name="add-circle" size={28} color={TINT} />
                </TouchableOpacity>
              </GlassCard>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { paddingLeft: 40, color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroTitle: { color: '#fff', fontSize: 24, fontWeight: '800', marginTop: 6 },
  heroBody: { color: 'rgba(255,255,255,0.9)', fontSize: 14, marginTop: 8, lineHeight: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 10 },
  title: { color: colors.text.primary, fontSize: 15, fontWeight: '700' },
  sub: { color: colors.text.muted, fontSize: 12, marginTop: 2 },
  input: { backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10 },
  primaryBtn: { backgroundColor: TINT, borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
});
