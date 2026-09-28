/**
 * Daily Briefing — today's readiness call, insights that cite the user's own
 * numbers, and the weekly report. Questions go to the Coach chat.
 */
import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar, ActivityIndicator, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { colors, spacing } from '../../src/theme';
import { GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { asArray, postJson } from '../../src/services/http';

const TINT = '#6366F1';
const PRIORITY_COLORS: Record<string, string> = { high: '#EF4444', medium: '#F59E0B', low: '#10B981' };
const CATEGORY_ICONS: Record<string, string> = {
  recovery: 'battery-charging', safety: 'medkit', hrv: 'pulse', sleep: 'moon', load: 'barbell',
  consistency: 'calendar', mind: 'happy',
};

interface Insight { category: string; title: string; message: string; action: string; priority: string }
interface Briefing { date: string; today: Insight | null; insights: Insight[]; to_unlock: string[]; motivation: string }
interface Report { status: string; period?: string; summary?: string; focus?: string; message?: string }

export default function BriefingScreen() {
  const router = useRouter();
  const [rated, setRated] = useState<Record<string, boolean>>({});
  const { data, loading, refresh, refreshing } = useApis<{ briefing: Briefing; report: Report }>({
    briefing: '/ai-coach/briefing',
    report: '/ai-coach/weekly-report',
  });
  const briefing = data.briefing;
  const report = data.report;

  const rate = async (category: string, helpful: boolean) => {
    setRated((r) => ({ ...r, [category]: helpful }));
    await postJson('/ai-coach/feedback', { category, helpful });
  };

  if (loading) {
    return <View style={[styles.container, styles.center]}><ActivityIndicator size="large" color={TINT} /></View>;
  }

  const today = briefing?.today;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={TINT} />}>
        <LinearGradient colors={[TINT, '#4338CA', colors.bg.deep]} style={styles.hero}>
          <Text style={styles.heroMuted}>Daily Briefing</Text>
          {today ? (
            <>
              <Text style={styles.heroTitle}>{today.title}</Text>
              <Text style={styles.heroBody}>{today.message}</Text>
            </>
          ) : (
            <>
              <Text style={styles.heroTitle}>Check in to get today's call</Text>
              <Text style={styles.heroBody}>Your readiness comes from your own HRV, sleep and how you feel.</Text>
            </>
          )}
          {briefing?.motivation ? <Text style={[styles.heroMuted, { marginTop: 12, fontStyle: 'italic' }]}>{briefing.motivation}</Text> : null}
        </LinearGradient>

        {asArray<Insight>(briefing?.insights).length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="What Your Data Says" icon="analytics" iconColor={TINT} />
            {asArray<Insight>(briefing?.insights).map((i) => (
              <GlassCard key={i.title} style={[styles.card, { borderLeftColor: PRIORITY_COLORS[i.priority] ?? TINT }]}>
                <View style={styles.cardHead}>
                  <Ionicons name={(CATEGORY_ICONS[i.category] ?? 'bulb') as any} size={20} color={PRIORITY_COLORS[i.priority] ?? TINT} />
                  <Text style={styles.cardTitle}>{i.title}</Text>
                </View>
                <Text style={styles.body}>{i.message}</Text>
                <Text style={styles.action}>→ {i.action}</Text>
                <View style={styles.rateRow}>
                  {rated[i.category] === undefined ? (
                    <>
                      <Text style={styles.muted}>Useful?</Text>
                      <TouchableOpacity onPress={() => rate(i.category, true)} accessibilityLabel="Useful">
                        <Ionicons name="thumbs-up-outline" size={18} color={colors.text.muted} />
                      </TouchableOpacity>
                      <TouchableOpacity onPress={() => rate(i.category, false)} accessibilityLabel="Not useful">
                        <Ionicons name="thumbs-down-outline" size={18} color={colors.text.muted} />
                      </TouchableOpacity>
                    </>
                  ) : (
                    <Text style={styles.muted}>Thanks, noted.</Text>
                  )}
                </View>
              </GlassCard>
            ))}
          </View>
        )}

        {asArray<string>(briefing?.to_unlock).length > 0 && (
          <View style={styles.section}>
            <SectionHeaderPremium title="Unlock More Insights" icon="lock-open" iconColor={TINT} />
            <GlassCard>
              {asArray<string>(briefing?.to_unlock).map((m) => (
                <Text key={m} style={styles.body}>• Log {m}</Text>
              ))}
            </GlassCard>
          </View>
        )}

        <View style={styles.section}>
          <SectionHeaderPremium title="This Week" subtitle={report?.period} icon="document-text" iconColor={TINT} />
          <GlassCard>
            {report?.status === 'ok' ? (
              <>
                <Text style={styles.body}>{report.summary}</Text>
                <Text style={styles.action}>{report.focus}</Text>
              </>
            ) : (
              <Text style={styles.muted}>{report?.message ?? 'The weekly report could not be loaded.'}</Text>
            )}
          </GlassCard>
        </View>

        <View style={styles.section}>
          <TouchableOpacity style={styles.primaryBtn} onPress={() => router.push('/chat' as any)}>
            <Ionicons name="chatbubble-ellipses" size={18} color="#fff" />
            <Text style={styles.primaryBtnText}>Ask your coach</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center' },
  scrollContent: { paddingBottom: 100 },
  hero: { paddingTop: 60, paddingBottom: 24, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroMuted: { color: 'rgba(255,255,255,0.8)', fontSize: 13 },
  heroTitle: { color: '#fff', fontSize: 26, fontWeight: '800', marginTop: 6 },
  heroBody: { color: 'rgba(255,255,255,0.9)', fontSize: 14, marginTop: 6, lineHeight: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  card: { marginBottom: 10, borderLeftWidth: 3 },
  cardHead: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  cardTitle: { color: colors.text.primary, fontSize: 15, fontWeight: '700', flex: 1 },
  body: { color: colors.text.secondary, fontSize: 14, marginTop: 6, lineHeight: 20 },
  action: { color: TINT, fontSize: 13, fontWeight: '600', marginTop: 8 },
  muted: { color: colors.text.muted, fontSize: 12 },
  rateRow: { flexDirection: 'row', alignItems: 'center', gap: 14, marginTop: 10 },
  primaryBtn: { flexDirection: 'row', gap: 8, backgroundColor: TINT, borderRadius: 12, padding: 14, alignItems: 'center', justifyContent: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
});
