import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, TextInput, StyleSheet, Alert, ActivityIndicator,
} from 'react-native';
import { Utensils, Plus, Trash2, Sparkles, ChefHat, Camera } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import { LoadingScreen } from '../../src/components';
import { api } from '../../src/services/api';
import { API_BASE_URL } from '../../src/services/config';
import { useUserStore } from '../../src/stores';
import { useTheme } from '../../src/services/theme';
import { authHeader } from '../../src/services/authToken';

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
const CARBS_TARGET = 300;
const FAT_TARGET = 70;

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
  const [filterType, setFilterType] = useState<string | null>(null);
  const [analyzingPhoto, setAnalyzingPhoto] = useState(false);

  useEffect(() => { fetchData(); fetchCurrentPlan(); }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const [mealsRes, sumRes] = await Promise.all([
        fetch(`${API}/api/v1/nutrition/meals?user_id=${userId}`, { headers: authHeader() }),
        fetch(`${API}/api/v1/nutrition/daily?user_id=${userId}`, { headers: authHeader() }),
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
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setShowForm(false);
        setName(''); setCalories(''); setProtein(''); setCarbs(''); setFat('');
        fetchData();
      } else {
        const detail = await res.text().catch(() => '');
        Alert.alert('Could not log meal', `Server returned ${res.status}.${detail ? ` ${detail.slice(0, 200)}` : ''}`);
      }
    } catch (err: any) {
      Alert.alert('Could not reach the server', err?.message || String(err));
    }
  }

  async function deleteMeal(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await fetch(`${API}/api/v1/nutrition/meals/${id}?user_id=${userId}`, { method: 'DELETE', headers: authHeader() });
      if (res.ok) {
        fetchData();
      } else {
        const detail = await res.text().catch(() => '');
        Alert.alert('Could not delete meal', `Server returned ${res.status}.${detail ? ` ${detail.slice(0, 200)}` : ''}`);
      }
    } catch (err: any) {
      Alert.alert('Could not reach the server', err?.message || String(err));
    }
  }

  async function photoLog() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Camera permission needed', 'Enable camera access to log a meal from a photo.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ base64: true, quality: 0.5 });
    if (result.canceled || !result.assets?.[0]?.base64) return;

    setAnalyzingPhoto(true);
    try {
      const res = await api.photoLogMeal(result.assets[0].base64, mealType, userId);
      if (res.foods.length === 0) {
        Alert.alert("Couldn't identify the meal", res.suggestions[0] || 'Try a clearer photo, or log it manually.');
      } else {
        Alert.alert('Meal logged', res.foods.map((f) => f.name).join(', '));
      }
      fetchData();
    } catch {
      Alert.alert("Couldn't analyze photo", 'Check your connection and try again.');
    }
    setAnalyzingPhoto(false);
  }

  function MacroCard({ label, current, target, color }: { label: string; current: number; target: number; color: string }) {
    const pct = target > 0 ? Math.min((current / target) * 100, 100) : 0;
    return (
      <View style={s.macroCard}>
        <Text style={[s.macroCardValue, { color }]}>{Math.round(current)}g</Text>
        <Text style={s.macroCardLabel}>{label}</Text>
        <View style={s.macroBarBg}>
          <View style={[s.macroBarFill, { width: `${pct}%`, backgroundColor: color }]} />
        </View>
        <Text style={s.macroCardTarget}>{target}g target</Text>
      </View>
    );
  }

  if (loading) return <LoadingScreen />;

  const caloriePct = summary && summary.calorie_target > 0
    ? Math.min(100, Math.round((summary.total_calories / summary.calorie_target) * 100))
    : 0;
  const visibleMeals = filterType ? meals.filter((m) => m.meal_type === filterType) : meals;

  return (
    <View style={s.container}>
      <Text style={s.title}>Nutrition</Text>
      <Text style={s.subtitle}>Track your fuel</Text>

      {summary && (
        <View style={s.ringContainer}>
          <View style={[s.ring, { borderColor: caloriePct >= 100 ? theme.danger : theme.primary }]}>
            <Text style={s.ringNum}>{summary.total_calories}</Text>
            <Text style={s.ringLabel}>of {summary.calorie_target} kcal</Text>
          </View>
          <Text style={s.remaining}>{summary.remaining_calories} kcal remaining</Text>
        </View>
      )}

      {summary && (
        <View style={s.macroRow}>
          <MacroCard label="Protein" current={summary.total_protein} target={summary.protein_target} color={theme.success} />
          <MacroCard label="Carbs" current={summary.total_carbs} target={CARBS_TARGET} color={theme.primaryLight} />
          <MacroCard label="Fat" current={summary.total_fat} target={FAT_TARGET} color={theme.warning} />
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

      <View style={s.actionRow}>
        <TouchableOpacity style={[s.addBtn, { flex: 1 }]} onPress={() => setShowForm(!showForm)}>
          <Plus size={16} color="#fff" />
          <Text style={s.addBtnText}>Log Meal</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.cameraBtn} onPress={photoLog} disabled={analyzingPhoto}>
          {analyzingPhoto ? <ActivityIndicator size="small" color="#fff" /> : <Camera size={18} color="#fff" />}
        </TouchableOpacity>
      </View>

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

      <View style={s.filterRow}>
        <TouchableOpacity
          style={[s.filterTab, filterType === null && s.filterTabActive]}
          onPress={() => setFilterType(null)}
        >
          <Text style={[s.filterText, filterType === null && s.filterTextActive]}>All</Text>
        </TouchableOpacity>
        {MEAL_TYPES.map((t) => (
          <TouchableOpacity
            key={t}
            style={[s.filterTab, filterType === t && s.filterTabActive]}
            onPress={() => setFilterType(filterType === t ? null : t)}
          >
            <Text style={[s.filterText, filterType === t && s.filterTextActive]}>{t}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={visibleMeals}
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
    ringContainer: { alignItems: 'center', marginBottom: 16 },
    ring: {
      width: 140, height: 140, borderRadius: 70, borderWidth: 6,
      alignItems: 'center', justifyContent: 'center', backgroundColor: theme.surface,
    },
    ringNum: { fontSize: 30, fontWeight: '800', color: theme.text },
    ringLabel: { fontSize: 12, color: theme.textMuted, marginTop: 2 },
    remaining: { fontSize: 12, color: theme.success, fontWeight: '500', marginTop: 8 },
    macroRow: { flexDirection: 'row', gap: 10, marginBottom: 16 },
    macroCard: {
      flex: 1, backgroundColor: theme.surface, borderRadius: 12, padding: 10, alignItems: 'center',
    },
    macroCardValue: { fontSize: 16, fontWeight: '800' },
    macroCardLabel: { fontSize: 11, color: theme.textSecondary, marginTop: 2, marginBottom: 6 },
    macroCardTarget: { fontSize: 9, color: theme.textMuted, marginTop: 4 },
    macroBarBg: { height: 5, width: '100%', backgroundColor: theme.surfaceHover, borderRadius: 3 },
    macroBarFill: { height: 5, borderRadius: 3 },
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
    actionRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
    addBtn: {
      flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
      backgroundColor: theme.primary, borderRadius: 12, padding: 12,
    },
    addBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
    cameraBtn: {
      width: 46, alignItems: 'center', justifyContent: 'center',
      backgroundColor: '#10B981', borderRadius: 12,
    },
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
    filterRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
    filterTab: {
      paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999,
      backgroundColor: theme.surface, borderWidth: 1, borderColor: theme.border,
    },
    filterTabActive: { backgroundColor: theme.primary, borderColor: theme.primary },
    filterText: { fontSize: 12, color: theme.textMuted, textTransform: 'capitalize' },
    filterTextActive: { color: '#fff', fontWeight: '600' },
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
