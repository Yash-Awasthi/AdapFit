import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, TextInput, StyleSheet, Alert, ScrollView,
} from 'react-native';
import { Utensils, Plus, Trash2, Sparkles, ChefHat } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import { LoadingScreen } from '../../src/components';
import { api } from '../../src/services/api';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';

const API = API_BASE_URL;

interface Meal {
  id: string;
  name: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  meal_type: string;
  logged_at: string;
}

interface Summary {
  date: string;
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  meal_count: number;
  calorie_target: number;
  protein_target: number;
  remaining_calories: number;
  remaining_protein: number;
}

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'];
const QUICK_MEALS = [
  { name: 'Greek Yogurt', cal: 150, pro: 15, carb: 8, fat: 5 },
  { name: 'Protein Shake', cal: 250, pro: 30, carb: 10, fat: 8 },
  { name: 'Chicken Breast', cal: 200, pro: 35, carb: 0, fat: 4 },
  { name: 'Banana', cal: 105, pro: 1, carb: 27, fat: 0 },
];

export default function NutritionScreen() {
  const { theme } = useTheme();
  const s = makeStyles(theme);
  const userId = useUserStore((s) => s.userId);
  const profile = useUserStore((s) => s.profile);
  const [meals, setMeals] = useState<Meal[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [generatedPlan, setGeneratedPlan] = useState<any | null>(null);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [calories, setCalories] = useState('');
  const [protein, setProtein] = useState('');
  const [carbs, setCarbs] = useState('');
  const [fat, setFat] = useState('');
  const [mealType, setMealType] = useState('lunch');

  useEffect(() => { fetchData(); fetchCurrentPlan(); }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [mealsRes, sumRes] = await Promise.all([
        fetch(`${API}/api/v1/nutrition/meals?user_id=${userId}`),
        fetch(`${API}/api/v1/nutrition/daily?user_id=${userId}`),
      ]);
      if (mealsRes.ok) setMeals(await mealsRes.json());
      if (sumRes.ok) setSummary(await sumRes.json());
    } catch {}
    setLoading(false);
  }

  // Picks up any plan the AI coach chat already generated for today.
  async function fetchCurrentPlan() {
    try {
      const plan = await api.getCurrentMealPlan(userId);
      if (plan && plan.targets) setGeneratedPlan(plan);
    } catch {}
  }

  async function handleGeneratePlan() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setGenerating(true);
    try {
      const plan = await api.generateMealPlan({
        weight_kg: 75,
        goal: profile?.primary_goal || 'hypertrophy',
        training_day: true,
      }, userId);
      setGeneratedPlan(plan);
    } catch (e) {
      Alert.alert('Notice', 'Could not generate meal plan right now.');
    }
    setGenerating(false);
  }

  async function logMeal(quick?: typeof QUICK_MEALS[0]) {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    const payload = quick
      ? { name: quick.name, calories: quick.cal, protein_g: quick.pro, carbs_g: quick.carb, fat_g: quick.fat, meal_type: 'snack' }
      : { name: name.trim(), calories: parseInt(calories) || 0, protein_g: parseFloat(protein) || 0, carbs_g: parseFloat(carbs) || 0, fat_g: parseFloat(fat) || 0, meal_type: mealType };
    if (!payload.name) return;
    try {
      const res = await fetch(`${API}/api/v1/nutrition/meals?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setShowForm(false);
        setName(''); setCalories(''); setProtein(''); setCarbs(''); setFat('');
        fetchData();
      }
    } catch {}
  }

  async function deleteMeal(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await fetch(`${API}/api/v1/nutrition/meals/${id}?user_id=${userId}`, { method: 'DELETE' });
      if (res.ok) fetchData();
    } catch {}
  }

  function MacroBar({ label, current, target, color }: { label: string; current: number; target: number; color: string }) {
    const pct = target > 0 ? Math.min((current / target) * 100, 100) : 0;
    return (
      <View style={s.macroCol}>
        <Text style={s.macroLabel}>{label}</Text>
        <View style={s.macroBarBg}>
          <View style={[s.macroBarFill, { width: `${pct}%`, backgroundColor: color }]} />
        </View>
        <Text style={s.macroValue}>{Math.round(current)}g</Text>
      </View>
    );
  }

  if (loading) return <LoadingScreen />;

  return (
    <View style={s.container}>
      <Text style={s.title}>Nutrition</Text>
      <Text style={s.subtitle}>Track your fuel</Text>

      {summary && (
        <View style={s.summaryCard}>
          <Text style={s.calBig}>{summary.total_calories}</Text>
          <Text style={s.calLabel}>/ {summary.calorie_target} kcal</Text>
          <View style={s.macroRow}>
            <MacroBar label="Protein" current={summary.total_protein} target={summary.protein_target} color={theme.success} />
            <MacroBar label="Carbs" current={summary.total_carbs} target={300} color={theme.primaryLight} />
            <MacroBar label="Fat" current={summary.total_fat} target={70} color={theme.warning} />
          </View>
          <Text style={s.remaining}>{summary.remaining_calories} kcal remaining</Text>
        </View>
      )}

      {/* AI Meal Plan Generator Button */}
      <TouchableOpacity
        style={s.aiPlanBtn}
        onPress={handleGeneratePlan}
        disabled={generating}
      >
        <Sparkles size={16} color={theme.primaryLight} />
        <Text style={s.aiPlanText}>
          {generating ? 'Generating Smart Plan...' : 'Generate AI Day Meal Plan'}
        </Text>
      </TouchableOpacity>

      {/* Generated Plan Preview Modal/Card */}
      {generatedPlan && (
        <View style={s.planCard}>
          <View style={s.planHeader}>
            <ChefHat size={16} color={theme.success} />
            <Text style={s.planTitle}>
              AI Plan: {generatedPlan.targets?.target_calories ?? 2400} kcal ({generatedPlan.goal})
            </Text>
          </View>
          <Text style={s.planDetails}>
            P: {generatedPlan.targets?.protein_g}g · C: {generatedPlan.targets?.carbs_g}g · F: {generatedPlan.targets?.fat_g}g
          </Text>
          {generatedPlan.meals && (
            <View style={s.planMealList}>
              {generatedPlan.meals.slice(0, 3).map((m: any, idx: number) => (
                <Text key={idx} style={s.planMealItem}>
                  • {m.name}: {m.foods?.map((f: any) => f.food_name).join(', ')}
                </Text>
              ))}
            </View>
          )}
        </View>
      )}

      <View style={s.quickRow}>
        {QUICK_MEALS.map((q) => (
          <TouchableOpacity key={q.name} style={s.quickBtn} onPress={() => logMeal(q)}>
            <Text style={s.quickText}>{q.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity style={s.addBtn} onPress={() => setShowForm(!showForm)}>
        <Plus size={16} color="#fff" />
        <Text style={s.addBtnText}>Log Meal</Text>
      </TouchableOpacity>

      {showForm && (
        <View style={s.form}>
          <TextInput style={s.input} value={name} onChangeText={setName} placeholder="Meal name" placeholderTextColor={theme.textMuted} />
          <View style={s.formRow}>
            <TextInput style={[s.input, { flex: 1 }]} value={calories} onChangeText={setCalories}
              placeholder="Cal" placeholderTextColor={theme.textMuted} keyboardType="numeric" />
            <TextInput style={[s.input, { flex: 1 }]} value={protein} onChangeText={setProtein}
              placeholder="Protein" placeholderTextColor={theme.textMuted} keyboardType="numeric" />
          </View>
          <View style={s.formRow}>
            <TextInput style={[s.input, { flex: 1 }]} value={carbs} onChangeText={setCarbs}
              placeholder="Carbs" placeholderTextColor={theme.textMuted} keyboardType="numeric" />
            <TextInput style={[s.input, { flex: 1 }]} value={fat} onChangeText={setFat}
              placeholder="Fat" placeholderTextColor={theme.textMuted} keyboardType="numeric" />
          </View>
          <View style={s.typeRow}>
            {MEAL_TYPES.map((t) => (
              <TouchableOpacity
                key={t}
                style={[s.typeBtn, mealType === t && s.typeBtnActive]}
                onPress={() => setMealType(t)}
              >
                <Text style={[s.typeText, mealType === t && s.typeTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <TouchableOpacity style={s.submitBtn} onPress={() => logMeal()}>
            <Text style={s.submitBtnText}>Save</Text>
          </TouchableOpacity>
        </View>
      )}

      <FlatList
        data={meals}
        keyExtractor={(i) => i.id}
        contentContainerStyle={s.list}
        renderItem={({ item }) => (
          <View style={s.mealCard}>
            <View style={s.mealInfo}>
              <View style={s.mealHeader}>
                <Text style={s.mealName}>{item.name}</Text>
                <Text style={s.mealType}>{item.meal_type}</Text>
              </View>
              <Text style={s.mealMacros}>
                {item.calories} kcal · P{item.protein_g}g · C{item.carbs_g}g · F{item.fat_g}g
              </Text>
            </View>
            <TouchableOpacity onPress={() => deleteMeal(item.id)}>
              <Trash2 size={16} color={theme.danger} />
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background, padding: 20 },
    title: { fontSize: 28, fontWeight: '700', color: theme.text, marginTop: 48 },
    subtitle: { fontSize: 14, color: theme.textMuted, marginBottom: 16 },
    summaryCard: {
      backgroundColor: theme.surface, borderRadius: 16, padding: 20, alignItems: 'center', marginBottom: 12,
    },
    calBig: { fontSize: 48, fontWeight: '800', color: theme.text },
    calLabel: { fontSize: 14, color: theme.textMuted, marginBottom: 12 },
    macroRow: { flexDirection: 'row', gap: 16, width: '100%', marginBottom: 8 },
    macroCol: { flex: 1 },
    macroLabel: { fontSize: 11, color: theme.textSecondary, marginBottom: 4 },
    macroBarBg: { height: 6, backgroundColor: theme.surfaceHover, borderRadius: 3, marginBottom: 2 },
    macroBarFill: { height: 6, borderRadius: 3 },
    macroValue: { fontSize: 11, color: '#CBD5E1' },
    remaining: { fontSize: 12, color: theme.success, fontWeight: '500' },
    aiPlanBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 8,
      backgroundColor: '#1E1B4B',
      borderColor: theme.primary,
      borderWidth: 1,
      borderRadius: 12,
      padding: 10,
      marginBottom: 12,
    },
    aiPlanText: { color: theme.primaryLight, fontSize: 13, fontWeight: '600' },
    planCard: {
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 12,
      marginBottom: 12,
      borderLeftWidth: 4,
      borderLeftColor: theme.success,
    },
    planHeader: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    planTitle: { fontSize: 14, fontWeight: '600', color: theme.text },
    planDetails: { fontSize: 12, color: theme.textSecondary, marginTop: 4 },
    planMealList: { marginTop: 6 },
    planMealItem: { fontSize: 11, color: '#CBD5E1', marginTop: 2 },
    quickRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
    quickBtn: {
      backgroundColor: 'rgba(34, 197, 94, 0.15)', borderRadius: 12,
      paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1, borderColor: theme.success,
    },
    quickText: { fontSize: 12, color: theme.success, fontWeight: '500' },
    addBtn: {
      flexDirection: 'row', alignItems: 'center', gap: 8,
      backgroundColor: theme.primary, borderRadius: 12, padding: 12, marginBottom: 12,
    },
    addBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
    form: { backgroundColor: theme.surface, borderRadius: 12, padding: 16, marginBottom: 12 },
    input: {
      backgroundColor: theme.background, borderRadius: 8, padding: 12,
      fontSize: 14, color: theme.text, marginBottom: 8,
    },
    formRow: { flexDirection: 'row', gap: 8 },
    typeRow: { flexDirection: 'row', gap: 8, marginBottom: 8 },
    typeBtn: {
      flex: 1, paddingVertical: 8, borderRadius: 8, backgroundColor: theme.background, alignItems: 'center',
    },
    typeBtnActive: { backgroundColor: theme.primary },
    typeText: { fontSize: 12, color: theme.textMuted },
    typeTextActive: { color: theme.text, fontWeight: '600' },
    submitBtn: { backgroundColor: theme.success, borderRadius: 8, padding: 12, alignItems: 'center' },
    submitBtnText: { color: theme.background, fontSize: 14, fontWeight: '600' },
    list: { paddingBottom: 40 },
    mealCard: {
      flexDirection: 'row', alignItems: 'center', backgroundColor: theme.surface,
      borderRadius: 12, padding: 14, marginBottom: 8,
    },
    mealInfo: { flex: 1 },
    mealHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    mealName: { fontSize: 15, fontWeight: '600', color: theme.text },
    mealType: { fontSize: 11, color: theme.primaryLight, backgroundColor: 'rgba(129,140,248,0.15)', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
    mealMacros: { fontSize: 12, color: theme.textSecondary, marginTop: 4 },
  });
}
