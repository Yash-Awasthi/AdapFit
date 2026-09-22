/**
 * Skin Health — mole tracking by measurement, and real UV.
 *
 * A mole is tracked by measuring it: size in millimetres and colour, recorded
 * over time. That is what turns the "E" of ABCDE — evolving — into something
 * a phone can actually notice, and change is the sign that most warrants a
 * clinician. There is no photo analysis here, because the one that existed
 * returned the same reassuring verdict for every mole.
 *
 * UV comes from Open-Meteo for the user's location rather than a fixed 4.
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, TextInput, Modal, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { ScreenWrapper } from '../../src/components/ScreenWrapper';
import { GlassCard, SectionHeaderPremium, ScoreRing } from '../../src/components/PremiumComponents';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray, asNumber } from '../../src/services/http';

interface ABCDEScore {
  asymmetry: number;
  border: number;
  color_irregularity: number;
  diameter: number;
  evolution: number;
  total: number;
  risk_level: string;
}

interface Mole {
  id: string;
  name: string;
  body_location: string;
  size_mm: number;
  color: string;
  last_checked: number;
  abcde_score: ABCDEScore;
  status: string;
}

interface UVReading {
  status?: 'ok' | 'unavailable';
  uv_index?: number;
  level?: string;
  protection_needed?: string;
  sunscreen_spf?: string;
  message?: string;
}

const RISK_COLOR: Record<string, string> = {
  low: '#22C55E',
  moderate: '#F59E0B',
  high: '#EF4444',
};

const UV_LEVELS = [
  { level: 'Low', color: '#22C55E' },
  { level: 'Moderate', color: '#F59E0B' },
  { level: 'High', color: '#F97316' },
  { level: 'Very High', color: '#EF4444' },
  { level: 'Extreme', color: '#DC2626' },
];

const ABCDE_GUIDE = [
  { letter: 'A', key: 'asymmetry' as const, label: 'Asymmetry', desc: 'One half unlike the other' },
  { letter: 'B', key: 'border' as const, label: 'Border', desc: 'Irregular, scalloped, or poorly defined' },
  { letter: 'C', key: 'color_irregularity' as const, label: 'Color', desc: 'Varied from one area to another' },
  { letter: 'D', key: 'diameter' as const, label: 'Diameter', desc: 'Larger than 6mm (pencil eraser)' },
  { letter: 'E', key: 'evolution' as const, label: 'Evolving', desc: 'Changing in size, shape, or color' },
];

// Where the user is, for the UV reading. The profile does not carry a
// location yet, so this is asked for rather than guessed.
const DEFAULT_LOCATION = '';

function MoleForm({ visible, title, submitLabel, onClose, onSubmit, withName }: {
  visible: boolean;
  title: string;
  submitLabel: string;
  withName: boolean;
  onClose: () => void;
  onSubmit: (values: { name: string; location: string; size: number; color: string }) => Promise<void>;
}) {
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [size, setSize] = useState('');
  const [color, setColor] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    const parsed = Number(size);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      Alert.alert('Measurement needed', 'Measure the mole across its widest point, in millimetres.');
      return;
    }
    if (withName && !name.trim()) {
      Alert.alert('Name it', 'Give the mole a name so you can find it again.');
      return;
    }
    setSaving(true);
    await onSubmit({ name: name.trim(), location: location.trim(), size: parsed, color: color.trim() });
    setSaving(false);
    setName('');
    setLocation('');
    setSize('');
    setColor('');
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>{title}</Text>
          {withName && (
            <>
              <TextInput style={styles.input} placeholder="Name, e.g. left forearm"
                placeholderTextColor={colors.text.muted} value={name} onChangeText={setName}
                accessibilityLabel="Mole name" />
              <TextInput style={styles.input} placeholder="Body area, e.g. arm"
                placeholderTextColor={colors.text.muted} value={location} onChangeText={setLocation}
                accessibilityLabel="Body area" />
            </>
          )}
          <TextInput style={styles.input} placeholder="Width in mm, at the widest point"
            placeholderTextColor={colors.text.muted} keyboardType="decimal-pad"
            value={size} onChangeText={setSize} accessibilityLabel="Width in millimetres" />
          <TextInput style={styles.input} placeholder="Colour, e.g. brown"
            placeholderTextColor={colors.text.muted} value={color} onChangeText={setColor}
            accessibilityLabel="Colour" />
          <View style={styles.modalActions}>
            <TouchableOpacity onPress={onClose} style={[styles.modalButton, styles.modalCancel]}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={submit} disabled={saving} style={[styles.modalButton, styles.modalSave]}>
              <Text style={styles.modalSaveText}>{saving ? 'Saving…' : submitLabel}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

export default function SkinHealthScreen() {
  const [location, setLocation] = useState(DEFAULT_LOCATION);
  const [adding, setAdding] = useState(false);
  const [measuring, setMeasuring] = useState<Mole | null>(null);

  const { data, loading, refreshing, refresh, reload } = useApis<{
    moles: { moles: Mole[] };
    uv: UVReading;
  }>({
    moles: '/skin/moles',
    uv: location ? `/environmental/uv-index/${encodeURIComponent(location)}` : '/skin/uv-history',
  });

  const moles = asArray<Mole>(data.moles?.moles);
  const uv = location ? data.uv : null;

  // The highest ABCDE total across tracked moles, which is what should draw
  // the eye. No moles means no score rather than a reassuring one.
  const highest = moles.reduce((worst, mole) => Math.max(worst, mole.abcde_score?.total ?? 0), 0);
  const skinScore = moles.length ? Math.max(0, 100 - highest * 20) : null;

  const addMole = async (values: { name: string; location: string; size: number; color: string }) => {
    const result = await postJson('/skin/mole', {
      name: values.name,
      body_location: values.location || 'unspecified',
      size_mm: values.size,
      color: values.color || 'brown',
      notes: '',
    });
    if (!result) {
      Alert.alert('Not saved', 'The mole could not be saved.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    await reload();
  };

  const measureMole = async (values: { size: number; color: string }) => {
    if (!measuring) return;
    const result = await postJson<{ changes?: string[]; recommendation?: string; error?: string }>(
      `/skin/mole/${measuring.id}/measure`,
      { size_mm: values.size, color: values.color },
    );
    if (!result || result.error) {
      Alert.alert('Not recorded', result?.error ?? 'The measurement could not be saved.');
      return;
    }
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    if (result.changes?.length) {
      Alert.alert('This mole has changed', `${result.changes.join('\n')}\n\n${result.recommendation ?? ''}`);
    }
    await reload();
  };

  return (
    <ScreenWrapper
      title="Skin Health"
      subtitle="Track and monitor your skin"
      gradient={['#F97316', '#F59E0B']}
      rightAction={{ icon: 'add', onPress: () => setAdding(true) }}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
    >
      <View style={styles.scoreSection}>
        <ScoreRing
          score={skinScore ?? 0}
          size={120}
          strokeWidth={8}
          color={colors.health.calm}
          label="SKIN"
          sublabel={skinScore !== null ? `${moles.length} tracked` : 'Nothing tracked'}
        />
      </View>

      <SectionHeaderPremium
        icon="medical"
        iconColor="#EF4444"
        title="Mole Tracker"
        action={{ label: 'Add Mole', onPress: () => setAdding(true) }}
      />
      {moles.length === 0 ? (
        <GlassCard variant="light" style={styles.sectionCard}>
          <Text style={styles.emptyTitle}>No moles tracked</Text>
          <Text style={styles.emptyText}>
            Add one with its width in millimetres. Measuring it again later is what catches
            change, which is the sign worth showing a clinician.
          </Text>
        </GlassCard>
      ) : (
        moles.map((mole) => {
          const tint = RISK_COLOR[mole.abcde_score?.risk_level] ?? '#94A3B8';
          return (
            <GlassCard key={mole.id} variant="light" style={styles.moleCard}>
              <View style={styles.moleHeader}>
                <View style={[styles.moleIcon, { backgroundColor: tint + '15' }]}>
                  <Ionicons name="medical" size={18} color={tint} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.moleName}>{mole.name}</Text>
                  <Text style={styles.moleMeta}>
                    {mole.body_location} • {mole.size_mm} mm • {mole.color}
                  </Text>
                </View>
                <View style={[styles.riskBadge, { backgroundColor: tint + '15' }]}>
                  <Text style={[styles.riskText, { color: tint }]}>{mole.abcde_score?.risk_level}</Text>
                </View>
              </View>
              <View style={styles.abcdeRow}>
                {ABCDE_GUIDE.map((item) => {
                  const active = (mole.abcde_score?.[item.key] ?? 0) > 0;
                  return (
                    <View key={item.letter} style={[styles.abcdeItem, active && styles.abcdeItemActive]}>
                      <Text style={[styles.abcdeLetter, active && styles.abcdeLetterActive]}>{item.letter}</Text>
                    </View>
                  );
                })}
                <TouchableOpacity
                  style={styles.measureBtn}
                  onPress={() => setMeasuring(mole)}
                  accessibilityRole="button"
                  accessibilityLabel={`Record a new measurement for ${mole.name}`}
                >
                  <Ionicons name="resize" size={14} color="#F97316" />
                  <Text style={styles.measureText}>Measure</Text>
                </TouchableOpacity>
              </View>
            </GlassCard>
          );
        })
      )}

      <SectionHeaderPremium icon="information-circle" iconColor="#3B82F6" title="ABCDE Guide" />
      <GlassCard variant="light" style={styles.sectionCard}>
        {ABCDE_GUIDE.map((item, i) => (
          <View key={item.letter} style={[styles.abcdeGuideItem, i < 4 && styles.guideDivider]}>
            <View style={styles.abcdeGuideLetter}>
              <Text style={styles.abcdeGuideLetterText}>{item.letter}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.abcdeGuideLabel}>{item.label}</Text>
              <Text style={styles.abcdeGuideDesc}>{item.desc}</Text>
            </View>
          </View>
        ))}
        <Text style={styles.emptyText}>
          ABCDE is a prompt to get a mole looked at. It does not diagnose or rule out skin
          cancer — only a clinician can.
        </Text>
      </GlassCard>

      <SectionHeaderPremium icon="sunny" iconColor="#F59E0B" title="UV Index" />
      <GlassCard variant="light" style={styles.sectionCard}>
        <TextInput
          style={styles.input}
          placeholder="Your town or city"
          placeholderTextColor={colors.text.muted}
          value={location}
          onChangeText={setLocation}
          accessibilityLabel="Location for the UV reading"
        />
        {uv?.status === 'ok' ? (
          <>
            <View style={styles.uvCurrent}>
              <Text style={styles.uvValue}>{asNumber(uv.uv_index)}</Text>
              <Text style={styles.uvLabel}>{uv.level}</Text>
              <Text style={styles.uvProtection}>
                {uv.protection_needed} · SPF {uv.sunscreen_spf}
              </Text>
            </View>
            <View style={styles.uvBar}>
              {UV_LEVELS.map((level) => (
                <View key={level.level} style={[styles.uvSegment, { backgroundColor: level.color, flex: 1 }]} />
              ))}
            </View>
            <View style={styles.uvLabels}>
              {UV_LEVELS.map((level) => (
                <Text key={level.level} style={styles.uvLabelSmall}>{level.level}</Text>
              ))}
            </View>
          </>
        ) : (
          <Text style={styles.emptyText}>
            {location
              ? uv?.message ?? 'No UV reading for that location.'
              : 'Enter where you are for today’s UV index.'}
          </Text>
        )}
      </GlassCard>

      <MoleForm
        visible={adding}
        title="Track a new mole"
        submitLabel="Add"
        withName
        onClose={() => setAdding(false)}
        onSubmit={addMole}
      />
      <MoleForm
        visible={measuring !== null}
        title={measuring ? `Measure ${measuring.name}` : 'Measure'}
        submitLabel="Record"
        withName={false}
        onClose={() => setMeasuring(null)}
        onSubmit={measureMole}
      />
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  scoreSection: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.lg },
  sectionCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.md },
  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyText: { fontSize: 13, color: colors.text.muted, marginTop: 6, lineHeight: 19 },

  moleCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  moleHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  moleIcon: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  moleName: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  moleMeta: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  riskText: { fontSize: 11, fontWeight: '700', textTransform: 'capitalize' },
  abcdeRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md },
  abcdeItem: { width: 32, height: 32, borderRadius: 8, backgroundColor: colors.surface.divider, justifyContent: 'center', alignItems: 'center' },
  abcdeItemActive: { backgroundColor: '#EF444420', borderWidth: 1, borderColor: '#EF4444' },
  abcdeLetter: { fontSize: 12, fontWeight: '700', color: colors.text.muted },
  abcdeLetterActive: { color: '#EF4444' },
  measureBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, marginLeft: 'auto', paddingHorizontal: 10, paddingVertical: 6, borderRadius: radius.md, backgroundColor: '#F9731615' },
  measureText: { fontSize: 12, fontWeight: '700', color: '#F97316' },

  abcdeGuideItem: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  guideDivider: { borderBottomWidth: 1, borderBottomColor: colors.surface.divider },
  abcdeGuideLetter: { width: 32, height: 32, borderRadius: 8, backgroundColor: '#3B82F615', justifyContent: 'center', alignItems: 'center' },
  abcdeGuideLetterText: { fontSize: 14, fontWeight: '800', color: '#3B82F6' },
  abcdeGuideLabel: { fontSize: 14, fontWeight: '700', color: colors.text.primary },
  abcdeGuideDesc: { fontSize: 12, color: colors.text.muted, marginTop: 1 },

  uvCurrent: { alignItems: 'center', marginTop: spacing.md, marginBottom: spacing.lg },
  uvValue: { fontSize: 48, fontWeight: '800', color: '#F59E0B' },
  uvLabel: { fontSize: 16, fontWeight: '700', color: colors.text.primary, marginTop: 4, textTransform: 'capitalize' },
  uvProtection: { fontSize: 13, color: '#F59E0B', marginTop: 4, textAlign: 'center' },
  uvBar: { flexDirection: 'row', height: 8, borderRadius: 4, overflow: 'hidden' },
  uvSegment: { height: '100%' },
  uvLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.xs },
  uvLabelSmall: { fontSize: 9, color: colors.text.muted, flex: 1, textAlign: 'center' },

  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15, marginTop: spacing.sm },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bg.elevated, padding: spacing.xl, borderTopLeftRadius: 24, borderTopRightRadius: 24 },
  modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text.primary },
  modalActions: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.lg },
  modalButton: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.md, alignItems: 'center' },
  modalCancel: { backgroundColor: colors.surface.divider },
  modalCancelText: { color: colors.text.muted, fontWeight: '700' },
  modalSave: { backgroundColor: '#F97316' },
  modalSaveText: { color: '#FFF', fontWeight: '700' },
});
