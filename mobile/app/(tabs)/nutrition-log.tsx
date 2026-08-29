/**
 * Nutrition Log — Premium Nutrition Tracking
 * Glassmorphism cards, macro rings, meal cards, food search
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, glass } from '../../src/theme';
import {
  ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium, StatCard,
} from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const API = 'http://localhost:8000/api/v1';

const MACRO_COLORS = {
  protein: '#EF4444',
  carbs: '#F59E0B',
  fat: '#22C55E',
  fiber: '#06B6D4',
};

const FOOD_DATABASE = [
  { name: 'Grilled Chicken Breast', calories: 248, protein: 46, carbs: 0, fat: 5, icon: '🍖' },
  { name: 'Brown Rice', calories: 216, protein: 5, carbs: 45, fat: 2, icon: '🍚' },
  { name: 'Salmon Fillet', calories: 367, protein: 39, carbs: 0, fat: 22, icon: '🐟' },
  { name: 'Avocado', calories: 322, protein: 4, carbs: 17, fat: 30, icon: '🥑' },
  { name: 'Greek Yogurt', calories: 130, protein: 23, carbs: 8, fat: 1, icon: '🥛' },
  { name: 'Banana', calories: 105, protein: 1, carbs: 27, fat: 0, icon: '🍌' },
  { name: 'Eggs (2)', calories: 148, protein: 13, carbs: 1, fat: 10, icon: '🥚' },
  { name: 'Oatmeal', calories: 154, protein: 5, carbs: 27, fat: 3, icon: '🥣' },
  { name: 'Sweet Potato', calories: 115, protein: 2, carbs: 27, fat: 0, icon: '🍠' },
  { name: 'Almonds', calories: 164, protein: 6, carbs: 6, fat: 14, icon: '🥜' },
];

const MEALS = [
  { name: 'Breakfast', icon: 'sunny', color: '#F59E0B', time: '8:00 AM' },
  { name: 'Lunch', icon: 'restaurant', color: '#22C55E', time: '12:30 PM' },
  { name: 'Dinner', icon: 'moon', color: '#6366F1', time: '7:00 PM' },
  { name: 'Snacks', icon: 'cookie', color: '#F97316', time: '3:00 PM' },
];

export default function NutritionLogScreen() {
  const [search, setSearch] = useState('');
  const [totalCalories, setTotalCalories] = useState(1850);
  const [totalProtein, setTotalProtein] = useState(120);
  const [totalCarbs, setTotalCarbs, ] = useState(210);
  const [totalFat, setTotalFat] = useState(65);
  const [selectedMeal, setSelectedMeal] = useState(0);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  const calorieTarget = 2200;
  const proteinTarget = 150;
  const carbsTarget = 275;
  const fatTarget = 75;

  useEffect(() => {
    Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
  }, []);

  const calorieProgress = Math.min(100, (totalCalories / calorieTarget) * 100);
  const proteinProgress = Math.min(100, (totalProtein / proteinTarget) * 100);
  const carbsProgress = Math.min(100, (totalCarbs / carbsTarget) * 100);
  const fatProgress = Math.min(100, (totalFat / fatTarget) * 100);

  const filteredFoods = search
    ? FOOD_DATABASE.filter(f => f.name.toLowerCase().includes(search.toLowerCase()))
    : FOOD_DATABASE;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <LinearGradient colors={['#22C55E', '#06B6D4']} style={styles.header}>
        <Text style={styles.headerTitle}>🥗 Nutrition Log</Text>
        <Text style={styles.headerSubtitle}>Track your daily nutrition intake</Text>
      </LinearGradient>

      {/* Calorie Ring */}
      <View style={styles.calorieSection}>
        <ScoreRing score={calorieProgress} size={140} strokeWidth={10} color={calorieProgress > 90 ? colors.health.heart : colors.health.nutrition} label="CALORIES" />
        <View style={styles.calorieInfo}>
          <Text style={styles.calorieConsumed}>{totalCalories}</Text>
          <Text style={styles.calorieTarget}>/ {calorieTarget} kcal</Text>
          <Text style={styles.calorieRemaining}>{calorieTarget - totalCalories} remaining</Text>
        </View>
      </View>

      {/* Macro Breakdown */}
      <SectionHeaderPremium icon="pie-chart" iconColor={colors.health.nutrition} title="Macros" />
      <View style={styles.macroGrid}>
        <GlassCard variant="light" style={styles.macroCard}>
          <View style={[styles.macroIcon, { backgroundColor: MACRO_COLORS.protein + '15' }]}>
            <Ionicons name="flash" size={18} color={MACRO_COLORS.protein} />
          </View>
          <Text style={[styles.macroValue, { color: MACRO_COLORS.protein }]}>{totalProtein}g</Text>
          <Text style={styles.macroLabel}>Protein</Text>
          <ProgressBarPremium value={totalProtein} max={proteinTarget} color={MACRO_COLORS.protein} height={4} />
          <Text style={styles.macroTarget}>{proteinTarget}g target</Text>
        </GlassCard>
        <GlassCard variant="light" style={styles.macroCard}>
          <View style={[styles.macroIcon, { backgroundColor: MACRO_COLORS.carbs + '15' }]}>
            <Ionicons name="leaf" size={18} color={MACRO_COLORS.carbs} />
          </View>
          <Text style={[styles.macroValue, { color: MACRO_COLORS.carbs }]}>{totalCarbs}g</Text>
          <Text style={styles.macroLabel}>Carbs</Text>
          <ProgressBarPremium value={totalCarbs} max={carbsTarget} color={MACRO_COLORS.carbs} height={4} />
          <Text style={styles.macroTarget}>{carbsTarget}g target</Text>
        </GlassCard>
        <GlassCard variant="light" style={styles.macroCard}>
          <View style={[styles.macroIcon, { backgroundColor: MACRO_COLORS.fat + '15' }]}>
            <Ionicons name="water" size={18} color={MACRO_COLORS.fat} />
          </View>
          <Text style={[styles.macroValue, { color: MACRO_COLORS.fat }]}>{totalFat}g</Text>
          <Text style={styles.macroLabel}>Fat</Text>
          <ProgressBarPremium value={totalFat} max={fatTarget} color={MACRO_COLORS.fat} height={4} />
          <Text style={styles.macroTarget}>{fatTarget}g target</Text>
        </GlassCard>
      </View>

      {/* Meal Sections */}
      <SectionHeaderPremium icon="restaurant" iconColor="#F59E0B" title="Today's Meals" />
      <View style={styles.mealTabs}>
        {MEALS.map((meal, i) => (
          <TouchableOpacity
            key={i}
            style={[styles.mealTab, selectedMeal === i && { backgroundColor: meal.color + '20', borderColor: meal.color + '50' }]}
            onPress={() => setSelectedMeal(i)}
          >
            <Ionicons name={meal.icon as any} size={16} color={selectedMeal === i ? meal.color : colors.text.muted} />
            <Text style={[styles.mealTabText, selectedMeal === i && { color: meal.color }]}>{meal.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Food Search */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={18} color={colors.text.muted} />
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder="Search foods..."
            placeholderTextColor={colors.text.muted}
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => setSearch('')}>
              <Ionicons name="close-circle" size={18} color={colors.text.muted} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Food List */}
      <View style={styles.foodGrid}>
        {filteredFoods.map((food, i) => (
          <TouchableOpacity key={i} style={styles.foodCard}>
            <Text style={styles.foodIcon}>{food.icon}</Text>
            <Text style={styles.foodName} numberOfLines={1}>{food.name}</Text>
            <Text style={styles.foodCalories}>{food.calories} kcal</Text>
            <View style={styles.foodMacros}>
              <Text style={[styles.foodMacro, { color: MACRO_COLORS.protein }]}>P: {food.protein}g</Text>
              <Text style={[styles.foodMacro, { color: MACRO_COLORS.carbs }]}>C: {food.carbs}g</Text>
              <Text style={[styles.foodMacro, { color: MACRO_COLORS.fat }]}>F: {food.fat}g</Text>
            </View>
            <TouchableOpacity style={styles.addBtn}>
              <Ionicons name="add-circle" size={24} color={colors.health.nutrition} />
            </TouchableOpacity>
          </TouchableOpacity>
        ))}
      </View>

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

  // Calorie Section
  calorieSection: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xl, marginTop: spacing.xl, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  calorieInfo: { alignItems: 'center' },
  calorieConsumed: { fontSize: 32, fontWeight: '800', color: colors.text.primary },
  calorieTarget: { fontSize: 14, color: colors.text.muted },
  calorieRemaining: { fontSize: 12, color: colors.health.nutrition, fontWeight: '600', marginTop: 4 },

  // Macros
  macroGrid: { flexDirection: 'row', gap: spacing.md, paddingHorizontal: spacing.screenPadding },
  macroCard: { flex: 1, alignItems: 'center' },
  macroIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.xs },
  macroValue: { fontSize: 20, fontWeight: '800' },
  macroLabel: { fontSize: 12, color: colors.text.muted, marginTop: 2, marginBottom: spacing.sm },
  macroTarget: { fontSize: 10, color: colors.text.muted, marginTop: spacing.xs },

  // Meal Tabs
  mealTabs: { flexDirection: 'row', gap: spacing.sm, paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  mealTab: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border },
  mealTabText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },

  // Search
  searchContainer: { paddingHorizontal: spacing.screenPadding, marginBottom: spacing.lg },
  searchBar: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, backgroundColor: colors.bg.card, paddingHorizontal: spacing.lg, paddingVertical: spacing.md, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.surface.border },
  searchInput: { flex: 1, color: colors.text.primary, fontSize: 15 },

  // Food Grid
  foodGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, paddingHorizontal: spacing.screenPadding },
  foodCard: {
    width: (SCREEN_WIDTH - spacing.screenPadding * 2 - spacing.md) / 2,
    backgroundColor: colors.bg.card, borderRadius: radius.lg, padding: spacing.md,
    borderWidth: 1, borderColor: colors.surface.border,
  },
  foodIcon: { fontSize: 28, marginBottom: spacing.xs },
  foodName: { fontSize: 13, fontWeight: '600', color: colors.text.primary },
  foodCalories: { fontSize: 12, color: colors.health.nutrition, fontWeight: '700', marginTop: 2 },
  foodMacros: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs },
  foodMacro: { fontSize: 10, fontWeight: '600' },
  addBtn: { position: 'absolute', top: spacing.sm, right: spacing.sm },
});
