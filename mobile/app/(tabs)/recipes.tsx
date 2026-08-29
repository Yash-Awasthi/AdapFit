/**
 * AI Recipe Generator — Meal planning, recipes, grocery lists
 */
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, typography, spacing, radius, presets, glass } from '../../src/theme';

import { API_V1 as API } from '../../src/services/config';
function RecipeCard({ recipe, onPress }: { recipe: any; onPress: () => void }) {
  const dietColors: Record<string, string> = { 'high-protein': colors.health.heart, vegan: colors.health.calm, keto: colors.health.energy, 'low-carb': colors.primary, 'gluten-free': colors.health.sleep };
  return (
    <TouchableOpacity style={[ns.recipeCard, glass.light]} onPress={onPress}>
      <View style={[ns.recipeImage, { backgroundColor: (dietColors[recipe.diet?.[0]] || colors.primary) + '20' }]}>
        <Ionicons
          name={recipe.cuisine === 'Thai' ? 'flame-outline' : recipe.cuisine === 'Mediterranean' ? 'leaf-outline' : recipe.cuisine === 'Italian' ? 'pizza-outline' : recipe.cuisine === 'Asian' ? 'nutrition-outline' : 'restaurant-outline'}
          size={32}
          color={dietColors[recipe.diet?.[0]] || colors.primary}
        />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[typography.label.lg as any, { color: colors.text.primary }]} numberOfLines={1}>{recipe.name}</Text>
        <Text style={[typography.body.xs as any, { color: colors.text.muted }]}>{recipe.cuisine} • {recipe.prep_time + recipe.cook_time} min</Text>
        <View style={ns.recipeMacros}>
          <Text style={[ns.macroBadge, { color: colors.health.heart }]}>{recipe.calories} cal</Text>
          <Text style={[ns.macroBadge, { color: colors.primary }]}>P:{recipe.protein}g</Text>
          <Text style={[ns.macroBadge, { color: colors.health.energy }]}>C:{recipe.carbs}g</Text>
          <Text style={[ns.macroBadge, { color: colors.health.calm }]}>F:{recipe.fat}g</Text>
        </View>
        <View style={{ flexDirection: 'row', gap: spacing.xs, marginTop: spacing.xs }}>
          {recipe.tags?.slice(0, 2).map((t: string) => (
            <Text key={t} style={[ns.tag, { backgroundColor: colors.primary + '20', color: colors.primary }]}>{t}</Text>
          ))}
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function RecipesScreen() {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [selectedDiet, setSelectedDiet] = useState('');
  const [tab, setTab] = useState<'browse' | 'mealplan' | 'grocery'>('browse');

  const diets = ['high-protein', 'vegan', 'keto', 'low-carb', 'gluten-free', 'meal-prep'];

  useEffect(() => { loadRecipes(); }, []);

  const loadRecipes = async (diet: string = '') => {
    const params = new URLSearchParams();
    if (diet) params.set('diet', diet);
    const r = await fetch(`${API}/recipes/all?${params}`);
    const d = await r.json();
    setRecipes(d.recipes || []);
  };

  const searchRecipes = async () => {
    if (!query.trim()) { loadRecipes(selectedDiet); return; }
    const r = await fetch(`${API}/recipes/search?query=${encodeURIComponent(query)}&diet=${selectedDiet}`);
    const d = await r.json();
    setRecipes(d.recipes || []);
  };

  return (
    <ScrollView style={ns.container}>
      <View style={ns.header}>
        <Text style={typography.heading.h1 as any}>Recipes</Text>
        <Text style={typography.body.sm as any}>AI-powered meal planning</Text>
      </View>

      {/* Tab Bar */}
      <View style={ns.tabBar}>
        {[{ key: 'browse', label: 'Recipes' }, { key: 'mealplan', label: 'Meal Plan' }, { key: 'grocery', label: 'Grocery' }].map(t => (
          <TouchableOpacity key={t.key} style={[ns.tab, tab === t.key && ns.tabActive]} onPress={() => setTab(t.key as any)}>
            <Text style={[ns.tabText, tab === t.key && ns.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {tab === 'browse' && (
        <>
          {/* Search */}
          <View style={ns.searchRow}>
            <TextInput style={ns.searchInput} value={query} onChangeText={setQuery} placeholder="Search recipes..." placeholderTextColor={colors.text.muted} onSubmitEditing={searchRecipes} />
            <TouchableOpacity style={ns.searchBtn} onPress={searchRecipes}><Ionicons name="search" size={18} color="#FFF" /></TouchableOpacity>
          </View>

          {/* Diet Filters */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={ns.dietScroll}>
            {diets.map(d => (
              <TouchableOpacity key={d} style={[ns.dietPill, selectedDiet === d && ns.dietActive]} onPress={() => { setSelectedDiet(selectedDiet === d ? '' : d); setTimeout(() => loadRecipes(selectedDiet === d ? '' : d), 100); }}>
                <Text style={[ns.dietText, selectedDiet === d && { color: '#FFF' }]}>{d}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Recipe Cards */}
          {recipes.map(r => (
            <View key={r.id} style={{ marginHorizontal: spacing.lg, marginBottom: spacing.md }}>
              <RecipeCard recipe={r} onPress={() => {}} />
            </View>
          ))}
        </>
      )}

      {tab === 'mealplan' && (
        <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
          <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>AI Meal Plan</Text>
          <Text style={[typography.body.sm as any, { color: colors.text.muted, marginBottom: spacing.md }]}>Generate a personalized 7-day meal plan based on your goals</Text>
          <TouchableOpacity style={[presets.buttonPrimary]}>
            <Ionicons name="sparkles" size={16} color="#FFF" />
            <Text style={[typography.label.lg as any, { color: '#FFF' }]}>Generate Meal Plan</Text>
          </TouchableOpacity>
        </View>
      )}

      {tab === 'grocery' && (
        <View style={[presets.card, { marginHorizontal: spacing.lg }]}>
          <Text style={[typography.heading.h4 as any, { marginBottom: spacing.md }]}>Grocery List</Text>
          <Text style={[typography.body.sm as any, { color: colors.text.muted }]}>Generate a grocery list from your meal plan</Text>
        </View>
      )}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const ns = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  header: { padding: spacing.screenPadding, paddingTop: 50, paddingBottom: spacing.md },
  tabBar: { flexDirection: 'row', marginHorizontal: spacing.lg, marginBottom: spacing.lg, backgroundColor: colors.bg.card, borderRadius: radius.md, padding: 4 },
  tab: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: radius.sm },
  tabActive: { backgroundColor: colors.health.energy },
  tabText: { fontSize: 13, fontWeight: '600', color: colors.text.muted },
  tabTextActive: { color: '#FFF' },
  searchRow: { flexDirection: 'row', gap: spacing.sm, marginHorizontal: spacing.lg, marginBottom: spacing.md },
  searchInput: { flex: 1, backgroundColor: colors.bg.input, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm + 2, color: colors.text.primary, borderWidth: 1, borderColor: colors.surface.border },
  searchBtn: { backgroundColor: colors.health.energy, width: 44, borderRadius: radius.md, justifyContent: 'center', alignItems: 'center' },
  dietScroll: { paddingHorizontal: spacing.lg, marginBottom: spacing.md, maxHeight: 40 },
  dietPill: { paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.pill, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border, marginRight: spacing.sm },
  dietActive: { backgroundColor: colors.health.energy, borderColor: colors.health.energy },
  dietText: { fontSize: 12, color: colors.text.muted, fontWeight: '600' },
  recipeCard: { flexDirection: 'row', padding: spacing.md, borderRadius: radius.md, gap: spacing.md },
  recipeImage: { width: 72, height: 72, borderRadius: radius.md, justifyContent: 'center', alignItems: 'center' },
  recipeMacros: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs },
  macroBadge: { fontSize: 11, fontWeight: '700' },
  tag: { fontSize: 10, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, fontWeight: '600', overflow: 'hidden' },
});
