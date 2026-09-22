/**
 * Health Equity — community SDOH scoring and local resources.
 *
 * The overall score only counts categories someone actually scored, so a
 * community with one category filled in shows that one score, not five
 * invented 50s averaged in with it.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, TextInput,
  StatusBar, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, typography } from '../../src/theme';
import { ScoreRing, GlassCard, SectionHeaderPremium } from '../../src/components/PremiumComponents';
import { useApi, useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

const CATEGORIES = [
  { key: 'economic_stability', label: 'Economic Stability' },
  { key: 'education_access', label: 'Education Access' },
  { key: 'healthcare_access', label: 'Healthcare Access' },
  { key: 'neighborhood_environment', label: 'Neighborhood' },
  { key: 'social_community', label: 'Social & Community' },
  { key: 'food_security', label: 'Food Security' },
];

interface Community { id: string; name: string; population: number; overall_score: number; equity_grade?: string }
interface Recommendation { name: string; impact: string; cost: string; target_category: string; description: string }
interface Resource { id: string; name: string; type: string; address: string; phone: string }

export default function HealthEquityScreen() {
  const userId = useUserStore((s) => s.userId);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState('');
  const [population, setPopulation] = useState('');
  const [scores, setScores] = useState<Record<string, string>>({});

  const { data: communitiesData, loading: communitiesLoading, reload: reloadCommunities } = useApi<Community[]>('/health-equity/communities');
  const communities = asArray<Community>(communitiesData);
  const community = communities[0];

  const { data, loading, refresh, refreshing, reload } = useApis<{
    recommendations: Recommendation[];
    resources: Resource[];
  }>(community ? {
    recommendations: `/health-equity/recommendations/${community.id}`,
    resources: `/health-equity/resources/${community.id}`,
  } : null);

  const recommendations = asArray<Recommendation>(data.recommendations);
  const resources = asArray<Resource>(data.resources);

  const createCommunity = useCallback(async () => {
    if (!name.trim() || !population.trim()) {
      Alert.alert('Details needed', 'Enter a community name and population.');
      return;
    }
    setBusy(true);
    const id = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const result = await postJson(`/health-equity/community/create`, {
      community_id: `${id}-${userId}`,
      name: name.trim(),
      population: Math.round(Number(population)) || 0,
    });
    setBusy(false);
    if (!result) {
      Alert.alert('Not created', 'The community profile could not be created.');
      return;
    }
    await reloadCommunities();
  }, [name, population, userId, reloadCommunities]);

  const submitScores = useCallback(async () => {
    const entered = Object.fromEntries(
      Object.entries(scores).filter(([, v]) => v.trim()).map(([k, v]) => [k, Number(v)])
    );
    if (Object.keys(entered).length === 0) {
      Alert.alert('No scores entered', 'Score at least one category, 0-100.');
      return;
    }
    setBusy(true);
    const result = await postJson('/health-equity/sdoh/score', { community_id: community!.id, category_scores: entered });
    setBusy(false);
    if (!result) {
      Alert.alert('Not saved', 'The scores could not be saved.');
      return;
    }
    await reloadCommunities();
    await reload();
  }, [scores, community, reloadCommunities, reload]);

  if (communitiesLoading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#6366F1" />
      </View>
    );
  }

  if (!community) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <LinearGradient colors={['#6366F1', '#8B5CF6', '#0F1629']} style={styles.hero}>
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Health Equity</Text>
            <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>Register a Community</Text>
          </LinearGradient>
          <View style={styles.section}>
            <GlassCard>
              <TextInput
                style={styles.input}
                placeholder="Community name"
                placeholderTextColor={colors.text.muted}
                value={name}
                onChangeText={setName}
              />
              <TextInput
                style={styles.input}
                placeholder="Population"
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={population}
                onChangeText={setPopulation}
              />
              <TouchableOpacity style={styles.primaryBtn} onPress={createCommunity} disabled={busy}>
                <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Create'}</Text>
              </TouchableOpacity>
            </GlassCard>
          </View>
        </ScrollView>
      </View>
    );
  }

  const scored = community.overall_score > 0;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor="#6366F1" />}
      >
        <LinearGradient colors={['#6366F1', '#8B5CF6', '#0F1629']} style={styles.hero}>
          <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.7)' }]}>Health Equity</Text>
          <Text style={[typography.heading.h1, { color: '#fff', marginTop: 4 }]}>{community.name}</Text>
          {scored ? (
            <View style={styles.scoreRow}>
              <ScoreRing score={community.overall_score} size={100} color={colors.health.activity} />
              <View style={{ flex: 1, marginLeft: 16 }}>
                <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)' }]}>SDOH Score</Text>
                <Text style={[typography.metric.large, { color: '#fff' }]}>{community.overall_score}/100</Text>
                <Text style={[typography.body.sm, { color: colors.health.warning }]}>Grade: {community.equity_grade}</Text>
              </View>
            </View>
          ) : (
            <Text style={[typography.body.sm, { color: 'rgba(255,255,255,0.6)', marginTop: 8 }]}>Score categories below to see a rating.</Text>
          )}
        </LinearGradient>

        <View style={styles.section}>
          <SectionHeaderPremium title="Score SDOH Categories" icon="analytics" iconColor="#6366F1" />
          <GlassCard>
            <Text style={styles.helperText}>0-100, higher is better. Leave blank what you can't estimate.</Text>
            {CATEGORIES.map((c) => (
              <TextInput
                key={c.key}
                style={styles.input}
                placeholder={c.label}
                placeholderTextColor={colors.text.muted}
                keyboardType="numeric"
                value={scores[c.key] ?? ''}
                onChangeText={(v) => setScores((prev) => ({ ...prev, [c.key]: v }))}
              />
            ))}
            <TouchableOpacity style={styles.primaryBtn} onPress={submitScores} disabled={busy}>
              <Text style={styles.primaryBtnText}>{busy ? 'Saving…' : 'Save scores'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Recommended Interventions" icon="bulb" iconColor="#F59E0B" />
          {loading ? (
            <ActivityIndicator color="#6366F1" />
          ) : recommendations.length === 0 ? (
            <Text style={styles.emptyText}>{scored ? 'No weak categories found.' : 'Score a category below 60 to see recommendations.'}</Text>
          ) : (
            recommendations.map((r, i) => (
              <GlassCard key={`${r.name}-${i}`} style={{ marginBottom: 10 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{r.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 4 }]}>{r.description}</Text>
              </GlassCard>
            ))
          )}
        </View>

        <View style={styles.section}>
          <SectionHeaderPremium title="Local Resources" icon="location" iconColor="#22C55E" />
          {resources.length === 0 ? (
            <Text style={styles.emptyText}>No resources added yet.</Text>
          ) : (
            resources.map((r) => (
              <GlassCard key={r.id} style={{ marginBottom: 10 }}>
                <Text style={[typography.body.md, { color: colors.text.primary }]}>{r.name}</Text>
                <Text style={[typography.body.xs, { color: colors.text.muted, marginTop: 2 }]}>{r.type} · {r.address}</Text>
              </GlassCard>
            ))
          )}
        </View>
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  center: { justifyContent: 'center', alignItems: 'center', flex: 1 },
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
  primaryBtn: { backgroundColor: '#6366F1', borderRadius: 12, padding: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
});
