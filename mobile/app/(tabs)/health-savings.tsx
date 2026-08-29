/**
 * Health Savings Account — HSA/FSA Expense Tracking
 * Balance, contributions, expenses, eligible categories, transaction history.
 */
import React, { useState, useRef } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Animated, Dimensions, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium, ProgressBarPremium, StatCard } from '../../src/components/PremiumComponents';
import { BarChart, MiniLineChart } from '../../src/components/HealthCharts';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const mockData = {
  accountType: 'HSA',
  balance: 3250.00,
  contributions: 4150.00,
  expenses: 899.50,
  limit: 4300,
  monthlyExpenses: [
    { label: 'Jan', value: 120 },
    { label: 'Feb', value: 85 },
    { label: 'Mar', value: 200 },
    { label: 'Apr', value: 45 },
    { label: 'May', value: 180 },
    { label: 'Jun', value: 95 },
  ],
  recentTransactions: [
    { desc: 'Annual Physical', amount: 35.00, date: 'Jun 15', category: 'Doctor Visit', eligible: true },
    { desc: 'Lab Work - CBC', amount: 45.50, date: 'Jun 10', category: 'Lab Work', eligible: true },
    { desc: 'Prescription - Metformin', amount: 15.00, date: 'Jun 5', category: 'Prescription', eligible: true },
    { desc: 'Dental Cleaning', amount: 75.00, date: 'May 28', category: 'Dental', eligible: true },
    { desc: 'New Glasses', amount: 185.00, date: 'May 15', category: 'Vision', eligible: true },
  ],
  eligibleCategories: [
    { name: 'Doctor Visits', icon: 'medical', color: '#EF4444' },
    { name: 'Prescriptions', icon: 'medical', color: '#F59E0B' },
    { name: 'Dental', icon: 'medical', color: '#06B6D4' },
    { name: 'Vision', icon: 'eye', color: '#8B5CF6' },
    { name: 'Lab Work', icon: 'flask', color: '#22C55E' },
    { name: 'Mental Health', icon: 'heart', color: '#A78BFA' },
  ],
};

export default function HealthSavingsScreen() {
  const utilization = (mockData.expenses / mockData.contributions * 100).toFixed(0);
  const remaining = mockData.limit - mockData.contributions;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <LinearGradient colors={['#22C55E', '#06B6D4', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Health Savings Account</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{mockData.accountType}</Text>
          <Text style={[typography.metric.hero, { color: '#fff', marginTop: 16 }]}>${mockData.balance.toLocaleString()}</Text>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Available Balance</Text>
          <View style={styles.statsRow}>
            <View style={styles.statBox}>
              <Text style={[typography.metric.small, { color: '#fff' }]}>${mockData.contributions.toLocaleString()}</Text>
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Contributed</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Text style={[typography.metric.small, { color: '#fff' }]}>${mockData.expenses.toLocaleString()}</Text>
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Spent</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statBox}>
              <Text style={[typography.metric.small, { color: '#fff' }]}>${remaining.toLocaleString()}</Text>
              <Text style={[typography.body.xs, { color: 'rgba(255,255,255,0.6)' }]}>Remaining</Text>
            </View>
          </View>
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Contribution Limit" icon="wallet" iconColor="#22C55E" />
          <GlassCard>
            <ProgressBarPremium value={mockData.contributions} max={mockData.limit} color="#22C55E" showLabel />
            <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 8 }]}>${remaining.toLocaleString()} remaining for 2025</Text>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Monthly Expenses" icon="bar-chart" iconColor={colors.health.activity} />
          <GlassCard>
            <BarChart data={mockData.monthlyExpenses.map(m => ({ value: m.value, label: m.label, color: '#06B6D4' }))} height={100} />
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Eligible Categories" icon="checkmark-circle" iconColor="#22C55E" />
          <View style={styles.categoriesGrid}>
            {mockData.eligibleCategories.map((cat, i) => (
              <TouchableOpacity key={i} style={styles.categoryCard} activeOpacity={0.7}>
                <View style={[styles.categoryIcon, { backgroundColor: cat.color + '18' }]}>
                  <Ionicons name={cat.icon as any} size={20} color={cat.color} />
                </View>
                <Text style={[typography.body.sm, { color: colors.text.primary, marginTop: 6 }]}>{cat.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Recent Transactions" icon="receipt" iconColor={colors.health.nutrition} />
          {mockData.recentTransactions.map((t, i) => (
            <View key={i} style={styles.transactionCard}>
              <View style={[styles.txIcon, { backgroundColor: colors.health.success + '18' }]}>
                <Ionicons name="receipt" size={16} color={colors.health.success} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{t.desc}</Text>
                <Text style={[typography.body.sm, { color: colors.text.muted }]}>{t.category} • {t.date}</Text>
              </View>
              <View>
                <Text style={[typography.body.md, { color: colors.health.danger, fontWeight: '600' }]}>-${t.amount.toFixed(2)}</Text>
                {t.eligible && <Text style={[typography.body.xs, { color: colors.health.success, textAlign: 'right' }]}>Eligible</Text>}
              </View>
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
  statsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', marginTop: 20, backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 16, padding: 16 },
  statBox: { alignItems: 'center', flex: 1 },
  statDivider: { width: 1, height: 32, backgroundColor: 'rgba(255,255,255,0.15)' },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  categoriesGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  categoryCard: { width: (SCREEN_WIDTH - spacing.screenPadding * 2 - 20) / 3, alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: colors.surface.border },
  categoryIcon: { width: 44, height: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  transactionCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.surface.border, gap: 12 },
  txIcon: { width: 32, height: 32, borderRadius: 8, justifyContent: 'center', alignItems: 'center' },
});
