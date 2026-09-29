/**
 * Precision Nutrition — microbiome/metabolic-type profile and real food log.
 *
 * The gut health score the old sample showed was never computed anywhere
 * in the backend, so it's gone; what's here is the profile you set up and
 * the food you actually logged today.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, typography } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const MICROBIOME_TYPES = ['bacteroides_high', 'firmicutes_high', 'prevotella_high', 'balanced'];
const METABOLIC_TYPES = ['slow_oxidizer', 'moderate_oxidizer', 'fast_oxidizer'];

interface Profile { status?: string; microbiome?: { name: string }; metabolic?: { name: string }; macros?: { carbs_g: number; protein_g: number; fat_g: number } }
interface FoodRec { category: string; items: string[]; benefits: string; personalized_score: number }
interface DailySummary { total_calories: number; meals_logged: number }

export default function PrecisionNutritionScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [microbiome, setMicrobiome] = useState('balanced');
  const [metabolic, setMetabolic] = useState('moderate_oxidizer');
  const [meal, setMeal] = useState('');
  const [items, setItems] = useState('');
  const [calories, setCalories] = useState('');

  const { data, loading, refresh, refreshing, reload } = useApis<{
    profile: Profile;
    foods: FoodRec[];
    daily: DailySummary;
  }>({
    profile: `/precision-nutrition/profile/${userId}`,
    foods: `/precision-nutrition/food-recommendations/${userId}`,
    daily: `/precision-nutrition/daily-summary/${userId}`,
  });

  const profile = data.profile;
  const hasProfile = !!profile && profile.status !== 'no_data';
  const foods = asArray<FoodRec>(data.foods);
  const daily = data.daily;

  const setup = useCallback(async () => {
    setBusy(true);
    const result = await postJson('/precision-nutrition/profile/create', {
      user_id: userId, microbiome_type: microbiome, metabolic_type: metabolic,
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not saved', 'The profile could not be created.');
      return;
    }
    await reload();
  }, [userId, microbiome, metabolic, reload]);

  const logFood = useCallback(async () => {
    const cals = Number(calories);
    if (!meal.trim() || !items.trim() || !Number.isFinite(cals) || cals <= 0) {
      Alert.alert('Details needed', 'Enter the meal, items, and calories.');
      return;
    }
    setBusy(true);
    const result = await postJson('/precision-nutrition/food/log', {
      user_id: userId, meal: meal.trim(), items: items.split(',').map((s) => s.trim()).filter(Boolean), calories: Math.round(cals),
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not saved', 'The entry could not be logged.');
      return;
    }
    setMeal(''); setItems(''); setCalories('');
    await reload();
  }, [meal, items, calories, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#22C55E" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#22C55E" />}
      >
        <LinearGradient colors={['#22C55E', '#10B981', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Precision Nutrition</Text>
          {hasProfile ? (
            <>
              <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{profile!.microbiome?.name}</Text>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 2 }]}>{profile!.metabolic?.name}</Text>
              {profile!.macros && (
                <Text style={[typography.body.sm, { color: '#fff', marginTop: 12 }]}>
                  Target: {profile!.macros.carbs_g}g carbs · {profile!.macros.protein_g}g protein · {profile!.macros.fat_g}g fat
                </Text>
              )}
            </>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 8 }]}>Set up your profile to get recommendations.</Text>
          )}
        </LinearGradient>

        {!hasProfile && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Set Up Profile" icon="analytics" iconColor="#22C55E" />
            <GlassCard>
              <Text style={styles.helperText}>Microbiome type</Text>
              <View style={styles.chipRow}>
                {MICROBIOME_TYPES.map((m) => (
                  <TouchableOpacity key={m} style={[styles.chip, microbiome === m && styles.chipActive]} onPress={() => setMicrobiome(m)}>
                    <Text style={[styles.chipText, microbiome === m && styles.chipTextActive]}>{m.replace('_', ' ')}</Text>
                  </TouchableOpacity>
                ))}
              </View>
              <Text style={styles.helperText}>Metabolic type</Text>
              <View style={styles.chipRow}>
                {METABOLIC_TYPES.map((m) => (
                  <TouchableOpacity key={m} style={[styles.chip, metabolic === m && styles.chipActive]} onPress={() => setMetabolic(m)}>
                    <Text style={[styles.chipText, metabolic === m && styles.chipTextActive]}>{m.replace('_', ' ')}</Text>
                  </TouchableOpacity>
                ))}
              </View>
              <TouchableOpacity style={styles.primaryBtn} onPress={setup} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save profile'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {!!hasProfile && (
          <>
            <View style={styles.section}>
              <SectionHeaderPremium title="Log a Meal" icon="restaurant" iconColor="#F59E0B" />
              <GlassCard>
                <TextInput style={styles.input} placeholder="Meal (e.g. breakfast)" placeholderTextColor={colors.text.muted} value={meal} onChangeText={setMeal} />
                <TextInput style={styles.input} placeholder="Items, comma separated" placeholderTextColor={colors.text.muted} value={items} onChangeText={setItems} />
                <TextInput style={styles.input} placeholder="Calories" placeholderTextColor={colors.text.muted} keyboardType="numeric" value={calories} onChangeText={setCalories} />
                <TouchableOpacity style={styles.primaryBtn} onPress={logFood} disabled={busy}>
                  <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Log meal'}</Text>
                </TouchableOpacity>
              </GlassCard>
              {!!daily && (
                <Text style={[styles.helperText, { marginTop: 8 }]}>
                  Today: {daily.total_calories} cal across {daily.meals_logged} meal{daily.meals_logged === 1 ? '' : 's'}
                </Text>
              )}
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Food Recommendations" icon="nutrition" iconColor="#22C55E" />
              {foods.map((f) => (
                <GlassCard key={f.category} style={{ marginBottom: 10 }}>
                  <Text style={[typography.body.md, { color: colors.text.primary, textTransform: 'capitalize' }]}>{f.category.replace('_', ' ')}</Text>
                  <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 4 }]}>{f.items.join(', ')}</Text>
                </GlassCard>
              ))}
            </View>
          </>
        )}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  helperText: { color: colors.text.muted, fontSize: 13, marginBottom: 8 },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#22C55E', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  chipActive: { backgroundColor: '#22C55E20', borderColor: '#22C55E' },
  chipText: { color: colors.text.muted, fontSize: 12, textTransform: 'capitalize' },
  chipTextActive: { color: '#22C55E', fontWeight: '700' },
});
