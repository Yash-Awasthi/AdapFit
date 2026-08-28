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
    <ScrollView style={styles.container}>
      {/* Daily Summary */}
      <View style={styles.summaryCard}>
        <Text style={styles.summaryTitle}>Today's Intake</Text>
        <View style={styles.macroRow}>
          <View style={styles.macroItem}>
            <Text style={[styles.macroValue, totalCal > calGoal && { color: '#EF4444' }]}>{totalCal}</Text>
            <Text style={styles.macroLabel}>/ {calGoal} cal</Text>
          </View>
          <View style={styles.macroItem}>
            <Text style={[styles.macroValue, { color: '#3B82F6' }]}>{totalProtein}g</Text>
            <Text style={styles.macroLabel}>/ {proteinGoal}g protein</Text>
          </View>
          <View style={styles.macroItem}>
            <Text style={styles.macroValue}>{totalCarbs}g</Text>
            <Text style={styles.macroLabel}>carbs</Text>
          </View>
          <View style={styles.macroItem}>
            <Text style={styles.macroValue}>{totalFat}g</Text>
            <Text style={styles.macroLabel}>fat</Text>
          </View>
        </View>
        {/* Progress bar */}
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${Math.min(100, (totalCal / calGoal) * 100)}%` }]} />
        </View>
      </View>

      {/* Meal Type Selector */}
      <View style={styles.mealTypeRow}>
        {MEAL_TYPES.map((mt) => (
          <TouchableOpacity
            key={mt.id}
            style={[styles.mealTypeBtn, selectedMealType === mt.id && { backgroundColor: mt.color + '20', borderColor: mt.color }]}
            onPress={() => {
              Haptics.selectionAsync();
              setSelectedMealType(mt.id);
            }}
          >
            <mt.icon size={16} color={selectedMealType === mt.id ? mt.color : '#8B96AB'} />
            <Text style={[styles.mealTypeText, selectedMealType === mt.id && { color: mt.color }]}>
              {mt.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Quick Add */}
      <Text style={styles.sectionTitle}>Quick Add</Text>
      <View style={styles.quickGrid}>
        {QUICK_MEALS.map((meal, i) => (
          <TouchableOpacity key={i} style={styles.quickCard} onPress={() => addQuickMeal(meal)}>
            <Text style={styles.quickName} numberOfLines={1}>{meal.name}</Text>
            <Text style={styles.quickCal}>{meal.cal} cal</Text>
            <Text style={styles.quickMacro}>P:{meal.p} C:{meal.c} F:{meal.f}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Custom Entry */}
      <Text style={styles.sectionTitle}>Custom Entry</Text>
      <View style={styles.customCard}>
        <TextInput
          style={styles.customInput}
          placeholder="Food name"
          placeholderTextColor="#475569"
          value={customName}
          onChangeText={setCustomName}
        />
        <View style={styles.customRow}>
          <TextInput
            style={[styles.customInput, styles.customSmall]}
            placeholder="Cal"
            placeholderTextColor="#475569"
            keyboardType="numeric"
            value={customCal}
            onChangeText={setCustomCal}
          />
          <TextInput
            style={[styles.customInput, styles.customSmall]}
            placeholder="Protein"
            placeholderTextColor="#475569"
            keyboardType="numeric"
            value={customProtein}
            onChangeText={setCustomProtein}
          />
          <TextInput
            style={[styles.customInput, styles.customSmall]}
            placeholder="Carbs"
            placeholderTextColor="#475569"
            keyboardType="numeric"
            value={customCarbs}
            onChangeText={setCustomCarbs}
          />
          <TextInput
            style={[styles.customInput, styles.customSmall]}
            placeholder="Fat"
            placeholderTextColor="#475569"
            keyboardType="numeric"
            value={customFat}
            onChangeText={setCustomFat}
          />
        </View>
        <TouchableOpacity style={styles.addBtn} onPress={addCustomMeal}>
          <Plus size={18} color="#fff" />
          <Text style={styles.addBtnText}>Add Meal</Text>
        </TouchableOpacity>
      </View>

      {/* Today's Log */}
      {todayMeals.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>Today's Log ({todayMeals.length})</Text>
          {todayMeals.map((meal) => (
            <View key={meal.id} style={styles.logRow}>
              <View style={styles.logInfo}>
                <Text style={styles.logName}>{meal.name}</Text>
                <Text style={styles.logType}>{meal.meal_type}</Text>
              </View>
              <Text style={styles.logCal}>{meal.calories} cal</Text>
            </View>
          ))}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', padding: 20 },
  summaryCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  summaryTitle: { fontSize: 14, fontWeight: '600', color: '#F8FAFC', marginBottom: 12 },
  macroRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  macroItem: { alignItems: 'center' },
  macroValue: { fontSize: 18, fontWeight: '800', color: '#F8FAFC' },
  macroLabel: { fontSize: 10, color: '#8B96AB' },
  progressBar: { height: 6, backgroundColor: '#334155', borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: 6, backgroundColor: '#22C55E', borderRadius: 3 },

  mealTypeRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  mealTypeBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: '#334155',
  },
  mealTypeText: { fontSize: 11, fontWeight: '600', color: '#8B96AB' },

  sectionTitle: { fontSize: 14, fontWeight: '600', color: '#F8FAFC', marginBottom: 8, marginTop: 8 },
  quickGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 16 },
  quickCard: {
    width: '48%',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 10,
  },
  quickName: { fontSize: 12, fontWeight: '600', color: '#F8FAFC', marginBottom: 2 },
  quickCal: { fontSize: 14, fontWeight: '700', color: '#22C55E' },
  quickMacro: { fontSize: 10, color: '#8B96AB' },

  customCard: { backgroundColor: '#1E293B', borderRadius: 12, padding: 12, marginBottom: 16 },
  customInput: {
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 10,
    fontSize: 13,
    color: '#F8FAFC',
    marginBottom: 8,
  },
  customRow: { flexDirection: 'row', gap: 6 },
  customSmall: { flex: 1 },
  addBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#22C55E',
    borderRadius: 8,
    padding: 10,
  },
  addBtnText: { color: '#0F172A', fontWeight: '700', fontSize: 13 },

  logRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 10,
    marginBottom: 4,
  },
  logInfo: { flex: 1 },
  logName: { fontSize: 13, fontWeight: '600', color: '#F8FAFC' },
  logType: { fontSize: 10, color: '#8B96AB', textTransform: 'capitalize' },
  logCal: { fontSize: 13, fontWeight: '700', color: '#22C55E' },
});
