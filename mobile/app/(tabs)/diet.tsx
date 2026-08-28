import React, { useEffect, useState, useCallback } from "react";
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Dimensions,
} from "react-native";
import { Plus, Camera, Utensils, Flame, Dumbbell, Droplets, Target, X } from "lucide-react-native";
import { useTheme } from "../../src/services/theme";

const API = "http://localhost:8000";
const { width: SCREEN_WIDTH } = Dimensions.get("window");

interface Meal {
  id: string; name: string; calories: number;
  protein_g: number; carbs_g: number; fat_g: number;
  meal_type: string; date: string;
}

interface DailyTotals {
  calories: number; protein_g: number; carbs_g: number; fat_g: number;
  fiber_g: number; meal_count: number;
}

interface QuickFood {
  name: string; calories: number; protein: number; carbs: number; fat: number;
}

const QUICK_FOODS: QuickFood[] = [
  { name: "Chicken Breast", calories: 165, protein: 31, carbs: 0, fat: 3.6 },
  { name: "Banana", calories: 105, protein: 1.3, carbs: 27, fat: 0.4 },
  { name: "Eggs (2)", calories: 156, protein: 13, carbs: 1.1, fat: 11 },
  { name: "Greek Yogurt", calories: 118, protein: 20, carbs: 7.2, fat: 1.4 },
  { name: "Oats (100g)", calories: 389, protein: 17, carbs: 66, fat: 7 },
  { name: "Rice (1 cup)", calories: 216, protein: 5, carbs: 45, fat: 1.8 },
  { name: "Salmon", calories: 208, protein: 20, carbs: 0, fat: 13 },
  { name: "Whey Shake", calories: 120, protein: 25, carbs: 3, fat: 1.5 },
  { name: "Apple", calories: 95, protein: 0.5, carbs: 25, fat: 0.3 },
  { name: "Almonds (30g)", calories: 173, protein: 6.3, carbs: 6.5, fat: 15 },
  { name: "Sweet Potato", calories: 103, protein: 2.3, carbs: 24, fat: 0.1 },
  { name: "Bread (2 slices)", calories: 132, protein: 4.4, carbs: 24, fat: 1.6 },
];

const TARGETS = { calories: 2500, protein: 150, carbs: 300, fat: 80 };

const MACRO_COLORS = { calories: "#F59E0B", protein: "#EF4444", carbs: "#3B82F6", fat: "#8B5CF6" };

