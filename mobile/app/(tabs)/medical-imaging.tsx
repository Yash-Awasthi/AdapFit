/**
 * Skin spot check — ABCDE screening from a photo the server measures, or
 * from the user's own assessment when a photo will not work. A score is a
 * prompt to see a dermatologist, not a diagnosis.
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, TextInput, Dimensions, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { postJson } from '../../src/services/http';
import { COINS, photographAndMeasure } from '../../src/services/photoMeasure';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface ABCDEDetail {
  score: string;
  value: number | boolean;
}

interface LesionResult {
  status: 'scored' | 'insufficient_data';
  abcde_score?: number;
  criteria_assessed?: number;
  abcde_details?: Record<string, ABCDEDetail>;
  risk_level?: string;
  recommendation?: string;
  follow_up_schedule?: { next_exam: string; specialist: string; imaging: string };
  self_monitoring?: string[];
  disclaimer?: string;
  message?: string;
}

const RISK_COLOR: Record<string, string> = {
  low: '#22C55E',
  medium: '#F59E0B',
  high: '#F97316',
  critical: '#EF4444',
};

// Each slider criterion, with the question that decides it. Worded as a
// judgement the user can actually make while looking at the lesion.
const CRITERIA = [
  { key: 'asymmetry_score', letter: 'A', label: 'Asymmetry', question: 'If you folded it in half, how unlike would the halves be?' },
  { key: 'border_irregularity', letter: 'B', label: 'Border', question: 'How ragged or poorly defined is the edge?' },
  { key: 'color_variation', letter: 'C', label: 'Colour', question: 'How much does the colour vary across it?' },
] as const;

const LEVELS = [
  { value: 0.1, label: 'Not at all' },
  { value: 0.35, label: 'Slightly' },
  { value: 0.6, label: 'Noticeably' },
  { value: 0.9, label: 'Very' },
];

export default function MedicalImagingScreen() {
  const [scores, setScores] = useState<Record<string, number>>({});
  const [diameter, setDiameter] = useState('');
  const [evolving, setEvolving] = useState(false);
  const [result, setResult] = useState<LesionResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [coin, setCoin] = useState<number | null>(null);

  const measurePhoto = async () => {
    setSubmitting(true);
    const out = await photographAndMeasure<{ success: boolean; data: LesionResult & { message?: string } }>(
      '/medical-imaging/measure-photo', coin, evolving ? { evolution_detected: 'true' } : {}
    );
    setSubmitting(false);
    if (out === 'cancelled') return;
    if (!out?.success) {
      Alert.alert('Try another photo', out?.data?.message ?? 'The photo could not be measured.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setResult(out.data);
  };

  const answered = CRITERIA.filter((c) => scores[c.key] !== undefined).length;
  const ready = answered === CRITERIA.length && Number(diameter) > 0;

  const assess = async () => {
    const size = Number(diameter);
    if (!ready || !Number.isFinite(size)) {
      Alert.alert('A few more answers', 'Answer all three questions and measure the lesion across its widest point.');
      return;
    }
    setSubmitting(true);
    const response = await postJson<{ success: boolean; data: LesionResult }>(
      '/medical-imaging/analyze-lesion',
      {
        asymmetry_score: scores.asymmetry_score,
        border_irregularity: scores.border_irregularity,
        color_variation: scores.color_variation,
        diameter_mm: size,
        evolution_detected: evolving,
      }
    );
    setSubmitting(false);
    if (!response?.data) {
      Alert.alert('Could not score', 'The assessment could not be completed.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setResult(response.data);
  };

  const reset = () => {
    setScores({});
    setDiameter('');
    setEvolving(false);
    setResult(null);
  };

  const risk = result?.risk_level ?? 'low';
  const tint = RISK_COLOR[risk] ?? '#94A3B8';

  return (
    <ScreenWrapper
      title="Skin Lesion Check"
      subtitle="ABCDE screening from your own assessment"
      gradient={['#EF4444', '#F97316']}
      rightAction={result ? { icon: 'refresh', onPress: reset } : undefined}
    >
      <GlassCard variant="light" style={styles.sectionCard}>
        <Text style={styles.introTitle}>How this works</Text>
        <Text style={styles.introText}>
          Photograph the spot in daylight, about 10 cm away, centred with clear skin around it. Put a
          coin flat beside it to measure its size. ABCDE decides whether a spot is worth showing a
          dermatologist, and nothing more. The photo is not kept.
        </Text>
      </GlassCard>

      {!result && (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.introTitle}>Measure from a photo</Text>
          <View style={styles.levelRow}>
            {COINS.map((c) => {
              const on = coin === c.mm;
              return (
                <TouchableOpacity key={c.label} style={[styles.levelBtn, on && styles.levelBtnOn]} onPress={() => setCoin(c.mm)}
                  accessibilityRole="radio" accessibilityState={{ selected: on }}>
                  <Text style={[styles.levelText, on && styles.levelTextOn]}>{c.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <TouchableOpacity style={[styles.levelBtn, evolving && styles.levelBtnOn, { marginTop: spacing.sm }]}
            onPress={() => setEvolving(!evolving)} accessibilityRole="checkbox" accessibilityState={{ checked: evolving }}>
            <Text style={[styles.levelText, evolving && styles.levelTextOn]}>It has changed recently</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.levelBtn, styles.levelBtnOn, { marginTop: spacing.md }]} onPress={measurePhoto}
            disabled={submitting} accessibilityRole="button">
            <Text style={[styles.levelText, styles.levelTextOn]}>{submitting ? 'Measuring…' : 'Take photo'}</Text>
          </TouchableOpacity>
          <Text style={styles.abcdeDesc}>Or answer the questions below yourself.</Text>
        </GlassCard>
      )}

      {result?.status === 'scored' ? (
        <>
          <View style={styles.resultSection}>
            <View style={[styles.resultBadge, { backgroundColor: tint + '20', borderColor: tint }]}>
              <Text style={[styles.resultScore, { color: tint }]}>{result.abcde_score}/{result.criteria_assessed ?? 5}</Text>
              <Text style={[styles.resultRisk, { color: tint }]}>{risk}</Text>
            </View>
            <Text style={styles.resultRecommendation}>{result.recommendation}</Text>
          </View>

          <SectionHeaderPremium icon="list" iconColor="#3B82F6" title="What Was Assessed" />
          <GlassCard variant="light" style={styles.sectionCard}>
            {Object.entries(result.abcde_details ?? {}).map(([key, detail]) => (
              <View key={key} style={styles.detailRow}>
                <Text style={styles.detailLabel}>{key.replace(/_/g, ' ')}</Text>
                <Text style={[styles.detailValue, {
                  color: ['normal', 'regular', 'uniform', 'stable', 'not_measured', 'not_assessed'].includes(detail.score) ? '#22C55E' : tint,
                }]}>
                  {detail.score.replace(/_/g, ' ')}
                </Text>
              </View>
            ))}
          </GlassCard>

          {result.follow_up_schedule && (
            <GlassCard variant="light" style={styles.sectionCard}>
              <Text style={styles.introTitle}>Follow up</Text>
              <Text style={styles.introText}>
                {result.follow_up_schedule.next_exam} · {result.follow_up_schedule.specialist}
              </Text>
            </GlassCard>
          )}

          <GlassCard variant="light" style={styles.sectionCard}>
            <Text style={styles.disclaimer}>{result.disclaimer}</Text>
          </GlassCard>
        </>
      ) : (
        <>
          <SectionHeaderPremium
            icon="scan"
            iconColor="#EF4444"
            title="Assess the Lesion"
            subtitle={`${answered} of ${CRITERIA.length} answered`}
          />
          {CRITERIA.map((criterion) => (
            <GlassCard key={criterion.key} variant="light" style={styles.sectionCard}>
              <View style={styles.criterionHeader}>
                <View style={styles.abcdeLetter}>
                  <Text style={styles.abcdeLetterText}>{criterion.letter}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.abcdeLabel}>{criterion.label}</Text>
                  <Text style={styles.abcdeDesc}>{criterion.question}</Text>
                </View>
              </View>
              <View style={styles.levelRow}>
                {LEVELS.map((level) => {
                  const selected = scores[criterion.key] === level.value;
                  return (
                    <TouchableOpacity
                      key={level.label}
                      style={[styles.levelBtn, selected && styles.levelBtnOn]}
                      onPress={() => setScores((prev) => ({ ...prev, [criterion.key]: level.value }))}
                      accessibilityRole="radio"
                      accessibilityState={{ selected }}
                      accessibilityLabel={`${criterion.label}: ${level.label}`}
                    >
                      <Text style={[styles.levelText, selected && styles.levelTextOn]}>{level.label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </GlassCard>
          ))}

          <GlassCard variant="light" style={styles.sectionCard}>
            <View style={styles.criterionHeader}>
              <View style={styles.abcdeLetter}>
                <Text style={styles.abcdeLetterText}>D</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.abcdeLabel}>Diameter</Text>
                <Text style={styles.abcdeDesc}>Width at the widest point, in millimetres</Text>
              </View>
            </View>
            <TextInput
              style={styles.input}
              placeholder="e.g. 5"
              placeholderTextColor={colors.text.muted}
              keyboardType="decimal-pad"
              value={diameter}
              onChangeText={setDiameter}
              accessibilityLabel="Diameter in millimetres"
            />
          </GlassCard>

          <GlassCard variant="light" style={styles.sectionCard}>
            <View style={styles.criterionHeader}>
              <View style={styles.abcdeLetter}>
                <Text style={styles.abcdeLetterText}>E</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.abcdeLabel}>Evolving</Text>
                <Text style={styles.abcdeDesc}>Has it changed in size, shape or colour?</Text>
              </View>
            </View>
            <View style={styles.levelRow}>
              {[{ label: 'No change', value: false }, { label: 'It has changed', value: true }].map((option) => (
                <TouchableOpacity
                  key={option.label}
                  style={[styles.levelBtn, evolving === option.value && styles.levelBtnOn]}
                  onPress={() => setEvolving(option.value)}
                  accessibilityRole="radio"
                  accessibilityState={{ selected: evolving === option.value }}
                >
                  <Text style={[styles.levelText, evolving === option.value && styles.levelTextOn]}>
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </GlassCard>

          <TouchableOpacity
            style={[styles.submitBtn, !ready && styles.submitBtnOff]}
            onPress={assess}
            disabled={submitting}
            accessibilityRole="button"
            accessibilityLabel="Score this lesion"
          >
            <Ionicons name="checkmark-circle" size={20} color="#FFF" />
            <Text style={styles.submitBtnText}>{submitting ? 'Scoring…' : 'Score this lesion'}</Text>
          </TouchableOpacity>

          {result?.status === 'insufficient_data' && (
            <GlassCard variant="light" style={styles.sectionCard}>
              <Text style={styles.introText}>{result.message}</Text>
            </GlassCard>
          )}
        </>
      )}
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  introTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  introText: { fontSize: 13, color: colors.text.muted, marginTop: 6, lineHeight: 19 },
  disclaimer: { fontSize: 12, color: colors.text.muted, lineHeight: 18 },

  criterionHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  abcdeLetter: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#EF444415', justifyContent: 'center', alignItems: 'center' },
  abcdeLetterText: { fontSize: 16, fontWeight: '800', color: '#EF4444' },
  abcdeLabel: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  abcdeDesc: { fontSize: 12, color: colors.text.muted, marginTop: 2, lineHeight: 17 },

  levelRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
  levelBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: colors.surface.divider },
  levelBtnOn: { backgroundColor: '#EF4444' },
  levelText: { fontSize: 12, fontWeight: '600', color: colors.text.muted },
  levelTextOn: { color: '#FFF' },

  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15, marginTop: spacing.md },

  submitBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.sm, marginHorizontal: spacing.screenPadding, marginBottom: spacing.xl, backgroundColor: '#EF4444', paddingVertical: spacing.lg, borderRadius: radius.button },
  submitBtnOff: { opacity: 0.5 },
  submitBtnText: { fontSize: 16, fontWeight: '700', color: '#FFF' },

  resultSection: { alignItems: 'center', marginVertical: spacing.lg, paddingHorizontal: spacing.screenPadding },
  resultBadge: { paddingHorizontal: spacing.xl, paddingVertical: spacing.lg, borderRadius: radius.lg, borderWidth: 2, alignItems: 'center' },
  resultScore: { fontSize: 36, fontWeight: '800' },
  resultRisk: { fontSize: 14, fontWeight: '700', textTransform: 'capitalize', marginTop: 2 },
  resultRecommendation: { fontSize: 14, color: colors.text.primary, textAlign: 'center', marginTop: spacing.md, lineHeight: 20 },

  detailRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm },
  detailLabel: { fontSize: 14, color: colors.text.muted, textTransform: 'capitalize' },
  detailValue: { fontSize: 14, fontWeight: '700', textTransform: 'capitalize' },

});
