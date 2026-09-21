/**
 * Medication Tracker — today's schedule, adherence and refill alerts.
 *
 * Marking a dose writes it and reloads rather than flipping a local flag: the
 * adherence figure above the list is computed server-side from the same logs,
 * so an optimistic tick would disagree with the score next to it.
 */
import React, { useCallback, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, RefreshControl, Alert, Modal, TextInput,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { colors, spacing, radius } from '../../src/theme';
import { GlassCard, SectionHeaderPremium, ScoreRing, ProgressBarPremium } from '../../src/components/PremiumComponents';
import { SCREEN_HEADER_TOP } from '../../src/theme/layout';
import { useApis } from '../../src/hooks/useApi';
import { postJson, asArray } from '../../src/services/http';

interface ScheduleEntry {
  medication: string;
  dosage: string;
  time: string;
  status: 'taken' | 'pending' | 'missed' | 'skipped';
  category: string;
  med_id: string;
}

interface TodaySchedule {
  date: string;
  total_doses: number;
  taken: number;
  pending: number;
  missed: number;
  adherence_pct: number;
  schedule: ScheduleEntry[];
}

interface RefillAlert {
  medication: string;
  refill_date: string;
  days_until: number;
  urgency: 'critical' | 'warning';
}

// Colour is per category rather than per medication: a stable palette keyed by
// list position would recolour every row as soon as one is added.
const CATEGORY_COLOR: Record<string, string> = {
  prescription: '#EF4444',
  supplement: '#F59E0B',
  otc: '#3B82F6',
};

function colorFor(category: string): string {
  return CATEGORY_COLOR[category] ?? '#8B5CF6';
}

function AddMedicationModal({ visible, onClose, onAdded }: {
  visible: boolean; onClose: () => void; onAdded: () => void;
}) {
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [time, setTime] = useState('08:00');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!name.trim() || !dosage.trim()) {
      Alert.alert('Add medication', 'Name and dosage are both needed.');
      return;
    }
    setSaving(true);
    const result = await postJson('/medication/add', {
      name: name.trim(),
      dosage: dosage.trim(),
      frequency: 'once_daily',
      times: [time.trim()],
      category: 'supplement',
    });
    setSaving(false);
    if (!result) {
      Alert.alert('Could not save', 'The medication was not added. Check your connection and try again.');
      return;
    }
    setName('');
    setDosage('');
    onAdded();
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.modalBackdrop}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Add a medication</Text>
          <TextInput
            style={styles.input}
            placeholder="Name (e.g. Vitamin D3)"
            placeholderTextColor={colors.text.muted}
            value={name}
            onChangeText={setName}
            accessibilityLabel="Medication name"
          />
          <TextInput
            style={styles.input}
            placeholder="Dosage (e.g. 2000 IU)"
            placeholderTextColor={colors.text.muted}
            value={dosage}
            onChangeText={setDosage}
            accessibilityLabel="Dosage"
          />
          <TextInput
            style={styles.input}
            placeholder="Time (24h, e.g. 08:00)"
            placeholderTextColor={colors.text.muted}
            value={time}
            onChangeText={setTime}
            accessibilityLabel="Time of day"
          />
          <View style={styles.modalActions}>
            <TouchableOpacity onPress={onClose} style={[styles.modalButton, styles.modalCancel]}>
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={save} disabled={saving} style={[styles.modalButton, styles.modalSave]}>
              <Text style={styles.modalSaveText}>{saving ? 'Saving…' : 'Add'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

export default function MedicationScreen() {
  const [adding, setAdding] = useState(false);
  const { data, loading, refreshing, refresh, reload } = useApis<{
    today: TodaySchedule;
    refills: { alerts: RefillAlert[] };
  }>({ today: '/medication/today', refills: '/medication/refills' });

  const today = data.today ?? null;
  const schedule = asArray<ScheduleEntry>(today?.schedule);
  const refills = asArray<RefillAlert>(data.refills?.alerts);
  const refillByName = new Map(refills.map((r) => [r.medication, r]));

  const markTaken = useCallback(async (entry: ScheduleEntry) => {
    if (entry.status === 'taken') return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const result = await postJson('/medication/dose', { medication_id: entry.med_id, status: 'taken' });
    if (!result) {
      Alert.alert('Not recorded', 'The dose could not be logged. Try again when you are back online.');
      return;
    }
    await reload();
  }, [reload]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.primary} />}
    >
      <LinearGradient colors={['#F59E0B', '#F97316']} style={styles.header}>
        <Text style={styles.headerTitle} accessibilityRole="header">Medications</Text>
        <Text style={styles.headerSubtitle}>Track your medication schedule</Text>
      </LinearGradient>

      <View style={styles.scoreSection}>
        <ScoreRing
          score={today?.adherence_pct ?? 0}
          size={120}
          strokeWidth={8}
          color={colors.health.calm}
          label="ADHERENCE"
        />
        <View style={styles.scoreInfo}>
          <Text style={styles.scoreValue}>{today?.taken ?? 0}/{today?.total_doses ?? 0}</Text>
          <Text style={styles.scoreLabel}>taken today</Text>
          <ProgressBarPremium
            value={today?.taken ?? 0}
            max={Math.max(1, today?.total_doses ?? 0)}
            color={colors.health.calm}
            height={6}
          />
        </View>
      </View>

      <SectionHeaderPremium icon="calendar" iconColor="#F59E0B" title="Today's Schedule" />

      {schedule.length === 0 && (
        <GlassCard variant="light" style={styles.medCard}>
          <Text style={styles.emptyTitle}>Nothing scheduled</Text>
          <Text style={styles.emptyBody}>
            Add a medication and its times, and the doses for each day appear here.
          </Text>
        </GlassCard>
      )}

      {schedule.map((entry) => {
        const tint = colorFor(entry.category);
        const refill = refillByName.get(entry.medication);
        return (
          <GlassCard key={`${entry.med_id}-${entry.time}`} variant="light" style={styles.medCard}>
            <View style={styles.medRow}>
              <View style={[styles.medIcon, { backgroundColor: tint + '15' }]}>
                <Ionicons name="medical" size={20} color={tint} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.medName}>{entry.medication}</Text>
                <Text style={styles.medDetail}>{entry.dosage} • {entry.time}</Text>
              </View>
              <TouchableOpacity
                style={[styles.medCheck, entry.status === 'taken' && { backgroundColor: colors.health.calm }]}
                onPress={() => markTaken(entry)}
                accessibilityRole="button"
                accessibilityLabel={
                  entry.status === 'taken'
                    ? `${entry.medication} already taken`
                    : `Mark ${entry.medication} as taken`
                }
              >
                <Ionicons
                  name={entry.status === 'taken' ? 'checkmark' : 'add'}
                  size={18}
                  color={entry.status === 'taken' ? '#FFF' : colors.text.muted}
                />
              </TouchableOpacity>
            </View>
            {refill && (
              <View style={styles.refillWarning}>
                <Ionicons name="warning" size={12} color="#F59E0B" />
                <Text style={styles.refillText}>
                  {refill.days_until === 0 ? 'Refill due today' : `Refill in ${refill.days_until} days`}
                </Text>
              </View>
            )}
          </GlassCard>
        );
      })}

      <TouchableOpacity
        style={styles.addButton}
        onPress={() => setAdding(true)}
        accessibilityRole="button"
        accessibilityLabel="Add a medication"
      >
        <Ionicons name="add" size={18} color="#FFF" />
        <Text style={styles.addButtonText}>Add medication</Text>
      </TouchableOpacity>

      <AddMedicationModal visible={adding} onClose={() => setAdding(false)} onAdded={reload} />

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg.deep },
  contentContainer: { paddingBottom: 100 },
  center: { flex: 1, backgroundColor: colors.bg.deep, justifyContent: 'center', alignItems: 'center' },
  header: { paddingTop: SCREEN_HEADER_TOP, paddingBottom: spacing.xl, paddingHorizontal: spacing.screenPadding, borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  headerTitle: { fontSize: 24, fontWeight: '800', color: '#FFF' },
  headerSubtitle: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 },

  scoreSection: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xl, marginTop: spacing.xl, marginBottom: spacing.lg, paddingHorizontal: spacing.screenPadding },
  scoreInfo: { flex: 1 },
  scoreValue: { fontSize: 28, fontWeight: '800', color: colors.text.primary },
  scoreLabel: { fontSize: 13, color: colors.text.muted, marginBottom: spacing.sm },

  medCard: { marginHorizontal: spacing.screenPadding, marginBottom: spacing.sm },
  medRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  medIcon: { width: 40, height: 40, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  medName: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  medDetail: { fontSize: 12, color: colors.text.muted, marginTop: 2 },
  medCheck: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.surface.divider, justifyContent: 'center', alignItems: 'center' },
  refillWarning: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.xs, backgroundColor: '#F59E0B15', borderRadius: 6 },
  refillText: { fontSize: 11, color: '#F59E0B', fontWeight: '600' },

  emptyTitle: { fontSize: 15, fontWeight: '700', color: colors.text.primary },
  emptyBody: { fontSize: 13, color: colors.text.muted, marginTop: 4, lineHeight: 18 },

  addButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: spacing.xs, marginHorizontal: spacing.screenPadding, marginTop: spacing.lg, paddingVertical: spacing.md, borderRadius: radius.lg, backgroundColor: '#F59E0B' },
  addButtonText: { fontSize: 15, fontWeight: '700', color: '#FFF' },

  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: colors.bg.elevated, padding: spacing.xl, borderTopLeftRadius: 24, borderTopRightRadius: 24, gap: spacing.md },
  modalTitle: { fontSize: 18, fontWeight: '800', color: colors.text.primary },
  input: { backgroundColor: colors.surface.divider, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: spacing.md, color: colors.text.primary, fontSize: 15 },
  modalActions: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm },
  modalButton: { flex: 1, paddingVertical: spacing.md, borderRadius: radius.md, alignItems: 'center' },
  modalCancel: { backgroundColor: colors.surface.divider },
  modalCancelText: { color: colors.text.muted, fontWeight: '700' },
  modalSave: { backgroundColor: '#F59E0B' },
  modalSaveText: { color: '#FFF', fontWeight: '700' },
});
