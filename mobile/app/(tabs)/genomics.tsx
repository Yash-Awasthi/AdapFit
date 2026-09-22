/**
 * Genomics Insights — pharmacogenomics and traits from uploaded variants.
 *
 * Every gene the panel shows has to be one the user actually entered: the
 * backend now refuses to fill in "normal" for a gene nobody tested, so the
 * screen only renders what came back.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApi } from '../../src/hooks/useApi';
import { postJson } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const KNOWN_GENES = ['MTHFR', 'FTO', 'APOE', 'LCT', 'CYP1A2', 'CYP2D6', 'CYP2C19', 'VDR', 'ALDH2'];

interface DiseaseRisk { risk_score: number; risk_level: string; recommendations: string[] }
interface PgxEntry { type: string; affected_drugs: string[]; action: string }
interface NutriEntry { variant_present: boolean; impact: string; recommendation: string; recommended_foods: string[] }
interface Trait { trait: string; status: string; confidence: number }

interface Profile {
  status?: 'no_data';
  message?: string;
  genetic_health_score?: number;
  disease_risks?: Record<string, DiseaseRisk>;
  pharmacogenomics?: Record<string, PgxEntry>;
  nutrigenomics?: Record<string, NutriEntry>;
  genetic_traits?: Trait[];
  total_variants_analyzed?: number;
}

const riskColors: Record<string, string> = { low: '#22C55E', moderate: '#F59E0B', high: '#EF4444' };

export default function GenomicsScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [variants, setVariants] = useState<Record<string, string>>({});

  const { data, loading, refresh, refreshing, reload } = useApi<{ data: Profile }>(`/genomics/profile/${userId}`);
  const profile = data?.data;
  const hasProfile = !!profile && profile.status !== 'no_data';

  const submit = useCallback(async () => {
    const entered = Object.fromEntries(Object.entries(variants).filter(([, v]) => v.trim()));
    if (Object.keys(entered).length === 0) {
      Alert.alert('No variants entered', 'Enter at least one gene variant from your test results.');
      return;
    }
    setBusy(true);
    const result = await postJson('/genomics/analyze', { user_id: userId, genetic_data: { variants: entered } });
    setBusy(false);
    if (!result) {
      Alert.alert('Not saved', 'The analysis could not be run.');
      return;
    }
    await reload();
  }, [variants, userId, reload]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#8B5CF6" />
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
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#8B5CF6" />}
      >
        <LinearGradient colors={['#8B5CF6', '#6366F1', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Genomics Insights</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Your DNA Profile</Text>
          {hasProfile ? (
            <View style={styles.scoreRow}>
              <ScoreRing score={profile!.genetic_health_score ?? 0} size={100} color="#22C55E" />
              <View style={{ flex: 1, marginLeft: 16 }}>
                <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>{profile!.total_variants_analyzed} variants analyzed</Text>
              </View>
            </View>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)', marginTop: 8 }]}>
              Enter results from a DNA test to see your risk and pharmacogenomics profile.
            </Text>
          )}
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Enter Gene Variants" icon="add-circle" iconColor="#8B5CF6" />
          <GlassCard>
            <Text style={styles.helperText}>Leave blank any gene you don't have a result for.</Text>
            {KNOWN_GENES.map((gene) => (
              <TextInput
                key={gene}
                style={styles.input}
                placeholder={`${gene} variant (e.g. C677T)`}
                placeholderTextColor={colors.text.muted}
                value={variants[gene] ?? ''}
                onChangeText={(v) => setVariants((prev) => ({ ...prev, [gene]: v }))}
              />
            ))}
            <TouchableOpacity style={styles.primaryBtn} onPress={submit} disabled={busy}>
              <Text style={styles.primaryBtnText}>{busy ? 'Analyzing…' : 'Analyze'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>

        {hasProfile && (
          <>
            {profile!.disease_risks && Object.keys(profile!.disease_risks).length > 0 && (
              <View style={styles.section}>
                <SectionHeaderPremium title="Disease Risk" icon="analytics" iconColor="#8B5CF6" />
                {Object.entries(profile!.disease_risks).map(([disease, r]) => (
                  <GlassCard key={disease} style={{ marginBottom: 10 }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                      <Text style={[typography.body.md, { color: colors.text.primary, textTransform: 'capitalize' }]}>{disease.replace('_', ' ')}</Text>
                      <Text style={[typography.label.sm, { color: riskColors[r.risk_level] ?? colors.text.muted }]}>{r.risk_level.toUpperCase()}</Text>
                    </View>
                    <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 4 }]}>{r.recommendations[0]}</Text>
                  </GlassCard>
                ))}
              </View>
            )}

            {profile!.genetic_traits && profile!.genetic_traits.length > 0 && (
              <View style={styles.section}>
                <SectionHeaderPremium title="Genetic Traits" icon="finger-print" iconColor="#A78BFA" />
                <View style={styles.traitsGrid}>
                  {profile!.genetic_traits.map((t) => (
                    <View key={t.trait} style={styles.traitCard}>
                      <Text style={[typography.body.sm, { color: colors.text.muted }]}>{t.trait}</Text>
                      <Text style={[typography.body.md, { color: colors.text.primary, fontWeight: '600', marginTop: 2 }]}>{t.status}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {profile!.pharmacogenomics && (
              <View style={styles.section}>
                <SectionHeaderPremium title="Pharmacogenomics" icon="medkit" iconColor="#F59E0B" />
                {Object.entries(profile!.pharmacogenomics)
                  .filter(([, p]) => p.type !== 'not_tested')
                  .map(([gene, p]) => (
                    <GlassCard key={gene} style={{ marginBottom: 10 }}>
                      <Text style={[typography.body.md, { color: colors.text.primary }]}>{gene} · {p.type}</Text>
                      <Text style={[typography.body.sm, { color: colors.text.muted, marginTop: 4 }]}>{p.action}</Text>
                    </GlassCard>
                  ))}
                {Object.values(profile!.pharmacogenomics).every((p) => p.type === 'not_tested') && (
                  <Text style={styles.emptyText}>No pharmacogenomic genes tested yet.</Text>
                )}
              </View>
            )}
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
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginTop: 20 },
  section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.xl },
  helperText: { color: colors.text.muted, fontSize: 13, marginBottom: 8 },
  emptyText: { color: colors.text.muted, fontSize: 13 },
  input: {
    backgroundColor: colors.bg.card, borderRadius: 12, padding: 12, color: colors.text.primary,
    borderWidth: 1, borderColor: colors.surface.border, marginBottom: 10,
  },
  primaryBtn: { backgroundColor: '#8B5CF6', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  traitsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  traitCard: { width: '47%', backgroundColor: colors.bg.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: colors.surface.border },
});
