/**
 * Health Savings Account — real balance, contributions, and expenses.
 *
 * An expense's eligible flag now comes from the category, not a hardcoded
 * true, so the category breakdown and history reflect what was actually
 * logged rather than a always-eligible sample month.
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

interface Account { type: string; balance: number; total_contributions: number; total_expenses: number; contribution_limit: number }
interface Summary {
  error?: string;
  account?: Account;
  summary?: { contributions_this_year: number; expenses_this_year: number; current_balance: number; remaining_to_contribute: number };
  category_breakdown?: Record<string, number>;
  recent_transactions?: { id: string; type: string; amount: number; category?: string; description?: string; eligible?: boolean }[];
}

export default function HealthSavingsScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [accountType, setAccountType] = useState<'hsa' | 'fsa'>('hsa');
  const [contribAmount, setContribAmount] = useState('');
  const [expAmount, setExpAmount] = useState('');
  const [expCategory, setExpCategory] = useState('');
  const [expDesc, setExpDesc] = useState('');

  const { data, loading, refresh, refreshing, reload } = useApis<{ summary: Summary }>({
    summary: `/health-savings/summary/${userId}`,
  });

  const summary = data.summary;
  const hasAccount = !!summary && !summary.error;
  const transactions = asArray<NonNullable<Summary['recent_transactions']>[number]>(summary?.recent_transactions);

  const createAccount = useCallback(async () => {
    setBusy(true);
    const result = await postJson('/health-savings/account/create', { user_id: userId, account_type: accountType });
    setBusy(false);
    if (!result) {
      Alert.alert('Not created', 'The account could not be created.');
      return;
    }
    await reload();
  }, [userId, accountType, reload]);

  const contribute = useCallback(async () => {
    const amount = Number(contribAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      Alert.alert('Amount needed', 'Enter a contribution amount.');
      return;
    }
    setBusy(true);
    const result = await postJson('/health-savings/contribute', { user_id: userId, amount });
    setBusy(false);
    if (!result || (result as any).error) {
      Alert.alert('Not saved', (result as any)?.error ?? 'The contribution could not be saved.');
      return;
    }
    setContribAmount('');
    await reload();
  }, [contribAmount, userId, reload]);

  const logExpense = useCallback(async () => {
    const amount = Number(expAmount);
    if (!Number.isFinite(amount) || amount <= 0 || !expCategory.trim()) {
      Alert.alert('Details needed', 'Enter an amount and a category.');
      return;
    }
    setBusy(true);
    const result = await postJson('/health-savings/expense', {
      user_id: userId, amount, category: expCategory.trim(), description: expDesc.trim() || expCategory.trim(),
    });
    setBusy(false);
    if (!result || (result as any).error) {
      Alert.alert('Not saved', (result as any)?.error ?? 'The expense could not be saved.');
      return;
    }
    setExpAmount('');
    setExpDesc('');
    await reload();
  }, [expAmount, expCategory, expDesc, userId, reload]);

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
        <LinearGradient colors={['#22C55E', '#06B6D4', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Health Savings Account</Text>
          {hasAccount ? (
            <>
              <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{summary!.account!.type.toUpperCase()}</Text>
              <Text style={[typography.metric.hero, { color: '#fff', marginTop: 16 }]}>${summary!.summary!.current_balance.toLocaleString()}</Text>
              <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>Available Balance</Text>
            </>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 8 }]}>Open an account to start tracking.</Text>
          )}
        </LinearGradient>

        {!hasAccount && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Open an Account" icon="wallet" iconColor="#22C55E" />
            <GlassCard>
              <View style={styles.chipRow}>
                {(['hsa', 'fsa'] as const).map((t) => (
                  <TouchableOpacity key={t} style={[styles.chip, accountType === t && styles.chipActive]} onPress={() => setAccountType(t)}>
                    <Text style={[styles.chipText, accountType === t && styles.chipTextActive]}>{t.toUpperCase()}</Text>
                  </TouchableOpacity>
                ))}
              </View>
              <TouchableOpacity style={styles.primaryBtn} onPress={createAccount} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Open account'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        )}

        {!!hasAccount && (
          <>
            <View style={styles.section}>
              <SectionHeaderPremium title="Contribute" icon="add-circle" iconColor="#22C55E" />
              <GlassCard>
                <TextInput
                  style={styles.input}
                  placeholder="Amount"
                  placeholderTextColor={colors.text.muted}
                  keyboardType="decimal-pad"
                  value={contribAmount}
                  onChangeText={setContribAmount}
                />
                <TouchableOpacity style={styles.primaryBtn} onPress={contribute} disabled={busy}>
                  <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Add contribution'}</Text>
                </TouchableOpacity>
              </GlassCard>
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Log an Expense" icon="receipt" iconColor="#F59E0B" />
              <GlassCard>
                <TextInput
                  style={styles.input}
                  placeholder="Amount"
                  placeholderTextColor={colors.text.muted}
                  keyboardType="decimal-pad"
                  value={expAmount}
                  onChangeText={setExpAmount}
                />
                <TextInput
                  style={styles.input}
                  placeholder="Category (e.g. Doctor Visit)"
                  placeholderTextColor={colors.text.muted}
                  value={expCategory}
                  onChangeText={setExpCategory}
                />
                <TextInput
                  style={styles.input}
                  placeholder="Description (optional)"
                  placeholderTextColor={colors.text.muted}
                  value={expDesc}
                  onChangeText={setExpDesc}
                />
                <TouchableOpacity style={styles.primaryBtn} onPress={logExpense} disabled={busy}>
                  <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Log expense'}</Text>
                </TouchableOpacity>
              </GlassCard>
            </View>

            <View style={styles.section}>
              <SectionHeaderPremium title="Recent Transactions" icon="list" iconColor={colors.text.muted} />
              {transactions.length === 0 ? (
                <Text style={styles.emptyText}>No transactions yet.</Text>
              ) : (
                transactions.slice().reverse().map((t) => (
                  <View key={t.id} style={styles.txRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={[typography.body.md, { color: colors.text.primary }]}>{t.description ?? t.category ?? t.type}</Text>
                      {t.type === 'expense' && (
                        <Text style={[typography.body.xs, { color: t.eligible ? colors.health.success : colors.health.warning }]}>
                          {t.eligible ? 'Eligible' : 'Not eligible — check your plan'}
                        </Text>
                      )}
                    </View>
                    <Text style={[typography.body.md, { color: t.type === 'contribution' ? colors.health.success : colors.text.primary, fontWeight: '700' }]}>
                      {t.type === 'contribution' ? '+' : '-'}${t.amount.toFixed(2)}
                    </Text>
                  </View>
                ))
              )}
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
  emptyText: { color: colors.text.muted, fontSize: 13 },
  txRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 0.5, borderBottomColor: colors.surface.divider },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#22C55E', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  chipRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  chip: { flex: 1, paddingVertical: 10, borderRadius: 10, backgroundColor: colors.bg.card, borderWidth: 1, borderColor: colors.surface.border, alignItems: 'center' },
  chipActive: { backgroundColor: '#22C55E20', borderColor: '#22C55E' },
  chipText: { color: colors.text.muted, fontSize: 13, fontWeight: '600' },
  chipTextActive: { color: '#22C55E' },
});
