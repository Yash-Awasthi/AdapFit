/**
 * Today's decision card.
 *
 * The one answer the home screen leads with. Numbers appear only as the
 * reasons behind the decision, never as a wall of readings the user has to
 * interpret themselves.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius } from '../theme';
import { getJson, asArray } from '../services/http';
import { useUserStore } from '../stores';

type DecisionName = 'TRAIN' | 'REDUCE' | 'RECOVER' | 'REST';

interface DecisionPayload {
  decision: DecisionName;
  headline: string;
  reasons: string[];
  cautions: string[];
  confidence: 'low' | 'medium' | 'high';
  intensity_ceiling_pct: number;
  safety_override: string | null;
}

const STYLE: Record<DecisionName, { color: string; icon: string; action: string; route: string }> = {
  TRAIN: { color: colors.health.calm, icon: 'barbell', action: 'Start workout', route: '/workout' },
  REDUCE: { color: colors.health.stress, icon: 'trending-down', action: 'See lighter session', route: '/workout' },
  RECOVER: { color: colors.health.activity, icon: 'leaf', action: 'Start recovery session', route: '/workout' },
  REST: { color: colors.health.sleep, icon: 'moon', action: 'Plan tomorrow', route: '/trends' },
};

export function TodayDecision() {
  const router = useRouter();
  const userId = useUserStore((s) => s.userId);
  const [data, setData] = useState<DecisionPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [showWhy, setShowWhy] = useState(false);

  const load = useCallback(async () => {
    const result = await getJson<DecisionPayload>(`/decision/today?user_id=${userId}`);
    setData(result);
    setLoading(false);
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <View style={[styles.card, styles.loading]}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }
  if (!data) return null;

  const style = STYLE[data.decision] ?? STYLE.REDUCE;
  const reasons = asArray<string>(data.reasons);
  const cautions = asArray<string>(data.cautions);

  return (
    <View style={[styles.card, { borderColor: style.color + '55' }]}>
      <View style={styles.top}>
        <View style={[styles.icon, { backgroundColor: style.color + '22' }]}>
          <Ionicons name={style.icon as any} size={24} color={style.color} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.label}>TODAY</Text>
          <Text style={[styles.headline, { color: style.color }]} numberOfLines={2}>
            {data.headline}
          </Text>
        </View>
      </View>

      {data.decision === 'REST' && (
        <View style={styles.restNote}>
          <Ionicons name="checkmark-circle" size={14} color={colors.health.calm} />
          <Text style={styles.restNoteText}>Rest is part of the plan, not a missed day.</Text>
        </View>
      )}

      <TouchableOpacity
        style={styles.whyToggle}
        onPress={() => setShowWhy((v) => !v)}
        accessibilityRole="button"
        accessibilityLabel={showWhy ? 'Hide reasons' : 'Show reasons'}
      >
        <Text style={styles.whyText}>Why</Text>
        <Ionicons
          name={showWhy ? 'chevron-up' : 'chevron-down'}
          size={14}
          color={colors.text.muted}
        />
      </TouchableOpacity>

      {showWhy && (
        <View style={styles.reasons}>
          {reasons.map((r) => (
            <View key={r} style={styles.reasonRow}>
              <Ionicons name="ellipse" size={5} color={style.color} />
              <Text style={styles.reasonText}>{r}</Text>
            </View>
          ))}
          {cautions.map((c) => (
            <View key={c} style={styles.reasonRow}>
              <Ionicons name="alert-circle-outline" size={13} color={colors.health.stress} />
              <Text style={[styles.reasonText, { color: colors.health.stress }]}>{c}</Text>
            </View>
          ))}
          <Text style={styles.confidence}>
            Confidence: {data.confidence}
          </Text>
        </View>
      )}

      <TouchableOpacity
        style={[styles.action, { backgroundColor: style.color }]}
        onPress={() => router.push(style.route as any)}
        accessibilityRole="button"
      >
        <Text style={styles.actionText}>{style.action}</Text>
        <Ionicons name="arrow-forward" size={16} color="#FFF" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: spacing.screenPadding,
    marginTop: spacing.xl,
    backgroundColor: colors.bg.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.surface.border,
    padding: spacing.lg,
  },
  loading: { alignItems: 'center', justifyContent: 'center', minHeight: 120 },
  top: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  icon: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  label: {
    fontSize: 11, fontWeight: '700', color: colors.text.muted,
    letterSpacing: 1, marginBottom: 2,
  },
  headline: { fontSize: 20, fontWeight: '800', letterSpacing: -0.3 },

  restNote: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: spacing.md },
  restNoteText: { flex: 1, fontSize: 12, color: colors.text.secondary },

  whyToggle: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: spacing.md },
  whyText: { fontSize: 13, fontWeight: '700', color: colors.text.muted },

  reasons: { marginTop: spacing.sm, gap: spacing.sm },
  reasonRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  reasonText: { flex: 1, fontSize: 13, color: colors.text.secondary, lineHeight: 19 },
  confidence: { fontSize: 11, color: colors.text.muted, marginTop: spacing.xs },

  action: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm,
    height: 46, borderRadius: radius.button, marginTop: spacing.lg,
  },
  actionText: { fontSize: 15, fontWeight: '700', color: '#FFF' },
});