function MacroBar({ label, current, target, color, styles }: { label: string; current: number; target: number; color: string; styles: ReturnType<typeof makeStyles> }) {
  const pct = Math.min(100, (current / target) * 100);
  return (
    <View style={styles.macroBar}>
      <View style={styles.macroBarHeader}>
        <Text style={styles.macroLabel}>{label}</Text>
        <Text style={[styles.macroValue, { color }]}>
          {Math.round(current)} / {target}{label === "Calories" ? "" : "g"}
        </Text>
      </View>
      <View style={styles.macroBarTrack}>
        <View style={[styles.macroBarFill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

function MiniChart({ data, color, styles }: { data: number[]; color: string; styles: ReturnType<typeof makeStyles> }) {
  const max = Math.max(...data, 1);
  return (
    <View style={styles.miniChart}>
      {data.map((v, i) => (
        <View
          key={i}
          style={[
            styles.miniBar,
            { height: `${(v / max) * 100}%`, backgroundColor: color, opacity: 0.5 + (i / data.length) * 0.5 },
          ]}
        />
      ))}
    </View>
  );
}

export default function DietScreen() {
  const { theme } = useTheme();
  const [userId] = useState("default");
  const [meals, setMeals] = useState<Meal[]>([]);
  const [totals, setTotals] = useState<DailyTotals>({ calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0, meal_count: 0 });
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [showCustomAdd, setShowCustomAdd] = useState(false);
  const [customName, setCustomName] = useState("");
  const [customCal, setCustomCal] = useState("");
  const [customProtein, setCustomProtein] = useState("");
  const [chartData, setChartData] = useState<number[]>([0, 0, 0, 0, 0, 0, 0]);

  useEffect(() => { loadDaily(); loadChart(); }, []);

  const loadDaily = async () => {
    try {
      const r = await fetch(`${API}/api/v1/diet/daily?user_id=${userId}`);
      const d = await r.json();
      setMeals(d.meals || []);
      setTotals(d.totals || { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0, meal_count: 0 });
    } catch {}
  };

  const loadChart = async () => {
    try {
      const r = await fetch(`${API}/api/v1/diet/chart?user_id=${userId}&days=7`);
      const d = await r.json();
      setChartData((d.chart || []).map((c: any) => c.calories || 0));
    } catch {}
  };

  const quickAdd = async (food: QuickFood) => {
    try {
      await fetch(`${API}/api/v1/diet/quick-add/${encodeURIComponent(food.name)}?user_id=${userId}`, {
        method: "POST",
      });
      setShowQuickAdd(false);
      loadDaily();
      loadChart();
    } catch {}
  };

  const customAdd = async () => {
    if (!customName || !customCal) return;
    try {
      await fetch(`${API}/api/v1/diet/log?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: customName, calories: parseFloat(customCal),
          protein_g: parseFloat(customProtein || "0"),
          carbs_g: 0, fat_g: 0, meal_type: "snack",
        }),
      });
      setShowCustomAdd(false);
      setCustomName(""); setCustomCal(""); setCustomProtein("");
      loadDaily();
      loadChart();
    } catch {}
  };

  const caloriePct = Math.round((totals.calories / TARGETS.calories) * 100);
  const proteinPct = Math.round((totals.protein_g / TARGETS.protein) * 100);

  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      <ScrollView style={s.scroll} contentContainerStyle={{ paddingBottom: 100 }} showsVerticalScrollIndicator={false}>
        {/* Daily Calorie Ring */}
        <View style={s.ringContainer}>
          <View style={s.ring}>
            <Text style={s.ringNum}>{Math.round(totals.calories)}</Text>
            <Text style={s.ringLabel}>calories</Text>
            <Text style={s.ringTarget}>of {TARGETS.calories}</Text>
          </View>
          <Text style={[s.ringPct, { color: caloriePct > 100 ? theme.danger : theme.success }]}>
            {caloriePct}% of target
          </Text>
        </View>

        {/* Macro Progress Bars */}
        <View style={s.macros}>
          <MacroBar label="Calories" current={totals.calories} target={TARGETS.calories} color={MACRO_COLORS.calories} styles={s} />
          <MacroBar label="Protein" current={totals.protein_g} target={TARGETS.protein} color={MACRO_COLORS.protein} styles={s} />
          <MacroBar label="Carbs" current={totals.carbs_g} target={TARGETS.carbs} color={MACRO_COLORS.carbs} styles={s} />
          <MacroBar label="Fat" current={totals.fat_g} target={TARGETS.fat} color={MACRO_COLORS.fat} styles={s} />
        </View>

        {/* 7-Day Chart */}
        <View style={s.chartSection}>
          <Text style={s.chartTitle}>7-Day Calorie Trend</Text>
          <MiniChart data={chartData} color="#F59E0B" styles={s} />
        </View>

        {/* Today's Meals */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>Today's Meals ({totals.meal_count})</Text>
          {meals.length === 0 ? (
            <Text style={s.emptyText}>No meals logged today</Text>
          ) : (
            meals.map((m) => (
              <View key={m.id} style={s.mealCard}>
                <View style={s.mealIcon}>
                  <Utensils size={16} color={theme.primaryLight} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={s.mealName}>{m.name}</Text>
                  <Text style={s.mealMeta}>
                    {m.meal_type} • {Math.round(m.calories)} cal • P:{Math.round(m.protein_g)}g
                  </Text>
                </View>
              </View>
            ))
          )}
        </View>
      </ScrollView>

      {/* FAB */}
      <View style={s.fabRow}>
        <TouchableOpacity style={s.fab} onPress={() => setShowQuickAdd(true)}>
          <Plus size={22} color="#FFF" />
        </TouchableOpacity>
        <TouchableOpacity style={[s.fab, { backgroundColor: "#8B5CF6" }]} onPress={() => setShowCustomAdd(true)}>
          <Dumbbell size={20} color="#FFF" />
        </TouchableOpacity>
        <TouchableOpacity style={[s.fab, { backgroundColor: "#10B981" }]}>
          <Camera size={20} color="#FFF" />
        </TouchableOpacity>
      </View>

      {/* Quick Add Modal */}
      {showQuickAdd && (
        <View style={s.modal}>
          <View style={s.modalContent}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>Quick Add</Text>
              <TouchableOpacity onPress={() => setShowQuickAdd(false)}>
                <X size={20} color={theme.textSecondary} />
              </TouchableOpacity>
            </View>
            <ScrollView style={{ maxHeight: 350 }}>
              {QUICK_FOODS.map((f, i) => (
                <TouchableOpacity key={i} style={s.quickItem} onPress={() => quickAdd(f)}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.quickName}>{f.name}</Text>
                    <Text style={s.quickMacros}>
                      P:{f.protein}g C:{f.carbs}g F:{f.fat}g
                    </Text>
                  </View>
                  <Text style={s.quickCal}>{f.calories} cal</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      )}

      {/* Custom Add Modal */}
      {showCustomAdd && (
        <View style={s.modal}>
          <View style={s.modalContent}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>Add Custom Food</Text>
              <TouchableOpacity onPress={() => setShowCustomAdd(false)}>
                <X size={20} color={theme.textSecondary} />
              </TouchableOpacity>
            </View>
            <TextInput style={s.input} placeholder="Food name" placeholderTextColor={theme.textMuted} value={customName} onChangeText={setCustomName} />
            <TextInput style={s.input} placeholder="Calories" placeholderTextColor={theme.textMuted} keyboardType="numeric" value={customCal} onChangeText={setCustomCal} />
            <TextInput style={s.input} placeholder="Protein (g)" placeholderTextColor={theme.textMuted} keyboardType="numeric" value={customProtein} onChangeText={setCustomProtein} />
            <TouchableOpacity style={s.saveBtn} onPress={customAdd}>
              <Text style={s.saveBtnText}>Add Food</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.background },
    scroll: { flex: 1, padding: 16 },
    ringContainer: { alignItems: "center", marginBottom: 20 },
    ring: {
      width: 140, height: 140, borderRadius: 70, borderWidth: 6,
      borderColor: "#F59E0B", alignItems: "center", justifyContent: "center",
      backgroundColor: theme.surface,
    },
    ringNum: { color: theme.text, fontSize: 28, fontWeight: "700" },
    ringLabel: { color: theme.textSecondary, fontSize: 12 },
    ringTarget: { color: theme.textMuted, fontSize: 11 },
    ringPct: { fontSize: 14, fontWeight: "600", marginTop: 8 },
    macros: { marginBottom: 20 },
    macroBar: { marginBottom: 10 },
    macroBarHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
    macroLabel: { color: theme.textSecondary, fontSize: 13 },
    macroValue: { fontSize: 13, fontWeight: "600" },
    macroBarTrack: { height: 8, backgroundColor: theme.surfaceHover, borderRadius: 4 },
    macroBarFill: { height: 8, borderRadius: 4 },
    chartSection: { marginBottom: 20 },
    chartTitle: { color: theme.text, fontSize: 15, fontWeight: "600", marginBottom: 10 },
    miniChart: { flexDirection: "row", alignItems: "flex-end", height: 80, gap: 4 },
    miniBar: { flex: 1, borderRadius: 4, minHeight: 4 },
    section: { marginBottom: 20 },
    sectionTitle: { color: theme.text, fontSize: 15, fontWeight: "600", marginBottom: 10 },
    emptyText: { color: theme.textMuted, fontSize: 13, fontStyle: "italic" },
    mealCard: {
      flexDirection: "row", alignItems: "center", gap: 10,
      backgroundColor: theme.surface, borderRadius: 8, padding: 12, marginBottom: 6,
    },
    mealIcon: {
      width: 32, height: 32, borderRadius: 16, backgroundColor: theme.primaryBg,
      alignItems: "center", justifyContent: "center",
    },
    mealName: { color: theme.text, fontSize: 14, fontWeight: "500" },
    mealMeta: { color: theme.textSecondary, fontSize: 12, marginTop: 2 },
    fabRow: { position: "absolute", bottom: 20, right: 20, gap: 10, flexDirection: "row" },
    fab: {
      width: 52, height: 52, borderRadius: 26, backgroundColor: theme.primary,
      alignItems: "center", justifyContent: "center",
      shadowColor: "#000", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 4,
    },
    modal: {
      position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: "rgba(0,0,0,0.7)", justifyContent: "flex-end",
    },
    modalContent: { backgroundColor: theme.surface, borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 20 },
    modalHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
    modalTitle: { color: theme.text, fontSize: 18, fontWeight: "700" },
    quickItem: {
      flexDirection: "row", alignItems: "center", justifyContent: "space-between",
      paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: theme.border,
    },
    quickName: { color: theme.text, fontSize: 14, fontWeight: "500" },
    quickMacros: { color: theme.textSecondary, fontSize: 11, marginTop: 2 },
    quickCal: { color: "#F59E0B", fontSize: 14, fontWeight: "600" },
    input: {
      backgroundColor: theme.background, borderRadius: 8, padding: 12, color: theme.text,
      fontSize: 14, marginBottom: 10,
    },
    saveBtn: { backgroundColor: theme.primary, borderRadius: 8, padding: 14, alignItems: "center", marginTop: 8 },
    saveBtnText: { color: "#F8FAFC", fontWeight: "600", fontSize: 15 },
  });
}
