/**
 * Quick Nutrition Logger — fast meal logging with macro estimation.
 * Supports quick-add presets and manual entry.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { Plus, Camera, Zap, Coffee, Utensils, Apple, Moon } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { useTheme } from '../services/theme';

interface MealEntry {
  id: string;
  name: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  meal_type: string;
  timestamp: string;
}

const QUICK_MEALS: { name: string; cal: number; p: number; c: number; f: number; icon: any }[] = [
  { name: 'Chicken Breast (200g)', cal: 330, p: 62, c: 0, f: 7, icon: Utensils },
  { name: 'Rice (1 cup)', cal: 206, p: 4, c: 45, f: 0.4, icon: Utensils },
  { name: 'Banana', cal: 105, p: 1, c: 27, f: 0.3, icon: Apple },
  { name: 'Protein Shake', cal: 150, p: 30, c: 3, f: 2, icon: Zap },
  { name: 'Eggs (3)', cal: 234, p: 21, c: 1, f: 16, icon: Utensils },
  { name: 'Greek Yogurt (200g)', cal: 130, p: 20, c: 8, f: 2, icon: Utensils },
  { name: 'Oats (100g)', cal: 389, p: 17, c: 66, f: 7, icon: Utensils },
  { name: 'Sweet Potato (200g)', cal: 172, p: 3, c: 41, f: 0.2, icon: Apple },
  { name: 'Salmon (150g)', cal: 280, p: 34, c: 0, f: 16, icon: Utensils },
  { name: 'Almonds (30g)', cal: 173, p: 6, c: 6, f: 15, icon: Apple },
  { name: 'Avocado', cal: 234, p: 3, c: 12, f: 21, icon: Apple },
  { name: 'Cottage Cheese (150g)', cal: 120, p: 14, c: 5, f: 5, icon: Utensils },
];

const MEAL_TYPES = [
  { id: 'breakfast', label: 'Breakfast', icon: Coffee, color: '#F59E0B' },
  { id: 'lunch', label: 'Lunch', icon: Utensils, color: '#22C55E' },
  { id: 'dinner', label: 'Dinner', icon: Moon, color: '#6366F1' },
  { id: 'snack', label: 'Snack', icon: Apple, color: '#EC4899' },
];

interface NutritionLoggerProps {
  onLogMeal?: (meal: MealEntry) => void;
  dailyGoal?: { calories: number; protein: number };
}

export function NutritionLogger({ onLogMeal, dailyGoal }: NutritionLoggerProps) {
  const { theme } = useTheme();
  const [selectedMealType, setSelectedMealType] = useState('lunch');
  const [customName, setCustomName] = useState('');
  const [customCal, setCustomCal] = useState('');
  const [customProtein, setCustomProtein] = useState('');
  const [customCarbs, setCustomCarbs] = useState('');
  const [customFat, setCustomFat] = useState('');
  const [todayMeals, setTodayMeals] = useState<MealEntry[]>([]);

  const totalCal = todayMeals.reduce((s, m) => s + m.calories, 0);
  const totalProtein = todayMeals.reduce((s, m) => s + m.protein, 0);
  const totalCarbs = todayMeals.reduce((s, m) => s + m.carbs, 0);
  const totalFat = todayMeals.reduce((s, m) => s + m.fat, 0);

  const calGoal = dailyGoal?.calories || 2500;
  const proteinGoal = dailyGoal?.protein || 150;

  function addQuickMeal(meal: typeof QUICK_MEALS[0]) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const entry: MealEntry = {
      id: Date.now().toString(),
      name: meal.name,
      calories: meal.cal,
      protein: meal.p,
      carbs: meal.c,
      fat: meal.f,
      meal_type: selectedMealType,
      timestamp: new Date().toISOString(),
    };
    setTodayMeals((prev) => [...prev, entry]);
    onLogMeal?.(entry);
  }

  function addCustomMeal() {
    if (!customName.trim()) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    const entry: MealEntry = {
      id: Date.now().toString(),
      name: customName,
      calories: parseInt(customCal) || 0,
      protein: parseInt(customProtein) || 0,
      carbs: parseInt(customCarbs) || 0,
      fat: parseInt(customFat) || 0,
      meal_type: selectedMealType,
      timestamp: new Date().toISOString(),
    };
    setTodayMeals((prev) => [...prev, entry]);
    onLogMeal?.(entry);
    setCustomName('');
    setCustomCal('');
    setCustomProtein('');
    setCustomCarbs('');
    setCustomFat('');
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Daily Summary */}
      <View style={[styles.summaryCard, { backgroundColor: theme.surface }]}>
        <Text style={[styles.summaryTitle, { color: theme.text }]}>Today's Intake</Text>
        <View style={styles.macroRow}>
          <View style={styles.macroItem}>
            <Text style={[styles.macroValue, { color: theme.text }, totalCal > calGoal && { color: theme.danger }]}>{totalCal}</Text>
            <Text style={[styles.macroLabel, { color: theme.textMuted }]}>/ {calGoal} cal</Text>
          </View>
          <View style={styles.macroItem}>
            <Text style={[styles.macroValue, { color: '#3B82F6' }]}>{totalProtein}g</Text>
            <Text style={[styles.macroLabel, { color: theme.textMuted }]}>/ {proteinGoal}g protein</Text>
          </View>
          <View style={styles.macroItem}>
            <Text style={[styles.macroValue, { color: theme.text }]}>{totalCarbs}g</Text>
            <Text style={[styles.macroLabel, { color: theme.textMuted }]}>carbs</Text>
          </View>
          <View style={styles.macroItem}>
            <Text style={[styles.macroValue, { color: theme.text }]}>{totalFat}g</Text>
            <Text style={[styles.macroLabel, { color: theme.textMuted }]}>fat</Text>
          </View>
        </View>
        {/* Progress bar */}
        <View style={[styles.progressBar, { backgroundColor: theme.border }]}>
          <View style={[styles.progressFill, { backgroundColor: theme.success, width: `${Math.min(100, (totalCal / calGoal) * 100)}%` }]} />
        </View>
      </View>

      {/* Meal Type Selector */}
      <View style={styles.mealTypeRow}>
        {MEAL_TYPES.map((mt) => (
          <TouchableOpacity
            key={mt.id}
            style={[
              styles.mealTypeBtn,
              { backgroundColor: theme.surface, borderColor: theme.border },
              selectedMealType === mt.id && { backgroundColor: mt.color + '20', borderColor: mt.color },
            ]}
            onPress={() => {
              Haptics.selectionAsync();
              setSelectedMealType(mt.id);
            }}
          >
            <mt.icon size={16} color={selectedMealType === mt.id ? mt.color : theme.textMuted} />
            <Text style={[styles.mealTypeText, { color: theme.textMuted }, selectedMealType === mt.id && { color: mt.color }]}>
              {mt.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Quick Add */}
      <Text style={[styles.sectionTitle, { color: theme.text }]}>Quick Add</Text>
      <View style={styles.quickGrid}>
        {QUICK_MEALS.map((meal, i) => (
          <TouchableOpacity key={i} style={[styles.quickCard, { backgroundColor: theme.surface }]} onPress={() => addQuickMeal(meal)}>
            <Text style={[styles.quickName, { color: theme.text }]} numberOfLines={1}>{meal.name}</Text>
            <Text style={[styles.quickCal, { color: theme.success }]}>{meal.cal} cal</Text>
            <Text style={[styles.quickMacro, { color: theme.textMuted }]}>P:{meal.p} C:{meal.c} F:{meal.f}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Custom Entry */}
      <Text style={[styles.sectionTitle, { color: theme.text }]}>Custom Entry</Text>
      <View style={[styles.customCard, { backgroundColor: theme.surface }]}>
        <TextInput
          style={[styles.customInput, { backgroundColor: theme.background, color: theme.text }]}
          placeholder="Food name"
          placeholderTextColor={theme.textMuted}
          value={customName}
          onChangeText={setCustomName}
        />
        <View style={styles.customRow}>
          <TextInput
            style={[styles.customInput, styles.customSmall, { backgroundColor: theme.background, color: theme.text }]}
            placeholder="Cal"
            placeholderTextColor={theme.textMuted}
            keyboardType="numeric"
            value={customCal}
            onChangeText={setCustomCal}
          />
          <TextInput
            style={[styles.customInput, styles.customSmall, { backgroundColor: theme.background, color: theme.text }]}
            placeholder="Protein"
            placeholderTextColor={theme.textMuted}
            keyboardType="numeric"
            value={customProtein}
            onChangeText={setCustomProtein}
          />
          <TextInput
            style={[styles.customInput, styles.customSmall, { backgroundColor: theme.background, color: theme.text }]}
            placeholder="Carbs"
            placeholderTextColor={theme.textMuted}
            keyboardType="numeric"
            value={customCarbs}
            onChangeText={setCustomCarbs}
          />
          <TextInput
            style={[styles.customInput, styles.customSmall, { backgroundColor: theme.background, color: theme.text }]}
            placeholder="Fat"
            placeholderTextColor={theme.textMuted}
            keyboardType="numeric"
            value={customFat}
            onChangeText={setCustomFat}
          />
        </View>
        <TouchableOpacity style={[styles.addBtn, { backgroundColor: theme.success }]} onPress={addCustomMeal}>
          <Plus size={18} color="#fff" />
          <Text style={styles.addBtnText}>Add Meal</Text>
        </TouchableOpacity>
      </View>

      {/* Today's Log */}
      {todayMeals.length > 0 && (
        <>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Today's Log ({todayMeals.length})</Text>
          {todayMeals.map((meal) => (
            <View key={meal.id} style={[styles.logRow, { backgroundColor: theme.surface }]}>
              <View style={styles.logInfo}>
                <Text style={[styles.logName, { color: theme.text }]}>{meal.name}</Text>
                <Text style={[styles.logType, { color: theme.textMuted }]}>{meal.meal_type}</Text>
              </View>
              <Text style={[styles.logCal, { color: theme.success }]}>{meal.calories} cal</Text>
            </View>
          ))}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  summaryCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  summaryTitle: { fontSize: 14, fontWeight: '600', marginBottom: 12 },
  macroRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  macroItem: { alignItems: 'center' },
  macroValue: { fontSize: 18, fontWeight: '800' },
  macroLabel: { fontSize: 10 },
  progressBar: { height: 6, borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: 6, borderRadius: 3 },

  mealTypeRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  mealTypeBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  mealTypeText: { fontSize: 11, fontWeight: '600' },

  sectionTitle: { fontSize: 14, fontWeight: '600', marginBottom: 8, marginTop: 8 },
  quickGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 16 },
  quickCard: {
    width: '48%',
    borderRadius: 8,
    padding: 10,
  },
  quickName: { fontSize: 12, fontWeight: '600', marginBottom: 2 },
  quickCal: { fontSize: 14, fontWeight: '700' },
  quickMacro: { fontSize: 10 },

  customCard: { borderRadius: 12, padding: 12, marginBottom: 16 },
  customInput: {
    borderRadius: 8,
    padding: 10,
    fontSize: 13,
    marginBottom: 8,
  },
  customRow: { flexDirection: 'row', gap: 6 },
  customSmall: { flex: 1 },
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    borderRadius: 8,
    padding: 10,
  },
  addBtnText: { color: '#0F172A', fontWeight: '700', fontSize: 13 },

  logRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 8,
    padding: 10,
    marginBottom: 4,
  },
  logInfo: { flex: 1 },
  logName: { fontSize: 13, fontWeight: '600' },
  logType: { fontSize: 10, textTransform: 'capitalize' },
  logCal: { fontSize: 13, fontWeight: '700' },
});
