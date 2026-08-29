/**
 * Precision Nutrition — Microbiome-Based Diet Dashboard
 * Microbiome profile, metabolic type, personalized meal plan, food recommendations, supplements.
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  microbiomeType: 'Firmicutes-Dominant',
  metabolicType: 'Moderate Oxidizer',
  gutHealthScore: 72,
  macros: { carbs: 200, protein: 150, fat: 67 },
  mealPlan: [
    { day: 'Monday', meals: [
      { type: 'Breakfast', foods: ['Oatmeal with blueberries', 'Green tea'], cal: 380 },
      { type: 'Lunch', foods: ['Grilled salmon quinoa bowl', 'Mixed greens'], cal: 520 },
      { type: 'Snack', foods: ['Greek yogurt with nuts'], cal: 180 },
      { type: 'Dinner', foods: ['Lentil soup with fermented veggies'], cal: 480 },
    ]},
    { day: 'Tuesday', meals: [
      { type: 'Breakfast', foods: ['Kefir smoothie', 'Chia seeds'], cal: 350 },
      { type: 'Lunch', foods: ['Mediterranean chickpea salad'], cal: 450 },
      { type: 'Snack', foods: ['Kimchi rice crackers'], cal: 120 },
      { type: 'Dinner', foods: ['Baked cod with sweet potato'], cal: 500 },
    ]},
  ],
  foodRecommendations: [
    { category: 'Fermented', items: ['Yogurt', 'Kefir', 'Kimchi', 'Sauerkraut', 'Miso'], score: 10, color: '#22C55E' },
    { category: 'Prebiotic Rich', items: ['Garlic', 'Onion', 'Asparagus', 'Oats', 'Banana'], score: 9, color: '#06B6D4' },
    { category: 'Omega-3 Rich', items: ['Salmon', 'Mackerel', 'Walnuts', 'Flaxseed'], score: 9, color: '#8B5CF6' },
    { category: 'Polyphenol Rich', items: ['Blueberries', 'Green tea', 'Dark chocolate', 'Turmeric'], score: 8, color: '#F59E0B' },
  ],
  supplements: [
    { name: 'Probiotics', dosage: '10B CFU daily', timing: 'Morning', goal: 'Gut Health' },
    { name: 'Omega-3', dosage: '2000mg EPA/DHA', timing: 'With meals', goal: 'Inflammation' },
    { name: 'Vitamin D3', dosage: '2000 IU', timing: 'Morning', goal: 'Immunity' },
    { name: 'Magnesium', dosage: '400mg', timing: 'Evening', goal: 'Sleep' },
  ],
  nutrientsToday: { calories: 1530, target: 2000, protein: 95, targetP: 150, fiber: 22, targetF: 35, water: 5, targetW: 8 },
};

export default function PrecisionNutritionScreen() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#22C55E', '#10B981', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Precision Nutrition</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Your Microbiome</Text>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 2 }]}>{mockData.microbiomeType} • {mockData.metabolicType}</Text>
          <View style={styles.scoreRow}>
            <ScoreRing score={mockData.gutHealthScore} size={100} color="#22C55E" />
            <View style={{ flex: 1, marginLeft: 16 }}>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Gut Health Score</Text>
              <Text style={[typography.metric.large, { color: '#fff' }]}>{mockData.gutHealthScore}/100</Text>
              <Text style={[typography.body.sm, { color: '#22C55E' }]}>Above Average</Text>
            </View>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Today's Nutrition" icon="nutrition" iconColor="#22C55E" />
          <View style={styles.macroRow}>
            {[
              { label: 'Calories', value: mockData.nutrientsToday.calories, target: mockData.nutrientsToday.target, unit: 'kcal', color: '#22C55E' },
              { label: 'Protein', value: mockData.nutrientsToday.protein, target: mockData.nutrientsToday.targetP, unit: 'g', color: '#EF4444' },
              { label: 'Fiber', value: mockData.nutrientsToday.fiber, target: mockData.nutrientsToday.targetF, unit: 'g', color: '#06B6D4' },
            ].map((m, i) => (
              <View key={i} style={styles.macroCard}>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{m.label}</Text>
                <Text style={[typography.metric.small, { color: m.color }]}>{m.value}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>/ {m.target} {m.unit}</Text>
                <View style={[styles.macroBar, { backgroundColor: m.color + '20' }]}>
                  <View style={[styles.macroBarFill, { width: `${Math.min(m.value / m.target * 100, 100)}%`, backgroundColor: m.color }]} />
                </View>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Food Recommendations" icon="leaf" iconColor="#10B981" />
          {mockData.foodRecommendations.map((f, i) => (
            <GlassCard key={i} style={{ marginBottom: 10 }}>
              <View style={styles.foodHeader}>
                <Text style={[typography.label.md, { color: f.color }]}>{f.category}</Text>
                <View style={[styles.scoreBadge, { backgroundColor: f.color + '20' }]}>
                  <Text style={[typography.body.sm, { color: f.color, fontWeight: '700' }]}>{f.score}/10</Text>
                </View>
              </View>
              <View style={styles.foodItems}>
                {f.items.map((item, j) => (
                  <View key={j} style={[styles.foodPill, { borderColor: f.color + '30' }]}>
                    <Text style={[typography.body.xs, { color: f.color }]}>{item}</Text>
                  </View>
                ))}
              </View>
            </GlassCard>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Meal Plan" icon="calendar" iconColor={colors.primary} />
          {mockData.mealPlan.map((day, i) => (
            <GlassCard key={i} style={{ marginBottom: 10 }}>
              <Text style={[typography.label.md, { color: colors.primary, marginBottom: 10 }]}>{day.day}</Text>
              {day.meals.map((meal, j) => (
                <View key={j} style={styles.mealRow}>
                  <Text style={[typography.body.sm, { color: colors.text.muted, width: 70 }]}>{meal.type}</Text>
                  <Text style={[typography.body.sm, { color: colors.text.primary, flex: 1 }]}>{meal.foods.join(', ')}</Text>
                  <Text style={[typography.body.xs, { color: colors.text.muted }]}>{meal.cal} cal</Text>
                </View>
              ))}
            </GlassCard>
          ))}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Supplement Protocol" icon="medical" iconColor={colors.health.energy} />
          {mockData.supplements.map((s, i) => (
            <View key={i} style={styles.supplementCard}>
              <View style={[styles.supIcon, { backgroundColor: colors.health.energy + '18' }]}>
                <Ionicons name="medical" size={16} color={colors.health.energy} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{s.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted }]}>{s.dosage} • {s.timing}</Text>
              </View>
              <Text style={[typography.body.xs, { color: colors.health.energy }]}>{s.goal}</Text>
            </View>
          ))}
        </View>
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  macroRow: { flexDirection: 'row', gap: 10 },
  macroCard: { flex: 1, backgroundColor: colors.bg.card, borderRadius: 14, padding: 12, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
  macroBar: { width: '100%', height: 4, borderRadius: 2, marginTop: 6, overflow: 'hidden' },
  macroBarFill: { height: '100%', borderRadius: 2 },
  foodHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  scoreBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  foodItems: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  foodPill: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  mealRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  supplementCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border, gap: 10 },
  supIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
});
