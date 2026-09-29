/**
 * Longevity — a lifestyle score from answers the user actually gives.
 *
 * The assessment is the screen: without answers there is no score, because
 * unanswered factors are excluded rather than assumed to be good. Biological
 * age is deliberately not shown — a questionnaire cannot produce one, and the
 * number this used to display was the user's real age minus a flat four years.
 */
import React, { useMemo, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, TextInput, Alert, ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { postJson, asArray, asNumber } from '../../src/services/http';
import { useUserStore } from '../../src/stores';

interface FactorScore {
  value: number;
  score: number;
  unit: string;
  status: string;
}

interface Intervention {
  factor: string;
  action: string;
  benefit_years?: number;
  priority?: string;
}

interface BlueZones {
  habits_present: number;
  habits_total: number;
  score: number;
  present: string[];
  missing: string[];
}

interface Assessment {
  status: 'scored' | 'insufficient_data';
  longevity_score?: number;
  factors_answered?: number;
  factors_total?: number;
  unanswered?: string[];
  factor_scores?: Record<string, FactorScore>;
  blue_zones_alignment?: BlueZones;
  top_interventions?: Intervention[];
  longevity_tier?: string;
  disclaimer?: string;
  message?: string;
}

// The questions, in the units the backend scores against.
const QUESTIONS: { key: string; label: string; hint: string; keyboard: 'numeric' | 'decimal-pad' }[] = [
  { key: 'exercise', label: 'Exercise', hint: 'minutes per week', keyboard: 'numeric' },
  { key: 'sleep', label: 'Sleep', hint: 'hours per night', keyboard: 'decimal-pad' },
  { key: 'nutrition', label: 'Diet quality', hint: 'your own score out of 100', keyboard: 'numeric' },
  { key: 'stress', label: 'Stress', hint: '1 (none) to 10 (constant)', keyboard: 'numeric' },
  { key: 'social_connection', label: 'Social connection', hint: 'out of 100', keyboard: 'numeric' },
  { key: 'smoking', label: 'Smoking', hint: 'cigarettes per day, 0 if none', keyboard: 'numeric' },
  { key: 'alcohol', label: 'Alcohol', hint: 'drinks per week, 0 if none', keyboard: 'numeric' },
];

const BLUE_ZONE_LABELS: Record<string, { label: string; icon: string; color: string; desc: string }> = {
  natural_movement: { label: 'Move Naturally', icon: 'walk', color: '#22C55E', desc: 'Active without structured exercise' },
  sense_of_purpose: { label: 'Purpose', icon: 'compass', color: '#3B82F6', desc: 'A reason to get up' },
  downshift: { label: 'Down Shift', icon: 'moon', color: '#8B5CF6', desc: 'A daily ritual for stress' },
  '80_percent_rule': { label: '80% Rule', icon: 'restaurant', color: '#F59E0B', desc: 'Stop eating at 80% full' },
  plant_slant: { label: 'Plant Slant', icon: 'leaf', color: '#22C55E', desc: 'Mostly plants' },
  wine_at_5: { label: 'Wine at 5', icon: 'wine', color: '#EC4899', desc: 'Moderate, and with others' },
  belong_to_tribe: { label: 'Belong', icon: 'people', color: '#F97316', desc: 'A community you are part of' },
  loved_ones_first: { label: 'Loved Ones First', icon: 'heart', color: '#EF4444', desc: 'Family close and first' },
};

function prettyFactor(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function statusColor(status: string): string {
  if (status === 'optimal') return '#22C55E';
  if (status === 'above_optimal' || status === 'near_optimal') return '#F59E0B';
  return '#EF4444';
}

export default function LongevityScreen() {
  const userId = useUserStore((s) => s.userId);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [editing, setEditing] = useState(true);

  const answeredCount = useMemo(
    () => QUESTIONS.filter((q) => Number.isFinite(Number(answers[q.key])) && answers[q.key] !== '').length,
    [answers]
  );

  const submit = async () => {
    const lifestyle: Record<string, number> = {};
    for (const question of QUESTIONS) {
      const raw = answers[question.key];
      if (raw !== undefined && raw !== '' && Number.isFinite(Number(raw))) {
        lifestyle[question.key] = Number(raw);
      }
    }
    if (Object.keys(lifestyle).length < 4) {
      Alert.alert('A few more answers', 'Answer at least four factors — blanks are left out rather than assumed.');
      return;
    }

    setSubmitting(true);
    const result = await postJson<{ success: boolean; data: Assessment }>('/longevity/assess', {
      user_id: userId,
      lifestyle_data: lifestyle,
    });
    setSubmitting(false);

    if (!result?.data) {
      Alert.alert('Could not assess', 'The assessment could not be completed. Try again when you are online.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setAssessment(result.data);
    setEditing(result.data.status !== 'scored');
  };

  const score = asNumber(assessment?.longevity_score);
  const blueZones = assessment?.blue_zones_alignment;
  const factors = assessment?.factor_scores ?? {};
  const interventions = asArray<Intervention>(assessment?.top_interventions);

  return (
    <ScreenWrapper
      title="Longevity"
      subtitle="Score the habits that add years"
      gradient={['#22C55E', '#06B6D4']}
      rightAction={assessment?.status === 'scored' && !editing
        ? { icon: 'create', onPress: () => setEditing(true) }
        : undefined}
    >
      {!!editing && (
        <>
          <SectionHeaderPremium
            icon="clipboard"
            iconColor="#22C55E"
            title="Your Lifestyle"
            subtitle={`${answeredCount} of ${QUESTIONS.length} answered`}
          />
          <GlassCard variant="light" style={styles.sectionCard}>
            <Text style={styles.formIntro}>
              Leave anything blank that you do not know. Blanks are left out of the score
              rather than counted as good.
            </Text>
            {QUESTIONS.map((question) => (
              <View key={question.key} style={styles.field}>
                <View style={styles.fieldLabels}>
                  <Text style={styles.fieldLabel}>{question.label}</Text>
                  <Text style={styles.fieldHint}>{question.hint}</Text>
                </View>
                <TextInput
                  style={styles.input}
                  keyboardType={question.keyboard}
                  value={answers[question.key] ?? ''}
                  onChangeText={(text) => setAnswers((prev) => ({ ...prev, [question.key]: text }))}
                  placeholder="—"
                  placeholderTextColor={colors.text.muted}
                  accessibilityLabel={`${question.label}, ${question.hint}`}
                />
              </View>
            ))}
            <TouchableOpacity
              style={styles.submitButton}
              onPress={submit}
              disabled={submitting}
              accessibilityRole="button"
              accessibilityLabel="Calculate longevity score"
            >
              <Text style={styles.submitText}>{submitting ? 'Scoring…' : 'Score my habits'}</Text>
            </TouchableOpacity>
          </GlassCard>
        </>
      )}

      {assessment?.status === 'insufficient_data' && (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.emptyText}>{assessment.message}</Text>
        </GlassCard>
      )}

      {assessment?.status === 'scored' && (
        <>
          <View style={styles.scoreSection}>
            <ScoreRing
              score={Math.round(score)}
              size={120}
              strokeWidth={8}
              color="#22C55E"
              label="LIFESTYLE"
              sublabel={assessment.longevity_tier ?? ''}
            />
            <Text style={styles.scoreNote}>
              From {assessment.factors_answered} of {assessment.factors_total} factors
            </Text>
          </View>

          <GlassCard variant="light" style={styles.sectionCard}>
            <Text style={styles.disclaimer}>{assessment.disclaimer}</Text>
          </GlassCard>

          <SectionHeaderPremium icon="stats-chart" iconColor="#3B82F6" title="Your Factors" />
          {Object.entries(factors).map(([key, factor]) => (
            <GlassCard key={key} variant="light" style={styles.zoneCard}>
              <View style={styles.zoneRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.zoneName}>{prettyFactor(key)}</Text>
                  <Text style={styles.zoneDesc}>{factor.value} {factor.unit}</Text>
                </View>
                <Text style={[styles.zoneScore, { color: statusColor(factor.status) }]}>
                  {Math.round(factor.score * 100)}%
                </Text>
              </View>
              <ProgressBarPremium value={factor.score * 100} max={100} color={statusColor(factor.status)} height={4} />
            </GlassCard>
          ))}

          {asArray<string>(assessment.unanswered).length > 0 && (
            <GlassCard variant="light" style={styles.sectionCard}>
              <Text style={styles.emptyText}>
                Not answered, and not counted: {assessment.unanswered!.map(prettyFactor).join(', ')}.
              </Text>
            </GlassCard>
          )}

          {!!blueZones && (
            <>
              <SectionHeaderPremium
                icon="globe"
                iconColor="#22C55E"
                title="Blue Zones Alignment"
                subtitle={`${blueZones.habits_present} of ${blueZones.habits_total} habits`}
              />
              {[...blueZones.present, ...blueZones.missing].map((habit) => {
                const style = BLUE_ZONE_LABELS[habit];
                if (!style) return null;
                const present = blueZones.present.includes(habit);
                return (
                  <GlassCard key={habit} variant="light" style={[styles.zoneCard, !present && styles.zoneMissing]}>
                    <View style={styles.zoneRow}>
                      <View style={[styles.zoneIcon, { backgroundColor: style.color + '15' }]}>
                        <Ionicons name={style.icon as any} size={18} color={present ? style.color : colors.text.muted} />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.zoneName}>{style.label}</Text>
                        <Text style={styles.zoneDesc}>{style.desc}</Text>
                      </View>
                      <Ionicons
                        name={present ? 'checkmark-circle' : 'ellipse-outline'}
                        size={22}
                        color={present ? style.color : colors.text.muted}
                      />
                    </View>
                  </GlassCard>
                );
              })}
            </>
          )}

          {interventions.length > 0 && (
            <>
              <SectionHeaderPremium icon="bulb" iconColor="#F59E0B" title="Where to Start" />
              {interventions.map((item, i) => (
                <GlassCard key={i} variant="light" style={styles.zoneCard}>
                  <Text style={styles.zoneName}>{item.action}</Text>
                  {typeof item.benefit_years === 'number' && (
                    <Text style={styles.zoneDesc}>
                      Population studies associate this with about {item.benefit_years} extra years —
                      an average across many people, not a prediction for you.
                    </Text>
                  )}
                </GlassCard>
              ))}
            </>
          )}
        </>
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  formIntro: { fontSize: 13, color: colors.text.muted, lineHeight: 19, marginBottom: spacing.md },
  field: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  fieldLabels: { flex: 1 },
  fieldLabel: { fontSize: 14, fontWeight: '600', color: colors.text.primary },
  fieldHint: { fontSize: 11, color: colors.text.muted, marginTop: 2 },
  input: { width: 96, backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, color: colors.text.primary, fontSize: 15, textAlign: 'right' },
  submitButton: { backgroundColor: '#22C55E', borderRadius: radius.md, paddingVertical: spacing.md, alignItems: 'center', marginTop: spacing.sm },
  submitText: { color: '#FFF', fontWeight: '700', fontSize: 15 },

  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  scoreNote: { fontSize: 12, color: colors.text.muted, marginTop: spacing.sm },
  disclaimer: { fontSize: 12, color: colors.text.muted, lineHeight: 18 },
  emptyText: { fontSize: 13, color: colors.text.muted, lineHeight: 19 },

  zoneCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  zoneMissing: { opacity: 0.6 },
  zoneRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  zoneIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  zoneName: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  zoneDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 17 },
  zoneScore: { fontSize: 16, fontWeight: '800' },
});
